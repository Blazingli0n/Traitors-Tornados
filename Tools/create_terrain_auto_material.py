import unreal


DEST_FOLDER = "/Game/Terrain/Materials"
MASTER_PATH = f"{DEST_FOLDER}/M_Terrain_Auto"
ACTIVE_INSTANCE_PATH = "/Game/Building/Materials/Instances/Polygonal/MI_Polygonal_Landscape"

GRASS_ALBEDO = "/Game/Building/Textures/Environment/S/Tiles/T_Tile_Grass_001_A"
GROUND_ALBEDO = "/Game/Building/Textures/Environment/S/Tiles/T_Tile_Ground_001_A"
ROCK_ALBEDO = "/Game/Building/Textures/Environment/S/Tiles/T_Tile_Rock_Cracked_001_A"
GROUND_NORMAL = "/Game/Building/Textures/Environment/S/Tiles/T_Tile_Ground_001_N"
WORLD_ALIGNED_TEXTURE = "/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture"
LANDSCAPE_GRASS_TYPE = "/Game/Building/FoliageType/Polygonal/LG_Grass_001"


def load_required(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"Required asset was not found: {path}")
    return asset


def set_prop(obj, name, value):
    obj.set_editor_property(name, value)
    return obj


def expression(material, cls, x, y, desc=""):
    node = unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)
    if not node:
        raise RuntimeError(f"Failed to create {cls.__name__}")
    if desc:
        node.set_editor_property("desc", desc)
    return node


def connect(source, output_name, target, input_name):
    if not unreal.MaterialEditingLibrary.connect_material_expressions(
        source, output_name, target, input_name
    ):
        raise RuntimeError(
            f"Failed connection: {source.get_class().get_name()}[{output_name}] -> "
            f"{target.get_class().get_name()}[{input_name}]"
        )


def scalar_parameter(material, name, default, x, y, group="Terrain Controls"):
    node = expression(material, unreal.MaterialExpressionScalarParameter, x, y, name)
    set_prop(node, "parameter_name", unreal.Name(name))
    set_prop(node, "default_value", float(default))
    set_prop(node, "group", unreal.Name(group))
    return node


def vector_parameter(material, name, color, x, y, group="Terrain Colors"):
    node = expression(material, unreal.MaterialExpressionVectorParameter, x, y, name)
    set_prop(node, "parameter_name", unreal.Name(name))
    set_prop(node, "default_value", unreal.LinearColor(*color))
    set_prop(node, "group", unreal.Name(group))
    return node


def texture_parameter(material, name, texture, coords, x, y, sampler_type=None):
    node = expression(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y, name)
    set_prop(node, "parameter_name", unreal.Name(name))
    set_prop(node, "texture", texture)
    set_prop(node, "group", unreal.Name("Terrain Textures"))
    if sampler_type is not None:
        set_prop(node, "sampler_type", sampler_type)
    connect(coords, "", node, "UVs")
    return node


def texture_object_parameter(material, name, texture, x, y):
    node = expression(material, unreal.MaterialExpressionTextureObjectParameter, x, y, name)
    set_prop(node, "parameter_name", unreal.Name(name))
    set_prop(node, "texture", texture)
    set_prop(node, "group", unreal.Name("Terrain Textures"))
    return node


def constant3(material, color, x, y, desc=""):
    node = expression(material, unreal.MaterialExpressionConstant3Vector, x, y, desc)
    set_prop(node, "constant", unreal.LinearColor(*color, 1.0))
    return node


def multiply(material, a, b, x, y, desc=""):
    node = expression(material, unreal.MaterialExpressionMultiply, x, y, desc)
    connect(a, "", node, "A")
    connect(b, "", node, "B")
    return node


def lerp(material, a, b, alpha, x, y, desc=""):
    node = expression(material, unreal.MaterialExpressionLinearInterpolate, x, y, desc)
    connect(a, "", node, "A")
    connect(b, "", node, "B")
    connect(alpha, "", node, "Alpha")
    return node


