import bpy
import math
import os
import random
from mathutils import Vector


OUTPUT_DIR = r"C:\Users\ryant\OneDrive\Desktop\OriginalTrees_V9"
BLEND_PATH = os.path.join(OUTPUT_DIR, "OriginalPackStyleTrees_V9.blend")


# Original silhouettes using the same broad low-poly conifer design language as the reference pack.
# No reference mesh, topology, vertex positions, UVs, or textures are imported by this generator.
TREE_CONFIGS = (
    {
        "name": "SM_OriginalFir_01_Full",
        "seed": 12011,
        "height": 1260.0,
        "base_radius": 34.0,
        "clear": 0.27,
        "fans": 30,
        "tiers": 15,
        "branches": 3,
        "max_length": 315.0,
        "max_width": 94.0,
        "lean": (13.0, -7.0),
        "curve": (12.0, -6.0),
        "density": 1.00,
        "profile": "full",
    },
    {
        "name": "SM_OriginalFir_02_Tall",
        "seed": 23027,
        "height": 1510.0,
        "base_radius": 31.0,
        "clear": 0.39,
        "fans": 25,
        "tiers": 13,
        "branches": 3,
        "max_length": 290.0,
        "max_width": 82.0,
        "lean": (-19.0, 11.0),
        "curve": (-10.0, 6.0),
        "density": 0.86,
        "profile": "tall",
    },
    {
        "name": "SM_OriginalFir_03_Heavy",
        "seed": 34039,
        "height": 1360.0,
        "base_radius": 40.0,
        "clear": 0.23,
        "fans": 36,
        "tiers": 15,
        "branches": 4,
        "max_length": 355.0,
        "max_width": 108.0,
        "lean": (8.0, 15.0),
        "curve": (9.0, 11.0),
        "density": 1.10,
        "profile": "heavy",
    },
    {
        "name": "SM_OriginalFir_04_Crooked",
        "seed": 45053,
        "height": 1410.0,
        "base_radius": 36.0,
        "clear": 0.31,
        "fans": 28,
        "tiers": 14,
        "branches": 3,
        "max_length": 325.0,
        "max_width": 90.0,
        "lean": (78.0, -31.0),
        "curve": (54.0, -29.0),
        "density": 0.92,
        "profile": "crooked",
        "wind_angle": -0.34,
    },
    {
        "name": "SM_OriginalFir_05_Young",
        "seed": 56081,
        "height": 720.0,
        "base_radius": 22.0,
        "clear": 0.22,
        "fans": 21,
        "tiers": 11,
        "branches": 3,
        "max_length": 175.0,
        "max_width": 56.0,
        "lean": (4.0, 5.0),
        "curve": (6.0, 4.0),
        "density": 0.91,
        "profile": "young",
    },
    {
        "name": "SM_OriginalFir_06_Windswept",
        "seed": 67057,
        "height": 1320.0,
        "base_radius": 35.0,
        "clear": 0.34,
        "fans": 27,
        "tiers": 14,
        "branches": 3,
        "max_length": 335.0,
        "max_width": 88.0,
        "lean": (96.0, 22.0),
        "curve": (46.0, 18.0),
        "density": 0.88,
        "profile": "windswept",
        "wind_angle": 0.18,
    },
)


