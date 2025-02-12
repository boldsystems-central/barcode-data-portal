import sys
import pathlib
import ujson


sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
from dao import NAME_MAP, get_cb_meta_ids, get_cb_documents
from util import (
    sanitize_triplets_from_query,
    generate_query_id_from_triplets,
    write_summary_cache_with_query_id,
    reduce_summary_aggregates,
    write_cache_with_meta_ids,
)


def generate_summary_cache(triplet_queries):
    docs_to_cache = {}
    summary_docs = {}

    for query in triplet_queries:
        triplets = sanitize_triplets_from_query(
            query, "full"
        )  # For consistency in cache access
        query_id = generate_query_id_from_triplets(triplets)

        meta_ids = get_cb_meta_ids(
            triplets, NAME_MAP["summary"]["bucket"], NAME_MAP["summary"]["collection"]
        )
        write_summary_cache_with_query_id(query_id, meta_ids)

        meta_ids_fetch = [
            meta_id for meta_id in meta_ids if meta_id not in summary_docs
        ]
        docs_fetch = get_cb_documents(
            meta_ids_fetch,
            NAME_MAP["summary"]["bucket"],
            NAME_MAP["summary"]["collection"],
        )
        for meta_id, doc in zip(meta_ids_fetch, docs_fetch):
            docs_to_cache[meta_id] = ujson.dumps(doc, default=str)

            for key, aggregates in doc["aggregates"].items():
                doc[key] = aggregates
            del doc["aggregates"]
            summary_docs[meta_id] = doc

        reduce_doc = reduce_summary_aggregates(
            (summary_docs[meta_id] for meta_id in meta_ids)
        )
        docs_to_cache[query_id] = ujson.dumps(reduce_doc, default=str)

    write_cache_with_meta_ids(docs_to_cache, None)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input JSON as list of triplet queries (list of lists)",
    )
    args = parser.parse_args()

    input_file = args.input

    with open(input_file) as fp:
        triplet_queries = ujson.load(fp)

    generate_summary_cache(triplet_queries)
