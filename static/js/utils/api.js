/**
 * API 请求工具模块
 * 
 * 封装所有与后端 API 的通信
 */

import { API_BASE_URL } from '../config.js';

/**
 * 发送 GET 请求
 * 
 * @param {string} endpoint - API 端点路径
 * @returns {Promise<any>} 响应数据
 * @throws {Error} 请求失败时抛出错误
 * 
 * @example
 * const data = await get('/history');
 * console.log(data);
 */
export async function get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

/**
 * 发送 POST 请求
 * 
 * @param {string} endpoint - API 端点路径
 * @param {Object} data - 请求体数据
 * @returns {Promise<any>} 响应数据
 * @throws {Error} 请求失败时抛出错误
 * 
 * @example
 * const result = await post('/auth', { sessdata: 'xxx', bili_jct: 'xxx', buvid3: 'xxx' });
 */
export async function post(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (!response.ok) {
        // 使用后端返回的错误消息
        const errorMessage = result.message || `HTTP ${response.status}: ${response.statusText}`;
        const error = new Error(errorMessage);
        error.responseData = result;
        throw error;
    }
    
    return result;
}

/**
 * 发送 DELETE 请求
 * 
 * @param {string} endpoint - API 端点路径
 * @returns {Promise<any>} 响应数据
 * @throws {Error} 请求失败时抛出错误
 * 
 * @example
 * await delete('/history/123');
 */
export async function del(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

/**
 * 上传文件
 * 
 * @param {string} endpoint - API 端点路径
 * @param {FormData} formData - 包含文件的表单数据
 * @returns {Promise<any>} 响应数据
 * @throws {Error} 上传失败时抛出错误
 * 
 * @example
 * const formData = new FormData();
 * formData.append('file', file);
 * formData.append('title', '视频标题');
 * const result = await upload('/upload/file', formData);
 */
export async function upload(endpoint, formData) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

/**
 * 检查服务器健康状态
 * 
 * @returns {Promise<boolean>} 服务器是否正常
 * 
 * @example
 * const isHealthy = await checkHealth();
 * if (isHealthy) {
 *     console.log('服务器运行正常');
 * }
 */
export async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return response.ok;
    } catch (e) {
        return false;
    }
}
