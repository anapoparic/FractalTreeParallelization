"""
Symmetric Tree Experiment Runner
=================================
Runs strong and weak scaling experiments for symmetric fractal tree.
Delegates to run_experiments.py with --tree symmetric.

Usage:
    python run_experiments_symmetric.py
    python run_experiments_symmetric.py --runs 5
    python run_experiments_symmetric.py --lang python
    python run_experiments_symmetric.py --scaling strong
"""
import sys
import os
import subprocess

args = [sys.executable, os.path.join(os.path.dirname(__file__), 'run_experiments.py'),
        '--tree', 'symmetric'] + sys.argv[1:]
subprocess.run(args)
