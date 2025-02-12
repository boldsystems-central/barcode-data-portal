from functools import wraps
import sys, time, datetime


def timed(func):
    @wraps(func)
    def timed_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        total_time = datetime.timedelta(seconds=time.time() - start_time)

        print(f"{func.__name__} {total_time}", file=sys.stderr)
        return result

    return timed_wrapper


import argparse
import hashlib
import json
import random
import sys

import psycopg2
import psycopg2.extras
from psycopg2 import sql

from urllib.parse import urlencode
from urllib.request import urlopen

# dsn is retrieved via http://192.168.12.112:5000/?token=<token>
__SERVICE_URL = ["http://192.168.12.112:5000/", "http://192.168.12.126:5000/"]


def fetch_dsn_from_tokenmanager(token):
    params = urlencode({"token": token})

    url_list = __SERVICE_URL
    random.shuffle(url_list)

    for url in url_list:
        dbconn = json.load(urlopen(f"{url}?{params}"))
        if dbconn:
            break

    if not dbconn:
        return None

    host = str(dbconn.get("server", ""))
    db = str(dbconn.get("db", ""))
    user = str(dbconn.get("user", ""))
    password = str(dbconn.get("password", ""))
    dsn = f"host='{host}' dbname='{db}' user='{user}' password='{password}'"

    # refreshing views requires user to be view owner.
    # switch user from apache to postgres
    # TODO: create a new DB token for this purpose and remove hardcoded user
    dsn = f"host='{host}' dbname='{db}' user='postgres' password='{password}'"

    return dsn


## OPTIONAL TOKENS
## mas_master_prod - DB1 (104.111)
## mas_yesterday_prod - DB2 (104.112)
## mas_master_test - DB1-ALT (63.64)


def get_connection(token="mas_master_prod"):
    """
    Return an instantiated psycopg2 connection object to the
    db associated to the token but with no caching
    """
    dsn = fetch_dsn_from_tokenmanager(token)

    try:
        conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception:
        conn = None

    return conn


def get_connection_dev():
    return psycopg2.connect(
        "postgresql://postgres:@localhost/newdb12",
        client_encoding="LATIN1",  # TODO: remove once database is utf8 encoded
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def refresh_views(conn, materialized_views):
    with conn.cursor() as cursor:
        for view in materialized_views:
            cursor.execute('REFRESH MATERIALIZED VIEW "{view}"'.format(view=view))
        conn.commit()


def vacuum_analyse(conn, tables):
    # By default, autocommit is disabled which makes psycopg2 wrap sql
    # with a transaction block and a mannual commit is required at the end.
    # But, since vacuum cannot run inside a transaction block,
    # autocommit is temporarely enabled, which runs+commits each statement
    # individually without an explicit transaction
    conn.autocommit = True
    with conn.cursor() as cursor:
        for table in tables:
            cursor.execute('VACUUM ANALYZE "{table}"'.format(table=table))
    conn.autocommit = False


@timed
def fetch_records(conn, view):
    main_query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(view))

    with conn.cursor() as cursor:
        cursor.execute(main_query)
        return cursor.fetchall()


def drop_unwanted_fields(records, unwanted_fields=set()):
    for record in records:
        for field in unwanted_fields:
            record.pop(field, None)
    return records


def drop_empty_fields(records):
    for record in records:
        empty_fields = [key for key, value in record.items() if value in ("", None)]
        for field in empty_fields:
            record.pop(field)
    return records


def sort_array_fields(records, ignore_fields=set()):
    for record in records:
        array_fields = [
            key
            for key, value in record.items()
            if isinstance(value, list) and key not in ignore_fields
        ]
        for field in array_fields:
            record[field].sort()
    return records


def add_record_hash_field(records):
    for record in records:
        json_string = json.dumps(record, default=str, sort_keys=True)
        record["pre_md5hash"] = hashlib.md5(json_string.encode("utf8")).hexdigest()
    return records


def print_jsonl(records):
    for record in records:
        print(json.dumps(record, default=str, sort_keys=True))


def main(args):
    conn = get_connection()
    conn.set_client_encoding("LATIN1")

    materialized_views = [
        "tax_denorm_mat",
        "barcodecluster_tax_uniqueid_mat",
        "barcodecluster_counts_mat",
    ]
    refresh_views(conn, materialized_views)
    vacuum_analyse(conn, materialized_views)

    records = fetch_records(conn, args.view)
    records = drop_unwanted_fields(
        records,
        unwanted_fields=set(
            [
                field.strip()
                for field in args.unwanted_fields.split(",")
                if field.strip()
            ]
        ),
    )
    if args.drop_empty_fields:
        records = drop_empty_fields(records)
    if args.sort_array_fields:
        records = sort_array_fields(
            records,
            ignore_fields=set(
                [
                    field.strip()
                    for field in args.sort_array_ignore_fields.split(",")
                    if field.strip()
                ]
            ),
        )

    records = add_record_hash_field(records)
    print_jsonl(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--view", required=True, type=str, help="newdb12 singlepane_view to export."
    )

    parser.add_argument(
        "--unwanted-fields",
        default="",
        type=str,
        help="CSV string of database fields to drop from export.",
    )

    parser.add_argument(
        "--drop-empty-fields",
        action=argparse.BooleanOptionalAction,
        help="Remove empty fields in each record from export.",
    )

    parser.add_argument(
        "--sort-array-fields",
        action=argparse.BooleanOptionalAction,
        help="Sort array fields in each record in export.",
    )

    parser.add_argument(
        "--sort-array-ignore-fields",
        default="",
        type=str,
        help="CSV string of database fields to ignore when --sort-array-fields is set.",
    )

    args = parser.parse_args()
    main(args)
