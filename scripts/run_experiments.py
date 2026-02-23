"""
Experiment Runner
=================
Runs strong and weak scaling experiments for Python and Rust.
Each configuration is executed NUM_RUNS times and results saved to CSV.

Usage:
    python run_all.py                         # Run all (3 runs each)
    python run_all.py --runs 5                # Run with 5 runs each
    python run_all.py --lang python           # Only Python
    python run_all.py --lang rust             # Only Rust
    python run_all.py --scaling strong        # Only strong scaling
    python run_all.py --lang python --scaling strong --runs 3  # Specific config
"""
import subprocess
import os
import sys
import re
import csv
import time
import argparse

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PYTHON_EXP_DIR = os.path.join(PROJECT_ROOT, 'python', 'experiments')
RUST_DIR = os.path.join(PROJECT_ROOT, 'rust')
RUST_BIN_DIR = os.path.join(RUST_DIR, 'target', 'release')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'experiments')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CORE_COUNTS = [1, 2, 4, 8]
DEFAULT_RUNS = 3

# Parameters used in each experiment (trunk_length=100, ratio=0.67, branch_angle=30)
# Strong scaling: fixed problem size (min_length=0.01)
# Weak scaling: min_length = 0.5 * 0.67^log2(cores) — one level deeper per 2x cores
MIN_LENGTH_PARAMS = {
    'strong': {1: 0.01,  2: 0.01,  4: 0.01,  8: 0.01},
    'weak':   {1: 0.5,   2: 0.335, 4: 0.224, 8: 0.150},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def count_branches(length, ratio, min_length):
    """Count total branches in the fractal tree (matches Rust lib implementation)."""
    if length < min_length:
        return 0
    return 1 + 2 * count_branches(length * ratio, ratio, min_length)


def parse_time(output):
    """Parse 'Finish in X.XXXXX secounds(s)' from experiment output."""
    match = re.search(r'Finish in ([\d.]+) secounds', output)
    if match:
        return float(match.group(1))
    raise ValueError(f"Could not parse time from output:\n{output}")


def build_rust(verbose=True):
    """Build all Rust experiment binaries with cargo --release."""
    if verbose:
        print("\n  Building Rust experiments with cargo...")
    result = subprocess.run(
        ['cargo', 'build', '--release'],
        capture_output=True, text=True, cwd=RUST_DIR
    )
    if result.returncode != 0:
        raise RuntimeError(f"Rust build failed:\n{result.stderr}")
    if verbose:
        print("  Build done.")


def rust_bin_path(scaling, cores):
    """Return path to the compiled Rust experiment binary."""
    name = f'exp_{scaling}_{cores}'
    if sys.platform == 'win32':
        name += '.exe'
    return os.path.join(RUST_BIN_DIR, name)


def run_single(cmd, timeout=600):
    """Run a single experiment and return execution time."""
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(f"Experiment failed ({cmd}):\nstderr: {result.stderr}")
    return parse_time(result.stdout)


def format_duration(seconds):
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = int(minutes // 60)
    mins = minutes % 60
    return f"{hours}h {mins}m {secs}s"


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
def run_all_configs(language, scaling, num_runs):
    """Run all core-count configurations for a language and scaling type."""
    csv_path = os.path.join(OUTPUT_DIR, f'{language}_{scaling}.csv')
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    rows = []
    total_configs = len(CORE_COUNTS)
    total_runs_all = total_configs * num_runs
    completed = 0
    overall_start = time.time()

    for config_idx, cores in enumerate(CORE_COUNTS):
        min_length = MIN_LENGTH_PARAMS[scaling][cores]
        nodes = count_branches(100.0, 0.67, min_length)

        if language == 'python':
            script = os.path.join(PYTHON_EXP_DIR, scaling, f'{cores}.py')
            cmd = [sys.executable, script]
        else:
            cmd = [rust_bin_path(scaling, cores)]

        print(f"\n  [{config_idx+1}/{total_configs}] {cores} core(s) | "
              f"{nodes:,} branches | {num_runs} runs:")

        config_start = time.time()
        for run in range(1, num_runs + 1):
            try:
                t = run_single(cmd)
            except Exception as e:
                print(f"\n    Run {run} FAILED: {e}")
                continue

            rows.append({
                'cores': cores,
                'run': run,
                'time': f'{t:.6f}',
                'branches': nodes
            })
            completed += 1

            elapsed = time.time() - overall_start
            if completed > 0:
                eta = elapsed / completed * (total_runs_all - completed)
                eta_str = format_duration(eta)
            else:
                eta_str = "?"
            print(f"\r    Run {run}/{num_runs}: {t:.3f}s  "
                  f"[ETA: {eta_str}]", end='', flush=True)

        config_time = time.time() - config_start
        print(f"\n    Config done in {format_duration(config_time)}")

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['cores', 'run', 'time', 'branches'])
        writer.writeheader()
        writer.writerows(rows)

    total_time = time.time() - overall_start
    print(f"\n  Saved: {csv_path}")
    print(f"  Total time: {format_duration(total_time)}")
    return rows


def main():
    parser = argparse.ArgumentParser(description='Run scaling experiments')
    parser.add_argument('--runs', type=int, default=DEFAULT_RUNS,
                        help=f'Number of runs per config (default: {DEFAULT_RUNS})')
    parser.add_argument('--lang', choices=['python', 'rust', 'all'], default='all',
                        help='Language to test (default: all)')
    parser.add_argument('--scaling', choices=['strong', 'weak', 'all'], default='all',
                        help='Scaling type (default: all)')
    args = parser.parse_args()

    languages = ['python', 'rust'] if args.lang == 'all' else [args.lang]
    scalings = ['strong', 'weak'] if args.scaling == 'all' else [args.scaling]

    print("=" * 60)
    print("  EXPERIMENT RUNNER")
    print("=" * 60)
    print(f"  Runs per config: {args.runs}")
    print(f"  Languages: {', '.join(languages)}")
    print(f"  Scaling: {', '.join(scalings)}")
    print(f"  Total experiments: {len(languages) * len(scalings) * len(CORE_COUNTS) * args.runs}")

    # Build Rust binaries once if needed
    if 'rust' in languages:
        build_rust()

    global_start = time.time()

    for lang in languages:
        for scaling in scalings:
            print(f"\n{'=' * 60}")
            print(f"  {lang.upper()} - {scaling.upper()} SCALING")
            print(f"{'=' * 60}")
            run_all_configs(lang, scaling, args.runs)

    total = time.time() - global_start
    print(f"\n{'=' * 60}")
    print(f"  ALL DONE in {format_duration(total)}")
    print(f"  Results saved to: {OUTPUT_DIR}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
