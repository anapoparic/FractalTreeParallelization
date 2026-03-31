from python.symmetric_parallel import run_parallel

# Weak scaling: 2 processes, min_length=0.335 (~64K branches, 2x work)
# min_length = 0.5 * 0.67^1 — one level deeper, doubles total branches
if __name__ == '__main__':
    result = run_parallel(
        trunk_length=100.0,
        ratio=0.67,
        branch_angle=30.0,
        min_length=0.335,
        num_processes=2,
    )
    print(f"Finish in {result['execution_time']:.5f} seconds(s)")
