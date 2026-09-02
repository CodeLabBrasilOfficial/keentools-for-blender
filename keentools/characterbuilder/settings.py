from bpy.types import PropertyGroup
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty,
                       FloatProperty, IntProperty, PointerProperty,
                       StringProperty)
from bpy.types import Image, Object


class CBPin(PropertyGroup):
    """A mesh vertex and its desired normalized image position."""

    pin_id: StringProperty(name='ID')
    vertex_index: IntProperty(name='Vertex', min=-1, default=-1)
    x: FloatProperty(name='X', min=0.0, max=1.0, default=0.5)
    y: FloatProperty(name='Y', min=0.0, max=1.0, default=0.5)
    weight: FloatProperty(name='Weight', min=0.0, default=1.0)
    radius: FloatProperty(name='Influence', min=0.0001, default=0.25)
    enabled: BoolProperty(name='Enabled', default=True)
    region: StringProperty(name='Region', default='UNASSIGNED')
    symmetry_mode: EnumProperty(
        name='Symmetry',
        items=(('LINKED', 'Linked', 'Mirror this pin when possible'),
               ('INDEPENDENT', 'Independent', 'Do not mirror this pin'),
               ('PARTIAL', 'Partially Linked', 'Use session symmetry strength')),
        default='PARTIAL')
    mirror_pin_id: StringProperty(name='Mirror Pin ID')


class CBReferenceView(PropertyGroup):
    reference_id: StringProperty(name='ID')
    name: StringProperty(name='Name', default='Reference')
    image: PointerProperty(name='Image', type=Image)
    camera: PointerProperty(name='Camera', type=Object)
    pins: CollectionProperty(name='Pins', type=CBPin)
    enabled: BoolProperty(name='Enabled', default=True)
    view_type: EnumProperty(
        name='View Type',
        items=(('FRONT', 'Front', ''), ('BACK', 'Back', ''),
               ('LEFT', 'Left', ''), ('RIGHT', 'Right', ''),
               ('FRONT_LEFT_3Q', 'Front Left 3/4', ''),
               ('FRONT_RIGHT_3Q', 'Front Right 3/4', ''),
               ('CUSTOM', 'Custom', '')),
        default='CUSTOM')
    weight: FloatProperty(name='View Weight', min=0.0, max=1.0, default=1.0)
    focal_length: FloatProperty(name='Focal Length', min=0.01, default=50.0)
    sensor_width: FloatProperty(name='Sensor Width', min=0.01, default=36.0)
    image_offset_x: FloatProperty(name='Image Offset X', default=0.0)
    image_offset_y: FloatProperty(name='Image Offset Y', default=0.0)
    image_scale: FloatProperty(name='Image Scale', min=0.01, default=1.0)


class CBSceneSettings(PropertyGroup):
    mesh: PointerProperty(name='Genesis 9 Mesh', type=Object)
    views: CollectionProperty(name='Reference Views', type=CBReferenceView)
    active_view: IntProperty(name='Active View', min=0, default=0)
    active_pin: IntProperty(name='Active Pin', min=-1, default=-1)
    pin_mode: BoolProperty(name='Character Pin Mode', default=False)
    solve_strength: FloatProperty(name='Solve Strength', min=0.0, max=1.0,
                                  default=0.65)
    preserve_face: BoolProperty(
        name='Preserve FaceBuilder head', default=True,
        description='Avoids changing vertices in the existing face vertex group')
    face_group: StringProperty(name='Face group', default='FaceBuilder')
    session_active: BoolProperty(name='Session Active', default=False)

    def active_reference(self):
        if 0 <= self.active_view < len(self.views):
            return self.views[self.active_view]
        return None
