import math
import time
import contextlib
import io
import csv
import os

from sequential import generate_fractal_tree
from parallel import run_parallel

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, 'data', 'experiments')
CSV_PATH     = os.path.join(OUTPUT_DIR, 'python_symmetric_variable_min_length.csv')

# Phase 3 — variable min_length (controls tree depth / problem size)
# Fixed: ratio=0.67, angle=30°, cores=4
# Question: how does problem size affect parallelization efficiency?

NUM_PROCESSES = 4
TRUNK_LENGTH  = 100.0
RATIO         = 0.67
ANGLE         = 30.0
VALUES        = [0.2, 0.1, 0.05, 0.01]

def _time_sequential(min_length):
    angle_rad = math.radians(ANGLE)
    t0 = time.perf_counter()
    branches = generate_fractal_tree(0, 0, TRUNK_LENGTH, math.pi / 2, RATIO, angle_rad, min_length)
    return time.perf_counter() - t0, len(branches)

def _time_parallel(min_length):
    with contextlib.redirect_stdout(io.StringIO()):
        result = run_parallel(
            trunk_length=TRUNK_LENGTH,
            ratio=RATIO,
            branch_angle=ANGLE,
            min_length=min_length,
            num_processes=NUM_PROCESSES,
        )
    return result['execution_time']

if __name__ == '__main__':
    print(f"\n=== Variable min_length | ratio={RATIO}, angle={ANGLE}°, cores={NUM_PROCESSES} ===")
    print(f"{'min_length':>12} {'branches':>12} {'seq (s)':>10} {'par (s)':>10} {'speedup':>9} {'efficiency':>12}")
    print("-" * 70)

    rows = []
    for val in VALUES:
        seq_time, branch_count = _time_sequential(val)
        par_time               = _time_parallel(val)
        speedup                = seq_time / par_time
        efficiency             = speedup / NUM_PROCESSES

        print(f"{val:>12} {branch_count:>12,} {seq_time:>10.5f} {par_time:>10.5f} {speedup:>8.3f}x {efficiency:>11.1%}")
        rows.append({'min_length': val, 'branches': branch_count,
                     'seq_time': f'{seq_time:.6f}', 'par_time': f'{par_time:.6f}',
                     'speedup': f'{speedup:.4f}', 'efficiency': f'{efficiency:.4f}'})

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['min_length', 'branches', 'seq_time', 'par_time', 'speedup', 'efficiency'])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved: {CSV_PATH}")
