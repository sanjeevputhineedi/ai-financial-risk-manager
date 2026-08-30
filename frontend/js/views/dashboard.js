/**
 * Dashboard View
 * Displays platform risk metrics, distribution charts, escrow pool, and quick actions.
 */
const DashboardView = {
    async render() {
        return `
            <div class="view-enter">
                <div class="section-header">
                    <div>
                        <h1 class="section-title">Risk & Intelligence Dashboard</h1>
                        <p class="section-subtitle">Real-time payment monitoring, multi-layer ML risk telemetry, and escrow pool state.</p>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="btn btn-secondary" onclick="DashboardView.loadData()">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
                            Refresh
                        </button>
                        <button class="btn btn-primary" onclick="window.appRouter.navigate('send-money')">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                            New Transfer
                        </button>
                    </div>
                </div>

                <!-- Live Metrics Grid -->
                <div class="metrics-grid">
                    <div class="glass-card metric-card">
                        <div class="metric-icon primary">⚡</div>
                        <div class="metric-value" id="dash-total-tx">-</div>
                        <div class="metric-label">Total Transactions</div>
                    </div>
                    <div class="glass-card metric-card">
                        <div class="metric-icon warning">🛡️</div>
                        <div class="metric-value" id="dash-held-count">-</div>
                        <div class="metric-label">In Escrow Cooling</div>
                    </div>
                    <div class="glass-card metric-card">
                        <div class="metric-icon success">💰</div>
                        <div class="metric-value" id="dash-escrow-balance">-</div>
                        <div class="metric-label">Escrow Pool Volume</div>
                    </div>
                    <div class="glass-card metric-card">
                        <div class="metric-icon accent">🧠</div>
                        <div class="metric-value" id="dash-fl-rounds">-</div>
                        <div class="metric-label">Federated FL Rounds</div>
                    </div>
                </div>

                <!-- Charts & Distributions -->
                <div class="charts-grid">
                    <div class="glass-card chart-container">
                        <h2 class="chart-title">Risk Level Distribution</h2>
                        <div class="chart-canvas-wrapper" style="height: 200px;">
                            <canvas id="chart-risk-donut"></canvas>
                        </div>
                        <div id="risk-legend" style="display: flex; justify-content: space-around; margin-top: 12px; font-size: 0.75rem; color: var(--text-secondary);">
                            <span style="color: var(--success-400);">● Low</span>
                            <span style="color: var(--warning-400);">● Medium</span>
                            <span style="color: var(--danger-400);">● High</span>
                            <span style="color: var(--critical-400);">● Critical</span>
                        </div>
                    </div>

                    <div class="glass-card chart-container">
                        <h2 class="chart-title">Transaction Risk Distribution</h2>
                        <div class="chart-canvas-wrapper" style="height: 200px;">
                            <canvas id="chart-risk-bars"></canvas>
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-tertiary); text-align: center; margin-top: 8px;">
                            Breakdown across 4 AI severity thresholds
                        </div>
                    </div>
                </div>

                <!-- Intelligence & Mitigations Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
                    <div class="glass-card">
                        <h2 style="font-size: 1rem; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-400)" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
                            AI Risk Telemetry
                        </h2>
                        <div style="display: flex; flex-direction: column; gap: 12px; font-size: 0.85rem;">
                            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px;">
                                <span style="color: var(--text-secondary);">Avg. Personal Behavioral Risk</span>
                                <span id="dash-avg-personal" style="font-family: var(--font-mono); font-weight: 600;">-</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px;">
                                <span style="color: var(--text-secondary);">Avg. Payee Reputation Risk</span>
                                <span id="dash-avg-payee" style="font-family: var(--font-mono); font-weight: 600;">-</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px;">
                                <span style="color: var(--text-secondary);">Suspicious Payees Tracked</span>
                                <span id="dash-suspicious-count" style="font-family: var(--font-mono); font-weight: 600; color: var(--danger-400);">-</span>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: var(--text-secondary);">False Positives Mitigated</span>
                                <span id="dash-mitigated-count" style="font-family: var(--font-mono); font-weight: 600; color: var(--success-400);">-</span>
                            </div>
                        </div>
                    </div>

                    <div class="glass-card">
                        <h2 style="font-size: 1rem; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary-400)" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                            Escrow Cooling Status
                        </h2>
                        <div style="display: flex; flex-direction: column; gap: 12px; font-size: 0.85rem;">
                            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px;">
                                <span style="color: var(--text-secondary);">Total Held Volume</span>
                                <span id="dash-held-volume" style="font-family: var(--font-mono); font-weight: 600; color: var(--warning-400);">-</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px;">
                                <span style="color: var(--text-secondary);">Total Refunded Volume</span>
                                <span id="dash-refunded-volume" style="font-family: var(--font-mono); font-weight: 600; color: var(--primary-400);">-</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px;">
                                <span style="color: var(--text-secondary);">Community Fraud Reports</span>
                                <span id="dash-fraud-reports" style="font-family: var(--font-mono); font-weight: 600; color: var(--danger-400);">-</span>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: var(--text-secondary);">Active FL Nodes</span>
                                <span id="dash-fl-clients" style="font-family: var(--font-mono); font-weight: 600; color: var(--accent-400);">-</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    async afterRender() {
        await this.loadData();
    },

    async loadData() {
        try {
            const metrics = await window.api.getDashboardMetrics();
            
            // Populate metric cards
            document.getElementById('dash-total-tx').textContent = metrics.total_transactions;
            document.getElementById('dash-held-count').textContent = metrics.held_summary.currently_held;
            document.getElementById('dash-escrow-balance').textContent = `₹${metrics.escrow_pool_balance.toLocaleString('en-IN')}`;
            document.getElementById('dash-fl-rounds').textContent = metrics.federated_rounds_completed;

            // Populate telemetry
            document.getElementById('dash-avg-personal').textContent = `${metrics.average_personal_risk}/100`;
            document.getElementById('dash-avg-payee').textContent = `${metrics.average_payee_risk}/100`;
            document.getElementById('dash-suspicious-count').textContent = metrics.suspicious_recipients_count;
            document.getElementById('dash-mitigated-count').textContent = metrics.false_positives_mitigated;

            // Populate escrow status
            document.getElementById('dash-held-volume').textContent = `₹${metrics.held_summary.total_held_volume.toLocaleString('en-IN')}`;
            document.getElementById('dash-refunded-volume').textContent = `₹${metrics.held_summary.total_refunded_volume.toLocaleString('en-IN')}`;
            document.getElementById('dash-fraud-reports').textContent = metrics.fraud_reports_count;
            document.getElementById('dash-fl-clients').textContent = `${metrics.active_federated_clients} online`;

            // Render Donut Chart
            const dist = metrics.risk_distribution;
            const chartData = [
                { label: 'Low', value: dist.low, color: '#10b981' },
                { label: 'Medium', value: dist.medium, color: '#f59e0b' },
                { label: 'High', value: dist.high, color: '#ef4444' },
                { label: 'Critical', value: dist.critical, color: '#ec4899' }
            ];
            window.MiniChart.renderDonut(document.getElementById('chart-risk-donut'), chartData);
            window.MiniChart.renderBars(document.getElementById('chart-risk-bars'), chartData);

        } catch (err) {
            console.error('Failed to load dashboard metrics:', err);
            window.showToast('Could not load live metrics', 'error');
        }
    }
};

window.DashboardView = DashboardView;
