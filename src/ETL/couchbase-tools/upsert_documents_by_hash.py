import argparse
import sys
from datetime import timedelta, datetime
from couchbase.options import QueryOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
import ujson

from bulk_upsert_documents import upsert_document_collection

_BATCH_SIZE = 5000


def get_cluster(username, password, endpoint):
    options = ClusterOptions(PasswordAuthenticator(username, password))
    cluster = Cluster(endpoint, options)
    cluster.wait_until_ready(timedelta(seconds=5))
    return cluster


def get_documents_from_CB(cb_object, primary_key, match_ids):
    cb_documents = {}
    cluster = get_cluster(
        cb_object["username"], cb_object["password"], cb_object["endpoint"]
    )
    try:
        # record_id and pre_md5hash document
        query = f'select meta().id AS record_id, pre_md5hash from `{cb_object["bucket"]}`.`{cb_object["scope"]}`.`{cb_object["collection"]}` where meta().id in $1'
        result = cluster.query(query, QueryOptions(positional_parameters=[match_ids]))
        for row in result.rows():
            cb_document = row
            cb_documents[str(cb_document[primary_key])] = cb_document
    except Exception as e:
        print(e, file=sys.stderr)
    return cb_documents


def diff_documents(incoming_document, cb_matched_document):
    return incoming_document["pre_md5hash"] != cb_matched_document["pre_md5hash"]


def collect_upserts(incoming_documents, cb_matched_documents):
    upsert_subset = {}

    for id, incoming_document in incoming_documents.items():
        cb_matched_document = cb_matched_documents.get(id, None)
        if not cb_matched_document or diff_documents(
            incoming_document, cb_matched_document
        ):
            upsert_subset[id] = incoming_document

    return upsert_subset


def process_batch(documents, primary_key, indexed_column_set, cb_object, batch):
    match_subset = {}
    # check presence in dict and update indexed_column
    for id in documents.keys():
        if id in indexed_column_set:
            indexed_column_set[id] = True  # match found
            match_subset[id] = True

    # return data for intersects from CB
    match_ids = list(match_subset.keys())
    cb_matched_documents = get_documents_from_CB(cb_object, primary_key, match_ids)

    # do comparison
    upsert_subset = collect_upserts(documents, cb_matched_documents)
    print(ujson.dumps(list(upsert_subset.keys())))

    upsert_document_collection(cb_object, upsert_subset)
    print(f"Upserting batch {batch} with {len(upsert_subset)}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        required=True,
        type=argparse.FileType("r"),
        help="File containing documents to upsert.",
    )

    parser.add_argument("--index_column", required=True, type=str)
    parser.add_argument(
        "--index_column_file",
        required=True,
        type=argparse.FileType("r"),
        help="File containing index column values as document IDs.",
    )

    # CB connection
    parser.add_argument("--username", required=True, type=str)
    parser.add_argument("--password", required=True, type=str)
    parser.add_argument("--endpoint", required=True, type=str)

    parser.add_argument("--bucket", default="BCDM", type=str)
    parser.add_argument("--scope", default="_default", type=str)
    parser.add_argument("--collection", default="primary", type=str)

    args = parser.parse_args()
    primary_key = args.index_column

    cb_object = {
        "endpoint": args.endpoint,
        "username": args.username,
        "password": args.password,
        "collection": args.collection,
        "bucket": args.bucket,
        "scope": args.scope,
    }

    print("Bringing in Index column. . .", file=sys.stderr)
    indexed_column_set = {}
    for index_line in args.index_column_file:
        index = ujson.loads(index_line)
        value = index["id"]
        indexed_column_set[value] = False

    print(
        f"{len(indexed_column_set)} indexes brought in. at {datetime.now()}",
        file=sys.stderr,
    )

    batch_documents = {}
    batch = 1

    # batching
    for document in args.file:
        document = ujson.loads(document)

        if primary_key not in document:
            continue

        id = str(document[primary_key])
        batch_documents[id] = document

        if len(batch_documents) >= _BATCH_SIZE:
            print(f"processing batch {batch} at {datetime.now()}", file=sys.stderr)
            process_batch(
                batch_documents, primary_key, indexed_column_set, cb_object, batch
            )
            batch_documents = {}
            batch += 1

    if batch_documents:
        print(f"processing batch {batch} at {datetime.now()}", file=sys.stderr)
        process_batch(
            batch_documents, primary_key, indexed_column_set, cb_object, batch
        )
        batch += 1

    # handle deletions
    delete_ids = [
        id for id, value in indexed_column_set.items() if not value
    ]  # will filter all the ones that are no longer in BOLD/no longer public
    print(f"printing {len(delete_ids)} documents for deletion", file=sys.stderr)
    print(ujson.dumps(delete_ids))
