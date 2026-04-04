# B站视频上传工具

## 📋 项目概述

**项目名称**: B站视频上传工具  
**项目简介**: 一个简洁高效的B站视频上传管理工具，支持批量上传、配置模板、上传历史记录等功能。  
**技术栈**: Python + Flask + JavaScript + SQLite

### 优势

0. **极简不可超越**: 最简单的实现方案就是好方案，追求人人看的懂的开源项目
1. **单一职责**: 每个文件只负责一个功能模块
2. **易于维护**: 修改某个功能只需编辑对应文件
3. **便于测试**: 可以单独测试每个模块
4. **代码复用**: 工具函数可以在多个模块中使用
5. **清晰注释**: 每个函数都有详细的中文文档

## 🚀 快速开始

---

## 🚀 部署说明

### 环境要求

- Python 3.8+
- pip / pip3

```bash
up本人本地版本：
Python 3.9.6
pip 21.2.4
```

### 安装步骤

1. 克隆项目
```bash
git clone git@github.com:xiaolang90/bili-agent.git
cd bili-agent
```

2. 安装依赖
```bash
pip install flask flask-cors bilibili-api-python Werkzeug
亦或
pip3 install flask flask-cors bilibili-api-python Werkzeug
```

```bash
确保本地有安装ffmpeg(木有安装的话，无法截取视频帧作为B站视频封面)
ffmpeg>=4.0.0

up本人本地版本：
flask 3.1.3
flask-cors 6.0.2
bilibili-api-python 17.4.1
Werkzeug 3.1.7
ffmpeg 4.4.6
```

## 🔧 后端模块说明

### backend/config.py
配置常量集中管理：
- 服务器配置（端口 5001）
- 上传文件限制（16GB）
- 数据库配置
- ffmpeg 配置(如果你已经安装过ffmpeg, 这里务必改成你自己的绝对路径，
- 如：FFMPEG_PATH = '/opt/local/bin/ffmpeg')

3. 启动服务
```bash
python run.py
亦或
python3 run.py
```

4. 访问应用
打开浏览器访问: http://localhost:5001

## 🐛 故障排除

### 端口冲突
- 如果 5001 端口被占用
- 找出占用进程：lsof -i:5001
- 杀掉占用进程：kill -9 [目标pid]
- 或者修改 `backend/config.py`:

```python
SERVER_PORT = 5002  # 改为其他端口
```

### 更多代码相关的详细信息，请参阅CODE.md
```
CODE.md，文档由 deploy.py 自动生成*
```

## 📄 License
- MIT

## 🙏 致谢

- 原项目作者
- bilibili-api-python 库
- Flask 框架
