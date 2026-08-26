from pathlib import Path

from playwright.async_api import async_playwright


CARD_WIDTH = 750
CARD_HEIGHT = 1039


async def render_card(page_url: str, output_path: Path) -> None:
    """Open the render-only page and capture the physical card area as a PNG."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": CARD_WIDTH, "height": CARD_HEIGHT}, device_scale_factor=1)
        await page.goto(page_url, wait_until="networkidle")
        await page.locator(".card").screenshot(path=str(output_path))
        await browser.close()

