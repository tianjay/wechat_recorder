# 微信聊天记录读取器 - 项目规则

## 环境管理
- windows 开发/运行环境
- 使用 `uv` 作为Python包管理器和环境管理器
- Python版本: 3.9+
- 虚拟环境位置: `.venv` (项目根目录)

## 开发规范
- 代码风格: PEP 8
- 使用类型注解
- 模块化设计，功能分离

## 依赖管理
- 主要依赖: 
  - pyautogui: 自动化控制
  - opencv-python: 图像处理
  - pytesseract: OCR识别
  - pillow: 图像处理
  - numpy: 数值计算

## 项目结构
```
wechat_recorder/
├── src/
│   ├── core/           # 核心功能模块
│   ├── utils/          # 工具函数
│   └── main.py         # 主程序
├── tests/              # 测试代码
├── data/               # 数据文件
├── config/             # 配置文件
└── docs/               # 文档
```

## 开发命令
- `uv run python -m src.main`: 运行主程序
- `uv add <package>`: 添加依赖
- `uv sync`: 同步依赖
- `uv lock`: 锁定依赖版本

## 构建和部署
- 使用 `uv build` 构建项目
- 使用 `uv publish` 发布包(可选)

## 版本控制
- 使用语义化版本控制
- 主版本.次版本.修订版本 (MAJOR.MINOR.PATCH)