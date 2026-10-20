"""Selangor arena -- Kuala Selangor at dusk: the grandmother's swept kampung yard on the Sungai Selangor
(design_art.md section c; USER_SPEC: "modern city buildings next to an older kampung house ... his
grandmother preparing nasi lemak nearby").
Ground: swept laterite-ochre laman (broom arcs) with grass edges, mangrove mud on the river bank.
Apron: nasi lemak tray + tiffin carrier, coconut basket, lidi broom + selipar, Danial's string + spare top.
Far band: the river with a timber pangkalan, moored sampans, nipah, berembang mangroves full of fireflies.
Left flank: grandmother's nasi lemak gerai (zinc canopy, plastic stools, old bicycle) + batik drying racks.
Right flank: foot of Bukit Melawati -- laterite fort wall, steps, old cannon, modern street lamp, rain tree.
Far set (vista): old kampung house with lit windows across the river, the modern city skyline behind it,
Bukit Melawati with the lighthouse lit, estuary to the sea, layered ridges and dusk cloud flats.

  blender -b --factory-startup -P art_src/arena_selangor.py -- --export --render game,vista --out <dir>

The section "shared backdrop helpers" (vista-facing cloud flats, ridge layers, smooth domes, visibility)
is imported by arena_nsembilan.py and arena_terengganu.py.
"""
import sys, os, math, random, json
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)  # blender-mcp re-runs
import numpy as np
from mathutils import Vector
from arenakit import P, xf, aim, join, paint, tint, nz, smooth01
from arena_penang import glow_grad

# Godot ARENA_DEFS["selangor"] recommendation (+ b_* = Blender preview factors only)
MOOD = {"sky_top": (0.15, 0.16, 0.38), "sky_horizon": (0.98, 0.58, 0.46), "fog": (0.62, 0.47, 0.58),
        "fog_density": 0.0042, "sun_color": (1.0, 0.68, 0.52), "sun_energy": 0.85,
        "lantern": (1.0, 0.68, 0.36), "lantern_energy": 1.7, "exposure": 0.95, "ambient": 0.5,
        "b_sun": 2.8, "b_world": 0.8, "b_fill": 0.45, "b_lantern": 12.0}


# ================================================================ shared backdrop helpers
VCAM = (-1.5, -12.5)  # vista camera (Blender xy); looks along +y, yaw = degrees right of +y


def vyaw(x, y):
    return math.degrees(math.atan2(x - VCAM[0], y - VCAM[1]))


def in_vista(x, y, pad=0.0):
    dx, dy = x - VCAM[0], y - VCAM[1]
    return dy > 2 and -58 - pad < math.degrees(math.atan2(dx, dy)) < 44 + pad


def in_battle(x, y, pad=0.0):
    return y > -6.5 - pad and abs(x) < 11 + 0.55 * (y + 6.5) + pad


def visible(x, y, pad=0.0):
    """inside the battle frame or the vista frustum (nothing else is ever seen)."""
    return in_battle(x, y, pad) or in_vista(x, y, pad * 2)


def mix(a, b, t):
    return np.asarray(a, dtype=np.float64) * (1 - t) + np.asarray(b, dtype=np.float64) * t


def face_vista(p, x, y, z):
    """place a piece built in local XZ (front normal -Y) at (x,y,z), turned to face the vista camera."""
    th = math.atan2(VCAM[0] - x, y - VCAM[1])
    return xf(p, (x, y, z), (0, 0, th))


def cloud_flat(w, h, seed, lit, shade, n=44, rows=3, rim=0.0):
    """stage-flat cloud: scalloped top (union of bumps), soft flat underside, local XZ facing -Y.
    Vertex colour shade (bottom) -> lit (top). rim>0 adds a thin top lip that catches the light."""
    rng = random.Random(seed)
    nb = max(3, int(w / h * 1.5))
    bumps = []
    for i in range(nb):
        t = (i + 0.5) / nb
        bx = (t - 0.5) * w * 0.84 + rng.uniform(-0.05, 0.05) * w
        br = h * rng.uniform(0.34, 0.62) * (1.0 - 0.5 * abs(2 * t - 1))
        bumps.append((bx, br, h * 0.12 + br * rng.uniform(-0.3, 0.1)))

    def top(x):
        best = -1.0
        for bx, br, bz in bumps:
            d = br * br - (x - bx) ** 2
            if d > 0:
                best = max(best, bz + math.sqrt(d))
        return best

    xs = [x for x in np.linspace(-w * 0.55, w * 0.55, n * 3) if top(x) > 0.02 * h]
    xs = [xs[0]] + list(np.linspace(xs[0], xs[-1], n)[1:-1]) + [xs[-1]]
    hmax = max(top(x) for x in xs)
    v, c, f = [], [], []
    for x in xs:
        tz = top(x)
        bz = -0.05 * h * (1 - (2 * x / w) ** 2) + 0.03 * h * nz(x, 0, 0, 0.3, seed)
        for j in range(rows + 1):
            z = bz + (tz - bz) * j / rows
            v.append((x, 0.0, z))
            k = smooth01(0.0, 1.0, (z - bz) / max(1e-6, hmax)) ** 0.8
            c.append(list(mix(shade, lit, k)) + [1.0])
    R = rows + 1
    for i in range(len(xs) - 1):
        for j in range(rows):
            a = i * R + j
            f.append((a, a + R, a + R + 1, a + 1))
    p = P(v, f, c)
    if rim > 0:
        base = len(v)
        for i, x in enumerate(xs):
            q = v[i * R + rows]
            v.append((q[0], rim, q[2] - rim * 0.3))
            c.append(list(np.asarray(lit) * 0.92) + [1.0])
        rf = [(i * R + rows, base + i, base + i + 1, (i + 1) * R + rows) for i in range(len(xs) - 1)]
        p = P(v, f + rf, c)
    return p


def ridge_layer(dist, a0, a1, base, h0, h1, seed, rgb_top, rgb_base, n=90, freq=3.0, crowns=0.0, lean=0.3,
                peaks=None):
    """vista-facing ridge silhouette on an arc `dist` m from the vista camera, yaw a0..a1 degrees.
    crowns adds tree-crown bumps on the crest; peaks [(yaw, height, width_deg)] adds summits."""
    v, c, f = [], [], []
    rows = 3
    for i in range(n + 1):
        u = i / n
        a = math.radians(a0 + (a1 - a0) * u)
        s = 0.5 + 0.5 * (0.65 * nz(u * freq, 0.37 * seed, 0, 1.0, seed) + 0.35 * nz(u * freq * 2.7, 1.3, 0, 1.0, seed + 1))
        top = h0 + (h1 - h0) * s
        if crowns:
            top += crowns * abs(nz(u * n * 0.45, 2.1, 0, 1.0, seed + 2))
        for (pa, ph, pw) in (peaks or []):
            top += ph * math.exp(-((a0 + (a1 - a0) * u - pa) / pw) ** 2)
        dx, dy = math.sin(a), math.cos(a)
        for j in range(rows + 1):
            t = j / rows
            z = base + (top - base) * t ** 0.85
            d = dist + lean * (z - base)
            v.append((VCAM[0] + d * dx, VCAM[1] + d * dy, z))
            c.append(list(mix(rgb_base, rgb_top, t ** 0.7)) + [1.0])
    R = rows + 1
    for i in range(n):
        for j in range(rows):
            a = i * R + j
            f.append((a, a + R, a + R + 1, a + 1))
    return P(v, f, c)


def dome(R, H, seed, seg=56, rings=14, base=-1.0, lump=0.0, lump_s=0.6, squash=(1.0, 1.0), power=1.6):
    """smooth hill: polar mesh, cos-power profile, wobbly footprint, optional canopy lumps. Centre (0,0)."""
    v, f = [(0.0, 0.0, H)], []
    for k in range(1, rings + 1):
        t = k / rings
        for i in range(seg):
            a = 2 * math.pi * i / seg
            wob = 1.0 + 0.18 * nz(math.cos(a) * 1.3, math.sin(a) * 1.3, 0, 1.0, seed)
            r = R * t * wob
            x, y = r * math.cos(a) * squash[0], r * math.sin(a) * squash[1]
            z = base + (H - base) * math.cos(math.pi * 0.5 * t) ** power
            if lump:
                z += lump * (0.5 + 0.5 * nz(x, y, 0, lump_s, seed + 3)) * (1 - t ** 3) + lump * 0.5 * abs(nz(x, y, 0, lump_s * 3, seed + 4)) * (1 - t ** 3)
            v.append((x, y, z))
    for i in range(seg):
        f.append((0, 1 + i, 1 + (i + 1) % seg))
    for k in range(rings - 1):
        a0, a1 = 1 + k * seg, 1 + (k + 1) * seg
        for i in range(seg):
            j = (i + 1) % seg
            f.append((a0 + i, a1 + i, a1 + j, a0 + j))
    return P(v, f)


def write_mood(arena_id, mood, extra=None):
    """dump the Godot ARENA_DEFS recommendation (b_* preview keys stripped) next to the report."""
    o = K._argv(None)
    if not o["out"]:
        return
    d = {k: (list(v) if isinstance(v, tuple) else v) for k, v in mood.items() if not k.startswith("b_")}
    d.update(extra or {})
    with open(os.path.join(o["out"], "%s_mood.json" % arena_id), "w") as fh:
        json.dump(d, fh, indent=1)


# ================================================================ palette (sRGB)
YARD = (0.62, 0.51, 0.39)
YARD_LT = (0.70, 0.60, 0.46)
YARD_DK = (0.50, 0.41, 0.32)
GRASS_G = (0.33, 0.43, 0.19)
GRASS_TINT = (0.40, 0.50, 0.22)
MUD = (0.40, 0.37, 0.37)
MUD_WET = (0.27, 0.27, 0.31)
LATERITE = (0.52, 0.34, 0.26)
TIMBER = (0.46, 0.33, 0.22)
TIMBER_DK = (0.28, 0.19, 0.13)
BAMBOO = (0.66, 0.58, 0.34)
IRON = (0.14, 0.14, 0.15)
ZINC = (0.56, 0.57, 0.58)
RUST = (0.52, 0.30, 0.18)
LEAF = (0.18, 0.30, 0.14)
LEAF_LT = (0.30, 0.45, 0.18)
NIPAH = (0.34, 0.46, 0.20)
RIVER = (0.36, 0.38, 0.52)
RIVER_EDGE = (0.38, 0.36, 0.40)
SEA = (0.30, 0.33, 0.42)
BATIK = {"indigo": (0.14, 0.18, 0.44), "red": (0.68, 0.16, 0.13), "gold": (0.88, 0.63, 0.17), "teal": (0.08, 0.45, 0.46),
         "magenta": (0.62, 0.17, 0.42), "soga": (0.46, 0.28, 0.14), "cream": (0.90, 0.83, 0.66), "green": (0.20, 0.46, 0.22)}

# ================================================================ layout
WZ = -0.44         # river surface (main.tscn's dark Ground plane sits at -0.5 out to 22 m)
BED = -1.15
RC = [(-200, 10.6), (-60, 9.9), (-20, 9.2), (-4, 9.4), (1.5, 10.0), (5.2, 12.4), (7.6, 16.8), (9.0, 24.0),
      (9.6, 34.0), (9.0, 48.0), (8.0, 66.0), (8.0, 100.0), (10.0, 160.0), (20.0, 400.0)]
