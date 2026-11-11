import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fusion.sensor_sim import get_preset_scenario, create_manual_reading
from fusion.sensor_validator import validate_sensor_readings
from fusion.risk_engine import evaluate_field_risk
from fusion.recommend import generate_field_recommendations

class TestRiskEngine(unittest.TestCase):
    def test_healthy_low_moisture_high_temp(self):
        # Healthy prediction + moisture 15.0% + temp 34.0°C -> water stress HIGH
        unc_res = {"status": "confident", "top1": "Tomato___healthy"}
        reading = create_manual_reading(soil_moisture=15.0, temperature=34.0, humidity=50.0, light=70.0)
        val_reading = validate_sensor_readings(reading)
        
        risk = evaluate_field_risk(unc_res, "Tomato___healthy", "Tomato", val_reading)
        self.assertEqual(risk["water_stress_risk"], "HIGH")
        self.assertEqual(risk["disease_status_used"], "Tomato___healthy")
        # Healthy prediction does NOT hide environmental risk
        self.assertIn("HIGH water stress risk", " ".join(risk["reasons"]))
        
        recs = generate_field_recommendations(risk, "en")
        self.assertTrue(any("Possible water stress" in r for r in recs))

    def test_disease_sustained_high_humidity(self):
        # Disease + humidity 88.0% -> disease spread risk HIGH
        unc_res = {"status": "confident", "top1": "Tomato___Early_blight"}
        reading = get_preset_scenario("humid_disease_favourable")
        val_reading = validate_sensor_readings(reading)
        
        risk = evaluate_field_risk(unc_res, "Tomato___Early_blight", "Tomato", val_reading)
        self.assertEqual(risk["disease_spread_risk"], "HIGH")
        self.assertEqual(risk["overall_risk"], "HIGH")
        self.assertIn("HIGH disease spread risk", " ".join(risk["reasons"]))

    def test_disease_adequate_moisture_no_irrigation_advice(self):
        # Disease + adequate moisture (45.0% > 20.0%) -> water stress LOW
        unc_res = {"status": "confident", "top1": "Tomato___Early_blight"}
        reading = get_preset_scenario("humid_disease_favourable") # moisture = 45.0%
        val_reading = validate_sensor_readings(reading)
        
        risk = evaluate_field_risk(unc_res, "Tomato___Early_blight", "Tomato", val_reading)
        self.assertEqual(risk["water_stress_risk"], "LOW")
        
        recs = generate_field_recommendations(risk, "en")
        self.assertTrue(any("Soil moisture is adequate" in r for r in recs))
        self.assertFalse(any("Possible water stress" in r for r in recs))

    def test_uncertain_image_assesses_environment(self):
        # Uncertain image status -> disease status UNKNOWN, but environment evaluated
        unc_res = {"status": "uncertain", "top1": "Tomato___Early_blight", "reason": "Low confidence"}
        reading = create_manual_reading(soil_moisture=15.0, temperature=34.0, humidity=88.0, light=50.0)
        val_reading = validate_sensor_readings(reading)
        
        risk = evaluate_field_risk(unc_res, "Tomato___Early_blight", "Tomato", val_reading)
        self.assertEqual(risk["disease_status_used"], "UNKNOWN")
        self.assertEqual(risk["water_stress_risk"], "HIGH")
        self.assertEqual(risk["disease_spread_risk"], "MODERATE")
        self.assertTrue(any("Uncertain model prediction" in u for u in risk["unknown_inputs"]))

    def test_missing_sensor_yields_unknown(self):
        # Missing moisture sensor -> water stress risk UNKNOWN
        unc_res = {"status": "confident", "top1": "Tomato___healthy"}
        reading = get_preset_scenario("missing_sensor")
        val_reading = validate_sensor_readings(reading)
        
        risk = evaluate_field_risk(unc_res, "Tomato___healthy", "Tomato", val_reading)
        self.assertEqual(risk["water_stress_risk"], "UNKNOWN")
        self.assertEqual(risk["disease_spread_risk"], "UNKNOWN")
        self.assertTrue(any("Soil Moisture" in u for u in risk["unknown_inputs"]))

    def test_healthy_image_never_suppresses_environmental_risk(self):
        # Visually healthy leaf + 88% humidity -> MODERATE environmental disease spread risk
        unc_res = {"status": "confident", "top1": "Tomato___healthy"}
        reading = create_manual_reading(soil_moisture=50.0, temperature=25.0, humidity=88.0, light=70.0)
        val_reading = validate_sensor_readings(reading)
        
        risk = evaluate_field_risk(unc_res, "Tomato___healthy", "Tomato", val_reading)
        self.assertEqual(risk["disease_spread_risk"], "MODERATE")
        self.assertIn("MODERATE environmental disease risk", " ".join(risk["reasons"]))

if __name__ == "__main__":
    unittest.main()
