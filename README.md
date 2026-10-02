# NSE OHLCV probe

`check_ohlcv.py` downloads daily OHLCV rows from the StockScans chart endpoint and checks whether the response is usable price history.

```powershell
python check_ohlcv.py
```

It checks TDPOWERSYS and RELIANCE plus HDFCBANK, ICICIBANK, TCS, INFY, SBIN, ITC, LT, BHARTIARTL, HINDUNILVR, and AXISBANK. For every symbol it writes `reports/NSE_<SYMBOL>_1D.csv` and a combined `reports/quality_report.json`.

The response layout is `date, open, high, low, close, volume`. Checks cover response identity, daily timeframe, schema, ISO dates, numeric/finite values, positive prices, non-negative volume, valid OHLC relationships, duplicate/out-of-order dates, and weekday gaps. Weekday gaps are warnings because they may be NSE holidays.

If `hasMore` is `true`, the API has signalled that the returned window may not be the complete history. The download is usable, but a paging method must be established before relying on it as a full historical archive.

Run a smaller set with:

```powershell
python check_ohlcv.py --symbols RELIANCE TCS
```
