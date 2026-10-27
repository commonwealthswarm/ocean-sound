"""Recompute analyses/w005-010.json results from its embedded verbatim values.

Standard library only, no network. Exits 1 if any recomputed value differs.
Usage: python3 scripts/analyses/w005-010.py [path/to/w005-010.json]
"""
import json
import os
import statistics
import sys


def compute(data):
    overall = data["verbatim"]["overall"]
    rows = data["verbatim"]["segment_windows"]
    rms = [r[2] for r in rows]
    peak = [r[3] for r in rows]
    dom = [r[4] for r in rows]
    cen = [r[5] for r in rows]
    o_rms = overall["rms_dbfs"]
    med = statistics.median(rms)
    return {
        "n_windows": len(rows),
        "rms_dbfs_min": min(rms),
        "rms_dbfs_max": max(rms),
        "rms_dbfs_median": round(med, 3),
        "rms_dbfs_mean_of_db": round(statistics.fmean(rms), 3),
        "windows_rms_above_overall": sum(1 for v in rms if v > o_rms),
        "windows_rms_equal_overall": sum(1 for v in rms if v == o_rms),
        "windows_rms_below_overall": sum(1 for v in rms if v < o_rms),
        "rms_min_minus_overall_db": round(min(rms) - o_rms, 3),
        "rms_max_minus_overall_db": round(max(rms) - o_rms, 3),
        "rms_median_minus_overall_db": round(med - o_rms, 3),
        "peak_dbfs_min": min(peak),
        "peak_dbfs_max": max(peak),
        "peak_max_minus_overall_peak_db": round(max(peak) - overall["peak_dbfs"], 3),
        "dominant_hz_values": sorted(set(dom)),
        "centroid_hz_min": min(cen),
        "centroid_hz_max": max(cen),
        "centroid_hz_mean": round(statistics.fmean(cen), 3),
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "..", "..", "analyses", "w005-010.json")
    path = sys.argv[1] if len(sys.argv) > 1 else default
    with open(path) as f:
        data = json.load(f)
    got = compute(data)
    want = data["results"]
    bad = 0
    for key, value in got.items():
        expected = want.get(key)
        if isinstance(value, float) and isinstance(expected, (int, float)):
            ok = abs(value - expected) < 1e-6
        else:
            ok = value == expected
        print(f"{'ok ' if ok else 'BAD'} {key}: computed={value} stored={expected}")
        bad += 0 if ok else 1
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
