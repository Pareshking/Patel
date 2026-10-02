from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "nifty_index_history" / "max_history"
TARGETS = {
    "NIFTY50": 50,
    "NIFTYNEXT50": 50,
    "NIFTYMIDCAP150": 150,
    "NIFTYSMALLCAP250": 250,
    "NIFTYMICROCAP250": 250,
}
EXPECTED_INTERVALS = {
    "NIFTY50": 83,
    "NIFTYNEXT50": 178,
    "NIFTYMIDCAP150": 442,
    "NIFTYSMALLCAP250": 886,
    "NIFTYMICROCAP250": 814,
}
EXPECTED_STARTS = {
    "NIFTY50": "2014-01-01",
    "NIFTYNEXT50": "2014-01-01",
    "NIFTYMIDCAP150": "2016-04-01",
    "NIFTYSMALLCAP250": "2016-04-01",
    "NIFTYMICROCAP250": "2019-04-01",
}


def read(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_day(value: str, *, allow_blank: bool = False) -> date | None:
    if not value and allow_blank:
        return None
    assert value, "date field must not be blank"
    return date.fromisoformat(value)


def main() -> None:
    anchor = read("official_anchor_2026-10-02.csv")
    anchor_counts = Counter(row["index"] for row in anchor)
    print("ANCHOR", anchor_counts)
    assert anchor_counts == Counter(TARGETS), f"unexpected anchor counts: {anchor_counts}"
    assert not any(row["symbol"].strip().upper().startswith("DUMMY") for row in anchor)
    anchor_keys = [(row["index"], row["symbol"].strip().upper()) for row in anchor]
    assert len(anchor_keys) == len(set(anchor_keys)), "duplicate index/symbol in canonical anchor"

    intervals = read("yurukatsu_target_intervals.csv")
    interval_counts = Counter(row["index"] for row in intervals)
    print("INTERVALS", interval_counts)
    assert interval_counts == Counter(EXPECTED_INTERVALS), f"unexpected PIT interval counts: {interval_counts}"
    assert len(intervals) == 2403
    assert not any(row["symbol"].strip().upper().startswith("DUMMY") for row in intervals), (
        "DUMMY* placeholders must not appear in canonical PIT intervals"
    )

    interval_keys: set[tuple[str, str, str]] = set()
    grouped: dict[tuple[str, str], list[tuple[date, date | None]]] = defaultdict(list)
    earliest: dict[str, date] = {}
    for row in intervals:
        index = row["index"]
        symbol = row["symbol"].strip().upper()
        start = parse_day(row["valid_from"])
        end = parse_day(row["valid_to"], allow_blank=True)
        assert start is not None
        assert index in TARGETS, f"unknown index in PIT interval: {index}"
        assert end is None or end >= start, f"invalid interval for {index}/{symbol}: {start} -> {end}"
        key = (index, symbol, start.isoformat())
        assert key not in interval_keys, f"duplicate interval key: {key}"
        interval_keys.add(key)
        grouped[(index, symbol)].append((start, end))
        earliest[index] = min(earliest.get(index, start), start)

    for (index, symbol), ranges in grouped.items():
        ranges.sort(key=lambda item: item[0])
        for previous, current in zip(ranges, ranges[1:]):
            previous_end = previous[1]
            assert previous_end is not None and previous_end < current[0], (
                f"overlapping or open-ended intervals for {index}/{symbol}: {previous} then {current}"
            )

    # The official 2025-08-22 review makes MSUMI, not MOTHERSON, the Smallcap 250 member from 2025-09-30.
    smallcap_intervals = [row for row in intervals if row["index"] == "NIFTYSMALLCAP250"]
    assert any(row["symbol"] == "MSUMI" and row["valid_from"] == "2025-09-30" for row in smallcap_intervals)
    assert not any(row["symbol"] == "MOTHERSON" and row["valid_from"] == "2025-09-30" for row in smallcap_intervals)
    # HEG's continuing security changes symbol to HEGAM; DUMMYHEG is a separate demerger placeholder.
    heg = next(row for row in smallcap_intervals if row["symbol"] == "HEG" and row["valid_from"] == "2020-06-26")
    assert heg["valid_to"] == "2026-09-04"
    assert any(row["symbol"] == "HEGAM" and row["valid_from"] == "2026-09-07" and not row["valid_to"] for row in smallcap_intervals)

    observed_starts = {index: day.isoformat() for index, day in earliest.items()}
    print("EARLIEST_INTERVAL_STARTS", observed_starts)
    assert observed_starts == EXPECTED_STARTS, f"unexpected maximum-history starts: {observed_starts}"

    events = read("official_2026_interim_events.csv")
    assert len(events) == 250, f"expected 250 official override/event rows, got {len(events)}"
    for row in events:
        assert row["index"] in TARGETS, f"unknown index in official events: {row['index']}"
        parse_day(row["event_announcement_date"])
        parse_day(row["effective_date"])
        assert row["action"] in {"ADD", "REMOVE"}, f"unexpected event action: {row['action']}"
        assert row["source_url"].startswith("https://"), f"missing source URL: {row}"
        assert row["confidence"] == "OFFICIAL_PRIMARY", f"non-primary row in official event ledger: {row}"

    dummies = [row for row in events if row["symbol"].strip().upper().startswith("DUMMY")]
    print("DUMMY_EVENTS", Counter(row["index"] for row in dummies), "count", len(dummies))
    assert len(dummies) == 10, f"expected to retain 10 DUMMY* event records, got {len(dummies)}"
    assert all(row["canonical_effect"] == "DUMMY" for row in dummies)
    print("OFFICIAL_EVENTS", Counter((row["index"], row["effective_date"], row["action"]) for row in events))

    # The raw third-party intervals are evidence, not the final canonical history.
    # Apply official 2026 changes in the saved effective artifact and prove it ends
    # at the exact official anchor, not merely at the right row counts.
    effective = read("effective_intervals_2026-10-02.csv")
    effective_counts = Counter(row["index"] for row in effective)
    print("EFFECTIVE_INTERVALS", effective_counts)
    assert len(effective) == 2521, f"unexpected effective interval rows: {len(effective)}"
    assert not any(row["symbol"].strip().upper().startswith("DUMMY") for row in effective)
    effective_grouped: dict[tuple[str, str], list[tuple[date, date | None]]] = defaultdict(list)
    for row in effective:
        index = row["index"]
        symbol = row["symbol"].strip().upper()
        start = parse_day(row["valid_from"])
        end = parse_day(row["valid_to"], allow_blank=True)
        assert index in TARGETS, f"unknown effective index: {index}"
        assert start is not None and (end is None or end >= start), f"invalid effective interval: {row}"
        effective_grouped[(index, symbol)].append((start, end))
    for key, ranges in effective_grouped.items():
        ranges.sort(key=lambda item: item[0])
        for previous, current in zip(ranges, ranges[1:]):
            assert previous[1] is not None and previous[1] < current[0], (
                f"overlapping effective intervals for {key}: {previous} then {current}"
            )

    def members_on(rows: list[dict[str, str]], checkpoint: str) -> set[tuple[str, str]]:
        return {
            (row["index"], row["symbol"].strip().upper())
            for row in rows
            if row["valid_from"] <= checkpoint and (not row["valid_to"] or row["valid_to"] > checkpoint)
        }

    anchor_set = set(anchor_keys)
    effective_anchor_set = members_on(effective, "2026-10-02")
    assert effective_anchor_set == anchor_set, (
        f"effective history does not exactly match official anchor; "
        f"missing={sorted(anchor_set - effective_anchor_set)[:20]}, "
        f"extra={sorted(effective_anchor_set - anchor_set)[:20]}"
    )
    for checkpoint in ("2024-09-30", "2024-10-01", "2025-03-28", "2025-09-30", "2026-03-30", "2026-09-30", "2026-10-02"):
        counts = Counter(index for index, _ in members_on(effective, checkpoint))
        print("CHECKPOINT_COUNTS", checkpoint, {index: counts[index] for index in TARGETS})
        if checkpoint == "2026-03-30":
            assert counts == Counter(TARGETS), f"Block 01 boundary cardinality mismatch: {counts}"

    application_audit = read("event_application_audit.csv")
    assert len(application_audit) == len(events) == 246
    application_counts = Counter(row["application_result"] for row in application_audit)
    expected_application_counts = Counter({
        "APPLIED_ADD": 120,
        "APPLIED_REMOVE": 120,
        "NOOP_DUMMY_EXCLUDED": 10,
        "NOOP_REMOVE_NOT_ACTIVE": 0,
        "NOOP_ADD_ALREADY_ACTIVE": 0,
    })
    print("EVENT_APPLICATION_RESULTS", application_counts)
    assert application_counts == expected_application_counts, (
        f"event application ledger drift: {application_counts}"
    )
    assert all(row["source_url"].startswith("https://") for row in application_audit)
    assert all(row["application_result"] for row in application_audit)

    print("AUDIT PASS: source intervals, effective interval integrity, exact current anchor identity, event application audit, provenance, and DUMMY* exclusion")

if __name__ == "__main__":
    main()
