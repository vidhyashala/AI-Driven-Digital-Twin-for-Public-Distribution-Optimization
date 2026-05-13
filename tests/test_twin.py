from app.models import Commodity, ShopState, TwinEvent
from app.optimization.rl_env import VitaranAllocationEnv
from app.simulation.twin_engine import AnnapurnaTwinCore


def test_twin_ingestion_and_risk_field_updates_inventory():
    twin = AnnapurnaTwinCore(
        shops={
            "s1": ShopState(
                shop_id="s1",
                district="d1",
                inventory={Commodity.RICE: 10.0},
                daily_demand={Commodity.RICE: 10.0},
                vulnerability_index=0.5,
            )
        }
    )
    twin.ingest_event(
        TwinEvent(
            entity_id="s1",
            entity_type="shop",
            timestamp=1.0,
            payload={"inventory": {"rice": 20.0}, "climate_risk": 0.7},
            trust_score=0.5,
        )
    )
    assert twin.shops["s1"].inventory[Commodity.RICE] == 15.0
    assert twin.simulate_horizon()["s1"]["rice"] > 0


def test_optimizer_prioritizes_high_risk_shop():
    shops = {
        "low": ShopState(
            shop_id="low",
            district="d",
            inventory={Commodity.RICE: 100.0},
            daily_demand={Commodity.RICE: 5.0},
        ),
        "high": ShopState(
            shop_id="high",
            district="d",
            inventory={Commodity.RICE: 1.0},
            daily_demand={Commodity.RICE: 20.0},
            vulnerability_index=0.9,
            climate_risk=0.8,
        ),
    }
    env = VitaranAllocationEnv(shops=shops, warehouse_inventory={Commodity.RICE: 100.0})
    decisions = env.recommend_allocations("w1")
    assert decisions[0].shop_id == "high"
