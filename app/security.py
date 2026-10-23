import hmac
import hashlib
from app.settings import settings


def verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    if not signature_header:
        return False

    computed_signature = hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_signature, signature_header)
