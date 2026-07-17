#!/usr/bin/env bash
set -euo pipefail

container_id="${1:?pass the active training container id}"
checkpoint="$HOME/projects/robot-3d-detection/OpenPCDet/output/nuscenes_models/pointpillar_nuscenes_mini_3sweeps/default/ckpt/checkpoint_epoch_10.pth"
project_script="/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection/scripts/eval_nuscenes_temporal.sh"

# Training writes the final checkpoint before Docker removes its container.
while docker inspect -f '{{.State.Running}}' "$container_id" 2>/dev/null | grep -q true; do
  sleep 60
done

until [[ -f "$checkpoint" ]]; do
  sleep 30
done

exec env MAX_SWEEPS=3 bash "$project_script"
