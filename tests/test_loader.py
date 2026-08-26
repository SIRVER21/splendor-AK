from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import Card
from app.services.card_loader import CardLoader


def test_example_card_loads() -> None:
    root = Path(__file__).resolve().parents[1]
    card = CardLoader(root).load("op_001")
    assert card.name == "Exusiai"
    assert card.active_costs == [("lmd", "LMD", 2), ("logistics", "Logistics", 1)]


def test_originium_is_required_on_tier_three_only() -> None:
    data = CardLoader(Path(__file__).resolve().parents[1]).load("op_001").model_dump()
    data["tier"] = 3
    with pytest.raises(ValidationError, match="require at least 1 Originium"):
        Card.model_validate(data)

    data["cost"]["originium"] = 1
    assert Card.model_validate(data).cost.originium == 1
