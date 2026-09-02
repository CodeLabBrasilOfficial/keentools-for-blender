"""Modal Character Pin Mode: create, select, drag and delete image pins."""

import uuid

from bpy.types import Operator
from bpy.props import BoolProperty

from .camera_utils import (apply_reference_camera, region_to_image,
                           image_to_region, set_camera_view)
from .pin_draw import CharacterPinDrawer


def _settings(context):
    return context.scene.keentools_characterbuilder


class CB_OT_PinMode(Operator):
    bl_idname = 'keentools.character_pin_mode'
    bl_label = 'Enter Character Pin Mode'
    bl_options = {'REGISTER', 'UNDO'}

    _drawer = None
    _area = None
    _previous_camera = None
    _dragging = False
    _drag_pin = -1
    _old_target = None

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, 'keentools_characterbuilder', None)
        return bool(settings and settings.session_active and settings.active_reference())

    def _view(self, context):
        return _settings(context).active_reference()

    def _pin_at(self, context, x, y):
        view = self._view(context)
        if not view:
            return -1
        region = next((r for r in context.area.regions if r.type == 'WINDOW'), None)
        if not region:
            return -1
        best, best_dist = -1, 14.0
        for index, pin in enumerate(view.pins):
            px, py = image_to_region(context.area, pin.x, pin.y)
            distance = ((px - x) ** 2 + (py - y) ** 2) ** 0.5
            if distance < best_dist:
                best, best_dist = index, distance
        return best

    def _finish(self, context, cancelled=False):
        settings = _settings(context)
        settings.pin_mode = False
        self._dragging = False
        self._drag_pin = -1
        if self._drawer:
            self._drawer.unregister()
        if self._previous_camera:
            context.scene.camera = self._previous_camera
        self._previous_camera = None
        if context.area:
            context.area.tag_redraw()
        return {'CANCELLED' if cancelled else 'FINISHED'}

    def invoke(self, context, event):
        view = self._view(context)
        if not view or not view.camera or not view.image:
            self.report({'ERROR'}, 'Reference view needs an image and camera')
            return {'CANCELLED'}
        self._previous_camera = context.scene.camera
        apply_reference_camera(view)
        set_camera_view(context, view.camera)
        settings = _settings(context)
        settings.pin_mode = True
        self._area = context.area
        self._drawer = CharacterPinDrawer()
        self._drawer.register(context.area, settings)
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE', 'WINDOW_DEACTIVATE'}:
            return self._finish(context, cancelled=True)
        if event.type == 'DELETE' and event.value == 'PRESS':
            view = self._view(context)
            if view and 0 <= _settings(context).active_pin < len(view.pins):
                view.pins.remove(_settings(context).active_pin)
                _settings(context).active_pin = -1
                context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        if event.type == 'MOUSEMOVE':
            if self._dragging:
                point = region_to_image(context.area, event.mouse_region_x, event.mouse_region_y)
                if point:
                    pin = self._view(context).pins[self._drag_pin]
                    pin.x, pin.y = point
                    context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            settings = _settings(context)
            pin_index = self._pin_at(context, event.mouse_region_x, event.mouse_region_y)
            if pin_index >= 0:
                settings.active_pin = pin_index
                self._drag_pin = pin_index
                self._dragging = True
                pin = self._view(context).pins[pin_index]
                self._old_target = (pin.x, pin.y)
            else:
                point = region_to_image(context.area, event.mouse_region_x, event.mouse_region_y)
                if point:
                    pin = self._view(context).pins.add()
                    pin.pin_id = str(uuid.uuid4())
                    pin.x, pin.y = point
                    pin.vertex_index = -1
                    pin.region = 'UNASSIGNED'
                    settings.active_pin = len(self._view(context).pins) - 1
                    self._drag_pin = settings.active_pin
                    self._dragging = True
                    self._old_target = point
                    context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self._dragging = False
            self._drag_pin = -1
            return {'RUNNING_MODAL'}
        return {'RUNNING_MODAL'}
