from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

import os
import pathlib
import qrcode
import sys
import tempfile

try:
    import util
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import util

route = APIRouter(tags=["qr"])


@route.get(
    "/qr-code/sequence",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"image/jpeg": {}},
            "description": "Sequence QR Image",
        },
    },
)
async def generate_sequence_qr_code(
    request: Request,
    sequence: str = Query(title="Sequence to translate"),
):
    """
    Generate a QR code of the given sequence.

    - **sequence**: Sequence string.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp_qr_file:
        img = qrcode.make(f"{request.base_url}sequence/{sequence}")
        img.save(tmp_qr_file.name)

        return FileResponse(
            tmp_qr_file.name,
            media_type="image/png",
            background=BackgroundTask(lambda tmp: os.remove(tmp), tmp_qr_file.name),
        )


@route.get(
    "/qr-code/record",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"image/jpeg": {}},
            "description": "Record QR Image",
        },
    },
)
async def generate_record_qr_code(
    request: Request,
    processid: str = Query(title="Process ID of the record"),
):
    """
    Generate a QR code of the given record based on processid.

    - **processid**: Process ID string.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp_qr_file:
        img = qrcode.make(f"{request.base_url}record/{processid}")
        img.save(tmp_qr_file.name)

        return FileResponse(
            tmp_qr_file.name,
            media_type="image/png",
            background=BackgroundTask(lambda tmp: os.remove(tmp), tmp_qr_file.name),
        )

