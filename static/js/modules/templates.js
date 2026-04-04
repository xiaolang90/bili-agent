import { get, post, del } from '../utils/api.js';
import { log } from '../utils/log.js';

/**
 * 当前模板列表
 * @type {Array}
 */
let currentTemplates = [];

/**
 * 分类映射数据
 * @type {Object|null}
 */
let categoryMapping = null;

/**
 * 当前选中的一级分类ID
 * @type {string|null}
 */
let currentMainCategoryId = null;

/**
 * 初始化模板模块
 * 
 * 加载模板列表并绑定事件
 */
export function initTemplates() {
    loadTemplates();
    loadCategoryMapping();
    bindEvents();
    initConfigHelpImage();
}

/**
 * 加载分类映射数据
 */
async function loadCategoryMapping() {
    try {
        const response = await fetch('/config/bilibili_tid_mapping.json');
        if (!response.ok) {
            throw new Error('Failed to load category mapping');
        }
        categoryMapping = await response.json();
        initCategorySelects();
    } catch (error) {
        log('error', `加载分类映射失败: ${error.message}`);
    }
}

/**
 * 初始化分类选择器
 * 用户选择一级分类后，显示对应的二级分类
 */
function initCategorySelects() {
    const mainSelect = document.getElementById('mainCategorySelect');
    const subSelect = document.getElementById('subCategorySelect');
    
    if (!mainSelect || !subSelect || !categoryMapping) return;
    
    // 填充分类选项（一级分类）
    mainSelect.innerHTML = '<option value="">-- 选择一级分类 --</option>';
    Object.entries(categoryMapping).forEach(([id, data]) => {
        const option = document.createElement('option');
        option.value = id;
        option.textContent = data.name;
        mainSelect.appendChild(option);
    });
    
    // 一级分类改变时更新二级分类选项
    mainSelect.addEventListener('change', () => {
        currentMainCategoryId = mainSelect.value;
        updateSubCategoryOptions();
        updateTidInput();
    });
    
    // 二级分类改变时更新 tid
    subSelect.addEventListener('change', () => {
        updateTidInput();
    });
}

/**
 * 更新二级分类选项
 */
function updateSubCategoryOptions() {
    const subSelect = document.getElementById('subCategorySelect');
    
    if (!subSelect || !categoryMapping || !currentMainCategoryId) {
        subSelect.innerHTML = '<option value="">-- 选择二级分类 --</option>';
        subSelect.disabled = true;
        return;
    }
    
    const categoryData = categoryMapping[currentMainCategoryId];
    if (!categoryData || !categoryData.sub_categories) {
        subSelect.innerHTML = '<option value="">-- 选择二级分类 --</option>';
        subSelect.disabled = true;
        return;
    }
    
    // 填充二级分类选项
    subSelect.innerHTML = '<option value="">-- 选择二级分类 --</option>';
    Object.entries(categoryData.sub_categories).forEach(([id, name]) => {
        const option = document.createElement('option');
        option.value = id;
        option.textContent = name;
        subSelect.appendChild(option);
    });
    subSelect.disabled = false;
}

/**
 * 更新隐藏的 tid 输入框
 * 使用选中的二级分类ID作为 tid
 */
function updateTidInput() {
    const subSelect = document.getElementById('subCategorySelect');
    const tidInput = document.getElementById('defaultTid');
    
    if (tidInput && subSelect) {
        tidInput.value = subSelect.value || '';
    }
}

/**
 * 根据 tid 设置分类选择器
 * 
 * @param {string} tid - 分类ID（二级分类的 tid）
 */
function setCategoryByTid(tid) {
    if (!categoryMapping || !tid) return;
    
    const mainSelect = document.getElementById('mainCategorySelect');
    const subSelect = document.getElementById('subCategorySelect');
    
    // 查找包含该 tid 的一级分类
    for (const [mainId, data] of Object.entries(categoryMapping)) {
        if (data.sub_categories && data.sub_categories[tid]) {
            // 设置一级分类
            mainSelect.value = mainId;
            currentMainCategoryId = mainId;
            
            // 更新二级分类选项
            updateSubCategoryOptions();
            
            // 设置二级分类
            subSelect.value = tid;
            
            // 更新 tid 输入框
            updateTidInput();
            return;
        }
    }
    
    // 如果没找到匹配的子分类，尝试直接匹配一级分类
    if (categoryMapping[tid]) {
        mainSelect.value = tid;
        currentMainCategoryId = tid;
        updateSubCategoryOptions();
        updateTidInput();
    }
}

