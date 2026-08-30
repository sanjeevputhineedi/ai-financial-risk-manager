/**
 * Send Money View (Core Interactive Flow)
 * Allows entering amount, recipient VPA/UPI, runs real-time risk assessment,
 * and handles payment creation / warning confirmation / escrow holds.
 */
const SendMoneyView = {
    currentRiskAssessment: null,
    riskDebounceTimer: null,

    async render() {
        return `
            <div class="view-enter">
                <div class="section-header">
                    <div>
                        <h1 class="section-title">Send Money (Simulated UPI)</h1>
                        <p class="section-subtitle">Real-time dual-risk evaluation: Personal spending pattern + Payee scam intelligence.</p>
                    </div>
                </div>

                <div class="send-money-layout">
                    <!-- Left: Transfer Form -->
                    <div class="glass-card">
                        <form id="form-send-money" onsubmit="SendMoneyView.handleSubmit(event)">
                            <div class="amount-display">
                                <span class="amount-prefix">₹</span>
                                <span class="amount-value" id="display-amount">500</span>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="tx-amount">Transfer Amount (INR)</label>
                                <input
                                    type="number"
                                    id="tx-amount"
                                    class="form-input"
                                    value="500"
                                    min="1"
                                    step="1"
                                    required
                                    oninput="SendMoneyView.onAmountChange(this.value)"
                                >
                            </div>

                            <!-- Quick Amount Selectors -->
                            <div style="display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap;">
                                <button type="button" class="btn btn-ghost" style="border: 1px solid var(--border-subtle);" onclick="SendMoneyView.setQuickAmount(250)">₹250 (Safe)</button>
                                <button type="button" class="btn btn-ghost" style="border: 1px solid var(--border-subtle);" onclick="SendMoneyView.setQuickAmount(1500)">₹1,500 (Medium)</button>
                                <button type="button" class="btn btn-ghost" style="border: 1px solid var(--border-subtle);" onclick="SendMoneyView.setQuickAmount(8500)">₹8,500 (High)</button>
                                <button type="button" class="btn btn-ghost" style="border: 1px solid var(--border-subtle);" onclick="SendMoneyView.setQuickAmount(22000)">₹22,000 (Critical)</button>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="tx-recipient">Recipient UPI ID / VPA</label>
                                <input
                                    type="text"
                                    id="tx-recipient"
                                    class="form-input"
                                    placeholder="e.g. merchant@upi or friend@oksbi"
                                    value="grocery_store@upi"
                                    required
                                    oninput="SendMoneyView.onRecipientChange(this.value)"
                                >
                            </div>

                            <!-- Preset Recipient Presets for Testing -->
                            <div style="display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap;">
                                <button type="button" class="btn btn-ghost" style="font-size: 0.75rem; border: 1px solid var(--border-subtle);" onclick="SendMoneyView.setPresetRecipient('grocery_store@upi', 'Fresh Mart')">
                                    🛒 Verified Merchant
                                </button>
                                <button type="button" class="btn btn-ghost" style="font-size: 0.75rem; border: 1px solid var(--border-subtle);" onclick="SendMoneyView.setPresetRecipient('friend@upi', 'Rahul Sharma')">
                                    👤 Known Friend
                                </button>
                                <button type="button" class="btn btn-ghost" style="font-size: 0.75rem; border: 1px solid rgba(245,158,11,0.4); color: var(--warning-400);" onclick="SendMoneyView.setPresetRecipient('unverified_vendor@upi', 'Electro Hub')">
                                    ⚠️ Unverified Vendor
                                </button>
                                <button type="button" class="btn btn-ghost" style="font-size: 0.75rem; border: 1px solid rgba(239,68,68,0.4); color: var(--danger-400);" onclick="SendMoneyView.setPresetRecipient('suspicious_lottery@upi', 'Lucky Draws')">
                                    🚨 Reported Scam VPA
                                </button>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="tx-notes">Transaction Note / Purpose (Optional)</label>
                                <input
                                    type="text"
                                    id="tx-notes"
                                    class="form-input"
                                    placeholder="e.g. Groceries, Dinner split, Electronics"
                                    value="Monthly grocery essentials"
                                >
                            </div>

                            <button type="submit" class="btn btn-primary btn-full btn-lg" id="btn-pay" style="margin-top: 8px;">
                                Proceed to Pay ₹<span id="btn-pay-amount">500</span>
                            </button>
                        </form>
                    </div>

                    <!-- Right: Live AI Dual-Risk Telemetry & Gauges -->
                    <div class="glass-card risk-panel">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <h2 style="font-size: 1rem; font-weight: 700;">Live AI Risk Assessment</h2>
                            <div id="risk-loading" class="spinner hidden" style="width: 14px; height: 14px;"></div>
                        </div>

                        <!-- Overall Risk Gauge -->
                        <div id="overall-gauge-container" style="display: flex; justify-content: center; margin: 10px 0;"></div>

                        <!-- Dual Scores Sub-grid -->
                        <div class="risk-scores-row">
                            <div class="risk-score-item">
                                <div class="risk-score-label">Personal Risk</div>
                                <div class="risk-score-value" id="score-personal" style="color: var(--primary-400);">-</div>
                                <div style="font-size: 0.7rem; color: var(--text-tertiary);">Behavioral Anomaly</div>
                            </div>
                            <div class="risk-score-item">
                                <div class="risk-score-label">Payee Risk</div>
                                <div class="risk-score-value" id="score-payee" style="color: var(--accent-400);">-</div>
                                <div style="font-size: 0.7rem; color: var(--text-tertiary);">Scam / Network ML</div>
                            </div>
                        </div>

                        <!-- Decision & Policy Badge -->
                        <div style="text-align: center; margin: 12px 0;">
                            <span class="status-badge" id="risk-decision-badge">ANALYZING</span>
                        </div>

                        <!-- AI Reason Explanations -->
                        <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-tertiary); margin-top: 16px;">
                            AI Explainability & Risk Signals:
                        </div>
                        <div class="risk-reasons" id="risk-reasons-list">
                            <div class="risk-reason">
                                <span class="risk-reason-icon">💡</span>
                                <span>Adjust amount or recipient to trigger real-time AI risk evaluation.</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    async afterRender() {
        this.gauge = new window.RiskGauge('overall-gauge-container', {
            size: 180,
            title: 'Combined Risk Score'
        });
        this.triggerRiskAnalysis();
    },

    onAmountChange(val) {
        const num = parseFloat(val) || 0;
        document.getElementById('display-amount').textContent = num.toLocaleString('en-IN');
        document.getElementById('btn-pay-amount').textContent = num.toLocaleString('en-IN');
        this.debouncedRiskAnalysis();
    },

    onRecipientChange() {
        this.debouncedRiskAnalysis();
    },

    setQuickAmount(amount) {
        document.getElementById('tx-amount').value = amount;
        this.onAmountChange(amount);
    },

    setPresetRecipient(vpa, note) {
        document.getElementById('tx-recipient').value = vpa;
        if (note) {
            document.getElementById('tx-notes').value = `Payment for ${note}`;
        }
        this.onRecipientChange();
    },

    debouncedRiskAnalysis() {
        clearTimeout(this.riskDebounceTimer);
        this.riskDebounceTimer = setTimeout(() => {
            this.triggerRiskAnalysis();
        }, 350);
    },

    async triggerRiskAnalysis() {
        const amount = parseFloat(document.getElementById('tx-amount')?.value) || 500;
        const recipient = document.getElementById('tx-recipient')?.value.trim() || 'grocery_store@upi';
        const notes = document.getElementById('tx-notes')?.value || '';
        const user = window.api.getUser();
        const senderId = user ? user.username || user.email : 'alice@upi';

        const loading = document.getElementById('risk-loading');
        if (loading) loading.classList.remove('hidden');

        try {
            const riskData = await window.api.analyzeRisk(senderId, recipient, amount, { notes });
            this.currentRiskAssessment = riskData;

            // Update gauge and scores
            if (this.gauge) {
                this.gauge.setValue(riskData.overall_risk);
            }
            document.getElementById('score-personal').textContent = Math.round(riskData.personal_risk);
            document.getElementById('score-payee').textContent = Math.round(riskData.payee_risk);

            // Decision badge
            const badge = document.getElementById('risk-decision-badge');
            badge.className = `status-badge status-${riskData.risk_level.toLowerCase()}`;
            badge.textContent = `DECISION: ${riskData.decision} (${riskData.risk_level})`;

            // Reasons list
            const reasonsContainer = document.getElementById('risk-reasons-list');
            reasonsContainer.innerHTML = riskData.reasons.map(r => {
                const isDanger = r.toLowerCase().includes('fraud') || r.toLowerCase().includes('anomaly') || r.toLowerCase().includes('high');
                return `
                    <div class="risk-reason ${isDanger ? 'risk-reason-danger' : ''}">
                        <span class="risk-reason-icon">${isDanger ? '🚨' : '🛡️'}</span>
                        <span>${r}</span>
                    </div>
                `;
            }).join('');

        } catch (err) {
            console.error('Risk analysis failed:', err);
        } finally {
            if (loading) loading.classList.add('hidden');
        }
    },

    async handleSubmit(e) {
        e.preventDefault();
        const amount = parseFloat(document.getElementById('tx-amount').value);
        const recipientVpa = document.getElementById('tx-recipient').value.trim();
        const notes = document.getElementById('tx-notes').value.trim();
        const btn = document.getElementById('btn-pay');

        if (!amount || amount <= 0) {
            window.showToast('Please enter a valid amount', 'warning');
            return;
        }

        // Check if high risk requires modal confirmation first
        if (this.currentRiskAssessment && (this.currentRiskAssessment.decision === 'WARN' || this.currentRiskAssessment.decision === 'HOLD')) {
            this.showRiskWarningModal(amount, recipientVpa, notes);
            return;
        }

        // Otherwise execute directly
        await this.executeTransfer(amount, recipientVpa, notes, false);
    },

    showRiskWarningModal(amount, recipientVpa, notes) {
        const assessment = this.currentRiskAssessment;
        const isHold = assessment.requires_hold || assessment.decision === 'HOLD';

        const content = `
            <div class="modal-header">
                <h3 class="modal-title" style="color: ${isHold ? 'var(--danger-400)' : 'var(--warning-400)'};">
                    ${isHold ? '⚠️ High Risk Warning & Escrow Hold' : '⚡ Payment Advisory'}
                </h3>
                <button class="modal-close" onclick="window.closeModal()">✕</button>
            </div>
            <div class="confirm-risk-display">
                <div class="confirm-amount">₹${amount.toLocaleString('en-IN')}</div>
                <div class="confirm-recipient">To: <span style="font-family: var(--font-mono); color: var(--accent-400);">${recipientVpa}</span></div>
            </div>

            <div style="background: rgba(239,68,68,0.08); border-left: 3px solid var(--danger-400); padding: 12px; border-radius: var(--radius-sm); margin: 16px 0; font-size: 0.82rem;">
                <div style="font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">
                    Risk Level: ${assessment.risk_level} (Score: ${assessment.overall_risk}/100)
                </div>
                ${assessment.reasons.map(r => `<div style="color: var(--text-secondary); margin-top: 4px;">• ${r}</div>`).join('')}
            </div>

            ${isHold ? `
                <div style="padding: 10px 14px; background: rgba(99,102,241,0.1); border-radius: var(--radius-sm); font-size: 0.78rem; color: var(--primary-200); margin-bottom: 20px;">
                    🔒 <strong>Protection Active:</strong> Funds will be held in the Fund Manager escrow cooling period for 30 minutes. You can dispute or reverse before final settlement.
                </div>
            ` : ''}

            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="window.closeModal()">Cancel Transfer</button>
                <button class="btn ${isHold ? 'btn-danger' : 'btn-primary'}" onclick="SendMoneyView.confirmAndPay(${amount}, '${recipientVpa}', '${encodeURIComponent(notes)}')">
                    ${isHold ? 'Confirm & Hold in Escrow' : 'Proceed with Payment'}
                </button>
            </div>
        `;

        window.showModal(content);
    },

    async confirmAndPay(amount, recipientVpa, encodedNotes) {
        window.closeModal();
        const notes = decodeURIComponent(encodedNotes);
        await this.executeTransfer(amount, recipientVpa, notes, true);
    },

    async executeTransfer(amount, recipientVpa, notes, bypassRiskWarning) {
        const btn = document.getElementById('btn-pay');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Processing Payment...';
        }

        try {
            const idempotencyKey = 'tx-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
            const res = await window.api.createTransaction({
                recipient_vpa: recipientVpa,
                amount: parseFloat(amount),
                notes: notes || 'UPI Transfer',
                idempotency_key: idempotencyKey,
                bypass_risk_warning: bypassRiskWarning
            });

            if (res.status === 'COMPLETED') {
                window.showToast(`₹${amount.toLocaleString('en-IN')} paid successfully to ${recipientVpa}!`, 'success');
            } else if (res.status === 'HELD') {
                window.showToast(`Payment of ₹${amount.toLocaleString('en-IN')} placed in Escrow Cooling Period.`, 'warning');
            } else if (res.status === 'CONFIRMATION_REQUIRED') {
                window.showToast(`Transfer requires explicit confirmation.`, 'info');
            }

            // Refresh user account balance in nav
            window.appRouter.updateBalance();
            window.appRouter.navigate('transactions');

        } catch (err) {
            window.showToast(err.message || 'Payment initiation failed', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `Proceed to Pay ₹<span id="btn-pay-amount">${amount}</span>`;
            }
        }
    }
};

window.SendMoneyView = SendMoneyView;
