#!/usr/bin/env python3
"""
统计和日志路由模块

处理统计数据和日志相关的 API：
- 获取统计信息
- 获取日志
- 清空日志
- 健康检查
"""

from flask import Blueprint, jsonify

from database import db
from utils.helpers import add_log

# 创建蓝图
stats_bp = Blueprint('stats', __name__, url_prefix='/api')

# 全局日志存储
upload_log = []


@stats_bp.route('/health', methods=['GET'])
def health():
    """
    健康检查端点
    
    用于检查服务器是否正常运行
    
    Returns:
        JSON: 健康状态
    """
    return jsonify({
        "status": "ok",
        "message": "服务器正常运行"
    })


@stats_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    获取统计信息
    
    返回视频和上传的统计数据：
    - 总视频数
    - 各状态视频数量
    - 成功/失败上传数
    
    Returns:
        JSON: 统计数据
    """
    try:
        stats = db.get_stats()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@stats_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    获取上传日志
    
    Returns:
        JSON: 日志列表
    """
    return jsonify({
        "logs": upload_log
    })


@stats_bp.route('/logs/clear', methods=['POST'])
def clear_logs():
    """
    清空上传日志
    
    Returns:
        JSON: 清空结果
    """
    global upload_log
    upload_log = []
    return jsonify({
        "success": True,
        "message": "日志已清空"
    })


def get_log_storage():
    """
    获取日志存储列表
    
    Returns:
        list: 日志存储列表的引用
    """
    return upload_log
