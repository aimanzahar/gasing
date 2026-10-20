"""Kampung arena -- the title / Endless / multiplayer backdrop (design_art.md section c, kampung brief).
Golden hour in a Malay village yard: swept laterite with grass edges and broom marks.
Apron: mengkuang mats with spare tops + cords, sireh tray + kettle, coconut shells + kukur kelapa stool.
Far band: perigi (well) with pulley frame, reban (chicken coop) + hens, firewood rack + chopping block, banana clump.
Left flank: rumah kampung on stilts (bumbung panjang atap roof, tebar layar gables with crossed pemeleh boards),
serambi with jerejak railing, tangga with tempayan + slippers at its foot. Right flank: two dwarf + one tall coconut
palm, a fruiting rambutan. Far set: kampung houses among a palm skyline, a surau with a tiered roof, painted hill
ranges + golden clouds. No hazard.

  blender -b --factory-startup -P art_src/arena_kampung.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)  # blender-mcp re-runs
import numpy as np
from arenakit import P, xf, join, paint, tint, nz, smooth01

# Godot ARENA_DEFS["kampung"] recommendation (+ b_* = Blender preview factors only)
MOOD = {"sky_top": (0.34, 0.47, 0.74), "sky_horizon": (1.0, 0.72, 0.40), "fog": (0.95, 0.74, 0.48),
        "fog_density": 0.003, "sun_color": (1.0, 0.80, 0.55), "sun_energy": 1.3,
        "lantern": (1.0, 0.66, 0.34), "lantern_energy": 1.6, "exposure": 0.95, "ambient": 0.38,
        "b_sun": 3.8, "b_world": 0.9, "b_fill": 0.4, "b_lantern": 12.0}

# ---------------------------------------------------------------- palette (sRGB)
LATERITE = (0.55, 0.32, 0.19)
LAT_DUST = (0.63, 0.43, 0.28)
LAT_DAMP = (0.43, 0.25, 0.16)
GRASS = (0.34, 0.41, 0.16)
GRASS_DRY = (0.50, 0.47, 0.23)
GRASS_TINT = (0.42, 0.50, 0.20)
TIMBER = (0.50, 0.36, 0.24)
TIMBER_LT = (0.60, 0.46, 0.32)
TIMBER_DK = (0.30, 0.20, 0.13)
WALL = (0.56, 0.42, 0.29)
ATAP = (0.54, 0.40, 0.26)
ATAP_OLD = (0.42, 0.33, 0.24)
MENGKUANG = (0.70, 0.58, 0.38)
DYE_RED = (0.62, 0.16, 0.12)
DYE_GREEN = (0.16, 0.36, 0.22)
LEAF_PALM = (0.30, 0.44, 0.16)
LEAF_DK = (0.18, 0.29, 0.12)
BANANA = (0.34, 0.50, 0.18)
STONE = (0.50, 0.47, 0.42)
PLASTER = (0.80, 0.74, 0.62)
CLAY = (0.58, 0.32, 0.20)
BRASS = (0.78, 0.58, 0.26)
SHELL = (0.40, 0.28, 0.17)

YC = (-0.8, 0.9)                 # yard centre
YAX, YAY_FAR, YAY_NEAR, YPW = 9.0, 8.6, 6.4, 2.2
HOUSE = dict(x0=-11.4, x1=-7.9, y0=-2.1, y1=3.3, fh=1.4, wh=2.1, rise=1.9, over=0.55)
SERAMBI_X = -6.7                 # outer edge of the verandah deck
SFH = 1.05                       # verandah floor height
TANGGA_Y = (0.15, 1.05)
WELL = (-4.3, 7.5)
COOP = (3.7, 7.7)
RACK = (-0.4, 8.9)
PATHS = [[(-5.8, 0.6), (-4.6, 0.4)], [(-3.0, 4.0), (-3.8, 6.1), (-4.1, 6.6)], [(3.0, 3.6), (4.4, 6.0), (6.4, 10.5), (9.5, 16.0), (12.0, 22.0)],
         [(1.0, -4.6), (1.4, -7.5), (1.0, -12.0)]]


def seg_dist(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


def path_dist(x, y):
    return min(seg_dist(x, y, a, b) for pl in PATHS for a, b in zip(pl[:-1], pl[1:]))


def yard_d(x, y):
    dx, dy = x - YC[0], y - YC[1]
    ay = YAY_FAR if dy > 0 else YAY_NEAR
    return ((abs(dx) / YAX) ** YPW + (abs(dy) / ay) ** YPW) ** (1.0 / YPW) + 0.1 * nz(x, y, 0, 0.35, 5)


def ground(x, y):
    r = math.hypot(x, y)
    h = 0.02 * nz(x, y, 0, 0.4, 1) + 0.01 * nz(x, y, 0, 1.4, 2)
    h += 0.07 * smooth01(0.95, 1.25, yard_d(x, y))                      # grass verge a touch higher than the swept yard
    h -= 0.025 * (1 - smooth01(0.1, 0.7, path_dist(x, y)))              # worn paths
    h += smooth01(24.0, 110.0, r) * (0.9 + 0.7 * nz(x, y, 0, 0.025, 3))  # gentle rise toward the hills
    return float(h)


def in_vista(x, y):
    dx, dy = x + 1.5, y + 12.5
    return dy > 2 and -58 < math.degrees(math.atan2(dx, dy)) < 44


def visible(x, y, pad=0.0):
    return (y > -6.5 - pad and abs(x) < 11 + 0.55 * (y + 6.5) + pad) or in_vista(x, y)


def mix(a, b, t):
    return np.asarray(a, dtype=np.float64) * (1 - t) + np.asarray(b, dtype=np.float64) * t


def broom(x, y):
    """sapu lidi marks: fans of parallel arcs swept around a few standing points (0..1)."""
    best = 0.0
    for k, (cx, cy, s) in enumerate(((-3.6, -3.0, 1.0), (2.8, 4.0, 0.9), (-5.2, 3.8, 0.8), (4.4, -3.2, 0.9),
                                     (0.2, 6.4, 0.8), (-0.8, -6.0, 0.7), (6.6, 0.8, 0.8), (-6.4, -4.4, 0.8), (-2.2, 5.2, 0.7))):
        d = math.hypot(x - cx, y - cy)
        m = (1 - smooth01(2.0, 3.6, d)) * smooth01(0.4, 0.9, d)
        if m <= 0:
            continue
        a = math.atan2(y - cy, x - cx)
        wave = 0.5 + 0.5 * math.sin(d * 6.3 + 1.2 * math.sin(a * 2 + k))
        best = max(best, m * s * wave)
    return best


def gcolor(x, y, z):
    r = math.hypot(x, y)
    n1 = nz(x, y, 0, 0.45, 11)
    n2 = nz(x, y, 0, 2.1, 12)
    n3 = nz(x, y, 0, 6.0, 13)
    yd = yard_d(x, y)
    pd = path_dist(x, y)
    base = np.array(LATERITE) * (1 + 0.10 * n1 + 0.07 * n2 + 0.04 * n3)
    bm = broom(x, y)
    base = mix(base, LAT_DUST, 0.7 * bm)                                             # swept arcs: dusty crests ...
    base = mix(base, LAT_DAMP, 0.22 * smooth01(0.0, 0.25, bm) * (1 - smooth01(0.3, 0.7, bm)))   # ... darker troughs
    base = mix(base, LAT_DAMP, 0.55 * smooth01(0.15, 0.55, nz(x, y, 0, 0.3, 15)))    # damp patches
    hx = HOUSE
    eave = (hx["x0"] - 0.8 < x < SERAMBI_X + 0.5) and (hx["y0"] - 0.8 < y < hx["y1"] + 0.8)
    if eave:
        base = mix(base, LAT_DAMP, 0.45)                                              # drip line / shade under the house
    base = mix(base, LAT_DUST, 0.6 * (1 - smooth01(0.0, 0.55, pd)))                   # trodden paths
    base = mix(base, np.array(LAT_DUST) * 0.96, 0.55 * (1 - smooth01(4.6, 5.6, r)))   # compacted apron
    grass = smooth01(0.9, 1.08, yd)
    tufts = smooth01(0.35, 0.65, nz(x, y, 0, 0.8, 16)) * smooth01(0.7, 0.92, yd)      # grass creeping into the yard edge
    g = min(1.0, grass + 0.7 * tufts) * smooth01(0.25, 0.8, pd)
    gc = mix(GRASS, GRASS_DRY, 0.5 + 0.5 * nz(x, y, 0, 0.12, 17)) * (1 + 0.1 * n2)
    if r > 30:                                                                        # far fields: gold-green mosaic
        f = 0.5 + 0.5 * math.sin(x * 0.11 + 0.6 * nz(x, y, 0, 0.03, 18)) * math.sin(y * 0.09)
        gc = mix(gc, (0.56, 0.52, 0.22), 0.5 * smooth01(0.3, 0.7, f) * smooth01(30, 45, r))
    base = mix(base, gc, g)
    return tuple(base)


def gkind(x, y, z):
    if math.hypot(x, y) > 23:
        return "MatGrass_lawn"
    yd = yard_d(x, y)
    if yd > 1.0 and path_dist(x, y) > 0.5:
        return "MatGrass_lawn"
    return "MatGround_laterite"


def gcull(cx, cy, zmax):
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


def bx(sx, sy, sz, loc, rot=(0, 0, 0), bev=0.0):
    return xf(K.box(sx, sy, sz, bev=bev), loc, rot)


# ---------------------------------------------------------------- building parts
def plank_grid(a, b, z0, z1, pitch=0.18, rows=2, seed=0, out=None):
    """vertical-plank wall panel from 2D point a to b (normal = left of a->b unless `out` flips it),
    vertex-colour plank stripes. Single-sided."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(round(L / pitch)))
    v, f = [], []
    for i in range(n + 1):
        t = i / n
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        for j in range(rows + 1):
            v.append((x, y, z0 + (z1 - z0) * j / rows))
    for i in range(n):
        for j in range(rows):
            q = i * (rows + 1) + j
            f.append((q, q + rows + 1, q + rows + 2, q + 1))
    p = P(v, f)
    if out:
        p.f = [tuple(reversed(x)) for x in p.f]
    return p


