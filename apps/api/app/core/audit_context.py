from dataclasses import dataclass


@dataclass
class AuditContext:
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
