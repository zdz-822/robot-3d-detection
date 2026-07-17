#!/usr/bin/env bash
set -euo pipefail

project_dir="${1:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
image_name="${IMAGE_NAME:-robot-3d-detection:ros2-humble}"
ros_domain_id="${ROS_DOMAIN_ID:-0}"
wait_seconds="${DISCOVERY_WAIT_SEC:-10}"
report_dir="$project_dir/data/g1_probe"
timestamp="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$report_dir"
docker run --rm --network host \
  -e "ROS_DOMAIN_ID=$ros_domain_id" \
  -v "$project_dir:/workspace/project" \
  "$image_name" \
  bash -lc "source /opt/ros/humble/setup.bash && cd /workspace/project/ros2_ws && colcon build --symlink-install && source install/setup.bash && ros2 run robot_3d_detection ros2_interface_probe --ros-args -p discovery_wait_sec:=$wait_seconds" 2>&1 \
  | tee "$report_dir/g1_ros_interface_$timestamp.txt"
