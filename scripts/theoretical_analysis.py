"""
Optimal Split Depth Analysis
==============================
Uses analytical branch counting to find the theoretically optimal split_depth
for both symmetric and asymmetric fractal trees.

The parallel implementation splits the tree at a fixed depth before dispatching
subtasks to the Pool:
    current heuristic: split_depth = max(1, ceil(log2(num_processes * 4)))

This script asks: is that the best split depth, given the actual tree structure?

For each candidate split_depth d, it computes:
  - N_seq          : branches computed sequentially (2^d - 1)
  - Subtask sizes  : analytically, per subtask (all equal for symmetric,
                     varies for asymmetric because r_left != r_right)
  - Load imbalance : max_task / mean_task  (1.0 = perfect balance)
  - T_ideal        : N_seq + ceil(N_parallel / N)   [best case, perfect balance]
  - T_worst        : N_seq + max_task               [worst case, one slow worker]

The optimal split_depth minimises T_ideal (or T_worst).

Usage: python scripts/theoretical_analysis.py
"""
import math
import os
import csv
from math import comb, log, floor, ceil, log2

# ---------------------------------------------------------------------------
# Paths & parameters
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR     = os.path.join(PROJECT_ROOT, 'data')

TRUNK_LENGTH = 100.0
MIN_LENGTH   = 0.01
CORE_COUNTS  = [1, 2, 4, 8]
MAX_SPLIT    = 12   # maximum split depth to evaluate

SYM_RATIO    = 0.67
ASYM_L_RATIO = 0.67
ASYM_R_RATIO = 0.57


# ---------------------------------------------------------------------------
# Analytical branch counting
# ---------------------------------------------------------------------------
def count_branches_symmetric(L, ratio, min_length):
    """Total branches in a symmetric tree (closed form)."""
    if L < min_length:
        return 0
    d_max = floor(log(min_length / L) / log(ratio))
    return 2 ** (d_max + 1) - 1


def count_branches_asymmetric(L, r_left, r_right, min_length):
    """Total branches in an asymmetric tree (analytical double sum)."""
    if L < min_length:
        return 0
    d_left  = floor(log(min_length / L) / log(r_left))
    d_right = floor(log(min_length / L) / log(r_right))
    total = 0
    for k in range(d_left + 1):
        for m in range(d_right + 1):
            if L * (r_left ** k) * (r_right ** m) >= min_length:
                total += comb(k + m, k)
    return total


# ---------------------------------------------------------------------------
# Subtask analysis at a given split depth
# ---------------------------------------------------------------------------
def subtasks_symmetric(L, ratio, min_length, split_depth):
    """
    Returns list of subtask sizes at the given split depth.
    All subtasks start at length L * ratio^split_depth → all equal.
    """
    start_len = L * (ratio ** split_depth)
    if start_len < min_length:
        return []
    size = count_branches_symmetric(start_len, ratio, min_length)
    count = 2 ** split_depth
    return [size] * count


def subtasks_asymmetric(L, r_left, r_right, min_length, split_depth):
    """
    Returns list of subtask sizes at the given split depth.
    A subtask with k left-turns and m right-turns (k+m=split_depth) starts at
    length L * r_left^k * r_right^m.  There are C(d,k) such subtasks.
    Sizes differ because r_left != r_right → load imbalance.
    """
    d = split_depth
    sizes = []
    for k in range(d + 1):
        m = d - k
        start_len = L * (r_left ** k) * (r_right ** m)
        if start_len < min_length:
            continue
        size = count_branches_asymmetric(start_len, r_left, r_right, min_length)
        count = comb(d, k)   # number of paths with exactly k lefts and m rights
        sizes.extend([size] * count)
    return sizes


# ---------------------------------------------------------------------------
# Timing model
# ---------------------------------------------------------------------------
def analyse_split_depth(split_depth, subtask_sizes, n_processes):
    """
    Given a list of subtask sizes and a process count, compute the theoretical
    execution cost (in units of 'branches computed').

    T_ideal : N_seq + ceil(N_parallel / N)   — perfect load balance
    T_worst : N_seq + max_task               — one worker gets the biggest task
    """
    n_seq = 2 ** split_depth - 1

    if not subtask_sizes:
        return None

    n_par      = sum(subtask_sizes)
    max_task   = max(subtask_sizes)
    mean_task  = n_par / len(subtask_sizes)
    imbalance  = max_task / mean_task if mean_task > 0 else 1.0
    num_tasks  = len(subtask_sizes)

    t_ideal = n_seq + math.ceil(n_par / n_processes)
    t_worst = n_seq + max_task

    return {
        'split_depth' : split_depth,
        'n_seq'       : n_seq,
        'num_tasks'   : num_tasks,
        'n_parallel'  : n_par,
        'max_task'    : max_task,
        'mean_task'   : mean_task,
        'imbalance'   : imbalance,
        't_ideal'     : t_ideal,
        't_worst'     : t_worst,
    }


def current_split_depth(n_processes):
    return max(1, ceil(log2(n_processes * 4)))


