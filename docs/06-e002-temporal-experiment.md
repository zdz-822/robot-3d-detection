# E002: 三帧时序点云融合

## 假设

将相邻历史点云通过 nuScenes 提供的车辆位姿变换对齐到当前雷达坐标系，并保留时间差特征，可增加远距离和稀疏目标的有效点数，提高检测召回。

## 实验设计

| 项目 | E001 | E002 |
| --- | --- | --- |
| 输入 | 单帧 | 当前帧 + 2 个历史帧 |
| `MAX_SWEEPS` | 1 | 3 |
| 模型 | PointPillars multi-head | 同一模型 |
| 数据划分 | nuScenes mini | 同一划分 |
| 训练 | 10 epochs, batch 2 | 10 epochs, batch 2 |

保持模型和数据划分不变，只改变时序输入，才可以将指标变化归因于多帧点云融合。

## 结果

| 指标 | E001 单帧 | E002 三帧 | 变化 |
| --- | ---: | ---: | ---: |
| mAP | 0.0931 | 0.1176 | +0.0245 |
| NDS | 0.1761 | 0.1790 | +0.0029 |
| car AP | 0.4315 | 0.4582 | +0.0267 |
| pedestrian AP | 0.3857 | 0.5105 | +0.1248 |
| truck AP | 0.0840 | 0.0968 | +0.0128 |
| bus AP | 0.0284 | 0.1037 | +0.0753 |

E002 在相同模型、训练轮数和数据划分下，仅增加两帧历史点云便提升了 mAP；行人与公交车提升更明显，说明时序融合增加了稀疏目标的有效点数。该结果仅用于验证工程方案，nuScenes mini 数据量较小，不能作为完整 nuScenes 榜单指标。

## 输出位置

- 权重：`/home/zhou/projects/robot-3d-detection/OpenPCDet/output/nuscenes_models/pointpillar_nuscenes_mini_3sweeps/default/ckpt/checkpoint_epoch_10.pth`
- 官方评测：`/home/zhou/projects/robot-3d-detection/OpenPCDet/output/nuscenes_models/pointpillar_nuscenes_mini_3sweeps/default/eval/eval_with_train/epoch_10/val/final_result/`
