"""Files built from the day files: the ``full`` files in the archive and the release files."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Any

from .catalog import IMPORTANT, NAMES
from .store import CALENDARS, JALALI, Archive, Rates, parse_key, write_text

# currency/{code}.json has always been keyed by Jalali dates (the Gregorian ones used to be
# written first and then overwritten). Consumers depend on that, so it stays Jalali.
CURRENCY_FILES_CALENDAR = JALALI

RECENT_WINDOWS = (7, 31)


def write_full_files(archive: Archive) -> list[Path]:
    """Write ``{year}/{month}/full`` and ``{year}/full``, mapping each day to its rates, for both calendars.

    Returns the files whose content changed.
    """
    changed = []
    for calendar in CALENDARS:
        groups: dict[str, dict[str, Rates]] = defaultdict(dict)
        for key, rates in archive.days(calendar):
            year, month, _ = key.split("/")
            groups[f"{year}/{month}"][key] = rates
            groups[year][key] = rates
        for prefix, days in groups.items():
            path = archive.path(calendar, f"{prefix}/full")
            if write_text(path, json.dumps(days, ensure_ascii=False)):
                changed.append(path)
    return changed


def write_artifacts(archive: Archive, out_dir: Path) -> list[Path]:
    """Write the release files (see "Files" in README.md) to ``out_dir``. Returns the files written."""
    written: list[Path] = []

    def dump(name: str, data: Any, *, compact: bool = True) -> None:
        path = out_dir / name
        write_text(path, json.dumps(data, ensure_ascii=False, separators=(",", ":") if compact else None))
        written.append(path)

    for calendar in CALENDARS:
        days = dict(archive.days(calendar))
        if not days:
            continue
        dump(f"{calendar}_all.json", days, compact=False)

        slim = {key: _without_names(rates) for key, rates in days.items()}
        dump(f"{calendar}_all.min.json", slim)
        dump(f"{calendar}_imp.min.json", {key: _only(rates, IMPORTANT) for key, rates in slim.items()})

        last = parse_key(next(reversed(slim)), calendar)
        for count in RECENT_WINDOWS:
            first = last - timedelta(days=count - 1)
            tail = list(slim.items())[-count:]
            dump(f"{calendar}_{count}days.min.json", {k: v for k, v in tail if parse_key(k, calendar) >= first})

        if calendar == CURRENCY_FILES_CALENDAR:
            for code in _codes(slim.values()):
                dump(f"currency/{code}.json", {key: rates[code] for key, rates in slim.items() if code in rates})

    return written


def _without_names(rates: Rates) -> Rates:
    return {code: {k: v for k, v in quote.items() if k != "name"} for code, quote in rates.items()}


def _only(rates: Rates, codes: tuple[str, ...]) -> Rates:
    return {code: rates[code] for code in codes if code in rates}


def _codes(days: Any) -> list[str]:
    """Every code that appears on any day, catalog codes first in catalog order."""
    seen = {code for rates in days for code in rates}
    return [code for code in NAMES if code in seen] + sorted(seen - NAMES.keys())
