from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse
import ujson as json

from views import templates

import httpx
from collections import defaultdict
from util import get_app_url, get_triplets_from_query_id

route = APIRouter(tags=["views"])


@route.get("/result", response_class=HTMLResponse)
async def show_search_result(request: Request, query: str):
    urls = [request.url]
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.get(
                url=f"{get_app_url()}/api/query/parse", params={"query": query}
            )
            resp.raise_for_status()
            urls.append(resp.url)
            terms = resp.json()["terms"]

            # TODO: What to do if preprocessor does not come up with valid triplets?
            resp = await client.get(
                url=f"{get_app_url()}/api/query/preprocessor", params={"query": terms}
            )
            resp.raise_for_status()
            urls.append(resp.url)
            processed_query = resp.json()

            resolved_query = ";".join(
                term["matched"] for term in processed_query["successful_terms"]
            )

            params = {
                "query": resolved_query,
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
                    ]
                ),
            }
            resp = await client.get(url=f"{get_app_url()}/api/summary", params=params)
            resp.raise_for_status()
            urls.append(resp.url)
            summary = defaultdict(lambda: defaultdict(lambda: 0))
            summary.update(resp.json())  # TODO: If nothing, return error?

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

            params = {"query": resolved_query}
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

    response_params = {
        "request": request,
        "query_id": query_id,
        "triplets": json.dumps(triplets),
        "extent_limit": extent_limit,
        "image_count": image_count,
        "stats": stats,
        "inst": summary["inst"],
        "sequence_run_site": summary["sequence_run_site"],
        "identified_by": summary["identified_by"],
        "title": "Search Results",
        "subtitle": query,
        "banner_bg_class": "beetle",
        "urls": urls,
    }
    return templates.TemplateResponse("result.jinja2", response_params)
