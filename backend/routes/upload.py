#!/usr/bin/env python3
"""
上传相关路由模块

处理视频文件上传的 API：
- 文件上传接收
- 上传任务创建
- 上传队列管理
"""

import os
import asyncio
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from config import UPLOAD_FOLDER
from database import db
from utils.helpers import add_log, allowed_file
from routes.auth import get_current_uploader

# 创建蓝图
upload_bp = Blueprint('upload', __name__, url_prefix='/api')


@upload_bp.route('/upload/file', methods=['POST'])
def upload_file():
    """
    接收上传的视频文件
    
    处理流程：
    1. 验证上传器是否已初始化
    2. 验证文件是否存在且格式正确
    3. 保存到临时目录
    4. 创建视频记录和上传任务
    
    Request:
        - file: 视频文件
        - title: 视频标题（可选，默认使用文件名）
        - desc: 视频描述
        - tags: 视频标签
        - tid: 分类ID
        
    Returns:
        JSON: 包含 task_id 的任务创建结果
    """
    uploader = get_current_uploader()
    
    try:
        if uploader is None:
            return jsonify({
                "success": False,
                "message": "您需要先录入B站登录信息"
            }), 400
        
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "message": "未上传文件"
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "success": False,
                "message": "文件名为空"
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "message": "不支持的文件格式"
            }), 400
        
        # 获取上传参数
        title = request.form.get('title', file.filename)
        desc = request.form.get('desc', '')
        tags = request.form.get('tags', '')
        tid = request.form.get('tid', '202', type=int)
        original = request.form.get('original', 'true').lower() == 'true'
        no_reprint = request.form.get('no_reprint', 'true').lower() == 'true'
        
        # 保存临时文件
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)
        
        # 添加到数据库
        video_id = db.add_video(filename, title, desc, tags)
        
        add_log("info", f"文件已保存: {filename}")
        
        # 返回视频ID，前端可以继续轮询状态
        return jsonify({
            "success": True,
            "video_id": video_id,
            "message": "文件已接收，开始上传"
        })
    
    except Exception as e:
        add_log("error", f"上传失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@upload_bp.route('/videos', methods=['GET'])
def get_videos():
    """
    获取视频列表
    
    Query Parameters:
        - page: 页码（默认1）
        - limit: 每页数量（默认20）
        - status: 按状态筛选（可选）
        
    Returns:
        JSON: 视频列表和分页信息
    """
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status', None, type=str)
        
        offset = (page - 1) * limit
        videos = db.get_videos(status=status, limit=limit, offset=offset)
        
        return jsonify({
            "success": True,
            "data": videos,
            "page": page,
            "limit": limit
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@upload_bp.route('/videos/<video_id>/delete', methods=['POST'])
def delete_video(video_id):
    """
    删除视频记录
    
    Args:
        video_id: 视频ID
        
    Returns:
        JSON: 删除结果
    """
    try:
        db.delete_video(video_id)
        add_log("info", f"已删除视频: {video_id}")
        
        return jsonify({
            "success": True,
            "message": "视频已删除"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@upload_bp.route('/videos/<video_id>/update', methods=['POST'])
def update_video(video_id):
    """
    更新视频信息
    
    Request Body:
        - title: 新标题（可选）
        - description: 新描述（可选）
        - tags: 新标签（可选）
        - status: 新状态（可选）
        
    Returns:
        JSON: 更新结果
    """
    try:
        data = request.get_json() or {}
        
        # 这里简化处理，实际应该使用数据库的 update 方法
        # 为了简化，先获取连接直接更新
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # 只更新提供的字段
        if 'title' in data:
            cursor.execute('UPDATE videos SET title = ? WHERE id = ?', (data['title'], video_id))
        if 'description' in data:
            cursor.execute('UPDATE videos SET description = ? WHERE id = ?', (data['description'], video_id))
        if 'tags' in data:
            cursor.execute('UPDATE videos SET tags = ? WHERE id = ?', (data['tags'], video_id))
        if 'status' in data:
            cursor.execute('UPDATE videos SET status = ? WHERE id = ?', (data['status'], video_id))
        
        cursor.execute('UPDATE videos SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (video_id,))
        conn.commit()
        conn.close()
        
        add_log("info", f"已更新视频: {video_id}")
        
        return jsonify({
            "success": True,
            "message": "视频已更新"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
