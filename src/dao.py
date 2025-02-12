import datetime
import logging
import re
import time
import ujson
import uuid
from collections import defaultdict
from functools import lru_cache

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import (
    ClusterOptions,
    ClusterTimeoutOptions,
    QueryOptions,
    GetMultiOptions,
)

from settings import settings

query_logger = logging.getLogger("query_logger")

_ID_PATTERN = re.compile(r"\W")
EXTENT_LIMIT = {"limited": 1000, "large": 20000}

# Couchbase defaults
_CB_ENDPOINT = settings.couchbase_endpoint
_CB_USER = settings.couchbase_user
_CB_PASS = settings.couchbase_password
_CB_TIMEOUT = settings.couchbase_timeout

# TODO: Refine timeout options
_CB_CLUSTER = Cluster(
    _CB_ENDPOINT,
    ClusterOptions(PasswordAuthenticator(_CB_USER, _CB_PASS)),
    timeout_options=ClusterTimeoutOptions(
        bootstrap_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        connect_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        resolve_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        kv_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        kv_durable_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        views_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        query_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        analytics_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        search_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        management_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        dns_srv_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
        config_idle_redial_timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
    ),
)
_CB_CLUSTER.wait_until_ready(datetime.timedelta(seconds=5))

NAME_MAP = {
    "primary_data": {"bucket": "BCDM", "collection": "primary"},
    "summary": {"bucket": "DERIVED", "collection": "tax_geo_inst_summaries"},
    "country_summary": {"bucket": "DERIVED", "collection": "country_summaries"},
    "inst_summary": {"bucket": "DERIVED", "collection": "institution_summaries"},
    "seqsite_summary": {
        "bucket": "DERIVED",
        "collection": "sequence_run_site_summaries",
    },
    "bin_summary": {"bucket": "DERIVED", "collection": "bin_summaries"},
    "dataset_summary": {"bucket": "DERIVED", "collection": "dataset_summaries"},
    "primer_summary": {"bucket": "DERIVED", "collection": "primer_summaries"},
    "taxonomy_summary": {"bucket": "DERIVED", "collection": "taxonomy_summaries"},
    "terms": {"bucket": "DERIVED", "collection": "accepted_terms"},
    "ancillary": {"bucket": "ANCILLARY"},
}

# Column mapping based on the scope and subscope
# TODO: Revisit 'all' scope
COLUMN_MAPPING = {
    "tax": {
        "kingdom": "kingdom",
        "phylum": "phylum",
        "class": "class",
        "order": "order",
        "family": "family",
        "subfamily": "subfamily",
        "tribe": "tribe",
        "genus": "genus",
        "species": "species",
        "subspecies": "subspecies",
    },
    "geo": {
        "country/ocean": "country/ocean",
        "country": "country/ocean",
        "ocean": "country/ocean",
        "province/state": "province/state",
        "province": "province/state",
        "state": "province/state",
        "region": "region",
    },
    "inst": {
        "name": "inst",
        "seqsite": "sequence_run_site",
    },
    "ids": {
        "processid": "processid",
        "sampleid": "sampleid",
        "insdcacs": "insdc_acs",
    },
    "bin": {
        "uri": "bin_uri",
    },
    "recordsetcode": {
        "code": "bold_recordset_code_arr",
    },
    "all": {
        "na": "na",
    },
}

###
# Couchbase DAO
###


def _get_cb_cluster():
    return _CB_CLUSTER


def _get_scopes():
    return list(COLUMN_MAPPING.keys())


