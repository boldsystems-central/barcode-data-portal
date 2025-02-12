import json
import sys

doc = json.load(sys.stdin)

for key, aggregates in doc["aggregates"].items():
    doc[key] = aggregates
del doc["aggregates"]


def reduce_summary_aggregates(documents):
    merged_document = {}
    for document in documents:
        for field in document.keys():
            if type(document.get(field)) == dict:
                merged_document.setdefault(field, {})
                for key in document.get(field, {}).keys():
                    merged_document[field].setdefault(key, 0)
                    merged_document[field][key] += document[field][key]

    return merged_document


print(json.dumps(reduce_summary_aggregates([doc])))
