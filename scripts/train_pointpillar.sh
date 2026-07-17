#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"
batch_size="${BATCH_SIZE:-2}"
workers="${WORKERS:-4}"
config="tools/cfgs/kitti_models/pointpillar.yaml"

if [[ ! -f "$source_dir/$config" ]]; then
  echo "PointPillars config is missing. Check OpenPCDet source: $source_dir" >&2
  exit 1
fi

cd "$source_dir"
python tools/train.py --cfg_file "$config" --batch_size "$batch_size" --workers "$workers"
