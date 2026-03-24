import math
import time
import contextlib
import io
import csv
import os

from sequential_asymmetric import generate_fractal_tree_asymmetric
from parallel_asymmetric import run_parallel_asymmetric

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, 'data', 'experiments')
CSV_PATH     = os.path.join(OUTPUT_DIR, 'python_asymmetric_variable_ratio.csv')

# Phase 3 — variable reduction ratio, asymmetric tree
# Fixed: left_angle=35°, right_angle=25°, min_length=1.0, cores=4
#
# left_ratio varies: [0.5, 0.6, 0.7, 0.8]
# right_ratio = left_ratio - 0.10 (preserves the original 0.67/0.57 offset)
#
# min_length=1.0 is chosen so all ratio values produce a runnable experiment.
# Branch count grows exponentially with ratio — this spread is intentional:
#   left=0.5, right=0.4 → tiny tree    (overhead-dominated, poor speedup)
#   left=0.8, right=0.7 → large tree   (compute-dominated, better speedup)

NUM_PROCESSES  = 4
TRUNK_LENGTH   = 100.0
LEFT_ANGLE     = 35.0
RIGHT_ANGLE    = 25.0
MIN_LENGTH     = 1.0
RATIO_OFFSET   = 0.10   # right_ratio is always left_ratio - RATIO_OFFSET
LEFT_RATIOS    = [0.5, 0.6, 0.7, 0.8]

def _time_sequential(left_ratio, right_ratio):
    left_rad  = math.radians(LEFT_ANGLE)
    right_rad = math.radians(RIGHT_ANGLE)
    t0 = time.perf_counter()
    branches = generate_fractal_tree_asymmetric(
        0, 0, TRUNK_LENGTH, math.pi / 2,
        left_ratio, right_ratio, left_rad, right_rad, MIN_LENGTH,
    )
    return time.perf_counter() - t0, len(branches)

def _time_parallel(left_ratio, right_ratio):
    with contextlib.redirect_stdout(io.StringIO()):
        result = run_parallel_asymmetric(
            trunk_length=TRUNK_LENGTH,
            left_ratio=left_ratio,
            right_ratio=right_ratio,
            left_angle=LEFT_ANGLE,
            right_angle=RIGHT_ANGLE,
            min_length=MIN_LENGTH,
            num_processes=NUM_PROCESSES,
        )
    return result['execution_time']

if __name__ == '__main__':
    print(f"\n=== Variable ratio (asymmetric) | left_angle={LEFT_ANGLE}°, right_angle={RIGHT_ANGLE}°, "
          f"min_length={MIN_LENGTH}, cores={NUM_PROCESSES} ===")
    print(f"{'left r':>8} {'right r':>8} {'branches':>12} {'seq (s)':>10} {'par (s)':>10} {'speedup':>9} {'efficiency':>12}")
    print("-" * 74)

    rows = []
    for left_ratio in LEFT_RATIOS:
        right_ratio                = round(left_ratio - RATIO_OFFSET, 2)
        seq_time, branch_count     = _time_sequential(left_ratio, right_ratio)
        par_time                   = _time_parallel(left_ratio, right_ratio)
        speedup                    = seq_time / par_time
        efficiency                 = speedup / NUM_PROCESSES

        print(f"{left_ratio:>8.2f} {right_ratio:>8.2f} {branch_count:>12,} "
              f"{seq_time:>10.5f} {par_time:>10.5f} {speedup:>8.3f}x {efficiency:>11.1%}")
        rows.append({'left_ratio': left_ratio, 'right_ratio': right_ratio, 'branches': branch_count,
                     'seq_time': f'{seq_time:.6f}', 'par_time': f'{par_time:.6f}',
                     'speedup': f'{speedup:.4f}', 'efficiency': f'{efficiency:.4f}'})

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['left_ratio', 'right_ratio', 'branches', 'seq_time', 'par_time', 'speedup', 'efficiency'])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved: {CSV_PATH}")