class MeshBuilder:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.materials = []
        self.colors = []

    def vertex(self, position, color):
        self.vertices.append(tuple(position))
        self.colors.append(color)
        return len(self.vertices) - 1

    def face(self, indices, material_index):
        self.faces.append(tuple(indices))
        self.materials.append(material_index)

    def tapered_segment(self, start, end, radius_start, radius_end, sides=7):
        start = Vector(start)
        end = Vector(end)
        axis = (end - start).normalized()
        reference = Vector((0, 0, 1)) if abs(axis.z) < 0.92 else Vector((1, 0, 0))
        side_axis = axis.cross(reference).normalized()
        up_axis = axis.cross(side_axis).normalized()
        rings = []
        for center, radius in ((start, radius_start), (end, radius_end)):
            ring = []
            for side in range(sides):
                angle = math.tau * side / sides
                ring.append(
                    self.vertex(
                        center + side_axis * math.cos(angle) * radius + up_axis * math.sin(angle) * radius,
                        (0.0, 0.0, 0.0, 1.0),
                    )
                )
            rings.append(ring)
        for side in range(sides):
            nxt = (side + 1) % sides
            self.face((rings[0][side], rings[0][nxt], rings[1][nxt], rings[1][side]), 0)
        self.face(tuple(reversed(rings[0])), 0)
        self.face(tuple(rings[1]), 0)

    def curved_trunk(self, points, radii, sides=8):
        rings = []
        for center, radius in zip(points, radii):
            ring = []
            for side in range(sides):
                angle = math.tau * side / sides
                ring.append(
                    self.vertex(
                        Vector(center) + Vector((math.cos(angle) * radius, math.sin(angle) * radius, 0.0)),
                        (0.0, 0.0, 0.0, 1.0),
                    )
                )
            rings.append(ring)
        for ring_index in range(len(rings) - 1):
            for side in range(sides):
                nxt = (side + 1) % sides
                self.face(
                    (
                        rings[ring_index][side],
                        rings[ring_index][nxt],
                        rings[ring_index + 1][nxt],
                        rings[ring_index + 1][side],
                    ),
                    0,
                )
        self.face(tuple(reversed(rings[0])), 0)
        self.face(tuple(rings[-1]), 0)

    def folded_fan(
        self,
        root,
        direction,
        length,
        max_width,
        sag,
        tip_lift,
        sideways_curve,
        thickness,
        asymmetry,
        wind_weight,
    ):
        """Original closed foliage fan with a curved spine, central fold, and jagged outline."""
        root = Vector(root)
        horizontal = Vector((direction.x, direction.y, 0.0)).normalized()
        lateral = Vector((-horizontal.y, horizontal.x, 0.0))
        vertical = Vector((0.0, 0.0, 1.0))
        fractions = (0.0, 0.19, 0.43, 0.68, 0.86, 1.0)
        width_profile = (0.08, 0.48, 0.88, 1.0, 0.62, 0.025)
        ridge_profile = (0.12, 0.42, 0.95, 0.72, 0.38, 0.08)
        sections = []

        for index, fraction in enumerate(fractions):
            curve_z = -sag * math.sin(math.pi * fraction) + tip_lift * fraction**3
            curve_side = sideways_curve * math.sin(math.pi * fraction)
            center = root + horizontal * length * fraction + lateral * curve_side + vertical * curve_z
            width = max_width * width_profile[index]
            left_width = width * (1.0 + asymmetry)
            right_width = width * (1.0 - asymmetry)
            ridge = thickness * ridge_profile[index]
            bottom = thickness * (0.30 + 0.28 * ridge_profile[index])
            color_weight = min(1.0, wind_weight * (0.20 + 0.80 * fraction))
            color = (color_weight, 0.0, 0.0, 1.0)
            sections.append(
                {
                    "top_left": self.vertex(center - lateral * left_width, color),
                    "top_ridge": self.vertex(center + vertical * ridge, color),
                    "top_right": self.vertex(center + lateral * right_width, color),
                    "bottom_left": self.vertex(center - lateral * left_width - vertical * bottom, color),
                    "bottom_ridge": self.vertex(center - vertical * bottom, color),
                    "bottom_right": self.vertex(center + lateral * right_width - vertical * bottom, color),
                }
            )

        for index in range(len(sections) - 1):
            a = sections[index]
            b = sections[index + 1]
            self.face((a["top_left"], b["top_left"], b["top_ridge"], a["top_ridge"]), 1)
            self.face((a["top_ridge"], b["top_ridge"], b["top_right"], a["top_right"]), 1)
            self.face((a["bottom_ridge"], b["bottom_ridge"], b["bottom_left"], a["bottom_left"]), 1)
            self.face((a["bottom_right"], b["bottom_right"], b["bottom_ridge"], a["bottom_ridge"]), 1)
            self.face((a["top_left"], a["bottom_left"], b["bottom_left"], b["top_left"]), 1)
            self.face((a["bottom_right"], a["top_right"], b["top_right"], b["bottom_right"]), 1)

        first = sections[0]
        last = sections[-1]
        self.face(
            (
                first["top_left"], first["top_ridge"], first["top_right"],
                first["bottom_right"], first["bottom_ridge"], first["bottom_left"],
            ),
            1,
        )
        self.face(
            (
                last["bottom_left"], last["bottom_ridge"], last["bottom_right"],
                last["top_right"], last["top_ridge"], last["top_left"],
            ),
            1,
        )

    def folded_plate(
        self,
        root,
        direction,
        length,
        max_width,
        sag,
        tip_lift,
        sideways_curve,
        thickness,
        asymmetry,
        roll,
        wind_weight,
        growth_up=None,
    ):
        """Broad closed plate that can pitch and roll as part of a compound bough fan."""
        root = Vector(root)
        axis = Vector(direction).normalized()
        bend_up = Vector(growth_up).normalized() if growth_up is not None else Vector((0.0, 0.0, 1.0))
        reference = bend_up
        if abs(axis.dot(reference)) > 0.94:
            reference = Vector((1.0, 0.0, 0.0))
            if abs(axis.dot(reference)) > 0.94:
                reference = Vector((0.0, 1.0, 0.0))
        base_lateral = axis.cross(reference).normalized()
        base_normal = base_lateral.cross(axis).normalized()
        lateral = base_lateral * math.cos(roll) + base_normal * math.sin(roll)
        normal = base_normal * math.cos(roll) - base_lateral * math.sin(roll)
        fractions = (0.0, 0.18, 0.40, 0.63, 0.83, 1.0)
        width_profile = (0.07, 0.53, 0.91, 1.0, 0.68, 0.035)
        ridge_profile = (0.10, 0.48, 1.0, 0.78, 0.42, 0.06)
        sections = []

        for index, fraction in enumerate(fractions):
            center = (
                root
                + axis * length * fraction
                + lateral * (sideways_curve * math.sin(math.pi * fraction))
                + bend_up * (-sag * math.sin(math.pi * fraction) + tip_lift * fraction**3)
            )
            width = max_width * width_profile[index]
            left_width = width * (1.0 + asymmetry)
            right_width = width * (1.0 - asymmetry)
            ridge = thickness * ridge_profile[index]
            underside = thickness * (0.35 + 0.25 * ridge_profile[index])
            color_weight = min(1.0, wind_weight * (0.20 + 0.80 * fraction))
            color = (color_weight, 0.0, 0.0, 1.0)
            sections.append(
                {
                    "tl": self.vertex(center - lateral * left_width, color),
                    "tr": self.vertex(center + lateral * right_width, color),
                    "tc": self.vertex(center + normal * ridge, color),
                    "bl": self.vertex(center - lateral * left_width - normal * underside, color),
                    "br": self.vertex(center + lateral * right_width - normal * underside, color),
                    "bc": self.vertex(center - normal * underside, color),
                }
            )

        for index in range(len(sections) - 1):
            a = sections[index]
            b = sections[index + 1]
            self.face((a["tl"], b["tl"], b["tc"], a["tc"]), 1)
            self.face((a["tc"], b["tc"], b["tr"], a["tr"]), 1)
            self.face((a["bc"], b["bc"], b["bl"], a["bl"]), 1)
            self.face((a["br"], b["br"], b["bc"], a["bc"]), 1)
            self.face((a["tl"], a["bl"], b["bl"], b["tl"]), 1)
            self.face((a["br"], a["tr"], b["tr"], b["br"]), 1)

        first = sections[0]
        last = sections[-1]
        self.face((first["tl"], first["tc"], first["tr"], first["br"], first["bc"], first["bl"]), 1)
        self.face((last["bl"], last["bc"], last["br"], last["tr"], last["tc"], last["tl"]), 1)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(collection):
            if datablock.users == 0:
                collection.remove(datablock)


