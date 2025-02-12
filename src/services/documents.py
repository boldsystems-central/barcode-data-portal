from fastapi import APIRouter, Path, Query, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel
from typing import List, Dict

import pandas as pd
import pathlib
import os
import subprocess
import sys
import tempfile
import ujson

try:
    import dao
    import util
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import dao
    import util

route = APIRouter(tags=["documents"])


class Documents(BaseModel):
    data: List[Dict]
    recordsTotal: int
    recordsFiltered: int


# TODO: Integrate util.py to fetch these values, functions
_DL_BATCH_SIZE = 10000
_DL_MAX_SIZE = 1000000
_DWC_TOOL = os.path.join(util.APP_ROOT, "tools", "dataMapConverter.py")
_DWC_MAP = os.path.join(util.DATA_MODEL_PATH, "mapping_BCDM_to_DWC.tsv")


def _delete_tmp_files(tmp_files):
    """
    Delete temporary files in module using os.remove

    - **tmp_files**: List of files to delete
    """
    for tmp_file in tmp_files:
        os.remove(tmp_file)


@route.get(
    "/documents/{query_id}",
    response_model=Documents,
    response_description="Document Set, Tailored For DataTables",
)
def retrieve_documents(
    query_id: str = Path(title="Documents query ID"),
    length: int = Query(default=1, title="Documents limit", ge=0),
    start: int = Query(default=0, title="Documents offset", ge=0),
):
    """
    Retrieve a set of documents IDs from an encoded query (query_id) and fetch a set
    of documents of `length` size after `start` offset. If request size exceeds number of
    documents available after offset, will return documents with size less than requested.

    - **query_id**: Encoded triplets query from `/api/query`
    - **length**: Number of documents to retrieve (minimum 0)
    - **start**: Offset of documents from beginning of documents in query (minimum 0)
    """
    triplets = util.get_triplets_from_query_id(query_id)

    cb_data = "primary_data"
    bucket = dao.NAME_MAP[cb_data]["bucket"]
    collection = dao.NAME_MAP[cb_data]["collection"]

    if not (meta_ids := util.get_cache_from_query_id(query_id)):
        meta_ids = dao.get_cb_meta_ids(triplets, bucket, collection)
        util.write_cache_with_query_id(query_id, meta_ids)

    total_count = len(meta_ids)
    default_object = util.get_default_data_model_object()

    rows = []
    meta_ids.sort()
    meta_ids = meta_ids[start : start + length]
    results = util.get_cache_from_meta_ids(meta_ids)

    missing_results = {}
    for idx, (meta_id, result) in enumerate(zip(meta_ids, results)):
        if result is None:
            rows.append(result)
            missing_results[meta_id] = idx
        else:
            data = default_object.copy()
            data.update(ujson.loads(result))
            data["count"] = total_count
            rows.append(data)

    if missing_results:
        docs_to_cache = {}
        missing_meta_ids = list(missing_results.keys())
        missing_docs = dao.get_cb_documents(missing_meta_ids, bucket, collection)
        for meta_id, missing_doc in zip(missing_meta_ids, missing_docs):
            docs_to_cache[meta_id] = ujson.dumps(missing_doc, default=str)

            data = default_object.copy()
            data.update(missing_doc)
            data["count"] = total_count
            rows[missing_results[meta_id]] = data

        util.write_cache_with_meta_ids(docs_to_cache)

    return {"data": rows, "recordsTotal": total_count, "recordsFiltered": total_count}


@route.get(
    "/documents/{query_id}/query",
    response_model=List,
    response_description="Original Query Tokens",
)
async def retrieve_documents_query(
    query_id: str = Path(title="Documents query ID"),
):
    """
    Retrieve the original query from an encoded query (query_id)

    - **query_id**: Encoded triplets query from `/api/query`
    """
    triplets = util.get_triplets_from_query_id(query_id)
    return triplets


