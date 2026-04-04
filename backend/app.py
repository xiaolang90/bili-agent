#!/usr/bin/env python3
"""
Flask 应用主入口

此模块创建 Flask 应用实例，注册所有蓝图，配置静态文件服务。

启动方式：
    python run.py
    
或直接使用：
    python -m backend.app
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from config import UPLOAD_FOLDER, MAX_FILE_SIZE, SERVER_HOST, SERVER_PORT, DEBUG_MODE
from routes import auth_bp, upload_bp, history_bp, templates_bp, stats_bp
from routes.upload_sse import upload_sse_bp


def create_app() -> Flask:
    """
    创建并配置 Flask 应用
    
    Returns:
        Flask: 配置好的 Flask 应用实例
    """
    # 创建 Flask 应用
    # static_folder 指向 static 目录，用于服务前端文件
    app = Flask(__name__, 
                static_folder='../static',
                static_url_path='')
    
    # 配置
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    # 启用跨域支持
    CORS(app)
    
    # 注册蓝图
    _register_blueprints(app)
    
    # 注册错误处理
    _register_error_handlers(app)
    
    # 注册首页路由
    @app.route('/')
    def index():
        """首页 - 返回前端页面"""
        return send_from_directory('../static', 'index.html')
    
    # 注册配置文件路由
    @app.route('/config/bilibili_tid_mapping.json')
    def serve_tid_mapping():
        """提供B站分类映射配置文件"""
        return send_from_directory('config', 'bilibili_tid_mapping.json')
    
    return app


def _register_blueprints(app: Flask) -> None:
    """
    注册所有 Flask Blueprint
    
    Args:
        app: Flask 应用实例
    """
    # 认证相关路由
    app.register_blueprint(auth_bp)
    
    # 上传相关路由
    app.register_blueprint(upload_bp)
    
    # 历史记录路由
    app.register_blueprint(history_bp)
    
    # 配置模板路由
    app.register_blueprint(templates_bp)
    
    # 统计和日志路由
    app.register_blueprint(stats_bp)
    
    # SSE 同步上传路由
    app.register_blueprint(upload_sse_bp)


def _register_error_handlers(app: Flask) -> None:
    """
    注册错误处理函数
    
    Args:
        app: Flask 应用实例
    """
    @app.errorhandler(413)
    def too_large(e):
        """文件过大错误"""
        return {
            "success": False,
            "message": "文件过大，超过100GB限制"
        }, 413
    
    @app.errorhandler(500)
    def internal_error(e):
        """服务器内部错误"""
        return {
            "success": False,
            "message": "服务器内部错误"
        }, 500


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    print("=" * 60)
    print("B站视频上传工具 - 重构版后端服务器")
    print("=" * 60)
    print(f"\n📡 侦听地址: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"🌐 前端访问: http://{SERVER_HOST}:{SERVER_PORT}")
    print("\n[模块结构]")
    print("   backend/")
    print("   ├── config.py          - 配置常量")
    print("   ├── database.py        - 数据库操作")
    print("   ├── uploader_core.py   - B站上传核心")
    print("   ├── app.py             - Flask 应用")
    print("   ├── routes/")
    print("   │   ├── auth.py        - 认证路由")
    print("   │   ├── upload.py      - 上传路由")
    print("   │   ├── history.py     - 历史记录路由")
    print("   │   ├── config_templates.py - 配置模板路由")
    print("   │   └── stats.py       - 统计路由")
    print("   └── utils/")
    print("       ├── helpers.py     - 通用工具")
    print("       └── video.py       - 视频处理")
    print("\n" + "=" * 60)
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
