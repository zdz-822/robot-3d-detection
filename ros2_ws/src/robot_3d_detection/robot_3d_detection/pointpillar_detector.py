"""Run the one-sweep PointPillars model on PointCloud2 messages."""

import math
import os
from pathlib import Path

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped, Quaternion
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from vision_msgs.msg import Detection3D, Detection3DArray, ObjectHypothesisWithPose

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets import DatasetTemplate
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils


def yaw_to_quaternion(yaw):
    return Quaternion(x=0.0, y=0.0, z=math.sin(yaw / 2.0), w=math.cos(yaw / 2.0))


def stamp_to_seconds(stamp):
    return stamp.sec + stamp.nanosec * 1e-9


def pose_to_matrix(message):
    pose = message.pose
    x, y, z, w = pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w
    rotation = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float32)
    transform = np.eye(4, dtype=np.float32)
    transform[:3, :3] = rotation
    transform[:3, 3] = [pose.position.x, pose.position.y, pose.position.z]
    return transform


def pointcloud_to_xyzi(message):
    """Read common PointCloud2 layouts without assuming a fixed point stride."""
    fields = {field.name: field for field in message.fields}
    required = ("x", "y", "z")
    if any(name not in fields for name in required):
        raise ValueError("PointCloud2 must contain x, y, and z float32 fields")
    intensity_name = next((name for name in ("intensity", "reflectivity", "i") if name in fields), None)
    selected = list(required) + ([intensity_name] if intensity_name else [])
    for name in selected:
        if fields[name].datatype != PointField.FLOAT32:
            raise ValueError(f"PointCloud2 field {name} must use FLOAT32")
    dtype = np.dtype({
        "names": selected,
        "formats": ["<f4"] * len(selected),
        "offsets": [fields[name].offset for name in selected],
        "itemsize": message.point_step,
    })
    records = np.frombuffer(message.data, dtype=dtype, count=message.width * message.height)
    intensity = records[intensity_name] if intensity_name else np.ones(len(records), dtype=np.float32)
    return np.column_stack((records["x"], records["y"], records["z"], intensity)).astype(np.float32, copy=False)


