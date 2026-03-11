import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import generate_transits


class GenerateTransitsReliabilityTests(unittest.TestCase):
    def test_is_valid_number_rejects_nan(self):
        self.assertTrue(generate_transits._is_valid_number(12.3))
        self.assertFalse(generate_transits._is_valid_number(float("nan")))

    @patch("scripts.generate_transits.resolve_body", side_effect=RuntimeError("boom"))
    def test_main_writes_fallback_payload_on_failure(self, _mock_resolve):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "current_week.json"
            generate_transits.main(output_path=out_path)

            self.assertTrue(out_path.exists())
            payload = json.loads(out_path.read_text())
            self.assertTrue(generate_transits._is_valid_output_payload(payload))
            self.assertIn("generation_warning", payload)


if __name__ == "__main__":
    unittest.main()
