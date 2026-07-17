from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    points_topic = LaunchConfiguration("points_topic")
    odom_topic = LaunchConfiguration("odom_topic")
    cfg_file = LaunchConfiguration("cfg_file")
    ckpt = LaunchConfiguration("ckpt")
    arguments = [
        DeclareLaunchArgument("points_topic", default_value="/lidar/points"),
        DeclareLaunchArgument("odom_topic", default_value="/odom"),
        DeclareLaunchArgument("cfg_file"),
        DeclareLaunchArgument("ckpt"),
        DeclareLaunchArgument("lidar_x", default_value="0.0"),
        DeclareLaunchArgument("lidar_y", default_value="0.0"),
        DeclareLaunchArgument("lidar_z", default_value="0.0"),
        DeclareLaunchArgument("lidar_roll", default_value="0.0"),
        DeclareLaunchArgument("lidar_pitch", default_value="0.0"),
        DeclareLaunchArgument("lidar_yaw", default_value="0.0"),
    ]
    pose_bridge = Node(
        package="robot_3d_detection",
        executable="odometry_to_lidar_pose",
        parameters=[{
            "odom_topic": odom_topic,
            "pose_topic": "/lidar/pose",
            "lidar_x": LaunchConfiguration("lidar_x"),
            "lidar_y": LaunchConfiguration("lidar_y"),
            "lidar_z": LaunchConfiguration("lidar_z"),
            "lidar_roll": LaunchConfiguration("lidar_roll"),
            "lidar_pitch": LaunchConfiguration("lidar_pitch"),
            "lidar_yaw": LaunchConfiguration("lidar_yaw"),
        }],
        output="screen",
    )
    detector = Node(
        package="robot_3d_detection",
        executable="pointpillar_detector",
        name="g1_temporal_detector",
        parameters=[{
            "cfg_file": cfg_file,
            "ckpt": ckpt,
            "input_topic": points_topic,
            "output_topic": "/perception/detections",
            "pose_topic": "/lidar/pose",
            "temporal_sweeps": 3,
            "score_threshold": 0.35,
        }],
        output="screen",
    )
    visualizer = Node(
        package="robot_3d_detection",
        executable="detection_marker_visualizer",
        parameters=[{
            "input_topic": "/perception/detections",
            "marker_topic": "/perception/markers",
        }],
        output="screen",
    )
    return LaunchDescription(arguments + [pose_bridge, detector, visualizer])
