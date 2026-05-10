from python.symmetric_sequential import run_sequential

# Weak scaling baseline: 1 process, min_length=0.04 (~1M branches)
result = run_sequential(
    trunk_length=100.0,
    ratio=0.67,
    branch_angle=30.0,
    min_length=0.04,
)
print(f"Finish in {result['execution_time']:.5f} seconds(s)")
