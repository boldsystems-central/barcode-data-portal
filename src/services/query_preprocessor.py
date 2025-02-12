from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

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


class TermMatch(BaseModel):
    submitted: str
    matched: str


class QueryPreprocessorSuccess(BaseModel):
    successful_terms: List[TermMatch]


class QueryPreprocessorFail(BaseModel):
    successful_terms: List[TermMatch]
    failed_terms: List[TermMatch]


# example: tax:na:Actias;geo:na:Canada
@route.get(
    "/query/preprocessor",
    responses={
        200: {
            "model": QueryPreprocessorSuccess,
            "description": "Successful Query Preprocessing",
        },
        400: {
            "model": QueryPreprocessorFail,
            "description": "Failed Query Preprocessing",
        },
    },
)
def resolve_query(query: str = Query(min_length=3, max_length=250)):
    """
    Processes and resolves query tokens if matches are found. If matches are not found, will attempt
    to infer possible values for the intended search and return successfully. If triplet token cannot
    be resolved unambiguously, will return possible values but return as an error. If no tokens are
    processed, will also return an error.

    - **query**: A semicolon delimited set of "triplet" tokens. The format for each triplet is
                 [scope]:[subscope]:[value], but can also accept "doublet" ([scope]:[value]) and
                 "singleton" ([value]) tokens.
    """
    tokens = [item.strip() for item in query.split(";") if item.strip()]

    successful_terms = []
    failed_terms = []
    for token in tokens:
        term = token.split(":", 2)[-1]

        resolved_triplets = dao.resolve_term(term)
        if not resolved_triplets:
            # TODO: If token came with scope/subscope, confirm that we ignore them?
            partial_triplet = util.generate_partial_triplet(term)
            successful_terms.append(
                {
                    "submitted": token,
                    "matched": ";".join(util.expand_non_term_triplets(partial_triplet)),
                }
            )
        else:
            triplet = util.generate_triplet_from_token(token)
            sanitized_triplet = util.sanitize_triplet(triplet)

            matched = []
            for triplet_to_match in resolved_triplets:
                if util.match_triplet_to_resolved_triplet(
                    sanitized_triplet, triplet_to_match
                ):
                    matched.append(triplet_to_match)

            if len(matched) == 1:
                # Direct term match
                successful_terms.append({"submitted": triplet, "matched": matched[0]})
            else:
                # Ambiguous term
                failed_terms.append(
                    {"submitted": triplet, "matched": ";".join(resolved_triplets)}
                )

    if failed_terms or not successful_terms:
        return JSONResponse(
            content={
                "successful_terms": successful_terms,
                "failed_terms": failed_terms,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    else:
        return {"successful_terms": successful_terms}
