"""Kelantan arena -- wau festival on a harvested padi field by the casuarina coast, windy gold afternoon
(design_art.md section c; USER_SPEC: a wau bulan rising against the wind, carvers at work).
Ground: trodden sandy yard around the dish, kite-maker's workspace behind it, stubble field (golden rows)
with grassy bunds all round. Apron: unpapered wau frames on a mat, string reels, bamboo strips.
Far band: finished waus laid flat on mengkuang mats, a drying rack, straw stacks.
Left flank: kite-maker's house (singgora tile roof, tebar layar gable, carved kerawang panels).
Right flank: nasi kerabu stall, an upright wau on its stand, festival pennants and casuarinas
streaming toward +x (wind hazard dir +x).
Far set (vista): stubble plain, kampung roofs, casuarina beach + sea, waus flying, wind-streaked clouds.

  blender -b --factory-startup -P art_src/arena_kelantan.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)
import numpy as np
from arenakit import P, xf, join, paint, tint, nz, smooth01

# Godot ARENA_DEFS["kelantan"] recommendation (+ b_* = Blender preview factors only)
MOOD = {"sky_top": (0.12, 0.40, 0.88), "sky_horizon": (0.98, 0.82, 0.58), "fog": (0.92, 0.82, 0.64),
        "fog_density": 0.0026, "sun_color": (1.0, 0.84, 0.58), "sun_energy": 1.2,
        "lantern": (1.0, 0.74, 0.42), "lantern_energy": 1.2, "exposure": 1.0, "ambient": 0.5,
        "b_sun": 3.8, "b_world": 1.0, "b_fill": 0.4, "b_lantern": 10.0}

# ---------------------------------------------------------------- palette (sRGB)
YARD = (0.62, 0.51, 0.34)
YARD_LT = (0.72, 0.60, 0.40)
SOIL = (0.62, 0.50, 0.28)     # gold stubble base (windy gold afternoon)
STRAW_G = (0.80, 0.68, 0.40)
GRASSY = (0.42, 0.48, 0.22)
DAMP = (0.44, 0.38, 0.29)
SAND = (0.80, 0.72, 0.56)
TIMBER = (0.50, 0.36, 0.24)
TIMBER_LT = (0.62, 0.48, 0.32)
TIMBER_DK = (0.25, 0.17, 0.11)
BAMBOO = (0.66, 0.58, 0.38)
TILE = (0.62, 0.30, 0.18)
MAT = (0.66, 0.56, 0.36)
STRAW = (0.70, 0.58, 0.33)
STUBBLE = (0.70, 0.60, 0.34)
GRASS_T = (0.42, 0.50, 0.22)
LEAF_DK = (0.18, 0.28, 0.16)
CASU = (0.22, 0.34, 0.21)
SEA = (0.24, 0.42, 0.46)
CLAY = (0.58, 0.34, 0.22)
IRON = (0.26, 0.25, 0.24)
# wau colours: (base, border, band, motif)
WAU_COLS = [((0.70, 0.12, 0.10), (0.08, 0.07, 0.10), (0.92, 0.70, 0.18), (0.12, 0.32, 0.62)),
            ((0.10, 0.30, 0.62), (0.08, 0.07, 0.10), (0.94, 0.78, 0.25), (0.76, 0.16, 0.12)),
            ((0.92, 0.68, 0.14), (0.42, 0.06, 0.06), (0.74, 0.14, 0.10), (0.12, 0.40, 0.28)),
            ((0.12, 0.42, 0.30), (0.08, 0.07, 0.10), (0.94, 0.80, 0.30), (0.74, 0.14, 0.12)),
            ((0.88, 0.86, 0.80), (0.10, 0.20, 0.50), (0.74, 0.16, 0.12), (0.92, 0.70, 0.18))]

# ---------------------------------------------------------------- layout
AX, AYF, AYN, PW = 6.7, 6.3, 5.8, 2.4         # trodden platform around the dish (superellipse)
HOUSE = (-10.1, 1.7, 0.0)                       # kite-maker's house centre (x, y, rot); gable faces +x
STALL = (8.9, 3.1, -0.45)                      # nasi kerabu stall
YARDS = [(-9.6, 1.7, 3.9, 3.4), (-1.0, 7.6, 6.8, 2.3), (8.7, 3.4, 3.0, 3.2)]   # (x, y, rx, ry) bare earth
BUND_X = [-50.5, -38.5, -26.5, -14.5, 13.5, 25.5, 37.5, 49.5]
BUND_Y = [-31.0, -19.0, -7.4, 11.0, 23.0, 35.0, 47.0]
PATHS = [[(-4.9, 1.3), (-6.6, 1.6), (-7.4, 1.7)], [(4.6, 2.2), (6.3, 2.8), (7.4, 3.0)],
         [(-1.0, 4.4), (-0.6, 6.0), (0.2, 9.5), (1.0, 13.0), (2.0, 24.0), (3.5, 40.0), (5.0, 56.0)],
         [(1.2, -4.5), (1.6, -6.4), (2.2, -9.5), (3.2, -14.0)]]
BEACH_Y = 58.0                                  # casuarina belt + beach run across the vista


def plat_d(x, y):
    ay = AYF if y > 0 else AYN
    return ((abs(x) / AX) ** PW + (abs(y) / ay) ** PW) ** (1.0 / PW)


def seg_dist(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


def path_dist(x, y):
    return min(seg_dist(x, y, a, b) for pl in PATHS for a, b in zip(pl[:-1], pl[1:]))


def yard_w(x, y):
    """1 on bare trodden earth (platform + work yards), 0 in the field."""
    w = 1.0 - smooth01(0.95, 1.12, plat_d(x, y))
    for (cx, cy, rx, ry) in YARDS:
        d = math.hypot((x - cx) / rx, (y - cy) / ry)
        w = max(w, 1.0 - smooth01(0.8, 1.05, d + 0.12 * nz(x, y, 0, 0.6, 7)))
    return w


def bund_d(x, y):
    d = min(min(abs(x - b) for b in BUND_X), min(abs(y - b) for b in BUND_Y))
    return d


def beach(y):
    return smooth01(BEACH_Y - 6.0, BEACH_Y + 2.0, y)


def ground(x, y):
    yw = yard_w(x, y)
    field = -0.07 + 0.02 * nz(x, y, 0, 0.9, 3) + 0.012 * nz(x, y, 0, 3.1, 4)
    bd = bund_d(x, y)
    if math.hypot(x, y) < 70:
        field = max(field, 0.11 - 0.36 * smooth01(0.0, 0.62, bd))      # low grassy bunds (batas)
    h = field * (1 - yw) + (0.03 + 0.015 * nz(x, y, 1, 0.8, 5)) * yw
    pd = path_dist(x, y)
    if pd < 0.7:
        h -= 0.025 * (1 - smooth01(0.15, 0.7, pd))
    b = beach(y)
    if b > 0:  # beach dune -> sand slope -> sea
        h = h * (1 - b) + b * (0.25 + 0.2 * nz(x, y, 0, 0.15, 9) - 1.1 * smooth01(BEACH_Y + 9, BEACH_Y + 16, y))
    return float(h)


def in_vista(x, y):
    dx, dy = x + 1.5, y + 12.5
    return dy > 2 and -58 < math.degrees(math.atan2(dx, dy)) < 44


def visible(x, y, pad=0.0):
    return (y > -6.5 - pad and abs(x) < 11 + 0.55 * (y + 6.5) + pad) or in_vista(x, y)


def mix(a, b, t):
    return np.asarray(a, dtype=float) * (1 - t) + np.asarray(b, dtype=float) * t


def gcolor(x, y, z):
    n1 = nz(x, y, 0, 0.42, 11)
    n2 = nz(x, y, 0, 2.1, 12)
    n3 = nz(x, y, 0, 6.5, 13)
    yw = yard_w(x, y)
    pd = path_dist(x, y)
    field = np.array(SOIL) * (1 + 0.1 * n1 + 0.07 * n2 + 0.04 * n3)
    field = mix(field, STRAW_G, 0.55 * smooth01(-0.2, 0.5, nz(x, y, 0, 0.3, 14)))     # strewn straw
    field = mix(field, DAMP, 0.25 * smooth01(0.25, 0.7, nz(x, y, 0, 0.5, 15)))
    field = mix(field, np.array(GRASSY) * (1 + 0.1 * n2), 0.85 * (1 - smooth01(0.15, 0.75, bund_d(x, y))))
    yard = np.array(YARD) * (1 + 0.08 * n1 + 0.06 * n2 + 0.05 * n3)
    yard = mix(yard, YARD_LT, 0.45 * smooth01(0.1, 0.55, nz(x, y, 0, 0.55, 16)) * smooth01(7.0, 9.0, math.hypot(x, y)))
    yard = mix(yard, np.array(GRASSY) * 0.95, 0.65 * smooth01(0.05, 0.6, n1) * smooth01(0.3, 1.0, pd) * smooth01(5.6, 7.0, math.hypot(x, y)))
    c = mix(field, yard, yw)
    c = mix(c, np.array(GRASSY) * (1 + 0.08 * n2), 0.55 * yw * (1 - yw) * 4 * smooth01(0.3, 0.8, pd))  # verge
    c = mix(c, YARD_LT, 0.55 * (1 - smooth01(0.0, 0.6, pd)))                                         # worn paths
    r = math.hypot(x, y)
    c = mix(c, np.array(YARD) * 0.96, 0.6 * (1 - smooth01(4.6, 5.6, r)))                             # apron
    b = beach(y)
    if b > 0:
        c = mix(c, np.array(SAND) * (1 + 0.06 * n2), b)
    return tuple(c)


def gkind(x, y, z):
    return "MatGround_field"


def gcull(cx, cy, zmax):
    if cy > BEACH_Y + 15 and zmax < SEA_Z - 0.05:
        return True
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


SEA_Z = -0.45


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


# ---------------------------------------------------------------- local helpers (kit is frozen)
def cells(grid, colfn, flip=False):
    """per-face quads (unique verts -> crisp cut-paper colours). grid[i][j] = (x, y, z)."""
    v, f, c = [], [], []
    R, C = len(grid) - 1, len(grid[0]) - 1
    for i in range(R):
        for j in range(C):
            q = [grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]]
            if flip:
                q = q[::-1]
            b = len(v)
            v += q
            f.append((b, b + 1, b + 2, b + 3))
            col = colfn(i, j, R, C)
            c += [list(col) + [1.0]] * 4
    return P(v, f, c)


def wau(H=2.2, cols=WAU_COLS[0], bow=True, paper=True, seed=0):
    """wau bulan, upright in local XZ, facing -y, crescent bottom at z=0. Returns (cloth, frame).
    Wings with swept tips, waist, crescent-moon tail with horns up, head, busur bow, tassels."""
    base, border, band, motif = cols
    s = H

    def ring_col(i, j, R, C, edge_rows=1):
        d = min(i, R - 1 - i)
        if d < edge_rows:
            return border
        if d < edge_rows + 1:
            return band
        return motif if (j + 2 * i) % 4 == 0 else base

    def pt(u, v, k=0.0):
        return (u * s, -0.05 * s * (1 - (u / 0.66) ** 2) + k, v * s)

    cl = []
    if paper:
        # wings: columns across the span, rows bottom->top
        C, R = 22, 6
        g = []
        for i in range(R + 1):
            row = []
            for j in range(C + 1):
                sj = -1 + 2 * j / C
                a = abs(sj)
                top = 0.87 - 0.04 * a + 0.07 * a ** 6
                bot = 0.585 + 0.315 * a ** 2.6
                row.append(pt(0.66 * sj, bot + (top - bot) * i / R))
            g.append(row)
        cl.append(cells(g, lambda i, j, R, C: ring_col(i, j, R, C) if 2 < j < C - 3 else (border if i in (0, R - 1) else band)))
        # crescent tail (outer -> inner rows), horns up
        C, R = 22, 5
        a0, a1, cy, Ro = math.radians(198), math.radians(342), 0.63, 0.52
        g = []
        for i in range(R + 1):
            row = []
            for j in range(C + 1):
                a = a0 + (a1 - a0) * j / C
                w = 0.2 * math.sin(math.pi * j / C) ** 0.75
                rr = Ro - w * i / R
                row.append(pt(rr * math.cos(a), cy + rr * math.sin(a)))
            g.append(row)
        cl.append(cells(g, lambda i, j, R, C: ring_col(i, j, R, C) if 1 < j < C - 2 else border, flip=True))
        # waist + head (narrow strips along v)
        for (v0, v1, wfn) in ((0.30, 0.62, lambda t: 0.055 + 0.03 * (1 - t)), (0.86, 1.03, lambda t: 0.075 * math.sin(math.pi * min(1, t * 1.1)) + 0.005)):
            R = 4
            g = []
            for i in range(R + 1):
                t = i / R
                w = wfn(t)
                g.append([pt(-w, v0 + (v1 - v0) * t, -0.002), pt(0, v0 + (v1 - v0) * t, -0.002), pt(w, v0 + (v1 - v0) * t, -0.002)])
            cl.append(cells(g, lambda i, j, R, C: band if i in (0, R - 1) else (motif if i == 2 else base)))
        # tassels (rambu) at the wing tips and horns
        for (u, v) in ((-0.66, 0.90), (0.66, 0.90), (Ro * math.cos(a0), cy + Ro * math.sin(a0)), (Ro * math.cos(a1), cy + Ro * math.sin(a1))):
            q = K.strip_mesh([pt(u, v), pt(u * 1.05, v - 0.07), pt(u * 1.08, v - 0.16)], [0.02 * s, 0.025 * s, 0.01 * s], up=(0, 1, 0), seed=seed)
            q.c = np.tile(list(band) + [1.0], (len(q.v), 1))
            cl.append(q)
    fr = []
    r = 0.012 * s
    fr.append(K.tube([pt(0, 0.1, 0.01), pt(0, 0.6, 0.01), pt(0, 1.05, 0.01)], r, seg=5))                       # spine
    fr.append(K.tube([pt(-0.66 + 0.66 * 2 * k / 8, 0.87 - 0.04 * abs(-1 + 2 * k / 8) + 0.07 * abs(-1 + 2 * k / 8) ** 6, 0.012) for k in range(9)], r * 0.8, seg=4))
    fr.append(K.tube([pt(0.52 * math.cos(a), 0.63 + 0.52 * math.sin(a), 0.012) for a in np.linspace(math.radians(198), math.radians(342), 10)], r * 0.8, seg=4))
    if not paper:  # bare frame: inner ribs
        fr.append(K.tube([pt(-0.62, 0.70, 0.01), pt(0, 0.62, 0.01), pt(0.62, 0.70, 0.01)], r * 0.7, seg=4))
        fr.append(K.tube([pt(0.36 * math.cos(a), 0.63 + 0.36 * math.sin(a), 0.01) for a in np.linspace(math.radians(205), math.radians(335), 8)], r * 0.7, seg=4))
    if bow:  # busur (hummer bow) above the head
        fr.append(K.tube([pt(-0.46, 0.93, 0.03), pt(-0.2, 1.06, 0.03), pt(0, 1.09, 0.03), pt(0.2, 1.06, 0.03), pt(0.46, 0.93, 0.03)], r * 0.9, seg=4))
    return (join(cl) if cl else None), join(fr)


def face_cam(p, x, y, z):
    """turn a -y-facing card toward the vista eye and place it at (x, y, z)."""
    return K.face_eye(p, (x, y, z))


def casuarina(h=9.0, seed=0, lean=0.9, lod=0):
    """rhu (casuarina): slim leaning trunk, wispy pendulous clumps flagged downwind (+x). (wood, leaf)."""
    rng = random.Random(seed)
    pts = []
    for t in np.linspace(0, 1, 6):
        pts.append((lean * h * 0.18 * t ** 1.6 + 0.15 * math.sin(t * 5 + seed), 0.1 * math.sin(t * 3 + seed), h * 0.82 * t))
    wood = [K.tube(pts, [0.16, 0.13, 0.11, 0.09, 0.07, 0.05], seg=6 if not lod else 4)]
    leaf = []
    nclump = 3 if lod else 5
    for k in range(nclump):
        t = 0.45 + 0.55 * k / max(1, nclump - 1)
        c = np.array(pts[min(5, int(t * 5 + 0.5))])
        off = np.array((0.5 + rng.uniform(0.0, 0.9) * (1 - t * 0.5), rng.uniform(-0.6, 0.6), rng.uniform(-0.3, 0.3)))
        rr = h * (0.15 - 0.06 * t) * rng.uniform(0.85, 1.15)
        b = K.canopy(rr, seed=seed * 11 + k, lumps=2 if lod else 3, sub=1 if lod else 2, squash=0.7, spread=0.6)
        b.v[:, 0] *= 1.35  # stretched downwind
        z = b.v[:, 2]
        b.v[:, 2] -= 0.35 * np.clip(-z, 0, None)  # droop the skirts
        leaf.append(xf(b, tuple(c + off)))
        if not lod and k < nclump - 1:  # bare branch into each clump
            wood.append(K.tube([tuple(c), tuple(c + off * 0.8)], [0.05, 0.025], seg=4))
    return join(wood), join(leaf)


def straw_stack(r=0.9, h=1.0, seed=0, seg=18):
    """timbunan jerami: domed straw stack with a ragged skirt."""
    prof = [(0.0, -0.05), (r * 1.08, -0.05), (r * 1.05, h * 0.12), (r * 0.95, h * 0.45), (r * 0.7, h * 0.78), (r * 0.32, h * 0.97), (0.0, h)]
    return K.lathe(prof, seg=seg, cap0=False, cap1=False,
                   rfn=lambda a, t: 1.0 + 0.07 * math.sin(a * 7 + seed) + 0.05 * math.sin(a * 13 + seed * 2) * (1 - t))


def perforated(w, h, nx, ny, keep, tri=False):
    """flat panel in local XZ (faces -y), base at z=0, centred in x; keep(i, j, u, v) decides each cell
    (carved kerawang fretwork). tri=True: clip to a gable triangle."""
    v, f = [], []
    for j in range(ny):
        for i in range(nx):
            u0, u1 = i / nx, (i + 1) / nx
            v0, v1 = j / ny, (j + 1) / ny
            uc, vc = (u0 + u1) / 2, (v0 + v1) / 2
            if tri and abs(uc - 0.5) * 2 > 1 - vc:
                continue
            if not keep(i, j, uc, vc):
                continue
            b = len(v)
            v += [((u0 - 0.5) * w, 0, v0 * h), ((u1 - 0.5) * w, 0, v0 * h), ((u1 - 0.5) * w, 0, v1 * h), ((u0 - 0.5) * w, 0, v1 * h)]
            f.append((b, b + 1, b + 2, b + 3))
    return P(v, f)


def singgora_roof(w, d, rise, over=0.4, tw=0.17, th=0.16, seed=0):
    """gable roof of singgora clay tiles (staggered pointed scales), ridge along X, eave at z=0.
    Returns (tiles, underlay)."""
    rng = random.Random(seed)
    W = w + 2 * over
    half = d / 2 + over
    L = math.hypot(half, rise)
    nc = max(3, int(L / th))
    cols = max(4, int(W / tw))
    v, f, c = [], [], []
    for side in (-1, 1):
        for k in range(nc):
            t0, t1 = k / nc, min(1.0, (k + 1.45) / nc)
            lift = 0.012 * k
            off = 0.5 * (k % 2)
            for i in range(-1, cols + 1):
                x0 = (-0.5 + (i + off) / cols) * W
                x1 = x0 + W / cols
                if x1 < -W / 2 or x0 > W / 2:
                    continue
                x0, x1 = max(x0, -W / 2), min(x1, W / 2)
                xm = 0.5 * (x0 + x1)

                def P3(x, t, dz=0.0):
                    return (x, side * half * (1 - t), rise * t + lift + dz + 0.03)
                tip = max(0.0, t0 - 0.35 / nc)
                b = len(v)
                v += [P3(x0, t0 + 0.12 / nc), P3(xm, tip), P3(x1, t0 + 0.12 / nc), P3(x1, t1), P3(x0, t1)]
                f += [(b, b + 1, b + 2, b + 3, b + 4)] if side < 0 else [(b + 4, b + 3, b + 2, b + 1, b)]
                sh = rng.uniform(0.84, 1.12) * (0.9 + 0.1 * (k % 2))
                col = list(np.clip(np.array(TILE) * sh * (1 - 0.18 * (1 - t0)), 0, 1)) + [1.0]
                c += [col] * 5
    tiles = P(v, f, c)
    under = []
    for side in (-1, 1):
        q = P([(-W / 2, side * half, -0.02), (W / 2, side * half, -0.02), (W / 2, 0, rise - 0.02), (-W / 2, 0, rise - 0.02)],
              [(0, 1, 2, 3)] if side > 0 else [(3, 2, 1, 0)])
        under.append(K.dbl(q))
    ridge = K.tube([(-W / 2, 0, rise + 0.07), (W / 2, 0, rise + 0.07)], 0.07, seg=6)
    return tiles, join(under), ridge


# ---------------------------------------------------------------- props
def put_all(A, set_, groups, x, y, gz, rz):
    for mat, lst in groups.items():
        for (p, kw) in lst:
            q = xf(p, (x, y, gz), (0, 0, rz))
            if kw is None:
                A.add(set_, mat, q)
            else:
                A.add(set_, mat, paint(q, ground=gz, **kw))


def house(A, x, y, rz):
    """rumah Kelantan: on stilts, singgora tiles, tebar layar gable with sobek barge boards + kerawang."""
    W, D, FH, WH, RISE = 4.0, 3.1, 1.05, 1.65, 1.55
    G = {"MatWood_timber": [], "MatTile_singgora": [], "MatRock_clay": [], "MatThatch_mengkuang": [], "MatCloth_wau": [], "MatMetal_iron": []}
    wood = lambda p, col=TIMBER, **kw: G["MatWood_timber"].append((p, {**dict(rgb=col, var=0.08, ao=0.45, ao_h=1.4, namp=0.1, ns=3, stretch=(1, 1, 0.2)), **kw}))
    for px in np.linspace(-W / 2 + 0.1, W / 2 - 0.1, 4):
        for py in (-D / 2 + 0.1, 0.0, D / 2 - 0.1):
            wood(xf(K.box(0.15, 0.15, FH + (WH if py != 0 or abs(px) > 1.5 else 0.0), bev=0.02), (px, py, 0.0)))
            G["MatRock_clay"].append((xf(K.lathe([(0, 0), (0.17, 0), (0.15, 0.16), (0.11, 0.2), (0, 0.2)], seg=10), (px, py, -0.04)),
                                      dict(rgb=(0.52, 0.47, 0.40), ao=0.4, ao_h=0.25)))
    for py in (-D / 2 + 0.1, D / 2 - 0.1):  # floor beams + wall plates
        wood(xf(K.box(W + 0.3, 0.14, 0.14, bev=0.015), (0, py, FH - 0.14)), TIMBER_DK)
        wood(xf(K.box(W + 0.2, 0.12, 0.12, bev=0.015), (0, py, FH + WH - 0.06)), TIMBER_DK)
    for k in range(13):  # floor planks (visible at the anjung)
        wood(xf(K.plank(D + 0.1, 0.3, 0.04, warp=0.008), (-W / 2 + 0.15 + k * 0.31, 0, FH), (0, 0, math.pi / 2)), TIMBER_LT)
    # plank walls: lower body + dark kerawang band; front (+x) wall has a door
    for side in (-1, 1):
        wall = xf(K.box(W - 0.1, 0.06, WH - 0.38, bev=0.01), (0, side * (D / 2 - 0.08), FH + 0.04))
        G["MatWood_timber"].append((wall, None))
        wall.c = None
        paint(wall, TIMBER, var=0.04, ao=0.4, ao_h=2.5, ground=0)
        tint(wall, lambda v, c: c * (0.84 + 0.16 * (np.floor((v[:, 0] + 7) * 5.2) % 2))[:, None])
        band = xf(K.box(W - 0.1, 0.05, 0.36, bev=0.005), (0, side * (D / 2 - 0.09), FH + WH - 0.36))
        wood(band, (0.09, 0.06, 0.05), top=0.0)
        for kx in (-1.2, 0.0, 1.2):  # carved kerawang panels (floral lattice)
            kp = perforated(1.0, 0.3, 20, 6, lambda i, j, u, v: ((i + j) % 3 != 0) and not (abs(u - 0.5) < 0.12 and abs(v - 0.5) < 0.25))
            kp = xf(kp, (kx, side * (D / 2 - 0.035) - (0 if side > 0 else 0), FH + WH - 0.33), (0, 0, 0 if side < 0 else math.pi))
            wood(kp, TIMBER_LT, top=0.1)
        for kx in (-1.0, 1.0):  # windows: dark opening + open shutters
            wood(xf(K.box(0.7, 0.05, 0.8, bev=0.005), (kx, side * (D / 2 - 0.05), FH + 0.45)), (0.08, 0.06, 0.05), top=0.0)
            for sx in (-1, 1):
                wood(xf(K.box(0.36, 0.035, 0.8, bev=0.006), (kx + sx * 0.55, side * (D / 2 + 0.02) + 0.12 * side, FH + 0.45), (0, 0, sx * side * 0.6)), (0.30, 0.42, 0.40))
    for sx in (-1, 1):  # gable end walls
        wall = xf(K.box(0.06, D - 0.1, WH - 0.04, bev=0.01), (sx * (W / 2 - 0.05), 0, FH + 0.02))
        G["MatWood_timber"].append((wall, None))
        paint(wall, TIMBER, var=0.04, ao=0.4, ao_h=2.5, ground=0)
        tint(wall, lambda v, c: c * (0.84 + 0.16 * (np.floor((v[:, 1] + 7) * 5.2) % 2))[:, None])
    wood(xf(K.box(0.05, 0.85, 1.45, bev=0.006), (W / 2 + 0.01, 0.0, FH + 0.02)), (0.07, 0.05, 0.04), top=0.0)   # door opening
    wood(xf(K.box(0.04, 0.42, 1.45, bev=0.006), (W / 2 + 0.25, -0.62, FH + 0.02), (0, 0, 0.9)), (0.48, 0.30, 0.18))  # open door leaf
    # anjung: small landing + steps toward the dish (+x)
    wood(xf(K.box(0.9, 1.4, 0.08, bev=0.015), (W / 2 + 0.45, 0, FH - 0.08)), TIMBER_LT)
    for k in range(4):
        wood(xf(K.box(0.3, 1.0, 0.05, bev=0.01), (W / 2 + 1.05 + 0.3 * k, 0, FH - 0.32 - 0.26 * k)), TIMBER_LT)
    for sy in (-0.52, 0.52):
        wood(K.tube([(W / 2 + 0.9, sy, FH), (W / 2 + 2.25, sy, -0.02)], 0.04, seg=5), TIMBER_DK)
        wood(K.tube([(W / 2 + 0.9, sy, FH + 0.75), (W / 2 + 2.15, sy, 0.6)], 0.03, seg=5), TIMBER_DK)
        wood(xf(K.box(0.07, 0.07, 0.75, bev=0.01), (W / 2 + 0.9, sy, FH)), TIMBER_DK)
    # roof: singgora tiles + soffit + ridge
    tiles, under, ridge = singgora_roof(W, D, RISE, over=0.45, seed=4)
    zr = FH + WH
    G["MatTile_singgora"].append((xf(tiles, (0, 0, zr)), None))
    wood(xf(under, (0, 0, zr)), TIMBER_DK, top=0.0, ao=0.0)
    G["MatTile_singgora"].append((xf(ridge, (0, 0, zr)), dict(rgb=(0.48, 0.22, 0.14), ao=0.0)))
    # tebar layar: gable triangle boards, perforated sun-ray fretwork + sobek barge boards + finial
    Wr = W / 2 + 0.45
    for sx in (-1, 1):
        gb = perforated(D + 0.5, RISE + 0.1, 26, 12,
                        lambda i, j, u, v: not ((j in (3, 4, 7, 8) and (i % 2 == 0)) or (abs(u - 0.5) < 0.05 and 2 < j < 10)), tri=True)
        gb = xf(gb, (sx * (Wr - 0.06), 0, zr - 0.02), (0, 0, math.pi / 2 if sx > 0 else -math.pi / 2))
        wood(gb, (0.50, 0.34, 0.21), ao=0.0, top=0.1)
        back = K.dbl(P([(sx * (Wr - 0.2), -D / 2 - 0.2, zr), (sx * (Wr - 0.2), D / 2 + 0.2, zr), (sx * (Wr - 0.2), 0, zr + RISE)], [(0, 1, 2)]))
        wood(back, (0.08, 0.06, 0.05), ao=0.0, top=0.0)
        for sy in (-1, 1):  # sobek barge boards with scalloped lower edge
            pts = []
            for t in np.linspace(0, 1, 9):
                pts.append((sx * (Wr + 0.03), sy * (D / 2 + 0.45) * (1 - t), zr - 0.05 + (RISE + 0.08) * t))
            bb = K.strip_mesh(pts, [0.11] * 9, up=(1, 0, 0))
            wood(K.dbl(bb), (0.30, 0.20, 0.13), ao=0.0)
            wood(K.tube([(sx * (Wr + 0.03), sy * (D / 2 + 0.45), zr - 0.05), (sx * (Wr + 0.03), sy * (D / 2 + 0.62), zr - 0.22)], [0.05, 0.02], seg=5), (0.30, 0.20, 0.13))
        wood(K.tube([(sx * (Wr + 0.03), 0, zr + RISE + 0.02), (sx * (Wr + 0.06), 0, zr + RISE + 0.5), (sx * (Wr + 0.2), 0, zr + RISE + 0.75)], [0.06, 0.04, 0.012], seg=6), (0.30, 0.20, 0.13))
    # under-house workshop: frames leaning on stilts, bamboo strips, a basket
    for k, (px, py, rot) in enumerate(((-0.6, -D / 2 - 0.05, 0.25), (0.8, -D / 2 - 0.05, -0.2))):
        cl, fr = wau(1.3, paper=False, bow=False, seed=k)
        wood(xf(fr, (px, py - 0.2, 0.0), (rot, 0, 0)), BAMBOO, ao=0.2, top=0.1)
    for k in range(9):
        wood(K.tube([(-1.2 + 0.03 * k, -0.6 + 0.09 * k, 0.05), (0.9 + 0.02 * k, -0.5 + 0.09 * k, 0.07)], 0.012, seg=4), BAMBOO)
    G["MatThatch_mengkuang"].append((xf(K.basket(0.2, 0.22), (1.4, 0.4, 0.0)), dict(rgb=(0.55, 0.44, 0.28), ao=0.4, ao_h=0.2)))
    G["MatRock_clay"].append((xf(K.jar(0.24, 0.55), (W / 2 + 0.4, 1.0, -0.03)), dict(rgb=CLAY, ao=0.4, ao_h=0.3, top=0.2)))  # tempayan by the steps
    gz = ground(x, y)
    put_all(A, "battle", G, x, y, gz, rz)
    A.contact(x, y, 3.2, 0.25)
    A.contact(x + 2.6, y, 1.2, 0.2)


def flat_wau(A, x, y, rz, cols, H=2.0, mat_w=None, seed=0):
    """a finished wau drying flat on a mengkuang mat (reads top-down from the battle camera)."""
    gz = ground(x, y)
    if mat_w:
        mw, md = mat_w
        m = xf(K.box(mw, md, 0.02, bev=0.004), (x, y, gz), (0, 0, rz))
        paint(m, MAT, var=0.03, ao=0.0, top=0.0)
        tint(m, lambda v, c, x=x, y=y: c * (0.86 + 0.14 * ((np.floor(((v[:, 0] - x) * math.cos(rz) + (v[:, 1] - y) * math.sin(rz)) * 12) +
                                                             np.floor((-(v[:, 0] - x) * math.sin(rz) + (v[:, 1] - y) * math.cos(rz)) * 12)) % 2))[:, None])
        A.add("battle", "MatThatch_mengkuang", m)
        A.contact(x, y, max(mw, md) * 0.6, 0.18)
    cl, fr = wau(H, cols, seed=seed)
    lay = lambda p: xf(xf(p, (0, 0, 0), (-math.pi / 2, 0, 0)), (x, y - 0.55 * H, gz + 0.05), (0, 0, 0))
    q = xf(lay(cl), (0, 0, 0))
    q.v[:, :2] = (q.v[:, :2] - [x, y]) @ np.array([[math.cos(rz), math.sin(rz)], [-math.sin(rz), math.cos(rz)]]) + [x, y]
    A.add("battle", "MatCloth_wau", q)
    r = lay(fr)
    r.v[:, :2] = (r.v[:, :2] - [x, y]) @ np.array([[math.cos(rz), math.sin(rz)], [-math.sin(rz), math.cos(rz)]]) + [x, y]
    A.add("battle", "MatWood_timber", paint(r, BAMBOO, ao=0.0, top=0.0))


def stall(A, x, y, rz):
    """gerai nasi kerabu: posts, nipah roof, painted counter with a tray of blue rice and side dishes."""
    G = {"MatWood_timber": [], "MatThatch_mengkuang": [], "MatLeaf_canopy": [], "MatMetal_iron": [], "MatRock_clay": [], "MatCloth_wau": []}
    wood = lambda p, col=TIMBER, **kw: G["MatWood_timber"].append((p, {**dict(rgb=col, var=0.08, ao=0.4, ao_h=1.2, namp=0.1, ns=3, stretch=(1, 1, 0.2)), **kw}))
    Wd, Dp = 2.4, 1.7
    for sx in (-1, 1):
        for sy in (-1, 1):
            wood(xf(K.post(2.25 if sy > 0 else 2.0, 0.055, seed=sx * 3 + sy), (sx * Wd / 2, sy * Dp / 2, -0.05)), BAMBOO)
    roof = K.thatch_roof(Wd, Dp, 0.55, courses=4, over=0.3, seed=21, tooth=0.05, cw=0.18)
    G["MatThatch_mengkuang"].append((xf(roof, (0, 0, 2.05)), dict(rgb=(0.56, 0.44, 0.28), var=0.04, ao=0.0, top=0.3, namp=0.2, ns=3, stretch=(6, 6, 0.4))))
    # counter (front faces -y), blue-green painted panel with a white trim
    wood(xf(K.box(2.0, 0.7, 0.82, bev=0.02), (0, -0.25, 0.0)), (0.20, 0.42, 0.46))
    wood(xf(K.box(2.06, 0.76, 0.05, bev=0.01), (0, -0.25, 0.82)), TIMBER_LT)
    wood(xf(K.box(2.02, 0.02, 0.06, bev=0.005), (0, -0.61, 0.62)), (0.85, 0.82, 0.72))
    # dulang tray: banana leaf, blue rice mounds, kerabu herbs, sambal, fried fish, keropok
    G["MatMetal_iron"].append((xf(K.lathe([(0, 0), (0.34, 0), (0.37, 0.04), (0.35, 0.045), (0, 0.01)], seg=20), (-0.4, -0.25, 0.87)), dict(rgb=(0.62, 0.48, 0.24), ao=0.0)))
    G["MatLeaf_canopy"].append((xf(K.lathe([(0, 0), (0.33, 0), (0.33, 0.006), (0, 0.006)], seg=14), (-0.4, -0.25, 0.9)), dict(rgb=(0.22, 0.42, 0.18), ao=0.0)))
    for k, (dx, dy) in enumerate(((-0.12, -0.08), (0.1, 0.05), (-0.05, 0.14), (0.14, -0.12))):
        G["MatCloth_wau"].append((xf(K.lathe([(0, 0), (0.11, 0), (0.09, 0.05), (0.04, 0.08), (0, 0.085)], seg=12), (-0.4 + dx, -0.25 + dy, 0.9)),
                                  dict(rgb=(0.30, 0.42, 0.78) if k < 3 else (0.85, 0.85, 0.80), ao=0.25, ao_h=0.06, top=0.2)))
    for k, (dx, col) in enumerate(((0.25, (0.30, 0.52, 0.18)), (0.48, (0.70, 0.16, 0.10)), (0.70, (0.72, 0.52, 0.22)))):
        G["MatRock_clay"].append((xf(K.lathe([(0, 0), (0.08, 0), (0.11, 0.06), (0.1, 0.065), (0, 0.04)], seg=12), (dx, -0.38, 0.87)), dict(rgb=(0.86, 0.84, 0.78), ao=0.0)))
        G["MatCloth_wau"].append((xf(K.lathe([(0, 0), (0.09, 0), (0, 0.02)], seg=10), (dx, -0.38, 0.91)), dict(rgb=col, ao=0.0)))
    for k in range(3):  # tiffin carrier (mangkuk tingkat)
        G["MatMetal_iron"].append((xf(K.lathe([(0, 0), (0.1, 0), (0.1, 0.09), (0, 0.09)], seg=12), (0.6, -0.05, 0.87 + 0.095 * k)), dict(rgb=(0.62, 0.62, 0.60), ao=0.0)))
    G["MatMetal_iron"].append((K.tube([(0.5, -0.05, 1.15), (0.6, -0.05, 1.27), (0.7, -0.05, 1.15)], 0.008, seg=4), dict(rgb=(0.4, 0.4, 0.4), ao=0.0)))
    # cooking at the back: clay stove + pot, firewood
    G["MatRock_clay"].append((xf(K.lathe([(0, 0), (0.3, 0), (0.28, 0.35), (0.22, 0.4), (0, 0.4)], seg=14), (-0.6, 0.45, 0.0)), dict(rgb=CLAY, ao=0.45, ao_h=0.35)))
    G["MatMetal_iron"].append((xf(K.lathe([(0, 0), (0.18, 0.02), (0.26, 0.16), (0.25, 0.22), (0, 0.2)], seg=14), (-0.6, 0.45, 0.4)), dict(rgb=IRON, ao=0.0)))
    for k in range(4):
        wood(K.tube([(-0.95 + 0.06 * k, 0.75, 0.05 + 0.08 * (k % 2)), (-0.25, 0.75 + 0.05 * k, 0.04)], 0.035, seg=5), TIMBER_DK)
    # bench in front + hanging banana leaves bundle + a cloth flap
    wood(xf(K.box(1.6, 0.3, 0.05, bev=0.01), (0, -1.15, 0.42)), TIMBER_LT)
    for sx in (-0.65, 0.65):
        wood(xf(K.box(0.06, 0.26, 0.42, bev=0.008), (sx, -1.15, 0.0)), TIMBER_DK)
    flap = K.strip_mesh([(-Wd / 2, -Dp / 2 - 0.3, 2.0), (0, -Dp / 2 - 0.32, 2.02), (Wd / 2, -Dp / 2 - 0.3, 2.0)], [0.17, 0.17, 0.17], up=(0, 1, 0))
    flap.v[:, 2] -= 0.14
    G["MatCloth_wau"].append((flap, dict(rgb=(0.72, 0.14, 0.12), ao=0.0, top=0.0)))
    gz = ground(x, y)
    put_all(A, "battle", G, x, y, gz, rz)
    A.contact(x, y, 2.0, 0.3)


def upright_wau(A, x, y, rz, cols, H=2.4, set_="battle"):
    """a finished wau on a bamboo stand (A-frame), facing the camera."""
    gz = ground(x, y)
    cl, fr = wau(H, cols, seed=3)
    stand = [K.tube([(-0.5, 0.35, 0), (0, 0.05, H * 0.6)], 0.03, seg=5), K.tube([(0.5, 0.35, 0), (0, 0.05, H * 0.6)], 0.03, seg=5),
             K.tube([(0, 0.6, 0), (0, 0.05, H * 0.6)], 0.03, seg=5), K.tube([(-0.35, 0.28, 0.4), (0.35, 0.28, 0.4)], 0.02, seg=4)]
    lift = 0.45
    A.add(set_, "MatCloth_wau", xf(xf(cl, (0, 0, lift), (-0.12, 0, 0)), (x, y, gz), (0, 0, rz)))
    A.add(set_, "MatWood_timber", paint(xf(join(xf(fr, (0, 0, lift), (-0.12, 0, 0)), join(stand)), (x, y, gz), (0, 0, rz)), BAMBOO, ao=0.3, ao_h=0.6, ground=gz))
    A.contact(x, y, 0.8, 0.25)


def banner(x, y, z, L, h, seed, c0, c1):
    """vertical streaming banner (umbul-umbul cloth), local helper producing a two-colour ribbon in XZ."""
    v, f, c = [], [], []
    n = 10
    for k in range(n + 1):
        t = k / n
        px = x + L * t
        py = y + 0.15 * math.sin(t * 6.5 + seed) * t
        zt = z - 0.25 * t * t
        hh = h * (1 - 0.92 * t)
        v += [(px, py, zt), (px, py, zt - hh)]
        col = c0 if (k * 3 // n) % 2 == 0 else c1
        c += [list(col) + [1.0]] * 2
    for k in range(n):
        f.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
    return P(v, f, c)


def pole_with_banner(A, x, y, h=4.4, c0=(0.80, 0.16, 0.12), c1=(0.94, 0.74, 0.20), set_="battle", seed=0):
    gz = ground(x, y)
    A.add(set_, "MatWood_timber", paint(K.tube([(x, y, gz - 0.2), (x + 0.03, y, gz + h * 0.6), (x + 0.22, y + 0.02, gz + h)],
                                                [0.05, 0.04, 0.022], seg=5 if set_ == "battle" else 4), BAMBOO, ao=0.3, ao_h=1.0, ground=gz))
    A.add(set_, "MatCloth_wau" if set_ == "battle" else "MatSky_backdrop", banner(x + 0.08, y, gz + h - 0.1, h * 0.62, 0.62, seed, c0, c1))


def reel(r=0.11, w=0.16):
    """kayu gulung tali: a wooden string reel with a handle, lying on its side (axis along x)."""
    body = K.lathe([(0, -w / 2), (r, -w / 2), (r, -w / 2 + 0.02), (r * 0.62, -w / 2 + 0.03), (r * 0.62, w / 2 - 0.03), (r, w / 2 - 0.02), (r, w / 2), (0, w / 2)], seg=12)
    string = K.lathe([(0, -w / 2 + 0.03), (r * 0.8, -w / 2 + 0.03), (r * 0.82, 0), (r * 0.8, w / 2 - 0.03), (0, w / 2 - 0.03)], seg=12)
    return xf(body, (0, 0, r), (0, math.pi / 2, 0)), xf(string, (0, 0, r), (0, math.pi / 2, 0))


def apron(A):
    """three small clusters (<=0.6 m, muted near the rope): bare wau frames on a mat, reels + string, bamboo strips."""
    # (1) left-near: mat with two unpapered frames, a knife and bamboo strips
    mx, my, rz = -5.4, -1.7, 0.35
    m = xf(K.box(1.9, 1.4, 0.02, bev=0.004), (mx, my, ground(mx, my)), (0, 0, rz))
    A.add("battle", "MatThatch_mengkuang", tint(paint(m, MAT, var=0.03, ao=0.0, top=0.0), lambda v, c: c * (0.86 + 0.14 * ((np.floor(v[:, 0] * 11) + np.floor(v[:, 1] * 11)) % 2))[:, None]))
    for k, (dx, dy, rr) in enumerate(((-0.3, 0.1, 0.4), (0.45, -0.2, 0.1))):
        cl, fr = wau(1.15, paper=False, bow=False, seed=10 + k)
        q = xf(xf(fr, (0, -0.6, 0), (-math.pi / 2, 0, 0)), (mx + dx, my + dy, ground(mx, my) + 0.035), (0, 0, rz + rr))
        A.add("battle", "MatWood_timber", paint(q, BAMBOO, ao=0.0, top=0.0))
    for k in range(7):
        a = rz + 0.05 * k
        A.add("battle", "MatWood_timber", paint(K.tube([(mx - 0.9 + 0.02 * k, my + 0.6 + 0.04 * k, ground(mx, my) + 0.03), (mx + 0.3 + 0.02 * k, my + 0.75 + 0.04 * k, ground(mx, my) + 0.03)], 0.011, seg=4), BAMBOO, ao=0.0))
    A.contact(mx, my, 1.4, 0.2)
    # (2) right-far apron: reels with string + a coil of string and a pot of glue
    for k, (rx, ry, rr) in enumerate(((4.3, 3.6, 0.4), (4.75, 3.05, 1.5), (4.0, 4.3, 2.4))):
        body, string = reel()
        gz = ground(rx, ry)
        A.add("battle", "MatWood_timber", paint(xf(body, (rx, ry, gz), (0, 0, rr)), TIMBER_LT, ao=0.3, ao_h=0.1, ground=gz))
        A.add("battle", "MatCloth_wau", paint(xf(string, (rx, ry, gz), (0, 0, rr)), (0.86, 0.84, 0.78), ao=0.2, ao_h=0.1, ground=gz))
        A.contact(rx, ry, 0.45, 0.25)
    gz = ground(4.9, 3.85)
    A.add("battle", "MatCloth_wau", paint(K.tube(K.arc((4.4, 3.6, gz + 0.02), (5.4, 4.2, gz + 0.01), 0.0, n=8, side=(0.2, -0.3, 0)), 0.006, seg=3), (0.86, 0.84, 0.78), ao=0.0))
    A.add("battle", "MatRock_clay", paint(on_ground(K.jar(0.1, 0.18), 5.2, 3.3, 0.01), CLAY, ao=0.4, ao_h=0.15, ground=ground(5.2, 3.3)))
    # (3) far-left apron: bundles of split bamboo + a woven basket
    for k in range(3):
        bx, by = -3.6 + 0.35 * k, 4.9 - 0.1 * k
        gz = ground(bx, by)
        for j in range(6):
            A.add("battle", "MatWood_timber", paint(K.tube([(bx - 0.5, by - 0.05 + 0.02 * j, gz + 0.03 + 0.02 * (j % 2)), (bx + 0.5, by + 0.05 + 0.02 * j, gz + 0.03 + 0.02 * (j % 2))], 0.014, seg=4), BAMBOO, ao=0.2, ao_h=0.05, ground=gz))
    A.add("battle", "MatThatch_mengkuang", paint(on_ground(K.basket(0.18, 0.22), -2.5, 5.4), (0.56, 0.44, 0.28), ao=0.4, ao_h=0.2, ground=ground(-2.5, 5.4)))
    A.contact(-3.2, 5.0, 0.9, 0.22)


def drying_rack(A, x, y, rz):
    """bamboo rack with drying kite papers + a frame (far band, <= 2 m)."""
    gz = ground(x, y)
    wood, cloth = [], []
    for sx in (-1.3, 1.3):
        wood.append(K.tube([(sx, -0.45, 0), (sx, 0, 1.6)], 0.03, seg=5))
        wood.append(K.tube([(sx, 0.45, 0), (sx, 0, 1.6)], 0.03, seg=5))
    wood.append(K.tube([(-1.45, 0, 1.6), (1.45, 0, 1.6)], 0.028, seg=5))
    wood.append(K.tube([(-1.35, -0.25, 0.8), (1.35, -0.25, 0.8)], 0.02, seg=4))
    cols = [(0.72, 0.14, 0.10), (0.94, 0.76, 0.24), (0.14, 0.32, 0.64), (0.86, 0.84, 0.78)]
    for k in range(4):  # paper sheets hung over the top bar
        sx = -1.0 + 0.66 * k
        sheet = K.strip_mesh([(sx, -0.22, 0.85), (sx, -0.06, 1.25), (sx, 0.0, 1.6), (sx, 0.08, 1.25), (sx, 0.22, 0.95)], [0.26] * 5, up=(1, 0, 0), seed=k)
        sheet.c = np.tile(list(cols[k]) + [1.0], (len(sheet.v), 1))
        cloth.append(sheet)
    A.add("battle", "MatWood_timber", [paint(xf(q, (x, y, gz), (0, 0, rz)), BAMBOO, ao=0.3, ao_h=1.0, ground=gz) for q in wood])
    A.add("battle", "MatCloth_wau", [xf(q, (x, y, gz), (0, 0, rz)) for q in cloth])
    A.contact(x, y, 1.6, 0.2)


def banana_clump(A, x, y, seed, set_="battle"):
    rng = random.Random(seed)
    for k, (dx, dy, h) in enumerate(((0, 0, 2.7), (0.7, -0.9, 2.0), (-0.6, 0.8, 1.4))):
        st, lv = K.banana(h * rng.uniform(0.9, 1.1), seed=seed + k, leaves=6 if h > 2 else 4)
        px, py = x + dx, y + dy
        gz = ground(px, py)
        rz = rng.uniform(0, 6.28)
        A.add(set_, "MatLeaf_canopy", paint(xf(lv, (px, py, gz - 0.05), (0, 0, rz)), (0.36, 0.50, 0.20), var=0.08, ao=0.35, ao_h=2.4, ground=gz, top=0.25, namp=0.15, ns=2))
        A.add(set_, "MatWood_timber", paint(xf(st, (px, py, gz - 0.05), (0, 0, rz)), (0.44, 0.44, 0.26), var=0.06, ao=0.4, ao_h=1.2, ground=gz))
        A.contact(px, py, 1.0, 0.22)


def casu_tree(A, x, y, h, seed, set_="battle", lod=0):
    wd, lf = casuarina(h, seed=seed, lod=lod)
    gz = ground(x, y)
    A.add(set_, "MatWood_timber", paint(xf(wd, (x, y, gz - 0.1)), (0.36, 0.29, 0.23), var=0.08, ao=0.4, ao_h=1.5, ground=gz, namp=0.15, ns=3))
    A.add(set_, "MatLeaf_canopy", paint(xf(lf, (x, y, gz - 0.1)), CASU, var=0.1, ao=0.3, ao_h=h, ground=gz, top=0.35, namp=0.2, ns=1.2))
    if set_ == "battle":
        A.contact(x + 1.0, y, 1.8, 0.25)


def stubble_rows(A, x0, x1, y0, y1, step=0.42):
    """harvested padi: stubble rows along x (golden blades via the Grass scatter)."""
    y = y0 + 0.3
    while y < y1 - 0.3:
        run = None
        x = x0 + 0.3
        while x <= x1 - 0.3:
            ok = yard_w(x, y) < 0.15 and bund_d(x, y) > 0.55 and visible(x, y) and path_dist(x, y) > 0.6 and math.hypot(x, y) > 6.2
            if ok and run is None:
                run = x
            if (not ok or x + 0.5 > x1 - 0.3) and run is not None:
                if x - run > 0.6:
                    A.scatter_strip("Grass", 70, (run, y), (x, y), 0.07, lambda a, b: ground(a, b) + 0.005, STUBBLE, step=99)
                run = None
            x += 0.5
        y += step


# ---------------------------------------------------------------- far set
def far_house(A, x, y, rz, seed):
    rng = random.Random(seed)
    W, D, FH = rng.uniform(4.0, 5.5), rng.uniform(3.0, 3.6), 1.0
    gz = ground(x, y)
    wood = [xf(K.post(FH + 0.2, 0.09, seed=seed + k, seg=4), (sx * W * 0.45, sy * D * 0.45, -0.2)) for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1)))]
    walls = xf(K.box(W, D, 1.8, bev=0.03), (0, 0, FH))
    tiles, under, ridge = singgora_roof(W, D, 1.5, over=0.4, tw=0.5, th=0.45, seed=seed)
    A.add("far", "MatWood_timber", [paint(xf(q, (x, y, gz), (0, 0, rz)), TIMBER_DK, ao=0.3, ao_h=1.0, ground=gz) for q in wood])
    A.add("far", "MatWood_timber", paint(xf(walls, (x, y, gz), (0, 0, rz)), [(0.50, 0.36, 0.24), (0.58, 0.46, 0.32), (0.44, 0.32, 0.22)][seed % 3], var=0.05, ao=0.3, ao_h=3, ground=gz))
    holes = [xf(K.box(0.6, 0.06, 0.75, bev=0.0), (sx * W * 0.28, -D / 2 - 0.02, FH + 0.6)) for sx in (-1, 1)] + [xf(K.box(0.8, 0.06, 1.4, bev=0.0), (0, -D / 2 - 0.02, FH + 0.05))]
    A.add("far", "MatWood_timber", [paint(xf(q, (x, y, gz), (0, 0, rz)), (0.10, 0.07, 0.05), ao=0.0, top=0.0) for q in holes])
    A.add("far", "MatTile_singgora", xf(tiles, (x, y, gz + FH + 1.8), (0, 0, rz)))
    A.add("far", "MatTile_singgora", paint(xf(ridge, (x, y, gz + FH + 1.8), (0, 0, rz)), (0.46, 0.21, 0.13), ao=0.0))


def sky_wau(A, x, y, z, H, cols, seed, string_to=None):
    cl, fr = wau(H, cols, seed=seed)
    tilt = -0.25
    q = face_cam(xf(cl, (0, 0, 0), (tilt, 0, 0.15 * math.sin(seed))), x, y, z)
    A.add("far", "MatSky_backdrop", q)
    A.add("far", "MatWood_timber", paint(face_cam(xf(fr, (0, 0, 0), (tilt, 0, 0)), x, y, z), BAMBOO, ao=0.0))
    if string_to:  # kite line sagging down to the flyer (visible as a fine stroke near the kite)
        gx, gy = string_to
        a = (x, y, z + 0.5 * H)
        b = (gx, gy, ground(gx, gy) + 1.0)
        A.add("far", "MatSky_backdrop", paint(K.tube(K.arc(a, b, -6.0, n=10), 0.05, seg=3, cap=False), (0.92, 0.90, 0.84), ao=0.0))


def far_field(A):
    """far stubble plain: bund lines (cheap) + straw stacks + a pondok, kampung cluster with singgora roofs."""
    for xb in BUND_X:
        for (ya, yb) in ((-20.0, 11.0), (11.0, 50.0)):
            pts = [(xb, ya), (xb, yb)]
            if not any(visible(xb, yy) for yy in np.linspace(ya, yb, 8)) or math.hypot(xb, (ya + yb) / 2) < 23:
                continue
            p = K.extrude(pts, [(-0.5, -0.07), (0.0, 0.12), (0.5, -0.07)], zfn=lambda a, b: 0.0, step=4.0, cap=False)
            A.add("far", "MatGround_field", paint(p, GRASSY, var=0.05, ao=0.0, top=0.2))
    for yb in BUND_Y:
        if yb < 11:
            continue
        p = K.extrude([(-70.0, yb), (70.0, yb)], [(-0.5, -0.07), (0.0, 0.12), (0.5, -0.07)], zfn=lambda a, b: 0.0, step=4.0, cap=False)
        p.f = [f for f in p.f if visible(*p.v[list(f)].mean(axis=0)[:2]) and math.hypot(*p.v[list(f)].mean(axis=0)[:2]) > 22]
        A.add("far", "MatGround_field", paint(p, GRASSY, var=0.05, ao=0.0, top=0.2))
    rng = random.Random(8)
    for k, (x, y) in enumerate(((-14, 30), (-4, 38), (9, 27), (14, 44), (-22, 44), (4, 50), (-9, 24))):
        A.add("far", "MatGround_field", paint(on_ground(straw_stack(rng.uniform(1.0, 1.4), rng.uniform(1.0, 1.5), seed=k, seg=12), x, y), STRAW, var=0.08, ao=0.35, ao_h=1.0, ground=ground(x, y), top=0.25))
    for k, (x, y, rz) in enumerate(((17.0, 31.0, 0.3), (24.0, 38.0, -0.2), (12.5, 40.5, 0.1), (30.0, 30.0, 0.5))):
        far_house(A, x, y, rz, k)
    for k, (x, y) in enumerate(((20.5, 34.5), (15.0, 36.0), (27.5, 42.0), (33.0, 34.0), (10.0, 34.0), (22.0, 46.0))):
        tr, lf = K.coconut_palm(rng.uniform(7.0, 9.5), seed=820 + k, fronds=8)
        A.add("far", "MatWood_timber", paint(xf(tr, (x, y, ground(x, y) - 0.1)), (0.42, 0.36, 0.28), ao=0.3, ao_h=2, ground=0))
        A.add("far", "MatLeaf_canopy", paint(xf(lf, (x, y, ground(x, y) - 0.1)), (0.28, 0.38, 0.17), var=0.1, ao=0, top=0.35, namp=0.15, ns=1))
    for k, (x, y, h) in enumerate(((-9.0, 28.0, 4.5), (6.5, 22.0, 5.0), (-18.0, 36.0, 4.0))):  # flagpoles along the path
        pole_with_banner(A, x, y, h, WAU_COLS[k][0], WAU_COLS[k][2], set_="far", seed=k + 30)


def lobed_card(circles, cols=14, rows=3, puff=0.3, flat_base=0.6):
    """stage-flat silhouette from overlapping circles (cx, cz, r) in local XZ, facing -y, centre bulged
    toward -y for shading. Columns span the circles' union; bottom edge flattened by flat_base."""
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


