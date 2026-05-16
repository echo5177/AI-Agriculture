# AI-Agriculture (智慧农业 AI 系统 - 水稻病害检测)

这是一个面向智慧农业的 AI 系统原型，集成了**水稻叶片病害目标检测（Object Detection）**与**图像分类（Image Classification）**双模型架构。系统提供精美的 Web 仪表盘，支持**手机端实时摄像头拍摄识别**和**本地图片上传诊断**。

## 核心亮点

- **🎯 目标检测 (YOLO)**：基于 YOLOv8 训练的病害检测模型，能在叶片上精准定位多个病斑并画出检测框（Bounding Box），支持 8 类水稻病害识别。
- **🔬 双模型架构**：轻量级分类模型（边缘端快速筛查）+ YOLO 检测模型（云端精准定位），体现云边协同设计。
- **📱 实时摄像头**：支持在浏览器中直接调用摄像头，周期性抓取帧并上传进行 AI 推理，模拟田间实时监控。
- **🖥️ 水稻专属仪表盘**：精美的米黄色暖色调前端界面，实时展示环境传感器数据（模拟）与 AI 诊断历史。
- **⚡ 全 Python 架构**：无需配置数据库或 Rust 环境，在 Windows 本地一键启动。

## 快速启动 (Windows)

1. **环境准备**：
   确保已安装 Python 3.9+。建议使用你已有的 `plant` conda 环境。

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **启动系统**：
   在根目录下运行：
   ```bash
   python -m ai_engine.main
   ```

4. **访问系统**：
   - **主仪表盘**: [http://localhost:8000](http://localhost:8000)
   - **手机端访问**: 请查看下方 [手机端使用指南](#手机端使用指南)。

## 手机端使用指南

通过手机使用本项目可以获得最真实的"田间实时诊断"体验。

1. **同一网络**：确保你的手机和电脑连接在**同一个 Wi-Fi** 下。
2. **获取电脑 IP**：
   - 在电脑终端运行 `ipconfig`。
   - 找到 `无线局域网适配器 Wi-Fi` 下的 `IPv4 地址`（通常是 `192.168.x.x` 或 `10.x.x.x`）。
3. **手机访问**：
   - 打开手机浏览器（Chrome 或 Safari）。
   - 输入：`http://你的电脑IP:8000` (例如 `http://192.168.1.10:8000`)。
4. **实时 AI 诊断**：
   - 点击主页上的 **"实时摄像头 PoC"** 按钮。
   - 在弹出的米黄色窗口中点击"启动摄像头"。
   - 点击"开始循环抓拍"，手机拍摄到的画面将实时传输回电脑后端，并自动完成 AI 病害推理。

## YOLO 模型训练

本项目使用 [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) 进行水稻叶片病害目标检测训练。

### 数据集

训练使用的是 `RiceLeafAnnotatedDataset/`，包含 8 类水稻病害的标注数据：

| 编号 | 类别名称 | 中文名 |
|------|---------|--------|
| 0 | Bacterial_Leaf_Blight | 白叶枯病 |
| 1 | Brown_Spot | 褐斑病 |
| 2 | HealthyLeaf | 健康叶片 |
| 3 | Leaf_Blast | 叶瘟病 |
| 4 | Leaf_Scald | 叶烫伤病 |
| 5 | Narrow_Brown_Leaf_Spot | 窄褐条斑病 |
| 6 | Neck_Blast | 颈瘟病 |
| 7 | Rice_Hispa | 稻潜叶虫 |

### 训练命令

```bash
# 快速测试（5 轮，验证流程是否正常）
python scripts/train_yolo.py --epochs 5

# 标准训练（25 轮，默认参数）
python scripts/train_yolo.py

# 完整训练（使用更大模型 + 更多轮次）
python scripts/train_yolo.py --model yolov8s.pt --epochs 50 --imgsz 640

# 如果 GPU 显存不足，减小 batch size
python scripts/train_yolo.py --batch 8
```

训练完成后，最佳权重保存在 `runs/detect/train/weights/best.pt`。将其复制到 `models/` 目录即可部署：

```bash
copy runs\detect\train\weights\best.pt models\yolov8_rice_leaf.pt
```

## 目录结构

- `ai_engine/`：后端推理服务逻辑（FastAPI）。
- `frontend/rice/`：系统前端代码，包含仪表盘与摄像头采集页面。
- `models/`：AI 模型权重文件（分类器 + YOLO 检测器）。
- `scripts/`：训练脚本，包含 `train_yolo.py`（YOLO 目标检测训练）。
- `RiceLeafAnnotatedDataset/`：YOLO 格式标注数据集（train/valid/test）。
- `local_data/`：运行时本地存储（上传图片与 JSON 元数据）。

## 演示技巧 (必看)
1. **启动服务**后，先在电脑或手机上打开 `mobile_live_capture.html`。
2. 点击"启动摄像头"，然后点击"开始循环上传"。
3. 随后回到主仪表盘页面，你会发现"视觉 AI 反馈"面板会实时刷新你刚刚拍摄到的画面和诊断结果。
