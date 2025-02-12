from fastapi import HTTPException, status

import base64
import csv
import datetime
import logging
import pathlib
import redis
import ujson
import zlib

from settings import settings

sec_logger = logging.getLogger("sec_logger")

APP_ROOT = settings.app_root
DATA_MODEL_PATH = (
    pathlib.Path(settings.module_root, "barcode-core-data-model").resolve().as_posix()
)
STATS_META_ID = "stats"

# Redis cache
_REDIS_POOL = redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    encoding="utf-8",
    decode_responses=True,
)
_REDIS_TTL = 604800  # 7 days

# Triplets configuration
_SCOPE_MAP = {
    "tax": [
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
        "subfamily",
        "tribe",
        "genus",
        "species",
        "subspecies",
    ],
    "geo": ["country/ocean", "province/state", "region"],
    "inst": ["name", "seqsite"],
    "ids": ["processid", "sampleid", "insdcasc"],
    "bin": ["uri"],
    "recordsetcode": ["code"],
}

###
# Utilities
###


def get_app_url():
    return (
        settings.app_url
        if settings.app_url
        else f"http://{settings.app_host}:{settings.app_port}"
    )


def get_caos_url():
    return settings.caos_url


###
# Triplets and Cache/Data
###


def generate_partial_triplet(term):
    return f"na:na:{term}"


def generate_triplet_from_token(token):
    parts = token.split(":", 2)

    while len(parts) < 3:
        parts.insert(len(parts) - 1, "na")

    for i in range(len(parts) - 1):
        if not parts[i].strip():
            parts[i] = "na"

    return ":".join(parts)


def expand_non_term_triplets(triplet):
    # TODO: Support filling in only 'na' values?
    expanded_triplets = []
    _, _, value = triplet.split(":", 2)

    # TODO: Validate implementation
    # TODO: Integrate more branches for other scopes/scope combinations?
    if value.startswith("BOLD:"):
        possible_scopes = ["bin"]
    elif value.startswith("DS-") or value.startswith("DATASET-"):
        possible_scopes = ["recordsetcode"]
    else:
        possible_scopes = ["ids"]  # TODO: Integrate bin scope, but as an id?

    for scope in possible_scopes:
        for subscope in _SCOPE_MAP.get(scope, []):
            expanded_triplets.append(f"{scope}:{subscope}:{value}")

    return expanded_triplets


def match_triplet_to_resolved_triplet(triplet, resolved_triplet):
    scope, subscope, value = triplet.split(":", 2)
    resolved_scope, resolved_subscope, resolved_value = resolved_triplet.split(":", 2)

    return (
        (scope == "na" or scope == resolved_scope)
        and (subscope == "na" or subscope == resolved_subscope)
        and (value == resolved_value)
    )


def sanitize_triplet(triplet):
    scope, subscope, value = triplet.split(":", 2)
    return f"{scope.lower()}:{subscope.lower()}:{value}"


def sanitize_triplets_from_query(query, extent="limited"):
    triplets = [triplet.strip() for triplet in query.split(";")]

    sanitized_triplets = []
    for triplet in triplets:
        sanitized_triplets.append(sanitize_triplet(triplet))

    sanitized_triplets.sort()
    sanitized_triplets.append(extent)
    return sanitized_triplets


def sanitize_term(term):
    # TODO:
    return term


def generate_query_id_from_triplets(triplets):
    # TODO: If query_id too long, truncate/modify and store triplet in file system
    return base64.b64encode(
        zlib.compress(";".join(triplets).encode(), 1), altchars=b"-_"
    ).decode()


def get_triplets_from_query_id(query_id):
    # TODO: If query_id prefixed with mem:, look into file system for triplets
    return (
        zlib.decompress(base64.b64decode(query_id.encode(), altchars=b"-_"))
        .decode()
        .split(";")
    )


def get_cache_from_query_id(query_id):
    cache_file = pathlib.Path(settings.cache_path, f"{query_id}.txt")
    try:
        with open(cache_file) as fp:
            return fp.read().splitlines()
    except:
        return []


def write_cache_with_query_id(query_id, data):
    cache_file = pathlib.Path(settings.cache_path, f"{query_id}.txt")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as fp:
        fp.write("\n".join(data))

    cache_metadata_file = pathlib.Path(settings.cache_path, f"{query_id}.metadata.json")
    metadata = {"created": str(datetime.datetime.now())}
    with open(cache_metadata_file, "w") as fp:
        ujson.dump(metadata, fp)


def get_cache_from_meta_ids(meta_ids):
    try:
        with redis.StrictRedis(connection_pool=_REDIS_POOL) as redis_conn:
            return redis_conn.mget(meta_ids)
    except redis.exceptions.ConnectionError:
        return [None] * len(meta_ids)


def write_cache_with_meta_ids(meta_ids_and_data, ttl=_REDIS_TTL):
    try:
        with redis.StrictRedis(connection_pool=_REDIS_POOL) as redis_conn:
            pipeline = redis_conn.pipeline(transaction=False)
            for meta_id, data in meta_ids_and_data.items():
                pipeline.set(meta_id, data, ex=ttl)
            return pipeline.execute()
    except redis.exceptions.ConnectionError:
        return [False] * len(meta_ids_and_data)


def get_default_data_model_object():
    data_model = {}

    with open(f"{DATA_MODEL_PATH}/field_definitions.tsv") as fp:
        tsv_file = csv.reader(fp, delimiter="\t")

        # Skip header
        _ = next(tsv_file)

        for line in tsv_file:
            data_model[line[0]] = None

    return data_model


def get_summary_cache_from_query_id(query_id):
    cache_file = pathlib.Path(settings.cache_path, f"{query_id}.summary.txt")
    try:
        with open(cache_file) as fp:
            return fp.read().splitlines()
    except:
        return []


def write_summary_cache_with_query_id(query_id, data):
    cache_file = pathlib.Path(settings.cache_path, f"{query_id}.summary.txt")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as fp:
        fp.write("\n".join(data))

    cache_metadata_file = pathlib.Path(
        settings.cache_path, f"{query_id}.summary.metadata.json"
    )
    metadata = {"created": str(datetime.datetime.now())}
    with open(cache_metadata_file, "w") as fp:
        ujson.dump(metadata, fp)


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


def generate_ancillary_set_meta_id(
    ancillary_collection,
    derived_collection,
    ancillary_join_key,
    derived_join_key,
    join_type,
):
    return f"ancillary-set:{ancillary_collection},{derived_collection},{ancillary_join_key},{derived_join_key},{join_type}"


def generate_map_meta_id(query_id, offset, countryIso):
    return f"map:{query_id},{offset},{countryIso}"


def generate_tax_map_meta_id(query_id, node_threshold):
    return f"tax-map:{query_id},{node_threshold}"


###
# Security
###


def raise_security_warning(request):
    # TODO: Implement security checks on API endpoints
    sec_logger.warn(
        f'{request.client.host}:{request.client.port} - "{request.method} {request.url.path} {request["type"].upper()}/{request["http_version"]}"'
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Failed security check"
    )


###
# Offline
###


def get_offline_switch() -> str:
    try:
        with open(pathlib.Path(settings.offline_path, "offline.txt")) as fp:
            offline_msg = fp.read()
            return offline_msg.strip() if offline_msg.strip() else None
    except:
        return None


def get_notice_switch() -> str:
    try:
        with open(pathlib.Path(settings.offline_path, "notice.txt")) as fp:
            notice_msg = fp.read()
            return notice_msg.strip() if notice_msg.strip() else None
    except:
        return None
