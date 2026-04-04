#!/usr/bin/env python3
"""
路由模块

集中导出所有 Flask Blueprint，便于在 app.py 中统一注册。

使用方式：
    from routes import auth_bp, upload_bp, history_bp, templates_bp, stats_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    ...
"""

from .auth import auth_bp
from .upload import upload_bp
from .history import history_bp
from .config_templates import templates_bp
from .stats import stats_bp

__all__ = [
    'auth_bp',
    'upload_bp',
    'history_bp',
    'templates_bp',
    'stats_bp',
]
