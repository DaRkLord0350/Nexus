from dataclasses import dataclass


@dataclass
class TenantContext:
    organization_id: str | None = None
    user_id: str | None = None
    is_superuser: bool = False
