#!/usr/bin/env python3
"""Download and validate daily NSE OHLCV data from StockScans."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime
from pathlib import Path


DEFAULT_SYMBOLS = [
    "TDPOWERSYS",
    "RELIANCE",
    "HDFCBANK",
    "ICICIBANK",
    "TCS",
    "INFY",
    "SBIN",
    "ITC",
    "LT",
    "BHARTIARTL",
    "HINDUNILVR",
    "AXISBANK",
]
BASE_URL = "https://www.stockscans.in/api/charts/ohlcv"
CSV_COLUMNS = ("date", "open", "high", "low", "close", "volume")


def fetch(symbol: str, timeout: int, before: str | None = None) -> dict:
    instrument = urllib.parse.quote(f"NSE:{symbol}", safe="")
    query = urllib.parse.urlencode({"tf": "1D", **({"before": before} if before else {})})
    url = f"{BASE_URL}/{instrument}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "ohlcv-quality-check/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        body = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            body = gzip.decompress(body)
        return json.loads(body.decode("utf-8"))


def years_ago(years: int) -> date:
    today = date.today()
    try:
        return today.replace(year=today.year - years)
    except ValueError:  # February 29 on a non-leap target year.
        return today.replace(year=today.year - years, day=28)


def fetch_history(symbol: str, timeout: int, start_date: date) -> tuple[dict, int, bool, bool]:
    before = None
    pages: list[dict] = []

    while True:
        page = fetch(symbol, timeout, before)
        prices = page.get("prices")
        if not isinstance(prices, list) or not prices:
            raise RuntimeError("API returned an empty prices page")
        pages.append(page)

        oldest = prices[0][0]
        try:
            oldest_date = datetime.strptime(oldest, "%Y-%m-%d").date()
        except (TypeError, ValueError) as error:
            raise RuntimeError(f"API returned an invalid oldest date: {oldest!r}") from error
        if oldest_date <= start_date or not page.get("hasMore"):
            break
        if oldest == before:
            raise RuntimeError("pagination did not advance")
        before = oldest

    combined = {**pages[0], "prices": sorted((row for page in pages for row in page["prices"]), key=lambda row: row[0])}
    reached_requested_start = oldest_date <= start_date
    return combined, len(pages), bool(pages[-1].get("hasMore")), reached_requested_start


def weekday_gaps(dates: list[date]) -> list[str]:
    gaps = []
    for previous, current in zip(dates, dates[1:]):
        missing = []
        probe = previous.fromordinal(previous.toordinal() + 1)
        while probe < current:
            if probe.weekday() < 5:
                missing.append(probe.isoformat())
            probe = probe.fromordinal(probe.toordinal() + 1)
        if missing:
            gaps.append(f"{previous.isoformat()} to {current.isoformat()}: {', '.join(missing)}")
    return gaps


def validate(payload: dict, symbol: str) -> tuple[list[list[object]], dict]:
    problems: list[str] = []
    warnings: list[str] = []
    prices = payload.get("prices")

    if payload.get("companyId") != f"NSE:{symbol}":
        problems.append(f"companyId is {payload.get('companyId')!r}, expected NSE:{symbol}")
    if payload.get("exchange") != "NSE":
        problems.append(f"exchange is {payload.get('exchange')!r}, expected NSE")
    if payload.get("tf") != "1D":
        problems.append(f"tf is {payload.get('tf')!r}, expected 1D")
    if not isinstance(prices, list) or not prices:
        problems.append("prices is missing or empty")
        return [], {"status": "failed", "problems": problems, "warnings": warnings}

    valid_rows: list[list[object]] = []
    parsed_dates: list[date] = []
    for index, row in enumerate(prices):
        prefix = f"row {index + 1}"
        if not isinstance(row, list) or len(row) != 6:
            problems.append(f"{prefix}: expected six fields [date, open, high, low, close, volume]")
            continue
        raw_date, *raw_values = row
        try:
            parsed_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date()
        except ValueError:
            problems.append(f"{prefix}: invalid date {raw_date!r}")
            continue
        try:
            open_, high, low, close, volume = (float(value) for value in raw_values)
        except (TypeError, ValueError):
            problems.append(f"{prefix}: OHLCV values must be numeric")
            continue
        if not all(math.isfinite(value) for value in (open_, high, low, close, volume)):
            problems.append(f"{prefix}: OHLCV contains a non-finite value")
            continue
        if min(open_, high, low, close) <= 0:
            problems.append(f"{prefix}: OHLC prices must be positive")
        if volume < 0:
            problems.append(f"{prefix}: volume cannot be negative")
        if high < max(open_, low, close) or low > min(open_, high, close):
            problems.append(f"{prefix}: OHLC relationship is invalid")
        valid_rows.append([parsed_date.isoformat(), open_, high, low, close, volume])
        parsed_dates.append(parsed_date)

    duplicate_dates = sorted(day.isoformat() for day, count in Counter(parsed_dates).items() if count > 1)
    if duplicate_dates:
        problems.append("duplicate dates: " + ", ".join(duplicate_dates))
    if parsed_dates != sorted(parsed_dates):
        problems.append("dates are not in ascending order")
    gaps = weekday_gaps(sorted(set(parsed_dates)))
    if gaps:
        warnings.append(f"{len(gaps)} weekday gap(s); these can be NSE holidays or missing sessions")
    report = {
        "status": "passed" if not problems else "failed",
        "company_name": payload.get("name"),
        "company_id": payload.get("companyId"),
        "has_more": payload.get("hasMore"),
        "row_count": len(valid_rows),
        "start_date": valid_rows[0][0] if valid_rows else None,
        "end_date": valid_rows[-1][0] if valid_rows else None,
        "problems": problems,
        "warnings": warnings,
        "weekday_gap_count": len(gaps),
        "weekday_gap_examples": gaps[:10],
    }
    return valid_rows, report


def write_csv(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and check daily NSE OHLCV history.")
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS, help="NSE symbols without the NSE: prefix")
    parser.add_argument("--out-dir", default="reports", help="Directory for CSV downloads and quality_report.json")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    parser.add_argument("--years", type=int, default=10, help="Trailing calendar years of daily history to download")
    args = parser.parse_args()
    if args.years < 1:
        parser.error("--years must be at least 1")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    requested_start = years_ago(args.years)
    report = {
        "source": BASE_URL,
        "timeframe": "1D",
        "requested_years": args.years,
        "requested_start_date": requested_start.isoformat(),
        "symbols": {},
    }
    failures = 0

    for input_symbol in args.symbols:
        symbol = input_symbol.upper().removeprefix("NSE:")
        try:
            payload, page_count, more_history_available, reached_requested_start = fetch_history(symbol, args.timeout, requested_start)
            payload["prices"] = [row for row in payload["prices"] if row[0] >= requested_start.isoformat()]
            rows, result = validate(payload, symbol)
            result["page_count"] = page_count
            result["requested_start_date"] = requested_start.isoformat()
            result["coverage_satisfies_request"] = bool(rows) and reached_requested_start
            result["more_history_available"] = more_history_available
            if result["coverage_satisfies_request"] and more_history_available:
                result["warnings"].append("Older history is also available; the CSV is intentionally limited to the requested range")
            if result["coverage_satisfies_request"] and rows[0][0] > requested_start.isoformat():
                result["warnings"].append("The requested start date was not a trading session; the CSV begins on the next available date")
            elif not result["coverage_satisfies_request"]:
                result["warnings"].append("The available history does not reach the requested start date")
            if rows:
                write_csv(out_dir / f"NSE_{symbol}_1D.csv", rows)
            report["symbols"][symbol] = result
            failures += result["status"] != "passed"
            print(f"{symbol}: {result['status']} | {result.get('start_date')} to {result.get('end_date')} | {result.get('row_count')} rows")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, RuntimeError) as error:
            failures += 1
            report["symbols"][symbol] = {"status": "failed", "problems": [str(error)], "warnings": []}
            print(f"{symbol}: failed | {error}", file=sys.stderr)

    (out_dir / "quality_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {out_dir / 'quality_report.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

