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
import csv
import hashlib
import json
import random
import re
import sys

import psycopg2
import psycopg2.extras

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


def read_universal_mapping(file_obj, delimiter="\t"):
    reader = csv.DictReader(file_obj, delimiter=delimiter)
    universal_mapping = {
        f'{row["bold_field"]}': row["bcdm_field"]
        for row in reader
        if all([row.get("bold_field"), row.get("bcdm_field")])
    }
    return universal_mapping


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


def batches(iterable, batch_size=1):
    for offset in range(0, len(iterable), batch_size):
        yield iterable[offset : (offset + batch_size)]


def read_processids(file_obj):
    return [line.strip() for line in file_obj.readlines() if line.strip()]


def fetch_processids(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT processid FROM data_release")
        return [row["processid"] for row in cursor.fetchall()]


@timed
def fetch_records(conn, processids, markercode):
    # The assumption is made that all fields in the single pane view are relevent, even if they do not map to the output
    main_query = """
        SELECT * FROM bold4_singlepane_view
        WHERE "seqentry.processid" IN %(processids)s
    """

    params = {
        "processids": tuple(processids),
    }

    if markercode:
        main_query += ' AND "marker.code" = %(markercode)s'
        params["markercode"] = markercode

    with conn.cursor() as cursor:
        cursor.execute(main_query, params)
        return cursor.fetchall()


@timed
def generate_inmemory_indexes(conn, markercode):
    index_primers = {}
    index_pcr = {}
    with conn.cursor() as cursor:
        cursor.execute("select id, compact_str from primer_compact_view")
        index_primers = {row["id"]: row["compact_str"] for row in cursor.fetchall()}

        sql = """
        select fk_seqentry as "seqentry.id", fk_primer_f, fk_primer_r
        from pcr
        left join trace on (pcr.id=fk_pcr)
        inner join marker on (pcr.fk_marker=marker.id)
        where status<>'failed' """

        if markercode:
            sql += f"and marker.code = '{markercode}'"

        cursor.execute(sql)

        for row in cursor.fetchall():
            seqentry_id = row["seqentry.id"]
            fk_primer_f = row["fk_primer_f"]
            fk_primer_r = row["fk_primer_r"]

            # TODO: at the time of writing, this takes 8GB of RAM primarly because of size primitives. Look at solutions using numpy lookup and pandas. If that does not reduce the memory considerably, then transition to golang.
            index_pcr.setdefault(seqentry_id, []).append((fk_primer_f, fk_primer_r))

    return index_primers, index_pcr


def filter_records(records, filter_no_seq):
    records_to_keep = []
    for record in records:
        if filter_no_seq and not record["seqentry.processid.marker.code"]:
            continue
        records_to_keep.append(record)
    return records_to_keep


def process(records):
    pid_markers = {}
    date_strformat = "%Y-%m-%d"

    # this is post processing after queries
    for record in records:
        # set tax.refr to None if tax rank is not 17
        if record["tax_rank.numerical_posit"] != 17:
            record["tax.refr"] = None

        # aggregate markers by processid
        pid_markers.setdefault(record["seqentry.processid"], []).append(
            record["marker.code"]
        )

        # Logic to construct the collection date start and end
        if record.get("specimendetails.collectiondate"):
            collection_date_accuracy = record.get(
                "specimendetails.collectiondate_precision"
            )

            # replace accuracy with start and end
            if collection_date_accuracy:
                collection_date = datetime.datetime.strptime(
                    record["specimendetails.collectiondate"], date_strformat
                )

                if collection_date_accuracy > 1:
                    record["collection_date_end"] = datetime.datetime.strftime(
                        collection_date
                        + datetime.timedelta(days=collection_date_accuracy),
                        date_strformat,
                    )
                elif collection_date_accuracy < 1:
                    record["collection_date_end"] = record[
                        "specimendetails.collectiondate"
                    ]
                    record["specimendetails.collectiondate"] = (
                        datetime.datetime.strftime(
                            collection_date
                            + datetime.timedelta(days=collection_date_accuracy),
                            date_strformat,
                        )
                    )

    for record in records:
        record["marker_count"] = len(pid_markers[record["seqentry.processid"]])

    return records


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


def rename_fields(records, mapping):
    new_records = []
    for record in records:
        new_records.append(
            {
                mapping.get(table_column, table_column): val
                for table_column, val in record.items()
            }
        )
    return new_records


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


@timed
def apply_inmemory_indexes(records, index_primers, index_pcr):
    for record in records:
        seqentry_id = record["seqentry.id"]

        if seqentry_id in index_pcr:
            primers_f = {
                index_primers.get(i)
                for i, _ in index_pcr[seqentry_id]
                if index_primers.get(i)
            }
            primers_r = {
                index_primers.get(i)
                for _, i in index_pcr[seqentry_id]
                if index_primers.get(i)
            }

            record["pcr_compact_view.primers_f"] = list(primers_f)
            record["pcr_compact_view.primers_r"] = list(primers_r)
    return records


def sanitize_records(records):
    for record in records:
        for key, value in record.items():
            if isinstance(value, str):
                record[key] = re.sub(r"[\r\n]+", " ", value).replace("\t", " ")
    return records


def add_record_hash_field(records):
    for record in records:
        json_string = json.dumps(record, sort_keys=True)
        record["pre_md5hash"] = hashlib.md5(json_string.encode("utf8")).hexdigest()
    return records


def print_jsonl(records):
    for record in records:
        print(json.dumps(record, sort_keys=True))


def main(args):
    universal_column_mapping = read_universal_mapping(args.tsv_mapping)

    conn = get_connection()
    conn.set_client_encoding("LATIN1")

    materialized_views = [
        "dataset_seq_pivot_mat",
        "tax_denorm_mat",
        "primer_compact_mat_view",
    ]
    refresh_views(conn, materialized_views)
    vacuum_analyse(conn, materialized_views)

    index_primers, index_pcr = generate_inmemory_indexes(conn, args.markercode)

    processids = read_processids(args.processids_file)

    for processids_batch in batches(processids, batch_size=5000):
        records = fetch_records(conn, processids_batch, args.markercode)
        records = filter_records(records, args.filter_no_seq)
        records = process(records)
        records = drop_unwanted_fields(
            records,
            unwanted_fields={
                "tax_rank.numerical_posit",
                "specimendetails__identifier.person.email",
                "specimendetails.verbatim_species",
                "specimendetails.verbatim_genus",
                "specimendetails.verbatim_tribe",
                "specimendetails.verbatim_subfamily",
                "specimendetails.verbatim_family",
                "specimendetails.verbatim_order",
                "specimendetails.verbatim_class",
                "specimendetails.verbatim_phylum",
                "specimendetails.verbatim_kingdom",
                "verbatim_identifier",
                "location.verbatim_country",
                "location.verbatim_province",
                "location.verbatim_country_iso_alpha3",
            },
        )
        records = drop_empty_fields(records)

        # apply in memory indexes
        records = apply_inmemory_indexes(records, index_primers, index_pcr)
        # drop seqentry.id as it is only used for applying in-memory index
        records = drop_unwanted_fields(records, unwanted_fields={"seqentry.id"})

        records = sort_array_fields(records, ignore_fields={"location.coord"})
        records = rename_fields(records, universal_column_mapping)
        records = sanitize_records(records)
        records = add_record_hash_field(records)
        print_jsonl(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--tsv-mapping",
        required=True,
        type=argparse.FileType("r"),
        help="TSV file that maps database table.column to universal name.",
    )

    parser.add_argument(
        "--processids-file",
        required=True,
        type=argparse.FileType("r"),
        help="File containing newline delimited processids.",
    )

    parser.add_argument(
        "--markercode",
        default="",
        type=str,
        help="Marker code (default is all markers).",
    )

    parser.add_argument(
        "--filter-no-seq",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Filter out records without sequences (default is on).",
    )

    args = parser.parse_args()
    main(args)
