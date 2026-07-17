#!/usr/bin/env python3
"""Convert raw XYZI float32 point clouds into OpenPCDet custom-dataset arrays."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert .bin XYZI point clouds to float32 [N, 4] .npy files."
    )
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing .bin frames")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for converted .npy frames")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output files")
    parser.add_argument("--dry-run", action="store_true", help="Validate files without writing output")
    return parser.parse_args()


def convert_frame(source: Path, destination: Path, overwrite: bool, dry_run: bool) -> int:
    points = np.fromfile(source, dtype=np.float32)
    if points.size == 0:
        raise ValueError(f"Empty point cloud: {source}")
    if points.size % 4 != 0:
        raise ValueError(
            f"Point cloud must contain x, y, z, intensity float32 values: {source}"
        )

    points = points.reshape(-1, 4)
    if not np.isfinite(points).all():
        raise ValueError(f"Point cloud contains NaN or infinity: {source}")

    if destination.exists() and not overwrite:
        raise FileExistsError(f"Output exists, use --overwrite to replace it: {destination}")

    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        np.save(destination, points)
    return len(points)


def main() -> None:
    args = parse_args()
    if not args.input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {args.input_dir}")

    frames = sorted(args.input_dir.glob("*.bin"))
    if not frames:
        raise SystemExit(f"No .bin files found in: {args.input_dir}")

    point_count = 0
    for source in frames:
        destination = args.output_dir / f"{source.stem}.npy"
        point_count += convert_frame(source, destination, args.overwrite, args.dry_run)

    mode = "validated" if args.dry_run else "converted"
    print(f"{mode} {len(frames)} frames with {point_count} points in total")


if __name__ == "__main__":
    main()
