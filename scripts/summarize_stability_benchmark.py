"""Summarize repeated ROS 2 temporal detector replay logs without extra packages."""

import csv
import re
import statistics
import sys
from pathlib import Path


DETECTION_PATTERN = re.compile(
    r"Published (?P<count>\d+) detections; end-to-end detector latency "
    r"(?P<latency>[0-9.]+) ms"
)


def percentile(values, percent):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def format_ms(value):
    return "-" if value is None else f"{value:.1f} ms"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: summarize_stability_benchmark.py RESULT_DIR")

    result_dir = Path(sys.argv[1])
    run_times = {}
    with (result_dir / "run_times.csv").open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            run_times[int(row["run"])] = {
                "exit_code": int(row["exit_code"]),
                "wall_time_sec": float(row["wall_time_sec"]),
            }

    runs = []
    all_latencies = []
    steady_latencies = []
    all_targets = []
    for log_path in sorted(result_dir.glob("run_*.log")):
        run_id = int(log_path.stem.split("_")[1])
        matches = [
            (int(match.group("count")), float(match.group("latency")))
            for match in DETECTION_PATTERN.finditer(log_path.read_text(encoding="utf-8", errors="replace"))
        ]
        latencies = [latency for _, latency in matches]
        targets = [count for count, _ in matches]
        replay_complete = "Replay complete" in log_path.read_text(encoding="utf-8", errors="replace")
        success = run_times[run_id]["exit_code"] == 0 and replay_complete and len(matches) == 10
        runs.append({
            "id": run_id,
            "success": success,
            "detections": len(matches),
            "targets": targets,
            "latencies": latencies,
            **run_times[run_id],
        })
        all_latencies.extend(latencies)
        steady_latencies.extend(latencies[1:])
        all_targets.extend(targets)

    successful_runs = sum(run["success"] for run in runs)
    lines = [
        "# E009: 连续回放稳定性与延迟评测",
        "",
        "## 配置",
        "",
        "- 输入：nuScenes v1.0-mini 同一连续场景的 12 帧 LiDAR 与位姿回放。",
        "- 模型：E002 PointPillars 三帧时序融合，RTX 4060 Laptop GPU。",
        "- 判定：每轮应在前 2 帧缓存后产生 10 帧检测，并出现 `Replay complete`。",
        "- 延迟范围：节点内点云解析、三帧对齐、模型推理、NMS 与消息构造；不包含真实雷达传输与 DDS 网络传输。",
        "",
        "## 汇总结果",
        "",
        f"- 完整轮次：`{successful_runs}/{len(runs)}`。",
        f"- 检测发布帧数：`{sum(run['detections'] for run in runs)}`，每轮期望 `10` 帧。",
        f"- 全部检测延迟 P50 / P95 / 最大值：`{format_ms(percentile(all_latencies, 50))}` / `{format_ms(percentile(all_latencies, 95))}` / `{format_ms(max(all_latencies) if all_latencies else None)}`。",
        f"- 排除每轮首次 CUDA 预热后的稳定延迟 P50 / P95 / 最大值：`{format_ms(percentile(steady_latencies, 50))}` / `{format_ms(percentile(steady_latencies, 95))}` / `{format_ms(max(steady_latencies) if steady_latencies else None)}`。",
        f"- 每帧平均检测目标数：`{statistics.mean(all_targets):.1f}`。" if all_targets else "- 每帧平均检测目标数：`-`。",
        "",
        "## 分轮结果",
        "",
        "| 轮次 | 完整结束 | 检测帧数 | 平均目标数 | 首次延迟 | 稳定延迟均值 | 墙钟时间 |",
        "| ---: | :---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in runs:
        first_latency = run["latencies"][0] if run["latencies"] else None
        stable = run["latencies"][1:]
        target_mean = statistics.mean(run["targets"]) if run["targets"] else None
        lines.append(
            f"| {run['id']} | {'通过' if run['success'] else '未通过'} | {run['detections']} | "
            f"{'-' if target_mean is None else f'{target_mean:.1f}'} | {format_ms(first_latency)} | "
            f"{format_ms(statistics.mean(stable) if stable else None)} | {run['wall_time_sec']:.0f} s |"
        )
    lines.extend([
        "",
        "## 结论",
        "",
        "本评测验证的是固定 nuScenes mini 回放场景上的软件链路稳定性，不代表真实 G1 雷达的精度、网络延迟或长期可靠性。真实上机前仍需采集机器人数据并重复同类评测。",
    ])
    (result_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
