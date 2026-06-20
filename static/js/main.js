/* ==========================================================================
   Learnix Main Layout Controller
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initTheme();
    initNotifications();
    autoDismissToasts();
});

/* 1. Sidebar responsive toggle functions */
function initSidebar() {
    const sidebar = document.getElementById('appSidebar');
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    const closeBtn = document.getElementById('sidebarCloseBtn');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.add('open');
        });
    }
    
    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => {
            sidebar.classList.remove('open');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 1024 && sidebar.classList.contains('open')) {
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        }
    });

    // Highlight active navigation link
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath.includes(href.split('/').pop())) {
            link.classList.add('active');
        }
    });
}

/* 2. Theme switcher (persisted in localStorage) */
function initTheme() {
    const themeToggle = document.getElementById('themeToggleBtn');
    const htmlEl = document.documentElement;
    
    // Read cached preference or default to dark
    const cachedTheme = localStorage.getItem('learnix-theme') || 'dark';
    htmlEl.setAttribute('data-theme', cachedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlEl.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            htmlEl.setAttribute('data-theme', newTheme);
            localStorage.setItem('learnix-theme', newTheme);
            
            // Trigger feedback toast
            showGlobalToast('info', `Switched to ${newTheme} theme mode.`);
        });
    }
}

/* 3. Notifications indicator counter */
function initNotifications() {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;
    
    // We fetch notifications count or inspect list sizes
    // Let's set a mock baseline on dashboard or read it
    const fetchUnreadCount = () => {
        // Safe check if we are on pages that render counters
        const recList = document.querySelectorAll('.rec-item').length;
        // Seed it or check from elements
        const initialVal = parseInt(badge.innerText) || 0;
        if (initialVal === 0 && recList > 0) {
            badge.innerText = recList - 1 > 0 ? recList - 1 : 1;
        }
    };
    
    fetchUnreadCount();
}

/* 4. Auto-dismiss flash messages */
function autoDismissToasts() {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            setTimeout(() => toast.remove(), 400);
        }, 4500);
    });
}

/* 5. Expose Global dynamic toast widget generator */
function showGlobalToast(category, message) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${category}`;
    toast.role = 'alert';
    
    // Icon mapping
    let iconClass = 'fa-info-circle';
    if (category === 'success') iconClass = 'fa-check-circle';
    else if (category === 'danger') iconClass = 'fa-exclamation-circle';
    else if (category === 'warning') iconClass = 'fa-exclamation-triangle';
    
    toast.innerHTML = `
        <div class="toast-icon"><i class="fas ${iconClass}"></i></div>
        <div class="toast-content">${message}</div>
        <button class="toast-close-btn" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.appendChild(toast);
    
    // Auto destroy
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 400);
    }, 4500);
}

