# Concrete Plan for Bachelor's Thesis

---

## Phase 1 — Asymmetric Tree Experiments (mandatory)

This is a direct copy of the structure you already have for the symmetric tree. You need to create:

**Python experiments** (`python/experiments/asymmetric/strong/` and `weak/`)

- 1, 2, 4, 8 cores — same pattern as `python/experiments/strong/1.py`

**Rust experiments** (`rust/experiments/asymmetric/strong/` and `weak/`)

- 1, 2, 4, 8 threads — same pattern as `rust/experiments/strong/1.rs`

**Result:** Speedup graphs for the asymmetric tree, Amdahl + Gustafson analysis.

---

## Phase 2 — Symmetric vs. Asymmetric Comparison (mandatory)

Run both tree types with the same total number of branches (tune parameters to make them comparable) and demonstrate:

- Does the symmetric or asymmetric tree scale better?
- Why? (unbalanced workload in the asymmetric case)

This is a new analysis not currently present in `report.md`.

---

## Phase 3 — Variable Parameter Experiments (mandatory per proposal)

Instead of varying the number of cores, keep the core count fixed (e.g. 4) and vary:

| Parameter       | Test Values        |
| --------------- | ------------------ |
| Tree depth      | 8, 10, 12, 14, 16  |
| Branching angle | 15°, 30°, 45°, 60° |
| Reduction ratio | 0.5, 0.6, 0.7, 0.8 |

**Research question:** How does the tree structure affect parallelization efficiency?

---

## Phase 4 — Theoretical Model (the 5/5 differentiator)

Derive a formula for the number of branches at depth `d` for the asymmetric tree:

- **Symmetric:** `N(d) = 2^d` while `length * ratio^d >= min_length`
- **Asymmetric:** not as straightforward, since the left and right branches have different ratios

Specifically: derive `d_max_left` and `d_max_right` — the maximum depth of the left and right sides — and from that analytically compute the total number of branches. Then:

1. Compute `p = parallel_portion / total` theoretically
2. Compare against empirically measured speedup
3. Show where theory and practice diverge, and explain why

This is an **original contribution** that no one else has.

---

## Phase 5 — Work-Stealing Instrumentation (optional, but very strong)

Add load imbalance measurement — how much work each worker actually does:

**Python:** in the `_worker` function, measure the number of branches each worker generated and save it alongside the timing.

**Rust:** Rayon doesn't give direct per-thread stats, but you can use `std::sync::atomic::AtomicUsize` counters per task.

Then show in a graph:

- **Symmetric tree:** all workers do approximately the same amount of work
- **Asymmetric tree:** Python has significant imbalance; Rust corrects it via work-stealing

---

- **Phases 1–3** are the minimum for a solid thesis.
- **Phase 4** is what separates _good_ from _excellent_.
- **Phase 5** is the bonus that backs up theory with empirical evidence.

---

## For a 5/5 Grade — `generate_graphs.py` Improvements

Currently the graphs only display the raw speedup from the data. For the thesis, you should add:

**Load imbalance graph:** for each task, measure the number of branches generated and show the distribution (box plot or histogram) — symmetric vs. asymmetric tree, Python vs. Rust.

**Parametric analysis graph:** a new chart type where the x-axis is not the number of cores but the `left_ratio / right_ratio` ratio, and the y-axis is speedup.
