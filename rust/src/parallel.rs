use fractal_tree::{
    count_branches, print_header, print_params, print_extra_param, print_result, save_result
    Branch, FractalResult, Parameters,
};
use rayon::prelude::*;
use std::f64::consts::PI;
use std::thread;
use std::time::Instant;
use std::error::Error

struct TaskParams {
    x: f64, 
    y: f64, 
    length: f64, 
    angle: f64, 
    depth: usize,
}

fn generate_subtree(
    x: f64, 
    y: f64, 
    length: f64, 
    angle: f64,
    ratio: f64, 
    branch_angle_rad: f64, 
    min_length: f64, 
    depth: usize,
) -> Vec<Branch> {
    let mut branches = Vec::with_capacity(count_branches(length, ratio, min_length));

    fn recurse(
        branches: &mut Vec<Branch>, 
        x: f64, 
        y: f64, 
        length: f64, 
        angle: f64,
        ratio: f64, 
        branch_angle_rad: f64, 
        min_length: f64, 
        depth: usize,
    ) {
        if length < min_length { return; }
        let end_x = x + length * angle.cos();
        let end_y = y + length * angle.sin();
        branches.push(Branch { x1: x, y1: y, x2: end_x, y2: end_y, depth });

        let child_length = length * ratio;
        recurse(branches, end_x, end_y, child_length, angle + branch_angle_rad, ratio, branch_angle_rad, min_length, depth + 1);
        recurse(branches, end_x, end_y, child_length, angle - branch_angle_rad, ratio, branch_angle_rad, min_length, depth + 1);
    }

    recurse(&mut branches, x, y, length, angle, ratio, branch_angle_rad, min_length, depth);
    branches
}

/// Expand tree to split_depth, collecting upper branches and leaf task params.
fn collect_tasks(
    upper_branches: &mut Vec<Branch>, 
    x: f64, 
    y: f64, 
    length: f64, 
    angle: f64,
    ratio: f64, 
    branch_angle_rad: f64, 
    depth: usize, 
    split_depth: usize,
) -> Vec<TaskParams> {
    if depth >= split_depth {
        return vec![TaskParams { x, y, length, angle, depth }];
    }
    let end_x = x + length * angle.cos();
    let end_y = y + length * angle.sin();
    upper_branches.push(Branch { x1: x, y1: y, x2: end_x, y2: end_y, depth });

    let child_length = length * ratio;
    let mut subtasks = collect_tasks(upper_branches, end_x, end_y, child_length, angle + branch_angle_rad, ratio, branch_angle_rad, depth + 1, split_depth);
    subtasks.extend(collect_tasks(upper_branches, end_x, end_y, child_length, angle - branch_angle_rad, ratio, branch_angle_rad, depth + 1, split_depth));
    subtasks
}

pub fn run_parallel(
    trunk_length: f64, 
    ratio: f64, 
    branch_angle: f64, 
    min_length: f64,
    num_threads: Option<usize>, 
    _output_file: &str,
) -> Result<FractalResult, Box<dyn Error>> {

    let num_threads = num_threads.unwrap_or_else(|| {
        thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    });

    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(num_threads)
        .build()?;

    let branch_angle_rad = branch_angle.to_radians();
    let split_depth = (num_threads * 4).next_power_of_two().trailing_zeros() as usize;

    print_header("Parallel Simple (Rust)");
    print_params(trunk_length, ratio, branch_angle, min_length);
    print_extra_param("threads", &num_threads);
    print_extra_param("split_depth", &split_depth);

    let start = Instant::now();

    let mut upper_branches = vec![Branch { x1: 0.0, y1: 0.0, x2: 0.0, y2: trunk_length, depth: 0 }];
    let child_length = trunk_length * ratio;
    let mut tasks = collect_tasks(&mut upper_branches, 0.0, trunk_length, child_length, PI / 2.0 + branch_angle_rad, ratio, branch_angle_rad, 1, split_depth);
    tasks.extend(collect_tasks(&mut upper_branches, 0.0, trunk_length, child_length, PI / 2.0 - branch_angle_rad, ratio, branch_angle_rad, 1, split_depth));

    // Parallel: rayon distributes tasks across threads, each returns pre-allocated Vec
    let subtree_results: Vec<Vec<Branch>> = pool.install(|| {
        tasks.par_iter()
            .map(|task| generate_subtree(task.x, task.y, task.length, task.angle, ratio, branch_angle_rad, min_length, task.depth))
            .collect()
    });

    let execution_time = start.elapsed().as_secs_f64();

    let total_branches = upper_branches.len() + subtree_results.iter().map(|subtree| subtree.len()).sum::<usize>();
    let max_depth = subtree_results.iter()
        .filter_map(|subtree| subtree.last().map(|branch| branch.depth))
        .max()
        .unwrap_or(0);

    print_result(execution_time, total_branches, max_depth);

    // let mut all_groups = vec![upper_branches];
    // all_groups.extend(subtree_results);
    // save_result(&mut result, &all_groups, _output_file)?;

    Ok(FractalResult {
        parameters: Parameters { trunk_length, ratio, branch_angle, min_length },
        execution_time,
        total_branches,
        max_depth,
        iterations: Vec::new(),
    })
}

fn main() -> Result<(), Box<dyn Error>> {
    run_parallel_simple(100.0, 0.67, 30.0, 0.01, None, "../data/parallel_simple_rust.json")?;
    Ok(())
}
