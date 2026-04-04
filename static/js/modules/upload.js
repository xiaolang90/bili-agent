/**
 * 上传模块
 * 
 * 处理文件上传、队列管理和进度显示
 */

import { upload, get } from '../utils/api.js';
import { log } from '../utils/log.js';
import { formatFileSize } from '../utils/format.js';
import { STATUS_TEXT } from '../config.js';
import { getUploadConfig, hasDefaultConfig } from './templates.js';

/**
 * 上传队列
 * @type {Array}
 */
let uploadQueue = [];

/**
 * 是否正在上传
 * @type {boolean}
 */
let isUploading = false;

/**
 * 初始化上传模块
 * 
 * 绑定拖拽、文件选择和上传按钮事件
 */
export function initUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    
    // 点击上传区域触发文件选择
    dropZone.addEventListener('click', () => fileInput.click());
    
    // 拖拽事件
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        addFiles(e.dataTransfer.files);
    });
    
    // 文件选择事件
    fileInput.addEventListener('change', () => {
        addFiles(fileInput.files);
    });
    
    // 上传按钮
    document.getElementById('uploadBtn').addEventListener('click', startUpload);
}

/**
 * 添加文件到上传队列
 * 
 * @param {FileList} files - 文件列表
 */
function addFiles(files) {
    let addedCount = 0;
    for (const file of files) {
        if (file.type.startsWith('video/')) {
            uploadQueue.push({
                file: file,
                status: 'added',
                progress: 0
            });
            log('info', `已添加视频: ${file.name} (${formatFileSize(file.size)})`);
            addedCount++;
        } else {
            log('error', `不支持的文件类型: ${file.name}`);
        }
    }
    updateFileList();
    
    // 如果有文件被添加，滚动到上传队列区域，距离顶部100px
    if (addedCount > 0) {
        scrollToUploadQueue();
    }
}

/**
 * 滚动到上传队列区域
 * 距离顶部100px
 */