def stripes(seed, base, k=0.26):
    rng = random.Random(seed)
    jit = [1 + rng.uniform(-0.08, 0.08) for _ in range(400)]

    def fn(v, c):
        idx = (np.floor((v[:, 0] + v[:, 1]) / 0.18).astype(int)) % 400
        alt = 1.0 - k * (np.floor((v[:, 0] + v[:, 1]) / 0.18) % 2)
        return c * (alt * np.array([jit[i] for i in idx]))[:, None]
    return fn


def atap_slope(L, D, drop, courses=6, cw=0.3, seed=0, tooth=0.06, thick=0.06):
    """one single-sided thatch slope: length L along X, from the ridge line (y=0, z=0) down to the eave at
    y=-D, z=-drop. Overlapping courses with jagged eaves + a lip. Normals face up/-y."""
    rng = random.Random(seed)
    cols = max(4, int(L / cw))
    ps = []
    for c in range(courses):
        t0 = 1.0 - (c + 1.3) / courses
        t1 = 1.0 - c / courses
        t0 = max(0.0, t0)
        v, f = [], []
        for i in range(cols + 1):
            x = (i / cols - 0.5) * L
            dr = tooth * rng.random()
            for t, e in ((t1, dr), (t0, 0.0)):
                v.append((x, -D * t, -drop * t - e))
        for i in range(cols):
            a = 2 * i
            f.append((a, a + 2, a + 3, a + 1))
        sheet = P(v, f)
        lv, lf = [], []
        for i in range(cols + 1):
            x, y, z = v[2 * i]
            lv += [(x, y, z), (x, y + 0.01, z - thick)]
        for i in range(cols):
            a = 2 * i
            lf.append((a, a + 1, a + 3, a + 2))
        ps.append(join(sheet, P(lv, lf)))
    p = join(ps)
    return p


def course_tint(zref, drop, courses):
    return lambda v, c: c * (0.84 + 0.2 * (np.floor((zref - v[:, 2]) / max(drop, 1e-6) * courses + 0.5) % 2))[:, None]


def sunburst(cx, y, z0, half, rise, n=9, out=-1):
    """tebar layar gable panel: fan of planks radiating from the bottom centre (Wood, alternating tones)."""
    v = [(cx, y, z0 + 0.05)]
    for i in range(n + 1):
        t = i / n
        if t <= 0.5:
            px, pz = cx - half + 2 * half * t, z0 + rise * (2 * t)
        else:
            px, pz = cx - half + 2 * half * t, z0 + rise * (2 - 2 * t)
        v.append((px, y, pz))
    f = [(0, i + 1, i + 2) if out < 0 else (0, i + 2, i + 1) for i in range(n)]
    p = P(v, f)
    p.c = np.ones((len(v), 4))
    return p


