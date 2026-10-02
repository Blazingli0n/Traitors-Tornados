import unreal


MASTER_PATH = "/Game/Terrain/Materials/M_Terrain_Auto"
INSTANCE_PATH = "/Game/Building/Materials/Instances/Polygonal/MI_Polygonal_Landscape"


def require_asset(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"Missing required asset: {path}")
    return asset


master = require_asset(MASTER_PATH)
instance = require_asset(INSTANCE_PATH)

parent = instance.get_editor_property("parent")
if parent != master:
    raise RuntimeError(
        f"Landscape instance parent mismatch: {parent.get_path_name() if parent else 'None'}"
    )

expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(master))
if len(expressions) < 20:
    raise RuntimeError(f"Terrain material graph is unexpectedly small: {len(expressions)} nodes")

reported_layer_names = sorted(
    str(node.get_editor_property("parameter_name"))
    for node in expressions
    if isinstance(node, unreal.MaterialExpressionLandscapeLayerSample)
)
layer_names = sorted(set(reported_layer_names))
if layer_names != ["Dirt", "Grass", "WetDirt"]:
    raise RuntimeError(f"Unexpected Landscape target layers: {reported_layer_names}")

world_aligned_calls = [
    node
    for node in expressions
    if isinstance(node, unreal.MaterialExpressionMaterialFunctionCall)
    and node.get_editor_property("material_function")
    and "WorldAlignedTexture" in node.get_editor_property("material_function").get_path_name()
]
if not world_aligned_calls:
    raise RuntimeError("World-aligned rock projection is missing from the terrain material")

grass_outputs = [
    node
    for node in expressions
    if isinstance(node, unreal.MaterialExpressionLandscapeGrassOutput)
]
if len(grass_outputs) != 1:
    raise RuntimeError(f"Expected one Landscape Grass Output, found {len(grass_outputs)}")
grass_types = list(grass_outputs[0].get_editor_property("grass_types"))
if len(grass_types) != 1 or not grass_types[0].get_editor_property("grass_type"):
    raise RuntimeError("Landscape Grass Output is missing its grass type")

errors = list(unreal.MaterialEditingLibrary.recompile_material(master))
if errors:
    raise RuntimeError("Material compile errors: " + " | ".join(str(error) for error in errors))

unreal.log(f"TERRAIN_VALIDATE: Parent={parent.get_path_name()}")
unreal.log(f"TERRAIN_VALIDATE: Expressions={len(expressions)}")
unreal.log(f"TERRAIN_VALIDATE: TargetLayers={layer_names}")
unreal.log("TERRAIN_VALIDATE: WorldAlignedRock=Present")
unreal.log("TERRAIN_VALIDATE: LandscapeGrass=Present")
unreal.log("TERRAIN_VALIDATE: CompileErrors=0")
