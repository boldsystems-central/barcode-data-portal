from fastapi import FastAPI, APIRouter, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from settings import settings
from util import get_offline_switch

import logging.config
import time
import traceback

logging.config.fileConfig(settings.log_config_path, disable_existing_loggers=False)
exc_logger = logging.getLogger("exc_logger")

from services import (
    test,
    query,
    query_parse,
    query_preprocessor,
    summary,
    documents,
    ancillary,
    maps,
    counts,
    stats,
    images,
    taxonomy,
    qr,
    terms,
    develop,
)
from views import (
    index,
    record,
    recordset,
    country,
    inst,
    bin,
    primer,
    result,
    lookup,
    api,
    about,
    sequence,
    templates,
    theme,
)

app = FastAPI(docs_url="/api/docs", redoc_url="/api/redoc", title="BOLD Portal")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/wp-content", StaticFiles(directory="static/wp-content"), name="wp-content")
app.mount(
    "/wp-includes", StaticFiles(directory="static/wp-includes"), name="wp-includes"
)
app.mount("/wp-json", StaticFiles(directory="static/wp-json"), name="wp-json")

# API (Services) Routes #

api_router = APIRouter(prefix="/api")
api_router.include_router(query.route)
api_router.include_router(query_parse.route)
api_router.include_router(query_preprocessor.route)
api_router.include_router(terms.route)
api_router.include_router(summary.route)
api_router.include_router(documents.route)
api_router.include_router(ancillary.route)
api_router.include_router(maps.route)
api_router.include_router(counts.route)
api_router.include_router(stats.route)
api_router.include_router(images.route)
api_router.include_router(taxonomy.route)
api_router.include_router(qr.route)
api_router.include_router(test.route)
api_router.include_router(develop.route)

app.include_router(api_router)

# View Routes #

app.include_router(index.route)
app.include_router(record.route)
app.include_router(recordset.route)
app.include_router(country.route)
app.include_router(inst.route)
app.include_router(bin.route)
app.include_router(primer.route)
app.include_router(result.route)
app.include_router(lookup.route)
app.include_router(api.route)
app.include_router(about.route)
app.include_router(sequence.route)
app.include_router(theme.route)


# Middleware #


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def check_and_redirect_offline(request: Request, call_next):
    offline = get_offline_switch()
    response = None

    if offline:
        if "application/json" in request.headers.get("accept", list()) or (
            request.url.path.startswith("/api")
            and request.url.path not in ["/api/docs", "/api"]
        ):
            return JSONResponse(
                content={"detail": "BOLD Portal API unavailable"},
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        elif "text/html" in request.headers.get("accept", list()):
            response_params = {
                "title": "Public Data Portal",
                "subtitle": "",
                "search_page": True,
                "wp_footer": True,
                "message": offline,
                "request": request,
            }
            return templates.TemplateResponse("offline.jinja2", response_params)
        else:
            response = await call_next(request)
    else:
        response = await call_next(request)
    return response


# General Exception Handling #


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    exc_logger.error(
        f'{request.client.host}:{request.client.port} - "{request.method} {request.url.path} {request["type"].upper()}/{request["http_version"]}"\n{traceback.format_exc()}'
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"[ERROR] Unknown exception: {exc}"},
    )
