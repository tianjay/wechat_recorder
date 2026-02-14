# 微信聊天记录读取器 (WeChat Recorder)

一个基于 Windows UI 自动化和图像识别技术的微信聊天记录提取工具。通过模拟用户操作（滚动、点击）并结合 OCR 技术，自动从 PC 端微信窗口中提取聊天记录（文本、图片、文件）。

## ⚠️ Windows 环境开发须知

本项目依赖于 Windows 系统的 UI 交互和屏幕图像，开发和运行时请注意：

1.  **DPI 缩放影响**：Windows 的显示缩放（如 125%, 150%）会影响坐标计算。**强烈建议在开发和运行时将系统显示缩放设置为 100%**，或在代码中显式处理 DPI 转换。
2.  **窗口独占性**：程序运行时需要控制鼠标和键盘，且微信窗口必须保持在前台可见。**建议在虚拟机或闲置 PC 上运行**，以免干扰正常工作。
3.  **微信版本差异**：不同版本的 PC 微信 UI 布局可能微调，建议固定使用最新稳定版进行适配。
4.  **性能消耗**：实时 OCR 和图像匹配消耗较高 CPU/GPU 资源。

## 核心架构与技术栈

项目采用分层架构，将控制逻辑、视觉处理和数据存储分离：

### 1. 控制层 (Controller Layer)
负责窗口定位、元素交互和输入模拟。
-   **uiautomation**: 优先使用。通过 Windows Accessibility API 直接获取微信窗口句柄、位置和部分控件树，比图像识别更稳定。
-   **pywin32**: 辅助窗口管理。
-   **PyAutoGUI**: 用于 `uiautomation` 无法覆盖的自定义绘图区域的点击和滚动模拟。

### 2. 视觉层 (Vision Layer)
负责屏幕捕获、图像预处理和内容识别。
-   **OpenCV**: 用于图像预处理（二值化、去噪）、聊天气泡轮廓检测、以及滚动时的图像拼接（特征匹配）。
-   **Tesseract OCR**: 基础 OCR 引擎，用于提取文本。
-   **Pillow**: 图像格式转换与裁剪。

### 3. 数据层 (Data Layer)
负责数据清洗、结构化和持久化。
-   **Pandas/SQLite**: 结构化存储聊天记录。
-   **Deduplicator**: 基于图像特征或文本内容的去重算法（处理滚动产生的重复内容）。

## 安装与配置

### 环境要求
-   Windows 10/11
-   Python 3.9+
-   Tesseract OCR (需安装并配置 PATH)

### 安装依赖
推荐使用 `uv` 进行包管理：

```bash
# 安装 uv (如果尚未安装)
pip install uv

# 创建虚拟环境并同步依赖
uv venv
uv pip install -r requirements.txt
```

## 使用方法

1.  **准备环境**：确保显示缩放为 100%，安装好 Tesseract OCR。
2.  **启动微信**：登录 PC 微信，并打开要提取的聊天窗口。
3.  **运行程序**：
    ```bash
    python -m src.main
    ```
4.  **操作提示**：程序启动后会自动寻找微信窗口。请勿移动鼠标或遮挡窗口。按 `Ctrl+C` 或预设热键停止录制。

## 项目结构

```
wechat_recorder/
├── src/
│   ├── core/
│   │   ├── controller.py   # 窗口控制与输入模拟
│   │   ├── capturer.py     # 屏幕截图与图像获取
│   │   ├── parser.py       # OCR 与内容解析
│   │   └── recorder.py     # 主录制流程控制
│   ├── utils/              # 图像处理、日志等工具
│   └── main.py             # 入口文件
├── config/                 # 配置文件
├── data/                   # 抓取结果存储
├── docs/                   # 开发文档
├── tests/                  # 测试用例
└── requirements.txt
```

## 许可证

MIT License
