use fractal_tree::{generate_fractal_tree_asymmetric, collect_tasks_asymmetric, Branch};
use rayon::prelude::*;
use std::f64::consts::PI;
use std::time::Instant;
use std::fs;
use std::io::Write;
use std::path::Path;

const NUM_THREADS: usize = 8;
const NUM_RUNS:    usize = 3;
const MIN_LENGTH:  f64   = 0.01;
const TRUNK:       f64   = 100.0;
const LEFT_RATIO:  f64   = 0.67;
const RIGHT_RATIO: f64   = 0.57;
const LEFT_ANGLE:  f64   = 35.0;   // degrees
const RIGHT_ANGLE: f64   = 25.0;   // degrees
const MAX_DEPTH:   usize = 12;

// Variable split_depth experiment — asymmetric tree, Rust/Rayon
// Fixed: left_ratio=0.67, right_ratio=0.57, min_length=0.01, threads=8
//
// split_depth varies: 1 to 12
// Each depth is run NUM_RUNS times; mean is reported.
//
// Purpose: find the empirically optimal split_depth for Rayon work-stealing.
// Hypothesis: shallow splits are sufficient because work-stealing handles
// load imbalance dynamically — unlike Python's static pool.map.

fn run_parallel(left_angle_rad: f64, right_angle_rad: f64, split: usize, pool: &rayon::ThreadPool) -> f64 {
    let start = Instant::now();

    let mut upper = vec![Branch { x1: 0.0, y1: 0.0, x2: 0.0, y2: TRUNK, depth: 0 }];
    let mut tasks = collect_tasks_asymmetric(
        &mut upper,
        0.0, TRUNK, TRUNK * LEFT_RATIO, PI / 2.0 + left_angle_rad,
        LEFT_RATIO, RIGHT_RATIO, left_angle_rad, right_angle_rad, 1, split,
    );
    tasks.extend(collect_tasks_asymmetric(
        &mut upper,
        0.0, TRUNK, TRUNK * RIGHT_RATIO, PI / 2.0 - right_angle_rad,
        LEFT_RATIO, RIGHT_RATIO, left_angle_rad, right_angle_rad, 1, split,
    ));

    let _results: Vec<Vec<Branch>> = pool.install(|| {
        tasks.par_iter().map(|t| generate_fractal_tree_asymmetric(
            t.x, t.y, t.length, t.angle,
            LEFT_RATIO, RIGHT_RATIO, left_angle_rad, right_angle_rad, MIN_LENGTH, t.depth,
        )).collect()
    });

    start.elapsed().as_secs_f64()
}

fn main() {
    let left_angle_rad  = LEFT_ANGLE.to_radians();
    let right_angle_rad = RIGHT_ANGLE.to_radians();
    let pool = rayon::ThreadPoolBuilder::new().num_threads(NUM_THREADS).build().unwrap();
    let heuristic_depth = (NUM_THREADS * 4).next_power_of_two().ilog2() as usize;

    // sequential baseline
    let seq_start = Instant::now();
    let seq_branches = generate_fractal_tree_asymmetric(
        0.0, 0.0, TRUNK, PI / 2.0,
        LEFT_RATIO, RIGHT_RATIO, left_angle_rad, right_angle_rad, MIN_LENGTH, 0,
    );
    let seq_time = seq_start.elapsed().as_secs_f64();
    let branch_count = seq_branches.len();

    println!("\n=== Variable split_depth (asymmetric, Rust) | threads={NUM_THREADS}, \
              left_ratio={LEFT_RATIO}, right_ratio={RIGHT_RATIO}, min_length={MIN_LENGTH} ===");
    println!("  Sequential baseline: {seq_time:.5}s  ({branch_count} branches)");
    println!();
    println!("{:>6} {:>7} {:>13} {:>9} {:>12}  note",
             "depth", "tasks", "par_mean (s)", "speedup", "efficiency");
    println!("{}", "-".repeat(65));

    let mut csv_rows: Vec<String> = Vec::new();
    csv_rows.push("split_depth,num_tasks,branches,seq_time,par_mean,speedup,efficiency".to_string());

    for depth in 1..=MAX_DEPTH {
        let num_tasks = 2_usize.pow(depth as u32);
        let times: Vec<f64> = (0..NUM_RUNS)
            .map(|_| run_parallel(left_angle_rad, right_angle_rad, depth, &pool))
            .collect();
        let par_mean   = times.iter().sum::<f64>() / NUM_RUNS as f64;
        let speedup    = seq_time / par_mean;
        let efficiency = speedup / NUM_THREADS as f64;
        let note = if depth == heuristic_depth { "<-- heuristic" } else { "" };

        println!("{depth:>6} {num_tasks:>7} {par_mean:>13.5} {speedup:>8.3}x {pct:>11.1}%  {note}",
                 pct = efficiency * 100.0);

        csv_rows.push(format!("{},{},{},{:.6},{:.6},{:.4},{:.4}",
                              depth, num_tasks, branch_count, seq_time, par_mean, speedup, efficiency));
    }

    // save CSV
    let out_dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent().unwrap()
        .join("data").join("asymmetric").join("split_depth");
    fs::create_dir_all(&out_dir).unwrap();
    let csv_path = out_dir.join("empirical_rust.csv");
    let mut file = fs::File::create(&csv_path).unwrap();
    for row in &csv_rows {
        writeln!(file, "{row}").unwrap();
    }
    println!("\nSaved: {}", csv_path.display());
}
