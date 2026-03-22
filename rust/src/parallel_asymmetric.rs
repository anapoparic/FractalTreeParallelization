use fractal_tree::{
    generate_fractal_tree_asymmetric, collect_tasks_asymmetric,
    print_header, print_params, print_extra_param, print_result,
    Branch,
};
use rayon::prelude::*;
use std::f64::consts::PI;
use std::thread;
use std::time::Instant;
use std::error::Error;


pub fn run_parallel_asymmetric(
    trunk_length: f64,
    left_ratio: f64,
    right_ratio: f64,
    left_angle: f64,
    right_angle: f64,
    min_length: f64,
    num_threads: Option<usize>,
) -> Result<f64, Box<dyn Error>> {

    let num_threads = num_threads.unwrap_or_else(|| {
        thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    });

    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(num_threads)
        .build()?;

    let left_angle_rad  = left_angle.to_radians();
    let right_angle_rad = right_angle.to_radians();
    let split_depth = (num_threads * 4).next_power_of_two().ilog2() as usize;

    print_header("Parallel Asymmetric (Rust)");
    print_params(trunk_length, left_ratio, left_angle, min_length);
    print_extra_param("right_ratio", &right_ratio);
    print_extra_param("right_angle", &right_angle);
    print_extra_param("threads", &num_threads);
    print_extra_param("split_depth", &split_depth);

    let start = Instant::now();

    let mut upper_branches = vec![Branch { x1: 0.0, y1: 0.0, x2: 0.0, y2: trunk_length, depth: 0 }];

    // Left child of root uses left_ratio / left_angle; right child uses right_ratio / right_angle.
    let mut tasks = collect_tasks_asymmetric(
        &mut upper_branches,
        0.0, trunk_length, trunk_length * left_ratio, PI / 2.0 + left_angle_rad,
        left_ratio, right_ratio, left_angle_rad, right_angle_rad, 1, split_depth,
    );
    tasks.extend(collect_tasks_asymmetric(
        &mut upper_branches,
        0.0, trunk_length, trunk_length * right_ratio, PI / 2.0 - right_angle_rad,
        left_ratio, right_ratio, left_angle_rad, right_angle_rad, 1, split_depth,
    ));

    // Tasks have unequal sizes when left_ratio ≠ right_ratio — Rayon work-stealing
    // redistributes them dynamically, unlike Python's static pool.map split.
    let subtree_results: Vec<Vec<Branch>> = pool.install(|| {
        tasks.par_iter()
            .map(|task| generate_fractal_tree_asymmetric(
                task.x, task.y, task.length, task.angle,
                left_ratio, right_ratio, left_angle_rad, right_angle_rad,
                min_length, task.depth,
            ))
            .collect()
    });

    let execution_time = start.elapsed().as_secs_f64();

    let total_branches: usize = upper_branches.len()
        + subtree_results.iter().map(|s| s.len()).sum::<usize>();
    let max_depth = subtree_results.iter()
        .flat_map(|subtree| subtree.iter())
        .map(|b| b.depth)
        .max()
        .unwrap_or(0);

    print_result(execution_time, total_branches, max_depth);

    Ok(execution_time)
}


fn main() -> Result<(), Box<dyn Error>> {
    run_parallel_asymmetric(100.0, 0.67, 0.57, 35.0, 25.0, 0.01, None)?;
    Ok(())
}