def rumah(A):
    """rumah kampung (bumbung panjang) on 12 posts, ridge along y, verandah + tangga toward the ring (+x)."""
    H = HOUSE
    x0, x1, y0, y1, fh, wh, rise, over = H["x0"], H["x1"], H["y0"], H["y1"], H["fh"], H["wh"], H["rise"], H["over"]
    eave = fh + wh
    xc, yc = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    gz = ground(xc, yc)
    wood, dark, thatch, rock, glow, cloth, metal, light_wood = [], [], [], [], [], [], [], []
    ys = np.linspace(y0, y1, 4)
    for px in (x0, xc, x1):
        for k, py in enumerate(ys):
            top = eave if px != xc else fh
            wood.append(bx(0.15, 0.15, top + 0.05, (px, py, gz - 0.02), bev=0.015))
            rock.append(on_ground(K.smooth_rock(0.17, seed=int(px * 7 + py * 3) + 40, sub=2, squash=(1, 1, 0.45), flat=0.3), px, py, 0.03))
    for px in (x0, xc, x1):  # rasuk (floor beams)
        dark.append(bx(0.12, y1 - y0 + 0.3, 0.14, (px, yc, gz + fh - 0.16)))
    wood.append(bx(x1 - x0 + 0.2, y1 - y0 + 0.2, 0.06, (xc, yc, gz + fh - 0.03)))
    # walls: front (+x), back, gable ends -- vertical planks, window openings as dark recesses with open shutters
    wl = [plank_grid((x1 + 0.02, y0), (x1 + 0.02, y1), gz + fh, gz + eave, seed=1, out=True),
          plank_grid((x0 - 0.02, y0), (x0 - 0.02, y1), gz + fh, gz + eave, seed=2),
          plank_grid((x0, y0 - 0.02), (x1, y0 - 0.02), gz + fh, gz + eave, seed=3, out=True),
          plank_grid((x0, y1 + 0.02), (x1, y1 + 0.02), gz + fh, gz + eave, seed=4)]
    for k, w in enumerate(wl):
        paint(w, WALL, var=0.04, ao=0.35, ao_h=1.0, ground=gz + fh, top=0.0, namp=0.08, ns=2.0, seed=k)
        tint(w, stripes(k, WALL))
    A.add("battle", "MatWood_timber", wl)
    for zz in (gz + fh + 0.02, gz + eave - 0.06):  # sill + top plate rails
        dark.append(bx(0.07, y1 - y0 + 0.16, 0.1, (x1 + 0.05, yc, zz)))
        dark.append(bx(0.07, y1 - y0 + 0.16, 0.1, (x0 - 0.05, yc, zz)))
        dark.append(bx(x1 - x0 + 0.16, 0.07, 0.1, (xc, y0 - 0.05, zz)))
        dark.append(bx(x1 - x0 + 0.16, 0.07, 0.1, (xc, y1 + 0.05, zz)))

    def window(px, py, axis, outward):
        """axis 'y' = window in a wall running along y (front/back), 'x' = gable wall."""
        w, hgt, zb = 0.78, 1.15, gz + fh + 0.45
        if axis == "y":
            dark.append(bx(0.04, w, hgt, (px + 0.02 * outward, py, zb)))
            light_wood.append(bx(0.06, w + 0.16, 0.08, (px + 0.04 * outward, py, zb - 0.06)))
            light_wood.append(bx(0.06, w + 0.16, 0.36, (px + 0.04 * outward, py, zb + hgt + 0.02)))     # kerawang transom
            for s in (-1, 1):  # daun tingkap swung open
                light_wood.append(xf(K.box(0.4, 0.035, hgt, bev=0.0), (px + outward * 0.22, py + s * (w / 2 + 0.17), zb),
                                     (0, 0, math.radians(70) * s * outward)))
        else:
            dark.append(bx(w, 0.04, hgt, (px, py + 0.02 * outward, zb)))
            light_wood.append(bx(w + 0.16, 0.06, 0.08, (px, py + 0.04 * outward, zb - 0.06)))
            light_wood.append(bx(w + 0.16, 0.06, 0.36, (px, py + 0.04 * outward, zb + hgt + 0.02)))
            for s in (-1, 1):
                light_wood.append(xf(K.box(0.035, 0.4, hgt, bev=0.0), (px + s * (w / 2 + 0.17), py + outward * 0.22, zb),
                                     (0, 0, -math.radians(70) * s * outward)))
    for py in (y0 + 1.25, y1 - 1.25):
        window(x1 + 0.02, py, "y", 1)
    window(x0 - 0.02, yc, "y", -1)
    window(xc, y0 - 0.02, "x", -1)
    window(xc, y1 + 0.02, "x", 1)
    # main roof: two single-sided atap slopes, ridge along y
    L = y1 - y0 + 2 * over
    D = (x1 - x0) / 2 + over
    drop = rise * D / ((x1 - x0) / 2)
    zr = gz + eave + rise
    for side in (1, -1):
        s = atap_slope(L, D, drop, courses=7, cw=0.3, seed=10 + side, tooth=0.07)
        s = xf(s, (0, 0, 0), (0, 0, math.pi / 2 if side > 0 else -math.pi / 2))   # -y slope -> +x (side 1) / -x
        s = xf(s, (xc, yc, zr))
        paint(s, ATAP, var=0.04, ao=0.0, top=0.3, namp=0.22, ns=2.5, stretch=(6, 6, 0.4), seed=20 + side)
        tint(s, course_tint(zr, drop, 7))
        tint(s, lambda v, c: c * (0.82 + 0.18 * smooth01(-1.6, 0.0, v[:, 2] - zr))[:, None])   # weathered low courses
        thatch.append(s)
    thatch.append(paint(K.tube([(xc, y0 - over - 0.05, zr + 0.03), (xc, y1 + over + 0.05, zr + 0.03)], 0.09, seg=6), ATAP_OLD, ao=0.0, top=0.2))
    # gables: tebar layar sunburst + crossed pemeleh (bargeboards) extending past the apex
    half = (x1 - x0) / 2 + 0.05
    for gy, out in ((y0 - 0.06, -1), (y1 + 0.06, 1)):
        sb = sunburst(xc, gy, gz + eave, half, rise - 0.05, n=11, out=out)
        sb.c[:, :3] = np.array(TIMBER_LT)
        sb.c[0, :3] = np.array(TIMBER_DK)
        light_wood.append(sb)
        for s in (-1, 1):
            a = (xc + s * (half + over * 0.9), gy + out * 0.08, gz + eave - drop * over / D * 0.9 + 0.02)
            b = (xc - s * 0.42, gy + out * 0.08, zr + 0.42 * rise / half + 0.04)
            dx_, dz_ = b[0] - a[0], b[2] - a[2]
            ln = math.hypot(dx_, dz_)
            board = K.box(ln, 0.05, 0.2, bev=0.008)
            board.v[:, 0] += ln / 2
            board.v[:, 2] -= 0.1
            ang = math.atan2(dz_, dx_)
            dark.append(xf(board, a, (0, -ang, 0)))
            dark.append(xf(K.lathe([(0.0, 0.0), (0.05, 0.0), (0.06, 0.1), (0.02, 0.22), (0.0, 0.24)], seg=5),
                           (b[0] + 0.03 * s, b[1], b[2] - 0.03), (0, math.radians(30) * s, 0)))   # upturned tip
    # serambi: deck, outer posts, jerejak railing, lean-to atap roof
    sy0, sy1 = y0 + 0.35, y1 - 0.35
    sx = SERAMBI_X
    wood.append(bx(sx - x1 + 0.1, sy1 - sy0, 0.06, ((sx + x1) / 2, (sy0 + sy1) / 2, gz + SFH - 0.03)))
    dark.append(bx(0.12, sy1 - sy0, 0.14, (sx + 0.06, (sy0 + sy1) / 2, gz + SFH - 0.17)))
    sroof_lo = gz + 2.55
    for py in np.linspace(sy0, sy1, 5):
        wood.append(bx(0.12, 0.12, 2.55 - 0.02, (sx + 0.06, py, gz - 0.02), bev=0.012))
        if abs(py - (sy0 + sy1) / 2) > 0.1:
            rock.append(on_ground(K.smooth_rock(0.14, seed=int(py * 11) + 70, sub=2, squash=(1, 1, 0.45)), sx + 0.06, py, 0.03))
    rail_z = (gz + SFH + 0.08, gz + SFH + 0.72)
    runs = [((sx + 0.06, sy0), (sx + 0.06, TANGGA_Y[0] - 0.05)), ((sx + 0.06, TANGGA_Y[1] + 0.05), (sx + 0.06, sy1)),
            ((x1 + 0.05, sy0), (sx + 0.06, sy0)), ((x1 + 0.05, sy1), (sx + 0.06, sy1))]
    for (ax_, ay_), (bx_, by_) in runs:
        ln = math.hypot(bx_ - ax_, by_ - ay_)
        ang = math.atan2(by_ - ay_, bx_ - ax_)
        mx_, my_ = (ax_ + bx_) / 2, (ay_ + by_) / 2
        for zz in rail_z:
            light_wood.append(xf(K.box(ln, 0.06, 0.06, bev=0.0), (mx_, my_, zz), (0, 0, ang)))
        nb = max(1, int(ln / 0.15))
        for i in range(nb):
            t = (i + 0.5) / nb
            light_wood.append(xf(K.lathe([(0.025, 0.0), (0.03, 0.12), (0.02, 0.3), (0.03, 0.48), (0.025, 0.6)], seg=4, cap0=False, cap1=False),
                                 (ax_ + (bx_ - ax_) * t, ay_ + (by_ - ay_) * t, rail_z[0])))
    lean = atap_slope(sy1 - sy0 + 1.0, sx - x1 + 0.45, (gz + eave - 0.3) - sroof_lo, courses=4, cw=0.3, seed=31, tooth=0.06)
    lean = xf(xf(lean, (0, 0, 0), (0, 0, math.pi / 2)), (x1 + 0.05, (sy0 + sy1) / 2, gz + eave - 0.3))
    paint(lean, ATAP, var=0.04, ao=0.0, top=0.3, namp=0.22, ns=2.5, stretch=(6, 6, 0.4), seed=33)
    tint(lean, course_tint(gz + eave - 0.3, (gz + eave - 0.3) - sroof_lo, 4))
    thatch.append(lean)
    # tangga: stringers, 4 steps, newel posts + hand rails
    ty = 0.5 * (TANGGA_Y[0] + TANGGA_Y[1])
    tw = TANGGA_Y[1] - TANGGA_Y[0]
    steps = 4
    run = (-5.74 - sx) / steps
    for i in range(steps):
        zz = gz + SFH * (steps - i) / (steps + 1)
        wood.append(bx(run + 0.06, tw - 0.08, 0.05, (sx + run * (i + 0.5) + 0.02, ty, zz)))
    for s in (-1, 1):
        yy = ty + s * (tw / 2 - 0.02)
        dark.append(K.tube([(sx + 0.05, yy, gz + SFH - 0.02), (-5.72, yy, gz + 0.02)], 0.045, seg=4))
        light_wood.append(bx(0.09, 0.09, 0.95, (-6.08, yy + s * 0.04, gz - 0.02)))
        light_wood.append(K.tube([(-6.08, yy + s * 0.04, gz + 0.93), (sx + 0.06, yy + s * 0.04, gz + SFH + 0.72)], 0.03, seg=5))
    # tempayan + gayung + foot stone at the tangga foot, slippers on the step, pot plants
    jx, jy = -5.65, -0.35
    clay = [on_ground(K.jar(0.21, 0.5), jx, jy, 0.03)]
    shell = [xf(K.lathe([(0.0, 0.0), (0.06, 0.005), (0.085, 0.04), (0.09, 0.075), (0.08, 0.075), (0.075, 0.045), (0.0, 0.015)], seg=8),
                (jx + 0.05, jy + 0.03, ground(jx, jy) + 0.47))]
    wood.append(K.tube([(jx + 0.05, jy + 0.03, ground(jx, jy) + 0.52), (jx + 0.3, jy - 0.12, ground(jx, jy) + 0.55)], 0.012, seg=4))
    rock.append(on_ground(K.smooth_rock(0.32, seed=88, sub=2, squash=(1.3, 1, 0.25), flat=0.3), -5.55, 0.62, 0.02))
    slip = []
    for k, (sxp, syp, rz, col) in enumerate(((-5.62, 0.38, 0.2, (0.20, 0.36, 0.62)), (-5.6, 0.62, 0.05, (0.22, 0.38, 0.64)),
                                            (-5.5, 0.95, -0.4, (0.70, 0.22, 0.16)), (-5.42, 1.18, -0.3, (0.72, 0.24, 0.18)))):
        sl = K.box(0.25, 0.095, 0.022, bev=0.008)
        slip.append(paint(xf(sl, (sxp, syp, ground(sxp, syp) + 0.004), (0, 0, rz)), col, ao=0.0, top=0.15))
    pots = []
    for k, (px, py) in enumerate(((-6.35, -0.75), (-6.4, 1.95), (-7.3, -1.8))):
        pots.append(paint(on_ground(K.lathe([(0.0, 0.0), (0.12, 0.0), (0.17, 0.26), (0.19, 0.28), (0.15, 0.28), (0.0, 0.25)], seg=10, cap1=False), px, py, 0.01),
                          CLAY, ao=0.4, ao_h=0.2, ground=ground(px, py), top=0.15))
        leaf = K.smooth_rock(0.3, seed=150 + k, sub=2, amp=0.35, freq=2.4, squash=(1, 1, 0.8), flat=0.6, relax=1)
        lf = paint(xf(leaf, (px, py, ground(px, py) + 0.24)), (0.22, 0.38, 0.15), var=0.08, ao=0.3, ao_h=0.4, ground=ground(px, py) + 0.24, top=0.35, namp=0.2, ns=4)
        tint(lf, lambda v, c, k=k: np.where((K.nfield(v, 6.0, 300 + k) > 0.45)[:, None],
                                            np.array([0.86, 0.22, 0.42, 1.0]) if k != 1 else np.array([0.95, 0.62, 0.20, 1.0]), c))
        A.add("battle", "MatLeaf_canopy", lf)
    # pelita on the verandah post + its light; a batik sarong drying over the rail
    lpx, lpy = sx + 0.1, sy1 - 0.6
    glow.append(xf(K.lathe([(0, 0), (0.05, 0.0), (0.06, 0.06), (0.03, 0.12), (0, 0.13)], seg=8), (lpx - 0.12, lpy, gz + 2.0)))
    metal.append(bx(0.14, 0.03, 0.03, (lpx - 0.05, lpy, gz + 1.98)))
    A.light((lpx - 0.12, lpy, gz + 2.12), 16.0, (1.0, 0.62, 0.3), range_m=4)
    sar = K.strip_mesh([(sx + 0.08, sy0 + 0.25 + 0.3 * k, rail_z[1] + 0.02 - 0.03 * math.sin(k * 1.3)) for k in range(5)], [0.42] * 5,
                       up=(1, 0, 0), seed=7)
    sar.v[:, 0] += 0.03
    sar.v[:, 2] -= 0.2
    cloth.append(sar)
    # firewood under the floor + a basket
    for k in range(6):
        wood.append(K.tube([(x0 + 0.5, y0 + 0.6 + 0.14 * k, gz + 0.08 + 0.12 * (k % 2)), (x0 + 1.5, y0 + 0.62 + 0.14 * k, gz + 0.07 + 0.12 * (k % 2))], 0.055, seg=6))

    A.add("battle", "MatWood_timber", [paint(q, TIMBER, var=0.1, ao=0.5, ao_h=1.0, ground=gz, namp=0.1, ns=3.0, stretch=(1, 1, 0.2)) for q in wood])
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_DK, var=0.08, ao=0.3, ao_h=1.0, ground=gz, namp=0.1, ns=3.0) for q in dark])
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_LT, var=0.06, ao=0.25, ao_h=1.2, ground=gz, top=0.1) if q.c is None or np.allclose(q.c, 1)
                                      else q for q in light_wood])
    A.add("battle", "MatThatch_atap", thatch)
    A.add("battle", "MatRock_stone", [paint(q, STONE, ao=0.45, ao_h=0.15, ground=gz, top=0.2) for q in rock])
    A.add("battle", "MatRock_stone", [paint(q, CLAY, ao=0.45, ao_h=0.3, ground=gz, top=0.2) for q in clay])
    A.add("battle", "MatWood_timber", [paint(q, SHELL, ao=0.0, top=0.2) for q in shell])
    A.add("battle", "MatCloth_batik", slip)
    A.add("battle", "MatRock_stone", pots)
    A.add("battle", "MatGlow_pelita", [paint(q, (1.0, 0.8, 0.5), ao=0.0, top=0.0) for q in glow])
    A.add("battle", "MatMetal_brass", [paint(q, BRASS, ao=0.0) for q in metal])
    A.add("battle", "MatCloth_batik", [tint(paint(q, (0.24, 0.30, 0.55), var=0.0, ao=0.15, ground=gz), lambda v, c: c * np.where(
        (np.floor(v[:, 1] * 9) % 3 == 0)[:, None], np.array([2.4, 1.5, 0.55, 1]), 1.0)) for q in cloth])
    A.contact(xc, yc, 4.2, 0.28)
    A.contact(jx, jy, 0.6, 0.35)
    A.scatter_patch("Grass", 26, x0 - 0.4, y1 + 0.6, 1.4, ground, GRASS_TINT, seed=61)
    A.scatter_patch("Grass", 26, x0 + 0.6, y0 - 0.9, 1.2, ground, GRASS_TINT, seed=62)


