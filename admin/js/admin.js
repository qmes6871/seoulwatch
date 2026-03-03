/**
 * Seoul Watch Admin - JavaScript Utilities
 */

// ============================================================================
// Authentication
// ============================================================================

function getToken() {
    return localStorage.getItem('adminToken');
}

function checkAuth() {
    const token = getToken();
    const expiry = localStorage.getItem('adminTokenExpiry');

    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    // Check if token is expired
    if (expiry && Date.now() > parseInt(expiry)) {
        logout();
        return;
    }

    // Verify token with server
    verifyToken(token);
}

async function verifyToken(token) {
    try {
        const response = await fetch('/seoulwatch/api/auth/verify', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            logout();
        }
    } catch (error) {
        console.error('Token verification failed:', error);
        // Don't logout on network errors, let the user continue
    }
}

function logout() {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminTokenExpiry');
    window.location.href = 'login.html';
}


// ============================================================================
// API Request Helper
// ============================================================================

async function apiRequest(url, options = {}) {
    const token = getToken();

    const headers = {
        'Authorization': `Bearer ${token}`,
    };

    // Don't set Content-Type for FormData (browser sets it with boundary)
    if (!options.isFormData) {
        headers['Content-Type'] = 'application/json';
    }

    const config = {
        ...options,
        headers: {
            ...headers,
            ...options.headers
        }
    };

    // Remove isFormData flag from config
    delete config.isFormData;

    const response = await fetch(url, config);

    // Handle 401 Unauthorized
    if (response.status === 401) {
        logout();
        throw new Error('Session expired');
    }

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || 'Request failed');
    }

    return data;
}


// ============================================================================
// Toast Notifications
// ============================================================================

function showToast(message, type = 'info') {
    // Create container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Create toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toast-icon">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>`,
        error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toast-icon">
            <path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>`,
        warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toast-icon">
            <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>`,
        info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toast-icon">
            <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>`
    };

    toast.innerHTML = `
        ${icons[type] || icons.info}
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}


// ============================================================================
// Utility Functions
// ============================================================================

function formatPrice(price) {
    return '₩' + price.toLocaleString('ko-KR');
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

function truncate(str, length = 50) {
    if (!str) return '';
    if (str.length <= length) return str;
    return str.substring(0, length) + '...';
}


// ============================================================================
// Mobile Menu Toggle
// ============================================================================

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar && sidebar.classList.contains('open')) {
        if (!sidebar.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    }
});


// ============================================================================
// Form Validation
// ============================================================================

function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });

    return isValid;
}


// ============================================================================
// Drag and Drop Helpers
// ============================================================================

function initSortable(containerId, onSort) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let draggedItem = null;

    container.addEventListener('dragstart', (e) => {
        draggedItem = e.target.closest('[draggable="true"]');
        if (draggedItem) {
            draggedItem.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }
    });

    container.addEventListener('dragend', (e) => {
        if (draggedItem) {
            draggedItem.classList.remove('dragging');
            draggedItem = null;
            if (onSort) onSort();
        }
    });

    container.addEventListener('dragover', (e) => {
        e.preventDefault();
        const afterElement = getDragAfterElement(container, e.clientY);
        if (draggedItem) {
            if (afterElement == null) {
                container.appendChild(draggedItem);
            } else {
                container.insertBefore(draggedItem, afterElement);
            }
        }
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('[draggable="true"]:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}


// ============================================================================
// Confirmation Dialog
// ============================================================================

function confirm(message) {
    return window.confirm(message);
}


// ============================================================================
// Keyboard Shortcuts
// ============================================================================

document.addEventListener('keydown', (e) => {
    // Escape key closes modals
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal.active');
        if (activeModal) {
            activeModal.classList.remove('active');
        }
    }

    // Ctrl/Cmd + S to save (if save function exists)
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (typeof saveProduct === 'function') {
            saveProduct();
        }
    }
});


// ============================================================================
// Export Functions (for module usage if needed)
// ============================================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        checkAuth,
        logout,
        apiRequest,
        showToast,
        formatPrice,
        debounce,
        formatDate,
        truncate
    };
}
