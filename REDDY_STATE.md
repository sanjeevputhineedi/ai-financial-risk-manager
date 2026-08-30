# Reddy State

Current checkpoint:
R15 — Final Payee Intelligence Package

Status:
COMPLETE (all R1–R15 checkpoints implemented, tested, and passing)

Completed:
- R1: Synthetic payee dataset generator (6 profile classes, 13 direct features, reproducible seed, realistic ~15% fraud-like imbalance, injected overlap noise for non-trivial separability)
- R2: Feature engineering (`features.py`) — 20-dim documented, deterministic, normalized feature vector; no data leakage; temporal + rolling + graph-placeholder features
- R3: Baseline RandomForest model (`model.py`) — payee_risk_score 0-100, risk_level, confidence, model_version="payee-v1"
- R4: Reputation engine (`reputation.py`) — configurable increase/decay/repetition-amplification; verified matches spec's expected trajectories
- R5: Report evidence model (`reports.py`) — 5 categories, outcome multipliers, no invented legal certainty
- R6: Transaction graph (`graph_features.py`) — NetworkX MultiDiGraph, verified a recipient with 0 direct complaints shows elevated risk from suspicious neighbors
- R7: Graph-based risk integration (`risk_integration.py`) — documented 45/35/20 weighted combination, GNN interface stub for future work
- R8: Explainability (`explainability.py`) — rule-based reasons (always available) + optional SHAP hook
- R9: API contract (`api.py`) — `analyze_payee(payee_id, transaction_context)` matches Murali's expected schema exactly
- R10: Evaluation (`evaluate_model.py`) — precision/recall/F1/ROC-AUC/PR-AUC/confusion matrix/FPR, reproducible with seed
- R11: False-positive experiment (`false_positive_experiment.py`) — PASSES: reported-legitimate (46.4, decaying) vs actual-suspicious (100.0, escalating), 53.6-point gap
- R12: Adversarial/evasion scenarios (`adversarial_scenarios.py`) — 3 scenarios, all show graph/reputation add value over naive report-count baseline
- R13/R14: Integration tests (`test_integration.py`) — simulated Murali backend calls + Sanjeev combiner stability checks, all pass
- R15: Final docs (`docs/PAYEE_RISK.md`) + this state file

Files created:
- data/fraud/generate_dataset.py
- data/fraud/synthetic_payees.csv (10,000 rows, seed=42)
- ml/payee_risk/features.py
- ml/payee_risk/model.py
- ml/payee_risk/reputation.py
- ml/payee_risk/reports.py
- ml/payee_risk/risk_integration.py
- ml/payee_risk/explainability.py
- ml/payee_risk/api.py
- ml/graph/graph_features.py
- experiments/evaluate_model.py
- experiments/false_positive_experiment.py
- experiments/adversarial_scenarios.py
- experiments/evaluation_results.json
- experiments/false_positive_results.json
- experiments/adversarial_results.json
- tests/test_integration.py
- models/payee_risk_model.pkl
- models/payee_risk_model.meta.json
- docs/PAYEE_RISK.md
- REDDY_STATE.md

Files modified:
- (none — greenfield build)

Model:
- RandomForestClassifier, n_estimators=200, max_depth=8, class_weight="balanced"
- model_version: "payee-v1"
- Trained on data/fraud/synthetic_payees.csv, seed=42, 80/20 train/test split

Evaluation:
- precision=0.993, recall=0.997, f1=0.995, roc_auc=1.000, pr_auc=1.000, fpr=0.0012
- See experiments/evaluation_results.json for full output
- Caveat documented in docs/PAYEE_RISK.md: near-ceiling metrics reflect synthetic data structure, not production-grade guarantee

Known issues:
- Reputation state is in-memory only in PayeeRiskService — needs to be backed by Murali's `payee_reputation` / `risk_events` DB tables in production integration (interface is ready, storage is not Reddy's to own per ownership boundary)
- Graph is built fresh per process; no persistence layer for transaction graph edges yet (also DB territory)
- ROC-AUC still rounds to 1.000 despite injected noise; if a reviewer wants more separation for a more "realistic" evaluation story, increase noise magnitude in generate_dataset.py (search "Inject realistic overlap noise")
- SHAP not installed by default (optional dependency) — rule-based explanations are the primary/required path and always work

Exact next task:
- Package this workstream into the shared GitHub repo under the ownership boundary paths from REDDY.md section 2 (ml/payee_risk/, ml/graph/, data/fraud/), and hand the docs/PAYEE_RISK.md contract to Murali for his M5 (`/risk/analyze`) and M6 (payee reputation API) integration.

Integration contract:
- `analyze_payee(payee_id, transaction_context)` -> {payee_risk, risk_level, confidence, reasons, model_version}
- transaction_context = {"record": {...direct features...}, "graph_features": {...optional...}}
- Contract is STABLE as of model_version "payee-v1" — do not change field names without updating this file + docs/PAYEE_RISK.md + notifying Murali/Sanjeev

Last commit:
- Not yet committed — this package was built locally and needs to be pushed to the shared repo (see "Exact next task")