def crown_card(h, w, seed, lean=0.5):
    """casuarina crown flat: lobes stacked along a leaning axis, flagged downwind (+x), drooping skirts."""
    rng = random.Random(seed)
    circ = []
    for k in range(5):
        t = k / 4
        z = h * (0.18 + 0.68 * t)
        r = w * (0.5 - 0.26 * t) * rng.uniform(0.85, 1.1)
        circ.append((lean * z + w * 0.18 * rng.uniform(-1, 1) + 0.12 * w, z, r))
    p = lobed_card(circ, cols=14, rows=3, puff=0.25, flat_base=0.75)
    z = p.v[:, 2]
    k = 0.6 + 0.5 * smooth01(z.min(), z.max(), z)
    p.c = np.ones((len(p.v), 4))
    p.c[:, :3] = np.asarray(CASU)[None, :] * k[:, None]
    return p


def coast(A):
    """casuarina belt on the dune (flat crowns on real trunks, two staggered rows), sand, sea to the horizon."""
    rng = random.Random(12)
    for row, (yb, step) in enumerate(((BEACH_Y, 4.0), (BEACH_Y + 8.0, 5.2))):
        for k, x in enumerate(np.arange(-80, 80, step)):
            x += rng.uniform(-1.2, 1.2)
            if rng.random() < 0.22:
                continue
            y = yb + rng.uniform(-2.0, 2.5)
            if not in_vista(x, y):
                continue
            h = rng.uniform(9, 13) * (0.85 if row else 1.0)
            gz = ground(x, y)
            lean = rng.uniform(0.6, 1.4)
            A.add("far", "MatWood_timber", paint(K.tube([(x, y, gz - 0.3), (x + lean * 0.4, y, gz + h * 0.45), (x + lean * 1.1, y, gz + h * 0.7)],
                                                       [0.16, 0.12, 0.07], seg=4, cap=False), (0.34, 0.28, 0.22), ao=0.0))
            cr = face_cam(crown_card(h * 0.55, h * rng.uniform(0.22, 0.32), seed=k + 40 * row), 0, 0, 0)
            if row:
                cr.c[:, :3] = cr.c[:, :3] * 0.7 + np.array((0.46, 0.52, 0.52)) * 0.3
            A.add("far", "MatLeaf_canopy", xf(cr, (x + lean * 0.9, y, gz + h * 0.42)))
    ys = np.arange(BEACH_Y + 10, 420, 40.0)
    v, f = [], []
    for y in ys:
        v += [(-400.0, y, SEA_Z), (400.0, y, SEA_Z)]
    for i in range(len(ys) - 1):
        a = 2 * i
        f.append((a, a + 1, a + 3, a + 2))
    p = P(v, f)
    p.c = np.array([[*SEA, 0.55 if i < 2 else 1.0] for i in range(len(v))])
    A.add("far", "MatWater_sea", p)


