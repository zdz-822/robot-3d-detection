# E006: ROS 2 三帧时序点云融合

## 目标

将 E002 的三帧时序融合从离线训练数据加载器迁移到 ROS 2 推理流程。每次推理使用当前激光扫描与前两次扫描，而不是只使用单帧 `PointCloud2`。

## 数据流

```text
nuScenes LiDAR + nuScenes ego pose / sensor calibration
    -> /lidar/points (PointCloud2)
    -> /lidar/pose (PoseStamped, global_from_lidar)
    -> temporal PointPillars detector
    -> cache 3 scans, ego-pose alignment, time_lag feature
    -> E002 checkpoint
    -> /perception/detections (Detection3DArray)
```

## 对齐方法

令 `T_global_lidar(t)` 表示 t 时刻雷达坐标系到全局坐标系的变换。对历史帧 `h` 的点云，转换到当前帧 `c` 的雷达坐标系：

```text
T_current_from_history = inverse(T_global_lidar(c)) * T_global_lidar(h)
```

历史点经过该变换后与当前点拼接，并增加 `time_lag = timestamp(h) - timestamp(c)`。当前帧的时间差为 0，历史帧为负值。

## 验收标准

- 回放节点为每个 `PointCloud2` 发布相同时间戳的 `PoseStamped`。
- 检测节点缓存 3 帧，前两帧只建立缓存，从第 3 帧起运行 E002 推理。
- E002 三帧权重输出标准 `Detection3DArray`。
- 单帧 E004 启动文件和推理路径保持可用。

## 实际验收结果

- 回放节点成功从 nuScenes 元数据读取每帧的 ego pose 与雷达标定，发布与点云相同时间戳的 `/lidar/pose`。
- 时序检测节点成功加载 E002 的 `MAX_SWEEPS=3` 权重；第 1、2 帧仅建立缓存，第 3 帧开始执行时序推理。
- 在 12 帧回放中，后续 10 帧全部发布 `Detection3DArray`，每帧输出 2 至 14 个高置信度 3D 检测框。
- E004 单帧回放在改动后复测通过，12 帧仍全部产生检测结果。
- 在 RTX 4060 Laptop GPU 上，首次三帧推理因 CUDA 预热耗时约 1238 ms；之后 9 次节点内端到端检测耗时为 88.7 至 208.0 ms。该统计包含 PointCloud2 解析、三帧对齐、模型推理、NMS 和消息构造，不包含机器人传感器传输与 DDS 网络延迟。

## 复现入口

在 WSL 中执行 `scripts/run_ros2_temporal_replay.sh`。它会使用 E002 权重和三帧配置启动 ROS 2 时序回放，完成后自动退出。
