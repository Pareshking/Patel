# Cross-check report

This report records independent checks performed for the maximum-history layer.

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
| NIFTYSMALLCAP250 | 2026-03-31 | 250 | 250 | 249 | One symbol/identity difference: MSUMI vs MOTHERSON. |

These results reinforce the provenance policy: Floyd is an independent diagnostic source, not a replacement for NSE/Nifty primary releases. The Smallcap discrepancies are too large to merge mechanically.

## 2026-10-02 anchor reconciliation observations

The official current snapshots all match target cardinalities after excluding DUMMY*: 50 / 50 / 150 / 250 / 250. The upstream state at its 2026-05-15 boundary reconciles exactly to the Oct-2 anchor for Nifty 50, Next 50 and Midcap 150 after applying the official 2026 events captured in this layer. Smallcap and Microcap still surface corporate-action / identity transitions that require an explicit primary-source mapping before calling the whole chain fully reconciled:

- Smallcap: HEG vs current HEGAM, MOTHERSON vs current MSUMI, and the May-2026 GSPL to CIEINDIA replacement require symbol/identity treatment in the final PIT chain.
- Microcap: the upstream May-15 state is one row above target because the September 2026 THANGAMAYL exclusion must be applied; the remaining current-anchor transition should be finalized against the exact post-demerger identity chain.

No third-party discrepancy was silently promoted to an authoritative event.
