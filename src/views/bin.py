from fastapi import APIRouter, Request, Path, Query, HTTPException, status
from fastapi.responses import HTMLResponse

from views import templates

import httpx
from collections import defaultdict
from util import get_app_url

route = APIRouter(tags=["views"])


@route.get("/bin", response_class=HTMLResponse)
async def show_bin_home(
    request: Request,
):
    return templates.TemplateResponse(
        "bin_home.jinja2",
        {
            "title": "BIN Home",
            "subtitle": "Barcode Index Numbers Home Page",
            "search_page": True,
            # "banner_bg_class": "fish",
            "wp_footer": True,
            "request": request,
        },
    )


@route.get("/bin/{bin_uri}", response_class=HTMLResponse)
async def show_bin(
    request: Request,
    bin_uri: str = Path(title="BIN URI"),
    extent: str = Query("large", title="Document extent"),
):
    urls = [request.url]
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            query = f"bin:uri:{bin_uri}"

            params = {
                "query": query,
                "fields": ",".join(
                    [
                        "specimens",
                        "marker_code",
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
            summary.update(resp.json())
            count = summary["counts"]["specimens"]

            if count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"BIN {bin_uri} not found",
                )

            stats = {
                "specimens": summary["counts"]["specimens"],
                "sequences": sum(summary["marker_code"].values()),
                "records_w_species": sum(summary["species"].values()),
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
        "bin.jinja2",
        {
            "request": request,
            "bin_uri": bin_uri,
            "query_id": query_id,
            "extent_limit": extent_limit,
            "image_count": image_count,
            "stats": stats,
            "countries": summary["country/ocean"],
            "inst": summary["inst"],
            "sequence_run_site": summary["sequence_run_site"],
            "identified_by": summary["identified_by"],
            "title": bin_uri,
            "subtitle": f"Summary and records of {bin_uri}",
            "banner_bg_class": "coralspiral",
            "urls": urls,
        },
    )
