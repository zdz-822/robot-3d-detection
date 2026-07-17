# Unitree G1 预部署指南

## 当前可直接使用的部署包

`run_g1_temporal_detector.sh` 会在外接 NVIDIA GPU 电脑上启动 E002 三帧时序检测。容器通过主机网络订阅机器人 ROS 2 话题，不运行任何运动控制命令。

```text
G1 LiDAR PointCloud2 ----> /lidar/points -----------+
G1 base Odometry --------> /odom -> pose bridge ----+-> E002 temporal detector -> /perception/detections
```

检测器要求三帧点云与对应的全局 LiDAR 位姿。位姿桥将机器人 base 的 `Odometry` 与“base 到 LiDAR”的静态安装外参相乘，输出 `/lidar/pose`。

## 上机前必须确认

1. G1 是否安装 LiDAR，且 Unitree SDK2 或 ROS 2 驱动能发布原始 `PointCloud2`。
2. 实际点云话题名和里程计话题名，例如 `/lidar/points`、`/odom` 仅是默认值。
3. LiDAR 相对机器人 base 坐标系的平移和旋转外参；不能长期使用默认 0。
4. G1 与外接 RTX 笔记本处于同一网络，ROS 2 `ROS_DOMAIN_ID` 一致，且 DDS 发现通信正常。
5. 点云中的 `x/y/z` 坐标确实属于 LiDAR 坐标系，或已相应调整 LiDAR 外参。

## 启动方式

在外接 GPU 笔记本的 WSL 中，先根据实际话题与安装位姿设置环境变量，再启动：

```bash
export POINTS_TOPIC=/actual/lidar/topic
export ODOM_TOPIC=/actual/odom/topic
export ROS_DOMAIN_ID=0
export LIDAR_X=0.0
export LIDAR_Y=0.0
export LIDAR_Z=0.0
export LIDAR_ROLL=0.0
export LIDAR_PITCH=0.0
export LIDAR_YAW=0.0
bash scripts/run_g1_temporal_detector.sh
```

`/perception/detections` 输出标准 `vision_msgs/Detection3DArray`。第一阶段只检查检测框是否合理并在 RViz/可视化中观察，禁止直接用于 G1 步态、避障或控制。

## 现实限制

- 当前 E002 权重在 nuScenes mini 训练，类别主要是道路目标；它可以用于接入验证，但不应期待室内 G1 场景的稳定业务效果。
- 真正上机前必须采集 G1 的点云，使用 E005 工具标注 `Pedestrian`、`Cart`、`Pallet`、`Cone` 等目标并微调。
- 若 G1 不提供 LiDAR 原始点云，或只提供相机图像，当前 LiDAR 项目不能直接运行，需要接入外部 LiDAR 或修改感知方案。
