from fastapi import APIRouter, Path, Query, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List

import httpx
import pathlib
import re
import sys
import time
import ujson
import urllib.parse
from collections import defaultdict

try:
    import dao
    import util
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import dao
    import util

route = APIRouter(tags=["taxonomy"])


class TaxonomyDescription(BaseModel):
    text: str
    url: str


class TaxonomyHierarchySummary(BaseModel):
    phylum: List[dict]
    class_: List[dict] = Field(alias="class")
    order: List[dict]
    family: List[dict]
    subfamily: List[dict]
    tribe: List[dict]
    genus: List[dict]
    species: List[dict]
    subspecies: List[dict]


class TaxonomyRankSummary(BaseModel):
    kingdom: dict
    phylum: dict
    class_: dict = Field(alias="class")
    order: dict
    family: dict
    subfamily: dict
    tribe: dict
    genus: dict
    species: dict
    subspecies: dict


class TaxonomySummary(BaseModel):
    taxonomy: TaxonomyRankSummary


class TaxonomyMapSummary(BaseModel):
    taxonomy_lineage: dict
    taxonomy: TaxonomyRankSummary


_TAX_MAP_CACHE_THRESHOLD = 2  # In seconds; if tax map generation exceeds this, cache
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


rank_names = {
    "species": 17,
    "genus": 14,
    "subfamily": 12,
    "family": 11,
    "order": 8,
    "class": 5,
    "phylum": 2,
    "speci": 17,
    "subfa": 12,
    "famil": 11,
    "phylu": 2,
}


# Simulating a manual wiki entry retrieval
def get_manual_wiki_entry(name_to_check):
    manual_wiki_entries = {
        "2:Cnidaria": "Cnidaria description from manual wiki",
        "2:Porifera": "Porifera description from manual wiki",
    }
    return {"text": manual_wiki_entries.get(name_to_check, ""), "article": ""}


@route.get(
    "/taxonomy/description",
    response_model=TaxonomyDescription,
    response_description="Taxonomy Description",
)
async def retrieve_taxonomy_description(
    request: Request,
    name: str = Query(title="Taxonomy Name"),
    rank: str = Query(title="Taxonomy Rank"),
):
    """
    Retrieve a taxonomy description from BOLD as a proxy endpoint.

    - **name**: Taxonomy name
    - **rank**: Taxonomy rank
    """
    description = {}

    name_to_check = name
    wiki_text = ""

    # If rank is provided, adjust name to check and look for manual wiki
    if rank:
        if not rank.isdigit():
            rank = rank_names.get(rank, rank)
        name_to_check = f"{rank}:{name}"
        manual_wiki = get_manual_wiki_entry(name_to_check)
        wiki_text = manual_wiki["text"]

    # If nothing found in manual, search Wikipedia
    if not wiki_text:
        search_text = urllib.parse.quote(name)  # URL encoding
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&titles={search_text}&redirects=1&exintro=1&explaintext=1"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(wiki_url)
                wiki_response = response.json()
                pages = wiki_response["query"]["pages"]
                first_page = next(iter(pages.values()))

                if first_page["pageid"] == -1:
                    wiki_text = "No Wikipedia page found for this term."
                else:
                    wiki_text = first_page.get("extract", "")
                    wiki_text = re.sub(r"\s*\(\s*\)\s*", " ", wiki_text).strip()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve description, please try again",
            )

    description = {"text": wiki_text, "url": str(request.url)}

    return description


@route.get(
    "/taxonomy/hierarchy",
    response_model=TaxonomyHierarchySummary,
    response_description="Taxonomy Hierarchy",
)
async def retrieve_taxonomy_hierarchy(
    name: str = Query(title="Taxonomy Name"),
    rank: str = Query(title="Taxonomy Rank"),
):
    """
    Generate a taxonomy hierarchy based on taxonomy name and rank.
    Returns a frequency of taxonomy names found in query by rank across
    the hierarchy, from all rank levels higher than the current rank
    up to the next immediate rank.

    - **name**: Taxonomy name
    - **rank**: Taxonomy rank
    """
    tax_doc = {rank.replace("`", ""): [] for rank in _TAX_RANKS}

    tax_data = dao.get_cb_taxonomy_summaries_by_name_and_rank(name, rank)
    if tax_data:
        tax_summary = tax_data[0]
        tax_doc[rank].append(tax_summary)

        taxid = tax_summary["taxid"]
        parent_taxid = tax_summary["parent_taxid"]

        parent_tax_data = dao.get_cb_taxonomy_summaries_by_taxids([taxid])
        # Loop up the hierarchy and fill information
        while parent_tax_data:
            tax_summary = parent_tax_data[0]
            rank = tax_summary["rank_name"]
            tax_doc[rank].append(tax_summary)

            parent_taxid = tax_summary["parent_taxid"]
            parent_tax_data = dao.get_cb_taxonomy_summaries_by_taxids([parent_taxid])

        # Retrieve immediate child summaries in hierarchy
        child_tax_data = dao.get_cb_taxonomy_summaries_by_parent_taxids([taxid])
        for child_tax_summary in child_tax_data:
            rank = child_tax_summary["rank_name"]
            tax_doc[rank].append(child_tax_summary)

    return tax_doc


