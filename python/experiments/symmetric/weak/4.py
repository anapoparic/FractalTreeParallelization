from python.symmetric_parallel import run_parallel

# Weak scaling: 4 processes, min_length=0.017956 (~4.2M branches, 4x work)
# min_length = 0.04 * 0.67^2 — two levels deeper, 4x total branches
if __name__ == '__main__':
    result = run_parallel(
        trunk_length=100.0,
        ratio=0.67,
        branch_angle=30.0,
        min_length=0.017956,
        num_processes=4,
    )
    print(f"Finish in {result['execution_time']:.5f} seconds(s)")