# ---------------------------------------------------------------- yard props
def perigi(A):
    """well: plastered ring wall with moss, water, timber A-frame with kerek pulley, timba bucket, washing stones."""
    x, y = WELL
    gz = ground(x, y)
    ring = K.lathe([(0.82, 0.0), (0.84, 0.62), (0.80, 0.70), (0.62, 0.70), (0.58, 0.64), (0.58, 0.1)], seg=22, cap0=False, cap1=False)
    ring = xf(ring, (x, y, gz - 0.05))
    paint(ring, PLASTER, var=0.03, ao=0.45, ao_h=0.5, ground=gz, top=0.2, namp=0.1, ns=4)
    tint(ring, lambda v, c: c * (1 - 0.35 * smooth01(0.1, 0.6, K.nfield(v, 2.5, 91)) * (1 - smooth01(gz + 0.1, gz + 0.5, v[:, 2])))[:, None]
         * np.where((v[:, 2] < gz + 0.25)[:, None], np.array([0.78, 0.86, 0.7, 1]), 1.0))
    A.add("battle", "MatRock_stone", ring)
    wat = K.lathe([(0.0, 0.0), (0.6, 0.0)], seg=16, cap0=False, cap1=False)
    wat = xf(wat, (x, y, gz + 0.38))
    wat.f = [tuple(reversed(f)) for f in wat.f]
    wat.c = np.tile([0.16, 0.22, 0.22, 1.0], (len(wat.v), 1))
    A.add("battle", "MatWater_well", wat)
    wood = []
    for s in (-1, 1):
        wood.append(K.tube([(x + s * 0.95, y - 0.05, gz - 0.05), (x + s * 0.72, y, gz + 1.85)], [0.07, 0.06], seg=6))
    wood.append(K.tube([(x - 0.82, y, gz + 1.8), (x + 0.82, y, gz + 1.8)], 0.05, seg=6))
    wheel = xf(K.lathe([(0.0, -0.03), (0.13, -0.03), (0.1, 0.0), (0.13, 0.03), (0.0, 0.03)], seg=10), (x, y, gz + 1.68), (math.pi / 2, 0, 0))
    wood.append(wheel)
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_DK, var=0.06, ao=0.3, ao_h=1.0, ground=gz) for q in wood])
    A.add("battle", "MatThatch_atap", paint(K.tube([(x + 0.12, y, gz + 1.68), (x + 0.12, y, gz + 1.0)], 0.01, seg=3), (0.6, 0.5, 0.35), ao=0))
    bucket = K.lathe([(0.0, 0.0), (0.12, 0.0), (0.16, 0.26), (0.14, 0.26), (0.11, 0.03), (0.0, 0.03)], seg=10, cap1=False)
    A.add("battle", "MatMetal_brass", paint(xf(bucket, (x + 0.12, y, gz + 0.74)), (0.55, 0.55, 0.52), ao=0.0, top=0.2))
    pail = K.lathe([(0.0, 0.0), (0.17, 0.0), (0.2, 0.22), (0.18, 0.22), (0.15, 0.02), (0.0, 0.02)], seg=10, cap1=False)
    A.add("battle", "MatMetal_brass", paint(on_ground(pail, x + 1.15, y - 0.75), (0.32, 0.46, 0.58), ao=0.3, ao_h=0.1, ground=gz, top=0.2))
    stones = [on_ground(K.smooth_rock(0.3 + 0.06 * k, seed=120 + k, sub=2, squash=(1.3, 1, 0.22), flat=0.3), x + dx, y + dy, 0.03)
              for k, (dx, dy) in enumerate(((0.95, -0.9), (-0.2, -1.15), (-1.0, -0.6)))]
    A.add("battle", "MatRock_stone", [paint(q, (0.46, 0.44, 0.40), ao=0.4, ao_h=0.1, ground=gz, top=0.25) for q in stones])
    A.contact(x, y, 1.6, 0.35)
    A.scatter_patch("Grass", 30, x - 0.2, y + 0.9, 0.8, ground, (0.34, 0.48, 0.18), seed=71)


def chicken(x, y, rz, col, seed):
    rng = random.Random(seed)
    gz = ground(x, y)
    body = K.lathe([(0.0, 0.0), (0.06, 0.02), (0.1, 0.08), (0.09, 0.15), (0.05, 0.19), (0.0, 0.2)], seg=7)
    body = xf(body, (0, 0, 0), (0, math.pi / 2 - 0.25, 0))
    body.v[:, 2] += 0.14
    head = xf(K.smooth_rock(0.045, seed=seed, sub=1, flat=1.0, relax=1), (0.17, 0, 0.22))
    tail = K.P([(-0.02, -0.03, 0.17), (-0.02, 0.03, 0.17), (-0.13, 0.0, 0.32)], [(0, 1, 2)])
    legs = [K.tube([(0.02, s * 0.03, 0.08), (0.03, s * 0.03, 0.0)], 0.008, seg=3) for s in (-1, 1)]
    out = []
    out.append(paint(xf(join(body, tail), (x, y, gz), (0, 0, rz)), col, var=0.1, ao=0.2, ao_h=0.1, ground=gz, top=0.3))
    out.append(paint(xf(head, (x, y, gz), (0, 0, rz)), (0.75, 0.16, 0.10) if rng.random() < 0.5 else col, ao=0.0, top=0.2))
    out += [paint(xf(l, (x, y, gz), (0, 0, rz)), (0.8, 0.6, 0.2), ao=0) for l in legs]
    return out


def reban(A):
    """raised chicken coop: slatted box on legs, atap roof, ramp; hens pecking around a feed tray."""
    x, y = COOP
    gz = ground(x, y)
    rz = -0.25
    wood, dark = [], []
    for sx in (-0.65, 0.65):
        for sy in (-0.45, 0.45):
            dark.append(bx(0.07, 0.07, 0.55, (sx, sy, -0.02)))
    wood.append(bx(1.45, 1.0, 0.05, (0, 0, 0.5)))
    wood.append(bx(1.45, 0.04, 0.75, (0, 0.48, 0.55)))
    for sx in (-0.7, 0.7):
        wood.append(bx(0.04, 1.0, 0.75, (sx, 0, 0.55)))
    for k in range(9):  # front slats
        wood.append(bx(0.05, 0.03, 0.72, (-0.64 + k * 0.16, -0.5, 0.55)))
    wood.append(xf(K.box(0.32, 0.9, 0.025, bev=0.0), (0.25, -0.88, 0.25), (math.radians(35), 0, 0)))
    roof = atap_slope(1.8, 0.75, 0.25, courses=3, cw=0.28, seed=5)
    roof2 = xf(atap_slope(1.8, 0.75, 0.25, courses=3, cw=0.28, seed=6), (0, 0, 0), (0, 0, math.pi))
    rf = [xf(roof, (0, 0, 1.55)), xf(roof2, (0, 0, 1.55))]
    put = lambda q: xf(q, (x, y, gz), (0, 0, rz))
    A.add("battle", "MatWood_timber", [paint(put(q), (0.52, 0.40, 0.28), var=0.12, ao=0.4, ao_h=0.8, ground=gz, namp=0.12, ns=4) for q in wood])
    A.add("battle", "MatWood_timber", [paint(put(q), TIMBER_DK, ao=0.3, ao_h=0.4, ground=gz) for q in dark])
    A.add("battle", "MatThatch_atap", [tint(paint(put(q), ATAP_OLD, var=0.05, ao=0.0, top=0.3, namp=0.2, ns=3), course_tint(gz + 1.55, 0.25, 3)) for q in rf])
    hens = []
    for k, (hx, hy, r_, col) in enumerate(((2.9, 6.6, 0.4, (0.55, 0.30, 0.14)), (2.4, 7.4, 2.4, (0.86, 0.80, 0.68)),
                                           (4.6, 6.5, 4.0, (0.30, 0.20, 0.13)), (3.4, 6.1, 5.2, (0.62, 0.36, 0.16)),
                                           (-6.9, -2.9, 1.2, (0.58, 0.33, 0.15)))):
        hens += chicken(hx, hy, r_, col, 200 + k)
    A.add("battle", "MatCloth_batik", hens)
    tray = K.lathe([(0.0, 0.0), (0.22, 0.0), (0.24, 0.05), (0.22, 0.05), (0.0, 0.02)], seg=10)
    A.add("battle", "MatWood_timber", paint(on_ground(tray, 3.3, 6.85), (0.40, 0.30, 0.20), ao=0.3, ao_h=0.05, ground=gz))
    rng = random.Random(4)
    grain = []
    for k in range(10):
        a, d = rng.uniform(0, 6.28), rng.uniform(0.25, 0.55)
        grain.append(xf(K.box(0.03, 0.03, 0.01, bev=0.0), (3.3 + d * math.cos(a), 6.85 + d * math.sin(a), ground(3.3, 6.85) + 0.002), (0, 0, a)))
    A.add("battle", "MatThatch_atap", [paint(q, (0.86, 0.74, 0.40), ao=0, top=0) for q in grain])
    A.contact(x, y, 1.4, 0.3)
    A.scatter_patch("Grass", 28, x + 1.2, y + 0.6, 0.9, ground, GRASS_TINT, seed=81)


