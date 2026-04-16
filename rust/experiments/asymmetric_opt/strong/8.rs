use fractal_tree::{generate_fractal_tree_asymmetric, collect_tasks_asymmetric, Branch};
use rayon::prelude::*;
use std::f64::consts::PI;
use std::time::Instant;

const NUM_THREADS: usize = 8;
const MIN_LENGTH: f64 = 0.01;
const SPLIT_DEPTH: usize = 11;

// Asymmetric strong scaling: 8 threads, split_depth=11 (optimal for T_worst)
fn main() {
    let left_ratio = 0.67_f64;
    let right_ratio = 0.57_f64;
    let left_angle = 35.0_f64.to_radians();
    let right_angle = 25.0_f64.to_radians();
    let pool = rayon::ThreadPoolBuilder::new().num_threads(NUM_THREADS).build().unwrap();

    let start = Instant::now();
    let mut upper = vec![Branch { x1: 0.0, y1: 0.0, x2: 0.0, y2: 100.0, depth: 0 }];
    let mut tasks = collect_tasks_asymmetric(
        &mut upper, 0.0, 100.0, 100.0 * left_ratio, PI / 2.0 + left_angle,
        left_ratio, right_ratio, left_angle, right_angle, 1, SPLIT_DEPTH,
    );
    tasks.extend(collect_tasks_asymmetric(
        &mut upper, 0.0, 100.0, 100.0 * right_ratio, PI / 2.0 - right_angle,
        left_ratio, right_ratio, left_angle, right_angle, 1, SPLIT_DEPTH,
    ));
    let _results: Vec<Vec<Branch>> = pool.install(|| {
        tasks.par_iter().map(|t| generate_fractal_tree_asymmetric(
            t.x, t.y, t.length, t.angle,
            left_ratio, right_ratio, left_angle, right_angle, MIN_LENGTH, t.depth,
        )).collect()
    });
    println!("Finish in {:.5} seconds(s)", start.elapsed().as_secs_f64());
}
