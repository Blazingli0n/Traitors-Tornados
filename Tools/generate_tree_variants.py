import bpy
import math
import os
import random
from collections import deque
from mathutils import Vector, Matrix


SOURCE_FBX = r"C:\Users\ryant\OneDrive\Desktop\SM_Tree_004.FBX"
OUTPUT_DIR = r"C:\Users\ryant\OneDrive\Desktop\TreeVariants"


VARIANTS = (
    {
        "suffix": "NarrowTall",
        "radial": 0.76,
        "height": 1.07,
        "cluster_xy": 0.92,
        "cluster_z": 1.00,
        "lean_x": 0.0,
        "lean_y": 0.0,
        "twist": 7.0,
    },
    {
        "suffix": "Broad",
        "radial": 1.18,
        "height": 0.96,
        "cluster_xy": 1.05,
        "cluster_z": 0.96,
        "lean_x": 0.0,
        "lean_y": 0.0,
        "twist": 9.0,
    },
    {
        "suffix": "Compact",
        "radial": 0.91,
        "height": 0.86,
        "cluster_xy": 1.04,
        "cluster_z": 0.96,
        "lean_x": 0.0,
        "lean_y": 0.0,
        "twist": 10.0,
    },
    {
        "suffix": "Windswept",
        "radial": 0.96,
        "height": 1.00,
        "cluster_xy": 0.96,
        "cluster_z": 1.00,
        "lean_x": 115.0,
        "lean_y": -20.0,
        "twist": 16.0,
    },
    {
        "suffix": "Layered",
        "radial": 1.00,
        "height": 1.02,
        "cluster_xy": 0.95,
        "cluster_z": 0.94,
        "lean_x": 0.0,
        "lean_y": 0.0,
        "twist": 12.0,
        "layered": True,
    },
    {
        "suffix": "NaturalAsym",
        "radial": 1.02,
        "height": 0.99,
        "cluster_xy": 0.98,
        "cluster_z": 1.00,
        "lean_x": -48.0,
        "lean_y": 72.0,
        "twist": 18.0,
        "asymmetry": True,
    },
)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        if material.users == 0:
            bpy.data.materials.remove(material)


def canonicalize_material_names(mesh):
    for material in mesh.materials:
        if not material:
            continue
        lower_name = material.name.lower()
        if any(token in lower_name for token in ("pine", "leaf", "foliage")):
            material.name = "MI_Polygonal_Pine"
        elif "wood" in lower_name:
            material.name = "Wood"


def rebuild_surface_normals(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if obj.data.has_custom_normals:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.update()


def connected_components(mesh):
    adjacency = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)

    component_of = [-1] * len(mesh.vertices)
    components = []
    for root in range(len(mesh.vertices)):
        if component_of[root] >= 0:
            continue
        component_index = len(components)
        queue = deque([root])
        component_of[root] = component_index
        vertices = []
        while queue:
            current = queue.popleft()
            vertices.append(current)
            for neighbor in adjacency[current]:
                if component_of[neighbor] < 0:
                    component_of[neighbor] = component_index
                    queue.append(neighbor)
        components.append(vertices)

    component_materials = [set() for _ in components]
    for polygon in mesh.polygons:
        component_materials[component_of[polygon.vertices[0]]].add(polygon.material_index)

    return [
        vertices
        for index, vertices in enumerate(components)
        if component_materials[index] == {0}
    ]


def transform_foliage(mesh, settings, seed):
    components = connected_components(mesh)
    centers = []
    for component in components:
        center = sum((mesh.vertices[index].co for index in component), Vector()) / len(component)
        centers.append(center)

    leaf_base = min(center.z for center in centers)
    leaf_top = max(center.z for center in centers)
    leaf_range = max(leaf_top - leaf_base, 1.0)
    rng = random.Random(seed)

    for component, center in zip(components, centers):
        normalized_height = max(0.0, min(1.0, (center.z - leaf_base) / leaf_range))
        radial = settings["radial"]
        if settings.get("layered"):
            radial *= 0.92 + 0.14 * math.sin(normalized_height * math.pi * 7.0)
        if settings.get("asymmetry"):
            direction = math.atan2(center.y, center.x)
            radial *= 1.0 + 0.10 * math.cos(direction - 0.65)

        new_center = Vector(
            (
                center.x * radial + settings["lean_x"] * normalized_height**1.55,
                center.y * radial + settings["lean_y"] * normalized_height**1.55,
                leaf_base + (center.z - leaf_base) * settings["height"],
            )
        )

        random_yaw = math.radians(rng.uniform(-settings["twist"], settings["twist"]))
        yaw_matrix = Matrix.Rotation(random_yaw, 4, "Z")
        individual_scale = rng.uniform(0.94, 1.06)

        for vertex_index in component:
            local = mesh.vertices[vertex_index].co - center
            local = yaw_matrix @ local
            local.x *= settings["cluster_xy"] * individual_scale
            local.y *= settings["cluster_xy"] * individual_scale
            local.z *= settings["cluster_z"] * individual_scale
            mesh.vertices[vertex_index].co = new_center + local

    mesh.update()
    return len(components)


def export_variant(settings, variant_index):
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=SOURCE_FBX)

    tree = bpy.data.objects.get("SM_Tree_004")
    collision = bpy.data.objects.get("UCX_SM_Tree_004")
    if tree is None or tree.type != "MESH":
        raise RuntimeError("SM_Tree_004 mesh was not found after FBX import")
    if collision is None or collision.type != "MESH":
        raise RuntimeError("UCX_SM_Tree_004 collision mesh was not found after FBX import")

    canonicalize_material_names(tree.data)
    cluster_count = transform_foliage(tree.data, settings, 4400 + variant_index)
    rebuild_surface_normals(tree)
    rebuild_surface_normals(collision)
    asset_name = f"SM_Tree_004_{settings['suffix']}"
    tree.name = asset_name
    tree.data.name = asset_name
    collision.name = f"UCX_{asset_name}"
    collision.data.name = f"UCX_{asset_name}"

    bpy.ops.object.select_all(action="DESELECT")
    tree.select_set(True)
    collision.select_set(True)
    bpy.context.view_layer.objects.active = tree

    output_path = os.path.join(OUTPUT_DIR, asset_name + ".fbx")
    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=False,
        bake_space_transform=False,
        add_leaf_bones=False,
        axis_forward="-Y",
        axis_up="Z",
        path_mode="AUTO",
    )
    print(f"EXPORTED {output_path} foliage_clusters={cluster_count}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for index, settings in enumerate(VARIANTS):
        export_variant(settings, index)
    print(f"GENERATED_VARIANTS count={len(VARIANTS)} directory={OUTPUT_DIR}")


main()
