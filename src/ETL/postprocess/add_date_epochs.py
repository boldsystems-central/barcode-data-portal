import datetime
import sys
import ujson as json

_DATE_FIELDS = [
    "bin_created_date",
    "collection_date_end",
    "collection_date_start",
    "processid_minted_date",
    "sequence_upload_date",
]


for line in sys.stdin:
    record = json.loads(line)

    for date_field in _DATE_FIELDS:
        if date_field in record:
            record[f"{date_field}_epoch"] = datetime.datetime.strptime(
                record[date_field], "%Y-%m-%d"
            ).timestamp()

    print(json.dumps(record) + "\n")
