# Idea for extending the thesis

#### Hey there, i was working on this project in past month. Project topic is Fractal Tree parallelization in Rust and Python - comparison of these two languages for this specific problem - using Amdahls's and Gustafson's law. You can understand what is fractal tree - running visualization of fractal tree in file [visualization](../FractalTreeParallelization/python/tree-visualization.py).

## VERY IMPORTANT TO KNOW

### I need to represent this project to my professor and discuss with him about extending the same for my thesis. Before you suggest any idea - have on my mind that i will represent those ideas to my professor, so ideas must be technically feasible.

#### Can you analyze my project?

- You can start from [README](../FractalTreeParallelization/README.md) - this is the base idea of university project, rate complexity of this idea on scale 1-5 for thesis.
- Before we start with real Python implementation - you can find shared functions inside [utils file](../FractalTreeParallelization/python/utils.py)
- You can find **Python sequential version** inside this file [Python sequential](../FractalTreeParallelization/python/sequential.py) - rate this implementation, if you see possible improvements - suggest them
- Before we move on Rust implementation - you can find shared functions in [lib file](../FractalTreeParallelization/rust/src/lib.rs)
- You can find **Rust sequential version** inside file [Rust sequential](../FractalTreeParallelization/rust/src/sequential.rs) - rate this implementation, if you see possible improvements - suggest them
- Now when you analyzed Python and Rust sequential version, compare them, explain **what is worth mentioning in presenting this work**. Why is this project good base for thesis? What do we observe in this analysis? What are conclusions?
- Let's move on parallel versions.
- First analyze **Python parallel version** [Python parallel](../FractalTreeParallelization/python/parallel.py) - rate this implementation, if you see possible improvements - suggest them. Compare Python sequential version with parallel, mark only important conclusions
- Second - analyze **Rust parallel version** [Rust parallel](../FractalTreeParallelization/rust/src/parallel.rs) - rate this implementation, if you see possible improvements - suggest them. Compare Rust sequential version with parallel and mark only important conclusions

#### You have seen my main logic, now we can move on experiments and Amdahl's and Gustafson's analysis. Take a look on next experiment's files:

- 1. **Python experiments**
  - Strong scaling
    - [1 core experiment](../FractalTreeParallelization/python/experiments/strong/1.py)
    - [2 cores experiment](../FractalTreeParallelization/python/experiments/strong/2.py)
    - [4 cores experiment](../FractalTreeParallelization/python/experiments/strong/4.py)
    - [8 cores experiment](../FractalTreeParallelization/python/experiments/strong/8.py)
  - Weak scaling
    - [1 core experiment](../FractalTreeParallelization/python/experiments/weak/1.py)
    - [2 cores experiment](../FractalTreeParallelization/python/experiments/weak/2.py)
    - [4 cores experiment](../FractalTreeParallelization/python/experiments/weak/4.py)
    - [8 cores experiment](../FractalTreeParallelization/python/experiments/weak/8.py)
- 2. **Rust experiments**
  - Strong scaling
    - [1 core experiment](../FractalTreeParallelization/rust/experiments/strong/1.rs)
    - [2 cores experiment](../FractalTreeParallelization/rust/experiments/strong/2.rs)
    - [4 cores experiment](../FractalTreeParallelization/rust/experiments/strong/4.rs)
    - [8 cores experiment](../FractalTreeParallelization/rust/experiments/strong/8.rs)
  - Weak scaling
    - [1 core experiment](../FractalTreeParallelization/rust/experiments/weak/1.rs)
    - [2 cores experiment](../FractalTreeParallelization/rust/experiments/weak/2.rs)
    - [4 cores experiment](../FractalTreeParallelization/rust/experiments/weak/4.rs)
    - [8 cores experiment](../FractalTreeParallelization/rust/experiments/weak/8.rs)

- Give me concise description - why we used those experiments, what they tell us, what is so important in those experiments for my thesis? What should i mark as very important in discussion with my professor?

#### Last one, but not least important is my [report](../FractalTreeParallelization/report.md). Analyze this report, please, and tell me what do you think about it?

#### Now, that you're all set, give me your best and honest opinion about my work - is this project good? Can it be better? What is complexity of this project? Should it be extended? If it should, what are best ideas for extending (one little idea is - same implementation but in Golang, but it's backup plan if there is nothing more intersting)?
