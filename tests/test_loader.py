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


def test_originium_bonus_is_required_on_tier_three_only() -> None:
    data = CardLoader(Path(__file__).resolve().parents[1]).load("op_001").model_dump()
    data["tier"] = 3
    data["originium_bonus"] = 0
    with pytest.raises(ValidationError, match="grant exactly 1 Originium"):
        Card.model_validate(data)

    data["originium_bonus"] = 1
    assert Card.model_validate(data).originium_bonus == 1


def test_emblem_count_is_limited_to_two() -> None:
    data = CardLoader(Path(__file__).resolve().parents[1]).load("op_001").model_dump()
    data["rhodes_island_emblems"] = 2
    assert Card.model_validate(data).rhodes_island_emblems == 2
    data["rhodes_island_emblems"] = 3
    with pytest.raises(ValidationError):
        Card.model_validate(data)
