from fastapi import APIRouter, Request, Path, Query, HTTPException, status
from fastapi.responses import HTMLResponse
import ujson as json

from views import templates, generate_cumulative_date_histogram

import httpx
from collections import defaultdict
from util import get_app_url, get_triplets_from_query_id

route = APIRouter(tags=["views"])


@route.get("/recordset", response_class=HTMLResponse)
async def show_recordset_home(
    request: Request,
):
    return templates.TemplateResponse(
        "recordset_home.jinja2",
        {
            "title": "Dataset Home",
            "subtitle": "Dataset records home page",
            "search_page": True,
            # "banner_bg_class": "fish",
            "wp_footer": True,
            "request": request,
        },
    )


@route.get("/recordset/{recordsetcode}", response_class=HTMLResponse)
async def show_recordset(
    request: Request,
    recordsetcode: str = Path(title="Recordset code"),
    extent: str = Query("large", title="Document extent"),
):
    urls = [request.url]
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            query = f"recordsetcode:code:{recordsetcode}"

            params = {
                "query": query,
                "fields": ",".join(
                    [
                        "specimens",
                        "marker_code",
                        "bin_uri",
                        "species",
                        "country/ocean",
                        "inst",
                        "sequence_run_site",
                        "identified_by",
                        "collection_date_start",
                    ]
                ),
            }
            resp = await client.get(url=f"{get_app_url()}/api/summary", params=params)
            resp.raise_for_status()
            urls.append(resp.url)
            summary = defaultdict(lambda: defaultdict(lambda: 0))
            summary.update(resp.json())
            count = summary["counts"]["specimens"]

            if count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Recordset {recordsetcode} not found",
                )

            stats = {
                "specimens": summary["counts"]["specimens"],
                "sequences": sum(summary["marker_code"].values()),
                "records_w_bins": sum(summary["bin_uri"].values()),
                "records_w_species": sum(summary["species"].values()),
                "bins": len(summary["bin_uri"]),
                "species": len(summary["species"]),
                "countries/oceans": len(summary["country/ocean"]),
                "institutions": len(summary["inst"]),
            }

            params = {"query": query, "extent": extent}
            resp = await client.get(url=f"{get_app_url()}/api/query", params=params)
            resp.raise_for_status()
            urls.append(resp.url)
            query_resp = resp.json()
            query_id = query_resp["query_id"]
            extent_limit = query_resp["extent_limit"]
            triplets = get_triplets_from_query_id(query_id)

            resp = await client.get(
                url=f"{get_app_url()}/api/images/{query_id}",
            )
            resp.raise_for_status()
            urls.append(resp.url)
            image_response = resp.json()

            image_count = 0
            for images in image_response["images"].values():
                image_count += len(images)

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Page failed to load, please try again",
        )

    return templates.TemplateResponse(
        "recordset.jinja2",
        {
            "request": request,
            "recordsetcode": recordsetcode,
            "query_id": query_id,
            "triplets": json.dumps(triplets),
            "extent_limit": extent_limit,
            "image_count": image_count,
            "stats": stats,
            "inst": summary["inst"],
            "sequence_run_site": summary["sequence_run_site"],
            "identified_by": summary["identified_by"],
            "collection_date_start": generate_cumulative_date_histogram(
                summary["collection_date_start"]
            ),
            "title": f"Dataset: {recordsetcode}",
            "subtitle": f"Summary and records of {recordsetcode}",
            "urls": urls,
        },
    )
