# AI Engine (AIT103 Academic Prototype)

本项目是 AI-Agriculture 平台的轻量化 AI 推理引擎原型，专门针对 AIT103 学术演示进行了“瘦身”优化。它移除了复杂的云端网关和数据库依赖，实现了本地化的图片上传、AI 诊断及结果持久化。

## 目录结构

```
ai_engine/
├── main.py                          # FastAPI 入口（模型加载、路由挂载、静态资源）
└── crops/                           # 核心识别逻辑
    └── rice/
        └── inference/
            ├── api.py               # 单文件逻辑核心：包含所有接口、校验与 Mock 逻辑
            └── rice_leaf_classifier.py  # 水稻病害 AI 分类器
local_data/
└── uploads/                         # 本地存储：保存图片及 .json 元数据
```

## 核心功能：识别与存储闭环

在演示版本中，我们实现了**无数据库持久化方案**：
1.  **上传存储**：前端上传的图片保存至 `local_data/uploads/`，文件名使用 UUID。
2.  **实时推理**：保存成功后立即调用 `RiceLeafClassifier` 进行病害识别。
3.  **结果固化**：推理结果（类别、置信度、时间戳）会被写入同名的 `.json` 元数据文件中。
4.  **历史回显**：诊断记录接口（`/api/v1/image/uploads`）会扫描该目录并读取 `.json` 文件，确保刷新页面后识别结果不丢失。

## API 说明

### 核心业务接口

| 方法 | 路径 | 说明 |
|------|------|------|
| **POST** | `/api/v1/image/upload` | **上传并识别**。接收图片，保存并返回 AI 推理结果。 |
| **GET** | `/api/v1/image/file` | **获取图片**。根据 `upload_id` 返回图片二进制流。 |
| **GET** | `/api/v1/image/uploads` | **诊断记录**。返回最近上传的识别历史（混合真实与 Mock 数据）。 |

### 模型与健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 基础服务健康检查 |
| GET | `/api/v1/rice/health` | 水稻识别模型加载状态检查 |
| POST | `/api/v1/rice/predict` | 原始推理接口（仅推理，不保存） |

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
| `MODEL_CHECKPOINT_PATH` | 模型权重路径 | `models/rice/rice_leaf_classifier/best_model.pth` |
| `MODEL_ADVICE_FILE` | 病害处理建议映射表 | `models/rice/rice_leaf_classifier/advice_map.yaml` |

---
*Note: 此版本专为单机演示设计，如需恢复分布式或云端模式，请参考 git 历史中的 `enterprise-main` 分支。*
