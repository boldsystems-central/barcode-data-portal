import sys
import ujson as json
import argparse
import traceback
from collections import defaultdict

SUMMARY_KEY = "taxid"  # this is what we will aggregate by
_SPECIMEN_CENTRIC = [
    "bin_uri",
    "collection_date_start",
    "coord",
    "country/ocean",
    "identified_by",
    "inst",
    "species",
]
_TAX_RANKS = [
    "phylum",
    "class",
    "order",
    "family",
    "subfamily",
    "tribe",
    "genus",
    "species",
    "subspecies",
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
    tax_rank_map = defaultdict(lambda: [])
    tax_child_map = defaultdict(lambda: [])

    pid_map = {}
    summary_stats = {}
    summary = defaultdict(
        lambda: {}
    )  # entire collection, one key per entity you want to group by

    try:
        # load public+private stats data from registry file and initialize public stats data
        with open(args.registry_file) as f:
            for line in f:
                registry_data = json.loads(line)

                taxid = registry_data["taxid"]
                summary[taxid].update(
                    {
                        "taxid": taxid,
                        "taxon": registry_data[registry_data["rank_name"]],
                        "parent_taxid": registry_data["parent_taxid"],
                        "rank_name": registry_data["rank_name"],
                        "all_specimens": registry_data["tax_stats.specimens_all"],
                        "all_specimens_seq": registry_data[
                            "tax_stats.specimens_seq_all"
                        ],
                        "all_specimens_barcodes": registry_data[
                            "tax_stats.specimens_barcodes_all"
                        ],
                        "all_species": registry_data["tax_stats.species_all"],
                        "all_species_seq": registry_data["tax_stats.species_seq_all"],
                        "all_species_barcodes": registry_data[
                            "tax_stats.species_barcodes_all"
                        ],
                        "all_barcodes": registry_data["tax_stats.barcodes_all"],
                        "all_sequences": registry_data["tax_stats.sequences_all"],
                        "sequences": 0,
                        "specimens": 0,
                        "identified_by": 0,
                        "country/ocean": 0,
                        "inst": 0,
                        "bin_uri": 0,
                        "species": 0,
                        "sequence_upload_date": 0,
                        "coord": 0,
                        "sequence_run_site": 0,
                        "collection_date_start": 0,
                    }
                )

                tax_rank_map[registry_data["rank_name"]].append(taxid)
                tax_child_map[registry_data["parent_taxid"]].append(taxid)

        for jline in sys.stdin:
            record = json.loads(jline)
            if SUMMARY_KEY in record:
                taxid = record[
                    SUMMARY_KEY
                ]  # akin to tax geo key, entity you want to group by
            else:
                continue  # if the taxid field is missing, the json line will not be considered for summary calc

            # formatting before summary stats assembly
            # creates a process_id counter ; should be = # of jsonl processed
            if record["processid"] not in pid_map:
                pid_map[record["processid"]] = len(pid_map)

            record = round_coords(record=record, digits=1)
            record = format_date_for_summary(record, "sequence_upload_date")
            record = format_date_for_summary(record, "collection_date_start")

            # 1. summary stats assembly # if the taxid doesn't exist, put in empty fields
            # these default properties tell us what are the aggregates we want to know about an taxid
            summary_stats.setdefault(
                taxid,
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
            for prop in summary_stats[taxid].keys():  # loop over the default props
                if prop in record:
                    r_value = record[prop]  # get value from BCDM record
                    summary_stats[taxid][prop].setdefault(
                        r_value, []
                    )  # start with default empty array
                    # if it already exists
                    i = pid_map[record["processid"]]  # its index in the pid_map
                    summary_stats[taxid][prop][r_value].append(i)  #

        #  for all summary stats assembled, get counts and aggregates
        for taxid in summary_stats.keys():
            props = list(summary_stats[taxid].keys())

            for prop in props:
                if prop == "marker_code":
                    summary[taxid]["sequences"] = sum(
                        (
                            len(pids)
                            for pids in summary_stats[taxid]["marker_code"].values()
                        )
                    )
                elif prop == "processid":
                    summary[taxid]["specimens"] = len(summary_stats[taxid][prop])
                else:
                    summary[taxid][prop] = len(summary_stats[taxid][prop])
            summary[taxid][SUMMARY_KEY] = taxid

        #  iterate ranks from bottom up and aggregate stats up the hierarchy
        stats_to_aggregate = (
            "sequences",
            "specimens",
            "identified_by",
            "country/ocean",
            "inst",
            "bin_uri",
            "species",
            "sequence_upload_date",
            "coord",
            "sequence_run_site",
            "collection_date_start",
        )
        for rank in _TAX_RANKS[::-1][1:]:
            rank_taxids = tax_rank_map[rank]
            for taxid in rank_taxids:
                aggregate_data = defaultdict(lambda: 0)
                child_taxids = tax_child_map[taxid]
                for child_taxid in child_taxids:
                    taxid_data = summary[child_taxid]
                    for key in stats_to_aggregate:
                        aggregate_data[key] += taxid_data[key]

                for key in stats_to_aggregate:
                    summary[taxid][key] += aggregate_data[key]

        #  write summaries to file - one per taxid
        with open(args.summary_file, "w") as f:
            for c in summary.keys():
                f.write(json.dumps(summary[c]) + "\n")

    except Exception as e:
        print(traceback.format_exc())
        print("Error", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry_file", type=str)
    parser.add_argument("--summary_file", type=str)
    args = parser.parse_args()

    main(args)
