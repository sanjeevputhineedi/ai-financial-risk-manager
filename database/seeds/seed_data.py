"""
Seed data generator for simulated academic UPI prototype.
Populates simulated users, accounts, payee reputations, and fund manager escrow pool.
"""

from datetime import datetime, timezone
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models import (
    User,
    Account,
    Recipient,
    PayeeReputation,
    FundManagerAccount,
    ModelVersion,
    FederatedClient
)
from backend.app.core.logging import logger


def seed_database():
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).first():
            logger.info("Database already seeded. Skipping initial seed.")
            return

        logger.info("Seeding users...")
        default_pwd = get_password_hash("password123")
        
        alice = User(
            email="alice@example.com",
            username="alice",
            full_name="Alice Smith",
            hashed_password=default_pwd,
            role="USER"
        )
        bob = User(
            email="bob@example.com",
            username="bob",
            full_name="Bob Sharma",
            hashed_password=default_pwd,
            role="USER"
        )
        admin = User(
            email="admin@example.com",
            username="admin",
            full_name="Risk Platform Admin",
            hashed_password=default_pwd,
            role="ADMIN"
        )
        
        db.add_all([alice, bob, admin])
        db.flush()

        logger.info("Seeding simulated accounts...")
        alice_account = Account(
            user_id=alice.id,
            upi_id="alice@upi",
            account_number="SIMU_ACC_1001",
            balance=25000.0,
            currency="INR"
        )
        bob_account = Account(
            user_id=bob.id,
            upi_id="bob@upi",
            account_number="SIMU_ACC_1002",
            balance=15000.0,
            currency="INR"
        )
        db.add_all([alice_account, bob_account])

        logger.info("Seeding Fund Manager Escrow Account...")
        escrow_pool = FundManagerAccount(
            account_number="ESCROW_POOL_001",
            balance=0.0,
            currency="INR",
            last_audit_at=datetime.now(timezone.utc)
        )
        db.add(escrow_pool)

        logger.info("Seeding Payee Reputations...")
        payees = [
            PayeeReputation(
                payee_vpa="legitimate_merchant@upi",
                payee_name="SuperMart Grocery",
                total_transactions=150,
                successful_transactions=148,
                reported_count=0,
                reputation_score=98.0,
                risk_score=5.0,
                risk_level="LOW"
            ),
            PayeeReputation(
                payee_vpa="bob@upi",
                payee_name="Bob Sharma",
                total_transactions=12,
                successful_transactions=12,
                reported_count=0,
                reputation_score=95.0,
                risk_score=8.0,
                risk_level="LOW"
            ),
            PayeeReputation(
                payee_vpa="new_vendor_electronics@upi",
                payee_name="Quick Gadgets Online",
                total_transactions=10,
                successful_transactions=8,
                reported_count=1,
                reputation_score=55.0,
                risk_score=45.0,
                risk_level="MEDIUM"
            ),
            PayeeReputation(
                payee_vpa="suspicious_phishing_agent@upi",
                payee_name="Instant Reward Center",
                total_transactions=45,
                successful_transactions=10,
                reported_count=8,
                reputation_score=15.0,
                risk_score=85.0,
                risk_level="HIGH"
            ),
            PayeeReputation(
                payee_vpa="lottery_scam_support@upi",
                payee_name="International Prize Claim",
                total_transactions=30,
                successful_transactions=2,
                reported_count=15,
                reputation_score=2.0,
                risk_score=98.0,
                risk_level="CRITICAL"
            )
        ]
        db.add_all(payees)

        logger.info("Seeding Recipients for Alice...")
        recipients = [
            Recipient(
                user_id=alice.id,
                payee_vpa="bob@upi",
                payee_name="Bob Sharma",
                account_number="SIMU_ACC_1002",
                is_verified=True,
                risk_level="LOW"
            ),
            Recipient(
                user_id=alice.id,
                payee_vpa="legitimate_merchant@upi",
                payee_name="SuperMart Grocery",
                is_verified=True,
                risk_level="LOW"
            ),
            Recipient(
                user_id=alice.id,
                payee_vpa="suspicious_phishing_agent@upi",
                payee_name="Instant Reward Center",
                is_verified=False,
                risk_level="HIGH"
            )
        ]
        db.add_all(recipients)

        logger.info("Seeding Model Versions & Federated Clients...")
        models = [
            ModelVersion(
                model_name="payee_risk",
                version="payee-v1",
                metrics={"precision": 0.993, "recall": 0.997, "f1": 0.995, "roc_auc": 1.000},
                is_active=True
            ),
            ModelVersion(
                model_name="personal_risk",
                version="personal-v1",
                metrics={"accuracy": 0.965, "f1": 0.942},
                is_active=True
            )
        ]
        db.add_all(models)

        client1 = FederatedClient(client_id="client_sim_001", status="ONLINE", last_round=3)
        client2 = FederatedClient(client_id="client_sim_002", status="ONLINE", last_round=3)
        db.add_all([client1, client2])

        db.commit()
        logger.info("Database seeding successfully completed!")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
