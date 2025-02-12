from fastapi import APIRouter, Query

import pathlib
import sys

from starlette import status
from starlette.responses import JSONResponse

try:
    import dao
    import util
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import dao
    import util

route = APIRouter(tags=["terms"])


@route.get("/terms", response_description="Matching list of terms")
async def fetch_term_hits(
    partial_term: str = Query(title="Partial term"),
    limit: int = Query(20, title="Limit # of hits to return"),
):
    """
    Return top X terms that match the supplied partial term at the start of the term.
    This is analagous to `^{partial_term}.*` in regex. Terms are standardized to optimize
    creating matches easily with proxy characters.

    - **partial_term**: Start of term to search for
    """
    scope = None
    if ":" in partial_term:
        scope, potential_term = partial_term.split(":", 1)
        if scope not in dao._get_scopes():
            scope = None
        else:
            partial_term = potential_term

    # TODO: centralise this in a method so creating the index and querying it uses the same logic!
    str_sanitize_mapping = str.maketrans({'"': "-", "?": "-", " ": "_", "'": "-"})
    sanitized_partial_term = (
        partial_term.strip().lower().translate(str_sanitize_mapping)
    )

    if len(sanitized_partial_term) < 3:
        return JSONResponse(
            content="term length is too short",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    hits = dao.query_term_hits(sanitized_partial_term, scope, limit)

    return hits
