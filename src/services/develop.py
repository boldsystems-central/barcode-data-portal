from typing import Any, Dict

from fastapi import APIRouter, Query
from pydantic import BaseModel

from dao import _get_cb_cluster

route = APIRouter(tags=["upsert"])


class InputData(BaseModel):
    bucket: str
    collection: str
    id_doc_dict: Dict[str, Any]
    scope: str = "_default"


@route.post("/develop/upsert/batch", include_in_schema=False)
async def upsert(input: InputData):
    bucket = _get_cb_cluster().bucket(input.bucket)
    collection = bucket.scope(input.scope).collection(input.collection)

    upsert_results = collection.upsert_multi(input.id_doc_dict)

    responses = []
    for k, v in upsert_results.results.items():
        responses.append(f"Doc upserted: key={k}, cas={v.cas}")

    return {"responses": responses}


@route.get("/develop/retrieve_data_by_value", include_in_schema=False)
async def retrieve_data_by_value(bucket: str, collection: str, field: str, value: str):
    query = f"""
            SELECT * FROM `{bucket}`.`_default`.`{collection}` where `{field}`='{value}';
        """
    results = _get_cb_cluster().query(query)
    documents = []
    for row in results.rows():
        documents.append(row)

    return documents
