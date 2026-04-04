#!/usr/bin/env python3
"""
B站上传工具 - 上线预处理脚本

功能：
1. 清理日志文件
2. 清理本地数据库文件
3. 自动生成 code.md 项目文档
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
LOG_DIR = BACKEND_DIR / "log"
DB_FILE = PROJECT_ROOT / "bilibili_uploader_refactored.db"
CODE_MD_FILE = PROJECT_ROOT / "CODE.md"


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step_num, total, message):
    """打印步骤信息"""
    print(f"\n[{step_num}/{total}] {message}")


def confirm(message):
    """确认操作"""
    response = input(f"\n{message} (y/n): ").strip().lower()
    return response in ('y', 'yes', '是')


def clean_logs():
    """清理日志文件"""
    if not LOG_DIR.exists():
        print("  日志目录不存在，跳过")
        return 0
    
    log_files = list(LOG_DIR.glob("*.log"))
    if not log_files:
        print("  没有日志文件需要清理")
        return 0
    
    count = 0
    for log_file in log_files:
        try:
            log_file.unlink()
            print(f"  ✓ 已删除: {log_file.name}")
            count += 1
        except Exception as e:
            print(f"  ✗ 删除失败 {log_file.name}: {e}")
    
    return count


def clean_database():
    """清理数据库文件"""
    if not DB_FILE.exists():
        print("  数据库文件不存在，跳过")
        return False
    
    try:
        DB_FILE.unlink()
        print(f"  ✓ 已删除: {DB_FILE.name}")
        return True
    except Exception as e:
        print(f"  ✗ 删除失败: {e}")
        return False


def count_lines(file_path):
    """统计文件代码行数"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except:
        return 0


def get_file_info(file_path):
    """获取文件信息"""
    lines = count_lines(file_path)
    size = file_path.stat().st_size if file_path.exists() else 0
    return {
        'name': file_path.name,
        'lines': lines,
        'size': size
    }


def scan_project_structure():
    """扫描项目结构"""
    structure = {
        'backend': {'files': [], 'total_lines': 0},
        'frontend': {'files': [], 'total_lines': 0},
        'config': {'files': [], 'total_lines': 0},
        'root': {'files': [], 'total_lines': 0}
    }
    
    # 扫描后端文件
    if BACKEND_DIR.exists():
        for py_file in BACKEND_DIR.rglob("*.py"):
            rel_path = py_file.relative_to(PROJECT_ROOT)
            info = get_file_info(py_file)
            structure['backend']['files'].append({
                'path': str(rel_path),
                **info
            })
            structure['backend']['total_lines'] += info['lines']
    
    # 扫描前端文件
    static_dir = PROJECT_ROOT / "static"
    if static_dir.exists():
        for ext in ['*.js', '*.html', '*.css']:
            for file in static_dir.rglob(ext):
                rel_path = file.relative_to(PROJECT_ROOT)
                info = get_file_info(file)
                structure['frontend']['files'].append({
                    'path': str(rel_path),
                    **info
                })
                structure['frontend']['total_lines'] += info['lines']
    
    # 扫描配置文件
    config_dir = BACKEND_DIR / "config"
    if config_dir.exists():
        for file in config_dir.glob("*.json"):
            rel_path = file.relative_to(PROJECT_ROOT)
            info = get_file_info(file)
            structure['config']['files'].append({
                'path': str(rel_path),
                **info
            })
            structure['config']['total_lines'] += info['lines']
    
    # 扫描根目录文件
    for file in PROJECT_ROOT.glob("*.py"):
        info = get_file_info(file)
        structure['root']['files'].append({
            'path': file.name,
            **info
        })
        structure['root']['total_lines'] += info['lines']
    
    # 计算总计
    structure['total_lines'] = (
        structure['backend']['total_lines'] +
        structure['frontend']['total_lines'] +
        structure['config']['total_lines'] +
        structure['root']['total_lines']
    )
    
    return structure