def para_kayu(A):
    """firewood rack: posts + rails holding stacked split logs under a small atap roof, chopping block + axe."""
    x, y = RACK
    gz = ground(x, y)
    rz = 0.08
    wood, logs = [], []
    for sx in (-1.0, 1.0):
        for sy in (-0.3, 0.3):
            wood.append(bx(0.08, 0.08, 1.3, (sx, sy, -0.02)))
    for sy in (-0.3, 0.3):
        wood.append(bx(2.1, 0.06, 0.06, (0, sy, 0.12)))
    rng = random.Random(9)
    for row in range(5):
        for k in range(12):
            lx = -0.92 + k * 0.165 + (0.08 if row % 2 else 0)
            if lx > 0.95:
                continue
            r_ = rng.uniform(0.06, 0.085)
            zz = 0.22 + row * 0.15
            logs.append(K.tube([(lx, -0.36, zz), (lx + rng.uniform(-0.02, 0.02), 0.36, zz + rng.uniform(-0.01, 0.01))], r_, seg=5))
    roof = atap_slope(2.5, 0.6, 0.18, courses=2, cw=0.3, seed=12)
    roof2 = xf(atap_slope(2.5, 0.6, 0.18, courses=2, cw=0.3, seed=13), (0, 0, 0), (0, 0, math.pi))
    put = lambda q: xf(q, (x, y, gz), (0, 0, rz))
    A.add("battle", "MatWood_timber", [paint(put(q), TIMBER_DK, ao=0.35, ao_h=1.0, ground=gz) for q in wood])
    A.add("battle", "MatWood_timber", [tint(paint(put(q), (0.58, 0.44, 0.30), var=0.12, ao=0.35, ao_h=0.8, ground=gz),
                                            lambda v, c: c * np.where((np.abs((v[:, 1] - y) * math.cos(rz) - (v[:, 0] - x) * math.sin(rz)) > 0.34)[:, None],
                                                                      np.array([1.25, 1.15, 1.0, 1]), np.array([0.85, 0.82, 0.8, 1])))
                                       for q in logs])
    A.add("battle", "MatThatch_atap", [tint(paint(put(q), ATAP_OLD, var=0.05, ao=0.0, top=0.3, namp=0.2, ns=3), course_tint(gz + 1.28, 0.18, 2))
                                       for q in (xf(roof, (0, 0, 1.28)), xf(roof2, (0, 0, 1.28)))])
    bxx, byy = x + 1.6, y - 0.8
    block = K.lathe([(0.0, 0.0), (0.26, 0.0), (0.27, 0.36), (0.0, 0.37)], seg=10)
    A.add("battle", "MatWood_timber", tint(paint(on_ground(block, bxx, byy, 0.02), (0.46, 0.34, 0.23), ao=0.4, ao_h=0.3, ground=gz),
                                           lambda v, c: np.where((v[:, 2] > ground(bxx, byy) + 0.3)[:, None], c * np.array([1.35, 1.25, 1.1, 1]), c)))
    A.add("battle", "MatWood_timber", paint(K.tube([(bxx + 0.05, byy, ground(bxx, byy) + 0.36), (bxx + 0.35, byy - 0.45, ground(bxx, byy) + 0.05)], 0.02, seg=4),
                                            (0.55, 0.42, 0.28), ao=0))
    A.add("battle", "MatMetal_brass", paint(xf(K.box(0.14, 0.03, 0.1, bev=0.0), (bxx + 0.05, byy, ground(bxx, byy) + 0.35), (0, 0, -1.0)), (0.35, 0.34, 0.33), ao=0))
    A.contact(x, y, 1.5, 0.3)
    A.contact(bxx, byy, 0.5, 0.3)


def banana_clump(A, x, y, seed, n=4):
    rng = random.Random(seed)
    for k in range(n):
        a = rng.uniform(0, 6.28)
        d = 0 if k == 0 else rng.uniform(0.6, 1.2)
        h = rng.uniform(2.2, 3.1) * (1 if k < 2 else 0.6)
        px, py = x + d * math.cos(a), y + d * math.sin(a)
        st, lv = K.banana(h, seed=seed + k, leaves=6 if h > 2 else 4)
        gz = ground(px, py)
        rz = rng.uniform(0, 6.28)
        A.add("battle", "MatLeaf_canopy", paint(xf(lv, (px, py, gz - 0.05), (0, 0, rz)), BANANA, var=0.08, ao=0.35, ao_h=2.4, ground=gz, top=0.25, namp=0.15, ns=2))
        A.add("battle", "MatWood_timber", paint(xf(st, (px, py, gz - 0.05), (0, 0, rz)), (0.42, 0.44, 0.24), var=0.06, ao=0.4, ao_h=1.2, ground=gz))
        A.contact(px, py, 0.9, 0.25)
    A.scatter_patch("Grass", 26, x, y, 1.7, ground, GRASS_TINT, seed=seed)


def mat(cx, cy, w, d, rz, seed, border=DYE_RED, field=MENGKUANG):
    """mengkuang mat: woven diagonal check + dyed border bands, frayed edge, lying flat on the ground."""
    nx, ny = max(4, int(w / 0.1)), max(3, int(d / 0.1))
    p = K.grid(w, d, nx, ny)
    gz = ground(cx, cy)
    u = p.v[:, 0] / w + 0.5
    vv = p.v[:, 1] / d + 0.5
    chk = (np.floor((p.v[:, 0] + p.v[:, 1]) * 14) + np.floor((p.v[:, 0] - p.v[:, 1]) * 14)) % 2
    edge = np.minimum(np.minimum(u, 1 - u) * w, np.minimum(vv, 1 - vv) * d)
    band = (edge > 0.07) & (edge < 0.15)
    c = np.tile(np.asarray(field, dtype=np.float64), (len(p.v), 1)) * (0.9 + 0.12 * chk)[:, None]
    c[band] = np.asarray(border) * (0.9 + 0.15 * chk[band])[:, None]
    c[(edge > 0.2) & (edge < 0.24)] = np.asarray(DYE_GREEN)
    q = xf(p, (cx, cy, 0), (0, 0, rz))
    q.v[:, 2] = np.array([ground(a, b) + 0.012 for a, b, _ in q.v])
    q.c = np.ones((len(q.v), 4))
    q.c[:, :3] = np.clip(c, 0, 1)
    return q


def gasing_small(kind, seed):
    """spare top for the mats (local, upright, tip at z=0)."""
    if kind == "uri":
        prof = [(0.0, 0.0), (0.012, 0.01), (0.03, 0.03), (0.13, 0.08), (0.15, 0.1), (0.14, 0.12), (0.06, 0.15), (0.03, 0.18), (0.0, 0.19)]
    else:
        prof = [(0.0, 0.0), (0.012, 0.012), (0.05, 0.06), (0.1, 0.13), (0.11, 0.16), (0.09, 0.22), (0.05, 0.26), (0.02, 0.28), (0.0, 0.29)]
    return K.lathe(prof, seg=12, cap0=False, cap1=False)


