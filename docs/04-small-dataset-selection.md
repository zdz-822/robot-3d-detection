# 小规模数据集选型：nuScenes v1.0-mini

## 决定

第一轮工程验证从 KITTI 切换到 `nuScenes v1.0-mini`。它用于跑通 PointPillars/CenterPoint 的训练、评估和可视化链路；不把 mini 上的最终指标当作可与论文或完整数据集横向比较的性能结论。

## 原因

- nuScenes 官方 devkit 的预定义划分为 8 个 `mini_train` 场景、2 个 `mini_val` 场景，适合调试和可视化。
- OpenPCDet 官方文档明确支持 `v1.0-mini` 数据目录和 nuScenes 数据处理流程。
- 相比 KITTI 的完整 Velodyne 下载，mini 版本明显更适合当前网络环境和单机验证；实际压缩包大小以登录 nuScenes 下载页显示为准，通常约数 GB。
- mini 数据只用于工程链路验证。简历项目的关键指标应来自后续自采机器人数据或可获得的更大数据集。

## 下载方式

1. 在 [nuScenes 下载页](https://www.nuscenes.org/download) 注册并接受使用条款。
2. 选择 `v1.0-mini`，下载页面所列该版本的全部归档包。
3. 解压后确保根目录至少包含 `samples/`、`sweeps/`、`maps/`、`v1.0-mini/`。

建议放置到：

```text
/home/zhou/datasets/nuscenes/
├── samples/
├── sweeps/
├── maps/
└── v1.0-mini/
```

## 许可证

nuScenes devkit 要求用户创建账户并同意使用条款；其数据在官方说明中标注为非商业使用。代码的开源许可证不改变数据集本身的使用限制。

## 一手来源

- nuScenes devkit 的 [README](https://github.com/nutonomy/nuscenes-devkit/blob/master/README.md)：说明需在官方下载页注册并同意条款，且 nuScenes 根目录需要 `samples`、`sweeps`、`maps` 与 `v1.0-*` 元数据目录。
- nuScenes devkit 的 [splits.py](https://github.com/nutonomy/nuscenes-devkit/blob/master/python-sdk/nuscenes/utils/splits.py)：定义 `mini_train` 为 8 个场景、`mini_val` 为 2 个场景，并将其定位为用于可视化和调试的 mini 子集。
- OpenPCDet 的 [Getting Started](https://github.com/open-mmlab/OpenPCDet/blob/master/docs/GETTING_STARTED.md)：明确列出 `v1.0-mini` 的目录布局与 nuScenes 数据预处理入口。
