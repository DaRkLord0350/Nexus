import re
from pathlib import Path

INVALID_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.-]+")


def secure_filename(filename: str) -> str:
    name = Path(filename).name
    name = name.strip().replace(" ", "_")
    name = INVALID_FILENAME_CHARS.sub("", name)
    return name or "file"


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()


def parse_metadata(metadata: str | None) -> dict[str, str] | None:
    if not metadata:
        return None
    try:
        import json

        parsed = json.loads(metadata)
        if isinstance(parsed, dict):
            return {str(key): str(value) for key, value in parsed.items()}
    except ValueError:
        pass
    return None
