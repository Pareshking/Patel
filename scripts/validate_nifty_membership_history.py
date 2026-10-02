#!/usr/bin/env python3
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'nifty_index_history'
ANCHOR = DATA / 'anchors' / '2026-10-02' / 'canonical'
FILES = {'Nifty 50':'Nifty_50.csv','Nifty Next 50':'Nifty_Next_50.csv','Nifty Midcap 150':'Nifty_Midcap_150.csv','Nifty Smallcap 250':'Nifty_Smallcap_250.csv','Nifty Microcap 250':'Nifty_Microcap_250.csv'}
EXPECTED = {'Nifty 50':50,'Nifty Next 50':50,'Nifty Midcap 150':150,'Nifty Smallcap 250':250,'Nifty Microcap 250':250}
SEPT30 = {'Nifty 50':(1,1),'Nifty Next 50':(5,5),'Nifty Midcap 150':(13,13),'Nifty Smallcap 250':(33,33),'Nifty Microcap 250':(59,59)}

def clean(s): return (s or '').strip().upper()
def read_csv(path):
    with path.open(encoding='utf-8', newline='') as f: return list(csv.DictReader(f))

def main():
    anchor = {}
    for idx, filename in FILES.items():
        rows = read_csv(ANCHOR / filename)
        symbols = {clean(r['Symbol']) for r in rows if clean(r['Symbol']) and not clean(r['Symbol']).startswith('DUMMY')}
        assert len(symbols) == EXPECTED[idx], f'{idx}: anchor count {len(symbols)} != {EXPECTED[idx]}'
        anchor[idx] = symbols
    events = read_csv(DATA / 'nifty_membership_events_2024_2026.csv')
    assert all(not clean(r['symbol']).startswith('DUMMY') for r in events)
    by = {}
    for r in events:
        if r['effective_date'] == '2026-09-30' and r['source_tier'] == 'official_primary':
            key = r['index']
            by.setdefault(key, [0,0])
            if r['action'] == 'ADD': by[key][0] += 1
            if r['action'] == 'REMOVE': by[key][1] += 1
    for idx, expected in SEPT30.items(): assert tuple(by.get(idx, [0,0])) == expected, (idx, by.get(idx))
    pit = read_csv(DATA / 'nifty_membership_pit_2024_2026.csv')
    assert all(not clean(r['symbol']).startswith('DUMMY') for r in pit)
    for idx, expected in EXPECTED.items():
        active = {r['symbol'] for r in pit if r['index'] == idx and r['valid_from'] <= '2026-10-02' and (not r['valid_to'] or r['valid_to'] > '2026-10-02')}
        assert active == anchor[idx], f'{idx}: PIT replay does not match frozen anchor'
    extended = read_csv(DATA / 'nifty_membership_pit_extended.csv')
    assert all(not clean(r['symbol']).startswith('DUMMY') for r in extended)
    print('PASS: anchors, DUMMY exclusion, Sep-30 reconciliation and PIT replay all verified.')

if __name__ == '__main__': main()