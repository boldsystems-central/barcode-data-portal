import pathlib
import sys


sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
from util import generate_query_id_from_triplets, sanitize_triplets_from_query


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--triplets",
        required=True,
        help="Triplets to encode into query ID",
    )
    parser.add_argument(
        "-e",
        "--extent",
        required=True,
        help="Extent to encode into query ID",
    )
    args = parser.parse_args()

    triplets = args.triplets
    extent = args.extent

    print(
        generate_query_id_from_triplets(sanitize_triplets_from_query(triplets, extent))
    )
