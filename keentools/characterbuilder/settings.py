from bpy.types import PropertyGroup
from bpy.props import (BoolProperty, CollectionProperty, FloatProperty,
                       IntProperty, PointerProperty, StringProperty)
from bpy.types import Image, Object


class CBPin(PropertyGroup):
    """A mesh vertex and its desired normalized image position."""

    vertex_index: IntProperty(name='Vertex', min=0)
    x: FloatProperty(name='X', min=0.0, max=1.0, default=0.5)
    y: FloatProperty(name='Y', min=0.0, max=1.0, default=0.5)
    weight: FloatProperty(name='Weight', min=0.0, default=1.0)
    radius: FloatProperty(name='Influence', min=0.0001, default=0.25)


class CBReferenceView(PropertyGroup):
    name: StringProperty(name='Name', default='Reference')
    image: PointerProperty(name='Image', type=Image)
    camera: PointerProperty(name='Camera', type=Object)
    pins: CollectionProperty(name='Pins', type=CBPin)
    enabled: BoolProperty(name='Enabled', default=True)


class CBSceneSettings(PropertyGroup):
    mesh: PointerProperty(name='Genesis 9 Mesh', type=Object)
    views: CollectionProperty(name='Reference Views', type=CBReferenceView)
    active_view: IntProperty(name='Active View', min=0, default=0)
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
