from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from views import templates

route = APIRouter(tags=["views"])


@route.get("/primer", response_class=HTMLResponse)
async def show_primer_home(
    request: Request,
):
    return templates.TemplateResponse(
        "primer_home.jinja2",
        {
            "title": "Primer Home",
            "subtitle": "Primer records home page",
            "search_page": True,
            # "banner_bg_class": "fish",
            "wp_footer": True,
            "request": request,
        },
    )
