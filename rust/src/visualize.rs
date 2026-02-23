use fractal_tree::{generate_fractal_tree, save_result, FractalResult, Parameters};
use plotters::prelude::*;
use serde::Deserialize;
use std::f64::consts::PI;
use std::{error::Error, fs, path::PathBuf};

const TRUNK_LENGTH: f64 = 100.0;
const RATIO: f64 = 0.67;
const BRANCH_ANGLE_DEG: f64 = 30.0;
const MIN_LENGTH: f64 = 2.0;

const IMG_W: u32 = 900;
const IMG_H: u32 = 900;
const BG: RGBColor = RGBColor(15, 15, 20);

#[derive(Deserialize)]
struct VisIteration {
    iteration: usize,
    branch_count: usize,
    branches: Vec<[f64; 4]>,
}

#[derive(Deserialize)]
struct VisResult {
    max_depth: usize,
    total_branches: usize,
    iterations: Vec<VisIteration>,
}

fn main() -> Result<(), Box<dyn Error>> {
    println!("=== Fractal Tree Visualizer ===");
    println!(
        "Parameters: trunk={}, ratio={}, angle={}°, min_length={}",
        TRUNK_LENGTH, RATIO, BRANCH_ANGLE_DEG, MIN_LENGTH
    );

    // Step 1: Generate and save JSON
    let json_path = generate_and_save()?;

    // Step 2: Read the saved JSON
    println!("\nReading: {}", json_path.display());
    let json_str = fs::read_to_string(&json_path)?;
    let data: VisResult = serde_json::from_str(&json_str)?;
    println!(
        "Loaded: {} branches, {} iterations (max depth {})",
        data.total_branches,
        data.iterations.len(),
        data.max_depth
    );

    // Step 3: Compute bounds from the final (complete) iteration
    let bounds = data
        .iterations
        .last()
        .map(|it| compute_bounds(&it.branches))
        .unwrap_or((-120.0, 120.0, -10.0, 120.0));

    // Step 4: Generate one PNG per iteration
    let out_dir =
        PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../data/output/frames"));
    fs::create_dir_all(&out_dir)?;
    println!(
        "\nSaving {} frames to: {}\n",
        data.iterations.len(),
        out_dir.display()
    );

    for iter in &data.iterations {
        let path = out_dir.join(format!("frame_{:03}.png", iter.iteration));
        draw_frame(
            path.to_str().unwrap(),
            &iter.branches,
            bounds,
            iter.iteration,
            data.max_depth,
        )?;
        println!(
            "  frame_{:03}.png  ({} branches)",
            iter.iteration, iter.branch_count
        );
    }

    println!("\nDone! {} frames saved.", data.iterations.len());
    Ok(())
}

/// Generate fractal tree with MIN_LENGTH, save to JSON, return path.
fn generate_and_save() -> Result<PathBuf, Box<dyn Error>> {
    let angle_rad = BRANCH_ANGLE_DEG.to_radians();
    let branches =
        generate_fractal_tree(0.0, 0.0, TRUNK_LENGTH, PI / 2.0, RATIO, angle_rad, MIN_LENGTH, 0);
    let max_depth = branches.iter().map(|b| b.depth).max().unwrap_or(0);

    println!(
        "Generated: {} branches, max depth {}",
        branches.len(),
        max_depth
    );

    let mut result = FractalResult {
        parameters: Parameters {
            trunk_length: TRUNK_LENGTH,
            ratio: RATIO,
            branch_angle: BRANCH_ANGLE_DEG,
            min_length: MIN_LENGTH,
        },
        execution_time: 0.0,
        total_branches: branches.len(),
        max_depth,
        iterations: Vec::new(),
    };

    let filename = "visualization.json";
    save_result(&mut result, &[branches], filename)?;

    Ok(PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../data/output")).join(filename))
}

fn compute_bounds(branches: &[[f64; 4]]) -> (f64, f64, f64, f64) {
    let (mut xmin, mut xmax, mut ymin, mut ymax) =
        (f64::MAX, f64::MIN, f64::MAX, f64::MIN);
    for b in branches {
        xmin = xmin.min(b[0]).min(b[2]);
        xmax = xmax.max(b[0]).max(b[2]);
        ymin = ymin.min(b[1]).min(b[3]);
        ymax = ymax.max(b[1]).max(b[3]);
    }
    let xm = (xmax - xmin) * 0.06;
    let ym = (ymax - ymin) * 0.06;
    (xmin - xm, xmax + xm, ymin - ym, ymax + ym)
}

fn branch_color(b: &[f64; 4]) -> RGBColor {
    let len = ((b[2] - b[0]).powi(2) + (b[3] - b[1]).powi(2)).sqrt();
    let t = (1.0 - len / TRUNK_LENGTH).clamp(0.0, 1.0);
    RGBColor(
        lerp(139.0, 180.0, t) as u8,
        lerp(90.0, 220.0, t) as u8,
        lerp(43.0, 100.0, t) as u8,
    )
}

fn lerp(a: f64, b: f64, t: f64) -> f64 {
    a + (b - a) * t
}

fn draw_frame(
    path: &str,
    branches: &[[f64; 4]],
    (xmin, xmax, ymin, ymax): (f64, f64, f64, f64),
    depth: usize,
    max_depth: usize,
) -> Result<(), Box<dyn Error>> {
    let root = BitMapBackend::new(path, (IMG_W, IMG_H)).into_drawing_area();
    root.fill(&BG)?;

    let mut chart = ChartBuilder::on(&root)
        .margin(30)
        .caption(
            format!("Fractal Tree  |  Iteration {}/{}", depth, max_depth),
            ("sans-serif", 18)
                .into_font()
                .color(&RGBColor(190, 190, 190)),
        )
        .build_cartesian_2d(xmin..xmax, ymin..ymax)?;

    chart.configure_mesh().disable_mesh().draw()?;

    chart.draw_series(branches.iter().map(|b| {
        PathElement::new(vec![(b[0], b[1]), (b[2], b[3])], branch_color(b))
    }))?;

    root.present()?;
    Ok(())
}
