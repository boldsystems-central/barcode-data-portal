from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

import pyparsing as pr

_UNKNOWN = "na"  # for unknown scope or rank of the query triplet <scope>:<rank>:<value>

route = APIRouter(tags=["query"])


class QueryParseResults(BaseModel):
    terms: str
    ignored_terms: List[str]


def preprocess_input(query_str):
    # Basic cleansing of input string
    new_str = query_str.strip().replace("/", "").replace('""', "")

    # Check for invalid patterns (will throw error if not validated)
    # TODO: this needs improvement.  Probably better to use stricter pyparsing patterns and capture parsing exception
    if new_str.count('"') % 2 != 0:
        raise Exception("Inbalance quotation characters in query term")
    if new_str.count("[") != new_str.count("]"):
        raise Exception("Inbalance scope characters in query term")

    return new_str


def gen_query_parser():
    # Define patterns

    # scope = pr.one_of (" ".join (_SCOPES))
    allowed_punctuation_in_word = ".-_':()"
    allowed_punctuation_in_phrase = " .-_':(),"
    allowed_quote_char = '"'

    scope_like_str = pr.Combine("[" + pr.Word(pr.alphanums + " ") + "]")
    phrase = pr.Word(pr.alphanums + allowed_punctuation_in_phrase)
    single_term = (
        pr.Word(pr.alphanums + allowed_punctuation_in_word)
        + pr.ZeroOrMore(" ")
        + pr.Opt(scope_like_str)
    )
    quoted_multiword_term = (
        pr.Suppress(allowed_quote_char)
        + phrase
        + pr.Suppress(allowed_quote_char)
        + pr.Opt(scope_like_str)
    )
    query_pattern = pr.OneOrMore(quoted_multiword_term | single_term | scope_like_str)

    return query_pattern


def parse_query(query_str):
    parser = gen_query_parser()

    # Parse
    query_obj = {}
    mismatched_terms = []

    # try:
    tokens = parser.search_string(
        query_str
    )  # Unmatched text won't stop processing downstream terms. Only return valid matched terms
    if tokens:
        tokens = sum(tokens)

    last_token = None  # initialize
    for token in tokens:
        if token.startswith("[") and token.endswith("]"):  # find scope
            if last_token is not None:
                query_obj[last_token]["scope"] = (
                    token.rstrip("]").lstrip("[").strip()
                )  # removing flanking whitespace
                last_token = None
            else:
                mismatched_terms.append(token)

        else:  # find query term
            query_obj[token] = {"value": token.strip(), "scope": _UNKNOWN}
            last_token = token

    return query_obj, mismatched_terms


def postprocess_response(triplets, mismatched_terms):
    results = {}
    for key, obj in triplets.items():
        # Construct triplet string in  <scope>:<rank>:<value> format where rank is not yet known
        triplets[key] = ":".join([obj["scope"], _UNKNOWN, obj["value"]])

    results["terms"] = ";".join(triplets.values())
    results["ignored_terms"] = mismatched_terms
    return results


@route.get(
    "/query/parse",
    response_model=QueryParseResults,
    response_description="Query Parse Results",
)
async def query_terms_parsing(query: str):
    """
    A service that accepts a free text query string and parse it into a semicolon separated list of triplets of
    search terms in the following format `<scope>:<rank>:<term>`.

    - **query**: String where multiple search terms are separated by space with the optional scope specified as *[scope]* after a term.
                 Double quote (") must be used to specify multi-word search term. Single quote can be used as part of a word/phrase.
                 Example) `Ontario "Homo sapiens" [tax]` will be parsed into `tax:na:Homo sapiens;na:na:Ontario`
    """
    cleansed_query = preprocess_input(query)
    parsed_query, errors = parse_query(cleansed_query)
    response = postprocess_response(parsed_query, errors)
    return response
