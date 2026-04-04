# B站视频上传工具 - 项目代码文档

> 自动生成时间: 2026-04-04 12:15:51

## 📋 项目概述

**项目名称**: B站视频上传工具  
**项目简介**: 一个简洁高效的B站视频上传管理工具，支持批量上传、配置模板、上传历史记录等功能。  
**技术栈**: Python + Flask + JavaScript + SQLite

---

## 📦 项目依赖

```
```

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
| backend/app.py | 141 | - |
| backend/config.py | 85 | - |
| backend/database.py | 720 | - |
| backend/routes/__init__.py | 27 | - |
| backend/routes/auth.py | 261 | - |
| backend/routes/config_templates.py | 240 | - |
| backend/routes/history.py | 180 | - |
| backend/routes/stats.py | 102 | - |
| backend/routes/upload.py | 216 | - |
| backend/routes/upload_sse.py | 292 | - |
| backend/uploader_core.py | 413 | - |
| backend/utils/__init__.py | 33 | - |
| backend/utils/helpers.py | 140 | - |
| backend/utils/video.py | 220 | - |

**后端代码总计**: 3,070 行

### 前端文件详情

| 文件路径 | 代码行数 | 说明 |
|---------|---------|------|
| static/css/main.css | 1,870 | - |
| static/index.html | 261 | - |
| static/js/config.js | 74 | - |
| static/js/main.js | 92 | - |
| static/js/modules/auth.js | 547 | - |
| static/js/modules/history.js | 324 | - |
| static/js/modules/stats.js | 15 | - |
| static/js/modules/tabs.js | 58 | - |
| static/js/modules/templates.js | 664 | - |
| static/js/modules/upload.js | 592 | - |
| static/js/utils/api.js | 122 | - |
| static/js/utils/audio.js | 210 | - |
| static/js/utils/format.js | 116 | - |
| static/js/utils/log.js | 62 | - |

**前端代码总计**: 5,007 行

---

## 🔌 后端API接口文档

### 接口概览


#### auth.py - 认证相关路由模块

| 接口地址 | 方法 | 功能描述 |
|---------|------|---------|
| `/api/auth` | GET | 获取数据库中保存的认证配置 |
| `/api/auth` | POST | 保存认证配置到数据库 |
| `/api/auth/test` | POST | 测试认证信息是否有效 |
| `/api/auth/clear` | POST | 清空数据库中的认证配置 |
| `/api/upload/init` | POST | 初始化上传会话 |

#### config_templates.py - 上传配置模板路由模块

| 接口地址 | 方法 | 功能描述 |
|---------|------|---------|
| `/api/upload-config-templates` | GET | 获取所有上传配置模板 |
| `/api/upload-config-templates/<template_id>` | GET | 获取单个上传配置模板 |
| `/api/upload-config-templates/default` | GET | 获取默认上传配置模板 |
| `/api/upload-config-templates` | POST | 创建新的上传配置模板 |
| `/api/upload-config-templates/<template_id>` | POST | 更新上传配置模板 |
| `/api/upload-config-templates/<template_id>` | DELETE | 删除上传配置模板 |

#### history.py - 上传历史记录路由模块

| 接口地址 | 方法 | 功能描述 |
|---------|------|---------|
| `/api/history` | GET | 获取上传历史记录 |
| `/api/history/<history_id>` | DELETE | 删除单条上传历史记录 |
| `/api/history/clear` | POST | 清空所有上传历史记录 |
| `/api/history/export` | GET | 导出上传历史为 CSV 文件 |

#### stats.py - 统计和日志路由模块

| 接口地址 | 方法 | 功能描述 |
|---------|------|---------|
| `/api/health` | GET | 健康检查端点 |
| `/api/stats` | GET | 获取统计信息 |
| `/api/logs` | GET | 获取上传日志 |
| `/api/logs/clear` | POST | 清空上传日志 |

#### upload.py - 上传相关路由模块

