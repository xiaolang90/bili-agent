#!/usr/bin/env python3
"""
上传 SSE 实时进度推送模块

处理视频上传的同步上传和实时进度推送。
使用 SSE (Server-Sent Events) 向前端推送上传进度。
"""

import os
import json
import time
import queue
import threading
from flask import Blueprint, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename

from config import UPLOAD_FOLDER
from database import db
from utils.helpers import add_log, allowed_file
from routes.auth import get_current_uploader

# 创建蓝图
upload_sse_bp = Blueprint('upload_sse', __name__, url_prefix='/api')

# 全局进度队列，用于 SSE 推送
progress_queues = {}

# 全局取消标志，用于取消上传
cancel_flags = {}


def get_progress_queue(upload_id):
    """获取或创建进度队列"""
    if upload_id not in progress_queues:
        progress_queues[upload_id] = queue.Queue()
    return progress_queues[upload_id]


def set_cancel_flag(upload_id):
    """设置取消标志"""
    cancel_flags[upload_id] = True


def clear_cancel_flag(upload_id):
    """清除取消标志"""
    if upload_id in cancel_flags:
        del cancel_flags[upload_id]


def is_cancelled(upload_id):
    """检查是否已取消"""
    return cancel_flags.get(upload_id, False)


def send_progress(upload_id, progress, message, status='uploading'):
    """发送进度更新"""
    if upload_id in progress_queues:
        data = {
            'progress': progress,
            'message': message,
            'status': status,
            'timestamp': time.time()
        }
        progress_queues[upload_id].put(data)


def cleanup_progress_queue(upload_id):
    """清理进度队列"""
    if upload_id in progress_queues:
        del progress_queues[upload_id]


@upload_sse_bp.route('/upload/progress/<upload_id>')
def upload_progress(upload_id):
    """
    SSE 端点：获取上传进度
    
    客户端通过 EventSource 连接此端点接收实时进度
    """
    def generate():
        q = get_progress_queue(upload_id)
        
        # 发送初始连接成功消息
        yield f"data: {json.dumps({'type': 'connected', 'upload_id': upload_id})}\n\n"
        
        while True:
            try:
                # 等待进度更新，超时 30 秒
                data = q.get(timeout=30)
                yield f"data: {json.dumps(data)}\n\n"
                
                # 如果上传完成或出错，结束 SSE 连接
                if data.get('status') in ['completed', 'error']:
                    break
            except queue.Empty:
                # 发送心跳保持连接
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        # 清理队列
        cleanup_progress_queue(upload_id)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'  # 禁用 Nginx 缓冲
        }
    )


@upload_sse_bp.route('/upload/cancel/<upload_id>', methods=['POST'])
def cancel_upload(upload_id):
    """
    取消上传
    
    设置取消标志，通知上传线程停止
    """
    try:
        set_cancel_flag(upload_id)
        send_progress(upload_id, 0, "已取消", "cancelled")
        add_log("info", f"上传已取消: {upload_id}")
        return jsonify({
            "success": True,
            "message": "上传已取消"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@upload_sse_bp.route('/upload/sync', methods=['POST'])
def upload_sync():
    """
    同步上传视频文件
    
    接收文件后立即开始上传，通过 SSE 推送进度
    
    Request:
        - file: 视频文件
        - title: 视频标题
        - desc: 视频描述
        - tags: 视频标签
        - tid: 分类ID
        - upload_id: 用于 SSE 进度推送的唯一ID
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
        upload_id = request.form.get('upload_id', '')
        
        # 保存临时文件
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)
        
        add_log("info", f"开始同步上传: {filename}")
        
        # 执行同步上传
        try:
            # 导入 asyncio 用于运行异步上传代码
            import asyncio
            
            # 定义进度回调函数 - 直接使用后端返回的原始进度值
            def progress_callback(progress, message):
                if upload_id:
                    send_progress(upload_id, progress, message, "uploading")
            
            # 创建事件循环运行上传
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行上传 - 传入 task_id 以启用进度跟踪日志
            result = loop.run_until_complete(
                uploader.upload_video(
                    video_path=temp_path,
                    title=title,
                    desc=desc,
                    tags=tags,
                    tid=tid,
                    original=original,
                    no_reprint=no_reprint,
                    task_id=upload_id,
                    progress_callback=progress_callback
                )
            )
            loop.close()
            
            # 添加到数据库
            video_id = db.add_video(filename, title, desc, tags)
            
            if result.get('success'):
                # 添加上传历史
                db.add_upload_history(
                    video_id=video_id,
                    filename=filename,
                    title=title,
                    status='success',
                    message='上传成功',
                    duration=result.get('duration', 0)
                )
                
                # 发送完成进度
                if upload_id:
                    send_progress(upload_id, 100, "上传成功", "completed")
                
                add_log("success", f"上传成功: {title}")
                
                return jsonify({
                    "success": True,
                    "message": "上传成功",
                    "video_id": video_id,
                    "data": result
                })
            else:
                # 添加上传历史（失败）
                db.add_upload_history(
                    video_id=video_id,
                    filename=filename,
                    title=title,
                    status='error',
                    message=result.get('message', '上传失败'),
                    duration=result.get('duration', 0)
                )
                
                # 发送错误进度
                if upload_id:
                    error_msg = result.get('message', '上传失败')
                    # 处理特定的网络错误
                    if "Cannot connect to host" in error_msg or "nodename nor servname" in error_msg:
                        error_msg = "无法连接到B站服务器，请检查网络连接或稍后重试"
                    send_progress(upload_id, 0, error_msg, "error")
                
                add_log("error", f"上传失败: {title} - {result.get('message')}")
                
                return jsonify({
                    "success": False,
                    "message": result.get('message', '上传失败'),
                    "video_id": video_id
                })
                
        except Exception as upload_error:
            # 发送错误进度
            if upload_id:
                error_msg = str(upload_error)
                # 处理特定的网络错误
                if "Cannot connect to host" in error_msg or "nodename nor servname" in error_msg:
                    error_msg = "无法连接到B站服务器，请检查网络连接或稍后重试"
                send_progress(upload_id, 0, error_msg, "error")
            
            raise upload_error
            
    except Exception as e:
        add_log("error", f"上传失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
