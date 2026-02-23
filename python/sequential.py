import math
import time
from utils import print_header, print_params, print_result

# Returns list of (x1, y1, x2, y2, depth) tuples.
def generate_fractal_tree(x, y, length, angle, ratio, branch_angle_radians, min_length, start_depth=0):

    branches = []

    def recurse(x, y, length, angle, depth):
        if length < min_length:
            return

        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        branches.append((x, y, end_x, end_y, depth))

        new_length = length * ratio
        recurse(end_x, end_y, new_length, angle + branch_angle_radians, depth + 1)
        recurse(end_x, end_y, new_length, angle - branch_angle_radians, depth + 1)

    recurse(x, y, length, angle, start_depth)
    return branches


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

    max_depth = max(b[4] for b in branches) if branches else 0
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
