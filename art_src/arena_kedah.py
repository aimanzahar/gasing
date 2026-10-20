"""Kedah arena -- harvest time on the Muda plain under a clear blue sky (design_art.md section c, USER_SPEC Kedah).
Ground: round threshing ground (packed earth, straw litter) in a patchwork of paddy plots that step down in
shallow terraces from a raised concrete canal: ripe gold rice, cut stubble with sheaf stooks, young green and
flooded plots. Apron: guni rice sacks, nyiru tray, sickles, grain mat; tong banting thresher on the platform rim.
Far band: concrete canal with a row of wheel sluice gates (one open, spilling into a flooded plot), footbridge.
Left flank: jelapang rice barn on a kampung mound (palms, banana, sacks). Right flank: kerbau in a mud wallow
under a shade tree, sheaf stooks on the stubble. Far set (vista): endless paddy patchwork, kampung tree islands,
layered tree lines, Gunung Jerai, relief cumulus clouds.

  blender -b --factory-startup -P art_src/arena_kedah.py -- --export --render game,vista --out <dir>

Also the shared helper module for arena_perak.py / arena_pahang.py (vista layers, clouds, skirt, blobs).
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import bpy, bmesh
import arenakit as K
importlib.reload(K)  # blender-mcp re-runs
import numpy as np
from mathutils import Vector
from arenakit import P, xf, aim, join, paint, tint, nz, smooth01

# Godot ARENA_DEFS["kedah"] recommendation (+ b_* = Blender preview factors only)
MOOD = {"sky_top": (0.24, 0.47, 0.82), "sky_horizon": (0.86, 0.85, 0.74), "fog": (0.78, 0.80, 0.78),
        "fog_density": 0.0028, "sun_color": (1.0, 0.91, 0.74), "sun_energy": 1.15,
        "lantern": (1.0, 0.80, 0.50), "lantern_energy": 1.0, "exposure": 0.85, "ambient": 0.5,
        "b_sun": 4.0, "b_world": 1.0, "b_fill": 0.4, "b_lantern": 6.0}

# ================================================================ shared helpers (perak / pahang import these)
CAM_V = (-1.5, -12.5)          # vista camera (Blender xy), looks toward +y, yaw range ~ -45..+34 deg


def in_vista(x, y):
    dx, dy = x - CAM_V[0], y - CAM_V[1]
    return dy > 2 and -58 < math.degrees(math.atan2(dx, dy)) < 44


def in_battle(x, y, pad=0.0):
    """ground-level footprint of the battle camera (Godot (0,9,7) -> origin, FOV 55, 16:9)."""
    if y < -5.6 - pad or y > 13.2 + pad:
        return False
    return abs(x) < 0.9255 * (9 * 0.789 + (y + 7) * 0.614) + 0.6 + pad


def visible(x, y, pad=0.0):
    return in_battle(x, y, pad) or in_vista(x, y)


def vpt(yaw_deg, d):
    """point at yaw (deg, + toward +x) and distance d from the vista camera."""
    a = math.radians(yaw_deg)
    return CAM_V[0] + d * math.sin(a), CAM_V[1] + d * math.cos(a)


def mix(a, b, t):
    return np.asarray(a, dtype=float) * (1 - t) + np.asarray(b, dtype=float) * t


def blob(r=(1, 1, 1), sub=2, seed=0, amp=0.0, freq=1.5):
    """smooth ellipsoid (icosphere), centred at the origin; optional noise lumps."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    o = Vector((seed * 3.1, seed * 1.7, seed * 0.9))
    for v in bm.verts:
        d = v.co.normalized()
        k = 1.0 + (amp * K.mnoise.noise(d * freq + o) if amp else 0.0)
        v.co = Vector((d.x * k * r[0], d.y * k * r[1], d.z * k * r[2]))
    return K.from_bm(bm)


def pillow(sx, sy, sz, seed=0, ears=True):
    """stuffed sack: rounded box with slack lumps and tied corner ears; base at z=0."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    rng = random.Random(seed)
    o = Vector((seed * 2.3, seed * 0.7, 1.1))
    for v in bm.verts:
        d = v.co.normalized()
        q = Vector([math.copysign(abs(c) ** 0.55, c) for c in d])
        q /= max(abs(q.x), abs(q.y), abs(q.z))
        q = q.lerp(d, 0.35)
        k = 1 + 0.07 * K.mnoise.noise(d * 2.2 + o)
        v.co = Vector((q.x * sx * 0.5 * k, q.y * sy * 0.5 * k, q.z * sz * 0.5 * k))
        if v.co.z < -sz * 0.36:
            v.co.z = -sz * 0.36 - (v.co.z + sz * 0.36) * 0.25
    p = K.from_bm(bm)
    p.v[:, 2] -= p.v[:, 2].min()
    if ears:
        e = [K.xf(K.lathe([(0.0, 0.0), (0.045, 0.0), (0.03, 0.05), (0.05, 0.1), (0.0, 0.12)], seg=6),
                  (sgn * sx * 0.46, rng.uniform(-0.1, 0.1) * sy, sz * 0.45), (0, sgn * 1.2, 0)) for sgn in (-1, 1)]
        p = join(p, e)
    return p


def band(rr, a0, a1, hfn, depth, n=72, z0=-0.3, prof=None):
    """layered far silhouette (tree line / ridge / hill) lofted along an arc of radius rr around the vista
    camera from yaw a0 to a1 (deg). hfn(yaw) -> crest height. prof: [(radial offset frac, height frac)]."""
    prof = prof or [(-1.0, 0.0), (-0.62, 0.55), (-0.25, 0.92), (0.1, 1.0), (0.55, 0.72), (1.0, 0.0)]
    v, f = [], []
    m = len(prof)
    for i in range(n + 1):
        yaw = a0 + (a1 - a0) * i / n
        h = hfn(yaw)
        a = math.radians(yaw)
        sx, sy = math.sin(a), math.cos(a)
        for (o, t) in prof:
            d = rr + o * depth
            v.append((CAM_V[0] + d * sx, CAM_V[1] + d * sy, z0 + (h - z0) * t if t else z0))
    for i in range(n):
        for k in range(m - 1):
            a = i * m + k
            f.append((a, a + 1, a + m + 1, a + m))
    return P(v, f)


def paint_band(p, low, high, z0, z1, seed=0, namp=0.1, ns=0.08):
    """vertical gradient (foot -> crest) + broad noise patches for far silhouettes."""
    t = smooth01(z0, z1, p.v[:, 2])
    c = np.asarray(low)[None, :] * (1 - t[:, None]) + np.asarray(high)[None, :] * t[:, None]
    c *= (1 + namp * K.nfield(p.v, ns, seed))[:, None]
    p.c = np.ones((len(p.v), 4))
    p.c[:, :3] = np.clip(c, 0, 1)
    return p


def relief_cloud(yaw, d, z, w, h, seed=0, top=(0.98, 0.97, 0.93), bot=(0.70, 0.74, 0.82), puffs=5):
    """stylised carved cumulus: overlapping domed relief puffs on a card facing the vista camera (stage-set
    cloud). Base flattened. Returns a coloured piece."""
    rng = random.Random(seed)
    cx, cy = vpt(yaw, d)
    a = math.radians(yaw)
    fwd = np.array((math.sin(a), math.cos(a), 0.0))     # away from the camera
    side = np.array((math.cos(a), -math.sin(a), 0.0))
    ps = []
    spec = [(0.0, 0.0, 0.32, 0.55)]
    for i in range(puffs - 1):
        ox = rng.uniform(-0.38, 0.38)
        spec.append((ox, rng.uniform(-0.05, 0.25) * (1 - abs(ox)), rng.uniform(0.16, 0.26), rng.uniform(0.32, 0.5)))
    n = 24
    for k, (ox, oz, rx, rz) in enumerate(spec):
        rx, rz = rx * w, rz * h
        pc = np.array((cx, cy, z)) + side * ox * w + np.array((0, 0, oz * h + rz * 0.35))
        rings = (1.0, 0.82, 0.5)
        v, f = [], []
        for s in rings:
            for i in range(n):
                t = 2 * math.pi * i / n
                bump = 1 + 0.07 * math.sin(t * 5 + seed + k) + 0.04 * math.sin(t * 9 + k)
                lx, lz = math.cos(t) * rx * bump * s, math.sin(t) * rz * bump * s
                lz = max(lz, -rz * 0.35 * s - 0.02 * rz)           # flat-ish base
                depth = -0.55 * rx * math.sqrt(max(0.0, 1 - s * s)) - 0.02 * k * rx   # domed toward the camera
                v.append(tuple(pc + side * lx + np.array((0, 0, lz)) + fwd * depth))
        v.append(tuple(pc - fwd * (0.6 * rx + 0.02 * k * rx)))
        for r_ in range(len(rings) - 1):
            for i in range(n):
                j = (i + 1) % n
                a0, b0 = r_ * n, (r_ + 1) * n
                f.append((a0 + i, a0 + j, b0 + j, b0 + i))
        c0 = len(rings) * n - n
        for i in range(n):
            f.append((c0 + i, c0 + (i + 1) % n, len(v) - 1))
        q = P(v, f)
        zt = smooth01(z - 0.1 * h, z + 0.75 * h, q.v[:, 2])
        nn = K.vnormals(q)
        lit = 0.9 + 0.12 * np.clip(-nn @ fwd, 0, 1) + 0.06 * nn[:, 2]
        c = (np.asarray(bot)[None, :] * (1 - zt[:, None]) + np.asarray(top)[None, :] * zt[:, None]) * lit[:, None]
        q.c = np.ones((len(q.v), 4))
        q.c[:, :3] = np.clip(c, 0, 1)
        ps.append(q)
    return join(ps)


def skirt(r0, r1, a0, a1, z, rgb, n=24):
    """flat far plain beyond the terrain, in the vista sector only (no world edge)."""
    v, f = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        for r in (r0, r1):
            v.append((CAM_V[0] + r * math.sin(a), CAM_V[1] + r * math.cos(a), z))
    for i in range(n):
        f.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    p = P(v, f)
    p.c = np.tile(list(rgb) + [1.0], (len(v), 1))
    return p


def flatten_preview_ground():
    """slope arenas drop below main.gd's y=-0.5 Ground plane -> hide its Blender stand-in in previews."""
    rig = K.preview_rig

    def _rig(mood):
        rig(mood)
        g = bpy.data.objects.get("PreviewGround")
        if g:
            g.hide_render = True
    K.preview_rig = _rig


