from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from views import templates

route = APIRouter(tags=["views"])


@route.get("/theme", response_class=HTMLResponse)
def show_sequence(request: Request):
    response_params = {
        "title": "Public Data Portal",
        "subtitle": "",
        "search_page": True,
        "wp_footer": True,
        "request": request,
    }
    return templates.TemplateResponse("theme.jinja2", response_params)
