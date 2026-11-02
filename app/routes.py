from decimal import Decimal
from flask import Blueprint, request, jsonify, abort
from sqlalchemy import select, func
from app.postgresql import async_session
from app.models import (
    AccountModel,
    FundingModel,
    AuthorizationModel,
    RefundModel,
    PaymentStatus,
)
from app.security import verify_signature
from app.services import process_webhook_event

api_bp = Blueprint("api", __name__)


@api_bp.route("/webhooks", methods=["POST"])
async def handle_webhook():
    raw_body = request.data
    signature = request.headers.get("X-PayFlow-Signature")

    if not verify_signature(raw_body, signature):
        return jsonify({"error": "Invalid signature"}), 401

    try:
        event_data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

    async with async_session() as session:
        try:
            await process_webhook_event(session, event_data)
            await session.commit()
        except Exception as e:
            print(f"WEBHOOK ERROR: {e}")
            await session.rollback()
            pass

    return jsonify({"status": "success"}), 200


@api_bp.route("/accounts/<account_id>/balance", methods=["GET"])
async def get_balance(account_id: str):
    async with async_session() as session:
        account = await session.get(AccountModel, account_id)
        if not account:
            return {"error": "Account not found"}, 404

        # 1. Funded (сума поповнень)
        funded_res = await session.execute(
            select(func.sum(FundingModel.amount)).where(
                FundingModel.account_id == account_id
            )
        )
        funded = funded_res.scalar() or Decimal("0.00")

        # 2. Pending (сума авторизацій у статусі PENDING)
        pending_res = await session.execute(
            select(func.sum(AuthorizationModel.authorized_amount)).where(
                AuthorizationModel.account_id == account_id,
                AuthorizationModel.status == PaymentStatus.PENDING,
            )
        )
        pending = pending_res.scalar() or Decimal("0.00")

        # 3. Captured (сума списань по CAPTURED авторизаціях)
        captured_res = await session.execute(
            select(func.sum(AuthorizationModel.captured_amount)).where(
                AuthorizationModel.account_id == account_id,
                AuthorizationModel.status == PaymentStatus.CAPTURED,
            )
        )
        captured = captured_res.scalar() or Decimal("0.00")

        # 4. Refunded (сума всіх повернень)
        refunded_res = await session.execute(
            select(func.sum(RefundModel.amount)).where(
                RefundModel.account_id == account_id
            )
        )
        refunded = refunded_res.scalar() or Decimal("0.00")

        # Формула балансу згідно з умовами завдання
        available = funded - pending - captured + refunded

        return (
            jsonify(
                {
                    "account_id": account.account_id,
                    "currency": account.currency,
                    "available": f"{available:.2f}",
                    "pending": f"{pending:.2f}",
                }
            ),
            200,
        )


@api_bp.route("/accounts/<account_id>/transactions", methods=["GET"])
async def get_transactions(account_id: str):
    async with async_session() as session:
        account = await session.get(AccountModel, account_id)
        if not account:
            return {"error": "Account not found"}, 404

        result = await session.execute(
            select(AuthorizationModel).where(
                AuthorizationModel.account_id == account_id
            )
        )
        authorizations = result.scalars().all()

        items = []
        for auth in authorizations:
            items.append(
                {
                    "authorization_id": auth.authorization_id,
                    "merchant": auth.merchant,
                    "currency": auth.currency,
                    "status": (
                        auth.status.value
                        if isinstance(auth.status, PaymentStatus)
                        else auth.status
                    ),
                    "authorized_amount": f"{auth.authorized_amount:.2f}",
                    "captured_amount": f"{auth.captured_amount:.2f}",
                    "refunded_amount": f"{auth.refunded_amount:.2f}",
                    "created_at": auth.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            )

        return jsonify({"items": items}), 200
