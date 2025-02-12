import pandas as pd
from functools import partial
import re
import json


# TODO: Determine behaviour if None for preprocessors/converters, throw error?


def preprocess_string(row, bcdm_field, bcdm_format):
    if pd.isnull(row[bcdm_field]):
        return None

    if re.match(rf"{bcdm_format.replace('%s', '.*')}", row[bcdm_field]):
        return row[bcdm_field]
    else:
        return bcdm_format % (row[bcdm_field],)


def preprocess_date(row, bcdm_field, bcdm_format):
    if pd.isnull(row[bcdm_field]):
        return None

    try:
        return pd.to_datetime(row[bcdm_field]).strftime(bcdm_format)
    except:
        return None


def convert_string_to_array(row, bcdm_field):
    if isinstance(row[bcdm_field], str):
        return (
            row[bcdm_field]
            .replace("(", "", 1)[::-1]
            .replace(")", "", 1)[::-1]
            .split(",")
        )
    else:
        return None


# TODO: Determine behaviour if not in map?
def convert_char_to_string(row, bcdm_field, dwc_format):
    dwc_lookup = json.loads(dwc_format)
    return dwc_lookup.get(row[bcdm_field], None)


def convert_array_to_string(row, bcdm_field, dwc_format):
    return dwc_format % (",".join(row[bcdm_field]),)


def convert_data_by_map(input_file, output_file, map_file):
    map_df = pd.read_csv(map_file, delimiter="\t")
    map_df = map_df[map_df["dwc_field"].notnull()]
    col_rename_map = {
        row.bcdm_field: row.dwc_field
        for row in map_df[["bcdm_field", "dwc_field"]].itertuples()
    }

    preprocess_map = {}
    conversion_map = {}
    for row in map_df.itertuples():
        if row.bcdm_format != "default":
            if row.bcdm_type == "string":
                preprocess_map[row.bcdm_field] = partial(
                    preprocess_string,
                    bcdm_field=row.bcdm_field,
                    bcdm_format=row.bcdm_format,
                )
            elif row.bcdm_type == "string:date":
                preprocess_map[row.bcdm_field] = partial(
                    preprocess_date,
                    bcdm_field=row.bcdm_field,
                    bcdm_format=row.bcdm_format,
                )
            else:
                raise ValueError(
                    f"Unsupported preprocess operand: {row.bcdm_type} ({row.bcdm_format})"
                )

        if row.bcdm_type != row.dwc_type:
            if row.bcdm_type == "char" and row.dwc_type == "string":
                conversion_map[row.bcdm_field] = partial(
                    convert_char_to_string,
                    bcdm_field=row.bcdm_field,
                    dwc_format=row.dwc_format,
                )
            elif row.bcdm_type == "string" and row.dwc_type == "array":
                conversion_map[row.bcdm_field] = partial(
                    convert_string_to_array, bcdm_field=row.bcdm_field
                )
            elif row.bcdm_type == "array" and row.dwc_type == "string":
                conversion_map[row.bcdm_field] = partial(
                    convert_array_to_string,
                    bcdm_field=row.bcdm_field,
                    dwc_format=row.dwc_format,
                )
            else:
                raise ValueError(
                    f"Unsupported conversion operand: {row.bcdm_type} - {row.dwc_type}"
                )

    df = pd.read_json(input_file, lines=True)
    df = df.drop(
        columns=df.columns.difference(col_rename_map.keys()),
        errors="ignore",
    )
    for field, preprocess_func in preprocess_map.items():
        if field in df.columns:
            df[field] = df.apply(preprocess_func, axis=1)
    for field, conversion_func in conversion_map.items():
        if field in df.columns:
            df[field] = df.apply(conversion_func, axis=1)
    df.rename(columns=col_rename_map).to_json(output_file, orient="records", lines=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input JSON lines file",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output JSON lines file",
    )
    parser.add_argument(
        "-m",
        "--map",
        required=True,
        help="Data map file",
    )
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output
    map_file = args.map

    convert_data_by_map(input_file, output_file, map_file)
