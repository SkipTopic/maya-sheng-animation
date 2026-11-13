"""Maya camera creation, movement, activation and shot playblast helpers.

Functions never save or open scenes. Use a versioned work scene and new output dirs.
"""

import glob
import json
import math
import os
import re
import maya.cmds as cmds


def _look_rotation(camera, aim):
    locator = None
    constraint = None
    try:
        locator = cmds.spaceLocator(name="TMP_SHENG_CAMERA_AIM")[0]
        cmds.setAttr(locator + ".translate", *aim)
        constraint = cmds.aimConstraint(
            locator,
            camera,
            aimVector=(0.0, 0.0, -1.0),
            upVector=(0.0, 1.0, 0.0),
            worldUpType="vector",
            worldUpVector=(0.0, 1.0, 0.0),
        )[0]
        cmds.refresh(force=True)
        return list(cmds.xform(camera, q=True, ws=True, ro=True))
    finally:
        if constraint and cmds.objExists(constraint):
            cmds.delete(constraint)
        if locator and cmds.objExists(locator):
            cmds.delete(locator)
        cmds.refresh(force=True)


def create_shot_camera(name, eye, aim, focal_length=50.0, near_clip=5.0, far_clip=2200.0):
    """Create a perspective shot camera and return its actual Maya transform name."""
    camera = cmds.camera(name=name)[0]
    shape = cmds.listRelatives(camera, shapes=True, fullPath=True)[0]
    cmds.setAttr(shape + ".orthographic", False)
    cmds.setAttr(shape + ".focalLength", float(focal_length))
    cmds.setAttr(shape + ".nearClipPlane", float(near_clip))
    cmds.setAttr(shape + ".farClipPlane", float(far_clip))
    cmds.setAttr(shape + ".renderable", True)
    cmds.setAttr(camera + ".translate", *eye)
    rotation = _look_rotation(camera, aim)
    cmds.xform(camera, ws=True, ro=rotation)
    cmds.refresh(force=True)
    return camera


def keyframe_camera_move(camera, start, end, eye_start, aim_start, eye_end, aim_end,
                         replace_existing=False):
    """Key eye and aim-derived orientation at the inclusive shot endpoints."""
    if end < start:
        raise ValueError("end must be >= start")
    incoming = (cmds.listConnections(camera + ".translate", type="animCurve", s=True, d=False) or [])
    incoming += cmds.listConnections(camera + ".rotate", type="animCurve", s=True, d=False) or []
    if incoming and not replace_existing:
        raise RuntimeError("Camera already has animation; use a new camera or explicitly replace: %s" % incoming)

    previous_time = cmds.currentTime(q=True)
    records = []
    try:
        for frame, eye, aim in ((start, eye_start, aim_start), (end, eye_end, aim_end)):
            cmds.currentTime(frame)
            cmds.setAttr(camera + ".translate", *eye)
            rotation = _look_rotation(camera, aim)
            cmds.xform(camera, ws=True, ro=rotation)
            for attr in ("translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"):
                cmds.setKeyframe(camera, attribute=attr, time=frame)
            records.append({"frame": frame, "eye": list(eye), "aim": list(aim), "rotation": rotation})
    finally:
        cmds.currentTime(previous_time)
    eye_distance = math.sqrt(sum((eye_end[i] - eye_start[i]) ** 2 for i in range(3)))
    aim_distance = math.sqrt(sum((aim_end[i] - aim_start[i]) ** 2 for i in range(3)))
    return {"camera": camera, "start": start, "end": end, "endpoints": records,
            "eye_motion_distance": eye_distance, "aim_motion_distance": aim_distance}


