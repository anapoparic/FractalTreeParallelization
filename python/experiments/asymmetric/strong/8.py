from python.asymmetric_parallel import run_parallel_asymmetric

# Asymmetric strong scaling: 8 processes, fixed problem size (~8.5M branches)
if __name__ == '__main__':
    result = run_parallel_asymmetric(
        trunk_length=100.0,
        left_ratio=0.67,
        right_ratio=0.57,
        left_angle=35.0,
        right_angle=25.0,
        min_length=0.0023,
        num_processes=8,
    )
    print(f"Finish in {result['execution_time']:.5f} seconds(s)")
