"""
Variable Parameter Experiment Runner
=====================================
Runs variable parameter experiments for symmetric and asymmetric trees.
Each script prints results to stdout and saves a CSV to data/experiments/.

Usage:
    python run_variable_experiments.py                        # Run all
    python run_variable_experiments.py --tree symmetric       # Only symmetric
    python run_variable_experiments.py --tree asymmetric      # Only asymmetric
    python run_variable_experiments.py --param ratio          # Only ratio
    python run_variable_experiments.py --param min_length     # Only min_length
    python run_variable_experiments.py --param angle          # Only angle
"""
import sys
import os
import subprocess
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PYTHON_EXP_DIR = os.path.join(PROJECT_ROOT, 'python', 'experiments')

TREES  = ['symmetric', 'asymmetric']
PARAMS = ['ratio', 'min_length', 'angle']


def main():
    parser = argparse.ArgumentParser(description='Run variable parameter experiments')
    parser.add_argument('--tree',  choices=['symmetric', 'asymmetric', 'all'], default='all')
    parser.add_argument('--param', choices=['ratio', 'min_length', 'angle', 'all'], default='all')
    args = parser.parse_args()

    trees  = TREES  if args.tree  == 'all' else [args.tree]
    params = PARAMS if args.param == 'all' else [args.param]

    print("=" * 60)
    print("  VARIABLE PARAMETER EXPERIMENT RUNNER")
    print("=" * 60)
    print(f"  Tree types: {', '.join(trees)}")
    print(f"  Parameters: {', '.join(params)}")
    print(f"  Total experiments: {len(trees) * len(params)}")

    for tree in trees:
        for param in params:
            script = os.path.join(PYTHON_EXP_DIR, tree, 'variable', f'{param}.py')
            print(f"\n{'=' * 60}")
            print(f"  {tree.upper()} - {param.upper()}")
            print(f"{'=' * 60}")
            result = subprocess.run([sys.executable, script])
            if result.returncode != 0:
                print(f"\n  FAILED: {script}")

    print(f"\n{'=' * 60}")
    print(f"  ALL DONE")
    print(f"  Results saved to: {os.path.join(PROJECT_ROOT, 'data', 'experiments')}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
