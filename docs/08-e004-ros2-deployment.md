# E004: ROS 2 离线部署

## 目标

将 3D 检测模型从训练脚本封装为机器人软件中的 ROS 2 节点。演示不依赖真实机器人：用 nuScenes 连续点云模拟雷达，并发布标准 `PointCloud2` 消息。

## 节点结构

```text
nuScenes .pcd.bin 文件
    -> nuscenes_pointcloud_replay
    -> /lidar/points (sensor_msgs/PointCloud2)
    -> pointpillar_detector
    -> /perception/detections (vision_msgs/Detection3DArray)
```

`nuscenes_pointcloud_replay` 以 2Hz 发布 E003 中同一场景的 12 帧点云。`pointpillar_detector` 订阅点云、运行 PointPillars，并将类别、置信度、三维中心、尺寸和朝向发布为标准 3D 检测消息。

## 模型选择

本次部署使用 E001 单帧权重，因为一个 `PointCloud2` 消息对应当前单帧点云。E002 的三帧模型已证明时序融合有效；要将它直接放入 ROS 2，需要额外增加“缓存最近三帧 + 根据机器人位姿对齐历史点云”的时序融合节点。这将作为后续增强，而不混淆单帧消息接口与三帧研究实验。

## 验收标准

- ROS 2 Humble 与 OpenPCDet 运行于同一 GPU 容器。
- 12 帧点云连续发布到 `/lidar/points`。
- 每帧从 `/perception/detections` 输出 `Detection3DArray`，包含至少一个高置信度检测结果。

## 实际验收结果

- 已构建镜像：`robot-3d-detection:ros2-humble`。
- `nuscenes_pointcloud_replay` 成功发布连续 12 帧，每帧约 3.47 万个点。
- `pointpillar_detector` 成功加载 E001 第 10 轮权重，并对 12 帧全部发布检测结果。
- 每帧输出 `3` 至 `14` 个高置信度 3D 检测框，两个节点在回放结束后正常退出。

## 复现入口

在 WSL 中执行 `scripts/run_ros2_replay.sh`。脚本会构建工作区、启动两个节点并自动在 12 帧回放完成后退出。
