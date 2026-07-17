# E007: ROS 2 3D 检测可视化

## 目标

将模型发布的 `vision_msgs/Detection3DArray` 转换为 RViz 可直接显示的 `visualization_msgs/MarkerArray`，用于仿真演示和未来 G1 上机观察。

## 数据流

```text
/perception/detections (Detection3DArray)
    -> detection_marker_visualizer
    -> /perception/markers (MarkerArray)
    -> RViz MarkerArray display
```

G1 传感器仿真使用独立命名空间：`/g1_sim/perception/detections -> /g1_sim/perception/markers`。

## Marker 约定

- 半透明彩色立方体：目标 3D 框，尺寸和朝向与检测框一致。
- 框顶文字：类别和置信度，例如 `pedestrian 0.82`。
- 车辆为橙色、行人为黄色、公交车为蓝色、自行车为绿色；未知类别为白色。
- Marker 生命周期为 1.5 秒，避免旧检测框残留。

## RViz 使用

在能够运行 RViz 2 的 ROS 环境中，添加 `MarkerArray` Display，并选择：

- 仿真：`/g1_sim/perception/markers`
- 真实 G1：`/perception/markers`

同时添加 `PointCloud2` Display 查看点云。固定坐标系应选择与点云 header 一致的 LiDAR frame。第一阶段只观察视觉结果，不接入运动控制。

## 仿真验证结果

2026-07-17 已使用 G1 传感器级仿真完成 12 帧端到端验证：

- 前 2 帧进入三帧时序缓存，不发布检测结果，这是预期行为。
- 后 10 帧均发布检测结果，每帧 1 到 14 个目标，对应生成 2 到 28 个 Marker（每个目标包含一个 3D 框和一条文字标签）。
- 除首次 CUDA 预热外，后续检测处理延迟约为 81 到 131 ms；该时间不包含真实雷达传输与 ROS 2 网络传输。
- 点云回放、位姿转换、时序检测和可视化节点均正常退出。

本次验证说明感知与显示链路已经可用。Docker/WSL 环境未启动 RViz 图形界面；在带 RViz 2 的 ROS 环境中订阅上述 MarkerArray 话题即可看到三维框。