function scrollToUploadQueue() {
    const uploadQueueCard = document.querySelector('#tab-upload .card:nth-child(2)');
    if (uploadQueueCard) {
        const offsetTop = uploadQueueCard.getBoundingClientRect().top + window.pageYOffset - 100;
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

/**
 * 更新文件列表显示
 * 
 * 渲染上传队列到页面
 */
function updateFileList() {
    const fileListEl = document.getElementById('fileList');
    
    if (uploadQueue.length === 0) {
        fileListEl.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <p>暂无待上传文件</p>
            </div>
        `;
        return;
    }
    
    fileListEl.innerHTML = uploadQueue.map((item, index) => `
        <div class="file-item" data-index="${index}">
            <div class="file-info">
                <span class="file-name">${item.file.name}</span>
                <span class="file-size">${formatFileSize(item.file.size)}</span>
            </div>
            <div class="file-status-wrapper">
                ${item.status === 'added' ? `
                    <button class="remove-queue-btn" data-index="${index}" title="移除队列">✕</button>
                ` : ''}
                ${item.status === 'uploading' ? `
                    <button class="cancel-upload-btn" data-index="${index}" title="取消上传">✕</button>
                ` : ''}
                ${item.status === 'error' || item.status === 'cancelled' ? `
                    <button class="retry-upload-btn" data-index="${index}" title="重新上传">🔄</button>
                ` : ''}
                <span class="file-status ${item.status}">${STATUS_TEXT[item.status] || item.status}</span>
            </div>
        </div>
        ${item.status === 'uploading' || item.status === 'error' || item.status === 'cancelled' ? `
            <div class="progress-bar-container">
                <div class="progress-bar">
                    <div class="progress-fill ${item.status === 'error' || item.status === 'cancelled' ? 'error' : ''}" style="width: ${item.progress}%"></div>
                </div>
                <span class="progress-text">${item.progress}%</span>
            </div>
            <div class="progress-message">${item.progressMessage || '准备上传...'}</div>
        ` : ''}
    `).join('');
    
    // 绑定移除队列按钮事件
    document.querySelectorAll('.remove-queue-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const index = parseInt(btn.dataset.index);
            removeFromQueue(index);
        });
    });
    
    // 绑定取消上传按钮事件
    document.querySelectorAll('.cancel-upload-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const index = parseInt(btn.dataset.index);
            cancelUpload(index);
        });
    });
    
    // 绑定重新上传按钮事件
    document.querySelectorAll('.retry-upload-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const index = parseInt(btn.dataset.index);
            retryUpload(index);
        });
    });
}

/**
 * 显示居中强提示 Alert
 * 
 * @param {string} message - 提示消息
 * @param {Function} onConfirm - 确认回调
 */
function showCenterAlert(message, onConfirm) {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'alert-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        backdrop-filter: blur(4px);
    `;
    
    // 创建提示框
    const alertBox = document.createElement('div');
    alertBox.className = 'alert-box';
    alertBox.style.cssText = `
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 2px solid #ef4444;
        border-radius: 16px;
        padding: 32px 40px;
        max-width: 420px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(239, 68, 68, 0.4), 0 0 0 1px rgba(239, 68, 68, 0.2);
        animation: alertSlideIn 0.3s ease;
    `;
    
    alertBox.innerHTML = `
        <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
        <h3 style="color: #ef4444; font-size: 20px; margin-bottom: 16px; font-weight: 600;">无法开始上传</h3>
        <p style="color: #cbd5e1; font-size: 15px; line-height: 1.6; margin-bottom: 24px;">${message}</p>
        <button id="alertConfirmBtn" style="
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border: none;
            padding: 12px 32px;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        ">前往设置</button>
    `;
    
    overlay.appendChild(alertBox);
    document.body.appendChild(overlay);
    
    // 添加动画样式
    if (!document.getElementById('alert-animations')) {
        const style = document.createElement('style');
        style.id = 'alert-animations';
        style.textContent = `
            @keyframes alertSlideIn {
                from { transform: scale(0.9); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            @keyframes alertSlideOut {
                from { transform: scale(1); opacity: 1; }
                to { transform: scale(0.9); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
    
    // 绑定确认按钮事件
    const confirmBtn = alertBox.querySelector('#alertConfirmBtn');
    confirmBtn.addEventListener('mouseenter', () => {
        confirmBtn.style.transform = 'scale(1.05)';
        confirmBtn.style.boxShadow = '0 4px 16px rgba(239, 68, 68, 0.4)';
    });
    confirmBtn.addEventListener('mouseleave', () => {
        confirmBtn.style.transform = 'scale(1)';
        confirmBtn.style.boxShadow = 'none';
    });
    
    confirmBtn.addEventListener('click', () => {
        alertBox.style.animation = 'alertSlideOut 0.2s ease';
        setTimeout(() => {
            overlay.remove();
            if (onConfirm) onConfirm();
        }, 200);
    });
    
    // 点击遮罩层关闭
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            alertBox.style.animation = 'alertSlideOut 0.2s ease';
            setTimeout(() => overlay.remove(), 200);
        }
    });
}

/**
 * 检查上传会话是否已初始化
 * 
 * 通过检查是否有认证配置来判断
 * @returns {Promise<boolean>} 会话是否已初始化
 */
async function checkUploadSession() {
    try {
        // 检查是否有认证配置
        const result = await get('/auth');
        // 如果有认证数据且包含 sessdata，说明已配置
        if (result.success && result.data && result.data.sessdata) {
            return true;
        }
        return false;
    } catch (e) {
        return false;
    }
}

/**
 * 开始上传
 * 
 * 上传队列中的所有文件
 */
async function startUpload() {
    if (isUploading) {
        log('error', '正在上传中，请等待完成');
        return;
    }
    
    const waitingItems = uploadQueue.filter(item => item.status === 'added');
    if (waitingItems.length === 0) {
        // 未上传视频时，先滚动到添加视频文件区域
        const dropZoneCard = document.querySelector('#tab-upload .card:first-child');
        if (dropZoneCard) {
            const offsetTop = dropZoneCard.getBoundingClientRect().top + window.pageYOffset - 20;
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
        // 延迟显示提示，让用户先看到滚动效果
        setTimeout(() => {
            showCenterAlert('请先添加视频文件！<br>点击或拖拽视频文件到上传区域。', null);
        }, 300);
        return;
    }
    
    // 先检查上传会话是否已初始化
    const sessionReady = await checkUploadSession();
    if (!sessionReady) {
        showCenterAlert(
            '您需要先录入B站登录信息！<br>请前往「设置」选项卡 填写并保存 B站 认证信息（SESSDATA、bili_jct、buvid3），然后点击「保存认证信息」按钮，设置页有教程，包教包会。',
            () => {
                // 切换到设置 Tab
                const settingsTabBtn = document.querySelector('[data-tab="tab-settings"]');
                if (settingsTabBtn) {
                    settingsTabBtn.click();
                }
                // 滚动到认证配置区域
                setTimeout(() => {
                    const settingsPane = document.getElementById('tab-settings');
                    if (settingsPane) {
                        const authCard = settingsPane.querySelector('.card');
                        if (authCard) {
                            authCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
                }, 100);
            }
        );
        return;
    }
    
    // 再检查是否有默认模板
    const hasDefault = await hasDefaultConfig();
    if (!hasDefault) {
        showCenterAlert(
            '您还没有设置默认上传模板！<br>请先前往「设置」选项卡 创建并设置一个默认模板，否则无法开始上传。',
            () => {
                // 切换到设置 Tab
                const settingsTabBtn = document.querySelector('[data-tab="tab-settings"]');
                if (settingsTabBtn) {
                    settingsTabBtn.click();
                }
            }
        );
        return;
    }
    
    // 获取上传配置
    const uploadConfig = await getUploadConfig();
    
    // 如果没有配置（返回null），阻断上传流程
    if (!uploadConfig) {
        log('error', '上传已阻断：未设置默认模板');
        return;
    }
    
    log('info', `使用配置: 分类ID=${uploadConfig.tid}, 标签=${uploadConfig.tags}`);
    
    isUploading = true;
    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ 上传中...';
    
    log('info', `开始上传 ${waitingItems.length} 个文件...`);
    
    // 逐个上传文件（使用 SSE 同步上传）
    for (const item of waitingItems) {
        item.status = 'uploading';
        updateFileList();
        
        try {
            // 处理描述中的占位符
            let videoTitle = item.file.name.replace(/\.[^/.]+$/, '');
            // 标题不能超过70个字符，超过则截取前70个字符
            if (videoTitle.length > 70) {
                videoTitle = videoTitle.substring(0, 70);
                log('warn', `视频标题过长，已截取前70个字符: ${videoTitle}`);
            }
            const desc = uploadConfig.desc.replace(/\{\{title\}\}/g, videoTitle);
            
            // 生成唯一上传 ID
            const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            item.uploadId = uploadId;
            
            // 创建 SSE 连接接收进度
            const eventSource = new EventSource(`/api/upload/progress/${uploadId}`);
            let sseClosed = false;
            
            // 监听进度更新
            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'heartbeat' || data.type === 'connected') {
                        return; // 忽略心跳和连接消息
                    }
                    
                    if (data.progress !== undefined) {
                        item.progress = data.progress;
                        item.progressMessage = data.message;
                        updateFileList();
                        
                        // 更新日志
                        if (data.progress % 10 === 0) {
                            log('info', `${item.file.name}: ${data.progress}% - ${data.message}`);
                        }
                    }
                    
                    // 上传完成或出错或取消
                    if (data.status === 'completed' || data.status === 'error' || data.status === 'cancelled') {
                        if (!sseClosed) {
                            sseClosed = true;
                            eventSource.close();
                        }
                    }
                } catch (e) {
                    console.error('解析 SSE 消息失败:', e);
                }
            };
            
            eventSource.onerror = (error) => {
                if (!sseClosed) {
                    sseClosed = true;
                    eventSource.close();
                }
            };
            
            // 创建表单数据
            const formData = new FormData();
            formData.append('file', item.file);
            formData.append('title', videoTitle);
            formData.append('desc', desc);
            formData.append('tags', uploadConfig.tags);
            formData.append('tid', uploadConfig.tid);
            formData.append('upload_id', uploadId);
            
            // 使用 fetch 同步上传
            const response = await fetch('/api/upload/sync', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            // 关闭 SSE 连接
            eventSource.close();
            
            if (result.success) {
                item.status = 'success';
                item.progress = 100;
                log('success', `${item.file.name}: 上传成功`);
            } else {
                item.status = 'error';
                item.progressMessage = result.message;
                log('error', `${item.file.name}: ${result.message}`);
            }
        } catch (error) {
            item.status = 'error';
            item.progressMessage = error.message;
            log('error', `${item.file.name}: ${error.message}`);
        }
        
        updateFileList();
    }
    
    // 上传完成
    isUploading = false;
    uploadBtn.disabled = false;
    uploadBtn.textContent = '🚀 开始上传';
    log('success', '所有上传任务已完成');
    
    // 清空已完成的文件
    setTimeout(() => {
        uploadQueue = uploadQueue.filter(item => item.status !== 'success');
        updateFileList();
    }, 3000);
}

/**
 * 取消上传
 * 
 * @param {number} index - 文件在队列中的索引
 */
async function cancelUpload(index) {
    const item = uploadQueue[index];
    if (!item || item.status !== 'uploading') {
        return;
    }
    
    if (!confirm(`确定要取消上传 "${item.file.name}" 吗？`)) {
        return;
    }
    
    try {
        // 发送取消请求到后端
        const response = await fetch(`/api/upload/cancel/${item.uploadId}`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            item.status = 'cancelled';
            item.progress = 0;
            item.progressMessage = '已取消';
            log('info', `${item.file.name}: 上传已取消`);
        } else {
            log('error', `${item.file.name}: 取消上传失败 - ${result.message}`);
        }
    } catch (error) {
        // 即使请求失败，也标记为已取消
        item.status = 'cancelled';
        item.progress = 0;
        item.progressMessage = '已取消';
        log('info', `${item.file.name}: 上传已取消`);
    }
    
    updateFileList();
}

/**
 * 重新上传
 * 
 * @param {number} index - 文件在队列中的索引
 */
async function retryUpload(index) {
    const item = uploadQueue[index];
    if (!item || (item.status !== 'error' && item.status !== 'cancelled')) {
        return;
    }
    
    // 重置状态
    item.status = 'added';
    item.progress = 0;
    item.progressMessage = '';
    updateFileList();
    
    log('info', `${item.file.name}: 已重置为待上传状态`);
    
    // 自动开始上传（如果当前没有在上传）
    if (!isUploading) {
        startUpload();
    }
}

/**
 * 从队列中移除文件
 * 
 * @param {number} index - 文件在队列中的索引
 */
function removeFromQueue(index) {
    const item = uploadQueue[index];
    if (!item || item.status !== 'added') {
        return;
    }
    
    if (!confirm(`确定要从队列中移除 "${item.file.name}" 吗？`)) {
        return;
    }
    
    // 从队列中移除
    uploadQueue.splice(index, 1);
    log('info', `${item.file.name}: 已从队列中移除`);
    
    updateFileList();
}
