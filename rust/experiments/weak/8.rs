use fractal_tree::{generate_fractal_tree, collect_tasks, Branch};
use rayon::prelude::*;
use std::f64::consts::PI;
use std::time::Instant;

const NUM_THREADS: usize = 8;
// min_length = 0.5 * 0.67^3 = 0.150 — three levels deeper, ~8x branches
const MIN_LENGTH: f64 = 0.150;

// Weak scaling: 8 threads, min_length=0.150 (~8x work vs n=1)
fn main() {
    let (ratio, ba) = (0.67_f64, 30.0_f64.to_radians());
    let split = (NUM_THREADS * 4).next_power_of_two().ilog2() as usize;
    let pool = rayon::ThreadPoolBuilder::new().num_threads(NUM_THREADS).build().unwrap();

    let start = Instant::now();
    let mut upper = vec![Branch { x1: 0.0, y1: 0.0, x2: 0.0, y2: 100.0, depth: 0 }];
    let cl = 100.0 * ratio;
    let mut tasks = collect_tasks(&mut upper, 0.0, 100.0, cl, PI / 2.0 + ba, ratio, ba, 1, split);
    tasks.extend(collect_tasks(&mut upper, 0.0, 100.0, cl, PI / 2.0 - ba, ratio, ba, 1, split));
    let _results: Vec<Vec<Branch>> = pool.install(|| {
        tasks.par_iter().map(|t| generate_fractal_tree(t.x, t.y, t.length, t.angle, ratio, ba, MIN_LENGTH, t.depth)).collect()
    });
    println!("Finish in {:.5} secounds(s)", start.elapsed().as_secs_f64());
}
