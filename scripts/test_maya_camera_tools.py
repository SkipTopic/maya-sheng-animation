"""Temporary-camera smoke test for maya_camera_tools inside Maya.

The test never opens or saves a scene. It creates a temporary sphere and camera,
playblasts three frames, verifies count and image variation, then removes the nodes.
"""

import hashlib
import json
import os
import maya.cmds as cmds
from maya_camera_tools import create_shot_camera, keyframe_camera_move, playblast_shot


def _hash(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_test(output_path=None, frames_dir=None):
    camera = None
    sphere = None
    previous_time = cmds.currentTime(q=True)
    report = {"ok": False}
    try:
        before_helpers = set(cmds.ls("TMP_SHENG_CAMERA_AIM*", long=True) or [])
        sphere = cmds.polySphere(name="TMP_SHENG_TEST_SPHERE", radius=8.0)[0]
        camera = create_shot_camera(
            name="TMP_SHENG_TEST_CAMERA",
            eye=[100.0, 55.0, 100.0],
            aim=[0.0, 0.0, 0.0],
            focal_length=50.0,
        )
        move = keyframe_camera_move(
            camera,
            1,
            3,
            eye_start=[100.0, 55.0, 100.0],
            aim_start=[0.0, 0.0, 0.0],
            eye_end=[112.0, 62.0, 108.0],
            aim_end=[0.0, 0.0, 0.0],
        )
        if frames_dir is None:
            frames_dir = os.path.join(os.path.expanduser("~"), "maya_sheng_camera_test_frames")
        output_base = os.path.join(frames_dir, "S001")
        shot = playblast_shot(camera, 1, 3, output_base, width=427, height=240, overwrite=True)
        hashes = [_hash(path) for path in shot["files"]]
        report.update({
            "camera": camera,
            "move": move,
            "shot": shot,
            "image_hashes": hashes,
            "temporary_aim_helpers_left": sorted(set(cmds.ls("TMP_SHENG_CAMERA_AIM*", long=True) or []) - before_helpers),
        })
        report["ok"] = bool(
            shot["actual_frames"] == 3 and
            len(set(hashes)) == 3 and
            move["eye_motion_distance"] > 0 and
            not report["temporary_aim_helpers_left"]
        )
        if not report["ok"]:
            raise RuntimeError("Camera smoke test failed: %s" % report)
    except Exception as exc:
        report["error_message"] = repr(exc)
    finally:
        curves = []
        if camera and cmds.objExists(camera):
            curves = cmds.listConnections(camera, type="animCurve", s=True, d=False) or []
        if camera and cmds.objExists(camera):
            cmds.delete(camera)
        if sphere and cmds.objExists(sphere):
            cmds.delete(sphere)
        for curve in set(curves):
            if cmds.objExists(curve):
                try:
                    cmds.delete(curve)
                except Exception:
                    pass
        cmds.currentTime(previous_time)
        cmds.select(clear=True)
        cmds.refresh(force=True)

    if output_path:
        parent = os.path.dirname(output_path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
    return report


if __name__ == "__maya_cmd__":
    run_test()
