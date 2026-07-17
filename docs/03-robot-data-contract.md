# 自定义机器人数据约定

该约定在 KITTI 基线后实施。目标是将移动机器人激光雷达数据稳定转换为 OpenPCDet 可读取的格式，而不是把传感器日志与训练代码耦合在一起。

## 第一版类别

| 类别 | 定义 | 初始目标 |
| --- | --- | --- |
| `Pedestrian` | 行走或站立的人 | 安全相关，优先保证召回 |
| `Cart` | 手推车、周转车 | 机器人常见动态障碍物 |
| `Pallet` | 托盘及装载物 | 仓储场景关键静态目标 |
| `Cone` | 路锥、隔离桶 | 小目标，用于检验稀疏点云改进 |

## 单帧输入

采集侧保留 `float32` 的 `.bin` 文件，每个点为：

```text
x, y, z, intensity
```

坐标系统一为激光雷达坐标系：`x` 向前、`y` 向左、`z` 向上。记录每帧时间戳和机器人在世界坐标系中的位姿。

OpenPCDet 的官方 custom dataset 模板读取 `.npy` 点云。因此本项目的转换器将原始 `.bin` 写为 `float32[N, 4]` 的 `.npy` 文件，目录结构遵循：

```text
data/custom/
├── ImageSets/train.txt
├── ImageSets/val.txt
├── points/000001.npy
└── labels/000001.txt
```

## 3D 标注

每个目标采用：

```text
class_name, x, y, z, dx, dy, dz, yaw
```

其中 `(x, y, z)` 是 3D 框中心，`dx/dy/dz` 分别对应前向、横向、竖向尺寸，`yaw` 绕 z 轴旋转。第一版只做检测；跟踪 ID 作为可选字段保留给后续评估。

OpenPCDet custom template 的标签行顺序为：

```text
x y z dx dy dz yaw class_name
```

## 多帧融合的约束

对当前时刻 `t` 融合 `t-1` 到 `t-4` 的点云。每帧先由里程计或定位模块变换到 `t` 的雷达坐标系，再附加 `time_lag` 特征。训练集、验证集、测试集必须按采集序列切分，不能随机打散相邻帧，避免时序泄漏。
