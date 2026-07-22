import base64
import hashlib
import hmac
import time

from app.core.config import settings

DOWNLOAD_TOKEN_DELIMITER = ":"


def generate_download_token(resource_id: str, expires_in: int) -> str:
    """Shared by FileService and MediaService for signed local-storage download links."""
    expires_at = int(time.time()) + expires_in
    data = f"{resource_id}{DOWNLOAD_TOKEN_DELIMITER}{expires_at}"
    signature = hmac.new(settings.secret_key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
    token = f"{data}{DOWNLOAD_TOKEN_DELIMITER}{signature}"
    return base64.urlsafe_b64encode(token.encode("utf-8")).decode("utf-8").rstrip("=")


def verify_download_token(token: str) -> str | None:
    try:
        padded_token = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded_token).decode("utf-8")
        resource_id, expires_at_str, signature = raw.rsplit(DOWNLOAD_TOKEN_DELIMITER, 2)
        expires_at = int(expires_at_str)
    except (ValueError, TypeError):
        return None

    if expires_at < int(time.time()):
        return None

    expected = hmac.new(settings.secret_key.encode("utf-8"), f"{resource_id}{DOWNLOAD_TOKEN_DELIMITER}{expires_at}".encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None

    return resource_id
