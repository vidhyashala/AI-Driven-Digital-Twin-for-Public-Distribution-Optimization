"""Digital twin simulation engine for AstraKshetra Nexus."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models import Commodity, ShopState, TwinEvent
from app.services.prediction import DrishtiPredictor


@dataclass
class AnnapurnaTwinCore:
    """Maintains executable shop states and simulates entitlement pressure."""

    shops: dict[str, ShopState] = field(default_factory=dict)
    predictor: DrishtiPredictor = field(default_factory=DrishtiPredictor)

    def ingest_event(self, event: TwinEvent) -> None:
        """Assimilate a physical event using simple trust-weighted updates."""
        if event.entity_type != "shop" or event.entity_id not in self.shops:
            return
        shop = self.shops[event.entity_id]
        payload_inventory = event.payload.get("inventory", {})
        for key, observed_value in payload_inventory.items():
            commodity = Commodity(key)
            prior = shop.inventory.get(commodity, 0.0)
            shop.inventory[commodity] = round(
                event.trust_score * float(observed_value) + (1 - event.trust_score) * prior,
                3,
            )
        if "fraud_risk" in event.payload:
            shop.fraud_risk = min(1.0, max(0.0, float(event.payload["fraud_risk"])))
        if "climate_risk" in event.payload:
            shop.climate_risk = min(1.0, max(0.0, float(event.payload["climate_risk"])))

    def simulate_horizon(self, horizon_days: int = 7) -> dict[str, dict[str, float]]:
        """Project commodity-wise entitlement failure risk for each shop."""
        field: dict[str, dict[str, float]] = {}
        for shop_id, shop in self.shops.items():
            field[shop_id] = {
                commodity.value: self.predictor.entitlement_failure_risk(shop, commodity, horizon_days)
                for commodity in Commodity
            }
        return field
