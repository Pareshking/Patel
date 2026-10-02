# StockScans OHLCV storage benchmark

This experiment is isolated to `Pareshking/Patel`.

## Goal

Determine whether the durable historical OHLCV representation should be CSV or
Parquet, and which ZSTD compression level is sensible for long-lived R2 object
storage.

The benchmark uses actual StockScans CSV output produced by `check_ohlcv.py`.
Raw market-data files and generated benchmark outputs are intentionally ignored
by Git.

## Run

Acquire real data first:

```powershell
python check_ohlcv.py --symbols RELIANCE TDPOWERSYS HDFCBANK TCS INFY SBIN --years 10
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the local benchmark:

```powershell
python bench_ohlcv.py --input-dir reports
```

It compares CSV with uncompressed Parquet and Parquet + ZSTD levels 1, 3, and
6. For Parquet it records full-history, trailing-252-row, latest-session, and
date/close selected-column read latency. Each latency is median/min/max over
the requested repeats.

These are **local filesystem** timings. They are not R2 network timings.

## Incremental refresh contract

Historical rows are keyed by `(symbol, date)`. An overlapping incoming row
replaces the existing row, allowing provider corrections to be adopted.
Identical overlap is idempotent. A publication sequence should upload and
verify a candidate object before changing the current pointer; an interrupted
publication therefore leaves the previous current object authoritative.

The included tests cover correction, idempotence, duplicate-key rejection, and
pointer safety.

## Final layout decision

Do not choose the final R2 object layout from theory alone. Measure actual
10-year files first. Start with one Parquet object per symbol for simple,
targeted retrieval. If the 1,000-symbol benchmark shows that bulk scans are
dominated by object-count/network overhead, run a second experiment with
consolidated multi-symbol Parquet before changing the production layout.

## Live-access limitation

A network-enabled environment is required for `check_ohlcv.py`. If StockScans
cannot be reached, do not invent benchmark measurements. Run the benchmark
against real CSV files acquired previously or in another network-enabled
environment and preserve the exact measurement environment in the report.