@route.get(
    "/taxonomy/{query_id}",
    response_model=TaxonomySummary,
    response_description="Taxonomy Summary",
)
async def generate_taxonomy_summary(
    query_id: str = Path(title="Documents query ID"),
):
    """
    Generate a taxonomy summary from an encoded query (`query_id`).
    Returns a frequency of taxonomy names found in query by rank.

    - **query_id**: Encoded triplets query from `/api/query`
    """
    triplets = util.get_triplets_from_query_id(query_id)
    fields = _TAX_RANKS

    # TODO: Integrate summary data
    cb_data = "primary_data"
    bucket = dao.NAME_MAP[cb_data]["bucket"]
    collection = dao.NAME_MAP[cb_data]["collection"]

    documents = dao.get_cb_group_by_field_documents(
        triplets, fields, bucket, collection
    )
    stats = defaultdict(lambda: {})
    for row in documents:
        if val := row.get("val"):
            count = len(set(row["processids"]))
            stats[row["field"].replace("`", "")][val] = count

    taxonomy = {}
    for field in fields:
        taxonomy[field.replace("`", "")] = {}
    taxonomy.update(stats)

    return {"taxonomy": taxonomy}


@route.get(
    "/taxonomy/{query_id}/map",
    response_model=TaxonomyMapSummary,
    response_description="Taxonomy Map Summary",
)
async def generate_taxonomy_map_summary(
    query_id: str = Path(title="Documents query ID"),
    node_threshold: int = Query(
        default=1000, title="Node threshold where child ranks are omitted"
    ),
):
    """
    Generate a taxonomy tree map from an encoded query (`query_id`).
    Returns a mapping of child-parent relations and frequency of taxonomy names
    found in query by rank. If one or more kingdoms' frequencies exceed the
    fractional threshold of `TAX_THRESHOLD`, other kingdoms not meeting the threshold
    will be omitted from the result.

    - **query_id**: Encoded triplets query from `/api/query`
    - **node_threshold**: Threshold to limit cumulative node count descending
                          through taxonomy ranks
    """
    triplets = util.get_triplets_from_query_id(query_id)

    triplets[-1] = "full"  # For consistency in cache access
    query_id = util.generate_query_id_from_triplets(triplets)

    tax_map_meta_id = util.generate_tax_map_meta_id(query_id, node_threshold)

    if tax_map := util.get_cache_from_meta_ids([tax_map_meta_id])[0]:
        return ujson.loads(tax_map)

    start_time = time.perf_counter()

    fields = _TAX_RANKS

    taxonomy_lineage = {}
    taxonomy = {}

    search_summary = True
    for triplet in triplets[:-1]:
        if (
            not triplet.startswith("geo")
            and not triplet.startswith("tax")
            and not triplet.startswith("inst:name")
        ):
            search_summary = False

    if search_summary:
        documents = []
        if meta_ids := util.get_summary_cache_from_query_id(query_id):
            results = util.get_cache_from_meta_ids(meta_ids)
            if all(results):
                for result in results:
                    document = ujson.loads(result)
                    document["specimens"] = document["counts"]["specimens"]
                    documents.append(document)

        if not documents:
            cb_data = "summary"
            bucket = dao.NAME_MAP[cb_data]["bucket"]
            collection = dao.NAME_MAP[cb_data]["collection"]

            documents = dao.get_cb_field_values(
                triplets, fields + ["counts.specimens"], bucket, collection
            )
    else:
        documents = dao.get_cb_taxonomy_paths(triplets)

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
    count_by_rank.update({rank: len(names) for rank, names in names_by_rank.items()})

    # 2. Operation/sanitize block
    # Construct stats and lineages with cleansed name
    # Keep/drop columns by node_threshold
    count = 0
    columns = []
    for rank in fields:
        rank = rank.replace("`", "")
        if count < node_threshold:
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
                    parent = resolve_nonunique_names(document.get(parent_rank), kingdom)

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

    end_time = time.perf_counter()

    if end_time - start_time > _TAX_MAP_CACHE_THRESHOLD:
        docs_to_cache = {tax_map_meta_id: ujson.dumps(tax_map, default=str)}
        util.write_cache_with_meta_ids(docs_to_cache, 86400)  # 1 day TTL

    return tax_map