# ================================================================ Kedah palette (sRGB)
EARTH = (0.58, 0.46, 0.31)
EARTH_DK = (0.47, 0.36, 0.24)
DUST = (0.66, 0.56, 0.40)
STRAW = (0.74, 0.62, 0.36)
GOLD = (0.80, 0.63, 0.25)
GOLD_SOIL = (0.56, 0.47, 0.24)
STUB = (0.60, 0.50, 0.30)
GRASSY = (0.36, 0.44, 0.18)
BUND_TOP = (0.42, 0.50, 0.20)
YOUNG = (0.40, 0.58, 0.22)
WET = (0.30, 0.25, 0.18)
MUD = (0.36, 0.29, 0.21)
TIMBER = (0.47, 0.37, 0.27)
TIMBER_DK = (0.32, 0.24, 0.17)
ZINC = (0.55, 0.32, 0.20)
CONC = (0.72, 0.70, 0.64)
STEEL = (0.30, 0.37, 0.43)
WHEEL_RED = (0.62, 0.16, 0.12)
JUTE = (0.64, 0.53, 0.36)
KERBAU = (0.23, 0.22, 0.23)
LEAF_DK = (0.18, 0.30, 0.13)
LEAF = (0.26, 0.40, 0.15)
BANANA = (0.36, 0.52, 0.19)
W_YOUNG = (0.25, 0.36, 0.25)
W_SKY = (0.40, 0.52, 0.62)
W_EDGE = (0.36, 0.33, 0.24)
W_CANAL = (0.30, 0.40, 0.38)

# ================================================================ layout
AX, AY_FAR, AY_NEAR, PW = 6.6, 5.5, 6.6, 2.4       # threshing ground (superellipse)
MOUND = (-10.0, 2.4, 3.1)                          # jelapang kampung mound (x, y, r)
TMOUND = (11.2, 5.6, 1.8)                          # shade-tree mound
WALLOW = (8.1, 3.0, 1.75, 1.25, 0.5)              # kerbau wallow (x, y, rx, ry, rot)
YC, CW, CT, CF, CWZ = 6.6, 0.45, 0.50, 0.12, 0.33  # canal: centre y, inner half width, wall top, floor, water
EMB = (5.5, 7.7, 0.12)                            # embankment band y0..y1, top
GATES = [(-9.0, True), (-3.6, False), (4.4, False)]  # clear of the HUD score plaque (|x|<2)
BRIDGE_X = 2.0
COLW, ROWH, ROW0F, ROW0N = 8.0, 4.5, 7.7, -6.8    # plot grid: centre column |x|<6, rows of 4.5 m
WETS = ("young", "flood")
STATE = {(-1, 0): "ripe", (1, 0): "stubble", (0, 0): "plat", (-1, 1): "flood", (0, 1): "ripe", (1, 1): "young",
         (0, -1): "ripe", (-1, -1): "young", (1, -1): "ripe", (-2, 0): "ripe", (2, 0): "stubble", (-2, 1): "ripe",
         (2, 1): "ripe", (0, 2): "stubble", (-1, 2): "ripe", (1, 2): "ripe", (2, 2): "young", (-2, 2): "plough",
         (0, 3): "ripe", (1, 3): "stubble", (-1, 3): "young", (3, 1): "ripe", (3, 2): "flood", (-3, 1): "young"}


def col_of(x):
    if abs(x) < 6.0:
        return 0, -6.0, 6.0
    k = int((abs(x) - 6.0) // COLW)
    a, b = 6.0 + k * COLW, 6.0 + (k + 1) * COLW
    return (k + 1, a, b) if x > 0 else (-(k + 1), -b, -a)


def row_of(y):
    if y >= ROW0F:
        k = int((y - ROW0F) // ROWH)
        return k + 1, ROW0F + k * ROWH, ROW0F + (k + 1) * ROWH
    if y >= ROW0N:
        return 0, ROW0N, ROW0F
    k = int((ROW0N - y) // ROWH)
    return -(k + 1), ROW0N - (k + 1) * ROWH, ROW0N - k * ROWH


def state(i, j):
    if (i, j) in STATE:
        return STATE[(i, j)]
    r = random.Random(i * 7919 + j * 104729).random()
    return "ripe" if r < 0.5 else "stubble" if r < 0.68 else "young" if r < 0.84 else "flood" if r < 0.93 else "plough"


def level(j):
    """terraces step down away from the canal (water flows between levels)."""
    if j == 0:
        return -0.12
    if j > 0:
        return [-0.06, -0.14][j - 1] if j <= 2 else -0.22
    return -0.18 if j == -1 else -0.26


def cell(x, y):
    i, x0, x1 = col_of(x)
    j, y0, y1 = row_of(y)
    return i, j, x0, y0, x1, y1


def plat_d(x, y):
    ay = AY_FAR if y > 0 else AY_NEAR
    return ((abs(x) / AX) ** PW + (abs(y) / ay) ** PW) ** (1.0 / PW)


def _raise(top, base, d, d0, d1):
    return top + (base - top) * smooth01(d0, d1, d)


def wallow_d(x, y):
    cx, cy, rx, ry, rot = WALLOW
    dx, dy = x - cx, y - cy
    c, s = math.cos(rot), math.sin(rot)
    u, v = dx * c + dy * s, -dx * s + dy * c
    return math.hypot(u / rx, v / ry) * (1 + 0.12 * nz(x, y, 0, 1.3, 44))


def land_h(x, y):
    """raised land: threshing ground, kampung mound, tree mound, canal embankment; -1 elsewhere."""
    base = -0.5
    d = plat_d(x, y)
    h = _raise(0.035 * (1 - min(d, 1.0) ** 2) + 0.015 * nz(x, y, 0, 0.8, 3), base, d, 1.0, 1.2)
    dm = math.hypot(x - MOUND[0], y - MOUND[1]) / MOUND[2]
    h = max(h, _raise(0.16 * (1 - min(dm, 1) ** 2) + 0.03 * nz(x, y, 1, 0.9, 4), base, dm, 1.0, 1.35))
    dt = math.hypot(x - TMOUND[0], y - TMOUND[1]) / TMOUND[2]
    h = max(h, _raise(0.12 * (1 - min(dt, 1) ** 2), base, dt, 1.0, 1.4))
    # causeway platform -> mound
    t = max(0.0, min(1.0, (x + 6.0) / (MOUND[0] + 2.0 + 6.0)))
    cy = 1.2 + (MOUND[1] - 1.2) * t
    if -8.8 < x < -5.5:
        h = max(h, _raise(0.03, base, abs(y - cy), 0.7, 1.15))
    e0, e1, et = EMB
    de = max(e0 - y, y - e1, 0.0)
    h = max(h, _raise(et + 0.02 * nz(x, y, 2, 1.0, 5), base, de, 0.0, 0.55))
    return float(h)


def ground(x, y):
    h = land_h(x, y)
    i, j, x0, y0, x1, y1 = cell(x, y)
    st = state(i, j)
    lv = level(j)
    if st in WETS:
        b = lv - 0.16 + 0.02 * nz(x, y, 5, 1.5, 8)
    elif st == "plough":
        b = lv - 0.03 + 0.035 * math.sin(y * 8.0 + 0.6 * nz(x, y, 0, 1.3, 6))
    elif st == "stubble":
        b = lv + 0.012 * nz(x, y, 3, 1.2, 7) + 0.008 * math.sin(y * 20.0)
    else:
        b = lv + 0.015 * nz(x, y, 3, 1.0, 7)
    h = max(h, b)
    wd = wallow_d(x, y)
    if wd < 1.35:
        h = min(h, h + (-0.40 - h) * (1 - smooth01(0.7, 1.35, wd)))
    return h


def wallow_z():
    return -0.24


def in_water(x, y):
    if wallow_d(x, y) < 1.0:
        return "wallow"
    if abs(y - YC) < CW + 0.16 and land_h(x, y) > 0.0:
        return "canal"
    i, j, *_ = cell(x, y)
    if state(i, j) in WETS and land_h(x, y) < level(j) - 0.04:
        return "plot"
    return None


def gcolor(x, y, z):
    n1 = nz(x, y, 0, 0.45, 11)
    n2 = nz(x, y, 0, 2.3, 12)
    n3 = nz(x, y, 0, 6.0, 13)
    i, j, *_ = cell(x, y)
    st = state(i, j)
    lv = level(j)
    lh = land_h(x, y)
    r = math.hypot(x, y)
    if lh < z - 0.005 or lh < lv:  # in a plot (below raised land)
        if st in WETS:
            c = mix(MUD, WET, 0.6)
        elif st == "plough":
            fur = 0.5 + 0.5 * math.sin(y * 8.0 + 0.6 * nz(x, y, 0, 1.3, 6))
            c = np.array(MUD) * (0.85 + 0.25 * fur)
        elif st == "stubble":
            c = np.array(STUB) * (1 + 0.1 * n1 + 0.06 * n2) * (0.9 + 0.1 * math.sin(y * 20.0))
            c = mix(c, EARTH_DK, 0.25 * smooth01(0.2, 0.6, nz(x, y, 0, 0.5, 17)))
        else:
            c = np.array(GOLD_SOIL) * (1 + 0.1 * n1 + 0.06 * n2)
        wd = wallow_d(x, y)
        if wd < 1.6:
            c = mix(c, WET, 0.85 * (1 - smooth01(1.0, 1.6, wd)))
        if r > 23:
            c = mix(c, {"ripe": (0.72, 0.60, 0.30), "stubble": (0.68, 0.59, 0.42), "young": (0.38, 0.52, 0.24),
                        "flood": (0.42, 0.52, 0.56), "plough": (0.46, 0.37, 0.27)}.get(st, GOLD), 0.8)
        return tuple(np.clip(c, 0, 1))
    # raised land: earth, grassy edges, straw litter on the threshing ground
    d = plat_d(x, y)
    base = np.array(EARTH) * (1 + 0.1 * n1 + 0.07 * n2 + 0.04 * n3)
    base = mix(base, DUST, 0.5 * smooth01(0.1, 0.5, nz(x, y, 0, 0.5, 16)))
    base = mix(base, STRAW, 0.45 * smooth01(0.25, 0.6, nz(x, y, 0, 1.1, 18)) * (1 - smooth01(0.9, 1.0, d)))
    grass = smooth01(0.82, 1.05, d) * 0.85
    dm = math.hypot(x - MOUND[0], y - MOUND[1]) / MOUND[2]
    grass = max(grass, 0.8 * smooth01(0.25, 0.7, dm) * (0.6 + 0.4 * n1))
    de = abs(y - YC)
    if de < 1.4 and d > 0.95:
        grass = max(grass, 0.9)
    base = mix(base, np.array(GRASSY) * (1 + 0.12 * n2), min(1.0, grass))
    base = mix(base, np.array(EARTH) * 1.04, 0.6 * (1 - smooth01(4.6, 5.6, r)))   # trodden apron
    wet = 1 - smooth01(lv - 0.02, lv + 0.12, z)
    base = mix(base, WET, 0.45 * wet)
    if r > 23:
        base = mix(base, (0.52, 0.52, 0.30), 0.5)
    return tuple(np.clip(base, 0, 1))


def gkind(x, y, z):
    if math.hypot(x, y) > 23:
        return "MatGround_padang"
    if land_h(x, y) < z - 0.005 or land_h(x, y) < level(cell(x, y)[1]):
        return "MatMud_sawah"
    return "MatGround_padang"


def gcull(cx, cy, zmax):
    w = in_water(cx, cy)
    if w == "canal":
        return True
    if w == "wallow":
        return zmax < wallow_z() - 0.03
    if w == "plot":
        return zmax < level(cell(cx, cy)[1]) - 0.05
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


def water_quad(x0, y0, x1, y1, z, inner, edge, inset=0.5, a_in=1.0, a_edge=1.0):
    v = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z),
         (x0 + inset, y0 + inset, z), (x1 - inset, y0 + inset, z), (x1 - inset, y1 - inset, z), (x0 + inset, y1 - inset, z)]
    p = P(v, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)])
    p.c = np.array([list(edge) + [a_edge]] * 4 + [list(inner) + [a_in]] * 4)
    return p


