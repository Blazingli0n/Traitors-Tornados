import bpy
import math
import os
import random
from mathutils import Vector


OUTPUT_DIR = r"C:\Users\ryant\OneDrive\Desktop\OriginalTrees"
BLEND_PATH = os.path.join(OUTPUT_DIR, "OriginalTreeFamily.blend")


TREE_CONFIGS = (
    {
        "name": "SM_OriginalPine_Alpine",
        "seed": 1103,
        "height": 1500.0,
        "base_radius": 42.0,
        "tiers": 15,
        "branches": 5,
        "max_branch": 235.0,
        "clear": 0.15,
        "branch_rise": 0.06,
        "leaf_width": 34.0,
        "leaf_thickness": 9.0,
        "leaf_clusters": 3,
        "lean": (22.0, -12.0),
        "profile": "spire",
    },
    {
        "name": "SM_OriginalPine_Broad",
        "seed": 2207,
        "height": 1180.0,
        "base_radius": 58.0,
        "tiers": 12,
        "branches": 7,
        "max_branch": 350.0,
        "clear": 0.12,
        "branch_rise": -0.07,
        "leaf_width": 52.0,
        "leaf_thickness": 13.0,
        "leaf_clusters": 4,
        "lean": (-18.0, 14.0),
        "profile": "broad",
    },
    {
        "name": "SM_OriginalPine_Windswept",
        "seed": 3319,
        "height": 1360.0,
        "base_radius": 50.0,
        "tiers": 11,
        "branches": 5,
        "max_branch": 285.0,
        "clear": 0.21,
        "branch_rise": 0.01,
        "leaf_width": 38.0,
        "leaf_thickness": 10.0,
        "leaf_clusters": 3,
        "lean": (175.0, 46.0),
        "wind_bias": (0.85, 0.22),
        "profile": "windswept",
    },
    {
        "name": "SM_OriginalPine_Sapling",
        "seed": 4421,
        "height": 720.0,
        "base_radius": 25.0,
        "tiers": 8,
        "branches": 5,
        "max_branch": 155.0,
        "clear": 0.10,
        "branch_rise": 0.14,
        "leaf_width": 28.0,
        "leaf_thickness": 8.0,
        "leaf_clusters": 3,
        "lean": (10.0, 8.0),
        "profile": "sapling",
    },
    {
        "name": "SM_OriginalPine_OldGrowth",
        "seed": 5531,
        "height": 1670.0,
        "base_radius": 74.0,
        "tiers": 12,
        "branches": 7,
        "max_branch": 410.0,
        "clear": 0.30,
        "branch_rise": -0.13,
        "leaf_width": 50.0,
        "leaf_thickness": 14.0,
        "leaf_clusters": 4,
        "lean": (-30.0, -18.0),
        "profile": "old_growth",
    },
    {
        "name": "SM_OriginalPine_TwinPeak",
        "seed": 6647,
        "height": 1430.0,
        "base_radius": 55.0,
        "tiers": 13,
        "branches": 6,
        "max_branch": 300.0,
        "clear": 0.17,
        "branch_rise": 0.02,
        "leaf_width": 42.0,
        "leaf_thickness": 11.0,
        "leaf_clusters": 3,
        "lean": (34.0, 18.0),
        "profile": "twin",
        "twin_top": True,
    },
    {
        "name": "SM_OriginalPine_Sparse",
        "seed": 7753,
        "height": 1510.0,
        "base_radius": 47.0,
        "tiers": 9,
        "branches": 4,
        "max_branch": 315.0,
        "clear": 0.24,
        "branch_rise": -0.03,
        "leaf_width": 37.0,
        "leaf_thickness": 10.0,
        "leaf_clusters": 2,
        "lean": (-42.0, 55.0),
        "profile": "sparse",
    },
    {
        "name": "SM_OriginalPine_Compact",
        "seed": 8861,
        "height": 980.0,
        "base_radius": 49.0,
        "tiers": 14,
        "branches": 8,
        "max_branch": 255.0,
        "clear": 0.09,
        "branch_rise": 0.03,
        "leaf_width": 43.0,
        "leaf_thickness": 12.0,
        "leaf_clusters": 4,
        "lean": (8.0, -14.0),
        "profile": "compact",
    },
)


