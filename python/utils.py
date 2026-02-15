import time
import json
import os

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


def group_by_iterations(branches):
    
    if not branches:
        return []

    max_depth = max(b[4] for b in branches)
    iterations = []

    for d in range(max_depth + 1):
        branches_up_to_depth = [b for b in branches if b[4] <= d]
        iterations.append({
            'iteration': d,
            'branch_count': len(branches_up_to_depth),
            'branches': [(x1, y1, x2, y2) for x1, y1, x2, y2, _ in branches_up_to_depth]
        })

    return iterations

# Handle group_by_iterations + JSON serialization + file write
def save_result(result, branches, output_file):

    print("Starting JSON serialization...")
    serial_start = time.perf_counter()

    max_depth = max(b[4] for b in branches) if branches else 0
    iterations = group_by_iterations(branches)
    result['iterations'] = iterations
    result['total_branches'] = len(branches)
    result['max_depth'] = max_depth

    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    serial_time = time.perf_counter() - serial_start
    print(f"JSON serialization finished in {serial_time:.6f}s")
    print(f"Saved to: {output_file}")
