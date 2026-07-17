#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"
dataset_dir="${2:-$HOME/datasets/nuscenes}"
project_dir="${3:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"
image_name="${IMAGE_NAME:-robot-3d-detection:ros2-humble}"
checkpoint="$source_dir/output/nuscenes_models/pointpillar_nuscenes_mini_3sweeps/default/ckpt/checkpoint_epoch_10.pth"
container_checkpoint="/workspace/OpenPCDet/output/nuscenes_models/pointpillar_nuscenes_mini_3sweeps/default/ckpt/checkpoint_epoch_10.pth"
manifest="$project_dir/artifacts/e003_bev/manifest.json"

for path in "$checkpoint" "$manifest" "$dataset_dir/samples/LIDAR_TOP" "$dataset_dir/v1.0-mini/sample.json"; do
  if [[ ! -e "$path" ]]; then
    echo "Required path is missing: $path" >&2
    exit 1
  fi
done

# WSLg forwards the Linux GUI window to Windows. The simulator and RViz stay in one container.
docker run --rm --gpus all --ipc=host --shm-size=8g \
  -e DISPLAY -e WAYLAND_DISPLAY -e XDG_RUNTIME_DIR \
  -v /mnt/wslg:/mnt/wslg \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$source_dir:/workspace/OpenPCDet" \
  -v "$dataset_dir:$dataset_dir:ro" \
  -v "$project_dir:/workspace/project" \
  "$image_name" \
  bash -lc "source /opt/ros/humble/setup.bash && \
    python /workspace/project/scripts/patch_openpcdet_optional_datasets.py /workspace/OpenPCDet && \
    python /workspace/project/scripts/patch_openpcdet_numpy_compat.py /workspace/OpenPCDet && \
    python /workspace/project/scripts/create_nuscenes_temporal_config.py /workspace/OpenPCDet --max-sweeps 3 && \
    export PYTHONPATH=/workspace/OpenPCDet && \
    cd /workspace/project/ros2_ws && \
    colcon build --symlink-install && \
    source install/setup.bash; \
    ros2 launch robot_3d_detection g1_sensor_sim.launch.py \
      data_root:=$dataset_dir \
      manifest:=/workspace/project/artifacts/e003_bev/manifest.json \
      cfg_file:=/workspace/OpenPCDet/tools/cfgs/nuscenes_models/pointpillar_nuscenes_mini_3sweeps.yaml \
      ckpt:=$container_checkpoint & \
    sim_pid=\$!; trap 'kill \$sim_pid 2>/dev/null || true' EXIT; \
    rviz2 -d /workspace/project/configs/g1_sensor_sim.rviz"