def _triplets_to_condition(triplets: list):
    # Query object has 3 layers: dict (scope), dict(subscope), list(values). This
    # is used to build the params and conditions for querying. This structure makes
    # it easier to group those of the same scope together
    query_obj = defaultdict(lambda: defaultdict(list))

    for triplet in triplets[:-1]:  # Exclude extent from triplet set
        # Error handling if not a valid triplet
        if len(triplet.split(":", 2)) != 3:
            raise Exception(f"'{triplet}' is an invalid triplet")

        scope, subscope, value = triplet.split(":", 2)

        # Resolve column name
        column = COLUMN_MAPPING.get(scope, {}).get(subscope)

        # Skip if column not found
        if not column:
            continue

        query_obj[scope][column].append(value)

    # Error handling if nothing in query_obj
    if not query_obj:
        raise Exception("Query invalid - built query object is empty")

    conditions_list = []
    params = {}

    # Loop through query_obj and join together those in the same scope with an OR
    for scope, columns in query_obj.items():
        if scope == "all":
            conditions_list.append("1 = 1")
            continue

        # Update param dict with current scope. Used later to substitute for querying
        params.update(
            {
                f"{scope}_{re.sub(_ID_PATTERN, '_', column)}": values
                for column, values in columns.items()
            }
        )

        if scope == "recordsetcode":
            condition_set = " OR ".join(
                [
                    f"ANY code IN bold_recordset_code_arr SATISFIES code IN ${scope}_{re.sub(_ID_PATTERN, '_', column)} END"
                    for column in columns.keys()
                ]
            )
        else:
            # Build an OR-joined condition and add to conditions list
            condition_set = " OR ".join(
                [
                    f"`{column}` IN ${scope}_{re.sub(_ID_PATTERN, '_', column)}"
                    for column in columns.keys()
                ]
            )
            condition_set = f"({condition_set})"

        conditions_list.append(condition_set)

    # Join all the conditions (not in same scope) with an AND
    conditions = " AND ".join(conditions_list)

    return conditions, params


def _triplets_to_condition_terms(triplets: list):
    # Column mapping based on the scope and subscope
    column_mapping = {
        "tax": {
            "kingdom": "kingdom",
            "phylum": "phylum",
            "class": "class",
            "order": "order",
            "family": "family",
            "subfamily": "subfamily",
            "tribe": "tribe",
            "genus": "genus",
            "species": "species",
            "subspecies": "subspecies",
        },
        "geo": {
            "country/ocean": "country/ocean",
            "country": "country/ocean",
            "ocean": "country/ocean",
            "province/state": "province/state",
            "province": "province/state",
            "state": "province/state",
            "region": "region",
        },
        "inst": {
            "name": "name",
        },
        "ids": {
            "processid": "processid",
            "sampleid": "sampleid",
            "insdcacs": "insdcacs",
        },
        "bin": {
            "uri": "uri",
        },
        "recordsetcode": {
            "code": "code",
        },
        "all": {
            "na": "na",
        },
    }

    # Query object has 3 layers: dict (scope), dict(subscope), list(values). This
    # is used to build the params and conditions for querying. This structure makes
    # it easier to group those of the same scope together
    query_obj = defaultdict(lambda: defaultdict(list))

    for triplet in triplets[:-1]:  # Exclude extent from triplet set
        # Error handling if not a valid triplet
        if len(triplet.split(":", 2)) != 3:
            raise Exception(f"'{triplet}' is an invalid triplet")

        scope, subscope, value = triplet.split(":", 2)

        # Resolve column name
        column = column_mapping.get(scope, {}).get(subscope)

        # Skip if column not found
        if not column:
            continue

        query_obj[scope][column].append(value)

    # Error handling if nothing in query_obj
    if not query_obj:
        raise Exception("Query invalid - built query object is empty")

    conditions_list = []
    params = {}

    # Loop through query_obj and join together those in the same scope with an OR
    for scope, columns in query_obj.items():
        if scope == "all":
            conditions_list.append("1 = 1")
            continue

        # Update param dict with current scope. Used later to substitute for querying
        params.update(
            {
                f"{scope}_{re.sub(_ID_PATTERN, '_', column)}": values
                for column, values in columns.items()
            }
        )

        # Build an OR-joined condition and add to conditions list
        condition_set = " OR ".join(
            [
                f"(`scope` = '{scope}' AND field = '{column}' AND term IN ${scope}_{re.sub(_ID_PATTERN, '_', column)})"
                for column in columns.keys()
            ]
        )

        conditions_list.append(condition_set)

    # Join all the conditions with an OR
    conditions = " OR ".join(conditions_list)

    return conditions, params


