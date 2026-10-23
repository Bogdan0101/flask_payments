from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    ProcessedEventModel,
    AccountModel,
    FundingModel,
    AuthorizationModel,
    RefundModel,
    PaymentStatus,
)


async def process_webhook_event(session: AsyncSession, event_data: dict):
    event_id = event_data["id"]
    event_type = event_data["type"]
    raw_created_at = event_data["created_at"]
    event_created_at = datetime.fromisoformat(raw_created_at.replace("Z", "+00:00"))
    data = event_data["data"]

    # 1. Перевірка ідемпотентності
    existing_event = await session.get(ProcessedEventModel, event_id)
    if existing_event:
        return

    # Допоміжна перевірка/створення акаунта для будь-якої події (захист від відсутності акаунта)
    account_id = data.get("account_id")
    if account_id:
        account = await session.get(AccountModel, account_id)
        if not account:
            account = AccountModel(
                account_id=account_id,
                currency=data.get("currency", "USD"),
                created_at=event_created_at,
            )
            session.add(account)
            await session.flush()

    # 2. Обробка бізнес-логіки за типом події
    if event_type == "account.funded":
        amount = Decimal(data["amount"])
        currency = data["currency"]

        funding = FundingModel(
            id=event_id, account_id=account_id, amount=amount, currency=currency
        )
        session.add(funding)

    elif event_type == "authorization.created":
        auth_id = data["authorization_id"]
        account_id = data["account_id"]

        auth = await session.get(AuthorizationModel, auth_id)
        if not auth:
            auth = AuthorizationModel(
                authorization_id=auth_id,
                account_id=account_id,
                merchant=data["merchant"],
                currency=data["currency"],
                status=PaymentStatus.PENDING,
                authorized_amount=Decimal(data["amount"]),
                captured_amount=Decimal("0.00"),
                refunded_amount=Decimal("0.00"),
                created_at=event_created_at,
            )
            session.add(auth)

    elif event_type == "authorization.captured":
        auth_id = data["authorization_id"]
        captured_amount = Decimal(data["amount"])

        auth = await session.get(AuthorizationModel, auth_id)
        if auth:
            auth.status = PaymentStatus.CAPTURED
            auth.captured_amount = captured_amount

    elif event_type == "authorization.reversed":
        auth_id = data["authorization_id"]

        auth = await session.get(AuthorizationModel, auth_id)
        if auth:
            auth.status = PaymentStatus.REVERSED

    elif event_type == "refund.created":
        refund_id = data["refund_id"]
        auth_id = data["authorization_id"]
        account_id = data["account_id"]
        refund_amount = Decimal(data["amount"])

        existing_refund = await session.get(RefundModel, refund_id)
        if not existing_refund:
            refund = RefundModel(
                refund_id=refund_id,
                authorization_id=auth_id,
                account_id=account_id,
                amount=refund_amount,
                currency=data["currency"],
            )
            session.add(refund)

            auth = await session.get(AuthorizationModel, auth_id)
            if auth:
                auth.refunded_amount += refund_amount

    # 3. Фіксуємо подію в таблиці ідемпотентності
    event_log = ProcessedEventModel(
        id=event_id, type=event_type, created_at=event_created_at
    )
    session.add(event_log)
    await session.commit()
