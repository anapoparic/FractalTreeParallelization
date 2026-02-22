import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sequential import run_sequential

# Strong scaling baseline: sequential, fixed problem size
result = run_sequential(
    trunk_length=100.0,
    ratio=0.67,
    branch_angle=30.0,
    min_length=0.01,
)
print(f"Finish in {result['execution_time']:.5f} secounds(s)")
