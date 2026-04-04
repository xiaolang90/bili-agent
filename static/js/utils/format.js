/**
 * 格式化工具模块
 * 
 * 提供各种数据格式化功能
 */

/**
 * 格式化时间字符串
 * 
 * 将 ISO 时间字符串格式化为易读的日期和时间
 * 
 * @param {string} timeStr - ISO 格式时间字符串
 * @returns {string} 格式化后的 HTML 字符串
 * 
 * @example
 * const html = formatTime('2024-01-15T10:30:00');
 * // 返回: <div class="time-date">2024/01/15</div><div class="time-hms">10:30:00</div>
 */
export function formatTime(timeStr) {
    if (!timeStr) return '-';
    
    const date = new Date(timeStr);
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
        timeZone: 'Asia/Shanghai'
    };
    
    // 使用东八区时间格式化
    const formatter = new Intl.DateTimeFormat('zh-CN', options);
    const parts = formatter.formatToParts(date);
    
    // 提取日期和时间部分
    const datePart = `${parts.find(p => p.type === 'year').value}/${parts.find(p => p.type === 'month').value}/${parts.find(p => p.type === 'day').value}`;
    const timePart = `${parts.find(p => p.type === 'hour').value}:${parts.find(p => p.type === 'minute').value}:${parts.find(p => p.type === 'second').value}`;
    
    return `<div class="time-date">${datePart}</div><div class="time-hms">${timePart}</div>`;
}

/**
 * 格式化文件大小
 * 
 * @param {number} bytes - 文件大小（字节）
 * @returns {string} 格式化后的字符串
 * 
 * @example
 * formatFileSize(1024);      // "1.00 KB"
 * formatFileSize(1048576);   // "1.00 MB"
 * formatFileSize(1073741824); // "1.00 GB"
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + units[i];
}

/**
 * 截断文件名
 * 
 * 保留文件名的开头和扩展名，中间用省略号代替
 * 
 * @param {string} filename - 原始文件名
 * @param {number} maxLength - 最大长度（默认 30）
 * @returns {string} 截断后的文件名
 * 
 * @example
 * truncateFilename('very_long_filename_here.mp4', 20);
 * // 返回: 'very_lo...here.mp4'
 */
export function truncateFilename(filename, maxLength = 30) {
    if (filename.length <= maxLength) {
        return filename;
    }
    
    const extIndex = filename.lastIndexOf('.');
    if (extIndex > 0) {
        const ext = filename.slice(extIndex);
        const name = filename.slice(0, extIndex);
        const keep = maxLength - ext.length - 3;
        
        if (keep > 5) {
            return name.slice(0, keep) + '...' + ext;
        }
    }
    
    return filename.slice(0, maxLength - 3) + '...';
}

/**
 * 转义 HTML 特殊字符
 * 
 * 防止 XSS 攻击
 * 
 * @param {string} text - 原始文本
 * @returns {string} 转义后的文本
 * 
 * @example
 * escapeHtml('<script>alert("xss")</script>');
 * // 返回: '<script>alert("xss")</script>'
 */
export function escapeHtml(text) {
    if (!text) return '';
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
