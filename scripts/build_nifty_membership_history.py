#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nifty_index_history"
ANCHOR = DATA / "anchors" / "2026-10-02" / "canonical"
YURU_URL = "https://raw.githubusercontent.com/yurukatsu/nse-historical-membership/6695e8468c42ed5222265a5078a53a298cec88f7/index_history/data/index_membership_history.csv"
INDEXES = ["Nifty 50", "Nifty Next 50", "Nifty Midcap 150", "Nifty Smallcap 250", "Nifty Microcap 250"]
EXPECTED = {"Nifty 50": (1, 1), "Nifty Next 50": (5, 5), "Nifty Midcap 150": (13, 13), "Nifty Smallcap 250": (33, 33), "Nifty Microcap 250": (59, 59)}
FILES = {"Nifty 50": "Nifty_50.csv", "Nifty Next 50": "Nifty_Next_50.csv", "Nifty Midcap 150": "Nifty_Midcap_150.csv", "Nifty Smallcap 250": "Nifty_Smallcap_250.csv", "Nifty Microcap 250": "Nifty_Microcap_250.csv"}
PATCHES = [
    ("Nifty Smallcap 250", "2026-05-31", "REMOVE", "MOTHERSON", "provisional_independent_checkpoint", "https://github.com/floyds1995/Auto-Index-Constituents-Tracker/blob/main/NSE/Nifty_Smallcap_250.csv", "floyd_snapshot", "Exact NSE effective date unresolved."),
    ("Nifty Smallcap 250", "2026-05-31", "ADD", "CIEINDIA", "provisional_independent_checkpoint", "https://github.com/floyds1995/Auto-Index-Constituents-Tracker/blob/main/NSE/Nifty_Smallcap_250.csv", "floyd_snapshot", "Exact NSE effective date unresolved."),
    ("Nifty Smallcap 250", "2026-05-31", "ADD", "MSUMI", "provisional_independent_checkpoint", "https://github.com/floyds1995/Auto-Index-Constituents-Tracker/blob/main/NSE/Nifty_Smallcap_250.csv", "floyd_snapshot", "Exact NSE effective date unresolved."),
    ("Nifty Next 50", "2026-06-15", "ADD", "VAML", "official_corporate_action_conversion", "https://www.niftyindices.com/Press_Release/ind_prs23042026.pdf", "press_release", "Canonical conversion from DUMMYVEDL1 after listing."),
    ("Nifty Next 50", "2026-06-15", "ADD", "VEDPOWER", "official_corporate_action_conversion", "https://www.niftyindices.com/Press_Release/ind_prs23042026.pdf", "press_release", "Canonical conversion from DUMMYVEDL2 after listing."),
    ("Nifty Next 50", "2026-06-15", "ADD", "VOGL", "official_corporate_action_conversion", "https://www.niftyindices.com/Press_Release/ind_prs23042026.pdf", "press_release", "Canonical conversion from DUMMYVEDL3 after listing."),
    ("Nifty Next 50", "2026-06-15", "ADD", "VISL", "official_corporate_action_conversion", "https://www.niftyindices.com/Press_Release/ind_prs23042026.pdf", "press_release", "Canonical conversion from DUMMYVEDL4 after listing."),
    ("Nifty Next 50", "2026-06-19", "REMOVE", "VEDPOWER", "official_interim", "https://www.niftyindices.com/Press_Release/ind_prs17062026.pdf", "press_release", "Official exclusion."),
    ("Nifty Next 50", "2026-06-19", "REMOVE", "VISL", "official_interim", "https://www.niftyindices.com/Press_Release/ind_prs17062026.pdf", "press_release", "Official exclusion."),
    ("Nifty Next 50", "2026-06-23", "REMOVE", "VAML", "official_interim", "https://www.niftyindices.com/Press_Release/ind_prs19062026.pdf", "press_release", "Official exclusion."),
    ("Nifty Next 50", "2026-06-24", "REMOVE", "VOGL", "official_interim", "https://www.niftyindices.com/Press_Release/ind_prs22062026.pdf", "press_release", "Official exclusion."),
    ("Nifty Microcap 250", "2026-07-03", "ADD", "AGL", "official_corporate_action_conversion", "https://www.niftyindices.com/Press_Release/ind_prs07112025.pdf", "press_release", "Canonical conversion from DUMMYALCAR after listing."),
    ("Nifty Smallcap 250", "2026-07-17", "REMOVE", "JBCHEPHARM", "official_interim", "https://www.niftyindices.com/Press_Release/ind_prs13072026_1.pdf", "press_release", "Official replacement."),
    ("Nifty Smallcap 250", "2026-07-17", "ADD", "PFOCUS", "official_interim", "https://www.niftyindices.com/Press_Release/ind_prs13072026_1.pdf", "press_release", "Official replacement."),
    ("Nifty Microcap 250", "2026-07-17", "REMOVE", "PFOCUS", "official_interim", "https://www.niftyindices.com/Press_Release/ind_prs13072026_1.pdf", "press_release", "Official replacement."),
    ("Nifty Microcap 250", "2026-07-17", "ADD", "GRINDWELL", "official_interim", "https://www.niftyindices.com/Press_Release/ind_prs13072026_1.pdf", "press_release", "Official replacement."),
    ("Nifty Microcap 250", "2026-07-22", "REMOVE", "AGL", "official_interim", "https://www.niftyindices.com/Press_Release/ind_prs20072026.pdf", "press_release", "Official exclusion."),
    ("Nifty Smallcap 250", "2026-09-22", "REMOVE", "HEG", "independent_symbol_change_crosscheck", "https://raw.githubusercontent.com/floyds1995/Auto-Index-Constituents-Tracker/main/NSE/RawData/symbolchange.csv", "symbolchange", "HEG -> HEGAM effective 2026-09-22."),
    ("Nifty Smallcap 250", "2026-09-22", "ADD", "HEGAM", "independent_symbol_change_crosscheck", "https://raw.githubusercontent.com/floyds1995/Auto-Index-Constituents-Tracker/main/NSE/RawData/symbolchange.csv", "symbolchange", "HEG -> HEGAM effective 2026-09-22."),
]