# ================================================================ props
def bund(A, a, b, top, half=0.36, far=False, step=0.45):
    """paddy bund along a 2D segment; skipped under raised land / out of view."""
    pts = []
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    step = 3.0 if far else step
    k = max(1, int(L / step))
    for t in range(k + 1):
        x, y = a[0] + (b[0] - a[0]) * t / k, a[1] + (b[1] - a[1]) * t / k
        ok = land_h(x, y) < top - 0.06 and visible(x, y, pad=3.0) and wallow_d(x, y) > 1.3
        pts.append((x, y) if ok else None)
    runs, cur = [], []
    for p in pts + [None]:
        if p:
            cur.append(p)
        else:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
    lo = -0.34
    prof = ([(-half, lo), (0.0, top), (half, lo)] if far else
            [(-half, lo), (-half * 0.7, top - 0.07), (-half * 0.4, top - 0.02), (0.0, top), (half * 0.4, top - 0.02),
             (half * 0.7, top - 0.07), (half, lo)])
    out = []
    for run in runs:
        p = K.extrude(run, prof, step=step if not far else 3.0, jitter=0.0 if far else 0.1, seed=int(abs(run[0][0] * 7 + run[0][1] * 13)))
        z = p.v[:, 2]
        g = smooth01(top - 0.12, top - 0.01, z)
        n1 = np.array([nz(a_, b_, 0, 0.8, 21) for a_, b_, _ in p.v])
        c = (np.array(EARTH_DK)[None, :] * (1 - g[:, None]) + np.array(BUND_TOP)[None, :] * g[:, None]) * (1 + 0.12 * n1)[:, None]
        p.c = np.ones((len(p.v), 4))
        p.c[:, :3] = np.clip(c, 0, 1)
        out.append(p)
        if not far:
            for q0, q1 in zip(run[::3][:-1], run[::3][1:]):
                A.scatter_strip("Grass", 26, q0, q1, 0.3, lambda a_, b_: top - 0.01, (0.46, 0.52, 0.22), step=99)
    return out


def jelapang(A, x, y, rz):
    """Kedah rice barn: stilted plank granary, rusty corrugated zinc gable roof, door + ladder, stone footings."""
    W, D, FH, WH, RISE, OV = 3.0, 2.4, 0.95, 1.8, 1.25, 0.32
    EAVE = FH + WH
    wood, dark, zinc, rock, metal = [], [], [], [], []
    for sx in (-1.35, 0.0, 1.35):
        for sy in (-1.05, 1.05):
            wood.append(xf(K.post(FH + 0.05, 0.085, seed=int(sx * 10 + sy * 7), seg=7, lean=0.01), (sx, sy, 0.02)))
            rock.append(xf(K.rock(0.17, seed=int(sx * 3 + sy * 5 + 40), sub=2, squash=(1, 1, 0.55)), (sx, sy, -0.05)))
    for sy in (-1.05, 1.05):
        wood.append(xf(K.box(W + 0.25, 0.12, 0.13, bev=0.015), (0, sy, FH - 0.1)))
    wood.append(xf(K.box(W + 0.12, D + 0.12, 0.07, bev=0.012), (0, 0, FH)))
    dark.append(xf(K.box(W - 0.08, D - 0.08, WH, bev=0.01), (0, 0, FH + 0.05)))      # wall core
    n_long, n_short = 15, 12
    for k in range(n_long):  # vertical planks, front + back
        px = -W / 2 + (k + 0.5) * W / n_long
        for sy in (-1, 1):
            if sy < 0 and 0.55 < px < 1.25:  # door gap on the front
                continue
            wood.append(xf(K.box(W / n_long - 0.018, 0.035, WH - 0.02, bev=0.007), (px, sy * (D / 2 - 0.02), FH + 0.06)))
    for k in range(n_short):
        py = -D / 2 + (k + 0.5) * D / n_short
        for sx in (-1, 1):
            wood.append(xf(K.box(0.035, D / n_short - 0.018, WH - 0.02, bev=0.007), (sx * (W / 2 - 0.02), py, FH + 0.06)))
    for sx in (-1, 1):  # corner posts + top plates + sill
        for sy in (-1, 1):
            wood.append(xf(K.box(0.1, 0.1, WH + 0.1, bev=0.012), (sx * W / 2, sy * D / 2, FH)))
    for sy in (-1, 1):
        wood.append(xf(K.box(W + 0.12, 0.09, 0.09, bev=0.012), (0, sy * D / 2, EAVE - 0.05)))
        wood.append(xf(K.box(W + 0.12, 0.08, 0.08, bev=0.012), (0, sy * D / 2, FH + 0.05)))
    # door (half-open leaf) + frame
    dark.append(xf(K.box(0.66, 0.05, 1.3, bev=0.01), (0.9, -D / 2 + 0.03, FH + 0.12)))
    wood.append(xf(K.box(0.62, 0.04, 1.28, bev=0.008), (0.62, -D / 2 - 0.28, FH + 0.12), (0, 0, -0.95)))
    for ox in (0.55, 1.25):
        wood.append(xf(K.box(0.07, 0.07, 1.42, bev=0.01), (ox, -D / 2 - 0.03, FH + 0.08)))
    wood.append(xf(K.box(0.8, 0.07, 0.07, bev=0.01), (0.9, -D / 2 - 0.03, FH + 1.48)))
    # ladder to the door
    for ox in (0.68, 1.12):
        wood.append(K.tube([(ox, -D / 2 - 0.85, -0.02), (ox, -D / 2 - 0.08, FH + 0.12)], 0.028, seg=5))
    for k in range(4):
        t = (k + 1) / 5
        wood.append(K.tube([(0.66, -D / 2 - 0.85 + 0.77 * t, FH * t), (1.14, -D / 2 - 0.85 + 0.77 * t, FH * t)], 0.02, seg=5))
    # corrugated zinc gable roof (ridge along x)
    half = D / 2 + OV
    L = math.hypot(half, RISE)
    WR = W + 2 * OV
    nc = 34
    for side in (-1, 1):
        v, f = [], []
        for i in range(nc + 1):
            xx = -WR / 2 + WR * i / nc
            off = 0.035 * (i % 2)
            for t in (0.0, 0.5, 1.0):
                v.append((xx, side * half * (1 - t), EAVE - 0.08 + RISE * t + off))
        for i in range(nc):
            a = 3 * i
            for k in range(2):
                f.append((a + k, a + k + 3, a + k + 4, a + k + 1) if side > 0 else (a + k, a + k + 1, a + k + 4, a + k + 3))
        zinc.append(K.dbl(P(v, f)))
    zinc.append(K.tube([(-WR / 2, 0, EAVE - 0.06 + RISE + 0.02), (WR / 2, 0, EAVE - 0.06 + RISE + 0.02)], 0.09, seg=6))
    for sx in (-1, 1):  # plank gables + vent lattice + barge boards
        dark.append(K.dbl(P([(sx * (W / 2 + 0.01), -D / 2, EAVE), (sx * (W / 2 + 0.01), D / 2, EAVE),
                             (sx * (W / 2 + 0.01), 0, EAVE + RISE - 0.04)], [(0, 1, 2)])))
        for k in range(5):
            yy = -0.42 + 0.21 * k
            hh = (RISE - 0.1) * (1 - abs(yy) / (D / 2))
            wood.append(xf(K.box(0.03, 0.16, max(0.1, hh - 0.08), bev=0.006), (sx * (W / 2 + 0.03), yy, EAVE)))
        for s2 in (-1, 1):
            wood.append(K.tube([(sx * (WR / 2 - 0.02), s2 * (half + 0.02), EAVE - 0.1), (sx * (WR / 2 - 0.02), 0, EAVE + RISE - 0.02)], 0.03, seg=4))
    metal.append(xf(K.box(0.04, 0.06, 0.32, bev=0.005), (1.25, -D / 2 - 0.06, FH + 0.62)))  # hasp
    gz = ground(x, y)

    def put(lst):
        return [xf(p, (x, y, gz), (0, 0, rz)) for p in lst]
    A.add("battle", "MatWood_timber", [paint(q, TIMBER if i % 3 else TIMBER_DK, var=0.09, ao=0.5, ao_h=1.0, ground=gz, namp=0.12, ns=3.0, stretch=(1, 1, 0.15))
                                      for i, q in enumerate(put(wood))])
    A.add("battle", "MatWood_timber", [paint(q, (0.24, 0.18, 0.13), var=0.04, ao=0.4, ao_h=1.2, ground=gz) for q in put(dark)])
    rust = lambda v, c: c * (0.82 + 0.3 * np.clip(K.nfield(v, 1.4, 5, (1, 1, 0.2)), -0.6, 1))[:, None] * np.where((np.abs(v[:, 0] - x) % 0.6 < 0.3)[:, None], 1.0, 0.92)
    A.add("battle", "MatMetal_gate", [tint(paint(q, ZINC, var=0.04, ao=0.0, top=0.25), rust) for q in put(zinc)])
    A.add("battle", "MatMetal_gate", [paint(q, (0.25, 0.24, 0.22), ao=0.0) for q in put(metal)])
    A.add("battle", "MatRock_kerbau", [paint(q, (0.50, 0.48, 0.43), ao=0.5, ao_h=0.15, ground=gz - 0.05) for q in put(rock)])
    A.contact(x, y, 2.4, 0.38)