def skies(A):
    """waus flying + cloud flats layered at two depths (near streaks, far cumulus)."""
    sky_wau(A, 19.0, 62.0, 16.5, 8.5, WAU_COLS[0], 1, string_to=(11.0, 26.0))
    sky_wau(A, 5.0, 96.0, 25.0, 6.0, WAU_COLS[1], 2, string_to=(2.0, 40.0))
    sky_wau(A, 40.0, 104.0, 22.0, 6.5, WAU_COLS[2], 3, string_to=(26.0, 44.0))
    sky_wau(A, -12.0, 80.0, 23.0, 5.5, WAU_COLS[3], 4)
    sky_wau(A, 33.0, 70.0, 10.5, 4.0, WAU_COLS[4], 5, string_to=(22.0, 30.0))
    # painted cumulus (MatSky: unshaded + fog-free, so the haze is painted in: bases toward the horizon colour)
    K.cloud_bank(A, n=7, dist=(250, 400), az=(-44, 32), el=(6.0, 12.5), size=(70, 130), seed=3, mat="MatSky_backdrop",
                 top=(1.0, 0.99, 0.95), mid=(0.93, 0.93, 0.94), base=(0.76, 0.80, 0.88))
    K.cloud_bank(A, n=3, dist=(170, 200), az=(-10, 30), el=(9.0, 13.0), size=(50, 70), seed=4, mat="MatSky_backdrop",
                 top=(1.0, 1.0, 0.97), mid=(0.95, 0.95, 0.96), base=(0.78, 0.82, 0.90))


