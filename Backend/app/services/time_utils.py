from __future__ import annotations

import random
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from ..config import settings


def _parse_clock(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def random_schedule_for_day(base_day: datetime | None = None) -> datetime:
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz)
    day = (base_day.astimezone(tz) if base_day else now)

    start_t = _parse_clock(settings.posting_window_start)
    end_t = _parse_clock(settings.posting_window_end)

    start_dt = day.replace(hour=start_t.hour, minute=start_t.minute, second=0, microsecond=0)
    end_dt = day.replace(hour=end_t.hour, minute=end_t.minute, second=0, microsecond=0)

    if now > end_dt:
        start_dt = start_dt + timedelta(days=1)
        end_dt = end_dt + timedelta(days=1)

    window_seconds = int((end_dt - start_dt).total_seconds())
    if window_seconds <= 0:
        return start_dt.astimezone(ZoneInfo("UTC"))

    scheduled_local = start_dt + timedelta(seconds=random.randint(0, window_seconds))
    return scheduled_local.astimezone(ZoneInfo("UTC"))
