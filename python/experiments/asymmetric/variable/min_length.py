import math
import time
import contextlib
import io

from sequential_asymmetric import generate_fractal_tree_asymmetric
from parallel_asymmetric import run_parallel_asymmetric

# Phase 3 — variable min_length, asymmetric tree
# Fixed: left_ratio=0.67, right_ratio=0.57, left_angle=35°, right_angle=25°, cores=4
# Question: how does problem size affect parallelization efficiency?

NUM_PROCESSES = 4
TRUNK_LENGTH  = 100.0
LEFT_RATIO    = 0.67
RIGHT_RATIO   = 0.57
LEFT_ANGLE    = 35.0
RIGHT_ANGLE   = 25.0
VALUES        = [0.2, 0.1, 0.01, 0.001]

def _time_sequential(min_length):
    left_rad  = math.radians(LEFT_ANGLE)
    right_rad = math.radians(RIGHT_ANGLE)
    t0 = time.perf_counter()
    branches = generate_fractal_tree_asymmetric(
        0, 0, TRUNK_LENGTH, math.pi / 2,
        LEFT_RATIO, RIGHT_RATIO, left_rad, right_rad, min_length,
    )
    return time.perf_counter() - t0, len(branches)

def _time_parallel(min_length):
    with contextlib.redirect_stdout(io.StringIO()):
        result = run_parallel_asymmetric(
            trunk_length=TRUNK_LENGTH,
            left_ratio=LEFT_RATIO,
            right_ratio=RIGHT_RATIO,
            left_angle=LEFT_ANGLE,
            right_angle=RIGHT_ANGLE,
            min_length=min_length,
            num_processes=NUM_PROCESSES,
        )
    return result['execution_time']

if __name__ == '__main__':
    print(f"\n=== Variable min_length (asymmetric) | left_ratio={LEFT_RATIO}, right_ratio={RIGHT_RATIO}, "
          f"left_angle={LEFT_ANGLE}°, right_angle={RIGHT_ANGLE}°, cores={NUM_PROCESSES} ===")
    print(f"{'min_length':>12} {'branches':>12} {'seq (s)':>10} {'par (s)':>10} {'speedup':>9} {'efficiency':>12}")
    print("-" * 70)

    for val in VALUES:
        seq_time, branch_count = _time_sequential(val)
        par_time               = _time_parallel(val)
        speedup                = seq_time / par_time
        efficiency             = speedup / NUM_PROCESSES

        print(f"{val:>12} {branch_count:>12,} {seq_time:>10.5f} {par_time:>10.5f} {speedup:>8.3f}x {efficiency:>11.1%}")
