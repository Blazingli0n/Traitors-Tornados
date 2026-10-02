import bpy
import math
import os
from mathutils import Vector


SOURCE_DIR = os.environ.get(
    "TREE_PREVIEW_SOURCE",
    r"C:\Users\ryant\OneDrive\Desktop\TreeVariants",
)
PREVIEW_DIR = os.path.join(SOURCE_DIR, "Previews")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def point_camera(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main():
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    files = sorted(
        filename for filename in os.listdir(SOURCE_DIR) if filename.lower().endswith(".fbx")
    )

    for filename in files:
        clear_scene()
        path = os.path.join(SOURCE_DIR, filename)
        bpy.ops.import_scene.fbx(filepath=path)

        render_meshes = [
            obj for obj in bpy.context.scene.objects
            if obj.type == "MESH" and not obj.name.startswith("UCX_")
        ]
        for obj in bpy.context.scene.objects:
            if obj.name.startswith("UCX_"):
                obj.hide_render = True

        bounds = [obj.matrix_world @ Vector(corner) for obj in render_meshes for corner in obj.bound_box]
        bounds_min = Vector(tuple(min(point[axis] for point in bounds) for axis in range(3)))
        bounds_max = Vector(tuple(max(point[axis] for point in bounds) for axis in range(3)))
        center = (bounds_min + bounds_max) * 0.5
        dimensions = bounds_max - bounds_min
        frame_size = max(dimensions.z, dimensions.x * 1.25, dimensions.y * 1.25)

        camera_data = bpy.data.cameras.new("PreviewCamera")
        camera = bpy.data.objects.new("PreviewCamera", camera_data)
        bpy.context.scene.collection.objects.link(camera)
        camera.location = center + Vector((frame_size * 1.35, -frame_size * 2.4, frame_size * 0.30))
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = frame_size * 1.15
        camera.data.clip_start = max(frame_size * 0.001, 0.001)
        camera.data.clip_end = frame_size * 10.0
        point_camera(camera, center)
        bpy.context.scene.camera = camera

        scene = bpy.context.scene
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "MATERIAL"
        scene.display.shading.show_shadows = True
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "WORLD"
        scene.render.resolution_x = 520
        scene.render.resolution_y = 650
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.film_transparent = False
        scene.world.color = (0.035, 0.045, 0.06)
        scene.render.filepath = os.path.join(PREVIEW_DIR, os.path.splitext(filename)[0] + ".png")
        bpy.ops.render.render(write_still=True)
        print(f"RENDERED {scene.render.filepath} objects={len(render_meshes)}")


main()
