import json
from datetime import date, datetime, timedelta, timezone

import pytest
from bonbast import Coin, Currency, NetworkError, ParseError, Prices

from rates_archive.build import write_artifacts, write_full_files
from rates_archive.fetch import catch_up, last_published_day
from rates_archive.store import FIRST_DAY, GREGORIAN, JALALI, Archive, date_key, dump_day, normalize, parse_key
from rates_archive.verify import verify


def prices(usd: int) -> Prices:
    """What bonbast 2.x returns: uppercase currency codes and its own names."""
    return Prices(
        currencies=(
            Currency("USD", "US Dollar", sell=usd, buy=usd - 100),
            Currency("QAR", "Qatari Riyal", sell=7000, buy=None),
        ),
        coins=(Coin("emami1", "Emami", sell=900, buy=800), Coin("azadi1", "Azadi", sell=None, buy=None)),
    )


class FakeSource:
    def __init__(self, failures: dict[date, list[Exception]] | None = None) -> None:
        self.failures = failures or {}
        self.calls: list[date] = []

    def history(self, day: date) -> Prices:
        self.calls.append(day)
        pending = self.failures.get(day)
        if pending:
            raise pending.pop(0)
        return prices(1000 + day.day)


def no_sleep(_: float) -> None:
    pass


def seed(archive: Archive, first: date, count: int) -> None:
    for offset in range(count):
        day = first + timedelta(days=offset)
        archive.write_day(day, {"usd": {"name": "US Dollar", "sell": day.day, "buy": day.day}})


def test_normalize_converts_bonbast_2_output_to_the_archive_format():
    assert list(normalize(prices(5000).valid().to_dict()).items()) == [
        ("usd", {"name": "US Dollar", "sell": 5000, "buy": 4900}),
        ("qar", {"name": "Qatari Rial", "sell": 7000}),
        ("emami1", {"name": "emami", "sell": 900, "buy": 800}),
    ]


def test_normalize_keeps_unknown_codes_last_with_their_own_name():
    rates = normalize({"XYZ": {"name": "New Coin", "sell": 1.0, "buy": 2}, "eur": {"name": "x", "sell": 3, "buy": 4}})
    assert list(rates.items()) == [
        ("eur", {"name": "Euro", "sell": 3, "buy": 4}),
        ("xyz", {"name": "New Coin", "sell": 1, "buy": 2}),
    ]


def test_date_keys_round_trip_in_both_calendars():
    day = date(2026, 11, 27)
    assert date_key(day, GREGORIAN) == "2026/11/27"
    assert date_key(day, JALALI) == "1405/09/06"
    assert parse_key("1405/09/06", JALALI) == day
    assert date_key(FIRST_DAY, JALALI) == "1391/07/18"


def test_write_day_stores_identical_files_under_both_calendars(tmp_path):
    archive = Archive(tmp_path)
    archive.write_day(date(2026, 11, 27), {"USD": {"name": "US Dollar", "sell": 2, "buy": 1}})

    gregorian = (tmp_path / "gregorian/2026/11/27").read_text(encoding="utf-8")
    assert gregorian == (tmp_path / "jalali/1405/09/06").read_text(encoding="utf-8")
    assert json.loads(gregorian) == {"usd": {"name": "US Dollar", "sell": 2, "buy": 1}}
    assert archive.latest() == date(2026, 11, 27)


def test_catch_up_fetches_every_missing_day_through_until(tmp_path):
    archive = Archive(tmp_path)
    seed(archive, date(2026, 11, 20), 3)
    source = FakeSource()

    result = catch_up(archive, source, date(2026, 11, 26), sleep=no_sleep)

    assert source.calls == [date(2026, 11, d) for d in (23, 24, 25, 26)]
    assert result.fetched == source.calls and result.error is None
    assert archive.latest() == date(2026, 11, 26)
    assert archive.read(GREGORIAN, "2026/11/24")["usd"] == {"name": "US Dollar", "sell": 1024, "buy": 924}
    assert archive.read(JALALI, "1405/09/03") == archive.read(GREGORIAN, "2026/11/24")


def test_catch_up_does_nothing_when_up_to_date(tmp_path):
    archive = Archive(tmp_path)
    seed(archive, date(2026, 11, 20), 3)
    source = FakeSource()

    result = catch_up(archive, source, date(2026, 11, 22), sleep=no_sleep)

    assert source.calls == [] and result.fetched == []


def test_catch_up_stops_at_the_first_failing_day_so_no_gap_is_left(tmp_path):
    archive = Archive(tmp_path)
    seed(archive, date(2026, 11, 20), 1)
    source = FakeSource({date(2026, 11, 22): [ParseError("layout changed")]})

    result = catch_up(archive, source, date(2026, 11, 25), sleep=no_sleep)

    assert result.fetched == [date(2026, 11, 21)]
    assert result.failed_day == date(2026, 11, 22)
    assert isinstance(result.error, ParseError)
    assert archive.latest() == date(2026, 11, 21)


