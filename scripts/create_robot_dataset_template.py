#!/usr/bin/env python3
"""Create a tiny synthetic robot-data layout for validating the E005 tooling."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def make_points(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    background = rng.uniform(low=[-12, -8, -1.5, 0.05], high=[20, 8, 1.5, 0.8], size=(900, 4))
    obstacle = rng.normal(loc=[5.0, 1.0, 0.8, 0.7], scale=[0.8, 0.5, 0.6, 0.1], size=(180, 4))
    return np.vstack((background, obstacle)).astype(np.float32)


def main() -> None:
    args = parse_args()
    root = args.output_dir
    if root.exists() and any(root.iterdir()) and not args.overwrite:
        raise SystemExit(f"Output directory is not empty: {root}. Use --overwrite to replace its files.")

    for directory in (root / "raw_bin", root / "points", root / "labels", root / "ImageSets"):
        directory.mkdir(parents=True, exist_ok=True)
    samples = {
        "000001": ["5.0 1.0 0.8 0.8 0.6 1.7 0.0 Pedestrian", "9.0 -2.0 0.6 1.4 0.9 1.2 0.2 Cart"],
        "000002": ["6.0 0.5 0.5 1.2 1.0 1.0 -0.1 Pallet", "11.0 3.0 0.4 0.4 0.4 0.7 0.0 Cone"],
    }
    for offset, (sample_id, labels) in enumerate(samples.items()):
        make_points(20260717 + offset).tofile(root / "raw_bin" / f"{sample_id}.bin")
        (root / "labels" / f"{sample_id}.txt").write_text("\n".join(labels) + "\n", encoding="utf-8")
    (root / "ImageSets" / "train.txt").write_text("000001\n", encoding="utf-8")
    (root / "ImageSets" / "val.txt").write_text("000002\n", encoding="utf-8")
    (root / "README.md").write_text(
        "# E005 synthetic interface sample\n\n"
        "This directory contains generated test data only. It is not real robot data and must not be used for training metrics.\n"
        "Run convert_robot_points.py on raw_bin/ before validation.\n",
        encoding="utf-8",
    )
    print(f"Created synthetic E005 template in {root}")


if __name__ == "__main__":
    main()
