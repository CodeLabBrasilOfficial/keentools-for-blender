import bpy
from bpy.types import Operator, Panel
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from .camera_utils import apply_reference_camera, ensure_reference_camera
from .pin_interaction import CB_OT_PinMode
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


class CB_OT_AddReferencePhoto(Operator, ImportHelper):
    bl_idname = 'keentools.character_add_photo'
    bl_label = 'Add Reference Photo'
    bl_options = {'REGISTER', 'UNDO'}
    filter_glob: StringProperty(default='*.jpg;*.jpeg;*.png;*.webp;*.tif;*.tiff',
                                options={'HIDDEN'})

    def execute(self, context):
        settings = _settings(context)
        try:
            image = bpy.data.images.load(self.filepath, check_existing=True)
        except RuntimeError as err:
            self.report({'ERROR'}, f'Could not load image: {err}')
            return {'CANCELLED'}
        view = settings.views.add()
        view.reference_id = str(len(settings.views))
        view.name = image.name
        view.image = image
        camera = ensure_reference_camera(context.scene, view)
        view.focal_length = camera.data.lens
        view.sensor_width = camera.data.sensor_width
        apply_reference_camera(view)
        settings.active_view = len(settings.views) - 1
        self.report({'INFO'}, f'Reference added: {view.name}')
        return {'FINISHED'}


class CB_OT_RemoveReferenceView(Operator):
    bl_idname = 'keentools.character_remove_view'
    bl_label = 'Remove Reference View'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = _settings(context)
        if not (0 <= settings.active_view < len(settings.views)):
            return {'CANCELLED'}
        view = settings.views[settings.active_view]
        camera = view.camera
        settings.views.remove(settings.active_view)
        settings.active_view = min(settings.active_view, len(settings.views) - 1)
        if camera and camera.name.startswith('CB Camera ') and camera.users == 0:
            bpy.data.objects.remove(camera)
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
        layout.operator(CB_OT_AddReferencePhoto.bl_idname, icon='IMAGE_DATA')
        if settings.views:
            layout.prop(settings, 'active_view')
            view = settings.active_reference()
            if view:
                layout.prop(view, 'name')
                layout.prop(view, 'view_type')
                layout.prop(view, 'enabled')
                layout.prop(view, 'weight')
                layout.prop(view, 'camera')
                layout.prop(view, 'image')
                layout.operator(CB_OT_RemoveReferenceView.bl_idname, icon='X')
                layout.label(text=f'Pins in view: {len(view.pins)}')
                layout.operator(CB_OT_PinMode.bl_idname, icon='PINNED')
        else:
            layout.label(text='Add a reference photo to begin')
        layout.prop(settings, 'solve_strength')
        layout.prop(settings, 'preserve_face')
        if settings.preserve_face:
            layout.prop(settings, 'face_group')
        layout.operator(CB_OT_Solve.bl_idname, icon='MOD_SMOOTH')
        layout.operator(CB_OT_ResetMesh.bl_idname, icon='LOOP_BACK')
        layout.label(text=f'Reference views: {len(settings.views)}')
