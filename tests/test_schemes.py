from pathlib import Path

from app.models import Card
from app.services.splendor_schemes import SplendorSchemeCatalog


def test_catalog_contains_all_90_original_schemes() -> None:
    catalog = SplendorSchemeCatalog(Path(__file__).resolve().parents[1])
    assert len(catalog.schemes) == 90
    assert [scheme.id for scheme in catalog.schemes] == [f"op_{index:02d}" for index in range(1, 91)]


def test_first_black_scheme_uses_confirmed_resource_mapping() -> None:
    catalog = SplendorSchemeCatalog(Path(__file__).resolve().parents[1])
    scheme = catalog.schemes[0]
    assert scheme.source_color == "black"
    assert scheme.resource_type == "intelligence"
    assert scheme.tier == 1
    assert scheme.influence == 0
    assert scheme.cost == {
        "lmd": 1,
        "intelligence": 0,
        "logistics": 1,
        "medical": 1,
        "technology": 1,
    }


def test_scheme_match_is_derived_from_current_card_parameters() -> None:
    catalog = SplendorSchemeCatalog(Path(__file__).resolve().parents[1])
    scheme = catalog.schemes[0]
    card = Card(
        id="op_001",
        name="Example",
        tier=scheme.tier,
        operator_class="Sniper",
        influence=scheme.influence,
        artwork="assets/operators/exusiai.png",
        resource_type=scheme.resource_type,
        rhodes_island_emblems=0,
        cost=scheme.cost,
    )

    assert catalog.match(card) == scheme

    card.cost.logistics = 2
    assert catalog.match(card) is None


def test_scheme_usage_marks_duplicates() -> None:
    catalog = SplendorSchemeCatalog(Path(__file__).resolve().parents[1])
    scheme = catalog.schemes[0]
    base = {
        "tier": scheme.tier,
        "operator_class": "Sniper",
        "influence": scheme.influence,
        "artwork": "assets/operators/exusiai.png",
        "resource_type": scheme.resource_type,
        "rhodes_island_emblems": 0,
        "cost": scheme.cost,
    }
    cards = [Card(id="op_001", name="One", **base), Card(id="op_002", name="Two", **base)]

    usage = catalog.usage(cards)
    assert usage[scheme.id] == ["op_001", "op_002"]

    scheme_data = catalog.as_dicts(usage)[0]
    assert scheme_data["resource_label"] == "Intelligence"
    assert scheme_data["used_by"] == ["op_001", "op_002"]
