use fractal_tree::{
    generate_fractal_tree, generate_fractal_tree_asymmetric,
    collect_tasks, collect_tasks_asymmetric,
    Branch,
};
use rayon::prelude::*;
use std::f64::consts::PI;
use std::error::Error;


fn sort_branches(branches: &mut Vec<Branch>) {
    // Round to 1e-6 precision before comparing so that the ~6e-15 floating-point
    // discrepancy in the symmetric trunk endpoint (hardcoded 0 vs. computed cos(PI/2)*L)
    // does not affect sort order.
    branches.sort_by_key(|b| {
        let r = |x: f64| -> i64 { (x * 1e6).round() as i64 };
        (r(b.x1), r(b.y1), r(b.x2), r(b.y2), b.depth)
    });
}

fn branches_equal(a: &[Branch], b: &[Branch], tol: f64) -> bool {
    a.len() == b.len()
        && a.iter().zip(b.iter()).all(|(x, y)| {
            (x.x1 - y.x1).abs() < tol
                && (x.y1 - y.y1).abs() < tol
                && (x.x2 - y.x2).abs() < tol
                && (x.y2 - y.y2).abs() < tol
                && x.depth == y.depth
        })
}

fn check(name: &str, mut seq: Vec<Branch>, mut par: Vec<Branch>) -> bool {
    sort_branches(&mut seq);
    sort_branches(&mut par);
    let ok = branches_equal(&seq, &par, 1e-10);
    println!(
        "{}  {}  ({} branches)",
        if ok { "  OK  " } else { "  FAIL" },
        name,
        seq.len()
    );
    ok
}

fn parallel_sym(
    trunk_length: f64,
    ratio: f64,
    branch_angle_rad: f64,
    min_length: f64,
    num_threads: usize,
) -> Vec<Branch> {
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(num_threads)
        .build()
        .unwrap();
    let split_depth = (num_threads * 4).next_power_of_two().ilog2() as usize;

    let mut upper = vec![Branch { x1: 0.0, y1: 0.0, x2: 0.0, y2: trunk_length, depth: 0 }];
    let child_len = trunk_length * ratio;
    let mut tasks = collect_tasks(
        &mut upper, 0.0, trunk_length, child_len,
        PI / 2.0 + branch_angle_rad, ratio, branch_angle_rad, 1, split_depth,
    );
    tasks.extend(collect_tasks(
        &mut upper, 0.0, trunk_length, child_len,
        PI / 2.0 - branch_angle_rad, ratio, branch_angle_rad, 1, split_depth,
    ));

    let subtrees: Vec<Vec<Branch>> = pool.install(|| {
        tasks.par_iter()
            .map(|t| generate_fractal_tree(
                t.x, t.y, t.length, t.angle,
                ratio, branch_angle_rad, min_length, t.depth,
            ))
            .collect()
    });

    let mut all = upper;
    for sub in subtrees {
        all.extend(sub);
    }
    all
}

fn parallel_asym(
    trunk_length: f64,
    left_ratio: f64,
    right_ratio: f64,
    left_angle_rad: f64,
    right_angle_rad: f64,
    min_length: f64,
    num_threads: usize,
) -> Vec<Branch> {
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(num_threads)
        .build()
        .unwrap();
    let split_depth = (num_threads * 4).next_power_of_two().ilog2() as usize;

    let mut upper = vec![Branch { x1: 0.0, y1: 0.0, x2: 0.0, y2: trunk_length, depth: 0 }];
    let mut tasks = collect_tasks_asymmetric(
        &mut upper, 0.0, trunk_length, trunk_length * left_ratio,
        PI / 2.0 + left_angle_rad,
        left_ratio, right_ratio, left_angle_rad, right_angle_rad, 1, split_depth,
    );
    tasks.extend(collect_tasks_asymmetric(
        &mut upper, 0.0, trunk_length, trunk_length * right_ratio,
        PI / 2.0 - right_angle_rad,
        left_ratio, right_ratio, left_angle_rad, right_angle_rad, 1, split_depth,
    ));

    let subtrees: Vec<Vec<Branch>> = pool.install(|| {
        tasks.par_iter()
            .map(|t| generate_fractal_tree_asymmetric(
                t.x, t.y, t.length, t.angle,
                left_ratio, right_ratio, left_angle_rad, right_angle_rad, min_length, t.depth,
            ))
            .collect()
    });

    let mut all = upper;
    for sub in subtrees {
        all.extend(sub);
    }
    all
}

fn main() -> Result<(), Box<dyn Error>> {
    println!("=== Rust correctness verification ===\n");

    let branch_angle_rad = 30_f64.to_radians();
    let left_angle_rad   = 35_f64.to_radians();
    let right_angle_rad  = 25_f64.to_radians();

    let seq_sym = generate_fractal_tree(
        0.0, 0.0, 100.0, PI / 2.0, 0.67, branch_angle_rad, 0.01, 0,
    );
    let seq_asym = generate_fractal_tree_asymmetric(
        0.0, 0.0, 100.0, PI / 2.0,
        0.67, 0.57, left_angle_rad, right_angle_rad, 0.0023, 0,
    );

    let mut all_ok = true;

    for n in [1_usize, 2, 4, 8] {
        let par = parallel_sym(100.0, 0.67, branch_angle_rad, 0.01, n);
        all_ok &= check(&format!("symmetric   N={n}"), seq_sym.clone(), par);
    }

    for n in [1_usize, 2, 4, 8] {
        let par = parallel_asym(100.0, 0.67, 0.57, left_angle_rad, right_angle_rad, 0.0023, n);
        all_ok &= check(&format!("asymmetric  N={n}"), seq_asym.clone(), par);
    }

    println!();
    if all_ok {
        println!("All checks passed.");
    } else {
        eprintln!("One or more checks FAILED.");
        std::process::exit(1);
    }

    Ok(())
}
