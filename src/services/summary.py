from fastapi import APIRouter, Query
from typing import Dict, Any

import pathlib
import sys
import ujson
from collections import defaultdict

try:
    import dao
    import util
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import dao
    import util

route = APIRouter(tags=["summary"])

# TODO: Integrate with dao.py?
_ALLOWED_FIELDS_MAP = {
    "BCDM|primary_data": {
        "bin_uri": "bin_uri",
        "collection_date_start": "collection_date_start",
        "coord": "coord",
        "country/ocean": "`country/ocean`",
        "identified_by": "identified_by",
        "inst": "inst",
        "marker_code": "marker_code",
        "sequence_run_site": "sequence_run_site",
        "sequence_upload_date": "sequence_upload_date",
        "species": "species",
        "specimens": "processid",
    },
    "Aggregates|summary": {
        "bin_uri": "aggregates.bin_uri",
        "collection_date_start": "aggregates.collection_date_start",
        "coord": "aggregates.coord",
        "country/ocean": "aggregates.`country/ocean`",
        "identified_by": "aggregates.identified_by",
        "inst": "aggregates.inst",
        "marker_code": "aggregates.marker_code",
        "sequence_run_site": "aggregates.sequence_run_site",
        "sequence_upload_date": "aggregates.sequence_upload_date",
        "species": "aggregates.species",
        "specimens": "counts",
    },
}
_CACHE_FIELDS_MAP = {
    "bin_uri": "bin_uri",
    "collection_date_start": "collection_date_start",
    "coord": "coord",
    "country/ocean": "country/ocean",
    "identified_by": "identified_by",
    "inst": "inst",
    "marker_code": "marker_code",
    "sequence_run_site": "sequence_run_site",
    "sequence_upload_date": "sequence_upload_date",
    "species": "species",
    "specimens": "counts",
}
_COUNTS_ONLY = {"processid": "specimens"}
_SPECIMEN_CENTRIC = [
    "bin_uri",
    "collection_date_start",
    "coord",
    "`country/ocean`",
    "identified_by",
    "inst",
    "processid",
    "species",
]


@route.get(
    "/summary",
    response_model=Dict[str, Dict[Any, int] | int],
    response_description="Metadata Summary",
)
async def generate_metadata_summary(
    query: str = Query(title="Triplets query", min_length=3, max_length=250),
    fields: str = Query(title="Fields to query as CSV"),
    reduce: str = Query(default="", title="Fields to reduce as CSV"),
    reduce_operation: str = Query(
        default="count", title="Reduce operation (count)", regex="(count)"
    ),
):
    """
    Generate metadata summary by way of aggregating fields requested fields from documents selected by
    a query. For each field, will aggregate data into unique values and their frequencies. Can apply
    additional reduce operations to condense response.

    - **query**: A semicolon delimited set of "triplet" tokens. The format for each triplet is [scope]:[subscope]:[value]
    - **fields**: Field(s) to extract and aggregate, as CSV
    - **reduce**: Field(s) to perform an additional reduction on, as CSV
    - **reduce_operation**: Type of reduce, only available option is `count` (sum of all values in aggregates, excluding `counts`)
    """
    triplets = util.sanitize_triplets_from_query(
        query, "full"
    )  # For consistency in cache access
    fields = [field.strip() for field in fields.split(",") if field.strip()]

    search_summary_flags = {
        "summary": True,
        "seqsite_summary": True,
        "bin_summary": True,
        "dataset_summary": True,
    }

    for triplet in triplets[:-1]:
        if (
            not triplet.startswith("geo")
            and not triplet.startswith("tax")
            and not triplet.startswith("inst:name")
        ):
            search_summary_flags["summary"] = False
        if not triplet.startswith("inst:seqsite"):
            search_summary_flags["seqsite_summary"] = False
        if not triplet.startswith("bin"):
            search_summary_flags["bin_summary"] = False
        if not triplet.startswith("recordsetcode"):
            search_summary_flags["dataset_summary"] = False

    stats = {}
    if any(search_summary_flags.values()):
        query_id = util.generate_query_id_from_triplets(triplets)

        if reduce_doc := util.get_cache_from_meta_ids([query_id])[0]:
            reduce_doc = ujson.loads(reduce_doc)
            stats = {
                _CACHE_FIELDS_MAP.get(field): reduce_doc[_CACHE_FIELDS_MAP.get(field)]
                for field in fields
                if _CACHE_FIELDS_MAP.get(field)
            }
        else:
            cb_data = "summary"
            for cb_key, flag in search_summary_flags.items():
                if flag:
                    cb_data = cb_key
            bucket = dao.NAME_MAP[cb_data]["bucket"]
            collection = dao.NAME_MAP[cb_data]["collection"]

            field_set = set(
                [
                    _ALLOWED_FIELDS_MAP["Aggregates|summary"].get(field)
                    for field in fields
                    if _ALLOWED_FIELDS_MAP["Aggregates|summary"].get(field)
                ]
            )
            documents = dao.get_cb_field_values(triplets, field_set, bucket, collection)
            stats = util.reduce_summary_aggregates(documents)

        # Special cases for 'counts-only'
        counts_to_drop = []
        for field in stats.get("counts", {}):
            if field not in fields:
                counts_to_drop.append(field)

        for field in counts_to_drop:
            stats["counts"].pop(field)

    if not stats:
        cb_data = "primary_data"
        bucket = dao.NAME_MAP[cb_data]["bucket"]
        collection = dao.NAME_MAP[cb_data]["collection"]

        field_set = set(
            [
                _ALLOWED_FIELDS_MAP["BCDM|primary_data"].get(field)
                for field in fields
                if _ALLOWED_FIELDS_MAP["BCDM|primary_data"].get(field)
            ]
        )
        documents = dao.get_cb_group_by_field_documents(
            triplets, field_set, bucket, collection
        )

        stats = defaultdict(lambda: {})
        for row in documents:
            if val := row.get("val"):
                if isinstance(val, dict):
                    val = ujson.dumps(val)
                elif isinstance(val, list):
                    val = str(tuple(val))

                if row["field"] in _SPECIMEN_CENTRIC:
                    count = len(set(row["processids"]))
                else:
                    count = len(row["processids"])
                stats[row["field"]][val] = count

        # Special cases for 'counts-only'
        counts = {}
        for field in stats:
            if field in _COUNTS_ONLY:
                counts[_COUNTS_ONLY[field]] = sum(stats[field].values())

        if counts:
            stats["counts"] = counts

        for field in _COUNTS_ONLY:
            stats.pop(field, None)

    reduce = [field.strip() for field in reduce.split(",")]
    for field in stats:
        if field in reduce and field != "counts":
            if reduce_operation == "count":
                stats[field] = sum(stats[field].values())

    # Sanitize ` from field names (only needed for Couchbase)
    sanitized_stats = {}
    for field in stats:
        if field.startswith("`") and field.endswith("`"):
            sanitized_stats[field[1:-1]] = stats[field]
        else:
            sanitized_stats[field] = stats[field]

    return sanitized_stats
