import bpy
import math
import os
import random
from mathutils import Vector


OUTPUT_DIR = r"C:\Users\ryant\OneDrive\Desktop\OriginalTrees_V4"
BLEND_PATH = os.path.join(OUTPUT_DIR, "FreshTreeFamily_V4.blend")


# All silhouettes and geometry below are generated mathematically. No source FBX is imported.
TREE_CONFIGS = (
    {
        "name": "SM_FreshPine_FullCrown",
        "seed": 1019,
        "height": 1280.0,
        "base_radius": 48.0,
        "tiers": 11,
        "branches": 6,
        "max_bough": 330.0,
        "clear": 0.19,
        "crown": "classic",
        "lean": (12.0, -8.0),
        "density": 1.00,
    },
    {
        "name": "SM_FreshPine_HighCrown",
        "seed": 2081,
        "height": 1510.0,
        "base_radius": 43.0,
        "tiers": 9,
        "branches": 5,
        "max_bough": 295.0,
        "clear": 0.39,
        "crown": "high",
        "lean": (-22.0, 13.0),
        "density": 0.88,
    },
    {
        "name": "SM_FreshPine_WideCrown",
        "seed": 3049,
        "height": 1120.0,
        "base_radius": 61.0,
        "tiers": 9,
        "branches": 7,
        "max_bough": 405.0,
        "clear": 0.27,
        "crown": "wide",
        "lean": (16.0, 19.0),
        "density": 1.08,
    },
    {
        "name": "SM_FreshPine_Young",
        "seed": 4093,
        "height": 690.0,
        "base_radius": 25.0,
        "tiers": 7,
        "branches": 5,
        "max_bough": 170.0,
        "clear": 0.18,
        "crown": "young",
        "lean": (5.0, 7.0),
        "density": 0.92,
    },
    {
        "name": "SM_FreshPine_Windswept",
        "seed": 5051,
        "height": 1370.0,
        "base_radius": 54.0,
        "tiers": 10,
        "branches": 5,
        "max_bough": 350.0,
        "clear": 0.28,
        "crown": "windswept",
        "lean": (132.0, 34.0),
        "density": 0.94,
        "wind_angle": 0.22,
    },
    {
        "name": "SM_FreshPine_OldFork",
        "seed": 6011,
        "height": 1580.0,
        "base_radius": 73.0,
        "tiers": 10,
        "branches": 6,
        "max_bough": 390.0,
        "clear": 0.32,
        "crown": "old",
        "lean": (-28.0, -21.0),
        "density": 0.96,
        "forked": True,
    },
    {
        "name": "SM_FreshPine_NarrowSpire",
        "seed": 7043,
        "height": 1590.0,
        "base_radius": 39.0,
        "tiers": 14,
        "branches": 5,
        "max_bough": 220.0,
        "clear": 0.14,
        "crown": "spire",
        "lean": (-9.0, 11.0),
        "density": 0.92,
    },
    {
        "name": "SM_FreshPine_BrokenTop",
        "seed": 8089,
        "height": 1330.0,
        "base_radius": 57.0,
        "tiers": 10,
        "branches": 6,
        "max_bough": 345.0,
        "clear": 0.25,
        "crown": "broken",
        "lean": (38.0, -16.0),
        "density": 0.90,
        "broken_top": True,
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

    def tapered_segment(self, start, end, radius_start, radius_end, sides=7, material_index=0):
        start = Vector(start)
        end = Vector(end)
        direction = (end - start).normalized()
        reference = Vector((0, 0, 1)) if abs(direction.z) < 0.91 else Vector((1, 0, 0))
        axis_u = direction.cross(reference).normalized()
        axis_v = direction.cross(axis_u).normalized()
        rings = []
        for center, radius in ((start, radius_start), (end, radius_end)):
            ring = []
            for side in range(sides):
                angle = math.tau * side / sides
                ring.append(
                    self.vertex(
                        center + axis_u * math.cos(angle) * radius + axis_v * math.sin(angle) * radius,
                        (0.0, 0.0, 0.0, 1.0),
                    )
                )
            rings.append(ring)
        for side in range(sides):
            nxt = (side + 1) % sides
            self.face((rings[0][side], rings[0][nxt], rings[1][nxt], rings[1][side]), material_index)
        self.face(tuple(reversed(rings[0])), material_index)
        self.face(tuple(rings[1]), material_index)

    def trunk(self, points, radii, sides=9):
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

    def foliage_bough(
        self,
        root,
        direction,
        length,
        width,
        thickness,
        droop,
        tip_lift,
        wind_weight,
        skew=0.0,
    ):
        """Closed, broad, curved conifer bough. It reads as a leafy mass from every viewing angle."""
        root = Vector(root)
        horizontal = Vector((direction.x, direction.y, 0.0)).normalized()
        lateral = Vector((-horizontal.y, horizontal.x, 0.0))
        fractions = (0.0, 0.26, 0.58, 0.82, 1.0)
        widths = (0.12, 0.78, 1.0, 0.62, 0.035)
        thicknesses = (0.30, 0.82, 1.0, 0.66, 0.12)
        rings = []

        for index, fraction in enumerate(fractions):
            sideways = math.sin(fraction * math.pi) * skew
            z_curve = -droop * math.sin(fraction * math.pi) + tip_lift * fraction**3
            center = root + horizontal * (length * fraction) + lateral * sideways + Vector((0, 0, z_curve))
            half_width = width * widths[index]
            half_thickness = thickness * thicknesses[index]
            color_weight = min(1.0, wind_weight * (0.24 + 0.76 * fraction))
            color = (color_weight, 0.0, 0.0, 1.0)
            ring = (
                self.vertex(center + lateral * half_width + Vector((0, 0, half_thickness)), color),
                self.vertex(center - lateral * half_width + Vector((0, 0, half_thickness)), color),
                self.vertex(center - lateral * half_width - Vector((0, 0, half_thickness)), color),
                self.vertex(center + lateral * half_width - Vector((0, 0, half_thickness)), color),
            )
            rings.append(ring)

        for ring_index in range(len(rings) - 1):
            current = rings[ring_index]
            nxt = rings[ring_index + 1]
            for side in range(4):
                side_next = (side + 1) % 4
                self.face((current[side], current[side_next], nxt[side_next], nxt[side]), 1)
        self.face(tuple(reversed(rings[0])), 1)
        self.face(tuple(rings[-1]), 1)

    def foliage_crown_layer(
        self,
        center,
        radius,
        height,
        segments,
        rng,
        wind_weight,
        bias_angle=None,
        bias_strength=0.0,
    ):
        """Closed irregular conifer skirt with a peaked top and drooping branch tips."""
        center = Vector(center)
        phase = rng.uniform(0.0, math.tau)
        peak_height = min(height * 0.54, max(height * 0.18, radius * 0.88))
        shoulder_height = min(height * 0.24, peak_height * 0.55)
        apex = self.vertex(
            center + Vector((0.0, 0.0, peak_height)),
            (min(1.0, wind_weight * 0.82), 0.0, 0.0, 1.0),
        )
        bottom = self.vertex(
            center + Vector((0.0, 0.0, -height * 0.23)),
            (min(1.0, wind_weight * 0.38), 0.0, 0.0, 1.0),
        )
        shoulder_ring = []
        outer_ring = []
        lower_ring = []

        for segment in range(segments):
            angle = phase + math.tau * segment / segments
            direction = Vector((math.cos(angle), math.sin(angle), 0.0))
            wind_factor = 1.0
            if bias_angle is not None:
                wind_factor += bias_strength * math.cos(angle - bias_angle)
            # Alternating long and short lobes avoid a perfect Christmas-tree cone.
            lobe = 1.0 + (0.13 if segment % 2 == 0 else -0.07)
            lobe *= rng.uniform(0.88, 1.10) * wind_factor
            shoulder_radius = radius * rng.uniform(0.34, 0.47) * max(0.45, wind_factor)
            outer_radius = radius * lobe
            lower_radius = radius * rng.uniform(0.24, 0.38) * max(0.55, wind_factor)
            side_jitter = rng.uniform(-height * 0.035, height * 0.035)

            shoulder_ring.append(
                self.vertex(
                    center + direction * shoulder_radius + Vector((0.0, 0.0, shoulder_height + side_jitter)),
                    (min(1.0, wind_weight * 0.70), 0.0, 0.0, 1.0),
                )
            )
            outer_ring.append(
                self.vertex(
                    center
                    + direction * outer_radius
                    + Vector((0.0, 0.0, -height * rng.uniform(0.015, 0.16))),
                    (min(1.0, wind_weight), 0.0, 0.0, 1.0),
                )
            )
            lower_ring.append(
                self.vertex(
                    center
                    + direction * lower_radius
                    + Vector((0.0, 0.0, -height * rng.uniform(0.20, 0.31))),
                    (min(1.0, wind_weight * 0.52), 0.0, 0.0, 1.0),
                )
            )

        for segment in range(segments):
            nxt = (segment + 1) % segments
            self.face((apex, shoulder_ring[nxt], shoulder_ring[segment]), 1)
            self.face(
                (shoulder_ring[segment], shoulder_ring[nxt], outer_ring[nxt], outer_ring[segment]),
                1,
            )
            self.face((outer_ring[segment], outer_ring[nxt], lower_ring[nxt], lower_ring[segment]), 1)
            self.face((lower_ring[segment], lower_ring[nxt], bottom), 1)

    def foliage_tuft(self, start, end, width, thickness, bend, wind_weight, twist=0.0):
        """Tapered, faceted needle mass. Many overlapping tufts form a natural conifer bough."""
        start = Vector(start)
        end = Vector(end)
        axis = (end - start).normalized()
        reference = Vector((0, 0, 1)) if abs(axis.z) < 0.90 else Vector((1, 0, 0))
        lateral = axis.cross(reference).normalized()
        vertical = axis.cross(lateral).normalized()
        fractions = (0.0, 0.26, 0.58, 0.82, 1.0)
        profiles = (0.08, 0.78, 1.0, 0.62, 0.035)
        sides = 6
        rings = []
        for ring_index, fraction in enumerate(fractions):
            center = start.lerp(end, fraction) + vertical * (math.sin(math.pi * fraction) * bend)
            ring = []
            for side in range(sides):
                angle = math.tau * side / sides + twist * fraction
                irregular = 1.0 + 0.08 * math.sin(side * 2.17 + ring_index * 1.31 + twist)
                offset = (
                    lateral * math.cos(angle) * width
                    + vertical * math.sin(angle) * thickness
                ) * profiles[ring_index] * irregular
                color_weight = min(1.0, wind_weight * (0.24 + 0.76 * fraction))
                ring.append(self.vertex(center + offset, (color_weight, 0.0, 0.0, 1.0)))
            rings.append(ring)
        for ring_index in range(len(rings) - 1):
            for side in range(sides):
                nxt = (side + 1) % sides
                self.face(
                    (rings[ring_index][side], rings[ring_index][nxt], rings[ring_index + 1][nxt], rings[ring_index + 1][side]),
                    1,
                )
        self.face(tuple(reversed(rings[0])), 1)
        self.face(tuple(rings[-1]), 1)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(collection):
            if datablock.users == 0:
                collection.remove(datablock)


def material(name, color, roughness):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1.0)
    result.roughness = roughness
    return result


WOOD_MATERIAL = None
LEAF_MATERIAL = None


def trunk_center(config, fraction):
    lean_x, lean_y = config["lean"]
    bend = fraction**1.55
    wobble = math.sin(fraction * math.pi * 2.3 + config["seed"] * 0.013) * 5.5 * fraction
    return Vector(
        (
            lean_x * bend + wobble,
            lean_y * bend + math.cos(fraction * math.pi * 1.8 + config["seed"] * 0.009) * 4.0 * fraction,
            config["height"] * fraction,
        )
    )


def crown_profile(config, fraction):
    clear = config["clear"]
    local = max(0.0, min(1.0, (fraction - clear) / max(0.01, 1.0 - clear)))
    classic = math.sin(math.pi * local) ** 0.62
    crown = config["crown"]
    if crown == "classic":
        return classic * (1.08 - 0.18 * local)
    if crown == "high":
        return classic * (0.92 + 0.16 * local)
    if crown == "wide":
        return classic * (1.28 - 0.30 * local)
    if crown == "young":
        return classic * (0.86 + 0.20 * local)
    if crown == "windswept":
        return classic * (1.08 - 0.12 * local)
    if crown == "old":
        return classic * (1.22 - 0.27 * local)
    if crown == "spire":
        return classic * (0.78 + 0.08 * (1.0 - local))
    if crown == "broken":
        return classic * (1.12 - 0.22 * local)
    return classic


def create_mesh_object(name, builder, include_materials):
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


def add_crown_tiers(builder, config, rng, center_fn=trunk_center, fraction_start=None, fraction_end=0.94):
    clear = config["clear"] if fraction_start is None else fraction_start
    tiers = config["tiers"]
    for tier in range(tiers):
        fraction = clear + (tier + 0.25) / tiers * (fraction_end - clear)
        center = center_fn(config, fraction)
        profile = crown_profile(config, fraction)
        tier_length = config["max_bough"] * profile * rng.uniform(0.88, 1.10)
        local = (fraction - clear) / max(0.01, fraction_end - clear)
        branch_count = config["branches"] + (1 if tier % 3 == 1 and config["density"] > 1.0 else 0)
        start_angle = rng.uniform(0, math.tau) + tier * 0.48

        for branch_index in range(branch_count):
            angle = start_angle + math.tau * branch_index / branch_count + rng.uniform(-0.12, 0.12)
            if config["crown"] == "windswept":
                wind_angle = config["wind_angle"]
                base_direction = Vector((math.cos(angle), math.sin(angle), 0.0))
                wind_direction = Vector((math.cos(wind_angle), math.sin(wind_angle), 0.0))
                direction = (base_direction * 0.36 + wind_direction * 0.90).normalized()
                length = tier_length * rng.uniform(0.78, 1.24)
            else:
                direction = Vector((math.cos(angle), math.sin(angle), 0.0))
                length = tier_length * rng.uniform(0.88, 1.08)

            # Visible woody support makes the tree credible without dominating the crown.
            branch_end = center + direction * length * 0.88 + Vector((0, 0, -length * (0.035 + 0.045 * (1.0 - local))))
            branch_radius = max(1.8, config["base_radius"] * (0.090 - 0.035 * local))
            builder.tapered_segment(center, branch_end, branch_radius, 1.2, sides=6)

            width = length * rng.uniform(0.20, 0.27)
            thickness = max(6.0, width * rng.uniform(0.16, 0.23))
            droop = length * (0.075 + 0.045 * (1.0 - local))
            tip_lift = length * (0.045 + 0.13 * local)
            root = center + direction * length * 0.025
            builder.foliage_bough(
                root,
                direction,
                length,
                width,
                thickness,
                droop,
                tip_lift,
                wind_weight=0.45 + 0.55 * fraction,
                skew=rng.uniform(-width * 0.18, width * 0.18),
            )

            # Two angled side masses create a connected, tree-like branch cluster instead of a thin strip.
            if rng.random() < config["density"]:
                for side in (-1.0, 1.0):
                    side_angle = angle + side * rng.uniform(0.28, 0.43)
                    side_direction = Vector((math.cos(side_angle), math.sin(side_angle), 0.0))
                    if config["crown"] == "windswept":
                        wind_direction = Vector((math.cos(config["wind_angle"]), math.sin(config["wind_angle"]), 0.0))
                        side_direction = (side_direction * 0.42 + wind_direction * 0.82).normalized()
                    side_root = center + direction * length * rng.uniform(0.20, 0.32)
                    side_length = length * rng.uniform(0.50, 0.68)
                    builder.foliage_bough(
                        side_root,
                        side_direction,
                        side_length,
                        width * rng.uniform(0.58, 0.74),
                        thickness * 0.78,
                        droop * 0.58,
                        tip_lift * 0.70,
                        wind_weight=0.50 + 0.50 * fraction,
                        skew=rng.uniform(-width * 0.12, width * 0.12),
                    )


def build_tree(config):
    rng = random.Random(config["seed"])
    builder = MeshBuilder()

    trunk_segments = 13
    points = [trunk_center(config, index / trunk_segments) for index in range(trunk_segments + 1)]
    radii = [
        max(2.5, config["base_radius"] * (1.0 - index / trunk_segments) ** 1.04)
        for index in range(trunk_segments + 1)
    ]
    builder.trunk(points, radii, sides=9)
    # A branching skeleton covered by overlapping volumetric needle tufts.
    crown_end = 0.94 if not config.get("broken_top") else 0.88
    for tier in range(config["tiers"]):
        fraction = config["clear"] + (tier + 0.25) / config["tiers"] * (crown_end - config["clear"])
        fraction += rng.uniform(-0.009, 0.009)
        local = (fraction - config["clear"]) / max(0.01, crown_end - config["clear"])
        center = trunk_center(config, fraction)
        length_scale = max(0.10, (1.0 - local) ** 0.58)
        if config["crown"] == "wide":
            length_scale *= 1.18
        elif config["crown"] == "spire":
            length_scale *= 0.80
        elif config["crown"] == "young":
            length_scale *= 0.91
        elif config["crown"] == "old":
            length_scale *= 1.09
        branch_length = config["max_bough"] * length_scale
        branch_count = config["branches"] + (1 if tier % 3 == 1 and config["density"] > 1.0 else 0)
        phase = rng.uniform(0.0, math.tau) + tier * 0.53

        for branch_index in range(branch_count):
            angle = phase + math.tau * branch_index / branch_count + rng.uniform(-0.12, 0.12)
            direction = Vector((math.cos(angle), math.sin(angle), rng.uniform(-0.045, 0.075))).normalized()
            if config["crown"] == "windswept":
                wind_direction = Vector((math.cos(config["wind_angle"]), math.sin(config["wind_angle"]), 0.0))
                direction = (direction * 0.32 + wind_direction * 0.91).normalized()
            length = branch_length * rng.uniform(0.86, 1.12)
            sag = length * (0.055 + 0.045 * (1.0 - local))
            lift = length * (0.025 + 0.075 * local)
            mid = center + direction * length * 0.52 - Vector((0, 0, sag))
            end = center + direction * length + Vector((0, 0, lift - sag * 0.48))
            branch_radius = max(1.5, config["base_radius"] * (0.085 - local * 0.035))
            builder.tapered_segment(center, mid, branch_radius, branch_radius * 0.62, sides=6)
            builder.tapered_segment(mid, end, branch_radius * 0.62, 1.0, sides=6)

            # Main branch needle masses overlap to form a continuous bough.
            for tuft_index, along in enumerate((0.27, 0.43, 0.59, 0.74, 0.88)):
                tuft_center = center.lerp(mid, min(1.0, along / 0.52)) if along <= 0.52 else mid.lerp(end, (along - 0.52) / 0.48)
                tuft_length = length * rng.uniform(0.20, 0.27)
                tuft_start = tuft_center - direction * tuft_length * 0.42
                tuft_end = tuft_center + direction * tuft_length * 0.58
                tuft_width = max(16.0, length * rng.uniform(0.115, 0.145))
                builder.foliage_tuft(
                    tuft_start,
                    tuft_end,
                    tuft_width,
                    tuft_width * rng.uniform(0.76, 0.94),
                    bend=rng.uniform(-tuft_width * 0.18, tuft_width * 0.18),
                    wind_weight=0.45 + 0.55 * fraction,
                    twist=rng.uniform(-0.55, 0.55),
                )

            # Paired secondary twigs widen each bough and remove the bottle-brush look.
            for twig_index, along in enumerate((0.38, 0.61, 0.79)):
                base = center.lerp(mid, min(1.0, along / 0.52)) if along <= 0.52 else mid.lerp(end, (along - 0.52) / 0.48)
                for side in (-1.0, 1.0):
                    twig_angle = math.atan2(direction.y, direction.x) + side * rng.uniform(0.42, 0.62)
                    twig_direction = Vector((math.cos(twig_angle), math.sin(twig_angle), rng.uniform(0.03, 0.13))).normalized()
                    if config["crown"] == "windswept":
                        wind_direction = Vector((math.cos(config["wind_angle"]), math.sin(config["wind_angle"]), 0.05)).normalized()
                        twig_direction = (twig_direction * 0.46 + wind_direction * 0.72).normalized()
                    twig_length = length * rng.uniform(0.28, 0.43) * (1.0 - twig_index * 0.08)
                    twig_end = base + twig_direction * twig_length
                    builder.tapered_segment(base, twig_end, max(0.9, branch_radius * 0.42), 0.55, sides=5)
                    tuft_width = max(13.0, twig_length * rng.uniform(0.20, 0.27))
                    builder.foliage_tuft(
                        base - twig_direction * twig_length * 0.08,
                        twig_end + twig_direction * twig_length * 0.12,
                        tuft_width,
                        tuft_width * rng.uniform(0.74, 0.92),
                        bend=rng.uniform(-tuft_width * 0.22, tuft_width * 0.22),
                        wind_weight=0.52 + 0.48 * fraction,
                        twist=rng.uniform(-0.65, 0.65),
                    )

    # Upright leader and short top boughs close the crown naturally.
    leader_width = max(16.0, config["base_radius"] * 0.46)
    leader_limit = 0.90 if config.get("broken_top") else 1.0
    leader_base = 0.80 if config.get("broken_top") else 0.86
    for leader_index in range(3):
        start_fraction = leader_base + leader_index * 0.035
        end_fraction = min(leader_limit, start_fraction + 0.095)
        width_scale = 1.0 - leader_index * 0.14
        builder.foliage_tuft(
            trunk_center(config, start_fraction),
            trunk_center(config, end_fraction),
            leader_width * width_scale,
            leader_width * 0.72 * width_scale,
            5.0,
            0.94 + leader_index * 0.03,
            twist=0.22 + leader_index * 0.27,
        )
    for ring in range(4):
        fraction = (0.76 if not config.get("broken_top") else 0.72) + ring * 0.045
        center = trunk_center(config, fraction)
        top_length = config["max_bough"] * (0.25 - ring * 0.038)
        for branch_index in range(4):
            angle = branch_index * math.pi * 0.5 + ring * 0.58
            direction = Vector((math.cos(angle), math.sin(angle), 0.20)).normalized()
            builder.foliage_tuft(
                center,
                center + direction * top_length,
                max(12.0, top_length * 0.12),
                max(7.0, top_length * 0.075),
                bend=6.0,
                wind_weight=0.90 + ring * 0.02,
                twist=ring * 0.31,
            )

    if config.get("forked"):
        split = trunk_center(config, 0.59)
        fork_end = split + Vector((88.0, -55.0, config["height"] * 0.32))
        builder.tapered_segment(split, fork_end, config["base_radius"] * 0.18, 2.5, sides=7)
        builder.foliage_tuft(
            split.lerp(fork_end, 0.42),
            fork_end + Vector((0, 0, 45.0)),
            config["base_radius"] * 0.43,
            config["base_radius"] * 0.30,
            10.0,
            0.96,
            twist=-0.42,
        )

    if config.get("broken_top"):
        break_start = trunk_center(config, 0.88)
        break_end = break_start + Vector((10.0, -4.0, 68.0))
        builder.tapered_segment(break_start, break_end, 8.0, 4.0, sides=6)

    tree = create_mesh_object(config["name"], builder, include_materials=True)
    recalculate_normals(tree)

    collision_builder = MeshBuilder()
    collision_builder.tapered_segment(
        trunk_center(config, 0.0),
        trunk_center(config, 0.74),
        config["base_radius"] * 1.08,
        max(8.0, config["base_radius"] * 0.36),
        sides=10,
    )
    collision = create_mesh_object(f"UCX_{config['name']}", collision_builder, include_materials=False)
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
        f"EXPORTED_FRESH_TREE path={output_path} vertices={len(tree.data.vertices)} "
        f"polygons={len(tree.data.polygons)} materials={[m.name for m in tree.data.materials]}"
    )


def main():
    global WOOD_MATERIAL, LEAF_MATERIAL
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    clear_scene()
    WOOD_MATERIAL = material("Wood", (0.18, 0.065, 0.022), 0.90)
    LEAF_MATERIAL = material("Leaves", (0.105, 0.255, 0.042), 0.82)

    generated = []
    for index, config in enumerate(TREE_CONFIGS):
        tree, collision = build_tree(config)
        export_tree(tree, collision)
        offset = Vector(((index % 4) * 1150.0, (index // 4) * 1650.0, 0.0))
        tree.location += offset
        collision.location += offset
        generated.append((tree, collision))

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"GENERATED_FRESH_TREE_FAMILY count={len(generated)} blend={BLEND_PATH}")


main()
