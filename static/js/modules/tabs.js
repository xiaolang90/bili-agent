/**
 * 标签页切换模块
 * 
 * 处理三个主要标签页的切换逻辑
 */

// 导入历史监控控制函数
import { startHistoryMonitor, stopHistoryMonitor, isHistoryMonitorRunning } from './history.js';

/**
 * 初始化标签页功能
 * 
 * 绑定标签按钮的点击事件，实现标签页切换
 */
export function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            
            // 移除所有活动状态
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            // 激活当前标签
            btn.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            // 处理历史数据监控
            handleHistoryMonitor(targetTab);
        });
    });
}

/**
 * 处理历史数据监控
 * 
 * 切换到仪表盘Tab时开启监控，切换到其他Tab时关闭监控
 * 
 * @param {string} targetTab - 目标Tab ID
 */
function handleHistoryMonitor(targetTab) {
    if (targetTab === 'tab-dashboard') {
        // 切换到仪表盘Tab，开启监控
        if (!isHistoryMonitorRunning()) {
            startHistoryMonitor();
            // 显示友好提示
            alert('✅ 已开启上传数据监控');
        }
    } else {
        // 切换到其他Tab，关闭监控
        if (isHistoryMonitorRunning()) {
            stopHistoryMonitor();
        }
    }
}
