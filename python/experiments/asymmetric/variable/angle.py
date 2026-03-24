import math
import time
import contextlib
import io

from sequential_asymmetric import generate_fractal_tree_asymmetric
from parallel_asymmetric import run_parallel_asymmetric

# Phase 3 — variable branch angles, asymmetric tree
# Fixed: left_ratio=0.67, right_ratio=0.57, min_length=0.01, cores=4
#
# left_angle varies: [15°, 30°, 45°, 60°]
# right_angle scales proportionally to preserve original asymmetry ratio:
#   right_angle = left_angle * (25 / 35) ≈ left_angle * 0.714
#
# Note: angles do not change branch count — only ratio and min_length do.
# Speedup should remain roughly constant across all angle values, confirming
# that geometry alone has no effect on parallelization efficiency.

NUM_PROCESSES  = 4
TRUNK_LENGTH   = 100.0
LEFT_RATIO     = 0.67
RIGHT_RATIO    = 0.57
MIN_LENGTH     = 0.01
ANGLE_RATIO    = 25.0 / 35.0   # preserves original left/right angle proportion
LEFT_ANGLES    = [15.0, 30.0, 45.0, 60.0]

def _time_sequential(left_angle, right_angle):
    left_rad  = math.radians(left_angle)
    right_rad = math.radians(right_angle)
    t0 = time.perf_counter()
    branches = generate_fractal_tree_asymmetric(
        0, 0, TRUNK_LENGTH, math.pi / 2,
        LEFT_RATIO, RIGHT_RATIO, left_rad, right_rad, MIN_LENGTH,
    )
    return time.perf_counter() - t0, len(branches)

def _time_parallel(left_angle, right_angle):
    with contextlib.redirect_stdout(io.StringIO()):
        result = run_parallel_asymmetric(
            trunk_length=TRUNK_LENGTH,
            left_ratio=LEFT_RATIO,
            right_ratio=RIGHT_RATIO,
            left_angle=left_angle,
            right_angle=right_angle,
            min_length=MIN_LENGTH,
            num_processes=NUM_PROCESSES,
        )
    return result['execution_time']

if __name__ == '__main__':
    print(f"\n=== Variable branch angles (asymmetric) | left_ratio={LEFT_RATIO}, right_ratio={RIGHT_RATIO}, "
          f"min_length={MIN_LENGTH}, cores={NUM_PROCESSES} ===")
    print(f"{'left °':>8} {'right °':>8} {'branches':>12} {'seq (s)':>10} {'par (s)':>10} {'speedup':>9} {'efficiency':>12}")
    print("-" * 74)

    for left_angle in LEFT_ANGLES:
        right_angle                = round(left_angle * ANGLE_RATIO, 1)
        seq_time, branch_count     = _time_sequential(left_angle, right_angle)
        par_time                   = _time_parallel(left_angle, right_angle)
        speedup                    = seq_time / par_time
        efficiency                 = speedup / NUM_PROCESSES

        print(f"{left_angle:>8.1f} {right_angle:>8.1f} {branch_count:>12,} "
              f"{seq_time:>10.5f} {par_time:>10.5f} {speedup:>8.3f}x {efficiency:>11.1%}")
