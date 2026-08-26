import json
from pathlib import Path

from pydantic import ValidationError

from app.models import Card


class CardLoadError(ValueError):
    """A card JSON file is absent or does not satisfy the schema."""


class CardLoader:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.cards_dir = project_root / "cards"

    def load(self, card_id: str) -> Card:
        card_path = self.cards_dir / f"{card_id}.json"
        if not card_path.is_file():
            raise CardLoadError(f"Card '{card_id}' does not exist.")
        try:
            payload = json.loads(card_path.read_text(encoding="utf-8"))
            card = Card.model_validate(payload)
        except json.JSONDecodeError as error:
            raise CardLoadError(f"Invalid JSON in {card_path.name}: {error.msg}") from error
        except ValidationError as error:
            messages = "; ".join(
                f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                for item in error.errors()
            )
            raise CardLoadError(f"Invalid card data in {card_path.name}: {messages}") from error
        if card.id != card_id:
            raise CardLoadError(f"Filename '{card_id}.json' and JSON id '{card.id}' must match.")
        if not (self.project_root / card.artwork).is_file():
            raise CardLoadError(f"Artwork does not exist: {card.artwork}")
        return card

    def save(self, card_id: str, payload: dict) -> Card:
        """Validate and persist user-edited JSON while keeping filename and id aligned."""
        payload["id"] = card_id
        try:
            card = Card.model_validate(payload)
        except ValidationError as error:
            messages = "; ".join(
                f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                for item in error.errors()
            )
            raise CardLoadError(f"Invalid card data: {messages}") from error
        if not (self.project_root / card.artwork).is_file():
            raise CardLoadError(f"Artwork does not exist: {card.artwork}")
        path = self.cards_dir / f"{card_id}.json"
        path.write_text(json.dumps(card.model_dump(), indent=2) + "\n", encoding="utf-8")
        return card
