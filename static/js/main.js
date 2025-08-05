/**
 * 主要JavaScript文件
 * 包含全局共用函数和事件处理
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 导航栏活动项目高亮
    highlightActiveNavItem();
    
    // 初始化表单验证
    initFormValidation();
    
    // 初始化工具提示
    initTooltips();
});

/**
 * 高亮显示当前活动的导航项目
 */
function highlightActiveNavItem() {
    const currentPath = window.location.pathname;
    
    // 获取所有导航链接
    const navLinks = document.querySelectorAll('header a');
    
    // 遍历链接并检查是否与当前路径匹配
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
            // 如果有样式类，可以添加额外的高亮样式
            if (link.classList.contains('nav-link')) {
                link.classList.add('text-white');
                link.classList.add('fw-bold');
            }
        }
    });
}

/**
 * 初始化表单验证
 */
function initFormValidation() {
    // 获取所有需要验证的表单
    const forms = document.querySelectorAll('.needs-validation');
    
    // 遍历表单并添加提交事件监听器
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * 初始化Bootstrap工具提示
 */
function initTooltips() {
    // 检查是否存在Bootstrap的tooltip函数
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Tooltip !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * 显示加载指示器
 * @param {string} elementId - 要在其中显示加载指示器的元素ID
 * @param {string} message - 可选的加载消息
 */
function showLoader(elementId, message = '加载中...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center py-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">${message}</p>
            </div>
        `;
    }
}

/**
 * 显示错误消息
 * @param {string} elementId - 要在其中显示错误的元素ID
 * @param {string} message - 错误消息
 */
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-circle me-2"></i> ${message}
            </div>
        `;
    }
}

/**
 * 格式化日期
 * @param {Date|string} date - 日期对象或日期字符串
 * @param {string} format - 格式化选项 (short, long, time)
 * @return {string} 格式化后的日期字符串
 */
function formatDate(date, format = 'short') {
    if (!date) return '';
    
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    switch (format) {
        case 'short':
            return dateObj.toLocaleDateString('zh-CN');
        case 'long':
            return dateObj.toLocaleDateString('zh-CN', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        case 'time':
            return dateObj.toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        case 'datetime':
            return dateObj.toLocaleString('zh-CN');
        default:
            return dateObj.toLocaleDateString('zh-CN');
    }
}

/**
 * 格式化数字
 * @param {number} number - 要格式化的数字
 * @param {number} decimals - 小数位数
 * @return {string} 格式化后的数字字符串
 */
function formatNumber(number, decimals = 0) {
    if (number === null || number === undefined) return '';
    
    return number.toLocaleString('zh-CN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * 获取URL参数
 * @param {string} name - 参数名
 * @return {string|null} 参数值
 */
function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * 发送API请求
 * @param {string} url - API端点
 * @param {Object} options - fetch选项
 * @return {Promise} Promise对象
 */
async function apiRequest(url, options = {}) {
    try {
        // 设置默认选项
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const requestOptions = { ...defaultOptions, ...options };
        
        // 发送请求
        const response = await fetch(url, requestOptions);
        
        // 检查响应状态
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `请求失败: ${response.status}`);
        }
        
        // 返回响应数据
        return await response.json();
    } catch (error) {
        console.error('API请求出错:', error);
        throw error;
    }
}