use fractal_tree::{
    generate_fractal_tree, collect_tasks,
    print_header, print_params, print_extra_param, print_result, save_result,
    Branch, FractalResult, Parameters,
};
use rayon::prelude::*;
use std::f64::consts::PI;
use std::thread;
use std::time::Instant;
use std::error::Error;


pub fn run_parallel(
    trunk_length: f64, 
    ratio: f64, 
    branch_angle: f64, 
    min_length: f64,
    num_threads: Option<usize>, 
    output_file: &str,
) -> Result<FractalResult, Box<dyn Error>> {

    let num_threads = num_threads.unwrap_or_else(|| {
        thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    });

    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(num_threads)
        .build()?;

    let branch_angle_rad = branch_angle.to_radians();
    let split_depth = (num_threads * 4).next_power_of_two().ilog2() as usize;

    print_header("Parallel Simple (Rust)");
    print_params(trunk_length, ratio, branch_angle, min_length);
    print_extra_param("threads", &num_threads);
    print_extra_param("split_depth", &split_depth);

    let start = Instant::now();

    let mut upper_branches = vec![Branch { x1: 0.0, y1: 0.0, x2: 0.0, y2: trunk_length, depth: 0 }];
    let child_length = trunk_length * ratio;
    let mut tasks = collect_tasks(&mut upper_branches, 0.0, trunk_length, child_length, PI / 2.0 + branch_angle_rad, ratio, branch_angle_rad, 1, split_depth);
    tasks.extend(collect_tasks(&mut upper_branches, 0.0, trunk_length, child_length, PI / 2.0 - branch_angle_rad, ratio, branch_angle_rad, 1, split_depth));

    let subtree_results: Vec<Vec<Branch>> = pool.install(|| {
        tasks.par_iter()
            .map(|task| generate_fractal_tree(task.x, task.y, task.length, task.angle, ratio, branch_angle_rad, min_length, task.depth))
            .collect()
    });

    let execution_time = start.elapsed().as_secs_f64();

    let total_branches: usize = upper_branches.len() + subtree_results.iter().map(|subtree| subtree.len()).sum::<usize>();
    let max_depth = subtree_results.iter()
        .filter_map(|subtree| subtree.last().map(|branch| branch.depth))
        .max()
        .unwrap_or(0);

    print_result(execution_time, total_branches, max_depth);

    let mut result = FractalResult {
        parameters: Parameters { trunk_length, ratio, branch_angle, min_length },
        execution_time,
        total_branches,
        max_depth,
        iterations: Vec::new(),
    };

    let mut all_groups = vec![upper_branches];
    all_groups.extend(subtree_results);
    save_result(&mut result, &all_groups, output_file)?;

    Ok(result)
}

fn main() -> Result<(), Box<dyn Error>> {
    run_parallel(100.0, 0.67, 30.0, 0.01, None, "parallel_rust.json")?;
    Ok(())
}
