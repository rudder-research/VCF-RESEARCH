import os
import json
import pandas as pd
import yfinance as yf
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------
# AUTO-DETECT BASE DIRECTORY (works on Colab + Windows)
# ------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "registry" / "vcf_metric_registry.json"
RAW_DIR = BASE_DIR / "data_raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------
# LOAD REGISTRY
# ------------------------------------------------------
def load_registry():
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Registry not found: {REGISTRY_PATH}")

    with open(REGISTRY_PATH, "r") as f:
        return json.load(f)

# ------------------------------------------------------
# FETCH FRED
# ------------------------------------------------------
def fetch_fred_series(ticker):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ticker}"
    df = pd.read_csv(url)

    df.rename(columns={df.columns[0]: "date", df.columns[1]: "value"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.set_index("date")
    return df

# ------------------------------------------------------
# FETCH YAHOO
# ------------------------------------------------------
def fetch_yahoo_series(ticker):
    df = yf.download(ticker, progress=False)

    if "Adj Close" in df:
        df = df[["Adj Close"]].rename(columns={"Adj Close": "price"})
    else:
        df = df[["Close"]].rename(columns={"Close": "price"})

    df.index.name = "date"
    return df

# ------------------------------------------------------
# MAIN LOADER
# ------------------------------------------------------
def load_all_metrics():
    registry = load_registry()
    print("\n🚀 Starting full VCF data load...")

    for metric_id, meta in registry.items():
        src = meta.get("source")
        ticker = meta.get("ticker")

        print(f"\n📡 Fetching {metric_id}: {meta['display_name']}  (Source: {src})")

        if src == "FRED":
            df = fetch_fred_series(ticker)
        elif src == "YAHOO":
            df = fetch_yahoo_series(ticker)
        else:
            print(f"⚠ Unsupported source: {src}")
            continue

        out_path = RAW_DIR / f"{metric_id}.csv"
        df.to_csv(out_path)
        print(f"✔ Saved to {out_path}  ({len(df)} rows)")

# ------------------------------------------------------
if __name__ == "__main__":
    load_all_metrics()

