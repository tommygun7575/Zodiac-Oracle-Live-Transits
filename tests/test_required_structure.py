import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class RequiredStructureTests(unittest.TestCase):
    def test_required_file_structure_exists(self):
        required_files = [
            "scripts/__init__.py",
            "scripts/generate_transits.py",
            "scripts/bodies/__init__.py",
            "scripts/bodies/horizons_client.py",
            "scripts/bodies/miriade_client.py",
            "scripts/bodies/mpc_client.py",
            "docs/current_week.json",
        ]

        missing = [path for path in required_files if not (REPO_ROOT / path).exists()]
        self.assertEqual([], missing, f"Missing required file(s): {missing}")


if __name__ == "__main__":
    unittest.main()

