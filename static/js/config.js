/**
 * 全局配置文件
 * 
 * 此模块包含应用的所有全局配置常量
 */

/**
 * API 基础 URL
 * 指向重构版后端服务器（端口 5001）
 * @constant {string}
 */
export const API_BASE_URL = 'http://localhost:5001/api';

/**
 * 每页显示的历史记录数量
 * @constant {number}
 */
export const ITEMS_PER_PAGE = 10;

/**
 * 自动刷新历史记录的时间间隔（毫秒）
 * @constant {number}
 */
export const HISTORY_REFRESH_INTERVAL = 5000;

/**
 * 日志类型对应的图标
 * @constant {Object<string, string>}
 */
export const LOG_ICONS = {
    error: '❌',
    success: '✅',
    info: 'ℹ️',
    warn: '⚠️'
};

/**
 * 上传状态对应的中文文本
 * @constant {Object<string, string>}
 */
export const STATUS_TEXT = {
    added: '已添加',
    waiting: '等待中',
    queued: '已排队',
    pending: '处理中',
    uploading: '上传中',
    completed: '已完成',
    success: '成功',
    error: '失败',
    cancelled: '已取消'
};

/**
 * 支持的文件类型
 * @constant {Array<string>}
 */
export const SUPPORTED_VIDEO_TYPES = [
    'video/mp4',
    'video/x-matroska',
    'video/quicktime',
    'video/x-flv',
    'video/avi',
    'video/webm'
];

/**
 * 默认上传配置
 * @constant {Object}
 */
export const DEFAULT_UPLOAD_CONFIG = {
    tid: '201',
    tags: '日语,双语字幕,出口仁,日语语法,JLPT,N3',
    desc: '出口仁老师N3语法课：{{title}}\n\n自动上传，请勿搬运'
};
