"""
use:
    python run_query.py --username user --password 'password' --endpoint couchbase://localhost --file queries.n1ql
    python run_query.py --username user --password 'password' --endpoint couchbase://localhost --file queries.n1ql --pretty --sort
"""

import argparse
import sys
import time
import ujson
from datetime import timedelta

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, ClusterTimeoutOptions, QueryOptions


def get_cluster(username, password, endpoint, timeout):
    # TODO: Refine timeout options
    timeout_options = ClusterTimeoutOptions(
        bootstrap_timeout=timedelta(seconds=timeout),
        connect_timeout=timedelta(seconds=timeout),
        resolve_timeout=timedelta(seconds=timeout),
        kv_timeout=timedelta(seconds=timeout),
        kv_durable_timeout=timedelta(seconds=timeout),
        views_timeout=timedelta(seconds=timeout),
        query_timeout=timedelta(seconds=timeout),
        analytics_timeout=timedelta(seconds=timeout),
        search_timeout=timedelta(seconds=timeout),
        management_timeout=timedelta(seconds=timeout),
        dns_srv_timeout=timedelta(seconds=timeout),
        config_idle_redial_timeout=timedelta(seconds=timeout),
    )
    options = ClusterOptions(
        PasswordAuthenticator(username, password), timeout_options=timeout_options
    )
    cluster = Cluster(endpoint, options)
    cluster.wait_until_ready(timedelta(seconds=5))
    return cluster


def main(args):
    for query in args.file:
        # skip empty and single comment lines
        if not query.lstrip() or query.lstrip().startswith("--"):
            continue

        # run query and print rows
        cluster = get_cluster(args.username, args.password, args.endpoint, args.timeout)

        start_time = time.perf_counter()
        for row in cluster.query(query, QueryOptions(timeout=args.timeout)):
            json_str = ujson.dumps(
                row,
                indent=4 if args.pretty else 0,
                sort_keys=True if args.sort else False,
            )
            print(json_str)
        print(
            f"Query run\t{time.perf_counter() - start_time}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--username", required=True, type=str)
    parser.add_argument("--password", required=True, type=str)
    parser.add_argument("--endpoint", required=True, type=str)

    parser.add_argument(
        "--file",
        required=True,
        type=argparse.FileType("r"),
        help="File containing one N1QL per line.",
    )

    parser.add_argument(
        "--pretty",
        required=False,
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Pretty-print results. (default is --no-pretty)",
    )

    parser.add_argument(
        "--sort",
        required=False,
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Sort keys in results. (default is --no-sort)",
    )

    parser.add_argument(
        "--timeout",
        default=7200,
        type=int,
        help="Global timeout configuration (in seconds)",
    )

    args = parser.parse_args()
    main(args)
