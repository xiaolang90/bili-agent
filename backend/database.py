#!/usr/bin/env python3
"""
数据库管理模块 - 封装所有 SQLite 数据库操作

此模块提供 Database 类，用于管理：
- 视频元数据表 (videos)
- 上传历史表 (upload_history)
- 认证配置表 (config)
- 上传配置模板表 (upload_config_templates)

使用示例：
    from database import Database
    from config import DB_FILE
    
    db = Database(DB_FILE)
    video_id = db.add_video("video.mp4", "标题", "描述", "标签")
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any

from config import DB_FILE, MAX_HISTORY_KEEP


class Database:
    """
    SQLite 数据库管理类
    
    封装所有数据库操作，包括表的创建、数据的增删改查。
    使用上下文管理器确保连接正确关闭。
    """
    
    def __init__(self, db_file: str = DB_FILE):
        """
        初始化数据库管理器
        
        Args:
            db_file: SQLite 数据库文件路径
        """
        self.db_file = db_file
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        
        Returns:
            sqlite3.Connection: 配置好的数据库连接对象
            
        Note:
            连接使用 Row 工厂，可以通过列名访问数据
        """
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self) -> None:
        """
        初始化数据库表结构
        
        创建以下表（如果不存在）：
        - videos: 存储视频元数据
        - upload_history: 存储上传历史记录
        - config: 存储简单的键值对配置
        - upload_config_templates: 存储上传配置模板
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建视频表 - 存储视频的基本信息
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                category_id INT DEFAULT 202,
                cover_path TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建上传历史表 - 记录每次上传的结果
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upload_history (
                id TEXT PRIMARY KEY,
                video_id TEXT,
                filename TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT,
                message TEXT,
                duration REAL,
                started_at DATETIME,
                finished_at DATETIME,
                FOREIGN KEY (video_id) REFERENCES videos(id)
            )
        ''')
        
        # 创建配置表 - 存储简单的键值对配置
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # 创建上传配置模板表 - 支持多配置切换
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upload_config_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                tid TEXT DEFAULT '201',
                tags TEXT DEFAULT '日语,双语字幕,出口仁,日语语法,JLPT,N3',
                description TEXT DEFAULT '出口仁老师N3语法课：{{title}}\n\n自动上传，请勿搬运',
                is_default INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # 视频管理
    # =========================================================================
    
    def add_video(self, filename: str, title: str, desc: str = "", tags: str = "") -> str:
        """
        添加视频记录
        
        Args:
            filename: 视频文件名
            title: 视频标题
            desc: 视频描述（可选）
            tags: 视频标签，逗号分隔（可选）
            
        Returns:
            str: 新创建的视频记录 ID
        """
        video_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO videos (id, filename, title, description, tags)
            VALUES (?, ?, ?, ?, ?)
        ''', (video_id, filename, title, desc, tags))
        
        conn.commit()
        conn.close()
        return video_id
    
    def get_videos(self, status: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        获取视频列表
        
        Args:
            status: 按状态筛选（可选）
            limit: 返回的最大记录数
            offset: 分页偏移量
            
        Returns:
            List[Dict]: 视频记录列表，每个记录为字典格式
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT * FROM videos WHERE status = ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            ''', (status, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM videos
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_video_status(self, video_id: str, status: str) -> None:
        """
        更新视频状态
        
        Args:
            video_id: 视频记录 ID
            status: 新状态（如 'pending', 'uploading', 'completed', 'error'）
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE videos SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, video_id))
        
        conn.commit()
        conn.close()
    
    def delete_video(self, video_id: str) -> bool:
        """
        删除视频记录
        
        Args:
            video_id: 视频记录 ID
            
        Returns:
            bool: 是否成功删除
            
        Note:
            同时删除关联的上传历史记录
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        cursor.execute('DELETE FROM upload_history WHERE video_id = ?', (video_id,))
        
        conn.commit()
        conn.close()
        return True
    
    # =========================================================================
    # 上传历史管理
    # =========================================================================
    
    def add_upload_history(self, video_id: str, filename: str, title: str,
                           status: str, message: str, duration: float = 0) -> str:
        """
        添加上传历史记录
        
        自动清理旧记录，只保留最近 MAX_HISTORY_KEEP 条
        
        Args:
            video_id: 关联的视频 ID
            filename: 上传的文件名
            title: 视频标题
            status: 上传状态（'success' 或 'error'）
            message: 结果消息
            duration: 上传耗时（秒）
            
        Returns:
            str: 新创建的历史记录 ID
        """
        history_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 获取东八区当前时间
        from datetime import timezone, timedelta
        cst_tz = timezone(timedelta(hours=8))
        now_cst = datetime.now(cst_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO upload_history 
            (id, video_id, filename, title, status, message, duration, started_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (history_id, video_id, filename, title, status, message, duration, now_cst, now_cst))
        
        # 自动清理：只保留最近 N 条记录
        cursor.execute('''
            DELETE FROM upload_history 
            WHERE id NOT IN (
                SELECT id FROM upload_history 
                ORDER BY started_at DESC 
                LIMIT ?
            )
        ''', (MAX_HISTORY_KEEP,))
        
        deleted_count = cursor.rowcount
        if deleted_count > 0:
            print(f"[数据库] 自动清理: 删除了 {deleted_count} 条旧的上传历史记录")
        
        conn.commit()
        conn.close()
        return history_id
    
    def get_upload_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        获取上传历史记录
        
        Args:
            limit: 返回的最大记录数
            offset: 分页偏移量
            
        Returns:
            List[Dict]: 历史记录列表，按时间倒序排列
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM upload_history
            ORDER BY started_at DESC LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_upload_history(self, history_id: str) -> bool:
        """
        删除单条上传历史记录
        
        Args:
            history_id: 历史记录 ID
            
        Returns:
            bool: 是否成功删除
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM upload_history WHERE id = ?', (history_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def clear_upload_history(self) -> None:
        """清空所有上传历史记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM upload_history')
        conn.commit()
        conn.close()
    
    # =========================================================================
    # 统计信息
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict: 包含以下统计数据的字典：
                - total_videos: 总视频数
                - status_counts: 各状态视频数量
                - successful_uploads: 成功上传数
                - failed_uploads: 失败上传数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 总视频数
        cursor.execute('SELECT COUNT(*) as count FROM videos')
        total_videos = cursor.fetchone()['count']
        
        # 各状态数量
        cursor.execute('SELECT status, COUNT(*) as count FROM videos GROUP BY status')
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # 上传成功数
        cursor.execute('SELECT COUNT(*) as count FROM upload_history WHERE status = "success"')
        success_count = cursor.fetchone()['count']
        
        # 上传失败数
        cursor.execute('SELECT COUNT(*) as count FROM upload_history WHERE status = "error"')
        error_count = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            "total_videos": total_videos,
            "status_counts": status_counts,
            "successful_uploads": success_count,
            "failed_uploads": error_count
        }
    
    # =========================================================================
    # 通用配置管理
    # =========================================================================
    
    def set_config(self, key: str, value: str) -> None:
        """
        设置配置项
        
        Args:
            key: 配置键名
            value: 配置值
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value)
            VALUES (?, ?)
        ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def get_config(self, key: str, default: str = None) -> Optional[str]:
        """
        获取配置项
        
        Args:
            key: 配置键名
            default: 默认值（如果键不存在）
            
        Returns:
            str: 配置值，如果不存在则返回默认值
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        conn.close()
        
        return row['value'] if row else default
    
    def get_all_configs(self) -> Dict[str, str]:
        """
        获取所有配置项
        
        Returns:
            Dict[str, str]: 所有配置项的字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value FROM config')
        rows = cursor.fetchall()
        
        conn.close()
        
        return {row['key']: row['value'] for row in rows}
    
    # =========================================================================
    # 认证配置管理
    # =========================================================================
    
    def save_auth_config(self, sessdata: str, bili_jct: str, buvid3: str) -> None:
        """
        保存认证配置
        
        先删除旧配置，确保只有一个认证配置存在
        
        Args:
            sessdata: B站 SESSDATA Cookie
            bili_jct: B站 bili_jct Cookie
            buvid3: B站 buvid3 Cookie
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 先删除旧的认证配置
        cursor.execute('''
            DELETE FROM config 
            WHERE key IN ('auth_sessdata', 'auth_bili_jct', 'auth_buvid3')
        ''')
        
        # 插入新的认证配置
        cursor.execute('''
            INSERT INTO config (key, value)
            VALUES 
                ('auth_sessdata', ?),
                ('auth_bili_jct', ?),
                ('auth_buvid3', ?)
        ''', (sessdata, bili_jct, buvid3))
        
        conn.commit()
        conn.close()
    
    def get_auth_config(self) -> Dict[str, str]:
        """
        获取认证配置
        
        Returns:
            Dict[str, str]: 包含 sessdata, bili_jct, buvid3 的字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, value FROM config 
            WHERE key IN ('auth_sessdata', 'auth_bili_jct', 'auth_buvid3')
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        config = {}
        key_mapping = {
            'auth_sessdata': 'sessdata',
            'auth_bili_jct': 'bili_jct',
            'auth_buvid3': 'buvid3'
        }
        
        for row in rows:
            key = key_mapping.get(row['key'])
            if key:
                config[key] = row['value']
        
        return config
    
    def clear_auth_config(self) -> None:
        """
        清空认证配置
        
        删除数据库中保存的所有认证相关配置
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM config 
            WHERE key IN ('auth_sessdata', 'auth_bili_jct', 'auth_buvid3')
        ''')
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # 上传配置模板管理
    # =========================================================================
    
    def create_upload_config_template(self, name: str, tid: str = '201', 
                                      tags: str = '', description: str = '', 
                                      is_default: bool = False) -> str:
        """
        创建上传配置模板
        
        Args:
            name: 模板名称
            tid: 分类 ID
            tags: 标签，逗号分隔
            description: 视频描述
            is_default: 是否设为默认模板
            
        Returns:
            str: 新创建的模板 ID
            
        Raises:
            sqlite3.IntegrityError: 如果模板名称已存在
        """
        template_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 如果设置为默认，先将其他模板设为非默认
        if is_default:
            cursor.execute('UPDATE upload_config_templates SET is_default = 0')
        
        cursor.execute('''
            INSERT INTO upload_config_templates (id, name, tid, tags, description, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (template_id, name, tid, tags, description, 1 if is_default else 0))
        
        conn.commit()
        conn.close()
        return template_id
    
    def get_upload_config_templates(self) -> List[Dict]:
        """
        获取所有上传配置模板
        
        Returns:
            List[Dict]: 模板列表，默认模板排在最前面
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, tid, tags, description, is_default, created_at, updated_at
            FROM upload_config_templates
            ORDER BY is_default DESC, updated_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_upload_config_template(self, template_id: str) -> Optional[Dict]:
        """
        获取单个上传配置模板
        
        Args:
            template_id: 模板 ID
            
        Returns:
            Optional[Dict]: 模板数据，如果不存在则返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, tid, tags, description, is_default, created_at, updated_at
            FROM upload_config_templates WHERE id = ?
        ''', (template_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_default_upload_config_template(self) -> Optional[Dict]:
        """
        获取默认上传配置模板
        
        Returns:
            Optional[Dict]: 默认模板数据，如果没有设置则返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, tid, tags, description, is_default, created_at, updated_at
            FROM upload_config_templates WHERE is_default = 1 LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_upload_config_template(self, template_id: str, name: str = None, 
                                      tid: str = None, tags: str = None, 
                                      description: str = None, 
                                      is_default: bool = None) -> bool:
        """
        更新上传配置模板
        
        Args:
            template_id: 模板 ID
            name: 新名称（可选）
            tid: 新分类 ID（可选）
            tags: 新标签（可选）
            description: 新描述（可选）
            is_default: 是否设为默认（可选）
            
        Returns:
            bool: 是否成功更新
            
        Raises:
            sqlite3.IntegrityError: 如果新名称与其他模板重复
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 检查模板是否存在
        cursor.execute('SELECT id FROM upload_config_templates WHERE id = ?', (template_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        # 如果设置为默认，先将其他模板设为非默认
        if is_default:
            cursor.execute('UPDATE upload_config_templates SET is_default = 0')
        
        # 构建更新语句
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if tid is not None:
            updates.append('tid = ?')
            params.append(tid)
        if tags is not None:
            updates.append('tags = ?')
            params.append(tags)
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        if is_default is not None:
            updates.append('is_default = ?')
            params.append(1 if is_default else 0)
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            sql = f"UPDATE upload_config_templates SET {', '.join(updates)} WHERE id = ?"
            params.append(template_id)
            cursor.execute(sql, params)
        
        conn.commit()
        conn.close()
        return True
    
    def delete_upload_config_template(self, template_id: str) -> bool:
        """
        删除上传配置模板
        
        Args:
            template_id: 模板 ID
            
        Returns:
            bool: 是否成功删除
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM upload_config_templates WHERE id = ?', (template_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted


# 全局数据库实例
db = Database(DB_FILE)
