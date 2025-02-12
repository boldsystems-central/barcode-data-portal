from fastapi import APIRouter, Request, Path, Query, HTTPException, status
from fastapi.responses import HTMLResponse

from views import templates

import httpx
from collections import defaultdict
from util import get_app_url

route = APIRouter(tags=["views"])


@route.get("/record/{processid}", response_class=HTMLResponse)
async def show_record(
    request: Request,
    processid: str = Path(title="Record processid"),
    extent: str = Query("limited", title="Document extent"),
):
    urls = [request.url]
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            query = f"ids:processid:{processid}"

            params = {
                "query": query,
                "fields": ",".join(["marker_code"]),
            }
            resp = await client.get(url=f"{get_app_url()}/api/summary", params=params)
            resp.raise_for_status()
            urls.append(resp.url)
            summary = defaultdict(lambda: defaultdict(lambda: 0))
            summary.update(resp.json())
            count = sum(summary["marker_code"].values())

            if count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Record {processid} not found",
                )

            params = {"query": query, "extent": extent}
            resp = await client.get(url=f"{get_app_url()}/api/query", params=params)
            resp.raise_for_status()
            urls.append(resp.url)
            query_resp = resp.json()
            query_id = query_resp["query_id"]

            resp = await client.get(
                url=f"{get_app_url()}/api/documents/{query_id}",
                params={"length": count},
            )
            resp.raise_for_status()
            results = resp.json()
            urls.append(resp.url)
            records = results["data"]

            resp = await client.get(
                url=f"{get_app_url()}/api/images/{query_id}",
            )
            resp.raise_for_status()
            image_data = resp.json()

            dataset_data = {}
            if recordset_codes := records[0].get("bold_recordset_code_arr", []):
                params = {
                    "collection": "datasets",
                    "key": "dataset.code",
                    "values": ";".join(recordset_codes),
                }
                resp = await client.get(
                    url=f"{get_app_url()}/api/ancillary", params=params
                )
                resp.raise_for_status()
                datasets = resp.json()
                for document in datasets:
                    dataset_data[document["dataset.code"]] = document

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Page failed to load, please try again",
        )

    return templates.TemplateResponse(
        "record.jinja2",
        {
            "request": request,
            "processid": processid,
            "query_id": query_id,
            "records": records,
            "image_data": image_data,
            "dataset_data": dataset_data,
            "title": processid,
            "subtitle": f"Details of {processid}",
            "banner_bg_class": "mantis",
            "urls": urls,
        },
    )