def get_cb_meta_ids(triplets, bucket, collection):
    conditions, params = _triplets_to_condition(triplets)
    extent = triplets[-1]

    query = f"""
        SELECT meta().id
        FROM `{bucket}`.`_default`.`{collection}`
        WHERE {conditions}
    """
    if extent == "zero":
        query = f"{query} AND 1 = 0"
    elif extent != "full":
        query = f"{query} LIMIT {EXTENT_LIMIT.get(extent, 1)}"

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_meta_ids - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)}"
    )

    start_time = time.perf_counter()

    id_results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters=params,
            metrics=True,
        ),
    )

    meta_ids = []
    for meta_id in id_results:
        meta_ids.append(meta_id["id"])

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_meta_ids - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)} {id_results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return meta_ids


def get_cb_field_values(triplets, fields, bucket, collection, limit=None):
    if not fields:
        return []

    conditions, params = _triplets_to_condition(triplets)

    query = f"""
        SELECT
            {', '.join(fields)}
        FROM `{bucket}`.`_default`.`{collection}`
        WHERE {conditions}
    """
    if limit:
        query = f"{query} LIMIT {limit}"

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_field_values - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters=params,
            metrics=True,
        ),
    )

    documents = []
    for row in results.rows():
        documents.append(row)

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_field_values - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return documents


def get_cb_group_by_field_documents(triplets, fields, bucket, collection):
    if not fields:
        return []

    conditions, params = _triplets_to_condition(triplets)

    queries = [
        f"""
        SELECT
            "{field}" AS field,
            {field} AS val,
            ARRAY_AGG(processid) AS processids
        FROM `{bucket}`.`_default`.`{collection}`
        WHERE {conditions}
        GROUP BY {field}
    """
        for field in fields
    ]
    query = " UNION ".join(queries)

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_group_by_field_documents - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters=params,
            metrics=True,
        ),
    )

    documents = []
    for row in results.rows():
        documents.append(row)

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_group_by_field_documents - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return documents


def get_cb_documents(meta_ids, bucket, collection):
    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_documents - UUID: {query_uuid} {len(meta_ids)} meta_id(s) "
    )

    start_time = time.perf_counter()

    cluster = _get_cb_cluster()
    bucket = cluster.bucket(bucket)
    scope = bucket.scope("_default")
    collection = scope.collection(collection)

    # TODO: Attempt to recover documents that failed to fetch?
    docs = collection.get_multi(
        meta_ids,
        GetMultiOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT), return_exceptions=False
        ),
    )
    result_map = {}
    for value in docs.results.values():
        result_map[value.key] = value.content_as[dict]
    results = [result_map[meta_id] for meta_id in meta_ids]

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_documents - UUID: {query_uuid} {len(results)} result(s) {end_time - start_time}"
    )

    return results


###
# Terms DAO
###


