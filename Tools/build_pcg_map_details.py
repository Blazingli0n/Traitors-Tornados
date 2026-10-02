import unreal


GRAPH_PATH = "/Game/Levels/PCG_MapDetails"


PASSES = (
    {
        "name": "Trees",
        "density": 0.00035,
        "extent": 500.0,
        "slope_min": 0.78,
        "slope_max": 1.0,
        "scale_min": 0.85,
        "scale_max": 1.25,
        "cull_start": 70000,
        "cull_end": 100000,
        "collision": True,
        "seed": 1041,
        "meshes": (
            ("/Game/Building/Meshes/Environment/Polygonal/Foliage/SM_Tree_001", 4),
            ("/Game/Building/Meshes/Environment/Polygonal/Foliage/SM_Tree_002", 3),
            ("/Game/Building/Meshes/Environment/Polygonal/Foliage/SM_Tree_003", 3),
            ("/Game/Building/Meshes/Environment/Polygonal/Foliage/SM_Tree_004", 2),
        ),
    },
    {
        "name": "Mountain Rocks",
        "density": 0.0006,
        "extent": 220.0,
        "slope_min": 0.25,
        "slope_max": 0.95,
        "scale_min": 0.65,
        "scale_max": 1.65,
        "cull_start": 55000,
        "cull_end": 80000,
        "collision": True,
        "seed": 2077,
        "meshes": (
            ("/Game/Building/Meshes/Environment/Polygonal/Organic/SM_SmallRock_001", 3),
            ("/Game/Building/Meshes/Environment/Polygonal/Organic/SM_SmallRock_002", 3),
            ("/Game/Building/Meshes/Environment/Polygonal/Organic/SM_SmallRock_003", 2),
            ("/Game/Building/Meshes/Environment/Polygonal/Organic/SM_SmallRock_004", 2),
            ("/Game/Building/Meshes/Environment/Polygonal/Organic/SM_SmallRock_005", 2),
            ("/Game/Building/Meshes/Environment/Polygonal/Organic/SM_SmallRock_006", 2),
        ),
    },
    {
        "name": "Ferns",
        "density": 0.0012,
        "extent": 130.0,
        "slope_min": 0.70,
        "slope_max": 1.0,
        "scale_min": 0.70,
        "scale_max": 1.35,
        "cull_start": 25000,
        "cull_end": 40000,
        "collision": False,
        "seed": 3019,
        "meshes": (
            ("/Game/Building/Meshes/Environment/Polygonal/Foliage/SM_Fern_001", 1),
        ),
    },
    {
        "name": "Wildflowers",
        "density": 0.0008,
        "extent": 100.0,
        "slope_min": 0.84,
        "slope_max": 1.0,
        "scale_min": 0.75,
        "scale_max": 1.25,
        "cull_start": 22000,
        "cull_end": 35000,
        "collision": False,
        "seed": 4093,
        "meshes": (
            ("/Game/Building/Meshes/Environment/Polygonal/Foliage/SM_Flowers_001", 3),
            ("/Game/Building/Meshes/Environment/Polygonal/Foliage/SM_Flowers_002", 2),
        ),
    },
)


def load_required(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"Required asset was not found: {path}")
    return asset


def set_prop(obj, name, value):
    obj.set_editor_property(name, value)
    return obj


def add_node(graph, settings_class, title, x, y):
    node, settings = graph.add_node_of_type(settings_class)
    if not node or not settings:
        raise RuntimeError(f"Could not create PCG node: {settings_class.__name__}")
    set_prop(node, "node_title", unreal.Name(title))
    node.set_node_position(x, y)
    return node, settings


def add_edge(graph, source, source_pin, target, target_pin):
    result = graph.add_edge(
        source,
        unreal.Name(source_pin),
        target,
        unreal.Name(target_pin),
    )
    if not result:
        raise RuntimeError(
            f"Could not connect {source.get_name()}[{source_pin}] to "
            f"{target.get_name()}[{target_pin}]"
        )


def weighted_mesh_entry(mesh_path, weight, pass_settings):
    entry = unreal.PCGMeshSelectorWeightedEntry()
    descriptor = entry.get_editor_property("descriptor")
    set_prop(descriptor, "static_mesh", load_required(mesh_path))
    set_prop(descriptor, "instance_start_cull_distance", pass_settings["cull_start"])
    set_prop(descriptor, "instance_end_cull_distance", pass_settings["cull_end"])
    set_prop(descriptor, "use_default_collision", pass_settings["collision"])
    set_prop(descriptor, "can_ever_affect_navigation", pass_settings["collision"])
    entry.set_editor_property("descriptor", descriptor)
    entry.set_editor_property("weight", weight)
    return entry


