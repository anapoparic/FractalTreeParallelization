use fractal_tree::{
    generate_fractal_tree_asymmetric,
    print_header, print_params, print_extra_param, print_result,
};
use std::f64::consts::PI;
use std::time::Instant;
use std::error::Error;


pub fn run_sequential_asymmetric(
    trunk_length: f64,
    left_ratio: f64,
    right_ratio: f64,
    left_angle: f64,
    right_angle: f64,
    min_length: f64,
) -> Result<f64, Box<dyn Error>> {
    let left_angle_rad  = left_angle.to_radians();
    let right_angle_rad = right_angle.to_radians();

    print_header("Sequential Asymmetric (Rust)");
    print_params(trunk_length, left_ratio, left_angle, min_length);
    print_extra_param("right_ratio", &right_ratio);
    print_extra_param("right_angle", &right_angle);

    let start = Instant::now();
    let branches = generate_fractal_tree_asymmetric(
        0.0, 0.0, trunk_length, PI / 2.0,
        left_ratio, right_ratio, left_angle_rad, right_angle_rad,
        min_length, 0,
    );
    let execution_time = start.elapsed().as_secs_f64();

    let max_depth = branches.iter().map(|b| b.depth).max().unwrap_or(0);
    print_result(execution_time, branches.len(), max_depth);

    Ok(execution_time)
}


fn main() -> Result<(), Box<dyn Error>> {
    run_sequential_asymmetric(100.0, 0.67, 0.57, 35.0, 25.0, 0.01)?;
    Ok(())
}
