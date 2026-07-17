#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"
project_dir="${2:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
image_name="${IMAGE_NAME:-robot-3d-detection:ros2-humble}"
checkpoint="$source_dir/output/nuscenes_models/pointpillar_nuscenes_mini_3sweeps/default/ckpt/checkpoint_epoch_10.pth"
container_checkpoint="/workspace/OpenPCDet/output/nuscenes_models/pointpillar_nuscenes_mini_3sweeps/default/ckpt/checkpoint_epoch_10.pth"

points_topic="${POINTS_TOPIC:-/lidar/points}"
odom_topic="${ODOM_TOPIC:-/odom}"
ros_domain_id="${ROS_DOMAIN_ID:-0}"
lidar_x="${LIDAR_X:-0.0}"
lidar_y="${LIDAR_Y:-0.0}"
lidar_z="${LIDAR_Z:-0.0}"
lidar_roll="${LIDAR_ROLL:-0.0}"
lidar_pitch="${LIDAR_PITCH:-0.0}"
lidar_yaw="${LIDAR_YAW:-0.0}"

if [[ ! -f "$checkpoint" ]]; then
  echo "E002 checkpoint is missing: $checkpoint" >&2
  exit 1
fi

docker run --rm --network host --gpus all --ipc=host --shm-size=8g \
  -e "ROS_DOMAIN_ID=$ros_domain_id" \
  -v "$source_dir:/workspace/OpenPCDet" \
  -v "$project_dir:/workspace/project" \
  "$image_name" \
  bash -lc "source /opt/ros/humble/setup.bash && python /workspace/project/scripts/patch_openpcdet_optional_datasets.py /workspace/OpenPCDet && python /workspace/project/scripts/patch_openpcdet_numpy_compat.py /workspace/OpenPCDet && python /workspace/project/scripts/create_nuscenes_temporal_config.py /workspace/OpenPCDet --max-sweeps 3 && export PYTHONPATH=/workspace/OpenPCDet && cd /workspace/project/ros2_ws && colcon build --symlink-install && source install/setup.bash && ros2 launch robot_3d_detection g1_temporal_detector.launch.py points_topic:=$points_topic odom_topic:=$odom_topic cfg_file:=/workspace/OpenPCDet/tools/cfgs/nuscenes_models/pointpillar_nuscenes_mini_3sweeps.yaml ckpt:=$container_checkpoint lidar_x:=$lidar_x lidar_y:=$lidar_y lidar_z:=$lidar_z lidar_roll:=$lidar_roll lidar_pitch:=$lidar_pitch lidar_yaw:=$lidar_yaw"
