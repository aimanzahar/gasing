"""Negeri Sembilan arena -- Adat and consensus, late afternoon (design_art.md section c; USER_SPEC:
"distinctive curved-roof houses, villagers gathered discussing something together, a pot of rendang").
Ground: lawn and laterite apron with flagstone paths on an upper terrace; a stone-capped terrace edge drops
to a lower garden terrace (lotus pond, kemboja trees).
Apron: rendang kawah over firewood, mats laid for the musyawarah with brass trays, kettle, tepak sireh.
Left flank: two rangkiang (rice barns) with gonjong roofs + lesung. Right flank: balai adat (open meeting hall)
with an upswept gonjong roof, mats inside. Marawa banners in Negeri Sembilan yellow/red/black.
Far set (vista): rumah gadang with five gonjong on a knoll, Istana Lama Seri Menanti, paddy valley,
layered hills and late-afternoon cloud flats.

  blender -b --factory-startup -P art_src/arena_nsembilan.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)
import numpy as np
from arenakit import P, xf, aim, join, paint, tint, nz, smooth01
from arena_selangor import VCAM, in_vista, visible, mix, face_vista, cloud_flat, ridge_layer, dome, write_mood

MOOD = {"sky_top": (0.24, 0.40, 0.70), "sky_horizon": (0.98, 0.80, 0.56), "fog": (0.82, 0.78, 0.66),
        "fog_density": 0.0022, "sun_color": (1.0, 0.82, 0.56), "sun_energy": 1.15,
        "lantern": (1.0, 0.66, 0.32), "lantern_energy": 1.4, "exposure": 0.88, "ambient": 0.48,
        "b_sun": 3.4, "b_world": 0.9, "b_fill": 0.4, "b_lantern": 10.0}

# ---------------------------------------------------------------- palette (sRGB)
LAWN = (0.36, 0.48, 0.20)
LAWN_DK = (0.27, 0.38, 0.15)
LAWN_LT = (0.48, 0.56, 0.26)
EARTH = (0.60, 0.44, 0.31)
EARTH_LT = (0.68, 0.53, 0.38)
STONE = (0.62, 0.60, 0.55)
STONE_DK = (0.44, 0.42, 0.39)
TIMBER = (0.30, 0.20, 0.14)       # dark Minang timber
TIMBER_LT = (0.46, 0.33, 0.22)
IJUK = (0.17, 0.15, 0.14)         # black palm-fibre roofing
RED = (0.62, 0.13, 0.10)
GOLD = (0.86, 0.64, 0.20)
BLACK = (0.08, 0.07, 0.07)
BRASS = (0.78, 0.58, 0.26)
LEAF = (0.20, 0.33, 0.14)
GRASS_TINT = (0.42, 0.54, 0.22)
PANDAN = (0.72, 0.62, 0.40)
WATER = (0.30, 0.40, 0.42)

# ---------------------------------------------------------------- layout (Blender coords, +y far)
LOW_Z = -0.36                      # lower garden terrace (main.tscn's dark Ground plane sits at -0.5 out to 22 m)
VAL_Z = -3.4                       # paddy valley
POND = (-2.6, 8.4, 1.5)
STEPS_X = 1.6
BALAI = (9.3, 1.0)
RANGKIANG = [(-8.1, 0.2, 1.0), (-9.2, 3.5, 0.9)]
KNOLL = (13.5, 20.5, 7.0)          # rumah gadang knoll
KAWAH = (-5.1, -3.3)
PATHS = [[(0.5, -4.6), (0.4, -6.0), (0.0, -8.5)], [(4.6, 1.5), (6.2, 2.0), (7.2, 2.2)], [(-4.6, 0.9), (-6.0, 0.8), (-7.4, 0.6)],
         [(1.2, 4.6), (1.5, 5.4), (STEPS_X, 6.2)]]


def edge_y(x):
    return 5.95 + 0.25 * math.sin(0.33 * x + 0.5) + 0.12 * nz(x, 0, 0, 0.4, 2)


def _seg(px, py, a, b):
    ax_, ay_ = a
    bx, by = b
    dx, dy = bx - ax_, by - ay_
    t = max(0.0, min(1.0, ((px - ax_) * dx + (py - ay_) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax_ - t * dx, py - ay_ - t * dy)


def path_dist(x, y):
    return min(_seg(x, y, a, b) for pl in PATHS for a, b in zip(pl[:-1], pl[1:]))


def ground(x, y):
    n = 0.025 * nz(x, y, 0, 0.6, 3) + 0.012 * nz(x, y, 0, 2.0, 4)
    ey = edge_y(x)
    upper = n + 0.02 * max(0.0, -y - 6.0)
    lower = LOW_Z + 0.03 * nz(x, y, 1, 0.5, 5)
    h = upper + (lower - upper) * smooth01(ey - 0.05, ey + 0.35, y)       # terrace drop (stone capped)
    h = h + (VAL_Z - h) * smooth01(22.0, 31.0, y + max(0.0, 1.5 * nz(x, y, 0, 0.08, 6)))  # slope down to the paddy valley (beyond the Ground plane)
    kx, ky, kr = KNOLL  # rumah gadang knoll above the valley
    dk = math.hypot(x - kx, (y - ky) * 0.9)
    h = max(h, -0.3 + (VAL_Z - (-0.3)) * smooth01(kr, kr + 6.0, dk) + 0.04 * nz(x, y, 0, 0.5, 7))
    if math.hypot(x - POND[0], y - POND[1]) < POND[2] + 0.1:  # pond basin
        h = min(h, LOW_Z - 0.35)
    pd = path_dist(x, y)
    if pd < 0.5 and y < ey - 0.2:
        h -= 0.015 * (1 - smooth01(0.1, 0.5, pd))
    return float(h)


def gcolor(x, y, z):
    n1 = nz(x, y, 0, 0.45, 11)
    n2 = nz(x, y, 0, 2.3, 12)
    n3 = nz(x, y, 0, 6.0, 13)
    r = math.hypot(x, y)
    lawn = np.array(LAWN) * (1 + 0.10 * n1 + 0.07 * n2)
    lawn = mix(lawn, LAWN_DK, 0.45 * smooth01(0.1, 0.6, nz(x, y, 0, 0.35, 14)))
    lawn = mix(lawn, LAWN_LT, 0.35 * smooth01(0.2, 0.7, n3 * 0.5 + n2 * 0.5))
    # mown stripes on the upper lawn (late sun catches them)
    lawn = lawn * (0.96 + 0.05 * math.sin(x * 1.3 + 0.3 * n1))
    earth = np.array(EARTH) * (1 + 0.1 * n1 + 0.06 * n2 + 0.04 * n3)
    earth = mix(earth, EARTH_LT, 0.5 * (1 - smooth01(4.6, 5.8, r)))
    apron = 1 - smooth01(5.1, 6.2, r + 0.6 * n1)
    c = mix(lawn, earth, apron)
    c = mix(c, EARTH_LT, 0.55 * (1 - smooth01(0.0, 0.5, path_dist(x, y))) * (1 - smooth01(-0.2, 0.2, y - edge_y(x))))
    if z < -2.0:  # paddy valley: young-rice green and flooded cells catching the sky
        cell = (math.floor(x / 7.0 + 0.3 * n1) + math.floor(y / 5.0)) % 3
        c = mix(np.array((0.40, 0.56, 0.22)) * (1 + 0.1 * n2), (0.50, 0.58, 0.52), 0.6 if cell == 0 else 0.0)
        c = mix(c, (0.30, 0.44, 0.18), 0.4 if cell == 1 else 0.0)
    return tuple(c)


def gkind(x, y, z):
    if math.hypot(x, y) < 23 and (math.hypot(x, y) < 6.0 or path_dist(x, y) < 0.35):
        return "MatGround_earth"
    return "MatGrass_lawn"


def gcull(cx, cy, zmax):
    if math.hypot(cx - POND[0], cy - POND[1]) < POND[2] - 0.2 and zmax < LOW_Z - 0.1:
        return True
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


# ================================================================ Minang architecture kit
def gonjong_roof(L, W, R0, E0, Hh, Lh, He=0.2, nb=10, nh=9, nt=8, sag=1.0, horns=(True, True), thick=0.22):
    """Minang saddle roof, ridge along X, local z=0 at wall top. L = body length between the horn roots,
    W = eave-to-eave width, R0 = ridge height mid-span, E0 = eave height, Hh = extra rise at the horn tips,
    Lh = horn reach beyond the body. The ridge sags slightly, then sweeps up into tusk-like horns; a thick
    ijuk fascia runs along both eaves and tapers up each horn. horns=(left, right): False ends the roof
    square at the body (stepped anjung roofs tuck that end under the main roof).
    Returns (roof, ridge_line points)."""
    xs = [(-L / 2 - Lh) + Lh * i / nh for i in range(nh)] if horns[0] else []
    xs += [(-L / 2) + L * i / nb for i in range(nb + 1)]
    xs += [(L / 2) + Lh * (i / nh) for i in range(1, nh + 1)] if horns[1] else []
    v, f, ridge, lip = [], [], [], []
    for x in xs:
        p = min(1.0, abs(x) / (L / 2 + Lh))
        q = max(0.0, abs(x) - L / 2) / Lh
        zr = R0 + 0.1 * R0 * p ** 2 + Hh * q ** 1.7
        w = W / 2 * (1 - q) ** 1.9 * (1 + 0.1 * p * p)
        ze = E0 + He * p ** 2
        ze = ze + (zr - ze) * q ** 0.9
        xx = x + math.copysign(0.25 * Lh * q ** 2, x)  # tips reach outward
        ridge.append((xx, 0.0, zr))
        for j in range(nt + 1):
            t = -1 + 2 * j / nt
            z = ze + (zr - ze) * (1 - abs(t)) ** sag
            v.append((xx, t * w, z))
        lip.append((xx, w, ze, thick * (1 - q) ** 0.7))
    R = nt + 1
    for i in range(len(xs) - 1):
        for j in range(nt):
            a = i * R + j
            f.append((a, a + R, a + R + 1, a + 1))
    c = np.ones((len(v), 4))
    for k, (x, y, z) in enumerate(v):
        tt = abs(y) / max(1e-6, W / 2)
        band = 0.88 + 0.12 * math.sin(tt * 24.0)
        c[k, :3] = np.array(IJUK) * band * (0.82 + 0.4 * (1 - tt)) * (1 + 0.1 * nz(x, y, z, 2.0, 9))
    roof = K.dbl(P(v, f, c))
    # eave fascia: the cut edge of the thick ijuk layer, slightly lighter and warmer
    lv, lf, lc = [], [], []
    for side in (-1, 1):
        base = len(lv)
        for (xx, w, ze, th) in lip:
            lv += [(xx, side * w, ze), (xx, side * (w - 0.04), ze - th)]
            lc += [list(np.array(IJUK) * 1.5) + [1.0], list(np.array(IJUK) * 0.9) + [1.0]]
        for i in range(len(lip) - 1):
            a = base + 2 * i
            lf.append((a, a + 2, a + 3, a + 1) if side > 0 else (a, a + 1, a + 3, a + 2))
    return join(roof, K.dbl(P(lv, lf, lc))), ridge


MOTIF = {}


def carve_color(xm, zm, H, panel=1.1, window=None):
    """ukiran colouring at (metres along, metres up): black plinth + gold line, red panels with a gold
    cross-flower lattice between dark posts, gold pucuk-rebung triangles on black under the eaves."""
    v = zm / H
    if v < 0.1:
        return BLACK
    if v < 0.14:
        return GOLD
    if v > 0.8:
        if v < 0.83:
            return GOLD
        tri = abs((xm % 0.4) - 0.2) / 0.2
        return GOLD if (v - 0.83) / 0.17 < 1 - tri else BLACK
    u = xm % panel
    if u < 0.12:
        return TIMBER
    if window and window[0] < zm < window[1] and 0.25 < u < panel - 0.13:
        return (0.10, 0.07, 0.05)
    cu, cv = ((u - 0.12) % 0.3) - 0.15, ((zm - H * 0.14) % 0.3) - 0.15
    if abs(cu) + abs(cv) < 0.09:
        return GOLD if abs(cu) + abs(cv) > 0.03 else (0.20, 0.36, 0.30)
    if min(abs(cu), abs(cv)) < 0.02:
        return (0.48, 0.10, 0.08)
    return RED


def carved_wall(L, H, flare=0.08, step=0.1, window=None, panel=1.1, plain=False):
    """wall in local XZ (front normal -Y), x -L/2..L/2 flaring out by `flare` at the top, base z=0.
    One flat-coloured quad per cell (crisp carved-inlay look; colour sampled at the cell centre)."""
    nx_ = max(2, int(round(L / step)))
    nz_ = max(2, int(round(H / step)))
    v, c, f = [], [], []

    def pt(i, j):
        z = H * j / nz_
        k = 1 + flare * z / H
        return ((-L / 2 + L * i / nx_) * k, -0.5 * flare * z, z)
    for j in range(nz_):
        for i in range(nx_):
            col = (TIMBER_LT if (i % 4 == 0) else TIMBER) if plain else carve_color(L * (i + 0.5) / nx_, H * (j + 0.5) / nz_, H, panel, window)
            col = list(np.asarray(col) * (0.93 + 0.07 * math.sin(i * 1.7 + j * 0.9))) + [1.0]
            a = len(v)
            v += [pt(i, j), pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1)]
            c += [col] * 4
            f.append((a, a + 1, a + 2, a + 3))
    return P(v, f, c)


def walls_box(Lx, Ly, H, flare=0.08, step=0.1, window=None, side_window=None):
    """four flaring carved walls around a Lx x Ly footprint, base z=0."""
    out = []
    for rz, L, D, win in ((0.0, Lx, Ly, window), (math.pi, Lx, Ly, None), (math.pi / 2, Ly, Lx, side_window), (-math.pi / 2, Ly, Lx, side_window)):
        w = carved_wall(L, H, flare, step, win)
        w.v[:, 1] -= D / 2
        out.append(xf(w, (0, 0, 0), (0, 0, rz)))
    return out


def roof_horn_tips(ridge):
    a, b = ridge[0], ridge[-1]
    return [a, b]


def finial(tip, h=0.5, r=0.025):
    """brass spike continuing a gonjong horn tip."""
    return K.tube([tip, (tip[0] * 1.0, tip[1], tip[2] + h * 0.6), (tip[0], tip[1], tip[2] + h)], [r, r * 0.7, 0.002], seg=5)


def rangkiang(A, x, y, rz, s=1.0):
    """rice barn: four posts on stones, flaring carved body, steep gonjong roof (ridge along local X)."""
    Lx, Ly, H, FH = 1.5, 1.2, 1.25, 0.85
    wood, rock, metal = [], [], []
    for sx in (-0.6, 0.6):
        for sy in (-0.45, 0.45):
            wood.append(xf(K.box(0.12, 0.12, FH + 0.1, bev=0.015), (sx, sy, 0.05)))
            rock.append(xf(K.rock(0.13, seed=int(sx * 10 + sy * 20) + 50, sub=2, squash=(1, 1, 0.6)), (sx, sy, -0.03)))
    wood.append(xf(K.box(Lx + 0.25, Ly + 0.25, 0.1, bev=0.02), (0, 0, FH)))
    body = walls_box(Lx, Ly, H, flare=0.18, step=0.09)
    body = [xf(b, (0, 0, FH + 0.1)) for b in body]
    roof, ridge = gonjong_roof(1.6, 2.1, 1.35, -0.12, 0.85, 0.55, nb=6, nh=7, nt=8)
    roof = xf(roof, (0, 0, FH + 0.1 + H))
    tips = [(p[0], p[1], p[2] + FH + 0.1 + H) for p in roof_horn_tips(ridge)]
    for t in tips:
        metal.append(finial(t, 0.35))
    wood.append(xf(K.box(0.5, 0.06, 0.6, bev=0.01), (0, -Ly / 2 - 0.15, FH + 0.35)))  # small door
    wood.append(xf(K.box(0.6, 0.35, 0.05, bev=0.01), (0, -Ly / 2 - 0.35, FH * 0.5)))  # step
    gz = ground(x, y)
    put = lambda lst: [xf(p, (x, y, gz), (0, 0, rz), s) for p in lst]
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, var=0.06, ao=0.45, ao_h=1.0, ground=gz, namp=0.1, ns=4) for q in put(wood)])
    A.add("battle", "MatWood_timber", [tint(q, lambda v, c: c * (0.75 + 0.25 * smooth01(gz, gz + 2.0, v[:, 2]))[:, None]) for q in put(body)])
    A.add("battle", "MatThatch_ijuk", put([roof]))
    A.add("battle", "MatMetal_brass", [paint(q, BRASS, ao=0.0, top=0.3) for q in put(metal)])
    A.add("battle", "MatRock_stone", [paint(q, STONE_DK, ao=0.4, ao_h=0.15, ground=gz) for q in put(rock)])
    A.contact(x, y, 1.6 * s, 0.35)


def balai(A, x, y, rz):
    """balai adat: open meeting hall on posts, carved railing, mats + trays inside, big gonjong roof."""
    Lx, Ly, FH, PH = 3.6, 2.5, 0.62, 1.85
    wood, rock, metal, mats, glow = [], [], [], [], []
    for sx in (-1.7, -0.57, 0.57, 1.7):
        for sy in (-1.15, 1.15):
            wood.append(xf(K.box(0.14, 0.14, PH + 0.08, bev=0.02), (sx, sy, 0.0)))
            rock.append(xf(K.rock(0.15, seed=int(sx * 7 + sy * 3) + 70, sub=2, squash=(1, 1, 0.6)), (sx, sy, -0.03)))
    wood.append(xf(K.box(Lx + 0.3, Ly + 0.3, 0.1, bev=0.02), (0, 0, FH)))
    for sy in (-1.15, 1.15):  # beams
        wood.append(xf(K.box(Lx + 0.4, 0.14, 0.16, bev=0.02), (0, sy, PH - 0.08)))
    for sx in (-1.7, 1.7):
        wood.append(xf(K.box(0.14, Ly + 0.4, 0.16, bev=0.02), (sx, 0, PH - 0.08)))
    # carved railing panels on three sides (front open in the middle for the steps)
    for (px, py, rzz, L) in ((-1.15, -1.25, 0.0, 1.0), (1.15, -1.25, 0.0, 1.0), (0.0, 1.25, math.pi, 3.4), (-1.8, 0.0, -math.pi / 2, 2.3), (1.8, 0.0, math.pi / 2, 2.3)):
        w = carved_wall(L, 0.42, flare=0.0, step=0.09, panel=0.55)
        wood.append(xf(w, (px, py, FH + 0.1), (0, 0, rzz)))
    for k in range(3):  # steps
        wood.append(xf(K.box(0.9, 0.3, 0.06, bev=0.01), (0, -1.5 - 0.28 * k, FH - 0.2 * (k + 1))))
    # mats with brass trays (the gathering)
    mats.append(tikar(2.9, 1.9, seed=3, z=FH + 0.105))
    for (tx, ty) in ((-0.7, 0.2), (0.8, -0.15)):
        metal.append(xf(K.lathe([(0, 0), (0.24, 0.0), (0.27, 0.035), (0.25, 0.04), (0.2, 0.012), (0, 0.012)], seg=16, cap0=False), (tx, ty, FH + 0.11)))
        metal.append(xf(K.lathe([(0, 0), (0.07, 0), (0.08, 0.06), (0.05, 0.11), (0.02, 0.12), (0.02, 0.15), (0, 0.15)], seg=10), (tx + 0.08, ty + 0.05, FH + 0.15)))
        for c in range(3):
            metal.append(xf(K.lathe([(0, 0), (0.025, 0), (0.035, 0.05), (0, 0.05)], seg=8, cap0=False), (tx - 0.12 + 0.07 * c, ty - 0.1, FH + 0.15)))
    metal.append(xf(K.box(0.3, 0.2, 0.12, bev=0.02), (0.1, 0.55, FH + 0.11)))  # tepak sireh
    roof, ridge = gonjong_roof(3.6, 3.7, 1.45, -0.1, 1.05, 0.95, nb=10, nh=8, nt=10)
    roof = xf(roof, (0, 0, PH))
    for t in roof_horn_tips(ridge):
        metal.append(finial((t[0], t[1], t[2] + PH), 0.4))
    glow.append(xf(K.lathe([(0, 0), (0.06, 0.0), (0.075, 0.08), (0.05, 0.16), (0, 0.17)], seg=10), (0.0, 0.0, PH - 0.45)))
    gz = ground(x, y)
    put = lambda lst: [xf(p, (x, y, gz), (0, 0, rz)) for p in lst]
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, var=0.06, ao=0.45, ao_h=1.2, ground=gz, namp=0.1, ns=4) if q.c is None else q for q in put(wood)])
    A.add("battle", "MatThatch_ijuk", put([roof]))
    A.add("battle", "MatThatch_ijuk", put(mats))
    A.add("battle", "MatMetal_brass", [paint(q, BRASS, var=0.05, ao=0.0, top=0.3) for q in put(metal)])
    A.add("battle", "MatRock_stone", [paint(q, STONE_DK, ao=0.4, ao_h=0.15, ground=gz) for q in put(rock)])
    A.add("battle", "MatGlow_fire", [paint(q, (1.0, 0.85, 0.55), ao=0.0) for q in put(glow)])
    lp = xf(P([(0.0, 0.0, PH - 0.35)], []), (x, y, gz), (0, 0, rz)).v[0]
    A.light(tuple(lp), 12.0, (1.0, 0.72, 0.42), range_m=4)
    A.contact(x, y, 2.6, 0.35)


def tikar(W, D, seed=0, z=0.0, step=0.1):
    """woven mengkuang mat: chequer weave + coloured border stripes (vertex colour), flat at height z."""
    rng = random.Random(seed)
    cols = [(0.62, 0.16, 0.14), (0.20, 0.42, 0.24), (0.42, 0.20, 0.42), (0.14, 0.26, 0.48)]
    c1, c2 = cols[seed % 4], cols[(seed + 1) % 4]
    nx_, ny_ = int(W / step), int(D / step)
    v, c, f = [], [], []
    for j in range(ny_ + 1):
        for i in range(nx_ + 1):
            u, w = i / nx_, j / ny_
            v.append(((u - 0.5) * W, (w - 0.5) * D, z + 0.004 * math.sin(i * 1.3 + j)))
            e = min(u, 1 - u, w, 1 - w) * min(W, D)
            if e < 0.06:
                col = c1
            elif e < 0.12:
                col = PANDAN
            elif e < 0.2:
                col = c2
            else:
                col = np.array(PANDAN) * (0.88 if (i + j) % 2 else 1.04)
                if abs(((u * W) % 0.6) - 0.3) + abs(((w * D) % 0.6) - 0.3) < 0.08:
                    col = c1
            c.append(list(col) + [1.0])
    R = nx_ + 1
    for j in range(ny_):
        for i in range(nx_):
            a = j * R + i
            f.append((a, a + 1, a + R + 1, a + R))
    return P(v, f, c)


def kawah(A, x, y):
    """rendang kawah: wide iron cauldron on three stones over radiating firewood, glowing embers, sudip."""
    gz = ground(x, y)
    pot = K.lathe([(0.0, 0.0), (0.2, 0.0), (0.42, 0.08), (0.55, 0.22), (0.6, 0.3), (0.63, 0.31), (0.6, 0.32), (0.56, 0.25), (0.4, 0.12), (0.0, 0.09)],
                  seg=24, cap0=False, cap1=False)
    rend = K.lathe([(0.0, 0.2), (0.3, 0.2), (0.5, 0.24), (0.55, 0.255)], seg=24, cap0=False, cap1=False)
    rend.v[:, 2] += 0.015 * np.array([nz(a, b, 0, 9.0, 3) for a, b, _ in rend.v])
    stones = [xf(K.rock(0.16, seed=90 + k, sub=2, squash=(1, 0.9, 0.9)), (0.45 * math.cos(2.1 * k + 0.4), 0.45 * math.sin(2.1 * k + 0.4), -0.03)) for k in range(3)]
    logs = []
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        logs.append(K.tube([(0.12 * math.cos(a), 0.12 * math.sin(a), 0.07), (0.95 * math.cos(a), 0.95 * math.sin(a), 0.05)], [0.05, 0.06], seg=6))
    embers = [xf(K.rock(0.22, seed=97, sub=2, squash=(1, 1, 0.25)), (0, 0, -0.02))]
    sudip = K.tube([(-0.2, -0.1, 0.35), (-0.95, -0.55, 0.85)], 0.02, seg=5)
    blade = xf(K.box(0.12, 0.2, 0.012, bev=0.004), (-0.2, -0.1, 0.33), (-0.7, 0, 0.55))
    lift = 0.22
    A.add("battle", "MatMetal_brass", paint(xf(pot, (x, y, gz + lift)), (0.16, 0.15, 0.14), ao=0.0, top=0.25, namp=0.15, ns=6))
    A.add("battle", "MatRock_stone", paint(xf(rend, (x, y, gz + lift)), (0.36, 0.15, 0.08), var=0.0, ao=0.0, top=0.2, namp=0.3, ns=8))
    A.add("battle", "MatRock_stone", [paint(xf(q, (x, y, gz)), (0.40, 0.37, 0.33), ao=0.3, ao_h=0.2, ground=gz) for q in stones])
    A.add("battle", "MatWood_timber", [tint(paint(xf(q, (x, y, gz)), (0.42, 0.32, 0.22), ao=0.0, namp=0.2, ns=5),
                                            lambda v, c: c * (0.25 + 0.75 * smooth01(0.2, 0.55, np.hypot(v[:, 0] - x, v[:, 1] - y)))[:, None]) for q in logs])
    A.add("battle", "MatWood_timber", [paint(xf(q, (x, y, gz + lift)), TIMBER_LT, ao=0.0) for q in (sudip, blade)])
    A.add("battle", "MatGlow_fire", [paint(xf(q, (x, y, gz)), (1.0, 0.45, 0.12), ao=0.0, top=0.0) for q in embers])
    A.light((x, y, gz + 0.25), 10.0, (1.0, 0.5, 0.2), range_m=3)
    A.contact(x, y, 1.3, 0.45)
    # firewood stack + spice bowls beside the hearth
    for k in range(6):
        yy = y - 0.95 + 0.11 * (k % 3)
        zz = gz + 0.06 + 0.1 * (k // 3)
        A.add("battle", "MatWood_timber", paint(K.tube([(x - 0.9, yy, zz), (x - 0.25, yy + 0.05, zz)], 0.055, seg=6), (0.46, 0.35, 0.24), ao=0.3, ao_h=0.2, ground=gz, namp=0.2, ns=6))
    for k, col in enumerate(((0.70, 0.12, 0.08), (0.85, 0.62, 0.18), (0.55, 0.45, 0.30))):
        bx, by = x + 0.95 + 0.28 * k, y - 0.55 + 0.12 * k
        A.add("battle", "MatRock_stone", paint(xf(K.lathe([(0, 0), (0.1, 0.0), (0.13, 0.07), (0.11, 0.075), (0.0, 0.06)], seg=12), (bx, by, ground(bx, by))), (0.80, 0.78, 0.72), ao=0.0, top=0.2))
        A.add("battle", "MatRock_stone", paint(xf(K.rock(0.085, seed=40 + k, sub=2, squash=(1, 1, 0.35)), (bx, by, ground(bx, by) + 0.035)), col, ao=0.0, top=0.2))
    A.contact(x + 1.2, y - 0.4, 0.8, 0.25)


def marawa(A, x, y, h, seed, cols):
    """umbul-umbul banner pole: bamboo with a long vertical pennant in state colours."""
    rng = random.Random(seed)
    gz = ground(x, y)
    pole = K.tube([(x, y, gz - 0.2), (x + rng.uniform(-0.05, 0.05), y, gz + h)], [0.045, 0.025], seg=6)
    A.add("battle", "MatWood_timber", paint(pole, (0.68, 0.60, 0.36), ao=0.3, ao_h=1, ground=gz))
    n = 14
    L = h * 0.62
    v, c, f = [], [], []
    for i in range(n + 1):
        t = i / n
        z = gz + h - 0.15 - L * t
        sw = 0.18 * t ** 1.4 * math.sin(seed + t * 3.0)
        w = 0.34 * (1 - 0.65 * t)
        for k2, side in enumerate((0.0, 1.0)):
            v.append((x + 0.05 + side * w + sw * 0.3, y + sw, z - side * 0.12 * t))
            band = cols[min(len(cols) - 1, int(t * len(cols)))]
            c.append(list(band) + [1.0])
    for i in range(n):
        a = 2 * i
        f.append((a, a + 2, a + 3, a + 1))
    A.add("battle", "MatCloth_kain", P(v, f, c))


def kemboja(A, x, y, h, seed, set_="battle"):
    """frangipani: grey forked limbs, leaf tufts at the tips, white-yellow flowers."""
    rng = random.Random(seed)
    gz = ground(x, y)
    wood, leaf, fl = [], [], []
    tips = []

    def branch(p0, d, L, r, depth):
        p1 = (p0[0] + d[0] * L, p0[1] + d[1] * L, p0[2] + d[2] * L)
        wood.append(K.tube([p0, ((p0[0] + p1[0]) / 2 + 0.05, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2 + 0.05), p1], [r, r * 0.85, r * 0.7], seg=6))
        if depth == 0:
            tips.append(p1)
            return
        for k in range(2):
            a = rng.uniform(0, 2 * math.pi)
            nd = (d[0] * 0.5 + 0.6 * math.cos(a), d[1] * 0.5 + 0.6 * math.sin(a), d[2] * 0.6 + 0.5)
            l = math.sqrt(sum(q * q for q in nd))
            branch(p1, tuple(q / l for q in nd), L * 0.72, r * 0.7, depth - 1)
    branch((0, 0, -0.1), (0.05, 0.0, 1.0), h * 0.38, 0.12, 2)
    for t in tips:
        leaf.append(xf(K.canopy(0.42, seed=seed * 3 + len(leaf), lumps=2, sub=2, squash=0.6, spread=0.5), (t[0], t[1], t[2] - 0.05)))
        for k in range(4):
            a = rng.uniform(0, 2 * math.pi)
            c = (t[0] + 0.3 * math.cos(a), t[1] + 0.3 * math.sin(a), t[2] + rng.uniform(0.05, 0.2))
            s = 0.07
            pts = [(0, 0, 0.01)] + [(s * math.cos(2 * math.pi * j / 5), s * math.sin(2 * math.pi * j / 5), 0.0) for j in range(5)]
            fl.append(xf(P(pts, [(0, 1 + j, 1 + (j + 1) % 5) for j in range(5)]), c))
    A.add(set_, "MatWood_timber", [paint(xf(q, (x, y, gz)), (0.52, 0.48, 0.42), var=0.05, ao=0.3, ao_h=1.0, ground=gz) for q in wood])
    A.add(set_, "MatLeaf_canopy", [paint(xf(q, (x, y, gz)), (0.24, 0.40, 0.16), var=0.1, ao=0.35, ao_h=h, ground=gz, top=0.45, namp=0.2, ns=2) for q in leaf])
    A.add(set_, "MatLeaf_canopy", [tint(paint(xf(q, (x, y, gz)), (0.96, 0.94, 0.86), ao=0.0, top=0.0),
                                        lambda v, c: np.vstack([c[:1] * np.array([1.0, 0.85, 0.35, 1]), c[1:]])) for q in fl])
    if set_ == "battle":
        A.contact(x, y, 1.4, 0.3)


def bush(A, x, y, h, seed, rgb, flowers=None, set_="battle", sub=3):
    gz = ground(x, y)
    b = join([xf(K.rock(h * (0.5 if i == 0 else 0.4), seed=seed * 3 + i, sub=sub, amp=0.16, freq=1.5, squash=(1.15, 1, 0.8), flat=0.9),
                 (0.32 * h * (i - 0.5) * 2 if i else 0.0, 0.1 * h * i, 0.0)) for i in range(2)])
    b = paint(xf(b, (x, y, gz - 0.08)), rgb, var=0.1, ao=0.5, ao_h=h, ground=gz, top=0.4, namp=0.2, ns=3)
    A.add(set_, "MatLeaf_canopy", b)
    if flowers:
        rng = random.Random(seed)
        nrm = K.vnormals(b)
        fl = []
        for k in range(18):
            i = rng.randrange(len(b.v))
            if nrm[i][2] < 0.0:
                continue
            s_ = 0.075
            fl.append(xf(P([(0, 0, s_ * 0.35), (s_, 0, -s_ * 0.2), (-s_ * 0.5, s_ * 0.87, -s_ * 0.2), (-s_ * 0.5, -s_ * 0.87, -s_ * 0.2)],
                           [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]), tuple(b.v[i] + nrm[i] * 0.03)))
        A.add(set_, "MatLeaf_canopy", [paint(q, flowers, var=0.1, ao=0.0, top=0.3) for q in fl])
    A.contact(x, y, h * 0.9, 0.25)


# ---------------------------------------------------------------- props on the upper terrace
def flagstones(A):
    rng = random.Random(8)
    stones = []
    for pl in PATHS:
        for a, b in zip(pl[:-1], pl[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, int(L / 0.62))
            for i in range(n):
                t = (i + 0.5) / n
                x, y = a[0] + (b[0] - a[0]) * t + rng.uniform(-0.06, 0.06), a[1] + (b[1] - a[1]) * t + rng.uniform(-0.06, 0.06)
                if math.hypot(x, y) < 4.75 or y > edge_y(x) - 0.25:
                    continue
                st = K.box(rng.uniform(0.42, 0.55), rng.uniform(0.36, 0.46), 0.08, bev=0.025, jitter=0.012, seed=rng.randint(0, 99))
                stones.append(paint(xf(st, (x, y, ground(x, y) - 0.05), (0, 0, math.atan2(b[1] - a[1], b[0] - a[0]) + rng.uniform(-0.2, 0.2))),
                                    STONE if i % 3 else (0.56, 0.54, 0.48), var=0.1, ao=0.25, ao_h=0.08, ground=ground(x, y) - 0.05, top=0.25, namp=0.2, ns=6))
    A.add("battle", "MatRock_stone", stones)


def terrace_edge(A):
    """stone coping along the terrace drop + steps down to the lower garden."""
    rng = random.Random(12)
    stones = []
    x = -13.5
    while x < 13.5:
        w = rng.uniform(0.5, 0.75)
        if abs(x + w / 2 - STEPS_X) < 0.75:
            x += w
            continue
        ey = edge_y(x + w / 2)
        st = K.box(w - 0.04, 0.42, 0.22, bev=0.04, jitter=0.015, seed=rng.randint(0, 999))
        stones.append(paint(xf(st, (x + w / 2, ey + 0.05, ground(x + w / 2, ey - 0.3) - 0.1), (0, 0, rng.uniform(-0.05, 0.05))),
                            STONE if rng.random() > 0.3 else STONE_DK, var=0.12, ao=0.3, ao_h=0.15, ground=-0.1, top=0.3, namp=0.25, ns=5))
        x += w
    for k in range(2):  # steps down
        yy = edge_y(STEPS_X) + 0.05 + 0.42 * k
        zz = -0.04 - (LOW_Z * -1) * (k + 0.5) / 2
        hh = zz + 0.05 - (LOW_Z - 0.1)
        stones.append(paint(xf(K.box(1.25, 0.46, hh, bev=0.03, jitter=0.01, seed=k), (STEPS_X, yy, LOW_Z - 0.1)), STONE, var=0.08, ao=0.6, ao_h=0.3, ground=zz - 0.25, top=0.4, namp=0.2, ns=5))
    A.add("battle", "MatRock_stone", stones)


def gathering(A):
    """the musyawarah laid out on the far apron: mats, brass trays, kettle, cups, tepak sireh."""
    for k, (mx, my, rz, W, D) in enumerate(((-1.6, 5.0, 0.08, 2.2, 1.0), (2.9, 4.85, -0.15, 1.6, 0.95))):
        gz = ground(mx, my)
        A.add("battle", "MatThatch_ijuk", xf(tikar(W, D, seed=k + 1, z=0.012), (mx, my, gz), (0, 0, rz)))
        A.contact(mx, my, 1.2, 0.15)
    for (tx, ty) in ((-1.9, 5.05), (3.0, 4.9)):
        gz = ground(tx, ty) + 0.014
        A.add("battle", "MatMetal_brass", paint(xf(K.lathe([(0, 0), (0.24, 0.0), (0.27, 0.035), (0.25, 0.04), (0.2, 0.012), (0, 0.012)], seg=16, cap0=False), (tx, ty, gz)), BRASS, ao=0.0, top=0.3))
        A.add("battle", "MatMetal_brass", paint(xf(K.lathe([(0, 0), (0.07, 0), (0.08, 0.06), (0.05, 0.11), (0.02, 0.12), (0.02, 0.15), (0, 0.15)], seg=10), (tx + 0.07, ty + 0.04, gz + 0.012)),
                                                (0.86, 0.80, 0.70), ao=0.0, top=0.3))
        for c in range(4):
            a = 2 * math.pi * c / 4 + 0.4
            A.add("battle", "MatMetal_brass", paint(xf(K.lathe([(0, 0), (0.028, 0), (0.038, 0.055), (0, 0.055)], seg=8, cap0=False), (tx + 0.17 * math.cos(a), ty + 0.17 * math.sin(a), gz + 0.012)),
                                                    (0.92, 0.90, 0.84), ao=0.0, top=0.2))
    gz = ground(-0.6, 5.15)
    A.add("battle", "MatMetal_brass", paint(xf(K.box(0.32, 0.22, 0.13, bev=0.02), (-0.6, 5.15, gz + 0.012)), BRASS, ao=0.0, top=0.3))


def apron_left(A):
    """lesung + alu by the rangkiang; baskets of paddy."""
    lx, ly = -6.7, 2.4
    gz = ground(lx, ly)
    A.add("battle", "MatWood_timber", paint(xf(K.lathe([(0.0, 0.25), (0.2, 0.25), (0.22, 0.0), (0.26, 0.0), (0.24, 0.45), (0.2, 0.5), (0.13, 0.5), (0.1, 0.35), (0, 0.33)], seg=14, cap0=False), (lx, ly, gz - 0.02)),
                                            TIMBER_LT, ao=0.35, ao_h=0.4, ground=gz, namp=0.15, ns=5))
    A.add("battle", "MatWood_timber", paint(K.tube([(lx + 0.05, ly, gz + 0.4), (lx + 0.85, ly - 0.55, gz + 0.03)], [0.045, 0.05], seg=6), (0.56, 0.44, 0.30), ao=0.0))
    for k, (bx, by) in enumerate(((-6.95, 3.25), (-6.4, 3.5))):
        A.add("battle", "MatThatch_ijuk", tint(paint(on_ground(K.basket(0.18, 0.22), bx, by), (0.62, 0.50, 0.30), ao=0.4, ao_h=0.2, ground=ground(bx, by)),
                                               lambda v, c, bx=bx, by=by: c * (0.84 + 0.16 * ((np.floor(v[:, 2] * 40) + np.floor(np.arctan2(v[:, 1] - by, v[:, 0] - bx) * 5)) % 2))[:, None]))
        A.add("battle", "MatGrass_lawn", paint(xf(K.rock(0.17, seed=20 + k, sub=2, squash=(1, 1, 0.35)), (bx, by, ground(bx, by) + 0.18)), (0.82, 0.68, 0.34), ao=0.0, top=0.2))
    A.contact(lx, ly, 0.8, 0.3)


# ---------------------------------------------------------------- lower garden terrace
def pond(A):
    px, py, pr = POND
    z = LOW_Z - 0.08
    n = 28
    v = [(px, py, z)] + [(px + pr * 1.08 * math.cos(2 * math.pi * i / n), py + pr * 0.85 * math.sin(2 * math.pi * i / n), z) for i in range(n)]
    p = P(v, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)])
    p.c = np.array([list(WATER) + [1.0]] + [[0.34, 0.40, 0.36, 0.9]] * n)
    A.add("battle", "MatWater_pond", p)
    rng = random.Random(4)
    rim = []
    for i in range(22):
        a = 2 * math.pi * i / 22
        rx, ry = px + pr * 1.12 * math.cos(a), py + pr * 0.9 * math.sin(a)
        rim.append(paint(xf(K.rock(rng.uniform(0.16, 0.24), seed=300 + i, sub=2, squash=(1.2, 1, 0.55)), (rx, ry, LOW_Z - 0.12)), STONE_DK if i % 3 else STONE, ao=0.35, ao_h=0.15, ground=LOW_Z - 0.1, top=0.3))
    A.add("battle", "MatRock_stone", rim)
    pads, fl = [], []
    for k in range(9):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.2, 0.75) * pr
        cx, cy = px + d * math.cos(a), py + d * 0.8 * math.sin(a)
        r = rng.uniform(0.16, 0.26)
        m = 10
        pv = [(cx, cy, z + 0.015)] + [(cx + r * math.cos(0.5 + 5.6 * i / m), cy + r * math.sin(0.5 + 5.6 * i / m), z + 0.015) for i in range(m + 1)]
        pads.append(P(pv, [(0, 1 + i, 2 + i) for i in range(m)]))
        if k % 3 == 0:
            fl.append(xf(K.lathe([(0, 0), (0.05, 0.04), (0.09, 0.12), (0.04, 0.1), (0, 0.06)], seg=7), (cx, cy, z + 0.02)))
    A.add("battle", "MatLeaf_canopy", [paint(K.dbl(q), (0.26, 0.46, 0.20), var=0.1, ao=0.0, top=0.0) for q in pads])
    A.add("battle", "MatLeaf_canopy", [paint(q, (0.95, 0.55, 0.66), ao=0.0, top=0.3) for q in fl])


# ---------------------------------------------------------------- far set
def far_wall(L, H, flare, step=0.5, window=None, panel=1.4):
    return carved_wall(L, H, flare=flare, step=step, window=window, panel=panel)


def rumah_gadang(A, x, y, rz, s=1.0):
    """rumah gadang: flaring carved body on stilts, main gonjong pair, two stepped side roofs (four more horns),
    front porch gonjong facing the viewer -- five horn tips silhouetted against the sky."""
    Lx, Ly, FH, H = 9.0, 5.2, 1.7, 2.3
    wood, roofs, metal = [], [], []
    for sx in np.linspace(-Lx / 2 + 0.3, Lx / 2 - 0.3, 6):
        for sy in (-Ly / 2 + 0.3, 0.0, Ly / 2 - 0.3):
            wood.append(xf(K.box(0.22, 0.22, FH, bev=0.0), (sx, sy, -0.3)))
    wood.append(xf(K.box(Lx + 0.4, Ly + 0.4, 0.18, bev=0.0), (0, 0, FH - 0.1)))
    for rzz, L, D, win in ((0.0, Lx, Ly, (0.7, 1.6)), (math.pi / 2, Ly, Lx, None), (-math.pi / 2, Ly, Lx, None)):
        w = far_wall(L, H, 0.14, step=0.25, window=win, panel=1.5)
        w.v[:, 1] -= D / 2
        wood.append(xf(w, (0, 0, FH + 0.08), (0, 0, rzz)))
    top = FH + 0.08 + H * 1.14
    r1, ridge1 = gonjong_roof(Lx * 0.62, Ly + 2.2, 2.9, -0.15, 2.7, 2.4, nb=10, nh=9, nt=8)
    roofs.append(xf(r1, (0, 0, top - 0.2)))
    for t in roof_horn_tips(ridge1):
        metal.append(finial((t[0], t[1], t[2] + top - 0.2), 0.9, 0.06))
    for side in (-1, 1):  # stepped side roofs (anjung), lower, reaching further out
        r2, ridge2 = gonjong_roof(2.2, Ly + 1.6, 1.6, -0.1, 1.9, 1.7, nb=4, nh=8, nt=6, horns=(side < 0, side > 0))
        r2 = xf(r2, (side * (Lx * 0.5 - 0.9), 0, top - 0.6))
        # only the outer half of each side roof shows past the main roof
        roofs.append(r2)
        t = ridge2[-1] if side > 0 else ridge2[0]
        metal.append(finial((t[0] + side * (Lx * 0.5 - 0.9), t[1], t[2] + top - 0.6), 0.7, 0.05))
    r3, ridge3 = gonjong_roof(1.2, 2.6, 1.5, -0.05, 1.5, 1.1, nb=4, nh=7, nt=6)  # porch gonjong toward the viewer
    roofs.append(xf(xf(r3, (0, 0, 0), (0, 0, math.pi / 2)), (0, -Ly / 2 - 0.9, FH + H * 0.95)))
    t = ridge3[0]
    metal.append(xf(finial((t[0], t[1], t[2]), 0.6, 0.05), (0, 0, 0)))
    metal[-1] = xf(xf(metal[-1], (0, 0, 0), (0, 0, math.pi / 2)), (0, -Ly / 2 - 0.9, FH + H * 0.95))
    wood.append(xf(K.box(2.2, 1.8, 0.15, bev=0.0), (0, -Ly / 2 - 0.9, FH - 0.1)))
    for sx in (-0.9, 0.9):
        wood.append(xf(K.box(0.18, 0.18, FH + H * 0.95, bev=0.0), (sx, -Ly / 2 - 1.7, -0.3)))
    for k in range(6):
        wood.append(xf(K.box(1.2, 0.32, 0.08, bev=0.0), (0, -Ly / 2 - 2.0 - 0.3 * k, FH - 0.3 - 0.27 * k)))
    gz = ground(x, y)
    put = lambda lst: [xf(p, (x, y, gz), (0, 0, rz), s) for p in lst]
    A.add("far", "MatWood_timber", [paint(q, TIMBER, var=0.05, ao=0.35, ao_h=2.0, ground=gz) if q.c is None else q for q in put(wood)])
    A.add("far", "MatThatch_ijuk", put(roofs))
    A.add("far", "MatThatch_ijuk", [paint(q, BRASS, ao=0.0, top=0.4) for q in put(metal)])


def far_rangkiang(A, x, y, rz, s=1.0):
    gz = ground(x, y)
    wood = [xf(K.box(0.15, 0.15, 1.0, bev=0.0), (sx, sy, -0.1)) for sx in (-0.6, 0.6) for sy in (-0.45, 0.45)]
    wood.append(xf(K.box(1.75, 1.45, 0.1, bev=0.0), (0, 0, 0.9)))
    for rzz, L, D in ((0.0, 1.5, 1.2), (math.pi, 1.5, 1.2), (math.pi / 2, 1.2, 1.5), (-math.pi / 2, 1.2, 1.5)):
        w = far_wall(L, 1.25, 0.18, step=0.25, panel=0.75)
        w.v[:, 1] -= D / 2
        wood.append(xf(w, (0, 0, 1.0), (0, 0, rzz)))
    roof, _ = gonjong_roof(1.6, 2.1, 1.35, -0.12, 0.85, 0.55, nb=4, nh=5, nt=4)
    put = lambda lst: [xf(p, (x, y, gz), (0, 0, rz), s) for p in lst]
    A.add("far", "MatWood_timber", [paint(q, TIMBER, ao=0.3, ao_h=1, ground=gz) if q.c is None else q for q in put(wood)])
    A.add("far", "MatThatch_ijuk", put([xf(roof, (0, 0, 2.25 + 0.0))]))


def istana(A):
    """Istana Lama Seri Menanti: long dark-timber palace on posts, two storeys, central tower with tiered roofs."""
    a = math.radians(-7.0)
    x, y = VCAM[0] + 88 * math.sin(a), VCAM[1] + 88 * math.cos(a)
    gz = ground(x, y)
    th = math.atan2(VCAM[0] - x, y - VCAM[1])
    wood, roofs = [], []
    for sx in np.linspace(-11, 11, 9):
        wood.append(xf(K.box(0.4, 0.4, 2.4, bev=0.0), (sx, -3.6, -0.5)))
    for (W, D, z0, H, flare) in ((24.0, 8.0, 1.9, 3.0, 0.0), (18.0, 7.0, 4.9, 2.6, 0.0)):
        w = far_wall(W, H, flare, step=1.0, window=(0.8, 2.0), panel=1.6)
        w.v[:, 1] -= D / 2
        wood.append(xf(w, (0, 0, z0)))
        wood.append(xf(K.box(W, D, H, bev=0.0), (0, 0.05, z0)))
    roofs.append(xf(K.thatch_roof(24.0, 8.0, 1.4, courses=1, over=0.8, seed=3, tooth=0.0, cw=4.0), (0, 0, 4.9)))
    roofs.append(xf(K.thatch_roof(18.0, 7.0, 2.6, courses=1, over=0.8, seed=4, tooth=0.0, cw=4.0), (0, 0, 7.5)))
    wood.append(xf(K.box(4.5, 4.5, 5.0, bev=0.0), (0, -1.0, 7.5)))  # tower
    for k, (r, z, h) in enumerate(((4.2, 12.5, 1.6), (3.0, 14.4, 1.4), (1.8, 16.0, 2.4))):
        roofs.append(xf(K.lathe([(0, z - 0.3), (r * 1.414, z - 0.3), (0.0, z + h)], seg=4, phase=math.pi / 4, cap0=True), (0, -1.0, 0)))
        if k < 2:
            wood.append(xf(K.box(r * 1.4, r * 1.4, 1.1, bev=0.0), (0, -1.0, z + h - 0.6)))
    A.add("far", "MatWood_timber", [paint(xf(q, (x, y, gz), (0, 0, th)), TIMBER, var=0.05, ao=0.3, ao_h=3, ground=gz) if q.c is None else xf(q, (x, y, gz), (0, 0, th)) for q in wood])
    A.add("far", "MatThatch_ijuk", [paint(xf(q, (x, y, gz), (0, 0, th)), (0.24, 0.20, 0.18), var=0.04, top=0.3) for q in roofs])


def palms(A):
    rng = random.Random(9)
    for k, (x, y, h) in enumerate(((10.5, 21.0, 9.0), (20.5, 22.5, 10.0), (19.0, 30.0, 8.5), (-6.0, 30.0, 9.5), (-12.0, 26.0, 8.0),
                                   (4.0, 38.0, 9.0), (-18.0, 40.0, 10.0), (-1.0, 50.0, 8.5))):
        tr, lf = K.coconut_palm(h, seed=800 + k, fronds=8)
        gz = ground(x, y) - 0.1
        A.add("far", "MatWood_timber", paint(xf(tr, (x, y, gz)), (0.44, 0.38, 0.30), ao=0.3, ao_h=2, ground=gz))
        A.add("far", "MatLeaf_canopy", paint(xf(lf, (x, y, gz)), (0.26, 0.40, 0.16), var=0.1, ao=0.0, top=0.35, namp=0.15, ns=1))
    for k in range(10):  # orchard / kampung groves in the valley
        a = math.radians(rng.uniform(-30, 30))
        d = rng.uniform(40, 80)
        x, y = VCAM[0] + d * math.sin(a), VCAM[1] + d * math.cos(a)
        h = rng.uniform(4, 7)
        b = K.canopy(h * 0.45, seed=820 + k, lumps=3, sub=2, squash=0.75, spread=0.8)
        A.add("far", "MatLeaf_canopy", paint(xf(b, (x, y, ground(x, y) + h * 0.35)), (0.20, 0.32, 0.14), var=0.12, ao=0.4, ao_h=h, ground=ground(x, y), top=0.45))
        A.add("far", "MatWood_timber", paint(K.tube([(x, y, ground(x, y) - 0.2), (x, y, ground(x, y) + h * 0.45)], 0.18, seg=5), (0.32, 0.26, 0.2), ao=0))


def pinang(A, x, y, h, seed):
    """areca palm: ruler-straight ringed trunk, small tufted crown (vertical rhythm for the vista)."""
    rng = random.Random(seed)
    gz = ground(x, y)
    lean = (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15))
    top = (x + lean[0], y + lean[1], gz + h)
    A.add("far", "MatWood_timber", paint(K.tube([(x, y, gz - 0.1), top], [0.1, 0.07], seg=6), (0.58, 0.56, 0.48), ao=0.2, ao_h=2, ground=gz))
    lv = []
    for k in range(7):
        a = 2 * math.pi * k / 7 + rng.uniform(-0.2, 0.2)
        L = rng.uniform(1.6, 2.2)
        pts = [(top[0] + L * t * math.cos(a), top[1] + L * t * math.sin(a), top[2] + 0.9 * t - 1.3 * t * t) for t in (0, 0.33, 0.66, 1.0)]
        lv.append(K.strip_mesh(pts, [0.04, 0.22, 0.2, 0.03], fold=-0.3, tears=0.3, seed=seed * 9 + k))
    A.add("far", "MatLeaf_canopy", paint(join(lv), (0.30, 0.44, 0.18), var=0.1, ao=0.0, top=0.35))


def backdrop(A):
    A.add("far", "MatLeaf_canopy", ridge_layer(96, -60, 42, VAL_Z - 1.0, 5.0, 12.0, 61, (0.26, 0.40, 0.18), (0.18, 0.28, 0.13), n=90, freq=3.4, crowns=1.3, lean=0.5))
    A.add("far", "MatLeaf_canopy", ridge_layer(180, -60, 44, VAL_Z - 2.0, 14.0, 28.0, 62, (0.26, 0.40, 0.36), (0.18, 0.30, 0.26), n=70, freq=2.8, crowns=1.0,
                                                peaks=[(18, 8, 7)]))
    A.add("far", "MatLeaf_canopy", ridge_layer(340, -62, 46, VAL_Z - 4.0, 26.0, 46.0, 63, (0.42, 0.50, 0.66), (0.36, 0.44, 0.58), n=60, freq=2.2,
                                                peaks=[(-8, 16, 8), (30, 10, 6)]))
    for k, (yaw, dist, el, w, h) in enumerate(((-42, 250, 10.0, 110, 22), (-14, 290, 13.5, 140, 26), (12, 260, 11.0, 100, 20), (32, 230, 14.0, 90, 18),
                                                (-28, 210, 16.0, 60, 11), (24, 320, 7.0, 130, 16), (-2, 330, 6.0, 120, 14), (44, 200, 9.0, 60, 12))):
        a = math.radians(yaw)
        x, y = VCAM[0] + dist * math.sin(a), VCAM[1] + dist * math.cos(a)
        z = 3.2 + dist * math.tan(math.radians(el))
        A.add("far", "MatPlaster_cloud", face_vista(cloud_flat(w, h, seed=160 + k, lit=(1.0, 0.95, 0.84), shade=(0.62, 0.66, 0.80), n=30, rim=h * 0.08), x, y, z))


# ================================================================ build
def build(A):
    for name in ("MatGrass_lawn", "MatGround_earth", "MatRock_stone", "MatWood_timber", "MatThatch_ijuk", "MatLeaf_canopy",
                 "MatMetal_brass", "MatWater_pond", "MatCloth_kain", "MatPlaster_cloud"):
        A.mat(name)
    A.mat("MatGlow_fire", emit=(1.0, 0.62, 0.3), estr=3.5)

    # ---- flanks: rangkiang pair (left), balai adat (right)
    for k, (rx, ry, s) in enumerate(RANGKIANG):
        rangkiang(A, rx, ry, 0.12 if k else -0.1, s)
    balai(A, BALAI[0], BALAI[1], 0.06)
    apron_left(A)
    kemboja(A, -11.8, -1.6, 3.6, seed=5)
    kemboja(A, 12.2, -0.4, 3.4, seed=6)
    for k, (mx, my, cols) in enumerate(((6.6, 5.2, (GOLD, RED, BLACK)), (8.0, 5.4, (RED, BLACK, GOLD)), (-6.4, 5.3, (BLACK, GOLD, RED)), (-12.2, 4.6, (GOLD, RED, BLACK)))):
        marawa(A, mx, my, 4.4, seed=k, cols=cols)

    # ---- apron + paths + gathering + kawah
    kawah(A, KAWAH[0], KAWAH[1])
    gathering(A)
    flagstones(A)
    terrace_edge(A)
    for k, (bx, by, h, fl) in enumerate(((-4.4, -6.4, 0.9, (0.92, 0.32, 0.12)), (-2.9, -6.7, 0.8, (0.92, 0.32, 0.12)), (2.4, -6.6, 0.85, (0.95, 0.80, 0.25)),
                                          (3.9, -6.3, 0.95, (0.92, 0.32, 0.12)), (5.8, -4.6, 1.0, None), (-6.6, -4.4, 1.0, None))):
        bush(A, bx, by, h, seed=40 + k, rgb=(0.24, 0.40, 0.16), flowers=fl)
    for k, (px, py) in enumerate(((1.7, -6.45), (-1.3, -6.4))):  # potted plants either side of the path
        gz = ground(px, py)
        A.add("battle", "MatRock_stone", paint(xf(K.jar(0.2, 0.42), (px, py, gz - 0.02)), (0.66, 0.38, 0.24), ao=0.35, ao_h=0.3, ground=gz, top=0.2))
        lv = []
        for j in range(9):
            a = 2 * math.pi * j / 9
            lv.append(K.strip_mesh([(px, py, gz + 0.38), (px + 0.2 * math.cos(a), py + 0.2 * math.sin(a), gz + 0.68), (px + 0.38 * math.cos(a), py + 0.38 * math.sin(a), gz + 0.55)],
                                   [0.02, 0.07, 0.01], fold=0.3, seed=j))
        A.add("battle", "MatLeaf_canopy", paint(join(lv), (0.26, 0.48, 0.20), var=0.1, ao=0.0, top=0.3))
        A.contact(px, py, 0.5, 0.3)

    # ---- lower garden terrace (far band)
    pond(A)
    kemboja(A, 4.6, 8.0, 3.8, seed=7)
    kemboja(A, -7.2, 8.6, 4.2, seed=8)
    for k, (bx, by) in enumerate(((-5.0, 7.2), (0.2, 7.3), (6.5, 7.0), (-9.6, 7.4), (9.0, 7.6))):
        bush(A, bx, by, 0.8, seed=60 + k, rgb=(0.22, 0.38, 0.15), flowers=(0.95, 0.42, 0.55) if k % 2 else (0.95, 0.85, 0.30), sub=2)

    # ---- terrain
    A.terrain(ground, gcolor, kind=gkind, rin=4.5, rout=100.0, split=23.0, cull=gcull, seed=1)

    # ---- scatter: lawn tufts, terrace-edge grass, pond reeds
    rng = random.Random(3)
    for k in range(190):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(6.2, 14.5)
        x, y = r * math.cos(a), r * math.sin(a)
        if path_dist(x, y) < 0.55 or not visible(x, y) or abs(y - edge_y(x)) < 0.5 or math.hypot(x - POND[0], y - POND[1]) < POND[2] + 0.4:
            continue
        A.scatter_patch("Grass", 26, x, y, rng.uniform(0.6, 1.3), ground, GRASS_TINT, seed=k)
    for k in range(40):
        x = rng.uniform(-12, 12)
        if abs(x - STEPS_X) < 0.9:
            continue
        A.scatter_patch("Grass", 34, x, edge_y(x) - 0.45, rng.uniform(0.3, 0.5), ground, (0.46, 0.54, 0.24), seed=300 + k)
    for k in range(10):
        a = rng.uniform(0, 2 * math.pi)
        x, y = POND[0] + (POND[2] + 0.3) * 1.1 * math.cos(a), POND[1] + (POND[2] + 0.3) * 0.88 * math.sin(a)
        A.scatter_patch("Reed", 10, x, y, 0.35, ground, (0.40, 0.48, 0.22), seed=400 + k)

    # ---- far set
    rumah_gadang(A, KNOLL[0], KNOLL[1], math.atan2(VCAM[0] - KNOLL[0], KNOLL[1] - VCAM[1]), 1.1)
    far_rangkiang(A, KNOLL[0] - 7.4, KNOLL[1] - 2.5, -0.3, 1.0)
    far_rangkiang(A, KNOLL[0] - 5.4, KNOLL[1] - 4.6, -0.35, 0.85)
    rumah_gadang(A, 11.0, 58.0, math.atan2(VCAM[0] - 11.0, 58.0 - VCAM[1]), 0.9)
    far_rangkiang(A, 4.5, 55.0, -0.2, 1.2)
    for k, (x, y, h) in enumerate(((-5.5, 13.5, 7.5), (5.5, 15.0, 8.5), (-10.5, 16.0, 7.0), (7.5, 13.2, 6.5), (-1.0, 17.5, 8.0))):
        pinang(A, x, y, h, seed=k)
    istana(A)
    palms(A)
    backdrop(A)


if __name__ == "__main__":
    K.main("nsembilan", build, MOOD)
    write_mood("nsembilan", MOOD)
