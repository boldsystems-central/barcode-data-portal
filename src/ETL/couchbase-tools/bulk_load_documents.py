"""
use:
    python bulk_load_documents.py --username user --password 'password' --endpoint couchbase://localhost --primary-key key --file documents.jsonl
    python bulk_load_documents.py --username user --password 'password' --endpoint couchbase://localhost --primary-key key --bucket bucket --scope _default --collection _default --file documents.jsonl
"""

import argparse
import sys
import time
import ujson
from datetime import timedelta

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions

_BATCH_SIZE = 10000


def get_cluster(username, password, endpoint):
    options = ClusterOptions(PasswordAuthenticator(username, password))
    cluster = Cluster(endpoint, options)
    cluster.wait_until_ready(timedelta(seconds=5))
    return cluster


def main(args):
    cluster = get_cluster(args.username, args.password, args.endpoint)
    bucket = cluster.bucket(args.bucket)
    scope = bucket.scope(args.scope)
    collection = scope.collection(args.collection)

    documents = {}
    success_upload = 0
    failed_upload = 0
    start_time = time.perf_counter()
    for document in args.file:
        document = ujson.loads(document)
        if args.primary_key not in document:
            failed_upload += 1
            continue
        key = str(document[args.primary_key])
        documents[key] = document

        if len(documents) >= _BATCH_SIZE:
            result = collection.insert_multi(documents)
            print(
                f"Uploaded {len(result.results)}\t{time.perf_counter() - start_time}",
                file=sys.stderr,
            )
            success_upload += len(result.results)
            failed_upload += len(result.exceptions)

            del documents
            documents = {}
            start_time = time.perf_counter()

    if documents:
        result = collection.insert_multi(documents)
        print(
            f"Uploaded {len(result.results)}\t{time.perf_counter() - start_time}",
            file=sys.stderr,
        )
        success_upload += len(result.results)
        failed_upload += len(result.exceptions)

    print(f"Successfully Uploaded {success_upload}", file=sys.stderr)

    if failed_upload:
        print(
            f"Failed to Upload {failed_upload}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--username", required=True, type=str)
    parser.add_argument("--password", required=True, type=str)
    parser.add_argument("--endpoint", required=True, type=str)
    parser.add_argument("--primary-key", required=True, type=str)

    parser.add_argument("--bucket", default="BCDM", type=str)
    parser.add_argument("--scope", default="_default", type=str)
    parser.add_argument("--collection", default="primary", type=str)

    parser.add_argument(
        "--file",
        required=True,
        type=argparse.FileType("r"),
        help="File containing one document per line.",
    )

    args = parser.parse_args()
    main(args)
