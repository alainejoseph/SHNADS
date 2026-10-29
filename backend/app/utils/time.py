from datetime import datetime, timezone


def ensure_utc(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return dt


def to_utc_iso_z(dt):
    dt = ensure_utc(dt)
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
