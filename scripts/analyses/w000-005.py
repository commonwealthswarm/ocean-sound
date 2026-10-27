"""Recompute every result in analyses/w000-005.json from the verbatim server values embedded in it.

Standard library only; no network. Usage: python scripts/analyses/w000-005.py [path/to/w000-005.json]
Exits 1 if any recomputed result differs from the recorded one.
"""

import json
import os
import sys

DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "analyses", "w000-005.json")


def compute(doc):
    w = doc["verbatim"]["segment_windows"]
    overall = doc["verbatim"]["overall"]
    t0, rms, peak, dom, cen = w["t0"], w["rms_dbfs"], w["peak_dbfs"], w["dominant_hz"], w["centroid_hz"]
    n = len(t0)
    if not all(len(x) == n for x in (rms, peak, dom, cen)):
        raise ValueError("window arrays differ in length")
    i_peak = max(range(n), key=lambda i: peak[i])
    i_cmin = min(range(n), key=lambda i: cen[i])
    i_cmax = max(range(n), key=lambda i: cen[i])
    return {
        "n_windows": n,
        "rms_dbfs_min": min(rms),
        "rms_dbfs_max": max(rms),
        "rms_minus_overall_db_min": round(min(rms) - overall["rms_dbfs"], 1),
        "rms_minus_overall_db_max": round(max(rms) - overall["rms_dbfs"], 1),
        "peak_dbfs_min": min(peak),
        "peak_dbfs_max": peak[i_peak],
        "peak_dbfs_max_t0": t0[i_peak],
        "overall_peak_minus_segment_peak_max_db": round(overall["peak_dbfs"] - peak[i_peak], 1),
        "dominant_hz_distinct": sorted(set(dom)),
        "centroid_hz_min": cen[i_cmin],
        "centroid_hz_min_t0": t0[i_cmin],
        "centroid_hz_max": cen[i_cmax],
        "centroid_hz_max_t0": t0[i_cmax],
    }


def check(path=DEFAULT):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    computed = compute(doc)
    mismatches = {k: (doc["results"].get(k), v) for k, v in computed.items() if doc["results"].get(k) != v}
    extra = set(doc["results"]) - set(computed)
    return computed, mismatches, extra


def main(argv):
    computed, mismatches, extra = check(argv[1] if len(argv) > 1 else DEFAULT)
    print(json.dumps(computed, indent=2))
    if mismatches or extra:
        print("MISMATCH: %r; not recomputed: %r" % (mismatches, sorted(extra)), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
