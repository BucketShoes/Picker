# Blender 4.0 (Cycles) scene for the picker box, lit by its own LEDs.
# Usage: blender -b -P scene.py -- board.glb outdir views(comma list or "all") layers(comma list or "all") samples
#   layers: room, seat1..seat8.  Writes linear EXR per view/layer, unexposed (exposure applied when viewing).
import bpy, sys, math, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
GLB, OUT = args[0], args[1]
VIEWS = args[2] if len(args) > 2 else "all"
LAYERS = args[3] if len(args) > 3 else "all"
SAMPLES = int(args[4]) if len(args) > 4 else 512
RES = (1200, 800)
os.makedirs(OUT, exist_ok=True)

# --- physical numbers -------------------------------------------------------------------------------------------
LED_MCD = 40.0         # per LED at ~4 mA from the cell (LCSC page: 145-300 mcd at 20 mA; ~linear), water-clear
ROOM_LUX = 300.0       # typical indoor room at table height
RED = (1.0, 0.03, 0.0)  # ~625 nm, linear Rec.709
LUM = 0.2126 * RED[0] + 0.7152 * RED[1] + 0.0722 * RED[2]
CEIL_H = 2.0           # ceiling light height above table (m)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene

# --- identify the board layers (export-order names) -------------------------------------------------------------
def base(m):
    b = m.node_tree.nodes.get("Principled BSDF")
    return tuple(b.inputs["Base Color"].default_value)[:3] if b else (0, 0, 0)

board_body = mask = None
silk, copper = [], []
for o in bpy.data.objects:
    if o.type != "MESH" or not o.name.startswith("=>"):
        continue
    c = base(o.data.materials[0])
    if abs(c[0] - 0.42) < 0.01 and abs(c[2] - 0.29) < 0.01:
        board_body = o
    elif abs(c[0] - 0.1) < 0.01 and abs(c[2] - 0.166) < 0.01:
        mask = mask or []
        mask.append(o)
    elif c == (1.0, 1.0, 1.0):
        silk.append(o)
    else:
        copper.append(o)

# Recentre: board centre at origin, bottom at z=0.
root = bpy.data.objects["Node_0"]
bpy.context.view_layer.update()
pts = [board_body.matrix_world @ Vector(v) for v in board_body.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
root.location -= Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
bpy.context.view_layer.update()

# --- materials ----------------------------------------------------------------------------------------------------
def principled(name, color, metal=0.0, rough=0.5, alpha=1.0, coat=0.0, sss=0.0, sss_r=(1, 1, 1), trans=0.0, ior=1.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Subsurface Radius"].default_value = sss_r
    b.inputs["Subsurface Scale"].default_value = 0.001
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    return m

M_MASK = principled("mask", (0.13, 0.02, 0.22), rough=0.25, alpha=0.88, coat=0.3)
M_FR4 = principled("fr4", (0.42, 0.45, 0.29), rough=0.6, sss=0.3, sss_r=(1.0, 0.9, 0.4))
M_SILK = principled("silk", (0.8, 0.8, 0.78), rough=0.6)
M_HASL = principled("hasl", (0.75, 0.75, 0.74), metal=1.0, rough=0.3)
M_TABLE = principled("table", (0.16, 0.09, 0.05), rough=0.45)

board_body.data.materials[0] = M_FR4
for o in mask: o.data.materials[0] = M_MASK
for o in silk: o.data.materials[0] = M_SILK
for o in copper: o.data.materials[0] = M_HASL
for o in mask + silk:   # lift flat films clear of the copper surface to avoid z-fighting
    o.location.z += 0.00002 if o in mask else 0.00004

# Component materials: keep colours, fix the importer's metallic=1/rough=1.
for m in list(bpy.data.materials):
    if not m.name.startswith("mat_"):
        continue
    b = m.node_tree.nodes.get("Principled BSDF")
    c = tuple(b.inputs["Base Color"].default_value)[:3]
    greyish = max(c) - min(c) < 0.06 and max(c) > 0.4
    b.inputs["Metallic"].default_value = 1.0 if greyish else 0.0
    b.inputs["Roughness"].default_value = 0.35 if greyish else 0.4

# The 1206 cap model is orange; a real X5R 1206 is beige-brown.
bpy.data.materials["mat_13"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.45, 0.32, 0.2, 1)

# Imported custom normals on the holder are garbage (crumpled-foil look): drop them, shade flat.
for name in ("BAT1",):
    o = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    if o.data.has_custom_normals:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for p in o.data.polygons: p.use_smooth = False
    o.select_set(False)

# A CR2032 in the holder (stainless, 20 x 3.2 mm), centred on the holder's origin.
bpy.context.view_layer.update()
bat = bpy.data.objects["BAT1"]
bc = bat.matrix_world.translation
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.01, depth=0.0032, location=(bc.x, bc.y, bc.z + 0.0004 + 0.0016))
cell = bpy.context.object
for p in cell.data.polygons: p.use_smooth = abs(p.normal.z) < 0.5   # smooth side, flat faces
# JISP is holes only on the real board (header not fitted): drop its model.
bpy.data.objects.remove(bpy.data.objects["JISP"])
cell.data.materials.append(principled("cell", (0.78, 0.78, 0.8), metal=1.0, rough=0.22))

# LEDs: lens (mat_8) becomes clear epoxy that emits; one material per seat so each can be switched.
seat_mats = {}
lens_area = None
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("LED"):
        seat = int(o.name[3])
        if seat not in seat_mats:
            m = principled(f"lens_seat{seat}", (0.95, 0.95, 0.95), rough=0.08, trans=1.0)
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Emission Color"].default_value = (*RED, 1)
            seat_mats[seat] = m
        idx = [i for i, mm in enumerate(o.data.materials) if mm.name.startswith("mat_8")][0]
        o.data.materials[idx] = seat_mats[seat]
        o.data.materials[[i for i, mm in enumerate(o.data.materials) if mm.name.startswith("mat_9")][0]] = \
            principled("die", (0.5, 0.1, 0.05), rough=0.4)
        if lens_area is None:  # top-facing area of the lens, in m^2 (world scale)
            s = o.matrix_world.to_scale()
            lens_area = sum(p.area for p in o.data.polygons if p.material_index == idx and p.normal.z > 0.7) * s.x * s.y

# Lambertian lens: on-axis intensity I = S * LUM * A / pi  (Blender W/sr; 683 lm/W)
LED_STRENGTH = math.pi * (LED_MCD / 1000 / 683) / (LUM * lens_area)
print(f"lens top area {lens_area*1e6:.3f} mm^2, emission strength {LED_STRENGTH:.0f}")

# --- room -------------------------------------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, -0.00001))
table = bpy.context.object
table.data.materials.append(M_TABLE)

# Ceiling panel: small-source approx E = P/(pi d^2)  ->  P = E/683 * pi d^2. Offset so it isn't straight down.
bpy.ops.object.light_add(type="AREA", location=(0.4, -0.3, CEIL_H))
ceil = bpy.context.object
ceil.data.shape = "RECTANGLE"; ceil.data.size = 1.2; ceil.data.size_y = 0.6
ceil.data.color = (1.0, 0.93, 0.85)    # warm white
d2 = 0.4 ** 2 + 0.3 ** 2 + CEIL_H ** 2
ceil.data.energy = (ROOM_LUX * 0.8 / 683) * math.pi * d2 / (CEIL_H / math.sqrt(d2))
ceil.rotation_euler = (Vector((0, 0, 0)) - ceil.location).to_track_quat("-Z", "Y").to_euler()

world = bpy.data.worlds.new("room"); sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.9, 0.88, 0.85, 1)
WORLD_STRENGTH = ROOM_LUX * 0.2 / 683 / math.pi   # ambient fill = 20% of the room light

