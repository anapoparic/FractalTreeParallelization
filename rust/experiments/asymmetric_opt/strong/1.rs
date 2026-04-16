use fractal_tree::generate_fractal_tree_asymmetric;
use std::f64::consts::PI;
use std::time::Instant;

// Asymmetric strong scaling baseline (split_depth=11): sequential, fixed problem size
fn main() {
    let left_angle = 35.0_f64.to_radians();
    let right_angle = 25.0_f64.to_radians();
    let start = Instant::now();
    let _branches = generate_fractal_tree_asymmetric(
        0.0, 0.0, 100.0, PI / 2.0, 0.67, 0.57, left_angle, right_angle, 0.01, 0,
    );
    println!("Finish in {:.5} seconds(s)", start.elapsed().as_secs_f64());
}
