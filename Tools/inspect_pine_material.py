import unreal


INSTANCE_PATH = "/Game/Building/Materials/Instances/Polygonal/MI_Polygonal_Pine"


def describe_asset(asset, label):
    if not asset:
        unreal.log_warning(f"{label}: NONE")
        return
    unreal.log_warning(
        f"{label}: path={asset.get_path_name()} class={asset.get_class().get_name()}"
    )
    for property_name in (
        "parent",
        "two_sided",
        "shading_model",
        "tangent_space_normal",
        "use_material_attributes",
        "blend_mode",
    ):
        try:
            value = asset.get_editor_property(property_name)
            unreal.log_warning(f"  {property_name}={value}")
        except Exception as error:
            unreal.log_warning(f"  {property_name}=<unavailable: {error}>")


instance = unreal.EditorAssetLibrary.load_asset(INSTANCE_PATH)
describe_asset(instance, "INSTANCE")
try:
    unreal.log_warning(
        f"INSTANCE_BASE_PROPERTY_OVERRIDES={instance.get_editor_property('base_property_overrides')}"
    )
except Exception as error:
    unreal.log_warning(f"INSTANCE_BASE_PROPERTY_OVERRIDES unavailable: {error}")

for getter_name in (
    "get_scalar_parameter_names",
    "get_vector_parameter_names",
    "get_texture_parameter_names",
    "get_static_switch_parameter_names",
):
    getter = getattr(unreal.MaterialEditingLibrary, getter_name, None)
    if getter:
        try:
            unreal.log_warning(f"INSTANCE_{getter_name}={getter(instance)}")
        except Exception as error:
            unreal.log_warning(f"INSTANCE_{getter_name} unavailable: {error}")

current = instance
for depth in range(8):
    try:
        parent = current.get_editor_property("parent")
    except Exception:
        break
    if not parent:
        break
    describe_asset(parent, f"PARENT_{depth + 1}")
    current = parent

if isinstance(current, unreal.Material):
    expressions = unreal.MaterialEditingLibrary.get_material_expressions(current)
    unreal.log_warning(f"ROOT_EXPRESSIONS count={len(expressions)}")
    for expression in expressions:
        unreal.log_warning(
            f"  EXPR class={expression.get_class().get_name()} name={expression.get_name()}"
        )
