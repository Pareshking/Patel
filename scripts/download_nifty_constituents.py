from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


OUT = Path("data/nifty_index_history/current")
OUT.mkdir(parents=True, exist_ok=True)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/153.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": UA,
    "Referer": "https://www.niftyindices.com/",
    "Accept": "text/csv,text/plain,application/octet-stream;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SOURCES = {
    "NIFTY50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
    "NIFTYNEXT50": "https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv",
    "NIFTYMIDCAP150": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv",
    "NIFTYSMALLCAP250": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv",
    "NIFTYMICROCAP250": "https://www.niftyindices.com/IndexConstituent/ind_niftymicrocap250list.csv",
}

EXPECTED_ROWS = {
    "NIFTY50": 50,
    "NIFTYNEXT50": 50,
    "NIFTYMIDCAP150": 150,
    "NIFTYSMALLCAP250": 250,
    "NIFTYMICROCAP250": 250,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


session = requests.Session()
session.headers.update(HEADERS)

manifest = {
    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    "user_agent": UA,
    "sources": {},
}

for name, url in SOURCES.items():
    response = session.get(url, timeout=60)
    response.raise_for_status()
    raw = response.content

    if not raw.strip():
        raise RuntimeError(f"{name}: empty response")

    text = raw.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        raise RuntimeError(f"{name}: CSV has no data rows")

    header = rows[0]
    data_rows = [r for r in rows[1:] if any(cell.strip() for cell in r)]
    symbols = []
    symbol_col = next((i for i, h in enumerate(header) if h.strip().lower() == "symbol"), None)
    if symbol_col is None:
        raise RuntimeError(f"{name}: no SYMBOL column; header={header!r}")

    for row in data_rows:
        if symbol_col < len(row):
            symbols.append(row[symbol_col].strip())

    if len(symbols) != EXPECTED_ROWS[name]:
        raise RuntimeError(
            f"{name}: expected {EXPECTED_ROWS[name]} constituents, got {len(symbols)}"
        )
    if len(set(symbols)) != len(symbols):
        raise RuntimeError(f"{name}: duplicate symbols detected")

    path = OUT / f"{name}.csv"
    path.write_bytes(raw)

    manifest["sources"][name] = {
        "url": url,
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "bytes": len(raw),
        "rows": len(symbols),
        "sha256": sha256(raw),
        "columns": header,
    }

(OUT / "manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print(json.dumps(manifest, indent=2))
