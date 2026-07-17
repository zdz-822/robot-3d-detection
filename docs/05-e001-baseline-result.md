# E001: nuScenes mini PointPillars Baseline

## 结果

| 指标 | 数值 |
| --- | ---: |
| 数据集 | nuScenes v1.0-mini, 8 train scenes / 2 val scenes |
| 模型 | OpenPCDet PointPillars multi-head |
| 点云输入 | 单帧, `MAX_SWEEPS=1` |
| 训练 | 10 epochs, batch size 2 |
| mAP | 0.0931 |
| NDS | 0.1761 |

## 主要类别 AP

| 类别 | AP |
| --- | ---: |
| car | 0.432 |
| pedestrian | 0.386 |
| truck | 0.084 |
| bus | 0.028 |
| motorcycle | 0.001 |

其余类别在 mini 验证集上为 0，主要原因是 10 个场景中目标类别分布极不均衡，且训练样本量很小。

## 解释

该实验的目的不是获得可与完整 nuScenes 榜单横向比较的性能，而是验证完整工程链路：数据格式、nuScenes 元数据、单帧点云预处理、稀疏卷积、CUDA 扩展、训练、checkpoint 和官方评估均可复现。

`car` 和 `pedestrian` 已出现有效预测，说明模型训练、标签坐标和评估接口是正确的。下一阶段应以本结果作为对照，先在同一 mini 数据划分上增加多帧点云输入，再转向自采机器人数据进行低线束点云与小目标优化。

## 产物位置

```text
/home/zhou/projects/robot-3d-detection/OpenPCDet/output/nuscenes_models/pointpillar_nuscenes_mini/default/
├── ckpt/checkpoint_epoch_10.pth
└── eval/eval_with_train/epoch_10/val/final_result/
    ├── data/results_nusc.json
    └── metrics_summary.json
```
