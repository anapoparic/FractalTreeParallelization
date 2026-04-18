"""
Graph and Table Generator
=========================
Reads experiment CSV data and generates:
- 4 scaling graphs (PNG) matching the style from report.jpg
- Supporting tables with mean, stdev, outliers
- Amdahl's / Gustafson's Law analysis

Usage: python generate_graphs.py

Requires: matplotlib, numpy (pip install matplotlib)
"""
import os
import sys
import csv
import math
import platform
import statistics

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for saving files
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import numpy as np
except ImportError:
    print("ERROR: matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

CORE_COUNTS = [1, 2, 4, 8]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def read_csv(filepath):
    """Read experiment CSV. Returns {cores: [times]}, {cores: node_count}."""
    data = {}
    nodes = {}
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cores = int(row['cores'])
            t = float(row['time'])
            n = int(row['branches'])
            data.setdefault(cores, []).append(t)
            nodes[cores] = n
    return data, nodes


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
def calculate_outliers(times):
    """Identify outliers using IQR method."""
    sorted_t = sorted(times)
    n = len(sorted_t)
    if n < 4:
        return []
    q1 = sorted_t[n // 4]
    q3 = sorted_t[3 * n // 4]
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return [t for t in times if t < lower or t > upper]


def compute_stats(data, nodes):
    """Compute statistics for each core count."""
    stats = []
    for cores in sorted(data.keys()):
        times = data[cores]
        mean = statistics.mean(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0.0
        outliers = calculate_outliers(times)
        stats.append({
            'cores': cores,
            'nodes': nodes[cores],
            'mean': mean,
            'stdev': stdev,
            'min': min(times),
            'max': max(times),
            'outlier_count': len(outliers),
            'num_runs': len(times),
        })
    return stats


# ---------------------------------------------------------------------------
# Amdahl's and Gustafson's Laws
# ---------------------------------------------------------------------------
def amdahl_speedup(N, p):
    """Amdahl's Law: S(N) = 1 / ((1-p) + p/N), p = parallel fraction."""
    return 1.0 / ((1.0 - p) + p / N)


def gustafson_speedup(N, p):
    """Gustafson's Law: S(N) = N - (1-p)*(N-1), p = parallel fraction."""
    return N - (1.0 - p) * (N - 1)


def estimate_p_strong(stats):
    """Estimate parallel fraction p from strong scaling data.

    For each N > 1:
        S = T(1)/T(N)
        p = (1 - 1/S) / (1 - 1/N)
    Returns average p across all core counts.
    """
    t1 = stats[0]['mean']
    p_estimates = []
    for s in stats[1:]:
        N = s['cores']
        S = t1 / s['mean']
        p_i = (1.0 - 1.0 / S) / (1.0 - 1.0 / N)
        p_estimates.append(max(0.0, min(1.0, p_i)))
    if not p_estimates:
        return 1.0
    return sum(p_estimates) / len(p_estimates)


def estimate_p_weak(stats):
    """Estimate parallel fraction p from weak scaling data.

    Scaled speedup S_s = N * T(1) / T(N)
    Gustafson: S_s = 1 + p*(N-1)
    => p = (S_s - 1) / (N - 1)
    Returns average p across all core counts.
    """
    t1 = stats[0]['mean']
    p_estimates = []
    for s in stats[1:]:
        N = s['cores']
        S_scaled = N * t1 / s['mean']
        p_i = (S_scaled - 1.0) / (N - 1.0)
        p_estimates.append(max(0.0, min(1.0, p_i)))
    if not p_estimates:
        return 1.0
    return sum(p_estimates) / len(p_estimates)


# ---------------------------------------------------------------------------
# Graph: Strong Scaling
# ---------------------------------------------------------------------------
def plot_strong_scaling(stats, p, language, output_path):
    """Generate strong scaling graph (Amdahl's Law)."""
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 7))

    t1 = stats[0]['mean']
    cores = [s['cores'] for s in stats]
    speedups = [t1 / s['mean'] for s in stats]
    times = [s['mean'] for s in stats]

    max_c = max(cores)
    x_smooth = np.linspace(1, max_c, 200)

    # Ideal line: S = N
    ax.plot(x_smooth, x_smooth, '--', color='#00C853', linewidth=2,
            label='Ideal (S = N)', alpha=0.8)

    # Amdahl's theoretical curve
    amdahl_y = [amdahl_speedup(x, p) for x in x_smooth]
    ax.plot(x_smooth, amdahl_y, '-', color='#AA00FF', linewidth=1.5,
            label=f'Amdahl\'s Law (p = {p:.4f})', alpha=0.9)

    # Measured data points
    ax.plot(cores, speedups, 'o-', color='white', markersize=10,
            linewidth=2, label='Measured', zorder=5)

    # Time labels on each point
    for c, s, t in zip(cores, speedups, times):
        ax.annotate(f'{t:.3f}s',
                    xy=(c, s),
                    xytext=(15, -5),
                    textcoords='offset points',
                    color='#CCCCCC', fontsize=10,
                    arrowprops=dict(arrowstyle='-', color='#666666', lw=0.5))

    ax.set_xlabel('Number of processors', fontsize=13)
    ax.set_ylabel('Speedup', fontsize=13)
    ax.set_title(f'Strong Scaling — {language} (Amdahl\'s Law)', fontsize=15)
    ax.set_xticks(cores)
    ax.set_xlim(0.5, max_c + 0.5)
    ax.set_ylim(0, max_c + 1)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"    Graph saved: {output_path}")


# ---------------------------------------------------------------------------
# Graph: Weak Scaling
# ---------------------------------------------------------------------------
def plot_weak_scaling(stats, p, language, output_path):
    """Generate weak scaling graph (Gustafson's Law)."""
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 7))

    t1 = stats[0]['mean']
    cores = [s['cores'] for s in stats]
    scaled_speedups = [s['cores'] * t1 / s['mean'] for s in stats]
    times = [s['mean'] for s in stats]

    max_c = max(cores)
    x_smooth = np.linspace(1, max_c, 200)

    # Ideal line: S = N
    ax.plot(x_smooth, x_smooth, '--', color='#00C853', linewidth=2,
            label='Ideal (S = N)', alpha=0.8)

    # Gustafson's theoretical curve
    gustafson_y = [gustafson_speedup(x, p) for x in x_smooth]
    ax.plot(x_smooth, gustafson_y, '-', color='#AA00FF', linewidth=1.5,
            label=f'Gustafson\'s Law (p = {p:.4f})', alpha=0.9)

    # Measured data points
    ax.plot(cores, scaled_speedups, 'o-', color='white', markersize=10,
            linewidth=2, label='Measured', zorder=5)

    # Time labels on each point
    for c, s, t in zip(cores, scaled_speedups, times):
        ax.annotate(f'{t:.3f}s',
                    xy=(c, s),
                    xytext=(15, -5),
                    textcoords='offset points',
                    color='#CCCCCC', fontsize=10,
                    arrowprops=dict(arrowstyle='-', color='#666666', lw=0.5))

    ax.set_xlabel('Number of processors', fontsize=13)
    ax.set_ylabel('Scaled Speedup', fontsize=13)
    ax.set_title(f'Weak Scaling — {language} (Gustafson\'s Law)', fontsize=15)
    ax.set_xticks(cores)
    ax.set_xlim(0.5, max_c + 0.5)
    ax.set_ylim(0, max_c + 1)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"    Graph saved: {output_path}")


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def print_strong_table(stats, p, language):
    """Print strong scaling table with statistics."""
    t1 = stats[0]['mean']
    num_runs = stats[0]['num_runs']

    print(f"\n  {'=' * 78}")
    print(f"  Strong Scaling — {language}  ({num_runs} runs per config)")
    print(f"  {'=' * 78}")
    print(f"  Parallel fraction (p)    = {p:.4f} ({p * 100:.2f}%)")
    print(f"  Sequential fraction      = {1 - p:.4f} ({(1 - p) * 100:.2f}%)")
    if p < 1.0:
        print(f"  Amdahl's max speedup (inf cores) = {1 / (1 - p):.2f}")
    else:
        print(f"  Amdahl's max speedup (inf cores) = inf (fully parallelizable)")
    print()

    hdr = (f"  {'Cores':>5} | {'Nodes':>15} | {'Mean':>10} | "
           f"{'Stdev':>8} | {'Speedup':>8} | {'Amdahl':>8} | {'Outliers':>8}")
    sep = (f"  {'-' * 5}-+-{'-' * 15}-+-{'-' * 10}-+-"
           f"{'-' * 8}-+-{'-' * 8}-+-{'-' * 8}-+-{'-' * 8}")
    print(hdr)
    print(sep)

    for s in stats:
        speedup = t1 / s['mean']
        amdahl = amdahl_speedup(s['cores'], p)
        print(f"  {s['cores']:5d} | {s['nodes']:15,} | {s['mean']:9.3f}s | "
              f"{s['stdev']:7.3f}s | {speedup:8.3f} | {amdahl:8.3f} | "
              f"{s['outlier_count']:8d}")

    return t1