def configure_pass(graph, landscape_node, output_node, spec, index):
    y = -720 + index * 500

    sampler_node, sampler = add_node(
        graph,
        unreal.PCGSurfaceSamplerSettings,
        f"{spec['name']} Distribution",
        -850,
        y,
    )
    set_prop(sampler, "points_per_squared_meter", spec["density"])
    set_prop(sampler, "point_extents", unreal.Vector(spec["extent"], spec["extent"], 100.0))
    set_prop(sampler, "looseness", 1.0)
    set_prop(sampler, "seed", spec["seed"])

    normal_node, normal = add_node(
        graph,
        unreal.PCGNormalToDensitySettings,
        f"{spec['name']} Slope",
        -520,
        y,
    )
    set_prop(normal, "normal", unreal.Vector(0.0, 0.0, 1.0))
    set_prop(normal, "strength", 1.0)

    filter_node, density_filter = add_node(
        graph,
        unreal.PCGDensityFilterSettings,
        f"{spec['name']} Allowed Slopes",
        -200,
        y,
    )
    set_prop(density_filter, "lower_bound", spec["slope_min"])
    set_prop(density_filter, "upper_bound", spec["slope_max"])

    transform_node, transform = add_node(
        graph,
        unreal.PCGTransformPointsSettings,
        f"{spec['name']} Variation",
        120,
        y,
    )
    set_prop(transform, "rotation_min", unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
    set_prop(transform, "rotation_max", unreal.Rotator(pitch=0.0, yaw=360.0, roll=0.0))
    set_prop(transform, "scale_min", unreal.Vector(spec["scale_min"], spec["scale_min"], spec["scale_min"]))
    set_prop(transform, "scale_max", unreal.Vector(spec["scale_max"], spec["scale_max"], spec["scale_max"]))
    set_prop(transform, "uniform_scale", True)
    set_prop(transform, "seed", spec["seed"] + 31)

    spawner_node, spawner = add_node(
        graph,
        unreal.PCGStaticMeshSpawnerSettings,
        f"Spawn {spec['name']}",
        460,
        y,
    )
    selector = spawner.get_editor_property("mesh_selector_parameters")
    if not isinstance(selector, unreal.PCGMeshSelectorWeighted):
        spawner.set_mesh_selector_type(unreal.PCGMeshSelectorWeighted)
        selector = spawner.get_editor_property("mesh_selector_parameters")
    entries = [
        weighted_mesh_entry(mesh_path, weight, spec)
        for mesh_path, weight in spec["meshes"]
    ]
    set_prop(selector, "mesh_entries", entries)
    set_prop(spawner, "synchronous_load", True)
    set_prop(spawner, "seed", spec["seed"] + 73)

    add_edge(graph, landscape_node, "Out", sampler_node, "Surface")
    add_edge(graph, sampler_node, "Out", normal_node, "In")
    add_edge(graph, normal_node, "Out", filter_node, "In")
    add_edge(graph, filter_node, "Out", transform_node, "In")
    add_edge(graph, transform_node, "Out", spawner_node, "In")
    add_edge(graph, spawner_node, "Out", output_node, "Out")


def main():
    graph = load_required(GRAPH_PATH)
    if not isinstance(graph, unreal.PCGGraph):
        raise RuntimeError(f"Asset is not a PCG Graph: {GRAPH_PATH}")

    existing_nodes = list(graph.get_editor_property("nodes"))
    for existing_node in existing_nodes:
        graph.remove_node(existing_node)

    set_prop(
        graph,
        "description",
        "Procedural map detail: slope-aware trees, rocks, ferns, and wildflowers.",
    )

    landscape_node, landscape = add_node(
        graph,
        unreal.PCGGetLandscapeSettings,
        "Playable Landscape",
        -1220,
        0,
    )
    set_prop(landscape, "seed", 761)

    output_node = graph.get_output_node()
    output_node.set_node_position(820, 0)

    for index, spec in enumerate(PASSES):
        configure_pass(graph, landscape_node, output_node, spec, index)

    unreal.EditorAssetLibrary.save_loaded_asset(graph, only_if_is_dirty=False)
    unreal.log_warning(
        f"PCG_BUILD: Saved {GRAPH_PATH} with {len(graph.get_editor_property('nodes'))} generated nodes"
    )


try:
    main()
except Exception as exc:
    unreal.log_error(f"PCG_BUILD_FAILED: {exc}")
    raise
