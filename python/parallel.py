import math
import time
import numpy as np
from multiprocessing import Pool, cpu_count
from sequential import generate_fractal_tree
from utils import print_header, print_params, print_result, save_result


def _worker(args):
    x, y, length, angle, ratio, branch_angle_rad, min_length, depth = args
    branches = generate_fractal_tree(x, y, length, angle, ratio, branch_angle_rad, min_length, start_depth=depth)
    return np.array(branches, dtype=np.float64)


def _build_tasks(x, y, length, angle, ratio, branch_angle_rad, min_length, depth, target_depth, upper_branches):
    if depth >= target_depth:
        return [(x, y, length, angle, ratio, branch_angle_rad, min_length, depth)]

    end_x = x + length * math.cos(angle)
    end_y = y + length * math.sin(angle)
    upper_branches.append((x, y, end_x, end_y, depth))

    new_len = length * ratio
    left = _build_tasks(end_x, end_y, new_len, angle + branch_angle_rad, ratio, branch_angle_rad, min_length, depth + 1, target_depth, upper_branches)
    right = _build_tasks(end_x, end_y, new_len, angle - branch_angle_rad, ratio, branch_angle_rad, min_length, depth + 1, target_depth, upper_branches)
    return left + right


def run_parallel(trunk_length=100.0, ratio=0.67, branch_angle=30.0,
                        min_length=0.01, num_processes=None, output_file=None):

    if num_processes is None:
        num_processes = cpu_count()

    branch_angle_rad = math.radians(branch_angle)
    split_depth = max(1, math.ceil(math.log2(num_processes * 4)))

    print_header("Parallel Simple (Python)")
    print_params(trunk_length, ratio, branch_angle, min_length,
                 cores=num_processes, split_depth=split_depth)

    start_time = time.perf_counter()

    # Build upper levels sequentially
    upper_branches = [(0, 0, 0 + trunk_length * math.cos(math.pi / 2),
                        0 + trunk_length * math.sin(math.pi / 2), 0)]
    root_end_x, root_end_y = upper_branches[0][2], upper_branches[0][3]
    new_len = trunk_length * ratio

    tasks = _build_tasks(root_end_x, root_end_y, new_len, math.pi / 2 + branch_angle_rad,
                         ratio, branch_angle_rad, min_length, 1, split_depth, upper_branches)
    tasks += _build_tasks(root_end_x, root_end_y, new_len, math.pi / 2 - branch_angle_rad,
                          ratio, branch_angle_rad, min_length, 1, split_depth, upper_branches)

    with Pool(processes=num_processes) as pool:
        results = pool.map(_worker, tasks)

    upper_array = np.array(upper_branches, dtype=np.float64)
    branches = np.concatenate([upper_array] + results)

    execution_time = time.perf_counter() - start_time

    total_branches = len(branches)
    max_depth = int(branches[:, 4].max()) if total_branches > 0 else 0
    print_result(execution_time, total_branches, max_depth)

    result = {
        'parameters': {
            'trunk_length': trunk_length,
            'ratio': ratio,
            'branch_angle': branch_angle,
            'min_length': min_length,
            'split_depth': split_depth,
            'num_processes': num_processes,
        },
        'execution_time': execution_time,
    }
    
    if output_file is not None:
        save_result(result, branches, output_file)

    return result


if __name__ == "__main__":

    run_parallel(
        trunk_length=100.0,
        ratio=0.67,
        branch_angle=30.0,
        min_length=0.01,
        output_file="parallel_python.json"
    )
