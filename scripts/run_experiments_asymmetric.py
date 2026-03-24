"""
Asymmetric Tree Experiment Runner
===================================
Runs strong and weak scaling experiments for asymmetric fractal tree.
Delegates to run_experiments.py with --tree asymmetric.

Usage:
    python run_experiments_asymmetric.py
    python run_experiments_asymmetric.py --runs 5
    python run_experiments_asymmetric.py --lang python
    python run_experiments_asymmetric.py --scaling strong
"""
import sys
import os
import subprocess

args = [sys.executable, os.path.join(os.path.dirname(__file__), 'run_experiments.py'),
        '--tree', 'asymmetric'] + sys.argv[1:]
subprocess.run(args)
