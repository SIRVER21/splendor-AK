from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.card_loader import CardLoadError, CardLoader
from app.services.renderer import render_card

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = PROJECT_ROOT / "generated"
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


@app.get("/card/{card_id}", include_in_schema=False)
async def card_detail(request: Request, card_id: str):
    card = get_card_or_404(card_id)
    return templates.TemplateResponse(request, "card_detail.html", {"card": card, "png_exists": (GENERATED_DIR / f"{card.id}.png").is_file()})


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


@app.put("/api/card/{card_id}")
async def update_card(card_id: str, request: Request) -> dict:
    try:
        payload = await request.json()
        card = loader.save(card_id, payload)
    except (CardLoadError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"message": "Card saved. Generate PNG manually to update the image.", "card": card.model_dump()}


@app.get("/generated/{card_id}.png", include_in_schema=False)
async def generated_image(card_id: str) -> FileResponse:
    output_path = GENERATED_DIR / f"{card_id}.png"
    if not output_path.is_file():
        raise HTTPException(status_code=404, detail="PNG has not been generated yet.")
    return FileResponse(output_path, media_type="image/png")
