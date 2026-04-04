#!/usr/bin/env python3
"""
上传配置模板路由模块

处理配置模板的 CRUD 操作：
- 创建模板
- 获取模板列表
- 更新模板
- 删除模板
- 设置默认模板
"""

import sqlite3
from flask import Blueprint, request, jsonify

from database import db
from utils.helpers import add_log

# 创建蓝图
templates_bp = Blueprint('templates', __name__, url_prefix='/api')


@templates_bp.route('/upload-config-templates', methods=['GET'])
def get_templates():
    """
    获取所有上传配置模板
    
    Returns:
        JSON: 模板列表，默认模板排在最前面
    """
    try:
        templates = db.get_upload_config_templates()
        return jsonify({
            "success": True,
            "data": templates
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@templates_bp.route('/upload-config-templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """
    获取单个上传配置模板
    
    Args:
        template_id: 模板ID
        
    Returns:
        JSON: 模板详情
    """
    try:
        template = db.get_upload_config_template(template_id)
        if template:
            return jsonify({
                "success": True,
                "data": template
            })
        else:
            return jsonify({
                "success": False,
                "message": "模板不存在"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@templates_bp.route('/upload-config-templates/default', methods=['GET'])
def get_default_template():
    """
    获取默认上传配置模板
    
    Returns:
        JSON: 默认模板详情
    """
    try:
        template = db.get_default_upload_config_template()
        if template:
            return jsonify({
                "success": True,
                "data": template
            })
        else:
            return jsonify({
                "success": False,
                "message": "没有设置默认模板"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@templates_bp.route('/upload-config-templates', methods=['POST'])
def create_template():
    """
    创建新的上传配置模板
    
    Request Body:
        - name: 模板名称（必填）
        - tid: 分类ID（可选，默认201）
        - tags: 标签（可选）
        - description: 描述（可选）
        - is_default: 是否设为默认（可选）
        
    Returns:
        JSON: 创建结果，包含新模板ID
    """
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        tid = data.get('tid', '201')
        tags = data.get('tags', '')
        description = data.get('description', '')
        is_default = data.get('is_default', False)
        
        if not name:
            return jsonify({
                "success": False,
                "message": "模板名称不能为空"
            }), 400
        
        template_id = db.create_upload_config_template(
            name, tid, tags, description, is_default
        )
        add_log("info", f"已创建上传配置模板: {name}")
        
        return jsonify({
            "success": True,
            "template_id": template_id,
            "message": "模板已创建"
        })
    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "模板名称已存在"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@templates_bp.route('/upload-config-templates/<template_id>', methods=['POST'])
def update_template(template_id):
    """
    更新上传配置模板
    
    Args:
        template_id: 模板ID
        
    Request Body:
        - name: 新名称（可选）
        - tid: 新分类ID（可选）
        - tags: 新标签（可选）
        - description: 新描述（可选）
        - is_default: 是否设为默认（可选）
        
    Returns:
        JSON: 更新结果
    """
    try:
        data = request.get_json() or {}
        
        # 构建更新参数
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name'].strip()
        if 'tid' in data:
            update_data['tid'] = data['tid']
        if 'tags' in data:
            update_data['tags'] = data['tags']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'is_default' in data:
            update_data['is_default'] = data['is_default']
        
        success = db.update_upload_config_template(template_id, **update_data)
        
        if success:
            add_log("info", f"已更新上传配置模板: {template_id}")
            return jsonify({
                "success": True,
                "message": "模板已更新"
            })
        else:
            return jsonify({
                "success": False,
                "message": "模板不存在"
            }), 404
    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "模板名称已存在"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@templates_bp.route('/upload-config-templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """
    删除上传配置模板
    
    Args:
        template_id: 模板ID
        
    Returns:
        JSON: 删除结果
    """
    try:
        success = db.delete_upload_config_template(template_id)
        
        if success:
            add_log("info", f"已删除上传配置模板: {template_id}")
            return jsonify({
                "success": True,
                "message": "模板已删除"
            })
        else:
            return jsonify({
                "success": False,
                "message": "模板不存在"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
