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


def fetch(symbol: str, timeout: int) -> dict:
    instrument = urllib.parse.quote(f"NSE:{symbol}", safe="")
    url = f"{BASE_URL}/{instrument}?tf=1D"
    request = urllib.request.Request(url, headers={"User-Agent": "ohlcv-quality-check/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        body = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            body = gzip.decompress(body)
        return json.loads(body.decode("utf-8"))


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
    if payload.get("hasMore") is True:
        warnings.append("API returned hasMore=true: this download may be a capped window, not complete history")

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
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {"source": BASE_URL, "timeframe": "1D", "symbols": {}}
    failures = 0

    for input_symbol in args.symbols:
        symbol = input_symbol.upper().removeprefix("NSE:")
        try:
            payload = fetch(symbol, args.timeout)
            rows, result = validate(payload, symbol)
            if rows:
                write_csv(out_dir / f"NSE_{symbol}_1D.csv", rows)
            report["symbols"][symbol] = result
            failures += result["status"] != "passed"
            print(f"{symbol}: {result['status']} | {result.get('start_date')} to {result.get('end_date')} | {result.get('row_count')} rows")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, RuntimeError) as error:
            failures += 1
            report["symbols"][symbol] = {"status": "failed", "problems": [str(error)], "warnings": []}
            print(f"{symbol}: failed | {error}", file=sys.stderr)

    (out_dir / "quality_report.json").write_text(json.dumps(report, indent=2) + "
", encoding="utf-8")
    print(f"Report: {out_dir / 'quality_report.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
