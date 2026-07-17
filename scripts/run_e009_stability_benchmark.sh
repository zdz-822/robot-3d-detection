#!/usr/bin/env bash
set -euo pipefail

runs="${1:-3}"
source_dir="${2:-$HOME/projects/robot-3d-detection/OpenPCDet}"
dataset_dir="${3:-$HOME/datasets/nuscenes}"
project_dir="${4:-/mnt/c/Users/TR/Documents/Codex/2026-07-15/new-chat/robot-3d-detection}"

if ! [[ "$runs" =~ ^[1-9][0-9]*$ ]]; then
  echo "runs must be a positive integer" >&2
  exit 2
fi

result_dir="$project_dir/artifacts/e009_stability/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$result_dir"
printf 'run,exit_code,wall_time_sec\n' > "$result_dir/run_times.csv"

for run in $(seq 1 "$runs"); do
  log_file="$result_dir/run_$(printf '%02d' "$run").log"
  echo "[E009] Starting run $run/$runs"
  started_at=$(date +%s)
  set +e
  bash "$project_dir/scripts/run_g1_sensor_sim.sh" "$source_dir" "$dataset_dir" "$project_dir" > "$log_file" 2>&1
  exit_code=$?
  set -e
  elapsed=$(( $(date +%s) - started_at ))
  printf '%s,%s,%s\n' "$run" "$exit_code" "$elapsed" >> "$result_dir/run_times.csv"
  echo "[E009] Run $run finished with exit code $exit_code in ${elapsed}s"
done

python3 "$project_dir/scripts/summarize_stability_benchmark.py" "$result_dir"
echo "[E009] Report written to $result_dir/report.md"
