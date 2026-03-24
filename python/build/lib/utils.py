def print_header(name):
    print(f"\n=== {name} ===")


def print_params(trunk_length, length_ratio, branch_angle_deg, min_length, **kwargs):

    print(f"Parameters: trunk={trunk_length}, ratio={length_ratio}, "
          f"angle={branch_angle_deg}\u00b0, min_length={min_length}")

    for key, value in kwargs.items():
        print(f"  {key}: {value}")


def print_result(execution_time, num_branches, max_depth):

    print(f"Generation time: {execution_time:.6f}s")
    print(f"Branches: {num_branches:,} | Max depth: {max_depth}")
