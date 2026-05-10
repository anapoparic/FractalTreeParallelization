import math
import time
import numpy as np
from functools import lru_cache
from utils import print_header, print_params, print_result


def _count_asymmetric(starting_length, left_ratio, right_ratio, min_length):
    """Count branches exactly using memoization on (left_turns, right_turns).
    Runs in O(D_left × D_right) ≈ O(459) steps regardless of tree size."""
    @lru_cache(maxsize=None)
    def count(a, b):
        if starting_length * (left_ratio ** a) * (right_ratio ** b) < min_length:
            return 0
        return 1 + count(a + 1, b) + count(a, b + 1)
    return count(0, 0)


# Returns numpy array of shape (N, 5) with columns (x1, y1, x2, y2, depth).
# Asymmetric variant: left and right branches use different angles and ratios.
def generate_fractal_tree_asymmetric(x, y, length, angle, left_ratio, right_ratio,
                                     left_angle_rad, right_angle_rad, min_length, start_depth=0):
    if length < min_length:
        return np.empty((0, 5), dtype=np.float64)

    n_branches = _count_asymmetric(length, left_ratio, right_ratio, min_length)
    branches = np.empty((n_branches, 5), dtype=np.float64)
    idx = 0

    def recurse(x, y, length, angle, depth):
        nonlocal idx
        if length < min_length:
            return
        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        branches[idx] = (x, y, end_x, end_y, depth)
        idx += 1
        recurse(end_x, end_y, length * left_ratio,  angle + left_angle_rad,  depth + 1)
        recurse(end_x, end_y, length * right_ratio, angle - right_angle_rad, depth + 1)

    recurse(x, y, length, angle, start_depth)
    return branches[:idx]


def run_sequential_asymmetric(trunk_length=100.0, left_ratio=0.67, right_ratio=0.57,
                               left_angle=35.0, right_angle=25.0, min_length=1.0):

    left_angle_rad  = math.radians(left_angle)
    right_angle_rad = math.radians(right_angle)

    print_header("Sequential Asymmetric (Python)")
    print_params(trunk_length, left_ratio, left_angle, min_length,
                 right_ratio=right_ratio, right_angle=right_angle)

    start_time = time.perf_counter()
    branches = generate_fractal_tree_asymmetric(
        0, 0, trunk_length, math.pi / 2,
        left_ratio, right_ratio, left_angle_rad, right_angle_rad, min_length
    )
    execution_time = time.perf_counter() - start_time

    max_depth = int(branches[:, 4].max()) if len(branches) > 0 else 0
    print_result(execution_time, len(branches), max_depth)

    result = {
        'parameters': {
            'trunk_length': trunk_length,
            'left_ratio': left_ratio,
            'right_ratio': right_ratio,
            'left_angle': left_angle,
            'right_angle': right_angle,
            'min_length': min_length,
        },
        'execution_time': execution_time,
    }

    return result


if __name__ == "__main__":

    run_sequential_asymmetric(
        trunk_length=100.0,
        left_ratio=0.67,
        right_ratio=0.57,
        left_angle=35.0,
        right_angle=25.0,
        min_length=0.01,
    )
