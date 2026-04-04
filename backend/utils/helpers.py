#!/usr/bin/env python3
"""
通用工具函数模块

提供各种辅助函数，包括：
- 文件类型检查
- 日志记录
- 时间格式化
"""

from datetime import datetime
from typing import Set

from config import ALLOWED_EXTENSIONS


def allowed_file(filename: str) -> bool:
    """
    检查文件扩展名是否允许上传
    
    支持的格式：mp4, mkv, mov, flv, avi, webm
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否允许上传
        
    Example:
        >>> allowed_file("video.mp4")
        True
        >>> allowed_file("document.pdf")
        False
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_log(log_type: str, message: str, log_storage: list = None) -> None:
    """
    添加日志记录
    
    将日志条目添加到存储列表，并打印到控制台
    
    Args:
        log_type: 日志类型 ('info', 'success', 'error', 'warn', 'debug')
        message: 日志消息内容
        log_storage: 日志存储列表（可选，默认为 None）
        
    Example:
        >>> logs = []
        >>> add_log("info", "开始上传", logs)
        [2024-01-15 10:30:00] INFO: 开始上传
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        "type": log_type,
        "message": message,
        "timestamp": timestamp
    }
    
    if log_storage is not None:
        log_storage.append(log_entry)
    
    print(f"[{timestamp}] {log_type.upper()}: {message}")


def format_duration(seconds: float) -> str:
    """
    格式化时长为易读字符串
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化后的时长字符串
        
    Example:
        >>> format_duration(3661)
        '1小时1分1秒'
        >>> format_duration(45)
        '45秒'
    """
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒" if secs > 0 else f"{minutes}分"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分"


def truncate_filename(filename: str, max_length: int = 30) -> str:
    """
    截断文件名，保留开头和结尾
    
    用于在 UI 中显示过长的文件名
    
    Args:
        filename: 原始文件名
        max_length: 最大长度（默认 30）
        
    Returns:
        str: 截断后的文件名
        
    Example:
        >>> truncate_filename("very_long_filename_here.mp4", 20)
        'very_lo...here.mp4'
    """
    if len(filename) <= max_length:
        return filename
    
    ext_start = filename.rfind('.')
    if ext_start > 0:
        ext = filename[ext_start:]
        name = filename[:ext_start]
        keep = max_length - len(ext) - 3
        if keep > 5:
            return name[:keep] + '...' + ext
    
    return filename[:max_length - 3] + '...'


def safe_get(dictionary: dict, key: str, default=None):
    """
    安全获取字典值
    
    避免 KeyError，如果键不存在返回默认值
    
    Args:
        dictionary: 字典对象
        key: 键名
        default: 默认值
        
    Returns:
        键对应的值或默认值
    """
    return dictionary.get(key, default)
