# Backend Architecture & Platform Documentation

**Workstream Owner:** Murali  
**System:** AI Financial Risk Manager for UPI-like Digital Payments (Simulated Academic Prototype)

---

## 1. Overview & Architectural Principles

The backend provides the persistent transactional backbone, authentication, state engine, and escrow protection mechanisms for the AI Financial Risk Manager.

### Core Guarantees:
1. **100% Simulated Payment Rails:** No connection to real banking, UPI rails, or real financial credentials.
2. **Idempotency & Atomic State Transitions:** Prevents duplicate transactions and ensures double-entry balance consistency.
3. **Decoupled Risk Intelligence:** Backend coordinates risk analysis through stable contracts without hardcoding risk decisions inside the payment router.
4. **Fund Manager Escrow Protection:** Multi-layer protection holds high-risk funds in a cooling escrow pool with dynamic re-evaluation.
5. **Auditing & Zero Secret Leaks:** Every state transition is recorded in an append-only audit trail with automatic secret redaction.

---

## 2. 14 Database Entities (SQLAlchemy 2.0 / Alembic)

| Entity | Table Name | Purpose |
|---|---|---|
| `User` | `users` | Simulated user credentials and roles (`USER`, `ADMIN`, `RESEARCHER`) |
| `Account` | `accounts` | Simulated bank/UPI accounts with virtual balances |
| `Recipient` | `recipients` | Saved payees and contacts per user |
| `Transaction` | `transactions` | Core 9-state payment lifecycle record |
| `PayeeReputation` | `payee_reputation` | Cumulative reputation and risk state per payee VPA |
| `FraudReport` | `fraud_reports` | Crowdsourced user reports with 5 dispute categories |
| `RiskScore` | `risk_scores` | Model snapshots with reasons and confidence |
| `RiskEvent` | `risk_events` | Granular audit trail for reputation and risk score changes |
| `HeldTransaction` | `held_transactions` | Escrow state and cooling period countdown |
| `FundManagerAccount`| `fund_manager` | Escrow pool balance for held funds |
| `ModelVersion` | `model_versions` | Active AI models registry |
| `FederatedClient` | `federated_clients`| FL edge client state tracking |
| `FederatedRound` | `federated_rounds` | FL training round aggregation records |
| `AuditLog` | `audit_logs` | Immutable audit log of all financial/security operations |

---

## 3. Transaction State Machine

```text
       [INITIATED]
           │
           ▼
      [ANALYZING]
           │
  ┌────────┴──────────────────────────┐
  │                                   │
(LOW Risk)                    (HIGH/MEDIUM Risk)
  │                                   │
  ▼                                   ▼
[COMPLETED]                [CONFIRMATION_REQUIRED]
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                    [CANCELLED]               [CONFIRMED]
                                                   │
                                      ┌────────────┴────────────┐
                                      ▼                         ▼
                                 [COMPLETED]                 [HELD]
                                                                │
                                                   ┌────────────┴────────────┐
                                                   ▼                         ▼
                                              [RELEASED]                 [REFUNDED]
```

---

## 4. ML Risk Integration Contract (M5)

The backend bridges Reddy's Payee Risk Random Forest model (`ml.payee_risk.api.analyze_payee`) with a behavioral personal anomaly engine.

- **Thresholds:**
  - `overall_risk < 40.0`: `ALLOW` (Instant payment)
  - `40.0 <= overall_risk < 70.0`: `WARN` (Confirmation required)
  - `70.0 <= overall_risk < 92.0`: `HOLD` (Escrow cooling period hold)
  - `overall_risk >= 92.0`: `CRITICAL HOLD` (Escrow cooling period hold)

---

## 5. Fund Manager Cooling Period Engine (M7 & M8)

1. **Holding Funds:**
   - Sender balance debited: `balance = balance - amount`
   - Fund Manager escrow pool credited: `escrow_balance = escrow_balance + amount`
   - Recipient balance is NOT credited.
2. **Dynamic Re-evaluation:**
   - Periodic scan checks active held transactions against payee reputation updates.
   - If payee risk <= 40.0: Automatically released to recipient.
   - If payee risk >= 75.0: Automatically refunded to sender.
   - Idempotent and duplicate release/refund protected.
