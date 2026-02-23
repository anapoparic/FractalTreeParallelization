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
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'experiments')
GRAPH_DIR = os.path.join(PROJECT_ROOT, 'data', 'experiments', 'graphs')

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
def amdahl_speedup(N, f):
    """Amdahl's Law: S(N) = 1 / (f + (1-f)/N)."""
    return 1.0 / (f + (1.0 - f) / N)


def gustafson_speedup(N, f):
    """Gustafson's Law: S(N) = N - f*(N-1)."""
    return N - f * (N - 1)


def estimate_f_strong(stats):
    """Estimate sequential fraction f from strong scaling data.

    Uses the highest core-count result:
        S = T(1)/T(N)
        f = (1/S - 1/N) / (1 - 1/N)
    """
    t1 = stats[0]['mean']
    best = max(stats[1:], key=lambda s: s['cores']) if len(stats) > 1 else stats[0]
    S = t1 / best['mean']
    N = best['cores']
    if N <= 1:
        return 0.0
    f = (1.0 / S - 1.0 / N) / (1.0 - 1.0 / N)
    return max(0.0, min(1.0, f))


def estimate_f_weak(stats):
    """Estimate sequential fraction f from weak scaling data.

    Scaled speedup S_s = N * T(1) / T(N)
    Gustafson: S_s = N - f*(N-1)
    => f = (N - S_s) / (N - 1)
    """
    t1 = stats[0]['mean']
    best = max(stats[1:], key=lambda s: s['cores']) if len(stats) > 1 else stats[0]
    N = best['cores']
    if N <= 1:
        return 0.0
    S_scaled = N * t1 / best['mean']
    f = (N - S_scaled) / (N - 1)
    return max(0.0, min(1.0, f))


# ---------------------------------------------------------------------------
# Graph: Strong Scaling
# ---------------------------------------------------------------------------
def plot_strong_scaling(stats, f, language, output_path):
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
    ax.plot(x_smooth, x_smooth, '--', color='#FFA500', linewidth=2,
            label='Ideal (S = N)', alpha=0.8)

    # Amdahl's theoretical curve
    amdahl_y = [amdahl_speedup(x, f) for x in x_smooth]
    ax.plot(x_smooth, amdahl_y, '-', color='#FFD700', linewidth=1.5,
            label=f'Amdahl\'s Law (f = {f:.4f})', alpha=0.9)

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
def plot_weak_scaling(stats, f, language, output_path):
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
    ax.plot(x_smooth, x_smooth, '--', color='#FFA500', linewidth=2,
            label='Ideal (S = N)', alpha=0.8)

    # Gustafson's theoretical curve
    gustafson_y = [gustafson_speedup(x, f) for x in x_smooth]
    ax.plot(x_smooth, gustafson_y, '-', color='#FFD700', linewidth=1.5,
            label=f'Gustafson\'s Law (f = {f:.4f})', alpha=0.9)

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
def print_strong_table(stats, f, language):
    """Print strong scaling table with statistics."""
    t1 = stats[0]['mean']
    num_runs = stats[0]['num_runs']

    print(f"\n  {'=' * 78}")
    print(f"  Strong Scaling — {language}  ({num_runs} runs per config)")
    print(f"  {'=' * 78}")
    print(f"  Sequential fraction (f) = {f:.4f} ({f * 100:.2f}%)")
    print(f"  Parallelizable fraction  = {1 - f:.4f} ({(1 - f) * 100:.2f}%)")
    if f > 0:
        print(f"  Amdahl's max speedup (inf cores) = {1 / f:.2f}")
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
        amdahl = amdahl_speedup(s['cores'], f)
        print(f"  {s['cores']:5d} | {s['nodes']:15,} | {s['mean']:9.3f}s | "
              f"{s['stdev']:7.3f}s | {speedup:8.3f} | {amdahl:8.3f} | "
              f"{s['outlier_count']:8d}")

    return t1


def print_weak_table(stats, f, language):
    """Print weak scaling table with statistics."""
    t1 = stats[0]['mean']
    num_runs = stats[0]['num_runs']

    print(f"\n  {'=' * 84}")
    print(f"  Weak Scaling — {language}  ({num_runs} runs per config)")
    print(f"  {'=' * 84}")
    print(f"  Sequential fraction (f) = {f:.4f} ({f * 100:.2f}%)")
    print(f"  Gustafson's Law: S(N) = N - f*(N-1)")
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
        gustafson = gustafson_speedup(s['cores'], f)
        print(f"  {s['cores']:5d} | {s['nodes']:15,} | {s['mean']:9.3f}s | "
              f"{s['stdev']:7.3f}s | {scaled_s:8.3f} | {gustafson:9.3f} | "
              f"{s['outlier_count']:8d}")


def save_table_csv(stats, scaling_type, t1_mean, f, language, output_path):
    """Save detailed table to CSV for report inclusion."""
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if scaling_type == 'strong':
            writer.writerow(['cores', 'nodes', 'mean_time', 'stdev',
                             'speedup', 'amdahl_speedup', 'outliers', 'num_runs'])
            for s in stats:
                speedup = t1_mean / s['mean']
                amdahl = amdahl_speedup(s['cores'], f)
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
                gustafson = gustafson_speedup(s['cores'], f)
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
def process_experiment(language, scaling_type):
    """Process a single experiment (read CSV, compute stats, generate output)."""
    lang_lower = language.lower()
    csv_path = os.path.join(DATA_DIR, f'{lang_lower}_{scaling_type}.csv')

    if not os.path.exists(csv_path):
        print(f"\n  SKIP: {csv_path} not found")
        return False

    data, nodes = read_csv(csv_path)
    stats = compute_stats(data, nodes)

    if scaling_type == 'strong':
        f = estimate_f_strong(stats)
        t1 = print_strong_table(stats, f, language)
        plot_strong_scaling(stats, f, language,
                            os.path.join(GRAPH_DIR, f'strong_scaling_{lang_lower}.png'))
        save_table_csv(stats, 'strong', t1, f, language,
                       os.path.join(GRAPH_DIR, f'strong_scaling_{lang_lower}.csv'))
    else:
        f = estimate_f_weak(stats)
        print_weak_table(stats, f, language)
        t1 = stats[0]['mean']
        plot_weak_scaling(stats, f, language,
                          os.path.join(GRAPH_DIR, f'weak_scaling_{lang_lower}.png'))
        save_table_csv(stats, 'weak', t1, f, language,
                       os.path.join(GRAPH_DIR, f'weak_scaling_{lang_lower}.csv'))
    return True


def main():
    os.makedirs(GRAPH_DIR, exist_ok=True)

    print("=" * 70)
    print("  SCALING EXPERIMENT REPORT GENERATOR")
    print("=" * 70)

    print_system_info()

    found_any = False
    for language in ['Python', 'Rust']:
        for scaling in ['strong', 'weak']:
            if process_experiment(language, scaling):
                found_any = True

    if not found_any:
        print(f"\n  No experiment data found in: {DATA_DIR}")
        print(f"  Run experiments first:  python scripts/run_all.py")
        return

    print(f"\n  {'=' * 70}")
    print(f"  DONE")
    print(f"  Graphs and tables saved to: {GRAPH_DIR}")
    print(f"  {'=' * 70}")


if __name__ == '__main__':
    main()