def print_weak_table(stats, p, language):
    """Print weak scaling table with statistics."""
    t1 = stats[0]['mean']
    num_runs = stats[0]['num_runs']

    print(f"\n  {'=' * 84}")
    print(f"  Weak Scaling — {language}  ({num_runs} runs per config)")
    print(f"  {'=' * 84}")
    print(f"  Parallel fraction (p)    = {p:.4f} ({p * 100:.2f}%)")
    print(f"  Sequential fraction      = {1 - p:.4f} ({(1 - p) * 100:.2f}%)")
    print(f"  Gustafson's Law: S(N) = N - (1-p)*(N-1)")
    print(f"  Workload scaling: resize parameter increases with cores")
    print(f"    -> Higher resize = deeper tree = more nodes per core")
    print()

    hdr = (f"  {'Cores':>5} | {'Nodes':>15} | {'Mean':>10} | "
           f"{'Stdev':>8} | {'Scaled S':>8} | {'Gustafson':>9} | {'Outliers':>8}")
    sep = (f"  {'-' * 5}-+-{'-' * 15}-+-{'-' * 10}-+-"
           f"{'-' * 8}-+-{'-' * 8}-+-{'-' * 9}-+-{'-' * 8}")
    print(hdr)
    print(sep)

    for s in stats:
        scaled_s = s['cores'] * t1 / s['mean']
        gustafson = gustafson_speedup(s['cores'], p)
        print(f"  {s['cores']:5d} | {s['nodes']:15,} | {s['mean']:9.3f}s | "
              f"{s['stdev']:7.3f}s | {scaled_s:8.3f} | {gustafson:9.3f} | "
              f"{s['outlier_count']:8d}")


