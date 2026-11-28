"""Command line entry point: ``python -m rates_archive <command>``."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .store import GREGORIAN, Archive

REPO_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rates_archive", description="Maintain the archive of Rial exchange rates from bonbast.com."
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="the archive directory (default: this repository)")
    commands = parser.add_subparsers(dest="command", required=True)

    fetch = commands.add_parser("fetch", help="fetch every day missing since the newest stored day")
    fetch.add_argument(
        "--until",
        type=date.fromisoformat,
        help="the last day to fetch, as YYYY-MM-DD (default: yesterday in Tehran, the newest day bonbast.com has)",
    )
    fetch.add_argument("--limit", type=_positive_int, help="fetch at most this many days")
    fetch.add_argument(
        "--max-lag",
        type=int,
        default=1,
        help="exit with status 1 if the archive still ends more than this many days before --until (default: 1)",
    )
    fetch.add_argument("--timeout", type=float, default=30.0, help="seconds to wait for bonbast.com (default: 30)")

    commands.add_parser("aggregate", help="rewrite the monthly and yearly `full` files")
    artifacts = commands.add_parser("artifacts", help="write the release files")
    artifacts.add_argument("--out", type=Path, help="the output directory (default: artifact/ in the archive)")
    commands.add_parser("verify", help="check that the archive has no gaps and every day file is well-formed")
    commands.add_parser("normalize", help="rewrite the day files that are not in the archive's format")

    args = parser.parse_args(argv)
    archive = Archive(args.root)
    return {
        "fetch": _fetch,
        "aggregate": _aggregate,
        "artifacts": _artifacts,
        "verify": _verify,
        "normalize": _normalize,
    }[args.command](archive, args)


def _fetch(archive: Archive, args: argparse.Namespace) -> int:
    # Imported here so the other commands work without network libraries being configured.
    from bonbast import BonbastClient

    from .fetch import catch_up, last_published_day

    until = args.until or last_published_day()
    with BonbastClient(timeout=args.timeout) as client:
        result = catch_up(archive, client, until, limit=args.limit)

    for day in result.fetched:
        print(f"fetched {day}")
    if result.error:
        print(f"could not fetch {result.failed_day}: {result.error}", file=sys.stderr)

    latest = archive.latest()
    if latest is None:
        print("the archive is empty", file=sys.stderr)
        return 1
    lag = (until - latest).days
    if lag <= 0:
        print(f"up to date: the archive ends at {latest}")
        return 0
    print(f"the archive ends at {latest}, {lag} day(s) before {until}", file=sys.stderr)
    return 1 if lag > args.max_lag else 0


def _aggregate(archive: Archive, args: argparse.Namespace) -> int:
    from .build import write_full_files

    changed = write_full_files(archive)
    print(f"updated {len(changed)} full file(s)")
    return 0


def _artifacts(archive: Archive, args: argparse.Namespace) -> int:
    from .build import write_artifacts

    out = args.out or archive.root / "artifact"
    written = write_artifacts(archive, out)
    print(f"wrote {len(written)} file(s) to {out}")
    return 0


def _verify(archive: Archive, args: argparse.Namespace) -> int:
    from .verify import verify

    problems = verify(archive)
    for problem in problems[:50]:
        print(problem, file=sys.stderr)
    if len(problems) > 50:
        print(f"... and {len(problems) - 50} more", file=sys.stderr)
    if problems:
        return 1
    keys = archive.keys(GREGORIAN)
    print(f"ok: {len(keys)} days, {keys[0]} to {keys[-1]}")
    return 0


def _normalize(archive: Archive, args: argparse.Namespace) -> int:
    rewritten = archive.normalize_files()
    for path in rewritten:
        print(f"rewrote {path}")
    print(f"rewrote {len(rewritten)} file(s)")
    return 0


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number
