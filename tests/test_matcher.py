import unittest
from app.matcher import ProductMatcher

class TestProductMatcher(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            {"id": 1, "name": "Aashirvaad Shudh Chakki Atta 5kg", "gtin": "8901234567890"},
            {"id": 2, "name": "Maggi 2-Minute Noodles 70g", "gtin": "8901058000000"},
            {"id": 3, "name": "Tata Salt Vacuum Evaporated 1kg", "gtin": "8901030000000"},
            {"id": 4, "name": "Amul Taaza Milk 500ml", "gtin": "8901262000000"}
        ]
        self.matcher = ProductMatcher(self.catalog)

    def test_exact_gtin_match(self):
        res = self.matcher.match("Unknown Name", query_gtin="8901058000000")
        self.assertEqual(res["status"], "MATCHED")
        self.assertEqual(res["match"]["id"], 2)

    def test_normalization(self):
        # Test unit normalization
        self.assertEqual(self.matcher._normalize_text("Aashirvaad Atta 5 kg"), "aashirvaad atta 5000g")
        self.assertEqual(self.matcher._normalize_text("Aashirvaad Shudh Chakki Atta 5kg"), "aashirvaad shudh chakki atta 5000g")
        self.assertEqual(self.matcher._normalize_text("Maggi 2-Min 70g"), "maggi 2 min 70g")
        self.assertEqual(self.matcher._normalize_text("Amul Taaza 0.5L"), "amul taaza 500ml")

    def test_fuzzy_match_high_confidence(self):
        # Slight variation, should confidently match ID 1
        res = self.matcher.match("Ashirwad Shudh Chakki Atta 5kg")
        self.assertEqual(res["status"], "MATCHED")
        self.assertEqual(res["match"]["id"], 1)

    def test_fuzzy_match_suggestions(self):
        # More distant variation, should return suggestions
        res = self.matcher.match("Magi Masala Noodles")
        self.assertEqual(res["status"], "SUGGESTIONS")
        self.assertTrue(any(s["id"] == 2 for s in res["suggestions"]))

    def test_unmatched(self):
        # Completely unrelated
        res = self.matcher.match("Patanjali Dant Kanti 100g")
        self.assertEqual(res["status"], "UNMATCHED")

if __name__ == "__main__":
    unittest.main()
