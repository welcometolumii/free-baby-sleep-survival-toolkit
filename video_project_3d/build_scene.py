import bpy
import math
import os

# ---------------- SETTINGS ----------------
W, H = 640, 360
FPS = 24
DURATION_SEC = 207.41
TOTAL_FRAMES = int(DURATION_SEC * FPS)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.resolution_percentage = 100
scene.display.shading.type = 'SOLID'
scene.display.shading.use_scene_lights_render = True
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_depth = '8'
scene.render.film_transparent = False

# World - dark night
world = bpy.data.worlds["World"]
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.03, 0.03, 0.05, 1.0)
bg.inputs[1].default_value = 1.0

# ---------------- CLEAN DEFAULT OBJECTS ----------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ---------------- MATERIALS ----------------
def mat(name, color, emission=0.0, rough=0.5, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Emission Strength"].default_value = emission
    return m

RED    = mat("Red",   (0.85, 0.20, 0.20))
TEAL   = mat("Teal",  (0.20, 0.60, 0.60))
GREY   = mat("Grey",  (0.50, 0.50, 0.55), rough=0.8)
WHITE  = mat("White", (0.95, 0.95, 0.97), rough=0.2)
BLACK  = mat("Black", (0.06, 0.06, 0.08))
GOLD   = mat("Gold",  (0.95, 0.80, 0.25), emission=0.5)
BLUE   = mat("Blue",  (0.30, 0.45, 0.80))
FLOOR  = mat("Floor", (0.25, 0.22, 0.20), rough=0.9)
WALL   = mat("Wall",  (0.18, 0.16, 0.22), rough=0.9)

# ---------------- LIGHTING ----------------
def make_lighting():
    # Sun light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 8))
    sun = bpy.context.active_object
    sun.name = "sun"
    sun.data.energy = 3.0
    sun.data.color = (1.0, 0.95, 0.85)
    sun.rotation_euler = (math.radians(45), math.radians(30), 0)

    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-5, -5, 6))
    fill = bpy.context.active_object
    fill.name = "fill"
    fill.data.energy = 50.0
    fill.data.color = (0.8, 0.9, 1.0)
    fill.data.size = 4

    # Rim light
    bpy.ops.object.light_add(type='AREA', location=(0, 8, 4))
    rim = bpy.context.active_object
    rim.name = "rim"
    rim.data.energy = 80.0
    rim.data.color = (1.0, 0.8, 0.6)
    rim.data.size = 3

# ---------------- ENVIRONMENT ----------------
def make_room():
    # Floor - large plane
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.5))
    floor = bpy.context.active_object
    floor.name = "floor"
    floor.data.materials.append(FLOOR)

    # Back wall
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 8, 3))
    wall = bpy.context.active_object
    wall.name = "back_wall"
    wall.rotation_euler = (math.pi/2, 0, 0)
    wall.data.materials.append(WALL)

    # Side walls
    bpy.ops.mesh.primitive_plane_add(size=20, location=(-15, 0, 3))
    wall_l = bpy.context.active_object
    wall_l.name = "left_wall"
    wall_l.rotation_euler = (0, math.pi/2, 0)
    wall_l.data.materials.append(WALL)

    bpy.ops.mesh.primitive_plane_add(size=20, location=(15, 0, 3))
    wall_r = bpy.context.active_object
    wall_r.name = "right_wall"
    wall_r.rotation_euler = (0, -math.pi/2, 0)
    wall_r.data.materials.append(WALL)

    # Table
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2, 0.4))
    table = bpy.context.active_object
    table.name = "table"
    table.scale = (1.5, 1.0, 0.4)
    table.data.materials.append(RED)

