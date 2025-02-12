from fastapi import APIRouter, Request, Path, Query, HTTPException, status
from fastapi.responses import HTMLResponse
import ujson as json

from views import templates, generate_cumulative_date_histogram

import httpx
from collections import defaultdict
from util import get_app_url, get_triplets_from_query_id

route = APIRouter(tags=["views"])


@route.get("/country-ocean", response_class=HTMLResponse)
@route.get("/geo", response_class=HTMLResponse)
async def show_country_ocean_home(
    request: Request,
):
    return templates.TemplateResponse(
        "country_home.jinja2",
        {
            "title": "Country/Ocean Home",
            "subtitle": "Country records home page",
            "search_page": True,
            # "banner_bg_class": "fish",
            "wp_footer": True,
            "request": request,
        },
    )


@route.get("/country-ocean/{id}", response_class=HTMLResponse)
@route.get("/geo/{id}", response_class=HTMLResponse)
async def show_country_ocean(
    request: Request,
    id: str = Path(title="Country/ocean ID (name or geo ID)"),
    extent: str = Query("limited", title="Document extent"),
):
    urls = [request.url]
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            # Determine if ID given is name or geo ID
            # and grab the other ID from ancillary
            try:
                params = {
                    "collection": "countries",
                    "key": "id",
                    "values": id,
                    "fields": "name",
                }
                resp = await client.get(
                    url=f"{get_app_url()}/api/ancillary", params=params
                )
                resp.raise_for_status()
                urls.append(resp.url)
                name = resp.json()[0]["name"]
            except IndexError:
                name = id

                try:
                    params = {
                        "collection": "countries",
                        "key": "name",
                        "values": name,
                        "fields": "id",
                    }
                    resp = await client.get(
                        url=f"{get_app_url()}/api/ancillary", params=params
                    )
                    resp.raise_for_status()
                    urls.append(resp.url)
                    id = resp.json()[0]["id"]
                except IndexError:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Country/ocean {name} not found",
                    )

            query = f"geo:country/ocean:{name}"

            params = {
                "query": query,
                "fields": ",".join(
                    [
                        "specimens",
                        "marker_code",
                        "bin_uri",
                        "species",
                        "inst",
                        "sequence_run_site",
                        "identified_by",
                        "sequence_upload_date",
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
                    detail=f"Country/ocean {name} not found",
                )

            stats = {
                "specimens": summary["counts"]["specimens"],
                "sequences": sum(summary["marker_code"].values()),
                "records_w_bins": sum(summary["bin_uri"].values()),
                "records_w_species": sum(summary["species"].values()),
                "bins": len(summary["bin_uri"]),
                "species": len(summary["species"]),
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
        "country.jinja2",
        {
            "request": request,
            "name": name,
            "permalink": f"https://doi.org/10.5883/GEO-{id}",
            "query_id": query_id,
            "triplets": json.dumps(triplets),
            "extent_limit": extent_limit,
            "image_count": image_count,
            "stats": stats,
            "inst": summary["inst"],
            "sequence_run_site": summary["sequence_run_site"],
            "identified_by": summary["identified_by"],
            "sequence_upload_date": generate_cumulative_date_histogram(
                summary["sequence_upload_date"]
            ),
            "collection_date_start": generate_cumulative_date_histogram(
                summary["collection_date_start"]
            ),
            "title": name,
            "subtitle": f"Summary and records in {name}",
            "banner_bg_class": "fish",
            "urls": urls,
        },
    )