def query_term_hits(partial_term, term_scope, limit):
    clause = f"standardized_term LIKE $partial_term || '%'"
    if term_scope:
        clause += f" AND `scope` = $scope"

    query = f"""
        SELECT *
        FROM `{NAME_MAP["terms"]["bucket"]}`.`_default`.`{NAME_MAP["terms"]["collection"]}`
        WHERE {clause}
        ORDER BY records DESC, standardized_term ASC
        LIMIT {limit}
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start query_term_hits - UUID: {query_uuid} {' '.join(query.split())} {[partial_term, term_scope]}"
    )

    start_time = time.perf_counter()

    term_results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters={"partial_term": partial_term, "scope": term_scope},
            metrics=True,
        ),
    )

    term_hits = []
    for row in term_results.rows():
        term_hits.append(row["accepted_terms"])

    end_time = time.perf_counter()

    query_logger.info(
        f"End query_term_hits - UUID: {query_uuid} {' '.join(query.split())} {[partial_term, term_scope]} {term_results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return term_hits


def get_cb_counts(triplets):
    # TODO: Merge with standard fields fetch? Need to resolve difference in triplets_to_condition
    conditions, params = _triplets_to_condition_terms(triplets)

    query = f"""
        SELECT records, summaries
        FROM `{NAME_MAP["terms"]["bucket"]}`.`_default`.`{NAME_MAP["terms"]["collection"]}`
        WHERE {conditions}
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_counts - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)}"
    )

    start_time = time.perf_counter()

    term_results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters=params,
            metrics=True,
        ),
    )

    stats = {"records": 0, "summaries": 0}
    for row in term_results.rows():
        stats["records"] += row["records"]
        stats["summaries"] += row["summaries"]

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_counts - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)} {term_results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return stats


@lru_cache()
def resolve_term(term):
    # TODO: Merge with standard fields fetch? But WHERE clause needs to be less strict?
    query = f"""
        SELECT `scope`, field
        FROM `{NAME_MAP["terms"]["bucket"]}`.`_default`.`{NAME_MAP["terms"]["collection"]}`
        WHERE term = $term
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start resolve_term - UUID: {query_uuid} {' '.join(query.split())} {term}"
    )

    start_time = time.perf_counter()

    term_results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters={"term": term},
            metrics=True,
        ),
    )

    triplets = []
    for row in term_results.rows():
        scope = row["scope"]
        subscope = row["field"]
        triplets.append(f"{scope}:{subscope}:{term}")

    end_time = time.perf_counter()

    query_logger.info(
        f"End resolve_term - UUID: {query_uuid} {' '.join(query.split())} {term} {term_results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return triplets


###
# Ancillary DAO
###


def get_cb_ancillary_documents(
    ancillary_collection,
    derived_collection,
    ancillary_join_key,
    derived_join_key,
    join_type="LEFT JOIN",
    ancillary_key=None,
    values=None,
):
    query = f"""
        SELECT registry.*, summary.counts.*
        FROM `{NAME_MAP["ancillary"]["bucket"]}`.`_default`.`{ancillary_collection}` as registry
        {join_type}
        `{NAME_MAP["summary"]["bucket"]}`.`_default`.`{derived_collection}` as summary
        ON
        registry.`{ancillary_join_key}` = summary.`{derived_join_key}`
    """
    if ancillary_key:
        query += f"""
            WHERE registry.`{ancillary_key}` IN $values
        """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_ancillary_documents - UUID: {query_uuid} {' '.join(query.split())} {values}"
    )

    start_time = time.perf_counter()

    anc_results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters={"values": values},
            metrics=True,
        ),
    )

    documents = []
    for row in anc_results.rows():
        documents.append(row)

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_ancillary_documents - UUID: {query_uuid} {' '.join(query.split())} {values} {anc_results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return documents


def get_cb_ancillary_taxonomy_documents(limit=100):
    query = f"""
        SELECT registry.*
        FROM `{NAME_MAP["ancillary"]["bucket"]}`.`_default`.`taxonomies` as registry
        LIMIT {limit}
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_ancillary_taxonomy_documents - UUID: {query_uuid} {' '.join(query.split())} {limit}"
    )

    start_time = time.perf_counter()

    anc_results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            metrics=True,
        ),
    )

    documents = []
    for row in anc_results.rows():
        documents.append(row)

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_ancillary_taxonomy_documents - UUID: {query_uuid} {' '.join(query.split())} {limit} {anc_results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return documents


###
# Special Queries DAO
###


def get_cb_taxonomy_summaries_by_name_and_rank(name, rank):
    query = f"""
        SELECT `{NAME_MAP["taxonomy_summary"]["collection"]}`.*
        FROM `{NAME_MAP["taxonomy_summary"]["bucket"]}`.`_default`.`{NAME_MAP["taxonomy_summary"]["collection"]}`
        WHERE taxon = $name AND rank_name = $rank
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_taxonomy_summaries_by_name_and_rank - UUID: {query_uuid} {' '.join(query.split())} {[name, rank]}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters={"name": name, "rank": rank},
            metrics=True,
        ),
    )

    documents = []
    for row in results.rows():
        documents.append(row)

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_taxonomy_summaries_by_name_and_rank - UUID: {query_uuid} {' '.join(query.split())} {[name, rank]} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return documents


def get_cb_taxonomy_summaries_by_taxids(taxids):
    query = f"""
        SELECT `{NAME_MAP["taxonomy_summary"]["collection"]}`.*
        FROM `{NAME_MAP["taxonomy_summary"]["bucket"]}`.`_default`.`{NAME_MAP["taxonomy_summary"]["collection"]}`
        WHERE taxid IN $taxids
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_taxonomy_summaries_by_taxids - UUID: {query_uuid} {' '.join(query.split())} {taxids}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters={"taxids": taxids},
            metrics=True,
        ),
    )

    documents = []
    for row in results.rows():
        documents.append(row)

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_taxonomy_summaries_by_taxids - UUID: {query_uuid} {' '.join(query.split())} {taxids} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return documents


