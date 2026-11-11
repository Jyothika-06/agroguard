import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fusion.sensor_sim import get_preset_scenario
from fusion.sensor_validator import validate_sensor_readings

class TestSensorValidator(unittest.TestCase):
    def test_normal_scenario(self):
        reading = get_preset_scenario("normal")
        res = validate_sensor_readings(reading)
        self.assertFalse(res["has_missing_or_invalid"])
        for k, v in res["status"].items():
            self.assertEqual(v, "ok")
        self.assertEqual(res["clean_values"]["soil_moisture"], 50.0)

    def test_missing_sensor(self):
        reading = get_preset_scenario("missing_sensor")
        res = validate_sensor_readings(reading)
        self.assertTrue(res["has_missing_or_invalid"])
        self.assertEqual(res["status"]["soil_moisture"], "missing")
        self.assertEqual(res["status"]["humidity"], "missing")
        # Missing values must map to None (which evaluated to UNKNOWN in risk engine)
        self.assertIsNone(res["clean_values"]["soil_moisture"])
        self.assertIsNone(res["clean_values"]["humidity"])
        self.assertEqual(res["status"]["temperature"], "ok")

    def test_out_of_range(self):
        reading = get_preset_scenario("out_of_range")
        res = validate_sensor_readings(reading)
        self.assertTrue(res["has_missing_or_invalid"])
        self.assertEqual(res["status"]["soil_moisture"], "out_of_range")
        self.assertEqual(res["status"]["temperature"], "out_of_range")
        self.assertEqual(res["status"]["humidity"], "out_of_range")
        self.assertIsNone(res["clean_values"]["soil_moisture"])
        self.assertIsNone(res["clean_values"]["temperature"])
        self.assertIsNone(res["clean_values"]["humidity"])

if __name__ == "__main__":
    unittest.main()
