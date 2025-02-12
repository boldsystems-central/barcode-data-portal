from fastapi import APIRouter, Path
from fastapi.responses import HTMLResponse

route = APIRouter(tags=["views"])

@route.get("/lookup/{lookup_string}", response_class=HTMLResponse)
async def lookup(lookup_string: str = Path()):
    return lookup_string