def get_cb_taxonomy_summaries_by_parent_taxids(parent_taxids):
    query = f"""
        SELECT `{NAME_MAP["taxonomy_summary"]["collection"]}`.*
        FROM `{NAME_MAP["taxonomy_summary"]["bucket"]}`.`_default`.`{NAME_MAP["taxonomy_summary"]["collection"]}`
        WHERE parent_taxid IN $parent_taxids
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_taxonomy_summaries_by_parent_taxids - UUID: {query_uuid} {' '.join(query.split())} {parent_taxids}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters={"parent_taxids": parent_taxids},
            metrics=True,
        ),
    )

    documents = []
    for row in results.rows():
        documents.append(row)

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_taxonomy_summaries_by_parent_taxids - UUID: {query_uuid} {' '.join(query.split())} {parent_taxids} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return documents


def get_cb_taxonomy_paths(triplets):
    conditions, params = _triplets_to_condition(triplets)

    query = f"""
        SELECT kingdom, phylum, class, `order`, family, subfamily,
            tribe, genus, species, subspecies, ARRAY_AGG(processid) AS processids
        FROM `{NAME_MAP["primary_data"]["bucket"]}`.`_default`.`{NAME_MAP["primary_data"]["collection"]}`
        WHERE {conditions}
        GROUP BY kingdom, phylum, class, `order`, family, subfamily,
            tribe, genus, species, subspecies
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_cb_taxonomy_paths - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            named_parameters=params,
            metrics=True,
        ),
    )

    documents = []
    for row in results.rows():
        row["specimens"] = len(set(row["processids"]))
        documents.append(row)

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_cb_taxonomy_paths - UUID: {query_uuid} {' '.join(query.split())} {ujson.dumps(params)} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return documents


def get_total_seqs_stat():
    query = f"""
        SELECT COUNT(DISTINCT processid) AS count
        FROM `{NAME_MAP["primary_data"]["bucket"]}`.`_default`.`{NAME_MAP["primary_data"]["collection"]}`
        WHERE marker_code IN ['COI-5P', 'rbcL', 'matK', 'ITS', 'rbcLa'] AND nuc_basecount > 486
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_total_seqs_stat - UUID: {query_uuid} {' '.join(query.split())}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            metrics=True,
        ),
    )

    stat = 0
    for row in results.rows():
        stat = row["count"]

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_total_seqs_stat - UUID: {query_uuid} {' '.join(query.split())} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return stat


def get_total_bins_stat():
    query = f"""
        SELECT COUNT(DISTINCT bin_uri) AS count
        FROM `{NAME_MAP["primary_data"]["bucket"]}`.`_default`.`{NAME_MAP["primary_data"]["collection"]}`
        WHERE bin_uri IS NOT NULL
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_total_bins_stat - UUID: {query_uuid} {' '.join(query.split())}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            metrics=True,
        ),
    )

    stat = 0
    for row in results.rows():
        stat = row["count"]

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_total_bins_stat - UUID: {query_uuid} {' '.join(query.split())} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return stat