class MeshBuilder:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.face_materials = []
        self.colors = []

    def vertex(self, position, color):
        self.vertices.append(tuple(position))
        self.colors.append(color)
        return len(self.vertices) - 1

    def face(self, indices, material_index):
        self.faces.append(tuple(indices))
        self.face_materials.append(material_index)

    def tapered_segment(self, start, end, radius_start, radius_end, sides, material_index, color=(0, 0, 0, 1)):
        start = Vector(start)
        end = Vector(end)
        direction = (end - start).normalized()
        reference = Vector((0, 0, 1)) if abs(direction.z) < 0.90 else Vector((1, 0, 0))
        axis_u = direction.cross(reference).normalized()
        axis_v = direction.cross(axis_u).normalized()
        rings = []
        for center, radius in ((start, radius_start), (end, radius_end)):
            ring = []
            for side in range(sides):
                angle = math.tau * side / sides
                position = center + axis_u * math.cos(angle) * radius + axis_v * math.sin(angle) * radius
                ring.append(self.vertex(position, color))
            rings.append(ring)
        for side in range(sides):
            next_side = (side + 1) % sides
            self.face((rings[0][side], rings[0][next_side], rings[1][next_side], rings[1][side]), material_index)
        self.face(tuple(reversed(rings[0])), material_index)
        self.face(tuple(rings[1]), material_index)

    def curved_trunk(self, points, radii, sides=8):
        rings = []
        for center, radius in zip(points, radii):
            ring = []
            for side in range(sides):
                angle = math.tau * side / sides
                position = Vector(center) + Vector((math.cos(angle) * radius, math.sin(angle) * radius, 0))
                ring.append(self.vertex(position, (0, 0, 0, 1)))
            rings.append(ring)
        for ring_index in range(len(rings) - 1):
            for side in range(sides):
                next_side = (side + 1) % sides
                self.face(
                    (
                        rings[ring_index][side],
                        rings[ring_index][next_side],
                        rings[ring_index + 1][next_side],
                        rings[ring_index + 1][side],
                    ),
                    0,
                )
        self.face(tuple(reversed(rings[0])), 0)
        self.face(tuple(rings[-1]), 0)

    def leaf_spindle(self, start, end, width, thickness, wind_weight=1.0):
        start = Vector(start)
        end = Vector(end)
        direction = (end - start).normalized()
        reference = Vector((0, 0, 1)) if abs(direction.z) < 0.92 else Vector((1, 0, 0))
        axis_u = direction.cross(reference).normalized()
        axis_v = direction.cross(axis_u).normalized()
        middle = start.lerp(end, 0.56)
        start_index = self.vertex(start, (wind_weight * 0.20, 0, 0, 1))
        end_index = self.vertex(end, (wind_weight, 0, 0, 1))
        ring = [
            self.vertex(middle + axis_u * width, (wind_weight * 0.70, 0, 0, 1)),
            self.vertex(middle + axis_v * thickness, (wind_weight * 0.70, 0, 0, 1)),
            self.vertex(middle - axis_u * width, (wind_weight * 0.70, 0, 0, 1)),
            self.vertex(middle - axis_v * thickness, (wind_weight * 0.70, 0, 0, 1)),
        ]
        for index in range(4):
            next_index = (index + 1) % 4
            self.face((start_index, ring[next_index], ring[index]), 1)
            self.face((end_index, ring[index], ring[next_index]), 1)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(collection):
            if datablock.users == 0:
                collection.remove(datablock)


def material(name, color, roughness):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1.0)
    result.roughness = roughness
    return result


WOOD_MATERIAL = None
LEAF_MATERIAL = None


