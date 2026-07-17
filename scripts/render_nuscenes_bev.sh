#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"
dataset_dir="${2:-$HOME/datasets/nuscenes}"
project_dir="${3:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
output_dir="${4:-$project_dir/artifacts/e003_bev}"
image_name="${IMAGE_NAME:-robot-3d-detection:cuda12.1}"
max_sweeps="${MAX_SWEEPS:-3}"
num_frames="${NUM_FRAMES:-12}"
score_threshold="${SCORE_THRESHOLD:-0.35}"
checkpoint="$source_dir/output/nuscenes_models/pointpillar_nuscenes_mini_${max_sweeps}sweeps/default/ckpt/checkpoint_epoch_10.pth"

if [[ ! -f "$checkpoint" ]]; then
  echo "Checkpoint is missing: $checkpoint" >&2
  exit 1
fi

mkdir -p "$output_dir"

docker run --rm --gpus all --ipc=host --shm-size=8g \
  -v "$source_dir:/workspace/OpenPCDet" \
  -v "$dataset_dir:$dataset_dir" \
  -v "$project_dir:/workspace/project:ro" \
  -v "$output_dir:/workspace/output" \
  "$image_name" \
  bash -lc "python /workspace/project/scripts/patch_openpcdet_optional_datasets.py /workspace/OpenPCDet && python /workspace/project/scripts/patch_openpcdet_numpy_compat.py /workspace/OpenPCDet && python /workspace/project/scripts/create_nuscenes_temporal_config.py /workspace/OpenPCDet --max-sweeps $max_sweeps && export PYTHONPATH=/workspace/OpenPCDet && cd /workspace/OpenPCDet/tools && python /workspace/project/scripts/render_nuscenes_bev.py --cfg_file cfgs/nuscenes_models/pointpillar_nuscenes_mini_${max_sweeps}sweeps.yaml --ckpt /workspace/OpenPCDet/output/nuscenes_models/pointpillar_nuscenes_mini_${max_sweeps}sweeps/default/ckpt/checkpoint_epoch_10.pth --output_dir /workspace/output --num_frames $num_frames --score_threshold $score_threshold"