def save_table_csv(stats, scaling_type, t1_mean, p, language, output_path):
    """Save detailed table to CSV for report inclusion."""
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if scaling_type == 'strong':
            writer.writerow(['cores', 'nodes', 'mean_time', 'stdev',
                             'speedup', 'amdahl_speedup', 'outliers', 'num_runs'])
            for s in stats:
                speedup = t1_mean / s['mean']
                amdahl = amdahl_speedup(s['cores'], p)
                writer.writerow([
                    s['cores'], s['nodes'], f"{s['mean']:.6f}",
                    f"{s['stdev']:.6f}", f"{speedup:.4f}",
                    f"{amdahl:.4f}", s['outlier_count'], s['num_runs']
                ])
        else:  # weak
            writer.writerow(['cores', 'nodes', 'mean_time', 'stdev',
                             'scaled_speedup', 'gustafson_speedup', 'outliers', 'num_runs'])
            for s in stats:
                scaled_s = s['cores'] * t1_mean / s['mean']
                gustafson = gustafson_speedup(s['cores'], p)
                writer.writerow([
                    s['cores'], s['nodes'], f"{s['mean']:.6f}",
                    f"{s['stdev']:.6f}", f"{scaled_s:.4f}",
                    f"{gustafson:.4f}", s['outlier_count'], s['num_runs']
                ])

    print(f"    Table saved: {output_path}")


# ---------------------------------------------------------------------------
# System info
# ---------------------------------------------------------------------------
def print_system_info():
    """Print hardware/software environment details."""
    print(f"\n  {'=' * 60}")
    print(f"  SYSTEM INFORMATION")
    print(f"  {'=' * 60}")
    print(f"  OS:         {platform.system()} {platform.release()} ({platform.version()})")
    print(f"  Machine:    {platform.machine()}")
    print(f"  Processor:  {platform.processor()}")
    print(f"  CPU cores:  {os.cpu_count()} logical")
    print(f"  Python:     {platform.python_version()}")

    # Try to get Rust version
    try:
        import subprocess
        result = subprocess.run(['rustc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  Rust:       {result.stdout.strip()}")
    except FileNotFoundError:
        print(f"  Rust:       not found")

    # Try to get matplotlib version
    print(f"  matplotlib: {matplotlib.__version__}")
    print(f"  numpy:      {np.__version__}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def process_experiment(language, scaling_type, tree='symmetric'):
    """Process a single experiment (read CSV, compute stats, generate output)."""
    lang_lower = language.lower()
    csv_path = os.path.join(DATA_DIR, tree, scaling_type, f'{lang_lower}.csv')
    graph_dir = os.path.join(DATA_DIR, tree, scaling_type)

    if not os.path.exists(csv_path):
        print(f"\n  SKIP: {csv_path} not found")
        return False

    data, nodes = read_csv(csv_path)
    stats = compute_stats(data, nodes)

    label = f'{language} ({tree})'

    if scaling_type == 'strong':
        p = estimate_p_strong(stats)
        t1 = print_strong_table(stats, p, label)
        plot_strong_scaling(stats, p, label,
                            os.path.join(graph_dir, f'{lang_lower}.png'))
        save_table_csv(stats, 'strong', t1, p, label,
                       os.path.join(graph_dir, f'{lang_lower}_stats.csv'))
    else:
        p = estimate_p_weak(stats)
        print_weak_table(stats, p, label)
        t1 = stats[0]['mean']
        plot_weak_scaling(stats, p, label,
                          os.path.join(graph_dir, f'{lang_lower}.png'))
        save_table_csv(stats, 'weak', t1, p, label,
                       os.path.join(graph_dir, f'{lang_lower}_stats.csv'))
    return True


def main():

    print("=" * 70)
    print("  SCALING EXPERIMENT REPORT GENERATOR")
    print("=" * 70)

    print_system_info()

    found_any = False
    for tree in ['symmetric', 'asymmetric']:
        for language in ['Python', 'Rust']:
            for scaling in ['strong', 'weak']:
                if process_experiment(language, scaling, tree):
                    found_any = True

    if not found_any:
        print(f"\n  No experiment data found in: {DATA_DIR}")
        print(f"  Run experiments first:  python scripts/run_all.py")
        return

    print(f"\n  {'=' * 70}")
    print(f"  DONE")
    print(f"  Graphs and tables saved to: {DATA_DIR}")
    print(f"  {'=' * 70}")


if __name__ == '__main__':
    main()
