#!/usr/bin/env python
import pandas as pd
import requests
from datetime import datetime
from lxml import html
from pathlib import Path
from shutil import rmtree


def polish_time_index(extracted_date, df):
    df.index = extracted_date.isoformat() + " " + df.index
    df.index = pd.to_datetime(df.index, format="%Y-%m-%d %I:%M %p")


def dump_data(extracted_date, dump_dir, f_name_prefix, raw_data):
    the_html = html.tostring(raw_data)
    with open(dump_dir / (f_name_prefix + ".html"), mode="w", encoding="utf-8") as fd:
        fd.write(the_html.decode("utf-8"))
    df = pd.read_html(the_html, index_col=0)[0]
    polish_time_index(extracted_date, df)
    df.to_csv(dump_dir / (f_name_prefix + ".tsv"), sep="\t", encoding="utf-8")


def main():
    build_artifacts = Path("build")
    if build_artifacts.exists():
        rmtree(build_artifacts)

    build_artifacts.mkdir()

    page = requests.get("https://www.cboe.com/us/options/market_statistics/")
    content = html.fromstring(page.content)

    # raw_data
    extracted_date_str = content.xpath("/html/body/main/section[2]/div/h1/text()")[0]
    extracted_date_str = extracted_date_str.replace("Cboe Exchange Market Statistics for ", "")
    extracted_date = datetime.strptime(extracted_date_str, "%A, %B %d, %Y").date()

    raw_data = content.xpath("/html/body/main/section[2]/div")[0]

    if (
            len(raw_data) == 9 and
            raw_data[3].text == "Total" and
            raw_data[5].text == "Index Options" and
            raw_data[7].text == "Equity Options"
    ):
        dump_data(extracted_date, build_artifacts, "total_options", raw_data[4])
        dump_data(extracted_date, build_artifacts, "index_options", raw_data[6])
        dump_data(extracted_date, build_artifacts, "equity_options", raw_data[8])
    else:
        raw_data_as_html = html.tostring(raw_data)
        # The page structure is different to what we assume
        raise ValueError("Unable to parse: " + raw_data_as_html)


if __name__ == "__main__":
    main()
