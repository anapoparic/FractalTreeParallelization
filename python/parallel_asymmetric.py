import math
import time
import numpy as np
from multiprocessing import Pool, cpu_count
from sequential_asymmetric import generate_fractal_tree_asymmetric
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
                             min_length=0.01, num_processes=None):

    if num_processes is None:
        num_processes = cpu_count()

    left_angle_rad  = math.radians(left_angle)
    right_angle_rad = math.radians(right_angle)
    split_depth = max(1, math.ceil(math.log2(num_processes * 4)))

    print_header("Parallel Asymmetric (Python)")
    print_params(trunk_length, left_ratio, left_angle, min_length,
                 right_ratio=right_ratio, right_angle=right_angle,
                 cores=num_processes, split_depth=split_depth)

    start_time = time.perf_counter()

    # Root branch is always vertical (symmetric starting point)
    upper_branches = [(0, 0,
                       0 + trunk_length * math.cos(math.pi / 2),
                       0 + trunk_length * math.sin(math.pi / 2), 0)]
    root_end_x, root_end_y = upper_branches[0][2], upper_branches[0][3]

    tasks = _build_tasks(root_end_x, root_end_y, trunk_length * left_ratio,
                         math.pi / 2 + left_angle_rad,
                         left_ratio, right_ratio, left_angle_rad, right_angle_rad,
                         min_length, 1, split_depth, upper_branches)
    tasks += _build_tasks(root_end_x, root_end_y, trunk_length * right_ratio,
                          math.pi / 2 - right_angle_rad,
                          left_ratio, right_ratio, left_angle_rad, right_angle_rad,
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
