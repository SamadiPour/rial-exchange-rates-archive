"""Checks that the archive is complete and consistent."""

from __future__ import annotations

import json
from datetime import timedelta

from .store import FIRST_DAY, GREGORIAN, JALALI, Archive, date_key, dump_day, normalize, parse_key


def verify(archive: Archive) -> list[str]:
    """Return every problem found, or an empty list.

    Checks that the Gregorian days run from FIRST_DAY with no gap, that every day file is in the
    archive's format, and that jalali/ holds exactly the same days with identical contents.
    """
    keys = archive.keys(GREGORIAN)
    if not keys:
        return [f"no day files in {archive.path(GREGORIAN, '')}"]

    problems = []
    days = [parse_key(key, GREGORIAN) for key in keys]
    if days[0] != FIRST_DAY:
        problems.append(f"gregorian/ starts at {days[0]}, not {FIRST_DAY}")
    for previous, current in zip(days, days[1:]):
        if current - previous != timedelta(days=1):
            problems.append(f"gregorian/ is missing the days between {previous} and {current}")

    jalali_keys = set(archive.keys(JALALI))
    expected_jalali = set()
    for key, day in zip(keys, days):
        text = archive.path(GREGORIAN, key).read_text(encoding="utf-8")
        problem = _format_problem(text)
        if problem:
            problems.append(f"gregorian/{key}: {problem}")

        jalali_key = date_key(day, JALALI)
        expected_jalali.add(jalali_key)
        if jalali_key not in jalali_keys:
            problems.append(f"jalali/{jalali_key} is missing (gregorian/{key} exists)")
        elif archive.path(JALALI, jalali_key).read_text(encoding="utf-8") != text:
            problems.append(f"jalali/{jalali_key} differs from gregorian/{key}")

    for jalali_key in sorted(jalali_keys - expected_jalali):
        problems.append(f"jalali/{jalali_key} has no matching gregorian/ day")

    return problems


def _format_problem(text: str) -> str | None:
    try:
        data = json.loads(text)
        if not isinstance(data, dict) or not data:
            return "is not a non-empty JSON object"
        if dump_day(normalize(data)) != text:
            return "is not in the archive's format; run `python -m rates_archive normalize`"
    except (ValueError, TypeError, AttributeError) as error:
        return f"is invalid ({error})"
    return None
