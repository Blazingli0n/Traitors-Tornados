import bpy
from collections import Counter, deque


FBX_PATH = r"C:\Users\ryant\OneDrive\Desktop\SM_Tree_004.FBX"


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

print("TREE_INSPECT_BEGIN")
for obj in bpy.context.scene.objects:
    print(f"OBJECT name={obj.name!r} type={obj.type}")
    if obj.type != "MESH":
        continue

    mesh = obj.data
    print(
        f"MESH vertices={len(mesh.vertices)} edges={len(mesh.edges)} "
        f"polygons={len(mesh.polygons)} loops={len(mesh.loops)}"
    )
    print("MATERIALS " + repr([slot.name if slot else None for slot in mesh.materials]))
    print("UV_LAYERS " + repr([layer.name for layer in mesh.uv_layers]))
    print(
        "COLOR_ATTRIBUTES "
        + repr([(attr.name, attr.domain, attr.data_type) for attr in mesh.color_attributes])
    )

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

    polygon_counts = Counter()
    material_counts = {index: Counter() for index in range(len(components))}
    for polygon in mesh.polygons:
        component_index = component_of[polygon.vertices[0]]
        polygon_counts[component_index] += 1
        material_counts[component_index][polygon.material_index] += 1

    summaries = []
    for component_index, vertices in enumerate(components):
        coords = [mesh.vertices[index].co for index in vertices]
        mins = tuple(min(co[axis] for co in coords) for axis in range(3))
        maxs = tuple(max(co[axis] for co in coords) for axis in range(3))
        center = tuple((mins[axis] + maxs[axis]) * 0.5 for axis in range(3))
        size = tuple(maxs[axis] - mins[axis] for axis in range(3))
        summaries.append(
            (
                component_index,
                len(vertices),
                polygon_counts[component_index],
                dict(material_counts[component_index]),
                center,
                size,
            )
        )

    print(f"CONNECTED_COMPONENTS count={len(summaries)}")
    for summary in sorted(summaries, key=lambda item: item[1], reverse=True):
        index, vertex_count, polygon_count, materials, center, size = summary
        print(
            f"COMPONENT index={index} vertices={vertex_count} polygons={polygon_count} "
            f"materials={materials} center={tuple(round(v, 3) for v in center)} "
            f"size={tuple(round(v, 3) for v in size)}"
        )
print("TREE_INSPECT_END")
