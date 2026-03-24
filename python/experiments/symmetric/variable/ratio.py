import math
import time
import contextlib
import io

from sequential import generate_fractal_tree
from parallel import run_parallel

# Phase 3 — variable reduction ratio (controls how fast branches shrink)
# Fixed: angle=30°, min_length=1.0, cores=4
# Question: how does reduction ratio affect parallelization efficiency?
#
# min_length=1.0 is deliberately chosen so all ratio values produce a
# runnable experiment. Branch count grows exponentially with ratio:
#   ratio=0.5 → ~255 branches  (overhead-dominated, expect poor speedup)
#   ratio=0.6 → ~1,023 branches
#   ratio=0.7 → ~16,383 branches
#   ratio=0.8 → ~1,500,000 branches  (compute-dominated, expect real speedup)
# This spread is the experiment — it demonstrates how problem size driven by
# ratio determines whether parallelization pays off.

NUM_PROCESSES = 4
TRUNK_LENGTH  = 100.0
ANGLE         = 30.0
MIN_LENGTH    = 1.0
VALUES        = [0.5, 0.6, 0.7, 0.8]

def _time_sequential(ratio):
    angle_rad = math.radians(ANGLE)
    t0 = time.perf_counter()
    branches = generate_fractal_tree(0, 0, TRUNK_LENGTH, math.pi / 2, ratio, angle_rad, MIN_LENGTH)
    return time.perf_counter() - t0, len(branches)

def _time_parallel(ratio):
    with contextlib.redirect_stdout(io.StringIO()):
        result = run_parallel(
            trunk_length=TRUNK_LENGTH,
            ratio=ratio,
            branch_angle=ANGLE,
            min_length=MIN_LENGTH,
            num_processes=NUM_PROCESSES,
        )
    return result['execution_time']

if __name__ == '__main__':
    print(f"\n=== Variable ratio | angle={ANGLE}°, min_length={MIN_LENGTH}, cores={NUM_PROCESSES} ===")
    print(f"{'ratio':>8} {'branches':>12} {'seq (s)':>10} {'par (s)':>10} {'speedup':>9} {'efficiency':>12}")
    print("-" * 66)

    for val in VALUES:
        seq_time, branch_count = _time_sequential(val)
        par_time               = _time_parallel(val)
        speedup                = seq_time / par_time
        efficiency             = speedup / NUM_PROCESSES

        print(f"{val:>8.2f} {branch_count:>12,} {seq_time:>10.5f} {par_time:>10.5f} {speedup:>8.3f}x {efficiency:>11.1%}")
