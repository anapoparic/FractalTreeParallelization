# Code Analysis

## Hey there, can you analyze my existing code and give me a review:

- Is the implementation good?
- Can the implementation be better?
- Can I somehow improve my code? (make it cleaner, more optimal, etc.)
- Is something redundant?

---

## Existing Code

Before we start with the real Python implementation — you can find shared functions inside the [utils file](../FractalTreeParallelization/python/utils.py).

You can find the **Python sequential version (symetric fractal tree)** inside this file: [Python sequential symetric](../FractalTreeParallelization/python/sequential.py) — rate this implementation, and if you see possible improvements, suggest them.

You can find the **Python sequential version (asymmetric fractal tree)** inside this file: [Python sequential asymmetric](../FractalTreeParallelization/python/sequential_asymmetric.py) — rate this implementation, and if you see possible improvements, suggest them.

Before we move on to the Rust implementation — you can find shared functions in the [lib file](../FractalTreeParallelization/rust/src/lib.rs).

You can find the **Rust sequential version (symetric fractal tree)** inside this file: [Rust sequential symetric](../FractalTreeParallelization/rust/src/sequential.rs) — rate this implementation, and if you see possible improvements, suggest them.

You can find the **Rust sequential version (asymmetric fractal tree)** inside this file: [Rust sequential asymmetric](../FractalTreeParallelization/rust/src/sequential_asymmetric.rs) — rate this implementation, and if you see possible improvements, suggest them.

Now that you've analyzed the Python and Rust sequential versions, compare them and explain **what is worth mentioning when presenting this work**. Why is this project a good base for a thesis? What do we observe in this analysis? What are the conclusions?

Let's move on to the parallel versions.

First, analyze the **Python parallel version (symetric fractal tree)**: [Python parallel symetric](../FractalTreeParallelization/python/parallel.py) — rate this implementation, suggest improvements if any, and compare it with the Python sequential version, marking only the important conclusions.

First, analyze the **Python parallel version (asymmetric fractal tree)**: [Python parallel asymmetric](../FractalTreeParallelization/python/parallel_asymmetric.py) — rate this implementation, suggest improvements if any, and compare it with the Python sequential version, marking only the important conclusions.

Second, analyze the **Rust parallel version (symetric fractal tree)**: [Rust parallel symetric](../FractalTreeParallelization/rust/src/parallel.rs) — rate this implementation, suggest improvements if any, and compare it with the Rust sequential version, marking only the important conclusions.

Second, analyze the **Rust parallel version (asymmetric fractal tree)**: [Rust parallel asymmetric](../FractalTreeParallelization/rust/src/parallel_asymmetric.rs) — rate this implementation, suggest improvements if any, and compare it with the Rust sequential version, marking only the important conclusions.

---

## Experiments & Scaling Analysis

Now that you've seen the main logic, we can move on to experiments and Amdahl's and Gustafson's analysis. Take a look at the following experiment files:

### 1. Python Experiments

**Strong Scaling**

- [1 core](../FractalTreeParallelization/python/experiments/strong/1.py)
- [2 cores](../FractalTreeParallelization/python/experiments/strong/2.py)
- [4 cores](../FractalTreeParallelization/python/experiments/strong/4.py)
- [8 cores](../FractalTreeParallelization/python/experiments/strong/8.py)

**Weak Scaling**

- [1 core](../FractalTreeParallelization/python/experiments/weak/1.py)
- [2 cores](../FractalTreeParallelization/python/experiments/weak/2.py)
- [4 cores](../FractalTreeParallelization/python/experiments/weak/4.py)
- [8 cores](../FractalTreeParallelization/python/experiments/weak/8.py)

### 2. Rust Experiments

**Strong Scaling**

- [1 core](../FractalTreeParallelization/rust/experiments/strong/1.rs)
- [2 cores](../FractalTreeParallelization/rust/experiments/strong/2.rs)
- [4 cores](../FractalTreeParallelization/rust/experiments/strong/4.rs)
- [8 cores](../FractalTreeParallelization/rust/experiments/strong/8.rs)

**Weak Scaling**

- [1 core](../FractalTreeParallelization/rust/experiments/weak/1.rs)
- [2 cores](../FractalTreeParallelization/rust/experiments/weak/2.rs)
- [4 cores](../FractalTreeParallelization/rust/experiments/weak/4.rs)
- [8 cores](../FractalTreeParallelization/rust/experiments/weak/8.rs)

---

## Graphs & Report

Now that you understand the experiments, analyze the files used to generate the graphs and report:

- [run_experiments](../FractalTreeParallelization/scripts/run_experiments.py)
- [generate_graphs](../FractalTreeParallelization/scripts/generate_graphs.py)
- [report](../FractalTreeParallelization/report.md)
