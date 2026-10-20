"""Sabah arena -- levelled trail terrace on the flank of Kinabalu, cool montane morning
(design_art.md section c; USER_SPEC: Mount Kinabalu rising above the treeline, villagers preparing a trek).
Ground: moss + compact earth terrace cut into the hillside; the hill rises to the left behind a dry-stone
granite wall and falls away to the right into the valley (slope hazard dir +x).
Apron: walking sticks + siung hat, km trail post + log step + pitcher plants, hinava bowl with limes.
Far band: granite slabs, tree ferns, log steps of the summit trail climbing away up-left.
Left flank: trail hut (sago thatch) on the upper terrace, wakid back-baskets ready for the trek.
Right flank: big lichened granite boulder perched at the drop-off, ferns.
Far set (vista): Kinabalu's jagged granite crown in cloud, layered forested ridges, Kundasang terraces, valley river.

  blender -b --factory-startup -P art_src/arena_sabah.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)
import numpy as np
from arenakit import P, xf, join, paint, tint, nz, smooth01

# Godot ARENA_DEFS["sabah"] recommendation (+ b_* = Blender preview factors only)
MOOD = {"sky_top": (0.16, 0.40, 0.84), "sky_horizon": (0.80, 0.86, 0.90), "fog": (0.74, 0.80, 0.86),
        "fog_density": 0.002, "sun_color": (1.0, 0.92, 0.80), "sun_energy": 1.1,
        "lantern": (1.0, 0.80, 0.52), "lantern_energy": 1.3, "exposure": 0.9, "ambient": 0.5,
        "b_sun": 3.6, "b_world": 1.0, "b_fill": 0.45, "b_lantern": 10.0}

# ---------------------------------------------------------------- palette (sRGB)
EARTH = (0.47, 0.39, 0.30)
EARTH_LT = (0.55, 0.46, 0.35)
HUMUS = (0.33, 0.27, 0.21)
MOSS = (0.36, 0.46, 0.22)
MOSS_DK = (0.24, 0.34, 0.17)
GRANITE = (0.50, 0.50, 0.47)
GRANITE_DK = (0.36, 0.36, 0.34)
LICHEN = (0.64, 0.64, 0.54)
TIMBER = (0.46, 0.34, 0.23)
TIMBER_DK = (0.28, 0.20, 0.14)
SAGO = (0.52, 0.42, 0.28)
BAMBOO = (0.62, 0.56, 0.36)
FERN = (0.30, 0.46, 0.20)
FERN_LT = (0.42, 0.56, 0.24)
FOREST = (0.16, 0.27, 0.16)
GRASS_T = (0.42, 0.52, 0.24)
RATTAN = (0.56, 0.44, 0.27)
RIVER = (0.30, 0.42, 0.42)

# ---------------------------------------------------------------- layout
TERR = 6.1          # levelled terrace radius (cut into the slope)
WALL_R = 6.95       # dry-stone retaining wall arc (left, uphill side)
HUT = (-8.7, 4.6, -0.35)
BOULDER = (9.1, 3.2)
STEPS = [(-4.6, 5.0), (-5.0, 6.4), (-5.5, 7.8), (-6.2, 9.3), (-7.0, 10.8), (-7.9, 12.3), (-8.9, 13.8)]  # summit trail
KIN = (36.0, 220.0)  # Kinabalu summit plateau centre (x, y)


STREAM = [(0.4, 14.5), (3.4, 12.0), (6.6, 10.6), (9.6, 9.0), (12.6, 8.0), (16.0, 6.4), (20.0, 5.2), (24.5, 3.4), (34.0, 0.0), (48.0, -6.0)]
GROUND_PLANE = 22.5   # main.tscn keeps a dark Ground plane at y=-0.5 over +-22 m: stay above it inside that square


def stream_d(x, y):
    return min(seg_dist(x, y, a, b) for a, b in zip(STREAM[:-1], STREAM[1:]))


def slope_h(x, y):
    """hillside falling toward +x (hazard dir): high on the left behind the wall, a fill bank on the right,
    a gentle decline to the plane limit, then the drop into the valley beyond x 22."""
    n = 0.22 * nz(x, y, 0, 0.09, 3) + 0.07 * nz(x, y, 0, 0.4, 4)
    if x <= 0:
        h = -0.15 * x * smooth01(-1.0, -7.5, x) + 0.05 * max(0.0, y) + n
    else:
        h = -0.32 * smooth01(5.5, 8.0, x) - 0.008 * max(0.0, x - 8.0) + 0.02 * y * smooth01(10.0, 0.0, x) + n * 0.6
    h -= 0.22 * (1 - smooth01(0.4, 1.4, stream_d(x, y)))                          # stream bed
    if abs(x) < GROUND_PLANE and abs(y) < GROUND_PLANE:
        return max(h, -0.44)
    edge = GROUND_PLANE + 0.45 * max(0.0, y - 12.0) + 3.0 * nz(x, y, 0, 0.05, 6)   # valley rim recedes diagonally
    drop = 0.28 * max(0.0, x - edge) * smooth01(edge, edge + 10.0, x)
    return max(h - drop, -14.0 + 0.6 * nz(x, y, 0, 0.05, 5))


def ground(x, y):
    r = math.hypot(x, y)
    flat = 0.02 * nz(x, y, 0, 0.9, 7) + 0.01 * nz(x, y, 0, 3.0, 8)
    if x < 0 and slope_h(x, y) > 0.3:  # cut side: hard edge at the wall foot
        w = smooth01(WALL_R - 0.25, WALL_R + 0.3, r)
    else:
        w = smooth01(TERR - 0.1, TERR + 1.2, r)
    return float(flat * (1 - w) + slope_h(x, y) * w)


def seg_dist(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


def in_vista(x, y):
    dx, dy = x + 1.5, y + 12.5
    return dy > 2 and -58 < math.degrees(math.atan2(dx, dy)) < 44


def visible(x, y, pad=0.0):
    return (y > -6.5 - pad and abs(x) < 11 + 0.55 * (y + 6.5) + pad) or in_vista(x, y)


def mix(a, b, t):
    return np.asarray(a, dtype=float) * (1 - t) + np.asarray(b, dtype=float) * t


TRAILS = [[(-4.4, 3.2)] + STEPS, [(4.6, 1.8), (7.0, 1.0), (10.5, -0.6), (14.0, -2.5)], [(0.8, -4.6), (1.2, -7.0), (0.8, -11.0)]]


def path_dist(x, y):
    return min(seg_dist(x, y, a, b) for pl in TRAILS for a, b in zip(pl[:-1], pl[1:]))


def gcolor(x, y, z):
    n1 = nz(x, y, 0, 0.4, 11)
    n2 = nz(x, y, 0, 2.0, 12)
    n3 = nz(x, y, 0, 6.0, 13)
    r = math.hypot(x, y)
    pd = path_dist(x, y)
    moss = np.array(MOSS) * (1 + 0.12 * n1 + 0.08 * n2 + 0.05 * n3)
    moss = mix(moss, MOSS_DK, 0.5 * smooth01(0.0, 0.6, nz(x, y, 0, 0.6, 14)))
    moss = mix(moss, GRASS_T, 0.35 * smooth01(0.1, 0.6, nz(x, y, 0, 0.9, 15)))
    earth = np.array(EARTH) * (1 + 0.08 * n1 + 0.07 * n2 + 0.05 * n3)
    earth = mix(earth, EARTH_LT, 0.4 * smooth01(0.1, 0.6, nz(x, y, 0, 0.7, 16)))
    terrace = 1 - smooth01(TERR - 0.6, TERR + 0.9, r)
    c = mix(moss, earth, max(terrace * (0.75 + 0.25 * smooth01(-0.3, 0.3, n1)), 0.0))
    c = mix(c, np.array(MOSS) * 0.95, 0.45 * terrace * smooth01(0.25, 0.7, nz(x, y, 0, 0.55, 17)) * smooth01(5.4, 6.4, r))
    c = mix(c, np.array(HUMUS) * (1 + 0.1 * n2), 0.7 * (1 - smooth01(0.1, 0.65, pd)))           # trail soil
    c = mix(c, np.array(EARTH) * 0.98, 0.55 * (1 - smooth01(4.6, 5.6, r)))                     # apron
    if z < -3.0:  # valley slopes: forested
        c = mix(c, np.array(FOREST) * (1 + 0.25 * nz(x, y, 0, 0.3, 18)), smooth01(-3.0, -8.0, z))
    return tuple(c)


def gkind(x, y, z):
    return "MatGround_moss"


def gcull(cx, cy, zmax):
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


# ---------------------------------------------------------------- local helpers (kit is frozen)
def face_cam(p, x, y, z, cam=(-1.5, -12.5)):
    rz = math.atan2(x - cam[0], y - cam[1])
    return xf(p, (x, y, z), (0, 0, -rz))


def cloud_card(w, h, seed, n=6, rows=5, cols=40, puff=0.45):
    """flat-backed relief cloud (stage flat), scalloped top, base at z=0, faces -y."""
    rng = random.Random(seed)
    circ = []
    for k in range(n):
        cx = (-0.42 + 0.84 * (k + rng.uniform(0.2, 0.8)) / n) * w
        rr = h * rng.uniform(0.35, 0.62) * (1.25 - abs(cx) / w * 1.3)
        circ.append((cx, rr * rng.uniform(0.3, 0.6), rr))
    v, f = [], []
    for i in range(rows + 1):
        for j in range(cols + 1):
            x = (-0.5 + j / cols) * w
            top = max([cz + math.sqrt(max(0.0, rr * rr - (x - cx) ** 2)) for cx, cz, rr in circ] + [0.0])
            e = abs(x) / (0.5 * w)
            bot = 0.04 * h * e * e
            top = max(top, bot + 0.02 * h)
            t = i / rows
            v.append((x, -puff * h * math.sin(math.pi * t) ** 0.7 * (1 - e ** 2), bot + (top - bot) * t))
    for i in range(rows):
        for j in range(cols):
            a = i * (cols + 1) + j
            f.append((a, a + 1, a + cols + 2, a + cols + 1))
    return P(v, f)


def cloud(A, x, y, z, w, h, seed, top=(1.0, 1.0, 0.98), bot=(0.70, 0.76, 0.86), set_="far"):
    p = face_cam(cloud_card(w, h, seed), x, y, z)
    t = smooth01(z, z + h * 0.8, p.v[:, 2])
    p.c = np.ones((len(p.v), 4))
    p.c[:, :3] = np.asarray(bot)[None, :] * (1 - t[:, None]) + np.asarray(top)[None, :] * t[:, None]
    A.add(set_, "MatSky_cloud", p)   # unshaded + fog-free: colours are final (haze painted in)


def ridge(x0, x1, yc_fn, crest_fn, depth=40.0, foot=-15.0, cols=64, seed=0):
    """forested ridge (layered backdrop): heightfield strip across x; crest_fn(x) -> crest z, yc_fn(x) -> crest y.
    Rows: front foot, front shoulder, crest, back shoulder, back foot. Rounded, smooth-shaded."""
    v, f = [], []
    prof = [(-0.5, 0.0), (-0.22, 0.72), (0.0, 1.0), (0.2, 0.8), (0.5, 0.0)]
    for j in range(cols + 1):
        x = x0 + (x1 - x0) * j / cols
        yc, zc = yc_fn(x), crest_fn(x) + 1.4 * abs(math.sin(x * 0.55 + seed)) + 0.8 * abs(math.sin(x * 1.3 + 2 * seed))
        for (o, k) in prof:
            v.append((x, yc + o * depth, foot + (zc - foot) * (k ** 0.8)))
    m = len(prof)
    for j in range(cols):
        for i in range(m - 1):
            a = j * m + i
            f.append((a, a + m, a + m + 1, a + 1))
    return P(v, f)


def paint_forest(p, base=FOREST, crest=(0.28, 0.40, 0.22), seed=0, farm=None):
    """mottled canopy colour: darker gullies, lighter crowns, sunlit crest; optional farm-terrace stripes."""
    z = p.v[:, 2]
    zt = (z - z.min()) / max(1e-6, z.max() - z.min())
    n = np.array([nz(a, b, c, 0.12, seed) for a, b, c in p.v])
    n2 = np.array([nz(a, b, c, 0.45, seed + 1) for a, b, c in p.v])
    c = np.asarray(base)[None, :] * (0.78 + 0.3 * n[:, None] + 0.22 * n2[:, None])
    c = c * (1 - 0.5 * zt[:, None] ** 2) + np.asarray(crest)[None, :] * 0.5 * zt[:, None] ** 2
    if farm is not None:
        fm = farm(p.v)
        stripe = 0.5 + 0.5 * np.sin(p.v[:, 2] * 2.2)
        farmc = np.where(stripe[:, None] > 0.5, np.array([[0.46, 0.60, 0.30]]), np.array([[0.50, 0.42, 0.30]]))
        c = c * (1 - fm[:, None]) + farmc * fm[:, None]
    p.c = np.ones((len(p.v), 4))
    p.c[:, :3] = np.clip(c, 0, 1)
    return p


def smooth_blob(r, seed=0, seg=16, rings=9, amp=0.1, squash=0.72):
    """smooth canopy lump (lathe sphere + soft noise): no facets at battle scale. Base near z=0."""
    o = seed * 1.37
    prof = [(r * math.sin(math.pi * k / (rings - 1)), -r * squash * math.cos(math.pi * k / (rings - 1))) for k in range(rings)]
    p = K.lathe(prof, seg=seg, cap0=False, cap1=False,
                rfn=lambda a, t: 1.0 + amp * math.sin(a * 3 + o) * math.sin(t * 5 + o) + amp * 0.6 * math.sin(a * 5 - o * 2))
    p.v[:, 2] += r * squash * 0.55
    return p


# ---------------------------------------------------------------- props
def wakid(h=0.75, r=0.24, seg=14):
    """Kadazan-Dusun wakid: tall conical back-basket, wide mouth, rim, straps. Base at z=0."""
    body = K.lathe([(0.0, 0.0), (r * 0.42, 0.0), (r * 0.62, h * 0.35), (r * 0.9, h * 0.8), (r, h), (r * 1.06, h), (r * 1.06, h * 1.03),
                    (r * 0.95, h * 1.02), (r * 0.86, h * 0.8), (r * 0.56, h * 0.35), (r * 0.36, h * 0.04), (0.0, h * 0.04)], seg=seg, cap0=False, cap1=False)
    feet = [xf(K.box(0.04, 0.04, 0.12, bev=0.008), (sx * r * 0.32, sy * r * 0.32, -0.06)) for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1))]
    straps = [K.tube([(sx * r * 0.5, -r * 0.9, h * 0.9), (sx * r * 0.62, -r * 1.25, h * 0.55), (sx * r * 0.45, -r * 0.62, h * 0.18)], 0.016, seg=4) for sx in (-1, 1)]
    return body, join(feet + straps)


def siung(r=0.3, h=0.16):
    """Kadazan siung hat: wide flat cone with a pointed crown. Base (brim) at z=0."""
    return K.lathe([(r, 0.0), (r * 0.96, 0.01), (r * 0.5, h * 0.4), (r * 0.12, h * 0.85), (0.0, h)], seg=20, cap0=True, cap1=False)


def tree_fern(h=3.2, seed=0, fronds=10, lod=0):
    """Cyathea tree fern: shaggy trunk + crown of long arching pinnate fronds. Returns (trunk, leaf)."""
    rng = random.Random(seed)
    lean = (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15))
    path = [(lean[0] * h * t * t, lean[1] * h * t * t, h * t) for t in np.linspace(0, 1, 5)]
    trunk = K.tube(path, [0.16, 0.13, 0.12, 0.11, 0.12], seg=7 if not lod else 5,
                   ) if True else None
    top = np.array(path[-1])
    lv = []
    for k in range(fronds if not lod else 6):
        a = 2 * math.pi * k / fronds + rng.uniform(-0.25, 0.25)
        L = h * rng.uniform(0.62, 0.85)
        up = rng.uniform(0.25, 0.55)
        pts, ws = [], []
        n = 9 if not lod else 5
        for i in range(n):
            t = i / (n - 1)
            pts.append(tuple(top + np.array((L * t * math.cos(a), L * t * math.sin(a), L * (up * t - (up + 0.55) * t * t)))))
            ws.append(0.04 + 0.30 * math.sin(math.pi * min(1.0, t * 1.05)) * (1 - 0.3 * t))
        lv.append(K.strip_mesh(pts, ws, fold=-0.18, tears=0.55, seed=seed * 7 + k))
    for k in range(3 if not lod else 0):  # young fiddleheads
        a = rng.uniform(0, 2 * math.pi)
        lv.append(K.tube([tuple(top), tuple(top + np.array((0.15 * math.cos(a), 0.15 * math.sin(a), 0.35))), tuple(top + np.array((0.22 * math.cos(a), 0.22 * math.sin(a), 0.42)))], [0.03, 0.025, 0.04], seg=4))
    return trunk, join(lv)


def fern_clump(r=0.7, seed=0, n=7):
    """ground fern: arching fronds from a crown at z=0."""
    rng = random.Random(seed)
    lv = []
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.3, 0.3)
        L = r * rng.uniform(0.75, 1.1)
        up = rng.uniform(0.5, 0.9)
        pts = [(L * t * math.cos(a), L * t * math.sin(a), L * (up * t - (up + 0.25) * t * t) + 0.02) for t in np.linspace(0, 1, 6)]
        ws = [0.02 + 0.12 * math.sin(math.pi * min(1.0, t * 1.05)) * r for t in np.linspace(0, 1, 6)]
        lv.append(K.strip_mesh(pts, ws, fold=-0.15, tears=0.6, seed=seed * 5 + k))
    return join(lv)


def pitcher(seed=0):
    """Nepenthes: a few hanging pitchers with lids + strap leaves. Returns (pitchers, leaves). ~0.35 m."""
    rng = random.Random(seed)
    cups, lv = [], []
    for k in range(4):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.4, 0.4)
        d = rng.uniform(0.12, 0.25)
        cx, cy = d * math.cos(a), d * math.sin(a)
        cup = K.lathe([(0.0, 0.0), (0.04, 0.005), (0.055, 0.05), (0.045, 0.1), (0.036, 0.13), (0.045, 0.14), (0.04, 0.145)], seg=9, cap0=True, cap1=False)
        cups.append(xf(cup, (cx, cy, 0.0), (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0)))
        cups.append(xf(K.box(0.07, 0.05, 0.008, bev=0.003), (cx, cy - 0.01, 0.16), (0.6, 0, 0)))
        lv.append(K.strip_mesh([(0, 0, 0.02), (cx * 0.5, cy * 0.5, 0.12), (cx * 1.6, cy * 1.6, 0.08)], [0.01, 0.04, 0.01], seed=k))
    return join(cups), join(lv)


def wall_stones(A):
    """dry-stone granite retaining wall along the uphill (left) arc, two courses + capstones."""
    rng = random.Random(5)
    stones = []
    for course in range(3):
        a = math.radians(108 + course * 4)
        while a < math.radians(248):
            L = rng.uniform(0.55, 0.85)
            ar = L / WALL_R
            am = a + ar / 2
            x, y = WALL_R * math.cos(am), WALL_R * math.sin(am)
            gz = ground(x * 0.97, y * 0.97)
            hgt = 0.36 + 0.06 * rng.random()
            top = slope_h(x * 1.06, y * 1.06)
            if gz + course * 0.36 > top + 0.1:
                a += ar + 0.03
                continue
            st = K.box(L, 0.42, hgt, bev=0.08, seg=2, jitter=0.04, seed=int(a * 100) + course)
            stones.append(xf(st, (x, y, gz - 0.06 + course * 0.37), (0, 0, am + math.pi / 2 + rng.uniform(-0.06, 0.06))))
            a += ar + 0.02
    def mossy(p, i):
        paint(p, GRANITE if i % 3 else GRANITE_DK, var=0.14, ao=0.35, ao_h=0.9, ground=0.0, top=0.15, namp=0.2, ns=3)
        n = K.vnormals(p)
        m = np.clip(smooth01(0.55, 0.9, n[:, 2]) * (0.5 + 0.5 * K.nfield(p.v, 2.0, i)), 0, 1)
        p.c[:, :3] = p.c[:, :3] * (1 - m[:, None]) + np.asarray(MOSS)[None, :] * m[:, None]
        return p
    A.add("battle", "MatRock_granite", [mossy(s, i) for i, s in enumerate(stones)])
    A.contact(-WALL_R, 0.0, 2.0, 0.15)


def trail_hut(A, x, y, rz):
    """open trail shelter on short posts: sago thatch roof, plank floor, benches, wakid baskets, sticks."""
    W, D, FH, EAVE = 3.0, 2.3, 0.4, 1.95
    G = {"MatWood_timber": [], "MatThatch_sago": [], "MatRock_granite": []}
    gz = ground(x, y)
    wood = lambda p, col=TIMBER, **kw: G["MatWood_timber"].append((p, {**dict(rgb=col, var=0.09, ao=0.45, ao_h=1.0, namp=0.12, ns=3, stretch=(1, 1, 0.2)), **kw}))
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            wood(xf(K.post(EAVE + 0.05, 0.075, seed=sx * 3 + sy, seg=7), (sx * W / 2, sy * D / 2, -0.15)))
            G["MatRock_granite"].append((xf(K.rock(0.16, seed=sx * 5 + sy + 20, sub=2, squash=(1, 1, 0.5)), (sx * W / 2, sy * D / 2, -0.06)), dict(rgb=GRANITE, ao=0.4, ao_h=0.15)))
    for sy in (-1, 1):
        wood(xf(K.box(W + 0.3, 0.1, 0.1, bev=0.015), (0, sy * D / 2, FH - 0.1)), TIMBER_DK)
        wood(xf(K.box(W + 0.2, 0.09, 0.09, bev=0.012), (0, sy * D / 2, EAVE - 0.09)), TIMBER_DK)
    for k in range(12):
        wood(xf(K.plank(D + 0.1, 0.24, 0.04, warp=0.008), (-W / 2 + 0.12 + k * 0.252, 0, FH), (0, 0, math.pi / 2)), (0.54, 0.42, 0.28))
    for sx in (-1, 1):
        wood(xf(K.box(0.09, D, 0.09, bev=0.012), (sx * W / 2, 0, EAVE - 0.09)), TIMBER_DK)
    # bamboo half-wall at the back (+y) and a bench along it
    for k in range(20):
        wood(xf(K.post(0.75, 0.035, seed=k, seg=5, lean=0.0), (-W / 2 + 0.08 + k * 0.15, D / 2 - 0.05, FH)), BAMBOO)
    wood(xf(K.box(W - 0.3, 0.35, 0.05, bev=0.01), (0, D / 2 - 0.35, FH + 0.4)), (0.56, 0.44, 0.30))
    roof = K.thatch_roof(W, D, 1.0, courses=6, over=0.42, seed=8, tooth=0.08, cw=0.16)
    course = lambda v, c: c * (0.82 + 0.22 * (np.floor((v[:, 2] - EAVE - gz) * 6.0 / 1.0 + 0.5) % 2))[:, None]
    G["MatThatch_sago"].append((xf(roof, (0, 0, EAVE)), "roof"))
    for mat, lst in G.items():
        for (p, kw) in lst:
            q = xf(p, (x, y, gz), (0, 0, rz))
            if kw == "roof":
                q = tint(paint(q, SAGO, var=0.04, ao=0.0, top=0.3, namp=0.25, ns=3, stretch=(6, 6, 0.4)), course)
            A.add("battle", mat, q if not isinstance(kw, dict) else paint(q, ground=gz, **kw))
    # trek gear on the floor + by the steps: wakid baskets, siung hats, sticks, a rolled mat
    for k, (dx, dy, rr) in enumerate(((0.6, -0.4, 0.3), (1.0, 0.1, 1.2), (1.75, -1.55, 0.8))):
        body, extra = wakid(0.72 if k < 2 else 0.8)
        zz = FH + 0.02 if k < 2 else 0.0
        b = xf(xf(body, (dx, dy, zz), (0, 0, rr)), (x, y, gz), (0, 0, rz))
        A.add("battle", "MatThatch_sago", tint(paint(b, RATTAN, var=0.05, ao=0.35, ao_h=0.5, ground=gz + zz, top=0.2),
                                               lambda v, c: c * (0.84 + 0.16 * ((np.floor(v[:, 2] * 26) + np.floor(np.arctan2(v[:, 1] - y, v[:, 0] - x) * 9)) % 2))[:, None]))
        A.add("battle", "MatWood_timber", paint(xf(xf(extra, (dx, dy, zz), (0, 0, rr)), (x, y, gz), (0, 0, rz)), TIMBER_DK, ao=0.2, ground=gz))
    for k in range(4):
        a = 0.1 + 0.08 * k
        A.add("battle", "MatWood_timber", paint(K.tube([xf(P([(W / 2 + 0.15, -0.3 + 0.12 * k, 0.0)], []), (x, y, gz), (0, 0, rz)).v[0].tolist(),
                                                         xf(P([(W / 2 + 0.05, -0.25 + 0.12 * k, 1.35)], []), (x, y, gz), (0, 0, rz)).v[0].tolist()], 0.022, seg=5), (0.50, 0.38, 0.24), ao=0.2, ao_h=0.5, ground=gz))
    A.add("battle", "MatThatch_sago", paint(xf(xf(siung(), (0.2, 0.5, FH + 0.02), (0.0, 0, 0)), (x, y, gz), (0, 0, rz)), (0.66, 0.54, 0.34), ao=0.0, top=0.2))
    A.contact(x, y, 2.4, 0.28)


def boulder(A, x, y, r=1.6, seed=0, sub=3, squash=(1.25, 1.0, 0.82), sink=0.35, set_="battle"):
    """smooth granite boulder: rounded, lichened, moss on the upper faces, dark rain streaks."""
    p = K.rock(r, seed=seed, sub=sub, amp=0.2, freq=1.1, squash=squash, flat=0.35)
    gz = ground(x, y)
    p = xf(p, (x, y, gz - sink * r))
    n = K.vnormals(p)
    zt = (p.v[:, 2] - p.v[:, 2].min()) / max(1e-6, np.ptp(p.v[:, 2]))
    streak = 0.5 + 0.5 * K.nfield(p.v, 0.9, seed, stretch=(1, 1, 0.12))
    spots = smooth01(0.35, 0.7, K.nfield(p.v, 2.6, seed + 3))
    c = np.asarray(GRANITE)[None, :] * (1 - 0.35 * streak[:, None] * (1 - zt[:, None]))
    c = c * (1 - 0.5 * spots[:, None]) + np.asarray(LICHEN)[None, :] * 0.5 * spots[:, None]
    moss = np.clip(smooth01(0.6, 0.95, n[:, 2]) * smooth01(-0.1, 0.5, K.nfield(p.v, 1.1, seed + 7)), 0, 1)
    c = c * (1 - moss[:, None]) + np.asarray(MOSS)[None, :] * moss[:, None]
    c *= (0.62 + 0.38 * smooth01(0.0, 0.3, zt))[:, None]
    p.c = np.ones((len(p.v), 4))
    p.c[:, :3] = np.clip(c, 0, 1)
    A.add(set_, "MatRock_granite", p)
    if set_ == "battle":
        A.contact(x, y, r * 1.5, 0.3)


def slab(A, x, y, r, seed, rz=0.0):
    """flat granite outcrop slab breaking through the moss."""
    p = K.rock(r, seed=seed, sub=2, amp=0.2, freq=1.0, squash=(1.3, 0.9, 0.22), flat=0.1)
    gz = ground(x, y)
    p = xf(p, (x, y, gz - 0.08), (0, 0, rz))
    paint(p, GRANITE, var=0.08, ao=0.4, ao_h=0.12, ground=gz, top=0.25, namp=0.18, ns=2.2)
    tint(p, lambda v, c: c * (1 - 0.25 * smooth01(0.3, 0.7, K.nfield(v, 3.0, seed)))[:, None])
    A.add("battle", "MatRock_granite", p)
    A.contact(x, y, r * 1.4, 0.2)


def log_step(A, x, y, rz, L=1.1):
    gz = ground(x, y)
    A.add("battle", "MatWood_timber", paint(xf(K.tube([(-L / 2, 0, 0.07), (L / 2, 0, 0.07)], 0.085, seg=7), (x, y, gz - 0.02), (0, 0, rz)), (0.40, 0.30, 0.21), var=0.1, ao=0.4, ao_h=0.15, ground=gz, namp=0.15, ns=4))
    for s in (-1, 1):
        A.add("battle", "MatWood_timber", paint(xf(K.post(0.24, 0.03, seed=int(x * 9), seg=5, lean=0.0), (x + s * (L / 2 + 0.05) * math.cos(rz), y + s * (L / 2 + 0.05) * math.sin(rz), gz - 0.06)), TIMBER_DK, ao=0.2, ground=gz))


def km_post(A, x, y, rz, h=0.55):
    """trail km marker: squat timber post with a white-painted plate."""
    gz = ground(x, y)
    A.add("battle", "MatWood_timber", paint(xf(K.box(0.14, 0.14, h, bev=0.02), (x, y, gz - 0.04), (0, 0, rz)), TIMBER, ao=0.35, ao_h=0.3, ground=gz, top=0.1))
    A.add("battle", "MatWood_timber", paint(xf(K.box(0.2, 0.025, 0.16, bev=0.006), (x, y, gz + h - 0.26), (0, 0, rz)), (0.86, 0.84, 0.76), ao=0.0, top=0.0))
    A.add("battle", "MatWood_timber", paint(xf(K.box(0.12, 0.03, 0.04, bev=0.004), (x, y, gz + h - 0.2), (0, 0, rz)), (0.62, 0.14, 0.10), ao=0.0, top=0.0))
    A.contact(x, y, 0.35, 0.25)


KM4 = ("X.X.X...X...X.X", "XX..XX.XX...X.X", "X...X.X.X...XXX", "XX..X...X.....X", "X.X.X...X.....X")   # 'KM 4' pixel font


def trail_marker(A, x, y, rz):
    """carved Kadazan-Dusun trail marker (~1.4 m): ironwood post with notched bands, a carved head with a flat face,
    arms folded across the chest, painted red/white/black."""
    gz = ground(x, y)
    post = K.lathe([(0.13, 0.0), (0.12, 0.5), (0.14, 0.53), (0.11, 0.56), (0.11, 0.75), (0.14, 0.78), (0.12, 0.81), (0.12, 1.05),
                    (0.09, 1.08), (0.0, 1.08)], seg=10)
    bands = lambda v, c: np.where((((v[:, 2] - gz) > 0.5) & ((v[:, 2] - gz) < 0.82) & ((v[:, 2] - gz) % 0.1 < 0.035))[:, None],
                                  np.array([[0.62, 0.12, 0.08, 1]]), c)
    A.add("battle", "MatWood_timber", tint(paint(xf(post, (x, y, gz - 0.05)), TIMBER_DK, ao=0.35, ao_h=0.4, ground=gz, namp=0.15, ns=6), bands))
    head = smooth_blob(0.16, seed=7, seg=10, rings=7, amp=0.04, squash=1.15)
    face = [xf(K.box(0.2, 0.03, 0.2, bev=0.01), (0, -0.14, 0.1)), xf(K.box(0.05, 0.03, 0.03, bev=0.006), (-0.05, -0.16, 0.22)),
            xf(K.box(0.05, 0.03, 0.03, bev=0.006), (0.05, -0.16, 0.22)), xf(K.box(0.1, 0.03, 0.02, bev=0.004), (0, -0.16, 0.12))]
    arms = [K.tube([(sx * 0.13, -0.02, 0.0), (sx * 0.08, -0.13, -0.12), (-sx * 0.05, -0.14, -0.2)], 0.03, seg=5) for sx in (-1, 1)]
    for p, col in ((head, (0.30, 0.22, 0.15)), (face[0], (0.86, 0.84, 0.76)), (join(face[1:]), (0.08, 0.07, 0.06)), (join(arms), (0.30, 0.22, 0.15))):
        A.add("battle", "MatWood_timber", paint(xf(xf(p, (0, 0, 0), (0, 0, rz)), (x, y, gz + 1.08)), col, ao=0.0, top=0.2))
    A.contact(x, y, 0.45, 0.3)


def km_board(A, x, y, rz):
    """'KM 4' trail sign: brown board on two posts, cream pixel lettering, facing -y before rz."""
    gz = ground(x, y)
    pieces = [xf(K.box(0.09, 0.09, 1.2, bev=0.01), (sx * 0.4, 0.05, -0.1)) for sx in (-1, 1)]
    A.add("battle", "MatWood_timber", paint(xf(join(pieces), (x, y, gz), (0, 0, rz)), TIMBER_DK, ao=0.35, ao_h=0.4, ground=gz))
    A.add("battle", "MatWood_timber", paint(xf(K.box(1.0, 0.04, 0.42, bev=0.012), (x, y, gz + 0.66), (0, 0, rz)), (0.32, 0.21, 0.12), ao=0.0, top=0.1))
    px, quads = 0.058, []
    for r, row in enumerate(KM4):
        for c, ch in enumerate(row):
            if ch == "X":
                u, w = (c - (len(row) - 1) / 2) * px, 0.66 + 0.21 + (2 - r) * px
                quads.append(P([(u - px / 2, -0.025, w - px / 2), (u + px / 2, -0.025, w - px / 2), (u + px / 2, -0.025, w + px / 2), (u - px / 2, -0.025, w + px / 2)], [(0, 1, 2, 3)]))
    A.add("battle", "MatWood_timber", paint(xf(join(quads), (x, y, gz), (0, 0, rz)), (0.94, 0.84, 0.50), ao=0.0, top=0.0))
    A.contact(x, y, 0.5, 0.25)


def wakid_cluster(A, x, y):
    """three wakid back-baskets set down by the trail, one tipped over."""
    for k, (dx, dy, h, tip) in enumerate(((0.0, 0.0, 0.72, 0.0), (0.5, 0.35, 0.62, 0.0), (0.45, -0.4, 0.66, 1.35))):
        gz = ground(x + dx, y + dy)
        body, rest = wakid(h, 0.22)
        rot = (tip, 0, 0.6 * k)
        z = gz + (0.2 if tip else 0.0)
        A.add("battle", "MatThatch_sago", paint(xf(body, (x + dx, y + dy, z), rot), RATTAN, ao=0.3, ao_h=0.3, ground=gz, namp=0.2, ns=12))
        A.add("battle", "MatThatch_sago", paint(xf(rest, (x + dx, y + dy, z), rot), (0.40, 0.30, 0.18), ao=0.0))
    A.contact(x + 0.3, y, 0.9, 0.3)


def ferns_at(A, x, y, r, seed, set_="battle"):
    gz = ground(x, y)
    A.add(set_, "MatLeaf_fern", paint(xf(fern_clump(r, seed=seed), (x, y, gz), (0, 0, seed * 0.7)), FERN if seed % 2 else FERN_LT, var=0.1, ao=0.45, ao_h=r * 0.5, ground=gz, top=0.3, namp=0.12, ns=3))


def tfern(A, x, y, h, seed, set_="battle", lod=0):
    tr, lf = tree_fern(h, seed=seed, lod=lod)
    gz = ground(x, y)
    A.add(set_, "MatWood_timber", paint(xf(tr, (x, y, gz - 0.1)), (0.24, 0.18, 0.13), var=0.1, ao=0.3, ao_h=1.0, ground=gz, namp=0.3, ns=6))
    A.add(set_, "MatLeaf_fern", paint(xf(lf, (x, y, gz - 0.1)), FERN, var=0.1, ao=0.25, ao_h=h, ground=gz + h * 0.6, top=0.35, namp=0.15, ns=2))
    if set_ == "battle":
        A.contact(x, y, 1.2, 0.2)


def mossy_tree(A, x, y, h, seed, set_="battle"):
    """montane tree: crooked mossy trunk + clumped dark canopy."""
    rng = random.Random(seed)
    gz = ground(x, y)
    pts = [(0, 0, -0.2), (0.3 * rng.uniform(-1, 1), 0.2, h * 0.35), (0.5 * rng.uniform(-1, 1), 0.3 * rng.uniform(-1, 1), h * 0.65)]
    wood = [K.tube(pts, [0.28, 0.2, 0.14], seg=8)]
    leaf = []
    top = np.array(pts[-1])
    for k in range(4):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.4, 0.4)
        c = top + np.array((math.cos(a) * h * 0.18, math.sin(a) * h * 0.18, rng.uniform(-0.1, 0.25) * h))
        wood.append(K.tube([tuple(top - np.array((0, 0, h * 0.1))), tuple(c)], [0.1, 0.05], seg=5))
        leaf.append(xf(smooth_blob(h * rng.uniform(0.17, 0.23), seed=seed * 9 + k), tuple(c)))
    A.add(set_, "MatWood_timber", paint(xf(join(wood), (x, y, gz)), (0.30, 0.30, 0.22), var=0.1, ao=0.4, ao_h=2.0, ground=gz, namp=0.35, ns=2.5))
    A.add(set_, "MatLeaf_fern", paint(xf(join(leaf), (x, y, gz)), (0.20, 0.32, 0.17), var=0.12, ao=0.35, ao_h=h, ground=gz + h * 0.4, top=0.4, namp=0.2, ns=1.0))
    if set_ == "battle":
        A.contact(x, y, 1.8, 0.25)


def rhodo(A, x, y, r, seed):
    """rhododendron shrub with red flower clusters (the one warm accent, kept off the apron)."""
    gz = ground(x, y)
    b = K.canopy(r, seed=seed, lumps=3, sub=2, squash=0.65, spread=0.7)
    A.add("battle", "MatLeaf_fern", paint(xf(b, (x, y, gz)), (0.22, 0.36, 0.18), var=0.1, ao=0.4, ao_h=r * 1.5, ground=gz, top=0.35, namp=0.2, ns=2))
    rng = random.Random(seed)
    fl = []
    for k in range(9):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.3, 0.9) * r
        fl.append(xf(K.rock(0.07, seed=k + seed, sub=1, squash=(1, 1, 0.8)), (x + d * math.cos(a), y + d * math.sin(a), gz + r * rng.uniform(0.75, 1.05))))
    A.add("battle", "MatCloth_dye", paint(join(fl), (0.80, 0.18, 0.16), var=0.1, ao=0.0, top=0.2))


def stream(A):
    """mountain stream tumbling down to the right (downhill = hazard dir): ribbon on the carved bed,
    foam (alpha < 1) at the steps, wet rocks."""
    pts = []
    src = STREAM[:7] + [(23.2, 4.4)]   # ends at the lip of the valley drop
    for (x0, y0), (x1, y1) in zip(src[:-1], src[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        for t in np.linspace(0, 1, max(2, int(L / 0.8)), endpoint=False):
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    pts.append(src[-1])
    v, f, c = [], [], []
    prev = None
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty)
        nx_, ny_ = -ty / l, tx / l
        w = 0.55 + 0.15 * math.sin(i * 1.3)
        z = ground(x, y) + 0.1
        if abs(x) < GROUND_PLANE and abs(y) < GROUND_PLANE:
            z = max(z, -0.38)
        drop = 0.0 if prev is None else max(0.0, prev - z)
        prev = z
        foam = min(1.0, drop * 6.0)
        v += [(x - nx_ * w, y - ny_ * w, z), (x, y, z - 0.01), (x + nx_ * w, y + ny_ * w, z)]
        c += [[*RIVER, 0.55], [*RIVER, 1.0 - 0.7 * foam], [*RIVER, 0.55]]
    for i in range(len(pts) - 1):
        a = 3 * i
        f += [(a, a + 3, a + 4, a + 1), (a + 1, a + 4, a + 5, a + 2)]
    p = P(v, f, c)
    p.f = [q for q in p.f if visible(*p.v[list(q)].mean(axis=0)[:2], pad=4.0)]
    A.add("battle", "MatWater_stream", p)
    rng = random.Random(9)
    for k, (x, y) in enumerate(pts[2:-6:3]):
        if not visible(x, y):
            continue
        ox, oy = rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6)
        boulder(A, x + ox, y + oy, r=rng.uniform(0.18, 0.35), seed=400 + k, sub=2, squash=(1.2, 1.0, 0.7), sink=0.4)
    for k, (x, y) in enumerate(pts[1:-5:2]):
        if visible(x, y):
            A.scatter_patch("Reed", 9, x + rng.uniform(-1, 1), y + rng.uniform(-1, 1), 0.6, ground, (0.46, 0.52, 0.28), seed=500 + k)


# ---------------------------------------------------------------- far set
def kinabalu(A):
    """Kinabalu: broad forested massif, sheer granite walls, a wide summit plateau crowned by jagged spires
    (South Peak, Donkey's Ears, Low's Peak, St John's, Ugly Sister). Dense grid only around the crown."""
    cx, cy = KIN
    spires = [(-40, 0, 10, 3.2), (-31, -3, 18, 3.0), (-24, 3, 9, 4.0), (-15, -2, 13, 2.4), (-11, -2, 14, 2.2), (-3, 0, 10, 4.5),
              (6, -3, 19, 3.6), (13, 0, 12, 3.0), (20, -2, 16, 3.0), (27, 2, 11, 3.6), (34, -1, 14, 2.6), (42, 1, 8, 4.0)]

    def H(x, y):
        massif = 50.0 * math.exp(-(x * x / (2 * 85.0 ** 2) + y * y / (2 * 55.0 ** 2)))
        sx = smooth01(52.0, 40.0, abs(x))
        sy = smooth01(20.0, 9.0, abs(y + 2.0))
        plateau = 54.0 * sx * sy - 54.0 * (1 - sx * sy) * 0.0
        h = max(massif + 6.0 * nz(x, y, 0, 0.04, 21) + 2.5 * nz(x, y, 0, 0.12, 22), plateau + 3.0 * nz(x, y, 0, 0.1, 23) if sx * sy > 0.02 else -99)
        if sx * sy > 0.3:
            for (px, py, a, w) in spires:
                h = max(h, plateau + a * math.exp(-((x - px) ** 2 + ((y - py) * 0.7) ** 2) / (2 * w * w)) * (1 + 0.15 * nz(x, y, 0, 0.5, 24)))
        # gullies down the walls
        h -= 2.5 * smooth01(0.4, 0.9, nz(x * 0.6, y * 0.2, 0, 0.15, 25)) * smooth01(30.0, 45.0, h)
        return h - 4.0

    xs = np.concatenate([np.linspace(-200, -56, 12, endpoint=False), np.linspace(-56, 56, 64, endpoint=False), np.linspace(56, 200, 12)])
    ys = np.concatenate([np.linspace(-140, -24, 10, endpoint=False), np.linspace(-24, 22, 24, endpoint=False), np.linspace(22, 90, 5)])
    v, f = [], []
    for y in ys:
        for x in xs:
            v.append((cx + x, cy + y, H(x, y)))
    nx_ = len(xs)
    for j in range(len(ys) - 1):
        for i in range(nx_ - 1):
            a = j * nx_ + i
            f.append((a, a + 1, a + nx_ + 1, a + nx_))
    p = P(v, f)
    nrm = K.vnormals(p)
    z = p.v[:, 2]
    rock = smooth01(26.0, 40.0, z) * 0.6 + smooth01(0.35, 0.75, 1 - nrm[:, 2]) * smooth01(14.0, 30.0, z)
    rock = np.clip(rock, 0, 1)
    streak = 0.5 + 0.5 * K.nfield(p.v, 0.12, 31, stretch=(1, 1, 0.15))
    g = np.asarray((0.38, 0.40, 0.44))[None, :] * (0.75 + 0.35 * streak[:, None])
    fo = np.asarray((0.12, 0.21, 0.13))[None, :] * (0.85 + 0.3 * K.nfield(p.v, 0.08, 32)[:, None])
    scrub = np.asarray((0.26, 0.32, 0.22))[None, :]
    c = fo * (1 - smooth01(20.0, 32.0, z)[:, None]) + scrub * smooth01(20.0, 32.0, z)[:, None]
    c = c * (1 - rock[:, None]) + g * rock[:, None]
    p.c = np.ones((len(p.v), 4))
    p.c[:, :3] = np.clip(c, 0, 1)
    A.add("far", "MatRock_granite", p)


def ridges(A):
    """layered forested ridges between the valley and Kinabalu; the nearest carries Kundasang farm terraces."""
    specs = [  # (y crest fn, crest fn, depth, seed, colours, farm)
        (lambda x: 92 + 10 * math.sin(x * 0.03), lambda x: 6 + 7 * math.sin(x * 0.045 + 1) + 4 * nz(x, 0, 0, 0.08, 41) + 3 * smooth01(-20, 60, x), 50.0, 1,
         (0.18, 0.30, 0.17), (0.30, 0.42, 0.24), False),
        (lambda x: 138 + 12 * math.sin(x * 0.02 + 2), lambda x: 12 + 8 * math.sin(x * 0.03 + 2.4) + 5 * nz(x, 0, 0, 0.06, 42), 50.0, 2,
         (0.18, 0.28, 0.20), (0.28, 0.38, 0.28), False),
        (lambda x: 182 + 10 * math.sin(x * 0.02 + 4), lambda x: 19 + 9 * math.sin(x * 0.025 + 0.6) + 5 * nz(x, 0, 0, 0.05, 43), 50.0, 3,
         (0.22, 0.30, 0.26), (0.32, 0.40, 0.34), False),
    ]
    for (ycf, crf, dep, seed, base, crest, farm) in specs:
        p = ridge(-260, 300, ycf, crf, depth=dep, foot=-16.0, cols=150 if seed == 1 else 110, seed=seed)
        fm = (lambda v: np.clip(smooth01(15.0, 35.0, v[:, 0]) * smooth01(90.0, 30.0, v[:, 0]) * smooth01(-4.0, 2.0, v[:, 2]) *
                            (v[:, 1] < 92 + 10 * np.sin(v[:, 0] * 0.03) + 1), 0, 1)) if farm else None
        A.add("far", "MatLeaf_fern", paint_forest(p, base=base, crest=crest, seed=seed * 10, farm=fm))
    # Kundasang farm houses: white walls, bright roofs on the near ridge
    rng = random.Random(4)
    ycf, crf, dep = specs[0][0], specs[0][1], specs[0][2]
    for k, (x, dx) in enumerate(((28, -7), (38, -5), (47, -8), (58, -4), (33, -10))):
        y = ycf(x) + dx
        t = (y - ycf(x)) / dep  # same profile as ridge(): foot -> shoulder -> crest
        kk = np.interp(t, [-0.5, -0.22, 0.0], [0.0, 0.72, 1.0])
        z = -16.0 + (crf(x) + 1.4 * abs(math.sin(x * 0.55 + 1)) + 0.8 * abs(math.sin(x * 1.3 + 2)) + 16.0) * kk ** 0.8 - 0.6
        rz = rng.uniform(-0.3, 0.3)
        zb = z - 2.6   # sunk into the slope on a dark plinth, so the houses sit in the farmland instead of floating
        A.add("far", "MatWood_timber", paint(xf(K.box(3.0, 2.3, 1.6, bev=0.04), (x, y, zb - 1.5), (0, 0, rz)), (0.22, 0.20, 0.16), ao=0.0, top=0.1))
        A.add("far", "MatWood_timber", paint(xf(K.box(2.8, 2.1, 2.1, bev=0.04), (x, y, zb), (0, 0, rz)), (0.66, 0.64, 0.58), ao=0.3, ao_h=1.4, ground=zb))
        roof = K.thatch_roof(2.8, 2.1, 0.8, courses=1, over=0.2, seed=k, tooth=0.0, cw=1.4)
        A.add("far", "MatWood_timber", paint(xf(roof, (x, y, zb + 2.1), (0, 0, rz)), [(0.70, 0.16, 0.12), (0.16, 0.34, 0.62), (0.20, 0.46, 0.34)][k % 3], ao=0.0, top=0.2))


def valley(A):
    """river winding along the valley floor below the drop-off."""
    pts = [(14.0, -60.0), (26.0, -20.0), (30.0, 10.0), (24.0, 40.0), (34.0, 70.0), (60.0, 100.0), (90.0, 130.0)]
    v, f = [], []
    path = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 6, endpoint=False):
            path.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    path.append(pts[-1])
    for i, (x, y) in enumerate(path):
        a = path[max(0, i - 1)]
        b = path[min(len(path) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty)
        nx_, ny_ = -ty / l, tx / l
        w = 2.2 + 0.8 * math.sin(i * 0.7)
        z = -13.6
        v += [(x - nx_ * w, y - ny_ * w, z), (x + nx_ * w, y + ny_ * w, z)]
    for i in range(len(path) - 1):
        f.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    p = P(v, f)
    p.c = np.array([[*RIVER, 0.75 if i % 2 == 0 else 1.0] for i in range(len(v))])
    A.add("far", "MatWater_stream", p)


def far_forest(A):
    """montane forest flats on the hillside above the hut and along the valley rim (vista depth)."""
    rng = random.Random(17)
    for k in range(26):
        x = rng.uniform(-70, 60)
        y = rng.uniform(26, 70)
        b = math.degrees(math.atan2(x + 1.5, y + 12.5))
        if not in_vista(x, y) or -4.0 < b < 26.0:  # keep the corridor to Kinabalu open
            continue
        h = rng.uniform(8, 14)
        gz = ground(x, y)
        circ = [(rng.uniform(-0.25, 0.25) * h, h * (0.45 + 0.4 * t), h * (0.32 - 0.12 * t) * rng.uniform(0.8, 1.2)) for t in (0.0, 0.33, 0.66, 1.0)]
        card = lobed_card(circ, cols=12, rows=3, puff=0.25)
        z = card.v[:, 2]
        kk = 0.7 + 0.45 * smooth01(z.min(), z.max(), z)
        card.c = np.ones((len(card.v), 4))
        card.c[:, :3] = np.asarray((0.17, 0.28, 0.16))[None, :] * kk[:, None] * rng.uniform(0.85, 1.15)
        A.add("far", "MatLeaf_fern", face_cam(card, x, y, gz - 0.3))
        A.add("far", "MatWood_timber", paint(K.tube([(x, y, gz - 0.3), (x, y, gz + h * 0.5)], 0.25, seg=4, cap=False), (0.26, 0.24, 0.20), ao=0.0))


def lobed_card(circles, cols=14, rows=3, puff=0.3, flat_base=0.6):
    """stage-flat silhouette from overlapping circles (cx, cz, r) in local XZ, facing -y."""
    x0 = min(cx - r for cx, cz, r in circles)
    x1 = max(cx + r for cx, cz, r in circles)
    v, f = [], []
    last = None
    for j in range(cols + 1):
        x = x0 + (x1 - x0) * (0.02 + 0.96 * j / cols)
        tops, bots = [], []
        for cx, cz, r in circles:
            if abs(x - cx) < r:
                d = math.sqrt(r * r - (x - cx) ** 2)
                tops.append(cz + d)
                bots.append(cz - d * flat_base)
        top, bot = (max(tops), min(bots)) if tops else last
        last = (top, bot)
        e = abs(2 * (x - x0) / (x1 - x0) - 1)
        for i in range(rows + 1):
            t = i / rows
            z = bot + (top - bot) * t
            v.append((x, -puff * (top - bot) * math.sin(math.pi * (0.2 + 0.8 * t)) * (1 - e * e), z))
    for j in range(cols):
        for i in range(rows):
            a_ = j * (rows + 1) + i
            f.append((a_, a_ + rows + 1, a_ + rows + 2, a_ + 1))
    return P(v, f)


def skies(A):
    """cloud bank wrapping Kinabalu's waist + scattered cumulus at two depths."""
    cx, cy = KIN
    for k, (dx, dz, w, h) in enumerate(((-75, 14, 90, 13), (-15, 17, 80, 11), (55, 13, 100, 13), (115, 16, 70, 11))):
        cloud(A, cx + dx, cy - 70, dz, w, h, seed=k, top=(0.97, 0.98, 0.99), bot=(0.74, 0.80, 0.86))
    for k, (x, y, z, w, h) in enumerate(((-90, 300, 60, 90, 22), (-30, 340, 80, 120, 26), (150, 330, 72, 90, 22), (-160, 260, 44, 70, 16),
                                         (190, 260, 40, 70, 16), (100, 180, 44, 50, 12))):
        cloud(A, x, y, z, w, h, seed=10 + k)


# ---------------------------------------------------------------- build
def build(A):
    for name in ("MatGround_moss", "MatRock_granite", "MatWood_timber", "MatThatch_sago", "MatLeaf_fern", "MatCloth_dye", "MatWater_stream",
                 "MatSky_cloud"):
        A.mat(name)

    # ---- props
    wall_stones(A)
    trail_hut(A, *HUT)
    boulder(A, BOULDER[0], BOULDER[1], r=1.6, seed=3, squash=(1.2, 1.0, 1.0), sink=0.3)
    boulder(A, BOULDER[0] + 1.6, BOULDER[1] - 1.9, r=0.8, seed=4, sub=3)
    boulder(A, BOULDER[0] - 0.9, BOULDER[1] + 2.3, r=0.6, seed=5, sub=2)
    for (x, y, r, s) in ((2.6, 7.8, 1.1, 11), (-1.8, 8.4, 0.9, 12), (6.2, 6.8, 0.8, 13), (-3.6, -5.6, 0.7, 14), (7.4, -3.6, 0.9, 15)):
        slab(A, x, y, r, s, rz=s * 0.7)
    for k, (x, y) in enumerate(STEPS):
        nx_, ny_ = (STEPS[min(k + 1, len(STEPS) - 1)][0] - x), (STEPS[min(k + 1, len(STEPS) - 1)][1] - y)
        log_step(A, x, y, math.atan2(ny_, nx_) + math.pi / 2)
    km_post(A, -4.9, 4.6, 0.6)
    km_post(A, 5.7, 1.5, -0.3)
    # right flank: carved trail marker, 'KM 4' board and wakid baskets set down by the summit trail
    trail_marker(A, 7.3, 0.1, -0.4)
    km_board(A, 9.4, 0.2, -0.47)
    wakid_cluster(A, 8.2, 1.15)
    tfern(A, -5.4, 8.6, 2.9, seed=1)
    tfern(A, 4.8, 9.6, 3.4, seed=2)
    tfern(A, 11.6, 6.4, 3.6, seed=3)
    tfern(A, -12.4, -2.4, 3.2, seed=4)
    mossy_tree(A, -13.6, 4.6, 7.5, seed=5)
    mossy_tree(A, -9.4, 12.6, 8.0, seed=6)
    rhodo(A, 7.7, 7.4, 0.8, seed=7)
    rhodo(A, -7.6, -3.6, 0.7, seed=8)
    for k, (x, y, r) in enumerate(((7.0, 4.9, 0.7), (10.6, 1.0, 0.8), (6.8, -1.6, 0.6), (-3.0, 6.6, 0.6), (0.6, 7.0, 0.55), (-7.4, 4.4, 0.6),
                                   (3.9, 6.4, 0.5), (-6.0, -1.8, 0.5), (8.8, -1.2, 0.7), (-1.0, 9.6, 0.7))):
        ferns_at(A, x, y, r, seed=k)
    # ---- apron clusters (<=0.6 m, muted)
    # (1) walking sticks + siung hat on the left-near apron
    gz = ground(-5.1, -1.6)
    for k in range(3):
        A.add("battle", "MatWood_timber", paint(K.tube([(-5.8 + 0.05 * k, -2.4 + 0.12 * k, gz + 0.03), (-4.8 + 0.06 * k, -1.5 + 0.1 * k, gz + 0.03)], 0.02, seg=5), (0.50, 0.38, 0.25), ao=0.0))
    A.add("battle", "MatThatch_sago", paint(on_ground(siung(0.28), -4.75, -2.35, 0.0), (0.64, 0.52, 0.32), ao=0.3, ao_h=0.1, ground=gz, top=0.2))
    A.contact(-5.0, -1.8, 0.9, 0.22)
    # (2) pitcher plants + a log step on the far-right apron
    for k, (x, y) in enumerate(((4.2, 3.9), (4.75, 3.2))):
        cups, lv = pitcher(seed=k)
        gz = ground(x, y)
        A.add("battle", "MatLeaf_fern", paint(xf(lv, (x, y, gz), s=1.45), FERN_LT, ao=0.3, ao_h=0.15, ground=gz))   # ~0.5 m clumps
        A.add("battle", "MatLeaf_fern", tint(paint(xf(cups, (x, y, gz), s=1.45), (0.56, 0.30, 0.16), ao=0.3, ao_h=0.15, ground=gz, top=0.2),
                                              lambda v, c: c * np.where(v[:, 2:3] - v[:, 2].min() > 0.1, np.array([[1.25, 0.8, 0.7, 1]]), 1.0)))
    log_step(A, 3.9, 4.5, 0.75, L=0.9)
    # (3) hinava on a slab: wooden board, bowl of fish, small limes, chillies (far-left apron)
    hx, hy = -3.2, 4.85
    gz = ground(hx, hy)
    A.add("battle", "MatWood_timber", paint(xf(K.box(0.6, 0.38, 0.04, bev=0.01), (hx, hy, gz + 0.0), (0, 0, 0.3)), (0.56, 0.42, 0.28), ao=0.0))
    A.add("battle", "MatRock_granite", paint(xf(K.lathe([(0, 0), (0.1, 0), (0.14, 0.07), (0.13, 0.075), (0, 0.03)], seg=12), (hx - 0.1, hy, gz + 0.04)), (0.86, 0.84, 0.80), ao=0.0))
    A.add("battle", "MatCloth_dye", paint(xf(K.lathe([(0, 0), (0.12, 0), (0, 0.025)], seg=10), (hx - 0.1, hy, gz + 0.08)), (0.88, 0.76, 0.66), ao=0.0))
    for k in range(5):
        A.add("battle", "MatLeaf_fern", paint(xf(K.rock(0.028, seed=k, sub=1), (hx + 0.12 + 0.05 * (k % 3), hy - 0.08 + 0.06 * (k // 3), gz + 0.04)), (0.36, 0.58, 0.18), ao=0.0, top=0.3))
    A.add("battle", "MatCloth_dye", paint(K.tube([(hx + 0.05, hy + 0.12, gz + 0.05), (hx + 0.16, hy + 0.14, gz + 0.05)], 0.008, seg=4), (0.80, 0.14, 0.10), ao=0.0))
    A.contact(hx, hy, 0.5, 0.2)
    # near strip (vista foreground, <=1.2 m): a rest log + ferns
    gz = ground(-2.8, -7.4)
    A.add("battle", "MatWood_timber", paint(xf(K.tube([(-1.0, 0, 0.16), (1.0, 0.08, 0.15)], [0.17, 0.15], seg=9), (-2.8, -7.4, gz), (0, 0, 0.25)), (0.38, 0.30, 0.22), var=0.1, ao=0.4, ao_h=0.3, ground=gz, namp=0.25, ns=4))
    A.contact(-2.8, -7.4, 1.2, 0.25)
    ferns_at(A, -1.4, -7.9, 0.7, seed=31)
    ferns_at(A, 2.8, -8.2, 0.8, seed=32)

    stream(A)
    # fill-side edging: half-buried logs along the right terrace lip + scree trickling downhill (+x)
    for k, a in enumerate(np.linspace(math.radians(-50), math.radians(62), 9)):
        a2 = a + math.radians(12)
        r0 = TERR + 0.45
        p0 = (r0 * math.cos(a), r0 * math.sin(a))
        p1 = (r0 * math.cos(a2), r0 * math.sin(a2))
        g0, g1 = ground(*p0), ground(*p1)
        A.add("battle", "MatWood_timber", paint(K.tube([(p0[0], p0[1], g0 + 0.06), (p1[0], p1[1], g1 + 0.06)], 0.11, seg=7), (0.36, 0.28, 0.20), var=0.12, ao=0.45, ao_h=0.2, ground=min(g0, g1), namp=0.2, ns=4))
    rng = random.Random(77)
    for k in range(70):
        x = rng.uniform(7.2, 15.0)
        y = rng.uniform(-3.0, 7.0) + 0.25 * (x - 7.2)
        if stream_d(x, y) < 0.9 or math.hypot(x - BOULDER[0], y - BOULDER[1]) < 1.8:
            continue
        gz = ground(x, y)
        A.add("battle", "MatRock_granite", paint(xf(K.rock(rng.uniform(0.04, 0.12), seed=700 + k, sub=1, squash=(1, rng.uniform(0.6, 1), 0.6)), (x, y, gz - 0.02)),
                                                 GRANITE if k % 2 else GRANITE_DK, ao=0.3, ao_h=0.05, ground=gz))

    # ---- terrain
    A.terrain(ground, gcolor, kind=gkind, rin=4.5, rout=135.0, split=23.0, cull=gcull, seed=3)

    # ---- scatter: montane grass on the moss, sedges along the trail edges
    rng = random.Random(3)
    for k in range(260):
        x, y = rng.uniform(-16, 16), rng.uniform(-8, 14)
        r = math.hypot(x, y)
        if r < 6.4 or path_dist(x, y) < 0.5 or not visible(x, y) or (x < 0 and abs(r - WALL_R) < 0.6):
            continue
        A.scatter_patch("Grass", 30, x, y, rng.uniform(0.5, 1.1), ground, GRASS_T, seed=k)
    for k in range(26):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(5.9, 6.4)
        x, y = r * math.cos(a), r * math.sin(a)
        if path_dist(x, y) < 0.6:
            continue
        A.scatter_patch("Grass", 26, x, y, 0.35, ground, (0.46, 0.54, 0.26), seed=200 + k)
    for k in range(20):
        x, y = rng.uniform(10, 16), rng.uniform(-6, 12)
        A.scatter_patch("Reed", 8, x, y, 0.9, ground, (0.48, 0.52, 0.30), seed=300 + k)

    # ---- far set
    kinabalu(A)
    ridges(A)
    valley(A)
    far_forest(A)
    skies(A)


if __name__ == "__main__":
    K.main("sabah", build, MOOD)
