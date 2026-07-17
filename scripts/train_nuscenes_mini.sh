#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"
dataset_dir="${2:-$HOME/datasets/nuscenes}"
project_dir="${3:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
image_name="${IMAGE_NAME:-robot-3d-detection:cuda12.1}"

if [[ ! -f "$dataset_dir/openpcdet/v1.0-mini/nuscenes_infos_1sweeps_train.pkl" ]]; then
  echo "nuScenes mini infos are missing. Run prepare_nuscenes_mini.sh first." >&2
  exit 1
fi

docker run --rm --gpus all --ipc=host --shm-size=8g \
  -v "$source_dir:/workspace/OpenPCDet" \
  -v "$dataset_dir:$dataset_dir" \
  -v "$project_dir:/workspace/project:ro" \
  "$image_name" \
  bash -lc 'python /workspace/project/scripts/patch_openpcdet_optional_datasets.py /workspace/OpenPCDet && python /workspace/project/scripts/patch_openpcdet_numpy_compat.py /workspace/OpenPCDet && export PYTHONPATH=/workspace/OpenPCDet; python /workspace/project/scripts/create_nuscenes_mini_config.py /workspace/OpenPCDet && cd /workspace/OpenPCDet/tools && python train.py --cfg_file cfgs/nuscenes_models/pointpillar_nuscenes_mini.yaml --batch_size 2 --workers 4'
