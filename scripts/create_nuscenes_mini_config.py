#!/usr/bin/env python3
"""Create a one-sweep nuScenes-mini PointPillars config from OpenPCDet's baseline."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path, help="OpenPCDet source root")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_dir = args.source_dir / "tools" / "cfgs" / "nuscenes_models"
    source = config_dir / "cbgs_pp_multihead.yaml"
    target = config_dir / "pointpillar_nuscenes_mini.yaml"
    dataset_base = args.source_dir / "tools" / "cfgs" / "dataset_configs" / "nuscenes_dataset.yaml"

    with source.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    with dataset_base.open("r", encoding="utf-8") as handle:
        dataset_config = yaml.safe_load(handle)

    data_config = config["DATA_CONFIG"]
    data_config["VERSION"] = "v1.0-mini"
    data_config["MAX_SWEEPS"] = 1
    data_config["INFO_PATH"] = {
        "train": ["nuscenes_infos_1sweeps_train.pkl"],
        "test": ["nuscenes_infos_1sweeps_val.pkl"],
    }

    # Keep the official augmentation settings but point them at the one-sweep database.
    aug_list = deepcopy(dataset_config["DATA_AUGMENTOR"]["AUG_CONFIG_LIST"])
    for aug in aug_list:
        if aug.get("NAME") == "gt_sampling":
            aug["DB_INFO_PATH"] = ["nuscenes_dbinfos_1sweeps_withvelo.pkl"]
    if aug_list:
        data_config["DATA_AUGMENTOR"] = {"AUG_CONFIG_LIST": aug_list}

    config["OPTIMIZATION"]["BATCH_SIZE_PER_GPU"] = 2
    config["OPTIMIZATION"]["NUM_EPOCHS"] = 10

    with target.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
