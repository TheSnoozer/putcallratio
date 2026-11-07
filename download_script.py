#!/usr/bin/env python
import json

import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
from shutil import rmtree

# https://www.cboe.com/us/options/market_statistics/
# https://ww2.cboe.com/us/options/market_statistics
# https://www.cboe.com/markets/us/options/market-statistics/daily/?dt=2026-11-04
DATA_URL = "https://cdn-api.cboe.com/api/us/options/market-statistics/cone-current-market-statistics.json"

CATEGORIES = {
    "total": "total_options",
    "index": "index_options",
    "equity": "equity_options",
}


def dump_data(
    extracted_date,
    dump_dir: Path,
    f_name_prefix: str,
    rows
):
    df = pd.DataFrame(rows)
    df = df.rename(columns={"calls": "CALLS", "puts": "PUTS", "total": "TOTAL"})
    df["P/C RATIO"] = (df["PUTS"] / df["CALLS"]).round(2)
    df = df.set_index("time")
    df.index = extracted_date.isoformat() + " " + df.index
    df.index = pd.to_datetime(df.index, format="%Y-%m-%d %H:%M")

    df = df.rename_axis("TIME")
    col_transformation = {"CALLS": "int64", "PUTS": "int64", "TOTAL": "int64", "P/C RATIO": "float64"}
    df = df.astype(col_transformation)
    df.to_csv(dump_dir / (f_name_prefix + ".tsv"), sep="\t", encoding="utf-8")


def main():
    build_artifacts = Path("build")
    if build_artifacts.exists():
        rmtree(build_artifacts)

    build_artifacts.mkdir()

    page = requests.get(DATA_URL)
    page.raise_for_status()

    payload = page.json()
    extracted_date_str = payload["trading_dt"]
    extracted_date = datetime.strptime(extracted_date_str, "%Y-%m-%d").date()

    with open(build_artifacts / f"{extracted_date}_market_statistics.json", mode="w", encoding="utf-8") as fd:
        json.dump(payload, fd)

    for category, f_name_prefix in CATEGORIES.items():
        rows = payload["data"][category]
        dump_data(extracted_date, build_artifacts, f_name_prefix, rows)


if __name__ == "__main__":
    main()
