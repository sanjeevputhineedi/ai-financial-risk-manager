/**
 * Login & Registration View
 */
const LoginView = {
    render() {
        return `
            <div class="auth-container">
                <div class="glass-card auth-card">
                    <div class="auth-header">
                        <div class="auth-logo">
                            <div class="auth-logo-icon">
                                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                                </svg>
                            </div>
                        </div>
                        <h1 class="auth-title">RiskShield<span class="brand-ai">AI</span></h1>
                        <p class="auth-subtitle">AI Financial Risk Manager for UPI Payments</p>
                    </div>

                    <div class="auth-tabs">
                        <button class="auth-tab active" id="tab-login" onclick="LoginView.switchTab('login')">Sign In</button>
                        <button class="auth-tab" id="tab-register" onclick="LoginView.switchTab('register')">Create Account</button>
                    </div>

                    <!-- Login Form -->
                    <form id="form-login" onsubmit="LoginView.handleLogin(event)">
                        <div class="form-group">
                            <label class="form-label" for="login-email">Email Address</label>
                            <input type="email" id="login-email" class="form-input" placeholder="alice@example.com" value="alice@example.com" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="login-password">Password</label>
                            <input type="password" id="login-password" class="form-input" placeholder="••••••••" value="password123" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-full btn-lg" id="btn-login-submit" style="margin-top: 12px;">
                            Sign In to Account
                        </button>
                    </form>

                    <!-- Register Form (Hidden by default) -->
                    <form id="form-register" class="hidden" onsubmit="LoginView.handleRegister(event)">
                        <div class="form-group">
                            <label class="form-label" for="reg-fullname">Full Name</label>
                            <input type="text" id="reg-fullname" class="form-input" placeholder="e.g. Sanjeev Kumar" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="reg-username">Username</label>
                            <input type="text" id="reg-username" class="form-input" placeholder="sanjeev" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="reg-email">Email</label>
                            <input type="email" id="reg-email" class="form-input" placeholder="sanjeev@example.com" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="reg-password">Password</label>
                            <input type="password" id="reg-password" class="form-input" placeholder="At least 6 characters" minlength="6" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="reg-balance">Opening Balance (₹)</label>
                            <input type="number" id="reg-balance" class="form-input" value="25000" min="1000" step="500">
                        </div>
                        <button type="submit" class="btn btn-primary btn-full btn-lg" id="btn-reg-submit" style="margin-top: 12px;">
                            Register & Get UPI ID
                        </button>
                    </form>

                    <div style="margin-top: 20px; padding: 12px; background: rgba(99,102,241,0.06); border-radius: var(--radius-sm); font-size: 0.75rem; color: var(--text-secondary); text-align: center;">
                        <span style="color: var(--accent-400); font-weight: 600;">Demo Accounts:</span><br>
                        Alice (<code>alice@example.com</code> / <code>password123</code>)<br>
                        Admin (<code>admin@example.com</code> / <code>admin123</code>)
                    </div>
                </div>
            </div>
        `;
    },

    switchTab(tab) {
        const loginTab = document.getElementById('tab-login');
        const regTab = document.getElementById('tab-register');
        const loginForm = document.getElementById('form-login');
        const regForm = document.getElementById('form-register');

        if (tab === 'login') {
            loginTab.classList.add('active');
            regTab.classList.remove('active');
            loginForm.classList.remove('hidden');
            regForm.classList.add('hidden');
        } else {
            regTab.classList.add('active');
            loginTab.classList.remove('active');
            regForm.classList.remove('hidden');
            loginForm.classList.add('hidden');
        }
    },

    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        const btn = document.getElementById('btn-login-submit');

        btn.disabled = true;
        btn.innerHTML = '<div class="spinner"></div> Authenticating...';

        try {
            const data = await window.api.login(email, password);
            window.api.setAuth(data.access_token, data);
            window.showToast('Login successful! Welcome back.', 'success');
            window.appRouter.navigate('dashboard');
        } catch (err) {
            window.showToast(err.message || 'Invalid email or password', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Sign In to Account';
        }
    },

    async handleRegister(e) {
        e.preventDefault();
        const fullName = document.getElementById('reg-fullname').value.trim();
        const username = document.getElementById('reg-username').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const password = document.getElementById('reg-password').value;
        const initialBalance = parseFloat(document.getElementById('reg-balance').value) || 25000;
        const btn = document.getElementById('btn-reg-submit');

        btn.disabled = true;
        btn.innerHTML = '<div class="spinner"></div> Setting up account...';

        try {
            const data = await window.api.register({
                full_name: fullName,
                username,
                email,
                password,
                initial_balance: initialBalance
            });
            window.api.setAuth(data.access_token, data);
            window.showToast('Account created successfully!', 'success');
            window.appRouter.navigate('dashboard');
        } catch (err) {
            window.showToast(err.message || 'Registration failed', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Register & Get UPI ID';
        }
    }
};

window.LoginView = LoginView;
