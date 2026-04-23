from python.symmetric_parallel import run_parallel

# Weak scaling: 8 processes, min_length=0.012031 (~8.4M branches, 8x work)
# min_length = 0.04 * 0.67^3 — three levels deeper, 8x total branches
if __name__ == '__main__':
    result = run_parallel(
        trunk_length=100.0,
        ratio=0.67,
        branch_angle=30.0,
        min_length=0.012031,
        num_processes=8,
    )
    print(f"Finish in {result['execution_time']:.5f} seconds(s)")
