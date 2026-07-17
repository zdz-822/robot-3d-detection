#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"
image_name="${IMAGE_NAME:-robot-3d-detection:cuda12.1}"

if [[ ! -f "$source_dir/setup.py" ]]; then
  echo "OpenPCDet source is missing: $source_dir" >&2
  exit 1
fi

docker run --rm --gpus all --ipc=host \
  -e TORCH_CUDA_ARCH_LIST=8.9 \
  -e MAX_JOBS=2 \
  -v "$source_dir:/workspace/OpenPCDet" \
  "$image_name" \
  bash -lc 'python setup.py build_ext --inplace'
