#!/usr/bin/env python3
"""Validate an animation shotlist CSV using only the Python standard library."""

import argparse
import csv
import json
import os
import sys

REQUIRED_COLUMNS = {
    "shot_id", "start_frame", "end_frame", "dur_frames",
    "shot_size", "action", "camera_move",
}


def parse_fps(value):
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        return float(numerator) / float(denominator)
    return float(text)


def write_report(report, path):
    if not path:
        return
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)


def validate_file(path, fps=24.0, expect_shots=None, expect_total=None):
    report = {"file": path, "valid": False, "errors": [], "warnings": [], "shots": 0}
    try:
        fps_value = parse_fps(fps)
        if fps_value <= 0:
            raise ValueError("fps must be positive")
    except Exception as exc:
        report["errors"].append("Invalid fps: %s" % exc)
        return report
    report["fps"] = fps_value

    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            columns = set(reader.fieldnames or [])
            missing_columns = sorted(REQUIRED_COLUMNS - columns)
            if missing_columns:
                report["errors"].append("Missing columns: %s" % missing_columns)
                return report
            rows = list(reader)
    except Exception as exc:
        report["errors"].append("Cannot read CSV: %s" % exc)
        return report

    if not rows:
        report["errors"].append("Shotlist has no shots")
        return report

    seen_ids = set()
    previous_end = None
    total_frames = 0
    first_start = None
    last_end = None
    for index, row in enumerate(rows, start=1):
        label = row.get("shot_id") or "row_%d" % index
        shot_id = (row.get("shot_id") or "").strip()
        if not shot_id:
            report["errors"].append("Row %d has empty shot_id" % index)
        elif shot_id in seen_ids:
            report["errors"].append("Duplicate shot_id: %s" % shot_id)
        seen_ids.add(shot_id)
        try:
            start = int(row["start_frame"])
            end = int(row["end_frame"])
            duration = int(row["dur_frames"])
        except Exception as exc:
            report["errors"].append("%s has invalid frame integers: %s" % (label, exc))
            continue
        if start < 1 or end < start:
            report["errors"].append("%s has invalid range %s-%s" % (label, start, end))
            continue
        expected_duration = end - start + 1
        if duration != expected_duration:
            report["errors"].append("%s dur_frames=%s, expected %s" % (label, duration, expected_duration))
        if previous_end is not None and start != previous_end + 1:
            report["errors"].append("%s starts at %s after previous end %s; gap or overlap" % (label, start, previous_end))
        if first_start is None:
            first_start = start
        previous_end = end
        last_end = end
        total_frames += expected_duration
        if not (row.get("shot_size") or "").strip():
            report["warnings"].append("%s has empty shot_size" % label)
        if not (row.get("action") or "").strip():
            report["warnings"].append("%s has empty action; verify intentional placeholder" % label)
        duration_text = (row.get("dur_sec") or "").strip()
        if duration_text:
            try:
                seconds = float(duration_text)
                expected_seconds = expected_duration / fps_value
                tolerance = max(0.011, 1.0 / fps_value)
                if abs(seconds - expected_seconds) > tolerance:
                    report["warnings"].append("%s dur_sec=%s, frame-derived=%.4f" % (label, seconds, expected_seconds))
            except ValueError:
                report["warnings"].append("%s has non-numeric dur_sec" % label)

    report.update({
        "shots": len(rows),
        "first_start": first_start,
        "last_end": last_end,
        "total_frames": total_frames,
        "duration_seconds": total_frames / fps_value,
    })
    if first_start is not None and first_start != 1:
        report["errors"].append("First shot starts at %s, expected 1" % first_start)
    if expect_shots is not None and len(rows) != expect_shots:
        report["errors"].append("Shot count %s != expected %s" % (len(rows), expect_shots))
    if expect_total is not None and total_frames != expect_total:
        report["errors"].append("Total frames %s != expected %s" % (total_frames, expect_total))
    report["valid"] = not report["errors"]
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shotlist")
    parser.add_argument("--fps", default="24")
    parser.add_argument("--expect-shots", type=int)
    parser.add_argument("--expect-total", type=int)
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    report = validate_file(args.shotlist, fps=args.fps, expect_shots=args.expect_shots, expect_total=args.expect_total)
    write_report(report, args.report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
