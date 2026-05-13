"""FastAPI backend for the AstraKshetra Nexus PDS-DigitalTwin prototype."""

from __future__ import annotations

import time

from fastapi import FastAPI

from app.models import Commodity, ShopState, TwinEvent
from app.optimization.rl_env import VitaranAllocationEnv
from app.simulation.twin_engine import AnnapurnaTwinCore
from app.streaming.kafka_bus import KafkaTwinBus

app = FastAPI(
    title="PDS-DigitalTwin: AstraKshetra Nexus",
    description="AI-driven digital twin starter backend for public distribution optimization.",
    version="0.1.0",
)

bus = KafkaTwinBus()
twin = AnnapurnaTwinCore(
    shops={
        "shop-101": ShopState(
            shop_id="shop-101",
            district="Kshetra-North",
            inventory={Commodity.RICE: 120.0, Commodity.WHEAT: 80.0, Commodity.PULSES: 25.0},
            daily_demand={Commodity.RICE: 30.0, Commodity.WHEAT: 20.0, Commodity.PULSES: 8.0},
            vulnerability_index=0.72,
            fraud_risk=0.14,
            climate_risk=0.35,
        ),
        "shop-202": ShopState(
            shop_id="shop-202",
            district="Kshetra-South",
            inventory={Commodity.RICE: 55.0, Commodity.WHEAT: 140.0, Commodity.PULSES: 10.0},
            daily_demand={Commodity.RICE: 22.0, Commodity.WHEAT: 19.0, Commodity.PULSES: 7.0},
            vulnerability_index=0.88,
            fraud_risk=0.31,
            climate_risk=0.68,
        ),
    }
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "framework": "AstraKshetra Nexus"}


@app.post("/iot/events")
def ingest_iot_event(event: TwinEvent) -> dict[str, int | str]:
    """Ingest IoT/ePOS/GPS telemetry and update the digital twin."""
    bus.publish("pds.telemetry", event)
    for message in bus.consume("pds.telemetry"):
        twin.ingest_event(message)
    return {"status": "accepted", "processed_at": int(time.time())}


@app.get("/twin/paef")
def paef(horizon_days: int = 7) -> dict[str, dict[str, float]]:
    """Return the Pratyaksha Anticipatory Entitlement Field risk snapshot."""
    return twin.simulate_horizon(horizon_days=horizon_days)


@app.get("/optimize/allocations")
def optimize_allocations() -> list[dict[str, object]]:
    """Recommend deprivation-weighted stock transfers from a demo warehouse."""
    env = VitaranAllocationEnv(
        shops=twin.shops,
        warehouse_inventory={Commodity.RICE: 500.0, Commodity.WHEAT: 400.0, Commodity.PULSES: 120.0},
    )
    return [decision.to_json() for decision in env.recommend_allocations("warehouse-alpha")]
