/**
 * 音频工具模块
 * 
 * 提供安全的音频播放功能，避免 AbortError 错误
 */

/**
 * 安全播放音频
 * 
 * 处理浏览器自动播放策略，避免 play() 被中断的错误
 * 
 * @param {HTMLAudioElement} audio - 音频元素
 * @returns {Promise<boolean>} 是否成功播放
 */
export async function safePlay(audio) {
    if (!audio) return false;
    
    try {
        // 如果音频已经在播放，先暂停并重置
        if (!audio.paused) {
            audio.pause();
            audio.currentTime = 0;
        }
        
        // 等待音频准备好
        if (audio.readyState < 2) { // HAVE_CURRENT_DATA
            await new Promise((resolve, reject) => {
                const onCanPlay = () => {
                    audio.removeEventListener('canplay', onCanPlay);
                    audio.removeEventListener('error', onError);
                    resolve();
                };
                const onError = () => {
                    audio.removeEventListener('canplay', onCanPlay);
                    audio.removeEventListener('error', onError);
                    reject(new Error('音频加载失败'));
                };
                audio.addEventListener('canplay', onCanPlay);
                audio.addEventListener('error', onError);
                
                // 超时处理
                setTimeout(() => {
                    audio.removeEventListener('canplay', onCanPlay);
                    audio.removeEventListener('error', onError);
                    reject(new Error('音频加载超时'));
                }, 5000);
            });
        }
        
        // 尝试播放
        const playPromise = audio.play();
        
        if (playPromise !== undefined) {
            await playPromise;
            return true;
        }
        
        return true;
    } catch (error) {
        // 忽略 AbortError，这是正常的用户交互导致的
        if (error.name === 'AbortError') {
            console.log('[Audio] 播放被中断（正常情况）');
            return false;
        }
        
        // 忽略 NotAllowedError（自动播放策略）
        if (error.name === 'NotAllowedError') {
            console.log('[Audio] 自动播放被阻止，需要用户交互');
            return false;
        }
        
        console.warn('[Audio] 播放失败:', error.message);
        return false;
    }
}

/**
 * 安全暂停音频
 * 
 * @param {HTMLAudioElement} audio - 音频元素
 */
export function safePause(audio) {
    if (!audio) return;
    
    try {
        if (!audio.paused) {
            audio.pause();
        }
    } catch (error) {
        console.warn('[Audio] 暂停失败:', error.message);
    }
}

/**
 * 创建音频元素（带错误处理）
 * 
 * @param {string} src - 音频源 URL
 * @param {Object} options - 配置选项
 * @returns {HTMLAudioElement|null} 音频元素或 null
 */
export function createAudio(src, options = {}) {
    try {
        const audio = new Audio(src);
        
        // 设置属性
        if (options.loop !== undefined) audio.loop = options.loop;
        if (options.volume !== undefined) audio.volume = options.volume;
        if (options.muted !== undefined) audio.muted = options.muted;
        if (options.preload !== undefined) audio.preload = options.preload;
        
        // 预加载音频
        audio.load();
        
        return audio;
    } catch (error) {
        console.error('[Audio] 创建音频元素失败:', error.message);
        return null;
    }
}

/**
 * 播放通知音效（使用 Web Audio API 作为备选）
 * 
 * @param {Object} options - 配置选项
 * @param {number} options.frequency - 频率（Hz）
 * @param {number} options.duration - 持续时间（毫秒）
 * @param {string} options.type - 波形类型
 */
export async function playBeep(options = {}) {
    const { frequency = 800, duration = 200, type = 'sine' } = options;
    
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) {
            console.warn('[Audio] 浏览器不支持 Web Audio API');
            return false;
        }
        
        const audioContext = new AudioContext();
        
        // 处理自动播放策略
        if (audioContext.state === 'suspended') {
            try {
                await audioContext.resume();
            } catch (e) {
                console.log('[Audio] 无法恢复 AudioContext，需要用户交互');
                return false;
            }
        }
        
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = frequency;
        oscillator.type = type;
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration / 1000);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + duration / 1000);
        
        // 清理
        setTimeout(() => {
            try {
                oscillator.disconnect();
                gainNode.disconnect();
                audioContext.close();
            } catch (e) {
                // 忽略清理错误
            }
        }, duration + 100);
        
        return true;
    } catch (error) {
        console.warn('[Audio] 播放提示音失败:', error.message);
        return false;
    }
}

/**
 * 请求音频播放权限
 * 
 * 在用户交互时调用，以获得自动播放权限
 * 
 * @returns {Promise<boolean>} 是否获得权限
 */
export async function requestAudioPermission() {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return false;
        
        const audioContext = new AudioContext();
        
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }
        
        // 立即关闭，只是用来获取权限
        await audioContext.close();
        
        return true;
    } catch (error) {
        console.warn('[Audio] 请求音频权限失败:', error.message);
        return false;
    }
}
