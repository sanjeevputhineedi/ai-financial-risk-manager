# AI Financial Risk Manager for UPI-like Digital Payments

> An AI-powered dual-risk transaction protection architecture that combines personalized financial-behavior anomaly detection, payee reputation intelligence, transaction-graph analysis, federated learning, explainable AI, and adaptive cooling-period protection for UPI-like digital payments.

---

## Overview

This project is an **academic/research prototype** that uses a **simulated UPI-like payment environment** with **synthetic data only**. It does **not** connect to real UPI rails, real bank accounts, or real financial systems.

The system protects users through two independent AI assessments:

1. **Personal Financial Risk Score** — Detects if a transaction is unusually risky for a particular user based on their historical spending behavior.
2. **Payee/Scam Risk Score** — Evaluates whether the recipient is potentially suspicious or fraudulent using reputation intelligence and graph analysis.

A **Transaction Decision Engine** combines these signals. High-risk transactions can enter a simulated **Fund Manager / Escrow Cooling Period**, during which the recipient's risk is continuously re-evaluated. The money is either released to the recipient or returned to the sender based on configurable rules.

---

## Architecture

```
                         ┌─────────────────────────────┐
                         │      CENTRAL SERVER         │
                         │                             │
                         │ Payee Reputation Engine      │
                         │ Fraud Intelligence           │
                         │ Transaction Graph            │
                         │ FL Aggregation               │
                         │ Global Model                 │
                         └──────────────┬──────────────┘
                                        │
                           Model updates only
                                        │
                 ┌──────────────────────┼──────────────────────┐
                 │                      │                      │
          ┌──────▼──────┐       ┌──────▼──────┐       ┌──────▼──────┐
          │   Client A  │       │   Client B  │       │   Client C  │
          │ Local Data  │       │ Local Data  │       │ Local Data  │
          │ Local Model │       │ Local Model │       │ Local Model │
          └─────────────┘       └─────────────┘       └─────────────┘
```

### Transaction Flow

```
               TRANSACTION
                    │
           ┌────────┴────────┐
           │                 │
      USER RISK          PAYEE RISK
           │                 │
  Personal behavior      Fraud/reputation
  anomaly detection      intelligence
           │                 │
           └────────┬────────┘
                    │
              DECISION ENGINE
                    │
        ┌───────────┼───────────┐
        │           │           │
      ALLOW       WARN        PROTECT
        │           │           │
     Instant     Confirm      Hold
                               │
                        ┌──────┴──────┐
                        │             │
                     RELEASE        REFUND
```

---

## Technology Stack

| Layer                  | Technology                          |
| ---------------------- | ----------------------------------- |
| **Backend**            | Python, FastAPI, Pydantic           |
| **Database**           | PostgreSQL (Docker) / SQLite (dev)  |
| **ORM & Migrations**   | SQLAlchemy, Alembic                 |
| **ML**                 | pandas, NumPy, scikit-learn, SHAP   |
| **Federated Learning** | Flower                              |
| **Graph Analysis**     | NetworkX                            |
| **Authentication**     | JWT, bcrypt password hashing        |
| **Infrastructure**     | Docker, Docker Compose              |
| **Testing**            | Pytest, pytest-asyncio              |

---

## Project Structure

```
ai-financial-risk-manager/
│
├── backend/
│   └── app/
│       ├── api/            # API route handlers
│       ├── core/           # Config, database, security
│       ├── models/         # SQLAlchemy ORM models
│       ├── schemas/        # Pydantic request/response schemas
│       ├── services/       # Business logic layer
│       ├── repositories/   # Data access layer
│       └── main.py         # FastAPI application entry point
│
├── ml/
│   ├── payee_risk/         # Payee/scam risk model
│   └── graph/              # Transaction graph intelligence
│
├── data/                   # Synthetic datasets
├── database/
│   └── migrations/         # Alembic migration scripts
│
├── models/                 # Trained ML model artifacts
├── experiments/            # ML experiment results
├── scripts/                # Utility scripts
├── tests/                  # Integration & unit tests
├── docs/                   # Project documentation
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python** 3.10+
- **pip** (Python package manager)
- **Docker** & **Docker Compose** (optional, for containerized setup)

### Local Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ai-financial-risk-manager
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate        # Linux/macOS
   .\venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set a strong `SECRET_KEY`. The default `DATABASE_URL` uses SQLite for local development.

5. **Run database migrations**

   ```bash
   cd database
   alembic upgrade head
   cd ..
   ```

6. **Start the backend server**

   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API**

   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health check: [http://localhost:8000/health](http://localhost:8000/health)

### Docker Setup

```bash
docker-compose up --build
```

This starts both the **FastAPI backend** (port 8000) and **PostgreSQL** (port 5432).

---

## Environment Variables

| Variable                       | Description                                  | Default                         |
| ------------------------------ | -------------------------------------------- | ------------------------------- |
| `SECRET_KEY`                   | JWT signing secret (min 32 chars)            | *(must be set)*                 |
| `ALGORITHM`                    | JWT algorithm                                | `HS256`                         |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | Token expiry duration                        | `1440`                          |
| `DATABASE_URL`                 | Database connection string                   | `sqlite:///./financial_risk.db` |
| `COOLING_PERIOD_MINUTES`       | Fund manager hold duration                   | `30`                            |
| `RELEASE_RISK_THRESHOLD`       | Risk score below which funds are released    | `40.0`                          |
| `REFUND_RISK_THRESHOLD`        | Risk score above which funds are refunded    | `75.0`                          |
| `PERSONAL_RISK_HIGH_THRESHOLD` | Personal risk threshold for warnings         | `70.0`                          |
| `PAYEE_RISK_HIGH_THRESHOLD`    | Payee risk threshold for warnings            | `65.0`                          |
| `OVERALL_RISK_HOLD_THRESHOLD`  | Overall risk threshold for fund holds        | `70.0`                          |

