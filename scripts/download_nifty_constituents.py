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

# Official NSE archive endpoints behind the Nifty Indices constituent downloads.
# The Microcap filename intentionally contains the underscore before list.csv.
SOURCES = {
    "NIFTY50": "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
    "NIFTYNEXT50": "https://nsearchives.nseindia.com/content/indices/ind_niftynext50list.csv",
    "NIFTYMIDCAP150": "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
    "NIFTYSMALLCAP250": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
    "NIFTYMICROCAP250": "https://nsearchives.nseindia.com/content/indices/ind_niftymicrocap250_list.csv",
    "NIFTY500": "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv",
}

EXPECTED_ROWS = {
    "NIFTY50": 50,
    "NIFTYNEXT50": 50,
    "NIFTYMIDCAP150": 150,
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


def fetch_csv(name: str, url: str) -> tuple[bytes, list[str], list[list[str]], dict]:
    response = session.get(url, timeout=60, allow_redirects=True)
    response.raise_for_status()
    raw = response.content

    if not raw.strip():
        raise RuntimeError(f"{name}: empty response")

    text = raw.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        preview = text[:500].replace("\n", " ")
        raise RuntimeError(
            f"{name}: response is not a usable CSV; content_type="
            f"{response.headers.get('content-type')}; preview={preview!r}"
        )

    header = rows[0]
    symbol_col = next(
        (i for i, h in enumerate(header) if h.strip().lower() == "symbol"),
        None,
    )
    if symbol_col is None:
        preview = text[:500].replace("\n", " ")
        raise RuntimeError(
            f"{name}: no SYMBOL column; content_type="
            f"{response.headers.get('content-type')}; header={header!r}; "
            f"preview={preview!r}"
        )

    data_rows = [r for r in rows[1:] if any(cell.strip() for cell in r)]
    symbols = [
        r[symbol_col].strip()
        for r in data_rows
        if symbol_col < len(r) and r[symbol_col].strip()
    ]

    meta = {
        "url": url,
        "final_url": response.url,
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "bytes": len(raw),
        "rows": len(symbols),
        "sha256": sha256(raw),
        "columns": header,
    }
    return raw, symbols, data_rows, meta


downloaded: dict[str, tuple[bytes, list[str], list[list[str]], dict]] = {}

for name, url in SOURCES.items():
    raw, symbols, data_rows, meta = fetch_csv(name, url)
    downloaded[name] = (raw, symbols, data_rows, meta)
    (OUT / f"{name}.csv").write_bytes(raw)

    print(
        f"{name}: http={meta['http_status']} final_url={meta['final_url']} "
        f"content_type={meta['content_type']} bytes={meta['bytes']} "
        f"parsed_rows={len(symbols)}"
    )

# Validate exact sizes except Smallcap 250. The raw source snapshot is retained
# because the official download may contain an extra appended row.
for name, (_, symbols, data_rows, meta) in downloaded.items():
    expected = EXPECTED_ROWS[name]
    if name == "NIFTYSMALLCAP250":
        if len(symbols) < expected:
            raise RuntimeError(
                f"{name}: fewer than {expected} constituents: {len(symbols)}"
            )
    elif len(symbols) != expected:
        extra = data_rows[expected:] if len(data_rows) > expected else []
        raise RuntimeError(
            f"{name}: expected {expected} constituents, got {len(symbols)}; "
            f"extra_candidate_rows={extra!r}"
        )

    if len(set(symbols)) != len(symbols):
        raise RuntimeError(f"{name}: duplicate symbols detected")

    manifest["sources"][name] = meta

# Cross-check Smallcap 250 against the parent Nifty 500 universe.
n500_symbols = set(downloaded["NIFTY500"][1])
sc_raw, sc_symbols, sc_rows, sc_meta = downloaded["NIFTYSMALLCAP250"]

# SYMBOL is the third field in these official files, but locate it robustly.
sc_header = sc_rows[0]
sc_col = next(
    i for i, h in enumerate(sc_header) if h.strip().lower() == "symbol"
)
excess = sorted(set(sc_symbols) - n500_symbols)
intersection = [
    row for row in sc_rows[1:]
    if sc_col < len(row) and row[sc_col].strip() in n500_symbols
]

smallcap_status = "REVIEW"
if len(sc_symbols) == 250 and not excess:
    smallcap_status = "PASS"
elif len(sc_symbols) == 251 and len(excess) == 1 and len(intersection) == 250:
    canonical_path = OUT / "NIFTYSMALLCAP250_canonical.csv"
    canonical_path.write_text(
        ",".join(sc_header) + "\n"
        + "\n".join(",".join(r) for r in intersection) + "\n",
        encoding="utf-8",
    )
    smallcap_status = "RAW_251_CANONICAL_250"

manifest["smallcap250_parent_crosscheck"] = {
    "smallcap_raw_rows": len(sc_symbols),
    "nifty500_rows": len(n500_symbols),
    "smallcap_symbols_not_in_nifty500": excess,
    "smallcap_intersection_rows": len(intersection),
    "status": smallcap_status,
}

if smallcap_status == "REVIEW":
    raise RuntimeError(
        "Smallcap 250 cross-check requires review: "
        + json.dumps(manifest["smallcap250_parent_crosscheck"])
    )

(OUT / "manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print(json.dumps(manifest, indent=2))
