"""Deterministic event tags for alert stratification. No network. Calendar file is operator-maintained
(reference/event_calendar.csv: date,tag,scope  e.g. 2026-11-04,FOMC,*  or 2026-10-29,EARNINGS,AAPL).
Computed tags: OPEX_MONTHLY (3rd Friday), QUAD_WITCHING (3rd Friday of Mar/Jun/Sep/Dec), QUARTER_END (last
weekday of quarter; pass is_trading_day to respect holidays). Never invent FOMC/CPI/earnings dates: load them."""
import csv, datetime as dt

def third_friday(y, m):
    d = dt.date(y, m, 1)
    first_fri = d + dt.timedelta(days=(4 - d.weekday()) % 7)
    return first_fri + dt.timedelta(days=14)

def last_trading_day_of_quarter(y, q_month, is_trading_day=lambda d: d.weekday() < 5):
    d = (dt.date(y + (q_month == 12), q_month % 12 + 1, 1) - dt.timedelta(days=1))
    while not is_trading_day(d): d -= dt.timedelta(days=1)
    return d

def load_calendar(path):
    with open(path, newline="") as f:
        return [(dt.date.fromisoformat(r["date"]), r["tag"], r.get("scope", "*") or "*")
                for r in csv.DictReader(l for l in f if not l.startswith("#"))]

def tags_for(day: dt.date, ticker: str, calendar=(), is_trading_day=lambda d: d.weekday() < 5):
    t = set()
    if day == third_friday(day.year, day.month):
        t.add("OPEX_MONTHLY")
        if day.month in (3, 6, 9, 12): t.add("QUAD_WITCHING")
    if day.month in (3, 6, 9, 12) and day == last_trading_day_of_quarter(day.year, day.month, is_trading_day):
        t.add("QUARTER_END")
    for d, tag, scope in calendar:
        if d == day and scope in ("*", ticker): t.add(tag)
    return t

def _selftest():
    assert third_friday(2026, 10) == dt.date(2026, 10, 16)
    assert "OPEX_MONTHLY" in tags_for(dt.date(2026, 10, 16), "SPX")
    assert {"OPEX_MONTHLY", "QUAD_WITCHING"} <= tags_for(third_friday(2026, 12), "SPX")
    assert "QUARTER_END" in tags_for(dt.date(2026, 12, 31), "SPX")
    assert "QUARTER_END" not in tags_for(dt.date(2026, 12, 30), "SPX")
    cal = [(dt.date(2026, 11, 4), "FOMC", "*"), (dt.date(2026, 11, 4), "EARNINGS", "AAPL")]
    assert tags_for(dt.date(2026, 11, 4), "MSFT", cal) == {"FOMC"}
    assert tags_for(dt.date(2026, 11, 4), "AAPL", cal) == {"FOMC", "EARNINGS"}
    print("event_tags self-test ok")

if __name__ == "__main__": _selftest()
