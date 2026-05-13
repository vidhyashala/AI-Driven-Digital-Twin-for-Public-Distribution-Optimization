"""Domain models for the AstraKshetra Nexus PDS digital twin."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Commodity(StrEnum):
    """Supported public-distribution commodities."""

    RICE = "rice"
    WHEAT = "wheat"
    PULSES = "pulses"
    KEROSENE = "kerosene"


@dataclass
class TwinEvent:
    """Event emitted by a physical node into the cyber twin."""

    entity_id: str
    entity_type: str
    timestamp: float
    payload: dict[str, Any] = field(default_factory=dict)
    trust_score: float = 0.8

    def __post_init__(self) -> None:
        self.trust_score = min(1.0, max(0.0, self.trust_score))


@dataclass
class ShopState:
    """Executable fair-price-shop state used by simulation and optimization."""

    shop_id: str
    district: str
    inventory: dict[Commodity, float] = field(default_factory=dict)
    daily_demand: dict[Commodity, float] = field(default_factory=dict)
    vulnerability_index: float = 0.5
    fraud_risk: float = 0.0
    climate_risk: float = 0.0

    def __post_init__(self) -> None:
        self.vulnerability_index = min(1.0, max(0.0, self.vulnerability_index))
        self.fraud_risk = min(1.0, max(0.0, self.fraud_risk))
        self.climate_risk = min(1.0, max(0.0, self.climate_risk))


@dataclass
class AllocationDecision:
    """Recommended transfer from a warehouse to a shop."""

    warehouse_id: str
    shop_id: str
    commodity: Commodity
    quantity: float
    priority_score: float
    explanation: str

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["commodity"] = self.commodity.value
        return payload