def test_catch_up_retries_network_errors(tmp_path):
    archive = Archive(tmp_path)
    seed(archive, date(2026, 11, 20), 1)
    flaky = date(2026, 11, 21)
    source = FakeSource({flaky: [NetworkError("timeout"), NetworkError("timeout")]})

    result = catch_up(archive, source, flaky, retries=2, sleep=no_sleep)

    assert result.fetched == [flaky]
    assert source.calls == [flaky] * 3


def test_catch_up_gives_up_after_the_retries(tmp_path):
    archive = Archive(tmp_path)
    seed(archive, date(2026, 11, 20), 1)
    flaky = date(2026, 11, 21)
    source = FakeSource({flaky: [NetworkError("down")] * 3})

    result = catch_up(archive, source, flaky, retries=2, sleep=no_sleep)

    assert result.fetched == [] and isinstance(result.error, NetworkError)


def test_catch_up_starts_at_the_first_day_in_an_empty_archive(tmp_path):
    archive = Archive(tmp_path)
    source = FakeSource()

    catch_up(archive, source, date(2030, 1, 1), limit=2, sleep=no_sleep)

    assert source.calls == [FIRST_DAY, FIRST_DAY + timedelta(days=1)]


@pytest.mark.parametrize(
    ("utc", "expected"),
    [
        (datetime(2026, 11, 27, 20, 29, tzinfo=timezone.utc), date(2026, 11, 26)),  # 23:59 in Tehran
        (datetime(2026, 11, 27, 20, 30, tzinfo=timezone.utc), date(2026, 11, 27)),  # midnight in Tehran
    ],
)
def test_last_published_day_is_yesterday_in_tehran(utc, expected):
    assert last_published_day(utc) == expected


def test_verify_accepts_a_complete_archive_and_reports_problems(tmp_path):
    archive = Archive(tmp_path)
    seed(archive, FIRST_DAY, 5)
    assert verify(archive) == []

    (tmp_path / "gregorian/2012/10/11").unlink()
    (tmp_path / "jalali/1391/07/18").write_text("{}", encoding="utf-8")
    (tmp_path / "gregorian/2012/10/12").write_text(
        dump_day({"USD": {"name": "US Dollar", "sell": 1, "buy": 1}}), encoding="utf-8"
    )

    problems = verify(archive)

    assert "gregorian/ is missing the days between 2012-10-10 and 2012-10-12" in problems
    assert "jalali/1391/07/18 differs from gregorian/2012/10/09" in problems
    assert "jalali/1391/07/20 has no matching gregorian/ day" in problems
    assert any(problem.startswith("gregorian/2012/10/12: is not in the archive's format") for problem in problems)


def test_normalize_files_rewrites_only_files_out_of_format(tmp_path):
    archive = Archive(tmp_path)
    seed(archive, FIRST_DAY, 2)
    drifted = tmp_path / "gregorian/2012/10/10"
    drifted.write_text(dump_day({"USD": {"name": "US Dollar", "sell": 10, "buy": 10}}), encoding="utf-8")

    assert archive.normalize_files() == ["gregorian/2012/10/10"]
    assert archive.normalize_files() == []
    assert verify(archive) == []


def test_full_files_and_artifacts(tmp_path):
    archive = Archive(tmp_path)
    seed(archive, date(2026, 10, 1), 40)  # 2026-10-01 to 2026-11-09

    write_full_files(archive)
    month = json.loads((tmp_path / "gregorian/2026/10/full").read_text(encoding="utf-8"))
    year = json.loads((tmp_path / "jalali/1405/full").read_text(encoding="utf-8"))
    assert list(month)[0] == "2026/10/01" and len(month) == 31
    assert len(year) == 40
    assert write_full_files(archive) == []  # nothing changes on a second run

    out = tmp_path / "artifact"
    write_artifacts(archive, out)

    def load(name):
        return json.loads((out / name).read_text(encoding="utf-8"))

    assert load("gregorian_all.json")["2026/11/09"] == {"usd": {"name": "US Dollar", "sell": 9, "buy": 9}}
    assert load("gregorian_all.min.json")["2026/11/09"] == {"usd": {"sell": 9, "buy": 9}}
    assert list(load("gregorian_7days.min.json")) == [f"2026/11/{d:02d}" for d in range(3, 10)]
    assert len(load("jalali_31days.min.json")) == 31
    assert load("gregorian_imp.min.json")["2026/10/01"] == {"usd": {"sell": 1, "buy": 1}}
    assert list(load("currency/usd.json"))[0] == "1405/07/09"  # currency files are keyed by Jalali dates
    assert (out / "gregorian_all.min.json").read_text(encoding="utf-8").startswith('{"2026/10/01":{"usd"')
