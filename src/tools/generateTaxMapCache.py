import sys
import pathlib
import ujson
from collections import defaultdict


sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
from dao import get_cb_taxonomy_paths
from util import (
    sanitize_triplets_from_query,
    generate_query_id_from_triplets,
    generate_tax_map_meta_id,
    write_cache_with_meta_ids,
)


_NODE_THRESHOLD = 1000
_TAX_RANKS = [
    "kingdom",
    "phylum",
    "class",
    "`order`",
    "family",
    "subfamily",
    "tribe",
    "genus",
    "species",
    "subspecies",
]
_TAX_THRESHOLD = 0.95


def generate_tax_map_cache(triplet_queries):
    docs_to_cache = {}

    for query in triplet_queries:
        triplets = sanitize_triplets_from_query(
            query, "full"
        )  # For consistency in cache access
        query_id = generate_query_id_from_triplets(triplets)

        tax_map_meta_id = generate_tax_map_meta_id(query_id, _NODE_THRESHOLD)

        fields = _TAX_RANKS

        taxonomy_lineage = {}
        taxonomy = {}

        documents = get_cb_taxonomy_paths(triplets)

        # 1. Assessment block
        # Detect name duplicates for collision
        # Count unique names by rank
        unique_names = {}
        nonunique_names = set()
        names_by_rank = defaultdict(set)
        for document in documents:
            kingdom = document["kingdom"]
            for rank in fields:
                rank = rank.replace("`", "")
                if name := document.get(rank):
                    if name in unique_names and kingdom != unique_names[name]:
                        nonunique_names.add(name)
                    unique_names[name] = kingdom
                    names_by_rank[rank].add(name)

        resolve_nonunique_names = lambda name, kingdom: (
            f"{name} ({kingdom})" if name in nonunique_names else name
        )

        count_by_rank = defaultdict(lambda: 0)
        count_by_rank.update(
            {rank: len(names) for rank, names in names_by_rank.items()}
        )

        # 2. Operation/sanitize block
        # Construct stats and lineages with cleansed name
        # Keep/drop columns by node_threshold
        count = 0
        columns = []
        for rank in fields:
            rank = rank.replace("`", "")
            if count < _NODE_THRESHOLD:
                columns.append(rank)
            count += count_by_rank[rank]

        lineage = defaultdict(lambda: {})
        stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))
        for document in documents:
            count = document["specimens"]
            kingdom = document["kingdom"]
            stats[kingdom]["kingdom"][kingdom] += count

            for i in range(1, len(columns)):
                child_rank = columns[i]
                child = resolve_nonunique_names(document.get(child_rank), kingdom)
                if child:
                    j = 1

                    parent_rank = columns[i - j]
                    parent = resolve_nonunique_names(document.get(parent_rank), kingdom)
                    while not parent and i - j > 0:
                        j += 1
                        parent_rank = columns[i - j]
                        parent = resolve_nonunique_names(
                            document.get(parent_rank), kingdom
                        )

                    lineage[kingdom][child] = parent
                    stats[kingdom][child_rank][child] += count

        # 3. Postprocess block
        # Detect predominant kingdom
        # Exclude kingdom column from lineage if there is a predominant kingdom
        per_kingdom_frequency = defaultdict(lambda: 0)
        for kingdom, frequency in stats.items():
            per_kingdom_frequency[kingdom] += frequency["kingdom"][kingdom]
        total = sum(per_kingdom_frequency.values())

        if any(
            [
                frequency / total > _TAX_THRESHOLD
                for frequency in per_kingdom_frequency.values()
            ]
        ):
            predominant_kingdoms = [
                kingdom
                for kingdom, frequency in per_kingdom_frequency.items()
                if frequency / total > _TAX_THRESHOLD
            ]
            kingdoms_to_pop = []
            for kingdom in stats.keys():
                if kingdom not in predominant_kingdoms:
                    kingdoms_to_pop.append(kingdom)

            for kingdom in kingdoms_to_pop:
                lineage.pop(kingdom)
                stats.pop(kingdom)

        taxonomy_lineage = {}
        for kingdom_lineage in lineage.values():
            taxonomy_lineage.update(kingdom_lineage)

        taxonomy = {}
        for field in fields:
            taxonomy[field.replace("`", "")] = {}
        for kingdom_stats in stats.values():
            for rank, frequencies in kingdom_stats.items():
                taxonomy[rank].update(frequencies)

        tax_map = {
            "taxonomy_lineage": taxonomy_lineage,
            "taxonomy": taxonomy,
        }

        docs_to_cache[tax_map_meta_id] = ujson.dumps(tax_map, default=str)

    write_cache_with_meta_ids(docs_to_cache, None)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input JSON as list of triplet queries (list of lists)",
    )
    args = parser.parse_args()

    input_file = args.input

    with open(input_file) as fp:
        triplet_queries = ujson.load(fp)

    generate_tax_map_cache(triplet_queries)
