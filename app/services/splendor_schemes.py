import json
from dataclasses import dataclass
from pathlib import Path

from app.models import Card

RESOURCE_TYPES = ("lmd", "intelligence", "logistics", "medical", "technology")


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

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "tier": self.tier,
            "influence": self.influence,
            "resource_type": self.resource_type,
            "cost": self.cost,
            "source_color": self.source_color,
        }


class SplendorSchemeCatalog:
    def __init__(self, project_root: Path) -> None:
        self.path = project_root / "data" / "splendor_schemes.json"
        self._schemes = self._load()

    def _load(self) -> tuple[SplendorScheme, ...]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        schemes = tuple(SplendorScheme(**item) for item in payload)
        if len(schemes) != 90:
            raise ValueError(f"Expected 90 Splendor schemes, found {len(schemes)}.")
        if len({scheme.id for scheme in schemes}) != len(schemes):
            raise ValueError("Splendor scheme IDs must be unique.")
        return schemes

    @property
    def schemes(self) -> tuple[SplendorScheme, ...]:
        return self._schemes

    def as_dicts(self) -> list[dict]:
        return [scheme.as_dict() for scheme in self._schemes]

    def match(self, card: Card) -> SplendorScheme | None:
        return next((scheme for scheme in self._schemes if scheme.matches(card)), None)

    def usage(self, cards: list[Card]) -> dict[str, list[str]]:
        result = {scheme.id: [] for scheme in self._schemes}
        for card in cards:
            scheme = self.match(card)
            if scheme is not None:
                result[scheme.id].append(card.id)
        return result
