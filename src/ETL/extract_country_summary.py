# for every line in bcdm
# get country and define aggregate key - here it will be country name
# aggregate_key summary_key= what is the key used to identify the summary (i.e. country)
# set defaults
# using record populate these defaults + summary key
# aggregate populated properties grouped by country and summary key
# pull up that summary from db
# update
# write to country_summary.jsonl file - this will only be the countries that need to be updated
import sys
import ujson as json
import argparse
import traceback

SUMMARY_KEY = "country/ocean"  # this is what we will aggregate by
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
                country_key = record[SUMMARY_KEY]
            else:
                continue  # if the country field is missing, the json line will not be considered for summary calc

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

            # 1. summary assembly # if the country doesn't exist, put in empty fields
            # these default properties tell us what are the aggregates we want to know about a country
            summary.setdefault(
                country_key,
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
            for prop in summary[country_key].keys():  # loop over the default props
                if prop in record:
                    r_value = record[prop]  # get value from BCDM record
                    summary[country_key][prop].setdefault(
                        r_value, []
                    )  # start with default empty array
                    # if it already exists
                    i = pid_map[record["processid"]]  # its index in the pid_map
                    summary[country_key][prop][r_value].append(i)  #
        # #3.
        # get counts and aggregates once all countries are populated
        for country in summary.keys():
            props = list(
                summary[country].keys()
            )  # we don't want to loop over counts and aggs, get all default props

            summary[country]["counts"] = {}
            summary[country]["aggregates"] = {}
            for prop in props:
                if prop == "marker_code":
                    summary[country]["counts"]["sequences"] = sum(
                        (len(pids) for pids in summary[country]["marker_code"].values())
                    )
                elif (
                    prop == "processid"
                ):  # instead of processids we rename them as 'specimens'
                    summary[country]["counts"]["specimens"] = len(
                        summary[country][prop]
                    )
                else:
                    summary[country]["counts"][prop] = len(summary[country][prop])
                summary[country]["aggregates"][prop] = set_aggregates(
                    summary[country][prop], prop
                )
                summary[country].pop(prop)
            summary[country][SUMMARY_KEY] = country

    except Exception as e:
        print(traceback.format_exc())
        print(f"Error : {e}")

    # write summaries to file - one per country
    with open(args.summary_file, "w") as f:
        for c in summary.keys():
            f.write(json.dumps(summary[c]) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary_file", type=str)
    args = parser.parse_args()

    main(args)
