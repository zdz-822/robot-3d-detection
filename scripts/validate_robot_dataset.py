#!/usr/bin/env python3
"""Validate the point clouds, labels, and sequence splits for robot 3D detection."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np


DEFAULT_CLASSES = ("Pedestrian", "Cart", "Pallet", "Cone")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--classes", nargs="+", default=DEFAULT_CLASSES)
    parser.add_argument("--report", type=Path, help="Optional JSON validation report")
    return parser.parse_args()


def read_split(path: Path) -> list[str]:
    if not path.is_file():
        raise ValueError(f"Missing split file: {path}")
    sample_ids = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not sample_ids:
        raise ValueError(f"Split is empty: {path}")
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError(f"Split contains duplicate IDs: {path}")
    return sample_ids


def validate_label(path: Path, allowed_classes: set[str]) -> Counter:
    if not path.is_file():
        raise ValueError(f"Missing label file: {path}")
    counts: Counter = Counter()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 8:
            raise ValueError(f"{path}:{line_number} must contain 7 box values and one class name")
        try:
            x, y, z, dx, dy, dz, yaw = (float(value) for value in fields[:7])
        except ValueError as error:
            raise ValueError(f"{path}:{line_number} contains a non-numeric box value") from error
        if not all(math.isfinite(value) for value in (x, y, z, dx, dy, dz, yaw)):
            raise ValueError(f"{path}:{line_number} contains NaN or infinity")
        if min(dx, dy, dz) <= 0:
            raise ValueError(f"{path}:{line_number} has a non-positive box size")
        if not -math.pi <= yaw <= math.pi:
            raise ValueError(f"{path}:{line_number} yaw must be within [-pi, pi]")
        if fields[7] not in allowed_classes:
            raise ValueError(f"{path}:{line_number} has unknown class {fields[7]!r}")
        counts[fields[7]] += 1
    return counts


def validate_points(path: Path) -> int:
    if not path.is_file():
        raise ValueError(f"Missing converted point cloud: {path}")
    points = np.load(path)
    if points.dtype != np.float32 or points.ndim != 2 or points.shape[1] != 4 or len(points) == 0:
        raise ValueError(f"{path} must be a non-empty float32[N, 4] array")
    if not np.isfinite(points).all():
        raise ValueError(f"{path} contains NaN or infinity")
    return len(points)


def main() -> None:
    args = parse_args()
    root = args.data_root
    allowed_classes = set(args.classes)
    train_ids = read_split(root / "ImageSets" / "train.txt")
    val_ids = read_split(root / "ImageSets" / "val.txt")
    overlap = set(train_ids) & set(val_ids)
    if overlap:
        raise SystemExit(f"Train/val splits overlap: {sorted(overlap)}")

    class_counts: Counter = Counter()
    point_count = 0
    for sample_id in train_ids + val_ids:
        point_count += validate_points(root / "points" / f"{sample_id}.npy")
        class_counts.update(validate_label(root / "labels" / f"{sample_id}.txt", allowed_classes))

    report = {
        "data_root": str(root),
        "train_frames": len(train_ids),
        "val_frames": len(val_ids),
        "total_points": point_count,
        "class_counts": dict(sorted(class_counts.items())),
        "classes_without_boxes": sorted(allowed_classes - set(class_counts)),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
