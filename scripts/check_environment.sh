#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"

echo "Python: $(python3 --version)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

if [[ ! -f "$source_dir/setup.py" ]]; then
  echo "OpenPCDet source is missing or incomplete: $source_dir" >&2
  exit 1
fi

echo "OpenPCDet source: $source_dir"
echo "Environment prerequisites are present. Build the CUDA 12.1 training image before installing or running OpenPCDet."
