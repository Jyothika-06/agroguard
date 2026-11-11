import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fusion.uncertainty import assess_uncertainty

class TestUncertainty(unittest.TestCase):
    def setUp(self):
        self.classes = ["Tomato___healthy", "Tomato___Early_blight", "Tomato___Late_blight"]

    def test_high_confidence(self):
        # 90% top1, 5% top2 -> confident
        probs = [0.90, 0.05, 0.05]
        res = assess_uncertainty(probs, self.classes, conf_threshold=60.0, margin_threshold=15.0)
        self.assertEqual(res["status"], "confident")
        self.assertEqual(res["top1"], "Tomato___healthy")
        self.assertAlmostEqual(res["confidence"], 90.0)
        self.assertAlmostEqual(res["margin"], 85.0)

    def test_low_confidence(self):
        # 50% top1 (below 60.0%) -> uncertain
        probs = [0.50, 0.25, 0.25]
        res = assess_uncertainty(probs, self.classes, conf_threshold=60.0, margin_threshold=15.0)
        self.assertEqual(res["status"], "uncertain")
        self.assertIn("below prototype threshold", res["reason"])

    def test_small_margin(self):
        # Normalized distribution (~54.17% vs 45.83%, margin ~8.33% < 15.0%) -> uncertain
        probs = [0.65, 0.55, 0.0]
        # Normalize sum for testing margin logic
        probs = [p / sum(probs) for p in probs]

        res = assess_uncertainty(probs, self.classes, conf_threshold=50.0, margin_threshold=15.0)
        self.assertEqual(res["status"], "uncertain")
        self.assertIn("margin", res["reason"])

if __name__ == "__main__":
    unittest.main()
