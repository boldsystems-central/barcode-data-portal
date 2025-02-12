from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from typing import Dict

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

route = APIRouter(tags=["stats"])


@route.get(
    "/stats", response_model=Dict[str, int], response_description="General Statistics"
)
async def retrieve_general_stats(stat: str = Query(title="Stat to retrieve")):
    """
    Return a general statistic about the overall database.

    - **stat**: Stat to return
    """
    general_stats = util.get_cache_from_meta_ids([util.STATS_META_ID])[0]
    if general_stats is None:
        general_stats = {
            "total seqs": dao.get_total_seqs_stat(),
            "total bins": dao.get_total_bins_stat(),
            "animal species": dao.get_animal_species_stat(),
            "plant species": dao.get_plant_species_stat(),
            "fungi species": dao.get_fungi_species_stat(),
            "other species": dao.get_other_species_stat(),
        }

        docs_to_cache = {util.STATS_META_ID: ujson.dumps(general_stats)}
        util.write_cache_with_meta_ids(docs_to_cache, None)
    else:
        general_stats = ujson.loads(general_stats)

    if stat not in general_stats:
        return JSONResponse(
            content={"detail": f"{stat} not found"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return {stat: general_stats[stat]}