class PointPillarsDetector(Node):
    def __init__(self):
        super().__init__("pointpillar_detector")
        self.declare_parameter("cfg_file", "")
        self.declare_parameter("ckpt", "")
        self.declare_parameter("input_topic", "/lidar/points")
        self.declare_parameter("output_topic", "/perception/detections")
        self.declare_parameter("score_threshold", 0.35)
        self.declare_parameter("temporal_sweeps", 1)
        self.declare_parameter("pose_topic", "/lidar/pose")

        cfg_file = Path(self.get_parameter("cfg_file").value)
        checkpoint = Path(self.get_parameter("ckpt").value)
        if not cfg_file.is_file() or not checkpoint.is_file():
            raise FileNotFoundError("PointPillars config or checkpoint is missing")
        # OpenPCDet model configs reference their dataset config from tools/.
        previous_dir = Path.cwd()
        os.chdir(cfg_file.parents[2])
        try:
            cfg_from_yaml_file(str(cfg_file), cfg)
        finally:
            os.chdir(previous_dir)
        logger = common_utils.create_logger()
        self.dataset = DatasetTemplate(dataset_cfg=cfg.DATA_CONFIG, class_names=cfg.CLASS_NAMES, training=False, logger=logger)
        self.model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=self.dataset)
        self.model.load_params_from_file(filename=str(checkpoint), logger=logger, to_cpu=True)
        self.model.cuda()
        self.model.eval()
        self.class_names = cfg.CLASS_NAMES
        self.score_threshold = float(self.get_parameter("score_threshold").value)
        self.temporal_sweeps = int(self.get_parameter("temporal_sweeps").value)
        self.pose_by_stamp = {}
        self.pending_clouds = {}
        self.temporal_buffer = []
        self.publisher = self.create_publisher(Detection3DArray, self.get_parameter("output_topic").value, 10)
        self.subscription = self.create_subscription(PointCloud2, self.get_parameter("input_topic").value, self.on_pointcloud, 10)
        self.pose_subscription = None
        if self.temporal_sweeps > 1:
            self.pose_subscription = self.create_subscription(
                PoseStamped, self.get_parameter("pose_topic").value, self.on_pose, 10
            )
        self.get_logger().info(
            f"Detector is ready with {self.temporal_sweeps} sweep(s): "
            f"{self.get_parameter('input_topic').value} -> {self.get_parameter('output_topic').value}"
        )

    @staticmethod
    def stamp_key(header):
        return header.stamp.sec, header.stamp.nanosec

    def on_pose(self, message):
        key = self.stamp_key(message.header)
        self.pose_by_stamp[key] = pose_to_matrix(message)
        cloud = self.pending_clouds.pop(key, None)
        if cloud is not None:
            self.process_pointcloud(cloud, self.pose_by_stamp[key])
        # Keep a bounded lookup in case DDS delivers pose before point cloud.
        while len(self.pose_by_stamp) > self.temporal_sweeps * 4:
            self.pose_by_stamp.pop(next(iter(self.pose_by_stamp)))

    def on_pointcloud(self, message):
        if self.temporal_sweeps > 1:
            pose = self.pose_by_stamp.get(self.stamp_key(message.header))
            if pose is None:
                self.pending_clouds[self.stamp_key(message.header)] = message
                return
            self.process_pointcloud(message, pose)
            return
        self.process_pointcloud(message, None)

    def process_pointcloud(self, message, global_from_lidar):
        raw = pointcloud_to_xyzi(message)
        if self.temporal_sweeps == 1:
            points = np.column_stack((raw, np.zeros(len(raw), dtype=np.float32)))
        else:
            self.temporal_buffer.append((raw.copy(), global_from_lidar, stamp_to_seconds(message.header.stamp)))
            self.temporal_buffer = self.temporal_buffer[-self.temporal_sweeps:]
            if len(self.temporal_buffer) < self.temporal_sweeps:
                self.get_logger().info(f"Buffering temporal scans: {len(self.temporal_buffer)}/{self.temporal_sweeps}")
                return
            points = self.fuse_temporal_points()
        data_dict = self.dataset.prepare_data({"points": points, "frame_id": message.header.stamp.sec})
        batch_dict = self.dataset.collate_batch([data_dict])
        load_data_to_gpu(batch_dict)

        import torch

        with torch.no_grad():
            prediction, _ = self.model.forward(batch_dict)
        boxes = prediction[0]["pred_boxes"].detach().cpu().numpy()
        scores = prediction[0]["pred_scores"].detach().cpu().numpy()
        labels = prediction[0]["pred_labels"].detach().cpu().numpy()
        result = Detection3DArray()
        result.header = message.header
        for box, score, label in zip(boxes, scores, labels):
            if score < self.score_threshold:
                continue
            detection = Detection3D()
            detection.header = message.header
            hypothesis = ObjectHypothesisWithPose()
            hypothesis.hypothesis.class_id = self.class_names[int(label) - 1]
            hypothesis.hypothesis.score = float(score)
            detection.results.append(hypothesis)
            detection.bbox.center.position.x = float(box[0])
            detection.bbox.center.position.y = float(box[1])
            detection.bbox.center.position.z = float(box[2])
            detection.bbox.center.orientation = yaw_to_quaternion(float(box[6]))
            detection.bbox.size.x = float(box[3])
            detection.bbox.size.y = float(box[4])
            detection.bbox.size.z = float(box[5])
            result.detections.append(detection)
        self.publisher.publish(result)
        self.get_logger().info(f"Published {len(result.detections)} detections")

    def fuse_temporal_points(self):
        """Align buffered LiDAR frames to the latest LiDAR pose and append time lag."""
        _, current_global_from_lidar, current_time = self.temporal_buffer[-1]
        current_lidar_from_global = np.linalg.inv(current_global_from_lidar)
        fused = []
        for points, global_from_lidar, point_time in self.temporal_buffer:
            current_from_frame = current_lidar_from_global @ global_from_lidar
            aligned_xyz = points[:, :3] @ current_from_frame[:3, :3].T + current_from_frame[:3, 3]
            time_lag = np.full((len(points), 1), point_time - current_time, dtype=np.float32)
            fused.append(np.column_stack((aligned_xyz, points[:, 3], time_lag)))
        return np.concatenate(fused, axis=0).astype(np.float32, copy=False)


def main():
    rclpy.init()
    node = PointPillarsDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
