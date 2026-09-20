import unittest

from app.gpx import hash_gpx_content, parse_gpx


SIMPLE_GPX = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="ridgeline-test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Short test route</name>
    <trkseg>
      <trkpt lat="54.0000" lon="-2.0000"><ele>100</ele></trkpt>
      <trkpt lat="54.0010" lon="-2.0000"><ele>125</ele></trkpt>
      <trkpt lat="54.0020" lon="-2.0000"><ele>115</ele></trkpt>
    </trkseg>
  </trk>
</gpx>
"""


class GPXTest(unittest.TestCase):
    def test_parse_gpx_metrics(self):
        metrics = parse_gpx(SIMPLE_GPX)

        self.assertEqual(metrics["num_points"], 3)
        self.assertEqual(metrics["track_segments"], 1)
        self.assertGreater(metrics["distance_km"], 0)
        self.assertEqual(metrics["ascent_m"], 25)
        self.assertEqual(metrics["high_point_m"], 125)

    def test_hash_gpx_content_is_stable(self):
        self.assertEqual(hash_gpx_content(SIMPLE_GPX), hash_gpx_content(SIMPLE_GPX))


if __name__ == "__main__":
    unittest.main()
