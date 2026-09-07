# Arknights Card Generator

Local web-based card generator for a fan-made Arknights-themed version of Splendor.

The project allows you to create and edit cards, preview them in the browser and generate PNG files locally.

## Features

- Card gallery with search by ID and name.
- Create and edit cards through the web interface.
- Live card preview.
- Artwork upload with position and scale controls.
- Generate individual cards or all missing PNGs.
- Card data stored as JSON files in `cards/`.
- Complete schemes for all 90 original Splendor development cards.
- Scheme selector automatically fills card parameters.
- Automatic scheme matching and duplicate detection.

## Requirements

- Python 3.11+
- Chromium
- Playwright

## Installation

```bash
git clone https://github.com/SIRVER21/splendor-AK.git
cd splendor-AK

python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/playwright install chromium
```

## Running

```bash
.venv/bin/uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

The main page contains the card gallery.

## Card Schemes

The project contains the original parameters of all 90 Splendor development cards.

Schemes are identified as `op_01` through `op_90` and are stored in:

```text
data/splendor_card_tables.json
```

Original Splendor gem colors are mapped to project materials:

| Splendor | Project |
| --- | --- |
| Black | Intelligence |
| Blue | LMD |
| Green | Medical |
| Red | Logistics |
| White | Technology |

Original Splendor point values are used as Influence, and the original cost quantities are preserved.

Selecting a scheme in the editor automatically fills the corresponding Tier, Influence, material and costs.

A card matches a scheme only when its current parameters exactly match it. Changing those parameters removes the match automatically.

If multiple cards use the same scheme, the gallery and editor display a duplicate warning.

## Rendering

Cards are rendered locally using Playwright and Chromium.

Target card size:

```text
63.5 × 88 mm
```

PNG resolution:

```text
750 × 1039 px
```

Generated images are stored in:

```text
generated/
```

## Testing

Run the test suite with:

```bash
.venv/bin/pytest
```

## Project Structure

```text
app/          Application code
assets/       Card artwork and icons
cards/        Card JSON files
data/         Splendor scheme data
generated/    Generated PNG files
tests/        Tests
```

The project uses FastAPI, Jinja2, vanilla JavaScript, CSS, Pydantic, Playwright and JSON storage.
