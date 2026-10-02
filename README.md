# NSE OHLCV probe

`check_ohlcv.py` downloads ten years of daily OHLCV rows from the StockScans chart endpoint and checks whether the response is usable price history.

```powershell
python check_ohlcv.py
```

It checks TDPOWERSYS and RELIANCE plus HDFCBANK, ICICIBANK, TCS, INFY, SBIN, ITC, LT, BHARTIARTL, HINDUNILVR, and AXISBANK. For every symbol it writes `reports/NSE_<SYMBOL>_1D.csv` and a combined `reports/quality_report.json`.

The response layout is `date, open, high, low, close, volume`. Checks cover response identity, daily timeframe, schema, ISO dates, numeric/finite values, positive prices, non-negative volume, valid OHLC relationships, duplicate/out-of-order dates, and weekday gaps. Weekday gaps are warnings because they may be NSE holidays.

The chart endpoint caps each response at 1,000 rows. The script follows its supported `before=YYYY-MM-DD` cursor, using the oldest returned date to request older pages. It then retains the requested trailing range. The report states the number of pages fetched, whether the requested start date was reached, and whether older history remains available.

Run a smaller set with:

```powershell
python check_ohlcv.py --symbols RELIANCE TCS --years 5
```

