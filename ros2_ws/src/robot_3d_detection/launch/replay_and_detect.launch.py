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
        name="nuscenes_pointcloud_replay",
        # OpenPCDet imports CUDA extensions on startup, so wait before sending the first scan.
        parameters=[{"data_root": data_root, "manifest": manifest, "period_sec": 0.5, "startup_delay_sec": 15.0}],
        output="screen",
    )
    detector = Node(
        package="robot_3d_detection",
        executable="pointpillar_detector",
        name="pointpillar_detector",
        parameters=[{"cfg_file": cfg_file, "ckpt": ckpt, "score_threshold": 0.35}],
        output="screen",
    )
    shutdown_after_replay = RegisterEventHandler(
        OnProcessExit(target_action=replay, on_exit=[EmitEvent(event=Shutdown(reason="nuScenes replay complete"))])
    )
    return LaunchDescription([
        DeclareLaunchArgument("data_root"),
        DeclareLaunchArgument("manifest"),
        DeclareLaunchArgument("cfg_file"),
        DeclareLaunchArgument("ckpt"),
        detector,
        replay,
        shutdown_after_replay,
    ])
