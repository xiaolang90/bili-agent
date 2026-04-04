#!/usr/bin/env python3
"""
B站视频上传工具 - 重构版启动脚本

这是重构后项目的启动入口。

使用方法：
    python run.py
    
特性：
    - 端口 5001
    - 独立的数据库文件
    - 模块化的代码结构
    - 详细的代码注释

项目结构：
    bilibili-uploader-refactored/
    ├── run.py              # 启动脚本
    ├── backend/            # 后端代码
    │   ├── app.py          # Flask 应用
    │   ├── config.py       # 配置
    │   ├── database.py     # 数据库
    │   ├── uploader_core.py # 上传核心
    │   ├── routes/         # 路由模块
    │   └── utils/          # 工具模块
    └── static/             # 前端代码
        ├── index.html
        ├── css/
        └── js/
"""

import sys
import os

# 将 backend 目录添加到 Python 路径
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 导入并运行应用
from app import app, SERVER_HOST, SERVER_PORT, DEBUG_MODE

if __name__ == '__main__':
    print("=" * 60)
    print("B站视频上传工具 - 重构版")
    print("=" * 60)
    print(f"\n🚀 启动服务器...")
    print(f"📡 端口: {SERVER_PORT}")
    print(f"🌐 访问: http://{SERVER_HOST}:{SERVER_PORT}")
    print("=" * 60 + "\n")
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
