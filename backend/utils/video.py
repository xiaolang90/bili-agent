#!/usr/bin/env python3
"""
视频处理工具模块

提供视频相关的处理功能：
- 从视频截取封面图片
- 获取视频信息
- 视频格式转换相关

依赖：
    - ffmpeg: 用于视频封面提取
"""

import os
import time
import random
import subprocess
from pathlib import Path
from typing import Optional

from config import FFMPEG_PATH, COVER_EXTRACT_TIMEOUT, COVER_TIME_OFFSET, UPLOAD_FOLDER
from utils.helpers import add_log


def extract_video_cover(video_path: str, time_offset: int = COVER_TIME_OFFSET) -> Optional[str]:
    """
    从视频截取指定时间点作为封面图片
    
    使用 ffmpeg 从视频中提取一帧作为封面。如果指定时间点提取失败，
    会自动降级尝试提取第一帧。
    
    Args:
        video_path: 视频文件路径
        time_offset: 截取时间点（秒），默认 10 秒
        
    Returns:
        Optional[str]: 封面图片的临时文件路径，失败则返回 None
        
    Example:
        >>> cover = extract_video_cover("/path/to/video.mp4", 10)
        >>> if cover:
        ...     print(f"封面已生成: {cover}")
    
    Note:
        生成的封面文件为临时文件，使用完毕后需要手动删除
    """
    
    def try_extract(offset: int) -> Optional[str]:
        """
        尝试从指定时间点提取封面
        
        Args:
            offset: 时间点（秒）
            
        Returns:
            Optional[str]: 封面文件路径或 None
        """
        try:
            # 生成临时文件名（确保是 .jpg）
            temp_cover = os.path.join(
                UPLOAD_FOLDER,
                f"bilibili_cover_{int(time.time())}_{random.randint(1000, 9999)}.jpg"
            )
            
            # 使用 ffmpeg 截取指定时间的帧
            # 关键：-ss 必须在 -i 之前（快速寻址）
            cmd = [
                FFMPEG_PATH,
                '-ss', str(offset),  # 快速寻址
                '-i', video_path,
                '-vframes', '1',  # 只取1帧
                '-q:v', '2',  # 质量参数 (1=最高, 31=最低)
                '-y',  # 覆盖输出文件
                temp_cover
            ]
            
            # 执行命令（抑制 ffmpeg 的详细输出）
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=COVER_EXTRACT_TIMEOUT
            )
            
            # 检查文件是否成功生成
            if os.path.exists(temp_cover) and os.path.getsize(temp_cover) > 0:
                add_log("success", f"已从视频第{offset}秒截取封面 ({os.path.getsize(temp_cover)} 字节)")
                return temp_cover
            else:
                return None
        
        except Exception as e:
            add_log("debug", f"第{offset}秒提取失败: {str(e)[:100]}")
            return None
    
    try:
        # 第一步：尝试在指定时间点提取
        result = try_extract(time_offset)
        if result:
            return result
        
        # 第二步：改为提取第一帧
        add_log("warn", f"无法在第{time_offset}秒提取封面，改为提取第一帧")
        result = try_extract(0)
        if result:
            return result
        
        # 第三步：如果还是失败，返回 None（上传功能会使用占位符）
        add_log("error", "无法从视频提取任何封面，将使用占位符")
        return None
    
    except FileNotFoundError:
        add_log("warn", "ffmpeg 未安装，无法自动生成封面")
        return None
    except subprocess.TimeoutExpired:
        add_log("warn", "截取封面超时（>30秒）")
        return None
    except Exception as e:
        add_log("warn", f"截取封面异常: {str(e)[:100]}")
        return None


def get_video_info(video_path: str) -> dict:
    """
    获取视频文件信息
    
    使用 ffprobe 获取视频的元数据信息
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        dict: 包含视频信息的字典
        
    Example:
        >>> info = get_video_info("video.mp4")
        >>> print(f"时长: {info['duration']}秒")
        >>> print(f"分辨率: {info['width']}x{info['height']}")
    """
    info = {
        'duration': 0,
        'width': 0,
        'height': 0,
        'size': 0,
        'format': ''
    }
    
    try:
        # 获取文件大小
        if os.path.exists(video_path):
            info['size'] = os.path.getsize(video_path)
        
        # 使用 ffprobe 获取视频信息
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration',
            '-show_entries', 'format=duration',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            # 解析视频流信息
            if 'streams' in data and len(data['streams']) > 0:
                stream = data['streams'][0]
                info['width'] = int(stream.get('width', 0))
                info['height'] = int(stream.get('height', 0))
            
            # 解析格式信息
            if 'format' in data:
                duration = data['format'].get('duration', '0')
                info['duration'] = float(duration) if duration else 0
        
        # 获取文件格式
        info['format'] = Path(video_path).suffix.lower().lstrip('.')
        
    except FileNotFoundError:
        add_log("warn", "ffprobe 未安装，无法获取视频信息")
    except Exception as e:
        add_log("debug", f"获取视频信息失败: {str(e)[:100]}")
    
    return info


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为易读字符串
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的大小字符串
        
    Example:
        >>> format_file_size(1024)
        '1.00 KB'
        >>> format_file_size(1048576)
        '1.00 MB'
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
