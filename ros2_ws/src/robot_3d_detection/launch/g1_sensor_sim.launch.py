from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    data_root = LaunchConfiguration("data_root")
    manifest = LaunchConfiguration("manifest")
    cfg_file = LaunchConfiguration("cfg_file")
    ckpt = LaunchConfiguration("ckpt")
    replay = Node(
        package="robot_3d_detection",
        executable="nuscenes_pointcloud_replay",
        name="g1_sensor_simulator",
        parameters=[{
            "data_root": data_root,
            "manifest": manifest,
            "topic": "/g1_sim/lidar/points",
            "publish_odometry": True,
            "odom_topic": "/g1_sim/odom",
            "period_sec": 0.5,
            "startup_delay_sec": 15.0,
        }],
        output="screen",
    )
    pose_bridge = Node(
        package="robot_3d_detection",
        executable="odometry_to_lidar_pose",
        name="g1_sensor_sim_pose_bridge",
        parameters=[{
            "odom_topic": "/g1_sim/odom",
            "pose_topic": "/g1_sim/lidar/pose",
        }],
        output="screen",
    )
    detector = Node(
        package="robot_3d_detection",
        executable="pointpillar_detector",
        name="g1_sensor_sim_temporal_detector",
        parameters=[{
            "cfg_file": cfg_file,
            "ckpt": ckpt,
            "input_topic": "/g1_sim/lidar/points",
            "output_topic": "/g1_sim/perception/detections",
            "pose_topic": "/g1_sim/lidar/pose",
            "temporal_sweeps": 3,
            "score_threshold": 0.35,
        }],
        output="screen",
    )
    shutdown_after_replay = RegisterEventHandler(
        OnProcessExit(target_action=replay, on_exit=[EmitEvent(event=Shutdown(reason="G1 sensor simulation complete"))])
    )
    return LaunchDescription([
        DeclareLaunchArgument("data_root"),
        DeclareLaunchArgument("manifest"),
        DeclareLaunchArgument("cfg_file"),
        DeclareLaunchArgument("ckpt"),
        pose_bridge,
        detector,
        replay,
        shutdown_after_replay,
    ])
