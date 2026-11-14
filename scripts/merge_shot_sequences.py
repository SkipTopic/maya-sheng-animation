#!/usr/bin/env python3
"""Merge per-shot playblast PNGs into a continuous numeric frame sequence."""

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sys
from validate_shotlist import parse_fps, validate_file, write_report


def numeric_suffix(path):
    match = re.search(r"\.(\d+)\.png$", os.path.basename(path), flags=re.IGNORECASE)
    if not match:
        raise ValueError("Non-numeric shot frame name: %s" % path)
    return int(match.group(1))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def merge_shot_sequences(shotlist, raw_dir, output_dir, fps=24.0,
                         overwrite=False, report_path=None):
    shot_report = validate_file(shotlist, fps=fps)
    report = {"valid": False, "shotlist": shotlist, "raw_dir": raw_dir,
              "output_dir": output_dir, "errors": [], "shots": []}
    if not shot_report["valid"]:
        report["errors"].extend(shot_report["errors"])
        write_report(report, report_path)
        return report

    plan = []
    with open(shotlist, "r", encoding="utf-8-sig", newline="") as fh:
        import csv
        rows = list(csv.DictReader(fh))
    for row in rows:
        shot_id = row["shot_id"]
        start = int(row["start_frame"])
        end = int(row["end_frame"])
        paths = glob.glob(os.path.join(raw_dir, shot_id + ".*.png"))
        paths = [path for path in paths if os.path.isfile(path)]
        frame_numbers = []
        for path in paths:
            try:
                frame_numbers.append(numeric_suffix(path))
            except ValueError as exc:
                report["errors"].append(str(exc))
        ordered = [path for _frame, path in sorted(zip(frame_numbers, paths))]
        frame_numbers = sorted(frame_numbers)
        expected = set(range(start, end + 1))
        if len(paths) != len(expected) or set(frame_numbers) != expected:
            report["errors"].append("%s raw frame count/set mismatch: count=%s expected=%s" % (shot_id, len(paths), len(expected)))
            continue
        for path, frame in zip(ordered, frame_numbers):
            target = os.path.join(output_dir, "%04d.png" % frame)
            plan.append({"shot_id": shot_id, "frame": frame, "source": path, "target": target})
        report["shots"].append({"shot_id": shot_id, "start": start, "end": end, "frames": len(paths)})

    if not overwrite:
        existing = [item["target"] for item in plan if os.path.exists(item["target"])]
        if existing:
            report["errors"].append("Refusing to overwrite %s existing output files; use a new directory" % len(existing))
    if report["errors"]:
        write_report(report, report_path)
        return report

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    for item in plan:
        shutil.copy2(item["source"], item["target"])
        if sha256(item["source"]) != sha256(item["target"]):
            raise RuntimeError("Copied frame hash mismatch: %s" % item["target"])
    report["frames_written"] = len(plan)
    report["expected_frames"] = shot_report["total_frames"]
    report["valid"] = len(plan) == shot_report["total_frames"]
    if not report["valid"]:
        report["errors"].append("Written frame count does not match shotlist total")
    write_report(report, report_path)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shotlist", required=True)
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--fps", default="24")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite only planned target frames; prefer a new directory")
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    report = merge_shot_sequences(args.shotlist, args.raw_dir, args.output_dir,
                                  fps=parse_fps(args.fps), overwrite=args.overwrite,
                                  report_path=args.report)
    print(json.dumps({"valid": report["valid"], "frames_written": report.get("frames_written", 0),
                      "errors": report["errors"][:20], "report": args.report}, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