def sheaf(h=0.72, seed=0):
    """berkas padi: straw bundle tied at the waist, drooping grain heads. Returns (straw, heads)."""
    rng = random.Random(seed)
    prof = [(0.0, 0.0), (0.085, 0.0), (0.08, 0.06), (0.05, h * 0.36), (0.052, h * 0.42), (0.09, h * 0.7), (0.065, h * 0.93), (0.0, h)]
    body = K.lathe(prof, seg=6, rfn=lambda a, t: 1 + 0.14 * math.sin(a * 3 + seed) * (0.3 + t))
    tie = K.lathe([(0.055, h * 0.37), (0.062, h * 0.4), (0.055, h * 0.43)], seg=6, cap0=False, cap1=False)
    heads = []
    for k in range(4):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.3, 0.3)
        o = (0.04 * math.cos(a), 0.04 * math.sin(a), h * 0.9)
        e = (0.2 * math.cos(a), 0.2 * math.sin(a), h * 0.62)
        heads.append(K.tube(K.arc(o, e, 0.1, n=3), [0.024, 0.028, 0.02, 0.008], seg=3, cap=False))
    return join(body, tie), join(heads)


def stook(A, x, y, seed, n=5):
    rng = random.Random(seed)
    gz = ground(x, y)
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.2, 0.2)
        st, hd = sheaf(rng.uniform(0.66, 0.78), seed=seed * 10 + k)
        rot = (0.26 * math.sin(a), -0.26 * math.cos(a), rng.uniform(0, 6))
        loc = (x + 0.13 * math.cos(a), y + 0.13 * math.sin(a), gz - 0.02)
        A.add("battle", "MatThatch_straw", paint(xf(st, loc, (rot[0], rot[1], 0)), STRAW, var=0.07, ao=0.45, ao_h=0.35, ground=gz, namp=0.15, ns=8))
        A.add("battle", "MatThatch_straw", paint(xf(hd, loc, (rot[0], rot[1], 0)), (0.70, 0.53, 0.20), var=0.06, ao=0.1, ground=gz))
    A.contact(x, y, 0.55, 0.3)


def tong_banting(A, x, y):
    """threshing tub with a woven screen on three sides (screen faces away from the dish)."""
    rz = math.atan2(y, x) - math.pi / 2
    L, Wd, H = 1.3, 0.92, 0.5
    wood, screen, grain, rod = [], [], [], []
    wood.append(K.box(L, Wd, 0.06, bev=0.012))
    for sy in (-1, 1):
        for k in range(3):
            wood.append(xf(K.box(L + 0.06 * k * 0, 0.04, H / 3 - 0.01, bev=0.008), (0, sy * (Wd / 2 + 0.02 + 0.03 * k), 0.04 + k * H / 3), (sy * -0.16, 0, 0)))
    for sx in (-1, 1):
        for k in range(3):
            wood.append(xf(K.box(0.04, Wd + 0.06 * k, H / 3 - 0.01, bev=0.008), (sx * (L / 2 + 0.02 + 0.03 * k), 0, 0.04 + k * H / 3), (0, sx * 0.16, 0)))
        for sy in (-1, 1):
            wood.append(xf(K.box(0.07, 0.07, H + 0.05, bev=0.01), (sx * (L / 2 + 0.05), sy * (Wd / 2 + 0.05), 0.0), (sy * -0.16, sx * 0.16, 0)))
    # screen (tirai): back panel + two side wings, rising above the rim
    path = [(-L / 2 - 0.12, -0.05), (-L / 2 - 0.12, Wd / 2 + 0.12), (L / 2 + 0.12, Wd / 2 + 0.12), (L / 2 + 0.12, -0.05)]
    pts = []
    for (a, b) in zip(path[:-1], path[1:]):
        for t in np.linspace(0, 1, 6)[:-1]:
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    pts.append(path[-1])
    v, f = [], []
    for (px, py) in pts:
        bow = 0.04 * math.sin(math.pi * (px + L / 2) / L) if py > Wd / 2 else 0
        v += [(px, py + bow, H - 0.05), (px, py + bow, H + 0.25), (px, py + bow, H + 0.48)]
    for i in range(len(pts) - 1):
        for k in range(2):
            a = 3 * i + k
            f.append((a, a + 3, a + 4, a + 1))
    screen.append(K.dbl(P(v, f)))
    rod.append(K.tube([(p[0], p[1], H + 0.49) for p in pts[::2]] + [(pts[-1][0], pts[-1][1], H + 0.49)], 0.016, seg=4))
    for p in (pts[0], pts[5], pts[10], pts[-1]):
        rod.append(K.tube([(p[0], p[1], 0.3), (p[0], p[1], H + 0.5)], 0.018, seg=4))
    # grain heap + beating ladder
    grain.append(xf(K.lathe([(0.0, 0.0), (0.5, 0.0), (0.38, 0.12), (0.15, 0.22), (0.0, 0.24)], seg=14), (0, 0.05, 0.05), s=(1.1, 0.75, 1.0)))
    for ox in (-0.22, 0.22):
        wood.append(K.tube([(ox, 0.05, 0.08), (ox, 0.35, 0.62)], 0.022, seg=5))
    for k in range(4):
        t = (k + 1) / 5
        wood.append(K.tube([(-0.24, 0.05 + 0.3 * t, 0.08 + 0.54 * t), (0.24, 0.05 + 0.3 * t, 0.08 + 0.54 * t)], 0.016, seg=4))
    gz = ground(x, y)

    def put(lst):
        return [xf(p, (x, y, gz - 0.02), (0, 0, rz)) for p in lst]
    weave = lambda v, c: c * (0.82 + 0.18 * ((np.floor(v[:, 2] * 22) + np.floor((v[:, 0] + v[:, 1]) * 22)) % 2))[:, None]
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, var=0.08, ao=0.45, ao_h=0.5, ground=gz, namp=0.1, ns=4) for q in put(wood)])
    A.add("battle", "MatThatch_straw", [tint(paint(q, (0.62, 0.52, 0.34), var=0.03, ao=0.35, ao_h=0.9, ground=gz), weave) for q in put(screen)])
    A.add("battle", "MatWood_timber", [paint(q, (0.56, 0.48, 0.30), ao=0.2, ground=gz) for q in put(rod)])
    A.add("battle", "MatThatch_straw", [paint(q, GOLD, var=0.03, ao=0.25, ao_h=0.25, ground=gz, top=0.25, namp=0.15, ns=12) for q in put(grain)])
    A.contact(x, y, 1.2, 0.35)


