"""Checks the documentary MBARI excerpt record. It describes a source; it is not the source and not a finding."""

import json
import os
import unittest

from ocean_sound.provenance import validate_source_record

RECORD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sources", "mbari-excerpt.json")


def load_record():
    with open(RECORD_PATH, encoding="utf-8") as f:
        return json.load(f)


class MbariSourceRecordTests(unittest.TestCase):
    def setUp(self):
        self.rec = load_record()

    def test_record_is_valid(self):
        self.assertEqual(validate_source_record(self.rec), [])

    def test_status_is_unverified(self):
        self.assertEqual(self.rec["status"], "unverified")

    def test_no_sha256(self):
        self.assertNotIn("sha256", self.rec)

    def test_attribution_mentions_mbari_and_licence(self):
        self.assertIn("MBARI", self.rec["attribution"])
        self.assertIn("CC-BY 4.0", self.rec["attribution"])
        self.assertEqual(self.rec["license"], "CC-BY 4.0")
        self.assertEqual(self.rec["redistribution"], "attribution-required")

    def test_limits_present(self):
        limits = self.rec["limits"]
        self.assertIsInstance(limits, list)
        text = " ".join(limits).lower()
        for phrase in ("sample of one", "no population claim", "no call meaning claim"):
            self.assertIn(phrase, text)

    def test_not_original_source_and_not_a_discovery(self):
        self.assertFalse(self.rec["format"]["is_original_source"])
        self.assertEqual(self.rec["format"]["sample_rate_hz"], 16000)
        self.assertEqual(self.rec["format"]["bits_per_sample"], 24)
        self.assertEqual(self.rec["format"]["channels"], 1)
        self.assertFalse(self.rec["night_shift_discovery"])
        self.assertIn("NOT the original 256 kHz source", self.rec["description"])

    def test_not_publishable_and_file_not_in_repo(self):
        self.assertFalse(self.rec["publishable"])
        repo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        self.assertFalse(os.path.exists(os.path.join(repo, "data", "sources", self.rec["file_name"])))


if __name__ == "__main__":
    unittest.main()
