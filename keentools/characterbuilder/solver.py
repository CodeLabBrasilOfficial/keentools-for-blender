"""Small, deterministic body fitting kernel used by the Blender operators."""

import math

from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def _camera_axes(camera):
    matrix = camera.matrix_world.to_3x3()
    return matrix @ Vector((1.0, 0.0, 0.0)), matrix @ Vector((0.0, 1.0, 0.0))


def _project(scene, camera, point):
    return world_to_camera_view(scene, camera, point)


def _belongs_to_group(group, index):
    if not group:
        return False
    try:
        return group.weight(index) > 0.5
    except (RuntimeError, KeyError):
        return False


def solve_view(scene, mesh_object, view, strength, preserve_face=True,
               face_group='FaceBuilder'):
    """Apply image-space pin corrections with smooth local influence.

    This is a first-stage solver for an already imported Genesis 9 mesh. It
    does not infer hidden geometry; multiple views reduce ambiguity by adding
    corrections from each camera.
    """
    camera = view.camera
    if not camera or camera.type != 'CAMERA' or not view.pins:
        return 0

    group = mesh_object.vertex_groups.get(face_group) if preserve_face else None
    points = [mesh_object.matrix_world @ vertex.co
              for vertex in mesh_object.data.vertices]
    right, up = _camera_axes(camera)
    changed = 0

    for pin in view.pins:
        if pin.vertex_index >= len(points):
            continue
        anchor = points[pin.vertex_index]
        projected = _project(scene, camera, anchor)
        dx = pin.x - projected.x
        dy = pin.y - projected.y
        if abs(dx) + abs(dy) < 1e-7:
            continue

        depth = max(0.001, (camera.matrix_world.inverted() @ anchor).z * -1.0)
        scale_x = 2.0 * depth * math.tan(camera.data.angle_x / 2.0)
        scale_y = 2.0 * depth * math.tan(camera.data.angle_y / 2.0)
        delta = (right.normalized() * dx * scale_x +
                 up.normalized() * dy * scale_y) * strength * pin.weight

        for index, vertex in enumerate(mesh_object.data.vertices):
            if _belongs_to_group(group, index):
                continue
            distance = (points[index] - anchor).length
            influence = max(0.0, 1.0 - distance / pin.radius)
            if influence <= 0.0:
                continue
            vertex.co = mesh_object.matrix_world.inverted() @ (
                points[index] + delta * influence)
            points[index] = mesh_object.matrix_world @ vertex.co
            changed += 1
    mesh_object.data.update()
    return changed
