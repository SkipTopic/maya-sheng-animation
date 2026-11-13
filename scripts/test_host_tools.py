#!/usr/bin/env python3
"""Host-only smoke tests for shotlist and image-sequence validators."""

import json
import os
import struct
import tempfile
import zlib
from validate_shotlist import validate_file
from verify_image_sequence import verify_sequence


def write_png(path, width, height, rgb):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = bytearray()
    for _y in range(height):
        raw.append(0)
        raw.extend(bytes(rgb) * width)
    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    payload += chunk(b"IDAT", zlib.compress(bytes(raw)))
    payload += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(payload)


def run_test(output_path=None):
    with tempfile.TemporaryDirectory(prefix="maya_sheng_host_test_") as temp:
        shotlist = os.path.join(temp, "shotlist.csv")
        with open(shotlist, "w", encoding="utf-8", newline="") as fh:
            fh.write("shot_id,start_frame,end_frame,dur_frames,dur_sec,shot_size,action,camera_move\n")
            fh.write("S001,1,3,3,0.125,近景,test,static\n")
        shot_report = validate_file(shotlist, fps=24.0, expect_shots=1, expect_total=3)

        frames = os.path.join(temp, "frames")
        os.makedirs(frames)
        for frame, color in enumerate(((255, 0, 0), (0, 255, 0), (0, 0, 255)), start=1):
            write_png(os.path.join(frames, "%04d.png" % frame), 32, 24, color)
        sequence_report = verify_sequence(frames, shotlist, fps=24.0, width=32, height=24)

    report = {
        "ok": bool(shot_report["valid"] and sequence_report["valid"] and sequence_report["unique_frame_hashes"] == 3),
        "shotlist": shot_report,
        "sequence": sequence_report,
    }
    if output_path is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = os.path.join(root, "tests", "host_tools_test.json")
    parent = os.path.dirname(output_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"ok": report["ok"], "report": output_path}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    result = run_test()
    raise SystemExit(0 if result["ok"] else 1)
