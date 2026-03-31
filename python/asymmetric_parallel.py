import math
import time
import numpy as np
from multiprocessing import Pool, cpu_count
from asymmetric_sequential import generate_fractal_tree_asymmetric
from utils import print_header, print_params, print_result


def _worker(args):
    x, y, length, angle, left_ratio, right_ratio, left_angle_rad, right_angle_rad, min_length, depth = args
    branches = generate_fractal_tree_asymmetric(
        x, y, length, angle, left_ratio, right_ratio, left_angle_rad, right_angle_rad, min_length,
        start_depth=depth
    )
    return np.array(branches, dtype=np.float64)


def _build_tasks(x, y, length, angle, left_ratio, right_ratio, left_angle_rad, right_angle_rad,
                 min_length, depth, target_depth, upper_branches):
    if depth >= target_depth:
        return [(x, y, length, angle, left_ratio, right_ratio, left_angle_rad, right_angle_rad, min_length, depth)]

    end_x = x + length * math.cos(angle)
    end_y = y + length * math.sin(angle)
    upper_branches.append((x, y, end_x, end_y, depth))

    left = _build_tasks(end_x, end_y, length * left_ratio,  angle + left_angle_rad, 
                        left_ratio, right_ratio, left_angle_rad, right_angle_rad,
                        min_length, depth + 1, target_depth, upper_branches)

    right = _build_tasks(end_x, end_y, length * right_ratio, angle - right_angle_rad, 
                         left_ratio, right_ratio, left_angle_rad, right_angle_rad,
                         min_length, depth + 1, target_depth, upper_branches)
    return left + right


def run_parallel_asymmetric(trunk_length=100.0, left_ratio=0.67, right_ratio=0.57,
                             left_angle=35.0, right_angle=25.0,
                             min_length=0.01, num_processes=None, split_depth=None):

    if num_processes is None:
        num_processes = cpu_count()

    left_angle_rad  = math.radians(left_angle)
    right_angle_rad = math.radians(right_angle)
    if split_depth is None:
        split_depth = (num_processes * 4).bit_length() - 1

    print_header("Parallel Asymmetric (Python)")
    print_params(trunk_length, left_ratio, left_angle, min_length,
                 right_ratio=right_ratio, right_angle=right_angle,
                 cores=num_processes, split_depth=split_depth)

    start_time = time.perf_counter()

    start_x, start_y = 0, 0
    start_angle = math.pi / 2
    end_x = start_x + trunk_length * math.cos(start_angle)
    end_y = start_y + trunk_length * math.sin(start_angle)
    start_depth = 0

    upper_branches = [(start_x, start_y, end_x, end_y, start_depth)]

    left_child_len = trunk_length * left_ratio
    right_child_len = trunk_length * right_ratio
    left_child_angle_rad = start_angle + left_angle_rad
    right_child_angle_rad = start_angle - right_angle_rad

    # left subtree
    tasks = _build_tasks(end_x, end_y, 
                         left_child_len,left_child_angle_rad, 
                         left_ratio, right_ratio, 
                         left_angle_rad, right_angle_rad,
                         min_length, 1, split_depth, upper_branches)
    # right subtree
    tasks += _build_tasks(end_x, end_y, 
                          right_child_len, right_child_angle_rad,
                          left_ratio, right_ratio, 
                          left_angle_rad, right_angle_rad,
                          min_length, 1, split_depth, upper_branches)

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
            'left_ratio': left_ratio,
            'right_ratio': right_ratio,
            'left_angle': left_angle,
            'right_angle': right_angle,
            'min_length': min_length,
            'split_depth': split_depth,
            'num_processes': num_processes,
        },
        'execution_time': execution_time,
    }

    return result


if __name__ == "__main__":

    run_parallel_asymmetric(
        trunk_length=100.0,
        left_ratio=0.67,
        right_ratio=0.57,
        left_angle=35.0,
        right_angle=25.0,
        min_length=0.01,
    )
