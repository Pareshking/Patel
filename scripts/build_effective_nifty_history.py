from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "nifty_index_history" / "max_history"
CUTOFF = "2025-09-30"
ANCHOR_DATE = "2026-10-02"
TARGETS = {"NIFTY50": 50, "NIFTYNEXT50": 50, "NIFTYMIDCAP150": 150, "NIFTYSMALLCAP250": 250, "NIFTYMICROCAP250": 250}
RAW = "yurukatsu_target_intervals.csv"
EVENTS = "official_2026_interim_events.csv"
ANCHOR = "official_anchor_2026-10-02.csv"
OUTPUT = "effective_intervals_2026-10-02.csv"
EVENT_AUDIT = "event_application_audit.csv"
CHECKPOINT_2025 = "candidate_checkpoint_2025-09-30.csv"
CHECKPOINT_2026 = "candidate_checkpoint_2026-03-30.csv"


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, rows: list[dict[str, str]], fields: list[str]) -> None:
    with (ROOT / name).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def active(row: dict[str, str], day: str) -> bool:
    return row["valid_from"] <= day and (not row["valid_to"] or row["valid_to"] > day)


def dummy(row: dict[str, str]) -> bool:
    return row["symbol"].strip().upper().startswith("DUMMY") or row.get("canonical_effect") == "DUMMY"


