from decimal import Decimal
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Numeric, String, DateTime, ForeignKey
from app.postgresql import db


class PaymentStatus(str, Enum):
    PENDING = "pending"
    CAPTURED = "captured"
    REVERSED = "reversed"


class ProcessedEventModel(db.Model):
    __tablename__ = "processed_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AccountModel(db.Model):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())


class AuthorizationModel(db.Model):
    __tablename__ = "authorizations"

    authorization_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("accounts.account_id"), nullable=False
    )
    merchant: Mapped[str] = mapped_column(String(128), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        String(32), nullable=False, default=PaymentStatus.PENDING
    )
    authorized_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    captured_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    refunded_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class FundingModel(db.Model):
    __tablename__ = "fundings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("accounts.account_id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)


class RefundModel(db.Model):
    __tablename__ = "refunds"

    refund_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    authorization_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("authorizations.authorization_id"), nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("accounts.account_id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
