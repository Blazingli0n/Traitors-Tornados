import bpy
import glob
import math
import os
import random
from collections import Counter, deque

import numpy as np
from mathutils import Matrix, Vector


SOURCE_DIR = r"C:\Users\ryant\OneDrive\Desktop\TreeRAW"
OUTPUT_DIR = r"C:\Users\ryant\OneDrive\Desktop\TreeDistinct"


RECIPES = {
    "SM_Tree_001": (
        {
            "suffix": "AlpineSpire",
            "profile": "spire",
            "height": 1.13,
            "lean": (18.0, -8.0),
            "leaf_axes": (1.16, 0.66, 0.72),
            "twist": 18.0,
        },
        {
            "suffix": "HighCrown",
            "profile": "high_crown",
            "height": 1.02,
            "lean": (-20.0, 28.0),
            "leaf_axes": (0.94, 1.08, 0.82),
            "twist": 24.0,
        },
    ),
    "SM_Tree_002": (
        {
            "suffix": "WindBent",
            "profile": "windswept",
            "height": 0.96,
            "lean": (185.0, -42.0),
            "leaf_axes": (1.12, 0.70, 0.72),
            "twist": 28.0,
        },
        {
            "suffix": "DeepTiered",
            "profile": "tiered",
            "height": 1.06,
            "lean": (-12.0, 7.0),
            "leaf_axes": (1.08, 0.78, 0.75),
            "twist": 20.0,
        },
    ),
    "SM_Tree_003": (
        {
            "suffix": "BroadAncient",
            "profile": "broad",
            "height": 0.84,
            "lean": (24.0, 18.0),
            "leaf_axes": (0.90, 1.25, 0.86),
            "twist": 22.0,
        },
        {
            "suffix": "StormCrown",
            "profile": "broken_crown",
            "height": 0.94,
            "lean": (-125.0, 62.0),
            "leaf_axes": (1.14, 0.68, 0.70),
            "twist": 32.0,
        },
    ),
    "SM_Tree_004": (
        {
            "suffix": "NeedleColumn",
            "profile": "column",
            "height": 1.10,
            "lean": (8.0, -5.0),
            "leaf_axes": (1.28, 0.52, 0.62),
            "twist": 26.0,
        },
        {
            "suffix": "WildAsymmetric",
            "profile": "asymmetric",
            "height": 0.98,
            "lean": (72.0, 105.0),
            "leaf_axes": (1.04, 0.82, 0.78),
            "twist": 38.0,
        },
    ),
}


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

    component_materials = [Counter() for _ in components]
    for polygon in mesh.polygons:
        component_materials[component_of[polygon.vertices[0]]][polygon.material_index] += 1
    return components, component_materials


def find_foliage_material_index(mesh):
    for index, material in enumerate(mesh.materials):
        if material and any(token in material.name.lower() for token in ("pine", "leaf", "foliage")):
            return index
    raise RuntimeError(f"Could not identify foliage material on {mesh.name}")


def foliage_components(mesh):
    foliage_index = find_foliage_material_index(mesh)
    components, component_materials = connected_components(mesh)
    return [
        component
        for component, materials in zip(components, component_materials)
        if materials and materials.most_common(1)[0][0] == foliage_index
    ]


def overall_bounds(mesh):
    minimum_z = min(vertex.co.z for vertex in mesh.vertices)
    maximum_z = max(vertex.co.z for vertex in mesh.vertices)
    return minimum_z, maximum_z, max(maximum_z - minimum_z, 1.0)


def bend_tree(mesh, height_scale, lean):
    minimum_z, _, height = overall_bounds(mesh)
    for vertex in mesh.vertices:
        t = max(0.0, min(1.0, (vertex.co.z - minimum_z) / height))
        vertex.co.x += lean[0] * t**1.7
        vertex.co.y += lean[1] * t**1.7
        vertex.co.z = minimum_z + (vertex.co.z - minimum_z) * height_scale
    mesh.update()


def rebuild_surface_normals(obj):
    # FBX brings in custom corner normals. Once foliage islands are rotated or
    # non-uniformly reshaped, those stored normals no longer match the faces.
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


