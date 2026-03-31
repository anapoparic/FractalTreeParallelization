import math
import time
import contextlib
import io
import csv
import os

from asymmetric_sequential import generate_fractal_tree_asymmetric
from asymmetric_parallel import run_parallel_asymmetric

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, 'data', 'asymmetric', 'split_depth')
CSV_PATH     = os.path.join(OUTPUT_DIR, 'empirical_python.csv')

# Variable split_depth experiment — asymmetric tree, Python
# Fixed: left_ratio=0.67, right_ratio=0.57, min_length=0.01, cores=8
#
# split_depth varies: 1 to 12
# Each depth is run NUM_RUNS times; mean is reported.
#
# Purpose: find the empirically optimal split_depth for Python multiprocessing.
# Hypothesis: deeper splits increase pickle/IPC overhead and worsen performance
# even though T_worst analysis predicts improvement at depth ~11.

NUM_PROCESSES = 8
NUM_RUNS      = 3
TRUNK_LENGTH  = 100.0
LEFT_RATIO    = 0.67
RIGHT_RATIO   = 0.57
LEFT_ANGLE    = 35.0
RIGHT_ANGLE   = 25.0
MIN_LENGTH    = 0.01
SPLIT_DEPTHS  = list(range(1, 13))


def _time_sequential():
    left_rad  = math.radians(LEFT_ANGLE)
    right_rad = math.radians(RIGHT_ANGLE)
    t0 = time.perf_counter()
    branches = generate_fractal_tree_asymmetric(
        0, 0, TRUNK_LENGTH, math.pi / 2,
        LEFT_RATIO, RIGHT_RATIO, left_rad, right_rad, MIN_LENGTH,
    )
    return time.perf_counter() - t0, len(branches)


def _time_parallel(split_depth):
    with contextlib.redirect_stdout(io.StringIO()):
        result = run_parallel_asymmetric(
            trunk_length=TRUNK_LENGTH,
            left_ratio=LEFT_RATIO,
            right_ratio=RIGHT_RATIO,
            left_angle=LEFT_ANGLE,
            right_angle=RIGHT_ANGLE,
            min_length=MIN_LENGTH,
            num_processes=NUM_PROCESSES,
            split_depth=split_depth,
        )
    return result['execution_time']


if __name__ == '__main__':
    seq_time, branch_count = _time_sequential()
    num_tasks_at = lambda d: 2 ** d

    print(f"\n=== Variable split_depth (asymmetric, Python) | cores={NUM_PROCESSES}, "
          f"left_ratio={LEFT_RATIO}, right_ratio={RIGHT_RATIO}, min_length={MIN_LENGTH} ===")
    print(f"  Sequential baseline: {seq_time:.5f}s  ({branch_count:,} branches)")
    print()
    print(f"{'depth':>6} {'tasks':>7} {'par_mean (s)':>13} {'speedup':>9} {'efficiency':>12}  note")
    print("-" * 65)

    rows = []
    current_heuristic = max(1, math.ceil(math.log2(NUM_PROCESSES * 4)))

    for depth in SPLIT_DEPTHS:
        times = [_time_parallel(depth) for _ in range(NUM_RUNS)]
        par_mean  = sum(times) / NUM_RUNS
        speedup   = seq_time / par_mean
        efficiency = speedup / NUM_PROCESSES
        note = "<-- heuristic" if depth == current_heuristic else ""

        print(f"{depth:>6} {num_tasks_at(depth):>7,} {par_mean:>13.5f} {speedup:>8.3f}x {efficiency:>11.1%}  {note}")
        rows.append({
            'split_depth': depth,
            'num_tasks':   num_tasks_at(depth),
            'branches':    branch_count,
            'seq_time':    f'{seq_time:.6f}',
            'par_mean':    f'{par_mean:.6f}',
            'speedup':     f'{speedup:.4f}',
            'efficiency':  f'{efficiency:.4f}',
        })

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'split_depth', 'num_tasks', 'branches', 'seq_time', 'par_mean', 'speedup', 'efficiency'
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved: {CSV_PATH}")
