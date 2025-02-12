from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from views import templates

route = APIRouter(tags=["views"])


@route.get("/api", response_class=HTMLResponse)
def show_api(request: Request):
    response_params = {
        "title": "API",
        "subtitle": "",
        "search_page": True,
        "wp_footer": True,
        "request": request,
    }
    return templates.TemplateResponse("api.jinja2", response_params)
