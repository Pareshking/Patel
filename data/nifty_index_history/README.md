# Nifty constituent history — reconciled point-in-time database

## Scope

Primary history: 2024-01-01 through 2026-10-02 for Nifty 50, Nifty Next 50, Nifty Midcap 150, Nifty Smallcap 250 and Nifty Microcap 250.
Extended history: maximum practical coverage from the pinned upstream dataset: four broad indices from 2014-01-01 and Nifty Microcap 250 from 2021-10-01.

## Source hierarchy

1. Frozen official Oct-02-2026 Nifty/NSE constituent snapshots are the canonical anchor under anchors/2026-10-02/.
2. A pinned yurukatsu/nse-historical-membership commit is the first-pass PIT reconstruction source.
3. Original NSE/Nifty press releases are authoritative for official interim/corporate-action bridges and the Sep-30-2026 scheduled rebalance.
4. floyds1995/Auto-Index-Constituents-Tracker and BKKB20/nse-index-history are independent cross-check references, not canonical replacements.

## Canonicalization

Every symbol whose ticker starts with DUMMY (case-insensitive) is excluded from canonical membership. The exact official raw snapshots are frozen separately so the underlying source response remains auditable.

## Main artifacts

- nifty_membership_events_2024_2026.csv — dated membership events with provenance.
- nifty_membership_pit_2024_2026.csv — half-open PIT intervals for the primary window.
- nifty_membership_pit_extended.csv — extended PIT intervals.
- sources.json — pinned source commits and authoritative/cross-check URLs.
- validation_report.json — anchor, reconciliation and cross-check results.
- official_rebalance_counts.csv — final Sep-30-2026 reconciliation counts.
- crosscheck_floyd.csv — Oct-01-2026 independent snapshot comparison for the four indices available in Floyd.
- anchors/2026-10-02/ — immutable raw and canonical Oct-02-2026 anchor files.

## Key validation

- Canonical anchor counts replay exactly to 50 / 50 / 150 / 250 / 250 after DUMMY exclusion.
- Sep-30-2026 reconciliation counts are +1/-1, +5/-5, +13/-13, +33/-33 and +59/-59 respectively.
- Floyd Oct-01-2026 snapshots match the official Oct-02 anchor for Nifty 50, Next 50, Midcap 150 and Smallcap 250.
- One inferred duplicate event (GSPL on 2026-03-31) was removed because the symbol was already active until an official 2026-05-12 closure.

## Explicit unresolved item

Nifty Smallcap 250 has a provisional 2026-05-31 checkpoint: MOTHERSON out, CIEINDIA and MSUMI in. Floyd establishes the composition by that date, but the exact NSE effective date was not resolved in this pass. It is marked provisional rather than silently treated as authoritative.

HEG -> HEGAM is recorded as a symbol-change event effective 2026-09-22 using the NSE symbol-change archive mirrored by Floyd.

## Regeneration

Run python scripts/build_nifty_membership_history.py to rebuild the generated event/PIT outputs from the pinned source and frozen anchor.
Run python scripts/validate_nifty_membership_history.py to verify counts, DUMMY exclusion and final anchor replay.

## Attribution

The pinned upstream yurukatsu membership data repository identifies its data license as CC BY 4.0. Attribution and source commit are retained in sources.json.