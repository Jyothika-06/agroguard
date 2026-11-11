import os, sys, json, unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from model_utils import normalize_class_name
from config import CLASS_INDICES_PATH, TREATMENT_DB, FERTILIZER_DB, SUPPORTED_CROPS
from services import get_treatment, get_fertilizer


class TestClassNames(unittest.TestCase):
    def test_all_15_classes_normalize_and_resolve(self):
        with open(CLASS_INDICES_PATH) as f:
            raw_classes = json.load(f)
            
        self.assertEqual(len(raw_classes), 15, "Expected 15 classes in class_indices.json")
        
        for raw_name in raw_classes:
            norm_name = normalize_class_name(raw_name)
            
            # 1. Exact match in TREATMENT_DB
            self.assertIn(norm_name, TREATMENT_DB, f"Normalized class '{norm_name}' (from '{raw_name}') not found in TREATMENT_DB")
            
            # 2. Maps to a valid crop
            crop = None
            for c in SUPPORTED_CROPS:
                if norm_name.startswith(c) or raw_name.startswith(c):
                    crop = c
                    break
            self.assertIsNotNone(crop, f"Class '{raw_name}' does not map to any supported crop")
            
            # 3. Direct lookup in get_treatment returns TREATMENT_DB entry without fallback
            treatment = get_treatment(raw_name)
            self.assertEqual(treatment, TREATMENT_DB[norm_name], f"get_treatment('{raw_name}') did not return exact TREATMENT_DB entry")
            
            # 4. Fertilizer lookup returns valid entry
            fertilizer = get_fertilizer(crop, raw_name)
            self.assertIsNotNone(fertilizer, f"get_fertilizer('{crop}', '{raw_name}') returned None")
            self.assertIn("application", fertilizer, f"Fertilizer entry for '{crop}', '{raw_name}' missing application field")

if __name__ == "__main__":
    unittest.main()
