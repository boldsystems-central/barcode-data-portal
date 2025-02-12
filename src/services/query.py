from fastapi import APIRouter, Query
from pydantic import BaseModel

import pathlib
import sys

try:
    import dao
    import util
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import dao
    import util


route = APIRouter(tags=["query"])


class QueryResponse(BaseModel):
    query_id: str
    extent_limit: int | None


@route.get(
    "/query", response_model=QueryResponse, response_description="Query Response"
)
async def query_records(
    query: str = Query(min_length=3, max_length=250),
    extent: str = Query(
        default="limited", title="Document extent", regex="(zero|limited|large|full)"
    ),
):
    """
    A query endpoint to retrieve records from "triplet" search terms. Scopes are `tax`, `geo`, `ids`, `bin`, and `recordsetcode`.
    This queries the DB and saves the results to a tmp location, then it returns the `query_id` to the user.

    - **query**: A semicolon delimited set of "triplet" tokens. The format for each triplet is [scope]:[subscope]:[value]
    - **extent**: Set the number of document IDs to fetch (zero = 0 (query not run), full = all, others mappings found in `EXTENT_MAP`)
    """
    triplets = util.sanitize_triplets_from_query(query, extent)
    query_id = util.generate_query_id_from_triplets(triplets)

    cb_data = "primary_data"
    bucket = dao.NAME_MAP[cb_data]["bucket"]
    collection = dao.NAME_MAP[cb_data]["collection"]

    if not util.get_cache_from_query_id(query_id):
        meta_ids = dao.get_cb_meta_ids(triplets, bucket, collection)
        util.write_cache_with_query_id(query_id, meta_ids)

    if extent == "full":
        extent_limit = None
    else:
        extent_limit = dao.EXTENT_LIMIT.get(extent, 0)
    return {"query_id": query_id, "extent_limit": extent_limit}