| 接口地址 | 方法 | 功能描述 |
|---------|------|---------|
| `/api/upload/file` | POST | 接收上传的视频文件 |
| `/api/videos` | GET | 获取视频列表 |
| `/api/videos/<video_id>/delete` | POST | 删除视频记录 |
| `/api/videos/<video_id>/update` | POST | 更新视频信息 |

#### upload_sse.py - 上传 SSE 实时进度推送模块

| 接口地址 | 方法 | 功能描述 |
|---------|------|---------|
| `/api/upload/progress/<upload_id>` | [GET] | SSE 端点：获取上传进度 |
| `/api/upload/cancel/<upload_id>` | POST | 取消上传 |
| `/api/upload/sync` | POST | 同步上传视频文件 |

### 接口详细说明

#### /api/auth

- **请求方法**: GET
- **功能描述**: 获取数据库中保存的认证配置
- **所属模块**: auth.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/auth

- **请求方法**: POST
- **功能描述**: 保存认证配置到数据库
- **所属模块**: auth.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/auth/test

- **请求方法**: POST
- **功能描述**: 测试认证信息是否有效
- **所属模块**: auth.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/auth/clear

- **请求方法**: POST
- **功能描述**: 清空数据库中的认证配置
- **所属模块**: auth.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload/init

- **请求方法**: POST
- **功能描述**: 初始化上传会话
- **所属模块**: auth.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload-config-templates

- **请求方法**: GET
- **功能描述**: 获取所有上传配置模板
- **所属模块**: config_templates.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload-config-templates/<template_id>

- **请求方法**: GET
- **功能描述**: 获取单个上传配置模板
- **所属模块**: config_templates.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload-config-templates/default

- **请求方法**: GET
- **功能描述**: 获取默认上传配置模板
- **所属模块**: config_templates.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload-config-templates

- **请求方法**: POST
- **功能描述**: 创建新的上传配置模板
- **所属模块**: config_templates.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload-config-templates/<template_id>

- **请求方法**: POST
- **功能描述**: 更新上传配置模板
- **所属模块**: config_templates.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload-config-templates/<template_id>

- **请求方法**: DELETE
- **功能描述**: 删除上传配置模板
- **所属模块**: config_templates.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/history

- **请求方法**: GET
- **功能描述**: 获取上传历史记录
- **所属模块**: history.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/history/<history_id>

- **请求方法**: DELETE
- **功能描述**: 删除单条上传历史记录
- **所属模块**: history.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/history/clear

- **请求方法**: POST
- **功能描述**: 清空所有上传历史记录
- **所属模块**: history.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/history/export

- **请求方法**: GET
- **功能描述**: 导出上传历史为 CSV 文件
- **所属模块**: history.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/health

- **请求方法**: GET
- **功能描述**: 健康检查端点
- **所属模块**: stats.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/stats

- **请求方法**: GET
- **功能描述**: 获取统计信息
- **所属模块**: stats.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/logs

- **请求方法**: GET
- **功能描述**: 获取上传日志
- **所属模块**: stats.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/logs/clear

- **请求方法**: POST
- **功能描述**: 清空上传日志
- **所属模块**: stats.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload/file

- **请求方法**: POST
- **功能描述**: 接收上传的视频文件
- **所属模块**: upload.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/videos

- **请求方法**: GET
- **功能描述**: 获取视频列表
- **所属模块**: upload.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/videos/<video_id>/delete

- **请求方法**: POST
- **功能描述**: 删除视频记录
- **所属模块**: upload.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/videos/<video_id>/update

- **请求方法**: POST
- **功能描述**: 更新视频信息
- **所属模块**: upload.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload/progress/<upload_id>

- **请求方法**: [GET]
- **功能描述**: SSE 端点：获取上传进度
- **所属模块**: upload_sse.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload/cancel/<upload_id>

- **请求方法**: POST
- **功能描述**: 取消上传
- **所属模块**: upload_sse.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
#### /api/upload/sync

- **请求方法**: POST
- **功能描述**: 同步上传视频文件
- **所属模块**: upload_sse.py

**请求参数**:
```json
{
  // 根据具体接口填写
}
```

**响应参数**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

---

*本文档由 deploy.py 自动生成*