def parse_api_routes():
    """解析API路由信息"""
    routes_dir = BACKEND_DIR / "routes"
    apis = []
    
    if not routes_dir.exists():
        return apis
    
    for py_file in routes_dir.glob("*.py"):
        if py_file.name == '__init__.py':
            continue
        
        content = py_file.read_text(encoding='utf-8')
        
        # 提取模块描述
        module_desc = ""
        doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if doc_match:
            module_desc = doc_match.group(1).strip().split('\n')[0]
        
        # 提取路由装饰器和函数定义
        route_pattern = r'@(\w+)_bp\.route\([\'"](.+?)[\'"](?:,\s*methods=\[(.+?)\])?\)'
        func_pattern = r'def\s+(\w+)\s*\([^)]*\):'
        
        routes = re.finditer(route_pattern, content)
        for route in routes:
            bp_name = route.group(1)
            url = route.group(2)
            methods = route.group(3) if route.group(3) else "['GET']"
            methods = methods.replace("'", "").replace('"', "").replace(" ", "")
            
            # 获取函数名和文档字符串
            func_start = route.end()
            func_match = re.search(func_pattern, content[func_start:])
            if func_match:
                func_name = func_match.group(1)
                
                # 提取文档字符串
                doc_start = func_start + func_match.end()
                doc_match = re.search(r'"""(.*?)"""', content[doc_start:], re.DOTALL)
                description = ""
                if doc_match:
                    doc_content = doc_match.group(1).strip()
                    # 提取第一行作为描述
                    description = doc_content.split('\n')[0].strip()
                
                apis.append({
                    'module': py_file.stem,
                    'module_desc': module_desc,
                    'url': f"/api{url}",
                    'methods': methods,
                    'function': func_name,
                    'description': description
                })
    
    return apis


def get_requirements():
    """获取依赖列表"""
    req_file = PROJECT_ROOT / "requirements.txt"
    if req_file.exists():
        return req_file.read_text(encoding='utf-8').strip().split('\n')
    return []


def generate_code_md(structure, apis):
    """生成 code.md 文档"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""# B站视频上传工具 - 项目代码文档

> 自动生成时间: {now}

## 📋 项目概述

**项目名称**: B站视频上传工具  
**项目简介**: 一个简洁高效的B站视频上传管理工具，支持批量上传、配置模板、上传历史记录等功能。  
**技术栈**: Python + Flask + JavaScript + SQLite

---

"""
    
    # 依赖列表
    requirements = get_requirements()
    content += """## 📦 项目依赖

```
"""
    for req in requirements:
        content += f"{req}\n"
    
    content += """```

## 📁 目录结构

```
bili-agent/
├── backend/                    # 后端代码目录
│   ├── app.py                 # Flask 应用主入口
│   ├── config.py              # 配置常量
│   ├── database.py            # 数据库操作
│   ├── uploader_core.py       # B站上传核心
│   ├── routes/                # API路由模块
│   │   ├── auth.py            # 认证相关
│   │   ├── upload.py          # 上传相关
│   │   ├── upload_sse.py      # SSE同步上传
│   │   ├── history.py         # 历史记录
│   │   ├── config_templates.py # 配置模板
│   │   └── stats.py           # 统计日志
│   ├── utils/                 # 工具函数
│   │   ├── helpers.py         # 通用工具
│   │   └── video.py           # 视频处理
│   └── config/                # 配置文件
│       └── bilibili_tid_mapping.json  # 分区映射
├── static/                    # 前端静态文件
│   ├── index.html             # 主页面
│   ├── css/                   # 样式文件
│   │   └── main.css
│   └── js/                    # JavaScript模块
│       ├── main.js            # 主入口
│       ├── config.js          # 配置模块
│       └── modules/           # 功能模块
│           ├── auth.js        # 认证模块
│           ├── upload.js      # 上传模块
│           ├── history.js     # 历史模块
│           ├── templates.js   # 模板模块
│           ├── stats.js       # 统计模块
│           └── tabs.js        # 标签页模块
├── run.py                     # 启动脚本
├── requirements.txt           # 依赖列表
└── README.md                  # 项目说明
```

---

## 📊 代码统计

### 后端文件详情

| 文件路径 | 代码行数 | 说明 |
|---------|---------|------|
"""
    
    # 添加后端文件详情
    for file in sorted(structure['backend']['files'], key=lambda x: x['path']):
        content += f"| {file['path']} | {file['lines']:,} | - |\n"
    
    content += f"\n**后端代码总计**: {structure['backend']['total_lines']:,} 行\n\n"
    
    # 前端文件详情
    content += "### 前端文件详情\n\n| 文件路径 | 代码行数 | 说明 |\n|---------|---------|------|\n"
    for file in sorted(structure['frontend']['files'], key=lambda x: x['path']):
        content += f"| {file['path']} | {file['lines']:,} | - |\n"
    
    content += f"\n**前端代码总计**: {structure['frontend']['total_lines']:,} 行\n\n"
    
    # API接口文档
    content += """---

## 🔌 后端API接口文档

### 接口概览

"""
    
    # 按模块分组
    modules = {}
    for api in apis:
        module = api['module']
        if module not in modules:
            modules[module] = {
                'desc': api['module_desc'],
                'apis': []
            }
        modules[module]['apis'].append(api)
    
    # 生成API文档
    for module_name, module_data in sorted(modules.items()):
        content += f"\n#### {module_name}.py - {module_data['desc']}\n\n"
        content += "| 接口地址 | 方法 | 功能描述 |\n"
        content += "|---------|------|---------|\n"
        
        for api in module_data['apis']:
            content += f"| `{api['url']}` | {api['methods']} | {api['description']} |\n"
    
    # 详细API说明
    content += "\n### 接口详细说明\n\n"
    
    for module_name, module_data in sorted(modules.items()):
        for api in module_data['apis']:
            content += f"""#### {api['url']}

- **请求方法**: {api['methods']}
- **功能描述**: {api['description']}
- **所属模块**: {module_name}.py

**请求参数**:
```json
{{
  // 根据具体接口填写
}}
```

**响应参数**:
```json
{{
  "success": true,
  "message": "操作成功",
  "data": {{}}
}}
```

---

*本文档由 deploy.py 自动生成*
"""
    
    return content