def trunk_center(config, z_fraction):
    x = config["lean"][0] * z_fraction**1.65
    y = config["lean"][1] * z_fraction**1.65
    x += math.sin(z_fraction * math.pi * 2.2 + config["seed"] * 0.01) * 7.0 * z_fraction
    y += math.cos(z_fraction * math.pi * 1.7 + config["seed"] * 0.02) * 5.0 * z_fraction
    return Vector((x, y, config["height"] * z_fraction))


def branch_profile(config, t):
    profile = config["profile"]
    base = max(0.08, math.sin(math.pi * min(1.0, max(0.0, (t - config["clear"]) / (1.0 - config["clear"])))) ** 0.72)
    if profile == "spire":
        return base * (1.00 - 0.18 * t)
    if profile == "broad":
        return base * (1.15 - 0.12 * t)
    if profile == "windswept":
        return base * 0.92
    if profile == "sapling":
        return base * (0.82 + 0.22 * t)
    if profile == "old_growth":
        return base * (1.20 - 0.25 * t)
    if profile == "twin":
        return base * 1.02
    if profile == "sparse":
        return base * (1.08 - 0.15 * t)
    if profile == "compact":
        return base * 1.08
    return base


def make_mesh_object(name, builder, include_materials=True):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(builder.vertices, [], builder.faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if include_materials:
        mesh.materials.append(WOOD_MATERIAL)
        mesh.materials.append(LEAF_MATERIAL)
        for polygon, material_index in zip(mesh.polygons, builder.face_materials):
            polygon.material_index = material_index
            polygon.use_smooth = material_index == 0
        color_attribute = mesh.color_attributes.new(name="Color", type="FLOAT_COLOR", domain="POINT")
        for index, color in enumerate(builder.colors):
            color_attribute.data[index].color = color
    return obj


def recalculate_normals(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.update()


def build_tree(config):
    rng = random.Random(config["seed"])
    builder = MeshBuilder()
    trunk_segments = 12
    trunk_points = [trunk_center(config, index / trunk_segments) for index in range(trunk_segments + 1)]
    trunk_radii = [
        max(3.0, config["base_radius"] * (1.0 - index / trunk_segments) ** 0.68)
        for index in range(trunk_segments + 1)
    ]
    builder.curved_trunk(trunk_points, trunk_radii, sides=8)

    tier_start = config["clear"]
    for tier in range(config["tiers"]):
        t = tier_start + (tier + 0.35) / config["tiers"] * (0.93 - tier_start)
        center = trunk_center(config, t)
        branch_length = config["max_branch"] * branch_profile(config, t) * rng.uniform(0.84, 1.12)
        branch_count = config["branches"] + (1 if tier % 3 == 0 and config["profile"] in ("broad", "compact") else 0)
        tier_angle = rng.uniform(0, math.tau)
        for branch_index in range(branch_count):
            angle = tier_angle + math.tau * branch_index / branch_count + rng.uniform(-0.14, 0.14)
            horizontal = Vector((math.cos(angle), math.sin(angle), 0))
            if "wind_bias" in config:
                bias = Vector((*config["wind_bias"], 0))
                horizontal = (horizontal * 0.58 + bias).normalized()
            rise = config["branch_rise"] + rng.uniform(-0.035, 0.035)
            end = center + horizontal * branch_length + Vector((0, 0, branch_length * rise))
            branch_radius = max(2.0, config["base_radius"] * 0.11 * (1.0 - t) ** 0.4)
            builder.tapered_segment(center, end, branch_radius, 1.4, 6, 0)

            cluster_count = config["leaf_clusters"]
            for cluster_index in range(cluster_count):
                along = 0.26 + (cluster_index + 0.35) / cluster_count * 0.72
                cluster_center = center.lerp(end, along)
                cluster_length = branch_length * rng.uniform(0.26, 0.38)
                spread_angle = rng.uniform(-0.22, 0.22)
                rotated = Vector(
                    (
                        horizontal.x * math.cos(spread_angle) - horizontal.y * math.sin(spread_angle),
                        horizontal.x * math.sin(spread_angle) + horizontal.y * math.cos(spread_angle),
                        rng.uniform(-0.04, 0.12),
                    )
                ).normalized()
                leaf_start = cluster_center - rotated * cluster_length * 0.38
                leaf_end = cluster_center + rotated * cluster_length * 0.62
                taper = 0.72 + 0.32 * (1.0 - t)
                builder.leaf_spindle(
                    leaf_start,
                    leaf_end,
                    config["leaf_width"] * taper * rng.uniform(0.82, 1.15),
                    config["leaf_thickness"] * rng.uniform(0.82, 1.18),
                    wind_weight=0.45 + 0.55 * t,
                )

            terminal_start = center.lerp(end, 0.73)
            terminal_end = end + horizontal * branch_length * 0.14
            builder.leaf_spindle(
                terminal_start,
                terminal_end,
                config["leaf_width"] * rng.uniform(0.80, 1.05),
                config["leaf_thickness"],
                wind_weight=0.55 + 0.45 * t,
            )

    top_start = trunk_center(config, 0.78)
    top_end = trunk_center(config, 1.0) + Vector((0, 0, config["height"] * 0.055))
    builder.leaf_spindle(
        top_start,
        top_end,
        config["leaf_width"] * 0.72,
        config["leaf_thickness"],
        wind_weight=1.0,
    )

    if config.get("twin_top"):
        split = trunk_center(config, 0.61)
        twin_direction = Vector((0.22, -0.12, 0.96)).normalized()
        twin_end = split + twin_direction * config["height"] * 0.43
        builder.tapered_segment(split, twin_end, config["base_radius"] * 0.18, 3.0, 7, 0)
        for step in range(5):
            p = (step + 1) / 6
            center = split.lerp(twin_end, p)
            angle = step * 2.1 + 0.6
            direction = Vector((math.cos(angle), math.sin(angle), 0.10)).normalized()
            builder.leaf_spindle(
                center - direction * 42.0,
                center + direction * (95.0 - step * 8.0),
                config["leaf_width"] * (0.90 - step * 0.08),
                config["leaf_thickness"],
                wind_weight=0.75 + step * 0.05,
            )

    tree = make_mesh_object(config["name"], builder, include_materials=True)
    recalculate_normals(tree)

    collision_builder = MeshBuilder()
    collision_start = trunk_center(config, 0.0)
    collision_end = trunk_center(config, 0.72)
    collision_builder.tapered_segment(
        collision_start,
        collision_end,
        config["base_radius"] * 1.08,
        max(8.0, config["base_radius"] * 0.38),
        10,
        0,
    )
    collision = make_mesh_object(f"UCX_{config['name']}", collision_builder, include_materials=False)
    recalculate_normals(collision)
    collision.display_type = "WIRE"
    collision.hide_render = True
    return tree, collision


def export_tree(tree, collision):
    bpy.ops.object.select_all(action="DESELECT")
    tree.select_set(True)
    collision.select_set(True)
    bpy.context.view_layer.objects.active = tree
    output_path = os.path.join(OUTPUT_DIR, tree.name + ".fbx")
    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=False,
        bake_space_transform=False,
        add_leaf_bones=False,
        axis_forward="-Y",
        axis_up="Z",
        path_mode="AUTO",
    )
    print(
        f"EXPORTED_ORIGINAL_TREE path={output_path} vertices={len(tree.data.vertices)} "
        f"polygons={len(tree.data.polygons)} materials={[m.name for m in tree.data.materials]}"
    )


def main():
    global WOOD_MATERIAL, LEAF_MATERIAL
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    clear_scene()
    WOOD_MATERIAL = material("Wood", (0.20, 0.075, 0.025), 0.88)
    LEAF_MATERIAL = material("Leaves", (0.13, 0.30, 0.055), 0.78)

    generated = []
    for index, config in enumerate(TREE_CONFIGS):
        tree, collision = build_tree(config)
        export_tree(tree, collision)
        column = index % 4
        row = index // 4
        offset = Vector((column * 1200.0, row * 1500.0, 0))
        tree.location += offset
        collision.location += offset
        generated.append((tree, collision))

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"GENERATED_ORIGINAL_TREE_FAMILY count={len(generated)} blend={BLEND_PATH}")


main()