def bicycle():
    """basikal tua leaning on its stand: wheels, diamond frame, rattan basket. Local, wheels along x."""
    R = 0.33
    wheels = [xf(K.wheel(R, 0.014, spokes=8), (sx, 0, R)) for sx in (-0.52, 0.52)]
    tyres = [xf(K.tube([(R * math.cos(a), 0, R * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 19)], 0.022, seg=4, cap=False), (sx, 0, R)) for sx in (-0.52, 0.52)]
    bb, seat, head = (-0.05, 0, R), (-0.2, 0, R + 0.5), (0.38, 0, R + 0.52)
    frame = [K.tube([(-0.52, 0, R), bb, seat, (-0.52, 0, R)], 0.016, seg=4), K.tube([bb, head], 0.018, seg=4), K.tube([seat, head], 0.016, seg=4),
             K.tube([head, (0.52, 0, R)], 0.016, seg=4), K.tube([(head[0] - 0.03, -0.25, head[2] + 0.12), (head[0] - 0.03, 0.25, head[2] + 0.12)], 0.012, seg=4)]
    saddle = xf(K.box(0.2, 0.12, 0.05, bev=0.02), (seat[0], 0, seat[2] + 0.04))
    basket = xf(K.basket(0.16, 0.18, seg=10), (0.5, 0, R + 0.38))
    return join(wheels + frame), join(tyres + [saddle]), basket


