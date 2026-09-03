from base64 import b64decode
from pathlib import Path
from re import fullmatch

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import Card
from app.services.card_loader import CardLoadError, CardLoader
from app.services.renderer import render_card

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = PROJECT_ROOT / "generated"
ARTWORK_DIR = PROJECT_ROOT / "assets" / "operators"
loader = CardLoader(PROJECT_ROOT)

app = FastAPI(title="Arknights Card Generator")
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "app" / "static"), name="static")
app.mount("/assets", StaticFiles(directory=PROJECT_ROOT / "assets"), name="assets")
templates = Jinja2Templates(directory=PROJECT_ROOT / "app" / "templates")


def get_card_or_404(card_id: str):
    try:
        return loader.load(card_id)
    except CardLoadError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def save_uploaded_artwork(card_id: str, data_url: str) -> str:
    match = fullmatch(r"data:(image/(?:png|jpeg|webp));base64,(.+)", data_url)
    if not match:
        raise ValueError("Use a PNG, JPEG, or WebP image.")
    media_type, encoded = match.groups()
    raw = b64decode(encoded, validate=True)
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("Artwork must be 10 MB or smaller.")
    extensions = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
    extension = extensions[media_type]
    filename = f"{card_id}.{extension}"
    output_path = ARTWORK_DIR / filename
    ARTWORK_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw)
    return f"assets/operators/{filename}"


@app.get("/", include_in_schema=False)
async def home(request: Request):
    cards = loader.list_cards()
    gallery_cards = [
        {
            "card": card,
            "png_exists": (GENERATED_DIR / f"{card.id}.png").is_file(),
            "png_url": f"/generated/{card.id}.png",
        }
        for card in cards
    ]
    return templates.TemplateResponse(request, "gallery.html", {"cards": gallery_cards})


@app.get("/card/new", include_in_schema=False)
async def new_card(request: Request):
    cards = loader.list_cards()
    preview_card_id = cards[0].id if cards else None
    return templates.TemplateResponse(
        request,
        "card_detail.html",
        {
            "card": None,
            "is_new": True,
            "png_exists": False,
            "next_card_id": loader.next_card_id(),
            "preview_card_id": preview_card_id,
        },
    )


@app.get("/card/{card_id}", include_in_schema=False)
async def card_detail(request: Request, card_id: str):
    card = get_card_or_404(card_id)
    return templates.TemplateResponse(request, "card_detail.html", {"card": card, "is_new": False, "png_exists": (GENERATED_DIR / f"{card.id}.png").is_file()})


@app.get("/render/{card_id}", include_in_schema=False)
async def card_render(request: Request, card_id: str):
    return templates.TemplateResponse(request, "card_render.html", {"card": get_card_or_404(card_id)})


@app.post("/card/{card_id}/generate", include_in_schema=False)
async def generate_card(request: Request, card_id: str) -> RedirectResponse:
    card = get_card_or_404(card_id)
    await render_card(str(request.url_for("card_render", card_id=card.id)), GENERATED_DIR / f"{card.id}.png")
    return RedirectResponse(url=f"/card/{card.id}", status_code=303)


@app.post("/generate-missing", include_in_schema=False)
async def generate_missing(request: Request) -> RedirectResponse:
    for card in loader.list_cards():
        output_path = GENERATED_DIR / f"{card.id}.png"
        if not output_path.is_file():
            await render_card(str(request.url_for("card_render", card_id=card.id)), output_path)
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/card")
async def create_card(request: Request) -> dict:
    artwork_path = None
    try:
        payload = await request.json()
        artwork_data = payload.pop("artwork_data", None)
        if artwork_data is not None:
            if not isinstance(artwork_data, str):
                raise ValueError("Artwork data is required.")
            artwork_path = save_uploaded_artwork(payload["id"], artwork_data)
            payload["artwork"] = artwork_path
        card = loader.create(payload)
    except (CardLoadError, ValueError, KeyError) as error:
        if artwork_path:
            artwork_file = PROJECT_ROOT / artwork_path
            if artwork_file.is_file() and not (PROJECT_ROOT / "cards" / f"{payload.get('id', '')}.json").is_file():
                artwork_file.unlink()
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"message": "Card created.", "card": card.model_dump()}


@app.put("/api/card/{card_id}")
async def update_card(card_id: str, request: Request) -> dict:
    try:
        payload = await request.json()
        card = loader.save(card_id, payload)
    except (CardLoadError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"message": "Card saved. Generate PNG manually to update the image.", "card": card.model_dump()}


@app.post("/api/card/{card_id}/artwork")
async def upload_artwork(card_id: str, request: Request) -> dict:
    card = get_card_or_404(card_id)
    try:
        payload = await request.json()
        data_url = payload.get("data")
        if not isinstance(data_url, str):
            raise ValueError("Artwork data is required.")
        artwork_path = save_uploaded_artwork(card_id, data_url)
        updated = card.model_dump()
        updated["artwork"] = artwork_path
        loader.save(card_id, updated)
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"message": "Artwork uploaded.", "artwork": artwork_path}


@app.get("/generated/{card_id}.png", include_in_schema=False)
async def generated_image(card_id: str) -> FileResponse:
    output_path = GENERATED_DIR / f"{card_id}.png"
    if not output_path.is_file():
        raise HTTPException(status_code=404, detail="PNG has not been generated yet.")
    return FileResponse(output_path, media_type="image/png")
