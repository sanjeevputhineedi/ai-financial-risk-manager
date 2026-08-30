# Continuation Guide for Sanjeev

**Project**: AI Financial Risk Manager for UPI-like Digital Payments  
**Last Updated**: 2026-08-30  
**Test Suite Status**: 31 / 31 Automated Tests Passing (`pytest`)

---

## 1. Executive Summary & Current State

The project backend and payee risk ML intelligence foundations are **fully built, integrated, and tested**.

### Completed Workstreams:
1. **Murali Workstream (M1–M15 Completed)**:
   - FastAPI application with structured error handling, security middleware, JWT authentication, and native bcrypt hashing.
   - SQLAlchemy 2.0 ORM with 14 persistent entities, Alembic migrations (`database/migrations/`), and database seeds.
   - 9-state payment lifecycle (`INITIATED`, `ANALYZING`, `CONFIRMATION_REQUIRED`, `CONFIRMED`, `COMPLETED`, `HELD`, `RELEASED`, `REFUNDED`, `CANCELLED`).
   - Fund Manager / Escrow cooling period service with dynamic risk re-evaluation and auto-release / auto-refund triggers.
   - Immutable audit logging with credential redaction.
   - 27 automated tests under `backend/tests/` passing.
   - Multi-stage `Dockerfile` and `docker-compose.yml` (PostgreSQL + FastAPI).

2. **Reddy Workstream (R1–R15 Completed)**:
   - Synthetic payee fraud dataset generator (`data/fraud/`, 10k records, seed=42).
   - Payee risk Random Forest model (`models/payee_risk_model.pkl`) with 20 engineered features.
   - Payee reputation engine with dynamic increase/decay and evidence multipliers.
   - NetworkX transaction graph intelligence capturing counterparty concentration and suspicious neighbor ratios.
   - Integration tests (`tests/test_integration.py`) validating the ML API contract.

---

## 2. Immediate Next Tasks for Sanjeev

### Task A: Personal Financial Risk Model (Checkpoint 05)
- **Objective**: Build personalized spending behavior anomaly detection (statistical z-score + Isolation Forest / ML anomaly detector).
- **Location**: `ml/personal_risk/`
- **Requirements**:
  - Evaluate amount deviation against user's historical spend profile (mean, std dev, max, daily/weekly frequency).
  - Time-of-day deviation and recipient familiarity.
  - Return `personal_risk_score` (0–100), `risk_level` (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`), and `reasons[]`.
  - Connect this model into `backend/app/services/risk_service.py` to replace the heuristic placeholder.

### Task B: Dual-Risk Decision Engine Refinement (Checkpoint 08)
- **Objective**: Ensure seamless combination of `personal_risk` (Sanjeev) + `payee_risk` (Reddy) using policy thresholds.
- **Contract**: Schema documented in `docs/API.md` and `docs/PAYEE_RISK.md`.

### Task C: Federated Learning Simulation (Checkpoint 10)
- **Objective**: Implement FL using the **Flower** framework across >= 5 simulated clients with non-IID local transaction history.
- **Location**: `federated/` (`client.py`, `server.py`, `strategy.py`, `simulation.py`).
- **Privacy Rule**: Raw transaction records remain on local client nodes; only model parameter updates are aggregated centrally.

### Task D: Explainable AI & SHAP (Checkpoint 11)
- **Objective**: Expose clear, human-understandable reason codes and feature contributions for transactions flagged as `HIGH` or `CRITICAL`.
- **Location**: `ml/explainability/`

### Task E: UPI-like Frontend Application (Checkpoint 12)
- **Objective**: Build a simulated React + TypeScript + Tailwind UI that connects to the FastAPI backend.
- **Location**: `frontend/`
- **Key Flows**:
  1. Login / Register
  2. Send Money / Recipient selection
  3. Real-time Risk Assessment view (Personal score + Payee score)
  4. Escrow Cooling Period tracker (Held -> Released / Refunded)
  5. Transaction History & Analytics Dashboard

---

## 3. Quickstart & Verification Commands

### Run All Tests
```powershell
pytest
```
*Expected: 31 passed in ~10 seconds.*

### Run Integration Scenarios
```powershell
python scripts/run_integration_scenarios.py
```

### Start Backend Locally
```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 4. Key Reference Documents
- [README.md](file:///c:/Users/subha/OneDrive/Desktop/razor/ai-financial-risk-manager/README.md) — Main documentation and overview
- [DEVELOPMENT.md](file:///c:/Users/subha/OneDrive/Desktop/razor/DEVELOPMENT.md) — 15 checkpoint master specification
- [docs/API.md](file:///c:/Users/subha/OneDrive/Desktop/razor/ai-financial-risk-manager/docs/API.md) — FastAPI endpoint specification
- [docs/BACKEND.md](file:///c:/Users/subha/OneDrive/Desktop/razor/ai-financial-risk-manager/docs/BACKEND.md) — Architecture & services reference
- [docs/PAYEE_RISK.md](file:///c:/Users/subha/OneDrive/Desktop/razor/ai-financial-risk-manager/docs/PAYEE_RISK.md) — Payee ML intelligence contract
- [MURALI_STATE.md](file:///c:/Users/subha/OneDrive/Desktop/razor/ai-financial-risk-manager/MURALI_STATE.md) & [REDDY_STATE.md](file:///c:/Users/subha/OneDrive/Desktop/razor/ai-financial-risk-manager/REDDY_STATE.md) — Completed workstream checkpoints
