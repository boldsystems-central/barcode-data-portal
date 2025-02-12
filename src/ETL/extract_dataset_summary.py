import sys
import ujson as json
import argparse
import traceback
import re

SUMMARY_KEY = "dataset.code"  # this is what we will aggregate by
PATTERN = r"(DATASET|DS-)"
_SPECIMEN_CENTRIC = [
    "bin_uri",
    "collection_date_start",
    "coord",
    "country/ocean",
    "identified_by",
    "inst",
    "species",
]


def round_coords(record, digits):
    if "coord" in record and len(record["coord"]) == 2:
        record["coord"] = (
            round(record["coord"][0], digits),
            round(record["coord"][1], digits),
        )
    return record


def format_date_for_summary(record, datefield):
    if datefield in record and len(record[datefield]) > 5:
        record[datefield] = record[datefield][:7]
    return record


def set_aggregates(raw_aggregates, field):
    aggregates = {}
    for key, aggregate_list in raw_aggregates.items():
        if field in _SPECIMEN_CENTRIC:
            aggregates[key] = len(
                set(aggregate_list)
            )  # if field is specimen centric, use unique values
        else:
            aggregates[key] = len(aggregate_list)

    return aggregates


def main(args):
    pid_map = {}
    summary = {}  # entire collection, one key per entity you want to group by

    try:
        for jline in sys.stdin:
            record = json.loads(jline)
            # different signatures exist
            lookup_prop = (
                "bold_recordset_code_arr"
                if "bold_recordset_code_arr" in record
                else "recordset_code_arr"
            )
            if lookup_prop in record:
                # for every record get the datasets it belongs to : record datasets
                r_datasets = [s for s in record[lookup_prop] if re.search(PATTERN, s)]
            else:
                continue

            # formatting before summary assembly
            # creates a process_id counter ; should be = # of jsonl processed
            if record["processid"] not in pid_map:
                pid_map[record["processid"]] = len(pid_map)

            record = round_coords(record=record, digits=1)
            record = format_date_for_summary(record, "sequence_upload_date")
            record = format_date_for_summary(record, "collection_date_start")

            # for each of those datasets
            for dataset_key in r_datasets:
                # 1. create a summary default entry
                summary.setdefault(
                    dataset_key,
                    {
                        "identified_by": {},
                        "marker_code": {},
                        "country/ocean": {},
                        "inst": {},
                        "bin_uri": {},
                        "species": {},
                        "processid": {},
                        "sequence_upload_date": {},
                        "coord": {},
                        "sequence_run_site": {},
                        "collection_date_start": {},
                    },
                )

                # 2. assembly population from the record fields
                for prop in summary[dataset_key].keys():  # loop over the default props
                    if prop in record:
                        r_value = record[prop]  # get value from BCDM record
                        summary[dataset_key][prop].setdefault(
                            r_value, []
                        )  # start with default empty array
                        # if it already exists
                        i = pid_map[record["processid"]]  # its index in the pid_map
                        summary[dataset_key][prop][r_value].append(i)  #

        #  for all summaries assembled, get counts and aggregates
        for dataset in summary.keys():
            props = list(summary[dataset].keys())

            summary[dataset]["counts"] = {}
            summary[dataset]["aggregates"] = {}

            for prop in props:
                if prop == "marker_code":
                    summary[dataset]["counts"]["sequences"] = sum(
                        (len(pids) for pids in summary[dataset]["marker_code"].values())
                    )
                elif prop == "processid":
                    summary[dataset]["counts"]["specimens"] = len(
                        summary[dataset][prop]
                    )
                else:
                    summary[dataset]["counts"][prop] = len(summary[dataset][prop])
                summary[dataset]["aggregates"][prop] = set_aggregates(
                    summary[dataset][prop], prop
                )
                summary[dataset].pop(prop)

            # add its id to the object itself
            summary[dataset].update(
                {SUMMARY_KEY: dataset, "bold_recordset_code_arr": [dataset]}
            )

        #  write summaries to file - one per dataset
        with open(args.summary_file, "w") as f:
            for c in summary.keys():
                f.write(json.dumps(summary[c]) + "\n")

    except Exception as e:
        print(traceback.format_exc())
        print("Error", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary_file", type=str)
    args = parser.parse_args()

    main(args)
