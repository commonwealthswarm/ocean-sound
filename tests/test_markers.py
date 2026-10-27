"""Tests for ocean_sound.markers. Every fixture is SYNTHETIC and invented; nothing here is a finding."""

import copy
import unittest

from ocean_sound.markers import MarkerError, correct_marker, make_marker, sort_markers, validate_marker

SYNTHETIC_SHA = "0" * 63 + "1"
DURATION = 55.0


def synthetic_marker(**overrides):
    args = dict(
        source_id="synthetic-tone-source",
        sha256=SYNTHETIC_SHA,
        start_s=1.0,
        end_s=2.5,
        observation="SYNTHETIC: rising tone",
        quantity="peak_frequency",
        value=440.0,
        unit="Hz",
        method="SYNTHETIC test fixture: stdlib STFT peak bin",
        contributor="synthetic-agent",
        duration_s=DURATION,
        evidence=["synthetic-evidence-1"],
    )
    args.update(overrides)
    return make_marker(**args)


class MarkerTests(unittest.TestCase):
    def test_valid_marker_built(self):
        m = synthetic_marker()
        self.assertEqual(m["review_status"], "unreviewed")
        self.assertEqual(m["history"], [])
        self.assertIsNone(m["hypothesis"])

    def test_marker_past_duration_rejected(self):
        with self.assertRaises(MarkerError):
            synthetic_marker(start_s=54.0, end_s=56.0)

    def test_marker_negative_start_rejected(self):
        with self.assertRaises(MarkerError):
            synthetic_marker(start_s=-0.5, end_s=1.0)

    def test_end_must_follow_start(self):
        with self.assertRaises(MarkerError):
            synthetic_marker(start_s=3.0, end_s=3.0)

    def test_observation_required(self):
        for bad in ("", "   ", None):
            with self.assertRaises(MarkerError):
                synthetic_marker(observation=bad)

    def test_measurement_requires_unit(self):
        with self.assertRaises(MarkerError):
            synthetic_marker(unit="")

    def test_measurement_requires_method(self):
        with self.assertRaises(MarkerError):
            synthetic_marker(method=None)

    def test_measurement_value_must_be_number(self):
        with self.assertRaises(MarkerError):
            synthetic_marker(value="loud")
        with self.assertRaises(MarkerError):
            synthetic_marker(value=True)

    def test_hypothesis_stays_separate(self):
        m = synthetic_marker(hypothesis="SYNTHETIC hypothesis: contact call")
        self.assertEqual(m["observation"], "SYNTHETIC: rising tone")
        self.assertEqual(m["hypothesis"], "SYNTHETIC hypothesis: contact call")
        self.assertNotIn("contact call", m["observation"])
        self.assertNotIn("hypothesis", m["measurement"])

    def test_translation_style_fields_rejected(self):
        for field in ("translation", "meaning_text", "Meaning", "gloss", "decoded_message", "interpretation"):
            m = synthetic_marker()
            m[field] = "SYNTHETIC"
            with self.assertRaises(MarkerError, msg=field):
                validate_marker(m, DURATION)

    def test_translation_field_nested_in_measurement_rejected(self):
        m = synthetic_marker()
        m["measurement"]["translation"] = "SYNTHETIC"
        with self.assertRaises(MarkerError):
            validate_marker(m, DURATION)

    def test_unknown_field_rejected(self):
        m = synthetic_marker()
        m["note"] = "SYNTHETIC"
        with self.assertRaises(MarkerError):
            validate_marker(m, DURATION)

    def test_bad_review_status_rejected(self):
        with self.assertRaises(MarkerError):
            synthetic_marker(review_status="confirmed")

    def test_bad_sha256_rejected(self):
        with self.assertRaises(MarkerError):
            synthetic_marker(sha256="abc")

    def test_correction_appends_history_and_preserves_original(self):
        original = synthetic_marker()
        snapshot = copy.deepcopy(original)
        fixed = correct_marker(original, {"end_s": 3.0}, duration_s=DURATION,
                               corrected_by="synthetic-reviewer", note="SYNTHETIC: end time fixed")
        self.assertEqual(original, snapshot)
        self.assertEqual(fixed["end_s"], 3.0)
        self.assertEqual(len(fixed["history"]), 1)
        entry = fixed["history"][0]
        self.assertEqual(entry["revision"], 1)
        self.assertEqual(entry["previous"]["end_s"], 2.5)
        self.assertEqual(entry["corrected_by"], "synthetic-reviewer")
        again = correct_marker(fixed, {"review_status": "accepted"}, duration_s=DURATION,
                               corrected_by="synthetic-reviewer", note="SYNTHETIC: accepted")
        self.assertEqual([h["revision"] for h in again["history"]], [1, 2])
        self.assertEqual(again["history"][0], entry)
        self.assertEqual(again["history"][1]["previous"]["end_s"], 3.0)

    def test_correction_cannot_edit_history_or_add_translation(self):
        m = synthetic_marker()
        with self.assertRaises(MarkerError):
            correct_marker(m, {"history": []}, duration_s=DURATION, corrected_by="x", note="SYNTHETIC")
        with self.assertRaises(MarkerError):
            correct_marker(m, {"translation": "SYNTHETIC"}, duration_s=DURATION, corrected_by="x", note="SYNTHETIC")

    def test_invalid_correction_rejected(self):
        m = synthetic_marker()
        with self.assertRaises(MarkerError):
            correct_marker(m, {"end_s": 99.0}, duration_s=DURATION, corrected_by="x", note="SYNTHETIC")

    def test_ordering_is_deterministic(self):
        a = synthetic_marker(start_s=5.0, end_s=6.0)
        b = synthetic_marker(start_s=1.0, end_s=2.0, contributor="synthetic-b")
        c = synthetic_marker(start_s=1.0, end_s=2.0, contributor="synthetic-a")
        d = synthetic_marker(start_s=1.0, end_s=1.5)
        expected = [d, c, b, a]
        self.assertEqual(sort_markers([a, b, c, d]), expected)
        self.assertEqual(sort_markers([d, a, c, b]), expected)
        self.assertEqual(sort_markers(reversed(expected)), expected)


if __name__ == "__main__":
    unittest.main()
