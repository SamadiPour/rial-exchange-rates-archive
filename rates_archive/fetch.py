"""Fetching the days the archive is missing from bonbast.com."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Protocol

from bonbast import BonbastError, NetworkError, ParseError, Prices

from .store import FIRST_DAY, Archive, Rates, normalize

# Iran has not observed daylight saving time since 2022, so a fixed offset is exact.
TEHRAN = timezone(timedelta(hours=3, minutes=30), "Asia/Tehran")


class HistorySource(Protocol):
    """What the fetcher needs from bonbast.BonbastClient."""

    def history(self, day: date) -> Prices: ...


@dataclass
class CatchUpResult:
    fetched: list[date] = field(default_factory=list)
    # The day that could not be fetched, and why. Fetching stops there so the archive never has a gap.
    failed_day: date | None = None
    error: BonbastError | None = None


def last_published_day(now: datetime | None = None) -> date:
    """The newest day bonbast.com has history for: yesterday in Tehran."""
    now = now or datetime.now(timezone.utc)
    return now.astimezone(TEHRAN).date() - timedelta(days=1)


def to_rates(prices: Prices) -> Rates:
    return normalize(prices.valid().to_dict())


def catch_up(
    archive: Archive,
    source: HistorySource,
    until: date,
    *,
    limit: int | None = None,
    retries: int = 2,
    retry_wait: float = 10.0,
    pause: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> CatchUpResult:
    """Fetch every day after the newest stored one up to ``until``, oldest first, and store it.

    Network errors are retried ``retries`` times. Fetching stops at the first day that still
    fails, so the days after it are not stored before it is.
    """
    result = CatchUpResult()
    latest = archive.latest()
    day = latest + timedelta(days=1) if latest else FIRST_DAY

    while day <= until and (limit is None or len(result.fetched) < limit):
        if result.fetched:
            sleep(pause)
        try:
            rates = _fetch_day(source, day, retries, retry_wait, sleep)
        except BonbastError as error:
            result.failed_day, result.error = day, error
            break
        archive.write_day(day, rates)
        result.fetched.append(day)
        day += timedelta(days=1)

    return result


def _fetch_day(
    source: HistorySource, day: date, retries: int, retry_wait: float, sleep: Callable[[float], None]
) -> Rates:
    for attempt in range(retries + 1):
        try:
            rates = to_rates(source.history(day))
        except NetworkError:
            if attempt == retries:
                raise
            sleep(retry_wait * (attempt + 1))
            continue
        if not rates:
            raise ParseError(f"bonbast.com has no prices for {day}")
        return rates
    raise AssertionError("unreachable")
