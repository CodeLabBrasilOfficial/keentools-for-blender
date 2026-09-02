"""GPU overlay for Character Builder pins."""

import blf
import gpu
from bpy.types import SpaceView3D
from gpu_extras.batch import batch_for_shader

from .camera_utils import image_to_region


class CharacterPinDrawer:
    def __init__(self):
        self.handle = None
        self.area = None
        self.settings = None

    def register(self, area, settings):
        self.unregister()
        self.area = area
        self.settings = settings
        self.handle = SpaceView3D.draw_handler_add(
            self.draw, (), 'WINDOW', 'POST_PIXEL')

    def unregister(self):
        if self.handle is not None and self.area is not None:
            SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
        self.handle = None
        self.area = None
        self.settings = None

    def draw(self):
        if not self.area or not self.settings:
            return
        view = self.settings.active_reference()
        if not view:
            return
        region = next((r for r in self.area.regions if r.type == 'WINDOW'), None)
        if not region:
            return
        positions = []
        colors = []
        labels = []
        for index, pin in enumerate(view.pins):
            if not pin.enabled:
                continue
            px, py = image_to_region(self.area, pin.x, pin.y)
            positions.append((px, py))
            selected = index == self.settings.active_pin
            colors.append((1.0, 0.2, 0.05, 1.0) if selected
                          else (0.05, 0.85, 1.0, 1.0))
            labels.append((index, px, py, selected))

        if not positions:
            return
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        gpu.state.point_size_set(12.0)
        gpu.state.blend_set('ALPHA')
        for position, color in zip(positions, colors):
            point_batch = batch_for_shader(shader, 'POINTS', {'pos': [position]})
            shader.bind()
            shader.uniform_float('color', color)
            point_batch.draw(shader)
        gpu.state.point_size_set(1.0)

        for index, px, py, selected in labels:
            blf.size(0, 13)
            blf.color(0, 1.0, 1.0, 1.0, 1.0) if selected else blf.color(0, 1.0, 1.0, 1.0, 0.85)
            blf.position(0, px + 8, py + 5, 0)
            blf.draw(0, f'Pin {index + 1}')