---

## Key Features

### Dual-Risk Assessment
Every transaction is evaluated from two independent perspectives — the sender's personal financial behavior and the recipient's reputation — providing a comprehensive risk picture.

### Personalized Risk Detection
The personal risk model is tailored per-user. Two users making the same ₹9,000 payment may receive different risk scores because their historical spending behavior differs.

### Payee Reputation Engine
A dynamic reputation system that tracks recipient behavior over time. Legitimate behavior reduces risk; suspicious evidence increases it. A single complaint does **not** immediately flag a recipient as fraudulent.

### Transaction Graph Intelligence
Uses NetworkX to analyze transaction relationship networks, identifying suspicious recipients through network-level signals such as counterparty concentration, transaction velocity, and suspicious-neighbor ratio.

### Fund Manager / Escrow Protection
High-risk transactions enter a cooling period during which recipient risk is continuously re-evaluated:
- **Risk decreases** → Funds released to recipient
- **Risk increases** → Funds refunded to sender

### Federated Learning
Uses the Flower framework to simulate multiple clients training personal risk models locally. Raw personal transaction data remains on the client — only model updates are shared with the central server.

### Explainable AI
Every high-risk transaction provides human-readable explanations for why it was flagged, using feature importance analysis and SHAP where appropriate.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## API Documentation

Detailed API documentation is available at:
- **Interactive docs**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- **Reference docs**: See [`docs/API.md`](docs/API.md) and [`docs/BACKEND.md`](docs/BACKEND.md)

---

## Design Principles

| Principle                    | Description                                                          |
| ---------------------------- | -------------------------------------------------------------------- |
| **Security**                 | Protect users from fraud                                             |
| **Financial Safety**         | Reduce harmful impulsive transactions                                |
| **Privacy**                  | Keep personal financial behavior local via federated learning        |
| **User Autonomy**            | Do not automatically block every unusual transaction                 |
| **Explainability**           | Users should understand why the system is warning them               |
| **False-Positive Resistance**| A complaint is evidence, not proof                                   |
| **Adaptability**             | Risk changes as new evidence arrives                                 |
| **Reproducibility**          | Synthetic data, experiments, and models must be reproducible         |
| **Modularity**               | Each component should be independently replaceable                   |
| **Academic Credibility**     | Every major design decision should be measurable and defensible      |

---

## Risk Levels

| Level        | Action                                        |
| ------------ | --------------------------------------------- |
| **LOW**      | Instant simulated payment                     |
| **MEDIUM**   | Warning + user confirmation                   |
| **HIGH**     | Strong warning + confirmation + possible hold |
| **CRITICAL** | Strong warning + explicit confirmation + hold |

---

## Demo Scenarios

| #  | Scenario              | Amount  | Personal Risk | Payee Risk | Outcome         |
| -- | --------------------- | ------- | ------------- | ---------- | --------------- |
| 1  | Normal payment        | ₹500    | Low           | Low        | Instant payment |
| 2  | Impulsive payment     | ₹9,000  | High          | Low        | Warning         |
| 3  | Scam recipient        | ₹1,000  | Low           | High       | Strong warning  |
| 4  | Dual-risk transaction | ₹8,000  | High          | High       | Funds held      |
| 5  | False positive        | —       | —             | Elevated   | Risk decays → Released |
| 6  | Escalating scam       | —       | —             | Increasing | Threshold crossed → Refunded |

---

## Important Notices

> ⚠️ **This is a research prototype.** It uses only simulated payment environments and synthetic data. It must never be connected to real UPI rails, real bank accounts, or real financial systems.

> ⚠️ **Risk is not certainty.** The system uses terms like *risk*, *suspicion*, *probability*, and *confidence* — never definitive fraud labels based solely on model scores.

---

## Documentation

- [`docs/API.md`](docs/API.md) — API endpoint reference
- [`docs/BACKEND.md`](docs/BACKEND.md) — Backend architecture details
- [`docs/PAYEE_RISK.md`](docs/PAYEE_RISK.md) — Payee risk engine documentation
- [`DEVELOPMENT.md`](../DEVELOPMENT.md) — Full development specification & checkpoints

---

## License

This project is developed for academic/research purposes.
