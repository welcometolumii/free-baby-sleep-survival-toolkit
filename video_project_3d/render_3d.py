"""Animated software 3D renderer: stick figure synced to voiceover."""
import math
import numpy as np
import os
from PIL import Image, ImageDraw

W, H = 640, 360
FPS = 24
DURATION_SEC = 207.41
TOTAL_FRAMES = int(DURATION_SEC * FPS)

SKY_TOP = (25, 30, 50)
SKY_BOT = (100, 150, 200)
GROUND = (160, 160, 170)
HORIZON = (80, 90, 100)
RED = (240, 80, 80)
TEAL = (80, 200, 200)
GREY = (180, 180, 190)
WHITE = (255, 255, 255)
BLACK = (30, 30, 35)

LIGHT = np.array([0.4, -0.4, 0.8], dtype=float)
LIGHT = LIGHT / np.linalg.norm(LIGHT)

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def project(points, cam_pos, cam_rot, fov=60):
    forward = cam_rot @ np.array([0, 0, -1])
    up = cam_rot @ np.array([0, 1, 0])
    right = np.cross(forward, up)
    right = right / np.linalg.norm(right)
    up = up / np.linalg.norm(up)
    forward = forward / np.linalg.norm(forward)
    aspect = W / H
    f = 1.0 / math.tan(math.radians(fov) / 2)
    sx = np.zeros(len(points)); sy = np.zeros(len(points))
    depth = np.zeros(len(points)); valid = np.ones(len(points), dtype=bool)
    for i, p in enumerate(points):
        rel = p - cam_pos
        dz = float(np.dot(rel, forward))
        if dz <= 0.1:
            valid[i] = False; continue
        dx = float(np.dot(rel, right)); dy = float(np.dot(rel, up))
        sx[i] = W / 2 + dx * f * W / (dz * aspect)
        sy[i] = H / 2 - dy * f * H / dz
        depth[i] = dz
    return sx, sy, depth, valid

class StickFigure:
    def __init__(self, x=0, y=0, z=-0.5, jacket_color=RED):
        self.base = (x, y, z)
        self.jacket_color = jacket_color
        self.Hh = 1.8

    def joints(self, t, walk=0.0, lean=0.0, loc=None):
        Hh = self.Hh
        s = math.sin(walk); c = math.cos(walk)
        x, y, z = loc if loc else self.base
        j = {
            'head':       np.array([x, y, z + Hh + 0.25]),
            'neck':       np.array([x, y, z + Hh + 0.10]),
            'chest':      np.array([x, y, z + Hh - 0.40]),
            'hip':        np.array([x, y, z + Hh - 0.75]),
            'l_shoulder': np.array([x - 0.22, y, z + Hh - 0.50]),
            'l_elbow':    np.array([x - 0.22 - s*0.15, y, z + Hh - 1.00]),
            'l_hand':     np.array([x - 0.22 - s*0.18, y, z + Hh - 1.40]),
            'r_shoulder': np.array([x + 0.22, y, z + Hh - 0.50]),
            'r_elbow':    np.array([x + 0.22 + s*0.15, y, z + Hh - 1.00]),
            'r_hand':     np.array([x + 0.22 + s*0.18, y, z + Hh - 1.40]),
            'l_hip':      np.array([x - 0.12, y, z + Hh - 0.80]),
            'l_knee':     np.array([x - 0.12 + s*0.12, y, z + Hh - 1.40]),
            'l_ankle':    np.array([x - 0.12 + s*0.10, y, z + Hh - 2.00]),
            'l_foot':     np.array([x - 0.12 + s*0.08, y, z + Hh - 2.15]),
            'r_hip':      np.array([x + 0.12, y, z + Hh - 0.80]),
            'r_knee':     np.array([x + 0.12 - s*0.12, y, z + Hh - 1.40]),
            'r_ankle':    np.array([x + 0.12 - s*0.10, y, z + Hh - 2.00]),
            'r_foot':     np.array([x + 0.12 - s*0.08, y, z + Hh - 2.15]),
        }
        bones = [
            ('head', 'neck', WHITE, 10),
            ('neck', 'chest', self.jacket_color, 6),
            ('chest', 'hip', self.jacket_color, 6),
            ('chest', 'l_shoulder', self.jacket_color, 5),
            ('chest', 'r_shoulder', self.jacket_color, 5),
            ('l_shoulder', 'l_elbow', self.jacket_color, 5),
            ('l_elbow', 'l_hand', BLACK, 5),
            ('r_shoulder', 'r_elbow', self.jacket_color, 5),
            ('r_elbow', 'r_hand', BLACK, 5),
            ('hip', 'l_hip', GREY, 6),
            ('l_hip', 'l_knee', GREY, 6),
            ('l_knee', 'l_ankle', GREY, 6),
            ('l_ankle', 'l_foot', BLACK, 6),
            ('hip', 'r_hip', GREY, 6),
            ('r_hip', 'r_knee', GREY, 6),
            ('r_knee', 'r_ankle', GREY, 6),
            ('r_ankle', 'r_foot', BLACK, 6),
        ]
        return j, bones

    def transform(self, j, loc, lean=0.0, rot_z_angle=0.0):
        rz = rot_z(rot_z_angle + lean)
        return {k: (rz @ v) + np.array(loc) for k, v in j.items()}

SHOTS = [
    (1,       600,   "open"),
    (601,    1200,   "walk"),
    (1201,   1800,   "think"),
    (1801,   2400,   "talk"),
    (2401,   3000,   "move"),
    (3001,   3600,   "pause"),
    (3601,   4200,   "act"),
    (4201,   TOTAL_FRAMES, "end"),
]

