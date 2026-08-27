# Arknights Card Generator

Pierwszy etap lokalnego generatora: pojedynczy plik JSON jest renderowany jako podgląd HTML/CSS, a przycisk **Generate PNG** zapisuje obraz lokalnie.

## Uruchomienie

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/playwright install chromium
.venv/bin/uvicorn app.main:app --reload
```

Następnie otwórz `http://127.0.0.1:8000/card/op_001`.

## Dane karty

Każda karta jest osobnym plikiem w `cards/`. Pierwszy etap obsługuje następujący schemat:

```json
{
  "id": "op_001",
  "name": "Exusiai",
  "tier": 1,
  "operator_class": "Sniper",
  "influence": 1,
  "artwork": "assets/operators/exusiai.svg",
  "resource_type": "intelligence",
  "rhodes_island_emblems": 0,
  "cost": { "lmd": 2, "intelligence": 0, "logistics": 1, "medical": 0, "arts": 0 }
}
```

`tier` ma zakres 1–3, `influence` i wszystkie koszty nie mogą być ujemne, a wskazany artwork musi istnieć. Koszty o wartości `0` nie są wyświetlane. `resource_type` to niezależny materiał/operator accent i może być jednym z: `lmd`, `intelligence`, `logistics`, `medical`, `arts`. `Originium` nie jest walutą ani edytowalnym kosztem: jest automatycznym elementem designu każdej karty Tier 3 i tylko Tier 3.

## Następny etap

Galeria, wyszukiwanie, manifest hashów i generowanie brakujących kart zostaną dodane po zatwierdzeniu podstawowego przepływu.
