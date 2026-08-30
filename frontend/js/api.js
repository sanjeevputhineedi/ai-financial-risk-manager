/**
 * RiskShield AI - API Client Module
 * Handles JWT token storage, authenticated requests, and endpoint helpers.
 */
class ApiClient {
    constructor() {
        this.baseUrl = window.location.origin + '/api/v1';
        this.tokenKey = 'riskshield_access_token';
        this.userKey = 'riskshield_user';
    }

    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    setAuth(token, user) {
        localStorage.setItem(this.tokenKey, token);
        localStorage.setItem(this.userKey, JSON.stringify(user));
    }

    clearAuth() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
    }

    getUser() {
        try {
            return JSON.parse(localStorage.getItem(this.userKey));
        } catch {
            return null;
        }
    }

    isAuthenticated() {
        return !!this.getToken();
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const res = await fetch(url, {
                ...options,
                headers
            });

            if (res.status === 401) {
                this.clearAuth();
                if (window.appRouter) {
                    window.appRouter.navigate('login');
                }
                throw new Error('Session expired. Please log in again.');
            }

            const data = await res.json();
            if (!res.ok) {
                const message = data.detail || (data.errors ? JSON.stringify(data.errors) : 'Request failed');
                throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
            }
            return data;
        } catch (err) {
            console.error(`API Error [${endpoint}]:`, err);
            throw err;
        }
    }

    // ── Auth Endpoints ──
    async register(data) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    // ── Account & Recipient Endpoints ──
    async getMyAccount() {
        return this.request('/accounts/me');
    }

    async getRecipients() {
        return this.request('/recipients');
    }

    async addRecipient(data) {
        return this.request('/recipients', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // ── Transaction Endpoints ──
    async createTransaction(txData) {
        return this.request('/transactions', {
            method: 'POST',
            body: JSON.stringify(txData)
        });
    }

    async listTransactions() {
        return this.request('/transactions');
    }

    async getTransaction(id) {
        return this.request(`/transactions/${id}`);
    }

    async confirmTransaction(id, confirmed = true, userNotes = '') {
        return this.request(`/transactions/${id}/confirm`, {
            method: 'POST',
            body: JSON.stringify({ confirmed, user_notes: userNotes })
        });
    }

    async cancelTransaction(id, reason = 'User cancelled') {
        return this.request(`/transactions/${id}/cancel`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    // ── Risk ML Analysis (M5 / Checkpoint 08) ──
    async analyzeRisk(senderId, recipientId, amount, context = {}) {
        return this.request('/risk/analyze', {
            method: 'POST',
            body: JSON.stringify({
                sender_id: senderId,
                recipient_id: recipientId,
                amount: parseFloat(amount),
                context
            })
        });
    }

    // ── Escrow & Held Payments ──
    async listHeldPayments() {
        return this.request('/held-payments');
    }

    async releaseHeldPayment(id, reason = 'Administrative clearance') {
        return this.request(`/held-payments/${id}/release`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    async refundHeldPayment(id, reason = 'Administrative refund') {
        return this.request(`/held-payments/${id}/refund`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    async triggerCoolingReevaluation() {
        return this.request('/held-payments/reevaluate', {
            method: 'POST'
        });
    }

    // ── Payees & Fraud Reports ──
    async getPayeeRisk(payeeVpa) {
        return this.request(`/payees/${encodeURIComponent(payeeVpa)}/risk`);
    }

    async getPayeeReputation(payeeVpa) {
        return this.request(`/payees/${encodeURIComponent(payeeVpa)}/reputation`);
    }

    async submitFraudReport(reportData) {
        return this.request('/reports', {
            method: 'POST',
            body: JSON.stringify(reportData)
        });
    }

    async listFraudReports() {
        return this.request('/reports');
    }

    // ── Dashboard Metrics ──
    async getDashboardMetrics() {
        return this.request('/dashboard/metrics');
    }
}

window.api = new ApiClient();
