from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


ResourceAmount = Annotated[int, Field(ge=0)]
RESOURCE_LABELS = {
    "lmd": "LMD",
    "intelligence": "Intelligence",
    "logistics": "Logistics",
    "medical": "Medical",
    "arts": "Arts",
    "originium": "Originium",
}


class Cost(BaseModel):
    lmd: ResourceAmount = 0
    intelligence: ResourceAmount = 0
    logistics: ResourceAmount = 0
    medical: ResourceAmount = 0
    arts: ResourceAmount = 0
    originium: ResourceAmount = 0


class Card(BaseModel):
    id: Annotated[str, Field(pattern=r"^[a-z0-9_]+$")]
    name: Annotated[str, Field(min_length=1, max_length=80)]
    tier: Annotated[int, Field(ge=1, le=3)]
    operator_class: Annotated[str, Field(min_length=1, max_length=40)]
    influence: Annotated[int, Field(ge=0)]
    artwork: Annotated[str, Field(min_length=1)]
    cost: Cost

    @field_validator("name", "operator_class")
    @classmethod
    def no_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def validate_originium(self) -> "Card":
        if self.tier == 3 and self.cost.originium == 0:
            raise ValueError("Tier 3 cards require at least 1 Originium.")
        if self.tier != 3 and self.cost.originium != 0:
            raise ValueError("Originium is allowed only on Tier 3 cards.")
        return self

    @property
    def active_costs(self) -> list[tuple[str, str, int]]:
        return [(resource, RESOURCE_LABELS[resource], amount) for resource, amount in self.cost.model_dump().items() if amount]

    @property
    def resource_costs(self) -> list[tuple[str, str, int]]:
        return [(resource, RESOURCE_LABELS[resource], amount) for resource, amount in self.cost.model_dump().items()]
