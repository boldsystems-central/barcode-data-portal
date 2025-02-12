import sys
import ujson as json
import traceback

SUMMARY_KEY = "bin_uri"  # this is what we will aggregate by

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


def main():
    pid_map = {}
    summary = {}  # entire collection, one key per entity you want to group by
    summaries = []

    try:
        for jline in sys.stdin:
            record = json.loads(jline)
            if SUMMARY_KEY in record:
                bin_uri_key = record[
                    SUMMARY_KEY
                ]  # akin to tax geo key, entity you want to group by
            else:
                continue  # if the bin_uri field is missing, the json line will not be considered for summary calc

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

            # 1. summary assembly # if the bin_uri doesn't exist, put in empty fields
            # these default properties tell us what are the aggregates we want to know about a country
            summary.setdefault(
                bin_uri_key,
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
            for prop in summary[bin_uri_key].keys():  # loop over the default props
                if prop in record:
                    r_value = record[prop]  # get value from BCDM record
                    summary[bin_uri_key][prop].setdefault(
                        r_value, []
                    )  # start with default empty array
                    # if it already exists
                    i = pid_map[record["processid"]]  # its index in the pid_map
                    summary[bin_uri_key][prop][r_value].append(i)  #

        # 3.
        # get counts and aggregates once all bins are populated
        for binuri in summary.keys():
            props = list(
                summary[binuri].keys()
            )  # we don't want to loop over counts and aggs, get all default props

            summary[binuri]["counts"] = {}
            summary[binuri]["aggregates"] = {}

            for prop in props:
                if prop == "marker_code":
                    summary[binuri]["counts"]["sequences"] = sum(
                        (len(pids) for pids in summary[binuri]["marker_code"].values())
                    )
                elif (
                    prop == "processid"
                ):  # instead of processids we rename them as 'specimens'
                    summary[binuri]["counts"]["specimens"] = len(summary[binuri][prop])
                else:
                    summary[binuri]["counts"][prop] = len(summary[binuri][prop])
                summary[binuri]["aggregates"][prop] = set_aggregates(
                    summary[binuri][prop], prop
                )
                summary[binuri].pop(prop)
            summary[binuri][SUMMARY_KEY] = binuri
            summaries.append(
                summary[binuri]
            )  # because we want to rank them, ranking done in jq in the bash script

    except Exception as e:
        print(traceback.format_exc())
        print(f"Error : {e}")

    return summaries


if __name__ == "__main__":
    summaries = main()
    json.dump(summaries, sys.stdout)  # we return summaries to jq to sort and filter