def apron(A):
    """three apron clusters (<=0.6 m): tops on a mat, sireh tray + kettle, coconut corner by the palms."""
    # cluster A: left-near mat with spare tops, a cord coil, a knife
    mx, my = -5.25, -1.95
    A.add("battle", "MatThatch_atap", mat(mx, my, 1.5, 0.95, 0.5, 1))
    A.contact(mx, my, 1.1, 0.18)
    tops = [("jantung", mx + 0.2, my + 0.15, (0, 0, 0), (0.42, 0.18, 0.10)), ("uri", mx - 0.3, my - 0.25, (1.25, 0.0, 0.7), (0.30, 0.18, 0.10)),
            ("jantung", mx - 0.2, my + 0.45, (1.35, 0.0, 2.2), (0.48, 0.30, 0.14))]
    for kind, tx, ty, rot, col in tops:
        g = gasing_small(kind, 0)
        lift = 0.0 if rot == (0, 0, 0) else (0.15 if kind == "uri" else 0.11)
        q = xf(xf(g, (0, 0, 0), rot), (tx, ty, ground(tx, ty) + 0.012 + lift))
        z0 = q.v[:, 2].min()
        q.v[:, 2] += (ground(tx, ty) + 0.014) - z0
        paint(q, col, var=0.05, ao=0.2, ao_h=0.08, ground=ground(tx, ty), top=0.25)
        tint(q, lambda v, c, z0=q.v[:, 2].min(): c * np.where(((v[:, 2] - z0) % 0.09 < 0.02)[:, None], np.array([1.9, 1.4, 0.6, 1]), 1.0))
        A.add("battle", "MatWood_timber", q)
    for k, (cx, cy) in enumerate(((mx + 0.4, my - 0.25), (mx - 0.15, my + 0.5))):
        A.add("battle", "MatThatch_atap", paint(on_ground(K.rope_coil(0.13, 0.009, turns=4, layers=1, seed=k), cx, cy, -0.012), (0.76, 0.68, 0.50), ao=0.2, ao_h=0.03, ground=ground(cx, cy)))
    # cluster B: near-right mat with tepak sireh (brass box, open lid, cups), kettle + glasses
    sx, sy = 1.3, -5.35
    A.add("battle", "MatThatch_atap", mat(sx, sy, 1.2, 0.85, -0.15, 2, border=DYE_GREEN, field=(0.74, 0.62, 0.42)))
    A.contact(sx, sy, 0.9, 0.18)
    gz = ground(sx, sy) + 0.012
    brass = [xf(K.box(0.36, 0.24, 0.1, bev=0.015), (sx - 0.15, sy + 0.05, gz), (0, 0, -0.15)),
             xf(K.box(0.36, 0.02, 0.2, bev=0.008), (sx - 0.15 - 0.12 * math.sin(-0.15), sy + 0.05 + 0.12 * math.cos(-0.15) + 0.01, gz + 0.1), (math.radians(-20), 0, -0.15))]
    for k, (dx, dy) in enumerate(((-0.08, -0.02), (0.0, -0.02), (0.08, -0.02), (-0.04, 0.06), (0.04, 0.06))):
        brass.append(xf(K.lathe([(0.0, 0.0), (0.03, 0.0), (0.035, 0.04), (0.03, 0.05), (0.0, 0.05)], seg=6), (sx - 0.15 + dx, sy + 0.05 + dy, gz + 0.1)))
    kettle = K.lathe([(0.0, 0.0), (0.09, 0.0), (0.12, 0.08), (0.1, 0.16), (0.04, 0.2), (0.05, 0.22), (0.0, 0.23)], seg=10)
    brass.append(xf(kettle, (sx + 0.3, sy - 0.12, gz)))
    brass.append(K.tube([(sx + 0.39, sy - 0.12, gz + 0.08), (sx + 0.5, sy - 0.12, gz + 0.17)], [0.018, 0.01], seg=4))
    A.add("battle", "MatMetal_brass", [paint(q, BRASS, var=0.05, ao=0.2, ao_h=0.05, ground=gz, top=0.3) for q in brass])
    leaves = [xf(K.strip_mesh([(0, 0, 0), (0.07, 0.0, 0.004), (0.14, 0.0, 0.0)], [0.012, 0.035, 0.005], seed=k), (sx - 0.05 + 0.04 * k, sy - 0.2, gz + 0.004), (0, 0, 0.5 + 0.4 * k))
              for k in range(3)]
    A.add("battle", "MatLeaf_canopy", [paint(q, (0.24, 0.46, 0.16), ao=0, top=0) for q in leaves])
    for k in range(2):
        A.add("battle", "MatWater_well", paint(xf(K.lathe([(0.0, 0.0), (0.03, 0.0), (0.035, 0.08), (0.0, 0.07)], seg=6), (sx + 0.08 + 0.09 * k, sy - 0.32, gz)), (0.56, 0.36, 0.20), ao=0, alpha=1.0))
    # cluster C: coconut corner on the right apron -- husk pile, shell halves, kukur kelapa stool, parang
    cx, cy = 5.25, 1.55
    rng = random.Random(21)
    shells, husks = [], []
    for k in range(7):
        a, d = rng.uniform(0, 6.28), rng.uniform(0.1, 0.5)
        px, py = cx + 0.4 + d * math.cos(a), cy + 0.25 + d * math.sin(a)
        if k < 4:
            h = K.lathe([(0.0, 0.0), (0.07, 0.005), (0.1, 0.04), (0.11, 0.08), (0.09, 0.085), (0.08, 0.05), (0.0, 0.02)], seg=8)
            flip = rng.random() < 0.5
            q = xf(h, (0, 0, 0.085 if flip else 0.0), (math.pi if flip else 0.2, 0, a))
            shells.append(paint(on_ground(q, px, py, 0.01), SHELL, var=0.08, ao=0.3, ao_h=0.06, ground=ground(px, py), top=0.25))
        else:
            q = K.smooth_rock(0.14, seed=230 + k, sub=2, amp=0.15, squash=(1.3, 0.9, 0.85), flat=1.0, relax=1)
            husks.append(paint(on_ground(q, px, py, 0.03), (0.52, 0.40, 0.22), var=0.1, ao=0.3, ao_h=0.1, ground=ground(px, py), top=0.2, namp=0.2, ns=12))
    for k in range(3):  # whole green coconuts
        px, py = cx - 0.35 + 0.22 * k, cy - 0.45 + 0.08 * k
        q = K.smooth_rock(0.12, seed=260 + k, sub=2, amp=0.08, squash=(1, 1, 1.05), flat=1.0, relax=1)
        husks.append(paint(on_ground(q, px, py, 0.02), (0.40, 0.48, 0.16) if k != 1 else (0.62, 0.52, 0.20), var=0.05, ao=0.25, ao_h=0.1, ground=ground(px, py), top=0.3))
    stool = [bx(0.55, 0.16, 0.05, (0, 0, 0.22), bev=0.01)] + [bx(0.05, 0.05, 0.22, (sx_, sy_, 0)) for sx_ in (-0.22, 0.22) for sy_ in (-0.05, 0.05)]
    stool.append(K.tube([(0.27, 0, 0.26), (0.42, 0, 0.36)], 0.02, seg=4))
    A.add("battle", "MatWood_timber", [paint(xf(q, (cx - 0.35, cy + 0.15, ground(cx, cy)), (0, 0, 0.6)), (0.46, 0.33, 0.21), ao=0.35, ao_h=0.2, ground=ground(cx, cy)) for q in stool])
    A.add("battle", "MatMetal_brass", paint(xf(xf(K.lathe([(0.0, 0.0), (0.04, 0.02), (0.035, 0.05), (0.0, 0.06)], seg=6), (0.42, 0, 0.33)), (cx - 0.35, cy + 0.15, ground(cx, cy)), (0, 0, 0.6)), (0.5, 0.5, 0.48), ao=0))
    A.add("battle", "MatWood_timber", shells + husks)
    A.add("battle", "MatWood_timber", paint(K.tube([(cx + 0.1, cy - 0.6, ground(cx, cy) + 0.02), (cx + 0.35, cy - 0.75, ground(cx, cy) + 0.02)], 0.018, seg=4), (0.3, 0.2, 0.12), ao=0))
    A.add("battle", "MatMetal_brass", paint(xf(K.box(0.42, 0.05, 0.01, bev=0.0), (cx + 0.6, cy - 0.88, ground(cx, cy) + 0.015), (0, 0, -0.55)), (0.42, 0.42, 0.42), ao=0))
    A.contact(cx + 0.3, cy, 1.0, 0.25)


def litter(A):
    rng = random.Random(41)
    n = 0
    while n < 130:
        if n % 4 == 0:   # under the rambutan / palms
            a, d = rng.uniform(0, 6.28), rng.uniform(0.3, 2.4)
            x, y = 9.3 + d * math.cos(a), 2.7 + d * math.sin(a)
            if rng.random() < 0.4:
                x, y = 8.4 + d * 0.7 * math.cos(a), -0.7 + d * 0.7 * math.sin(a)
        else:
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(5.8, 9.5)
            x, y = r * math.cos(a), r * math.sin(a)
        if path_dist(x, y) < 0.3 or not visible(x, y) or math.hypot(x, y) < 5.6:
            continue
        n += 1
        gz = ground(x, y)
        if n % 3 == 0:  # fallen leaves + lidi bits
            p = K.strip_mesh([(0, 0, 0), (0.06, 0.0, 0.006), (0.12, 0.0, 0.0)], [0.01, 0.03, 0.005], seed=n)
            A.add("battle", "MatLeaf_canopy", paint(xf(p, (x, y, gz + 0.006), (0, 0, rng.uniform(0, 6.3))), (0.62, 0.48, 0.20) if n % 2 else (0.48, 0.28, 0.14), ao=0, top=0))
        else:
            p = K.smooth_rock(rng.uniform(0.03, 0.07), seed=900 + n, sub=1, squash=(1, rng.uniform(0.6, 1), 0.55), relax=1)
            A.add("battle", "MatRock_stone", paint(xf(p, (x, y, gz - 0.01)), (0.52, 0.40, 0.30) if n % 2 else (0.40, 0.30, 0.22), ao=0.3, ao_h=0.04, ground=gz))


def leafy_mass(cx, cy, cz, r, h, n, seed, rgb, sub=2, spheres=None):
    """broken, leafy foliage mass: n jagged lumps on an ellipsoid shell around (cx, cy, cz), per-lump tone shifts
    and darker cores, so it reads as clumps of leaves rather than smooth balls. `spheres` collects (centre, radius)."""
    rng = random.Random(seed)
    out = []
    for j in range(n):
        if j == 0:
            c, rr = (cx, cy, cz), r * 0.62
        else:
            a = rng.uniform(0, 6.28)
            el = rng.uniform(-0.6, 0.9)
            c = (cx + r * 0.68 * math.cos(a) * math.cos(el), cy + r * 0.68 * math.sin(a) * math.cos(el), cz + h * 0.5 * math.sin(el))
            rr = r * rng.uniform(0.3, 0.44)
        q = xf(K.smooth_rock(rr, seed=seed * 17 + j, sub=sub, amp=0.42, freq=3.2, squash=(1, 1, 0.85), flat=0.7, relax=1), c)
        tone = rng.uniform(0.82, 1.15)
        paint(q, tuple(np.asarray(rgb) * tone), var=0.0, ao=0.45, ao_h=h * 1.4, ground=cz - h * 0.6, top=0.45, namp=0.3, ns=6)
        out.append(q)
        if spheres is not None:
            spheres.append((np.array(c), rr * 0.85))
    return out


def blossoms(pieces, n, seed, rgb, size=0.05):
    """small coloured flowers on upward/outward vertices of foliage lumps (flat 4-point stars, 2 tris each)."""
    rng = random.Random(seed)
    cand = []
    for q in pieces:
        nn = K.vnormals(q)
        for i in np.nonzero(nn[:, 2] > 0.15)[0]:
            cand.append((q.v[i], nn[i]))
    v, f, c = [], [], []
    for k in range(min(n, len(cand))):
        p0, nrm = cand[rng.randrange(len(cand))]
        p0 = p0 + nrm * 0.025
        s_ = size * rng.uniform(0.8, 1.3)
        rot = rng.uniform(0, 3.14)
        b = len(v)
        for t in range(4):
            ang = rot + t * math.pi / 2
            v.append((p0[0] + s_ * math.cos(ang) * (1 if t % 2 == 0 else 0.7), p0[1] + s_ * math.sin(ang) * (1 if t % 2 == 0 else 0.7), p0[2] + 0.01 * (t % 2)))
        f += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        k_ = rng.uniform(0.85, 1.1)
        c += [[min(1, x * k_) for x in rgb] + [1.0]] * 4
    return P(v, f, c)


def ampaian(A):
    """washing line between two posts with drying batik kain + sarong (colour accents, far band right)."""
    a, b = (5.6, 11.2), (9.6, 12.4)
    gz = ground(*a)
    wood = [bx(0.08, 0.08, 1.9, (a[0], a[1], ground(*a) - 0.05)), bx(0.08, 0.08, 1.9, (b[0], b[1], ground(*b) - 0.05))]
    line = K.arc((a[0], a[1], ground(*a) + 1.78), (b[0], b[1], ground(*b) + 1.78), -0.12, n=10)
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_DK, ao=0.3, ao_h=1.0, ground=gz) for q in wood])
    A.add("battle", "MatThatch_atap", paint(K.tube(line, 0.008, seg=3, cap=False), (0.7, 0.66, 0.56), ao=0))
    cols = [((0.70, 0.18, 0.14), (0.95, 0.72, 0.25)), ((0.18, 0.30, 0.58), (0.88, 0.86, 0.80)), ((0.20, 0.45, 0.30), (0.90, 0.62, 0.20)),
            ((0.62, 0.22, 0.42), (0.95, 0.85, 0.55))]
    for k, (t0, t1) in enumerate(((0.08, 0.28), (0.32, 0.5), (0.55, 0.72), (0.76, 0.93))):
        i0, i1 = int(t0 * 10), int(t1 * 10)
        top = [line[i] for i in range(i0, i1 + 1)]
        cl = K.strip_mesh([(x_, y_, z_ - 0.42) for x_, y_, z_ in top], [0.42] * len(top), up=(-(b[1] - a[1]), b[0] - a[0], 0), seed=k)
        cl.v[:, 2] += 0.0
        base, motif = cols[k]
        A.add("battle", "MatCloth_batik", tint(paint(cl, base, var=0.04, ao=0.0, top=0.0),
                                               lambda v, c, m=motif: np.where((K.nfield(v, 6.0, 33) > 0.25)[:, None], np.array(list(m) + [1.0]), c)))
    A.contact(*a, 0.4, 0.3)
    A.contact(*b, 0.4, 0.3)


