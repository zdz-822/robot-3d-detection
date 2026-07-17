from setuptools import find_packages, setup


package_name = "robot_3d_detection"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/robot_3d_detection"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", [
            "launch/replay_and_detect.launch.py",
            "launch/replay_temporal_detect.launch.py",
        ]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "nuscenes_pointcloud_replay = robot_3d_detection.nuscenes_pointcloud_replay:main",
            "pointpillar_detector = robot_3d_detection.pointpillar_detector:main",
        ],
    },
)
