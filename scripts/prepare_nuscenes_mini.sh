#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"
dataset_dir="${2:-$HOME/datasets/nuscenes}"
project_dir="${3:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
image_name="${IMAGE_NAME:-robot-3d-detection:cuda12.1}"
layout_root="$dataset_dir/openpcdet"
layout_version_dir="$layout_root/v1.0-mini"

for path in "$source_dir/setup.py" "$dataset_dir/v1.0-mini/sample.json" "$dataset_dir/samples/LIDAR_TOP" "$dataset_dir/sweeps/LIDAR_TOP"; do
  if [[ ! -e "$path" ]]; then
    echo "Required path is missing: $path" >&2
    exit 1
  fi
done

mkdir -p "$layout_version_dir"
for entry in samples sweeps maps v1.0-mini; do
  ln -sfn "$dataset_dir/$entry" "$layout_version_dir/$entry"
done
ln -sfn "$layout_root" "$source_dir/data/nuscenes"

docker run --rm --gpus all --ipc=host \
  -v "$source_dir:/workspace/OpenPCDet" \
  -v "$dataset_dir:$dataset_dir" \
  -v "$project_dir:/workspace/project:ro" \
  "$image_name" \
  bash -lc 'python /workspace/project/scripts/patch_openpcdet_optional_datasets.py /workspace/OpenPCDet && python /workspace/project/scripts/create_nuscenes_mini_dataset_config.py /workspace/OpenPCDet && export PYTHONPATH=/workspace/OpenPCDet; cd /workspace/OpenPCDet/tools && python -m pcdet.datasets.nuscenes.nuscenes_dataset --func create_nuscenes_infos --cfg_file cfgs/dataset_configs/nuscenes_mini_dataset.yaml --version v1.0-mini'
