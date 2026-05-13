"""Starter reinforcement-learning style environment for PDS allocation."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models import AllocationDecision, Commodity, ShopState
from app.services.prediction import DrishtiPredictor


@dataclass
class VitaranAllocationEnv:
    """Greedy baseline that exposes RL-compatible state/action/reward concepts."""

    shops: dict[str, ShopState]
    warehouse_inventory: dict[Commodity, float]
    predictor: DrishtiPredictor = field(default_factory=DrishtiPredictor)

    def observe(self) -> dict[str, dict[str, float]]:
        return {
            shop_id: {
                commodity.value: self.predictor.entitlement_failure_risk(shop, commodity)
                for commodity in Commodity
            }
            for shop_id, shop in self.shops.items()
        }

    def recommend_allocations(self, warehouse_id: str, max_shipments: int = 10) -> list[AllocationDecision]:
        candidates: list[AllocationDecision] = []
        for shop in self.shops.values():
            for commodity in Commodity:
                risk = self.predictor.entitlement_failure_risk(shop, commodity)
                forecast = self.predictor.forecast_demand(shop, commodity)
                gap = max(0.0, forecast - shop.inventory.get(commodity, 0.0))
                priority = risk * (1.0 + shop.vulnerability_index + shop.climate_risk)
                if gap > 0 and self.warehouse_inventory.get(commodity, 0.0) > 0:
                    quantity = min(gap, self.warehouse_inventory[commodity])
                    candidates.append(
                        AllocationDecision(
                            warehouse_id=warehouse_id,
                            shop_id=shop.shop_id,
                            commodity=commodity,
                            quantity=round(quantity, 3),
                            priority_score=round(priority, 4),
                            explanation=(
                                f"High entitlement pressure: risk={risk}, "
                                f"vulnerability={shop.vulnerability_index}, climate={shop.climate_risk}."
                            ),
                        )
                    )
        candidates.sort(key=lambda decision: decision.priority_score, reverse=True)
        return candidates[:max_shipments]

    @staticmethod
    def reward(stockout_days: float, leakage_risk: float, delay_hours: float, served_ratio: float) -> float:
        return round(-2.0 * stockout_days - 1.5 * leakage_risk - 0.1 * delay_hours + 5.0 * served_ratio, 4)