# ---------------- 3D STICK FIGURE (LARGER, MORE VISIBLE) ----------------
def make_stick_figure(name, jacket_color=RED):
    """Build a 3D stick figure from cylinders + spheres. Larger scale."""
    parts = {}
    Hh = 2.0  # height in meters

    def cyl(name_, loc, rot, scale, mat_):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=1.0, location=loc)
        o = bpy.context.active_object
        o.name = name_
        o.rotation_euler = rot
        o.scale = scale
        o.data.materials.append(mat_)
        return o

    def sph(name_, loc, radius, mat_):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=24, ring_count=12)
        o = bpy.context.active_object
        o.name = name_
        o.scale = (radius, radius, radius)
        o.data.materials.append(mat_)
        return o

    # Head
    parts['head'] = sph(f"{name}_head", (0, 0, Hh + 0.3), 0.16, BLACK)
    # Torso
    parts['torso'] = cyl(f"{name}_torso", (0, 0, Hh - 0.4), (math.pi/2, 0, 0), (0.09, 0.09, 0.55), jacket_color)
    # Hips
    parts['hip'] = sph(f"{name}_hip", (0, 0, Hh - 0.75), 0.07, BLACK)
    # Upper legs
    parts['leg_l'] = cyl(f"{name}_leg_l", (-0.16, 0, Hh - 1.1), (math.pi/2, 0, 0.15), (0.08, 0.08, 1.0), GREY)
    parts['leg_r'] = cyl(f"{name}_leg_r", (0.16, 0, Hh - 1.1), (math.pi/2, 0, -0.15), (0.08, 0.08, 1.0), GREY)
    # Lower legs
    parts['shin_l'] = cyl(f"{name}_shin_l", (-0.16, 0, Hh - 1.9), (math.pi/2, 0, 0.15), (0.08, 0.08, 0.8), GREY)
    parts['shin_r'] = cyl(f"{name}_shin_r", (0.16, 0, Hh - 1.9), (math.pi/2, 0, -0.15), (0.08, 0.08, 0.8), GREY)
    # Feet
    parts['foot_l'] = sph(f"{name}_foot_l", (-0.16, 0, Hh - 2.25), 0.07, BLACK)
    parts['foot_r'] = sph(f"{name}_foot_r", (0.16, 0, Hh - 2.25), 0.07, BLACK)
    # Upper arms
    parts['arm_l'] = cyl(f"{name}_arm_l", (-0.28, 0, Hh - 0.5), (math.pi/2, 0, 0.5), (0.07, 0.07, 0.4), jacket_color)
    parts['arm_r'] = cyl(f"{name}_arm_r", (0.28, 0, Hh - 0.5), (math.pi/2, 0, -0.5), (0.07, 0.07, 0.4), jacket_color)
    # Forearms
    parts['fore_l'] = cyl(f"{name}_fore_l", (-0.28, 0, Hh - 1.1), (math.pi/2, 0, 0.5), (0.06, 0.06, 0.4), BLACK)
    parts['fore_r'] = cyl(f"{name}_fore_r", (0.28, 0, Hh - 1.1), (math.pi/2, 0, -0.5), (0.06, 0.06, 0.4), BLACK)
    # Hands
    parts['hand_l'] = sph(f"{name}_hand_l", (-0.28, 0, Hh - 1.5), 0.06, BLACK)
    parts['hand_r'] = sph(f"{name}_hand_r", (0.28, 0, Hh - 1.5), 0.06, BLACK)

    # Parent everything to root empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, -0.5))
    root = bpy.context.active_object
    root.name = f"{name}_root"
    for p in parts.values():
        p.parent = root
    parts['root'] = root
    return parts

