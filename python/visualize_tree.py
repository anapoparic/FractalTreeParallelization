"""
Fractal Tree Visualizer (matplotlib)
======================================
Generates and renders the asymmetric fractal tree used in the implementation.
Uses LineCollection to draw all branches at once — handles millions of branches.

Output: data/asymmetric_tree.png

Usage: python python/visualize_tree.py
"""
import math
import os
import time

import matplotlib.pyplot as plt
import matplotlib.collections as mc
import numpy as np

from sequential_asymmetric import generate_fractal_tree_asymmetric

# Parameters matching the implementation
TRUNK_LENGTH = 100.0
LEFT_RATIO   = 0.67
RIGHT_RATIO  = 0.57
LEFT_ANGLE   = 35.0
RIGHT_ANGLE  = 25.0
MIN_LENGTH   = 0.01

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'asymmetric_tree.png')


def main():
    print("Generating branches...")
    t0 = time.perf_counter()

    branches = generate_fractal_tree_asymmetric(
        0, 0, TRUNK_LENGTH, math.pi / 2,
        LEFT_RATIO, RIGHT_RATIO,
        math.radians(LEFT_ANGLE), math.radians(RIGHT_ANGLE),
        MIN_LENGTH
    )

    t1 = time.perf_counter()
    print(f"  {len(branches):,} branches in {t1 - t0:.2f}s")

    print("Rendering...")
    arr = np.array(branches, dtype=np.float32)

    segments = np.stack([arr[:, :2], arr[:, 2:4]], axis=1)
    depths   = arr[:, 4]

    # Colour: trunk = dark purple, tips = bright pink/white
    colors = plt.cm.RdPu(depths / depths.max())

    # Thicker lines near trunk, thinner at tips
    max_d = depths.max()
    linewidths = np.clip(1.5 * (1 - depths / max_d), 0.15, 1.5)

    fig, ax = plt.subplots(figsize=(12, 14), facecolor='#0f0f14')
    ax.set_facecolor('#0f0f14')

    lc = mc.LineCollection(segments, colors=colors, linewidths=linewidths, alpha=0.9)
    ax.add_collection(lc)
    ax.autoscale()
    ax.set_aspect('equal')
    ax.axis('off')

    ax.set_title(
        f'Asymmetric Fractal Tree  |  '
        f'L_ratio={LEFT_RATIO}  R_ratio={RIGHT_RATIO}  '
        f'L_angle={LEFT_ANGLE}°  R_angle={RIGHT_ANGLE}°  |  '
        f'{len(branches):,} branches',
        color='#cccccc', fontsize=11, pad=12
    )

    t2 = time.perf_counter()
    print(f"  Rendered in {t2 - t1:.2f}s")
    plt.show()


if __name__ == '__main__':
    main()
