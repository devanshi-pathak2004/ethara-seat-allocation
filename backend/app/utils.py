"""Small shared helpers."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware UTC now (replaces the deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)
