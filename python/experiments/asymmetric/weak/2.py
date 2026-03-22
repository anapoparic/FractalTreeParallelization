import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from parallel_asymmetric import run_parallel_asymmetric

# Asymmetric weak scaling: 2 processes, min_length=0.309
# min_length = 0.5 * sqrt(0.67 * 0.57)^1 — one level deeper, ~2x branches
if __name__ == '__main__':
    result = run_parallel_asymmetric(
        trunk_length=100.0,
        left_ratio=0.67,
        right_ratio=0.57,
        left_angle=35.0,
        right_angle=25.0,
        min_length=0.309,
        num_processes=2,
    )
    print(f"Finish in {result['execution_time']:.5f} seconds(s)")
