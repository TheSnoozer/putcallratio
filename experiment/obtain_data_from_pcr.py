#!/usr/bin/env python
import pandas as pd
import requests

from urllib.parse import urljoin

BASE_URL = "https://putcallratio.org/data/"


def get_local_file_name(reference_name: str) -> str:
    local_file_name = ""
    if "dataequity" in reference_name:
        local_file_name = "equity_options.tsv"
    elif "dataindex" in reference_name:
        local_file_name = "index_options.tsv"
    elif "datatotal" in reference_name:
        local_file_name = "total_options.tsv"
    else:
        raise ValueError(f"Unknown {reference_name=}")

    return local_file_name


def main():
    r = requests.get(BASE_URL, verify=False)
    r.raise_for_status()
    main_index_data_frame = pd.read_html(r.text)[0]
    main_index_data_frame["date"] = main_index_data_frame["Name"].str.extract(r"(\d{4}-\d{2}-\d{2})")
    main_index_data_frame = main_index_data_frame.dropna(subset=["date"])

    for group_name, group in main_index_data_frame.groupby(["date"]):
        print(f"Processing {group_name}...")
        if "2022" in group_name and "05" in group_name and "24" in group_name:
            for name in group["Name"]:
                if any(x in name for x in ["dataequity", "dataindex", "datatotal"]):
                    full_url = urljoin(BASE_URL, name)
                    print(f"\tNeed to download {full_url}")

                    # Read the potential new data
                    the_html = requests.get(full_url, verify=False).text
                    new_detail_data_frame = pd.read_html(the_html, index_col=0)[0]
                    new_detail_data_frame.index = group_name + " " + new_detail_data_frame.index
                    new_detail_data_frame.index = pd.to_datetime(new_detail_data_frame.index, format="%Y-%m-%d %I:%M %p")

                    # Read the existing data
                    existing_data_frame = pd.read_csv(
                        get_local_file_name(name),
                        sep="\t",
                        encoding="utf-8",
                        index_col=0,
                        parse_dates=[0],
                    )

                    # Merge the data
                    merged = pd.concat([new_detail_data_frame, existing_data_frame])
                    merged = (
                        merged.assign(
                            d=merged.index.date,
                            t=merged.index.time
                        ).sort_values(["d", "t"], ascending=[False, True])
                        .drop(["d", "t"], axis=1)
                    )

                    col_transformation = {"CALLS": "int64", "PUTS": "int64", "TOTAL": "int64", "P/C RATIO": "float64"}
                    merged = merged.dropna()
                    merged = merged.astype({k: v for k, v in col_transformation.items() if k in merged.columns})

                    # Dump it
                    merged.to_csv(get_local_file_name(name), sep="\t", encoding="utf-8")

            return


if __name__ == "__main__":
    main()
