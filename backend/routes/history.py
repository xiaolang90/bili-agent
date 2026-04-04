#!/usr/bin/env python3
"""
上传历史记录路由模块

处理上传历史相关的 API：
- 获取历史记录列表
- 删除单条历史
- 清空历史
- 导出历史为 CSV
"""

import csv
from datetime import datetime
from io import StringIO
from flask import Blueprint, request, jsonify

from database import db
from utils.helpers import add_log


def convert_to_cst(time_str):
    """
    将时间字符串转换为东八区（CST）时间
    
    Args:
        time_str: 原始时间字符串
        
    Returns:
        str: 东八区时间字符串，格式为 2024/01/15 10:30:00
    """
    if not time_str:
        return None
    
    try:
        # 解析原始时间
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        # 转换为东八区时间
        from datetime import timezone, timedelta
        cst_tz = timezone(timedelta(hours=8))
        dt_cst = dt.astimezone(cst_tz)
        # 格式化为字符串
        return dt_cst.strftime('%Y/%m/%d %H:%M:%S')
    except Exception:
        # 如果转换失败，返回原始值
        return time_str

# 创建蓝图
history_bp = Blueprint('history', __name__, url_prefix='/api')


@history_bp.route('/history', methods=['GET'])
def get_history():
    """
    获取上传历史记录
    
    Query Parameters:
        - page: 页码（默认1）
        - limit: 每页数量（默认100）
        
    Returns:
        JSON: 历史记录列表和分页信息
    """
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        offset = (page - 1) * limit
        history = db.get_upload_history(limit=limit, offset=offset)
        
        # 转换时间字段为东八区时间
        for item in history:
            if 'started_at' in item:
                item['started_at'] = convert_to_cst(item['started_at'])
            if 'finished_at' in item:
                item['finished_at'] = convert_to_cst(item['finished_at'])
            if 'created_at' in item:
                item['created_at'] = convert_to_cst(item['created_at'])
        
        return jsonify({
            "success": True,
            "data": history,
            "page": page,
            "limit": limit
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@history_bp.route('/history/<history_id>', methods=['DELETE'])
def delete_history_item(history_id):
    """
    删除单条上传历史记录
    
    Args:
        history_id: 历史记录ID
        
    Returns:
        JSON: 删除结果
    """
    try:
        deleted = db.delete_upload_history(history_id)
        
        if deleted:
            add_log("info", f"已删除上传历史: {history_id}")
            return jsonify({
                "success": True,
                "message": "记录已删除"
            })
        else:
            return jsonify({
                "success": False,
                "message": "记录不存在"
            }), 404
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@history_bp.route('/history/clear', methods=['POST'])
def clear_history():
    """
    清空所有上传历史记录
    
    Returns:
        JSON: 清空结果
    """
    try:
        db.clear_upload_history()
        
        add_log("info", "已清空上传历史")
        
        return jsonify({
            "success": True,
            "message": "历史已清空"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@history_bp.route('/history/export', methods=['GET'])
def export_history():
    """
    导出上传历史为 CSV 文件
    
    Returns:
        CSV: 包含所有历史记录的 CSV 文件
    """
    try:
        history = db.get_upload_history(limit=10000)
        
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['id', 'filename', 'title', 'status', 'message', 'duration', 'started_at']
        )
        writer.writeheader()
        
        for row in history:
            writer.writerow(row)
        
        return output.getvalue(), 200, {
            'Content-Disposition': 'attachment; filename=history.csv'
        }
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