def get_shot(f):
    for sf, ef, desc in SHOTS:
        if sf <= f <= ef:
            return desc, sf, ef
    return "end", SHOTS[-1][0], SHOTS[-1][1]

def camera(desc, f, sf):
    u = (f - sf) / 600.0
    t = f / FPS
    if desc == "open":
        return np.array([0.0, -10.0, 3.5]), rot_x(math.radians(70)), (0, 0, -0.5), t*0.15, 0.03*math.sin(t*0.05), 0.0
    elif desc == "walk":
        x = u * 4.0
        return np.array([x, -10.0 - x*0.3, 3.5]), rot_x(math.radians(70)), (x, 0, -0.5), t*0.4, 0.1, 0.0
    elif desc == "think":
        return np.array([3.0, -7.0, 3.5]), rot_x(math.radians(60)) @ rot_z(math.radians(25)), (3, 0, -0.5), 0.0, 0.0, 0.0
    elif desc == "talk":
        ang = math.radians(35 * math.sin(u*6))
        return np.array([4.0, -5.0, 2.8]), rot_x(math.radians(68)) @ rot_z(ang), (4, 0, -0.5), 0.0, 0.0, ang
    elif desc == "move":
        x = u * 6.0 - 3.0
        return np.array([x, -7.0 - abs(x)*0.2, 3.0]), rot_x(math.radians(72)), (x, 0, -0.5), t*0.5, 0.15, 0.0
    elif desc == "pause":
        return np.array([0.0, -11.0, 4.0]), rot_x(math.radians(65)), (0, 0, -0.5), 0.0, 0.0, 0.0
    elif desc == "act":
        sv = math.sin(u*4)
        return np.array([2.0, -6.0, 3.0]), rot_x(math.radians(72)) @ rot_z(sv*0.25), (2, 0, -0.5), 0.0, sv*0.25, sv*0.25
    elif desc == "end":
        return np.array([0.0, -10.0, 4.0]), rot_x(math.radians(68)), (0, 0, -0.5), 0.0, 0.0, 0.0
    return np.array([0.0, -10.0, 3.5]), rot_x(math.radians(70)), (0, 0, -0.5), 0.0, 0.0, 0.0

def draw_gradient(draw, top, bot):
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)],
                  fill=(int(top[0]*(1-t)+bot[0]*t),
                        int(top[1]*(1-t)+bot[1]*t),
                        int(top[2]*(1-t)+bot[2]*t)))

def render_frame(f, cam_pos, cam_rot, hero_loc, walk, lean, rot_z_angle, hero):
    img = Image.new("RGB", (W, H), SKY_TOP)
    draw = ImageDraw.Draw(img)
    draw_gradient(draw, SKY_TOP, SKY_BOT)
    hy = int(H * 0.62)
    draw.line([(0, hy), (W, hy)], fill=HORIZON, width=3)
    draw.rectangle([0, hy, W, H], fill=GROUND)

    j, bones = hero.joints(f / FPS, walk=walk, lean=lean, loc=hero_loc)
    j = hero.transform(j, hero_loc, lean=lean, rot_z_angle=rot_z_angle)

    names = list(j.keys())
    pts = np.array([j[n] for n in names])
    sx, sy, depth, valid = project(pts, cam_pos, cam_rot)

    bone_draw = []
    for ja, jb, color, width in bones:
        ia, ib = names.index(ja), names.index(jb)
        if valid[ia] and valid[ib]:
            bone_draw.append(((sx[ia], sy[ia]), (sx[ib], sy[ib]),
                             (depth[ia] + depth[ib]) / 2, color, width))

    bone_draw.sort(key=lambda b: -b[2])
    for (p1, p2, d, color, width) in bone_draw:
        offscreen1 = p1[0] < -100 or p1[0] > W+100 or p1[1] < -100 or p1[1] > H+100
        offscreen2 = p2[0] < -100 or p2[0] > W+100 or p2[1] < -100 or p2[1] > H+100
        if offscreen1 and offscreen2:
            continue
        draw.line([p1, p2], fill=color, width=width)

    for i, name in enumerate(names):
        if not valid[i]:
            continue
        x, y = sx[i], sy[i]
        if x < -20 or x > W+20 or y < -20 or y > H+20:
            continue
        if name == 'head':
            col, r = WHITE, 10
        elif 'foot' in name or 'hand' in name:
            col, r = BLACK, 7
        else:
            col, r = GREY, 6
        draw.ellipse([x-r, y-r, x+r, y+r], fill=col, outline=BLACK)

    return img

if __name__ == "__main__":
    hero = StickFigure()
    outdir = "/workspace/app/video_project_3d/frames"
    os.makedirs(outdir, exist_ok=True)

    print(f"Rendering {TOTAL_FRAMES} frames at {FPS}fps ({DURATION_SEC}s)")
    prev = None
    for f in range(1, TOTAL_FRAMES + 1):
        t = f / FPS
        desc, sf, ef = get_shot(f)
        cam_pos, cam_rot, hero_loc, walk, lean, rot_z_angle = camera(desc, f, sf)
        img = render_frame(f, cam_pos, cam_rot, hero_loc, walk, lean, rot_z_angle, hero)
        img.save(f"{outdir}/frame_{f:04d}.png")

        if f <= 5:
            arr = np.asarray(img)
            if prev is not None:
                diff = np.abs(arr.astype(int) - prev.astype(int)).mean()
                print(f"  Frame {f} ({desc}): diff_from_prev={diff:.2f}")
            prev = arr

        if f % 1000 == 0:
            print(f"  Frame {f}/{TOTAL_FRAMES} ({t:.1f}s)")

    print("Done rendering all frames")
