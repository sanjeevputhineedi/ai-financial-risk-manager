/**
 * Escrow & Fund Manager View
 * Tracks payments held in the cooling period, with countdown timers,
 * manual release/refund controls (admin demo), and dynamic re-evaluation trigger.
 */
const EscrowView = {
    async render() {
        return `
            <div class="view-enter">
                <div class="section-header">
                    <div>
                        <h1 class="section-title">Escrow & Cooling Period Tracker</h1>
                        <p class="section-subtitle">Fund Manager holds high-risk payments in an automated cooling pool for dynamic AI re-evaluation.</p>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="btn btn-primary" onclick="EscrowView.triggerReevaluation()">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                            Trigger Dynamic Re-evaluation
                        </button>
                        <button class="btn btn-secondary" onclick="EscrowView.loadHeldPayments()">
                            Refresh
                        </button>
                    </div>
                </div>

                <!-- Explanation Banner -->
                <div class="glass-card" style="margin-bottom: 20px; background: rgba(99,102,241,0.06); border-color: var(--border-accent);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <div style="font-size: 1.4rem;">🔒</div>
                        <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5;">
                            <strong style="color: var(--text-primary);">How Escrow Cooling Works:</strong> High-risk or anomalous transfers (Risk ≥ 70) are placed in the Fund Manager cooling pool for 30 minutes. If subsequent evidence emerges (e.g. fraud complaints filed), the funds can be automatically refunded to the sender, protecting them from irreversible scam loss. If the payee proves legitimate, funds are auto-released.
                        </div>
                    </div>
                </div>

                <!-- Held Payments List -->
                <div class="glass-card" style="padding: 0; overflow: hidden;">
                    <div style="overflow-x: auto;">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Status</th>
                                    <th>Held Amount</th>
                                    <th>Hold Expiry</th>
                                    <th>Cooldown Remaining</th>
                                    <th>Resolution Details</th>
                                    <th>Actions (Admin / Safe Demo)</th>
                                </tr>
                            </thead>
                            <tbody id="held-table-body">
                                <tr>
                                    <td colspan="6" style="text-align: center; padding: 40px;">
                                        <div class="spinner" style="margin: 0 auto 12px;"></div>
                                        <div style="color: var(--text-secondary);">Loading escrow pool status...</div>
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
        await this.loadHeldPayments();
    },

    async loadHeldPayments() {
        const tbody = document.getElementById('held-table-body');
        if (!tbody) return;

        try {
            const heldList = await window.api.listHeldPayments();

            if (!heldList || heldList.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6">
                            <div class="empty-state">
                                <div class="empty-state-icon">🛡️</div>
                                <div class="empty-state-title">No payments currently in Escrow</div>
                                <div class="empty-state-text">To test escrow protection, send a high-risk transfer (e.g. ₹8,500 to a reported scam VPA) from the Send Money tab.</div>
                                <button class="btn btn-primary" style="margin-top: 16px;" onclick="window.appRouter.navigate('send-money')">
                                    Test High-Risk Transfer
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = heldList.map(item => {
                const expiresAt = new Date(item.hold_expires_at);
                const now = new Date();
                const diffMs = expiresAt - now;
                const isExpired = diffMs <= 0;
                const minsLeft = Math.max(0, Math.floor(diffMs / 60000));
                const secsLeft = Math.max(0, Math.floor((diffMs % 60000) / 1000));

                const isHeld = item.status === 'HELD';
                const statusBadge = `
                    <span class="status-badge status-${item.status.toLowerCase()}">
                        <span class="status-dot"></span>
                        ${item.status}
                    </span>
                `;

                return `
                    <tr>
                        <td>${statusBadge}</td>
                        <td class="td-amount">₹${item.held_amount.toLocaleString('en-IN')}</td>
                        <td class="td-date">${expiresAt.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</td>
                        <td>
                            ${isHeld ? `
                                <div class="escrow-timer">
                                    ⏱️ ${isExpired ? 'Cooling Complete' : `${minsLeft}m ${secsLeft}s`}
                                </div>
                            ` : `
                                <span style="color: var(--text-tertiary); font-size: 0.8rem;">Resolved</span>
                            `}
                        </td>
                        <td style="font-size: 0.8rem; color: var(--text-secondary); max-width: 260px;">
                            ${item.release_reason ? `<span style="color: var(--accent-400);">Released:</span> ${item.release_reason}` : ''}
                            ${item.refund_reason ? `<span style="color: var(--danger-400);">Refunded:</span> ${item.refund_reason}` : ''}
                            ${!item.release_reason && !item.refund_reason ? 'In cooling period evaluation.' : ''}
                        </td>
                        <td>
                            ${isHeld ? `
                                <div style="display: flex; gap: 6px;">
                                    <button class="btn btn-success" style="padding: 4px 10px; font-size: 0.75rem;" onclick="EscrowView.releaseFunds('${item.id}')">
                                        Release
                                    </button>
                                    <button class="btn btn-danger" style="padding: 4px 10px; font-size: 0.75rem;" onclick="EscrowView.refundFunds('${item.id}')">
                                        Refund
                                    </button>
                                </div>
                            ` : `
                                <span style="font-size: 0.75rem; color: var(--text-tertiary);">Completed</span>
                            `}
                        </td>
                    </tr>
                `;
            }).join('');

        } catch (err) {
            console.error('Failed to load held payments:', err);
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; color: var(--danger-400); padding: 20px;">
                        Error loading escrow data: ${err.message}
                    </td>
                </tr>
            `;
        }
    },

    async releaseFunds(id) {
        try {
            await window.api.releaseHeldPayment(id, 'Admin manual clearance after merchant verification.');
            window.showToast('Funds successfully released to recipient!', 'success');
            await this.loadHeldPayments();
            window.appRouter.updateBalance();
        } catch (err) {
            window.showToast(err.message || 'Release failed', 'error');
        }
    },

    async refundFunds(id) {
        try {
            await window.api.refundHeldPayment(id, 'Admin manual refund: scam risk confirmed.');
            window.showToast('Funds refunded back to sender account!', 'info');
            await this.loadHeldPayments();
            window.appRouter.updateBalance();
        } catch (err) {
            window.showToast(err.message || 'Refund failed', 'error');
        }
    },

    async triggerReevaluation() {
        try {
            window.showToast('Running dynamic cooling re-evaluation across active held transfers...', 'info');
            const res = await window.api.triggerCoolingReevaluation();
            window.showToast(`Re-evaluation finished: ${res.length} payments re-assessed.`, 'success');
            await this.loadHeldPayments();
            window.appRouter.updateBalance();
        } catch (err) {
            window.showToast(err.message || 'Re-evaluation failed', 'error');
        }
    }
};

window.EscrowView = EscrowView;
