"""Multi-view character fitting for an existing Genesis 9 mesh.

This module is intentionally independent from FaceBuilder.  FaceBuilder's
native model remains responsible for facial fitting; this package owns the
body session and its persistent references.
"""

from bpy.props import PointerProperty

from .settings import CBSceneSettings, CBReferenceView, CBPin
from .operators import (CB_OT_CreateSession, CB_OT_AddReferenceView,
                        CB_OT_AddPin, CB_OT_Solve, CB_OT_ResetMesh,
                        CB_PT_Panel)


CLASSES_TO_REGISTER = (CBPin, CBReferenceView, CBSceneSettings,
                       CB_OT_CreateSession, CB_OT_AddReferenceView,
                       CB_OT_AddPin, CB_OT_Solve, CB_OT_ResetMesh,
                       CB_PT_Panel)


def register():
    import bpy
    from bpy.utils import register_class

    for cls in CLASSES_TO_REGISTER:
        register_class(cls)
    bpy.types.Scene.keentools_characterbuilder = PointerProperty(
        type=CBSceneSettings)


def unregister():
    import bpy
    from bpy.utils import unregister_class

    if hasattr(bpy.types.Scene, 'keentools_characterbuilder'):
        del bpy.types.Scene.keentools_characterbuilder
    for cls in reversed(CLASSES_TO_REGISTER):
        unregister_class(cls)
