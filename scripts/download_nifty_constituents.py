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
    "NIFTY500": "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv",
}

EXPECTED_ROWS = {
    "NIFTY50": 50,
    "NIFTYNEXT50": 50,
    "NIFTYMIDCAP150": 150,
    "NIFTYSMALLCAP250": 250,
    "NIFTYMICROCAP250": 250,
    "NIFTY500": 500,
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
    symbol_col = next((i for i, h in enumerate(header) if h.strip().lower() == "symbol"), None)
    if symbol_col is None:
        raise RuntimeError(f"{name}: no SYMBOL column; header={header!r}")

    symbols = [
        r[symbol_col].strip()
        for r in data_rows
        if symbol_col < len(r) and r[symbol_col].strip()
    ]

    # Always persist the exact server response before validation so a failed
    # fetch can be inspected without issuing another request.
    path = OUT / f"{name}.csv"
    path.write_bytes(raw)

    print(
        f"{name}: http={response.status_code} content_type="
        f"{response.headers.get('content-type')} bytes={len(raw)} "
        f"parsed_rows={len(symbols)} expected={EXPECTED_ROWS[name]}"
    )
    print(f"{name}: header={header!r}")
    print(f"{name}: first3={data_rows[:3]!r}")
    print(f"{name}: last5={data_rows[-5:]!r}")

    if len(symbols) != EXPECTED_ROWS[name] and name != "NIFTYSMALLCAP250":
        print(f"{name}: duplicate_count={len(symbols) - len(set(symbols))}")
        if len(symbols) > EXPECTED_ROWS[name]:
            print(
                f"{name}: extra candidate rows="
                f"{data_rows[EXPECTED_ROWS[name]:]!r}"
            )
        raise RuntimeError(
            f"{name}: expected {EXPECTED_ROWS[name]} constituents, got {len(symbols)}"
        )

    if len(set(symbols)) != len(symbols):
        raise RuntimeError(f"{name}: duplicate symbols detected")

    manifest["sources"][name] = {
        "url": url,
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "bytes": len(raw),
        "rows": len(symbols),
        "sha256": sha256(raw),
        "columns": header,
    }

if "NIFTY500" in manifest["sources"]:
    n500_path = OUT / "NIFTY500.csv"
    n500_text = n500_path.read_text(encoding="utf-8-sig")
    n500_rows = list(csv.reader(io.StringIO(n500_text)))
    n500_header = n500_rows[0]
    n500_col = next(i for i, h in enumerate(n500_header) if h.strip().lower() == "symbol")
    n500_symbols = {r[n500_col].strip() for r in n500_rows[1:] if n500_col < len(r) and r[n500_col].strip()}
    sc_path = OUT / "NIFTYSMALLCAP250.csv"
    sc_text = sc_path.read_text(encoding="utf-8-sig")
    sc_rows = list(csv.reader(io.StringIO(sc_text)))
    sc_header = sc_rows[0]
    sc_col = next(i for i, h in enumerate(sc_header) if h.strip().lower() == "symbol")
    sc_symbols = [r[sc_col].strip() for r in sc_rows[1:] if sc_col < len(r) and r[sc_col].strip()]
    excess = sorted(set(sc_symbols) - n500_symbols)
    missing_from_sc = sorted(n500_symbols - set(sc_symbols))
    manifest["smallcap250_parent_crosscheck"] = {
        "smallcap_raw_rows": len(sc_symbols),
        "nifty500_rows": len(n500_symbols),
        "smallcap_symbols_not_in_nifty500": excess,
        "nifty500_symbols_not_in_smallcap_raw": missing_from_sc,
        "status": "PASS" if len(sc_symbols) == 250 and not excess else "REVIEW",
    }

(OUT / "manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print(json.dumps(manifest, indent=2))
