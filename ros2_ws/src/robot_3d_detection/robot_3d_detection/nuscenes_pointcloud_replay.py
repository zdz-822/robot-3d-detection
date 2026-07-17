"""Publish a short nuScenes LiDAR sequence as ROS 2 PointCloud2 messages."""

import json
from pathlib import Path

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField


FIELDS = [
    PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
    PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
    PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
    PointField(name="intensity", offset=12, datatype=PointField.FLOAT32, count=1),
]


class NuScenesPointCloudReplay(Node):
    def __init__(self):
        super().__init__("nuscenes_pointcloud_replay")
        self.declare_parameter("data_root", "")
        self.declare_parameter("manifest", "")
        self.declare_parameter("topic", "/lidar/points")
        self.declare_parameter("period_sec", 0.5)
        self.declare_parameter("startup_delay_sec", 3.0)
        self.declare_parameter("publish_lidar_pose", False)
        self.declare_parameter("pose_topic", "/lidar/pose")
        self.declare_parameter("publish_odometry", False)
        self.declare_parameter("odom_topic", "/odom")
        data_root = Path(self.get_parameter("data_root").value)
        manifest_path = Path(self.get_parameter("manifest").value)
        if not data_root.exists() or not manifest_path.is_file():
            raise FileNotFoundError("data_root or E003 manifest is missing")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.frames = [{"path": data_root / "samples" / "LIDAR_TOP" / f"{frame['frame_id']}.bin", "token": frame["token"]} for frame in manifest["frames"]]
        self.frame_paths = [frame["path"] for frame in self.frames]
        missing_paths = [path for path in self.frame_paths if not path.is_file()]
        if missing_paths:
            raise FileNotFoundError(f"Replay frame is missing: {missing_paths[0]}")
        self.publisher = self.create_publisher(PointCloud2, self.get_parameter("topic").value, 10)
        self.publish_lidar_pose = bool(self.get_parameter("publish_lidar_pose").value)
        self.publish_odometry = bool(self.get_parameter("publish_odometry").value)
        self.pose_publisher = self.create_publisher(PoseStamped, self.get_parameter("pose_topic").value, 10)
        self.odom_publisher = self.create_publisher(Odometry, self.get_parameter("odom_topic").value, 10)
        if self.publish_lidar_pose or self.publish_odometry:
            self.load_lidar_poses(data_root)
        self.index = 0
        self.period_sec = float(self.get_parameter("period_sec").value)
        self.timer = self.create_timer(float(self.get_parameter("startup_delay_sec").value), self.start_replay)
        self.get_logger().info(
            f"Waiting for detector, then replaying {len(self.frame_paths)} nuScenes LiDAR frames on "
            f"{self.get_parameter('topic').value}"
        )

    def start_replay(self):
        self.timer.cancel()
        self.timer = self.create_timer(self.period_sec, self.publish_next)
        self.publish_next()

    def load_lidar_poses(self, data_root):
        """Attach a global-from-lidar transform to each replayed scan."""
        from nuscenes.nuscenes import NuScenes
        from pyquaternion import Quaternion

        nusc = NuScenes(version="v1.0-mini", dataroot=str(data_root), verbose=False)
        for frame in self.frames:
            sample = nusc.get("sample", frame["token"])
            sample_data = nusc.get("sample_data", sample["data"]["LIDAR_TOP"])
            ego_pose = nusc.get("ego_pose", sample_data["ego_pose_token"])
            calibrated_sensor = nusc.get("calibrated_sensor", sample_data["calibrated_sensor_token"])
            global_from_ego = Quaternion(ego_pose["rotation"]).transformation_matrix
            global_from_ego[:3, 3] = ego_pose["translation"]
            ego_from_lidar = Quaternion(calibrated_sensor["rotation"]).transformation_matrix
            ego_from_lidar[:3, 3] = calibrated_sensor["translation"]
            frame["global_from_lidar"] = global_from_ego @ ego_from_lidar

    def publish_next(self):
        if self.index >= len(self.frame_paths):
            self.get_logger().info("Replay complete")
            self.timer.cancel()
            raise SystemExit(0)

        frame = self.frames[self.index]
        raw_points = np.fromfile(frame["path"], dtype=np.float32).reshape(-1, 5)
        points = np.ascontiguousarray(raw_points[:, :4], dtype=np.float32)
        message = PointCloud2()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "lidar"
        message.height = 1
        message.width = len(points)
        message.fields = FIELDS
        message.is_bigendian = False
        message.point_step = 16
        message.row_step = message.point_step * message.width
        message.is_dense = True
        message.data = points.tobytes()
        if self.publish_lidar_pose or self.publish_odometry:
            pose = self.make_pose(message, frame["global_from_lidar"])
        if self.publish_lidar_pose:
            self.pose_publisher.publish(pose)
        if self.publish_odometry:
            odometry = Odometry()
            odometry.header = message.header
            odometry.child_frame_id = "base_link"
            odometry.pose.pose = pose.pose
            self.odom_publisher.publish(odometry)
        self.publisher.publish(message)
        self.get_logger().info(f"Published frame {self.index + 1}/{len(self.frame_paths)} ({len(points)} points)")
        self.index += 1

    @staticmethod
    def make_pose(pointcloud_message, global_from_lidar):
        from pyquaternion import Quaternion

        pose = PoseStamped()
        pose.header = pointcloud_message.header
        pose.pose.position.x, pose.pose.position.y, pose.pose.position.z = global_from_lidar[:3, 3]
        rotation = Quaternion(matrix=global_from_lidar[:3, :3])
        pose.pose.orientation.x = rotation.x
        pose.pose.orientation.y = rotation.y
        pose.pose.orientation.z = rotation.z
        pose.pose.orientation.w = rotation.w
        return pose


def main():
    rclpy.init()
    node = NuScenesPointCloudReplay()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
