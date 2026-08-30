/**
 * RiskShield AI — Main Single-Page Application Router & State Manager
 */
class AppRouter {
    constructor() {
        this.routes = {
            'login': window.LoginView,
            'dashboard': window.DashboardView,
            'send-money': window.SendMoneyView,
            'transactions': window.TransactionsView,
            'escrow': window.EscrowView,
            'reports': window.ReportsView
        };
        this.currentView = 'dashboard';
        this.init();
    }

    init() {
        // Setup navigation listeners
        document.querySelectorAll('.nav-link').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = btn.getAttribute('data-view');
                if (view) this.navigate(view);
            });
        });

        // Setup logout button
        const logoutBtn = document.getElementById('nav-logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                window.api.clearAuth();
                window.showToast('Logged out successfully.', 'info');
                this.navigate('login');
            });
        }

        // Handle initial routing
        if (!window.api.isAuthenticated()) {
            this.navigate('login');
        } else {
            this.navigate('dashboard');
        }
    }

    async navigate(viewName) {
        const view = this.routes[viewName];
        if (!view) {
            console.error(`Route ${viewName} not found`);
            return;
        }

        const isAuth = window.api.isAuthenticated();
        const mainNav = document.getElementById('main-nav');

        // Navigation visibility
        if (viewName === 'login' || !isAuth) {
            if (mainNav) mainNav.classList.add('hidden');
        } else {
            if (mainNav) mainNav.classList.remove('hidden');
            this.updateActiveNavLink(viewName);
            this.updateBalance();
        }

        // Render target view
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = await view.render();
            if (view.afterRender) {
                await view.afterRender();
            }
        }

        this.currentView = viewName;
        window.scrollTo(0, 0);
    }

    updateActiveNavLink(viewName) {
        document.querySelectorAll('.nav-link').forEach(btn => {
            if (btn.getAttribute('data-view') === viewName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    async updateBalance() {
        if (!window.api.isAuthenticated()) return;
        try {
            const acc = await window.api.getMyAccount();
            const balEl = document.getElementById('nav-balance-amount');
            if (balEl && acc) {
                balEl.textContent = `₹${acc.balance.toLocaleString('en-IN')}`;
            }
        } catch (err) {
            console.error('Failed to update balance:', err);
        }
    }
}

// ── Global Toast Notification System ──
window.showToast = function(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span style="font-weight: 700; font-size: 1rem;">${icons[type] || '•'}</span>
        <span style="flex: 1;">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
};

// ── Global Modal System ──
window.showModal = function(contentHtml) {
    const overlay = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    if (!overlay || !content) return;

    content.innerHTML = contentHtml;
    overlay.classList.remove('hidden');
};

window.closeModal = function() {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) overlay.classList.add('hidden');
};

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                window.closeModal();
            }
        });
    }

    // Initialize SPA Router
    window.appRouter = new AppRouter();
});
