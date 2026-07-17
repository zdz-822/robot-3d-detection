#!/usr/bin/env bash
set -euo pipefail

project_dir="${1:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
image_name="${IMAGE_NAME:-robot-3d-detection:ros2-humble}"
points_topic="${POINTS_TOPIC:-/lidar/points}"
odom_topic="${ODOM_TOPIC:-/odom}"
ros_domain_id="${ROS_DOMAIN_ID:-0}"
timestamp="$(date +%Y%m%d-%H%M%S)"
output_dir="$project_dir/data/g1_bags/$timestamp"

mkdir -p "$output_dir"
echo "Recording $points_topic and $odom_topic. Press Ctrl+C to stop."
docker run --rm --network host \
  -e "ROS_DOMAIN_ID=$ros_domain_id" \
  -v "$output_dir:/workspace/output" \
  "$image_name" \
  bash -lc "source /opt/ros/humble/setup.bash && ros2 bag record -o /workspace/output $points_topic $odom_topic /tf /tf_static"
