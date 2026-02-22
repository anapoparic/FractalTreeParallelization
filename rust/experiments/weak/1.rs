use fractal_tree::generate_fractal_tree;
use std::f64::consts::PI;
use std::time::Instant;

// Weak scaling baseline: sequential, min_length=0.5 (~32K branches)
fn main() {
    let branch_angle_rad = 30.0_f64.to_radians();
    let start = Instant::now();
    let _branches = generate_fractal_tree(
        0.0, 0.0, 100.0, PI / 2.0, 0.67, branch_angle_rad, 0.5, 0,
    );
    let t = start.elapsed().as_secs_f64();
    println!("Finish in {:.5} secounds(s)", t);
}
