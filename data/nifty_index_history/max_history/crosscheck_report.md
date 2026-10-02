# Cross-check report

This report records independent checks performed for the maximum-history layer. Third-party snapshots are diagnostics, not authoritative evidence for changing point-in-time membership.

## Floyd tracker

Source: https://github.com/floyds1995/Auto-Index-Constituents-Tracker, retrieved 2026-10-02. It provides date-level snapshots for Nifty 50, Nifty Next 50, Nifty Midcap 150 and Nifty Smallcap 250; it does not cover Nifty Microcap 250.

| Index | Date | Floyd rows | Yurukatsu rows | Overlap | Observation |
|---|---:|---:|---:|---:|---|
| NIFTY50 | 2024-09-30 | 51 | 50 | 50 | Floyd carries terminal alias LTM; membership set otherwise matches. |
| NIFTY50 | 2025-03-31 | 51 | 50 | 50 | Same LTM alias artifact. |
| NIFTY50 | 2025-09-30 | 51 | 50 | 50 | Same LTM alias artifact. |
| NIFTY50 | 2026-03-31 | 51 | 50 | 50 | Same LTM alias artifact. |
| NIFTYNEXT50 | 2024-09-30 | 50 | 49 | 49 | Floyd retains BANKBARODA; upstream reconstruction lacks it on this date. |
| NIFTYNEXT50 | 2025-03-31 | 50 | 49 | 49 | Same BANKBARODA discrepancy. |
| NIFTYNEXT50 | 2025-09-30 | 50 | 49 | 49 | Same BANKBARODA discrepancy. |
| NIFTYNEXT50 | 2026-03-31 | 50 | 50 | 50 | Full agreement at this checkpoint. |
| NIFTYMIDCAP150 | 2024-09-30 | 150 | 151 | 147 | Four symbol/identity differences require primary-source reconciliation. |
| NIFTYMIDCAP150 | 2025-03-31 | 150 | 149 | 147 | Three Floyd-only plus two upstream-only names. |
| NIFTYMIDCAP150 | 2025-09-30 | 150 | 149 | 148 | Two Floyd-only identity differences versus one upstream-only name. |
| NIFTYMIDCAP150 | 2026-03-31 | 150 | 150 | 150 | Full agreement at this checkpoint. |
| NIFTYSMALLCAP250 | 2024-09-30 | 276 | 250 | 244 | Floyd snapshot contains 26 more rows; not used as canonical evidence. |
| NIFTYSMALLCAP250 | 2025-03-31 | 250 | 250 | 220 | Material composition difference; requires primary-source event reconciliation. |
| NIFTYSMALLCAP250 | 2025-09-30 | 248 | 250 | 216 | Material composition difference; requires primary-source event reconciliation. |
| NIFTYSMALLCAP250 | 2026-03-31 | 250 | 250 | 249 | One symbol difference: MSUMI vs MOTHERSON; do not assume these are aliases. |

These results reinforce the provenance policy: Floyd is an independent diagnostic source, not a replacement for NSE/Nifty primary releases. The Smallcap discrepancies are too large to merge mechanically.

## 2026-10-02 anchor reconciliation observations

The official current snapshots all match target cardinalities after excluding DUMMY*: 50 / 50 / 150 / 250 / 250. After applying the captured official 2026 events from May onward, Nifty 50, Next 50 and Midcap 150 reconcile exactly to the Oct-2 anchor; Microcap also reconciles to 250 once the complete September 2026 exclusion list is applied. Smallcap still has unresolved historical identity/composition transitions, so the full chain is not yet certified as reconciled.

### HEG / HEGAM: corporate action, not a simple ticker alias

NSE Indices' primary release dated 2026-09-03 says HEG Ltd. demerged its graphite business into the resulting company HEG Graphite Ltd. It states that the resulting entity was represented by the temporary symbol DUMMYHEG at zero price in affected indices effective 2026-09-07 (close of 2026-09-04). Source: https://www.niftyindices.com/Press_Release/ind_prs03092026.pdf

Therefore, do not model HEG -> HEGAM as a simple rename without the exchange's resulting-security/listing and effective-date evidence. The current 2026-10-02 Smallcap anchor contains HEGAM, but the exact point-in-time transition from the temporary dummy record to the live symbol still needs primary-source verification. DUMMYHEG remains excluded from canonical membership under the explicit DUMMY* rule.

### MOTHERSON / MSUMI: do not alias

The Smallcap cross-check reports MOTHERSON versus MSUMI. These must not be silently treated as the same security or merged as a ticker alias. Resolve the historical membership difference using the applicable official index review/replacement notice and record the actual ADD/REMOVE effective date. Until that primary evidence is attached, mark the historical event unresolved rather than guessing.

### Other unresolved event

The May-2026 GSPL/CIEINDIA discrepancy remains an event-level reconciliation target; do not infer an effective date from a third-party snapshot alone.

### Microcap count reconciliation

The upstream May-15 state is one row above target until the September 2026 THANGAMAYL exclusion is applied; after that correction the canonical count reaches the Oct-2 target of 250.

No third-party discrepancy was silently promoted to an authoritative event.
