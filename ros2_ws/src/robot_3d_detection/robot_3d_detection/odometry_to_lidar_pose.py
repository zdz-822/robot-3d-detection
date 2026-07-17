"""Convert robot base odometry into the global LiDAR pose needed for temporal fusion."""

import math

import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node


def quaternion_to_matrix(quaternion):
    x, y, z, w = quaternion.x, quaternion.y, quaternion.z, quaternion.w
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float32)


def matrix_to_quaternion(rotation):
    trace = np.trace(rotation)
    if trace > 0:
        scale = 2.0 * math.sqrt(trace + 1.0)
        return rotation[2, 1] - rotation[1, 2], rotation[0, 2] - rotation[2, 0], rotation[1, 0] - rotation[0, 1], 0.25 * scale
    index = int(np.argmax(np.diag(rotation)))
    next_index, last_index = (index + 1) % 3, (index + 2) % 3
    scale = 2.0 * math.sqrt(1.0 + rotation[index, index] - rotation[next_index, next_index] - rotation[last_index, last_index])
    values = [0.0, 0.0, 0.0, 0.0]
    values[index] = 0.25 * scale
    values[3] = (rotation[last_index, next_index] - rotation[next_index, last_index]) / scale
    values[next_index] = (rotation[next_index, index] + rotation[index, next_index]) / scale
    values[last_index] = (rotation[last_index, index] + rotation[index, last_index]) / scale
    return values[0], values[1], values[2], values[3]


class OdometryToLidarPose(Node):
    def __init__(self):
        super().__init__("odometry_to_lidar_pose")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("pose_topic", "/lidar/pose")
        for name in ("lidar_x", "lidar_y", "lidar_z", "lidar_roll", "lidar_pitch", "lidar_yaw"):
            self.declare_parameter(name, 0.0)
        self.base_from_lidar = self.make_static_transform()
        self.publisher = self.create_publisher(PoseStamped, self.get_parameter("pose_topic").value, 10)
        self.subscription = self.create_subscription(Odometry, self.get_parameter("odom_topic").value, self.on_odometry, 10)
        self.get_logger().info(
            f"Converting {self.get_parameter('odom_topic').value} to {self.get_parameter('pose_topic').value}; "
            "set lidar_x/y/z/roll/pitch/yaw to the measured base-from-lidar extrinsic."
        )

    def make_static_transform(self):
        roll, pitch, yaw = (float(self.get_parameter(name).value) for name in ("lidar_roll", "lidar_pitch", "lidar_yaw"))
        cx, sx, cy, sy, cz, sz = math.cos(roll), math.sin(roll), math.cos(pitch), math.sin(pitch), math.cos(yaw), math.sin(yaw)
        transform = np.eye(4, dtype=np.float32)
        transform[:3, :3] = [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx], [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx], [-sy, cy * sx, cy * cx]]
        transform[:3, 3] = [float(self.get_parameter(name).value) for name in ("lidar_x", "lidar_y", "lidar_z")]
        return transform

    def on_odometry(self, message):
        global_from_base = np.eye(4, dtype=np.float32)
        global_from_base[:3, :3] = quaternion_to_matrix(message.pose.pose.orientation)
        global_from_base[:3, 3] = [message.pose.pose.position.x, message.pose.pose.position.y, message.pose.pose.position.z]
        global_from_lidar = global_from_base @ self.base_from_lidar
        pose = PoseStamped()
        pose.header = message.header
        pose.pose.position.x, pose.pose.position.y, pose.pose.position.z = (float(value) for value in global_from_lidar[:3, 3])
        pose.pose.orientation.x, pose.pose.orientation.y, pose.pose.orientation.z, pose.pose.orientation.w = (
            float(value) for value in matrix_to_quaternion(global_from_lidar[:3, :3])
        )
        self.publisher.publish(pose)


def main():
    rclpy.init()
    node = OdometryToLidarPose()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