def get_animal_species_stat():
    query = f"""
        SELECT COUNT(DISTINCT species) AS count
        FROM `{NAME_MAP["primary_data"]["bucket"]}`.`_default`.`{NAME_MAP["primary_data"]["collection"]}`
        WHERE species IS NOT MISSING
            AND nuc_basecount > 486 AND marker_code IN ['COI-5P']
            AND kingdom = 'Animalia'
            AND species NOT LIKE '% % %'
            AND species NOT LIKE '% sp'
            AND species NOT LIKE '%.%'
            AND species NOT LIKE '%.%'
            AND NOT REGEXP_CONTAINS(species, '[0-9]')
            AND species NOT LIKE '%Janzen%'
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_animal_species_stat - UUID: {query_uuid} {' '.join(query.split())}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            metrics=True,
        ),
    )

    stat = 0
    for row in results.rows():
        stat = row["count"]

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_animal_species_stat - UUID: {query_uuid} {' '.join(query.split())} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return stat


def get_plant_species_stat():
    query = f"""
        SELECT COUNT(DISTINCT species) AS count
        FROM `{NAME_MAP["primary_data"]["bucket"]}`.`_default`.`{NAME_MAP["primary_data"]["collection"]}`
        WHERE species IS NOT MISSING
            AND nuc_basecount > 486 AND marker_code IN ['COI-5P', 'matK', 'rbcL', 'rbcLa', 'trnH-psbA']
            AND kingdom = 'Plantae'
            AND species NOT LIKE '% % %'
            AND species NOT LIKE '% sp'
            AND species NOT LIKE '%.%'
            AND species NOT LIKE '%.%'
            AND NOT REGEXP_CONTAINS(species, '[0-9]')
            AND species NOT LIKE '%Janzen%'
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_plant_species_stat - UUID: {query_uuid} {' '.join(query.split())}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            metrics=True,
        ),
    )

    stat = 0
    for row in results.rows():
        stat = row["count"]

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_plant_species_stat - UUID: {query_uuid} {' '.join(query.split())} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return stat


def get_fungi_species_stat():
    query = f"""
        SELECT COUNT(DISTINCT species) AS count
        FROM `{NAME_MAP["primary_data"]["bucket"]}`.`_default`.`{NAME_MAP["primary_data"]["collection"]}`
        WHERE species IS NOT MISSING
            AND nuc_basecount > 486 AND marker_code IN ['COI-5P', 'ITS', 'ITS2']
            AND kingdom = 'Fungi'
            AND species NOT LIKE '% % %'
            AND species NOT LIKE '% sp'
            AND species NOT LIKE '%.%'
            AND species NOT LIKE '%.%'
            AND NOT REGEXP_CONTAINS(species, '[0-9]')
            AND species NOT LIKE '%Janzen%'
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_fungi_species_stat - UUID: {query_uuid} {' '.join(query.split())}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            metrics=True,
        ),
    )

    stat = 0
    for row in results.rows():
        stat = row["count"]

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_fungi_species_stat - UUID: {query_uuid} {' '.join(query.split())} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return stat


def get_other_species_stat():
    query = f"""
        SELECT COUNT(DISTINCT species) AS count
        FROM `{NAME_MAP["primary_data"]["bucket"]}`.`_default`.`{NAME_MAP["primary_data"]["collection"]}`
        WHERE species IS NOT MISSING
            AND nuc_basecount > 486 AND marker_code IN ['COI-5P']
            AND kingdom NOT IN ['Animalia', 'Plantae', 'Fungi']
            AND species NOT LIKE '% % %'
            AND species NOT LIKE '% sp'
            AND species NOT LIKE '%.%'
            AND species NOT LIKE '%.%'
            AND NOT REGEXP_CONTAINS(species, '[0-9]')
            AND species NOT LIKE '%Janzen%'
    """

    query_uuid = uuid.uuid4()
    query_logger.info(
        f"Start get_other_species_stat - UUID: {query_uuid} {' '.join(query.split())}"
    )

    start_time = time.perf_counter()

    results = _get_cb_cluster().query(
        query,
        QueryOptions(
            timeout=datetime.timedelta(seconds=_CB_TIMEOUT),
            metrics=True,
        ),
    )

    stat = 0
    for row in results.rows():
        stat = row["count"]

    end_time = time.perf_counter()

    query_logger.info(
        f"End get_other_species_stat - UUID: {query_uuid} {' '.join(query.split())} {results.metadata().metrics().execution_time().total_seconds()} {end_time - start_time}"
    )

    return stat
