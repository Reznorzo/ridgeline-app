import unittest

from app.models import GearItem
from app.services.recommend import generate_recommendation


class RecommendationTest(unittest.TestCase):
    def test_recommendation_output_shape(self):
        gear = [
            GearItem(name="Topo Mountain Racer 4"),
            GearItem(name="Waterproof Socks"),
            GearItem(name="Keela Saxon"),
        ]

        recommendation = generate_recommendation(
            route={"name": "Test route"},
            forecast={
                "valley_temp_min": 11,
                "valley_temp_max": 15,
                "high_route_temp_min": 5,
                "high_route_temp_max": 8,
                "rain_prob": 0.4,
                "wind_speed_mph": 24,
            },
            gear_items=gear,
        )

        buckets_by_name = {item.gear_item.name: item.bucket for item in recommendation.items}

        self.assertEqual(recommendation.confidence, "medium")
        self.assertIn("high_route_temp", recommendation.conditions)
        self.assertEqual(buckets_by_name["Topo Mountain Racer 4"], "wear")
        self.assertEqual(buckets_by_name["Waterproof Socks"], "pack")
        self.assertEqual(buckets_by_name["Keela Saxon"], "pack")


if __name__ == "__main__":
    unittest.main()
