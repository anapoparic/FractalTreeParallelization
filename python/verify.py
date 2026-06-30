"""
Verifies that the parallel implementations produce the same set of branches
as the sequential implementations (after lexicographic sort by coordinates).
"""
import math
import sys
import numpy as np
from multiprocessing import Pool, freeze_support

from symmetric_sequential import generate_fractal_tree
from symmetric_parallel import _worker, _build_tasks
from asymmetric_sequential import generate_fractal_tree_asymmetric
from asymmetric_parallel import _worker as _worker_asym, _build_tasks as _build_tasks_asym


def _parallel_sym(trunk_length, ratio, branch_angle, min_length, num_processes):
    branch_angle_rad = math.radians(branch_angle)
    split_depth = max(1, math.ceil(math.log2(num_processes * 4)))
    start_angle = math.pi / 2
    end_x = trunk_length * math.cos(start_angle)
    end_y = trunk_length * math.sin(start_angle)

    upper = [(0.0, 0.0, end_x, end_y, 0)]
    new_len = trunk_length * ratio
    tasks  = _build_tasks(end_x, end_y, new_len, start_angle + branch_angle_rad,
                          ratio, branch_angle_rad, min_length, 1, split_depth, upper)
    tasks += _build_tasks(end_x, end_y, new_len, start_angle - branch_angle_rad,
                          ratio, branch_angle_rad, min_length, 1, split_depth, upper)
    with Pool(processes=num_processes) as pool:
        results = pool.map(_worker, tasks)
    return np.concatenate([np.array(upper, dtype=np.float64)] + results)


def _parallel_asym(trunk_length, left_ratio, right_ratio,
                   left_angle, right_angle, min_length, num_processes):
    left_rad  = math.radians(left_angle)
    right_rad = math.radians(right_angle)
    split_depth = max(1, math.ceil(math.log2(num_processes * 4)))
    start_angle = math.pi / 2
    end_x = trunk_length * math.cos(start_angle)
    end_y = trunk_length * math.sin(start_angle)

    upper = [(0.0, 0.0, end_x, end_y, 0)]
    tasks  = _build_tasks_asym(end_x, end_y, trunk_length * left_ratio,
                               start_angle + left_rad,
                               left_ratio, right_ratio, left_rad, right_rad,
                               min_length, 1, split_depth, upper)
    tasks += _build_tasks_asym(end_x, end_y, trunk_length * right_ratio,
                               start_angle - right_rad,
                               left_ratio, right_ratio, left_rad, right_rad,
                               min_length, 1, split_depth, upper)
    with Pool(processes=num_processes) as pool:
        results = pool.map(_worker_asym, tasks)
    return np.concatenate([np.array(upper, dtype=np.float64)] + results)


def _sort(branches):
    # Lexicographic sort: primary x1, then y1, x2, y2, depth
    idx = np.lexsort((branches[:, 4], branches[:, 3], branches[:, 2],
                      branches[:, 1], branches[:, 0]))
    return branches[idx]


def _check(name, seq, par):
    seq_s, par_s = _sort(seq), _sort(par)
    if seq_s.shape != par_s.shape:
        print(f"  FAIL  {name}  branch count: seq={len(seq_s)}, par={len(par_s)}")
        return False
    ok = np.allclose(seq_s, par_s, atol=1e-10, rtol=0)
    print(f"{'  OK  ' if ok else '  FAIL'}  {name}  ({len(seq_s)} branches)")
    return ok


def main():
    SYM  = dict(trunk_length=100.0, ratio=0.67, branch_angle=30.0, min_length=0.01)
    ASYM = dict(trunk_length=100.0, left_ratio=0.67, right_ratio=0.57,
                left_angle=35.0, right_angle=25.0, min_length=0.0023)

    print("=== Python correctness verification ===\n")
    all_ok = True

    seq_sym = generate_fractal_tree(
        0, 0, SYM['trunk_length'], math.pi / 2,
        SYM['ratio'], math.radians(SYM['branch_angle']), SYM['min_length'],
    )
    for n in [1, 2, 4, 8]:
        all_ok &= _check(f"symmetric   N={n}", seq_sym, _parallel_sym(**SYM, num_processes=n))

    seq_asym = generate_fractal_tree_asymmetric(
        0, 0, ASYM['trunk_length'], math.pi / 2,
        ASYM['left_ratio'], ASYM['right_ratio'],
        math.radians(ASYM['left_angle']), math.radians(ASYM['right_angle']),
        ASYM['min_length'],
    )
    for n in [1, 2, 4, 8]:
        all_ok &= _check(f"asymmetric  N={n}", seq_asym, _parallel_asym(**ASYM, num_processes=n))

    print()
    print("All checks passed." if all_ok else "One or more checks FAILED.")
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    freeze_support()
    main()