def set_pose(fig, frame, walk_phase=0.0, lean=0.0, arm_swing=0.0, loc=(0,0,-0.5), scale=1.0):
    """Animate stick figure pose at a given frame with keyframes."""
    root = fig['root']
    root.location = loc
    root.scale = (scale, scale, scale)
    root.rotation_euler = (0, 0, lean)
    root.keyframe_insert(data_path="location", frame=frame)
    root.keyframe_insert(data_path="scale", frame=frame)
    root.keyframe_insert(data_path="rotation_euler", frame=frame)

    Hh = 2.0
    s = math.sin(walk_phase)
    c = math.cos(walk_phase)

    # Legs walk cycle
    fig['leg_l'].rotation_euler = (math.pi/2, s*0.7, 0.3*s)
    fig['leg_l'].keyframe_insert(data_path="rotation_euler", frame=frame)
    fig['shin_l'].rotation_euler = (math.pi/2, -c*0.9, 0.3*s)
    fig['shin_l'].keyframe_insert(data_path="rotation_euler", frame=frame)
    fig['foot_l'].location = (-0.16 + s*0.1, 0, Hh - 2.25 + abs(c)*0.06)
    fig['foot_l'].keyframe_insert(data_path="location", frame=frame)

    fig['leg_r'].rotation_euler = (math.pi/2, -s*0.7, -0.3*s)
    fig['leg_r'].keyframe_insert(data_path="rotation_euler", frame=frame)
    fig['shin_r'].rotation_euler = (math.pi/2, c*0.9, -0.3*s)
    fig['shin_r'].keyframe_insert(data_path="rotation_euler", frame=frame)
    fig['foot_r'].location = (0.16 - s*0.1, 0, Hh - 2.25 + abs(c)*0.06)
    fig['foot_r'].keyframe_insert(data_path="location", frame=frame)

    # Arms swing opposite
    fig['arm_l'].rotation_euler = (math.pi/2, -s*0.9, -0.5 + arm_swing)
    fig['arm_l'].keyframe_insert(data_path="rotation_euler", frame=frame)
    fig['fore_l'].rotation_euler = (math.pi/2, c*0.7, -0.5 + arm_swing)
    fig['fore_l'].keyframe_insert(data_path="rotation_euler", frame=frame)
    fig['hand_l'].location = (-0.28 - s*0.12, 0, Hh - 1.5)
    fig['hand_l'].keyframe_insert(data_path="location", frame=frame)

    fig['arm_r'].rotation_euler = (math.pi/2, s*0.9, 0.5 - arm_swing)
    fig['arm_r'].keyframe_insert(data_path="rotation_euler", frame=frame)
    fig['fore_r'].rotation_euler = (math.pi/2, -c*0.7, 0.5 - arm_swing)
    fig['fore_r'].keyframe_insert(data_path="rotation_euler", frame=frame)
    fig['hand_r'].location = (0.28 + s*0.12, 0, Hh - 1.5)
    fig['hand_r'].keyframe_insert(data_path="location", frame=frame)

    # Head bob and slight turn
    fig['head'].location = (0, 0, Hh + 0.3 + abs(s)*0.04)
    fig['head'].keyframe_insert(data_path="location", frame=frame)
    fig['head'].rotation_euler = (0, 0, s*0.15)
    fig['head'].keyframe_insert(data_path="rotation_euler", frame=frame)

# ---------------- CAMERA ----------------
def setup_camera():
    bpy.ops.object.camera_add(location=(0, -10, 3.5))
    cam = bpy.context.active_object
    cam.name = "hero_camera"
    cam.rotation_euler = (math.radians(70), 0, 0)
    cam.data.lens = 35
    scene.camera = cam
    return cam

def cam_keyframe(cam, frame, loc, rot):
    cam.location = loc
    cam.rotation_euler = rot
    cam.keyframe_insert(data_path="location", frame=frame)
    cam.keyframe_insert(data_path="rotation_euler", frame=frame)

# ---------------- TEXT OVERLAYS ----------------
def add_text(text, frame_start, frame_end, loc=(0, 5, 2), size=2, color=(1,1,1,1)):
    bpy.ops.object.text_add(location=loc)
    txt = bpy.context.active_object
    txt.name = f"text_{text[:10]}"
    txt.data.body = text
    txt.data.size = size
    txt.data.align_x = 'CENTER'
    txt.data.align_y = 'CENTER'
    txt.rotation_euler = (math.pi/2, 0, 0)
    txt.data.materials.append(WHITE)
    txt.hide_render = True
    txt.keyframe_insert(data_path="hide_render", frame=frame_start - 1)
    txt.hide_render = False
    txt.keyframe_insert(data_path="hide_render", frame=frame_start)
    txt.hide_render = True
    txt.keyframe_insert(data_path="hide_render", frame=frame_end + 1)
    return txt

# ---------------- BUILD SCENE ----------------
make_lighting()
make_room()
cam = setup_camera()
hero = make_stick_figure("hero")

# ---------------- ANIMATION SHOTS ----------------
SHOTS = [
    (1,        600,   "open"),
    (601,      1200,  "walk"),
    (1201,     1800,  "think"),
    (1801,     2400,  "talk"),
    (2401,     3000,  "move"),
    (3001,     3600,  "pause"),
    (3601,     4200,  "act"),
    (4201,     TOTAL_FRAMES, "end"),
]

