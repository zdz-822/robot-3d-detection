#!/usr/bin/env bash
set -euo pipefail

project_dir="${1:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
image_name="${IMAGE_NAME:-robot-3d-detection:ros2-humble}"

docker build -f "$project_dir/docker/Dockerfile.ros2" -t "$image_name" "$project_dir"
