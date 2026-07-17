#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"
dataset_dir="${2:-$HOME/datasets/KITTI}"

if [[ ! -f "$source_dir/setup.py" ]]; then
  echo "OpenPCDet source is missing: $source_dir" >&2
  exit 1
fi

if [[ ! -d "$dataset_dir/training" || ! -d "$dataset_dir/testing" ]]; then
  echo "KITTI is incomplete. Expected training and testing under: $dataset_dir" >&2
  exit 1
fi

for split in training testing; do
  link_path="$source_dir/data/kitti/$split"
  if [[ -e "$link_path" && ! -L "$link_path" ]]; then
    echo "Refusing to replace a non-link path: $link_path" >&2
    exit 1
  fi
  ln -sfn "$dataset_dir/$split" "$link_path"
done

cd "$source_dir"
python -m pcdet.datasets.kitti.kitti_dataset create_kitti_infos tools/cfgs/dataset_configs/kitti_dataset.yaml
echo "KITTI metadata created successfully."
