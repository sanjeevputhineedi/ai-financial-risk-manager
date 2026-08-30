# Payee/Scam Risk Intelligence — Reddy's Workstream

Part of **AI Financial Risk Manager for UPI-like Digital Payments**
(simulated academic prototype — no real UPI, no real accounts, no real payments).

## What this component does

Given a recipient (`payee_id`) and transaction context, `analyze_payee()`
returns a risk assessment combining three independent signals:

1. **Direct risk** — a RandomForest classifier over 20 documented, leakage-free
   behavioral features (account age, velocity, refund ratio, complaint rate, etc.)
2. **Reputation risk** — a stateful, decaying score that evolves with evidence
   over time; a single report never alone brands someone a scammer
3. **Graph risk** — NetworkX transaction-graph features capturing risk from
   *who a recipient is connected to*, not just their own history

These are combined with documented, fixed weights (45% direct / 35% reputation
/ 20% graph — see `ml/payee_risk/risk_integration.py`) into a single
`combined_payee_risk` score, translated into plain-language reasons.

## Architecture

```
data/fraud/generate_dataset.py   -> synthetic payee dataset (R1)
ml/payee_risk/features.py        -> feature engineering, 20-dim vector (R2)
ml/payee_risk/model.py           -> baseline RandomForest model (R3)
ml/payee_risk/reputation.py      -> dynamic reputation engine (R4)
ml/payee_risk/reports.py         -> report classification & evidentiary weight (R5)
ml/graph/graph_features.py       -> NetworkX transaction graph (R6)
ml/payee_risk/risk_integration.py-> combine direct+reputation+graph (R7)
ml/payee_risk/explainability.py  -> human-readable reasons + SHAP hook (R8)
ml/payee_risk/api.py             -> analyze_payee() — the stable contract (R9)
experiments/evaluate_model.py    -> precision/recall/F1/ROC-AUC/PR-AUC (R10)
experiments/false_positive_experiment.py -> key research result (R11)
experiments/adversarial_scenarios.py     -> evasion-resistance tests (R12)
tests/test_integration.py        -> simulated Murali + Sanjeev integration (R13/R14)
```

## The API contract (what Murali/Sanjeev call)

```python
from ml.payee_risk.api import analyze_payee

result = analyze_payee(payee_id, {"record": {...features...}})
```

```json
{
  "payee_risk": 79.99,
  "risk_level": "HIGH",
  "confidence": 0.55,
  "reasons": ["Multiple reports filed against this recipient", "..."],
  "model_version": "payee-v1"
}
```

This schema is **stable**. Any change requires updating this file,
`REDDY_STATE.md`, and notifying both other workstreams.

## Evaluation results (Checkpoint R10)

On a held-out 20% test split (n=2000, seed=42):

| Metric | Value |
|---|---|
| Precision | 0.993 |
| Recall | 0.997 |
| F1 | 0.995 |
| ROC-AUC | 1.000 |
| PR-AUC | 1.000 |
| False Positive Rate | 0.0012 |

**Honest caveat:** these numbers are near-ceiling because the synthetic
data generator (R1) produces classes with clearly-defined (if
overlapping) generative rules. Real-world payee data will be noisier
and less separable — these metrics validate the *pipeline*, not
production-grade fraud detection. See `data/fraud/generate_dataset.py`
for the injected overlap/noise that keeps this from being a trivial
100%-accuracy toy problem.

## Key research result (Checkpoint R11)

The reputation engine can distinguish a **reported-legitimate merchant**
(risk initially elevated by reports, but decays as behavior stays clean)
from an **actual suspicious merchant** (risk escalates with corroborating
evidence) — even though both started from the same seed score of 68.

- Reported-legitimate final score: **46.4** (trending down)
- Actual suspicious merchant final score: **100.0** (trending up)
- Score gap: **53.6 points**

Run: `python3 -m experiments.false_positive_experiment`

## Adversarial resistance (Checkpoint R12)

Synthetic-only evaluation (no real abuse tooling) of three evasion
patterns, all of which the graph/reputation layer catches even when a
naive "risk = report_count" system would score them as zero risk:

- **Rotating counterparties** (40 one-time senders, zero direct reports): naive risk = 0, graph risk > 0 due to suspicious neighbor ratio
- **Related account cluster** (mule ring, only 1 of 4 accounts reported): graph propagates risk to the other 3 unreported accounts
- **Activity cooldown** (report, go quiet, report again): decay lowers score during the quiet period but repetition amplification means round 2 lands higher than round 1, resisting simple wait-it-out evasion

Run: `python3 -m experiments.adversarial_scenarios`

## Integration status

- **Murali (backend):** `analyze_payee(payee_id, transaction_context)` is
  the exact interface his `/risk/analyze` payee-risk adapter should call.
  Malformed input raises a clear `ValueError` his backend can catch
  (per his M11 test requirement for "ML service" error handling).
- **Sanjeev (personal risk / decision combiner):** output includes
  `model_version` on every call and a stable numeric `payee_risk`
  (0-100) field for combining with `personal_risk`.

## How to reproduce everything

```bash
# R1 — generate dataset
python3 data/fraud/generate_dataset.py --n 10000 --seed 42 --out data/fraud/synthetic_payees.csv

# R3 — train baseline model
python3 -m ml.payee_risk.model

# R10 — evaluate
python3 -m experiments.evaluate_model

# R11 — false positive experiment
python3 -m experiments.false_positive_experiment

# R12 — adversarial scenarios
python3 -m experiments.adversarial_scenarios

# R13/R14 — integration tests
python3 -m tests.test_integration

# R9 — see the live API contract
python3 -m ml.payee_risk.api
```

## Known limitations / honest next steps

- Reputation state is currently in-memory (`PayeeRiskService.reputation_states`
  dict) — Murali's database owns persistence in production; this is a
  drop-in interface, not a storage layer.
- Graph risk uses a documented linear formula, not a GNN, per R7's explicit
  instruction not to build a GNN initially. `GraphRiskScorer` is the
  interface point for a future learned graph model.
- SHAP integration (`explainability.shap_top_features`) is wired but
  optional — install `shap` to enable it; rule-based reasons always work
  without it.
- Evaluation metrics are near-ceiling due to synthetic data separability;
  see the evaluation section caveat above.
