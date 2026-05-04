# AI-Agriculture (AIT103 演示版 - 水稻 + 实时摄像头)

这是一个针对 AIT103 课程优化的智慧农业 AI 系统原型。它展示了如何将水稻叶片病害识别模型集成到现代 Web 仪表盘中，并支持**手机端实时摄像头拍摄识别**。

## 核心亮点
- **实时摄像头 (加分项)**：支持在浏览器中直接调用摄像头，周期性抓取帧并上传进行 AI 推理，模拟田间实时监控。
- **水稻专属仪表盘**：精美的前端界面，实时展示环境传感器数据（模拟）与 AI 诊断历史。
- **全 Python 架构**：无需配置数据库或 Rust 环境，在 Windows 本地一键启动。

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
   - **主仪表盘**: [http://localhost:8000/rice_dashboard.html](http://localhost:8000/rice_dashboard.html)
   - **实时摄像头页面**: [http://localhost:8000/mobile_live_capture.html](http://localhost:8000/mobile_live_capture.html)

## 目录结构
- `ai_engine/`：后端推理服务逻辑（FastAPI）。
- `frontend/rice/`：系统前端代码，包含仪表盘与摄像头采集页面。
- `models/`：AI 模型权重文件（水稻分类器）。
- `scripts/`：包含 `without_bounding_box_kaggle_baseline.py` 等核心训练脚本。
- `local_data/`：测试用的示例数据。

## 演示技巧 (必看)
1. **启动服务**后，先在电脑或手机上打开 `mobile_live_capture.html`。
2. 点击“启动摄像头”，然后点击“开始循环上传”。
3. 随后回到主仪表盘页面，你会发现“视觉 AI 反馈”面板会实时刷新你刚刚拍摄到的画面和诊断结果。

## 许可证
本项目使用 MIT License。
