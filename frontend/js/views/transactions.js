/**
 * Transaction History View
 * Displays simulated user transaction ledger, state indicators, and AI risk details.
 */
const TransactionsView = {
    async render() {
        return `
            <div class="view-enter">
                <div class="section-header">
                    <div>
                        <h1 class="section-title">Transaction History</h1>
                        <p class="section-subtitle">Simulated UPI payment records with attached AI risk telemetry and lifecycle states.</p>
                    </div>
                    <button class="btn btn-secondary" onclick="TransactionsView.loadTransactions()">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
                        Refresh
                    </button>
                </div>

                <div class="glass-card" style="padding: 0; overflow: hidden;">
                    <div style="overflow-x: auto;">
                        <table class="data-table" id="tx-table">
                            <thead>
                                <tr>
                                    <th>Status</th>
                                    <th>Recipient</th>
                                    <th>Amount</th>
                                    <th>Overall Risk</th>
                                    <th>Personal / Payee</th>
                                    <th>Decision</th>
                                    <th>Date</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="tx-table-body">
                                <tr>
                                    <td colspan="8" style="text-align: center; padding: 40px;">
                                        <div class="spinner" style="margin: 0 auto 12px;"></div>
                                        <div style="color: var(--text-secondary);">Loading transaction ledger...</div>
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
        await this.loadTransactions();
    },

    async loadTransactions() {
        const tbody = document.getElementById('tx-table-body');
        if (!tbody) return;

        try {
            const txs = await window.api.listTransactions();

            if (!txs || txs.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8">
                            <div class="empty-state">
                                <div class="empty-state-icon">💸</div>
                                <div class="empty-state-title">No transactions yet</div>
                                <div class="empty-state-text">Make your first simulated transfer using the Send Money tab.</div>
                                <button class="btn btn-primary" style="margin-top: 16px;" onclick="window.appRouter.navigate('send-money')">
                                    Send Money Now
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = txs.map(tx => {
                const date = new Date(tx.created_at).toLocaleString('en-IN', {
                    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                });

                const riskLevel = tx.risk_level || 'LOW';
                const overallRisk = tx.overall_risk_score !== null && tx.overall_risk_score !== undefined ? tx.overall_risk_score : 10;
                const personalRisk = tx.personal_risk_score !== null && tx.personal_risk_score !== undefined ? Math.round(tx.personal_risk_score) : '-';
                const payeeRisk = tx.payee_risk_score !== null && tx.payee_risk_score !== undefined ? Math.round(tx.payee_risk_score) : '-';

                return `
                    <tr>
                        <td>
                            <span class="status-badge status-${tx.status.toLowerCase()}">
                                <span class="status-dot"></span>
                                ${tx.status}
                            </span>
                        </td>
                        <td>
                            <div style="font-weight: 600;">${tx.recipient_name || 'Recipient'}</div>
                            <div class="td-vpa">${tx.recipient_vpa}</div>
                        </td>
                        <td class="td-amount">₹${tx.amount.toLocaleString('en-IN')}</td>
                        <td>
                            <span class="risk-badge risk-badge-${riskLevel.toLowerCase()}">
                                ${overallRisk} / 100 (${riskLevel})
                            </span>
                        </td>
                        <td style="font-family: var(--font-mono); font-size: 0.8rem;">
                            <span style="color: var(--primary-400);">${personalRisk}</span> / 
                            <span style="color: var(--accent-400);">${payeeRisk}</span>
                        </td>
                        <td>
                            <span style="font-weight: 600; font-size: 0.8rem; color: ${tx.decision === 'HOLD' ? 'var(--danger-400)' : (tx.decision === 'WARN' ? 'var(--warning-400)' : 'var(--success-400)')}">
                                ${tx.decision || 'ALLOW'}
                            </span>
                        </td>
                        <td class="td-date">${date}</td>
                        <td>
                            ${tx.status === 'CONFIRMATION_REQUIRED' ? `
                                <button class="btn btn-primary" style="padding: 4px 10px; font-size: 0.75rem;" onclick="TransactionsView.confirmTx('${tx.id}')">
                                    Confirm
                                </button>
                            ` : (tx.status === 'HELD' ? `
                                <button class="btn btn-ghost" style="padding: 4px 8px; font-size: 0.75rem; color: var(--warning-400);" onclick="window.appRouter.navigate('escrow')">
                                    View Escrow
                                </button>
                            ` : `
                                <button class="btn btn-ghost" style="padding: 4px 8px; font-size: 0.75rem;" onclick="TransactionsView.showDetails('${tx.id}')">
                                    Details
                                </button>
                            `)}
                        </td>
                    </tr>
                `;
            }).join('');

        } catch (err) {
            console.error('Failed to load transactions:', err);
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; color: var(--danger-400); padding: 20px;">
                        Error loading transactions: ${err.message}
                    </td>
                </tr>
            `;
        }
    },

    async confirmTx(id) {
        try {
            await window.api.confirmTransaction(id, true);
            window.showToast('Transaction confirmed successfully!', 'success');
            await this.loadTransactions();
            window.appRouter.updateBalance();
        } catch (err) {
            window.showToast(err.message || 'Confirmation failed', 'error');
        }
    },

    async showDetails(id) {
        try {
            const tx = await window.api.getTransaction(id);
            const content = `
                <div class="modal-header">
                    <h3 class="modal-title">Transaction Details</h3>
                    <button class="modal-close" onclick="window.closeModal()">✕</button>
                </div>
                <div style="display: flex; flex-direction: column; gap: 12px; font-size: 0.85rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-secondary);">Transaction ID</span>
                        <code style="font-size: 0.75rem; color: var(--primary-300);">${tx.id}</code>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-secondary);">Recipient VPA</span>
                        <span style="font-family: var(--font-mono); color: var(--accent-400);">${tx.recipient_vpa}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-secondary);">Amount</span>
                        <span style="font-family: var(--font-mono); font-weight: 700;">₹${tx.amount.toLocaleString('en-IN')}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-secondary);">Status</span>
                        <span class="status-badge status-${tx.status.toLowerCase()}">${tx.status}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-secondary);">Personal Risk Score</span>
                        <span style="font-family: var(--font-mono);">${tx.personal_risk_score ?? 'N/A'}/100</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-secondary);">Payee Scam Risk Score</span>
                        <span style="font-family: var(--font-mono);">${tx.payee_risk_score ?? 'N/A'}/100</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-secondary);">Overall Combined Score</span>
                        <span style="font-family: var(--font-mono); font-weight: 700;">${tx.overall_risk_score ?? 'N/A'}/100</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-secondary);">Policy Decision</span>
                        <span style="font-weight: 600;">${tx.decision ?? 'ALLOW'}</span>
                    </div>
                    ${tx.notes ? `
                        <div style="border-top: 1px solid var(--border-subtle); padding-top: 8px;">
                            <span style="color: var(--text-secondary); display: block; margin-bottom: 4px;">Notes</span>
                            <div>${tx.notes}</div>
                        </div>
                    ` : ''}
                </div>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="window.closeModal()">Close</button>
                </div>
            `;
            window.showModal(content);
        } catch (err) {
            window.showToast('Could not load details', 'error');
        }
    }
};

window.TransactionsView = TransactionsView;
