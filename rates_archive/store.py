"""The day files under gregorian/ and jalali/, and the format they are stored in."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from datetime import date
from pathlib import Path
from typing import Any

import jdatetime

from .catalog import NAMES

GREGORIAN = "gregorian"
JALALI = "jalali"
CALENDARS = (GREGORIAN, JALALI)

# The first day bonbast.com has prices for, and the first day file of the archive.
FIRST_DAY = date(2012, 10, 9)

# {"usd": {"name": "US Dollar", "sell": 3550, "buy": 3500}, ...}
Rates = dict[str, dict[str, Any]]

_ORDER = {code: index for index, code in enumerate(NAMES)}


def date_key(day: date, calendar: str) -> str:
    """The ``YYYY/MM/DD`` key of a Gregorian date in a calendar, which is also its path under that calendar."""
    if calendar == JALALI:
        day = jdatetime.date.fromgregorian(date=day)
    return f"{day.year:04d}/{day.month:02d}/{day.day:02d}"


def parse_key(key: str, calendar: str) -> date:
    """The Gregorian date of a ``YYYY/MM/DD`` key in a calendar."""
    year, month, day = (int(part) for part in key.split("/"))
    if calendar == JALALI:
        return jdatetime.date(year, month, day).togregorian()
    return date(year, month, day)


def normalize(rates: Mapping[str, Mapping[str, Any]]) -> Rates:
    """Put the rates of a day in the archive's format.

    Codes are lowercase, known codes take their name from the catalog, prices are ints and a
    missing price is left out. Entries follow the catalog's order; unknown codes go last.
    """
    result: Rates = {}
    for code, quote in rates.items():
        code = code.lower()
        entry: dict[str, Any] = {"name": NAMES.get(code) or str(quote.get("name") or code)}
        for field in ("sell", "buy"):
            if quote.get(field) is not None:
                entry[field] = int(quote[field])
        if len(entry) > 1:
            result[code] = entry
    return dict(sorted(result.items(), key=lambda item: _ORDER.get(item[0], len(_ORDER))))


def dump_day(rates: Rates) -> str:
    return json.dumps(rates, indent=2, ensure_ascii=False)


def write_text(path: Path, text: str) -> bool:
    """Write a file unless it already holds exactly this text. Returns whether it was written."""
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


class Archive:
    """The archive rooted at a directory that holds gregorian/ and jalali/.

    Each day is stored twice, with identical contents: at ``gregorian/YYYY/MM/DD`` and at the
    same day's Jalali date under ``jalali/``.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def path(self, calendar: str, key: str) -> Path:
        return self.root / calendar / key

    def keys(self, calendar: str) -> list[str]:
        """The keys of every stored day in a calendar, oldest first."""
        base = self.root / calendar
        keys = []
        for path in base.glob("*/*/*"):
            parts = path.relative_to(base).parts
            if all(part.isdigit() for part in parts) and path.is_file():
                keys.append("/".join(parts))
        return sorted(keys)

    def read(self, calendar: str, key: str) -> Rates:
        return json.loads(self.path(calendar, key).read_text(encoding="utf-8"))

    def days(self, calendar: str) -> Iterator[tuple[str, Rates]]:
        """Every stored day in a calendar, oldest first."""
        for key in self.keys(calendar):
            yield key, self.read(calendar, key)

    def latest(self) -> date | None:
        """The newest stored day."""
        keys = self.keys(GREGORIAN)
        return parse_key(keys[-1], GREGORIAN) if keys else None

    def write_day(self, day: date, rates: Rates) -> None:
        """Store the rates of a day under both calendars."""
        text = dump_day(normalize(rates))
        for calendar in CALENDARS:
            write_text(self.path(calendar, date_key(day, calendar)), text)

    def normalize_files(self) -> list[str]:
        """Rewrite every day file that is not in the archive's format. Returns the files it rewrote."""
        rewritten = []
        for calendar in CALENDARS:
            for key in self.keys(calendar):
                path = self.path(calendar, key)
                text = dump_day(normalize(json.loads(path.read_text(encoding="utf-8"))))
                if write_text(path, text):
                    rewritten.append(f"{calendar}/{key}")
        return rewritten