def shrubs(A):
    """bunga raya (hibiscus) shrubs: near strip (vista foreground, <=1.2 m) + along the yard edge."""
    for k, (x, y, s) in enumerate(((2.3, -6.6, 0.85), (-2.6, -7.5, 0.9), (5.8, -5.6, 0.85), (-8.2, 5.6, 1.0), (6.4, 8.9, 0.9))):
        gz = ground(x, y)
        cz = gz + 0.36 * s
        sph = []
        lumps = leafy_mass(x, y, cz, 0.6 * s, 0.7 * s, 9, 400 + k, (0.17, 0.32, 0.11), spheres=sph)
        A.add("battle", "MatLeaf_canopy", lumps)
        A.add("battle", "MatLeaf_canopy", K.dbl(blossoms(lumps, 22, 450 + k, (0.92, 0.14, 0.10), size=0.065)))
        A.contact(x, y, 0.9 * s, 0.3)
        A.scatter_patch("Grass", 26, x, y, 0.9 * s, ground, GRASS_TINT, seed=420 + k)


def palms(A):
    """right flank: two dwarf palms (crowns inside the battle frame) + one tall leaning palm framing the vista."""
    spots = [(8.4, -0.7, 4.2, -0.3, 3), (7.3, 5.9, 3.4, 0.9, 5), (10.6, 6.6, 9.5, -1.9, 9)]
    for k, (x, y, h, ld, seed) in enumerate(spots):
        tr, lf, nu = K.hero_palm(h, seed=seed, fronds=14 if h < 7 else 15, bend=0.9 if h < 7 else 1.3, lean_dir=ld, leaflets=17,
                                 leaf_rgb=LEAF_PALM, old_rgb=(0.55, 0.52, 0.22), nuts=7 if h < 7 else 6)
        gz = ground(x, y)
        A.add("battle", "MatWood_timber", [xf(tr, (x, y, gz - 0.05)), xf(nu, (x, y, gz - 0.05))])
        A.add("battle", "MatLeaf_canopy", xf(lf, (x, y, gz - 0.05)))
        A.contact(x, y, 1.0, 0.3)
        A.scatter_patch("Grass", 28, x, y, 1.1, ground, GRASS_TINT, seed=600 + k)


def rambutan(A, x, y):
    w, _ = K.broadleaf_tree(4.3, 2.0, seed=17, lumps=1, trunk_r=0.15, branches=4, squash=0.75, sub=1)
    gz = ground(x, y)
    w = paint(xf(w, (x, y, gz)), (0.36, 0.28, 0.20), var=0.06, ao=0.45, ao_h=1.5, ground=gz, namp=0.12, ns=3)
    l = leafy_mass(x, y, gz + 3.2, 2.0, 1.9, 15, 707, (0.20, 0.34, 0.13))
    fruit = []
    rng = random.Random(708)
    for k in range(16):  # rambutan bunches: hairy red clusters hanging on the outer shell
        a, el = rng.uniform(0, 6.28), rng.uniform(-0.3, 0.7)
        c = (x + 2.0 * 0.92 * math.cos(a) * math.cos(el), y + 2.0 * 0.92 * math.sin(a) * math.cos(el), gz + 3.2 + 0.95 * math.sin(el))
        q = xf(K.smooth_rock(0.13, seed=760 + k, sub=1, amp=0.4, freq=4.0, squash=(1, 1, 1.2), flat=1.0, relax=0), c)
        fruit.append(paint(q, (0.80, 0.13, 0.08) if k % 4 else (0.90, 0.48, 0.10), var=0.1, ao=0.0, top=0.25))
    l = l + fruit
    A.add("battle", "MatWood_timber", w)
    A.add("battle", "MatLeaf_canopy", l)
    A.contact(x, y, 2.4, 0.38)
    A.scatter_patch("Grass", 26, x, y, 2.0, ground, (0.36, 0.46, 0.18), seed=707)
    rng = random.Random(70)
    fr = []
    for k in range(9):  # fallen fruit
        a, d = rng.uniform(0, 6.28), rng.uniform(0.6, 2.0)
        px, py = x + d * math.cos(a), y + d * math.sin(a)
        fr.append(paint(on_ground(K.smooth_rock(0.035, seed=720 + k, sub=1, flat=1.0, relax=1), px, py, 0.0), (0.72, 0.14, 0.08), ao=0.2, ao_h=0.04, ground=ground(px, py)))
    A.add("battle", "MatLeaf_canopy", fr)


# ---------------------------------------------------------------- far set
def far_house(A, x, y, rz, seed, roof="atap", wall=(0.56, 0.42, 0.29)):
    rng = random.Random(seed)
    W, D, FH, WH = rng.uniform(5.0, 6.5), rng.uniform(3.6, 4.4), rng.uniform(1.2, 1.6), 2.2
    gz = ground(x, y)
    wood = []
    for sx in (-0.45, 0.0, 0.45):
        for sy in (-0.45, 0.45):
            wood.append(bx(0.16, 0.16, FH + 0.1, (sx * W, sy * D, -0.05)))
    body = bx(W, D, WH, (0, 0, FH), bev=0.03)
    wins = [bx(0.7, 0.06, 1.0, (sx, -D / 2 - 0.02, FH + 0.6)) for sx in (-W * 0.28, 0.0, W * 0.28)]
    shut = [bx(0.32, 0.04, 1.0, (sx + s * 0.55, -D / 2 - 0.12, FH + 0.6), (0, 0, s * 0.9)) for sx in (-W * 0.28, W * 0.28) for s in (-1, 1)]
    rise = rng.uniform(1.6, 2.1)
    over = 0.5
    Dd = D / 2 + over
    drop = rise * Dd / (D / 2)
    slopes = [xf(atap_slope(W + 1.0, Dd, drop, courses=2 if roof == "atap" else 1, cw=0.9, seed=seed * 3 + s, tooth=0.08), (0, 0, FH + WH + rise),
                 (0, 0, 0 if s == 0 else math.pi)) for s in (0, 1)]
    gables = []
    for gx in (-1, 1):
        g = sunburst(0, 0, FH + WH, D / 2 + 0.05, rise - 0.05, n=7, out=gx)
        g = xf(g, (gx * (W / 2 + 0.03), 0, 0), (0, 0, math.pi / 2))
        g.c[:, :3] = np.array((0.66, 0.54, 0.38))
        gables.append(K.dbl(g))
    put = lambda q: K.cull_back(xf(q, (x, y, gz), (0, 0, rz)))
    A.add("far", "MatWood_timber", [paint(put(q), TIMBER_DK, ao=0.35, ao_h=1.5, ground=gz) for q in wood + wins])
    A.add("far", "MatWood_timber", [paint(put(q), (0.70, 0.56, 0.38), ao=0.0) for q in shut])
    A.add("far", "MatWood_timber", paint(put(body), wall, var=0.05, ao=0.3, ao_h=2.5, ground=gz + FH, namp=0.08, ns=1.5))
    A.add("far", "MatWood_timber", [put(q) for q in gables])
    if roof == "atap":
        A.add("far", "MatThatch_atap", [tint(paint(put(q), ATAP, var=0.06, top=0.25, namp=0.2, ns=1.2), course_tint(gz + FH + WH + rise, drop, 2)) for q in slopes])
    else:  # zinc: corrugation stripes + rust
        A.add("far", "MatTile_roof", [tint(paint(put(q), (0.56, 0.54, 0.52), var=0.05, top=0.3, namp=0.3, ns=0.6),
                                           lambda v, c: c * np.where((K.nfield(v, 0.5, seed) > 0.2)[:, None], np.array([1.1, 0.72, 0.52, 1]), 1.0)) for q in slopes])
    A.contact(x, y, 4.0, 0.2)


def surau(A, x, y):
    """kampung surau: plinth, cream walls with arched openings, verandah, 3-tier tajug pyramid roof + finial."""
    gz = ground(x, y)
    parts_w, parts_r = [], []
    parts_w.append(bx(8.4, 8.4, 0.7, (0, 0, -0.2), bev=0.05))
    body = bx(6.6, 6.6, 3.4, (0, 0, 0.5), bev=0.05)
    wins = [bx(0.9, 0.08, 1.9, (sx, -3.32, 1.0)) for sx in (-2.0, 0.0, 2.0)]
    wins += [bx(0.08, 0.9, 1.9, (-3.32, sy, 1.0)) for sy in (-2.0, 0.0, 2.0)]
    cols = [bx(0.25, 0.25, 2.9, (sx, -4.0, 0.5)) for sx in (-3.9, -1.3, 1.3, 3.9)]
    for k, (s0, s1, z0, z1) in enumerate(((5.6, 3.0, 3.9, 5.4), (3.4, 1.9, 6.0, 7.1), (2.1, 0.4, 7.6, 9.3))):
        tier = K.lathe([(s0 * 1.414, z0), (s1 * 1.414, z1)], seg=4, phase=math.pi / 4, cap0=False, cap1=(k == 2))
        lip = K.lathe([(s0 * 1.414, z0 - 0.08), (s0 * 1.414 + 0.05, z0), (s0 * 1.414, z0 + 0.02)], seg=4, phase=math.pi / 4, cap0=False, cap1=False)
        parts_r += [tier, lip]
        if k < 2:  # clerestory between tiers
            parts_w.append(bx(s1 * 1.414 * 0.62, s1 * 1.414 * 0.62, 0.6 if k == 0 else 0.5, (0, 0, z1 - 0.05)))
    finial = K.lathe([(0.0, 9.2), (0.22, 9.3), (0.32, 9.6), (0.12, 9.9), (0.05, 10.4), (0.0, 10.7)], seg=8)
    put = lambda q: K.cull_back(xf(q, (x, y, gz), (0, 0, 0.12)))
    A.add("far", "MatWood_timber", [paint(put(q), (0.80, 0.75, 0.64), var=0.03, ao=0.3, ao_h=2.0, ground=gz) for q in parts_w + [body] + cols])
    A.add("far", "MatWood_timber", [paint(put(q), (0.22, 0.30, 0.26), ao=0.0) for q in wins])
    A.add("far", "MatTile_roof", [tint(paint(put(q), (0.50, 0.24, 0.16), var=0.04, top=0.35, namp=0.15, ns=1.0),
                                       lambda v, c: c * (0.86 + 0.14 * (np.floor(v[:, 2] * 3.0) % 2))[:, None]) for q in parts_r])
    A.add("far", "MatTile_roof", paint(put(finial), BRASS, ao=0.0, top=0.3))


