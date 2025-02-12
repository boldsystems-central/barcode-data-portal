import sys
import pathlib
import ujson


sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
from dao import (
    get_total_seqs_stat,
    get_total_bins_stat,
    get_animal_species_stat,
    get_plant_species_stat,
    get_fungi_species_stat,
    get_other_species_stat,
)
from util import STATS_META_ID, write_cache_with_meta_ids


def generate_stats_cache():
    general_stats = {
        "total seqs": get_total_seqs_stat(),
        "total bins": get_total_bins_stat(),
        "animal species": get_animal_species_stat(),
        "plant species": get_plant_species_stat(),
        "fungi species": get_fungi_species_stat(),
        "other species": get_other_species_stat(),
    }

    docs_to_cache = {STATS_META_ID: ujson.dumps(general_stats)}
    write_cache_with_meta_ids(docs_to_cache, None)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    generate_stats_cache()
