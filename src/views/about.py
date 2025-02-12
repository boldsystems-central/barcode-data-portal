from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from views import templates

route = APIRouter(tags=["views"])


@route.get("/about", response_class=HTMLResponse)
def show_about(request: Request):
    response_params = {
        "title": "About",
        "subtitle": "",
        "search_page": True,
        "wp_footer": True,
        "request": request,
    }
    return templates.TemplateResponse("about.jinja2", response_params)
