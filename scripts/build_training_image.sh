#!/usr/bin/env bash
set -euo pipefail

project_dir="${1:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
image_name="${IMAGE_NAME:-robot-3d-detection:cuda12.1}"

docker build --tag "$image_name" --file "$project_dir/docker/Dockerfile" "$project_dir/docker"
echo "Training image built: $image_name"