def kerbau(graze=False, seed=0):
    """water buffalo: smooth blob body, crescent horns; faces -x. Returns (hide, horn)."""
    # one smooth lofted barrel body (rump -> hump -> neck): (x, z centre, half width, half height)
    secs = [(1.02, 0.98, 0.10, 0.10), (0.92, 0.99, 0.30, 0.30), (0.7, 1.0, 0.41, 0.40), (0.3, 0.97, 0.45, 0.44),
            (-0.1, 0.97, 0.47, 0.46), (-0.45, 1.03, 0.45, 0.47), (-0.78, 1.02, 0.34, 0.33), (-1.02, 0.96, 0.24, 0.24), (-1.12, 0.93, 0.12, 0.12)]
    n = 16
    v, f = [], []
    for (sx, zc, ry, rz) in secs:
        for i in range(n):
            a = 2 * math.pi * i / n
            belly = 1.0 - 0.12 * max(0.0, -math.sin(a))  # flatter underside
            v.append((sx, ry * math.cos(a), zc + rz * math.sin(a) * belly))
    for k in range(len(secs) - 1):
        for i in range(n):
            j = (i + 1) % n
            f.append((k * n + i, (k + 1) * n + i, (k + 1) * n + j, k * n + j))  # outward (sections run toward -x)
    f.append(tuple(range(n - 1, -1, -1)))
    f.append(tuple(range(len(v) - n, len(v))))
    b = [P(v, f)]
    hd = np.array((-0.12, 0, -0.42)) if graze else np.zeros(3)  # grazing: head lowered to the grass
    for k, (c, r, pitch) in enumerate((((-1.3, 0, 0.84), (0.3, 0.17, 0.19), 0.45), ((-1.53, 0, 0.71), (0.14, 0.135, 0.11), 0.2))):
        b.append(xf(xf(blob(r, sub=2, seed=seed + k, amp=0.04), rot=(0, pitch + (0.5 if graze else 0), 0)), tuple(np.add(c, hd * (1.0 + 0.3 * k)))))
    for s in (-1, 1):  # ears
        b.append(xf(blob((0.11, 0.05, 0.04), sub=1), tuple(np.add((-1.18, s * 0.21, 0.97), hd)), (0.3 * s, 0, 0.5 * s)))
    if True:
        for lx in (-0.55, 0.6):
            for s in (-1, 1):
                b.append(K.tube([(lx, s * 0.2, 0.86), (lx + 0.04, s * 0.22, 0.45), (lx - 0.02, s * 0.21, 0.06), (lx - 0.04, s * 0.21, 0.0)],
                                [0.12, 0.08, 0.065, 0.07], seg=7))
        b.append(K.tube([(0.98, 0, 1.12), (1.1, 0, 0.8), (1.12, 0.03, 0.5)], [0.035, 0.025, 0.02], seg=5))
        b.append(xf(blob((0.05, 0.05, 0.1), sub=1), (1.12, 0.03, 0.44)))
    horn = []
    for s in (-1, 1):
        path = [(-1.18, s * 0.11, 1.02), (-1.12, s * 0.42, 1.06), (-0.92, s * 0.62, 1.12), (-0.68, s * 0.6, 1.24), (-0.6, s * 0.5, 1.3)]
        horn.append(K.tube([tuple(np.add(q, hd)) for q in path], [0.075, 0.06, 0.045, 0.028, 0.008], seg=7))
    return join(b), join(horn)


def place_kerbau(A, x, y, rz, base, graze=False, seed=0):
    hide, horn = kerbau(graze, seed)
    hide = xf(hide, (x, y, base), (0, 0, rz))
    horn = xf(horn, (x, y, base), (0, 0, rz))
    mud = lambda v, c: c * 1.0 + (np.array([0.42, 0.34, 0.25, 1.0]) - c) * (0.75 * (1 - smooth01(base + 0.3, base + 0.62, v[:, 2])))[:, None]
    A.add("battle", "MatRock_kerbau", tint(paint(hide, KERBAU, var=0.03, ao=0.25, ao_h=0.9, ground=base, top=0.3, namp=0.08, ns=3), mud))
    side = np.abs((horn.v[:, :2] - np.array([x, y])) @ np.array([-math.sin(rz), math.cos(rz)]))  # tips paler
    A.add("battle", "MatRock_kerbau", tint(paint(horn, (0.30, 0.27, 0.22), ao=0.0, top=0.2),
                                          lambda v, c: c + (np.array([0.62, 0.57, 0.48, 1]) - c) * (0.8 * smooth01(0.4, 0.6, side))[:, None]))


def shade_tree(A, x, y, seed=0):
    rng = random.Random(seed)
    gz = ground(x, y)
    wood = [K.tube([(x, y, gz - 0.1), (x - 0.15, y - 0.1, gz + 1.0), (x - 0.35, y - 0.2, gz + 1.9)], [0.22, 0.17, 0.13], seg=8)]
    tips = [(-1.4, -0.9, 2.9), (0.9, -0.6, 3.0), (-0.3, 0.9, 3.1), (-1.0, 0.4, 2.6)]
    for (dx, dy, dz) in tips:
        wood.append(K.tube([(x - 0.35, y - 0.2, gz + 1.8), (x + dx * 0.5, y + dy * 0.5, gz + dz - 0.5), (x + dx, y + dy, gz + dz)], [0.1, 0.07, 0.04], seg=6))
    leaf = [xf(K.canopy(1.55, seed=seed * 3 + k, lumps=4, sub=2, squash=0.55, spread=0.75), (x + dx, y + dy, gz + dz - 0.1)) for k, (dx, dy, dz) in enumerate(tips[:3])]
    A.add("battle", "MatWood_timber", [paint(q, (0.36, 0.30, 0.24), var=0.06, ao=0.4, ao_h=1.0, ground=gz, namp=0.15, ns=3) for q in wood])
    A.add("battle", "MatLeaf_canopy", [paint(q, LEAF_DK, var=0.08, ao=0.45, ao_h=3.2, ground=gz, top=0.55, namp=0.2, ns=1.2) for q in leaf])
    A.contact(x, y, 2.6, 0.3)


def banana_clump(A, x, y, seed):
    rng = random.Random(seed)
    for k, (dx, dy, h) in enumerate(((0, 0, 2.7), (0.7, -0.9, 2.0), (-0.6, 0.8, 1.4))):
        st, lv = K.banana(h * rng.uniform(0.9, 1.1), seed=seed + k, leaves=6 if h > 2 else 4)
        px, py = x + dx, y + dy
        gz = ground(px, py)
        rz = rng.uniform(0, 6.28)
        A.add("battle", "MatLeaf_canopy", paint(xf(lv, (px, py, gz - 0.05), (0, 0, rz)), BANANA, var=0.08, ao=0.35, ao_h=2.4, ground=gz, top=0.25, namp=0.15, ns=2))
        A.add("battle", "MatWood_timber", paint(xf(st, (px, py, gz - 0.05), (0, 0, rz)), (0.42, 0.44, 0.24), var=0.06, ao=0.4, ao_h=1.2, ground=gz))
        A.contact(px, py, 0.9, 0.25)


def palm(A, x, y, h, seed, set_="battle"):
    tr, lf = K.coconut_palm(h, seed=seed, fronds=9 if set_ == "battle" else 7)
    gz = ground(x, y) if math.hypot(x, y) < 60 else -0.2
    A.add(set_, "MatWood_timber", tint(paint(xf(tr, (x, y, gz - 0.1)), (0.46, 0.39, 0.30), ao=0.3, ao_h=2, ground=gz, namp=0.1, ns=4),
                                       lambda v, c: c * (0.88 + 0.12 * (np.floor(v[:, 2] * 5) % 2))[:, None]))
    A.add(set_, "MatLeaf_canopy", paint(xf(lf, (x, y, gz - 0.1)), (0.30, 0.42, 0.16), var=0.1, ao=0, top=0.35, namp=0.15, ns=1))


