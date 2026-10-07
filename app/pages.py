from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).parent / "static"

router = APIRouter()


def _page(name: str) -> FileResponse:
    return FileResponse(STATIC_DIR / name, media_type="text/html")


@router.get("/", include_in_schema=False)
def index():
    return _page("index.html")


@router.get("/totem", include_in_schema=False)
def totem():
    return _page("totem.html")


@router.get("/cozinha", include_in_schema=False)
def kitchen():
    return _page("cozinha.html")


@router.get("/painel", include_in_schema=False)
def panel_page():
    return _page("painel.html")
