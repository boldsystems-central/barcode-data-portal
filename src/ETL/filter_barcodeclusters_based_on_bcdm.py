import argparse
import ujson as json

_SPECIMEN_CENTRIC = [
    "bin_uri",
    "collection_date_start",
    "coord",
    "country/ocean",
    "identified_by",
    "inst",
    "species",
]


def set_aggregates(raw_aggregates, field):
    aggregates = {}
    for key, aggregate_list in raw_aggregates.items():
        if field in _SPECIMEN_CENTRIC:
            aggregates[key] = len(set(aggregate_list))
        else:
            aggregates[key] = len(aggregate_list)

    return aggregates


parser = argparse.ArgumentParser(
    description="Subsamples barcodcluster data file based on the BINs contained within the BCDM file"
)
parser.add_argument("--bcdm", type=str, help="bcdm file")
parser.add_argument("--barcodeclusters", type=str, help="barcodeclusters")

args = parser.parse_args()

whitelist = {}

with open(args.bcdm) as bcdm:
    for line in bcdm:
        data = json.loads(line)
        if "bin_uri" in data:
            whitelist[data["bin_uri"]] = True


with open(args.barcodeclusters) as barcodeclusters:
    for line in barcodeclusters:
        data = json.loads(line)
        if data["barcodecluster.uri"] in whitelist:
            print(line.strip())
