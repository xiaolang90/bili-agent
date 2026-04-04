/**
 * 主入口模块
 * 
 * 应用初始化、事件绑定、模块协调
 */

import { initLog, log } from './utils/log.js';
import { checkHealth } from './utils/api.js';
import { initTabs } from './modules/tabs.js';
import { initAuth } from './modules/auth.js';
import { initUpload } from './modules/upload.js';
import { initHistory } from './modules/history.js';
import { initTemplates } from './modules/templates.js';
import { initStats } from './modules/stats.js';

/**
 * 设置全局错误处理
 * 捕获并处理特定的非关键错误
 */
function setupGlobalErrorHandling() {
    // 捕获未处理的 Promise 拒绝
    window.addEventListener('unhandledrejection', (event) => {
        const error = event.reason;
        
        // 忽略 AbortError（通常是音频播放被中断）
        if (error && error.name === 'AbortError') {
            console.log('[Global] 忽略 AbortError:', error.message);
            event.preventDefault();
            return;
        }
        
        // 忽略 NotAllowedError（自动播放策略）
        if (error && error.name === 'NotAllowedError') {
            console.log('[Global] 忽略 NotAllowedError:', error.message);
            event.preventDefault();
            return;
        }
        
        // 其他错误正常输出
        console.error('[Global] 未处理的 Promise 错误:', error);
    });
    
    // 捕获全局错误
    window.addEventListener('error', (event) => {
        // 忽略与音频相关的错误
        if (event.message && (
            event.message.includes('play()') ||
            event.message.includes('pause()') ||
            event.message.includes('AbortError')
        )) {
            console.log('[Global] 忽略音频相关错误:', event.message);
            event.preventDefault();
            return;
        }
    });
}

/**
 * 初始化应用
 * 
 * 按顺序初始化各个模块
 */
async function init() {
    // 设置全局错误处理
    setupGlobalErrorHandling();
    
    // 初始化日志模块
    initLog('log');
    log('info', '系统初始化中...');
    
    // 检查后端连接
    const isHealthy = await checkHealth();
    if (isHealthy) {
        log('success', '后端服务已连接 (端口 5001)');
    } else {
        log('error', '后端服务连接失败，请确保已运行: python run.py');
        return;
    }
    
    // 初始化各个模块
    initTabs();
    initAuth();
    initUpload();
    initHistory();
    initTemplates();
    initStats();
    
    log('success', '系统初始化完成！');
}

// 启动应用
document.addEventListener('DOMContentLoaded', init);