# ---------------------------------------------------------------------------
# Print & save helpers
# ---------------------------------------------------------------------------
def print_table(rows, optimal_ideal, optimal_worst, current_d):
    hdr = (f"  {'d':>3} | {'N_seq':>8} | {'tasks':>6} | {'N_par':>12} | "
           f"{'max_task':>10} | {'imbalance':>9} | {'T_ideal':>12} | {'T_worst':>12} | {'note':>12}")
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    for r in rows:
        note = []
        if r['split_depth'] == optimal_ideal: note.append('OPT_IDEAL')
        if r['split_depth'] == optimal_worst: note.append('OPT_WORST')
        if r['split_depth'] == current_d:     note.append('CURRENT')
        print(f"  {r['split_depth']:>3} | {r['n_seq']:>8,} | {r['num_tasks']:>6,} | "
              f"{r['n_parallel']:>12,} | {r['max_task']:>10,} | "
              f"{r['imbalance']:>9.3f} | {r['t_ideal']:>12,} | {r['t_worst']:>12,} | "
              f"{'  '.join(note)}")


def save_csv(rows, tree, n_processes):
    out_dir = os.path.join(DATA_DIR, tree, 'split_depth')
    os.makedirs(out_dir, exist_ok=True)
    filename = f'theoretical_{n_processes}.csv'
    path = os.path.join(out_dir, filename)
    fields = ['split_depth','n_seq','num_tasks','n_parallel',
              'max_task','mean_task','imbalance','t_ideal','t_worst']
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Main analysis per tree type
# ---------------------------------------------------------------------------
def analyse_tree(tree, branches_total, subtask_fn):
    print(f"\n{'=' * 80}")
    print(f"  {tree.upper()} TREE  —  N_total = {branches_total:,}")
    print(f"{'=' * 80}")

    for N in CORE_COUNTS:
        current_d = current_split_depth(N)
        print(f"\n  -- {N} core(s)  |  current split_depth = {current_d} "
              f"(heuristic: max(1, ceil(log2({N}*4)))) --\n")

        rows = []
        for d in range(1, MAX_SPLIT + 1):
            sizes = subtask_fn(d)
            if not sizes:
                break
            r = analyse_split_depth(d, sizes, N)
            if r:
                rows.append(r)

        if not rows:
            print("  No valid split depths found.")
            continue

        optimal_ideal = min(rows, key=lambda r: r['t_ideal'])['split_depth']
        optimal_worst = min(rows, key=lambda r: r['t_worst'])['split_depth']

        print_table(rows, optimal_ideal, optimal_worst, current_d)

        # Gain of optimal over current
        current_row  = next((r for r in rows if r['split_depth'] == current_d), None)
        optimal_row  = next((r for r in rows if r['split_depth'] == optimal_ideal), None)
        if current_row and optimal_row:
            gain = (current_row['t_ideal'] - optimal_row['t_ideal']) / current_row['t_ideal'] * 100
            print(f"\n  Theoretical gain of OPT_IDEAL over CURRENT: {gain:+.2f}%")
            if optimal_ideal < current_d:
                print(f"  -> current split_depth is TOO DEEP "
                      f"(wastes {current_row['n_seq'] - optimal_row['n_seq']:,} extra sequential branches)")
            elif optimal_ideal > current_d:
                print(f"  -> current split_depth is TOO SHALLOW "
                      f"(not enough tasks for good load balance)")
            else:
                print(f"  -> current split_depth is already optimal")

        save_csv(rows, tree.lower().replace(' ', '_'), N)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    n_sym  = count_branches_symmetric(TRUNK_LENGTH, SYM_RATIO, MIN_LENGTH)
    n_asym = count_branches_asymmetric(TRUNK_LENGTH, ASYM_L_RATIO, ASYM_R_RATIO, MIN_LENGTH)

    print("=" * 80)
    print("  OPTIMAL SPLIT DEPTH ANALYSIS")
    print("=" * 80)
    print(f"\n  Parameters:")
    print(f"    Trunk length      : {TRUNK_LENGTH}")
    print(f"    min_length        : {MIN_LENGTH}")
    print(f"    Symmetric  ratio  : {SYM_RATIO}   →  N_total = {n_sym:,}")
    print(f"    Asymmetric ratios : L={ASYM_L_RATIO} / R={ASYM_R_RATIO}  →  N_total = {n_asym:,}")
    print(f"\n  Model: T = N_seq + ceil(N_parallel / N_cores)  [ideal, units = branches]")
    print(f"         T = N_seq + max_task                    [worst case]")

    sym_subtasks  = lambda d: subtasks_symmetric( TRUNK_LENGTH, SYM_RATIO, MIN_LENGTH, d)
    asym_subtasks = lambda d: subtasks_asymmetric(TRUNK_LENGTH, ASYM_L_RATIO, ASYM_R_RATIO, MIN_LENGTH, d)

    analyse_tree('Symmetric',  n_sym,  sym_subtasks)
    analyse_tree('Asymmetric', n_asym, asym_subtasks)


if __name__ == '__main__':
    main()
