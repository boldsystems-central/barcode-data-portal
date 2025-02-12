from fastapi import APIRouter, Query
from typing import List, Dict

import pathlib
import sys
import ujson

try:
    import dao
    import util
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import dao
    import util


route = APIRouter(tags=["ancillary"])


join_map = {
    "barcodeclusters": {
        "derived_collection": "bin_summaries",
        "join_key": "barcodecluster.uri",
        "derived_join_key": "bin_uri",
    },
    "countries": {
        "derived_collection": "country_summaries",
        "join_key": "name",
        "derived_join_key": "country/ocean",
    },
    "datasets": {
        "derived_collection": "dataset_summaries",
        "join_key": "dataset.code",
        "derived_join_key": "dataset.code",
    },
    "institutions": {
        "derived_collection": "institution_summaries",
        "join_key": "name",
        "derived_join_key": "inst",
    },
    "primers": {
        "derived_collection": "primer_summaries",
        "join_key": "name",
        "derived_join_key": "name",
    },
    "taxonomies": {
        "derived_collection": "taxonomy_summaries",
        "join_key": "taxid",
        "derived_join_key": "taxid",
    },
}


@route.get(
    "/ancillary",
    response_model=List[Dict],
    response_description="Document List",
)
async def retrieve_ancillary_documents(
    collection: str = Query(title="Collection name to retrieve from"),
    key: str = Query(title="Field to query"),
    values: str = Query(title="Values to match, as semicolon delimited values"),
    fields: str = Query(
        default=None, title="Fields to select, as semicolon delimited values"
    ),
):
    """
    Retrieve ancillary documents from a collection. Designate a key field to match value(s) against
    to select a set of documents from the specified collection. If a collection that does not exist
    is specified or no documents with the selected key matches the value(s) no documents are returned.

    - **collection**: Collection name to retrieve from
    - **key**: Field to query within documents of collection
    - **values**: Values to match to key within document, as semicolon delimited values
    - **fields**: Fields to select, as semicolon delimited values
    """
    values = [value.strip() for value in values.split(";") if value.strip()]
    for value in set(values):
        try:
            values.append(float(value))  # Type-less matching (string <> int/float)
        except ValueError:
            pass

    if fields:
        fields = [field.strip() for field in fields.split(";") if field.strip()]

    ancillary_collection = collection
    derived_collection = join_map[collection]["derived_collection"]
    ancillary_join_key = join_map[collection]["join_key"]
    derived_join_key = join_map[collection]["derived_join_key"]

    documents = dao.get_cb_ancillary_documents(
        ancillary_collection,
        derived_collection,
        ancillary_join_key,
        derived_join_key,
        "LEFT JOIN",
        key,
        values,
    )

    if fields:
        for i, doc in enumerate(documents):
            documents[i] = {key: doc[key] for key in fields if key in doc}

    return documents


@route.get(
    "/ancillary-set",
    response_model=List[Dict],
    response_description="Document List for DataTables",
)
async def retrieve_ancillary_documents(
    collection: str = Query(title="Collection name to retrieve from"),
    fields: str = Query(
        default=None, title="Fields to select, as semicolon delimited values"
    ),
    min_records: int = Query(
        default=0,
        ge=0,
        title="Minimum # of records associated with registry entry",
    ),
):
    """
    Retrieve the entire set of ancillary documents from a collection.

    - **collection**: Collection name to retrieve from
    - **fields**: Fields to select, as semicolon delimited values
    - **min_records**: Minimum # of records associated with registry entry
    """
    if fields:
        fields = [field.strip() for field in fields.split(";") if field.strip()]

    # TEMP: To display 100 random taxonomies for landing page table
    # TODO: Refine query for production use
    if collection == "taxonomies":
        documents = dao.get_cb_ancillary_taxonomy_documents(100)
    else:
        ancillary_collection = collection
        derived_collection = join_map[collection]["derived_collection"]
        ancillary_join_key = join_map[collection]["join_key"]
        derived_join_key = join_map[collection]["derived_join_key"]
        if min_records > 0:
            join_type = "INNER JOIN"
        else:
            join_type = "LEFT JOIN"

        ancillary_id = util.generate_ancillary_set_meta_id(
            ancillary_collection,
            derived_collection,
            ancillary_join_key,
            derived_join_key,
            join_type,
        )

        if ancillary_doc := util.get_cache_from_meta_ids([ancillary_id])[0]:
            documents = ujson.loads(ancillary_doc)
        else:
            documents = dao.get_cb_ancillary_documents(
                ancillary_collection,
                derived_collection,
                ancillary_join_key,
                derived_join_key,
                join_type,
            )
            docs_to_cache = {ancillary_id: ujson.dumps(documents)}
            util.write_cache_with_meta_ids(docs_to_cache, 86400)  # 1 day TTL

    if min_records > 1:
        kept_documents = []
        for doc in documents:
            if doc["specimens"] >= min_records:
                kept_documents.append(doc)

        documents = kept_documents

    if fields:
        for i, doc in enumerate(documents):
            documents[i] = {key: doc[key] for key in fields if key in doc}

    return documents
