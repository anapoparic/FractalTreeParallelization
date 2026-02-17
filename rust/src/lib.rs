use serde::{Deserialize, Serialize};
use std::fs;
use std::time::Instant;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Branch {
    pub x1: f64,
    pub y1: f64,
    pub x2: f64,
    pub y2: f64,
    pub depth: usize,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Iteration {
    pub iteration: usize,
    pub branch_count: usize,
    pub branches: Vec<(f64, f64, f64, f64)>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Parameters {
    pub trunk_length: f64,
    pub ratio: f64,
    pub branch_angle: f64,
    pub min_length: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FractalResult {
    pub parameters: Parameters,
    pub execution_time: f64,
    pub total_branches: usize,
    pub max_depth: usize,
    pub iterations: Vec<Iteration>,
}

/// Count how many branches a subtree will produce (without generating them).
pub fn count_branches(length: f64, ratio: f64, min_length: f64) -> usize {
    if length < min_length { return 0; }
    1 + 2 * count_branches(length * ratio, ratio, min_length)
}

pub fn print_header(name: &str) {
    println!("\n=== {} ===", name);
}

pub fn print_params(trunk_length: f64, length_ratio: f64, branch_angle_deg: f64, min_length: f64) {
    println!(
        "Parameters: trunk={}, ratio={}, angle={}\u{00b0}, min_length={}",
        trunk_length, length_ratio, branch_angle_deg, min_length
    );
}

pub fn print_extra_param(key: &str, value: &dyn std::fmt::Display) {
    println!("  {}: {}", key, value);
}

pub fn print_result(execution_time: f64, num_branches: usize, max_depth: usize) {
    println!("Generation time: {:.6}s", execution_time);
    println!("Branches: {} | Max depth: {}", num_branches, max_depth);
}


pub fn save_result(
    result: &mut FractalResult,
    branch_groups: &[Vec<Branch>],
    output_file: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("Starting JSON serialization...");
    let serial_start = Instant::now();

    let max_depth = branch_groups.iter()
        .flat_map(|g| g.iter())
        .map(|b| b.depth)
        .max()
        .unwrap_or(0);
    let total: usize = branch_groups.iter().map(|g| g.len()).sum();
    let iterations = group_by_iterations(branch_groups);
    result.total_branches = total;
    result.max_depth = max_depth;
    result.iterations = iterations;

    if let Some(parent) = std::path::Path::new(output_file).parent() {
        fs::create_dir_all(parent)?;
    }
    let json = serde_json::to_string_pretty(result)?;
    fs::write(output_file, json)?;

    let serial_time = serial_start.elapsed().as_secs_f64();
    println!("JSON serialization finished in {:.6}s", serial_time);
    println!("Saved to: {}", output_file);

    Ok(())
}


pub fn group_by_iterations(branch_groups: &[Vec<Branch>]) -> Vec<Iteration> {
    let max_depth = branch_groups.iter()
        .flat_map(|g| g.iter())
        .map(|b| b.depth)
        .max();

    let max_depth = match max_depth {
        Some(d) => d,
        None => return Vec::new(),
    };

    let mut iterations = Vec::new();

    for d in 0..=max_depth {
        let branches_up_to_depth: Vec<_> = branch_groups
            .iter()
            .flat_map(|g| g.iter())
            .filter(|b| b.depth <= d)
            .map(|b| (b.x1, b.y1, b.x2, b.y2))
            .collect();

        iterations.push(Iteration {
            iteration: d,
            branch_count: branches_up_to_depth.len(),
            branches: branches_up_to_depth,
        });
    }

    iterations
}

