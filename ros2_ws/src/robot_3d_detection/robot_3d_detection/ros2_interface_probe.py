"""Discover LiDAR and pose topics exposed by a robot on the current ROS 2 domain."""

import json
import os

import rclpy
from rclpy.node import Node


TOPIC_TYPES = {
    "pointcloud_topics": "sensor_msgs/msg/PointCloud2",
    "odometry_topics": "nav_msgs/msg/Odometry",
    "pose_topics": "geometry_msgs/msg/PoseStamped",
    "tf_topics": "tf2_msgs/msg/TFMessage",
}


class Ros2InterfaceProbe(Node):
    def __init__(self):
        super().__init__("ros2_interface_probe")
        self.declare_parameter("discovery_wait_sec", 10)
        self.timer = self.create_timer(float(self.get_parameter("discovery_wait_sec").value), self.report_once)

    def report_once(self):
        self.timer.cancel()
        report = {key: [] for key in TOPIC_TYPES}
        for topic_name, topic_types in self.get_topic_names_and_types():
            for key, expected_type in TOPIC_TYPES.items():
                if expected_type in topic_types:
                    report[key].append(topic_name)
        report["ros_domain_id"] = os.environ.get("ROS_DOMAIN_ID", "0")
        self.get_logger().info("G1 interface report: " + json.dumps(report, ensure_ascii=False, sort_keys=True))
        raise SystemExit(0)


def main():
    rclpy.init()
    node = Ros2InterfaceProbe()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