def main() -> None:
    raw, events, anchor = read_csv(RAW), read_csv(EVENTS), read_csv(ANCHOR)
    state: dict[str, set[str]] = defaultdict(set)
    for row in anchor:
        state[row["index"]].add(row["symbol"].strip().upper())
    assert Counter(row["index"] for row in anchor) == Counter(TARGETS)
    assert not any(dummy(row) for row in anchor)

    # Reconstruct the next older half-year boundary backwards from the official current anchor.
    reverse_events = [e for e in events if e["effective_date"] > CUTOFF and not dummy(e)]
    reverse_events.sort(key=lambda e: (0 if e["action"] == "ADD" else 1, e["symbol"]))
    reverse_events.sort(key=lambda e: (
        date.fromisoformat(e["effective_date"]).toordinal(),
        date.fromisoformat(e["event_announcement_date"]).toordinal(),
    ), reverse=True)
    for event in reverse_events:
        members, symbol = state[event["index"]], event["symbol"].strip().upper()
        if event["action"] == "ADD":
            assert symbol in members, f"cannot reverse ADD absent from state: {event}"
            members.remove(symbol)
        else:
            assert symbol not in members, f"cannot reverse REMOVE already active: {event}"
            members.add(symbol)
    boundary_counts = {i: len(state[i]) for i in TARGETS}
    assert boundary_counts == TARGETS, f"boundary cardinality mismatch: {boundary_counts}"

    # Validate this boundary against the official September 2025 review deltas.
    review_2025 = [e for e in events if e["event_announcement_date"] == "2025-08-22"
                   and e["effective_date"] == CUTOFF and not dummy(e)]
    expected_review_counts = {
        ("NIFTY50", "ADD"): 2, ("NIFTY50", "REMOVE"): 2,
        ("NIFTYNEXT50", "ADD"): 4, ("NIFTYNEXT50", "REMOVE"): 4,
        ("NIFTYMIDCAP150", "ADD"): 13, ("NIFTYMIDCAP150", "REMOVE"): 13,
        ("NIFTYSMALLCAP250", "ADD"): 23, ("NIFTYSMALLCAP250", "REMOVE"): 23,
        ("NIFTYMICROCAP250", "ADD"): 39, ("NIFTYMICROCAP250", "REMOVE"): 39,
    }
    review_counts = Counter((e["index"], e["action"]) for e in review_2025)
    assert review_counts == expected_review_counts, f"September 2025 official review coverage mismatch: {review_counts}"
    for event in review_2025:
        members = state[event["index"]]
        symbol = event["symbol"].strip().upper()
        if event["action"] == "ADD":
            assert symbol in members, f"official September 2025 addition absent at boundary: {event}"
        else:
            assert symbol not in members, f"official September 2025 removal still active at boundary: {event}"

    checkpoint_rows = [
        {"index": index, "symbol": symbol, "as_of_date": CUTOFF,
         "reconstruction_method": "reverse official event chain from official 2026-10-02 anchor",
         "status": "RECONSTRUCTED_OFFICIAL_REVIEW_DELTA_VALIDATED",
         "source_file": EVENTS}
        for index, symbols in sorted(state.items()) for symbol in sorted(symbols)
    ]
    write_csv(CHECKPOINT_2025, checkpoint_rows, list(checkpoint_rows[0]))

    # Keep the upstream history only before the boundary. Force the boundary
    # active set to the reverse replay, then apply official events forward.
    intervals = [dict(r) for r in raw if r["valid_from"] <= CUTOFF]
    for pos in range(len(intervals) - 1, -1, -1):
        row = intervals[pos]
        if not active(row, CUTOFF):
            continue
        symbol = row["symbol"].strip().upper()
        if symbol in state[row["index"]]:
            row["valid_to"] = ""
        elif row["valid_from"] == CUTOFF:
            intervals.pop(pos)
        else:
            row["valid_to"] = CUTOFF

    for index, symbols in state.items():
        for symbol in symbols:
            if not any(r["index"] == index and r["symbol"].strip().upper() == symbol and active(r, CUTOFF)
                       for r in intervals):
                intervals.append({
                    "index": index,
                    "index_name": next((r["index_name"] for r in raw if r["index"] == index), index),
                    "symbol": symbol, "valid_from": CUTOFF, "valid_to": "", "weightage": "",
                    "source": "official_event_replay_boundary", "source_url": "",
                    "notes": "Membership as of 2026-03-30 reconstructed backward from official 2026-10-02 anchor through official 2026 events; boundary start does not imply first-ever inclusion",
                    "upstream_repo": "", "upstream_file": "", "upstream_commit": "",
                    "record_class": "official_event_replay_boundary",
                })

    audit_rows = []
    ordered_events = sorted(events, key=lambda e: (e["effective_date"], e["event_announcement_date"],
                                                   0 if e["action"] == "REMOVE" else 1, e["symbol"]))
    for event in ordered_events:
        symbol = event["symbol"].strip().upper()
        if dummy(event):
            result, reason = "NOOP_DUMMY_EXCLUDED", "DUMMY* placeholder excluded from canonical membership"
        elif event["effective_date"] <= CUTOFF:
            result, reason = "INCLUDED_IN_BOUNDARY_STATE", "Effective on/before reconstructed boundary; represented in boundary state"
        else:
            current = [r for r in intervals if r["index"] == event["index"]
                       and r["symbol"].strip().upper() == symbol and active(r, event["effective_date"])]
            if event["action"] == "REMOVE":
                if current:
                    for row in current:
                        row["valid_to"] = event["effective_date"]
                    result, reason = "APPLIED_REMOVE", "Closed active interval at official effective date"
                else:
                    result, reason = "NOOP_REMOVE_NOT_ACTIVE", "No active interval at effective date"
            elif current:
                result, reason = "NOOP_ADD_ALREADY_ACTIVE", "Symbol already active at effective date"
            else:
                intervals.append({
                    "index": event["index"],
                    "index_name": next((r["index_name"] for r in raw if r["index"] == event["index"]), event["index"]),
                    "symbol": symbol, "valid_from": event["effective_date"], "valid_to": "", "weightage": "",
                    "source": event["source_type"], "source_url": event["source_url"],
                    "notes": "Official event replay: " + event["notes"],
                    "upstream_repo": "", "upstream_file": "", "upstream_commit": "",
                    "record_class": "official_event_replay",
                })
                result, reason = "APPLIED_ADD", "Opened interval at official effective date"
        audit_rows.append({**event, "application_result": result, "application_reason": reason})

    intervals.sort(key=lambda r: (r["index"], r["symbol"], r["valid_from"]))
    write_csv(OUTPUT, intervals, list(raw[0]))
    write_csv(EVENT_AUDIT, audit_rows, list(audit_rows[0]))
    checkpoint_2026 = [
        {"index": index, "symbol": symbol, "as_of_date": "2026-03-30",
         "reconstruction_method": "reverse official event chain from official 2026-10-02 anchor",
         "status": "RECONSTRUCTED_OFFICIAL_REVIEW_DELTA_VALIDATED",
         "source_file": EVENTS}
        for index, symbol in sorted({(r["index"], r["symbol"].strip().upper()) for r in intervals
                                     if active(r, "2026-03-30")})
    ]
    write_csv(CHECKPOINT_2026, checkpoint_2026, list(checkpoint_2026[0]))

    actual_anchor = {(r["index"], r["symbol"].strip().upper()) for r in intervals if active(r, ANCHOR_DATE)}
    expected_anchor = {(r["index"], r["symbol"].strip().upper()) for r in anchor}
    assert actual_anchor == expected_anchor, f"anchor mismatch: missing={expected_anchor-actual_anchor}, extra={actual_anchor-expected_anchor}"
    groups: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for row in intervals:
        assert not dummy(row), f"DUMMY* in canonical intervals: {row}"
        groups[(row["index"], row["symbol"])].append((row["valid_from"], row["valid_to"] or "9999-12-31"))
    for key, ranges in groups.items():
        ranges.sort()
        for left, right in zip(ranges, ranges[1:]):
            assert left[1] < right[0], f"overlap for {key}: {left}, {right}"
    print("EFFECTIVE_INTERVAL_ROWS", len(intervals))
    print("BOUNDARY_COUNTS", boundary_counts)
    print("EVENT_APPLICATION_RESULTS", dict(Counter(r["application_result"] for r in audit_rows)))
    print("BUILD PASS: Block 02 boundary reconstructed backward from official anchor; Block 01 regenerated")


if __name__ == "__main__":
    main()
