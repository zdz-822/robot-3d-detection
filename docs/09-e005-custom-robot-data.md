# E005: 自定义机器人数据接口

## 目标

将真实雷达采集结果转换为 OpenPCDet `CustomDataset` 可读取的格式。该阶段只建立数据接口、校验和索引，不使用合成样例训练或报告模型指标。

## 数据目录

```text
data/custom/
├── raw_bin/             # 采集侧输出的原始 XYZI float32 文件
├── points/              # 转换后的 float32[N, 4] .npy 点云
├── labels/              # 每帧一个 3D 标注文本
├── ImageSets/train.txt  # 训练帧 ID，按采集序列划分
└── ImageSets/val.txt    # 验证帧 ID，不能与训练序列重叠
```

每个原始点为 `x y z intensity`，坐标约定为 x 向前、y 向左、z 向上。每个标注行为：

```text
x y z dx dy dz yaw class_name
```

第一版类别为 `Pedestrian`、`Cart`、`Pallet`、`Cone`。`yaw` 单位为弧度，取值范围 `[-pi, pi]`，三维框中心与尺寸均在雷达坐标系中。

## 实际使用顺序

1. 将真实雷达的 `.bin` 放入 `data/custom/raw_bin/`。
2. 使用 `convert_robot_points.py` 转换到 `data/custom/points/`。
3. 编写对应 `labels/<frame_id>.txt`，并按完整采集序列划分 `train.txt`、`val.txt`。
4. 运行 `prepare_robot_dataset.sh`。它会校验点云、标签、类别、尺寸、角度和训练/验证集重叠，并生成 OpenPCDet 所需的 `robot_infos_train.pkl`、`robot_infos_val.pkl`。
5. 再根据实际雷达量程调整 `configs/robot-custom-dataset.yaml` 的点云范围和体素大小，然后开始微调。

## 合成验证样例

项目可生成两个很小的合成帧，目的仅为验证格式链路。它们不是真实采集数据，不能用于训练、评测或写入简历指标。

内置 `CustomDataset` 的 KITTI 评测适配只原生支持三类语义。当前四类配置中的映射仅用于保持接口兼容；真实项目应在拿到足够数据后接入与机器人类别一致的自定义 mAP 评测，不应把映射后的 KITTI AP 当作最终业务指标。

## 接口验收结果

已在 `data/custom_interface_sample/` 创建仅用于工具验证的两个合成帧，并完成：

- 2 个原始 `.bin` 帧转换为 `float32[N, 4]` 的 `.npy` 点云，共 2160 个点。
- `train.txt` 与 `val.txt` 各包含 1 帧，校验确认没有重叠。
- `Pedestrian`、`Cart`、`Pallet`、`Cone` 四个类别各有 1 个有效标注。
- 已生成 `robot_infos_train.pkl` 和 `robot_infos_val.pkl`，确认可被 OpenPCDet `CustomDataset` 读取。

该样例只证明接口可用，不能用于训练、评测或产生任何模型指标。
