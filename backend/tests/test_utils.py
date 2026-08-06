import unittest

from backend.app.core.utils import (
    estimate_tokens,
    extract_json_from_llm,
    normalize_text,
    truncate_text,
    validate_mcq_structure,
)


class UtilityTests(unittest.TestCase):
    def test_extracts_json_from_markdown(self):
        payload = extract_json_from_llm('```json\n{"question": "Why?"}\n```')
        self.assertEqual(payload, {"question": "Why?"})

    def test_normalizes_supported_values(self):
        self.assertEqual(normalize_text(None), "")
        self.assertEqual(normalize_text(["cell", "biology"]), "cell biology")
        self.assertEqual(normalize_text("  physics  "), "physics")

    def test_validates_mcq_shape(self):
        mcq = {
            "question": "Which option is correct?",
            "options": {"A": "One", "B": "Two", "C": "Three", "D": "Four"},
            "correct": "B",
        }
        self.assertTrue(validate_mcq_structure(mcq))
        self.assertFalse(validate_mcq_structure({**mcq, "correct": "E"}))

    def test_text_helpers(self):
        self.assertEqual(estimate_tokens("one two three four"), 5)
        self.assertEqual(truncate_text("abcdefgh", 6), "abc...")


if __name__ == "__main__":
    unittest.main()
