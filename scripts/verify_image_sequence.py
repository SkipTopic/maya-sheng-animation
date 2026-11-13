#!/usr/bin/env python3
"""Verify a continuous PNG animation sequence against a shotlist CSV."""

import argparse
import hashlib
import json
import os
import re
import struct
import sys
from validate_shotlist import parse_fps, validate_file, write_report


def png_size(path):
    with open(path, "rb") as fh:
        header = fh.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("Not a valid PNG header")
    return struct.unpack(">II", header[16:24])


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_sequence(frames_dir, shotlist, fps=24.0, width=None, height=None):
    shot_report = validate_file(shotlist, fps=fps)
    report = {
        "frames_dir": frames_dir,
        "shotlist": shotlist,
        "valid": False,
        "errors": list(shot_report["errors"]),
        "warnings": list(shot_report["warnings"]),
        "shotlist_shots": shot_report.get("shots", 0),
        "expected_frames": shot_report.get("total_frames"),
    }
    if not shot_report["valid"]:
        return report

    files_by_frame = {}
    hashes = {}
    sizes = {}
    if not os.path.isdir(frames_dir):
        report["errors"].append("Frames directory does not exist")
        return report
    for name in os.listdir(frames_dir):
        if not name.lower().endswith(".png"):
            continue
        path = os.path.join(frames_dir, name)
        if not os.path.isfile(path):
            continue
        match = re.fullmatch(r"(\d+)\.png", name, flags=re.IGNORECASE)
        if not match:
            report["errors"].append("Non-numeric PNG frame name: %s" % name)
            continue
        frame = int(match.group(1))
        if frame in files_by_frame:
            report["errors"].append("Duplicate numeric frame %s: %s and %s" % (frame, files_by_frame[frame], name))
            continue
        files_by_frame[frame] = path
        hashes[frame] = file_sha256(path)
        try:
            sizes[frame] = png_size(path)
        except Exception as exc:
            report["errors"].append("Invalid PNG %s: %s" % (name, exc))

    total = shot_report["total_frames"]
    expected = set(range(1, total + 1))
    actual = set(files_by_frame)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        report["errors"].append("Missing frames: %s" % missing[:100])
    if unexpected:
        report["errors"].append("Unexpected frames: %s" % unexpected[:100])

    if width is not None or height is not None:
        for frame, size in sizes.items():
            if width is not None and size[0] != width:
                report["errors"].append("Frame %s width %s != %s" % (frame, size[0], width))
            if height is not None and size[1] != height:
                report["errors"].append("Frame %s height %s != %s" % (frame, size[1], height))

    duplicate_groups = {}
    for frame, digest in hashes.items():
        duplicate_groups.setdefault(digest, []).append(frame)
    duplicates = [sorted(frames) for frames in duplicate_groups.values() if len(frames) > 1]
    unique_hashes = len(duplicate_groups)
    if total > 1 and actual == expected and unique_hashes == 1:
        report["errors"].append("Every frame is identical; inspect camera activation and animation")

    per_shot = []
    with open(shotlist, "r", encoding="utf-8-sig", newline="") as fh:
        import csv
        for row in csv.DictReader(fh):
            start = int(row["start_frame"])
            end = int(row["end_frame"])
            present = sum(1 for frame in range(start, end + 1) if frame in files_by_frame)
            per_shot.append({
                "shot_id": row["shot_id"],
                "start": start,
                "end": end,
                "expected": end - start + 1,
                "present": present,
            })
            if present != end - start + 1:
                report["errors"].append("%s has %s frames, expected %s" % (row["shot_id"], present, end - start + 1))

    report.update({
        "actual_frames": len(files_by_frame),
        "missing_frames": missing,
        "unexpected_frames": unexpected,
        "unique_frame_hashes": unique_hashes,
        "duplicate_frame_groups": duplicates,
        "per_shot": per_shot,
        "png_sizes": {str(frame): list(size) for frame, size in sorted(sizes.items())},
        "note": "Duplicate frames may be valid in static shots; review duplicate groups and shot boundaries visually.",
    })
    report["valid"] = not report["errors"]
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames_dir")
    parser.add_argument("--shotlist", required=True)
    parser.add_argument("--fps", default="24")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    report = verify_sequence(args.frames_dir, args.shotlist, fps=parse_fps(args.fps), width=args.width, height=args.height)
    write_report(report, args.report)
    summary = {key: report.get(key) for key in ("valid", "expected_frames", "actual_frames", "unique_frame_hashes")}
    summary["errors"] = report["errors"][:20]
    summary["warnings_count"] = len(report["warnings"])
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
