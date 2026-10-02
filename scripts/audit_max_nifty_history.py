from __future__ import annotations
import csv
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"data"/"nifty_index_history"/"max_history"
TARGETS={"NIFTY50":50,"NIFTYNEXT50":50,"NIFTYMIDCAP150":150,"NIFTYSMALLCAP250":250,"NIFTYMICROCAP250":250}

def read(name):
    with (ROOT/name).open(encoding="utf-8") as f: return list(csv.DictReader(f))

def main():
    anchor=read("official_anchor_2026-10-02.csv")
    print("ANCHOR", Counter(r["index"] for r in anchor))
    assert not any(r["symbol"].upper().startswith("DUMMY") for r in anchor)
    for idx,want in TARGETS.items(): assert sum(r["index"]==idx for r in anchor)==want
    intervals=read("yurukatsu_target_intervals.csv")
    print("INTERVALS", Counter(r["index"] for r in intervals))
    dummies=[r for r in read("official_2026_interim_events.csv") if r["symbol"].upper().startswith("DUMMY")]
    print("DUMMY_EVENTS", Counter(r["index"] for r in dummies), "count", len(dummies))
    events=read("official_2026_interim_events.csv")
    print("OFFICIAL_EVENTS", Counter((r["index"],r["effective_date"],r["action"]) for r in events))

if __name__=="__main__": main()
