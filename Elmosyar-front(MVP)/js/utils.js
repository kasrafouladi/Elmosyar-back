// ════════════════════════════════════════════════════════════
// 🔧 تنظیمات اصلی - فقط اینجا URL Backend را تغییر دهید
// ════════════════════════════════════════════════════════════

const CONFIG = {
    // 👇 فقط این خط را تغییر دهید
    API_BASE: 'http://localhost:8000',
    
    // تنظیمات اضافی (در صورت نیاز)
    TIMEOUT: 30000, // 30 ثانیه
    ENABLE_CREDENTIALS: true
};

// ════════════════════════════════════════════════════════════
// 📡 کلاس مدیریت درخواست‌های API
// ════════════════════════════════════════════════════════════

class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    // متد کمکی برای ساخت URL کامل
    buildURL(endpoint) {
        // حذف اسلش اضافی
        const cleanBase = this.baseURL.replace(/\/$/, '');
        const cleanEndpoint = endpoint.replace(/^\//, '');
        return `${cleanBase}/${cleanEndpoint}`;
    }

    // متد عمومی برای درخواست‌های GET
    async get(endpoint, options = {}) {
        return this.request(endpoint, {
            method: 'GET',
            ...options
        });
    }

    // متد عمومی برای درخواست‌های POST
    async post(endpoint, data = null, options = {}) {
        const isFormData = data instanceof FormData;
        
        return this.request(endpoint, {
            method: 'POST',
            headers: isFormData ? {} : {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: isFormData ? data : (data ? JSON.stringify(data) : null),
            ...options
        });
    }

    // متد عمومی برای درخواست‌های PUT
    async put(endpoint, data = null, options = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: data ? JSON.stringify(data) : null,
            ...options
        });
    }

    // متد عمومی برای درخواست‌های DELETE
    async delete(endpoint, options = {}) {
        return this.request(endpoint, {
            method: 'DELETE',
            ...options
        });
    }

    // متد اصلی برای ارسال درخواست
    async request(endpoint, options = {}) {
        const url = this.buildURL(endpoint);
        
        const defaultOptions = {
            credentials: CONFIG.ENABLE_CREDENTIALS ? 'include' : 'same-origin',
            ...options
        };

        try {
            const response = await fetch(url, defaultOptions);
            
            // بررسی Content-Type برای تشخیص JSON
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                return { response, data };
            }
            
            // برای فایل‌ها یا محتوای غیر JSON
            const text = await response.text();
            return { response, data: text };
            
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }
}

// ساخت نمونه از API Client
const api = new APIClient(CONFIG.API_BASE);

// برای سازگاری با کد قبلی
const API_BASE = CONFIG.API_BASE;

// ════════════════════════════════════════════════════════════
// 🛠️ توابع کمکی
// ════════════════════════════════════════════════════════════

function showLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'flex';
    }
}

function hideLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
}

function showMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
        mainContent.insertBefore(messageDiv, mainContent.firstChild);
        
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'همین الان';
    if (minutes < 60) return `${minutes} دقیقه پیش`;
    if (hours < 24) return `${hours} ساعت پیش`;
    if (days < 7) return `${days} روز پیش`;
    
    return date.toLocaleDateString('fa-IR');
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ════════════════════════════════════════════════════════════
// 📤 Export برای استفاده در فایل‌های دیگر
// ════════════════════════════════════════════════════════════

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        CONFIG,
        api,
        API_BASE,
        showLoading,
        hideLoading,
        showMessage,
        formatDate,
        escapeHtml
    };
}