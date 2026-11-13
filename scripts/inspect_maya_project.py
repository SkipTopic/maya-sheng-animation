"""Read-only Maya project inspection for the maya-sheng-animation skill.

Call inside Maya:
    from inspect_maya_project import inspect_project
    report = inspect_project(
        joints=["Bip001Head"],
        output_path="D:/project/logs/scene_audit.json",
    )

This script never opens, saves, closes, or modifies the scene.
"""

import json
import os
import maya.cmds as cmds


def _vector(node, attr):
    try:
        return list(cmds.getAttr(node + "." + attr)[0])
    except Exception:
        return None


def inspect_joint(node):
    if not cmds.objExists(node):
        return {"missing": True}
    return {
        "parent": cmds.listRelatives(node, parent=True, fullPath=True) or [],
        "children": cmds.listRelatives(node, children=True, fullPath=True) or [],
        "local_translate": _vector(node, "translate"),
        "local_rotate": _vector(node, "rotate"),
        "local_scale": _vector(node, "scale"),
        "joint_orient": _vector(node, "jointOrient"),
        "world_translate": list(cmds.xform(node, q=True, ws=True, t=True)),
        "world_rotate": list(cmds.xform(node, q=True, ws=True, ro=True)),
        "rotate_connections": cmds.listConnections(node + ".rotate", s=True, d=False) or [],
    }


def inspect_mesh(shape):
    transform = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
    bbox = list(cmds.xform(transform, q=True, ws=True, bb=True))
    return {
        "shape": shape,
        "transform": transform,
        "parent": cmds.listRelatives(transform, parent=True, fullPath=True) or [],
        "visible": cmds.getAttr(transform + ".visibility"),
        "bbox": bbox,
        "size": [bbox[3] - bbox[0], bbox[4] - bbox[1], bbox[5] - bbox[2]],
        "vertices": cmds.polyEvaluate(shape, vertex=True),
        "faces": cmds.polyEvaluate(shape, face=True),
        "skin_clusters": cmds.listConnections(shape, type="skinCluster") or [],
        "shading_groups": cmds.listConnections(shape, type="shadingEngine") or [],
    }


def inspect_project(joints=None, output_path=None):
    report = {
        "scene": cmds.file(q=True, sceneName=True),
        "modified": cmds.file(q=True, modified=True),
        "maya_version": cmds.about(version=True),
        "linear_unit": cmds.currentUnit(q=True, linear=True),
        "time_unit": cmds.currentUnit(q=True, time=True),
        "playback": {
            "min": cmds.playbackOptions(q=True, min=True),
            "max": cmds.playbackOptions(q=True, max=True),
            "animation_start": cmds.playbackOptions(q=True, animationStartTime=True),
            "animation_end": cmds.playbackOptions(q=True, animationEndTime=True),
        },
        "references": cmds.file(q=True, reference=True) or [],
        "unknown_nodes": cmds.ls(type="unknown") or [],
        "assemblies": cmds.ls(assemblies=True) or [],
        "blend_shapes": cmds.ls(type="blendShape") or [],
        "delta_mush": cmds.ls(type="deltaMush") or [],
        "ik_handles": cmds.ls(type="ikHandle") or [],
        "constraints": cmds.ls(type="constraint") or [],
        "animation_curves": cmds.ls(type="animCurve") or [],
        "sdef_named_nodes": [n for n in cmds.ls(dag=True, long=True) or [] if "sdef" in n.lower()],
        "note": "Scene facts are not visual proof. Render and reopen the saved scene for acceptance.",
    }
    textures = []
    for node in cmds.ls(type="file") or []:
        textures.append({"node": node, "path": cmds.getAttr(node + ".fileTextureName")})
    report["file_textures"] = textures

    report["meshes"] = [
        inspect_mesh(shape)
        for shape in (cmds.ls(type="mesh", long=True) or [])
        if not cmds.getAttr(shape + ".intermediateObject")
    ]
    joint_names = cmds.ls(type="joint", long=True) or []
    report["joint_count"] = len(joint_names)
    report["joint_names"] = joint_names
    report["requested_joints"] = {node: inspect_joint(node) for node in (joints or [])}

    cameras = []
    for shape in cmds.ls(type="camera", long=True) or []:
        transform = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
        cameras.append({
            "transform": transform,
            "shape": shape,
            "focal_length": cmds.getAttr(shape + ".focalLength"),
            "orthographic": cmds.getAttr(shape + ".orthographic"),
            "near_clip": cmds.getAttr(shape + ".nearClipPlane"),
            "far_clip": cmds.getAttr(shape + ".farClipPlane"),
        })
    report["cameras"] = cameras

    animated = set()
    for curve in report["animation_curves"]:
        for node in cmds.listConnections(curve, s=False, d=True) or []:
            animated.add(node)
    report["animated_nodes"] = sorted(animated)
    report["visible_model_panels"] = [
        panel for panel in (cmds.getPanel(type="modelPanel") or [])
        if cmds.control(panel, q=True, visible=True)
    ]

    if output_path:
        parent = os.path.dirname(output_path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
    return report