def make_material(name, color, roughness):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1.0)
    result.roughness = roughness
    return result


WOOD_MATERIAL = None
LEAF_MATERIAL = None


def trunk_center(config, fraction):
    lean_x, lean_y = config["lean"]
    bend = fraction**1.62
    wobble_x = math.sin(fraction * math.pi * 2.15 + config["seed"] * 0.011) * 4.0 * fraction
    wobble_y = math.cos(fraction * math.pi * 1.76 + config["seed"] * 0.008) * 3.2 * fraction
    curve_x, curve_y = config.get("curve", (0.0, 0.0))
    curve_envelope = math.sin(math.pi * fraction) * (0.48 + 0.52 * fraction)
    return Vector(
        (
            lean_x * bend + curve_x * curve_envelope + wobble_x,
            lean_y * bend + curve_y * curve_envelope + wobble_y,
            config["height"] * fraction,
        )
    )


def trunk_frame(config, fraction):
    epsilon = 0.003
    lower = trunk_center(config, max(0.0, fraction - epsilon))
    upper = trunk_center(config, min(1.0, fraction + epsilon))
    tangent = (upper - lower).normalized()
    radial_x = Vector((1.0, 0.0, 0.0))
    radial_x -= tangent * radial_x.dot(tangent)
    if radial_x.length < 0.01:
        radial_x = Vector((0.0, 1.0, 0.0))
        radial_x -= tangent * radial_x.dot(tangent)
    radial_x.normalize()
    radial_y = tangent.cross(radial_x).normalized()
    return tangent, radial_x, radial_y