def main():
    """主函数"""
    print_header("B站上传工具 - 上线预处理脚本")
    
    print("\n此脚本将执行以下操作:")
    print("  1. 删除 backend/log/ 目录下的所有日志文件")
    print("  2. 删除本地数据库文件 bilibili_uploader_refactored.db")
    print("  3. 扫描项目结构并统计代码行数")
    print("  4. 解析所有API接口信息")
    print("  5. 生成/更新 code.md 文档")
    
    if not confirm("\n是否继续执行?"):
        print("\n已取消操作")
        sys.exit(0)
    
    # 步骤1: 清理日志
    print_step(1, 5, "清理日志文件")
    log_count = clean_logs()
    print(f"  共清理 {log_count} 个日志文件")
    
    # 步骤2: 清理数据库
    print_step(2, 5, "清理数据库文件")
    db_cleaned = clean_database()
    if db_cleaned:
        print("  数据库文件已清理")
    
    # 步骤3: 扫描项目结构
    print_step(3, 5, "扫描项目结构")
    structure = scan_project_structure()
    print(f"  后端文件: {len(structure['backend']['files'])} 个, {structure['backend']['total_lines']:,} 行")
    print(f"  前端文件: {len(structure['frontend']['files'])} 个, {structure['frontend']['total_lines']:,} 行")
    print(f"  配置文件: {len(structure['config']['files'])} 个, {structure['config']['total_lines']:,} 行")
    print(f"  总计: {structure['total_lines']:,} 行")
    
    # 步骤4: 解析API
    print_step(4, 5, "解析API接口")
    apis = parse_api_routes()
    print(f"  共发现 {len(apis)} 个API接口")
    
    # 步骤5: 生成文档
    print_step(5, 5, "生成 code.md 文档")
    try:
        content = generate_code_md(structure, apis)
        CODE_MD_FILE.write_text(content, encoding='utf-8')
        print(f"  ✓ 文档已生成: {CODE_MD_FILE.name}")
        print(f"  文档大小: {len(content):,} 字符")
    except Exception as e:
        print(f"  ✗ 生成失败: {e}")
        sys.exit(1)
    
    # 完成
    print_header("预处理完成")
    print("\n执行结果:")
    print(f"  ✓ 清理日志文件: {log_count} 个")
    print(f"  ✓ 清理数据库: {'是' if db_cleaned else '否'}")
    print(f"  ✓ 项目代码统计: {structure['total_lines']:,} 行")
    print(f"    - 后端: {structure['backend']['total_lines']:,} 行")
    print(f"    - 前端: {structure['frontend']['total_lines']:,} 行")
    print(f"  ✓ API接口数量: {len(apis)} 个")
    print(f"  ✓ 文档已更新: {CODE_MD_FILE.name}")
    
    print("\n" + "=" * 60)
    print("项目已准备好发布到 GitHub!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
