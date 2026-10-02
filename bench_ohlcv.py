#!/usr/bin/env python3
"""Benchmark StockScans OHLCV storage layouts without committing market data."""
from __future__ import annotations
import argparse,csv,json,platform,statistics,sys,tempfile,time
from pathlib import Path
COLUMNS=("date","open","high","low","close","volume")
LEVELS=(1,3,6)
def load_csv(p):
    with p.open(newline="",encoding="utf-8") as f:
        r=csv.DictReader(f)
        if tuple(r.fieldnames or ())!=COLUMNS: raise ValueError(f"expected {COLUMNS}, got {r.fieldnames!r}")
        return [[x["date"],float(x["open"]),float(x["high"]),float(x["low"]),float(x["close"]),int(float(x["volume"]))] for x in r]
def pa_pq():
    try:
        import pyarrow as pa, pyarrow.parquet as pq
    except ImportError as e: raise RuntimeError("install pyarrow first") from e
    return pa,pq
def table(rows):
    pa,_=pa_pq()
    return pa.Table.from_arrays([
      pa.array([r[0] for r in rows],type=pa.date32()),
      pa.array([r[1] for r in rows],type=pa.float64()),
      pa.array([r[2] for r in rows],type=pa.float64()),
      pa.array([r[3] for r in rows],type=pa.float64()),
      pa.array([r[4] for r in rows],type=pa.float64()),
      pa.array([r[5] for r in rows],type=pa.int64())],names=COLUMNS)
def timed(fn,n):
    vals=[]
    for _ in range(n):
        t=time.perf_counter(); fn(); vals.append((time.perf_counter()-t)*1000)
    return {"median_ms":statistics.median(vals),"min_ms":min(vals),"max_ms":max(vals)}
def bench_pq(p,rows,n):
    _,pq=pa_pq(); start=rows[-252][0] if len(rows)>=252 else rows[0][0]; latest=rows[-1][0]
    return {"bytes":p.stat().st_size,"queries":{
      "full_history":timed(lambda:pq.read_table(p),n),
      "trailing_252_rows":timed(lambda:pq.read_table(p,filters=[("date",">=",start)]),n),
      "latest_session":timed(lambda:pq.read_table(p,columns=["date","close"],filters=[("date","=",latest)]),n),
      "selected_columns":timed(lambda:pq.read_table(p,columns=["date","close"]),n)}}
def bench(in_dir,out,n,symbols):
    _,pq=pa_pq()
    files={s.upper():in_dir/f"NSE_{s.upper()}_1D.csv" for s in symbols}; files={s:p for s,p in files.items() if p.exists()}
    if not files: raise FileNotFoundError(f"no CSV files in {in_dir}")
    report={"benchmark":{"repeats":n,"symbols":sorted(files),"market_data_committed":False,
                         "environment":{"python":sys.version.split()[0],"platform":platform.platform()}},
            "symbols":{}}
    with tempfile.TemporaryDirectory(prefix="patel-parquet-bench-") as td:
        td=Path(td)
        for s,cp in files.items():
            rows=load_csv(cp); latest=rows[-1][0]
            e={"row_count":len(rows),"start_date":rows[0][0],"end_date":latest,"csv":{"bytes":cp.stat().st_size},"parquet":{}}
            for key,kwargs in [("uncompressed",{}),*[(f"zstd-{l}",{"compression":"zstd","compression_level":l}) for l in LEVELS]]:
                p=td/f"{s}.{key}.parquet"; pq.write_table(table(rows),p,**kwargs); e["parquet"][key]=bench_pq(p,rows,n)
            report["symbols"][s]=e
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir",type=Path,default=Path("reports"))
    ap.add_argument("--output",type=Path,default=Path("reports/benchmark_report.json"))
    ap.add_argument("--repeats",type=int,default=5)
    ap.add_argument("--symbols",nargs="+",default=["RELIANCE","TDPOWERSYS","HDFCBANK","TCS","INFY","SBIN"])
    a=ap.parse_args(); bench(a.input_dir,a.output,a.repeats,a.symbols)