def canal(A):
    """raised concrete U-channel along x with water; sluice gates with hand wheels; footbridge; open-gate spill."""
    prof = [(-CW - 0.15, 0.0), (-CW - 0.15, CT - 0.02), (-CW - 0.12, CT), (-CW, CT), (-CW, CF), (CW, CF), (CW, CT),
            (CW + 0.12, CT), (CW + 0.15, CT - 0.02), (CW + 0.15, 0.0)]
    for (x0, x1, set_, step) in ((-70.0, -18.0, "far", 3.0), (-18.0, 18.0, "battle", 0.5), (18.0, 70.0, "far", 3.0)):
        p = K.extrude([(x0, YC), (x1, YC)], prof, step=step)
        stain = lambda v, c: c * (1 - 0.35 * (1 - smooth01(CWZ - 0.02, CWZ + 0.06, v[:, 2])) * (np.abs(v[:, 1] - YC) < CW + 0.01))[:, None] \
            * (0.9 + 0.1 * np.clip(K.nfield(v, 0.9, 3, (1, 1, 2)), -1, 1))[:, None] * (1 - 0.18 * (np.abs(v[:, 0] % 4.0) < 0.04))[:, None]
        A.add(set_, "MatPlaster_canal" if set_ == "battle" else "MatRock_kerbau", tint(paint(p, CONC, var=0.0, ao=0.3, ao_h=0.4, ground=0.0, top=0.1), stain))
        if set_ == "battle":
            w = water_quad(x0, YC - CW, x1, YC + CW, CWZ, W_CANAL, (0.34, 0.40, 0.36), inset=0.12)
            A.add("battle", "MatWater_sawah", w)
        else:
            A.add("far", "MatWater_sawah", water_quad(x0, YC - CW, x1, YC + CW, CWZ, W_CANAL, W_CANAL, inset=0.1))
    for gx, open_ in GATES:
        conc, steel, red = [], [], []
        for sy in (-1, 1):
            conc.append(xf(K.box(0.42, 0.34, 0.27, bev=0.03), (gx, YC + sy * (CW + 0.1), CT - 0.02)))
            steel.append(xf(K.box(0.09, 0.09, 0.4, bev=0.01), (gx, YC + sy * (CW + 0.04), CT + 0.22)))
        steel.append(xf(K.box(0.12, 2 * CW + 0.3, 0.08, bev=0.012), (gx, YC, CT + 0.58)))  # wheels stay below the HUD bars
        lift = 0.3 if open_ else 0.0
        steel.append(xf(K.box(0.06, 2 * CW - 0.04, 0.36, bev=0.008), (gx, YC, CF + 0.02 + lift)))
        steel.append(K.tube([(gx, YC, CF + 0.36 + lift), (gx, YC, CT + 0.76)], 0.022, seg=6))
        red.append(xf(xf(K.wheel(0.25, 0.02, spokes=5), rot=(math.pi / 2, 0, 0)), (gx, YC, CT + 0.7)))
        red.append(K.tube([(gx + 0.2, YC + 0.12, CT + 0.7), (gx + 0.2, YC + 0.12, CT + 0.82)], 0.018, seg=4))
        A.add("battle", "MatPlaster_canal", [paint(q, (0.66, 0.64, 0.58), var=0.04, ao=0.35, ao_h=0.4, ground=CT - 0.05, namp=0.1, ns=4) for q in conc])
        A.add("battle", "MatMetal_gate", [tint(paint(q, STEEL, var=0.04, ao=0.3, ao_h=0.6, ground=CT, namp=0.12, ns=5),
                                               lambda v, c: c + (np.array([0.42, 0.24, 0.14, 1]) - c) * (0.5 * smooth01(0.2, 0.7, K.nfield(v, 4.0, 9)))[:, None]) for q in steel])
        A.add("battle", "MatMetal_gate", [paint(q, WHEEL_RED, var=0.03, ao=0.0, top=0.25) for q in red])
        if open_:  # water rushes through: foam in the canal + outlet culvert + spill into the flooded plot
            A.add("battle", "MatWater_sawah", water_quad(gx - 1.2, YC - CW, gx + 1.2, YC + CW, CWZ + 0.005, (0.5, 0.56, 0.52), (0.5, 0.56, 0.52), inset=0.3, a_in=0.35, a_edge=0.8))
            pipe = xf(K.lathe([(0.2, 0.0), (0.23, 0.0), (0.23, 0.35), (0.2, 0.35)], seg=12, cap0=False, cap1=False), (gx, YC + CW + 0.12, CF + 0.08), (-math.pi / 2, 0, 0))
            A.add("battle", "MatPlaster_canal", paint(pipe, (0.58, 0.57, 0.52), ao=0.2, ground=0.0))
            y0, y1 = YC + CW + 0.45, ROW0F + 0.9
            lz = level(1) - 0.02
            v = [(gx - 0.18, y0, CF + 0.12), (gx + 0.18, y0, CF + 0.12), (gx + 0.4, y1, lz + 0.01), (gx - 0.4, y1, lz + 0.01)]
            sp = P(v, [(0, 1, 2, 3)])
            sp.c = np.array([[0.55, 0.6, 0.56, 0.2]] * 2 + [[0.4, 0.5, 0.5, 0.6]] * 2)
            A.add("battle", "MatWater_sawah", sp)
    # footbridge (planks on two logs)
    wood = [xf(K.plank(1.7, 0.2, 0.04, warp=0.01), (BRIDGE_X + dx, YC, CT + 0.06), (0, 0, math.pi / 2)) for dx in (-0.22, 0.0, 0.22)]
    wood += [K.tube([(BRIDGE_X + dx, YC - 0.95, CT - 0.04), (BRIDGE_X + dx, YC + 0.95, CT - 0.04)], 0.05, seg=6) for dx in (-0.3, 0.3)]
    A.add("battle", "MatWood_timber", [paint(q, (0.50, 0.41, 0.30), var=0.1, ao=0.3, ao_h=0.3, ground=CT - 0.1) for q in wood])


def apron(A):
    """three small clusters on the threshing ground (<=0.6 m, nothing bright within 1.5 m of the rope)."""
    # near-left: rice sacks + gantang measure + sickle
    for k, (sx, sy, rz, s) in enumerate(((-4.15, -2.95, 0.4, 1.0), (-4.75, -2.35, 1.3, 0.95), (-4.55, -3.5, 2.2, 0.9))):
        p = pillow(0.62 * s, 0.4 * s, 0.34 * s, seed=k)
        q = on_ground(xf(p, rot=(0, 0, rz)), sx, sy, 0.02)
        A.add("battle", "MatCloth_guni", tint(paint(q, JUTE, var=0.05, ao=0.4, ao_h=0.3, ground=ground(sx, sy), top=0.2, namp=0.1, ns=8),
                                              lambda v, c, sx=sx, sy=sy: c * np.where((np.abs((v[:, 2] - ground(sx, sy)) - 0.16) < 0.03)[:, None], np.array([0.62, 0.72, 0.95, 1]), 1.0)))
        A.contact(sx, sy, 0.6, 0.35)
    gx, gy = -3.7, -3.75
    A.add("battle", "MatWood_timber", paint(on_ground(K.box(0.26, 0.26, 0.2, bev=0.015), gx, gy), (0.52, 0.40, 0.27), ao=0.4, ao_h=0.2, ground=ground(gx, gy)))
    A.add("battle", "MatThatch_straw", paint(on_ground(K.lathe([(0.0, 0.0), (0.11, 0.0), (0.06, 0.06), (0.0, 0.07)], seg=10), gx, gy, -0.17), GOLD, ao=0.1))
    # far-left: tong banting + lying sheaves + nyiru tray with grain
    tong_banting(A, -5.55, 3.55)
    for k, (sx, sy, rz) in enumerate(((-3.95, 3.1, 0.3), (-4.2, 2.75, 0.5), (-3.75, 3.5, 0.1))):
        st, hd = sheaf(0.66, seed=40 + k)
        gz = ground(sx, sy)
        rot = (math.pi / 2, 0, rz + 2.2)
        A.add("battle", "MatThatch_straw", paint(xf(st, (sx, sy, gz + 0.08), rot), STRAW, var=0.07, ao=0.3, ao_h=0.15, ground=gz, namp=0.15, ns=8))
        A.add("battle", "MatThatch_straw", paint(xf(hd, (sx, sy, gz + 0.08), rot), (0.70, 0.53, 0.20), ao=0.1))
    A.contact(-4.0, 3.1, 0.8, 0.3)
    nx_, ny_ = -3.2, 4.15
    tray = K.lathe([(0.0, 0.0), (0.3, 0.0), (0.34, 0.05), (0.33, 0.06), (0.29, 0.02), (0.0, 0.02)], seg=18)
    A.add("battle", "MatThatch_straw", tint(paint(on_ground(tray, nx_, ny_), (0.58, 0.48, 0.30), ao=0.3, ao_h=0.05, ground=ground(nx_, ny_)),
                                            lambda v, c: c * (0.84 + 0.16 * ((np.floor((v[:, 0] + v[:, 1]) * 25) + np.floor((v[:, 0] - v[:, 1]) * 25)) % 2))[:, None]))
    A.add("battle", "MatThatch_straw", paint(on_ground(K.lathe([(0.0, 0.0), (0.22, 0.0), (0.1, 0.04), (0.0, 0.05)], seg=12), nx_, ny_, -0.02), GOLD, ao=0.1, top=0.2))
    # right: mengkuang mat with drying grain, caping, water jar, sickles
    mx, my, mr = 6.25, -2.0, 0.35
    mat = K.dbl(xf(K.grid(1.8, 1.05, 12, 7), (mx, my, 0.0), (0, 0, mr)))
    mat.v[:, 2] = np.array([ground(a, b) + 0.012 for a, b, _ in mat.v])
    A.add("battle", "MatThatch_straw", tint(paint(mat, (0.60, 0.50, 0.32), var=0.02, ao=0.0, top=0.0),
                                            lambda v, c: c * (0.82 + 0.18 * ((np.floor(v[:, 0] * 10) + np.floor(v[:, 1] * 10)) % 2))[:, None]))
    grain = K.dbl(xf(K.grid(1.45, 0.75, 10, 5), (mx + 0.05, my, 0.0), (0, 0, mr)))
    grain.v[:, 2] = np.array([ground(a, b) + 0.028 + 0.012 * nz(a, b, 0, 6, 3) for a, b, _ in grain.v])
    A.add("battle", "MatThatch_straw", paint(grain, (0.78, 0.62, 0.28), var=0.02, ao=0.0, top=0.0, namp=0.12, ns=14))
    A.contact(mx, my, 1.1, 0.22)
    hx, hy = 5.05, -0.85
    A.add("battle", "MatThatch_straw", tint(paint(xf(K.caping(0.25, 0.11), (hx, hy, ground(hx, hy) + 0.06), (0.4, 0, 1.0)), (0.66, 0.55, 0.34), var=0.04, ao=0.3, ao_h=0.12, ground=ground(hx, hy), top=0.2),
                                            lambda v, c: c * (0.84 + 0.16 * ((np.floor(np.arctan2(v[:, 1] - hy, v[:, 0] - hx) * 6) + np.floor(np.hypot(v[:, 0] - hx, v[:, 1] - hy) * 40)) % 2))[:, None]))
    jx, jy = 5.35, -3.65
    A.add("battle", "MatRock_kerbau", paint(on_ground(K.jar(0.16, 0.34), jx, jy, 0.02), (0.55, 0.34, 0.22), ao=0.45, ao_h=0.2, ground=ground(jx, jy), top=0.2))
    A.contact(jx, jy, 0.45, 0.3)
    for k, (sx, sy, rz) in enumerate(((5.75, -3.15, 0.9), (4.85, -2.6, 2.6))):  # sabit: wooden handle + iron crescent blade
        gz = ground(sx, sy) + 0.02
        A.add("battle", "MatWood_timber", paint(K.tube([(sx, sy, gz), (sx + 0.24 * math.cos(rz), sy + 0.24 * math.sin(rz), gz)], 0.018, seg=5), (0.45, 0.32, 0.2), ao=0.0))
        bl = [(sx + 0.24 * math.cos(rz) + 0.16 * math.cos(rz + t), sy + 0.24 * math.sin(rz) + 0.16 * math.sin(rz + t) - 0.0, gz) for t in np.linspace(-0.2, 2.2, 7)]
        A.add("battle", "MatMetal_gate", paint(K.tube(bl, [0.012, 0.016, 0.016, 0.015, 0.012, 0.008, 0.003], seg=3), (0.36, 0.34, 0.32), ao=0.0))


