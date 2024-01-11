bl_info = {
    "name": "Transfer ShapeKeys via UV map",
    "author": "Fabrizio Nunnari",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Object > Transfer ShapeKey via UV",
    "description": "Transfers a ShapeKey from one object to another given they use UV maps that can show correctly the same texture",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}


import bpy
from bpy.types import Operator
from bpy.props import IntProperty, BoolProperty
from mathutils import Vector

from sktransfer.shapekeys import transfer_shapekey_via_uv

from typing import Tuple


class OBJECT_OT_transfer_shapekey_via_uv(Operator):
    """Transfer a ShypeKey between two objects using the UV maps to match ShapeKeys offset values."""

    bl_idname = "object.transfer_shapekey_via_uv"
    bl_label = "Transfer ShapeKey via UV"
    bl_options = {'REGISTER', 'UNDO'}

    buffer_size: IntProperty(
        name="buffer_size",
        default=256,
        description="The resolution (size X size) of the intermediate memory buffer storing the ShapeKey deltas and their interpolation."
                    "This will occupy 8*(size*size*4) memory for an numpy float64 ndarray."
                    "Increase this size if you have a high density of pixels in the UV and see distortions in the transferred ShapeKey."
    )

    #relative_to_normals: BoolProperty(
    #    name="relative_to_normals",
    #    default=False,
    #    description="If True, vertex offsets will be considered as relative to the vertex normals,"
    #                " otherwise, each offset is in object space."
    #)

    save_debug_images: BoolProperty(
        name="save_debug_images",
        default=False,
        description="If True, save some debug images to visually debug the transfer routine."
                    " Needs the PIL module installed (pip install pillow) !!!"
    )

    @staticmethod
    def _get_src_and_dst_object(context) -> Tuple[bpy.types.Object, bpy.types.Object]:
        """
        Small support function to distinguish between the destination (active object, selected with shift+click)
        and the source objects, selected as first (click)
        :param context:
        :return: A tuple with (source,destination) references
        """

        assert len(context.selected_objects) == 2

        # The destination object is the last selected (so the active one)
        dst_obj = context.active_object
        # And the source object is the other in the selected list
        src_obj = None
        for obj in context.selected_objects:
            if obj != dst_obj:
                src_obj = obj
                break
        assert src_obj is not None

        return src_obj, dst_obj

    @classmethod
    def poll(cls, context):

        # There must be an active object
        if context.active_object is None:
            return False

        # And exactly two selected objects
        if len(context.selected_objects) != 2:
            return False

        src_obj, dst_obj = OBJECT_OT_transfer_shapekey_via_uv._get_src_and_dst_object(context=context)

        # Both source and destination must be MESH types
        if src_obj.type != 'MESH':
            return False
        if dst_obj.type != 'MESH':
            return False

        # The source mesh must have at least 1 ShapeKey
        src_mesh = src_obj.data
        if src_mesh.shape_keys is None:
            return False

        # There must be at least one UV layer in the source mesh
        if src_mesh.uv_layers.active_index == -1:
            return False

        # There must be at least one UV layer in the destination mesh
        dst_mesh = dst_obj.data
        if dst_mesh.uv_layers.active_index == -1:
            return False

        # If all passed, the context is good.
        return True

    def execute(self, context):

        src_obj, dst_obj = OBJECT_OT_transfer_shapekey_via_uv._get_src_and_dst_object(context=context)
        assert src_obj.type == 'MESH'
        assert dst_obj.type == 'MESH'

        # Get references to mesh and shape key to save
        src_mesh = src_obj.data
        assert type(src_mesh) is bpy.types.Mesh

        src_active_sk_idx = src_obj.active_shape_key_index
        src_active_uv_idx = src_mesh.uv_layers.active_index

        dst_mesh = dst_obj.data
        dst_active_uv_idx = dst_mesh.uv_layers.active_index

        print(f"Transferring from object {src_obj.name} ShapeKey with idx {src_active_sk_idx}"
              f" using uv layer {src_active_uv_idx} --> to object {dst_obj.name} using uv {dst_active_uv_idx}...")
        transfer_shapekey_via_uv(src_obj=src_obj, src_sk_idx=src_active_sk_idx, src_uv_idx=src_active_uv_idx,
                                 dst_obj=dst_obj, dst_uv_idx=dst_active_uv_idx,
                                 resolution=(self.buffer_size, self.buffer_size),
                                 save_debug_images=self.save_debug_images)

        return {'FINISHED'}


#
# Registration

#def add_object_button(self, context):
#    self.layout.operator(
#        OBJECT_OT_transfer_shapekey_via_uv.bl_idname,
#        text="Add Object",
#        icon='PLUGIN')


# This allows you to right click on a button and link to documentation
#def add_object_manual_map():
#    url_manual_prefix = "https://github.com/DFKI-SignLanguage/Transfer-ShapeKeys-Via-UV-Blender-Addon/"
#    url_manual_mapping = (
#        ("bpy.ops.object.transfer_shapekey_via_uv", "manual.html"),
#    )
#    return url_manual_prefix, url_manual_mapping


def register():
    bpy.utils.register_class(OBJECT_OT_transfer_shapekey_via_uv)
    # bpy.utils.register_manual_map(add_object_manual_map)
    # bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_transfer_shapekey_via_uv)
    # bpy.utils.unregister_manual_map(add_object_manual_map)
    # bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)


#
# MAIN
# If executed manually, register the operator
if __name__ == "__main__":
    register()