def build_master_material():
    unreal.EditorAssetLibrary.make_directory(DEST_FOLDER)

    material = (
        unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
        if unreal.EditorAssetLibrary.does_asset_exist(MASTER_PATH)
        else None
    )
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_Terrain_Auto",
            DEST_FOLDER,
            unreal.Material,
            unreal.MaterialFactoryNew(),
        )
    if not material:
        raise RuntimeError("Could not create the automatic terrain master material")

    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    material.set_editor_property("two_sided", False)

    coords = expression(
        material,
        unreal.MaterialExpressionLandscapeLayerCoords,
        -1800,
        -50,
        "Landscape UVs. Mapping Scale controls ground texture tiling.",
    )
    set_prop(coords, "mapping_scale", 3.0)

    grass_tex = texture_parameter(
        material, "Grass Texture", load_required(GRASS_ALBEDO), coords, -1500, -700
    )
    ground_tex = texture_parameter(
        material, "Dirt Texture", load_required(GROUND_ALBEDO), coords, -1500, -350
    )
    rock_tex = texture_object_parameter(
        material, "Rock Texture", load_required(ROCK_ALBEDO), -1800, 250
    )
    rock_world_size = vector_parameter(
        material,
        "Rock World Size",
        (700.0, 700.0, 700.0, 0.0),
        -1800,
        450,
        "Terrain Controls",
    )
    world_aligned_rock = expression(
        material,
        unreal.MaterialExpressionMaterialFunctionCall,
        -1450,
        250,
        "World-aligned cliff texture prevents vertical stretching",
    )
    set_prop(world_aligned_rock, "material_function", load_required(WORLD_ALIGNED_TEXTURE))
    connect(rock_tex, "", world_aligned_rock, "TextureObject")
    connect(rock_world_size, "", world_aligned_rock, "TextureSize")
    ground_normal = texture_parameter(
        material,
        "Ground Normal",
        load_required(GROUND_NORMAL),
        coords,
        -1500,
        850,
        unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    )

    grass_tint = vector_parameter(material, "Grass Tint", (0.38, 0.48, 0.22, 1.0), -1200, -750)
    dirt_tint = vector_parameter(material, "Dirt Tint", (0.50, 0.32, 0.18, 1.0), -1200, -350)
    wet_tint = vector_parameter(material, "Wet Dirt Tint", (0.20, 0.13, 0.08, 1.0), -1200, -50)
    rock_tint = vector_parameter(material, "Rock Tint", (0.48, 0.46, 0.43, 1.0), -1050, 250)

    grass_color = multiply(material, grass_tex, grass_tint, -900, -700, "Grass color")
    dirt_color = multiply(material, ground_tex, dirt_tint, -900, -350, "Dirt color")
    wet_color = multiply(material, ground_tex, wet_tint, -900, -50, "Wet shoreline color")
    rock_color = expression(material, unreal.MaterialExpressionMultiply, -750, 250, "World-aligned rock color")
    connect(world_aligned_rock, "XYZ Texture", rock_color, "A")
    connect(rock_tint, "", rock_color, "B")

    grass_weight = expression(
        material, unreal.MaterialExpressionLandscapeLayerSample, -900, -1000, "Grass paint weight"
    )
    set_prop(grass_weight, "parameter_name", unreal.Name("Grass"))
    set_prop(grass_weight, "preview_weight", 1.0)
    dirt_weight = expression(
        material, unreal.MaterialExpressionLandscapeLayerSample, -900, -900, "Dirt paint weight"
    )
    set_prop(dirt_weight, "parameter_name", unreal.Name("Dirt"))
    wet_weight = expression(
        material, unreal.MaterialExpressionLandscapeLayerSample, -900, -800, "WetDirt paint weight"
    )
    set_prop(wet_weight, "parameter_name", unreal.Name("WetDirt"))

    grass_dim_scalar = scalar_parameter(material, "Unpainted Grass Brightness", 0.78, -650, -1050)
    grass_dim = multiply(material, grass_color, grass_dim_scalar, -600, -700, "Unpainted grass base")
    painted_grass = lerp(
        material, grass_dim, grass_color, grass_weight, -350, -650, "Preserve the existing Grass target layer"
    )
    flat_dirt = lerp(material, painted_grass, dirt_color, dirt_weight, -100, -450, "Painted dirt")
    flat_surface = lerp(material, flat_dirt, wet_color, wet_weight, 150, -300, "Painted wet dirt")

    normal_ws = expression(
        material, unreal.MaterialExpressionVertexNormalWS, -900, 550, "Landscape world-space normal"
    )
    normal_z = expression(material, unreal.MaterialExpressionComponentMask, -650, 550, "Up-facing amount")
    set_prop(normal_z, "r", False)
    set_prop(normal_z, "g", False)
    set_prop(normal_z, "b", True)
    set_prop(normal_z, "a", False)
    connect(normal_ws, "", normal_z, "")

    slope_amount = expression(
        material, unreal.MaterialExpressionOneMinus, -400, 550, "0 on flat ground, 1 on vertical cliffs"
    )
    connect(normal_z, "", slope_amount, "")

    slope_start = scalar_parameter(material, "Rock Slope Start", 0.22, -400, 700)
    slope_end = scalar_parameter(material, "Rock Slope End", 0.52, -400, 800)
    slope_mask = expression(
        material, unreal.MaterialExpressionSmoothStep, -100, 550, "Smooth automatic grass-to-rock slope mask"
    )
    connect(slope_start, "", slope_mask, "Min")
    connect(slope_end, "", slope_mask, "Max")
    connect(slope_amount, "", slope_mask, "Value")

    non_rock_mask = expression(
        material,
        unreal.MaterialExpressionOneMinus,
        150,
        650,
        "Prevent procedural grass from spawning on steep rock",
    )
    connect(slope_mask, "", non_rock_mask, "")
    grass_spawn_mask = multiply(
        material,
        grass_weight,
        non_rock_mask,
        400,
        650,
        "Painted Grass layer, restricted to buildable and rolling terrain",
    )
    grass_output = expression(
        material,
        unreal.MaterialExpressionLandscapeGrassOutput,
        700,
        650,
        "Restore the original procedural landscape grass",
    )
    grass_input = unreal.GrassInput()
    grass_input.set_editor_property("name", unreal.Name("Grass"))
    grass_input.set_editor_property("grass_type", load_required(LANDSCAPE_GRASS_TYPE))
    set_prop(grass_output, "grass_types", [grass_input])
    connect(grass_spawn_mask, "", grass_output, "Grass")

    final_color = lerp(
        material, flat_surface, rock_color, slope_mask, 450, -50, "Automatic steep-slope rock override"
    )
    flat_cliff_normal = constant3(material, (0.0, 0.0, 1.0), 150, 950, "Clean tangent-space cliff normal")
    final_normal = lerp(
        material,
        ground_normal,
        flat_cliff_normal,
        slope_mask,
        450,
        850,
        "Keep ground detail without stretching a top-down normal map across cliffs",
    )
    roughness = scalar_parameter(material, "Terrain Roughness", 0.86, 450, 1100)

    if not unreal.MaterialEditingLibrary.connect_material_property(
        final_color, "", unreal.MaterialProperty.MP_BASE_COLOR
    ):
        raise RuntimeError("Failed to connect Base Color")
    if not unreal.MaterialEditingLibrary.connect_material_property(
        final_normal, "", unreal.MaterialProperty.MP_NORMAL
    ):
        raise RuntimeError("Failed to connect Normal")
    if not unreal.MaterialEditingLibrary.connect_material_property(
        roughness, "", unreal.MaterialProperty.MP_ROUGHNESS
    ):
        raise RuntimeError("Failed to connect Roughness")

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    errors = list(unreal.MaterialEditingLibrary.recompile_material(material))
    if errors:
        raise RuntimeError("Material compile errors: " + " | ".join(str(error) for error in errors))
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def reparent_active_instance(material):
    instance = load_required(ACTIVE_INSTANCE_PATH)
    if not isinstance(instance, unreal.MaterialInstanceConstant):
        raise RuntimeError("The assigned Landscape material is not a MaterialInstanceConstant")

    unreal.MaterialEditingLibrary.clear_all_material_instance_parameters(instance)
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, material)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, unreal.Name("Rock Slope Start"), 0.22
    )
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, unreal.Name("Rock Slope End"), 0.52
    )
    unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


def main():
    unreal.log("TERRAIN_AUTO: Creating an independent automatic terrain material")
    material = build_master_material()
    instance = reparent_active_instance(material)
    unreal.log(f"TERRAIN_AUTO: Master material ready: {material.get_path_name()}")
    unreal.log(f"TERRAIN_AUTO: Assigned instance repaired: {instance.get_path_name()}")
    unreal.log("TERRAIN_AUTO: The original MM_Polygonal_Landscape master remains untouched")


try:
    main()
except Exception as exc:
    unreal.log_error(f"TERRAIN_AUTO_FAILED: {exc}")
    raise
