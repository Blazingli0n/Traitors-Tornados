import os
import unreal


ASSET_FOLDER = "/Game/Levels/FirstPerson"
SOURCE_FOLDER = r"C:\Users\ryant\OneDrive\Desktop\TreeDistinct"
TREE_NAMES = (
    "SM_Tree_001_AlpineSpire",
    "SM_Tree_001_HighCrown",
)


results = []
tasks = []
for tree_name in TREE_NAMES:
    asset_path = f"{ASSET_FOLDER}/{tree_name}"
    source_path = os.path.join(SOURCE_FOLDER, tree_name + ".fbx")
    tree = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not tree:
        unreal.log_warning(f"REIMPORT_SKIP missing_asset={asset_path}")
        continue
    if not os.path.isfile(source_path):
        unreal.log_warning(f"REIMPORT_SKIP missing_source={source_path}")
        continue

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    static_options = options.get_editor_property("static_mesh_import_data")
    static_options.set_editor_property("combine_meshes", False)
    static_options.set_editor_property(
        "normal_import_method",
        unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS,
    )
    static_options.set_editor_property("auto_generate_collision", False)
    static_options.set_editor_property("generate_lightmap_u_vs", True)

    task = unreal.AssetImportTask()
    task.set_editor_property("automated", True)
    task.set_editor_property("destination_name", tree_name)
    task.set_editor_property("destination_path", ASSET_FOLDER)
    task.set_editor_property("filename", source_path)
    task.set_editor_property("options", options)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("save", True)
    tasks.append(task)

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for task in tasks:
    imported_paths = list(task.get_editor_property("imported_object_paths"))
    success = bool(imported_paths)
    unreal.log_warning(
        f"REIMPORT_TREE source={task.get_editor_property('filename')} "
        f"imported={imported_paths} success={success}"
    )
    results.append((task.get_editor_property("destination_name"), success))

unreal.log_warning(f"REIMPORT_CORRECTED_TREES results={results}")
