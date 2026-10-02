import bpy
import glob
import os
from collections import Counter, deque


SOURCE_DIR = r"C:\Users\ryant\OneDrive\Desktop\TreeRAW"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def component_summary(mesh):
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
        index = len(components)
        queue = deque([root])
        component_of[root] = index
        vertices = []
        while queue:
            current = queue.popleft()
            vertices.append(current)
            for neighbor in adjacency[current]:
                if component_of[neighbor] < 0:
                    component_of[neighbor] = index
                    queue.append(neighbor)
        components.append(vertices)

    materials = [Counter() for _ in components]
    polygon_counts = Counter()
    for polygon in mesh.polygons:
        index = component_of[polygon.vertices[0]]
        polygon_counts[index] += 1
        materials[index][polygon.material_index] += 1
    return components, materials, polygon_counts


for source_path in sorted(glob.glob(os.path.join(SOURCE_DIR, "*.FBX"))):
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=source_path)
    print(f"TREE {os.path.basename(source_path)}")
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        components, materials, polygon_counts = component_summary(mesh)
        material_names = [material.name if material else None for material in mesh.materials]
        material_component_counts = Counter()
        for counts in materials:
            if counts:
                material_component_counts[counts.most_common(1)[0][0]] += 1
        print(
            f"  OBJECT {obj.name} verts={len(mesh.vertices)} polygons={len(mesh.polygons)} "
            f"components={len(components)} materials={material_names} "
            f"components_by_material={dict(material_component_counts)} "
            f"uvs={[layer.name for layer in mesh.uv_layers]} "
            f"colors={[attribute.name for attribute in mesh.color_attributes]}"
        )
