# G1 传感器级仿真平台

## 定位

该平台是 ROS 2 数据驱动仿真，不是 Gazebo 物理仿真。它使用 nuScenes 的真实连续点云和位姿，模拟未来 G1 对外发布的 LiDAR 与 Odometry 接口，因此可验证感知软件链路和部署参数，而不虚构 G1 的机械动力学或传感器噪声。

## 仿真话题

| 仿真话题 | 类型 | 真实 G1 对应接口 |
| --- | --- | --- |
| `/g1_sim/lidar/points` | `sensor_msgs/PointCloud2` | G1 LiDAR 点云 |
| `/g1_sim/odom` | `nav_msgs/Odometry` | G1 base 里程计 |
| `/g1_sim/lidar/pose` | `geometry_msgs/PoseStamped` | LiDAR 全局位姿 |
| `/g1_sim/perception/detections` | `vision_msgs/Detection3DArray` | 3D 检测输出 |

## 运行

```bash
bash scripts/run_g1_sensor_sim.sh
```

仿真从 nuScenes 同一场景回放 12 帧点云与位姿，位姿桥将模拟的 Odometry 转为 LiDAR PoseStamped，E002 检测节点从第 3 帧起运行三帧融合并发布检测结果。回放完成后自动退出。

## 能证明什么

- G1 预部署中的话题命名、Odometry 到 LiDAR 位姿桥和 E002 时序检测器可协同运行。
- 真实 G1 接入时，只需将 `/g1_sim/...` 替换为探测到的真实话题，并填写真实 LiDAR 外参。

## 实际仿真结果

- 模拟器成功回放 12 帧连续 LiDAR 点云，并为每帧发布模拟 G1 Odometry。
- `odometry_to_lidar_pose` 位姿桥成功将 `/g1_sim/odom` 转为 `/g1_sim/lidar/pose`。
- E002 三帧检测节点前两帧建立缓存，从第 3 帧开始持续输出 `/g1_sim/perception/detections`。
- 后续 10 帧均产生检测结果，每帧 2 至 14 个 3D 检测框，所有节点在回放结束后正常退出。

## 不能证明什么

- 不能代表 G1 的步态、动力学、激光雷达噪声或室内环境分布。
- 不能代表模型在真实 G1 场景的检测精度；这需要真实数据采集和 E005 微调。
