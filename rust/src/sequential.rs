use fractal_tree::{
    count_branches, print_header, print_params, print_result, save_result,
    Branch, FractalResult, Parameters,
};
use std::f64::consts::PI;
use std::time::Instant;
use std::error::Error;

fn generate_fractal_tree(
    x: f64, 
    y: f64, 
    length: f64, 
    angle: f64,
    ratio: f64, 
    branch_angle: f64, 
    min_length: f64, 
    start_depth: usize,
) -> Vec<Branch> {
    let mut branches = Vec::with_capacity(count_branches(length, ratio, min_length));

    fn recurse(
        branches: &mut Vec<Branch>,
        x: f64, 
        y: f64, 
        length: f64, 
        angle: f64,
        ratio: f64, 
        branch_angle: f64, 
        min_length: f64, 
        depth: usize,
    ) {
        if length < min_length {
            return;
        }
        let end_x = x + length * angle.cos();
        let end_y = y + length * angle.sin();
        branches.push(Branch { x1: x, y1: y, x2: end_x, y2: end_y, depth });

        let new_len = length * ratio;
        recurse(branches, end_x, end_y, new_len, angle + branch_angle, ratio, branch_angle, min_length, depth + 1);
        recurse(branches, end_x, end_y, new_len, angle - branch_angle, ratio, branch_angle, min_length, depth + 1);
    }

    recurse(&mut branches, x, y, length, angle, ratio, branch_angle, min_length, start_depth);
    branches
}

pub fn run_sequential(
    trunk_length: f64,
    ratio: f64,
    branch_angle: f64,
    min_length: f64,
    output_file: &str,
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

    let mut result = FractalResult {
        parameters: Parameters {
            trunk_length,
            ratio,
            branch_angle,
            min_length,
        },
        execution_time,
        total_branches: branches.len(),
        max_depth: max_depth,
        iterations: Vec::new(),
    };
    // save_result(&mut result, &[branches], output_file)?;

    Ok(result)
}

fn main() -> Result<(), Box<dyn Error>> {
    run_sequential(100.0, 0.67, 30.0, 0.01, "../data/sequential_rust.json")?;
    Ok(())
}
