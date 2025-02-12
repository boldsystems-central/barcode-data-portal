"""
use:
    python bulk_remove_documents.py --username user --password 'password' --endpoint couchbase://localhost --file ids.txt
    python bulk_remove_documents.py --username user --password 'password' --endpoint couchbase://localhost --bucket bucket --scope _default --collection _default --file ids.txt
"""

import argparse
import sys
import time
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

    ids = []
    success_remove = 0
    failed_remove = 0
    start_time = time.perf_counter()
    for id in args.file:
        ids.append(id.strip())

        if len(ids) >= _BATCH_SIZE:
            result = collection.remove_multi(ids)
            print(
                f"Removed {len(result.results)}\t{time.perf_counter() - start_time}",
                file=sys.stderr,
            )
            success_remove += len(result.results)
            failed_remove += len(result.exceptions)

            del ids
            ids = []
            start_time = time.perf_counter()

    if ids:
        result = collection.remove_multi(ids)
        print(
            f"Removed {len(result.results)}\t{time.perf_counter() - start_time}",
            file=sys.stderr,
        )
        success_remove += len(result.results)
        failed_remove += len(result.exceptions)

    print(f"Successfully Removed {success_remove}", file=sys.stderr)

    if failed_remove:
        print(
            f"Failed to Remove {failed_remove}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--username", required=True, type=str)
    parser.add_argument("--password", required=True, type=str)
    parser.add_argument("--endpoint", required=True, type=str)

    parser.add_argument("--bucket", default="BCDM", type=str)
    parser.add_argument("--scope", default="_default", type=str)
    parser.add_argument("--collection", default="primary", type=str)

    parser.add_argument(
        "--file",
        required=True,
        type=argparse.FileType("r"),
        help="File containing one ID per line.",
    )

    args = parser.parse_args()
    main(args)