/**
 * 初始化配置帮助图片点击全屏功能
 */
function initConfigHelpImage() {
    const tooltipImage = document.querySelector('.tooltip-image');
    if (tooltipImage) {
        tooltipImage.style.cursor = 'zoom-in';
        tooltipImage.addEventListener('click', (e) => {
            e.stopPropagation();
            showFullscreenImage(tooltipImage.src, tooltipImage.alt);
        });
    }
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
 * 绑定事件
 */
function bindEvents() {
    const saveAsDefaultBtn = document.getElementById('saveAsDefaultTemplateBtn');
    const deleteBtn = document.getElementById('deleteTemplateBtn');
    const templateSelect = document.getElementById('configTemplateSelect');
    
    // 选择模板后自动加载
    if (templateSelect) {
        templateSelect.addEventListener('change', () => {
            const templateId = templateSelect.value;
            if (templateId) {
                loadSelectedTemplate();
            } else {
                // 清空表单
                clearTemplateForm();
            }
        });
        console.log('[Templates] 模板选择器 change 事件已绑定');
    }
    
    if (saveAsDefaultBtn) {
        saveAsDefaultBtn.addEventListener('click', saveAsDefaultTemplate);
        console.log('[Templates] 存为模版并设为默认按钮事件已绑定');
    } else {
        console.warn('[Templates] 未找到存为模版并设为默认按钮');
    }
    
    if (deleteBtn) {
        deleteBtn.addEventListener('click', deleteSelectedTemplate);
        console.log('[Templates] 删除按钮事件已绑定');
    } else {
        console.warn('[Templates] 未找到删除按钮');
    }
}

/**
 * 清空模板表单
 */
function clearTemplateForm() {
    document.getElementById('templateName').value = '';
    document.getElementById('defaultTid').value = '';
    document.getElementById('defaultTags').value = '';
    document.getElementById('defaultDesc').value = '';
    // 重置分类选择器
    document.getElementById('mainCategorySelect').value = '';
    currentMainCategoryId = null;
    updateSubCategoryOptions();
}

/**
 * 加载模板列表
 */
async function loadTemplates() {
    try {
        console.log('[Templates] 开始加载模板列表...');
        const result = await get('/upload-config-templates');
        console.log('[Templates] 模板列表响应:', result);
        
        if (result.success) {
            currentTemplates = result.data || [];
            console.log('[Templates] 加载到模板数量:', currentTemplates.length);
            updateTemplateSelect();
        } else {
            console.warn('[Templates] 加载模板列表失败:', result.message);
        }
    } catch (error) {
        console.error('[Templates] 加载模板列表异常:', error);
        log('error', `加载模板列表失败: ${error.message}`);
    }
}

/**
 * 检查是否有默认配置
 * 
 * @returns {Promise<boolean>} 是否有默认配置
 */
export async function hasDefaultConfig() {
    try {
        const result = await get('/upload-config-templates/default');
        return result.success && result.data;
    } catch (e) {
        return false;
    }
}

/**
 * 获取上传配置
 * 
 * 优先获取默认模板，如果没有则从本地存储获取
 * 
 * @returns {Promise<Object|null>} 上传配置对象，如果没有配置则返回null
 */
export async function getUploadConfig() {
    // 优先获取默认模板
    try {
        const result = await get('/upload-config-templates/default');
        if (result.success && result.data) {
            return {
                tid: result.data.tid || '201',
                tags: result.data.tags || '',
                desc: result.data.description || ''
            };
        }
    } catch (e) {
        // 如果没有默认模板，显示红色醒目提示并强制用户交互
        if (e.message && e.message.includes('没有设置默认模板')) {
            showToast(
                '⚠️ 没有设置默认模板！请先创建并设置一个默认模板',
                'error',
                0,  // 不自动消失
                openSettingsAndScrollToConfig
            );
            return null;  // 返回null表示没有配置，阻断上传
        }
        console.log('获取默认模板:', e.message || '未设置');
    }
    
    // 如果没有默认模板，从本地存储获取
    try {
        const config = await localforage.getItem('bilibili_upload_config');
        if (config) {
            return {
                tid: config.tid || '201',
                tags: config.tags || '',
                desc: config.desc || ''
            };
        }
    } catch (e) {
        console.error('获取本地配置失败:', e);
    }
    
    // 返回默认值
    return {
        tid: '201',
        tags: '日语,双语字幕,出口仁,日语语法,JLPT,N3',
        desc: '出口仁老师N3语法课：{{title}}\n\n自动上传，请勿搬运'
    };
}

/**
 * 更新模板下拉选择框
 * 
 * 根据当前模板列表更新下拉框选项
 */
function updateTemplateSelect() {
    const select = document.getElementById('configTemplateSelect');
    select.innerHTML = '<option value="">-- 请选择模板 --</option>';
    
    currentTemplates.forEach(template => {
        console.log(`[Templates] 添加模板选项: ${template.name} (ID: ${template.id}, 默认: ${template.is_default})`);
        const option = document.createElement('option');
        option.value = template.id;
        option.textContent = template.name + (template.is_default ? ' (默认)' : '');
        select.appendChild(option);
    });
}

/**
 * 加载模板到表单
 * 
 * @param {Object} template - 模板数据对象
 */
function loadTemplateToForm(template) {
    document.getElementById('templateName').value = template.name || '';
    document.getElementById('defaultTid').value = template.tid || '';
    document.getElementById('defaultTags').value = template.tags || '';
    document.getElementById('defaultDesc').value = template.description || '';
    
    // 设置分类选择器
    setCategoryByTid(template.tid);
}

/**
 * 从表单获取配置数据
 * 
 * @returns {Object} 配置数据对象
 */
function getConfigFromForm() {
    return {
        name: document.getElementById('templateName').value.trim(),
        tid: document.getElementById('defaultTid').value.trim(),
        tags: document.getElementById('defaultTags').value.trim(),
        description: document.getElementById('defaultDesc').value.trim(),
        is_default: true  // 始终设为默认
    };
}

/**
 * 加载选中的模板
 * 
 * 从下拉框获取选中的模板并加载到表单
 */
async function loadSelectedTemplate() {
    const select = document.getElementById('configTemplateSelect');
    const templateId = select.value;
    
    if (!templateId) {
        log('warn', '请先选择一个模板');
        return;
    }
    
    const template = currentTemplates.find(t => t.id === templateId);
    if (template) {
        loadTemplateToForm(template);
        log('info', `已加载模板: ${template.name}`);
    }
}

/**
 * 存为模版并设为默认
 * 
 * 创建新模板并自动设为默认，不存在修改逻辑
 */
async function saveAsDefaultTemplate() {
    const config = getConfigFromForm();
    
    // 验证必填字段
    if (!config.name) {
        log('warn', '请输入模板名称');
        document.getElementById('templateName').focus();
        alert('⚠️ 请输入模板名称');
        return;
    }
    
    if (!config.tid) {
        log('warn', '请选择默认分类');
        alert('⚠️ 请选择默认分类');
        return;
    }
    
    if (!config.tags) {
        log('warn', '请输入默认标签');
        document.getElementById('defaultTags').focus();
        alert('⚠️ 请输入默认标签');
        return;
    }
    
    // 强制设为默认模板
    config.is_default = true;
    
    try {
        const result = await post('/upload-config-templates', config);
        log('success', '新模板已创建并设为默认');
        
        // 显示成功提示
        alert(`✅ 模板"${config.name}"已保存并设为默认！\n\n现在可以开始上传视频了。`);
        
        // 刷新模板列表
        await loadTemplates();
        
        // 选中新创建的模板（使用返回的 template_id 或 id）
        const newTemplateId = result.template_id || result.id;
        if (newTemplateId) {
            const select = document.getElementById('configTemplateSelect');
            select.value = newTemplateId;
            // 触发 change 事件以确保 UI 更新
            select.dispatchEvent(new Event('change'));
        }
    } catch (error) {
        // 直接使用 error.message（已由 api.js 处理为后端返回的消息）
        const errorMessage = error.message || '未知错误';
        
        log('error', `创建模板失败: ${errorMessage}`);
        alert(`❌ 创建模板失败\n\n${errorMessage}`);
    }
}

/**
 * 删除选中的模板
 * 
 * 从下拉框获取选中的模板并删除
 */
async function deleteSelectedTemplate() {
    const select = document.getElementById('configTemplateSelect');
    const templateId = select.value;
    
    if (!templateId) {
        log('warn', '请先选择一个模板');
        return;
    }
    
    const template = currentTemplates.find(t => t.id === templateId);
    if (!template) return;
    
    if (!confirm(`确定要删除模板 "${template.name}" 吗？`)) {
        return;
    }
    
    try {
        await del(`/upload-config-templates/${templateId}`);
        log('success', '模板已删除');
        
        // 清空表单
        document.getElementById('templateName').value = '';
        document.getElementById('defaultTid').value = '';
        document.getElementById('defaultTags').value = '';
        document.getElementById('defaultDesc').value = '';
        // 重置分类选择器
        document.getElementById('mainCategorySelect').value = '';
        
        await loadTemplates();
    } catch (error) {
        log('error', `删除模板失败: ${error.message}`);
    }
}

/**
 * 显示 Toast 通知
 * 
 * @param {string} message - 通知消息
 * @param {string} type - 通知类型: 'info' | 'success' | 'error' | 'warn'
 * @param {number} duration - 显示时长（毫秒）
 * @param {Function} onClick - 点击回调
 */
function showToast(message, type = 'info', duration = 3000, onClick = null) {
    // 创建 toast 元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // 图标
    const icons = {
        info: 'ℹ️',
        success: '✅',
        error: '❌',
        warn: '⚠️'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
        ${type === 'error' ? '<span style="margin-left:8px;font-size:12px;">点击前往设置 →</span>' : ''}
    `;
    
    // 样式
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : type === 'warn' ? '#f59e0b' : '#3b82f6'};
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
        z-index: 10000;
        font-size: 15px;
        font-weight: 500;
        animation: slideIn 0.3s ease;
        cursor: ${onClick ? 'pointer' : 'default'};
        max-width: 400px;
        line-height: 1.5;
    `;
    
    // 添加动画样式
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            @keyframes pulse {
                0%, 100% { box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4); }
                50% { box-shadow: 0 8px 32px rgba(239, 68, 68, 0.7); }
            }
            .toast-error {
                animation: slideIn 0.3s ease, pulse 2s infinite;
            }
        `;
        document.head.appendChild(style);
    }
    
    // 点击事件
    if (onClick) {
        toast.addEventListener('click', () => {
            onClick();
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        });
    }
    
    document.body.appendChild(toast);
    
    // 自动移除
    if (duration > 0) {
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    return toast;
}

/**
 * 打开设置Tab并滚动到上传配置部分
 */
function openSettingsAndScrollToConfig() {
    // 切换到设置Tab
    const settingsTabBtn = document.querySelector('[data-tab="tab-settings"]');
    if (settingsTabBtn) {
        settingsTabBtn.click();
    }
    
    // 滚动到上传配置部分
    setTimeout(() => {
        const configCard = document.querySelector('#tab-settings .card:nth-child(2)');
        if (configCard) {
            configCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // 高亮显示
            configCard.style.animation = 'highlight 1s ease';
            setTimeout(() => {
                configCard.style.animation = '';
            }, 1000);
        }
    }, 300);
}

// 添加高亮动画样式
if (!document.getElementById('highlight-style')) {
    const style = document.createElement('style');
    style.id = 'highlight-style';
    style.textContent = `
        @keyframes highlight {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
            50% { box-shadow: 0 0 20px 4px rgba(59, 130, 246, 0.5); }
        }
    `;
    document.head.appendChild(style);
}