def straw_heaps(A):
    """sheaf stooks waiting for the thresher on the platform rim (r >= 6: they are taller than the apron rule)."""
    for k, (x, y) in enumerate(((-6.35, -2.15), (-6.0, -3.25), (5.75, 3.0))):
        stook(A, x, y, seed=30 + k, n=4)


def litter(A):
    """straw wisps and grain spills on the threshing ground (never in the bright apron)."""
    rng = random.Random(41)
    n = 0
    while n < 120:
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(5.6, 7.2)
        x, y = r * math.cos(a), r * math.sin(a)
        if plat_d(x, y) > 0.97 or abs(y - YC) < 1.2:
            continue
        n += 1
        gz = ground(x, y)
        if n % 4:
            p = K.box(rng.uniform(0.14, 0.3), 0.014, 0.008, bev=0.0)
            A.add("battle", "MatThatch_straw", paint(xf(p, (x, y, gz + 0.003), (0, 0, rng.uniform(0, 3.14))), (0.78, 0.66, 0.40), ao=0.0, top=0.0))
        else:
            p = K.rock(rng.uniform(0.03, 0.07), seed=900 + n, sub=1, squash=(1, rng.uniform(0.6, 1), 0.55))
            A.add("battle", "MatRock_kerbau", paint(xf(p, (x, y, gz - 0.01)), (0.52, 0.46, 0.38), ao=0.3, ao_h=0.04, ground=gz))


def kampung(A):
    """left flank: jelapang on the mound + sacks + palms + banana + firewood."""
    jx, jy = MOUND[0] + 0.3, MOUND[1] - 0.1
    jelapang(A, jx, jy, 0.12)
    for k, (dx, dy, dz, rz) in enumerate(((1.9, -1.95, 0, 0.1), (2.55, -1.85, 0, -0.2), (2.2, -1.5, 0.3, 0.3), (1.65, -1.45, 0, 1.4))):
        sx, sy = jx + dx, jy + dy
        p = pillow(0.6, 0.4, 0.33, seed=20 + k)
        A.add("battle", "MatCloth_guni", paint(xf(p, (sx, sy, ground(sx, sy) - 0.02 + dz), (0, 0, rz)), JUTE, var=0.06, ao=0.4, ao_h=0.4, ground=ground(sx, sy), top=0.2, namp=0.1, ns=8))
    A.contact(jx + 2.1, jy - 1.7, 1.0, 0.35)
    palm(A, MOUND[0] - 2.2, MOUND[1] + 2.0, 6.4, 11)
    palm(A, MOUND[0] - 1.0, MOUND[1] - 2.6, 5.6, 12)
    banana_clump(A, MOUND[0] + 2.6, MOUND[1] + 2.4, seed=31)
    for k in range(5):  # firewood stack against the barn stilts
        x0, y0 = jx - 1.0, jy - 1.45
        A.add("battle", "MatWood_timber", paint(K.tube([(x0, y0 + 0.02 * k, ground(x0, y0) + 0.07 + 0.11 * (k % 3)), (x0 + 1.1, y0 + 0.05 + 0.02 * k, ground(x0, y0) + 0.07 + 0.11 * (k % 3))], 0.05, seg=6),
                                                (0.44, 0.33, 0.22), var=0.1, ao=0.4, ao_h=0.4, ground=ground(x0, y0)))
    A.scatter_patch("Grass", 26, MOUND[0] - 1.2, MOUND[1] + 0.6, 1.4, ground, (0.40, 0.48, 0.20), seed=5)


def right_flank(A):
    """kerbau wallow under a shade tree + sheaf stooks on the stubble."""
    cx, cy, rx, ry, rot = WALLOW
    n = 20
    rng = random.Random(8)
    v = [(cx, cy, wallow_z())]
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 1.06 + 0.08 * rng.random()
        u, w = math.cos(t) * rx * k, math.sin(t) * ry * k
        v.append((cx + u * math.cos(rot) - w * math.sin(rot), cy + u * math.sin(rot) + w * math.cos(rot), wallow_z()))
    p = P(v, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)])
    p.c = np.array([[0.36, 0.33, 0.26, 0.85]] + [[0.30, 0.26, 0.20, 0.7]] * n)
    A.add("battle", "MatWater_sawah", p)
    place_kerbau(A, cx - 0.25, cy + 0.15, 0.35, wallow_z() - 0.22, seed=1)
    place_kerbau(A, 10.3, 0.4, 2.3, ground(10.3, 0.4) - 0.02, graze=True, seed=2)
    A.contact(10.3, 0.4, 1.6, 0.3)
    A.contact(cx, cy, 2.4, 0.35)
    shade_tree(A, TMOUND[0], TMOUND[1], seed=4)
    for k, (x, y) in enumerate(((12.0, -1.0), (12.1, 1.9), (13.2, 0.5), (12.8, 3.6), (8.8, -1.7), (13.6, -2.3))):
        stook(A, x, y, seed=k + 3)
    A.scatter_patch("Grass", 30, TMOUND[0], TMOUND[1], 1.8, ground, (0.38, 0.47, 0.19), seed=9)
    A.scatter_patch("Reed", 8, cx - 1.6, cy + 1.0, 0.6, ground, (0.42, 0.48, 0.22), seed=10)


# ================================================================ far set
def far_house(A, x, y, rz, seed):
    """distant kampung house on stilts: plank body, gable roof (thatch-coloured wood), stairs."""
    wood = [xf(K.post(1.4, 0.12, seed=seed + k, seg=4), (sx, sy, -0.3)) for k, (sx, sy) in enumerate(((-2.2, -1.5), (2.2, -1.5), (-2.2, 1.5), (2.2, 1.5)))]
    wood.append(xf(K.box(4.8, 3.4, 2.2, bev=0.06), (0, 0, 1.1)))
    roof = xf(K.thatch_roof(4.8, 3.4, 1.6, courses=2, over=0.5, seed=seed, cw=0.9), (0, 0, 3.3))
    A.add("far", "MatWood_timber", [paint(xf(q, (x, y, 0), (0, 0, rz)), (0.56, 0.44, 0.31), var=0.06, ao=0.35, ao_h=2, ground=0) for q in wood])
    A.add("far", "MatWood_timber", paint(xf(roof, (x, y, 0), (0, 0, rz)), (0.50, 0.33, 0.22), var=0.05, ao=0, top=0.25))


