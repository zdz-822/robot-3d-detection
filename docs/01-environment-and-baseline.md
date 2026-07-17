# 环境与首个基线

## 已确认的机器条件

| 项目 | 当前条件 | 结论 |
| --- | --- | --- |
| 系统 | Ubuntu 22.04 (WSL2) | 可用 |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU | 可用 |
| 显存 | 8GB | 先做 PointPillars，单卡 batch size 设为 2 |
| 容器运行时 | Docker 29.5 | 可用，作为 CUDA 编译与训练环境 |
| 磁盘余量 | 约 897GB | 可容纳 KITTI 和训练输出 |

## 第一阶段范围

- 数据集：KITTI 3D Object Detection。
- 模型：OpenPCDet 的 `tools/cfgs/kitti_models/pointpillar.yaml`。
- 类别：`Car`、`Pedestrian`、`Cyclist`。
- 训练预算：单 GPU、总 batch size `2`、数据加载 workers `4`。
- 产物：训练配置、日志、最优 checkpoint、验证指标、至少 10 张可视化结果。

## 为什么先用 PointPillars

它将点云按垂直柱体编码到 BEV 特征图，训练和推理效率较好，适合作为 8GB 显存上的工程基线。后续的 CenterPoint 能复用点云预处理、数据接口、BEV 表征和大部分部署管线，因此不会浪费第一阶段工作。

## 源码位置

训练源码放在 WSL Linux 文件系统，而不是 `/mnt/c`：

```text
/home/zhou/projects/robot-3d-detection/OpenPCDet
```

在本项目目录中执行 `scripts/bootstrap_openpcdet.sh` 可下载官方源码。当前网络若导致 GitHub 大文件下载中断，脚本可再次运行；不要把未完成的目录当作有效源码。

## 数据目录约定

将 KITTI 数据放在 WSL 路径：

```text
/home/zhou/datasets/KITTI/
├── training/
└── testing/
```

OpenPCDet 源码内已有 `data/kitti/ImageSets` 的官方训练/验证划分。预处理脚本只会将其 `training` 和 `testing` 目录软链接到上面的外部数据路径，不会替换官方划分文件。数据下载与标注转换将在容器环境就绪后执行。

## 基线运行命令

以下命令将在源码和容器环境就绪后执行：

```bash
cd /home/zhou/projects/robot-3d-detection/OpenPCDet
python -m pcdet.datasets.kitti.kitti_dataset create_kitti_infos tools/cfgs/dataset_configs/kitti_dataset.yaml
python tools/train.py --cfg_file tools/cfgs/kitti_models/pointpillar.yaml --batch_size 2 --workers 4
python tools/test.py --cfg_file tools/cfgs/kitti_models/pointpillar.yaml --batch_size 2 --ckpt output/kitti_models/pointpillar/default/ckpt/checkpoint_epoch_*.pth
```

第三条的 checkpoint 名称需替换为实际最佳模型。训练开始前先运行环境检查脚本。

## 环境策略

不要直接使用 OpenPCDet 仓库自带的 Dockerfile：它固定为 CUDA 10.2 和 PyTorch 1.6，早于 RTX 4060 的 Ada 架构。项目使用 `docker/Dockerfile` 构建 CUDA 12.1 / PyTorch 2.2.2 开发容器，并在容器内以 `TORCH_CUDA_ARCH_LIST=8.9` 编译 CUDA 算子。镜像构建、GPU 验证和框架安装分别由 `scripts/build_training_image.sh`、`scripts/verify_training_image.sh`、`scripts/install_openpcdet.sh` 执行。
