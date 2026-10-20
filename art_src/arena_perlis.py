"""Perlis arena -- earthen bund platform among flooded paddy plots at dawn (design_art.md section c).
Ground: round packed-earth bund platform + causeways + pondok mound, ordered paddy grid (bunds,
planted/open/drained cells), irrigation channel with a timber sluice gate, tidal mud bank on the right.
Apron: wreck nod (barrel, ship's rope, plank), caping hats + seedling bundles, hoe + pot.
Left flank: pondok padi on stilts + bananas. Right flank: wreck spar + hull ribs on the mud + mangroves.
Far set (vista): paddy plain, Kuala Perlis jetty + fishing boats + stilt houses + palms, limestone karsts.

  blender -b --factory-startup -P art_src/arena_perlis.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)  # blender-mcp re-runs
import numpy as np
from arenakit import P, xf, aim, join, paint, tint, nz, smooth01

# Godot ARENA_DEFS["perlis"] recommendation (+ b_* = Blender preview factors only)
MOOD = {"sky_top": (0.34, 0.40, 0.62), "sky_horizon": (0.98, 0.66, 0.50), "fog": (0.80, 0.62, 0.56),
        "fog_density": 0.005, "sun_color": (1.0, 0.80, 0.62), "sun_energy": 1.1,
        "lantern": (1.0, 0.70, 0.42), "lantern_energy": 1.4, "exposure": 0.9, "ambient": 0.45,
        "b_sun": 3.6, "b_world": 0.9, "b_fill": 0.4, "b_lantern": 12.0}

# ---------------------------------------------------------------- palette (sRGB)
EARTH = (0.46, 0.35, 0.23)
DUST = (0.50, 0.41, 0.30)
DAMP = (0.37, 0.29, 0.20)
GRASSY = (0.31, 0.37, 0.17)
WET = (0.27, 0.23, 0.17)
MUD = (0.47, 0.40, 0.31)
MUD_WET = (0.31, 0.28, 0.23)
BUND_TOP = (0.33, 0.40, 0.18)
TIMBER = (0.44, 0.34, 0.24)
TIMBER_DK = (0.29, 0.21, 0.15)
WRECK = (0.36, 0.33, 0.29)
ATAP = (0.55, 0.42, 0.27)
STRAW = (0.50, 0.41, 0.27)
TAR_ROPE = (0.32, 0.25, 0.17)
IRON = (0.24, 0.23, 0.22)
LEAF_DK = (0.16, 0.26, 0.13)
BANANA = (0.33, 0.48, 0.18)
RICE = (0.46, 0.64, 0.25)
GRASS_TINT = (0.42, 0.50, 0.22)
SEEDLING = (0.40, 0.56, 0.22)
WATER_JADE = (0.26, 0.38, 0.31)
WATER_OPEN = (0.36, 0.42, 0.43)
WATER_EDGE = (0.38, 0.35, 0.27)
WATER_FAR_RICE = (0.36, 0.47, 0.22)
SEA = (0.34, 0.43, 0.43)
CLAY = (0.55, 0.33, 0.22)

# ---------------------------------------------------------------- layout
WATER_Z = -0.16
FLOOR_Z = -0.34
SEA_Z = -0.42
AX, AY_FAR, AY_NEAR, PW = 6.4, 5.8, 6.4, 2.3        # round bund platform (superellipse)
MOUND = (-8.5, 1.0, 2.3)                            # pondok mound (x, y, r)
CAUSEWAYS = [((-5.8, 0.7), (-7.6, 0.9), 0.75), ((1.4, -5.8), (1.6, -12.6), 0.7), ((5.6, 2.3), (7.4, 2.8), 0.7)]
GX = [-61.75 + 6.5 * k for k in range(12)]          # paddy grid bund lines (x): ... -3.25, 3.25, 9.75
GY = [-37.4, -32.4, -27.4, -22.4, -17.4, -12.4, -7.4, 6.6, 8.2, 13.2, 18.2, 23.2, 28.2, 34.2, 40.2, 46.2, 52.2, 58.2, 64.2]
CH0, CH1, CH_X1 = 6.85, 7.95, 7.4                   # channel water band (y) and its outlet x (weir)
CREEK_Y = 7.4
GATE_X = -4.2
DRAINED = {(-16.25, 8.2), (-9.75, -12.4), (-29.25, 18.2), (-3.25, 23.2), (-42.25, -7.4)}   # cell (x0, y0)
OPEN = {(-16.25, -7.4), (3.25, 13.2), (-22.75, 28.2), (-9.75, 34.2)}
PATHS = [[(-4.6, 0.6), (-6.2, 0.7), (-8.0, 0.85)], [(4.6, 2.0), (6.2, 2.5), (7.4, 2.8)],
         [(1.2, -4.5), (1.45, -6.3), (1.6, -8.4)], [(-2.0, 4.2), (-3.3, 5.2), (-4.0, 6.2)]]


def shore(y):
    return 12.6 + 1.6 * math.sin(0.11 * y + 0.4) + 0.1 * max(0.0, y - 10.0)


def is_mud(x, y):
    """tidal mud: east of the paddy grid, the block right of the platform, and the outlet creek."""
    if x > GX[-1] + 0.35:
        return True
    if -7.4 < y < 6.5 and x > 3.3:
        return True
    return CH0 - 0.3 <= y < 8.2 and x > CH_X1 - 0.3


def plat_d(x, y):
    ay = AY_FAR if y > 0 else AY_NEAR
    return ((abs(x) / AX) ** PW + (abs(y) / ay) ** PW) ** (1.0 / PW)


def seg_dist(px, py, a, b):
    ax_, ay_ = a
    bx, by = b
    dx, dy = bx - ax_, by - ay_
    t = max(0.0, min(1.0, ((px - ax_) * dx + (py - ay_) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax_ - t * dx, py - ay_ - t * dy)


def path_dist(x, y):
    return min(seg_dist(x, y, a, b) for pl in PATHS for a, b in zip(pl[:-1], pl[1:]))


def cell_of(x, y):
    """grid cell (x0, y0, x1, y1) containing the point, or None outside the paddy grid."""
    if x > GX[-1] or x < GX[0]:
        return None
    i = max(k for k in range(len(GX)) if GX[k] <= x)
    js = [k for k in range(len(GY) - 1) if GY[k] <= y < GY[k + 1]]
    if i >= len(GX) - 1 or not js:
        return None
    j = js[0]
    return GX[i], GY[j], GX[i + 1], GY[j + 1]


def is_channel(x, y):
    return CH0 - 0.15 <= y <= CH1 + 0.15 and x < CH_X1


def drained(c):
    return c is not None and (c[0], c[1]) in DRAINED


def _raise(top, d, d0, d1):
    return top + (FLOOR_Z - top) * smooth01(d0, d1, d)


def land_h(x, y):
    """height of raised land (platform / mound / causeways); dips to the paddy floor outside them."""
    d = plat_d(x, y)
    top = 0.035 * (1 - min(d, 1.0) ** 2) + 0.025 * nz(x, y, 0, 0.7, 3)
    h = _raise(top, d, 1.0, 1.15)
    dm = math.hypot(x - MOUND[0], y - MOUND[1]) / MOUND[2]
    h = max(h, _raise(0.04 + 0.02 * nz(x, y, 1, 0.9, 4), dm, 1.0, 1.28))
    for a, b, w in CAUSEWAYS:
        h = max(h, _raise(0.0 + 0.015 * nz(x, y, 2, 1.1, 5), seg_dist(x, y, a, b), w, w + 0.42))
    return float(h)


def ground(x, y):
    h = land_h(x, y)
    if is_mud(x, y):  # tidal mud bank sloping into the estuary, a creek carrying the channel outflow
        s = shore(y)
        mb = -0.07 + 0.035 * nz(x, y, 2, 0.8, 5) + 0.02 * nz(x, y, 2, 3.0, 6)
        mb -= 0.3 * smooth01(7.0, s + 0.6, x) + 0.4 * smooth01(s + 0.6, s + 4.0, x)
        if x > CH_X1 - 0.2:
            mb -= 0.32 * (1 - smooth01(0.3, 0.85, abs(y - CREEK_Y)))
        return max(h, mb)
    c = cell_of(x, y)
    if is_channel(x, y):
        h = max(h, -0.62)
    elif drained(c):  # ploughed, drying plot with furrows
        fur = 0.035 * math.sin(y * 9.0 + 0.6 * nz(x, y, 0, 1.3, 6))
        h = max(h, -0.11 + fur + 0.02 * nz(x, y, 3, 2.0, 7))
    else:
        h = max(h, FLOOR_Z + 0.02 * nz(x, y, 5, 1.5, 8))
    pd = path_dist(x, y)
    if pd < 0.6 and h > -0.05:
        h -= 0.022 * (1 - smooth01(0.1, 0.6, pd))
    return h


def in_water(x, y):
    """which water sheet covers (x, y): sea / creek / channel / paddy / None."""
    if x > shore(y) - 0.4:
        return "sea"
    if is_mud(x, y):
        return "creek" if x > CH_X1 - 0.3 and abs(y - CREEK_Y) < 0.45 else None
    if is_channel(x, y) and CH0 <= y <= CH1:
        return "channel"
    c = cell_of(x, y)
    if c is None or drained(c):
        return None
    return "paddy"


def in_vista(x, y):
    dx, dy = x + 1.5, y + 12.5
    return dy > 2 and -58 < math.degrees(math.atan2(dx, dy)) < 44


def visible(x, y, pad=0.0):
    """inside the battle frame or the vista frustum (nothing else is ever seen)."""
    return (y > -6.5 - pad and abs(x) < 11 + 0.55 * (y + 6.5) + pad) or in_vista(x, y)


def mix(a, b, t):
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def gcolor(x, y, z):
    n1 = nz(x, y, 0, 0.45, 11)
    n2 = nz(x, y, 0, 2.3, 12)
    n3 = nz(x, y, 0, 6.0, 13)
    wet = 1 - smooth01(WATER_Z - 0.02, WATER_Z + 0.14, z)
    if is_mud(x, y) and land_h(x, y) < -0.06:
        s = shore(y)
        c = np.array(MUD) * (1 + 0.12 * n1 + 0.07 * n2 + 0.04 * n3)
        c = mix(c, MUD_WET, 0.7 * smooth01(s - 3.5, s, x) + 0.35 * smooth01(0.2, 0.6, nz(x, y, 0, 0.6, 14)))
        c = mix(c, MUD_WET, 0.6 * (1 - smooth01(0.3, 0.9, abs(y - CREEK_Y))) * smooth01(CH_X1 - 0.5, CH_X1, x))
        return tuple(c)
    c = cell_of(x, y)
    if drained(c) and z < -0.03:
        fur = 0.5 + 0.5 * math.sin(y * 9.0 + 0.6 * nz(x, y, 0, 1.3, 6))
        base = np.array(MUD) * (0.82 + 0.25 * fur + 0.08 * n2)
        return tuple(base * (1 - 0.25 * wet))
    d = plat_d(x, y)
    pd = path_dist(x, y)
    base = np.array(EARTH) * (1 + 0.12 * n1 + 0.08 * n2 + 0.05 * n3)
    base = mix(base, DAMP, 0.65 * smooth01(0.1, 0.5, nz(x, y, 0, 0.35, 15)))          # damp low patches
    base = mix(base, DUST, 0.55 * smooth01(0.15, 0.45, nz(x, y, 0, 0.5, 16)))           # dry cracked patches
    grass = smooth01(0.05, 0.6, 0.45 + 0.6 * n1) * 0.55 + 0.6 * smooth01(0.8, 1.02, d)
    grass = min(1.0, grass * smooth01(0.25, 0.9, pd))
    base = mix(base, np.array(GRASSY) * (1 + 0.1 * n2), grass)
    base = mix(base, DUST, 0.75 * (1 - smooth01(0.0, 0.5, pd)))                          # worn paths
    r = math.hypot(x, y)
    base = mix(base, np.array(EARTH) * 1.05, 0.7 * (1 - smooth01(4.6, 5.5, r)))           # trodden apron
    base = mix(base, WET, 0.6 * wet)
    return tuple(base)


def gkind(x, y, z):
    if math.hypot(x, y) > 23:  # far set: one ground material (<=6 far materials)
        return "MatGround_bund"
    if (is_mud(x, y) and land_h(x, y) < -0.06) or (drained(cell_of(x, y)) and z < -0.03):
        return "MatMud_bank"
    if z > -0.05 and math.hypot(x, y) > 5.7 and nz(x, y, 0, 0.5, 16) > 0.3 and path_dist(x, y) > 0.5:
        return "MatMud_bank"  # sun-baked cracked patches
    return "MatGround_bund"


def gcull(cx, cy, zmax):
    w = in_water(cx, cy)
    if w == "sea":
        return zmax < SEA_Z - 0.04
    if w == "creek":
        return zmax < SEA_Z
    if w:
        return zmax < WATER_Z - 0.03
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


# ---------------------------------------------------------------- helpers
def on_ground(p, x, y, sink=0.0):
    """translate a local piece so its base sits on the terrain at (x, y)."""
    return xf(p, (x, y, ground(x, y) - sink))


def bund_line(A, path, half=0.42, top=0.06, step=0.45, far=False):
    """paddy bund (batas) along a 2D path: skip runs hidden under raised land, grassy crown + wet foot."""
    pts = []
    for (x0, y0), (x1, y1) in zip(path[:-1], path[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(L / step))
        pts += [(x0 + (x1 - x0) * i / k, y0 + (y1 - y0) * i / k) for i in range(k)]
    pts.append(path[-1])
    runs, cur = [], []
    for (x, y) in pts:
        ok = land_h(x, y) < top - 0.06 and visible(x, y, pad=3.0) and math.hypot(x, y) < 31 and not is_mud(x, y)
        if ok:
            cur.append((x, y))
        elif len(cur) > 1:
            runs.append(cur)
            cur = []
        else:
            cur = []
    if len(cur) > 1:
        runs.append(cur)
    prof = ([(-half, FLOOR_Z), (-half * 0.62, WATER_Z + 0.02), (0.0, top), (half * 0.62, WATER_Z + 0.02), (half, FLOOR_Z)]
            if far else
            [(-half, FLOOR_Z), (-half * 0.72, WATER_Z - 0.02), (-half * 0.45, top - 0.05), (0.0, top), (half * 0.45, top - 0.05),
             (half * 0.72, WATER_Z - 0.02), (half, FLOOR_Z)])
    out = []
    for run in runs:
        p = K.extrude(run, prof, step=step if not far else 2.5, jitter=0.0 if far else 0.12,
                      seed=int(abs(run[0][0] * 7 + run[0][1] * 13)))
        z = p.v[:, 2]
        n1 = np.array([nz(a, b, 0, 0.8, 21) for a, b, _ in p.v])
        g = smooth01(WATER_Z + 0.03, top - 0.01, z)
        c = (np.array(EARTH)[None, :] * (1 - g[:, None]) + np.array(BUND_TOP)[None, :] * g[:, None]) * (1 + 0.12 * n1)[:, None]
        wet = 1 - smooth01(WATER_Z - 0.03, WATER_Z + 0.1, z)
        c = c * (1 - 0.65 * wet[:, None]) + np.array(WET)[None, :] * 0.65 * wet[:, None]
        p.c = np.ones((len(p.v), 4))
        p.c[:, :3] = np.clip(c, 0, 1)
        out.append(p)
        if not far:  # grass verge along the bund crown
            pts = run[::3] + ([run[-1]] if (len(run) - 1) % 3 else [])
            for a, b in zip(pts[:-1], pts[1:]):
                A.scatter_strip("Grass", 30, a, b, 0.34, lambda a_, b_: top - 0.01, GRASS_TINT, step=99)
    return out


def water_cell(x0, y0, x1, y1, z, inner, edge, inset=0.5, a_in=1.0, a_edge=1.0):
    v = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z),
         (x0 + inset, y0 + inset, z), (x1 - inset, y0 + inset, z), (x1 - inset, y1 - inset, z), (x0 + inset, y1 - inset, z)]
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
    p = P(v, f)
    p.c = np.array([list(edge) + [a_edge]] * 4 + [list(inner) + [a_in]] * 4)
    return p


# ---------------------------------------------------------------- props
def pondok(A, x, y, rz):
    """pondok padi: field hut on stilts with atap gable roof, woven walls, ladder, lamp."""
    W, D, FH, EAVE = 2.4, 2.0, 1.15, 2.45
    wood, thatch, cloth, rock, glow, metal = [], [], [], [], [], []
    for sx in (-1.05, 0.0, 1.05):
        for sy in (-0.85, 0.85):
            wood.append(xf(K.post(EAVE if sx != 0 else FH + 0.05, 0.075, seed=int(sx * 10 + sy * 7)), (sx, sy, -0.05)))
            rock.append(xf(K.smooth_rock(0.15, seed=int(sx * 3 + sy * 5 + 40), sub=2, squash=(1, 1, 0.5)), (sx, sy, -0.04)))
    for sy in (-0.85, 0.85):
        wood.append(xf(K.box(2.5, 0.1, 0.1, bev=0.015), (0, sy, FH - 0.05)))
    for k in range(10):
        wood.append(xf(K.plank(2.0, 0.215, 0.035, warp=0.01), (-1.08 + k * 0.24, 0, FH + 0.05), (0, 0, math.pi / 2)))
    for sx in (-1.12, 1.12):  # top plates + wall rails
        wood.append(xf(K.box(0.09, 1.9, 0.09, bev=0.012), (sx, 0, EAVE - 0.09)))
    for sy in (-0.88, 0.88):
        wood.append(xf(K.box(2.4, 0.09, 0.09, bev=0.012), (0, sy, EAVE - 0.09)))
    wood.append(xf(K.box(2.3, 0.06, 0.06, bev=0.01), (0, -0.88, FH + 0.62)))      # front railing
    wood.append(xf(K.box(0.06, 1.7, 0.06, bev=0.01), (1.12, 0, FH + 0.62)))       # right railing
    # woven kelarai walls (back + left), with a diagonal weave in vertex colour
    weave = lambda v, c: c * (0.86 + 0.14 * ((np.floor((v[:, 0] + v[:, 2]) * 7) + np.floor((v[:, 1] + v[:, 2]) * 7)) % 2))[:, None]
    back = xf(K.box(2.2, 0.035, 1.1, bev=0.01), (0, 0.86, FH + 0.08))
    left = xf(K.box(0.035, 1.66, 1.1, bev=0.01), (-1.1, 0, FH + 0.08))
    gables = [K.dbl(P([(sx, -1.0, EAVE), (sx, 1.0, EAVE), (sx, 0, EAVE + 1.0)], [(0, 1, 2)])) for sx in (-1.13, 1.13)]
    roof = xf(K.thatch_roof(W, D, 1.05, courses=7, over=0.34, seed=3, tooth=0.07, cw=0.16), (0, 0, EAVE))
    for ox in (-0.2, 0.2):  # ladder
        wood.append(K.tube([(0.5 + ox, -1.6, -0.05), (0.5 + ox, -0.95, FH + 0.15)], 0.03, seg=5))
    for k in range(4):
        t = (k + 1) / 5
        wood.append(K.tube([(0.28, -1.6 + 0.65 * t, FH * t), (0.72, -1.6 + 0.65 * t, FH * t)], 0.022, seg=5))
    glow.append(xf(K.lathe([(0, 0), (0.05, 0.0), (0.06, 0.06), (0.03, 0.12), (0, 0.13)], seg=8), (0.55, -0.6, EAVE - 0.42)))
    metal.append(K.tube([(0.55, -0.6, EAVE - 0.29), (0.55, -0.6, EAVE - 0.05)], 0.006, seg=3))
    sar = K.strip_mesh([(1.14, -0.7 + 0.25 * k, FH + 0.66 - 0.04 * math.sin(k)) for k in range(6)], [0.3] * 6, up=(1, 0, 0), seed=5)
    sar.v[:, 0] += 0.02
    cloth.append(sar)
    thatch.append(xf(xf(K.caping(0.24, 0.1), (0, 0, 0), (math.pi / 2.2, 0, 0)), (-1.05, -0.95, 1.9)))
    jar = xf(K.jar(0.2, 0.46), (-0.75, -1.45, -0.04))
    for k in range(5):  # firewood under the floor
        wood.append(K.tube([(-0.6 + 0.02 * k, -0.3 + 0.13 * k, 0.08 + 0.12 * (k % 2)), (0.5, -0.25 + 0.13 * k, 0.07 + 0.12 * (k % 2))],
                           0.055, seg=6))

    gz = ground(x, y)

    def put(lst):
        return [xf(p, (x, y, gz), (0, 0, rz)) for p in lst]
    A.add("battle", "MatWood_timber", [paint(q, TIMBER if i % 3 else TIMBER_DK, var=0.1, ao=0.5, ao_h=1.0, ground=gz, namp=0.1, ns=3.0, stretch=(1, 1, 0.2))
                                      for i, q in enumerate(put(wood))])
    course = lambda v, c: c * (0.82 + 0.22 * (np.floor((v[:, 2] - gz - EAVE) * 7.0 / 1.05 + 0.5) % 2))[:, None] *         (0.8 + 0.2 * np.clip((v[:, 2] - gz - EAVE) / 1.05, 0, 1))[:, None]
    A.add("battle", "MatThatch_atap", [tint(paint(q, ATAP, var=0.04, ao=0.0, ground=gz, top=0.3, namp=0.25, ns=3.0, stretch=(6, 6, 0.4)), course)
                                      for q in put([roof])])
    A.add("battle", "MatThatch_atap", [tint(paint(q, STRAW, var=0.05, ao=0.4, ao_h=1.6, ground=gz), weave) for q in put([back, left] + gables)])
    A.add("battle", "MatThatch_atap", [paint(q, STRAW, ao=0.2, ground=gz) for q in put(thatch)])
    A.add("battle", "MatCloth_batik", [tint(paint(q, (0.30, 0.30, 0.46), var=0.0, ao=0.2, ground=gz),
                                            lambda v, c: c * (0.75 + 0.25 * (np.floor(v[:, 2] * 18) % 2))[:, None]) for q in put(cloth)])
    A.add("battle", "MatRock_stone", [paint(q, CLAY, ao=0.45, ao_h=0.3, ground=gz, top=0.2) for q in put([jar])])
    A.add("battle", "MatRock_stone", [paint(q, (0.42, 0.40, 0.36), ao=0.5, ao_h=0.15, ground=gz) for q in put(rock)])
    A.add("battle", "MatGlow_pelita", [paint(q, (1.0, 0.8, 0.5), ao=0.0, top=0.0) for q in put(glow)])
    A.add("battle", "MatMetal_iron", [paint(q, IRON, ao=0.0) for q in put(metal)])
    lp = xf(P([(0.55, -0.6, EAVE - 0.36)], []), (x, y, gz), (0, 0, rz)).v[0]
    A.light(tuple(lp), 14.0, (1.0, 0.62, 0.3), range_m=4)
    A.contact(x, y, 2.1, 0.32)


def banana_clump(A, x, y, seed):
    rng = random.Random(seed)
    for k, (dx, dy, h) in enumerate(((0, 0, 2.9), (0.7, -1.1, 2.2), (-0.6, 0.9, 1.5))):
        st, lv = K.banana(h * rng.uniform(0.9, 1.1), seed=seed + k, leaves=6 if h > 2 else 4)
        px, py = x + dx, y + dy
        gz = ground(px, py)
        rz = rng.uniform(0, 6.28)
        A.add("battle", "MatLeaf_canopy", paint(xf(lv, (px, py, gz - 0.05), (0, 0, rz)), BANANA, var=0.08, ao=0.35, ao_h=2.4, ground=gz, top=0.25, namp=0.15, ns=2))
        A.add("battle", "MatWood_timber", paint(xf(st, (px, py, gz - 0.05), (0, 0, rz)), (0.40, 0.42, 0.24), var=0.06, ao=0.4, ao_h=1.2, ground=gz))
        A.contact(px, py, 1.0, 0.25)
    A.scatter_patch("Grass", 24, x, y, 1.9, ground, GRASS_TINT, seed=seed)


def sluice_gate(A, x):
    """pintu air across the channel: posts, crossbeam, raised plank gate, screw + hand wheel, revetments."""
    yc = 0.5 * (CH0 + CH1)
    wood, metal, rock = [], [], []
    for yy in (CH0 - 0.18, CH1 + 0.18):
        wood.append(xf(K.box(0.2, 0.2, 1.65, bev=0.025), (x, yy, -0.55)))
        wood.append(xf(K.box(0.24, 0.24, 0.06, bev=0.015), (x, yy, 1.08)))
    wood.append(xf(K.box(0.18, 1.75, 0.16, bev=0.02), (x, yc, 0.86)))
    for k in range(5):  # gate boards, raised 0.2 above the water
        wood.append(xf(K.box(0.07, 0.215, 0.62, bev=0.012), (x + 0.12, CH0 + 0.11 + k * 0.22, WATER_Z + 0.2)))
    wood.append(xf(K.box(0.09, 1.15, 0.08, bev=0.012), (x + 0.12, yc, WATER_Z + 0.78)))
    for side in (-1, 1):  # plank walkway either side of the frame
        wood.append(xf(K.plank(1.8, 0.24, 0.05), (x - 0.35 * side, yc, 0.08), (0, 0, math.pi / 2)))
    metal.append(K.tube([(x + 0.12, yc, WATER_Z + 0.8), (x + 0.12, yc, 1.32)], 0.025, seg=6))
    metal.append(xf(K.wheel(0.2, 0.016), (x + 0.12, yc, 1.32), (math.pi / 2, 0, 0)))
    for side, yy in ((-1, CH0 - 0.06), (1, CH1 + 0.06)):  # timber revetment along both banks
        for row in range(2):
            wood.append(xf(K.plank(3.4, 0.16, 0.05, bev=0.01), (x + 0.4, yy, WATER_Z - 0.12 + row * 0.17), (math.pi / 2, 0, 0)))
        for k in range(5):
            wood.append(xf(K.post(0.55, 0.045, seed=k * 3 + side), (x - 1.2 + 0.8 * k, yy + side * 0.05, WATER_Z - 0.3)))
    for k in range(5):
        rock.append(xf(K.rock(0.18 + 0.05 * (k % 2), seed=60 + k, sub=2), (x + 0.6 + 0.3 * k, CH0 - 0.25 + (k % 2) * 1.6, WATER_Z - 0.12)))
    # outlet weir where the channel spills into the mud creek
    wood.append(xf(K.plank(1.5, 0.22, 0.06), (CH_X1 - 0.1, yc, WATER_Z - 0.18), (math.pi / 2, 0, math.pi / 2)))
    for yy in (CH0 - 0.1, CH1 + 0.1):
        wood.append(xf(K.post(0.6, 0.05, seed=int(yy * 10)), (CH_X1 - 0.1, yy, -0.5)))
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, var=0.1, ao=0.55, ao_h=0.5, ground=WATER_Z, namp=0.12, ns=3, stretch=(1, 1, 0.15)) for q in wood])
    A.add("battle", "MatMetal_iron", [paint(q, IRON, ao=0.2, ground=0.5) for q in metal])
    A.add("battle", "MatRock_stone", [paint(q, (0.40, 0.38, 0.34), ao=0.5, ao_h=0.2, ground=WATER_Z) for q in rock])


def apron(A):
    """three small clusters on the bund apron (<=0.6 m, nothing bright within 1.5 m of the rope)."""
    # wreck nod: barrel lying on its side, coil of ship's rope, broken plank with nails
    bw, bm = K.barrel(0.26, 0.6)
    bx, by = -5.05, -1.25
    for p, mat, col in ((bw, "MatWood_timber", (0.36, 0.26, 0.17)), (bm, "MatMetal_iron", IRON)):
        q = xf(p, (-0.3, 0, -0.26), (0, math.pi / 2, 0))  # lay it down (axis along x), centred on the origin
        q = xf(q, (bx, by, ground(bx, by) + 0.24), (0.08, 0, 0.5))
        A.add("battle", mat, paint(q, col, var=0.05, ao=0.5, ao_h=0.4, ground=ground(bx, by), namp=0.1, ns=4, stretch=(1, 1, 0.3)))
    A.contact(bx, by, 0.9, 0.38)
    rx, ry = -4.45, -2.75
    A.add("battle", "MatThatch_atap", paint(on_ground(K.rope_coil(0.42, 0.036, seed=2), rx, ry, 0.01), TAR_ROPE, var=0.04, ao=0.45, ao_h=0.15, ground=ground(rx, ry), namp=0.15, ns=8))
    A.contact(rx, ry, 0.7, 0.3)
    px, py = -5.25, -1.65
    A.add("battle", "MatWood_timber", paint(xf(K.plank(1.25, 0.24, 0.05, warp=-0.03), (px, py, ground(px, py) + 0.005), (0.05, 0, 1.2)), WRECK, var=0.06, ao=0.3, ao_h=0.1, ground=ground(px, py), namp=0.15, ns=4))
    for k in range(3):
        nx_, ny_ = px + (k - 1) * 0.4 * math.cos(1.2), py + (k - 1) * 0.4 * math.sin(1.2)
        A.add("battle", "MatMetal_iron", paint(xf(K.tube([(0, 0, 0), (0, 0, 0.05)], 0.008, seg=4), (nx_, ny_, ground(px, py) + 0.04)), (0.3, 0.2, 0.14), ao=0))
    # caping hats + seedling bundles + basket (far-right apron)
    for (hx, hy), tilt, rz in (((4.2, 4.35), 0.0, 0.0), ((4.85, 3.75), 0.42, 1.0)):
        A.add("battle", "MatThatch_atap", tint(paint(xf(K.caping(0.25, 0.11), (hx, hy, ground(hx, hy) + 0.02 + tilt * 0.15), (tilt, 0, rz)), STRAW, var=0.04, ao=0.35, ao_h=0.12, ground=ground(hx, hy), top=0.2),
                                                lambda v, c, hx=hx, hy=hy: c * (0.84 + 0.16 * ((np.floor(np.arctan2(v[:, 1] - hy, v[:, 0] - hx) * 6) + np.floor(np.hypot(v[:, 0] - hx, v[:, 1] - hy) * 40)) % 2))[:, None]))
        A.contact(hx, hy, 0.45, 0.3)
    bx, by = 5.1, 4.25
    A.add("battle", "MatThatch_atap", tint(paint(on_ground(K.basket(0.17, 0.2), bx, by), (0.45, 0.36, 0.24), ao=0.4, ao_h=0.2, ground=ground(bx, by)),
                                           lambda v, c: c * (0.85 + 0.15 * ((np.floor(v[:, 2] * 40) + np.floor(np.arctan2(v[:, 1] - by, v[:, 0] - bx) * 5)) % 2))[:, None]))
    A.contact(bx, by, 0.4, 0.3)
    for k, (sx, sy) in enumerate(((3.75, 4.85), (4.1, 5.0), (5.5, 3.5), (5.3, 4.75))):
        A.add("battle", "MatLeaf_canopy", paint(on_ground(K.seedling_bundle(0.3, seed=k), sx, sy, 0.02), SEEDLING, var=0.08, ao=0.45, ao_h=0.25, ground=ground(sx, sy)))
    # hoe + clay pot (far-left apron)
    hx, hy = -3.4, 4.75
    A.add("battle", "MatWood_timber", paint(K.tube([(hx - 0.55, hy - 0.2, ground(hx, hy) + 0.03), (hx + 0.55, hy + 0.15, ground(hx, hy) + 0.05)], 0.022, seg=5), (0.5, 0.38, 0.25), ao=0.3, ao_h=0.05, ground=ground(hx, hy)))
    A.add("battle", "MatMetal_iron", paint(xf(K.box(0.22, 0.26, 0.012, bev=0.004), (hx + 0.62, hy + 0.17, ground(hx, hy) + 0.01), (0, 0.3, 0.3)), (0.3, 0.28, 0.26), ao=0.0))
    px, py = -4.15, 4.35
    A.add("battle", "MatRock_stone", paint(on_ground(K.jar(0.15, 0.3), px, py, 0.02), CLAY, ao=0.45, ao_h=0.2, ground=ground(px, py), top=0.2))
    A.contact(px, py, 0.4, 0.3)
    for k, (sx, sy) in enumerate(((-2.5, 5.3), (-3.0, 5.1))):
        A.add("battle", "MatLeaf_canopy", paint(on_ground(K.seedling_bundle(0.28, seed=10 + k), sx, sy, 0.02), SEEDLING, var=0.08, ao=0.45, ao_h=0.25, ground=ground(sx, sy)))


def litter(A):
    """pebbles + straw bits on the outer platform and causeways (never on the bright apron)."""
    rng = random.Random(41)
    n = 0
    while n < 150:
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(5.7, 7.4)
        x, y = r * math.cos(a), r * math.sin(a)
        if land_h(x, y) < -0.06 or path_dist(x, y) < 0.25:
            continue
        n += 1
        gz = ground(x, y)
        if n % 3:
            p = K.rock(rng.uniform(0.03, 0.09), seed=900 + n, sub=1, squash=(1, rng.uniform(0.6, 1), 0.55))
            A.add("battle", "MatRock_stone", paint(xf(p, (x, y, gz - 0.01)), (0.44, 0.40, 0.34) if n % 2 else (0.30, 0.27, 0.23), ao=0.3, ao_h=0.04, ground=gz))
        else:
            p = K.box(rng.uniform(0.12, 0.22), 0.012, 0.008, bev=0.0)
            A.add("battle", "MatThatch_atap", paint(xf(p, (x, y, gz + 0.002), (0, 0, rng.uniform(0, 3.14))), (0.58, 0.50, 0.34), ao=0.0, top=0.0))


def wreck(A):
    """right flank: broken mast propped on a rock, rope, torn sail, hull ribs in the tidal mud."""
    wood, rope, metal, cloth, rock = [], [], [], [], []
    rk = (10.2, 2.4)
    rock.append(on_ground(K.rock(0.5, seed=91, sub=3, squash=(1.2, 1, 0.75)), rk[0], rk[1], 0.1))
    rock.append(on_ground(K.rock(0.28, seed=92, sub=2), rk[0] + 0.6, rk[1] - 0.5, 0.05))
    a = (7.3, -0.4, ground(7.3, -0.4) + 0.06)
    b = (10.8, 2.8, ground(rk[0], rk[1]) + 0.78)
    wood.append(K.tube([a, tuple(np.add(a, np.subtract(b, a) * 0.5)), b], [0.15, 0.13, 0.1], seg=9))
    for k in range(5):  # splintered broken end
        ang = k * 1.26
        tip = np.add(a, (-0.22 - 0.1 * (k % 3), -0.18 - 0.05 * (k % 2), 0.05 * math.sin(ang)))
        wood.append(K.tube([tuple(np.add(a, (0.02, 0.08 * math.cos(ang), 0.08 * math.sin(ang)))), tuple(tip)], [0.035, 0.004], seg=4, cap=False))
    for t in (0.3, 0.55, 0.8):
        c = np.add(a, np.subtract(b, a) * t)
        metal.append(aim(K.lathe([(0.15, -0.03), (0.16, 0.0), (0.15, 0.03)], seg=12, cap0=False, cap1=False), tuple(c), tuple(np.add(c, np.subtract(b, a)))))
    y0 = (8.6, 0.5, ground(8.6, 0.5) + 0.2)
    y1 = (9.4, 2.9, ground(9.4, 2.9) + 0.5)
    wood.append(K.tube([y0, y1], [0.07, 0.05], seg=7))
    rope.append(K.tube(K.arc(tuple(np.add(a, np.subtract(b, a) * 0.62)), (9.6, 0.4, ground(9.6, 0.4) + 0.02), 0.05, n=8, side=(0.3, -0.2, 0)), 0.025, seg=5))
    rope.append(K.tube(K.arc(tuple(np.add(a, np.subtract(b, a) * 0.85)), (11.0, 1.6, ground(11.0, 1.6) + 0.02), -0.2, n=8), 0.022, seg=5))
    sail = xf(K.grid(2.4, 1.1, 10, 5), (8.8, -0.4, 0), (0, 0, 0.35))  # crumpled torn sail draped on the mud
    sail.v[:, 2] = np.array([ground(px, py) + 0.025 + 0.09 * max(0.0, nz(px, py, 0, 2.2, 31)) for px, py, _ in sail.v])
    sail.f = [f for f in sail.f if nz(*sail.v[list(f)].mean(axis=0)[:2], 0, 1.8, 32) > -0.45]  # ragged holes
    cloth.append(sail)
    # hull ribs arching out of the mud along a buried keel (ribs rise seaward)
    k0, k1 = np.array((8.3, 3.6)), np.array((9.5, 7.3))
    n_ = np.array((k1 - k0)[1], dtype=float), -float((k1 - k0)[0])
    n_ = np.array(n_) / np.linalg.norm(n_)
    for i in range(6):
        t = i / 5
        c = k0 + (k1 - k0) * t
        h = [1.5, 1.75, 1.6, 1.2, 0.75, 1.35][i]
        top = c + n_ * (0.85 - 0.12 * (i % 2))
        gz = ground(c[0], c[1])
        path = K.arc((c[0] - n_[0] * 0.25, c[1] - n_[1] * 0.25, gz - 0.15), (top[0], top[1], gz + h), 0.0, n=6, side=(n_[0] * 0.45, n_[1] * 0.45, 0))
        wood.append(K.tube(path, [0.09, 0.085, 0.08, 0.075, 0.07, 0.06, 0.05], seg=6))
        path2 = K.arc((c[0] - n_[0] * 0.25, c[1] - n_[1] * 0.25, gz - 0.15), (c[0] - n_[0] * 0.9, c[1] - n_[1] * 0.9, gz + h * 0.45), 0.0, n=4, side=(-n_[0] * 0.2, -n_[1] * 0.2, 0))
        wood.append(K.tube(path2, [0.08, 0.075, 0.07, 0.06, 0.05], seg=6))
    wood.append(K.tube([(k0[0], k0[1], ground(*k0) - 0.04), (k1[0], k1[1], ground(*k1) - 0.04)], 0.13, seg=6))
    for i in range(2):  # surviving hull planks
        pts = []
        for t in np.linspace(0.0, 0.62, 5):
            c = k0 + (k1 - k0) * t
            pts.append((c[0] + n_[0] * (0.38 + 0.2 * i), c[1] + n_[1] * (0.38 + 0.2 * i), ground(c[0], c[1]) + 0.32 + 0.3 * i))
        wood.append(K.tube(pts, 0.05, seg=4))
    for k, (cx, cy, rz) in enumerate(((7.6, 5.2, 0.4), (8.0, 5.9, 1.9), (10.6, 5.6, 2.6))):  # loose planks + crate
        wood.append(xf(K.plank(1.1, 0.2, 0.045, warp=0.02), (cx, cy, ground(cx, cy) + 0.005), (0.04, 0, rz)))
    wood.append(xf(K.box(0.42, 0.42, 0.36, bev=0.03), (7.5, 6.3, ground(7.5, 6.3) - 0.05), (0.15, 0.08, 0.6)))
    A.add("battle", "MatWood_timber", [paint(q, WRECK, var=0.12, ao=0.5, ao_h=0.6, ground=-0.25, namp=0.2, ns=3, stretch=(1, 1, 0.3)) for q in wood])
    A.add("battle", "MatThatch_atap", [paint(q, TAR_ROPE, ao=0.2, ground=-0.2) for q in rope])
    A.add("battle", "MatMetal_iron", [paint(q, (0.30, 0.22, 0.17), ao=0.2, ground=-0.2) for q in metal])
    A.add("battle", "MatCloth_batik", [paint(q, (0.27, 0.25, 0.22), var=0.0, ao=0.3, ao_h=0.15, ground=-0.25, namp=0.25, ns=2) for q in cloth])
    A.add("battle", "MatRock_stone", [paint(q, (0.38, 0.36, 0.33), ao=0.45, ao_h=0.4, ground=-0.15, namp=0.12, ns=2) for q in rock])
    for (cx, cy, r) in ((8.9, 5.4, 2.0), (8.8, 0.9, 1.8), (10.2, 2.4, 0.9)):
        A.contact(cx, cy, r, 0.3)


def puddles(A):
    """tide pools on the mud bank: small sky-reflecting water discs, darker wet mud around them."""
    rng = random.Random(17)
    for k, (x, y, r) in enumerate(((7.6, -3.6, 0.7), (9.2, -1.6, 0.9), (8.1, 1.6, 0.5), (10.6, 0.2, 0.6), (7.4, -6.0, 0.8),
                                   (9.6, -4.8, 0.6), (10.9, 6.6, 0.7))):
        n = 9
        z = ground(x, y) + 0.012
        v = [(x, y, z)] + [(x + r * rng.uniform(0.6, 1.2) * math.cos(2 * math.pi * i / n),
                            y + r * rng.uniform(0.5, 1.0) * math.sin(2 * math.pi * i / n), z) for i in range(n)]
        p = P(v, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)])
        p.c = np.array([[0.30, 0.34, 0.35, 1.0]] + [[0.22, 0.21, 0.19, 0.85]] * n)
        A.add("battle", "MatWater_paddy", p)
        A.contact(x, y, r * 1.8, 0.3)


def mangroves(A, spots, set_="battle"):
    for k, (x, y, h) in enumerate(spots):
        wd, lf = K.mangrove(h, seed=200 + k + (50 if set_ == "far" else 0), lod=1 if set_ == "far" else 0)
        base = max(ground(x, y), SEA_Z - 0.05)
        A.add(set_, "MatWood_timber", paint(xf(wd, (x, y, base)), (0.33, 0.28, 0.22), var=0.08, ao=0.5, ao_h=1.2, ground=base, namp=0.12, ns=2))
        q = paint(xf(lf, (x, y, base)), LEAF_DK, var=0.12, ao=0.45, ao_h=h, ground=base, top=0.5, namp=0.25, ns=0.9)
        A.add(set_, "MatLeaf_canopy", K.cull_back(q) if set_ == "far" else q)
        A.contact(x, y, 1.8, 0.3)


def scarecrow(A, x, y):
    gz = ground(x, y)
    wood = [xf(K.post(1.7, 0.035, seed=4), (x, y, gz - 0.25)), K.tube([(x - 0.5, y, gz + 1.15), (x + 0.5, y, gz + 1.18)], 0.025, seg=5)]
    shirt = K.strip_mesh([(x - 0.45, y, gz + 1.16), (x, y, gz + 1.18), (x + 0.45, y, gz + 1.16)], [0.42, 0.45, 0.42], up=(0, 1, 0), tears=0.2, seed=3)
    shirt.v[:, 2] -= 0.18
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, ao=0.2, ground=gz) for q in wood])
    A.add("battle", "MatCloth_batik", paint(shirt, (0.55, 0.28, 0.20), ao=0.0, namp=0.15, ns=4))
    A.add("battle", "MatThatch_atap", paint(xf(K.caping(0.22, 0.1), (x, y, gz + 1.48)), STRAW, ao=0.0, top=0.2))


# ---------------------------------------------------------------- far set
def stilt_house(A, x, y, rz, seed):
    rng = random.Random(seed)
    W, D, FH = rng.uniform(4.0, 5.2), rng.uniform(3.2, 3.8), 1.6
    wood = []
    for sx in (-0.45, 0.0, 0.45):
        for sy in (-0.45, 0.45):
            wood.append(xf(K.post(FH + 0.4, 0.09, seed=seed + int(sx * 9 + sy * 5), seg=5), (sx * W, sy * D, SEA_Z - 0.4)))
    wood.append(xf(K.box(W + 0.4, D + 0.4, 0.15, bev=0.03), (0, 0, FH)))
    walls = xf(K.box(W, D, 2.0, bev=0.03), (0, 0, FH + 0.15))
    roof = xf(K.thatch_roof(W, D, 1.5, courses=3, over=0.45, seed=seed, tooth=0.08, cw=0.7), (0, 0, FH + 2.15))
    win = [xf(K.box(0.6, 0.05, 0.7, bev=0.01), (sx, -D / 2 - 0.02, FH + 0.9)) for sx in (-W * 0.25, W * 0.25)]
    wall_col = [(0.52, 0.40, 0.28), (0.46, 0.50, 0.46), (0.58, 0.48, 0.36)][seed % 3]
    A.add("far", "MatWood_timber", [K.cull_back(paint(xf(q, (x, y, 0), (0, 0, rz)), TIMBER_DK, var=0.1, ao=0.4, ao_h=2, ground=SEA_Z)) for q in wood + win])
    A.add("far", "MatWood_timber", K.cull_back(paint(xf(walls, (x, y, 0), (0, 0, rz)), wall_col, var=0.05, ao=0.3, ao_h=3, ground=SEA_Z, namp=0.1, ns=2)))
    A.add("far", "MatWood_timber", K.cull_back(paint(xf(roof, (x, y, 0), (0, 0, rz)), (0.50, 0.40, 0.30), var=0.06, top=0.2, namp=0.15, ns=1.5)))


def jetty(A):
    """Kuala Perlis fishing jetty: plank deck on piles from the shore out into the estuary, T-head shed."""
    yj = 37.0
    x0, x1 = shore(yj) - 1.0, shore(yj) + 15.0
    wood = []
    L = x1 - x0
    n = int(L / 2.6)
    for i in range(n + 1):
        xx = x0 + L * i / n
        for yy in (yj - 1.0, yj + 1.0):
            wood.append(xf(K.post(1.6, 0.11, seed=i * 2 + int(yy), seg=4), (xx, yy, SEA_Z - 0.8)))
    wood.append(xf(K.box(L, 2.3, 0.14, bev=0.03), (x0 + L / 2, yj, 0.75)))
    wood.append(xf(K.box(3.0, 7.0, 0.14, bev=0.03), (x1 + 1.3, yj, 0.75)))
    for yy in (yj - 3.0, yj + 3.0, yj):
        wood.append(xf(K.post(1.6, 0.11, seed=7 + int(yy), seg=5), (x1 + 1.3, yy, SEA_Z - 0.8)))
    shed = [xf(K.box(2.4, 3.2, 1.9, bev=0.03), (x1 + 1.3, yj + 1.5, 0.82))]
    roof = xf(K.thatch_roof(2.4, 3.2, 0.7, courses=2, over=0.3, seed=12, cw=0.6), (x1 + 1.3, yj + 1.5, 2.72), (0, 0, math.pi / 2))
    for k, xx in enumerate((x0 + 3, x0 + 8, x1)):  # lamp posts
        wood.append(xf(K.post(2.0, 0.05, seed=k, seg=5), (xx, yj + 1.05, 0.8)))
    A.add("far", "MatWood_timber", [paint(q, TIMBER, var=0.08, ao=0.4, ao_h=1.5, ground=SEA_Z) for q in wood])
    A.add("far", "MatWood_timber", [paint(q, (0.50, 0.44, 0.36), ao=0.3, ao_h=2, ground=0.8) for q in shed])
    A.add("far", "MatWood_timber", paint(roof, (0.50, 0.36, 0.26), var=0.05, top=0.2, namp=0.2, ns=1))
    boats = [((x0 + 5.0, yj - 2.6), 0.08, (0.22, 0.38, 0.62)), ((x0 + 9.5, yj + 2.7), -0.1, (0.65, 0.22, 0.16)),
             ((x1 - 1.0, yj - 2.9), 0.15, (0.85, 0.82, 0.74)), ((x1 + 4.2, yj + 1.5), 1.45, (0.25, 0.52, 0.36)),
             ((x0 + 2.0, yj + 6.5), 0.5, (0.85, 0.70, 0.25))]
    for k, ((bx, by), rz, col) in enumerate(boats):
        hull = xf(K.perahu(L=random.Random(k).uniform(5.0, 6.5), W=1.15, H=0.62, seed=k), (bx, by, SEA_Z - 0.18), (0, 0, rz))
        A.add("far", "MatWood_timber", K.cull_back(tint(paint(hull, col, var=0.06, ao=0.3, ao_h=0.6, ground=SEA_Z, top=0.1),
                                            lambda v, c: np.where((v[:, 2] > SEA_Z + 0.45)[:, None], c * np.array([1.25, 1.2, 1.15, 1]), c * np.where((v[:, 2] < SEA_Z + 0.12)[:, None], np.array([0.45, 0.42, 0.4, 1]), 1.0)))))


def karsts(A):
    """eroded limestone tower karsts (smooth, vegetated, fluted); the hero massif sits upper-right of the vista,
    behind the jetty. Vista-only: back faces culled. Farther ranges are painted ridge layers (backdrop)."""
    spec = [(17, 70, 27, 9.0, 36, 22), (25.0, 63.5, 15, 6.0, 26, 14), (9.0, 76, 18, 6.5, 26, 14),     # hero massif
            (1.5, 90, 21, 8.0, 28, 15), (-7.5, 96, 14, 6.0, 22, 12),
            (-16, 80, 17, 7.0, 22, 12), (-33, 98, 23, 10.0, 22, 12),   # behind the hub plaque
            (32, 95, 18, 8.0, 26, 14), (49, 112, 15, 9.0, 22, 11), (64, 99, 11, 7.0, 18, 10)]
    for k, (x, y, h, r, seg, rings) in enumerate(spec):
        p = K.smooth_karst(h, r, seed=300 + k, seg=seg, rings=rings, rock=(0.80, 0.78, 0.72), streak=(0.36, 0.36, 0.34),
                           stain=(0.70, 0.54, 0.38), veg=(0.21, 0.33, 0.14), veg2=(0.36, 0.47, 0.19))
        A.add("far", "MatRock_lime", K.cull_back(xf(p, (x, y, 0), (0, 0, k * 0.7))))


def backdrop(A):
    """painted far set (Sky kind, fog-free): karst range + Langkawi-ward shore + high hazy hills + dawn clouds.
    Bottoms sink below the terrain/sea edge, so no world edge or horizon seam shows anywhere in the vista."""
    A.add("far", "MatSky_backdrop", K.ridge_layer(175, az=(-52, 40), base=2.0, amp=19, seed=5, hills=16, ridge=0.35, canopy=0.7,
                                                  top=(0.60, 0.52, 0.50), bottom=(0.82, 0.63, 0.54), cols=80))
    A.add("far", "MatSky_backdrop", K.ridge_layer(265, az=(-52, 40), base=7, amp=20, seed=8, hills=8, ridge=0.1,
                                                  top=(0.75, 0.60, 0.59), bottom=(0.91, 0.65, 0.53), cols=60))
    K.cloud_bank(A, n=5, dist=(300, 430), el=(4.5, 11), seed=11, mat="MatSky_backdrop",
                 top=(1.0, 0.85, 0.74), mid=(0.95, 0.72, 0.63), base=(0.78, 0.59, 0.60))


def tree_belt(A):
    """distant kampung/palm tree line behind the paddy plain: hides the terrain edge in the vista."""
    rng = random.Random(77)
    for k in range(18):
        a = math.radians(rng.uniform(88, 205))
        r = rng.uniform(60, 70)
        x, y = r * math.cos(a), r * math.sin(a)
        if not in_vista(x, y):
            continue
        h = rng.uniform(4, 7)
        b = K.canopy(h * 0.5, seed=500 + k, lumps=4, sub=1, squash=0.8, spread=0.9)
        A.add("far", "MatLeaf_canopy", K.cull_back(paint(xf(b, (x, y, -0.4), s=(1.5, 1.5, 1.0)), (0.22, 0.31, 0.17), var=0.12, ao=0.35, ao_h=h, ground=0, top=0.3)))
    for k in range(9):
        a = math.radians(rng.uniform(95, 190))
        r = rng.uniform(52, 62)
        x, y = r * math.cos(a), r * math.sin(a)
        if not in_vista(x, y):
            continue
        tr, lf = K.coconut_palm(rng.uniform(6, 8), seed=600 + k, fronds=7)
        A.add("far", "MatWood_timber", paint(xf(tr, (x, y, -0.1)), (0.40, 0.34, 0.27), ao=0))
        A.add("far", "MatLeaf_canopy", paint(xf(lf, (x, y, -0.1)), (0.26, 0.36, 0.17), ao=0, top=0.3))


def village(A):
    for k, (x, y, rz) in enumerate(((shore(42) + 1.5, 42.5, 0.15), (shore(47) + 2.5, 47.5, -0.2), (shore(31) + 1.8, 30.5, 0.3))):
        stilt_house(A, x, y, rz, k)
    rng = random.Random(5)
    for k, (dx, y) in enumerate(((-2.0, 33.0), (-3.4, 40.0), (-1.2, 45.5), (-4.0, 49.0), (-1.0, 28.5), (-2.6, 52.5))):
        x = shore(y) + dx
        tr, lf = K.coconut_palm(rng.uniform(6.0, 8.0), seed=700 + k)
        A.add("far", "MatWood_timber", paint(xf(tr, (x, y, ground(x, y) - 0.1)), (0.42, 0.35, 0.27), ao=0.3, ao_h=2, ground=0))
        A.add("far", "MatLeaf_canopy", paint(xf(lf, (x, y, ground(x, y) - 0.1)), (0.27, 0.38, 0.17), var=0.1, ao=0, top=0.35, namp=0.15, ns=1))


# ---------------------------------------------------------------- build
def build(A):
    for name in ("MatGround_bund", "MatMud_bank", "MatWater_paddy", "MatWood_timber", "MatThatch_atap", "MatLeaf_canopy",
                 "MatRock_stone", "MatRock_lime", "MatMetal_iron", "MatCloth_batik", "MatSky_backdrop"):
        A.mat(name)
    A.mat("MatGlow_pelita", emit=(1.0, 0.72, 0.4), estr=4.0)

    # ---- props first (they register contact-darkening pools used by the terrain)
    pondok(A, MOUND[0] + 0.15, MOUND[1] - 0.1, -0.22)
    banana_clump(A, -10.5, 2.7, seed=31)
    sluice_gate(A, GATE_X)
    apron(A)
    litter(A)
    wreck(A)
    puddles(A)
    mangroves(A, [(11.4, -2.4, 3.6), (12.2, 1.2, 4.2), (11.5, 4.9, 4.5), (12.6, 8.4, 3.8), (10.9, 10.2, 3.2), (13.4, 12.0, 4.2),
                  (14.9, 3.2, 4.7), (15.0, 7.0, 4.0)])
    mangroves(A, [(shore(y) + dx, y, h) for (y, dx, h) in ((16, 0.5, 4.2), (21, -0.4, 3.6), (26, 0.8, 4.8),
                                                         (53, 0.5, 4.5), (60, 0.6, 4.4))], set_="far")
    scarecrow(A, -7.0, 10.6)
    # planting line + bundles on the near (camera-side) platform edge: vista foreground, <=1.2 m
    for sx in (-4.6, -0.9):
        A.add("battle", "MatWood_timber", paint(on_ground(K.post(0.95, 0.025, seed=int(sx * 5), seg=5), sx, -6.0, 0.15), TIMBER, ao=0.3, ao_h=0.3, ground=ground(sx, -6.0)))
    A.add("battle", "MatThatch_atap", paint(K.tube(K.arc((-4.6, -6.0, ground(-4.6, -6.0) + 0.72), (-0.9, -6.0, ground(-0.9, -6.0) + 0.72), -0.08, n=8), 0.006, seg=3), (0.55, 0.5, 0.4), ao=0))
    for k, (sx, sy) in enumerate(((-3.2, -6.2), (-2.6, -6.05), (2.6, -6.0))):
        A.add("battle", "MatLeaf_canopy", paint(on_ground(K.seedling_bundle(0.3, seed=20 + k), sx, sy, 0.03), SEEDLING, var=0.08, ao=0.45, ao_h=0.25, ground=ground(sx, sy)))

    # ---- terrain (to r 62) -- after props so contact pools land
    A.terrain(ground, gcolor, kind=gkind, rin=4.5, rout=130.0, split=23.0, cull=gcull, seed=1)

    # ---- paddy grid: bunds, water cells, rice rows
    for x in GX:  # bunds along x = const
        for y0, y1 in zip(GY[:-1], GY[1:]):
            if y0 == 6.6 and x < CH_X1:  # never dam the channel
                continue
            far = math.hypot(x, 0.5 * (y0 + y1)) > 23
            A.add("far" if far else "battle", "MatGround_bund", bund_line(A, [(x, y0), (x, y1)], half=0.42, far=far))
    for y in GY:
        for x0, x1 in zip(GX[:-1], GX[1:]):
            far = math.hypot(0.5 * (x0 + x1), y) > 23
            wide = y in (6.6, 8.2)
            A.add("far" if far else "battle", "MatGround_bund", bund_line(A, [(x0, y), (min(x1, 6.9) if -7.4 < y < 8.2 else x1, y)], half=0.55 if wide else 0.42, far=far))
    rngc = random.Random(9)
    for x0, x1 in zip(GX[:-1], GX[1:]):
        for y0, y1 in zip(GY[:-1], GY[1:]):
            if y0 == 6.6:  # channel row
                continue
            if x0 >= 3.25 and -7.4 <= y0 < 8.2:  # platform + mud bank
                continue
            cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
            if not any(visible(px, py, pad=2) for px in (x0, x1, cx) for py in (y0, y1, cy)) or math.hypot(cx, cy) > 70:
                continue
            if all(land_h(px, py) > WATER_Z for px in (x0, x1) for py in (y0, y1)):
                continue
            key = (x0, y0)
            if key in DRAINED:
                continue
            planted = key not in OPEN
            if math.hypot(cx, cy) > 22:
                inner = WATER_FAR_RICE if planted and rngc.random() < 0.7 else WATER_OPEN
                A.add("far", "MatWater_paddy", water_cell(x0, y0, x1, y1, WATER_Z, inner, WATER_EDGE, inset=0.6))
                continue
            A.add("battle", "MatWater_paddy", water_cell(x0, y0, x1, y1, WATER_Z, WATER_JADE if planted else WATER_OPEN, WATER_EDGE, inset=0.55))
            if planted:  # rice rows (along x), clipped where land rises above the water
                y = y0 + 0.55
                while y < y1 - 0.45:
                    run = None
                    x = x0 + 0.5
                    while x <= x1 - 0.45:
                        ok = land_h(x, y) < WATER_Z - 0.05 and visible(x, y)
                        if ok and run is None:
                            run = x
                        if (not ok or x + 0.5 > x1 - 0.45) and run is not None:
                            if x - run > 0.6:
                                A.scatter_strip("Paddy", 120, (run, y), (x, y), 0.05, lambda a, b: WATER_Z - 0.02, RICE, step=99)
                            run = None
                        x += 0.5
                    y += 0.34
    # channel water: foam (alpha<1) downstream of the gate and at the outlet weir
    for (a0, a1) in ((GX[0], -20.0), (-20.0, GATE_X), (GATE_X, GATE_X + 3.0), (GATE_X + 3.0, CH_X1 - 1.0), (CH_X1 - 1.0, CH_X1)):
        far = a1 <= -20.0
        foam_in = a0 == GATE_X
        foam_out = a1 == CH_X1
        p = water_cell(a0, CH0, a1, CH1, WATER_Z - 0.01, (0.22, 0.30, 0.27), (0.30, 0.31, 0.25), inset=0.25,
                       a_in=0.45 if (foam_in or foam_out) else 1.0, a_edge=0.65 if (foam_in or foam_out) else 1.0)
        if foam_in:  # fade the foam out downstream
            p.c[[1, 2, 5, 6], 3] = 1.0
        if foam_out:
            p.c[[0, 3, 4, 7], 3] = 1.0
        A.add("far" if far else "battle", "MatWater_paddy", p)
    # mud creek from the weir to the estuary (sea level), foam where the outflow lands
    ys = [CREEK_Y - 0.5, CREEK_Y + 0.5]
    xs = np.linspace(CH_X1 - 0.3, shore(CREEK_Y) + 0.3, 6)
    v = [(x, y + 0.12 * math.sin(x * 0.9), SEA_Z + 0.03) for x in xs for y in ys]
    f = [(2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1) for i in range(len(xs) - 1)]
    p = P(v, f)
    p.c = np.array([[0.24, 0.29, 0.26, 0.5 if i < 4 else 1.0] for i in range(len(v))])
    A.add("battle", "MatWater_paddy", p)
    # estuary / sea: battle strip by the mangroves + far sheet to the horizon
    for (ya, yb, set_) in ((-14.0, 22.0, "battle"), (22.0, 140.0, "far")):
        ys = np.arange(ya, yb + 0.01, 2.0 if set_ == "battle" else 6.0)
        v, f = [], []
        for y in ys:
            s = shore(y)
            v += [(s - 0.8, y, SEA_Z), (s + 2.5, y, SEA_Z), (30.0 if set_ == "battle" else 260.0, y, SEA_Z)]
        for i in range(len(ys) - 1):
            a = 3 * i
            f += [(a, a + 1, a + 4, a + 3), (a + 1, a + 2, a + 5, a + 4)]
        p = P(v, f)
        p.c = np.array([list(MUD_WET) + [0.7], list(SEA) + [1.0], list(SEA) + [1.0]] * len(ys))
        A.add(set_, "MatWater_paddy", p)
    p = P([(30.0, -14.0, SEA_Z), (260.0, -14.0, SEA_Z), (260.0, 22.0, SEA_Z), (30.0, 22.0, SEA_Z),
           (shore(140.0) + 2.5, 140.0, SEA_Z), (260.0, 140.0, SEA_Z), (340.0, 330.0, SEA_Z), (120.0, 330.0, SEA_Z)],
          [(0, 1, 2, 3), (4, 5, 6, 7)])
    p.c = np.tile(list(SEA) + [1.0], (8, 1))
    A.add("far", "MatWater_paddy", p)

    # ---- scatter: grass on the platform rim / mound / causeways / mud bank, reeds on channel + creek
    rng = random.Random(3)
    for k in range(70):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.84, 1.03)
        ay = AY_FAR if math.sin(a) > 0 else AY_NEAR
        x, y = AX * d * math.cos(a), ay * d * math.sin(a)
        if math.hypot(x, y) < 5.8 or path_dist(x, y) < 0.6 or not visible(x, y):
            continue
        A.scatter_patch("Grass", 30, x, y, rng.uniform(0.4, 1.0), ground, GRASS_TINT, seed=k)
    for k in range(14):
        a = rng.uniform(0, 2 * math.pi)
        x, y = MOUND[0] + rng.uniform(1.2, 2.2) * math.cos(a), MOUND[1] + rng.uniform(1.2, 2.2) * math.sin(a)
        A.scatter_patch("Grass", 28, x, y, 0.8, ground, GRASS_TINT, seed=50 + k)
    for (a, b, w) in CAUSEWAYS:
        for side in (-1, 1):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            ox, oy = -dy / L * side * (w - 0.2), dx / L * side * (w - 0.2)
            A.scatter_strip("Grass", 30, (a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy), 0.4, ground, GRASS_TINT, step=0.6)
    for x0, x1 in ((-14.0, GATE_X - 1.5), (GATE_X + 1.6, CH_X1 - 1.2)):
        for yy in (CH0 + 0.05, CH1 - 0.05):
            A.scatter_strip("Reed", 10, (x0, yy), (x1, yy), 0.35, lambda a, b: WATER_Z, (0.42, 0.48, 0.22), step=99)
    for k in range(30):
        y = rng.uniform(-6.0, 14.0)
        x = rng.uniform(7.2, shore(y) + 0.5)
        if not is_mud(x, y):
            continue
        A.scatter_patch("Reed", 9, x, y, rng.uniform(0.5, 1.0), lambda a, b: max(ground(a, b), SEA_Z), (0.36, 0.44, 0.22), seed=100 + k)
        if k % 2 == 0:
            A.scatter_patch("Grass", 22, x + 0.6, y - 0.4, 0.7, ground, (0.38, 0.44, 0.22), seed=150 + k)

    # ---- far set
    jetty(A)
    village(A)
    karsts(A)
    tree_belt(A)
    backdrop(A)


if __name__ == "__main__":
    K.main("perlis", build, MOOD)
