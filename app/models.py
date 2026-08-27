from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ResourceAmount = Annotated[int, Field(ge=0)]
RESOURCE_LABELS = {
    "lmd": "LMD",
    "intelligence": "Intelligence",
    "logistics": "Logistics",
    "medical": "Medical",
    "arts": "Arts",
}
ResourceType = Literal["lmd", "intelligence", "logistics", "medical", "arts"]


class Cost(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lmd: ResourceAmount = 0
    intelligence: ResourceAmount = 0
    logistics: ResourceAmount = 0
    medical: ResourceAmount = 0
    arts: ResourceAmount = 0


class Card(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Annotated[str, Field(pattern=r"^[a-z0-9_]+$")]
    name: Annotated[str, Field(min_length=1, max_length=80)]
    tier: Annotated[int, Field(ge=1, le=3)]
    operator_class: Annotated[str, Field(min_length=1, max_length=40)]
    influence: Annotated[int, Field(ge=0)]
    artwork: Annotated[str, Field(min_length=1)]
    resource_type: ResourceType = "lmd"
    rhodes_island_emblems: Annotated[int, Field(ge=0, le=2)] = 0
    cost: Cost

    @field_validator("name", "operator_class")
    @classmethod
    def no_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @property
    def active_costs(self) -> list[tuple[str, str, int]]:
        return [(resource, RESOURCE_LABELS[resource], amount) for resource, amount in self.cost.model_dump().items() if amount]

    @property
    def resource_costs(self) -> list[tuple[str, str, int]]:
        return [(resource, RESOURCE_LABELS[resource], amount) for resource, amount in self.cost.model_dump().items()]

    @property
    def resource_type_label(self) -> str:
        return RESOURCE_LABELS[self.resource_type]

    @property
    def roman_tier(self) -> str:
        return {1: "I", 2: "II", 3: "III"}[self.tier]