def far_set(A):
    rng = random.Random(77)
    # kampung tree islands in the paddy sea
    for k, (yaw, d, n) in enumerate(((-14, 72, 4), (5, 96, 5), (22, 66, 3), (30, 128, 4), (-27, 112, 3), (13, 158, 5), (-5, 182, 4), (36, 200, 3))):
        cx, cy = vpt(yaw, d)
        for t in range(max(2, n - 2)):
            x, y = cx + rng.uniform(-6, 6), cy + rng.uniform(-4, 4)
            h = rng.uniform(6, 10)
            c = blob((h * 0.62, h * 0.55, h * 0.3), sub=3 if (d < 100 and t < 2) else 2, seed=500 + k * 10 + t, amp=0.2, freq=2.4)
            A.add("far", "MatLeaf_canopy", paint(xf(c, (x, y, h * 0.62)), LEAF_DK if t % 2 else LEAF, var=0.1, ao=0.45, ao_h=h, ground=0, top=0.45, namp=0.12, ns=0.3))
            A.add("far", "MatWood_timber", paint(K.tube([(x, y, -0.2), (x + 0.3, y, h * 0.4)], [0.35, 0.25], seg=4), (0.30, 0.25, 0.2), ao=0))
        for t in range(rng.randint(1, 3)):
            palm(A, cx + rng.uniform(-7, 7), cy + rng.uniform(-5, 5), rng.uniform(8, 11), 600 + k * 5 + t, set_="far")
        if k in (0, 2, 5):  # kampung stilt house at the island edge
            far_house(A, cx + 5.0, cy - 4.0, rng.uniform(-0.4, 0.4), k)
    # layered tree lines (dark near -> paler far), then Jerai and the distant hills
    tl = lambda base, amp, s: (lambda yaw: base + amp * (0.55 + 0.45 * abs(math.sin(math.radians(yaw) * s))) + 1.5 * nz(yaw * 0.13, s, 0, 1, 7))
    A.add("far", "MatLeaf_canopy", paint_band(band(215, -52, 44, tl(6.0, 4.0, 23), 9, n=110), (0.16, 0.26, 0.13), (0.24, 0.36, 0.17), 0, 11, seed=1))
    A.add("far", "MatLeaf_canopy", paint_band(band(300, -52, 44, tl(8.0, 5.0, 17), 12, n=90), (0.20, 0.30, 0.18), (0.28, 0.38, 0.22), 0, 14, seed=2))

    def jerai(yaw):  # long massif rising from the plain, summit right of centre, steeper right shoulder
        t = (yaw - (-6)) / (46 - (-6))
        if t <= 0 or t >= 1:
            return 0.0
        s = math.sin(math.pi * t ** 0.85) ** 0.8
        return 2 + 84 * s + 7 * math.sin(t * 19 + 1) * s + 5 * nz(t * 6, 2, 0, 1, 3) * s
    jp = band(430, -6, 46, jerai, 140, n=100, prof=[(-1.0, 0.0), (-0.7, 0.45), (-0.35, 0.82), (0.0, 1.0), (0.4, 0.8), (1.0, 0.1)])
    A.add("far", "MatRock_kerbau", paint_band(jp, (0.12, 0.20, 0.17), (0.18, 0.26, 0.26), 0, 90, seed=3, namp=0.18, ns=0.02))
    foot = lambda yaw: 14 + 12 * math.sin(math.radians(yaw) * 9 + 0.5) ** 2 + 4 * nz(yaw * 0.11, 5, 0, 1, 6)
    A.add("far", "MatRock_kerbau", paint_band(band(360, -20, 48, foot, 60, n=50), (0.12, 0.20, 0.13), (0.17, 0.27, 0.17), 0, 26, seed=5))

    def hills(yaw):
        return 20 + 14 * math.sin(math.radians(yaw) * 7 + 1.0) + 6 * nz(yaw * 0.07, 9, 0, 1, 4)
    A.add("far", "MatRock_kerbau", paint_band(band(720, -54, 0, hills, 120, n=40), (0.34, 0.42, 0.42), (0.40, 0.47, 0.48), 0, 40, seed=4))
    # relief cumulus
    for k, (yaw, d, z, w, h) in enumerate(((16, 600, 122, 150, 50), (-2, 520, 96, 110, 38), (31, 470, 84, 80, 28), (-24, 560, 74, 120, 34),
                                           (-38, 640, 120, 150, 46))):
        A.add("far", "MatCloth_guni", relief_cloud(yaw, d, z, w, h, seed=k))
    A.add("far", "MatGround_padang", skirt(255, 1100, -56, 48, -0.25, (0.62, 0.58, 0.36)))


# ================================================================ build
def build(A):
    for name in ("MatGround_padang", "MatMud_sawah", "MatWater_sawah", "MatPlaster_canal", "MatMetal_gate", "MatWood_timber",
                 "MatThatch_straw", "MatCloth_guni", "MatLeaf_canopy", "MatRock_kerbau"):
        A.mat(name)

    # ---- props first (contact pools)
    kampung(A)
    right_flank(A)
    canal(A)
    apron(A)
    straw_heaps(A)
    litter(A)
    for k, (sx, sy) in enumerate(((-2.6, -6.9), (2.2, -7.0))):  # sheaves dropped on the near bund (vista foreground)
        st, hd = sheaf(0.68, seed=70 + k)
        gz = ground(sx, sy)
        A.add("battle", "MatThatch_straw", paint(xf(st, (sx, sy, gz + 0.06), (math.pi / 2, 0, 0.4 + k)), STRAW, var=0.07, ao=0.3, ao_h=0.15, ground=gz))
        A.add("battle", "MatThatch_straw", paint(xf(hd, (sx, sy, gz + 0.06), (math.pi / 2, 0, 0.4 + k)), (0.70, 0.53, 0.20), ao=0.1))

    # ---- terrain
    sp = lambda r: 0.3 if r < 12 else (0.3 + 0.07 * (r - 12) if r < 22 else (1.2 + 0.08 * (r - 22) if r < 80 else min(16.0, 5.8 + 0.2 * (r - 80))))
    A.terrain(ground, gcolor, kind=gkind, rin=4.5, rout=260.0, split=23.0, spacing=sp, cull=gcull, seed=1)

    # ---- plot grid: bunds, water sheets, paddy rows, stubble
    rows = [ROW0N - ROWH * k for k in range(8)][::-1] + [ROW0F + ROWH * k for k in range(14)]
    cols = [-6.0 - COLW * k for k in range(8)][::-1] + [6.0 + COLW * k for k in range(8)]
    for x in cols:
        for y0, y1 in zip(rows[:-1], rows[1:]):
            if y0 == ROW0N:
                continue  # central row: platform/mound/embankment edges
            ym = 0.5 * (y0 + y1)
            far = math.hypot(x, ym) > 23
            if far and (not in_vista(x, ym) or math.hypot(x, ym) > 75):
                continue
            j = row_of(ym)[0]
            top = level(j) + 0.12
            A.add("far" if far else "battle", "MatGround_padang", bund(A, (x, y0), (x, y1), top, far=far))
    for y in rows:
        for x0, x1 in zip(cols[:-1], cols[1:]):
            xm = 0.5 * (x0 + x1)
            far = math.hypot(xm, y) > 23
            if far and (not in_vista(xm, y) or math.hypot(xm, y) > 75):
                continue
            top = max(level(row_of(y - 0.1)[0]), level(row_of(y + 0.1)[0])) + 0.12
            A.add("far" if far else "battle", "MatGround_padang", bund(A, (x0, y), (x1, y), top, half=0.42 if y == ROW0N else 0.36, far=far))
    for x0, x1 in zip(cols[:-1], cols[1:]):
        for y0, y1 in zip(rows[:-1], rows[1:]):
            xm, ym = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
            i, j = col_of(xm)[0], row_of(ym)[0]
            st = state(i, j)
            lv = level(j)
            if not any(visible(px, py, pad=2) for px in (x0, x1, xm) for py in (y0, y1, ym)) or math.hypot(xm, ym) > 140:
                continue
            far = math.hypot(xm, ym) > 22
            if st in WETS:
                inner = W_YOUNG if st == "young" else W_SKY
                if far:
                    inner = (0.36, 0.48, 0.24) if st == "young" else (0.42, 0.52, 0.58)
                w = water_quad(x0, y0, x1, y1, lv - 0.02, inner, W_EDGE, inset=0.5)
                if (i, j) == (-1, 1):  # foam where the open gate spills in
                    w = water_quad(x0, y0, x1, y1, lv - 0.02, inner, W_EDGE, inset=0.5)
                    A.add("battle", "MatWater_sawah", water_quad(GATES[0][0] - 1.0, y0 + 0.3, GATES[0][0] + 1.0, y0 + 1.6, lv - 0.015, (0.5, 0.56, 0.54), (0.5, 0.56, 0.54), inset=0.45, a_in=0.4, a_edge=1.0))
                A.add("far" if far else "battle", "MatWater_sawah", w)
            if far:
                continue
            # paddy rows (ripe gold / young green) or stubble, clipped to open plot ground in view
            if st in ("ripe", "young"):
                tint_ = (GOLD if (i + j) % 2 else (0.76, 0.60, 0.24)) if st == "ripe" else YOUNG
                dens, width, step = (40, 0.2, 0.3) if st == "ripe" else (70, 0.06, 0.34)
                zf = (lambda a, b, lv=lv: lv + 0.01) if st == "ripe" else (lambda a, b, lv=lv: lv - 0.03)
                y = y0 + 0.45
                while y < y1 - 0.35:
                    run = None
                    x = x0 + 0.45
                    while x <= x1 - 0.35:
                        ok = land_h(x, y) < lv - 0.04 and visible(x, y) and wallow_d(x, y) > 1.4 and math.hypot(x, y - CAM_V[1]) < 40
                        if ok and run is None:
                            run = x
                        if (not ok or x + 0.5 > x1 - 0.35) and run is not None:
                            if x - run > 0.6:
                                A.scatter_strip("Paddy", dens, (run, y), (x, y), width, zf, tint_, step=99)
                            run = None
                        x += 0.5
                    y += step
            elif st == "stubble":
                for gy in np.arange(y0 + 0.5, y1 - 0.4, 0.55):
                    for gx in np.arange(x0 + 0.5, x1 - 0.4, 2.0):
                        if land_h(gx, gy) < lv - 0.04 and in_battle(gx, gy, 1.0) and wallow_d(gx, gy) > 1.5:
                            A.scatter_strip("Grass", 14, (gx, gy), (gx + 1.8, gy), 0.14, lambda a, b, lv=lv: lv, (0.70, 0.60, 0.36), step=99)
    # ---- grass on the platform rim, mound and embankment
    rng = random.Random(3)
    for k in range(80):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.88, 1.06)
        ay = AY_FAR if math.sin(a) > 0 else AY_NEAR
        x, y = AX * d * math.cos(a), ay * d * math.sin(a)
        if math.hypot(x, y) < 5.9 or not visible(x, y) or abs(y - YC) < 0.9:
            continue
        A.scatter_patch("Grass", 30, x, y, rng.uniform(0.4, 0.9), ground, (0.44, 0.50, 0.21), seed=k)
    for sy in (YC - CW - 0.5, YC + CW + 0.45):
        for x0 in np.arange(-16.0, 16.0, 2.0):
            if abs(x0 - BRIDGE_X) < 1.0 or any(abs(x0 - g[0]) < 0.7 for g in GATES):
                continue
            A.scatter_strip("Grass", 30, (x0, sy), (x0 + 1.7, sy), 0.42, ground, (0.42, 0.52, 0.21), step=0.6)

    far_set(A)


if __name__ == "__main__":
    K.main("kedah", build, MOOD)
