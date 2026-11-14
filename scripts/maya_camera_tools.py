"""Maya camera creation, movement, activation and shot playblast helpers.

Functions never save or open scenes. Use a versioned work scene and new output dirs.
"""

import glob
import hashlib
import json
import math
import os
import re
import struct
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
    if incoming and replace_existing:
        for curve in set(incoming):
            if cmds.objExists(curve):
                cmds.delete(curve)

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
    previous_camera = cmds.modelEditor(panel, q=True, camera=True)
    cmds.setFocus(panel)
    cmds.lookThru(panel, camera)
    cmds.refresh(force=True)
    active = cmds.modelEditor(panel, q=True, camera=True)
    if not active or cmds.ls(active, long=True)[0] != cmds.ls(camera, long=True)[0]:
        raise RuntimeError("Panel camera activation mismatch: %s != %s" % (active, camera))
    return {"panel": panel, "camera": cmds.ls(camera, long=True)[0], "previous_camera": previous_camera}


def _png_size(path):
    with open(path, "rb") as fh:
        header = fh.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("Invalid PNG header: %s" % path)
    return list(struct.unpack(">II", header[16:24]))


def _file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


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
                   overwrite=False, off_screen=False, panel=None,
                   require_variation=False, restore_state=True):
    """Playblast one inclusive shot range and verify frames, PNG sizes and hashes.

    overwrite=True deletes only files matching output_base + ".*.png" in the
    selected versioned output location. Use a new directory instead by default.
    """
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

    previous_time = cmds.currentTime(q=True)
    previous_selection = cmds.ls(selection=True, long=True) or []
    activation = activate_camera(camera, panel=panel)
    try:
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
    finally:
        if restore_state:
            cmds.currentTime(previous_time)
            previous_camera = activation.get("previous_camera")
            if previous_camera and cmds.objExists(previous_camera):
                cmds.lookThru(activation["panel"], previous_camera)
            existing_selection = [node for node in previous_selection if cmds.objExists(node)]
            if existing_selection:
                cmds.select(existing_selection, replace=True)
            else:
                cmds.select(clear=True)
            cmds.refresh(force=True)

    files = glob.glob(output_base + ".*.png")
    frame_numbers = [_numeric_frame_key(path, output_base) for path in files]
    files = [path for _frame, path in sorted(zip(frame_numbers, files))]
    frame_numbers = sorted(frame_numbers)
    expected = end - start + 1
    sizes = {os.path.basename(path): _png_size(path) for path in files}
    hashes = {os.path.basename(path): _file_hash(path) for path in files}
    unique_hashes = len(set(hashes.values()))
    result = {
        "camera": camera,
        "activation": activation,
        "start": start,
        "end": end,
        "expected_frames": expected,
        "actual_frames": len(files),
        "actual_frame_numbers": frame_numbers,
        "files": files,
        "returned": returned,
        "width": width,
        "height": height,
        "png_sizes": sizes,
        "image_hashes": hashes,
        "unique_image_hashes": unique_hashes,
        "all_frames_identical": unique_hashes == 1 and expected > 1,
        "state_restored": restore_state,
    }
    errors = []
    if len(files) != expected or set(frame_numbers) != set(range(start, end + 1)):
        errors.append("Frame count/set mismatch")
    for name, size in sizes.items():
        if size != [width, height]:
            errors.append("PNG size mismatch for %s: %s" % (name, size))
    if require_variation and result["all_frames_identical"]:
        errors.append("All frames are identical; inspect camera activation, animation and off-screen mode")
    if errors:
        raise RuntimeError("Playblast validation failed: %s" % json.dumps({"errors": errors, "result": result}, ensure_ascii=False))
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
