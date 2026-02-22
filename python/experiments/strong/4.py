import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from parallel import run_parallel

# Strong scaling: 4 processes, fixed problem size
if __name__ == '__main__':
    result = run_parallel(
        trunk_length=100.0,
        ratio=0.67,
        branch_angle=30.0,
        min_length=0.01,
        num_processes=4,
    )
    print(f"Finish in {result['execution_time']:.5f} secounds(s)")
