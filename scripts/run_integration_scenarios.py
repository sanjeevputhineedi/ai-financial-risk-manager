"""
Checkpoint M15 — End-to-End Integration Scenarios Runner
==========================================================
Demonstrates the 6 core transaction lifecycle scenarios defined in MURALI.md:

1. Normal payment: INR 500 -> Low risk -> Instant payment
2. Personal risk: INR 9,000 -> High personal risk -> Warning/Confirmation required
3. Payee risk: INR 1,000 -> Suspicious recipient -> Warning/Hold
4. Dual risk: INR 8,000 -> High/High -> Escrow Hold in Fund Manager
5. False positive resolution: Risk decreases during cooling period -> Dynamic auto-release
6. Scam escalation: Risk increases during cooling period -> Dynamic auto-refund
"""

import sys
import os
import uuid

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine
from database.seeds.seed_data import seed_database
from backend.app.models.user import User
from backend.app.models.account import Account
from backend.app.models.payee_reputation import PayeeReputation

client = TestClient(app)


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f" SCENARIO: {title}")
    print("=" * 70)


def run_all_scenarios():
    print("Initializing simulated environment & seeding database...")
    seed_database()

    # Reset Alice balance to INR 100,000 for clean scenario execution
    db = SessionLocal()
    alice_user = db.query(User).filter(User.email == "alice@example.com").first()
    if alice_user:
        alice_acc = db.query(Account).filter(Account.user_id == alice_user.id).first()
        if alice_acc:
            alice_acc.balance = 100000.0
            db.commit()
    db.close()

    # Step 1: Login Alice & Admin
    alice_login = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "password123"}).json()
    alice_token = alice_login["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    admin_login = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "password123"}).json()
    admin_token = admin_login["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    print(f"Logged in Alice ({alice_login['email']}) and Admin ({admin_login['email']})")

    # =========================================================================
    # Scenario 1: Normal Payment (INR 500 -> Low Risk -> Instant Execution)
    # =========================================================================
    print_banner("1. Normal Payment (INR 500 -> Low Risk -> Instant Execution)")
    s1_payload = {
        "recipient_vpa": "legitimate_merchant@upi",
        "recipient_name": "SuperMart Grocery",
        "amount": 500.0,
        "notes": "Routine grocery shopping",
        "idempotency_key": str(uuid.uuid4())
    }
    s1_res = client.post("/api/v1/transactions", json=s1_payload, headers=alice_headers).json()
    print(f"Transaction ID:   {s1_res['id']}")
    print(f"Amount:           INR {s1_res['amount']}")
    print(f"Personal Risk:    {s1_res['personal_risk_score']:.1f}")
    print(f"Payee Risk:       {s1_res['payee_risk_score']:.1f}")
    print(f"Overall Risk:     {s1_res['overall_risk_score']:.1f} ({s1_res['risk_level']})")
    print(f"Decision:         {s1_res['decision']}")
    print(f"Final Status:     {s1_res['status']}")
    assert s1_res["status"] == "COMPLETED"
    print("-> PASSED: Instant payment completed without friction.")

    # =========================================================================
    # Scenario 2: Personal Behavioral Anomaly (INR 9,000 -> Warning / Confirmation)
    # =========================================================================
    print_banner("2. Personal Behavioral Risk (INR 9,000 -> Warning / Confirmation)")
    s2_payload = {
        "recipient_vpa": "legitimate_merchant@upi",
        "recipient_name": "SuperMart Grocery",
        "amount": 9000.0,
        "notes": "Unusually high value transfer",
        "idempotency_key": str(uuid.uuid4())
    }
    s2_res = client.post("/api/v1/transactions", json=s2_payload, headers=alice_headers).json()
    print(f"Transaction ID:   {s2_res['id']}")
    print(f"Amount:           INR {s2_res['amount']}")
    print(f"Personal Risk:    {s2_res['personal_risk_score']:.1f} (High behavioral anomaly)")
    print(f"Payee Risk:       {s2_res['payee_risk_score']:.1f}")
    print(f"Overall Risk:     {s2_res['overall_risk_score']:.1f} ({s2_res['risk_level']})")
    print(f"Status:           {s2_res['status']}")
    assert s2_res["status"] == "CONFIRMATION_REQUIRED"

    # User confirms the large transfer
    s2_confirm = client.post(
        f"/api/v1/transactions/{s2_res['id']}/confirm",
        json={"confirmed": True, "user_notes": "I intend to make this high-value transfer"},
        headers=alice_headers
    ).json()
    print(f"Status after confirm: {s2_confirm['status']}")
    assert s2_confirm["status"] in ["COMPLETED", "HELD"]
    print("-> PASSED: User warned; transaction safely completed upon explicit confirmation.")

    # =========================================================================
    # Scenario 3: Payee Risk (INR 1,000 -> Suspicious Recipient -> Warning)
    # =========================================================================
    print_banner("3. Payee Risk (INR 1,000 -> Suspicious Recipient -> Warning)")
    s3_payload = {
        "recipient_vpa": "suspicious_phishing_agent@upi",
        "recipient_name": "Instant Reward Center",
        "amount": 1000.0,
        "notes": "Reward redemption fee",
        "idempotency_key": str(uuid.uuid4())
    }
    s3_res = client.post("/api/v1/transactions", json=s3_payload, headers=alice_headers).json()
    print(f"Transaction ID:   {s3_res['id']}")
    print(f"Amount:           INR {s3_res['amount']}")
    print(f"Personal Risk:    {s3_res['personal_risk_score']:.1f}")
    print(f"Payee Risk:       {s3_res['payee_risk_score']:.1f} (Elevated recipient complaints)")
    print(f"Overall Risk:     {s3_res['overall_risk_score']:.1f} ({s3_res['risk_level']})")
    print(f"Status:           {s3_res['status']}")
    assert s3_res["status"] == "CONFIRMATION_REQUIRED"
    print("-> PASSED: Recipient threat flagged; confirmation required.")

    # =========================================================================
    # Scenario 4: Dual Risk (INR 8,000 -> High/High -> Escrow Cooling Hold)
    # =========================================================================
    print_banner("4. Dual Risk (INR 8,000 -> High/High -> Escrow Cooling Hold)")
    s4_payload = {
        "recipient_vpa": "lottery_scam_support@upi",
        "recipient_name": "International Prize Claim",
        "amount": 8000.0,
        "notes": "Lottery prize processing fee",
        "bypass_risk_warning": True,
        "idempotency_key": str(uuid.uuid4())
    }
    s4_res = client.post("/api/v1/transactions", json=s4_payload, headers=alice_headers).json()
    print(f"Transaction ID:   {s4_res['id']}")
    print(f"Amount:           INR {s4_res['amount']}")
    print(f"Personal Risk:    {s4_res['personal_risk_score']:.1f}")
    print(f"Payee Risk:       {s4_res['payee_risk_score']:.1f}")
    print(f"Overall Risk:     {s4_res['overall_risk_score']:.1f} ({s4_res['risk_level']})")
    print(f"Decision:         {s4_res['decision']}")
    print(f"Status:           {s4_res['status']}")
    assert s4_res["status"] == "HELD"

    held_txs = client.get("/api/v1/held-payments").json()
    target_held = [h for h in held_txs if h["transaction_id"] == s4_res["id"]][0]
    print(f"Held Escrow ID:   {target_held['id']}")
    print(f"Cooling Period:   {target_held['cooling_period_minutes']} minutes")
    print("-> PASSED: Funds debited from sender and secured in Fund Manager Escrow pool.")

    # =========================================================================
    # Scenario 5: False Positive Mitigation (Risk Decays -> Auto-Release)
    # =========================================================================
    print_banner("5. False Positive Mitigation (Risk Decays -> Auto-Release)")
    db = SessionLocal()
    temp_payee = db.query(PayeeReputation).filter(PayeeReputation.payee_vpa == "temporary_flagged_merchant@upi").first()
    if not temp_payee:
        temp_payee = PayeeReputation(
            payee_vpa="temporary_flagged_merchant@upi",
            payee_name="Fresh Agro Direct",
            total_transactions=15,
            successful_transactions=10,
            reported_count=3,
            reputation_score=20.0,
            risk_score=85.0,
            risk_level="HIGH"
        )
        db.add(temp_payee)
        db.commit()
    else:
        temp_payee.risk_score = 85.0
        temp_payee.reputation_score = 20.0
        db.commit()
    db.close()

    s5_payload = {
        "recipient_vpa": "temporary_flagged_merchant@upi",
        "amount": 7000.0,
        "bypass_risk_warning": True,
        "notes": "Bulk produce order",
        "idempotency_key": str(uuid.uuid4())
    }
    s5_res = client.post("/api/v1/transactions", json=s5_payload, headers=alice_headers).json()
    print(f"Transaction ID:   {s5_res['id']} (Status: {s5_res['status']})")
    assert s5_res["status"] == "HELD"

    # Simulate merchant dispute resolved / verified legitimate -> risk drops to 30.0
    db = SessionLocal()
    payee = db.query(PayeeReputation).filter(PayeeReputation.payee_vpa == "temporary_flagged_merchant@upi").first()
    payee.risk_score = 30.0  # Drops below RELEASE_RISK_THRESHOLD (40.0)
    payee.reputation_score = 70.0
    db.commit()
    db.close()

    # Trigger Dynamic Cooling re-evaluation
    reeval = client.post("/api/v1/held-payments/reevaluate").json()
    released_events = [r for r in reeval if r["transaction_id"] == s5_res["id"]]
    assert len(released_events) > 0
    print(f"Dynamic Cooling Action: {released_events[0]['action']}")
    print(f"Reason: {released_events[0]['reason']}")
    assert released_events[0]["action"] == "RELEASED"
    print("-> PASSED: False positive detected and funds automatically released to merchant.")

    # =========================================================================
    # Scenario 6: Scam Escalation (Risk Increases -> Auto-Refund)
    # =========================================================================
    print_banner("6. Scam Escalation (Risk Increases -> Auto-Refund)")
    # Reset scam payee risk
    db = SessionLocal()
    scam_p = db.query(PayeeReputation).filter(PayeeReputation.payee_vpa == "suspicious_phishing_agent@upi").first()
    if scam_p:
        scam_p.risk_score = 80.0
        db.commit()
    db.close()

    s6_payload = {
        "recipient_vpa": "suspicious_phishing_agent@upi",
        "amount": 7500.0,
        "bypass_risk_warning": True,
        "notes": "Fast cash transfer",
        "idempotency_key": str(uuid.uuid4())
    }
    s6_res = client.post("/api/v1/transactions", json=s6_payload, headers=alice_headers).json()
    print(f"Transaction ID:   {s6_res['id']} (Status: {s6_res['status']})")
    assert s6_res["status"] == "HELD"

    # Another user reports this recipient, escalating risk
    client.post("/api/v1/reports", json={
        "payee_vpa": "suspicious_phishing_agent@upi",
        "category": "SUSPECTED_FRAUD",
        "description": "Victim reported complete loss of capital in ponzi scheme."
    }, headers=alice_headers)

    # Trigger Dynamic Cooling re-evaluation
    reeval2 = client.post("/api/v1/held-payments/reevaluate").json()
    refund_events = [r for r in reeval2 if r["transaction_id"] == s6_res["id"]]
    assert len(refund_events) > 0
    print(f"Dynamic Cooling Action: {refund_events[0]['action']}")
    print(f"Reason: {refund_events[0]['reason']}")
    assert refund_events[0]["action"] == "REFUNDED"
    print("-> PASSED: Scam escalation detected; funds protected and refunded to sender.")

    # =========================================================================
    # Check Dashboard Metrics
    # =========================================================================
    print_banner("Platform Live Dashboard Metrics Summary")
    dash = client.get("/api/v1/dashboard/metrics").json()
    print(f"Total Transactions:         {dash['total_transactions']}")
    print(f"Risk Distribution:          {dash['risk_distribution']}")
    print(f"Currently Held Volume:      INR {dash['held_summary']['total_held_volume']:.2f}")
    print(f"Total Refunded Volume:      INR {dash['held_summary']['total_refunded_volume']:.2f}")
    print(f"Fraud Reports Count:        {dash['fraud_reports_count']}")
    print(f"False Positives Mitigated:  {dash['false_positives_mitigated']}")
    print(f"Escrow Pool Balance:        INR {dash['escrow_pool_balance']:.2f}")
    print("\nALL 6 END-TO-END INTEGRATION SCENARIOS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    run_all_scenarios()
