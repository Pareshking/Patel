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
| NIFTYSMALLCAP250 | 2026-03-31 | 250 | 250 | 249 | The prior mismatch was MOTHERSON vs MSUMI. These are distinct securities; the upstream MOTHERSON interval was corrected to MSUMI using the official September 2025 review. |

These results reinforce the provenance policy: Floyd is an independent diagnostic source, not a replacement for NSE/Nifty primary releases. Large Smallcap composition differences in earlier checkpoints remain a historical reconciliation task and have not been merged mechanically.

## 2026-10-02 anchor reconciliation observations

The official current snapshots all match target cardinalities after excluding DUMMY*: 50 / 50 / 150 / 250 / 250. Official 2026 events and the latest primary-source identity corrections are stored separately from the first-pass intervals. The point-in-time history is a maximum-history reconstruction, not a claim that every earlier checkpoint has been independently proven against a complete set of archived official constituents.

### MOTHERSON / MSUMI: resolved as distinct securities

NSE Indices' 2025-08-22 broad-market review says changes take effect 2025-09-30 (close of 2025-09-29). It explicitly excludes Motherson Sumi Wiring India Ltd. (MSUMI) from Nifty Midcap 150 and includes MSUMI in Nifty Smallcap 250. Source: https://www.niftyindices.com/Press_Release/ind_prs22082025.pdf

The upstream Smallcap interval had incorrectly used MOTHERSON from 2025-09-30. MOTHERSON is Samvardhana Motherson International Ltd., a distinct security; it is not an alias for MSUMI. The interval has been corrected to MSUMI from 2025-09-30 using the official review source. The official current anchor separately places MOTHERSON in Nifty Next 50 and MSUMI in Nifty Smallcap 250.

### HEG / HEGAM: continuing security plus separate demerger entity

NSE Indices' primary release dated 2026-09-03 says HEG Ltd. demerged its graphite business into the resulting company HEG Graphite Ltd. It states that the resulting entity was represented by temporary symbol DUMMYHEG at zero price in affected indices effective 2026-09-07 (close of 2026-09-04). Source: https://www.niftyindices.com/Press_Release/ind_prs03092026.pdf

NSE's security page identifies HEGAM as HEG Advanced Materials Ltd. with ISIN INE545A01024, the same ISIN shown in NSE filings for the pre-demerger HEG Ltd. security. Source: https://www.nseindia.com/get-quote/equity/HEGAM/HEG-Advanced-Materials-Limited

The canonical interval therefore retains the historical HEG symbol through 2026-09-04 and records the continuing security as HEGAM from 2026-09-07. DUMMYHEG remains a separate demerger placeholder in the official event ledger and is excluded from canonical membership by the DUMMY* rule.

### GSPL / CIEINDIA: official replacement captured

The official 2026-05-04 release records CIEINDIA added to Nifty Smallcap 250 and GSPL removed, effective 2026-05-12. Source: https://www.niftyindices.com/Press_Release/ind_prs04052026.pdf. Both the event ledger and interval boundaries carry this replacement; it is no longer an unverified inference.

### Microcap count reconciliation

The upstream May-15 state is one row above target until the September 2026 THANGAMAYL exclusion is applied; after that correction the canonical count reaches the Oct-2 target of 250.

The unresolved work is now the material historical composition differences in the Smallcap 250 and smaller checkpoint-level gaps in other indices. Those require further official dated constituent lists/replacement notices; do not manufacture events from third-party snapshots.
