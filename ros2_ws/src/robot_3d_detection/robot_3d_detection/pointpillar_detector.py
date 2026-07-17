"""Run the one-sweep PointPillars model on PointCloud2 messages."""

import math
import os
from pathlib import Path

import numpy as np
import rclpy
from geometry_msgs.msg import Quaternion
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from vision_msgs.msg import Detection3D, Detection3DArray, ObjectHypothesisWithPose

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets import DatasetTemplate
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils


def yaw_to_quaternion(yaw):
    return Quaternion(x=0.0, y=0.0, z=math.sin(yaw / 2.0), w=math.cos(yaw / 2.0))


class PointPillarsDetector(Node):
    def __init__(self):
        super().__init__("pointpillar_detector")
        self.declare_parameter("cfg_file", "")
        self.declare_parameter("ckpt", "")
        self.declare_parameter("input_topic", "/lidar/points")
        self.declare_parameter("output_topic", "/perception/detections")
        self.declare_parameter("score_threshold", 0.35)

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
        self.publisher = self.create_publisher(Detection3DArray, self.get_parameter("output_topic").value, 10)
        self.subscription = self.create_subscription(PointCloud2, self.get_parameter("input_topic").value, self.on_pointcloud, 10)
        self.get_logger().info(
            f"Detector is ready: {self.get_parameter('input_topic').value} -> "
            f"{self.get_parameter('output_topic').value}"
        )

    def on_pointcloud(self, message):
        raw = np.frombuffer(message.data, dtype=np.float32).reshape(-1, message.point_step // 4)
        # The deployed baseline is one-sweep, so every current-frame point has timestamp zero.
        points = np.column_stack((raw[:, :4], np.zeros(len(raw), dtype=np.float32)))
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
