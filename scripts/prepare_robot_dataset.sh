#!/usr/bin/env bash
set -euo pipefail

project_dir="${1:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
data_root="${2:-$project_dir/data/custom}"
image_name="${IMAGE_NAME:-robot-3d-detection:cuda12.1}"

if [[ ! -d "$data_root" ]]; then
  echo "Dataset directory is missing: $data_root" >&2
  exit 1
fi

docker run --rm \
  -v "$project_dir:/workspace/project:ro" \
  -v "$data_root:/workspace/data" \
  "$image_name" \
  bash -lc "python /workspace/project/scripts/validate_robot_dataset.py --data-root /workspace/data --report /workspace/data/validation_report.json && python /workspace/project/scripts/create_robot_dataset_infos.py --data-root /workspace/data"
