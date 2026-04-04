#!/usr/bin/env python3
"""
认证相关路由模块

处理 B站 Cookie 认证相关的 API：
- 获取/保存认证配置
- 测试认证有效性
- 初始化上传会话
"""

import asyncio
from flask import Blueprint, request, jsonify

try:
    from bilibili_api import Credential, user
except ImportError:
    Credential = None
    user = None

from database import db
from utils.helpers import add_log

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api')

# 全局上传器实例（在 init_upload 中初始化）
current_uploader = None


@auth_bp.route('/auth', methods=['GET'])
def get_auth():
    """
    获取数据库中保存的认证配置
    
    Returns:
        JSON: 包含 sessdata, bili_jct, buvid3 的配置
    """
    try:
        auth_config = db.get_auth_config()
        return jsonify({
            "success": True,
            "data": auth_config
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@auth_bp.route('/auth', methods=['POST'])
def save_auth():
    """
    保存认证配置到数据库
    
    Request Body:
        - sessdata: B站 SESSDATA Cookie
        - bili_jct: B站 bili_jct Cookie
        - buvid3: B站 buvid3 Cookie
        
    Returns:
        JSON: 保存结果
    """
    try:
        data = request.get_json() or {}
        sessdata = data.get('sessdata', '').strip()
        bili_jct = data.get('bili_jct', '').strip()
        buvid3 = data.get('buvid3', '').strip()
        
        # 保存到数据库
        db.save_auth_config(sessdata, bili_jct, buvid3)
        add_log("info", "认证配置已保存到数据库")
        
        return jsonify({
            "success": True,
            "message": "认证配置已保存"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@auth_bp.route('/auth/test', methods=['POST'])
def test_auth():
    """
    测试认证信息是否有效
    
    使用 bilibili-api 验证认证信息，尝试获取用户信息
    
    Request Body:
        - sessdata: B站 SESSDATA Cookie
        - bili_jct: B站 bili_jct Cookie
        - buvid3: B站 buvid3 Cookie
        
    Returns:
        JSON: 验证结果，包含用户名和 MID
    """
    try:
        data = request.get_json() or {}
        sessdata = data.get('sessdata', '').strip()
        bili_jct = data.get('bili_jct', '').strip()
        buvid3 = data.get('buvid3', '').strip()
        
        # 检查是否提供了完整的认证信息
        if not sessdata or not bili_jct or not buvid3:
            return jsonify({
                "success": False,
                "message": "请提供完整的认证信息（SESSDATA、bili_jct、buvid3）"
            }), 400
        
        # 使用 bilibili-api 验证认证信息
        if Credential is None:
            return jsonify({
                "success": False,
                "message": "bilibili-api-python 未安装，无法验证认证信息"
            }), 500
        
        try:
            # 创建 Credential 对象
            credential = Credential(
                sessdata=sessdata,
                bili_jct=bili_jct,
                buvid3=buvid3
            )
            
            # 尝试获取用户信息来验证认证是否有效
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self_info = loop.run_until_complete(user.get_self_info(credential))
            
            # 如果能获取到用户信息，说明认证有效
            user_name = self_info.get('name', '未知用户')
            user_mid = self_info.get('mid', '未知ID')
            
            add_log("info", f"认证信息验证成功: {user_name} (MID: {user_mid})")
            
            return jsonify({
                "success": True,
                "message": f"认证信息有效，用户: {user_name}",
                "data": {
                    "name": user_name,
                    "mid": user_mid
                }
            })
            
        except Exception as e:
            error_msg = str(e)
            add_log("warn", f"认证信息验证失败: {error_msg}")
            
            # 根据错误类型返回不同的提示
            if "-101" in error_msg or "账号未登录" in error_msg:
                return jsonify({
                    "success": False,
                    "message": "认证信息已过期或无效，请重新登录B站获取"
                }), 401
            elif "-352" in error_msg:
                return jsonify({
                    "success": False,
                    "message": "请求被拒绝，可能是风控限制，请稍后再试"
                }), 403
            elif "-400" in error_msg:
                return jsonify({
                    "success": False,
                    "message": "请求参数错误，请检查认证信息格式"
                }), 400
            else:
                return jsonify({
                    "success": False,
                    "message": f"认证验证失败: {error_msg[:100]}"
                }), 401
    
    except Exception as e:
        add_log("error", f"认证测试异常: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"服务器异常: {str(e)}"
        }), 500


@auth_bp.route('/auth/clear', methods=['POST'])
def clear_auth():
    """
    清空数据库中的认证配置
    
    Returns:
        JSON: 清空结果
    """
    try:
        db.clear_auth_config()
        add_log("info", "认证配置已清空")
        
        return jsonify({
            "success": True,
            "message": "认证配置已清空"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@auth_bp.route('/upload/init', methods=['POST'])
def init_upload():
    """
    初始化上传会话
    
    使用数据库中的认证配置创建 BilibiliUploader 实例供后续上传使用
    如果没有配置，返回错误提示
    
    Returns:
        JSON: 初始化结果
    """
    global current_uploader
    
    try:
        # 从数据库获取认证配置
        auth_config = db.get_auth_config()
        
        # 获取认证信息
        sessdata = auth_config.get('sessdata', '').strip()
        bili_jct = auth_config.get('bili_jct', '').strip()
        buvid3 = auth_config.get('buvid3', '').strip()
        
        # 检查是否配置了认证信息
        if not sessdata or not bili_jct or not buvid3:
            return jsonify({
                "success": False,
                "message": "未配置认证信息，请先在设置中配置B站认证信息"
            }), 400
        
        # 延迟导入以避免循环依赖
        from uploader_core import BilibiliUploader
        current_uploader = BilibiliUploader(sessdata, bili_jct, buvid3)
        
        add_log("info", "上传会话已初始化（使用数据库认证配置）")
        
        return jsonify({
            "success": True,
            "message": "上传会话已初始化"
        })
    
    except Exception as e:
        add_log("error", f"初始化失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


def get_current_uploader():
    """
    获取当前上传器实例
    
    Returns:
        BilibiliUploader: 当前的上传器实例，可能为 None
    """
    return current_uploader
