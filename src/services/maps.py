from fastapi import APIRouter, Path, Query, HTTPException, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from ast import literal_eval as make_tuple

import base64
import httpx
import os
import pathlib
import subprocess
import sys
import tempfile

try:
    import util
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import util

route = APIRouter(tags=["maps"])

# TODO: Integrate util.py to fetch these values, functions
_MAP_TOOL = os.path.join(util.APP_ROOT, "tools", "generateMap.py")
_MAP_TEMPLATE = os.path.join(util.APP_ROOT, "tools", "worldmap_5000.png")
_MIN_HEIGHT = 40
_MIN_WIDTH = 40


@route.get(
    "/maps/{query_id}",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Map Image",
        },
    },
)
async def generate_map(
    query_id: str = Path(title="Documents query ID"),
    offset: int = Query(0, title="Count offset, for additional visual clarity)", ge=0),
    countryIso: str = Query(None, title="Country map to zoom into (by ISO code)"),
):
    """
    Generate a map of collection locations from an encoded query (query_id).

    - **query_id**: Encoded triplets query from `/api/query`
    - **offset**: Integer offset to emphasize markers
    - **countryIso**: ISO alpha2 country code to crop and zoom map into
    """
    triplets = util.get_triplets_from_query_id(query_id)

    triplets[-1] = "full"  # For consistency in cache access
    query_id = util.generate_query_id_from_triplets(triplets)

    if countryIso:
        map_meta_id = util.generate_map_meta_id(query_id, offset, countryIso)

        if map := util.get_cache_from_meta_ids([map_meta_id])[0]:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_map_file:
                tmp_map_file.write(base64.b64decode(map))
                tmp_map_file.seek(0)

                return FileResponse(
                    tmp_map_file.name,
                    media_type="image/png",
                    background=BackgroundTask(
                        lambda tmp: os.remove(tmp), tmp_map_file.name
                    ),
                )

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            params = {"query": ";".join(triplets[:-1]), "fields": "coord"}
            resp = await client.get(
                url=f"{util.get_app_url()}/api/summary", params=params
            )
            resp.raise_for_status()
            stats = resp.json()

            document = {}
            if countryIso:
                params = {
                    "collection": "countries",
                    "key": "iso_alpha_2",
                    "values": countryIso,
                }
                resp = await client.get(
                    url=f"{util.get_app_url()}/api/ancillary", params=params
                )
                resp.raise_for_status()
                datasets = resp.json()
                if datasets:
                    document = datasets[0]

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Map failed to generate, please try again",
        )

    coordinates = stats.get("coord", {})
    coordinates_input = "\n".join(
        [
            coordinate_str[1:-1]
            for coordinate_str, count in coordinates.items()
            for _ in range(count + offset)
        ]
    )

    # TODO: Create formula for calculating size factor as a gradient
    size_factor = 1
    if len(coordinates) > 1000:
        size_factor = 0.5

    crop = [-90, -180, 90, 180]
    crop_buffer = 0.05
    if document and document["boundingboxes"]:
        if countryIso == "FR":
            boundingbox_min = (-50.19693, -179)
            boundingbox_max = (51.26496, 174.4)
        else:
            boundingbox = document["boundingboxes"][0]
            delim_index = boundingbox.index("),(")

            boundingbox_min = make_tuple(boundingbox[delim_index + 2 :])
            boundingbox_max = make_tuple(boundingbox[: delim_index + 1])

        height_diff = 0
        width_diff = 0
        if height := boundingbox_max[0] - boundingbox_min[0] < _MIN_HEIGHT:
            height_diff = (_MIN_HEIGHT - height) / 2

        if width := boundingbox_max[1] - boundingbox_min[1] < _MIN_WIDTH:
            width_diff = (_MIN_WIDTH - width) / 2

        boundingbox_min = (
            boundingbox_min[0] - height_diff,
            boundingbox_min[1] - width_diff,
        )
        boundingbox_max = (
            boundingbox_max[0] + height_diff,
            boundingbox_max[1] + width_diff,
        )

        crop_buffer_x = (boundingbox_max[1] - boundingbox_min[1]) * crop_buffer / 2
        crop_buffer_y = (boundingbox_max[0] - boundingbox_min[0]) * crop_buffer / 2

        crop = [
            max(boundingbox_min[0] - crop_buffer_y, -90),
            max(boundingbox_min[1] - crop_buffer_x, -180),
            min(boundingbox_max[0] + crop_buffer_y, 90),
            min(boundingbox_max[1] + crop_buffer_x, 180),
        ]

    alpha = 180
    sort_order = "lh"

    with tempfile.NamedTemporaryFile(delete=False) as tmp_map_file:
        try:
            subprocess.run(
                [
                    sys.executable,
                    _MAP_TOOL,
                    _MAP_TEMPLATE,
                    tmp_map_file.name,
                    "--sizefactor",
                    str(size_factor),
                    "--crop",
                    str(crop),
                    "--alpha",
                    str(alpha),
                    "--sortorder",
                    sort_order,
                ],
                input=coordinates_input,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Map failed to generate, please try again",
            )

        if countryIso:
            map_meta_id = util.generate_map_meta_id(query_id, offset, countryIso)

            tmp_map_file.seek(0)
            map = base64.b64encode(tmp_map_file.read())

            docs_to_cache = {map_meta_id: map}
            util.write_cache_with_meta_ids(docs_to_cache, 86400)  # 1 day TTL

        tmp_map_file.seek(0)

        return FileResponse(
            tmp_map_file.name,
            media_type="image/png",
            background=BackgroundTask(lambda tmp: os.remove(tmp), tmp_map_file.name),
        )
