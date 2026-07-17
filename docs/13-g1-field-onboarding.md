# Unitree G1 现场接入清单

本清单用于第一次接入 G1 时收集真实接口信息。所有操作仅观察、记录和可视化，不发送运动控制指令。

## 1. 网络与 ROS 2 发现

让 G1 与外接 RTX 笔记本接入同一局域网，并确认双方使用相同的 `ROS_DOMAIN_ID`。在笔记本 WSL 中运行：

```bash
export ROS_DOMAIN_ID=0
bash scripts/probe_g1_ros_interface.sh
```

脚本会在 `data/g1_probe/` 保存报告，列出当前 ROS 2 域中发现的：

- `sensor_msgs/msg/PointCloud2` 点云话题。
- `nav_msgs/msg/Odometry` 里程计话题。
- `geometry_msgs/msg/PoseStamped` 位姿话题。
- `/tf`、`/tf_static` 坐标变换话题。

将该报告发回项目，再把真实话题名写入 `configs/unitree-g1-deployment.yaml`。

## 2. 只录数据，不运行检测

确认点云和里程计话题后，先录制 2 到 5 分钟的静止、慢走和有人经过场景：

```bash
export POINTS_TOPIC=/actual/lidar/topic
export ODOM_TOPIC=/actual/odom/topic
bash scripts/record_g1_sensor_bag.sh
```

录制文件保存在 `data/g1_bags/`，不会进入 Git。先检查坐标方向、时间戳、点数和位姿连续性，再进行检测。

## 3. 填写 LiDAR 外参

测量 LiDAR 原点相对 G1 base 坐标系的平移 `x/y/z` 和朝向 `roll/pitch/yaw`。暂时无法得到精确数值时，可从机器人 URDF、TF 树或传感器安装说明中查找；不要长期使用默认零值。

## 4. 启动感知

只有在点云、里程计、时间戳和外参均确认后，才运行 `run_g1_temporal_detector.sh`。输出只用于 RViz 或日志验证，禁止接入步态、导航或避障控制。

检测节点会打印每帧的 GPU 端到端检测耗时。现场应先忽略第一帧的 CUDA 预热时间，再记录稳定状态下的 30 帧平均值、P95 延迟和丢帧情况。

## 5. 数据闭环

从录制数据中选取 100 到 300 帧，标注行人、手推车、托盘和路锥，使用 E005 工具转换、校验并微调。完成这一步后，模型才有条件适应 G1 的真实雷达和场景。