# ---------------------------------------------------------------- build
def build(A):
    for name in ("MatGround_field", "MatWater_sea", "MatWood_timber", "MatThatch_mengkuang", "MatTile_singgora", "MatCloth_wau",
                 "MatLeaf_canopy", "MatRock_clay", "MatMetal_iron", "MatSky_backdrop"):
        A.mat(name)

    # ---- props (contact pools first)
    house(A, *HOUSE)
    banana_clump(A, -11.6, -1.6, seed=41)
    stall(A, *STALL)
    upright_wau(A, 7.4, 6.4, -0.25, WAU_COLS[1], H=2.3)
    pole_with_banner(A, 7.3, -0.9, 2.9, (0.80, 0.16, 0.12), (0.94, 0.74, 0.20), seed=1)
    pole_with_banner(A, 11.6, 6.6, 4.6, (0.12, 0.34, 0.66), (0.94, 0.80, 0.30), seed=2)
    pole_with_banner(A, -7.4, 4.8, 3.5, (0.12, 0.40, 0.28), (0.94, 0.80, 0.30), seed=3)
    casu_tree(A, 12.8, 3.4, 8.5, seed=71)
    casu_tree(A, 13.6, 9.6, 9.5, seed=72)
    apron(A)
    flat_wau(A, -3.4, 7.3, 0.12, WAU_COLS[0], mat_w=(2.2, 2.5), seed=1)
    flat_wau(A, 0.4, 8.0, -0.1, WAU_COLS[2], mat_w=(2.2, 2.5), seed=2)
    flat_wau(A, 3.9, 7.1, 0.25, WAU_COLS[3], H=1.8, mat_w=(2.0, 2.3), seed=3)
    drying_rack(A, -7.1, 7.6, 0.2)
    A.add("battle", "MatThatch_mengkuang", paint(on_ground(straw_stack(1.0, 1.15, seed=3), 7.6, 10.4), STRAW, var=0.08, ao=0.35, ao_h=1.0, ground=ground(7.6, 10.4), top=0.25))
    A.add("battle", "MatThatch_mengkuang", paint(on_ground(straw_stack(0.7, 0.8, seed=4), 6.1, 11.2), STRAW, var=0.08, ao=0.35, ao_h=0.8, ground=ground(6.1, 11.2), top=0.25))
    A.contact(7.2, 10.6, 1.8, 0.25)
    bm, bt, bk = bicycle()
    bx, by, brz = 7.6, 1.15, -0.25
    gz = ground(bx, by)
    for p_, mat, col in ((bm, "MatMetal_iron", (0.18, 0.32, 0.30)), (bt, "MatMetal_iron", (0.10, 0.10, 0.10)), (bk, "MatThatch_mengkuang", (0.56, 0.44, 0.28))):
        A.add("battle", mat, paint(xf(xf(p_, (0, 0, 0), (0.12, 0, 0)), (bx, by, gz), (0, 0, brz)), col, ao=0.3, ao_h=0.4, ground=gz))
    A.contact(bx, by, 0.8, 0.2)
    rng = random.Random(41)
    n = 0
    while n < 140:  # straw + bamboo shavings on the yard (never on the bright apron)
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(6.0, 9.5)
        x, y = r * math.cos(a), r * math.sin(a)
        if yard_w(x, y) < 0.5 or not visible(x, y):
            continue
        n += 1
        gz = ground(x, y)
        q = K.box(rng.uniform(0.14, 0.26), 0.014, 0.008, bev=0.0)
        A.add("battle", "MatThatch_mengkuang", paint(xf(q, (x, y, gz + 0.003), (0, 0, rng.uniform(0, 3.14))), STRAW if n % 3 else BAMBOO, ao=0.0, top=0.0))
    # near strip (vista foreground, <=1.2 m): a flyer's stake with its line, a reel, sandals
    sx, sy = -2.6, -7.6
    A.add("battle", "MatWood_timber", paint(on_ground(K.post(0.6, 0.035, seed=5, seg=5), sx, sy, 0.15), TIMBER, ao=0.3, ao_h=0.3, ground=ground(sx, sy)))
    body, string = reel()
    A.add("battle", "MatWood_timber", paint(xf(body, (sx + 0.4, sy - 0.2, ground(sx, sy)), (0, 0, 0.6)), TIMBER_LT, ao=0.3, ao_h=0.1, ground=ground(sx, sy)))
    A.add("battle", "MatCloth_wau", paint(xf(string, (sx + 0.4, sy - 0.2, ground(sx, sy)), (0, 0, 0.6)), (0.86, 0.84, 0.78), ao=0.2, ao_h=0.1, ground=ground(sx, sy)))

    # ---- terrain
    A.terrain(ground, gcolor, kind=gkind, rin=4.5, rout=130.0, split=23.0, cull=gcull, seed=2)

    # ---- bunds (battle): grassy crowns via scatter; stubble rows in the plots
    for xb in BUND_X:
        if abs(xb) < 23:
            for (ya, yb) in ((-14.0, -7.4), (-7.4, 11.0), (11.0, 23.0)):
                for t0 in np.arange(ya, yb, 1.2):
                    if visible(xb, t0) and yard_w(xb, t0) < 0.3:
                        A.scatter_strip("Grass", 34, (xb, t0), (xb, min(yb, t0 + 1.2)), 0.45, lambda a, b: ground(a, b), GRASS_T, step=99)
    for yb in BUND_Y:
        if abs(yb) < 23:
            for t0 in np.arange(-23.0, 23.0, 1.2):
                if visible(t0, yb) and yard_w(t0, yb) < 0.3 and math.hypot(t0, yb) < 23:
                    A.scatter_strip("Grass", 34, (t0, yb), (t0 + 1.2, yb), 0.45, lambda a, b: ground(a, b), GRASS_T, step=99)
    for (x0, x1) in ((-23.0, -14.5), (-14.5, 13.5), (13.5, 23.0)):
        for (y0, y1) in ((-14.0, -7.4), (-7.4, 11.0), (11.0, 21.0)):
            stubble_rows(A, x0, x1, y0, y1)
    # yard verges: grass tufts at the yard edges and around props
    rng = random.Random(3)
    for k in range(90):
        x, y = rng.uniform(-14, 14), rng.uniform(-8, 12)
        yw = yard_w(x, y)
        if not (0.15 < yw < 0.7) or math.hypot(x, y) < 6.3 or path_dist(x, y) < 0.6 or not visible(x, y):
            continue
        A.scatter_patch("Grass", 30, x, y, rng.uniform(0.4, 0.9), ground, GRASS_T, seed=k)
    for (x, y, r) in ((-11.6, -1.6, 1.6), (12.8, 3.4, 1.4), (13.6, 9.6, 1.5), (-7.0, -1.8, 0.8), (-8.2, 5.4, 0.9), (10.4, 0.0, 0.7)):
        A.scatter_patch("Grass", 26, x, y, r, ground, GRASS_T, seed=int(x * 7 + y))

    # ---- far set
    far_field(A)
    coast(A)
    skies(A)


if __name__ == "__main__":
    K.main("kelantan", build, MOOD)
