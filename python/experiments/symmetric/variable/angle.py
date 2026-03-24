import math
import time
import contextlib
import io

from sequential import generate_fractal_tree
from parallel import run_parallel

# Phase 3 — variable branch angle
# Fixed: ratio=0.67, min_length=0.01, cores=4
# Question: how does branching angle affect parallelization efficiency?
#
# Note: branch angle does NOT change the number of branches — only ratio and
# min_length determine when recursion stops. Angle only affects the geometry
# (shape) of the tree. Therefore speedup should remain roughly constant across
# angles, which is itself a valid scientific observation.

NUM_PROCESSES = 4
TRUNK_LENGTH  = 100.0
RATIO         = 0.67
MIN_LENGTH    = 0.01
VALUES        = [15.0, 30.0, 45.0, 60.0]

def _time_sequential(angle):
    angle_rad = math.radians(angle)
    t0 = time.perf_counter()
    branches = generate_fractal_tree(0, 0, TRUNK_LENGTH, math.pi / 2, RATIO, angle_rad, MIN_LENGTH)
    return time.perf_counter() - t0, len(branches)

def _time_parallel(angle):
    with contextlib.redirect_stdout(io.StringIO()):
        result = run_parallel(
            trunk_length=TRUNK_LENGTH,
            ratio=RATIO,
            branch_angle=angle,
            min_length=MIN_LENGTH,
            num_processes=NUM_PROCESSES,
        )
    return result['execution_time']

if __name__ == '__main__':
    print(f"\n=== Variable branch angle | ratio={RATIO}, min_length={MIN_LENGTH}, cores={NUM_PROCESSES} ===")
    print(f"{'angle (°)':>10} {'branches':>12} {'seq (s)':>10} {'par (s)':>10} {'speedup':>9} {'efficiency':>12}")
    print("-" * 68)

    for val in VALUES:
        seq_time, branch_count = _time_sequential(val)
        par_time               = _time_parallel(val)
        speedup                = seq_time / par_time
        efficiency             = speedup / NUM_PROCESSES

        print(f"{val:>10.1f} {branch_count:>12,} {seq_time:>10.5f} {par_time:>10.5f} {speedup:>8.3f}x {efficiency:>11.1%}")