for (sf, ef, desc) in SHOTS:
    if desc == "open":
        cam_keyframe(cam, sf, (0, -10, 3.5), (math.radians(70), 0, 0))
        set_pose(hero, sf, walk_phase=0, lean=0, loc=(0,0,-0.5), scale=1.0)
        for f in range(sf, ef+1, 6):
            set_pose(hero, f, walk_phase=f*0.15, lean=0.03*math.sin(f*0.05), loc=(0,0,-0.5), scale=1.0)
    elif desc == "walk":
        for f in range(sf, ef+1, 6):
            x = (f - sf) * 0.02
            cam_keyframe(cam, f, (x, -10 - x*0.3, 3.5), (math.radians(70), 0, 0))
            set_pose(hero, f, walk_phase=f*0.4, lean=0.1, loc=(x,0,-0.5), scale=1.0)
    elif desc == "think":
        for f in range(sf, ef+1, 6):
            cam_keyframe(cam, f, (3, -7, 3.5), (math.radians(60), 0, math.radians(25)))
            set_pose(hero, f, walk_phase=0, lean=0, loc=(3,0,-0.5), scale=1.0)
            fig = hero
            fig['arm_l'].rotation_euler = (math.pi/2, 0, 1.8)
            fig['arm_l'].keyframe_insert(data_path="rotation_euler", frame=f)
            fig['hand_l'].location = (-0.28, 0, 2.0 - 0.75 + 0.8)
            fig['hand_l'].keyframe_insert(data_path="location", frame=f)
    elif desc == "talk":
        for f in range(sf, ef+1, 6):
            ang = math.radians(35 * math.sin((f-sf)*0.06))
            cam_keyframe(cam, f, (4, -5, 2.8), (math.radians(68), 0, ang))
            set_pose(hero, f, walk_phase=0, lean=0, loc=(4,0,-0.5), scale=1.0)
            fig = hero
            fig['head'].rotation_euler = (0, 0, ang)
            fig['head'].keyframe_insert(data_path="rotation_euler", frame=f)
    elif desc == "move":
        for f in range(sf, ef+1, 6):
            x = (f - sf) * 0.03 - 3
            cam_keyframe(cam, f, (x, -7 - abs(x)*0.2, 3.0), (math.radians(72), 0, 0))
            set_pose(hero, f, walk_phase=f*0.5, lean=0.15, loc=(x,0,-0.5), scale=1.0)
    elif desc == "pause":
        for f in range(sf, ef+1, 6):
            cam_keyframe(cam, f, (0, -11, 4), (math.radians(65), 0, 0))
            set_pose(hero, f, walk_phase=0, lean=0, loc=(0,0,-0.5), scale=1.0)
    elif desc == "act":
        for f in range(sf, ef+1, 6):
            s = math.sin((f-sf)*0.12)
            cam_keyframe(cam, f, (2, -6, 3), (math.radians(72), 0, s*0.25))
            set_pose(hero, f, walk_phase=0, lean=s*0.25, loc=(2,0,-0.5), scale=1.0)
            fig = hero
            fig['arm_r'].rotation_euler = (math.pi/2, s*1.4, 0.5 + s*0.6)
            fig['arm_r'].keyframe_insert(data_path="rotation_euler", frame=f)
    elif desc == "end":
        for f in range(sf, ef+1, 12):
            cam_keyframe(cam, f, (0, -10, 4), (math.radians(68), 0, 0))
            set_pose(hero, f, walk_phase=0, lean=0, loc=(0,0,-0.5), scale=1.0)

add_text("3D EXPLAINER", 1, 120, loc=(0, 6, 2.5), size=3)

# ---------------- OUTPUT ----------------
scene.render.filepath = "/workspace/app/video_project_3d/frames/"
os.makedirs("/workspace/app/video_project_3d/frames", exist_ok=True)

# Save blend
bpy.ops.wm.save_as_mainfile(filepath="/workspace/app/video_project_3d/scene.blend")

print(f"Scene ready: {TOTAL_FRAMES} frames at {FPS}fps ({DURATION_SEC}s)")
print(f"Camera: {cam.name} at {cam.location}")
print(f"Hero root: {hero['root'].name} at {hero['root'].location}")
print(f"Sun: {bpy.data.objects.get('sun')}")
print(f"Fill: {bpy.data.objects.get('fill')}")
print(f"Rim: {bpy.data.objects.get('rim')}")