def activate_camera(camera, panel=None):
    """Activate an existing camera in a visible model panel.

    Prefer the active visible panel, then the main perspective panel, then the
    first visible panel. Pass panel explicitly in production for reproducibility.
    """
    if not cmds.objExists(camera):
        raise ValueError("Missing camera: %s" % camera)
    panels = cmds.getPanel(type="modelPanel") or []
    visible = [item for item in panels if cmds.control(item, q=True, visible=True)]
    if not visible:
        raise RuntimeError("No visible modelPanel")
    if panel is not None and panel not in visible:
        raise RuntimeError("Requested modelPanel is not visible: %s" % panel)
    if panel is None:
        focused = cmds.getPanel(withFocus=True)
        if focused in visible:
            panel = focused
        elif "modelPanel4" in visible:
            panel = "modelPanel4"
        else:
            panel = visible[0]
    cmds.setFocus(panel)
    cmds.lookThru(panel, camera)
    cmds.refresh(force=True)
    active = cmds.modelEditor(panel, q=True, camera=True)
    if not active or cmds.ls(active, long=True)[0] != cmds.ls(camera, long=True)[0]:
        raise RuntimeError("Panel camera activation mismatch: %s != %s" % (active, camera))
    return {"panel": panel, "camera": cmds.ls(camera, long=True)[0]}


def _numeric_frame_key(path, base):
    pattern = re.escape(os.path.basename(base)) + r"\.(\d+)\.png$"
    match = re.match(pattern, os.path.basename(path))
    if not match:
    # playblast may append frame padding in a different but still numeric form
        match = re.search(r"\.(\d+)\.png$", os.path.basename(path))
    if not match:
        raise ValueError("Non-numeric playblast frame name: %s" % path)
    return int(match.group(1))


def playblast_shot(camera, start, end, output_base, width=854, height=480,
                   overwrite=False, off_screen=False, panel=None):
    """Playblast one inclusive shot range and verify the exact file count."""
    if end < start:
        raise ValueError("end must be >= start")
    output_dir = os.path.dirname(output_base)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    existing = sorted(glob.glob(output_base + ".*.png"))
    if existing and not overwrite:
        raise FileExistsError("Shot output already exists; choose a new version directory: %s" % existing[:5])
    if overwrite:
        for path in existing:
            os.remove(path)

    activation = activate_camera(camera, panel=panel)
    cmds.currentTime(start)
    cmds.refresh(force=True)
    returned = cmds.playblast(
        startTime=start,
        endTime=end,
        format="image",
        filename=output_base,
        sequenceTime=False,
        clearCache=True,
        viewer=False,
        showOrnaments=False,
        offScreen=off_screen,
        percent=100,
        widthHeight=(width, height),
        quality=95,
        compression="png",
    )
    files = glob.glob(output_base + ".*.png")
    files = sorted(files, key=lambda path: _numeric_frame_key(path, output_base))
    expected = end - start + 1
    result = {
        "camera": camera,
        "activation": activation,
        "start": start,
        "end": end,
        "expected_frames": expected,
        "actual_frames": len(files),
        "files": files,
        "returned": returned,
        "width": width,
        "height": height,
    }
    if len(files) != expected:
        raise RuntimeError("Shot frame count mismatch: %s" % json.dumps(result, ensure_ascii=False))
    result["ok"] = True
    return result


def camera_signature(camera, digits=3):
    """Return position + orientation + focal length for meaningful duplication checks."""
    shape = cmds.listRelatives(camera, shapes=True, fullPath=True)[0]
    position = cmds.xform(camera, q=True, ws=True, t=True)
    rotation = cmds.xform(camera, q=True, ws=True, ro=True)
    focal = cmds.getAttr(shape + ".focalLength")
    return tuple(round(v, digits) for v in list(position) + list(rotation) + [focal])


def camera_uniqueness(cameras, digits=3):
    groups = {}
    for camera in cameras:
        signature = camera_signature(camera, digits=digits)
        groups.setdefault(signature, []).append(camera)
    return {
        "camera_count": len(cameras),
        "unique_count": len(groups),
        "duplicate_groups": [names for names in groups.values() if len(names) > 1],
    }


__all__ = [
    "create_shot_camera",
    "keyframe_camera_move",
    "activate_camera",
    "playblast_shot",
    "camera_signature",
    "camera_uniqueness",
]
