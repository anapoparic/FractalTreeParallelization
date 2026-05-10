use fractal_tree::{
    generate_fractal_tree,
    print_header, print_params, print_result,
    FractalResult, Parameters,
};
use std::f64::consts::PI;
use std::time::Instant;
use std::error::Error;

pub fn run_sequential(
    trunk_length: f64,
    ratio: f64,
    branch_angle: f64,
    min_length: f64,
) -> Result<FractalResult, Box<dyn Error>> {
    let branch_angle_radians = branch_angle.to_radians();

    print_header("Sequential (Rust)");
    print_params(trunk_length, ratio, branch_angle, min_length);

    let start_time = Instant::now();
    let branches = generate_fractal_tree(
        0.0, 0.0, trunk_length, PI / 2.0, ratio, branch_angle_radians, min_length, 0,
    );
    let execution_time = start_time.elapsed().as_secs_f64();

    let max_depth = branches.iter().map(|b| b.depth).max().unwrap_or(0);
    print_result(execution_time, branches.len(), max_depth);

    let result = FractalResult {
        parameters: Parameters {
            trunk_length,
            ratio,
            branch_angle,
            min_length,
        },
        execution_time,
        total_branches: branches.len(),
        max_depth,
        iterations: Vec::new(),
    };

    Ok(result)
}

fn main() -> Result<(), Box<dyn Error>> {
    run_sequential(100.0, 0.67, 30.0, 0.01)?;
    Ok(())
}
