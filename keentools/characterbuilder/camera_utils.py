"""Camera and image-view helpers for Character Builder."""

from typing import Optional, Tuple

import bpy

from ..utils.coords import get_camera_border


def ensure_reference_camera(scene, view, source=None):
    """Give a reference its own camera object and keep pose separate from shape."""
    if view.camera and view.camera.name in bpy.data.objects:
        return view.camera

    source = source if source and source.type == 'CAMERA' else scene.camera
    data = source.data.copy() if source else bpy.data.cameras.new('CB Reference Camera')
    camera = bpy.data.objects.new(f'CB Camera {view.name}', data)
    scene.collection.objects.link(camera)
    if source:
        camera.matrix_world = source.matrix_world.copy()
    view.camera = camera
    return camera


def apply_reference_camera(view) -> bool:
    camera = view.camera
    if not camera or camera.type != 'CAMERA':
        return False
    camera.data.lens = view.focal_length
    camera.data.sensor_width = view.sensor_width
    background = camera.data.background_images[0] \
        if camera.data.background_images else camera.data.background_images.new()
    background.image = view.image
    background.offset_x = view.image_offset_x
    background.offset_y = view.image_offset_y
    background.scale = view.image_scale
    background.alpha = 1.0
    background.display_depth = 'BACK'
    background.frame_method = 'FIT'
    camera.data.show_background_images = view.image is not None
    return True


def image_to_region(area, x: float, y: float) -> Tuple[float, float]:
    """Map normalized image coordinates (origin top-left) to region pixels."""
    x1, y1, x2, y2 = get_camera_border(area)
    return x1 + (x2 - x1) * x, y2 - (y2 - y1) * y


def region_to_image(area, px: float, py: float) -> Optional[Tuple[float, float]]:
    x1, y1, x2, y2 = get_camera_border(area)
    if x2 <= x1 or y2 <= y1:
        return None
    x = (px - x1) / (x2 - x1)
    y = (y2 - py) / (y2 - y1)
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
        return None
    return x, y


def set_camera_view(context, camera):
    context.scene.camera = camera
    context.space_data.region_3d.view_perspective = 'CAMERA'
    context.space_data.region_3d.view_camera_zoom = 0.0
    context.space_data.region_3d.view_camera_offset = (0.0, 0.0)
