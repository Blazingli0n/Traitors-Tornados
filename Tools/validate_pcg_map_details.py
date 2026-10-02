import unreal


GRAPH_PATH = "/Game/Levels/PCG_MapDetails"


graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
if not graph or not isinstance(graph, unreal.PCGGraph):
    raise RuntimeError(f"Missing PCG graph: {GRAPH_PATH}")

nodes = list(graph.get_editor_property("nodes"))
edges = list(graph.get_all_edges())

expected_counts = {
    "PCGGetLandscapeSettings": 1,
    "PCGSurfaceSamplerSettings": 4,
    "PCGNormalToDensitySettings": 4,
    "PCGDensityFilterSettings": 4,
    "PCGTransformPointsSettings": 4,
    "PCGStaticMeshSpawnerSettings": 4,
}

actual_counts = {}
spawners = []
for node in nodes:
    settings = node.get_settings()
    class_name = settings.get_class().get_name()
    actual_counts[class_name] = actual_counts.get(class_name, 0) + 1
    if isinstance(settings, unreal.PCGStaticMeshSpawnerSettings):
        spawners.append(settings)

for class_name, expected in expected_counts.items():
    actual = actual_counts.get(class_name, 0)
    if actual != expected:
        raise RuntimeError(f"Expected {expected} {class_name} nodes, found {actual}")

if len(nodes) != 21:
    raise RuntimeError(f"Expected 21 generated PCG nodes, found {len(nodes)}")
if len(edges) != 24:
    raise RuntimeError(f"Expected 24 PCG connections, found {len(edges)}")

mesh_paths = []
for spawner in spawners:
    selector = spawner.get_editor_property("mesh_selector_parameters")
    if not isinstance(selector, unreal.PCGMeshSelectorWeighted):
        raise RuntimeError("Static Mesh Spawner is not using the weighted selector")
    for entry in selector.get_editor_property("mesh_entries"):
        descriptor = entry.get_editor_property("descriptor")
        mesh = descriptor.get_editor_property("static_mesh")
        if not mesh:
            raise RuntimeError("PCG mesh entry has no Static Mesh")
        mesh_paths.append(str(mesh))

if len(mesh_paths) != 13:
    raise RuntimeError(f"Expected 13 weighted mesh entries, found {len(mesh_paths)}")

referencers = list(
    unreal.EditorAssetLibrary.find_package_referencers_for_asset(
        GRAPH_PATH,
        load_assets_to_confirm=True,
    )
)
unreal.log_warning(f"PCG_VALIDATE: Referencers={referencers}")
if not any("FirstPerson" in path for path in referencers):
    raise RuntimeError("The saved FirstPerson PCG Volume does not reference PCG_MapDetails")

unreal.log_warning(f"PCG_VALIDATE: Nodes={len(nodes)}")
unreal.log_warning(f"PCG_VALIDATE: Edges={len(edges)}")
unreal.log_warning(f"PCG_VALIDATE: MeshEntries={len(mesh_paths)}")
unreal.log_warning("PCG_VALIDATE: Passes=Trees,Rocks,Ferns,Wildflowers")
unreal.log_warning("PCG_VALIDATE: VolumeReference=Present")
