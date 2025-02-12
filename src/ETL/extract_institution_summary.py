import sys
import ujson as json
import argparse
import traceback

SUMMARY_KEY = "inst"  # this is what we will aggregate by, Institution
tax_ranks = (
    "kingdom,phylum,class,order,family,subfamily,tribe,genus,species,subspecies".split(
        ","
    )
)
geo_ranks = ["province/state"]
# tax_ranks + geo_ranks + tax_id, geo_id
key_fields = "kingdom,phylum,class,order,family,subfamily,tribe,genus,species,subspecies,country/ocean,province/state,taxid,geoid".split(
    ","
)

_SPECIMEN_CENTRIC = [
    "bin_uri",
    "collection_date_start",
    "coord",
    "country/ocean",
    "identified_by",
    "inst",
    "species",
]


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

            if SUMMARY_KEY in record:
                inst_key = record[
                    SUMMARY_KEY
                ]  # akin to tax geo key, entity you want to group by
            else:
                continue  # if the inst field is missing, the json line will not be considered for summary calc

            # creates a process_id counter ; should be = # of jsonl processed
            if record["processid"] not in pid_map:
                pid_map[record["processid"]] = len(pid_map)

            # rounding off geo coord
            if "coord" in record and len(record["coord"]) == 2:
                record["coord"] = (
                    round(record["coord"][0], 1),
                    round(record["coord"][1], 1),
                )

            # picking up month and year only from dates
            if (
                "sequence_upload_date" in record
                and len(record["sequence_upload_date"]) > 5
            ):
                record["sequence_upload_date"] = record["sequence_upload_date"][:7]

            if (
                "collection_date_start" in record
                and len(record["collection_date_start"]) > 5
            ):
                record["collection_date_start"] = record["collection_date_start"][:7]

            # 1. summary assembly # if the inst doesn't exist, put in empty fields
            # these default properties tell us what are the aggregates we want to know about an institution
            summary.setdefault(
                inst_key,
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
            # TODO test building defaults thru a loop on tax

            # 2. assembly population from the record fields
            for prop in summary[inst_key].keys():  # loop over the default props
                if prop in record:
                    r_value = record[prop]  # get value from BCDM record
                    summary[inst_key][prop].setdefault(
                        r_value, []
                    )  # start with default empty array
                    # if it already exists
                    i = pid_map[record["processid"]]  # its index in the pid_map
                    summary[inst_key][prop][r_value].append(i)  #

        # #3.
        # get counts and aggregates once all countries are populated
        for institution in summary.keys():
            props = list(
                summary[institution].keys()
            )  # we don't want to loop over counts and aggs

            summary[institution]["counts"] = {}
            summary[institution]["aggregates"] = {}

            for prop in props:
                if prop == "marker_code":
                    summary[institution]["counts"]["sequences"] = sum(
                        (
                            len(pids)
                            for pids in summary[institution]["marker_code"].values()
                        )
                    )
                elif (
                    prop == "processid"
                ):  # instead of processids we rename them as 'specimens'
                    summary[institution]["counts"]["specimens"] = len(
                        summary[institution][prop]
                    )
                else:
                    summary[institution]["counts"][prop] = len(
                        summary[institution][prop]
                    )
                summary[institution]["aggregates"][prop] = set_aggregates(
                    summary[institution][prop], prop
                )
                summary[institution].pop(prop)
            summary[institution][SUMMARY_KEY] = institution

    except Exception as e:
        print(traceback.format_exc())
        print(f"Error : {e}")

    # write summaries to file - one per institution
    with open(args.summary_file, "w") as f:
        for c in summary.keys():
            f.write(json.dumps(summary[c]) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary_file", type=str)
    args = parser.parse_args()
    main(args)
