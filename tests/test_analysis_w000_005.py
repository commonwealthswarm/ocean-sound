"""Runs scripts/analyses/w000-005.py on the values embedded in analyses/w000-005.json."""

import importlib.util
import os
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SCRIPT = os.path.join(ROOT, "scripts", "analyses", "w000-005.py")


def load_script():
    spec = importlib.util.spec_from_file_location("analysis_w000_005", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AnalysisW000005Tests(unittest.TestCase):
    def test_recomputed_results_match_recorded(self):
        computed, mismatches, extra = load_script().check()
        self.assertEqual(mismatches, {})
        self.assertEqual(extra, set())
        self.assertEqual(computed["n_windows"], 60)

    def test_dominant_frequency_single_value(self):
        computed, _, _ = load_script().check()
        self.assertEqual(computed["dominant_hz_distinct"], [15.625])


if __name__ == "__main__":
    unittest.main()
