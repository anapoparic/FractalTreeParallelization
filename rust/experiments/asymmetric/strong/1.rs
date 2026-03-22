use fractal_tree::generate_fractal_tree_asymmetric;
use std::f64::consts::PI;
use std::time::Instant;

// Asymmetric strong scaling baseline: sequential, fixed problem size (min_length=0.01)
fn main() {
    let left_angle = 35.0_f64.to_radians();
    let right_angle = 25.0_f64.to_radians();
    let start = Instant::now();
    let _branches = generate_fractal_tree_asymmetric(
        0.0, 0.0, 100.0, PI / 2.0, 0.67, 0.57, left_angle, right_angle, 0.01, 0,
    );
    let t = start.elapsed().as_secs_f64();
    println!("Finish in {:.5} seconds(s)", t);
}