def profile_values(profile, t, angle):
    radial = 1.0
    size = 1.0
    z_shift = 0.0
    side_x = 0.0
    side_y = 0.0

    if profile == "spire":
        radial = 0.56 + 0.26 * (1.0 - t)
        size = 0.78 + 0.10 * (1.0 - t)
    elif profile == "high_crown":
        if t < 0.38:
            radial = 0.35
            size = 0.28 + t * 0.55
            z_shift = 0.07
        else:
            radial = 1.02 + 0.16 * math.sin((t - 0.38) / 0.62 * math.pi)
            size = 0.98
    elif profile == "windswept":
        radial = 0.78 + 0.12 * math.sin(t * math.pi)
        size = 0.88
        side_x = 0.10 * t
        side_y = -0.035 * t
    elif profile == "tiered":
        radial = 0.78 + 0.27 * (0.5 + 0.5 * math.sin(t * math.pi * 8.0))
        size = 0.84 + 0.10 * (0.5 + 0.5 * math.sin(t * math.pi * 8.0))
    elif profile == "broad":
        radial = 1.22 + 0.24 * math.sin(t * math.pi)
        size = 1.04 + 0.12 * (1.0 - t)
    elif profile == "broken_crown":
        radial = 0.92 + 0.12 * math.sin(t * math.pi)
        size = 0.92 if t < 0.76 else 0.48
        if t > 0.76:
            side_x = -0.11 * (t - 0.76) / 0.24
            side_y = 0.06 * (t - 0.76) / 0.24
            z_shift = -0.08 * (t - 0.76) / 0.24
    elif profile == "column":
        radial = 0.54 + 0.10 * math.sin(t * math.pi)
        size = 0.72
    elif profile == "asymmetric":
        radial = 0.88 + 0.20 * math.cos(angle - 0.55)
        size = 0.90 + 0.08 * math.cos(angle + 0.8)
        side_x = 0.06 * t
        side_y = 0.09 * t

    return radial, size, z_shift, side_x, side_y


def reshape_cluster(mesh, indices, center, axes_scale, size, random_yaw):
    coordinates = np.array([mesh.vertices[index].co[:] for index in indices], dtype=float)
    centered = coordinates - np.mean(coordinates, axis=0)
    covariance = np.cov(centered.T) if len(indices) > 2 else np.eye(3)
    _, eigenvectors = np.linalg.eigh(covariance)
    eigenvectors = eigenvectors[:, ::-1]
    scale_matrix = eigenvectors @ np.diag(axes_scale) @ eigenvectors.T
    yaw = Matrix.Rotation(math.radians(random_yaw), 4, "Z")

    for index in indices:
        local = mesh.vertices[index].co - center
        transformed = Vector(scale_matrix @ np.array(local[:], dtype=float)) * size
        mesh.vertices[index].co = center + yaw @ transformed


def reshape_foliage(mesh, recipe, seed):
    components = foliage_components(mesh)
    centers = [
        sum((mesh.vertices[index].co for index in component), Vector()) / len(component)
        for component in components
    ]
    leaf_min = min(center.z for center in centers)
    leaf_max = max(center.z for center in centers)
    leaf_height = max(leaf_max - leaf_min, 1.0)
    rng = random.Random(seed)

    for component, old_center in zip(components, centers):
        t = max(0.0, min(1.0, (old_center.z - leaf_min) / leaf_height))
        angle = math.atan2(old_center.y, old_center.x)
        radial, size, z_shift, side_x, side_y = profile_values(recipe["profile"], t, angle)
        new_center = Vector(
            (
                old_center.x * radial + side_x * leaf_height,
                old_center.y * radial + side_y * leaf_height,
                old_center.z + z_shift * leaf_height,
            )
        )
        delta = new_center - old_center
        for index in component:
            mesh.vertices[index].co += delta
        reshape_cluster(
            mesh,
            component,
            new_center,
            recipe["leaf_axes"],
            size * rng.uniform(0.90, 1.10),
            rng.uniform(-recipe["twist"], recipe["twist"]),
        )
    mesh.update()
    return len(components)


def export_variant(source_path, source_name, recipe, variant_index):
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=source_path)
    tree = bpy.data.objects.get(source_name)
    collision = bpy.data.objects.get(f"UCX_{source_name}")
    if tree is None or tree.type != "MESH":
        raise RuntimeError(f"Missing tree mesh {source_name}")
    if collision is None or collision.type != "MESH":
        raise RuntimeError(f"Missing collision mesh UCX_{source_name}")

    canonicalize_material_names(tree.data)
    bend_tree(tree.data, recipe["height"], recipe["lean"])
    # Keep collision conservative: resize vertically and apply half the visual lean.
    bend_tree(
        collision.data,
        recipe["height"],
        (recipe["lean"][0] * 0.50, recipe["lean"][1] * 0.50),
    )
    cluster_count = reshape_foliage(tree.data, recipe, 9100 + variant_index)
    rebuild_surface_normals(tree)
    rebuild_surface_normals(collision)

    asset_name = f"{source_name}_{recipe['suffix']}"
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
    variant_index = 0
    for source_path in sorted(glob.glob(os.path.join(SOURCE_DIR, "*.FBX"))):
        source_name = os.path.splitext(os.path.basename(source_path))[0]
        if source_name not in RECIPES:
            continue
        for recipe in RECIPES[source_name]:
            export_variant(source_path, source_name, recipe, variant_index)
            variant_index += 1
    print(f"GENERATED_DISTINCT_TREE_FAMILY count={variant_index} directory={OUTPUT_DIR}")


main()
