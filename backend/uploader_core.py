#!/usr/bin/env python3
"""
B站视频上传核心模块

封装 BilibiliUploader 类，处理视频上传到 B站 的核心逻辑。

依赖：
    - bilibili-api-python: B站 API 封装库
    
使用示例：
    from uploader_core import BilibiliUploader
    
    uploader = BilibiliUploader(sessdata, bili_jct, buvid3)
    result = await uploader.upload_video(
        video_path="/path/to/video.mp4",
        title="视频标题",
        desc="视频描述",
        tags="标签1,标签2",
        tid=201
    )
"""

import os
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Callable

try:
    from bilibili_api import video_uploader, Credential
except ImportError:
    video_uploader = None
    Credential = None

from utils.helpers import add_log
from utils.video import extract_video_cover


class BilibiliUploader:
    """
    B站视频上传器
    
    封装 bilibili-api-python 库，提供视频上传功能。
    支持进度跟踪、封面提取、取消上传等功能。
    
    Attributes:
        credential: B站认证凭据
        results: 上传结果列表
        current_task: 当前正在执行的任务 ID
    """
    
    def __init__(self, sessdata: str, bili_jct: str, buvid3: str):
        """
        初始化上传器
        
        Args:
            sessdata: B站 SESSDATA Cookie
            bili_jct: B站 bili_jct Cookie
            buvid3: B站 buvid3 Cookie
            
        Raises:
            RuntimeError: 如果 bilibili-api-python 未安装
        """
        if Credential is None:
            raise RuntimeError("bilibili-api-python 未安装")
        
        self.credential = Credential(
            sessdata=sessdata,
            bili_jct=bili_jct,
            buvid3=buvid3
        )
        self.results = []
        self.current_task = None
    
    async def upload_video(
        self,
        video_path: str,
        title: str,
        desc: str = "",
        tags: str = "",
        tid: int = 208,
        original: bool = True,
        no_reprint: bool = True,
        cover_path: Optional[str] = None,
        task_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        上传单个视频到 B站
        
        完整的上传流程：
        1. 提取视频封面（如果未提供）
        2. 创建视频页面和元数据
        3. 设置进度跟踪回调
        4. 执行上传
        5. 清理临时文件
        
        Args:
            video_path: 视频文件路径
            title: 视频标题
            desc: 视频描述
            tags: 视频标签，逗号分隔
            tid: 视频分类 ID（默认 202=生活->日常）
            original: 是否为原创
            no_reprint: 是否禁止转载
            cover_path: 封面图片路径（可选，自动提取）
            task_id: 任务 ID（用于进度跟踪）
            progress_callback: 进度回调函数，接收 (progress, message)
            cancel_check: 取消检查函数，返回 True 表示取消上传
            
        Returns:
            Dict[str, Any]: 上传结果
                - success: 是否成功
                - message: 结果消息
                - filename: 文件名
                - title: 视频标题
                - duration: 上传耗时（秒）
        """
        temp_cover = None
        start_time = datetime.now()
        self.current_task = task_id
        
        try:
            add_log("info", f"开始上传: {Path(video_path).name}")
            
            if progress_callback:
                progress_callback(0, "准备上传...")
            
            # 如果没有提供封面，自动从视频第10秒截取
            if not cover_path:
                temp_cover = extract_video_cover(video_path, time_offset=10)
                if temp_cover:
                    cover_path = temp_cover
            
            # 创建视频页面
            page = video_uploader.VideoUploaderPage(
                path=video_path,
                title=title
            )
            
            # 处理标签
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            
            # 创建元数据
            meta = video_uploader.VideoMeta(
                tid=tid,
                title=title,
                desc=desc,
                cover=cover_path if cover_path else video_path,
                tags=tag_list,
                original=original,
                no_reprint=no_reprint
            )
            
            # 创建上传器
            uploader = video_uploader.VideoUploader(
                pages=[page],
                meta=meta,
                credential=self.credential
            )
            
            # 设置进度跟踪
            if task_id:
                self._setup_progress_tracking(
                    uploader, task_id, page,
                    progress_callback, cancel_check
                )
            
            # 执行上传
            add_log("info", f"正在上传视频: {title}")
            await uploader.start()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "message": "上传成功",
                "filename": Path(video_path).name,
                "title": title,
                "duration": duration
            }
            add_log("success", f"上传成功: {title}")
            
            if progress_callback:
                progress_callback(100, "上传成功")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            result = {
                "success": False,
                "message": str(e),
                "filename": Path(video_path).name,
                "title": title,
                "duration": duration
            }
            add_log("error", f"上传失败: {title} - {str(e)}")
            
            if progress_callback:
                progress_callback(0, str(e))
        
        finally:
            self.current_task = None
            # 清理临时生成的封面文件
            if temp_cover and os.path.exists(temp_cover):
                try:
                    os.remove(temp_cover)
                    add_log("info", "已清理临时封面文件")
                except Exception as e:
                    add_log("warn", f"清理临时文件失败: {str(e)}")
        
        self.results.append(result)
        return result
    
    def _setup_progress_tracking(
        self,
        uploader,
        task_id: str,
        page,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> None:
        """
        设置上传进度跟踪
        
        绑定各种上传事件，实时更新进度。参考实现中使用了事件驱动的方式来跟踪上传进度。
        
        Args:
            uploader: VideoUploader 实例
            task_id: 任务 ID
            page: VideoUploaderPage 实例
            progress_callback: 进度回调函数
            cancel_check: 取消检查函数
        """
        total_chunks = 0
        uploaded_chunks = 0
        last_progress = 0
        last_update_time = 0
        
        # 日志文件路径
        log_dir = os.path.join(os.path.dirname(__file__), 'log')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'upload_progress_{task_id}.log')
        
        def write_log(message):
            """写入进度日志"""
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_line = f"[{timestamp}] {message}\n"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
            # 同时输出到控制台
            print(f"[进度日志] {message}")
        
        # 初始化日志
        write_log(f"=== 开始上传任务: {task_id} ===")
        write_log(f"视频文件: {page.path if hasattr(page, 'path') else 'unknown'}")
        write_log(f"文件大小: {page.get_size() / 1024 / 1024:.2f} MB")
        
        def check_cancelled():
            """检查任务是否被取消"""
            if cancel_check:
                return cancel_check()
            return False
        
        def update_progress(progress, message, force=False):
            """更新进度，控制更新频率避免过于频繁"""
            nonlocal last_progress, last_update_time
            
            if not progress_callback:
                return
            
            current_time = time.time()
            
            # 强制更新、进度变化超过1%、或超过0.5秒未更新
            if force or progress != last_progress or (current_time - last_update_time) > 0.5:
                progress_callback(progress, message)
                last_progress = progress
                last_update_time = current_time
        
        # 预上传事件 - 获取文件信息
        @uploader.on(video_uploader.VideoUploaderEvents.PREUPLOAD.value)
        def on_preupload(event):
            nonlocal total_chunks
            if check_cancelled():
                raise Exception("任务已取消")
            
            # PREUPLOAD 事件的数据结构不同，event 是 {"page": page}
            page_data = event.get('page', page)
            file_size = page_data.get_size() if hasattr(page_data, 'get_size') else page.get_size()
            
            write_log(f"[PREUPLOAD] 事件触发")
            write_log(f"[PREUPLOAD] 文件大小: {file_size / 1024 / 1024:.2f} MB")
            write_log(f"[PREUPLOAD] 事件数据: {event}")
            
            update_progress(5, f"准备上传... ({file_size / 1024 / 1024:.1f}MB)", force=True)
        
        # 分块上传前事件
        @uploader.on(video_uploader.VideoUploaderEvents.PRE_CHUNK.value)
        def on_pre_chunk(event):
            nonlocal total_chunks
            if check_cancelled():
                raise Exception("任务已取消")
            
            # event 直接就是 chunk_event_callback_data 字典
            chunk_num = event.get('chunk_number', 0)
            total = event.get('total_chunk_count', 0)
            offset = event.get('offset', 0)
            
            # 更新总分块数（从事件中获取真实的分块数）
            if total > 0:
                total_chunks = total
            
            # 确保 total_chunks 至少为 1，避免除零错误
            effective_total = max(total_chunks, 1)
            
            # 计算进度 (5% 准备 + 90% 上传 + 5% 提交)
            # 限制进度在 5-95 之间，避免超过100%
            if effective_total > 0:
                progress = min(95, 5 + int((chunk_num / effective_total) * 90))
            else:
                progress = 5
            
            write_log(f"[PRE_CHUNK] 事件触发")
            write_log(f"[PRE_CHUNK] 分块编号: {chunk_num + 1}/{effective_total}")
            write_log(f"[PRE_CHUNK] 原始 total: {total}, total_chunks: {total_chunks}")
            write_log(f"[PRE_CHUNK] 偏移量: {offset}")
            write_log(f"[PRE_CHUNK] 事件数据: {event}")
            write_log(f"[PRE_CHUNK] 计算进度: {progress}%")
            
            update_progress(progress, f"上传中... {chunk_num + 1}/{effective_total}")
        
        # 分块上传后事件
        @uploader.on(video_uploader.VideoUploaderEvents.AFTER_CHUNK.value)
        def on_after_chunk(event):
            nonlocal uploaded_chunks, total_chunks
            if check_cancelled():
                raise Exception("任务已取消")
            
            # event 直接就是 chunk_event_callback_data 字典
            chunk_num = event.get('chunk_number', 0)
            total = event.get('total_chunk_count', 0)
            offset = event.get('offset', 0)
            
            # 更新总分块数（从事件中获取真实的分块数）
            if total > 0:
                total_chunks = total
            
            uploaded_chunks += 1
            
            # 确保 total_chunks 至少为 1，避免除零错误
            effective_total = max(total_chunks, 1)
            
            # 计算进度 (5% 准备 + 90% 上传 + 5% 提交)
            # 限制进度在 5-95 之间，避免超过100%
            if effective_total > 0:
                progress = min(95, 5 + int((uploaded_chunks / effective_total) * 90))
            else:
                progress = 5
            
            write_log(f"[AFTER_CHUNK] 事件触发")
            write_log(f"[AFTER_CHUNK] 已完成分块: {uploaded_chunks}/{effective_total}")
            write_log(f"[AFTER_CHUNK] 原始 total: {total}, total_chunks: {total_chunks}")
            write_log(f"[AFTER_CHUNK] 当前分块编号: {chunk_num}")
            write_log(f"[AFTER_CHUNK] 偏移量: {offset}")
            write_log(f"[AFTER_CHUNK] 事件数据: {event}")
            write_log(f"[AFTER_CHUNK] 计算进度: {progress}%")
            
            update_progress(progress, f"上传中... {uploaded_chunks}/{effective_total}")
        
        # 提交分P前事件
        @uploader.on(video_uploader.VideoUploaderEvents.PRE_PAGE_SUBMIT.value)
        def on_pre_page_submit(event):
            if check_cancelled():
                raise Exception("任务已取消")
            write_log(f"[PRE_PAGE_SUBMIT] 事件触发，进度: 95%")
            update_progress(95, "正在提交视频信息...", force=True)
        
        # 提交分P后事件
        @uploader.on(video_uploader.VideoUploaderEvents.AFTER_PAGE_SUBMIT.value)
        def on_after_page_submit(event):
            if check_cancelled():
                raise Exception("任务已取消")
            write_log(f"[AFTER_PAGE_SUBMIT] 事件触发，进度: 98%")
            update_progress(98, "正在完成上传...", force=True)
        
        # 上传完成事件
        @uploader.on(video_uploader.VideoUploaderEvents.COMPLETED.value)
        def on_completed(event):
            if check_cancelled():
                raise Exception("任务已取消")
            write_log(f"[COMPLETED] 事件触发，进度: 100%")
            write_log(f"[COMPLETED] 事件数据: {event}")
            write_log(f"=== 上传任务完成: {task_id} ===")
            update_progress(100, "上传成功", force=True)
        
        # 上传失败事件
        @uploader.on(video_uploader.VideoUploaderEvents.FAILED.value)
        def on_failed(event):
            # event 直接就是数据字典
            info = event.get('info', '上传失败')
            write_log(f"[FAILED] 事件触发，错误: {info}")
            write_log(f"[FAILED] 事件数据: {event}")
            update_progress(0, info, force=True)
        
        # 分块上传失败事件
        @uploader.on(video_uploader.VideoUploaderEvents.CHUNK_FAILED.value)
        def on_chunk_failed(event):
            # event 直接就是数据字典
            info = event.get('info', '分块上传失败')
            write_log(f"[CHUNK_FAILED] 事件触发，错误: {info}")
            write_log(f"[CHUNK_FAILED] 事件数据: {event}")
            update_progress(0, info, force=True)
