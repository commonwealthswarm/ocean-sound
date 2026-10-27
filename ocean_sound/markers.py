"""Listening markers: the record behind each marker on a listening page.

A marker keeps what was heard (observation) and what was measured (measurement) apart from any meaning hypothesis,
which may only live in its own optional field. Translation-style fields are refused outright. Corrections never
overwrite: each one appends the previous revision to the marker's history.
"""

import copy
import math
import re

REVIEW_STATUSES = ("unreviewed", "accepted", "changes_requested", "rejected")
MARKER_FIELDS = (
    "audio", "start_s", "end_s", "observation", "measurement", "review_status", "evidence", "contributor",
    "hypothesis", "history",
)
AUDIO_FIELDS = ("source_id", "sha256")
MEASUREMENT_FIELDS = ("quantity", "value", "unit", "method")
MAX_OBSERVATION_CHARS = 280
# Field names that would carry a meaning claim outside the separate hypothesis field.
FORBIDDEN_FIELD = re.compile(r"translat|meaning|gloss|decod|decipher|interpret|semantic", re.IGNORECASE)
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class MarkerError(ValueError):
    """The marker record is invalid."""


def _check_fields(mapping, allowed, where):
    if not isinstance(mapping, dict):
        raise MarkerError("%s must be an object" % where)
    for key in mapping:
        if FORBIDDEN_FIELD.search(str(key)):
            raise MarkerError("%s: field %r is not allowed; a meaning hypothesis belongs only in 'hypothesis'"
                              % (where, key))
        if key not in allowed:
            raise MarkerError("%s: unknown field %r" % (where, key))


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise MarkerError("%s must be a finite number" % name)
    return value


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise MarkerError("%s is required and must be non-empty text" % name)
    return value


def validate_marker(marker, duration_s):
    """Raise MarkerError unless marker is a valid record for audio of duration_s seconds. Returns marker."""
    _number(duration_s, "duration_s")
    if duration_s <= 0:
        raise MarkerError("duration_s must be positive")
    _check_fields(marker, MARKER_FIELDS, "marker")
    for key in MARKER_FIELDS:
        if key not in marker and key not in ("hypothesis", "history"):
            raise MarkerError("marker: missing field %r" % key)

    audio = marker["audio"]
    _check_fields(audio, AUDIO_FIELDS, "audio")
    _text(audio.get("source_id"), "audio.source_id")
    if not isinstance(audio.get("sha256"), str) or not SHA256.match(audio["sha256"]):
        raise MarkerError("audio.sha256 must be 64 lowercase hex characters")

    start = _number(marker["start_s"], "start_s")
    end = _number(marker["end_s"], "end_s")
    if start < 0 or end > duration_s:
        raise MarkerError("marker [%s, %s] lies outside the audio duration %s" % (start, end, duration_s))
    if end <= start:
        raise MarkerError("end_s must be greater than start_s")

    observation = _text(marker["observation"], "observation")
    if len(observation) > MAX_OBSERVATION_CHARS:
        raise MarkerError("observation must be at most %d characters" % MAX_OBSERVATION_CHARS)

    measurement = marker["measurement"]
    _check_fields(measurement, MEASUREMENT_FIELDS, "measurement")
    _text(measurement.get("quantity"), "measurement.quantity")
    _number(measurement.get("value"), "measurement.value")
    _text(measurement.get("unit"), "measurement.unit")
    _text(measurement.get("method"), "measurement.method")

    if marker["review_status"] not in REVIEW_STATUSES:
        raise MarkerError("review_status must be one of %s" % ", ".join(REVIEW_STATUSES))
    evidence = marker["evidence"]
    if not isinstance(evidence, list):
        raise MarkerError("evidence must be a list of references")
    for ref in evidence:
        _text(ref, "evidence reference")
    _text(marker["contributor"], "contributor")

    hypothesis = marker.get("hypothesis")
    if hypothesis is not None:
        _text(hypothesis, "hypothesis")
    if not isinstance(marker.get("history", []), list):
        raise MarkerError("history must be a list")
    return marker


def make_marker(*, source_id, sha256, start_s, end_s, observation, quantity, value, unit, method, contributor,
                duration_s, evidence=(), review_status="unreviewed", hypothesis=None):
    """Build and validate a new marker. The hypothesis, if any, stays in its own field."""
    marker = {
        "audio": {"source_id": source_id, "sha256": sha256},
        "start_s": start_s,
        "end_s": end_s,
        "observation": observation,
        "measurement": {"quantity": quantity, "value": value, "unit": unit, "method": method},
        "review_status": review_status,
        "evidence": list(evidence),
        "contributor": contributor,
        "hypothesis": hypothesis,
        "history": [],
    }
    return validate_marker(marker, duration_s)


def correct_marker(marker, changes, *, duration_s, corrected_by, note):
    """Return a corrected copy of marker. The previous revision is appended to history; nothing is overwritten."""
    _text(corrected_by, "corrected_by")
    _text(note, "note")
    if not isinstance(changes, dict) or not changes:
        raise MarkerError("changes must be a non-empty object")
    if "history" in changes:
        raise MarkerError("history cannot be edited directly")
    _check_fields(changes, MARKER_FIELDS, "changes")
    previous = copy.deepcopy(marker)
    history = previous.pop("history", [])
    corrected = copy.deepcopy(previous)
    corrected.update(copy.deepcopy(changes))
    corrected["history"] = history + [{
        "revision": len(history) + 1,
        "previous": previous,
        "corrected_by": corrected_by,
        "note": note,
    }]
    return validate_marker(corrected, duration_s)


def marker_sort_key(marker):
    return (
        marker["start_s"], marker["end_s"], marker["audio"]["source_id"], marker["contributor"],
        marker["measurement"]["quantity"], marker["observation"],
    )


def sort_markers(markers):
    """Deterministic order: by time, then source, contributor, quantity and observation."""
    return sorted(markers, key=marker_sort_key)
