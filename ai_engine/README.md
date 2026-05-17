# AI Engine (智慧农业 AI 推理引擎)

本项目是 AI-Agriculture 平台的 AI 推理引擎，采用**双模型架构**——基于 YOLOv8 的目标检测器（主力）和轻量级分类器（兜底），实现了本地化的图片上传、AI 诊断及结果持久化。

## 目录结构

```
ai_engine/
├── main.py                          # FastAPI 入口（模型加载、路由挂载、静态资源）
└── crops/                           # 核心识别逻辑
    └── rice/
        └── inference/
            ├── api.py               # 单文件逻辑核心：包含所有接口、校验与推理调度
            ├── yolo_detector.py     # [NEW] YOLOv8 目标检测器（BSR 后端渲染）
            └── rice_leaf_classifier.py  # 轻量级分类器（兜底/边缘端）
local_data/
└── uploads/                         # 本地存储：保存图片及 .json 元数据
models/
├── yolov8_rice_leaf.pt              # [NEW] YOLO 检测模型权重
└── rice/rice_leaf_classifier/       # 传统分类器权重
```

## 核心架构：BSR（Backend-Side Rendering）

本系统采用**后端渲染**策略处理 BBox 检测框：

1. **上传存储**：前端上传的图片保存至 `local_data/uploads/`，文件名使用 UUID。
2. **YOLO 检测**：保存成功后立即调用 `YoloDetector` 进行目标检测，精确定位每一个病斑。
3. **后端画框**：YOLO 推理完毕后，检测框（BBox）、类别标签和置信度**直接由后端画在图片上**（使用 Ultralytics 内置渲染器），生成一张"带框注释图"。
4. **替换存储**：将原始上传图替换为带框版本。前端在展示时，拉取到的已经是一张包含所有红绿色检测框的完整图片，**无需任何前端 JS 修改**。
5. **结果固化**：推理结果（类别、置信度、病斑数量、时间戳）写入同名 `.json` 元数据文件。
6. **历史回显**：诊断记录接口扫描目录并读取 `.json` 文件，确保刷新页面后识别结果不丢失。

### 为什么选择 BSR？
- **零前端改造**：不需要在手机端和 PC 端浏览器中编写复杂的 Canvas 坐标缩放逻辑。
- **所见即所得**：用户在仪表盘上看到的图片就是最终的检测结果，截图直接可用于报告和 PPT。
- **工业级标准**：这也是物联网边缘计算场景中常用的"服务端渲染"方案。

## 推理优先级

```
用户上传图片
     │
     ▼
YOLO 检测器是否已加载？
     ├── 是 → 运行 YOLO 目标检测 + BSR 画框  [优先]
     └── 否 → 分类器是否已加载？
                ├── 是 → 运行传统分类（无 BBox）
                └── 否 → 返回 Mock 数据（演示兜底）
```

## API 说明

### 核心业务接口

| 方法 | 路径 | 说明 |
|------|------|------|
| **POST** | `/api/v1/image/upload` | **上传并识别**。接收图片，YOLO 检测后返回带框图片和推理结果。 |
| **GET** | `/api/v1/image/file` | **获取图片**。根据 `upload_id` 返回带检测框的图片。 |
| **GET** | `/api/v1/image/uploads` | **诊断记录**。返回最近上传的识别历史。 |

### 模型与健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 基础服务健康检查 |
| GET | `/api/v1/rice/health` | 水稻识别模型加载状态检查 |

## 快速启动

确保已激活 Conda 环境并安装依赖：

```bash
# 1. 启动后端服务 (默认端口 8000)
python -m ai_engine.main

# 2. 访问控制台
# 浏览器打开 http://127.0.0.1:8000 即可自动跳转至前端看板
```

## 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `YOLO_MODEL_PATH` | YOLO 检测模型权重路径 | `models/yolov8_rice_leaf.pt` |
| `MODEL_CHECKPOINT_PATH` | 传统分类器权重路径 | `models/rice/rice_leaf_classifier/best_model.pth` |
| `MODEL_ADVICE_FILE` | 病害处理建议映射表 | `models/rice/rice_leaf_classifier/advice_map.yaml` |

---
*Note: 此版本专为单机演示设计，如需恢复分布式或云端模式，请参考 git 历史中的 `enterprise-main` 分支。*
