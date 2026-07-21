from contextvars import ContextVar

# A single request_id doubles as the correlation id for this service — there
# is only one backend process boundary today, so a distinct "correlation id"
# concept would just be a second name for the same value. If a downstream
# service is ever introduced, propagate this value as the correlation id
# rather than minting a new one.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_var.get()


def set_request_id(request_id: str | None) -> None:
    request_id_var.set(request_id)
