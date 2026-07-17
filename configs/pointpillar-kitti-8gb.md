# PointPillars / KITTI / RTX 4060 8GB 运行预算

| 参数 | 初始值 | 调整规则 |
| --- | ---: | --- |
| 总 batch size | 2 | CUDA OOM 时改为 1 |
| workers | 4 | CPU 或磁盘读取成为瓶颈时改为 6 或 8 |
| 训练精度 | FP32 | 基线稳定后再评估 AMP |
| 模型 | 官方 PointPillars 配置 | 不先改网络，先复现公开基线 |
| 数据范围 | 官方 KITTI 配置 | 后续自采机器人数据再缩短范围 |

实验记录中必须保存：Git commit、完整 YAML、GPU 型号、batch size、训练时长、AP 和推理耗时。任何网络改动都必须和同一数据划分上的单帧基线比较。