def clean(s: str) -> str:
    return (s or "").strip().upper()

def load_csv(text: str):
    return list(csv.DictReader(io.StringIO(text)))

def quote_csv(value):
    s = str(value if value is not None else "")
    return '"' + s.replace('"', '""') + '"' if any(c in s for c in ',\n\r"') else s

def write_csv(path: Path, headers, rows):
    body = [','.join(headers)]
    body.extend(','.join(quote_csv(v) for v in row) for row in rows)
    path.write_text('\n'.join(body) + '\n', encoding='utf-8')

def read_anchor(path: Path):
    rows = load_csv(path.read_text(encoding='utf-8'))
    return {clean(r['Symbol']) for r in rows if clean(r['Symbol']) and not clean(r['Symbol']).startswith('DUMMY')}

def associated_pr(notes: str):
    import re
    m = re.search(r'ind_prs[0-9_]+\.pdf', notes or '', re.I)
    return 'https://www.niftyindices.com/Press_Release/' + m.group(0) if m else ''

def build(start_date: str, source_rows, anchors):
    seeds = {idx: {} for idx in INDEXES}
    source_events = []
    for r in source_rows:
        idx = r['index_name']
        sym = clean(r['symbol'])
        vf = r.get('valid_from') or ''
        vt = r.get('valid_to') or ''
        src = r.get('source') or ''
        url = r.get('source_url') or ''
        notes = r.get('notes') or ''
        if vf <= start_date and (not vt or vt > start_date):
            seeds[idx][sym] = {'prov': 'seed_snapshot_inferred' if src == 'snapshot_floor' else 'source_backed_interval', 'url': url or associated_pr(notes), 'src': src, 'notes': notes}
        if start_date <= vf <= '2026-05-15':
            source_events.append([idx, vf, 'ADD', sym, 'seed_snapshot_inferred' if src == 'snapshot_floor' else 'yurukatsu_event', url, src, notes])
        if start_date <= vt <= '2026-05-15':
            source_events.append([idx, vt, 'REMOVE', sym, 'seed_closure_official' if src == 'snapshot_floor' and associated_pr(notes) else 'yurukatsu_event', url or associated_pr(notes), src, notes])
    active = {idx: set(seeds[idx]) for idx in INDEXES}
    events = []
    for e in sorted(source_events, key=lambda x: (x[1], x[2], x[3])):
        idx, date, action, sym = e[0], e[1], e[2], e[3]
        if action == 'REMOVE':
            if sym in active[idx]:
                events.append(e); active[idx].remove(sym)
        elif sym not in active[idx]:
            events.append(e); active[idx].add(sym)
    for e in PATCHES:
        events.append(list(e))
        if e[2] == 'REMOVE': active[e[0]].discard(e[3])
        else: active[e[0]].add(e[3])
    for idx in INDEXES:
        missing = sorted(active[idx] - anchors[idx])
        added = sorted(anchors[idx] - active[idx])
        if (len(added), len(missing)) != EXPECTED[idx]:
            raise RuntimeError(f'{idx}: final diff +{len(added)}/-{len(missing)}')
        for sym in missing:
            events.append([idx, '2026-09-30', 'REMOVE', sym, 'official_primary', 'https://www.niftyindices.com/Press_Release/ind_prs10082026.pdf', 'press_release', 'Official Sep-30-2026 reconstitution reconciled to Oct-02 anchor.'])
        for sym in added:
            events.append([idx, '2026-09-30', 'ADD', sym, 'official_primary', 'https://www.niftyindices.com/Press_Release/ind_prs10082026.pdf', 'press_release', 'Official Sep-30-2026 reconstitution reconciled to Oct-02 anchor.'])
    opens = {idx: {} for idx in INDEXES}
    for idx in INDEXES:
        for sym, meta in seeds[idx].items():
            opens[idx][sym] = {'from': start_date, **meta}
    intervals = []
    for e in sorted(events, key=lambda x: (x[0], x[1], x[2], x[3])):
        idx, date, action, sym, prov, url, src, notes = e
        if action == 'REMOVE':
            cur = opens[idx].pop(sym, None)
            if cur:
                intervals.append([idx, sym, cur['from'], date, cur['prov'], cur['url'], cur['src'], prov, url, notes])
        elif sym not in opens[idx]:
            opens[idx][sym] = {'from': date, 'prov': prov, 'url': url, 'src': src, 'notes': notes}
    for idx in INDEXES:
        for sym, cur in opens[idx].items():
            intervals.append([idx, sym, cur['from'], '', cur['prov'], cur['url'], cur['src'], '', '', 'Active in frozen 2026-10-02 anchor.'])
    return events, intervals

def main():
    with urllib.request.urlopen(YURU_URL, timeout=60) as r:
        source_rows = load_csv(r.read().decode('utf-8'))
    source_rows = [r for r in source_rows if r['index_name'] in INDEXES and r.get('symbol') and not clean(r['symbol']).startswith('DUMMY')]
    anchors = {idx: read_anchor(ANCHOR / FILES[idx]) for idx in INDEXES}
    events, intervals = build('2024-01-01', source_rows, anchors)
    write_csv(DATA / 'nifty_membership_events_2024_2026.csv', ['index','effective_date','action','symbol','source_tier','source_url','source_source_type','notes'], events)
    write_csv(DATA / 'nifty_membership_pit_2024_2026.csv', ['index','symbol','valid_from','valid_to','start_provenance','start_source_url','start_source_type','end_provenance','end_source_url','notes'], intervals)
    print('wrote primary history:', len(events), 'events and', len(intervals), 'intervals')

if __name__ == '__main__':
    main()