from python.asymmetric_parallel import run_parallel_asymmetric

# Asymmetric weak scaling: 4 processes, min_length=0.003819 (~4M branches, ~4x work)
# min_length = 0.01 * 0.618^2 — two levels deeper, ~4x branches
if __name__ == '__main__':
    result = run_parallel_asymmetric(
        trunk_length=100.0,
        left_ratio=0.67,
        right_ratio=0.57,
        left_angle=35.0,
        right_angle=25.0,
        min_length=0.003819,
        num_processes=4,
    )
    print(f"Finish in {result['execution_time']:.5f} seconds(s)")
