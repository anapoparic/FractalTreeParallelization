import math
import time
import numpy as np
from multiprocessing import Pool, cpu_count
from utils import print_header, print_params, print_result, save_result


def calculate_optimal_depth(trunk_length, ratio, min_length, num_cores):
    if ratio >= 1 or ratio <= 0:
        return 2

    estimated_depth = abs(math.log(min_length / trunk_length) / math.log(ratio))

    # Target: 2^parallel_depth = num_cores * 4 (oversubscription)
    target_tasks = num_cores * 4
    parallel_depth = max(1, int(math.log2(target_tasks)))

    max_parallel_depth = max(2, int(estimated_depth * 0.25))
    parallel_depth = min(parallel_depth, max_parallel_depth)

    return parallel_depth


def count_subtree_branches(length, ratio, min_length):
    if length < min_length:
        return 0
    return 1 + 2 * count_subtree_branches(length * ratio, ratio, min_length)


def generate_subtree_worker(args):
    x, y, length, angle, ratio, branch_angle, min_length, depth, subtree_size = args

    buffer = np.empty((subtree_size, 5), dtype=np.float64)
    idx = 0

    def recurse(x, y, length, angle, depth):
        nonlocal idx
        if length < min_length:
            return

        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        buffer[idx] = (x, y, end_x, end_y, depth)
        idx += 1

        new_len = length * ratio
        recurse(end_x, end_y, new_len, angle + branch_angle, depth + 1)
        recurse(end_x, end_y, new_len, angle - branch_angle, depth + 1)

    recurse(x, y, length, angle, depth)
    return buffer


def run_parallel(trunk_length=100.0, ratio=0.67, branch_angle=30.0,
                 min_length=0.01, num_processes=None, output_file="../data/parallel_python.json"):

    if num_processes is None:
        num_processes = cpu_count()

    branch_angle_radians = math.radians(branch_angle)

    # Calculate optimal parallel depth
    parallel_depth = calculate_optimal_depth(trunk_length, ratio, min_length, num_processes)
    num_tasks = 2 ** parallel_depth

    print_header("Parallel (Python)")
    print_params(trunk_length, ratio, branch_angle, min_length,
                 cores=num_processes, parallel_depth=parallel_depth, tasks=num_tasks)

    start_time = time.perf_counter()

    # Generate root
    root_end_x = 0 + trunk_length * math.cos(math.pi / 2)
    root_end_y = 0 + trunk_length * math.sin(math.pi / 2)
    upper_branches = [(0, 0, root_end_x, root_end_y, 0)]

    # Create tasks by traversing tree to parallel_depth
    task_args = []

    def create_tasks(x, y, length, angle, depth, target_depth):
        if depth >= target_depth:
            task_args.append((x, y, length, angle, ratio, branch_angle_radians,
                              min_length, depth))
            return

        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        upper_branches.append((x, y, end_x, end_y, depth))

        new_len = length * ratio
        create_tasks(end_x, end_y, new_len, angle + branch_angle_radians, depth + 1, target_depth)
        create_tasks(end_x, end_y, new_len, angle - branch_angle_radians, depth + 1, target_depth)

    new_len = trunk_length * ratio
    create_tasks(root_end_x, root_end_y, new_len, math.pi / 2 + branch_angle_radians, 1, parallel_depth)
    create_tasks(root_end_x, root_end_y, new_len, math.pi / 2 - branch_angle_radians, 1, parallel_depth)

    # Pre-calculate subtree size (all tasks at same depth have same size)
    subtree_size = count_subtree_branches(task_args[0][2], ratio, min_length)

    # Add subtree_size to each task's args
    task_args = [args + (subtree_size,) for args in task_args]

    # Process in parallel — each worker returns a numpy array
    with Pool(processes=num_processes) as pool:
        results = pool.map(generate_subtree_worker, task_args, chunksize=1)

    # Merge: convert upper branches to numpy + concatenate all arrays
    upper_array = np.array(upper_branches, dtype=np.float64)
    all_arrays = [upper_array] + results
    branches = np.concatenate(all_arrays)

    execution_time = time.perf_counter() - start_time

    total_branches = len(branches)
    max_depth_actual = int(branches[:, 4].max()) if total_branches > 0 else 0
    print_result(execution_time, total_branches, max_depth_actual)

    result = {
        'parameters': {
            'trunk_length': trunk_length,
            'ratio': ratio,
            'branch_angle': branch_angle,
            'min_length': min_length,
            'parallel_depth': parallel_depth,
            'num_processes': num_processes,
        },
        'execution_time': execution_time,
    }
    # save_result(result, all_branches, output_file)

    return result


if __name__ == "__main__":

    run_parallel(
        trunk_length = 100.0,
        ratio = 0.67,
        branch_angle = 30.0,
        min_length = 0.01,
        output_file = "../data/parallel_python.json"
    )
