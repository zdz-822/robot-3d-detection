#!/usr/bin/env python3
"""Render a short BEV detection sequence from the nuScenes mini validation split."""

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets import build_dataloader
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils


CLASS_COLORS = {
    "car": "#ff6b35",
    "truck": "#f7b801",
    "construction_vehicle": "#d95d39",
    "bus": "#6d9dc5",
    "trailer": "#9d4edd",
    "barrier": "#8d99ae",
    "motorcycle": "#ef476f",
    "bicycle": "#06d6a0",
    "pedestrian": "#ffd166",
    "traffic_cone": "#f4a261",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cfg_file", required=True, help="OpenPCDet model config")
    parser.add_argument("--ckpt", required=True, help="trained checkpoint")
    parser.add_argument("--output_dir", required=True, help="directory for PNG and GIF outputs")
    parser.add_argument("--num_frames", type=int, default=12, help="number of consecutive frames")
    parser.add_argument("--score_threshold", type=float, default=0.35, help="minimum prediction score")
    parser.add_argument("--max_predictions", type=int, default=30, help="max boxes drawn per frame")
    parser.add_argument("--gif_fps", type=float, default=3.0, help="GIF playback speed")
    return parser.parse_args()


def box_corners(box):
    """Return the four BEV corners of an OpenPCDet box [x, y, z, dx, dy, dz, heading]."""
    x, y, _, dx, dy, _, heading = box[:7]
    corners = np.array(
        [[dx / 2, dy / 2], [dx / 2, -dy / 2], [-dx / 2, -dy / 2], [-dx / 2, dy / 2], [dx / 2, dy / 2]],
        dtype=np.float32,
    )
    rotation = np.array(
        [[math.cos(heading), -math.sin(heading)], [math.sin(heading), math.cos(heading)]], dtype=np.float32
    )
    return corners @ rotation.T + np.array([x, y], dtype=np.float32)


def draw_box(ax, box, color, label=None, linewidth=1.7, linestyle="-"):
    corners = box_corners(box)
    ax.plot(corners[:, 0], corners[:, 1], color=color, linewidth=linewidth, linestyle=linestyle)
    front = corners[:2].mean(axis=0)
    center = np.asarray(box[:2])
    ax.plot([center[0], front[0]], [center[1], front[1]], color=color, linewidth=linewidth)
    if label:
        ax.text(
            center[0], center[1], label, color=color, fontsize=7, ha="center", va="center",
            bbox={"facecolor": "#101820", "alpha": 0.72, "edgecolor": "none", "pad": 1.2},
        )


def filter_ground_truth(info, point_cloud_range):
    boxes = np.asarray(info.get("gt_boxes", np.empty((0, 7))), dtype=np.float32)
    names = np.asarray(info.get("gt_names", []))
    if boxes.size == 0:
        return boxes.reshape(0, 7), names
    mask = (
        (boxes[:, 0] >= point_cloud_range[0])
        & (boxes[:, 0] <= point_cloud_range[3])
        & (boxes[:, 1] >= point_cloud_range[1])
        & (boxes[:, 1] <= point_cloud_range[4])
    )
    return boxes[mask], names[mask]


def find_scene_indices(dataset, count):
    """Use nuScenes sample links so animation frames come from one uninterrupted scene."""
    from nuscenes.nuscenes import NuScenes

    nusc = NuScenes(version=dataset.dataset_cfg.VERSION, dataroot=str(dataset.root_path), verbose=False)
    index_by_token = {info["token"]: index for index, info in enumerate(dataset.infos)}
    first_token = dataset.infos[0]["token"]
    sample = nusc.get("sample", first_token)
    while sample["prev"]:
        sample = nusc.get("sample", sample["prev"])

    indices = []
    while sample and len(indices) < count:
        index = index_by_token.get(sample["token"])
        if index is not None:
            indices.append(index)
        next_token = sample["next"]
        sample = nusc.get("sample", next_token) if next_token else None

    if len(indices) < count:
        raise RuntimeError(f"Only found {len(indices)} consecutive validation frames, expected {count}")
    return indices


def render_frame(output_path, frame_number, total_frames, points, gt_boxes, gt_names, pred_boxes, pred_scores, pred_labels, class_names, score_threshold, max_predictions, point_cloud_range):
    fig, ax = plt.subplots(figsize=(10, 10), dpi=150, facecolor="#101820")
    ax.set_facecolor("#101820")

    # Timestamp is zero for the current sweep and negative for older sweeps.
    max_points = 35000
    if len(points) > max_points:
        point_indices = np.linspace(0, len(points) - 1, max_points, dtype=np.int64)
        points = points[point_indices]
    timestamps = points[:, 4] if points.shape[1] > 4 else np.zeros(len(points))
    ax.scatter(points[:, 0], points[:, 1], c=timestamps, cmap="Blues", s=0.45, alpha=0.48, linewidths=0)

    for box in gt_boxes:
        draw_box(ax, box, "#42e8e0", linewidth=1.25, linestyle="--")

    keep = np.flatnonzero(pred_scores >= score_threshold)
    keep = keep[np.argsort(pred_scores[keep])[::-1][:max_predictions]]
    for index in keep:
        class_name = class_names[int(pred_labels[index]) - 1]
        color = CLASS_COLORS.get(class_name, "#ffffff")
        draw_box(ax, pred_boxes[index], color, label=f"{class_name} {pred_scores[index]:.2f}")

    ax.scatter([0], [0], marker="^", s=90, color="#ffffff", edgecolor="#101820", zorder=5)
    ax.set_xlim(point_cloud_range[0], point_cloud_range[3])
    ax.set_ylim(point_cloud_range[1], point_cloud_range[4])
    ax.set_aspect("equal")
    ax.grid(color="#39505e", alpha=0.35, linewidth=0.5)
    ax.tick_params(colors="#b9c7cf")
    for spine in ax.spines.values():
        spine.set_color("#54717f")
    ax.set_xlabel("Forward / x (m)", color="#dce7eb")
    ax.set_ylabel("Left / y (m)", color="#dce7eb")
    ax.set_title(
        f"E003 | Multi-sweep LiDAR 3D Detection | Frame {frame_number}/{total_frames}",
        color="#ffffff", fontsize=13, pad=12,
    )
    ax.plot([], [], color="#42e8e0", linewidth=1.25, linestyle="--", label="Ground-truth 3D box")
    legend = ax.legend(loc="upper left", frameon=True, facecolor="#101820", edgecolor="#54717f", fontsize=8)
    for text in legend.get_texts():
        text.set_color("#dce7eb")
    fig.text(0.5, 0.016, "Dashed cyan: ground truth | Solid color: prediction | Triangle: robot", ha="center", color="#dce7eb", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(output_path, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    args = parse_args()
    cfg_from_yaml_file(args.cfg_file, cfg)
    cfg.TAG = Path(args.cfg_file).stem
    cfg.EXP_GROUP_PATH = "/".join(args.cfg_file.split("/")[1:-1])
    logger = common_utils.create_logger()
    output_dir = Path(args.output_dir)
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    dataset, _, _ = build_dataloader(
        dataset_cfg=cfg.DATA_CONFIG,
        class_names=cfg.CLASS_NAMES,
        batch_size=1,
        dist=False,
        workers=0,
        logger=logger,
        training=False,
    )
    model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=dataset)
    model.load_params_from_file(filename=args.ckpt, logger=logger, to_cpu=True)
    model.cuda()
    model.eval()

    frame_indices = find_scene_indices(dataset, args.num_frames)
    point_cloud_range = np.asarray(cfg.DATA_CONFIG.POINT_CLOUD_RANGE, dtype=np.float32)
    manifest = {"checkpoint": args.ckpt, "score_threshold": args.score_threshold, "frames": []}

    with torch.no_grad():
        for sequence_index, dataset_index in enumerate(frame_indices, start=1):
            data_dict = dataset[dataset_index]
            points = data_dict["points"].copy()
            info = dataset.infos[dataset_index]
            gt_boxes, gt_names = filter_ground_truth(info, point_cloud_range)
            batch_dict = dataset.collate_batch([data_dict])
            load_data_to_gpu(batch_dict)
            pred_dicts, _ = model.forward(batch_dict)
            prediction = pred_dicts[0]

            pred_boxes = prediction["pred_boxes"].cpu().numpy()
            pred_scores = prediction["pred_scores"].cpu().numpy()
            pred_labels = prediction["pred_labels"].cpu().numpy()
            frame_path = frames_dir / f"frame_{sequence_index:03d}.png"
            render_frame(
                frame_path, sequence_index, len(frame_indices), points, gt_boxes, gt_names,
                pred_boxes, pred_scores, pred_labels, cfg.CLASS_NAMES, args.score_threshold,
                args.max_predictions, point_cloud_range,
            )
            manifest["frames"].append({
                "sequence_index": sequence_index,
                "frame_id": str(data_dict["frame_id"]),
                "token": info["token"],
                "predictions_drawn": int(np.sum(pred_scores >= args.score_threshold)),
            })
            logger.info("Rendered frame %d/%d: %s", sequence_index, len(frame_indices), frame_path)

    images = [Image.open(path).convert("RGB") for path in sorted(frames_dir.glob("frame_*.png"))]
    images[0].save(output_dir / "e003_multisweep_detection.gif", save_all=True, append_images=images[1:], duration=round(1000 / args.gif_fps), loop=0)
    for image in images:
        image.close()
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info("Wrote GIF and %d frame images to %s", len(frame_indices), output_dir)


if __name__ == "__main__":
    main()
