# Maximum Nifty constituent history

Reconstruction anchor: **2026-10-02 official NSE/Nifty constituent snapshots**. First-pass historical source: **yurukatsu/nse-historical-membership**, pinned to upstream commit **850da8ca193b289fc7471eee28362a7a058f8c2e**. Primary authority for 2026 tail corrections: official Nifty Indices press releases. The first four indices also have independent cross-check sources in BKKB20 and floyds1995; Microcap 250 is cross-checked primarily against NSE because those trackers do not cover Microcap 250.

## Files

- `official_anchor_2026-10-02.csv`: canonical 2026-10-02 membership snapshot for the five target indices.
- `yurukatsu_target_intervals.csv`: maximum available target-index point-in-time intervals from the pinned upstream reconstruction. First four indices are retained from 2014-01-01; Microcap 250 from 2019-04-01 (its launch era). DUMMY symbols are removed from this canonical interval file.
- `yurukatsu_candidate_events.csv`: events mechanically derived only from upstream explicit-source intervals; this is candidate evidence, not an NSE-certified event ledger.
- `official_2026_interim_events.csv`: official NSE/Nifty events needed to extend/correct the history around the upstream dataset's 2026-05-15 freshness boundary, including explicit DUMMY corporate-action records.

## Provenance policy

1. Current state is anchored to the official NSE archive CSVs stored under `data/nifty_index_history/current/canonical/`.
2. Yurukatsu data is used to reduce manual reconstruction work, not treated as authoritative merely because it is complete.
3. NSE/Nifty press releases override upstream inference when dates or events differ.
4. `DUMMY*` records are retained only in the corporate-action event file. They are **not canonical membership**. NSE releases explicitly describe these as zero-price demerger placeholders.
5. Upstream rows marked `snapshot_floor` or `inferred` remain visibly classified as inferred/snapshot-derived.
6. A future final PIT table should be generated only after event-chain reconciliation against the official release archive; this folder intentionally preserves the raw acceleration layer and authoritative overrides separately so provenance is reproducible.

## Half-year reconstruction status

- **2026-10-02:** official anchor, exact 750-symbol identity match.
- **2026-03-30 checkpoint:** latest official 2026 review deltas replayed and cardinality-checked.
- **2025-09-30 checkpoint:** reconstructed from the official current anchor and 2025/2026 event chain; cardinality matches, but the checkpoint is **BLOCKED** pending source-backed resolution of AKZOINDIA (Smallcap 250) and SUNDARMHLD (Microcap 250). See `block02_open_gaps.csv`. The SUNDARMHLD exit is inferred only and is not approved evidence.
- Older half-year blocks remain pending until identity-level reconciliation is complete. A passing structural CI run is not an approval of those blocks.

## Upstream limitations

The pinned upstream dataset reports membership through 2026-05-15 and last validation 2026-05-22. It claims high confidence from 2017 onward, with broad-family PR coverage extending earlier; Microcap 250 is described as reliable from 2021-10 onward where PR coverage begins. That means this folder is deliberately a **maximum-history reconstruction layer**, not a claim that every row is equally authoritative.

Upstream data license: CC BY 4.0; preserve attribution when redistributing the transformed dataset.
