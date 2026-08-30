/**
 * Fraud Reports & Dispute View
 * Allows users to report suspicious VPAs and see live fraud reports affecting payee reputation.
 */
const ReportsView = {
    async render() {
        return `
            <div class="view-enter">
                <div class="section-header">
                    <div>
                        <h1 class="section-title">Community Fraud Intelligence & Reports</h1>
                        <p class="section-subtitle">File fraud/scam disputes against recipients to train ML reputation decay in real time.</p>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start;">
                    <!-- Left: File Report Form -->
                    <div class="glass-card report-form-card">
                        <h2 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--danger-400)" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                            File a Dispute / Scam Report
                        </h2>

                        <form id="form-report" onsubmit="ReportsView.handleSubmit(event)">
                            <div class="form-group">
                                <label class="form-label" for="rep-vpa">Target Recipient UPI ID / VPA</label>
                                <input
                                    type="text"
                                    id="rep-vpa"
                                    class="form-input"
                                    placeholder="e.g. suspicious_lottery@upi"
                                    value="suspicious_lottery@upi"
                                    required
                                >
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="rep-category">Dispute Category</label>
                                <select id="rep-category" class="form-select" required>
                                    <option value="SUSPECTED_FRAUD">🚨 Suspected Fraud / Impersonation Scam</option>
                                    <option value="DELIVERY_DELAY">📦 Goods Never Delivered</option>
                                    <option value="SERVICE_DISPUTE">🔧 Service Not Rendered</option>
                                    <option value="REFUND_DISPUTE">↩️ Merchant Refusing Refund</option>
                                    <option value="OTHER">ℹ️ Other Suspicious Activity</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="rep-desc">Description of Incident</label>
                                <textarea
                                    id="rep-desc"
                                    class="form-textarea"
                                    placeholder="Provide detailed context regarding the fraud, false promises, or non-delivery..."
                                    required
                                >User claimed to represent lottery contest prize clearance and demanded immediate UPI transfer.</textarea>
                            </div>

                            <button type="submit" class="btn btn-danger btn-full btn-lg" id="btn-submit-report" style="margin-top: 8px;">
                                Submit Fraud Report
                            </button>
                        </form>
                    </div>

                    <!-- Right: Payee Reputation Lookup Tool -->
                    <div class="glass-card">
                        <h2 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-400)" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                            Live Payee Reputation Inspector
                        </h2>
                        <div style="display: flex; gap: 8px; margin-bottom: 16px;">
                            <input
                                type="text"
                                id="inspector-vpa"
                                class="form-input"
                                placeholder="Enter VPA to inspect"
                                value="suspicious_lottery@upi"
                                style="flex: 1;"
                            >
                            <button class="btn btn-secondary" onclick="ReportsView.inspectPayee()">
                                Inspect
                            </button>
                        </div>

                        <!-- Inspection Result -->
                        <div id="inspector-result" style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 16px; min-height: 180px;">
                            <div style="text-align: center; color: var(--text-secondary); padding: 20px 0;">
                                Click Inspect to query dynamic ML reputation and graph risk for this VPA.
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Fraud Reports Table -->
                <div class="glass-card" style="margin-top: 24px; padding: 0; overflow: hidden;">
                    <div style="padding: 16px 20px; border-bottom: 1px solid var(--border-subtle); font-weight: 700;">
                        Platform Fraud & Dispute Records
                    </div>
                    <div style="overflow-x: auto;">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Status</th>
                                    <th>Reported Payee</th>
                                    <th>Category</th>
                                    <th>Description</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody id="reports-table-body">
                                <tr>
                                    <td colspan="5" style="text-align: center; padding: 30px;">
                                        <div class="spinner" style="margin: 0 auto 8px;"></div>
                                        <div style="color: var(--text-secondary);">Loading reports...</div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    },

    async afterRender() {
        await this.loadReports();
        await this.inspectPayee();
    },

    async loadReports() {
        const tbody = document.getElementById('reports-table-body');
        if (!tbody) return;

        try {
            const reports = await window.api.listFraudReports();
            if (!reports || reports.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; color: var(--text-tertiary); padding: 30px;">
                            No community fraud reports filed yet.
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = reports.map(r => {
                const date = new Date(r.created_at).toLocaleDateString('en-IN', {
                    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                });
                return `
                    <tr>
                        <td>
                            <span class="status-badge status-${r.status === 'VERIFIED' ? 'critical' : 'warning'}">
                                ${r.status}
                            </span>
                        </td>
                        <td class="td-vpa">${r.payee_vpa}</td>
                        <td style="font-size: 0.8rem; font-weight: 600;">${r.category.replace('_', ' ')}</td>
                        <td style="font-size: 0.8rem; color: var(--text-secondary); max-width: 320px;">${r.description}</td>
                        <td class="td-date">${date}</td>
                    </tr>
                `;
            }).join('');

        } catch (err) {
            console.error('Failed to load reports:', err);
        }
    },

    async handleSubmit(e) {
        e.preventDefault();
        const vpa = document.getElementById('rep-vpa').value.trim();
        const category = document.getElementById('rep-category').value;
        const description = document.getElementById('rep-desc').value.trim();
        const btn = document.getElementById('btn-submit-report');

        btn.disabled = true;
        btn.innerHTML = '<div class="spinner"></div> Submitting Report...';

        try {
            await window.api.submitFraudReport({
                payee_vpa: vpa,
                category,
                description
            });

            window.showToast(`Report filed against ${vpa}. Payee reputation adjusted!`, 'success');
            await this.loadReports();
            await this.inspectPayee();
        } catch (err) {
            window.showToast(err.message || 'Submission failed', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Submit Fraud Report';
        }
    },

    async inspectPayee() {
        const vpa = document.getElementById('inspector-vpa')?.value.trim() || 'suspicious_lottery@upi';
        const resultContainer = document.getElementById('inspector-result');
        if (!resultContainer) return;

        resultContainer.innerHTML = '<div class="spinner" style="margin: 30px auto;"></div>';

        try {
            const rep = await window.api.getPayeeReputation(vpa);
            const risk = await window.api.getPayeeRisk(vpa);

            resultContainer.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <div style="font-weight: 700; font-size: 1rem;">${rep.payee_name || vpa}</div>
                        <div class="td-vpa">${rep.payee_vpa}</div>
                    </div>
                    <span class="risk-badge risk-badge-${rep.risk_level.toLowerCase()}">
                        ${rep.risk_score} / 100 (${rep.risk_level})
                    </span>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.8rem; margin: 12px 0;">
                    <div style="background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: var(--radius-sm);">
                        <span style="color: var(--text-tertiary);">Reputation Score:</span>
                        <div style="font-size: 1.1rem; font-weight: 700; font-family: var(--font-mono); color: ${rep.reputation_score > 60 ? 'var(--success-400)' : 'var(--danger-400)'};">
                            ${rep.reputation_score.toFixed(1)} / 100
                        </div>
                    </div>
                    <div style="background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: var(--radius-sm);">
                        <span style="color: var(--text-tertiary);">Fraud Reports Filed:</span>
                        <div style="font-size: 1.1rem; font-weight: 700; font-family: var(--font-mono); color: ${rep.reported_count > 0 ? 'var(--danger-400)' : 'var(--text-primary)'};">
                            ${rep.reported_count}
                        </div>
                    </div>
                </div>

                <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-tertiary); margin-bottom: 6px;">
                    Model Signals & Evidence:
                </div>
                <div style="display: flex; flex-direction: column; gap: 4px; font-size: 0.8rem;">
                    ${risk.reasons.map(r => `
                        <div style="color: var(--text-secondary);">• ${r}</div>
                    `).join('')}
                </div>
            `;
        } catch (err) {
            resultContainer.innerHTML = `
                <div style="text-align: center; color: var(--text-tertiary); padding: 20px 0;">
                    No previous reputation history for <code>${vpa}</code> (Default risk applied).
                </div>
            `;
        }
    }
};

window.ReportsView = ReportsView;