def length_profile(config, local):
    # Broad lower crown with a smooth but irregular taper toward the leader.
    scale = max(0.07, (1.0 - local) ** 0.58)
    profile = config["profile"]
    if profile == "heavy":
        scale *= 1.11 - 0.10 * local
    elif profile == "tall":
        scale *= 0.92 + 0.06 * local
    elif profile == "young":
        scale *= 0.91
    elif profile in ("crooked", "windswept"):
        scale *= 1.02
    return scale


def make_object(name, builder, include_materials=True):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(builder.vertices, [], builder.faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if include_materials:
        mesh.materials.append(WOOD_MATERIAL)
        mesh.materials.append(LEAF_MATERIAL)
        for polygon, material_index in zip(mesh.polygons, builder.materials):
            polygon.material_index = material_index
            polygon.use_smooth = material_index == 0
        colors = mesh.color_attributes.new(name="Color", type="FLOAT_COLOR", domain="POINT")
        for index, color in enumerate(builder.colors):
            colors.data[index].color = color
    return obj


def recalculate_normals(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def add_fan(builder, config, rng, fraction, angle, length_scale=1.0, width_scale=1.0):
    local = (fraction - config["clear"]) / max(0.01, 0.965 - config["clear"])
    local = min(1.0, max(0.0, local))
    direction = Vector((math.cos(angle), math.sin(angle), 0.0))
    if "wind_angle" in config:
        wind_direction = Vector((math.cos(config["wind_angle"]), math.sin(config["wind_angle"]), 0.0))
        bias = 0.54 if config["profile"] == "windswept" else 0.22
        direction = (direction * (1.0 - bias) + wind_direction * bias).normalized()

    length = config["max_length"] * length_profile(config, local) * length_scale * rng.uniform(0.88, 1.11)
    width = config["max_width"] * (0.68 + 0.32 * (1.0 - local)) * width_scale * rng.uniform(0.88, 1.10)
    root = trunk_center(config, fraction)
    branch_pitch = rng.uniform(-0.045, 0.025) + local * 0.055
    branch_end = root + direction * length + Vector((0.0, 0.0, length * branch_pitch))
    branch_radius = max(1.2, config["base_radius"] * (0.075 - local * 0.032))
    builder.tapered_segment(root, branch_end, branch_radius, 0.8, sides=6)
    builder.folded_fan(
        root + direction * length * 0.035,
        direction,
        length * 1.04,
        width,
        sag=length * rng.uniform(0.055, 0.105),
        tip_lift=length * rng.uniform(0.075, 0.145) + local * length * 0.055,
        sideways_curve=rng.uniform(-width * 0.18, width * 0.18),
        thickness=max(5.0, width * rng.uniform(0.11, 0.17)),
        asymmetry=rng.uniform(-0.16, 0.16),
        wind_weight=0.42 + 0.58 * fraction,
    )


def add_bough_cluster(builder, config, rng, fraction, angle, cluster_scale):
    local = (fraction - config["clear"]) / max(0.01, 0.955 - config["clear"])
    local = min(1.0, max(0.0, local))
    trunk_up, radial_x, radial_y = trunk_frame(config, fraction)
    horizontal = radial_x * math.cos(angle) + radial_y * math.sin(angle)
    if "wind_angle" in config:
        wind = radial_x * math.cos(config["wind_angle"]) + radial_y * math.sin(config["wind_angle"])
        bias = 0.58 if config["profile"] == "windswept" else 0.18
        horizontal = (horizontal * (1.0 - bias) + wind * bias).normalized()

    bough_length = (
        config["max_length"]
        * length_profile(config, local)
        * cluster_scale
        * rng.uniform(0.87, 1.10)
    )
    pitch = rng.uniform(-0.075, 0.015) + local * 0.060
    axis = (horizontal + trunk_up * pitch).normalized()
    root = trunk_center(config, fraction)
    sag = bough_length * rng.uniform(0.035, 0.070)
    mid = root + axis * bough_length * 0.52 - trunk_up * sag
    end = root + axis * bough_length + trunk_up * (bough_length * rng.uniform(0.015, 0.060) - sag * 0.45)
    branch_radius = max(1.15, config["base_radius"] * (0.070 - local * 0.030))
    builder.tapered_segment(root, mid, branch_radius, branch_radius * 0.58, sides=6)
    builder.tapered_segment(mid, end, branch_radius * 0.58, 0.70, sides=6)

    base_width = config["max_width"] * (0.82 + 0.18 * (1.0 - local)) * cluster_scale
    plate_specs = [
        # start-along, yaw, pitch delta, length, width, roll
        (0.04, 0.00, 0.00, 0.93, 1.02, rng.uniform(-0.10, 0.10)),
        (0.14, -rng.uniform(0.25, 0.39), rng.uniform(0.01, 0.08), rng.uniform(0.66, 0.78), rng.uniform(0.76, 0.92), rng.uniform(-0.30, -0.08)),
        (0.18, rng.uniform(0.27, 0.42), rng.uniform(-0.02, 0.07), rng.uniform(0.62, 0.76), rng.uniform(0.72, 0.90), rng.uniform(0.08, 0.30)),
        (0.38, -rng.uniform(0.34, 0.52), rng.uniform(0.05, 0.14), rng.uniform(0.46, 0.61), rng.uniform(0.62, 0.78), rng.uniform(-0.38, -0.12)),
        (0.43, rng.uniform(0.32, 0.50), rng.uniform(0.03, 0.13), rng.uniform(0.44, 0.58), rng.uniform(0.60, 0.76), rng.uniform(0.12, 0.38)),
    ]
    if rng.random() < 0.46 * config["density"]:
        plate_specs.append(
            (0.28, rng.uniform(-0.15, 0.15), rng.uniform(0.10, 0.19), rng.uniform(0.50, 0.64), rng.uniform(0.60, 0.76), rng.uniform(-0.22, 0.22))
        )

    for start_along, yaw, pitch_delta, length_scale, width_scale, roll in plate_specs:
        plate_root = root.lerp(mid, min(1.0, start_along / 0.52)) if start_along <= 0.52 else mid.lerp(end, (start_along - 0.52) / 0.48)
        plate_angle = angle + yaw
        plate_radial = radial_x * math.cos(plate_angle) + radial_y * math.sin(plate_angle)
        plate_direction = (plate_radial + trunk_up * (pitch + pitch_delta)).normalized()
        plate_length = bough_length * length_scale
        plate_width = base_width * width_scale * rng.uniform(0.90, 1.10)
        plate_sag = plate_length * rng.uniform(0.035, 0.090)
        if rng.random() < 0.30:
            plate_tip_lift = plate_length * rng.uniform(0.025, 0.065)
        else:
            plate_tip_lift = plate_length * rng.uniform(0.080, 0.155)
        builder.folded_plate(
            plate_root,
            plate_direction,
            plate_length,
            plate_width,
            plate_sag,
            plate_tip_lift,
            sideways_curve=rng.uniform(-plate_width * 0.20, plate_width * 0.20),
            thickness=max(6.0, plate_width * rng.uniform(0.17, 0.25)),
            asymmetry=rng.uniform(-0.18, 0.18),
            roll=roll,
            wind_weight=0.43 + 0.57 * fraction,
            growth_up=trunk_up,
        )


def build_tree(config):
    rng = random.Random(config["seed"])
    builder = MeshBuilder()

    trunk_segments = 13
    trunk_top = 0.972
    points = [trunk_center(config, (index / trunk_segments) * trunk_top) for index in range(trunk_segments + 1)]
    radii = [
        max(2.0, config["base_radius"] * 0.82 * (1.0 - index / trunk_segments) ** 1.02)
        for index in range(trunk_segments + 1)
    ]
    builder.curved_trunk(points, radii, sides=8)

    # Staggered compound boughs form uneven macro-clumps instead of clean ribbon shelves.
    golden_angle = math.radians(137.507764)
    macro_scales = [rng.uniform(0.86, 1.15) for _ in range(4)]
    macro_scales[rng.randrange(4)] *= rng.uniform(1.04, 1.13)
    for tier in range(config["tiers"]):
        local = (tier + 0.28) / config["tiers"]
        fraction = config["clear"] + local * (0.952 - config["clear"])
        fraction += rng.uniform(-0.019, 0.019)
        branch_count = config["branches"]
        if config["profile"] == "heavy" and tier % 4 == 1:
            branch_count += 1
        phase = tier * golden_angle + rng.uniform(-0.28, 0.28) + config["seed"] * 0.001
        macro_index = min(3, int(local * 4.0))
        tier_scale = macro_scales[macro_index] * rng.uniform(0.92, 1.09)
        for branch_index in range(branch_count):
            if rng.random() < 0.035 and config["profile"] in ("tall", "crooked", "windswept"):
                continue
            angle = phase + math.tau * branch_index / branch_count + rng.uniform(-0.16, 0.16)
            add_bough_cluster(
                builder,
                config,
                rng,
                min(0.955, fraction + rng.uniform(-0.006, 0.006)),
                angle,
                tier_scale * rng.uniform(0.88, 1.12),
            )

    # Tight upright folded plates wrap and hide the leader.
    top_height_scale = config["height"] / 1260.0
    for top_index in range(7):
        fraction = 0.83 + top_index * 0.018
        angle = top_index * golden_angle + 0.61
        trunk_up, radial_x, radial_y = trunk_frame(config, fraction)
        radial = rng.uniform(0.28, 0.48)
        radial_direction = radial_x * math.cos(angle) + radial_y * math.sin(angle)
        direction = (radial_direction * radial + trunk_up * rng.uniform(0.72, 0.96)).normalized()
        length = rng.uniform(95.0, 135.0) * top_height_scale * (1.0 - top_index * 0.045)
        width = rng.uniform(30.0, 44.0) * top_height_scale * (1.0 - top_index * 0.035)
        builder.folded_plate(
            trunk_center(config, fraction),
            direction,
            length,
            width,
            sag=length * 0.025,
            tip_lift=length * rng.uniform(0.02, 0.06),
            sideways_curve=rng.uniform(-8.0, 8.0) * top_height_scale,
            thickness=max(5.0, width * 0.18),
            asymmetry=rng.uniform(-0.12, 0.12),
            roll=rng.uniform(-0.32, 0.32),
            wind_weight=0.92 + top_index * 0.01,
            growth_up=trunk_up,
        )

    tree = make_object(config["name"], builder, include_materials=True)
    recalculate_normals(tree)

    collisions = []
    collision_segments = 4
    collision_top = 0.74
    for collision_index in range(collision_segments):
        start_fraction = collision_top * collision_index / collision_segments
        end_fraction = collision_top * (collision_index + 1) / collision_segments
        collision_builder = MeshBuilder()
        collision_builder.tapered_segment(
            trunk_center(config, start_fraction),
            trunk_center(config, end_fraction),
            max(6.0, config["base_radius"] * 0.89 * (1.0 - start_fraction) ** 1.02),
            max(5.0, config["base_radius"] * 0.89 * (1.0 - end_fraction) ** 1.02),
            sides=8,
        )
        collision = make_object(
            f"UCX_{config['name']}_{collision_index:02d}",
            collision_builder,
            include_materials=False,
        )
        recalculate_normals(collision)
        collision.display_type = "WIRE"
        collision.hide_render = True
        collisions.append(collision)
    return tree, collisions


def export_tree(tree, collisions):
    bpy.ops.object.select_all(action="DESELECT")
    tree.select_set(True)
    for collision in collisions:
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
        f"EXPORTED_PACK_STYLE_ORIGINAL path={output_path} vertices={len(tree.data.vertices)} "
        f"polygons={len(tree.data.polygons)} materials={[m.name for m in tree.data.materials]}"
    )


def main():
    global WOOD_MATERIAL, LEAF_MATERIAL
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    clear_scene()
    WOOD_MATERIAL = make_material("Wood", (0.18, 0.064, 0.022), 0.90)
    LEAF_MATERIAL = make_material("Leaves", (0.13, 0.285, 0.060), 0.79)

    generated = []
    for index, config in enumerate(TREE_CONFIGS):
        tree, collisions = build_tree(config)
        export_tree(tree, collisions)
        offset = Vector(((index % 3) * 1150.0, (index // 3) * 1650.0, 0.0))
        tree.location += offset
        for collision in collisions:
            collision.location += offset
        generated.append((tree, collisions))

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"GENERATED_PACK_STYLE_ORIGINAL_FAMILY count={len(generated)} blend={BLEND_PATH}")


main()