# --- cameras: eyes of seated players, ~0.6 m away, ~35 deg up ---------------------------------------------------
def cam(name, az_deg, el_deg, dist=0.6, lens=150):
    az, el = math.radians(az_deg), math.radians(el_deg)
    loc = Vector((dist * math.cos(el) * math.cos(az), dist * math.cos(el) * math.sin(az), dist * math.sin(el)))
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    sc.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (Vector((0, 0, 0.004)) - loc).to_track_quat("-Z", "Y").to_euler()
    c.data.lens = lens
    c.data.sensor_width = 36
    return c

views = {
    "side": cam("side", 0, 35, 0.6, 190),          # across the table, from beside seats 1-4 (+x side)
    "far": cam("far", 180, 25, 0.8, 230),      # from the other side, further away and lower
    "end": cam("end", -90, 30, 0.6, 160),  # from the short end
    "corner": cam("corner", -40, 22, 0.8, 220),
    "top": cam("top", 0, 89.9, 0.6, 140),
}

# --- render settings --------------------------------------------------------------------------------------------
sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices: d.use = d.type == "OPTIX"
sc.cycles.device = "GPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPTIX"
sc.cycles.max_bounces = 12
sc.cycles.blur_glossy = 1.0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = 0
sc.render.image_settings.file_format = "OPEN_EXR"
sc.render.image_settings.color_depth = "16"
sc.render.image_settings.exr_codec = "DWAA"

def set_layer(layer):
    room = layer == "room"
    ceil.hide_render = not room
    bg.inputs["Strength"].default_value = WORLD_STRENGTH if room else 0.0
    for s, m in seat_mats.items():
        m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = \
            LED_STRENGTH if layer == f"seat{s}" else 0.0

vnames = list(views) if VIEWS == "all" else VIEWS.split(",")
lnames = ["room"] + [f"seat{s}" for s in range(1, 9)] if LAYERS == "all" else LAYERS.split(",")
for v in vnames:
    sc.camera = views[v]
    for l in lnames:
        set_layer(l)
        sc.render.filepath = os.path.join(OUT, f"{v}_{l}.exr")
        bpy.ops.render.render(write_still=True)
        print("WROTE", sc.render.filepath)

# Exposure for viewing: 18% grey under ROOM_LUX should show as 0.18.
print("EXPOSURE_SCALE", 0.18 / (0.18 * ROOM_LUX / 683 / math.pi))
