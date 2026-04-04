/**
 * 认证管理模块
 * 
 * 处理 B站 Cookie 认证的加载、保存和测试
 */

import { get, post } from '../utils/api.js';
import { log } from '../utils/log.js';

/**
 * 初始化认证模块
 * 
 * 加载保存的认证信息并绑定事件
 */
export function initAuth() {
    loadAuth();
    
    // 绑定保存按钮
    document.getElementById('saveAuthBtn').addEventListener('click', saveAuth);
    
    // 绑定清空按钮
    document.getElementById('clearAuthBtn').addEventListener('click', clearAuth);
    
    // 初始化帮助图片点击全屏
    initAuthHelpImage();
    
    // 绑定复制按钮
    initCopyButtons();
}

/**
 * 初始化复制按钮
 * 
 * 为每个复制按钮绑定点击事件，复制字段名到剪贴板
 */
function initCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    copyButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const fieldName = btn.dataset.field;
            
            try {
                await navigator.clipboard.writeText(fieldName);
                
                // 显示复制成功状态
                const originalText = btn.textContent;
                btn.textContent = '✅ 已复制';
                btn.classList.add('copied');
                
                // 显示详细提示弹框
                showCopyModal(fieldName);
                
                // 2秒后恢复按钮状态
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('copied');
                }, 2000);
                
            } catch (err) {
                log('error', `复制失败: ${err.message}`);
                showCopyModal(fieldName, true);
            }
        });
    });
}

/**
 * 显示复制成功提示弹框
 * 
 * @param {string} fieldName - 字段名
 * @param {boolean} isError - 是否错误
 */
