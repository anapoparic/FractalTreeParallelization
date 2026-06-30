"""
Split-depth sensitivity plot
============================
Reads empirical_python.csv and empirical_rust.csv from
data/asymmetric/split_depth/ and produces a single PNG comparing
speedup vs split_depth for Python and Rust at N=8.

Output: zavrsni-rad/slike/split-depth-asym.png

Usage: python scripts/plot_split_depth.py
"""
import os
import csv

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPTS_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, '..'))
DATA_DIR     = os.path.join(PROJECT_ROOT, 'data', 'asymmetric', 'split_depth')
SLIKE_DIR    = os.path.abspath(os.path.join(PROJECT_ROOT, '..', 'zavrsni-rad', 'slike'))
OUT_PATH     = os.path.join(SLIKE_DIR, 'split-depth-asym.png')

HEURISTIC_D  = 5   # floor(log2(8 * 4)) for N=8


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def read_csv(path):
    depths, speedups = [], []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            depths.append(int(row['split_depth']))
            speedups.append(float(row['speedup']))
    return depths, speedups


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
def main():
    py_d, py_s = read_csv(os.path.join(DATA_DIR, 'empirical_python.csv'))
    rs_d, rs_s = read_csv(os.path.join(DATA_DIR, 'empirical_rust.csv'))

    rust_max_s = max(rs_s)
    rust_max_d = rs_d[rs_s.index(rust_max_s)]
    rust_heur_s = rs_s[rs_d.index(HEURISTIC_D)]

    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(10, 7))

    # --- curves ---
    ax.plot(rs_d, rs_s, 'o-',  color='#2E7D32', linewidth=2.5, markersize=8,
            label='Rust',   zorder=4)
    ax.plot(py_d, py_s, 's--', color='#6A1B9A', linewidth=2.5, markersize=8,
            label='Python', zorder=4)

    # --- heuristic vertical line ---
    ax.axvline(x=HEURISTIC_D, color='#E65100', linewidth=2, linestyle=':',
               label=f'Heuristic  d = {HEURISTIC_D}', zorder=3)

    # --- annotate Rust maximum ---
    ax.annotate(
        f'd = {rust_max_d},  S = {rust_max_s:.2f}×',
        xy=(rust_max_d, rust_max_s),
        xytext=(rust_max_d, rust_max_s - 1.4),
        color='#2E7D32', fontsize=12, fontweight='bold',
        ha='center',
        arrowprops=dict(arrowstyle='->', color='#2E7D32', lw=1.5),
    )

    # --- annotate heuristic Rust value ---
    ax.annotate(
        f'Heuristic:  S = {rust_heur_s:.2f}×',
        xy=(HEURISTIC_D, rust_heur_s),
        xytext=(HEURISTIC_D - 3.8, rust_heur_s + 0.4),
        color='#E65100', fontsize=12, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='#E65100', lw=1.5),
    )

    # --- axes & labels ---
    ax.set_xlabel('split_depth  (d)', fontsize=14)
    ax.set_ylabel('Speedup  S', fontsize=14)
    ax.set_title(
        'Effect of split_depth on speedup — asymmetric tree  (N = 8)',
        fontsize=15,
    )
    ax.tick_params(axis='both', labelsize=12)
    ax.set_xticks(rs_d)
    ax.set_xlim(0.5, max(rs_d) + 0.5)
    ax.set_ylim(0, rust_max_s + 0.9)
    ax.legend(loc='lower right', fontsize=12)
    ax.grid(True, alpha=0.3)

    # --- save ---
    os.makedirs(SLIKE_DIR, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {OUT_PATH}")


if __name__ == '__main__':
    main()
