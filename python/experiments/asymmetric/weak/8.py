from python.asymmetric_parallel import run_parallel_asymmetric

# Asymmetric weak scaling: 8 processes, min_length=0.118
# min_length = 0.5 * sqrt(0.67 * 0.57)^3 — three levels deeper, ~8x branches
if __name__ == '__main__':
    result = run_parallel_asymmetric(
        trunk_length=100.0,
        left_ratio=0.67,
        right_ratio=0.57,
        left_angle=35.0,
        right_angle=25.0,
        min_length=0.118,
        num_processes=8,
    )
    print(f"Finish in {result['execution_time']:.5f} seconds(s)")
