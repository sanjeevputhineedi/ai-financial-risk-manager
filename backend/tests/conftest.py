import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.core.database import Base, get_db
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.main import app
from backend.app.models import (
    User,
    Account,
    Recipient,
    PayeeReputation,
    FundManagerAccount,
    ModelVersion
)

# Use separate test database
TEST_DB_URL = "sqlite:///./test_financial_risk.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("test_financial_risk.db"):
        try:
            os.remove("test_financial_risk.db")
        except Exception:
            pass


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed baseline fixtures if empty
    if not session.query(User).filter(User.email == "alice@example.com").first():
        pwd = get_password_hash("password123")
        alice = User(
            id="user-alice-uuid",
            email="alice@example.com",
            username="alice",
            full_name="Alice Smith",
            hashed_password=pwd,
            role="USER"
        )
        bob = User(
            id="user-bob-uuid",
            email="bob@example.com",
            username="bob",
            full_name="Bob Sharma",
            hashed_password=pwd,
            role="USER"
        )
        admin = User(
            id="user-admin-uuid",
            email="admin@example.com",
            username="admin",
            full_name="Platform Admin",
            hashed_password=pwd,
            role="ADMIN"
        )
        session.add_all([alice, bob, admin])
        session.flush()

        alice_acc = Account(
            id="acc-alice-uuid",
            user_id=alice.id,
            upi_id="alice@upi",
            account_number="SIMU_ACC_ALICE",
            balance=25000.0,
            currency="INR"
        )
        bob_acc = Account(
            id="acc-bob-uuid",
            user_id=bob.id,
            upi_id="bob@upi",
            account_number="SIMU_ACC_BOB",
            balance=15000.0,
            currency="INR"
        )
        escrow = FundManagerAccount(
            account_number="ESCROW_POOL_001",
            balance=0.0,
            currency="INR"
        )
        session.add_all([alice_acc, bob_acc, escrow])

        # Payees
        legit_payee = PayeeReputation(
            payee_vpa="legitimate_merchant@upi",
            payee_name="SuperMart Grocery",
            total_transactions=50,
            successful_transactions=50,
            reported_count=0,
            reputation_score=98.0,
            risk_score=5.0,
            risk_level="LOW"
        )
        scam_payee = PayeeReputation(
            payee_vpa="suspicious_phishing@upi",
            payee_name="Fake Reward Agent",
            total_transactions=20,
            successful_transactions=2,
            reported_count=10,
            reputation_score=10.0,
            risk_score=90.0,
            risk_level="HIGH"
        )
        session.add_all([legit_payee, scam_payee])
        session.commit()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def alice_token(db_session):
    alice = db_session.query(User).filter(User.email == "alice@example.com").first()
    return create_access_token(alice.id)


@pytest.fixture
def admin_token(db_session):
    admin = db_session.query(User).filter(User.email == "admin@example.com").first()
    return create_access_token(admin.id)


@pytest.fixture
def alice_auth_headers(alice_token):
    return {"Authorization": f"Bearer {alice_token}"}


@pytest.fixture
def admin_auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
