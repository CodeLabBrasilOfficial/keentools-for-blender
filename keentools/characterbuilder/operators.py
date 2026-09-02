import bpy
from bpy.types import Operator, Panel
from bpy.props import IntProperty, FloatProperty, StringProperty

from .solver import solve_view


def _settings(context):
    return context.scene.keentools_characterbuilder


class CB_OT_CreateSession(Operator):
    bl_idname = 'keentools.character_create_session'
    bl_label = 'Use Selected Mesh as Genesis 9'

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'MESH'

    def execute(self, context):
        settings = _settings(context)
        settings.mesh = context.object
        settings.session_active = True
        base = settings.mesh.data.shape_keys.key_blocks.get('KT Character Base') \
            if settings.mesh.data.shape_keys else None
        if base is None:
            settings.mesh.shape_key_add(name='KT Character Base', from_mix=False)
        self.report({'INFO'}, 'Character session created for the selected mesh')
        return {'FINISHED'}


class CB_OT_AddReferenceView(Operator):
    bl_idname = 'keentools.character_add_view'
    bl_label = 'Add Reference View'
    image_name: StringProperty(name='Image datablock')
    camera_name: StringProperty(name='Camera object')

    def execute(self, context):
        settings = _settings(context)
        image = bpy.data.images.get(self.image_name) if self.image_name else None
        camera_obj = bpy.data.objects.get(self.camera_name) if self.camera_name else context.scene.camera
        if not camera_obj or camera_obj.type != 'CAMERA':
            self.report({'ERROR'}, 'Select or provide a camera for this view')
            return {'CANCELLED'}
        view = settings.views.add()
        view.name = f'View {len(settings.views)}'
        view.image = image
        view.camera = camera_obj
        settings.active_view = len(settings.views) - 1
        return {'FINISHED'}


class CB_OT_AddPin(Operator):
    bl_idname = 'keentools.character_add_pin'
    bl_label = 'Add Character Pin'
    vertex_index: IntProperty(name='Vertex Index', min=0)
    x: FloatProperty(name='Image X', min=0.0, max=1.0, default=0.5)
    y: FloatProperty(name='Image Y', min=0.0, max=1.0, default=0.5)
    radius: FloatProperty(name='Influence Radius', min=0.0001, default=0.25)

    def execute(self, context):
        view = _settings(context).active_reference()
        if not view:
            self.report({'ERROR'}, 'Add a reference view first')
            return {'CANCELLED'}
        pin = view.pins.add()
        pin.vertex_index, pin.x, pin.y, pin.radius = self.vertex_index, self.x, self.y, self.radius
        return {'FINISHED'}


class CB_OT_Solve(Operator):
    bl_idname = 'keentools.character_solve'
    bl_label = 'Solve Character From Views'

    def execute(self, context):
        settings = _settings(context)
        if not settings.mesh:
            self.report({'ERROR'}, 'Create a character session with a mesh first')
            return {'CANCELLED'}
        count = 0
        base = settings.mesh.data.shape_keys.key_blocks.get('KT Character Base') \
            if settings.mesh.data.shape_keys else None
        if base and len(base.data) == len(settings.mesh.data.vertices):
            for index, vertex in enumerate(settings.mesh.data.vertices):
                vertex.co = base.data[index].co
        for view in settings.views:
            if view.enabled:
                count += solve_view(context.scene, settings.mesh, view,
                                    settings.solve_strength,
                                    settings.preserve_face, settings.face_group)
        self.report({'INFO'}, f'Character solve updated {count} vertices')
        return {'FINISHED'}


class CB_OT_ResetMesh(Operator):
    bl_idname = 'keentools.character_reset_mesh'
    bl_label = 'Reset Character Mesh'

    def execute(self, context):
        settings = _settings(context)
        if not settings.mesh:
            return {'CANCELLED'}
        base = settings.mesh.data.shape_keys.key_blocks.get('KT Character Base') \
            if settings.mesh.data.shape_keys else None
        if base and len(base.data) == len(settings.mesh.data.vertices):
            for index, vertex in enumerate(settings.mesh.data.vertices):
                vertex.co = base.data[index].co
        settings.mesh.data.update()
        return {'FINISHED'}


class CB_PT_Panel(Panel):
    bl_idname = 'KEENTOOLS_PT_character_builder'
    bl_label = 'Character Builder'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Character'

    def draw(self, context):
        layout = self.layout
        settings = _settings(context)
        layout.operator(CB_OT_CreateSession.bl_idname, icon='MESH_MONKEY')
        if not settings.session_active:
            return
        layout.label(text=f'Mesh: {settings.mesh.name if settings.mesh else "None"}')
        layout.operator(CB_OT_AddReferenceView.bl_idname, icon='IMAGE_DATA')
        if settings.views:
            layout.prop(settings, 'active_view')
            view = settings.active_reference()
            layout.label(text=f'Pins in view: {len(view.pins) if view else 0}')
            pin = layout.operator(CB_OT_AddPin.bl_idname, icon='PINNED')
            pin.vertex_index = 0
            pin.x = 0.5
            pin.y = 0.5
        layout.prop(settings, 'solve_strength')
        layout.prop(settings, 'preserve_face')
        if settings.preserve_face:
            layout.prop(settings, 'face_group')
        layout.operator(CB_OT_Solve.bl_idname, icon='MOD_SMOOTH')
        layout.operator(CB_OT_ResetMesh.bl_idname, icon='LOOP_BACK')
        layout.label(text=f'Reference views: {len(settings.views)}')
