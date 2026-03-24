import math
import time
import numpy as np
from multiprocessing import Pool, cpu_count
from sequential import generate_fractal_tree
from utils import print_header, print_params, print_result


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
                        min_length=0.01, num_processes=None):

    if num_processes is None:
        num_processes = cpu_count()

    branch_angle_rad = math.radians(branch_angle)
    split_depth = max(1, math.ceil(math.log2(num_processes * 4)))

    print_header("Parallel (Python)")
    print_params(trunk_length, ratio, branch_angle, min_length,
                 cores=num_processes, split_depth=split_depth)

    start_time = time.perf_counter()

    # Build upper levels sequentially
    start_x, start_y = 0, 0
    start_angle = math.pi / 2
    end_x = start_x + trunk_length * math.cos(start_angle)
    end_y = start_y + trunk_length * math.sin(start_angle)
    start_depth = 0

    upper_branches = [(start_x, start_y, end_x, end_y, start_depth)]
    new_len = trunk_length * ratio
    left_child_angle_rad = start_angle + branch_angle_rad
    right_child_angle_rad = start_angle - branch_angle_rad

    # left subtree
    tasks = _build_tasks(end_x, end_y, 
                         new_len, left_child_angle_rad,
                         ratio, branch_angle_rad, 
                         min_length, 1, 
                         split_depth, upper_branches)
    
    # right subtree
    tasks += _build_tasks(end_x, end_y, 
                          new_len, right_child_angle_rad,
                          ratio, branch_angle_rad, 
                          min_length, 1, 
                          split_depth, upper_branches)

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

    return result


if __name__ == "__main__":

    run_parallel(
        trunk_length=100.0,
        ratio=0.67,
        branch_angle=30.0,
        min_length=0.01,
    )
