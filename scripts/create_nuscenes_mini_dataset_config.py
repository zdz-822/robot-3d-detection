#!/usr/bin/env python3
"""Create the complete one-sweep nuScenes-mini dataset config OpenPCDet needs."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    args = parser.parse_args()

    config_dir = args.source_dir / "tools" / "cfgs" / "dataset_configs"
    source = config_dir / "nuscenes_dataset.yaml"
    target = config_dir / "nuscenes_mini_dataset.yaml"
    with source.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    config["VERSION"] = "v1.0-mini"
    config["MAX_SWEEPS"] = 1
    config["INFO_PATH"] = {
        "train": ["nuscenes_infos_1sweeps_train.pkl"],
        "test": ["nuscenes_infos_1sweeps_val.pkl"],
    }

    aug_list = deepcopy(config["DATA_AUGMENTOR"]["AUG_CONFIG_LIST"])
    for aug in aug_list:
        if aug.get("NAME") == "gt_sampling":
            aug["DB_INFO_PATH"] = ["nuscenes_dbinfos_1sweeps_withvelo.pkl"]
    config["DATA_AUGMENTOR"]["AUG_CONFIG_LIST"] = aug_list

    with target.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
