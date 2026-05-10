import math
import time
import numpy as np
from utils import print_header, print_params, print_result

# Returns numpy array of shape (N, 5) with columns (x1, y1, x2, y2, depth).
def generate_fractal_tree(x, y, length, angle, ratio, branch_angle_radians, min_length, start_depth=0):
    if length < min_length:
        return np.empty((0, 5), dtype=np.float64)

    max_depth = math.floor(math.log(min_length / length) / math.log(ratio))
    branches = np.empty((2 ** (max_depth + 1) - 1, 5), dtype=np.float64)
    idx = 0

    def recurse(x, y, length, angle, depth):
        nonlocal idx
        if length < min_length:
            return
        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        branches[idx] = (x, y, end_x, end_y, depth)
        idx += 1
        new_length = length * ratio
        recurse(end_x, end_y, new_length, angle + branch_angle_radians, depth + 1)
        recurse(end_x, end_y, new_length, angle - branch_angle_radians, depth + 1)

    recurse(x, y, length, angle, start_depth)
    return branches[:idx]


def run_sequential(trunk_length=100.0, ratio=0.67, branch_angle=30.0,
                   min_length=1.0):

    branch_angle_radians = math.radians(branch_angle)

    print_header("Sequential (Python)")
    print_params(trunk_length, ratio, branch_angle, min_length)

    start_time = time.perf_counter()
    branches = generate_fractal_tree(
        0, 0, trunk_length, math.pi / 2, ratio, branch_angle_radians, min_length
    )
    execution_time = time.perf_counter() - start_time

    max_depth = int(branches[:, 4].max()) if len(branches) > 0 else 0
    print_result(execution_time, len(branches), max_depth)

    result = {
        'parameters': {
            'trunk_length': trunk_length,
            'ratio': ratio,
            'branch_angle': branch_angle,
            'min_length': min_length
        },
        'execution_time': execution_time,
    }

    return result


if __name__ == "__main__":

    run_sequential(
        trunk_length = 100.0,
        ratio = 0.67,
        branch_angle = 30.0,
        min_length = 0.01,
    )
