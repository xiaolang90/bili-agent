/**
 * 历史记录模块
 * 
 * 处理上传历史记录的获取、显示、搜索和删除
 */

import { get, del, post } from '../utils/api.js';
import { log } from '../utils/log.js';
import { formatTime } from '../utils/format.js';
import { ITEMS_PER_PAGE, HISTORY_REFRESH_INTERVAL } from '../config.js';

/**
 * 当前页码
 * @type {number}
 */
let currentPage = 1;

/**
 * 所有历史数据（用于搜索）
 * @type {Array}
 */
let allHistoryData = [];

/**
 * 历史数据监控定时器
 * @type {number|null}
 */
let historyMonitorInterval = null;

/**
 * 监控是否正在运行
 * @type {boolean}
 */
let isMonitorRunning = false;

/**
 * 初始化历史记录模块
 * 
 * 加载历史记录并绑定事件
 */
export function initHistory() {
    fetchHistory();
    
    // 绑定事件
    document.getElementById('prevPage').addEventListener('click', () => goToPage(currentPage - 1));
    document.getElementById('nextPage').addEventListener('click', () => goToPage(currentPage + 1));
    document.getElementById('clearHistoryBtn').addEventListener('click', clearAllHistory);
    document.getElementById('historySearch').addEventListener('input', handleSearch);
    document.getElementById('clearSearchBtn').addEventListener('click', clearSearch);
    
    // 绑定监控按钮事件
    const monitorBtn = document.getElementById('toggleHistoryMonitorBtn');
    if (monitorBtn) {
        monitorBtn.addEventListener('click', toggleHistoryMonitor);
    }
}

/**
 * 切换历史数据监控状态
 */
function toggleHistoryMonitor() {
    if (isMonitorRunning) {
        stopHistoryMonitor();
    } else {
        startHistoryMonitor();
    }
}

/**
 * 开始历史数据监控
 */
export function startHistoryMonitor() {
    if (isMonitorRunning) return;
    
    isMonitorRunning = true;
    updateMonitorButtonState();
    
    // 立即执行一次
    fetchHistory();
    
    // 设置定时器
    historyMonitorInterval = setInterval(() => {
        const searchTerm = document.getElementById('historySearch').value;
        if (!searchTerm) {
            fetchHistory();
        }
    }, HISTORY_REFRESH_INTERVAL);
    
    log('info', '历史数据监控已开启');
}

/**
 * 停止历史数据监控
 */
export function stopHistoryMonitor() {
    if (!isMonitorRunning) return;
    
    isMonitorRunning = false;
    
    if (historyMonitorInterval) {
        clearInterval(historyMonitorInterval);
        historyMonitorInterval = null;
    }
    
    updateMonitorButtonState();
    log('info', '历史数据监控已关闭');
}

/**
 * 更新监控按钮状态
 */
function updateMonitorButtonState() {
    const btn = document.getElementById('toggleHistoryMonitorBtn');
    if (!btn) return;
    
    const icon = btn.querySelector('.monitor-icon');
    const text = btn.querySelector('.monitor-text');
    
    if (isMonitorRunning) {
        btn.classList.add('active');
        if (icon) icon.textContent = '🟢';
        if (text) text.textContent = '监控运行中';
    } else {
        btn.classList.remove('active');
        if (icon) icon.textContent = '🔴';
        if (text) text.textContent = '开始历史数据监控';
    }
}

/**
 * 获取监控状态
 * @returns {boolean} 是否正在监控
 */
export function isHistoryMonitorRunning() {
    return isMonitorRunning;
}

/**
 * 获取历史记录
 * 
 * 从服务器获取上传历史数据
 */
async function fetchHistory() {
    try {
        const result = await get(`/history?page=${currentPage}&limit=${ITEMS_PER_PAGE}`);
        if (result.success && result.data) {
            allHistoryData = result.data;
            renderHistory(allHistoryData);
            updatePagination();
        }
    } catch (e) {
        log('error', `获取历史记录失败: ${e.message}`);
    }
}

