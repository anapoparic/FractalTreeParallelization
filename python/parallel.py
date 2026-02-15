import math
import time
import struct
from multiprocessing import Pool, cpu_count
from utils import print_header, print_params, print_result, save_result

# Each branch: 4 doubles (x1,y1,x2,y2) + 1 int (depth)
BRANCH_FORMAT = 'ddddi'
BRANCH_SIZE = struct.calcsize(BRANCH_FORMAT)


def calculate_optimal_depth(trunk_length, ratio, min_length, num_cores):
    """Calculate best parallel_depth to balance overhead vs parallelism."""
    if ratio >= 1 or ratio <= 0:
        return 2

    estimated_depth = abs(math.log(min_length / trunk_length) / math.log(ratio))

    # Target: 2^parallel_depth = num_cores * 2 (slight oversubscription)
    target_tasks = num_cores * 4
    parallel_depth = max(1, int(math.log2(target_tasks)))

    max_parallel_depth = max(2, int(estimated_depth * 0.25))
    parallel_depth = min(parallel_depth, max_parallel_depth)

    return parallel_depth


def generate_subtree_worker(args):
    x, y, length, angle, ratio, branch_angle, min_length, depth= args

    parts = []

    def recurse(x, y, length, angle, depth):
        if length < min_length:
            return

        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        parts.append(struct.pack(BRANCH_FORMAT, x, y, end_x, end_y, depth))

        new_len = length * ratio
        recurse(end_x, end_y, new_len, angle + branch_angle, depth + 1)
        recurse(end_x, end_y, new_len, angle - branch_angle, depth + 1)

    recurse(x, y, length, angle, depth)
    return b''.join(parts)


def unpack_branches(data):
    """Unpack a bytes buffer into branch tuples."""
    branches = []
    offset = 0
    while offset < len(data):
        branches.append(struct.unpack_from(BRANCH_FORMAT, data, offset))
        offset += BRANCH_SIZE
    return branches


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

    start_time = time.time()

    # Generate root
    root_end_x = 0 + trunk_length * math.cos(math.pi / 2)
    root_end_y = 0 + trunk_length * math.sin(math.pi / 2)
    branches = [(0, 0, root_end_x, root_end_y, 0)]

    # Create tasks by traversing tree to parallel_depth
    task_args = []

    def create_tasks(x, y, length, angle, depth, target_depth):
        if depth >= target_depth:
            task_args.append((x, y, length, angle, ratio, branch_angle_radians,
                              min_length, depth))
            return

        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        branches.append((x, y, end_x, end_y, depth))

        new_len = length * ratio
        create_tasks(end_x, end_y, new_len, angle + branch_angle_radians, depth + 1, target_depth)
        create_tasks(end_x, end_y, new_len, angle - branch_angle_radians, depth + 1, target_depth)

    new_len = trunk_length * ratio
    create_tasks(root_end_x, root_end_y, new_len, math.pi / 2 + branch_angle_radians, 1, parallel_depth)
    create_tasks(root_end_x, root_end_y, new_len, math.pi / 2 - branch_angle_radians, 1, parallel_depth)

    # Process in parallel — each worker returns bytes
    with Pool(processes=num_processes) as pool:
        results = pool.map(generate_subtree_worker, task_args, chunksize=1)

    # Unpack bytes buffers into branch tuples
    for data in results:
        branches.extend(unpack_branches(data))

    execution_time = time.time() - start_time

    max_depth_actual = max(b[4] for b in branches) if branches else 0
    print_result(execution_time, len(branches), max_depth_actual)

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