function showCopyModal(fieldName, isError = false) {
    // 如果已存在弹框，先移除
    const existingModal = document.querySelector('.copy-modal-overlay');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'copy-modal-overlay';
    
    // 创建弹框
    const modal = document.createElement('div');
    modal.className = 'copy-modal';
    
    const icon = isError ? '❌' : '✅';
    const title = isError ? '复制失败' : '复制成功';
    const message = isError 
        ? `无法复制 "${fieldName}" 到剪贴板，请手动复制。`
        : `已将 "<strong>${fieldName}</strong>" 粘贴到剪切板`;
    
    modal.innerHTML = `
        <div class="copy-modal-icon">${icon}</div>
        <div class="copy-modal-title">${title}</div>
        <div class="copy-modal-message">${message}</div>
        ${!isError ? `
        <div class="copy-modal-steps">
            <div class="copy-modal-step">
                <span class="step-num">1</span>
                <span>打开浏览器开发者工具，顶部菜单中找到【应用】/【Application】</span>
            </div>
            <div class="copy-modal-step">
                <span class="step-num">2</span>
                <span>切换到 Cookie 标签</span>
            </div>
            <div class="copy-modal-step">
                <span class="step-num">3</span>
                <span>搜索 "<code>${fieldName}</code>"</span>
            </div>
            <div class="copy-modal-step">
                <span class="step-num">4</span>
                <span>复制对应的【值】字段</span>
            </div>
        </div>
        <div class="copy-modal-hint">💡 粘贴到上方对应输入框中</div>
        ` : ''}
        <button class="copy-modal-close">知道了</button>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // 添加动画样式（如果不存在）
    if (!document.getElementById('copy-modal-styles')) {
        const style = document.createElement('style');
        style.id = 'copy-modal-styles';
        style.textContent = `
            .copy-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                animation: fadeIn 0.3s ease;
                backdrop-filter: blur(5px);
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            @keyframes slideUpModal {
                from { transform: translateY(30px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            .copy-modal {
                background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 32px;
                max-width: 420px;
                width: 90%;
                text-align: center;
                animation: slideUpModal 0.4s ease;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
            }
            .copy-modal-icon {
                font-size: 48px;
                margin-bottom: 16px;
            }
            .copy-modal-title {
                font-size: 20px;
                font-weight: 600;
                color: #fff;
                margin-bottom: 12px;
            }
            .copy-modal-message {
                font-size: 15px;
                color: rgba(255, 255, 255, 0.8);
                margin-bottom: 20px;
                line-height: 1.6;
            }
            .copy-modal-message strong {
                color: #60a5fa;
                font-weight: 600;
            }
            .copy-modal-message code {
                background: rgba(96, 165, 250, 0.2);
                color: #60a5fa;
                padding: 2px 8px;
                border-radius: 4px;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 13px;
            }
            .copy-modal-steps {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 16px;
                text-align: left;
            }
            .copy-modal-step {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 12px;
                font-size: 14px;
                color: rgba(255, 255, 255, 0.7);
            }
            .copy-modal-step:last-child {
                margin-bottom: 0;
            }
            .step-num {
                width: 24px;
                height: 24px;
                background: rgba(96, 165, 250, 0.2);
                color: #60a5fa;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: 600;
                flex-shrink: 0;
            }
            .copy-modal-hint {
                font-size: 13px;
                color: rgba(255, 255, 255, 0.5);
                margin-bottom: 24px;
                padding: 10px 16px;
                background: rgba(251, 114, 153, 0.1);
                border-radius: 8px;
                border-left: 3px solid #fb7299;
            }
            .copy-modal-close {
                background: linear-gradient(135deg, #fb7299 0%, #e64a85 100%);
                color: white;
                border: none;
                padding: 12px 32px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .copy-modal-close:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(251, 114, 153, 0.4);
            }
        `;
        document.head.appendChild(style);
    }
    
    // 绑定关闭事件
    const closeBtn = modal.querySelector('.copy-modal-close');
    closeBtn.addEventListener('click', () => {
        overlay.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => overlay.remove(), 300);
    });
    
    // 点击遮罩关闭
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => overlay.remove(), 300);
        }
    });
}

/**
 * 清空认证信息
 * 
 * 删除数据库中的认证信息并清空输入框
 */
async function clearAuth() {
    if (!confirm('确定要清空认证信息吗？这将删除所有保存的认证数据。')) {
        return;
    }
    
    const clearBtn = document.getElementById('clearAuthBtn');
    const originalText = clearBtn.textContent;
    
    try {
        // 显示 Loading 状态
        setButtonLoading(clearBtn, true, '清空中...');
        
        // 调用后端接口删除认证信息
        const result = await post('/auth/clear', {});
        
        if (result.success) {
            // 清空输入框
            document.getElementById('sessdata').value = '';
            document.getElementById('bili_jct').value = '';
            document.getElementById('buvid3').value = '';
            
            // 启用输入框
            setAuthInputsDisabled(false);
            
            log('success', '认证信息已清空');
            alert('✅ 认证信息已清空！');
        } else {
            log('error', `清空认证信息失败: ${result.message}`);
            alert(`❌ 清空认证信息失败\n\n${result.message}`);
        }
    } catch (error) {
        log('error', `清空认证信息失败: ${error.message}`);
        alert(`❌ 清空认证信息失败\n\n${error.message}`);
    } finally {
        // 恢复按钮状态
        setButtonLoading(clearBtn, false, originalText);
    }
}

/**
 * 设置认证输入框的禁用状态
 * 
 * @param {boolean} disabled - 是否禁用
 */
function setAuthInputsDisabled(disabled) {
    const inputs = ['sessdata', 'bili_jct', 'buvid3'];
    inputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.disabled = disabled;
            if (disabled) {
                input.style.opacity = '0.6';
                input.style.cursor = 'not-allowed';
            } else {
                input.style.opacity = '1';
                input.style.cursor = 'text';
            }
        }
    });
}

/**
 * 初始化认证帮助图片点击全屏功能
 */
function initAuthHelpImage() {
    const guideImages = document.querySelectorAll('.tooltip-guide-image');
    guideImages.forEach((guideImage) => {
        guideImage.addEventListener('click', (e) => {
            e.stopPropagation();
            showFullscreenImage(guideImage.src, guideImage.alt);
        });
    });
}

/**
 * 全屏显示图片
 * 
 * @param {string} src - 图片地址
 * @param {string} alt - 图片描述
 */
function showFullscreenImage(src, alt) {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'image-fullscreen-overlay';
    
    // 创建容器
    const container = document.createElement('div');
    container.className = 'image-fullscreen-container';
    
    // 创建图片
    const img = document.createElement('img');
    img.src = src;
    img.alt = alt;
    
    // 创建关闭提示
    const closeHint = document.createElement('div');
    closeHint.className = 'image-fullscreen-close';
    closeHint.textContent = '点击任意处关闭';
    
    container.appendChild(img);
    container.appendChild(closeHint);
    overlay.appendChild(container);
    document.body.appendChild(overlay);
    
    // 点击关闭
    overlay.addEventListener('click', () => {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 300);
    });
    
    // ESC键关闭
    const closeOnEsc = (e) => {
        if (e.key === 'Escape') {
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 300);
            document.removeEventListener('keydown', closeOnEsc);
        }
    };
    document.addEventListener('keydown', closeOnEsc);
}

/**
 * 从服务器加载认证配置
 * 
 * 获取数据库中保存的认证信息并填充到表单
 */
async function loadAuth() {
    try {
        const result = await get('/auth');
        if (result.success && result.data) {
            const auth = result.data;
            document.getElementById('sessdata').value = auth.sessdata || '';
            document.getElementById('bili_jct').value = auth.bili_jct || '';
            document.getElementById('buvid3').value = auth.buvid3 || '';
            
            // 如果有认证信息，禁用输入框并初始化上传会话
            if (auth.sessdata || auth.bili_jct || auth.buvid3) {
                setAuthInputsDisabled(true);
                
                // 自动初始化上传会话
                try {
                    await post('/upload/init', {});
                    log('info', '上传会话已自动初始化');
                } catch (initError) {
                    log('warn', `自动初始化上传会话失败: ${initError.message}`);
                }
            }
            
            log('info', '已从服务器加载认证信息');
        }
    } catch (e) {
        log('warn', '加载认证信息失败');
    }
}

/**
 * 保存认证配置
 * 
 * 验证并保存认证信息到服务器
 */
async function saveAuth() {
    const sessdata = document.getElementById('sessdata').value.trim();
    const bili_jct = document.getElementById('bili_jct').value.trim();
    const buvid3 = document.getElementById('buvid3').value.trim();
    
    // 验证输入
    if (!sessdata && !bili_jct && !buvid3) {
        log('info', '未填写认证信息');
        // 触发"如何获取"按钮的 hover 效果
        showAuthHelpTooltip();
        return;
    }
    
    if (!sessdata || !bili_jct || !buvid3) {
        log('warn', '请填写完整的认证信息');
        return;
    }
    
    const saveBtn = document.getElementById('saveAuthBtn');
    const originalText = saveBtn.textContent;
    
    try {
        // 显示 Loading 状态
        setButtonLoading(saveBtn, true);
        
        // 先测试认证信息
        log('info', '正在验证认证信息...');
        const testResult = await post('/auth/test', { sessdata, bili_jct, buvid3 });
        
        if (!testResult.success) {
            log('error', `认证验证失败: ${testResult.message}`);
            alert(`❌ 认证验证失败\n\n${testResult.message}`);
            return;
        }
        
        // 验证成功，保存到服务器
        await post('/auth', { sessdata, bili_jct, buvid3 });
        
        const userName = testResult.data?.name || '未知用户';
        log('success', `认证信息已保存，用户: ${userName}`);
        
        // 显示用户可感知的提示
        alert(`✅ 认证信息保存成功！\n\n用户: ${userName}\n\n上传会话已初始化，可以开始上传视频了。`);
        
        // 初始化上传会话
        await post('/upload/init', {});
        log('info', '上传会话已初始化');
        
        // 认证成功后禁用输入框
        setAuthInputsDisabled(true);
        
    } catch (error) {
        log('error', `保存认证失败: ${error.message}`);
        alert(`❌ 保存认证失败\n\n${error.message}`);
    } finally {
        // 恢复按钮状态
        setButtonLoading(saveBtn, false, originalText);
    }
}

/**
 * 设置按钮 Loading 状态
 * 
 * @param {HTMLElement} button - 按钮元素
 * @param {boolean} isLoading - 是否显示 Loading
 * @param {string} originalText - 原始按钮文字（恢复时使用）
 */
function setButtonLoading(button, isLoading, originalText = '') {
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = `
            <span class="loading-spinner"></span>
            <span>保存中...</span>
        `;
        button.style.cursor = 'not-allowed';
    } else {
        button.disabled = false;
        button.textContent = originalText || '保存认证信息';
        button.style.cursor = 'pointer';
    }
}

/**
 * 显示认证帮助提示
 * 
 * 触发"如何获取"按钮的 hover 效果
 */
function showAuthHelpTooltip() {
    const helpBtn = document.querySelector('.help-btn');
    if (helpBtn) {
        // 添加 show 类来触发 tooltip 显示
        helpBtn.classList.add('show-tooltip');
        
        // 3秒后自动隐藏
        setTimeout(() => {
            helpBtn.classList.remove('show-tooltip');
        }, 3000);
        
        // 点击其他地方时隐藏
        const hideTooltip = (e) => {
            if (!helpBtn.contains(e.target)) {
                helpBtn.classList.remove('show-tooltip');
                document.removeEventListener('click', hideTooltip);
            }
        };
        
        // 延迟绑定点击事件，避免立即触发
        setTimeout(() => {
            document.addEventListener('click', hideTooltip);
        }, 100);
    }
}
