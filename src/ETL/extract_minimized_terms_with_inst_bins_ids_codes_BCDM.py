import sys
import argparse
import ujson as json

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


parser = argparse.ArgumentParser(
    description="Processes BOLD singlepane data and extracts terms information.  The input is accepted as stdin."
)
parser.add_argument(
    "--terms_file",
    type=str,
    default="term_maps.jsonl",
    help="file where the mapping of terms to ids will be stored",
)
# parser.add_argument("--summary_file", type=str, default="term_summaries.jsonl", help="summary data that can be looked up by ids")


# BCDM field arrays
tax_ranks = (
    "kingdom,phylum,class,order,family,subfamily,tribe,genus,species,subspecies".split(
        ","
    )
)
geo_ranks = "country/ocean,province/state".split(",")
ids_ranks = "processid,sampleid,insdc_acs".split(",")

key_fields = "kingdom,phylum,class,order,family,subfamily,tribe,genus,species,subspecies,country/ocean,province/state,taxid,geoid,inst".split(
    ","
)

args = parser.parse_args()

pid_map = {}
summary = {}
terms = {}

for jline in sys.stdin:
    record = json.loads(jline)

    key = []
    geo_dict = {}
    tax_dict = {}

    # figure out all the keys
    if "taxid" in record:
        tax_dict = {"taxid": record["taxid"]}
    if "geoid" in record:
        geo_dict = {"geoid": record["geoid"]}

    for field in key_fields:
        key.append(record.get(field, None))

    for field in tax_ranks:
        if field in record and len(record[field]) > 1:
            tax_dict[field] = record[field]

    for field in geo_ranks:
        if field in record and len(record[field]) > 1:
            geo_dict[field] = record[field]

    tax_geo_inst_key = tuple(key)

    # preprocess and reformat
    if record["processid"] not in pid_map:
        pid_map[record["processid"]] = len(pid_map)

    if "coord" in record and len(record["coord"]) == 2:
        record["coord"] = (round(record["coord"][0], 1), round(record["coord"][1], 1))

    if "sequence_upload_date" in record and len(record["sequence_upload_date"]) > 5:
        record["sequence_upload_date"] = record["sequence_upload_date"][:7]

    if "collection_date_start" in record and len(record["collection_date_start"]) > 5:
        record["collection_date_start"] = record["collection_date_start"][:7]

    # term assembly
    str_sanitize_mapping = str.maketrans({'"': "-", "?": "-", " ": "_", "'": "-"})
    """
    scope = "tax"
    for rank in tax_ranks:
        if rank in record:
            field_name = rank
            term = record.get(field_name).strip().lower().translate(str_sanitize_mapping)  # lowercase
            if len(term)> 1:
                terms.setdefault(term, {"scope":scope,"field":field_name,"records":0, "priority":1, "original_term": record.get(field_name).strip()})
                terms[term]["records"]+=1

    scope = "geo"
    for rank in geo_ranks:
        if rank in record:
            field_name = rank
            term = record.get(field_name).strip().lower().translate(str_sanitize_mapping)  # lowercase
            if len(term)> 1:
                terms.setdefault(term, { "scope": scope,"field":field_name,"records":0, "priority":1, "original_term": record.get(field_name).strip()})
                terms[term]["records"]+=1
    """

    scope = "ids"
    for rank in ids_ranks:
        if rank in record:
            field_name = rank
            term = (
                record.get(field_name).strip().lower().translate(str_sanitize_mapping)
            )  # lowercase
            if len(term) > 1:
                terms.setdefault(
                    term,
                    {
                        "scope": scope,
                        "field": field_name,
                        "records": 0,
                        "priority": 1,
                        "original_term": record.get(field_name).strip(),
                    },
                )
                terms[term]["records"] += 1

    scope = "bin"
    field_name = "bin_uri"
    if field_name in record:
        term = record.get(field_name).strip().lower().translate(str_sanitize_mapping)
        if len(term) > 1:
            terms.setdefault(
                term,
                {
                    "scope": scope,
                    "field": "uri",
                    "records": 0,
                    "priority": 1,
                    "original_term": record.get(field_name).strip(),
                },
            )
            terms[term]["records"] += 1

    scope = "inst"
    field_name = "inst"
    if field_name in record:
        term = record.get(field_name).strip().lower().translate(str_sanitize_mapping)
        if len(term) > 1:
            terms.setdefault(
                term,
                {
                    "scope": scope,
                    "field": "name",
                    "records": 0,
                    "priority": 1,
                    "original_term": record.get(field_name).strip(),
                },
            )
            terms[term]["records"] += 1

    scope = "recordsetcode"
    field_name = "bold_recordset_code_arr"
    if field_name in record:
        recordset_terms = record.get(field_name)
        for term in recordset_terms:
            original_term = term
            term = term.strip().lower().translate(str_sanitize_mapping)
            if len(term) > 1:
                terms.setdefault(
                    term,
                    {
                        "scope": scope,
                        "field": "code",
                        "records": 0,
                        "priority": 1,
                        "original_term": original_term.strip(),
                    },
                )
                terms[term]["records"] += 1

# write out terms documents
with open(args.terms_file, "w") as f:
    for term, info in terms.items():
        # info["term"]=term
        info["term"] = info["original_term"]
        info["standardized_term"] = term
        # TODO: Determine if summary generation and count is required anymore,
        # see extract_terms_and_summary_from_BCDM.py also
        info["summaries"] = 0  # zero implies no summaries available
        f.write(json.dumps(info) + "\n")