@route.get(
    "/documents/{query_id}/download",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"text/plain": {}, "text/tab-separated-values": {}},
            "description": "Document Export",
        },
    },
)
def retrieve_documents_download(
    query_id: str = Path(title="Documents query ID"),
    format: str = Query(
        default="json", title="Download format", regex="(dwc|tsv|json)"
    ),
):
    """
    Generate a download file with documents from an encoded query (query_id). Will download up to a
    maximum of `DL_MAX_SIZE` documents for a given query and will ignore the query extent to always
    download the full extent.

    - **query_id**: Encoded triplets query from `/api/query`
    - **format**: Export format, available options are `dwc` (Darwin Core Model), `tsv` and `json`
    """
    triplets = util.get_triplets_from_query_id(query_id)
    triplets[-1] = "full"  # Always consider the full set of downloads

    cb_data = "primary_data"
    bucket = dao.NAME_MAP[cb_data]["bucket"]
    collection = dao.NAME_MAP[cb_data]["collection"]

    meta_ids = dao.get_cb_meta_ids(triplets, bucket, collection)[:_DL_MAX_SIZE]
    default_object = util.get_default_data_model_object()

    if format == "dwc":
        media_type = "text/plain"
    elif format == "tsv":
        media_type = "text/tab-separated-values"
    else:
        media_type = "text/plain"

    tmp_to_delete = []

    def iter_file():
        batch_counter = 0
        batch = meta_ids[
            _DL_BATCH_SIZE * batch_counter : _DL_BATCH_SIZE * (batch_counter + 1)
        ]

        while batch:
            rows = []
            results = util.get_cache_from_meta_ids(batch)

            # TODO: If general exception occurs, how will this file be cleaned up?
            tmp_cache_file = tempfile.NamedTemporaryFile(mode="r+", delete=False)
            tmp_to_delete.append(tmp_cache_file.name)

            missing_results = {}
            for idx, (meta_id, result) in enumerate(zip(batch, results)):
                if result is None:
                    rows.append(result)
                    missing_results[meta_id] = idx
                else:
                    data = default_object.copy()
                    data.update(ujson.loads(result))
                    rows.append(data)

            if missing_results:
                docs_to_cache = {}
                missing_meta_ids = list(missing_results.keys())
                missing_docs = dao.get_cb_documents(
                    missing_meta_ids, bucket, collection
                )
                for meta_id, missing_doc in zip(missing_meta_ids, missing_docs):
                    docs_to_cache[meta_id] = ujson.dumps(missing_doc, default=str)

                    data = default_object.copy()
                    data.update(missing_doc)
                    rows[missing_results[meta_id]] = data

                util.write_cache_with_meta_ids(docs_to_cache)

            for data in rows:
                tmp_cache_file.write(ujson.dumps(data, default=str) + "\n")

            if format == "dwc":
                tmp_cache_file.close()

                tmp_dwc_file = tempfile.NamedTemporaryFile(delete=False)
                tmp_dwc_file.close()
                tmp_to_delete.append(tmp_dwc_file.name)

                try:
                    subprocess.run(
                        [
                            sys.executable,
                            _DWC_TOOL,
                            "-i",
                            tmp_cache_file.name,
                            "-o",
                            tmp_dwc_file.name,
                            "-m",
                            _DWC_MAP,
                        ],
                        check=True,
                    )
                except subprocess.CalledProcessError:
                    _delete_tmp_files(tmp_to_delete)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="DWC file failed to generate, please try again",
                    )

                yield pd.read_json(tmp_dwc_file.name, lines=True).to_csv(
                    header=(batch_counter == 0), index=False, sep="\t"
                )

            elif format == "tsv":
                tmp_cache_file.close()
                yield pd.read_json(tmp_cache_file.name, lines=True).to_csv(
                    header=(batch_counter == 0), index=False, sep="\t"
                )

            else:
                tmp_cache_file.seek(0)
                yield from tmp_cache_file
                tmp_cache_file.close()

            batch_counter += 1
            batch = meta_ids[
                _DL_BATCH_SIZE * batch_counter : _DL_BATCH_SIZE * (batch_counter + 1)
            ]

    return StreamingResponse(
        iter_file(),
        media_type=media_type,
        background=BackgroundTask(_delete_tmp_files, tmp_to_delete),
    )
