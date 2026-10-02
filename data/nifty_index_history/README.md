# Nifty constituent history — Phase 1

Target: 2026-10-02 current universes worked backward to January 2024.

Official current constituent CSVs:
- Nifty 50: https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv
- Nifty Next 50: https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv
- Nifty Midcap 150: https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv
- Nifty Smallcap 250: https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv
- Nifty Microcap 250: https://www.niftyindices.com/IndexConstituent/ind_niftymicrocap250list.csv

The official reconstitution calendar says all five are reviewed semi-annually on the last working day of March and September.

Historical evidence rule: use official Nifty Indices / NSE press releases and circulars for additions, deletions, effective dates and interim corporate-action changes. Do not infer membership solely from current constituents or third-party history pages.

Event schema:
index,event_announcement_date,effective_date,action,symbol,company_name,source_url,source_type,notes

Status:
- Current raw CSV extraction is blocked by the research environment because Nifty Indices serves CSV as application/octet-stream.
- Official 2024 event anchors have been independently verified and are recorded separately.
- Full Jan-2024-to-current reconstruction still requires completing every scheduled and interim notice.
