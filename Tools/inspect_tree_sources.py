import bpy
import glob
import os


SOURCE_GLOB = r"C:\Users\ryant\OneDrive\Desktop\SM_Tree*.FBX"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


for path in sorted(glob.glob(SOURCE_GLOB)):
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    print(f"SOURCE {os.path.basename(path)}")
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            mesh = obj.data
            print(
                f"  OBJECT {obj.name} vertices={len(mesh.vertices)} polygons={len(mesh.polygons)} "
                f"materials={[material.name if material else None for material in mesh.materials]}"
            )
