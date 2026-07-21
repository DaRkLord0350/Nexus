import logging
from logging.config import dictConfig

from app.core.config import settings


def configure_logging() -> None:
    use_json = settings.log_format == "json" or settings.is_production_like
    level = settings.log_level.upper()

    formatters = {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "app.core.logging.JsonFormatter",
        },
    }

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if use_json else "default",
                "level": level,
            }
        },
        "root": {
            "handlers": ["console"],
            "level": level,
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            }
        },
    }
    dictConfig(logging_config)


class JsonFormatter(logging.Formatter):
    """Single-line JSON per record so CloudWatch Logs Insights can query
    fields directly. Includes the current request/correlation id (from
    app.core.request_context, set by AuditContextMiddleware) whenever a log
    call happens inside a request, plus any caller-supplied structured
    fields passed via `logger.info(msg, extra={"structured": {...}})` — used
    e.g. by AuditService to attach the created audit log's id."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        from app.core.request_context import get_request_id

        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id
            payload["correlation_id"] = request_id

        structured = getattr(record, "structured", None)
        if isinstance(structured, dict):
            payload.update(structured)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)
