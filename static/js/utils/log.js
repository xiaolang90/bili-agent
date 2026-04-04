/**
 * 日志工具模块
 * 
 * 提供统一的日志输出功能
 */

import { LOG_ICONS } from '../config.js';

/**
 * 日志输出元素
 * @type {HTMLElement|null}
 */
let logElement = null;

/**
 * 初始化日志模块
 * 
 * @param {string} elementId - 日志容器的 DOM 元素 ID
 */
export function initLog(elementId = 'log') {
    logElement = document.getElementById(elementId);
}

/**
 * 输出日志到页面和控制台
 * 
 * @param {string} type - 日志类型: 'error' | 'success' | 'info' | 'warn'
 * @param {string} message - 日志消息内容
 * 
 * @example
 * log('info', '系统初始化完成');
 * log('error', '上传失败: 网络错误');
 * log('success', '文件上传成功');
 */
export function log(type, message) {
    const timestamp = new Date().toLocaleTimeString();
    const icon = LOG_ICONS[type] || LOG_ICONS.info;
    
    // 输出到控制台
    console.log(`[${timestamp}] ${type.toUpperCase()}: ${message}`);
    
    // 输出到页面
    if (logElement) {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `
            <span class="log-time">[${timestamp}]</span>
            <span class="log-${type}">${icon} ${message}</span>
        `;
        logElement.appendChild(entry);
        logElement.scrollTop = logElement.scrollHeight;
    }
}

/**
 * 清空日志
 */
export function clearLog() {
    if (logElement) {
        logElement.innerHTML = '';
    }
}
