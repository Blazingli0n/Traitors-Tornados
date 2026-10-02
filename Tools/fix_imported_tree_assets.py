import unreal


TARGET_FOLDER = "/Game/Levels/FirstPerson"
SOURCE_FOLDER = "/Game/Building/Meshes/Environment/Polygonal/Foliage"


def slot_kind(slot):
    names = (
        str(slot.get_editor_property("material_slot_name")),
        str(slot.get_editor_property("imported_material_slot_name")),
    )
    combined = " ".join(names).lower()
    if any(token in combined for token in ("wood", "trunk", "bark")):
        return "wood"
    if any(token in combined for token in ("pine", "leaf", "foliage")):
        return "foliage"
    return "other"


def base_tree_for_variant(name):
    for index in range(1, 5):
        prefix = f"SM_Tree_{index:03d}"
        if name.startswith(prefix):
            return unreal.EditorAssetLibrary.load_asset(f"{SOURCE_FOLDER}/{prefix}")
    return None


subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
fixed = []

for asset_path in unreal.EditorAssetLibrary.list_assets(TARGET_FOLDER, recursive=True, include_folder=False):
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(asset, unreal.StaticMesh) or not asset.get_name().startswith("SM_Tree_"):
        continue

    base_tree = base_tree_for_variant(asset.get_name())
    if not base_tree:
        unreal.log_warning(f"Skipping {asset.get_path_name()}: no matching source tree")
        continue

    source_materials = {}
    for source_slot in base_tree.get_editor_property("static_materials"):
        kind = slot_kind(source_slot)
        material = source_slot.get_editor_property("material_interface")
        if kind != "other" and material:
            source_materials[kind] = material

    for slot_index, target_slot in enumerate(asset.get_editor_property("static_materials")):
        kind = slot_kind(target_slot)
        material = source_materials.get(kind)
        if material:
            asset.set_material(slot_index, material)
            unreal.log_warning(
                f"ASSIGN {asset.get_name()} slot={slot_index} kind={kind} "
                f"material={material.get_path_name()}"
            )

    # Match the source pack's build behavior. In particular, preserve imported
    # card normals instead of generating weighted normals across thin foliage.
    source_build_settings = subsystem.get_lod_build_settings(base_tree, 0)
    subsystem.set_lod_build_settings(asset, 0, source_build_settings)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    fixed.append(asset.get_path_name())

unreal.log_warning(f"FIXED_IMPORTED_TREES count={len(fixed)} assets={fixed}")
