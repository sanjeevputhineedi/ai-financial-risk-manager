"""Initial schema for 14 entities

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-30 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Accounts table
    op.create_table(
        'accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('upi_id', sa.String(length=100), nullable=False),
        sa.Column('account_number', sa.String(length=50), nullable=False),
        sa.Column('ifsc_code', sa.String(length=20), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('is_frozen', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)
    op.create_index(op.f('ix_accounts_account_number'), 'accounts', ['account_number'], unique=True)
    op.create_index(op.f('ix_accounts_upi_id'), 'accounts', ['upi_id'], unique=True)
    op.create_index(op.f('ix_accounts_user_id'), 'accounts', ['user_id'], unique=False)

    # Recipients table
    op.create_table(
        'recipients',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('payee_vpa', sa.String(length=100), nullable=False),
        sa.Column('payee_name', sa.String(length=255), nullable=False),
        sa.Column('account_number', sa.String(length=50), nullable=True),
        sa.Column('ifsc_code', sa.String(length=20), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipients_id'), 'recipients', ['id'], unique=False)
    op.create_index(op.f('ix_recipients_payee_vpa'), 'recipients', ['payee_vpa'], unique=False)
    op.create_index(op.f('ix_recipients_user_id'), 'recipients', ['user_id'], unique=False)

    # Transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('idempotency_key', sa.String(length=100), nullable=True),
        sa.Column('sender_account_id', sa.String(length=36), nullable=False),
        sa.Column('recipient_vpa', sa.String(length=100), nullable=False),
        sa.Column('recipient_name', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('personal_risk_score', sa.Float(), nullable=True),
        sa.Column('payee_risk_score', sa.Float(), nullable=True),
        sa.Column('overall_risk_score', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.String(length=50), nullable=True),
        sa.Column('decision', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sender_account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_idempotency_key'), 'transactions', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_transactions_recipient_vpa'), 'transactions', ['recipient_vpa'], unique=False)
    op.create_index(op.f('ix_transactions_sender_account_id'), 'transactions', ['sender_account_id'], unique=False)
    op.create_index(op.f('ix_transactions_status'), 'transactions', ['status'], unique=False)

    # Payee Reputation table
    op.create_table(
        'payee_reputation',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('payee_vpa', sa.String(length=100), nullable=False),
        sa.Column('payee_name', sa.String(length=255), nullable=True),
        sa.Column('total_transactions', sa.Integer(), nullable=False),
        sa.Column('successful_transactions', sa.Integer(), nullable=False),
        sa.Column('reported_count', sa.Integer(), nullable=False),
        sa.Column('reputation_score', sa.Float(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('last_evaluated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payee_reputation_id'), 'payee_reputation', ['id'], unique=False)
    op.create_index(op.f('ix_payee_reputation_payee_vpa'), 'payee_reputation', ['payee_vpa'], unique=True)

    # Fraud Reports table
    op.create_table(
        'fraud_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('reporter_user_id', sa.String(length=36), nullable=False),
        sa.Column('payee_vpa', sa.String(length=100), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reporter_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fraud_reports_id'), 'fraud_reports', ['id'], unique=False)
    op.create_index(op.f('ix_fraud_reports_payee_vpa'), 'fraud_reports', ['payee_vpa'], unique=False)
    op.create_index(op.f('ix_fraud_reports_reporter_user_id'), 'fraud_reports', ['reporter_user_id'], unique=False)
    op.create_index(op.f('ix_fraud_reports_transaction_id'), 'fraud_reports', ['transaction_id'], unique=False)

    # Risk Scores table
    op.create_table(
        'risk_scores',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('personal_risk', sa.Float(), nullable=False),
        sa.Column('payee_risk', sa.Float(), nullable=False),
        sa.Column('overall_risk', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_scores_id'), 'risk_scores', ['id'], unique=False)
    op.create_index(op.f('ix_risk_scores_transaction_id'), 'risk_scores', ['transaction_id'], unique=False)

    # Risk Events table
    op.create_table(
        'risk_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('old_risk', sa.Float(), nullable=False),
        sa.Column('new_risk', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_events_id'), 'risk_events', ['id'], unique=False)
    op.create_index(op.f('ix_risk_events_entity_id'), 'risk_events', ['entity_id'], unique=False)
    op.create_index(op.f('ix_risk_events_entity_type'), 'risk_events', ['entity_type'], unique=False)

    # Held Transactions table
    op.create_table(
        'held_transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('held_amount', sa.Float(), nullable=False),
        sa.Column('cooling_period_minutes', sa.Integer(), nullable=False),
        sa.Column('hold_expires_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('release_reason', sa.String(length=500), nullable=True),
        sa.Column('refund_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_held_transactions_id'), 'held_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_held_transactions_status'), 'held_transactions', ['status'], unique=False)
    op.create_index(op.f('ix_held_transactions_transaction_id'), 'held_transactions', ['transaction_id'], unique=True)

    # Fund Manager table
    op.create_table(
        'fund_manager',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('account_number', sa.String(length=50), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('last_audit_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fund_manager_account_number'), 'fund_manager', ['account_number'], unique=True)
    op.create_index(op.f('ix_fund_manager_id'), 'fund_manager', ['id'], unique=False)

    # Model Versions table
    op.create_table(
        'model_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_versions_id'), 'model_versions', ['id'], unique=False)
    op.create_index(op.f('ix_model_versions_model_name'), 'model_versions', ['model_name'], unique=False)

    # Federated Clients table
    op.create_table(
        'federated_clients',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('client_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('last_round', sa.Integer(), nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_federated_clients_client_id'), 'federated_clients', ['client_id'], unique=True)
    op.create_index(op.f('ix_federated_clients_id'), 'federated_clients', ['id'], unique=False)

    # Federated Rounds table
    op.create_table(
        'federated_rounds',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('client_count', sa.Integer(), nullable=False),
        sa.Column('global_loss', sa.Float(), nullable=True),
        sa.Column('global_metrics', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_federated_rounds_id'), 'federated_rounds', ['id'], unique=False)
    op.create_index(op.f('ix_federated_rounds_round_number'), 'federated_rounds', ['round_number'], unique=True)

    # Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('federated_rounds')
    op.drop_table('federated_clients')
    op.drop_table('model_versions')
    op.drop_table('fund_manager')
    op.drop_table('held_transactions')
    op.drop_table('risk_events')
    op.drop_table('risk_scores')
    op.drop_table('fraud_reports')
    op.drop_table('payee_reputation')
    op.drop_table('transactions')
    op.drop_table('recipients')
    op.drop_table('accounts')
    op.drop_table('users')
