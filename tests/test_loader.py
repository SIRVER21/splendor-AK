from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import Card
from app.services.card_loader import CardLoader


def test_example_card_loads() -> None:
    root = Path(__file__).resolve().parents[1]
    card = CardLoader(root).load("op_001")
    assert card.name == "Exusiai"
    assert all(amount > 0 for _, _, amount in card.active_costs)
    assert len(card.resource_costs) == 5


def test_operator_material_is_limited_to_material_resources() -> None:
    data = CardLoader(Path(__file__).resolve().parents[1]).load("op_001").model_dump()
    data["resource_type"] = "technology"
    assert Card.model_validate(data).resource_type_label == "Technology"

    data["resource_type"] = "originium"
    with pytest.raises(ValidationError):
        Card.model_validate(data)


def test_emblem_count_is_limited_to_two() -> None:
    data = CardLoader(Path(__file__).resolve().parents[1]).load("op_001").model_dump()
    data["rhodes_island_emblems"] = 2
    assert Card.model_validate(data).rhodes_island_emblems == 2
    data["rhodes_island_emblems"] = 3
    with pytest.raises(ValidationError):
        Card.model_validate(data)


def test_artwork_settings_have_defaults_and_validation() -> None:
    data = CardLoader(Path(__file__).resolve().parents[1]).load("op_001").model_dump()
    data.pop("artwork_x", None)
    data.pop("artwork_y", None)
    data.pop("artwork_scale", None)
    data.pop("background_color", None)
    card = Card.model_validate(data)
    assert card.artwork_x == 50
    assert card.artwork_y == 50
    assert card.artwork_scale == 1
    assert card.background_color == "#291931"

    data["artwork_scale"] = 4
    with pytest.raises(ValidationError):
        Card.model_validate(data)

    data["artwork_scale"] = 1
    data["background_color"] = "purple"
    with pytest.raises(ValidationError):
        Card.model_validate(data)


def test_create_card_writes_json(tmp_path: Path) -> None:
    root = tmp_path
    (root / "cards").mkdir()
    artwork = root / "assets" / "operators" / "new.png"
    artwork.parent.mkdir(parents=True)
    artwork.write_bytes(b"test")

    payload = {
        "id": "op_002",
        "name": "New Operator",
        "tier": 2,
        "operator_class": "Caster",
        "influence": 2,
        "artwork": "assets/operators/new.png",
        "resource_type": "technology",
        "rhodes_island_emblems": 1,
        "cost": {
            "lmd": 2,
            "intelligence": 1,
            "logistics": 0,
            "medical": 0,
            "technology": 2,
        },
    }

    card = CardLoader(root).create(payload)

    assert card.id == "op_002"
    assert (root / "cards" / "op_002.json").is_file()
    assert CardLoader(root).load("op_002").name == "New Operator"


def test_create_card_rejects_duplicate_id(tmp_path: Path) -> None:
    root = tmp_path
    (root / "cards").mkdir()
    (root / "assets").mkdir()
    (root / "cards" / "op_002.json").write_text("{}", encoding="utf-8")

    payload = {
        "id": "op_002",
        "name": "New Operator",
        "tier": 1,
        "operator_class": "Caster",
        "influence": 0,
        "artwork": "assets/new.png",
        "resource_type": "lmd",
        "cost": {},
    }

    with pytest.raises(ValueError, match="already exists"):
        CardLoader(root).create(payload)
