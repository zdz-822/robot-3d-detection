#!/usr/bin/env python3
"""Generate OpenPCDet configs for a multi-sweep nuScenes-mini experiment."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

import yaml


def configure_dataset(config: dict, max_sweeps: int) -> dict:
    config["VERSION"] = "v1.0-mini"
    config["MAX_SWEEPS"] = max_sweeps
    config["INFO_PATH"] = {
        "train": [f"nuscenes_infos_{max_sweeps}sweeps_train.pkl"],
        "test": [f"nuscenes_infos_{max_sweeps}sweeps_val.pkl"],
    }
    aug_list = deepcopy(config["DATA_AUGMENTOR"]["AUG_CONFIG_LIST"])
    for aug in aug_list:
        if aug.get("NAME") == "gt_sampling":
            aug["DB_INFO_PATH"] = [f"nuscenes_dbinfos_{max_sweeps}sweeps_withvelo.pkl"]
    config["DATA_AUGMENTOR"]["AUG_CONFIG_LIST"] = aug_list
    return config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--max-sweeps", type=int, default=3)
    args = parser.parse_args()
    if args.max_sweeps < 2:
        raise SystemExit("Temporal experiment requires at least 2 sweeps")

    dataset_dir = args.source_dir / "tools" / "cfgs" / "dataset_configs"
    model_dir = args.source_dir / "tools" / "cfgs" / "nuscenes_models"
    dataset_source = dataset_dir / "nuscenes_dataset.yaml"
    model_source = model_dir / "cbgs_pp_multihead.yaml"

    with dataset_source.open("r", encoding="utf-8") as handle:
        dataset_config = configure_dataset(yaml.safe_load(handle), args.max_sweeps)
    dataset_target = dataset_dir / f"nuscenes_mini_{args.max_sweeps}sweeps.yaml"
    with dataset_target.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(dataset_config, handle, sort_keys=False)

    with model_source.open("r", encoding="utf-8") as handle:
        model_config = yaml.safe_load(handle)
    data_config = model_config["DATA_CONFIG"]
    data_config["VERSION"] = "v1.0-mini"
    data_config["MAX_SWEEPS"] = args.max_sweeps
    data_config["INFO_PATH"] = dataset_config["INFO_PATH"]
    data_config["DATA_AUGMENTOR"] = dataset_config["DATA_AUGMENTOR"]
    model_config["OPTIMIZATION"]["BATCH_SIZE_PER_GPU"] = 2
    model_config["OPTIMIZATION"]["NUM_EPOCHS"] = 10
    model_target = model_dir / f"pointpillar_nuscenes_mini_{args.max_sweeps}sweeps.yaml"
    with model_target.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(model_config, handle, sort_keys=False)

    print(f"Wrote {dataset_target}")
    print(f"Wrote {model_target}")


if __name__ == "__main__":
    main()