/**
 * 渲染历史记录表格
 * 
 * @param {Array} data - 历史记录数据
 */
function renderHistory(data) {
    const tbody = document.getElementById('historyTableBody');
    
    if (data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>暂无上传历史</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = data.map(item => {
        const isSuccess = item.status === 'success';
        const statusClass = isSuccess ? 'success' : 'error';
        const statusText = isSuccess ? '成功' : '失败';
        const statusIcon = isSuccess ? '✓' : '✗';
        
        return `
            <tr data-id="${item.id}">
                <td>
                    <span class="status-badge ${statusClass}">
                        ${statusIcon} ${statusText}
                    </span>
                </td>
                <td>${formatTime(item.started_at || item.created_at)}</td>
                <td>${escapeHtml(item.filename || '未知')}</td>
                <td>${escapeHtml(item.title || '未知')}</td>
                <td class="${isSuccess ? 'result-success' : 'result-error'}">
                    ${escapeHtml(item.message || (isSuccess ? '上传成功' : '上传失败'))}
                </td>
                <td>
                    <button class="delete-btn" data-delete-id="${item.id}">🗑️ 删除</button>
                </td>
            </tr>
        `;
    }).join('');
    
    // 绑定删除按钮事件
    tbody.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const id = e.target.dataset.deleteId;
            deleteHistoryItem(id);
        });
    });
}

/**
 * 处理搜索输入
 * 
 * @param {Event} e - 输入事件
 */
function handleSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    filterHistory(searchTerm);
}

/**
 * 过滤历史记录
 * 
 * @param {string} searchTerm - 搜索关键词
 */
function filterHistory(searchTerm) {
    const pagination = document.getElementById('pagination');
    
    if (!searchTerm) {
        pagination.style.display = 'flex';
        renderHistory(allHistoryData);
        return;
    }
    
    // 搜索时隐藏分页
    pagination.style.display = 'none';
    
    const filtered = allHistoryData.filter(item => {
        const filenameMatch = item.filename && item.filename.toLowerCase().includes(searchTerm);
        const titleMatch = item.title && item.title.toLowerCase().includes(searchTerm);
        return filenameMatch || titleMatch;
    });
    
    renderHistory(filtered);
}

/**
 * 清空搜索
 */
function clearSearch() {
    document.getElementById('historySearch').value = '';
    filterHistory('');
}

/**
 * 跳转到指定页
 * 
 * @param {number} page - 目标页码
 */
function goToPage(page) {
    if (page < 1) return;
    currentPage = page;
    fetchHistory();
}

/**
 * 更新分页按钮状态
 */
function updatePagination() {
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = allHistoryData.length < ITEMS_PER_PAGE;
    pageInfo.textContent = `第 ${currentPage} 页`;
}

/**
 * 删除单条历史记录
 * 
 * @param {string} id - 历史记录ID
 */
async function deleteHistoryItem(id) {
    if (!confirm('确定要删除这条上传记录吗？')) return;
    
    try {
        await del(`/history/${id}`);
        allHistoryData = allHistoryData.filter(item => item.id !== id);
        renderHistory(allHistoryData);
        log('success', '已删除上传记录');
    } catch (e) {
        log('error', `删除失败: ${e.message}`);
    }
}

/**
 * 清空所有历史记录
 */
async function clearAllHistory() {
    if (!confirm('确定要清空所有上传历史吗？此操作不可恢复！')) return;
    
    try {
        await post('/history/clear', {});
        allHistoryData = [];
        renderHistory([]);
        log('success', '已清空所有上传历史');
    } catch (e) {
        log('error', `清空历史失败: ${e.message}`);
    }
}

/**
 * 转义 HTML 特殊字符
 * 
 * @param {string} text - 原始文本
 * @returns {string} 转义后的文本
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
