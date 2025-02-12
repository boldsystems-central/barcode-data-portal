import sys
import argparse
import ujson as json

SUMMARY_KEY = "tax_geo_inst_id"  # this is what we will aggregate by

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
            aggregates[key] = len(set(aggregate_list))
        else:
            aggregates[key] = len(aggregate_list)

    return aggregates


def summarize(input):
    summaries = {}

    tax_ranks = "kingdom,phylum,class,order,family,subfamily,tribe,genus,species,subspecies".split(
        ","
    )
    geo_ranks = "country/ocean,province/state".split(",")
    # tax_ranks + geo_ranks + tax_id, geo_id
    key_fields = "kingdom,phylum,class,order,family,subfamily,tribe,genus,species,subspecies,country/ocean,province/state,taxid,geoid,inst".split(
        ","
    )
    pid_map = {}
    summary = {}
    terms = {}

    for jline in input:
        record = json.loads(jline)

        key = []

        # figure out all the keys
        for field in key_fields:
            key.append(record.get(field, None))

        tax_geo_inst_key = tuple(key)

        # preprocess and reformat
        if record["processid"] not in pid_map:
            pid_map[record["processid"]] = len(pid_map)

        # rounding off geo coord
        if "coord" in record and len(record["coord"]) == 2:
            record["coord"] = (
                round(record["coord"][0], 1),
                round(record["coord"][1], 1),
            )

        # picking up month and year only from dates
        if "sequence_upload_date" in record and len(record["sequence_upload_date"]) > 5:
            record["sequence_upload_date"] = record["sequence_upload_date"][:7]

        if (
            "collection_date_start" in record
            and len(record["collection_date_start"]) > 5
        ):
            record["collection_date_start"] = record["collection_date_start"][:7]

        # term assembly
        tax_dict = {}  # tax metadata
        for rank in tax_ranks:
            if rank in record:
                term = record.get(rank)

                tax_dict[rank] = term

                tax_info = terms.setdefault(
                    term,
                    {
                        "scope": "tax",
                        "field": rank,
                        "tax_path": tax_dict.copy(),
                        "records": 0,
                        "summaries": 0,
                    },
                )

                # On tax term collision, keep term with higher rank
                term_path = tax_info.get("tax_path")
                if tax_dict != term_path:
                    term_scope = tax_info.get("scope")
                    term_rank = tax_info.get("field")
                    if term_scope == "tax" and tax_ranks.index(rank) < tax_ranks.index(
                        term_rank
                    ):
                        terms[term] = {
                            "scope": "tax",
                            "field": rank,
                            "tax_path": tax_dict.copy(),
                            "records": 0,
                            "summaries": 0,
                        }
                        terms[term]["records"] += 1
                else:
                    terms[term]["records"] += 1

        geo_dict = {}  # geo metadata
        for rank in geo_ranks:
            if rank in record:
                term = record.get(rank)

                geo_dict[rank] = term

                geo_info = terms.setdefault(
                    term,
                    {
                        "scope": "geo",
                        "field": rank,
                        "geo_path": geo_dict.copy(),
                        "records": 0,
                        "summaries": 0,
                    },
                )

                # On geo term collision, keep term with higher rank
                term_path = geo_info.get("geo_path")
                if geo_dict != term_path:
                    term_scope = geo_info.get("scope")
                    term_rank = geo_info.get("field")
                    if term_scope == "geo" and geo_ranks.index(rank) < geo_ranks.index(
                        term_rank
                    ):
                        terms[term] = {
                            "scope": "geo",
                            "field": rank,
                            "geo_path": geo_dict.copy(),
                            "records": 0,
                            "summaries": 0,
                        }
                        terms[term]["records"] += 1
                else:
                    terms[term]["records"] += 1

        # summary assembly
        summary.setdefault(
            tax_geo_inst_key,
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

        for field in summary[tax_geo_inst_key].keys():
            if field in record:
                summary[tax_geo_inst_key][field].setdefault(record[field], [])
                summary[tax_geo_inst_key][field][record[field]].append(
                    pid_map[record["processid"]]
                )

    for key in summary.keys():
        summary[key]["counts"] = {}
        summary[key]["aggregates"] = {}
        summary[key]["counts"]["bin_uri"] = len(summary[key]["bin_uri"])
        summary[key]["counts"]["species"] = len(summary[key]["species"])
        summary[key]["counts"]["specimens"] = len(summary[key]["processid"])
        summary[key]["counts"]["sequences"] = sum(
            (len(pids) for pids in summary[key]["marker_code"].values())
        )

        summary[key]["aggregates"]["identified_by"] = set_aggregates(
            summary[key]["identified_by"], "identified_by"
        )
        summary[key]["aggregates"]["marker_code"] = set_aggregates(
            summary[key]["marker_code"], "marker_code"
        )
        summary[key]["aggregates"]["country/ocean"] = set_aggregates(
            summary[key]["country/ocean"], "country/ocean"
        )
        summary[key]["aggregates"]["inst"] = set_aggregates(
            summary[key]["inst"], "inst"
        )
        summary[key]["aggregates"]["coord"] = set_aggregates(
            summary[key]["coord"], "coord"
        )
        summary[key]["aggregates"]["sequence_upload_date"] = set_aggregates(
            summary[key]["sequence_upload_date"], "sequence_upload_date"
        )
        summary[key]["aggregates"]["sequence_run_site"] = set_aggregates(
            summary[key]["sequence_run_site"], "sequence_run_site"
        )
        summary[key]["aggregates"]["collection_date_start"] = set_aggregates(
            summary[key]["collection_date_start"], "collection_date_start"
        )
        summary[key]["aggregates"]["species"] = set_aggregates(
            summary[key]["species"], "species"
        )
        summary[key]["aggregates"]["bin_uri"] = set_aggregates(
            summary[key]["bin_uri"], "bin_uri"
        )

        # remove the defaults since they've already been summarized
        summary[key].pop("bin_uri")
        summary[key].pop("species")
        summary[key].pop("marker_code")
        summary[key].pop("processid")

        summary[key].pop("identified_by")
        summary[key].pop("inst")
        summary[key].pop("coord")
        summary[key].pop("sequence_upload_date")
        summary[key].pop("sequence_run_site")
        summary[key].pop("collection_date_start")

        summary[key].update(dict(zip(key_fields, key)))
        # replacing the UUID key generation for e.g. "tax_geo_inst_id":"(173826,618,Centre for Biodiversity Genomics)"
        key_string = str(
            (summary[key]["taxid"], summary[key]["geoid"], summary[key]["inst"])
        ).replace(" ", "", 2)
        summary[key][SUMMARY_KEY] = key_string

        # one per jline -- one per summary
        summaries[key_string] = summary[key]

    return (summaries, terms)


def write_summaries(summaries, summary_file):
    with open(summary_file, "w") as f:
        for key in summaries.keys():
            f.write(json.dumps(summaries[key]) + "\n")


def write_terms(terms, terms_file):
    with open(terms_file, "w") as f:
        for term, info in terms.items():
            info["term"] = term
            # lowercase
            info["standardized_term"] = (
                term.strip().lower().translate(str_sanitize_mapping)
            )
            info["original_term"] = term.strip()
            info["priority"] = 1  # TODO: add different priority value
            f.write(json.dumps(info) + "\n")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Processes BOLD singlepane data and extracts terms and summary information.  The input is accepted as stdin."
    )
    # parser.add_argument("--min_overlap", type=int, default=462, help="length of all colums")
    # parser.add_argument("--max_gaps", type=int, default=12, help="tabular output")
    parser.add_argument(
        "--terms_file",
        type=str,
        default="term_maps.jsonl",
        help="file where the mapping of terms to ids will be stored",
    )
    parser.add_argument(
        "--summary_file",
        type=str,
        default="term_summaries.jsonl",
        help="summary data that can be looked up by ids",
    )

    args = parser.parse_args()

    summaries, terms = summarize(sys.stdin)
    # write summaries
    write_summaries(summaries, args.summary_file)

    # write out terms documents
    str_sanitize_mapping = str.maketrans({'"': "-", "?": "-", " ": "_", "'": "-"})
    write_terms(terms, args.terms_file)
