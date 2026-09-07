import json
from dataclasses import dataclass
from pathlib import Path

from app.models import Card

SOURCE_COLORS = ("black", "blue", "green", "red", "white")
SOURCE_TO_RESOURCE = {
    "black": "intelligence",
    "blue": "lmd",
    "green": "medical",
    "red": "logistics",
    "white": "technology",
}
RESOURCE_LABELS = {
    "lmd": "LMD",
    "intelligence": "Intelligence",
    "logistics": "Logistics",
    "medical": "Medical",
    "technology": "Technology",
}


@dataclass(frozen=True)
class SplendorScheme:
    id: str
    tier: int
    influence: int
    resource_type: str
    cost: dict[str, int]
    source_color: str

    def matches(self, card: Card) -> bool:
        return (
            card.tier == self.tier
            and card.influence == self.influence
            and card.resource_type == self.resource_type
            and all(getattr(card.cost, resource) == amount for resource, amount in self.cost.items())
        )

    def as_dict(self, used_by: list[str] | None = None) -> dict:
        return {
            "id": self.id,
            "tier": self.tier,
            "influence": self.influence,
            "resource_type": self.resource_type,
            "resource_label": RESOURCE_LABELS[self.resource_type],
            "cost": self.cost,
            "source_color": self.source_color,
            "used_by": used_by or [],
        }


class SplendorSchemeCatalog:
    def __init__(self, project_root: Path) -> None:
        self.path = project_root / "data" / "splendor_card_tables.json"
        self._schemes = self._load()

    def _load(self) -> tuple[SplendorScheme, ...]:
        tables = json.loads(self.path.read_text(encoding="utf-8"))
        schemes: list[SplendorScheme] = []
        for color in SOURCE_COLORS:
            rows = tables[color]
            if len(rows) != 18:
                raise ValueError(f"Expected 18 {color} cards, found {len(rows)}.")
            for index, row in enumerate(rows):
                if len(row) != 6:
                    raise ValueError(f"Invalid {color} card row at index {index}.")
                points, black, white, red, blue, green = row
                tier = 1 if index < 8 else 2 if index < 14 else 3
                scheme_id = f"op_{len(schemes) + 1:02d}"
                schemes.append(
                    SplendorScheme(
                        id=scheme_id,
                        tier=tier,
                        influence=points,
                        resource_type=SOURCE_TO_RESOURCE[color],
                        cost={
                            "lmd": blue,
                            "intelligence": black,
                            "logistics": red,
                            "medical": green,
                            "technology": white,
                        },
                        source_color=color,
                    )
                )
        if len(schemes) != 90:
            raise ValueError(f"Expected 90 Splendor schemes, found {len(schemes)}.")
        return tuple(schemes)

    @property
    def schemes(self) -> tuple[SplendorScheme, ...]:
        return self._schemes

    def usage(self, cards: list[Card]) -> dict[str, list[str]]:
        result = {scheme.id: [] for scheme in self._schemes}
        for card in cards:
            scheme = self.match(card)
            if scheme is not None:
                result[scheme.id].append(card.id)
        return result

    def as_dicts(self, usage: dict[str, list[str]] | None = None) -> list[dict]:
        usage = usage or {scheme.id: [] for scheme in self._schemes}
        return [scheme.as_dict(usage.get(scheme.id, [])) for scheme in self._schemes]

    def match(self, card: Card) -> SplendorScheme | None:
        return next((scheme for scheme in self._schemes if scheme.matches(card)), None)
