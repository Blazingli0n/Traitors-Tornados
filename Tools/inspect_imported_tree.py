import unreal


TREE_PATHS = (
    "/Game/Levels/FirstPerson/SM_Tree_001_AlpineSpire",
    "/Game/Levels/FirstPerson/SM_Tree_001_HighCrown",
    "/Game/Building/Meshes/Environment/Polygonal/Foliage/SM_Tree_001",
)
MATERIAL_PATHS = (
    "/Game/Levels/FirstPerson/MI_Polygonal_Pine",
    "/Game/Levels/FirstPerson/MI_Polygonal_Pine_TwoSided",
    "/Game/Building/Materials/Instances/Polygonal/MI_Polygonal_Pine",
)


for tree_path in TREE_PATHS:
    tree = unreal.EditorAssetLibrary.load_asset(tree_path)
    unreal.log_warning(f"TREE path={tree.get_path_name()} class={tree.get_class().get_name()}")
    for index, slot in enumerate(tree.get_editor_property("static_materials")):
        material = slot.get_editor_property("material_interface")
        unreal.log_warning(
            f"TREE_SLOT index={index} slot={slot.get_editor_property('material_slot_name')} "
            f"imported={slot.get_editor_property('imported_material_slot_name')} "
            f"material={material.get_path_name() if material else None}"
        )

    try:
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        build_settings = subsystem.get_lod_build_settings(tree, 0)
        unreal.log_warning(f"TREE_LOD0_BUILD_SETTINGS={build_settings}")
    except Exception as error:
        unreal.log_warning(f"TREE_LOD0_BUILD_SETTINGS unavailable: {error}")

for path in MATERIAL_PATHS:
    material = unreal.EditorAssetLibrary.load_asset(path)
    if not material:
        unreal.log_warning(f"MATERIAL missing path={path}")
        continue
    unreal.log_warning(
        f"MATERIAL path={path} class={material.get_class().get_name()}"
    )
    try:
        parent = material.get_editor_property("parent")
        unreal.log_warning(f"  parent={parent.get_path_name() if parent else None}")
    except Exception as error:
        unreal.log_warning(f"  parent unavailable: {error}")
    try:
        unreal.log_warning(
            f"  base_property_overrides={material.get_editor_property('base_property_overrides')}"
        )
    except Exception as error:
        unreal.log_warning(f"  base_property_overrides unavailable: {error}")
