from python.asymmetric_sequential import run_sequential_asymmetric

# Asymmetric strong scaling baseline: sequential, fixed problem size
result = run_sequential_asymmetric(
    trunk_length=100.0,
    left_ratio=0.67,
    right_ratio=0.57,
    left_angle=35.0,
    right_angle=25.0,
    min_length=0.01,
)
print(f"Finish in {result['execution_time']:.5f} seconds(s)")
