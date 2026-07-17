#!/usr/bin/env python3
"""Create OpenPCDet CustomDataset info files from validated robot labels."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    return parser.parse_args()


def read_infos(root: Path, split: str) -> list[dict]:
    sample_ids = [line.strip() for line in (root / "ImageSets" / f"{split}.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    infos = []
    for sample_id in sample_ids:
        boxes, names = [], []
        for line in (root / "labels" / f"{sample_id}.txt").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            fields = line.split()
            boxes.append([float(value) for value in fields[:7]])
            names.append(fields[7])
        infos.append({
            "point_cloud": {"num_features": 4, "lidar_idx": sample_id},
            "annos": {
                "name": np.asarray(names),
                "gt_boxes_lidar": np.asarray(boxes, dtype=np.float32).reshape(-1, 7),
            },
        })
    return infos


def main() -> None:
    args = parse_args()
    for split in ("train", "val"):
        infos = read_infos(args.data_root, split)
        destination = args.data_root / f"robot_infos_{split}.pkl"
        with destination.open("wb") as stream:
            pickle.dump(infos, stream)
        print(f"Wrote {len(infos)} {split} infos to {destination}")


if __name__ == "__main__":
    main()
