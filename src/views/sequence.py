from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from views import templates

route = APIRouter(tags=["views"])


@route.get("/sequence/{sequence}", response_class=HTMLResponse)
def show_sequence(request: Request, sequence):
    response_params = {
        "title": "Public Data Portal",
        "subtitle": "",
        "search_page": True,
        "wp_footer": True,
        "request": request,
        "sequence": sequence,
    }
    return templates.TemplateResponse("sequence.jinja2", response_params)
