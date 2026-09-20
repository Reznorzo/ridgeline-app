import unittest

from app.models import GearItem
from app.services.recommend import POLICY, generate_recommendation


def gear_item(name: str, category: str, **values) -> GearItem:
    slug = name.casefold().replace(" ", "-")
    return GearItem(id=f"gear:{slug}", name=name, category=category, owned=True, status=["owned"], **values)


def current_inventory() -> list[GearItem]:
    return [
        gear_item("Rab Borealis", "Jacket", protection_evidence="needs_test", breathability="high"),
        gear_item("Mountain Equipment Echo", "Jacket", protection_evidence="needs_test", breathability="moderate"),
        gear_item("Keela Saxon", "Jacket", waterproof=True, protection_evidence="confirmed"),
        gear_item("Patagonia Terrebonne Trousers", "Trousers", season="warm", breathability="high"),
        gear_item("Mountain Equipment Comici Trousers", "Trousers", season="all-weather"),
        gear_item("Mountain Equipment Ibex Trousers", "Trousers", season="winter"),
        gear_item("Keela Lightning Pro Overtrousers", "Overtrousers", layer_role="overtrouser"),
        gear_item("Topo Mountain Racer 4", "Footwear", waterproof=False, breathability="high"),
        gear_item("Scarpa Terra GTX", "Boots", waterproof=True),
        gear_item("Waterproof Socks", "Socks", waterproof=True),
    ]


def buckets(recommendation) -> dict[str, str]:
    return {item.gear_item.name: item.bucket for item in recommendation.items}


class RecommendationTest(unittest.TestCase):
    def test_warm_dry_high_effort_prefers_breathable_options(self):
        recommendation = generate_recommendation(
            route={"name": "Short loop", "expected_duration_min": 150},
            forecast={
                "high_route_temp_min": 12,
                "high_route_temp_max": 17,
                "rain_prob": 0.1,
                "rain_amount_mm": 0,
                "wind_speed_mph": 10,
            },
            gear_items=current_inventory(),
            exposure="sheltered",
            effort="high",
        )

        result = buckets(recommendation)
        self.assertEqual(result["Topo Mountain Racer 4"], "wear")
        self.assertEqual(result["Patagonia Terrebonne Trousers"], "wear")
        self.assertEqual(result["Rab Borealis"], "wear")
        self.assertEqual(result["Waterproof Socks"], "leave_home")
        self.assertEqual(result["Keela Saxon"], "leave_home")
        self.assertEqual(result["Keela Lightning Pro Overtrousers"], "leave_home")
        self.assertEqual(recommendation.summary, "Keep it light and breathable.")

    def test_warm_intermittent_shower_does_not_force_shell_wear(self):
        recommendation = generate_recommendation(
            route={"name": "Woodland", "expected_duration_min": 120},
            forecast={
                "high_route_temp_min": 12,
                "high_route_temp_max": 15,
                "rain_prob": 0.7,
                "rain_amount_mm": 0.5,
                "wind_speed_mph": 12,
            },
            gear_items=current_inventory(),
            exposure="sheltered",
            effort="high",
        )

        result = buckets(recommendation)
        self.assertEqual(result["Rab Borealis"], "wear")
        self.assertEqual(result["Keela Saxon"], "optional")
        self.assertEqual(result["Keela Lightning Pro Overtrousers"], "optional")
        self.assertEqual(result["Waterproof Socks"], "pack")
        self.assertNotEqual(result["Keela Saxon"], "wear")
        socks = next(item for item in recommendation.items if item.gear_item.name == "Waterproof Socks")
        self.assertEqual(socks.depends_on_gear_ids, ["gear:topo-mountain-racer-4"])
        self.assertTrue(socks.combination_reason)

    def test_cool_prolonged_rain_packs_confirmed_protection_and_overtrousers(self):
        recommendation = generate_recommendation(
            route={"name": "Long ridge", "expected_duration_min": 330},
            forecast={
                "high_route_temp_min": 6,
                "high_route_temp_max": 9,
                "rain_prob": 0.9,
                "rain_amount_mm": 6,
                "rain_duration_hours": 3,
                "wind_speed_mph": 28,
            },
            gear_items=current_inventory(),
            exposure="exposed",
        )

        result = buckets(recommendation)
        self.assertEqual(result["Mountain Equipment Echo"], "wear")
        self.assertEqual(result["Mountain Equipment Comici Trousers"], "wear")
        self.assertEqual(result["Keela Saxon"], "pack")
        self.assertEqual(result["Keela Lightning Pro Overtrousers"], "pack")
        self.assertEqual(result["Topo Mountain Racer 4"], "wear")
        self.assertEqual(result["Waterproof Socks"], "pack")

    def test_cold_wet_conditions_displace_topo_with_protective_boot(self):
        recommendation = generate_recommendation(
            route={"name": "Winter route", "expected_duration_min": 300},
            forecast={
                "high_route_temp_min": 2,
                "high_route_temp_max": 5,
                "rain_prob": 0.9,
                "rain_amount_mm": 8,
                "rain_duration_hours": 3,
                "wind_speed_mph": 30,
            },
            gear_items=current_inventory(),
            exposure="exposed",
        )

        result = buckets(recommendation)
        self.assertEqual(result["Scarpa Terra GTX"], "wear")
        self.assertEqual(result["Topo Mountain Racer 4"], "leave_home")
        self.assertEqual(result["Mountain Equipment Ibex Trousers"], "wear")
        self.assertEqual(result["Keela Saxon"], "pack")
        self.assertTrue(any("insulation" in warning for warning in recommendation.warnings))

    def test_missing_forecast_is_low_confidence_without_fabricated_conditions(self):
        recommendation = generate_recommendation(
            route={"name": "Unknown day", "expected_duration_min": 180},
            forecast={},
            gear_items=current_inventory(),
            exposure="mixed",
        )

        self.assertEqual(recommendation.confidence, "low")
        self.assertEqual(recommendation.conditions["temperature"], "Unknown")
        self.assertEqual(recommendation.conditions["wetting_load"], "unknown")
        self.assertTrue(any("No forecast snapshot" in warning for warning in recommendation.warnings))
        self.assertEqual(len(recommendation.items), len(current_inventory()))
        self.assertTrue(all(item.reason for item in recommendation.items))
        self.assertEqual(recommendation.policy_version, POLICY.version)

    def test_non_owned_items_are_not_recommended(self):
        inventory = current_inventory()
        inventory.append(GearItem(name="Shop-only jacket", category="Jacket", owned=False, status=[]))

        recommendation = generate_recommendation(
            route={"name": "Test", "expected_duration_min": 120},
            forecast={"high_route_temp_min": 12, "rain_amount_mm": 0, "rain_prob": 0.1},
            gear_items=inventory,
            exposure="sheltered",
        )

        self.assertNotIn("Shop-only jacket", buckets(recommendation))

    def test_severe_wind_warns_without_suppressing_loadout(self):
        recommendation = generate_recommendation(
            route={"name": "Exposed ridge", "expected_duration_min": 240},
            forecast={
                "high_route_temp_min": 7,
                "high_route_temp_max": 10,
                "rain_prob": 0.2,
                "rain_amount_mm": 0,
                "wind_speed_mph": 48,
            },
            gear_items=current_inventory(),
            exposure="exposed",
        )

        self.assertTrue(any("does not make an exposed route safe" in warning for warning in recommendation.warnings))
        self.assertEqual(len(recommendation.items), 10)


if __name__ == "__main__":
    unittest.main()
