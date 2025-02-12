import sys
import ujson as json
import argparse
import traceback


SUMMARY_KEY = "name"  # this is what we will aggregate by
_SPECIMEN_CENTRIC = [
    "bin_uri",
    "collection_date_start",
    "coord",
    "country/ocean",
    "identified_by",
    "inst",
    "species",
]
PRIMERS_FWD = "primers_forward"
PRIMERS_REV = "primers_reverse"


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


def main(args):
    pid_map = {}
    summary = {}
    primers = None
    fps = None
    rps = None

    try:
        for jline in sys.stdin:
            record = json.loads(jline)
            # for every record
            # get its forward and reverse primers if any
            if PRIMERS_FWD in record:
                fps = [primer.split(":")[0] for primer in record[PRIMERS_FWD]]
            if PRIMERS_REV in record:
                rps = [primer.split(":")[0] for primer in record[PRIMERS_REV]]

            if not fps or not rps:  # If neither found, continue
                continue
            else:
                primers = fps + rps

            # formatting before summary assembly
            # creates a process_id counter ; should be = # of jsonl processed
            if record["processid"] not in pid_map:
                pid_map[record["processid"]] = len(pid_map)

            record = round_coords(record=record, digits=1)
            record = format_date_for_summary(record, "sequence_upload_date")
            record = format_date_for_summary(record, "collection_date_start")

            # for each of the primers
            for primer_key in primers:
                # 1. create a summary default entry
                summary.setdefault(
                    primer_key,
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
                for prop in summary[primer_key].keys():  # loop over the default props
                    if prop in record:
                        r_value = record[prop]  # get value from BCDM record
                        summary[primer_key][prop].setdefault(
                            r_value, []
                        )  # start with default empty array
                        # if it already exists
                        i = pid_map[record["processid"]]  # its index in the pid_map
                        summary[primer_key][prop][r_value].append(i)  #

        # get counts and aggregates once all primer summaries are populated
        for primer in summary.keys():
            props = list(summary[primer].keys())

            summary[primer]["counts"] = {}
            summary[primer]["aggregates"] = {}

            for prop in props:
                if prop == "marker_code":
                    summary[primer]["counts"]["sequences"] = sum(
                        (len(pids) for pids in summary[primer]["marker_code"].values())
                    )
                elif prop == "processid":
                    summary[primer]["counts"]["specimens"] = len(summary[primer][prop])
                else:
                    summary[primer]["counts"][prop] = len(summary[primer][prop])
                summary[primer]["aggregates"][prop] = set_aggregates(
                    summary[primer][prop], prop
                )
                summary[primer].pop(prop)
            summary[primer][SUMMARY_KEY] = primer

        # write summaries to file - one per primer
        with open(args.summary_file, "w") as f:
            for c in summary.keys():
                f.write(json.dumps(summary[c]) + "\n")

    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary_file", type=str)
    args = parser.parse_args()

    main(args)
