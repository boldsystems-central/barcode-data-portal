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

route = APIRouter(tags=["counts"])


class MetadataCounts(BaseModel):
    records: int
    summaries: int


@route.get(
    "/counts", response_model=MetadataCounts, response_description="Metadata Counts"
)
async def generate_metadata_counts(
    query: str = Query(title="Triplets query", min_length=3, max_length=250)
):
    """
    Return simple metadata count statistics for a query in triplets form. If multiple terms are specified
    and matched, will combine and add results together.

    - **query**: A semicolon delimited set of "triplet" tokens. The format for each triplet is [scope]:[subscope]:[value]
    """
    triplets = util.sanitize_triplets_from_query(query)

    counts = dao.get_cb_counts(triplets)

    return counts
