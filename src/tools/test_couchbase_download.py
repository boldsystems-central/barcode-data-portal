import sys
import pathlib
import tempfile
import time
import ujson

sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
from util import sanitize_triplets_from_query

from dao import NAME_MAP, get_cb_meta_ids, get_cb_documents


def test_download():
    start_time = time.perf_counter()

    cb_data = "primary_data"
    bucket = NAME_MAP[cb_data]["bucket"]
    collection = NAME_MAP[cb_data]["collection"]

    query = "geo:country/ocean:South Africa"
    # query = "recordsetcode:na:DS-KMTPD1"
    triplets = sanitize_triplets_from_query(query, "full")
    print("TRIPLETS GENERATED", file=sys.stderr)

    end_time = time.perf_counter()
    print(f"TRIPLETS {end_time - start_time}", file=sys.stderr)

    meta_ids = get_cb_meta_ids(triplets, bucket, collection)
    print("META_IDS RETRIEVED", file=sys.stderr)

    end_time = time.perf_counter()
    print(f"META_IDS {end_time - start_time}", file=sys.stderr)

    BATCH_SIZE = 10000

    with tempfile.NamedTemporaryFile(mode="w") as tmp_file:
        batch_counter = 0
        batch = meta_ids[BATCH_SIZE * batch_counter : BATCH_SIZE * (batch_counter + 1)]

        while batch:
            results = get_cb_documents(batch, bucket, collection)

            for row in results:
                tmp_file.write(ujson.dumps(row, default=str) + "\n")

            print(f"{len(results)}_DOCS WRITTEN", file=sys.stderr)

            end_time = time.perf_counter()
            print(f"{len(results)}_DOCS {end_time - start_time}", file=sys.stderr)

            batch_counter += 1
            batch = meta_ids[
                BATCH_SIZE * batch_counter : BATCH_SIZE * (batch_counter + 1)
            ]


if __name__ == "__main__":
    test_download()