TERRACE = (9.4, 3.0, 2.3, 0.62)        # cannon terrace (x, y, r, z)
STALL = (-7.7, -2.6)
JETTY_X = 2.4
HOUSE = (-6.0, 19.0)
HILL = (24.0, 42.0, 16.0, 6.8)        # Bukit Melawati dome (x, y, R, H); its west foot dips into the river
PATHS = [[(1.5, 4.5), (2.0, 5.2), (2.4, 5.6)], [(-4.6, -1.6), (-6.0, -2.0), (-6.8, -2.3)],
         [(4.6, 1.2), (6.0, 1.5), (7.1, 1.8)], [(-4.4, 2.0), (-6.0, 2.6), (-7.2, 2.4)]]


def _seg(px, py, a, b):
    ax_, ay_ = a
    bx, by = b
    dx, dy = bx - ax_, by - ay_
    t = max(0.0, min(1.0, ((px - ax_) * dx + (py - ay_) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax_ - t * dx, py - ay_ - t * dy), ay_ + t * dy


def river(x, y):
    """(distance to the centreline, half width there)."""
    best, yc = 1e9, 0.0
    for a, b in zip(RC[:-1], RC[1:]):
        d, yy = _seg(x, y, a, b)
        if d < best:
            best, yc = d, yy
    return best, 3.1 + 0.16 * max(0.0, yc - 11.0) + 0.002 * max(0.0, yc - 60) ** 1.5


def path_dist(x, y):
    return min(_seg(x, y, a, b)[0] for pl in PATHS for a, b in zip(pl[:-1], pl[1:]))


def east(x, y):
    """0 west of the river, 1 on the Melawati side (east of the north-running reach / right flank)."""
    return smooth01(6.6, 8.6, x - 0.08 * max(0.0, y - 10.0))


def land(x, y):
    n = 0.03 * nz(x, y, 0, 0.6, 3) + 0.015 * nz(x, y, 0, 2.0, 4)
    rise = east(x, y) * (0.34 * max(0.0, x - 7.0) + 0.08 * max(0.0, x - 7.0) ** 1.4)
    rise = min(rise, 4.2) + 0.25 * east(x, y) * nz(x, y, 1, 0.25, 5)
    h = n + rise
    tx, ty, tr, tz = TERRACE  # flat cannon terrace cut into the slope
    h = h + (tz - h) * (1 - smooth01(tr * 0.8, tr * 1.25, math.hypot(x - tx, y - ty)))
    if -10.5 < x < -1.5 and 15.5 < y < 22.5:  # house yard across the river
        h = max(h, 0.15)
    return h * (1 - smooth01(70, 115, math.hypot(x, y)))


def sea_t(x, y):
    """1 inside the sea-plane region (beyond the estuary mouth), 0 on land."""
    return smooth01(-12.0, 0.0, y - (120 - 60 * (x + 40) / 340))


def ground(x, y):
    d, hw = river(x, y)
    h = land(x, y)
    h = h + (BED - h) * sea_t(x, y)
    bed = BED + 0.15 * nz(x, y, 0, 0.4, 6)
    t = smooth01(hw - 0.5, hw + 2.0 + 0.6 * nz(x, y, 0, 0.5, 7), d)
    h = bed + (h - bed) * t
    pd = path_dist(x, y)
    if pd < 0.5 and h > -0.1:
        h -= 0.02 * (1 - smooth01(0.1, 0.5, pd))
    return float(h)


def in_water(x, y):
    d, hw = river(x, y)
    return d < hw + 1.2


def gcolor(x, y, z):
    n1 = nz(x, y, 0, 0.45, 11)
    n2 = nz(x, y, 0, 2.3, 12)
    n3 = nz(x, y, 0, 6.0, 13)
    r = math.hypot(x, y)
    d, hw = river(x, y)
    # swept laman: broom arcs around the dish, lighter where trodden
    sweep = 0.5 + 0.5 * math.sin(r * 5.2 + 1.8 * nz(x, y, 0, 0.35, 14) + math.atan2(y, x) * 2.0)
    base = np.array(YARD) * (1 + 0.10 * n1 + 0.06 * n2 + 0.04 * n3) * (0.95 + 0.07 * sweep)
    base = mix(base, YARD_LT, 0.5 * (1 - smooth01(4.6, 6.0, r)))
    base = mix(base, YARD_DK, 0.35 * smooth01(0.2, 0.6, nz(x, y, 0, 0.4, 15)))
    yard = 1 - smooth01(6.4, 8.4, r + 1.6 * n1)
    grass = 1 - yard
    grass = max(grass, 0.75 * smooth01(0.35, 0.7, nz(x, y, 0, 0.6, 16)) * smooth01(5.6, 7.0, r))
    g = np.array(GRASS_G) * (1 + 0.12 * n2 + 0.08 * n1)
    g = mix(g, (0.42, 0.47, 0.22), 0.4 * smooth01(0.0, 0.6, n3))
    base = mix(base, g, min(1.0, grass) * smooth01(0.15, 0.6, path_dist(x, y)))
    e = east(x, y)  # Melawati slope: laterite showing through the grass
    base = mix(base, mix(g, LATERITE, 0.45 * smooth01(0.1, 0.5, nz(x, y, 0, 0.5, 17))), e * smooth01(7.0, 8.5, x))
    base = mix(base, YARD_LT, 0.6 * (1 - smooth01(0.0, 0.45, path_dist(x, y))))
    # river bank: mangrove mud, wet to the waterline
    bank = 1 - smooth01(hw + 1.4, hw + 3.0 + 0.8 * n1, d)
    mud = mix(np.array(MUD) * (1 + 0.1 * n2), MUD_WET, smooth01(WZ + 0.35, WZ - 0.05, z))
    base = mix(base, mud, bank)
    if r > 23:
        base = mix(base, (0.30, 0.38, 0.18), 0.6)  # far kampung land reads green under the dusk haze
    return tuple(base)


def gkind(x, y, z):
    d, hw = river(x, y)
    if math.hypot(x, y) < 23 and d < hw + 2.4 and z < 0.0:
        return "MatMud_bank"
    return "MatGround_yard"


def gcull(cx, cy, zmax):
    if (in_water(cx, cy) or sea_t(cx, cy) > 0.99) and zmax < WZ - 0.04:
        return True
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


# ================================================================ prop builders
def bamboo(a, b, r=0.04, seed=0, node=0.55):
    """bamboo pole a->b with node rings. Returns (pole, rings)."""
    A_, B_ = Vector(a), Vector(b)
    L = (B_ - A_).length
    pole = K.tube([a, tuple(A_.lerp(B_, 0.5)), b], [r * 1.05, r, r * 0.95], seg=7)
    rings = []
    k = 1
    while k * node < L - 0.05:
        c = A_.lerp(B_, k * node / L)
        rings.append(aim(K.lathe([(r * 1.0, -0.012), (r * 1.18, 0.0), (r * 1.0, 0.012)], seg=6, cap0=False, cap1=False),
                         tuple(c), tuple(c + (B_ - A_).normalized())))
        k += 1
    return pole, rings


def batik_pattern(kind, u, v, W, L, seed):
    """batik colour at panel coords (u across, v down), big colour shapes that survive vertex sampling."""
    B = BATIK
    border = u < 0.07 or u > 0.93 or v < 0.06 or v > 0.94
    if kind == 0:  # parang: diagonal bands, indigo/cream/soga with gold border
        if border:
            return B["gold"]
        s = (u * W + v * L) * 1.5
        k = int(math.floor(s)) % 3
        return (B["indigo"], B["cream"], B["soga"])[k]
    if kind == 1:  # big flowers on red with an indigo kepala (head panel)
        if v < 0.28:
            return B["indigo"] if not (0.12 < (v * 7) % 1.0 < 0.5) else B["gold"]
        cu, cv = (u * W) % 0.55 - 0.275, ((v - 0.28) * L) % 0.6 - 0.3
        rr = math.hypot(cu, cv)
        ang = math.atan2(cv, cu)
        if rr < 0.2 * (0.72 + 0.28 * math.cos(5 * ang)):
            return B["gold"] if rr > 0.06 else B["indigo"]
        return B["red"]
    if kind == 2:  # teal with magenta diamonds (songket-like lattice)
        if border:
            return B["magenta"]
        a = abs(((u * W) % 0.5) - 0.25) + abs(((v * L) % 0.5) - 0.25)
        return B["magenta"] if a < 0.14 else (B["cream"] if a < 0.19 else B["teal"])
    if kind == 3:  # pucuk rebung triangles along both ends, green body with gold dots
        for vv in (v, 1 - v):
            if vv < 0.22:
                tri = abs(((u * W) % 0.36) - 0.18) / 0.18
                return B["red"] if vv / 0.22 < 1 - tri else B["cream"]
        cu, cv = (u * W) % 0.3 - 0.15, (v * L) % 0.3 - 0.15
        return B["gold"] if math.hypot(cu, cv) < 0.06 else B["green"]
    # kind 4: gold body, soga + indigo wavy awan larat stripes
    s = math.sin(u * W * 6.0 + math.sin(v * L * 3.0) * 1.5)
    return B["indigo"] if s > 0.55 else (B["soga"] if s < -0.6 else B["gold"])


def batik_panel(W, L, kind, seed, sway=0.12, nxs=11, nzs=22):
    """hanging cloth in local XZ (top edge at z=0 along x, hangs down), billowing; vertex-coloured batik."""
    rng = random.Random(seed)
    ph = rng.uniform(0, 6.28)
    v, c, f = [], [], []
    for j in range(nzs + 1):
        t = j / nzs
        for i in range(nxs + 1):
            u = i / nxs
            x = (u - 0.5) * W
            y = 0.05 * math.sin(math.pi * u) * (0.3 + t) + sway * t ** 1.6 * math.sin(ph + u * 2.2) + 0.03 * math.sin(u * 9 + t * 4 + ph)
            z = -L * t + 0.04 * math.sin(math.pi * u) * t
            v.append((x, y, z))
            col = np.array(batik_pattern(kind, u, t, W, L, seed))
            col = col * (1.0 - 0.1 * t) * (0.94 + 0.06 * math.sin(u * 31 + t * 17))  # dye mottling
            c.append(list(np.clip(col, 0, 1)) + [1.0])
    R = nxs + 1
    for j in range(nzs):
        for i in range(nxs):
            a = j * R + i
            f.append((a, a + 1, a + R + 1, a + R))
    return P(v, f, c)


def batik_rack(A, x0, y0, x1, y1, kinds, seed, h=2.7):
    """two bamboo posts + crossbar along (x0,y0)->(x1,y1); batik lengths hanging from the bar."""
    wood, rings = [], []
    rng = random.Random(seed)
    for (px, py) in ((x0, y0), (x1, y1)):
        gz = ground(px, py)
        p, r = bamboo((px, py, gz - 0.1), (px + rng.uniform(-0.04, 0.04), py, gz + h + 0.12), r=0.045, seed=seed)
        wood.append(p)
        rings += r
        L0 = math.hypot(x1 - x0, y1 - y0)
        for s in (-1, 1):  # splayed struts, perpendicular to the rack
            q, _ = bamboo((px - s * 0.45 * (y1 - y0) / L0, py + s * 0.45 * (x1 - x0) / L0, gz - 0.05), (px, py, gz + h * 0.62), r=0.03, seed=seed + 1)
            wood.append(q)
    gz = ground(0.5 * (x0 + x1), 0.5 * (y0 + y1))
    bar, r = bamboo((x0, y0, gz + h), (x1, y1, gz + h), r=0.035, seed=seed + 2)
    wood.append(bar)
    rings += r
    A.add("battle", "MatWood_timber", [paint(q, BAMBOO, var=0.06, ao=0.35, ao_h=1.2, ground=gz, namp=0.08, ns=6, stretch=(1, 1, 0.2)) for q in wood])
    A.add("battle", "MatWood_timber", [paint(q, (0.48, 0.42, 0.24), ao=0.0) for q in rings])
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    n = len(kinds)
    W = (L - 0.3) / n - 0.08
    for k, kind in enumerate(kinds):
        t = (k + 0.5) / n
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        Lk = rng.uniform(1.9, 2.35)
        pnl = batik_panel(W, Lk, kind, seed * 10 + k)
        pnl = xf(pnl, (cx, cy, gz + h + 0.02), (0, 0, ang))
        A.add("battle", "MatCloth_batik", pnl)
        A.contact(cx, cy, 0.9, 0.18)


def zinc_sheet(w, d, ribs=22, amp=0.018):
    """corrugated zinc sheet in local XY (ribs along Y), centred, z ~ 0."""
    v, f = [], []
    nx_ = ribs * 2
    for j in range(3):
        for i in range(nx_ + 1):
            x = (i / nx_ - 0.5) * w
            v.append((x, (j / 2 - 0.5) * d, amp * math.sin(i * math.pi)))
    R = nx_ + 1
    for j in range(2):
        for i in range(nx_):
            a = j * R + i
            f.append((a, a + 1, a + R + 1, a + R))
    return K.dbl(P(v, f))


def stool(r=0.17, h=0.42):
    return K.lathe([(0, h), (r, h), (r * 1.02, h - 0.03), (r * 1.25, 0.0), (r * 1.18, 0.0), (r * 0.95, h - 0.05), (0, h - 0.05)], seg=14,
                   cap0=False, cap1=False)


def gerai(A, x, y, rz):
    """grandmother's nasi lemak stall: timber table, zinc canopy, pots, banana-leaf bungkus, lamp, stools."""
    wood, metal, clay, leaf, glow, cloth, plast = [], [], [], [], [], [], []
    for sx in (-0.75, 0.75):
        for sy in (-0.3, 0.3):
            wood.append(xf(K.box(0.07, 0.07, 0.78, bev=0.01), (sx, sy, 0)))
    for k in range(6):
        wood.append(xf(K.plank(1.7, 0.125, 0.03), (0, -0.33 + k * 0.13, 0.78)))
    wood.append(xf(K.box(1.55, 0.6, 0.025, bev=0.006), (0, 0, 0.2)))  # lower shelf
    for sx, h in ((-0.95, 2.15), (0.95, 2.15)):
        for sy, dh in ((-0.55, 0.0), (0.55, -0.22)):
            wood.append(xf(K.post(h + dh, 0.035, seed=int(sx * 10 + sy * 7), seg=6), (sx, sy, 0)))
    roof = zinc_sheet(2.3, 1.45)
    roof = xf(roof, (0, 0, 2.06), (math.atan2(0.22, 1.1), 0, 0))
    metal.append(roof)
    # big rice pot, sambal pot, enamel tray of eggs, banana-leaf bungkus pyramid, plates
    metal.append(xf(K.lathe([(0, 0), (0.2, 0), (0.22, 0.04), (0.22, 0.26), (0.24, 0.27), (0.22, 0.28), (0, 0.28)], seg=16), (-0.45, 0.05, 0.81)))
    metal.append(xf(K.lathe([(0, 0), (0.23, 0), (0.12, 0.06), (0.03, 0.08), (0, 0.1)], seg=12), (-0.45, 0.05, 1.09)))  # lid
    clay.append(xf(K.jar(0.13, 0.2), (0.15, 0.1, 0.81)))
    metal.append(xf(K.box(0.5, 0.34, 0.035, bev=0.008), (0.55, -0.1, 0.81)))
    for k in range(6):
        clay.append(xf(K.rock(0.03, seed=700 + k, sub=1, squash=(1, 0.8, 1.1)), (0.42 + 0.09 * (k % 3), -0.18 + 0.12 * (k // 3), 0.845)))
    for k in range(9):  # bungkus pyramids, stacked
        bx_, by_ = 0.25 + 0.13 * (k % 3) - 0.13, 0.22 + 0.11 * (k // 3) * 0.6
        bz = 0.81 + (0.075 if k >= 6 else 0.0)
        leaf.append(xf(P([(-0.05, -0.04, 0), (0.05, -0.04, 0), (0.0, 0.05, 0), (0, 0, 0.075)], [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)]),
                       (bx_ + 0.3, by_ - 0.05, bz), (0, 0, k * 0.7)))
    # hanging hurricane lamp
    glow.append(xf(K.lathe([(0, 0), (0.06, 0.0), (0.075, 0.08), (0.05, 0.17), (0, 0.18)], seg=10), (0.2, -0.35, 1.55)))
    metal.append(K.tube([(0.2, -0.35, 1.73), (0.2, -0.35, 2.0)], 0.006, seg=3))
    # cloth skirt on the table front
    skirt = batik_panel(1.7, 0.55, 2, 77, sway=0.02, nxs=10, nzs=4)
    cloth.append(xf(skirt, (0, -0.37, 0.79)))
    gz = ground(x, y)

    def put(lst):
        return [xf(p, (x, y, gz), (0, 0, rz)) for p in lst]
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, var=0.1, ao=0.45, ao_h=0.8, ground=gz, namp=0.12, ns=3, stretch=(1, 1, 0.2)) for q in put(wood)])
    A.add("battle", "MatMetal_iron", [tint(paint(q, ZINC, var=0.05, ao=0.0, top=0.1), lambda v, c: c * np.where(
        (np.array([nz(a, b, cc, 1.6, 21) for a, b, cc in v]) > 0.15)[:, None], np.array([0.92, 0.6, 0.42, 1]), 1.0)) for q in put(metal[:1])])
    A.add("battle", "MatMetal_iron", [paint(q, (0.70, 0.70, 0.70), var=0.03, ao=0.2, ao_h=0.2, ground=gz + 0.8) for q in put(metal[1:])])
    A.add("battle", "MatRock_laterite", [paint(q, (0.50, 0.26, 0.16), ao=0.3, ao_h=0.1, ground=gz + 0.8, top=0.2) for q in put(clay[:1])])
    A.add("battle", "MatRock_laterite", [paint(q, (0.92, 0.88, 0.80), ao=0.0, top=0.2) for q in put(clay[1:])])
    A.add("battle", "MatLeaf_canopy", [paint(q, (0.24, 0.42, 0.16), var=0.1, ao=0.0, top=0.25) for q in put(leaf)])
    A.add("battle", "MatGlow_lamp", [paint(q, (1.0, 0.85, 0.55), ao=0.0, top=0.0) for q in put(glow)])
    A.add("battle", "MatCloth_batik", put(cloth))
    lp = xf(P([(0.2, -0.35, 1.62)], []), (x, y, gz), (0, 0, rz)).v[0]
    A.light(tuple(lp), 16.0, (1.0, 0.70, 0.40), range_m=5)
    # plastic stools (modern) beside the stall
    for k, (dx, dy, col) in enumerate(((1.05, -0.95, (0.72, 0.14, 0.12)), (1.25, 0.45, (0.16, 0.34, 0.62)), (-0.2, -1.05, (0.72, 0.14, 0.12)))):
        sx_, sy_ = xf(P([(dx, dy, 0)], []), (x, y, 0), (0, 0, rz)).v[0][:2]
        A.add("battle", "MatCloth_batik", paint(on_ground(stool(), sx_, sy_), col, var=0.04, ao=0.3, ao_h=0.3, ground=ground(sx_, sy_), top=0.2))
        A.contact(sx_, sy_, 0.4, 0.25)
    A.contact(x, y, 1.6, 0.3)


def bicycle(A, x, y, rz, lean=0.2):
    """old basikal tua on its stand with a rear carrier and a front basket."""
    R = 0.33
    met, wood, cloth = [], [], []
    for cx in (-0.55, 0.55):
        rim = [(cx + R * math.cos(2 * math.pi * i / 24), 0, R + R * math.sin(2 * math.pi * i / 24)) for i in range(25)]
        met.append(K.tube(rim, 0.016, seg=5, cap=False))
        tyre = [(cx + (R + 0.012) * math.cos(2 * math.pi * i / 24), 0, R + (R + 0.012) * math.sin(2 * math.pi * i / 24)) for i in range(25)]
        cloth.append(K.tube(tyre, 0.02, seg=5, cap=False))
        for k in range(8):
            a = 2 * math.pi * k / 8
            met.append(K.tube([(cx, 0, R), (cx + R * math.cos(a), 0, R + R * math.sin(a))], 0.004, seg=3, cap=False))
    bb = (0.0, 0, 0.3)
    st = (-0.2, 0, 0.82)
    hd = (0.42, 0, 0.86)
    for a, b in ((bb, st), (bb, hd), (st, hd), (bb, (-0.55, 0, R)), (st, (-0.55, 0, R)), (hd, (0.55, 0, R)),
                 (hd, (0.47, 0, 1.0)), ((0.47, -0.25, 1.02), (0.47, 0.25, 1.02))):
        met.append(K.tube([a, b], 0.017, seg=6))
    met.append(xf(K.box(0.5, 0.26, 0.02, bev=0.005), (-0.5, 0, 0.66)))  # rear carrier
    for k in range(3):
        met.append(K.tube([(-0.72, -0.12 + 0.12 * k, 0.67), (-0.28, -0.12 + 0.12 * k, 0.67)], 0.008, seg=3))
    cloth.append(xf(K.lathe([(0, 0), (0.1, 0.0), (0.13, 0.03), (0.06, 0.05), (0, 0.05)], seg=10), (-0.2, 0, 0.84), s=(1.5, 1, 1)))  # saddle
    wood.append(xf(K.basket(0.15, 0.2, seg=12), (0.62, 0, 0.8)))
    met.append(K.tube([(-0.05, 0, 0.3), (-0.12, 0.25, 0.0)], 0.01, seg=4))  # stand
    gz = ground(x, y)
    put = lambda lst: [xf(xf(p, (0, 0, 0), (lean, 0, 0)), (x, y, gz), (0, 0, rz)) for p in lst]
    A.add("battle", "MatMetal_iron", [paint(q, (0.12, 0.13, 0.12), var=0.03, ao=0.0, top=0.3) for q in put(met)])
    A.add("battle", "MatCloth_batik", [paint(q, (0.10, 0.09, 0.08), ao=0.0) for q in put(cloth)])
    A.add("battle", "MatThatch_atap", [paint(q, (0.55, 0.42, 0.25), ao=0.2, ao_h=0.3, ground=gz) for q in put(wood)])
    A.contact(x, y, 0.8, 0.22)


def laterite_wall(A, pts, h, seed, cap=True):
    """course-laid laterite blocks along a 2D polyline, base on the lower ground."""
    rng = random.Random(seed)
    blocks = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        ang = math.atan2(y1 - y0, x1 - x0)
        courses = int(h / 0.26)
        for c in range(courses):
            off = 0.0 if c % 2 == 0 else 0.25
            s = -off
            while s < L - 0.05:
                bl = min(rng.uniform(0.42, 0.56), L - max(s, 0.0))
                a0 = max(s, 0.0)
                cx, cy = x0 + math.cos(ang) * (a0 + bl * 0.5), y0 + math.sin(ang) * (a0 + bl * 0.5)
                gz = min(ground(x0, y0), ground(x1, y1)) - 0.08
                b = K.box(bl - 0.025, 0.36, 0.25, bev=0.018, jitter=0.01, seed=rng.randint(0, 999))
                q = paint(xf(b, (cx, cy, gz + c * 0.26), (0, 0, ang + rng.uniform(-0.03, 0.03))),
                          LATERITE, var=0.14, ao=0.35, ao_h=0.6, ground=gz, namp=0.3, ns=5)
                if c == courses - 1:  # moss on the cap course
                    q = tint(q, lambda v, cc: np.where((K.vnormals(P(v, b.f))[:, 2] > 0.7)[:, None], cc * 0.4 + np.array([0.20, 0.27, 0.13, 0.6]), cc))
                blocks.append(q)
                s += bl
    A.add("battle", "MatRock_laterite", blocks)


def cannon(A, x, y, rz, gz, s=1.0):
    """old fort cannon on a timber carriage; barrel lathe along +x."""
    prof = [(0.0, -0.12), (0.06, -0.1), (0.07, -0.05), (0.05, -0.02), (0.15, 0.0), (0.19, 0.04), (0.19, 0.12), (0.17, 0.14), (0.17, 0.5),
            (0.185, 0.52), (0.185, 0.58), (0.155, 0.6), (0.135, 1.35), (0.15, 1.38), (0.15, 1.46), (0.13, 1.5), (0.16, 1.62), (0.16, 1.7),
            (0.075, 1.7), (0.075, 1.62), (0.0, 1.62)]
    barrel = xf(K.lathe(prof, seg=20, cap0=False, cap1=False), (0, 0, 0), (0, math.pi / 2 - 0.08, 0))
    trun = K.tube([(0.55, -0.27, 0.0), (0.55, 0.27, 0.0)], 0.05, seg=8)
    barrel = join(barrel, trun)
    barrel = xf(barrel, (-0.55, 0, 0.62))
    wood, met = [], [barrel]
    for sy in (-0.21, 0.21):
        wood.append(xf(K.box(1.1, 0.09, 0.32, bev=0.02), (-0.05, sy, 0.22)))
        wood.append(xf(K.box(0.6, 0.09, 0.18, bev=0.02), (-0.3, sy, 0.54)))
    wood.append(xf(K.box(0.24, 0.5, 0.1, bev=0.015), (0.3, 0, 0.2)))
    for ax_ in (-0.42, 0.3):
        met.append(K.tube([(ax_, -0.3, 0.17), (ax_, 0.3, 0.17)], 0.03, seg=6))
        for sy in (-0.3, 0.3):
            wood.append(xf(K.lathe([(0, -0.05), (0.17, -0.05), (0.17, 0.05), (0, 0.05)], seg=14), (ax_, sy, 0.17), (math.pi / 2, 0, 0)))
    put = lambda lst: [xf(p, (x, y, gz), (0, 0, rz), s) for p in lst]
    A.add("battle", "MatMetal_iron", [paint(q, IRON, var=0.03, ao=0.25, ao_h=0.4, ground=gz, namp=0.25, ns=4) for q in put(met)])
    A.add("battle", "MatWood_timber", [paint(q, (0.34, 0.22, 0.14), var=0.08, ao=0.4, ao_h=0.5, ground=gz, namp=0.12, ns=4) for q in put(wood)])
    A.contact(x, y, 1.2, 0.35)


def street_lamp(A, x, y, rz):
    gz = ground(x, y)
    pole = K.lathe([(0.0, 0.0), (0.16, 0.0), (0.16, 0.05), (0.08, 0.08), (0.065, 1.0), (0.05, 3.5), (0.0, 3.52)], seg=12, cap0=False)
    arm = K.tube(K.arc((0, 0, 3.35), (0.95, 0, 3.55), 0.25, n=6), 0.03, seg=6)
    head = xf(K.lathe([(0, 0), (0.1, 0.0), (0.16, 0.05), (0.12, 0.1), (0, 0.11)], seg=12), (1.05, 0, 3.42), s=(1.5, 1, 1))
    lens = xf(K.lathe([(0, 0.0), (0.11, 0.0), (0.0, -0.035)], seg=12, cap0=False), (1.05, 0, 3.42), s=(1.5, 1, 1))
    put = lambda lst: [xf(p, (x, y, gz), (0, 0, rz)) for p in lst]
    A.add("battle", "MatMetal_iron", [paint(q, (0.50, 0.52, 0.53), var=0.03, ao=0.25, ao_h=0.6, ground=gz, top=0.15) for q in put([pole, arm, head])])
    A.add("battle", "MatGlow_lamp", [paint(q, (1.0, 0.82, 0.5), ao=0.0, top=0.0) for q in put([lens])])
    lp = xf(P([(1.05, 0, 3.25)], []), (x, y, gz), (0, 0, rz)).v[0]
    A.light(tuple(lp), 40.0, (1.0, 0.68, 0.36), range_m=8)
    A.contact(x, y, 0.5, 0.25)


def rain_tree(A, x, y, h, seed, set_="battle", spread=1.0, away=None):
    """pokok hujan-hujan: flared trunk, few big limbs, wide umbrella canopy."""
    rng = random.Random(seed)
    gz = ground(x, y)
    wood = [K.tube([(0, 0, -0.2), (0.1, 0.05, h * 0.25), (0.2, -0.05, h * 0.45)], [0.42, 0.3, 0.26], seg=10)]
    for k in range(3):  # buttress flare
        a = 2 * math.pi * k / 3 + 0.4
        wood.append(K.tube([(0.5 * math.cos(a), 0.5 * math.sin(a), -0.1), (0.15 * math.cos(a), 0.15 * math.sin(a), 0.9)], [0.16, 0.08], seg=6))
    leaf = []
    for k in range(5):
        a = 2 * math.pi * k / 5 + rng.uniform(-0.3, 0.3) if away is None else away + (k - 2) * 0.5 + rng.uniform(-0.2, 0.2)
        L = h * spread * rng.uniform(0.5, 0.75)
        end = (L * math.cos(a), L * math.sin(a), h * rng.uniform(0.62, 0.8))
        wood.append(K.tube(K.arc((0.2, -0.05, h * 0.42), end, h * 0.12, n=5), [0.2, 0.17, 0.14, 0.11, 0.08, 0.06], seg=7))
        leaf.append(xf(K.canopy(h * 0.3 * spread, seed=seed * 9 + k, lumps=3, sub=2, squash=0.42, spread=0.8), (end[0], end[1], end[2] + 0.2)))
    leaf.append(xf(K.canopy(h * 0.36 * spread, seed=seed * 9 + 7, lumps=3, sub=2, squash=0.4, spread=0.6), (0.2, 0, h * 0.86)))
    A.add(set_, "MatWood_timber", [paint(xf(q, (x, y, gz)), (0.30, 0.25, 0.20), var=0.08, ao=0.5, ao_h=2.0, ground=gz, namp=0.15, ns=2) for q in wood])
    A.add(set_, "MatLeaf_canopy", [paint(xf(q, (x, y, gz)), LEAF, var=0.12, ao=0.5, ao_h=h * 0.9, ground=gz, top=0.55, namp=0.25, ns=0.8) for q in leaf])
    if set_ == "battle":
        A.contact(x, y, 2.2, 0.35)


def berembang(A, x, y, h, seed, flies=40, set_="battle"):
    """Sonneratia mangrove: leaning trunk, drooping canopy, pneumatophore spikes, fireflies in the crown."""
    rng = random.Random(seed)
    gz = max(ground(x, y), WZ - 0.1)
    lean = (rng.uniform(-0.3, 0.3), rng.uniform(-0.2, 0.3))
    top = (lean[0] * h * 0.25, lean[1] * h * 0.25, h * 0.55)
    wood = [K.tube([(0, 0, -0.3), (top[0] * 0.5, top[1] * 0.5, h * 0.3), top], [0.16, 0.12, 0.09], seg=8)]
    leaf = [xf(K.canopy(h * 0.32, seed=seed * 5, lumps=3 if set_ == "battle" else 2, sub=2, squash=0.55, spread=0.75), (top[0], top[1], top[2] - 0.1))]
    for k in range(3 if set_ == "battle" else 1):
        a = rng.uniform(0, 2 * math.pi)
        d = h * rng.uniform(0.18, 0.3)
        e = (top[0] + d * math.cos(a), top[1] + d * math.sin(a), top[2] - h * rng.uniform(0.0, 0.15))
        wood.append(K.tube([top, e], [0.06, 0.03], seg=5))
        leaf.append(xf(K.canopy(h * rng.uniform(0.18, 0.24), seed=seed * 5 + k + 1, lumps=2, sub=2, squash=0.65), (e[0], e[1], e[2] - 0.35)))
    leafp = join(leaf)
    spikes = []
    if set_ == "battle":
        for k in range(16):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(0.5, 1.6)
            px, py = r * math.cos(a), r * math.sin(a)
            spikes.append(xf(K.lathe([(0.018, 0), (0.008, 0.18), (0, 0.22)], seg=4, cap0=False), (px, py, max(ground(x + px, y + py), WZ - 0.1) - gz - 0.05)))
    A.add(set_, "MatWood_timber", [paint(xf(q, (x, y, gz)), (0.30, 0.26, 0.22), var=0.08, ao=0.45, ao_h=1.0, ground=gz, namp=0.1, ns=2) for q in wood + spikes])
    lp = paint(xf(leafp, (x, y, gz)), (0.17, 0.27, 0.15), var=0.1, ao=0.45, ao_h=h, ground=gz, top=0.5, namp=0.2, ns=0.9)
    A.add(set_, "MatLeaf_canopy", lp)
    if flies:  # fireflies: tiny glowing tetras just outside the crown surface (lower/outer side)
        nrm = K.vnormals(lp)
        flies_p = []
        for k in range(flies):
            i = rng.randrange(len(lp.v))
            if nrm[i][2] > 0.6:
                continue
            pos = lp.v[i] + nrm[i] * rng.uniform(0.08, 0.35)
            s = rng.uniform(0.025, 0.04)
            flies_p.append(xf(P([(0, 0, s), (s, 0, -s * 0.5), (-s * 0.5, s * 0.87, -s * 0.5), (-s * 0.5, -s * 0.87, -s * 0.5)],
                                [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]), tuple(pos)))
        A.add(set_, "MatGlow_lamp", [paint(q, (0.95, 1.0, 0.55), ao=0.0, top=0.0) for q in flies_p])
    if set_ == "battle":
        A.contact(x, y, 1.6, 0.3)


def nipah(A, x, y, seed, h=2.6, n=8, set_="battle"):
    rng = random.Random(seed)
    gz = max(ground(x, y), WZ - 0.05)
    lv = []
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.25, 0.25)
        L = h * rng.uniform(0.8, 1.15)
        up = rng.uniform(1.0, 1.6)
        path, wd = [], []
        for i in range(8):
            t = i / 7
            path.append((L * 0.55 * t * math.cos(a), L * 0.55 * t * math.sin(a), L * (up * t - 0.75 * up * t * t)))
            wd.append(0.04 + 0.28 * math.sin(math.pi * min(1.0, t * 1.1)))
        lv.append(K.strip_mesh(path, wd, fold=0.3, tears=0.6, seed=seed * 7 + k))
    A.add(set_, "MatLeaf_canopy", paint(xf(join(lv), (x, y, gz - 0.05)), NIPAH, var=0.1, ao=0.4, ao_h=1.5, ground=gz, top=0.3, namp=0.15, ns=1.5))


def sampan(A, x, y, rz, col, set_="battle", L=3.6, lamp=False):
    gz = WZ - 0.12
    hull = xf(K.perahu(L=L, W=0.85, H=0.42, seed=int(abs(x * 10))), (x, y, gz), (0, 0, rz))
    hull = tint(paint(hull, col, var=0.05, ao=0.3, ao_h=0.5, ground=gz, top=0.15),
                lambda v, c: np.where((v[:, 2] > gz + 0.36)[:, None], c * np.array([1.35, 1.3, 1.25, 1]),
                                      c * np.where((v[:, 2] < gz + 0.12)[:, None], np.array([0.4, 0.38, 0.38, 1]), 1.0)))
    A.add(set_, "MatWood_timber", hull)
    if lamp:
        p = xf(P([(L * 0.35, 0, 0)], []), (x, y, gz), (0, 0, rz)).v[0]
        A.add(set_, "MatWood_timber", paint(K.tube([(p[0], p[1], gz + 0.3), (p[0], p[1], gz + 1.25)], 0.02, seg=4), TIMBER_DK, ao=0))
        A.add(set_, "MatGlow_lamp", paint(xf(K.lathe([(0, 0), (0.05, 0.0), (0.06, 0.07), (0.035, 0.13), (0, 0.14)], seg=8), (p[0], p[1], gz + 1.05)), (1.0, 0.85, 0.55), ao=0))


def hyacinth(A):
    """floating water-hyacinth rafts drifting down the river: leaf rosettes + a few lilac flowers."""
    rng = random.Random(61)
    lv, fl = [], []
    for (cx, cy, n) in ((-3.0, 8.9, 5), (0.9, 9.6, 3), (-8.0, 9.7, 4), (4.6, 11.4, 3)):
        for k in range(n):
            px, py = cx + rng.uniform(-0.5, 0.5), cy + rng.uniform(-0.35, 0.35)
            for j in range(6):
                a = 2 * math.pi * j / 6 + rng.uniform(-0.3, 0.3)
                L = rng.uniform(0.18, 0.26)
                path = [(px, py, WZ + 0.02), (px + L * 0.5 * math.cos(a), py + L * 0.5 * math.sin(a), WZ + 0.09),
                        (px + L * math.cos(a), py + L * math.sin(a), WZ + 0.06)]
                lv.append(K.strip_mesh(path, [0.02, 0.09, 0.03], fold=-0.2, seed=k * 7 + j))
            if k % 2 == 0:
                fl.append(K.tube([(px, py, WZ + 0.05), (px + 0.02, py, WZ + 0.26)], [0.03, 0.025], seg=5))
    A.add("battle", "MatLeaf_canopy", [paint(q, (0.24, 0.42, 0.18), var=0.12, ao=0.0, top=0.35) for q in lv])
    A.add("battle", "MatLeaf_canopy", [paint(q, (0.62, 0.52, 0.86), ao=0.0, top=0.2) for q in fl])


def jetty(A):
    """pangkalan: timber deck on posts from the bank out over the river, mooring posts, a lamp."""
    wood = []
    y0, y1 = 5.3, 8.9
    n = 7
    for k in range(n + 1):
        yy = y0 + (y1 - y0) * k / n
        for sx in (-0.6, 0.6):
            wood.append(xf(K.post(1.6, 0.06, seed=k * 2 + int(sx > 0), seg=6), (JETTY_X + sx, yy, BED + 0.1)))
        wood.append(xf(K.box(1.4, 0.1, 0.08, bev=0.01), (JETTY_X, yy, 0.02)))
    for k in range(int((y1 - y0) / 0.21)):
        yy = y0 + 0.1 + k * 0.21
        wood.append(xf(K.plank(1.36, 0.19, 0.035, warp=0.005), (JETTY_X + 0.02 * math.sin(k * 3.1), yy, 0.1)))
    wood.append(xf(K.post(1.15, 0.05, seed=5), (JETTY_X + 0.62, y1, 0.08)))
    wood.append(K.tube([(JETTY_X + 0.62, y0 + 1.0, 0.75), (JETTY_X + 0.62, y1, 0.75)], 0.025, seg=5))
    A.add("battle", "MatWood_timber", [paint(q, (0.40, 0.31, 0.23) if i % 4 else (0.33, 0.25, 0.18), var=0.1, ao=0.5, ao_h=0.9, ground=WZ, namp=0.12, ns=4, stretch=(1, 1, 0.2))
                                       for i, q in enumerate(wood)])
    A.add("battle", "MatGlow_lamp", paint(xf(K.lathe([(0, 0), (0.06, 0.0), (0.07, 0.08), (0.04, 0.15), (0, 0.16)], seg=8), (JETTY_X + 0.62, y1, 1.24)), (1.0, 0.85, 0.55), ao=0))
    A.light((JETTY_X + 0.62, y1, 1.3), 14.0, (1.0, 0.7, 0.4), range_m=4)


def power_line(A):
    """modern intrusion: steel pole on the bank, three wires sagging across the river to the kampung."""
    poles = [(6.6, 5.4, "battle"), (-1.0, 15.4, "far"), (-10.0, 21.5, "far")]
    tops = []
    for (px, py, s) in poles:
        gz = ground(px, py)
        p = K.lathe([(0, 0), (0.12, 0.0), (0.09, 0.2), (0.07, 6.2), (0, 6.25)], seg=8, cap0=False)
        arm = xf(K.box(1.3, 0.08, 0.08, bev=0.01), (0, 0, 5.85))
        A.add(s, "MatMetal_iron" if s == "battle" else "MatPlaster_white", [paint(xf(q, (px, py, gz), (0, 0, 0.5)), (0.48, 0.49, 0.5), ao=0.3, ao_h=2, ground=gz) for q in (p, arm)])
        tops.append([xf(P([(dx, 0, 5.95)], []), (px, py, gz), (0, 0, 0.5)).v[0] for dx in (-0.55, 0.0, 0.55)])
    for a, b in zip(tops[:-1], tops[1:]):
        for k in range(3):
            pts = K.arc(tuple(a[k]), tuple(b[k]), -0.9, n=10)
            A.add("far", "MatPlaster_white", paint(K.tube(pts, 0.014, seg=3, cap=False), (0.12, 0.12, 0.14), ao=0))


def bush(A, x, y, h, seed, rgb=LEAF_LT, flowers=None, set_="battle"):
    gz = ground(x, y)
    b = join([xf(K.rock(h * (0.5 if i == 0 else 0.4), seed=seed * 3 + i, sub=3, amp=0.16, freq=1.5, squash=(1.15, 1, 0.8), flat=0.9),
                 (0.32 * h * (i - 0.5) * 2 if i else 0.0, 0.1 * h * i, 0.0)) for i in range(2)])
    b.v[:, 2] -= b.v[:, 2].min()
    b = paint(xf(b, (x, y, gz - 0.08)), rgb, var=0.1, ao=0.5, ao_h=h, ground=gz, top=0.4, namp=0.2, ns=3)
    A.add(set_, "MatLeaf_canopy", b)
    if flowers:
        rng = random.Random(seed)
        nrm = K.vnormals(b)
        fl = []
        for k in range(22):
            i = rng.randrange(len(b.v))
            if nrm[i][2] < -0.1:
                continue
            c = b.v[i] + nrm[i] * 0.03
            s = rng.uniform(0.07, 0.1)
            pts = [(0, 0, 0.02)] + [(s * math.cos(2 * math.pi * j / 5), s * math.sin(2 * math.pi * j / 5), 0.0) for j in range(5)]
            fl.append(xf(P(pts, [(0, 1 + j, 1 + (j + 1) % 5) for j in range(5)]), tuple(c), (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0)))
        A.add(set_, "MatLeaf_canopy", [tint(paint(q, flowers, var=0.08, ao=0.0, top=0.0), lambda v, cc: np.vstack([cc[:1] * np.array([0.5, 0.6, 0.3, 1]), cc[1:]])) for q in fl])
    A.contact(x, y, h * 0.9, 0.25)


def apron(A):
    """three low clusters on the swept yard (<=0.6 m)."""
    # grandmother's side: woven tray with bungkus, tiffin carrier, coconut basket
    tx, ty = -5.05, -1.9
    gz = ground(tx, ty)
    tray = K.lathe([(0, 0), (0.36, 0.0), (0.4, 0.05), (0.38, 0.06), (0.34, 0.015), (0, 0.015)], seg=20, cap0=False)
    A.add("battle", "MatThatch_atap", tint(paint(xf(tray, (tx, ty, gz + 0.005)), (0.62, 0.50, 0.32), ao=0.2, ao_h=0.05, ground=gz),
                                           lambda v, c: c * (0.86 + 0.14 * ((np.floor((v[:, 0] + v[:, 1]) * 18) + np.floor((v[:, 0] - v[:, 1]) * 18)) % 2))[:, None]))
    rng = random.Random(4)
    for k in range(7):
        a = 2 * math.pi * k / 7
        bx, by = tx + 0.2 * math.cos(a), ty + 0.2 * math.sin(a)
        A.add("battle", "MatLeaf_canopy", paint(xf(P([(-0.06, -0.05, 0), (0.06, -0.05, 0), (0.0, 0.06, 0), (0, 0, 0.09)], [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)]),
                                                   (bx, by, gz + 0.02), (0, 0, rng.uniform(0, 6))), (0.25, 0.44, 0.16), var=0.12, ao=0.0, top=0.25))
    A.contact(tx, ty, 0.6, 0.3)
    cx, cy = -5.35, -0.95
    gz = ground(cx, cy)
    tif = []
    for k in range(3):
        tif.append(xf(K.lathe([(0, 0), (0.1, 0.0), (0.11, 0.02), (0.11, 0.1), (0.1, 0.11), (0, 0.11)], seg=14), (cx, cy, gz + k * 0.11)))
    tif.append(K.tube(K.arc((cx - 0.11, cy, gz + 0.3), (cx + 0.11, cy, gz + 0.3), 0.14, n=6), 0.008, seg=4))
    A.add("battle", "MatMetal_iron", [tint(paint(q, (0.30, 0.52, 0.42), var=0.0, ao=0.3, ao_h=0.2, ground=gz, top=0.2),
                                           lambda v, c: c * np.where((np.abs(((v[:, 2] - gz) % 0.11) - 0.055) > 0.045)[:, None], np.array([1.6, 1.4, 1.2, 1]), 1.0)) for q in tif])
    A.contact(cx, cy, 0.3, 0.3)
    bx, by = -4.75, -3.0
    gz = ground(bx, by)
    A.add("battle", "MatThatch_atap", tint(paint(on_ground(K.basket(0.2, 0.22), bx, by), (0.50, 0.38, 0.22), ao=0.4, ao_h=0.2, ground=gz),
                                           lambda v, c: c * (0.84 + 0.16 * ((np.floor(v[:, 2] * 40) + np.floor(np.arctan2(v[:, 1] - by, v[:, 0] - bx) * 5)) % 2))[:, None]))
    for k in range(4):
        a = 2 * math.pi * k / 4
        A.add("battle", "MatRock_laterite", paint(xf(K.rock(0.085, seed=40 + k, sub=2, amp=0.1, squash=(1, 0.9, 1.05)), (bx + 0.07 * math.cos(a), by + 0.07 * math.sin(a), gz + 0.16)),
                                                  (0.40, 0.27, 0.15), ao=0.3, ao_h=0.1, ground=gz + 0.15, top=0.3, namp=0.2, ns=12))
    A.add("battle", "MatRock_laterite", paint(xf(K.rock(0.09, seed=48, sub=2, amp=0.1), (bx + 0.3, by - 0.12, gz - 0.01)), (0.40, 0.27, 0.15), ao=0.3, ao_h=0.1, ground=gz, top=0.3))
    A.contact(bx, by, 0.45, 0.3)
    # the lidi broom that swept the yard + selipar by the far-left apron
    lx, ly = -3.4, 3.95
    gz = ground(lx, ly)
    sticks = []
    for k in range(18):
        a = (k - 9) * 0.035
        sticks.append(K.tube([(lx, ly, gz + 0.03), (lx + 0.95 * math.cos(0.5 + a), ly + 0.95 * math.sin(0.5 + a), gz + 0.02)], 0.006, seg=3, cap=False))
    A.add("battle", "MatThatch_atap", [paint(q, (0.70, 0.60, 0.38), var=0.08, ao=0.0) for q in sticks])
    A.add("battle", "MatCloth_batik", paint(xf(K.box(0.07, 0.07, 0.05, bev=0.015), (lx + 0.06, ly + 0.03, gz + 0.02), (0, 0, 0.5)), (0.55, 0.15, 0.12), ao=0))
    for k, (sx, sy, rz) in enumerate(((-2.75, 4.35, 0.3), (-2.55, 4.45, 0.15))):
        A.add("battle", "MatCloth_batik", paint(xf(K.box(0.12, 0.27, 0.025, bev=0.01), (sx, sy, ground(sx, sy) + 0.003), (0, 0, rz)), (0.20, 0.36, 0.62), ao=0.0))
    # Danial's corner: coiled string, spare top, water bottle
    dx, dy = 4.85, -2.2
    gz = ground(dx, dy)
    A.add("battle", "MatThatch_atap", paint(on_ground(K.rope_coil(0.22, 0.012, turns=4, layers=1, seed=3), dx, dy, 0.0), (0.82, 0.76, 0.62), ao=0.2, ao_h=0.05, ground=gz))
    top = K.lathe([(0, 0), (0.02, 0.01), (0.15, 0.12), (0.17, 0.17), (0.12, 0.26), (0.03, 0.3), (0, 0.31)], seg=16)
    A.add("battle", "MatWood_timber", paint(xf(top, (dx + 0.45, dy + 0.35, gz + 0.12), (1.3, 0, 0.8)), (0.40, 0.20, 0.10), ao=0.2, ao_h=0.1, ground=gz))
    A.add("battle", "MatMetal_iron", paint(xf(K.lathe([(0, 0), (0.035, 0), (0.035, 0.17), (0.015, 0.21), (0, 0.21)], seg=10), (dx - 0.3, dy + 0.45, gz)), (0.45, 0.62, 0.70), ao=0.2, ao_h=0.05, ground=gz))
    A.contact(dx, dy, 0.5, 0.3)


def litter(A):
    rng = random.Random(41)
    n = 0
    while n < 70:
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(6.0, 8.0)
        x, y = r * math.cos(a), r * math.sin(a)
        if path_dist(x, y) < 0.3 or river(x, y)[0] < river(x, y)[1] + 2.5 or east(x, y) > 0.2:
            continue
        n += 1
        gz = ground(x, y)
        if n % 2:
            A.add("battle", "MatRock_laterite", paint(xf(K.rock(rng.uniform(0.03, 0.08), seed=900 + n, sub=1, squash=(1, 0.8, 0.55)), (x, y, gz - 0.01)),
                                                      (0.50, 0.32, 0.22) if n % 3 else (0.36, 0.30, 0.25), ao=0.3, ao_h=0.04, ground=gz))
        else:  # fallen rain-tree leaves
            A.add("battle", "MatLeaf_canopy", paint(xf(K.box(0.06, 0.03, 0.004, bev=0.0), (x, y, gz + 0.004), (0, 0, rng.uniform(0, 3))), (0.55, 0.45, 0.22), ao=0.0, top=0.0))


# ---------------------------------------------------------------- far set
def rumah(A, x, y, rz, s=1.0, lit=True, set_="far", wall=(0.50, 0.36, 0.24), roof=(0.46, 0.30, 0.22)):
    """rumah kampung Selangor: stilts on footings, timber walls, louvred windows (lit), long gable roof with
    crossed gable boards, lower serambi in front, tangga."""
    W, D, FH, WH = 7.0, 4.6, 1.5, 2.3
    bv = 0.0 if set_ == "far" else 0.02  # far: unbevelled boxes (12 tris)
    wood, roofs, glow = [], [], []
    for sx in (-0.47, -0.16, 0.16, 0.47):
        for sy in (-0.45, 0.0, 0.45):
            wood.append(xf(K.box(0.18, 0.18, FH, bev=bv), (sx * W, sy * D, -0.2)))
    wood.append(xf(K.box(W + 0.3, D + 0.3, 0.14, bev=bv), (0, 0, FH)))
    wood.append(xf(K.box(W, D, WH, bev=bv), (0, 0, FH + 0.14)))
    for sx in (-0.32, -0.1, 0.12, 0.34):  # windows on the front wall
        wood.append(xf(K.box(0.85, 0.08, 1.15, bev=bv), (sx * W, -D / 2 - 0.04, FH + 0.6)))
        glow.append(xf(K.box(0.6, 0.06, 0.9, bev=0.0), (sx * W, -D / 2 - 0.08, FH + 0.72)))
        wood += [xf(K.box(0.04, 0.04, 0.9, bev=0.0), (sx * W, -D / 2 - 0.13, FH + 0.72)), xf(K.box(0.6, 0.04, 0.04, bev=0.0), (sx * W, -D / 2 - 0.13, FH + 1.27))]   # mullion + transom
    roofs.append(xf(K.thatch_roof(W, D, 2.2, courses=3, over=0.55, seed=11, tooth=0.0, cw=0.7), (0, 0, FH + 0.14 + WH)))
    for sx in (-1, 1):  # crossed gable boards (sulur bayung)
        e = sx * (W / 2 + 0.55)
        wood.append(K.tube([(e, -D / 2 - 0.4, FH + WH + 0.1), (e, 0.25, FH + WH + 2.55)], 0.06, seg=4))
        wood.append(K.tube([(e, D / 2 + 0.4, FH + WH + 0.1), (e, -0.25, FH + WH + 2.55)], 0.06, seg=4))
    # serambi (front verandah) with a lower lean-to roof and railing
    wood.append(xf(K.box(W * 0.6, 1.8, 0.12, bev=bv), (-W * 0.15, -D / 2 - 0.9, FH - 0.25)))
    for sx in (-0.42, 0.12):
        wood.append(xf(K.box(0.12, 0.12, FH + 1.9, bev=bv), (sx * W, -D / 2 - 1.7, -0.2)))
    sr = K.thatch_roof(W * 0.62, 2.0, 0.5, courses=2, over=0.3, seed=12, tooth=0.0, cw=0.7)
    roofs.append(xf(sr, (-W * 0.15, -D / 2 - 0.95, FH + 1.75)))
    wood.append(xf(K.box(W * 0.58, 0.06, 0.6, bev=bv), (-W * 0.15, -D / 2 - 1.75, FH - 0.13)))
    for k in range(6):  # tangga
        t = k / 5
        wood.append(xf(K.box(1.0, 0.25, 0.06, bev=bv), (W * 0.18, -D / 2 - 1.3 - 1.4 * t, FH - 0.3 - (FH - 0.2) * t)))
    if lit:
        glow.append(xf(K.box(1.0, 0.06, 1.6, bev=0.0), (-W * 0.15, -D / 2 - 0.06, FH + 0.15)))  # open door
        wood += [xf(K.box(0.06, 0.06, 1.66, bev=0.0), (-W * 0.15 + sx * 0.52, -D / 2 - 0.1, FH + 0.15)) for sx in (-1, 1)]
        wood.append(xf(K.box(1.1, 0.06, 0.06, bev=0.0), (-W * 0.15, -D / 2 - 0.1, FH + 1.75)))
    put = lambda lst: [xf(q, (x, y, ground(x, y)), (0, 0, rz), s) for q in lst]
    A.add(set_, "MatWood_timber", [paint(q, wall if i % 5 else TIMBER_DK, var=0.06, ao=0.4, ao_h=2.5, ground=ground(x, y), namp=0.1, ns=2) for i, q in enumerate(put(wood))])
    A.add(set_, "MatWood_timber", [paint(q, roof, var=0.05, top=0.25, namp=0.15, ns=1.2) for q in put(roofs)])
    if lit:
        A.add(set_, "MatGlow_lamp", [glow_grad(paint(q, (1.0, 0.8, 0.5), ao=0.0)) for q in put(glow)])


def palm(A, x, y, h, seed, set_="far"):
    tr, lf = K.coconut_palm(h, seed=seed, fronds=8)
    gz = ground(x, y) - 0.1
    A.add(set_, "MatWood_timber", paint(xf(tr, (x, y, gz)), (0.42, 0.36, 0.28), ao=0.3, ao_h=2, ground=gz))
    A.add(set_, "MatLeaf_canopy", paint(xf(lf, (x, y, gz)), (0.24, 0.36, 0.16), var=0.1, ao=0.0, top=0.35, namp=0.15, ns=1))


def lighthouse(A, x, y, gz):
    """Altingsburg lighthouse on Bukit Melawati: white tapering tower, gallery, lit lantern room, cap."""
    tower = K.lathe([(0.0, -0.5), (1.5, -0.5), (1.5, 0.6), (1.25, 0.7), (0.95, 7.6), (1.35, 7.7), (1.35, 7.95), (0.0, 7.95)], seg=24, cap0=False)
    lantern = K.lathe([(0.0, 7.95), (0.8, 7.95), (0.8, 9.0), (0.0, 9.0)], seg=16, cap0=False, cap1=False)
    cap = K.lathe([(0.0, 9.0), (1.0, 9.0), (0.95, 9.12), (0.35, 9.75), (0.12, 9.9), (0.1, 10.3), (0.0, 10.35)], seg=16, cap0=False)
    rail = K.lathe([(1.32, 7.95), (1.34, 7.95), (1.34, 8.35), (1.32, 8.35)], seg=24, cap0=False, cap1=False)
    keeper = xf(K.box(3.4, 2.4, 2.2, bev=0.04), (2.6, -0.8, -0.3))
    keeper_roof = xf(K.thatch_roof(3.4, 2.4, 0.9, courses=2, over=0.3, seed=21, tooth=0.0, cw=0.8), (2.6, -0.8, 1.9))
    A.add("far", "MatPlaster_white", [paint(xf(q, (x, y, gz)), (0.93, 0.91, 0.88), var=0.02, ao=0.25, ao_h=3.0, ground=gz, top=0.12) for q in (tower, keeper)])
    A.add("far", "MatPlaster_white", [paint(xf(q, (x, y, gz)), (0.16, 0.16, 0.18), ao=0.0) for q in (cap, rail)])
    A.add("far", "MatPlaster_white", paint(xf(keeper_roof, (x, y, gz)), (0.60, 0.26, 0.18), top=0.25))
    A.add("far", "MatGlow_lamp", paint(xf(lantern, (x, y, gz)), (1.0, 0.85, 0.55), ao=0.0))
    A.light((x, y, gz + 8.5), 160.0, (1.0, 0.75, 0.45), range_m=14)


def melawati(A):
    hx, hy, R, H = HILL
    d = dome(R, H, seed=5, seg=56, rings=14, base=-1.5, lump=0.9, lump_s=0.32, squash=(1.1, 0.9), power=1.3)
    d = xf(d, (hx, hy, 0))

    def hcol(v, c):
        zt = np.clip(v[:, 2] / H, 0, 1)
        n1 = np.array([nz(a, b, cc, 0.3, 31) for a, b, cc in v])
        base = np.array(LEAF)[None, :] * (0.85 + 0.25 * zt[:, None]) * (1 + 0.18 * n1[:, None])
        lawn = np.array((0.36, 0.48, 0.22))[None, :]
        k = (smooth01(0.82, 0.95, zt) + 0.5 * smooth01(0.4, 0.7, n1))[:, None].clip(0, 1)
        return np.column_stack([base * (1 - k) + lawn * k, np.ones(len(v))])
    d.c = hcol(d.v, None)
    A.add("far", "MatLeaf_canopy", d)
    top = d.v[np.argmax(d.v[:, 2])]
    lighthouse(A, float(top[0]) - 1.0, float(top[1]) - 1.5, float(top[2]) - 0.5)
    for k, (dx, dy) in enumerate(((-6.5, -4.5), (5.5, -5.0), (-2.5, -9.0), (7.0, 2.5))):
        px, py = hx + dx, hy + dy
        rr = math.hypot(dx / 1.1, dy / 0.9) / R
        pz = -1.5 + (H + 1.5) * math.cos(math.pi * 0.5 * min(1.0, rr)) ** 1.3
        trunk = K.tube([(px, py, pz - 0.5), (px + 0.2, py, pz + 2.5)], [0.35, 0.25], seg=6)
        A.add("far", "MatWood_timber", paint(trunk, (0.30, 0.25, 0.2), ao=0))
        A.add("far", "MatLeaf_canopy", paint(xf(K.canopy(3.2, seed=80 + k, lumps=3, sub=2, squash=0.45, spread=0.7), (px, py, pz + 2.6)),
                                             (0.20, 0.32, 0.15), var=0.1, ao=0.4, ao_h=3, ground=pz + 2, top=0.5, namp=0.2, ns=0.6))


def city(A):
    """the modern skyline beyond the kampung: towers with lit floor bands, a domed mosque, a crane."""
    rng = random.Random(23)
    towers = []
    for k in range(13):
        yaw = -30 + 27 * k / 12 + rng.uniform(-1.0, 1.0)
        dist = rng.uniform(175, 215)
        a = math.radians(yaw)
        x, y = VCAM[0] + dist * math.sin(a), VCAM[1] + dist * math.cos(a)
        h = rng.uniform(16, 34) * (1.35 if k in (5, 6, 9) else 1.0)
        w = rng.uniform(7, 12)
        towers.append((x, y, h, w, k))
    for (x, y, h, w, k) in towers:
        body = [xf(K.box(w, w * 0.8, h, bev=0.2), (x, y, -1))]
        if k % 3 == 0:  # setback crown
            body.append(xf(K.box(w * 0.6, w * 0.5, h * 0.18, bev=0.15), (x, y, h - 1)))
            body.append(K.tube([(x, y, h - 1 + h * 0.18), (x, y, h + h * 0.4)], [0.3, 0.05], seg=4))
        col = [(0.42, 0.45, 0.58), (0.52, 0.52, 0.60), (0.36, 0.42, 0.52), (0.58, 0.56, 0.62)][k % 4]
        A.add("far", "MatPlaster_white", [face_vista(paint(xf(q, (-x, -y, 0)), col, var=0.05, ao=0.0, top=0.2), x, y, 0) for q in body])
        bands = []
        for f in range(int(h / 2.4)):
            if rng.random() < 0.45:
                z = 1.0 + f * 2.4
                ww = w * rng.uniform(0.3, 0.92)
                bands.append(xf(K.box(ww, 0.1, 0.55, bev=0.0), (rng.uniform(-0.5, 0.5) * (w - ww), -w * 0.4 - 0.06, z)))
        if bands:
            A.add("far", "MatGlow_lamp", [paint(face_vista(q, x, y, 0), (1.0, 0.8, 0.5), ao=0.0) for q in bands])
    # domed mosque (Shah Alam echo): blue dome + four minarets
    a = math.radians(-12.0)
    mx, my = VCAM[0] + 150 * math.sin(a), VCAM[1] + 150 * math.cos(a)
    dome_ = K.lathe([(0, 0), (8.0, 0.0), (8.2, 2.5), (7.4, 6.5), (5.0, 9.8), (2.0, 11.5), (0.3, 12.0), (0.2, 13.5), (0, 13.6)], seg=28, cap0=False)
    drum = K.lathe([(0, -1), (9.5, -1), (9.5, 3.0), (0, 3.0)], seg=28, cap0=False)
    A.add("far", "MatPlaster_white", paint(xf(drum, (mx, my, 0)), (0.82, 0.80, 0.78), ao=0.0, top=0.2))
    A.add("far", "MatPlaster_white", paint(xf(dome_, (mx, my, 3.0)), (0.22, 0.42, 0.72), var=0.02, ao=0.0, top=0.35))
    for k in range(4):
        aa = math.radians(45 + 90 * k)
        px, py = mx + 16 * math.cos(aa), my + 16 * math.sin(aa)
        mn = K.lathe([(0, -1), (1.1, -1), (1.0, 26.0), (1.6, 26.5), (1.6, 27.3), (0.8, 27.4), (0.7, 31.0), (0.0, 33.5)], seg=10, cap0=False)
        A.add("far", "MatPlaster_white", paint(xf(mn, (px, py, 0)), (0.84, 0.82, 0.80), ao=0.0, top=0.2))
    # construction crane (modern)
    a = math.radians(-4.0)
    cx, cy = VCAM[0] + 190 * math.sin(a), VCAM[1] + 190 * math.cos(a)
    mast = K.tube([(cx, cy, 0), (cx, cy, 44)], 0.7, seg=4)
    jib = K.tube([(cx - 10, cy, 44), (cx + 26, cy, 44)], 0.45, seg=4)
    A.add("far", "MatPlaster_white", [paint(q, (0.72, 0.58, 0.32), ao=0.0) for q in (mast, jib)])


def backdrop(A):
    # ridges: near forested bank behind the city base, mid hills, far Titiwangsa range (yaw left of the estuary)
    A.add("far", "MatLeaf_canopy", ridge_layer(72, -60, -3, -1.0, 2.5, 4.5, 40, (0.20, 0.30, 0.16), (0.13, 0.18, 0.12), n=90, freq=5.0, crowns=1.4, lean=0.5))
    A.add("far", "MatLeaf_canopy", ridge_layer(128, -60, -1, -1.5, 2.5, 6.5, 41, (0.22, 0.26, 0.24), (0.14, 0.16, 0.17), n=90, freq=4.0, crowns=1.2, lean=0.4))
    A.add("far", "MatLeaf_canopy", ridge_layer(245, -60, 3, -3.0, 6.0, 16.0, 42, (0.36, 0.34, 0.46), (0.26, 0.25, 0.36), n=70, freq=3.0, crowns=1.0))
    A.add("far", "MatLeaf_canopy", ridge_layer(470, -62, 7, -6.0, 18.0, 42.0, 43, (0.52, 0.45, 0.60), (0.44, 0.39, 0.54), n=60, freq=2.4,
                                                peaks=[(-14, 12, 6), (-36, 8, 5)]))
    # dusk cloud flats: lit warm on top, lavender underneath, layered in depth
    rng = random.Random(51)
    for k, (yaw, dist, el, w, h) in enumerate(((-45, 260, 9.0, 110, 20), (-18, 300, 12.5, 150, 24), (8, 280, 10.0, 90, 15), (26, 240, 13.5, 100, 18),
                                                (-30, 220, 15.5, 70, 11), (16, 330, 6.0, 140, 16), (-5, 340, 5.0, 160, 14), (40, 200, 7.0, 60, 10),
                                                (-55, 300, 4.5, 120, 14))):
        a = math.radians(yaw)
        x, y = VCAM[0] + dist * math.sin(a), VCAM[1] + dist * math.cos(a)
        z = 3.2 + dist * math.tan(math.radians(el))
        lit = (1.0, 0.82, 0.62) if el < 8 else (1.0, 0.70, 0.66)
        shade = (0.30, 0.27, 0.48) if el > 8 else (0.48, 0.36, 0.50)
        A.add("far", "MatPlaster_white", face_vista(cloud_flat(w, h, seed=60 + k, lit=lit, shade=shade, n=30, rim=h * 0.08), x, y, z))


def far_bank(A):
    rumah(A, HOUSE[0], HOUSE[1], 0.06)
    rumah(A, -14.5, 24.0, -0.2, s=0.85, lit=True, wall=(0.56, 0.48, 0.38), roof=(0.40, 0.33, 0.30))
    A.light((HOUSE[0] - 1.0, HOUSE[1] - 3.0, 2.6), 60.0, (1.0, 0.72, 0.42), range_m=8)
    for k, (x, y, h) in enumerate(((-10.0, 16.8, 8.5), (-2.0, 21.5, 9.5), (0.5, 17.2, 7.0), (-12.0, 19.5, 7.5),
                                   (-8.0, 27.0, 10.0), (2.5, 28.0, 8.5))):
        palm(A, x, y, h, seed=700 + k)
    for k, (x, y, h) in enumerate(((-18, 15.0, 5.0), (-25, 14.6, 5.6), (-32, 14.8, 4.8), (-13.0, 15.2, 4.2), (3.4, 22, 5.0), (2.0, 34, 5.5),
                                   (14.6, 19.0, 4.8), (16.0, 26.0, 5.5))):
        berembang(A, x, y, h, seed=300 + k, flies=16, set_="far")
    for k, (x, y) in enumerate(((-7.5, 15.0), (-14, 15.5), (1.8, 15.6), (3.8, 27.5))):
        nipah(A, x, y, seed=40 + k, h=2.8, n=7, set_="far")
    for k, (x, y, rz, col) in enumerate(((-4.0, 14.2, 0.3, (0.24, 0.42, 0.56)), (6.0, 30.0, 1.4, (0.60, 0.22, 0.16)))):
        sampan(A, x, y, rz, col, set_="far", L=3.8 if k else 3.4)


def water(A):
    """river sheet along the centreline (covers every culled bank face), estuary + sea plane."""
    path = [(x, y) for (x, y) in RC if y < 140]
    for (seg_from, seg_to, set_) in ((0, 3, "far"), (2, 7, "battle"), (6, len(path), "far")):
        pts = path[seg_from:seg_to]
        out = []
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            k = max(1, int(L / (1.5 if set_ == "battle" else 8.0)))
            out += [(x0 + (x1 - x0) * i / k, y0 + (y1 - y0) * i / k) for i in range(k)]
        out.append(pts[-1])
        v, f, c = [], [], []
        for i, (x, y) in enumerate(out):
            a = out[max(0, i - 1)]
            b = out[min(len(out) - 1, i + 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]
            l = math.hypot(tx, ty) or 1.0
            nx_, ny_ = -ty / l, tx / l
            hw = river(x, y)[1] + 1.6
            for o, col in ((-hw, RIVER_EDGE), (-hw * 0.6, RIVER), (0.0, RIVER), (hw * 0.6, RIVER), (hw, RIVER_EDGE)):
                v.append((x + nx_ * o, y + ny_ * o, WZ))
                c.append(list(col) + [1.0])
        for i in range(len(out) - 1):
            for j in range(4):
                a = i * 5 + j
                f.append((a, a + 5, a + 6, a + 1))
        # the near-bank strip gets a faint foam/ripple line where the river laps the mud
        A.add(set_, "MatWater_river", P(v, f, c))
    # sea beyond the estuary mouth, out to the horizon
    p = P([(-40, 120, WZ - 0.08), (300, 60, WZ - 0.08), (3000, 1500, WZ - 0.08), (-600, 3000, WZ - 0.08)], [(0, 1, 2, 3)])
    p.c = np.tile(list(SEA) + [1.0], (4, 1))
    A.add("far", "MatWater_river", p)


# ================================================================ build
def build(A):
    for name in ("MatGround_yard", "MatMud_bank", "MatWater_river", "MatWood_timber", "MatThatch_atap", "MatLeaf_canopy",
                 "MatCloth_batik", "MatMetal_iron", "MatRock_laterite", "MatPlaster_white"):
        A.mat(name)
    A.mat("MatGlow_lamp", emit=(1.0, 0.78, 0.45), estr=1.2)

    # ---- left flank: grandmother's stall, bicycle, batik racks, dye vats, wax table
    gerai(A, STALL[0], STALL[1], math.pi / 2 + 0.12)
    bicycle(A, -6.3, -4.9, 0.55)
    batik_rack(A, -7.9, -0.5, -8.15, 3.6, [0, 1, 2], seed=1)
    batik_rack(A, -10.0, 1.2, -10.4, 5.6, [3, 4, 1], seed=2, h=2.9)
    batik_rack(A, -6.9, 5.7, -9.0, 6.6, [2, 0], seed=3, h=2.5)
    for k, (vx, vy, col) in enumerate(((-6.7, 3.9, BATIK["indigo"]), (-6.4, 4.65, (0.50, 0.16, 0.12)))):
        bw, bm = K.barrel(0.3, 0.6)
        A.add("battle", "MatWood_timber", paint(on_ground(bw, vx, vy, 0.02), (0.40, 0.30, 0.22), var=0.06, ao=0.45, ao_h=0.5, ground=ground(vx, vy), namp=0.1, ns=4))
        A.add("battle", "MatMetal_iron", paint(on_ground(bm, vx, vy, 0.02), IRON, ao=0.0))
        A.add("battle", "MatWater_river", paint(xf(K.lathe([(0, 0), (0.25, 0)], seg=14, cap0=False, cap1=False), (vx, vy, ground(vx, vy) + 0.52)), col, ao=0.0, top=0.0))
        A.contact(vx, vy, 0.6, 0.3)
    wx, wy = -6.6, 1.55  # wax table: low bench, small stove, wax pot (canting work)
    gz = ground(wx, wy)
    tbl = [xf(K.box(0.9, 0.5, 0.04, bev=0.01), (wx, wy, gz + 0.42))] + [xf(K.box(0.05, 0.05, 0.42, bev=0.0), (wx + sx, wy + sy, gz)) for sx in (-0.4, 0.4) for sy in (-0.2, 0.2)]
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, ao=0.35, ao_h=0.4, ground=gz) for q in tbl])
    A.add("battle", "MatRock_laterite", paint(xf(K.jar(0.14, 0.2), (wx - 0.2, wy, gz + 0.46)), (0.45, 0.25, 0.15), ao=0.2, ao_h=0.1, ground=gz + 0.46))
    A.add("battle", "MatGlow_lamp", paint(xf(K.lathe([(0, 0), (0.09, 0), (0.09, 0.02), (0, 0.02)], seg=10), (wx - 0.2, wy, gz + 0.45)), (1.0, 0.5, 0.2), ao=0))
    A.add("battle", "MatMetal_iron", paint(xf(K.lathe([(0, 0), (0.08, 0), (0.09, 0.07), (0.08, 0.08), (0, 0.08)], seg=10), (wx - 0.2, wy, gz + 0.66)), (0.30, 0.28, 0.26), ao=0))
    A.add("battle", "MatCloth_batik", xf(batik_panel(0.7, 0.4, 1, 91, sway=0.0, nxs=8, nzs=5), (wx + 0.18, wy + 0.2, gz + 0.47), (math.pi / 2, 0, 0.1)))
    A.light((wx - 0.2, wy, gz + 0.8), 5.0, (1.0, 0.55, 0.25), range_m=2)
    A.contact(wx, wy, 0.8, 0.3)
    st, lv = K.banana(2.7, seed=3, leaves=6)
    for k, (bx, by, s) in enumerate(((-12.2, -2.6, 1.0), (-11.6, -3.9, 0.75))):
        A.add("battle", "MatLeaf_canopy", paint(on_ground(xf(lv, s=s), bx, by, 0.05), (0.30, 0.46, 0.18), var=0.08, ao=0.35, ao_h=2.2, ground=ground(bx, by), top=0.25, namp=0.15, ns=2))
        A.add("battle", "MatWood_timber", paint(on_ground(xf(st, s=s), bx, by, 0.05), (0.40, 0.42, 0.24), ao=0.4, ao_h=1.2, ground=ground(bx, by)))
    palm(A, -12.4, 7.0, 7.5, seed=91, set_="battle")

    # ---- right flank: Melawati foot -- terrace wall, steps, cannon, lamp, rain tree
    laterite_wall(A, [(7.25, -2.4), (7.05, 0.9)], 0.78, seed=5)
    laterite_wall(A, [(7.15, 2.35), (7.6, 5.0), (8.3, 6.0)], 0.78, seed=6)
    for k in range(4):  # steps up to the terrace: each tread clearly proud of the slope
        sx_ = 7.05 + k * 0.38
        top = max(0.12 + k * 0.17, max(ground(sx_ + dx, 1.62 + dy) for dx in (-0.2, 0.2) for dy in (-0.6, 0.6)) + 0.1)
        A.add("battle", "MatRock_laterite", paint(xf(K.box(0.44, 1.3, top + 0.45, bev=0.035, seed=k), (sx_, 1.62, -0.45)),
                                                  (0.66, 0.50, 0.40) if k % 2 else (0.58, 0.44, 0.35), var=0.04, ao=0.55, ao_h=0.17, ground=top - 0.17, top=0.6, namp=0.25, ns=5))
    cannon(A, TERRACE[0] - 0.2, TERRACE[1] + 0.2, 1.05, TERRACE[3], s=1.3)
    for k, (bx, by, bz) in enumerate(((8.4, 1.75, 0), (8.62, 1.75, 0), (8.84, 1.75, 0), (8.51, 1.94, 0), (8.73, 1.94, 0), (8.62, 1.85, 0.17))):
        A.add("battle", "MatMetal_iron", paint(xf(K.rock(0.1, seed=80 + k, sub=2, amp=0.03, squash=(1, 1, 1)), (bx, by, ground(bx, by) + bz - 0.02)), IRON, ao=0.2, ao_h=0.15, ground=ground(bx, by), top=0.3))
    street_lamp(A, 7.4, -1.5, -0.55)
    rain_tree(A, 13.9, 1.6, 8.0, seed=7, away=0.1)
    for k, (rx, ry) in enumerate(((10.6, -0.6), (11.4, 1.0), (9.0, 5.6))):
        A.add("battle", "MatRock_laterite", paint(on_ground(K.rock(0.35 + 0.1 * k, seed=120 + k, sub=3, squash=(1.2, 1, 0.6)), rx, ry, 0.08), (0.48, 0.32, 0.24),
                                                  ao=0.4, ao_h=0.3, ground=ground(rx, ry), namp=0.2, ns=3))
        A.contact(rx, ry, 0.8, 0.3)

    # ---- far band: bank, jetty, sampans, nipah, berembang + fireflies, nets, power pole
    jetty(A)
    sampan(A, JETTY_X + 1.35, 7.6, math.pi / 2 + 0.06, (0.20, 0.40, 0.55), lamp=True)
    sampan(A, -1.2, 10.3, 0.2, (0.62, 0.24, 0.16))
    sampan(A, 5.2, 13.2, 1.1, (0.22, 0.46, 0.30), set_="far")
    berembang(A, -6.2, 7.6, 5.5, seed=11, flies=60)
    berembang(A, 6.4, 9.6, 6.0, seed=12, flies=60)
    hyacinth(A)
    nipah(A, -3.6, 6.9, seed=1)
    nipah(A, -9.4, 7.6, seed=2, h=2.3)
    nipah(A, 4.6, 7.4, seed=3, h=2.2, n=7)
    nipah(A, 8.0, 12.5, seed=4, h=2.6)
    hx, hy = -1.4, 5.55  # upturned sampan on the bank
    hull = xf(K.perahu(L=2.8, W=0.7, H=0.32, seed=9), (0, 0, -0.34), (math.pi, 0, 0))
    A.add("battle", "MatWood_timber", paint(xf(hull, (hx, hy, ground(hx, hy) + 0.02), (0, 0, 0.15)), (0.36, 0.40, 0.42), var=0.06, ao=0.4, ao_h=0.4, ground=ground(hx, hy), namp=0.15, ns=3))
    A.contact(hx, hy, 1.4, 0.35)
    for k, (px, py) in enumerate(((-5.1, 5.5), (-4.0, 6.3))):  # net drying on two poles
        A.add("battle", "MatWood_timber", paint(on_ground(K.post(1.5, 0.035, seed=30 + k), px, py, 0.2), TIMBER_DK, ao=0.2, ao_h=0.4, ground=ground(px, py)))
    net = K.grid(1.35, 1.2, 8, 7)
    net.v = np.column_stack([net.v[:, 0], 0.03 * np.sin(net.v[:, 0] * 6), net.v[:, 1] * 0.95 - 0.02 * net.v[:, 0] ** 2])
    net = xf(net, (-4.55, 5.9, ground(-4.55, 5.9) + 0.75), (0, 0, math.atan2(0.8, 1.1)))
    A.add("battle", "MatCloth_batik", tint(paint(net, (0.42, 0.50, 0.46), ao=0.0, top=0.0),
                                           lambda v, c: c * (0.6 + 0.4 * ((np.floor(v[:, 2] * 22) + np.floor((v[:, 0] + v[:, 1]) * 18)) % 2))[:, None]))
    power_line(A)
    apron(A)
    litter(A)
    # ---- near strip (vista foreground, <=1.2 m): hibiscus hedge, bench, potted plant
    for k, (bx, by) in enumerate(((-4.2, -6.5), (-2.6, -6.7), (2.2, -6.6), (3.9, -6.3))):
        bush(A, bx, by, 0.95 + 0.1 * (k % 2), seed=200 + k, flowers=(0.80, 0.10, 0.12))
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, ao=0.35, ao_h=0.4, ground=ground(-0.2, -5.6)) for q in
                                       [xf(K.plank(1.5, 0.32, 0.04), (-0.2, -5.6, ground(-0.2, -5.6) + 0.42))] +
                                       [xf(K.box(0.06, 0.28, 0.42, bev=0.0), (-0.2 + sx, -5.6, ground(-0.2, -5.6))) for sx in (-0.6, 0.6)]])
    A.contact(-0.2, -5.6, 1.0, 0.25)

    # ---- terrain (after props so contact pools land)
    A.terrain(ground, gcolor, kind=gkind, rin=4.5, rout=140.0, split=23.0, cull=gcull, seed=1)
    water(A)

    # ---- scatter: yard-edge grass, slope grass, bank reeds
    rng = random.Random(3)
    for k in range(170):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(6.8, 14.0)
        x, y = r * math.cos(a), r * math.sin(a)
        d, hw = river(x, y)
        if d < hw + 2.4 or path_dist(x, y) < 0.6 or not visible(x, y) or in_water(x, y) or (x < -6.2 and -4 < y < 6.8 and r < 10.5):
            continue
        A.scatter_patch("Grass", 30, x, y, rng.uniform(0.6, 1.3), ground, GRASS_TINT, seed=k)
    for k in range(40):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(6.0, 7.6)
        x, y = r * math.cos(a), r * math.sin(a)
        if path_dist(x, y) < 0.6 or river(x, y)[0] < river(x, y)[1] + 2.5 or x < -6.0:
            continue
        A.scatter_patch("Grass", 24, x, y, rng.uniform(0.3, 0.6), ground, (0.44, 0.50, 0.24), seed=100 + k)
    for k in range(60):  # sparse tufts where the swept laman meets the grass
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(5.9, 7.0)
        x, y = r * math.cos(a), r * math.sin(a)
        if path_dist(x, y) < 0.5 or river(x, y)[0] < river(x, y)[1] + 2.5:
            continue
        A.scatter_patch("Grass", 14, x, y, rng.uniform(0.25, 0.5), ground, (0.46, 0.50, 0.26), seed=400 + k)
    for k in range(24):
        x = rng.uniform(-14, 6)
        d0 = river(x, 7.0)
        y = 9.4 - d0[1] - rng.uniform(0.9, 1.6)
        A.scatter_patch("Reed", 9, x, y, rng.uniform(0.5, 0.9), lambda a, b: max(ground(a, b), WZ), (0.40, 0.46, 0.22), seed=200 + k)

    # ---- far set
    far_bank(A)
    melawati(A)
    city(A)
    backdrop(A)


if __name__ == "__main__":
    K.main("selangor", build, MOOD)
    write_mood("selangor", MOOD)