def far_palms(A):
    rng = random.Random(77)
    placed = 0
    tries = 0
    while placed < 24 and tries < 400:
        tries += 1
        a = math.radians(rng.uniform(-44, 40))
        d = rng.uniform(32, 95)
        x, y = -1.5 + d * math.sin(a), -12.5 + d * math.cos(a)
        if math.hypot(x, y) < 24 or abs(x - 16) < 6 and abs(y - 42) < 6:
            continue
        placed += 1
        h = rng.uniform(9.0, 14.5)
        tr, lf = K.coconut_palm(h, seed=800 + placed, fronds=7)
        gz = ground(x, y)
        A.add("far", "MatWood_timber", paint(xf(tr, (x, y, gz - 0.1)), (0.46, 0.38, 0.29), ao=0.3, ao_h=3, ground=gz, top=0.0))
        A.add("far", "MatLeaf_canopy", paint(xf(lf, (x, y, gz - 0.1)), (0.28, 0.38, 0.15), var=0.12, ao=0.0, top=0.35, namp=0.15, ns=1))


def far_trees(A):
    """mango / durian / bamboo masses between the far houses (dark rounded silhouettes)."""
    rng = random.Random(55)
    for k in range(16):
        a = math.radians(rng.uniform(-50, 42))
        d = rng.uniform(28, 85)
        x, y = -1.5 + d * math.sin(a), -12.5 + d * math.cos(a)
        if math.hypot(x, y) < 24:
            continue
        h = rng.uniform(6, 11)
        b = K.canopy(h * 0.42, seed=900 + k, lumps=4, sub=2, squash=0.8, spread=0.8)
        gz = ground(x, y)
        A.add("far", "MatLeaf_canopy", K.cull_back(paint(xf(b, (x, y, gz + h * 0.45)), (0.17, 0.27, 0.12), var=0.12, ao=0.35, ao_h=h, ground=gz, top=0.4, namp=0.2, ns=0.5)))
        A.add("far", "MatWood_timber", paint(K.tube([(x, y, gz - 0.1), (x + 0.2, y, gz + h * 0.5)], [0.3, 0.2], seg=5), (0.30, 0.24, 0.18), ao=0))


def far_details(A):
    """midground between the yard and the far houses: hibiscus/croton hedge along the yard, bamboo fence along the
    lane, banana clumps beside the houses."""
    rng = random.Random(91)
    for k in range(14):  # hedge
        t = k / 13
        x, y = -6.0 + 26.0 * t, 14.5 + 2.5 * math.sin(t * 3.0) + rng.uniform(-0.4, 0.4)
        q = xf(K.smooth_rock(rng.uniform(0.6, 0.9), seed=950 + k, sub=2, amp=0.4, freq=2.6, squash=(1.4, 1, 0.8), flat=0.5, relax=1), (x, y, ground(x, y) - 0.1))
        q = paint(q, (0.18, 0.31, 0.12) if k % 3 else (0.30, 0.34, 0.12), var=0.1, ao=0.4, ao_h=1.0, ground=ground(x, y), top=0.4, namp=0.25, ns=3)
        tint(q, lambda v, c, k=k: np.where((K.nfield(v, 4.0, 960 + k) > 0.45)[:, None], np.array([0.86, 0.20, 0.12, 1.0]) if k % 2 else np.array([0.92, 0.70, 0.18, 1.0]), c))
        A.add("far", "MatLeaf_canopy", K.cull_back(q))
    posts = []
    for k in range(16):  # bamboo pagar along the lane to the far kampung
        t = k / 15
        x, y = 9.8 + 4.5 * t, 16.5 + 12.0 * t
        posts.append(xf(K.post(1.0, 0.035, seed=k, seg=5), (x - 0.8, y, ground(x - 0.8, y) - 0.05)))
    for zz in (0.45, 0.85):
        posts.append(K.tube([(9.0, 16.5, ground(9, 16.5) + zz), (13.5, 28.5, ground(13.5, 28.5) + zz)], 0.025, seg=4))
    A.add("far", "MatWood_timber", [paint(q, (0.62, 0.56, 0.34), ao=0.2, ao_h=0.8, ground=0.0) for q in posts])
    for k, (x, y) in enumerate(((3.0, 29.0), (12.5, 33.5), (21.0, 28.0), (-9.5, 33.0), (28.5, 41.0))):
        for j in range(2):
            px, py = x + 0.9 * j, y - 0.5 * j
            st, lv = K.banana(rng.uniform(2.6, 3.4), seed=970 + k * 2 + j, leaves=5)
            gz = ground(px, py)
            A.add("far", "MatLeaf_canopy", paint(xf(lv, (px, py, gz - 0.05), (0, 0, rng.uniform(0, 6.28))), BANANA, var=0.08, ao=0.3, ao_h=2.4, ground=gz, top=0.3))
            A.add("far", "MatWood_timber", paint(xf(st, (px, py, gz - 0.05)), (0.42, 0.44, 0.24), ao=0.3, ao_h=1.2, ground=gz))


def backdrop(A):
    """painted golden-hour set: forested hill line, Titiwangsa ranges, far peaks, warm clouds (Sky kind, fog-free)."""
    A.add("far", "MatSky_backdrop", K.ridge_layer(150, az=(-54, 42), base=3.0, amp=16, seed=21, hills=12, ridge=0.0, canopy=1.0,
                                                  top=(0.40, 0.42, 0.33), bottom=(0.74, 0.62, 0.46), cols=90))
    A.add("far", "MatSky_backdrop", K.ridge_layer(230, az=(-54, 42), base=10, amp=26, seed=24, hills=8, ridge=0.3,
                                                  top=(0.56, 0.52, 0.56), bottom=(0.86, 0.68, 0.52), cols=70))
    A.add("far", "MatSky_backdrop", K.ridge_layer(330, az=(-54, 42), base=18, amp=34, seed=27, hills=6, ridge=0.55,
                                                  top=(0.74, 0.62, 0.62), bottom=(0.95, 0.72, 0.52), cols=60))
    K.cloud_bank(A, n=6, dist=(320, 450), el=(5.5, 12.5), seed=31, mat="MatSky_backdrop",
                 top=(1.0, 0.90, 0.72), mid=(1.0, 0.76, 0.56), base=(0.86, 0.60, 0.52))


# ---------------------------------------------------------------- build
def build(A):
    for name in ("MatGround_laterite", "MatGrass_lawn", "MatWood_timber", "MatThatch_atap", "MatLeaf_canopy", "MatRock_stone",
                 "MatCloth_batik", "MatMetal_brass", "MatTile_roof", "MatWater_well", "MatSky_backdrop"):
        A.mat(name)
    A.mat("MatGlow_pelita", emit=(1.0, 0.72, 0.4), estr=4.0)

    rumah(A)
    perigi(A)
    reban(A)
    para_kayu(A)
    banana_clump(A, -7.6, 7.4, seed=31)
    banana_clump(A, 12.2, 5.6, seed=37, n=3)
    apron(A)
    litter(A)
    shrubs(A)
    palms(A)
    rambutan(A, 9.3, 2.7)
    ampaian(A)

    A.terrain(ground, gcolor, kind=gkind, rin=4.5, rout=130.0, split=23.0, cull=gcull, seed=2)

    # grass: verge ring around the swept yard + lawn fields beyond + clumps in the near strip
    rng = random.Random(3)
    for k in range(150):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.98, 1.5)
        dy_ = YAY_FAR if math.sin(a) > 0 else YAY_NEAR
        x, y = YC[0] + YAX * d * math.cos(a), YC[1] + dy_ * d * math.sin(a)
        if not visible(x, y) or path_dist(x, y) < 0.5 or (HOUSE["x0"] - 0.5 < x < SERAMBI_X and HOUSE["y0"] - 0.5 < y < HOUSE["y1"] + 0.5):
            continue
        A.scatter_patch("Grass", 30 if d < 1.2 else 22, x, y, rng.uniform(0.6, 1.4), ground, GRASS_TINT, seed=1000 + k)
    for k in range(40):
        x, y = rng.uniform(-6, 6), rng.uniform(-9.5, -6.2)
        if path_dist(x, y) < 0.5:
            continue
        A.scatter_patch("Grass", 30, x, y, rng.uniform(0.4, 0.9), ground, GRASS_TINT, seed=1200 + k)

    # far set
    for k, (x, y, rz, roof, wall) in enumerate(((6.5, 30, 0.25, "atap", (0.56, 0.42, 0.29)), (17.5, 25.5, -0.35, "zinc", (0.60, 0.72, 0.70)),
                                                (26, 34, 0.1, "atap", (0.58, 0.44, 0.30)), (-6, 38, -0.15, "zinc", (0.82, 0.76, 0.56)),
                                                (33, 47, 0.4, "zinc", (0.56, 0.66, 0.78)), (7, 50, 0.05, "atap", (0.52, 0.40, 0.28)),
                                                (-17, 30, 0.3, "atap", (0.56, 0.42, 0.29)), (44, 30, -0.5, "atap", (0.60, 0.46, 0.32)))):
        far_house(A, x, y, rz, seed=k, roof=roof, wall=wall)
    surau(A, 16.5, 41.5)
    far_palms(A)
    far_trees(A)
    far_details(A)
    backdrop(A)


if __name__ == "__main__":
    K.main("kampung", build, MOOD)
