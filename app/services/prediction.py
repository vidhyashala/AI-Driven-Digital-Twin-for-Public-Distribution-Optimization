"""Prediction microservice primitives for demand and risk intelligence."""

from __future__ import annotations

from app.models import Commodity, ShopState


class DrishtiPredictor:
    """Lightweight deterministic stand-in for transformer and graph models."""

    def forecast_demand(self, shop: ShopState, commodity: Commodity, horizon_days: int = 7) -> float:
        base = shop.daily_demand.get(commodity, 0.0) * horizon_days
        vulnerability_lift = 1.0 + 0.25 * shop.vulnerability_index
        climate_lift = 1.0 + 0.35 * shop.climate_risk
        return round(base * vulnerability_lift * climate_lift, 3)

    def entitlement_failure_risk(self, shop: ShopState, commodity: Commodity, horizon_days: int = 7) -> float:
        forecast = self.forecast_demand(shop, commodity, horizon_days)
        inventory = shop.inventory.get(commodity, 0.0)
        shortage_ratio = max(0.0, forecast - inventory) / max(forecast, 1.0)
        risk = 0.55 * shortage_ratio + 0.25 * shop.fraud_risk + 0.20 * shop.climate_risk
        return round(min(1.0, risk), 4)
