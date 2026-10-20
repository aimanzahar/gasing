"""Perak arena -- an old Kinta tin-mining slope (design_art.md section c, USER_SPEC Perak). SLOPE arena:
the land falls toward +x (ARENA_DEFS.perak.hazard.dir = (1, 0)); the dish sits level on a terrace cut into
the tailings, with a timber crib retaining wall uphill (-x) and a stone-pitched embankment downhill (+x).
Ground: pale tin tailings with wet rills running downhill, ore puddles, tailings mounds.
Apron: dulang pans, carbide lamps, a basket of tin ore, changkul. Far band: palong sluice chute on trestles that
grow taller downhill, water rushing down it. Left flank (uphill): limestone cliff with a cave mouth, spring pipe.
Right flank (downhill): turquoise mining pool with a rusted tin-dredge hulk and its bucket ladder.
Far set (vista): flooded valley of pools and white tailings islands, a second dredge, layered Kinta karsts, clouds.

NOTE main.gd: the terrain drops below y=-0.5 here, so the legacy "Ground" plane must be hidden for this arena.

  blender -b --factory-startup -P art_src/arena_perak.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)
import arena_kedah as KD  # shared vista helpers (band, clouds, skirt, blobs, camera footprints)
importlib.reload(KD)
import numpy as np
from arenakit import P, xf, aim, join, paint, tint, nz, smooth01
from arena_kedah import blob, pillow, band, paint_band, relief_cloud, skirt, vpt, in_vista, in_battle, mix, CAM_V

MOOD = {"sky_top": (0.36, 0.51, 0.72), "sky_horizon": (0.88, 0.86, 0.80), "fog": (0.70, 0.72, 0.70),
        "fog_density": 0.0025, "sun_color": (1.0, 0.93, 0.80), "sun_energy": 1.05,
        "lantern": (1.0, 0.70, 0.42), "lantern_energy": 1.2, "exposure": 0.8, "ambient": 0.5,
        "b_sun": 3.6, "b_world": 1.0, "b_fill": 0.4, "b_lantern": 6.0}

# ---------------------------------------------------------------- palette (sRGB)
TAIL = (0.52, 0.50, 0.45)       # pale tin tailings (kept below the dish value)
TAIL_DK = (0.42, 0.40, 0.36)
TAIL_WARM = (0.54, 0.46, 0.37)
TAIL_FAN = (0.64, 0.62, 0.57)   # fresh white tailings fanning downhill
RUSTSTAIN = (0.60, 0.44, 0.32)
WETSAND = (0.40, 0.40, 0.38)
LATERITE = (0.55, 0.35, 0.23)
GRASSY = (0.36, 0.43, 0.19)
LIME = (0.74, 0.72, 0.66)
TIMBER = (0.46, 0.37, 0.27)
TIMBER_DK = (0.30, 0.23, 0.17)
RUST = (0.50, 0.27, 0.15)
RUST_DK = (0.33, 0.19, 0.12)
ZINC = (0.56, 0.55, 0.52)
POOL = (0.22, 0.55, 0.54)
POOL_DEEP = (0.16, 0.42, 0.45)
POOL_MILK = (0.52, 0.66, 0.62)
LEAF = (0.24, 0.36, 0.15)
LEAF_DK = (0.16, 0.27, 0.12)
BRASS = (0.62, 0.48, 0.22)

# ---------------------------------------------------------------- layout
SLOPE = 0.2                      # natural fall per metre toward +x
POOL_Z = -2.45
TX, TY0, TYR = 6.5, 3.5, 2.7     # terrace half-width, start of the rounded far end, its depth
RILLS = [(-2.6, 0.5, 0.3), (1.6, 0.4, 2.1), (4.6, 0.6, 4.0), (-5.5, 0.5, 1.0)]   # (y0, meander amp, phase) downhill
MOUNDS = [(-8.0, 9.5, 1.6, 0.7), (9.0, 9.8, 2.0, 0.6), (-7.6, -4.6, 1.2, 0.4), (16.5, 11.0, 2.4, 0.7), (8.8, -4.2, 1.4, 0.4)]
PALONG = [(-11.6, 10.0), (-8.5, 8.2), (-5.0, 6.95), (0.0, 6.55), (5.0, 6.55), (9.0, 6.9), (12.6, 7.6)]


def cliff_x(y):
    """foot line of the limestone cliff on the uphill side."""
    return -9.3 + 0.5 * math.sin(y * 0.32 + 0.4) + 0.4 * smooth01(2.0, 9.0, y)


def smin(a, b, k):
    return -k * math.log(math.exp(-a / k) + math.exp(-b / k))


def nat_h(x, y):
    """natural hillside before the terrace cut: falls toward +x into the flooded valley."""
    h = -SLOPE * x + 0.06 * nz(x, y, 0, 0.35, 2) + 0.03 * nz(x, y, 0, 1.4, 3)
    h += 0.5 * smooth01(-9.0, -13.0, x)                     # steepening below the cliff
    dunes = 0.0
    if x > 20:
        dunes = 1.1 * smooth01(0.05, 0.45, nz(x, y, 0, 0.045, 9)) * smooth01(20, 34, x)
    valley = POOL_Z - 0.4 + dunes + 0.05 * nz(x, y, 0, 0.6, 4)
    h = -smin(-h, -valley, 0.35)                            # smooth max: the slope runs out onto the valley floor
    for (mx, my, mr, mh) in MOUNDS:
        d = math.hypot(x - mx, y - my) / mr
        if d < 1.6:
            h += mh * max(0.0, 1 - d * d / 2.56) ** 2
    for (y0, amp, ph) in RILLS:
        if x > 6.6:
            dy = abs(y - (y0 + amp * math.sin(0.55 * x + ph)))
            h -= 0.16 * (1 - smooth01(0.0, 0.55, dy)) * smooth01(7.0, 8.2, x) * (1 - smooth01(11.5, 12.8, x))
    return h


def terrace_d(x, y):
    """signed distance-ish outside the levelled terrace (<0 inside)."""
    if y <= TY0:
        return abs(x) - TX
    e = math.hypot(x / TX, (y - TY0) / TYR)
    return (e - 1.0) * (TX if abs(x) > (y - TY0) else TYR) * 0.75


def terrace_h(x, y):
    return 0.02 + 0.012 * nz(x, y, 0, 1.1, 5) - 0.002 * x


def ground(x, y):
    t = terrace_h(x, y)
    d = terrace_d(x, y)
    if d <= 0:
        return t - 0.05 * puddle(x, y)
    hn = nat_h(x, y)
    if hn >= t:   # uphill: the crib wall holds a near-vertical cut
        return t + (hn - t) * smooth01(0.12, 0.26, d)
    w = 0.25 + 0.75 * (t - hn)   # downhill: stone-pitched embankment ~1:0.75
    return t + (hn - t) * smooth01(0.0, w, d)


PUDDLES = [(-3.2, -6.4, 0.8, 0.5), (2.9, -7.2, 1.0, 0.6), (-5.2, 2.6, 0.45, 0.35)]


def puddle(x, y):
    m = 0.0
    for (px, py, rx, ry) in PUDDLES:
        d = math.hypot((x - px) / rx, (y - py) / ry)
        m = max(m, 1 - smooth01(0.6, 1.0, d))
    return m


def shore(y):
    """pool shoreline x (where the natural slope meets the water)."""
    return 12.3 + 0.5 * math.sin(0.3 * y + 1.0)


def gcolor(x, y, z):
    n1 = nz(x, y, 0, 0.4, 11)
    n2 = nz(x, y, 0, 2.0, 12)
    n3 = nz(x, y, 0, 5.5, 13)
    d = terrace_d(x, y)
    c = np.array(TAIL) * (1 + 0.07 * n1 + 0.05 * n2 + 0.03 * n3)
    c = mix(c, TAIL_WARM, 0.45 * smooth01(0.1, 0.5, nz(x, y, 0, 0.3, 14)))
    c = mix(c, TAIL_DK, 0.35 * smooth01(0.2, 0.6, nz(x, y, 0, 0.9, 15)))
    c = mix(c, RUSTSTAIN, 0.45 * smooth01(0.3, 0.7, nz(x, y, 0, 0.55, 19)))
    if d > 0 and x > 6.0:
        c = mix(c, TAIL_FAN, 0.7 * smooth01(0.0, 0.5, nz(x * 0.4, y, 0, 0.6, 20) + 0.3) * smooth01(9.0, 11.5, x))   # fresh white fans by the pool
    if d > 0:
        hn = nat_h(x, y)
        if hn < terrace_h(x, y) and d < 0.25 + 0.75 * (terrace_h(x, y) - hn):   # stone pitching on the embankment
            st = 0.5 + 0.5 * math.sin(x * 9.0 + nz(x, y, 0, 3, 3) * 3) * math.sin(y * 9.0)
            c = mix(c, (0.40, 0.39, 0.36), 0.7) * (0.8 + 0.3 * st)
        if x < -6.0:   # laterite + scrub on the uphill ledge below the cliff
            c = mix(c, LATERITE, 0.6 * smooth01(-6.6, -7.4, x))
            c = mix(c, GRASSY, 0.65 * smooth01(-0.1, 0.4, nz(x, y, 0, 0.7, 16)) * smooth01(-6.8, -7.8, x))
        for (y0, amp, ph) in RILLS:   # wet rills fan out downhill
            if x > 6.6:
                dy = abs(y - (y0 + amp * math.sin(0.55 * x + ph)))
                c = mix(c, (0.30, 0.31, 0.30), 0.85 * (1 - smooth01(0.1, 0.7 + 0.1 * (x - 6.6), dy)) * smooth01(6.9, 7.8, x))
        c = mix(c, WETSAND, 0.85 * (1 - smooth01(POOL_Z + 0.02, POOL_Z + 0.5, z)))      # wet shore band
    else:
        tr = abs(math.sin(y * 0.0 + x * 1.3 + 0.8 * nz(x, y, 0, 0.5, 18)))
        c = mix(c, TAIL_DK, 0.18 * (1 - smooth01(0.0, 0.15, tr)) * (1 - smooth01(4.4, 5.0, math.hypot(x, y))))  # cart tracks
        c = mix(c, np.array(TAIL) * 1.04, 0.5 * (1 - smooth01(4.6, 5.6, math.hypot(x, y))))
        c = mix(c, WETSAND, 0.75 * puddle(x, y))
    if math.hypot(x, y) > 23:
        c = mix(c, (0.80, 0.78, 0.72), 0.35)
    return tuple(np.clip(c, 0, 1))


def gkind(x, y, z):
    if math.hypot(x, y) > 23:
        return "MatSand_tailing"
    if terrace_d(x, y) > 0 and x < -6.7:
        return "MatGround_laterite"
    if z < POOL_Z + 0.35 or (terrace_d(x, y) <= 0 and puddle(x, y) > 0.3):
        return "MatMud_wet"
    return "MatSand_tailing"


def visible(x, y, pad=0.0):
    """battle footprint widened for the lower downhill ground (seen further out) + vista."""
    return in_battle(x - 0.12 * max(0.0, x), y, pad) or in_vista(x, y)


def gcull(cx, cy, zmax):
    if zmax < POOL_Z - 0.03 and cx > 6.0:
        return True
    if cx < cliff_x(cy) - 0.8 and -16 < cy < 40:
        return True   # behind the cliff face
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


# ---------------------------------------------------------------- props
def crib_wall(A):
    """timber crib retaining wall along the uphill edge of the terrace (logs + posts), height follows the cut."""
    logs, posts = [], []
    pts = []
    for y in np.arange(-14.0, TY0 + 0.01, 0.6):
        pts.append((-TX - 0.03, y))
    for k in range(1, 9):
        a = math.pi / 2 * k / 9
        pts.append((-(TX + 0.03) * math.cos(a), TY0 + (TYR + 0.03) * math.sin(a)))
    def cut(x, y):  # noise-free cut height so each log course runs unbroken
        return -SLOPE * (x - 0.25) + 0.5 * smooth01(-9.0, -13.0, x) - 0.02
    for lay in range(7):
        z = 0.12 + lay * 0.2
        run = []
        for q in pts + [None]:
            if q is not None and cut(*q) > z - 0.02:
                run.append((q[0], q[1], terrace_h(*q) + z - 0.06))
                continue
            if len(run) > 1:
                logs.append(K.tube(run, 0.115, seg=7))
            run = []
    for i, (x, y) in enumerate(pts[::3]):
        hh = cut(x, y)
        if hh > 0.25:
            posts.append(xf(K.post(hh + 0.18, 0.08, seed=i, seg=6, lean=0.0), (x + 0.12, y, terrace_h(x, y) - 0.1)))
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_DK if i % 2 else TIMBER, var=0.1, ao=0.45, ao_h=0.8, ground=0.0, namp=0.15, ns=3, stretch=(1, 1, 0.2)) for i, q in enumerate(logs)])
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_DK, var=0.08, ao=0.5, ao_h=0.6, ground=0.0) for q in posts])
    # timber kerb log + pegs along the downhill edge, a few dark stones down the pitched embankment
    kerb = [(TX - 0.1, y, terrace_h(TX, y) + 0.04) for y in np.arange(-11.0, TY0, 0.8)]
    kerb += [(TX * math.cos(math.pi / 2 * k / 8) - 0.1, TY0 + TYR * math.sin(math.pi / 2 * k / 8), 0.06) for k in range(1, 6)]
    A.add("battle", "MatWood_timber", paint(K.tube(kerb, 0.09, seg=7), TIMBER_DK, var=0.05, ao=0.2, ao_h=0.2, ground=-0.1, namp=0.15, ns=3, stretch=(1, 1, 0.2)))
    pegs = [xf(K.post(0.35, 0.04, seed=k, seg=5), (TX + 0.02, y, terrace_h(TX, y) - 0.2)) for k, y in enumerate(np.arange(-10.6, TY0, 1.6))]
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_DK, ao=0.3, ao_h=0.3, ground=-0.2) for q in pegs])
    rng = random.Random(4)
    stones = []
    for k in range(16):
        y = rng.uniform(-8.0, 3.0)
        x = TX + rng.uniform(0.3, 1.1)
        stones.append(xf(K.rock(rng.uniform(0.14, 0.24), seed=300 + k, sub=2, squash=(1.2, 1, 0.6)), (x, y, ground(x, y) - 0.06)))
    A.add("battle", "MatRock_lime", [paint(q, (0.46, 0.45, 0.42), var=0.1, ao=0.4, ao_h=0.2, ground=-1.0) for q in stones])


def palong(A):
    """sluice chute on trestles from the spring at the cliff down to the pool; trestles grow downhill."""
    pts = []
    for (a, b) in zip(PALONG[:-1], PALONG[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / 1.0))
        for t in range(k):
            pts.append((a[0] + (b[0] - a[0]) * t / k, a[1] + (b[1] - a[1]) * t / k))
    pts.append(PALONG[-1])
    s = [0.0]
    for (a, b) in zip(pts[:-1], pts[1:]):
        s.append(s[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    z0, z1 = ground(*PALONG[0]) + 0.35, POOL_Z + 1.5
    zs = [z0 + (z1 - z0) * (si / s[-1]) ** 0.9 for si in s]
    wood, water, foam = [], [], []
    W, Dp = 0.26, 0.3
    # trough: floor + two side boards along the path (extruded U)
    prof = [(-W - 0.04, Dp), (-W - 0.04, 0.0), (W + 0.04, 0.0), (W + 0.04, Dp), (W, Dp), (W, 0.05), (-W, 0.05), (-W, Dp)]
    v, f = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty)
        nx_, ny_ = -ty / l, tx / l
        for (o, z) in prof:
            v.append((x + nx_ * o, y + ny_ * o, zs[i] + z))
    m = len(prof)
    for i in range(len(pts) - 1):
        for k in range(m - 1):
            a = i * m + k
            f.append((a, a + m, a + m + 1, a + 1))
    trough = P(v, f)
    wv, wf = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        nx_, ny_ = -(b[1] - a[1]) / l, (b[0] - a[0]) / l
        for o in (-W + 0.01, W - 0.01):
            wv.append((x + nx_ * o, y + ny_ * o, zs[i] + 0.14))
    for i in range(len(pts) - 1):
        wf.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    wp = P(wv, wf)
    wp.c = np.array([[0.40, 0.56, 0.54, 0.35 + 0.3 * ((i // 2) % 3 == 0)] for i in range(len(wv))])
    A.add("battle", "MatWater_pool", wp)
    # riffles + trestles
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        nx_, ny_ = -(b[1] - a[1]) / l, (b[0] - a[0]) / l
        if i % 2 == 0 and 0 < i < len(pts) - 1:
            wood.append(K.tube([(x - nx_ * W, y - ny_ * W, zs[i] + 0.1), (x + nx_ * W, y + ny_ * W, zs[i] + 0.1)], 0.02, seg=4))
        if i % 2 == 1 or i == len(pts) - 1:
            g0 = ground(x - nx_ * 0.55, y - ny_ * 0.55)
            g1 = ground(x + nx_ * 0.55, y + ny_ * 0.55)
            top = zs[i] - 0.02
            for sgn, g in ((-1, g0), (1, g1)):
                foot = (x + sgn * nx_ * 0.55, y + sgn * ny_ * 0.55, min(g, top) - 0.1)
                wood.append(K.tube([foot, (x + sgn * nx_ * (W + 0.06), y + sgn * ny_ * (W + 0.06), top)], 0.045, seg=6))
            if top - min(g0, g1) > 0.7:   # cross brace on the tall downhill trestles
                wood.append(K.tube([(x - nx_ * 0.5, y - ny_ * 0.5, min(g0, top) + 0.1), (x + nx_ * 0.32, y + ny_ * 0.32, top - 0.1)], 0.03, seg=5))
            wood.append(K.tube([(x - nx_ * (W + 0.15), y - ny_ * (W + 0.15), top - 0.03), (x + nx_ * (W + 0.15), y + ny_ * (W + 0.15), top - 0.03)], 0.04, seg=5))
    # spring pipe from the cliff + waterfall into the pool at the end
    sx, sy = PALONG[0]
    wood.append(K.tube([(cliff_x(sy + 0.6) + 0.2, sy + 0.6, z0 + 0.4), (sx + 0.1, sy, z0 + 0.3)], 0.07, seg=6))
    ex, ey = PALONG[-1]
    fall = P([(ex - 0.2, ey - 0.25, zs[-1] + 0.12), (ex + 0.25, ey - 0.25, zs[-1] + 0.12), (ex + 0.65, ey - 0.3, POOL_Z + 0.02), (ex + 0.25, ey - 0.3, POOL_Z + 0.02)], [(0, 1, 2, 3)])
    fall.c = np.array([[0.62, 0.70, 0.66, 0.3]] * 4)
    A.add("battle", "MatWater_pool", K.dbl(fall))
    A.add("battle", "MatWater_pool", KD.water_quad(ex - 0.2, ey - 1.2, ex + 1.6, ey + 0.8, POOL_Z + 0.01, POOL_MILK, POOL, inset=0.6, a_in=0.3, a_edge=1.0))
    A.add("battle", "MatWood_timber", tint(paint(trough, TIMBER, var=0.06, ao=0.3, ao_h=0.4, ground=-3, namp=0.12, ns=3, stretch=(1, 1, 0.3)),
                                           lambda v, c: c * (0.9 + 0.1 * np.sin(v[:, 0] * 6.0 + v[:, 1] * 3.0))[:, None]))
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_DK, var=0.1, ao=0.4, ao_h=1.0, ground=-2.5, namp=0.12, ns=3) for q in wood])


def panel(w, h, nx, ny=2):
    """subdivided wall sheet in the XZ plane facing -y, centred in x, base at z=0 (carries vertex-colour streaks)."""
    v = [((i / nx - 0.5) * w, 0.0, h * j / ny) for j in range(ny + 1) for i in range(nx + 1)]
    f = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i) for j in range(ny) for i in range(nx)]
    return P(v, f)


def box_walls(w, d, h, loc, per=7.0):
    """four streak-able wall panels of a w x d x h box (base centre at loc)."""
    x, y, z = loc
    return [xf(panel(w, h, max(2, int(w * per))), (x, y - d / 2, z)), xf(panel(w, h, max(2, int(w * per))), (x, y + d / 2, z), (0, 0, math.pi)),
            xf(panel(d, h, max(2, int(d * per))), (x - w / 2, y, z), (0, 0, -math.pi / 2)), xf(panel(d, h, max(2, int(d * per))), (x + w / 2, y, z), (0, 0, math.pi / 2))]


def dredge(A, x, y, rz, s=1.0, set_="battle", stacker=False):
    """rusted tin-dredge hulk: raked pontoon with a deck rim, corrugated shed + winch house streaked with rust,
    a tall braced bucket-ladder gantry at the bow with a sheave, the bucket ladder (toward local -x), stack."""
    met, dark, wood = [], [], []
    L, Wd, Hh = 7.6, 4.6, 1.6
    deck = 0.8
    hull = xf(K.box(L, Wd, Hh, bev=0.08), (0, 0, -0.8))
    hull.v[:, 0] *= np.where(hull.v[:, 2] < -0.2, 0.86, 1.0)                        # raked bow/stern
    met.append(hull)
    met += [xf(panel(L * 0.97, 0.88, 40), (0, sy * (Wd / 2 + 0.01), -0.1), (0, 0, 0 if sy < 0 else math.pi)) for sy in (-1, 1)]   # streaked sides
    met.append(xf(K.box(L + 0.24, Wd + 0.24, 0.14, bev=0.03), (0, 0, deck - 0.07)))   # deck rim
    met += box_walls(5.2, 3.8, 2.7, (0.7, 0, deck))
    met += box_walls(2.6, 2.6, 1.6, (1.6, 0, deck + 2.7))                            # upper winch house
    for (bx, bw, bd, bz, br) in ((0.7, 5.6, 4.2, deck + 2.7, 0.9), (1.6, 3.0, 3.0, deck + 4.3, 0.7)):
        r = xf(K.box(bw, bd, 0.08, bev=0.02), (bx, 0, bz))
        r.v[:, 2] += br * (1 - np.abs(r.v[:, 1]) / (bd / 2))                       # gable roofs
        met.append(K.dbl(r))
    for sy in (-1, 1):  # windows
        for wx in (-1.0, 0.7, 2.4):
            dark.append(xf(K.box(0.7, 0.04, 0.6, bev=0.01), (wx, sy * 1.92, deck + 1.4)))
    # bucket-ladder gantry: four braced legs rising to a sheave frame over the bow
    gx0, gx1, gt = -L / 2 + 0.3, -L / 2 + 2.1, deck + 6.2
    top = {(sx, sy): (-L / 2 + (0.4 if sx < 0 else 1.2), sy * 0.75, gt) for sx in (-1, 1) for sy in (-1, 1)}
    for sy in (-1, 1):
        for sx, gx in ((-1, gx0), (1, gx1)):
            met.append(K.tube([(gx, sy * 1.7, deck), top[(sx, sy)]], 0.1, seg=6))
        for t0, t1 in ((0.0, 0.5), (0.5, 0.95)):   # X-bracing between the leg pair
            p = lambda gx, sx, t: tuple(np.array((gx, sy * 1.7, deck)) + (np.array(top[(sx, sy)]) - np.array((gx, sy * 1.7, deck))) * t)
            met.append(K.tube([p(gx0, -1, t0), p(gx1, 1, t1)], 0.045, seg=4))
            met.append(K.tube([p(gx1, 1, t0), p(gx0, -1, t1)], 0.045, seg=4))
    for sx in (-1, 1):
        met.append(K.tube([top[(sx, -1)], top[(sx, 1)]], 0.09, seg=6))
    met.append(K.tube([top[(-1, -1)], top[(1, -1)]], 0.08, seg=6))
    met.append(K.tube([top[(-1, 1)], top[(1, 1)]], 0.08, seg=6))
    sheave = (-L / 2 + 0.4, 0.0, gt + 0.15)
    met.append(xf(K.wheel(0.55, 0.05, spokes=6), sheave))
    # bucket ladder: two beams from the bow down into the water, a chain of buckets along the top
    a = np.array((-L / 2 + 0.2, 0, deck + 0.5))
    b = np.array((-L / 2 - 6.2, 0, -2.6))
    for sy in (-0.45, 0.45):
        met.append(K.tube([tuple(a + (0, sy, 0)), tuple(b + (0, sy, 0))], 0.12, seg=6))
    for t in np.linspace(0.03, 0.97, 16):
        c = a + (b - a) * t
        bk = xf(K.lathe([(0.0, 0.0), (0.24, 0.0), (0.32, 0.36), (0.0, 0.36)], seg=8, cap1=False), rot=(0, -0.55, 0))
        met.append(xf(bk, tuple(c + (0, 0, 0.16))))
    for sy in (-1, 1):  # hoist cables from the sheave frame to the ladder
        met.append(K.tube([(sheave[0], sy * 0.6, sheave[2]), tuple(a + (b - a) * 0.6 + (0, sy * 0.45, 0.1))], 0.022, seg=4))
    met.append(K.tube([(2.4, 0.9, deck + 2.7), (2.5, 0.9, deck + 5.6)], 0.22, seg=8))   # stack
    if stacker:  # tailings stacker conveyor rising from the stern
        for sy in (-0.35, 0.35):
            met.append(K.tube([(L / 2 - 0.5, sy, deck + 1.8), (L / 2 + 9.0, sy, deck + 7.0)], 0.12, seg=5))
        for t in np.linspace(0.15, 0.95, 6):
            p = np.array((L / 2 - 0.5, 0, deck + 1.8)) + np.array((9.5, 0, 5.2)) * t
            met.append(K.tube([tuple(p + (0, -0.35, 0)), tuple(p + (0, 0.35, 0))], 0.05, seg=4))
        met.append(K.tube([(L / 2 + 6.0, -1.5, -2.0), (L / 2 + 6.0, 0, deck + 5.2), (L / 2 + 6.0, 1.5, -2.0)], 0.1, seg=5))
    for k in range(8):  # deck railing posts
        wood.append(K.tube([(-L / 2 + 0.3 + k * 0.95, -Wd / 2 + 0.1, deck), (-L / 2 + 0.3 + k * 0.95, -Wd / 2 + 0.1, deck + 0.8)], 0.025, seg=4))
    wood.append(K.tube([(-L / 2 + 0.3, -Wd / 2 + 0.1, deck + 0.8), (L / 2 - 0.3, -Wd / 2 + 0.1, deck + 0.8)], 0.025, seg=4))

    def put(lst):
        return [xf(xf(q, s=s), (x, y, POOL_Z), (0, 0, rz)) for q in lst]
    corr = lambda v, c: c * (0.84 + 0.16 * (np.floor((v[:, 0] + v[:, 1]) * 7.0 / s) % 2))[:, None]
    rust = lambda v, c: c + (np.array([*RUST_DK, 1]) - c) * (0.6 * smooth01(-0.2, 0.6, K.nfield(v, 0.9 / s, 7, (1, 1, 0.3))))[:, None]
    streak = lambda v, c: c + (np.array([0.24, 0.12, 0.07, 1]) - c) * (0.75 * smooth01(0.1, 0.5, K.nfield(v, 2.4 / s, 9, (1, 1, 0.04))))[:, None]
    waterline = lambda v, c: c * np.where((v[:, 2] < POOL_Z + 0.35 * s)[:, None], np.array([0.55, 0.62, 0.6, 1]), 1.0)
    mt = "MatMetal_rust"
    A.add(set_, mt, [tint(tint(tint(tint(paint(q, RUST if i % 3 else (0.48, 0.42, 0.36), var=0.08, ao=0.3, ao_h=2.0 * s, ground=POOL_Z, top=0.2, namp=0.1, ns=1.5 / s),
                                         corr), rust), streak), waterline)
                     for i, q in enumerate(put(met))])
    A.add(set_, mt, [paint(q, (0.10, 0.10, 0.10), ao=0.0) for q in put(dark)])
    A.add(set_, mt if set_ == "far" else "MatWood_timber", [paint(q, (0.40, 0.33, 0.26), ao=0.0) for q in put(wood)])


def cliff(A):
    """limestone cliff face on the uphill flank: fluted, overhanging, vegetated ledges, cave mouth."""
    ys = np.arange(-14.0, 44.0, 0.7)
    zs = np.linspace(0.0, 1.0, 14)
    v, f, col = [], [], []
    cave = (3.2, 1.0, 1.6)   # (y, half width, height) at the foot
    for y in ys:
        xf_ = cliff_x(y)
        g = nat_h(xf_ + 0.4, y)
        top = g + 11.0 + 3.0 * nz(0, y, 0, 0.08, 3) + 1.5 * nz(0, y, 0, 0.3, 4)
        for t in zs:
            z = g - 0.4 + (top - g + 0.4) * t
            bulge = 0.9 * math.sin(math.pi * min(1.0, t * 1.15)) + 0.45 * math.sin(t * 9.0 + y * 0.4)
            flute = 0.28 * math.sin(y * 3.1 + 2.0 * nz(0, y, z, 0.4, 5)) + 0.35 * nz(xf_, y, z, 0.45, 6)
            x = xf_ - bulge - flute - 2.2 * t * t
            cv = 0.0
            if abs(y - cave[0]) < cave[1] and z - g < cave[2]:
                cv = math.sqrt(max(0.0, 1 - ((y - cave[0]) / cave[1]) ** 2 - ((z - g) / cave[2]) ** 2))
                x -= 1.3 * cv
            v.append((x, y, z))
            n = K.mnoise.noise(K.Vector((x * 0.3, y * 0.3, z * 0.3)))
            c = np.array(LIME) * (0.92 + 0.12 * n)
            c = mix(c, (0.46, 0.45, 0.42), 0.55 * smooth01(0.2, 0.7, nz(y, z * 0.15, 0, 0.6, 7)))   # rain streaks
            c = mix(c, LEAF_DK, 0.75 * smooth01(0.35, 0.65, nz(y, z, 0, 0.35, 8)) * (0.4 + 0.6 * (t > 0.35)))  # vegetation
            c = mix(c, (0.38, 0.36, 0.32), 0.5 * (1 - smooth01(0.0, 1.2, z - g)))
            c = mix(c, (0.06, 0.06, 0.06), min(1.0, cv * 2.5))
            col.append(c)
    n = len(zs)
    for i in range(len(ys) - 1):
        for k in range(n - 1):
            a = i * n + k
            f.append((a, a + n, a + n + 1, a + 1))
    p = P(v, f)
    p.c = np.ones((len(v), 4))
    p.c[:, :3] = np.clip(np.array(col) * 1.12, 0, 1)
    A.add("battle", "MatSand_tailing", p)   # Sand preset: smooth, streaky, light -- the face is back-lit
    # shrubs + ferns along the foot, a fig hanging off a ledge
    rng = random.Random(12)
    for k in range(9):
        y = rng.uniform(-5.0, 11.0)
        x = cliff_x(y) + rng.uniform(0.3, 1.2)
        gz = ground(x, y)
        q = KD.blob((rng.uniform(0.5, 0.9), rng.uniform(0.5, 0.8), rng.uniform(0.4, 0.6)), sub=2, seed=70 + k, amp=0.25, freq=2.5)
        A.add("battle", "MatLeaf_shrub", paint(xf(q, (x, y, gz + 0.2)), LEAF if k % 2 else LEAF_DK, var=0.1, ao=0.4, ao_h=0.9, ground=gz, top=0.4, namp=0.15, ns=2))
        A.contact(x, y, 1.0, 0.3)
    for k, (y, z) in enumerate(((-1.5, 5.5), (7.5, 7.0), (12.0, 4.5))):
        x = cliff_x(y) - 1.0 - 2.2 * (z / 11.0) ** 2
        q = K.canopy(1.3, seed=80 + k, lumps=3, sub=2, squash=0.6, spread=0.7)
        A.add("battle", "MatLeaf_shrub", paint(xf(q, (x + 0.6, y, nat_h(x, y) + z)), LEAF_DK, var=0.08, ao=0.3, ao_h=2, ground=nat_h(x, y) + z - 1, top=0.5))


def apron(A):
    """dulang pans, carbide lamps, a basket of tin ore, changkul; <=0.6 m, nothing bright by the rope."""
    pan = K.lathe([(0.0, 0.0), (0.06, 0.0), (0.3, 0.075), (0.31, 0.085), (0.29, 0.088), (0.05, 0.015), (0.0, 0.015)], seg=20)
    rings = lambda cx, cy: (lambda v, c: c * (0.86 + 0.14 * (np.floor(np.hypot(v[:, 0] - cx, v[:, 1] - cy) * 30) % 2))[:, None])
    for k, (x, y, dz, tilt) in enumerate(((-4.6, -2.4, 0.0, 0.0), (-4.6, -2.4, 0.06, 0.05), (-4.55, -2.38, 0.12, 0.08), (-5.25, -1.55, 0.18, 1.1))):
        gz = ground(x, y)
        q = xf(pan, (x, y, gz + dz), (tilt, 0, k))
        A.add("battle", "MatWood_timber", tint(paint(q, (0.50, 0.36, 0.24), var=0.05, ao=0.3, ao_h=0.12, ground=gz, top=0.2), rings(x, y)))
    A.contact(-4.7, -2.2, 0.9, 0.35)
    # basket of black tin ore + spilled ore
    bx, by = -4.15, -3.25
    A.add("battle", "MatThatch_atap", tint(paint(on_ground(K.basket(0.2, 0.24), bx, by), (0.48, 0.38, 0.25), ao=0.4, ao_h=0.2, ground=ground(bx, by)),
                                           lambda v, c: c * (0.85 + 0.15 * ((np.floor(v[:, 2] * 40) + np.floor(np.arctan2(v[:, 1] - by, v[:, 0] - bx) * 5)) % 2))[:, None]))
    A.add("battle", "MatRock_lime", paint(on_ground(K.lathe([(0.0, 0.0), (0.2, 0.0), (0.12, 0.05), (0.0, 0.07)], seg=10), bx, by, -0.2), (0.16, 0.15, 0.15), ao=0.0, top=0.3, namp=0.2, ns=20))
    for k in range(7):
        a = k * 0.9
        x, y = bx + 0.3 + 0.18 * math.cos(a), by - 0.2 + 0.12 * math.sin(a)
        A.add("battle", "MatRock_lime", paint(xf(K.rock(0.025, seed=k, sub=1), (x, y, ground(x, y))), (0.18, 0.17, 0.17), ao=0.0))
    A.contact(bx, by, 0.5, 0.35)
    # carbide lamps (brass body + reflector) on a plank, right side
    px_, py_ = 5.0, -1.9
    A.add("battle", "MatWood_timber", paint(on_ground(xf(K.plank(1.1, 0.22, 0.05), rot=(0, 0, 1.2)), px_, py_), TIMBER, ao=0.3, ao_h=0.05, ground=ground(px_, py_)))
    for k, (dx, dy) in enumerate(((-0.12, -0.25), (0.1, 0.2))):
        x, y = px_ + dx, py_ + dy
        gz = ground(x, y) + 0.05
        body = K.lathe([(0.0, 0.0), (0.05, 0.0), (0.055, 0.12), (0.035, 0.16), (0.04, 0.2), (0.0, 0.21)], seg=10)
        refl = xf(K.lathe([(0.012, 0.0), (0.07, 0.03), (0.075, 0.035)], seg=12, cap0=True, cap1=False), (0, 0, 0), (0, -1.4, 0))
        A.add("battle", "MatMetal_rust", paint(xf(body, (x, y, gz)), BRASS, var=0.03, ao=0.2, ao_h=0.1, ground=gz, top=0.3))
        A.add("battle", "MatMetal_rust", paint(xf(refl, (x - 0.06, y, gz + 0.15)), (0.70, 0.62, 0.40), ao=0.0, top=0.3))
    A.contact(px_, py_, 0.8, 0.3)
    # changkul (hoe) + ore sack
    hx, hy = 4.5, -3.6
    gz = ground(hx, hy)
    A.add("battle", "MatWood_timber", paint(K.tube([(hx - 0.55, hy - 0.25, gz + 0.03), (hx + 0.5, hy + 0.1, gz + 0.05)], 0.022, seg=5), (0.52, 0.40, 0.27), ao=0.0))
    A.add("battle", "MatMetal_rust", paint(xf(K.box(0.2, 0.24, 0.012, bev=0.004), (hx + 0.58, hy + 0.12, gz + 0.01), (0, 0.3, 0.3)), (0.32, 0.28, 0.25), ao=0.0))
    sx, sy = 5.25, -3.0
    A.add("battle", "MatCloth_haze", paint(on_ground(xf(pillow(0.55, 0.36, 0.3, seed=7), rot=(0, 0, 0.7)), sx, sy, 0.02), (0.58, 0.50, 0.38), var=0.05, ao=0.4, ao_h=0.3, ground=ground(sx, sy), top=0.2, namp=0.1, ns=8))
    A.contact(sx, sy, 0.6, 0.35)


def terrace_clutter(A):
    """two working clusters on the terrace beyond the apron: sleepers + shovels in a sand heap; sieves + ore sacks."""
    rng = random.Random(14)
    x0, y0 = -5.3, 4.9
    wood = []
    for k in range(5):
        wood.append(xf(K.box(1.6, 0.2, 0.12, bev=0.015), (x0 + rng.uniform(-0.05, 0.05), y0 - 0.22 * (k % 3), terrace_h(x0, y0) + 0.12 * (k // 3)), (0, 0, 0.5 + rng.uniform(-0.06, 0.06))))
    hx, hy = -3.6, 6.0
    heap = blob((0.6, 0.5, 0.32), sub=3, seed=5, amp=0.12, freq=2)
    heap.v[:, 2] = np.maximum(heap.v[:, 2], 0.0)
    A.add("battle", "MatSand_tailing", paint(xf(heap, (hx, hy, terrace_h(hx, hy) - 0.03)), TAIL_FAN, var=0.03, ao=0.4, ao_h=0.3, ground=0, top=0.25, namp=0.1, ns=6))
    for k, ang in enumerate((0.3, -0.25)):
        a = (hx + 0.1 * k, hy - 0.1, terrace_h(hx, hy) + 0.25)
        b = (hx + 0.1 * k + 0.8 * math.sin(ang), hy - 0.1 - 0.15, a[2] + 0.75)
        wood.append(K.tube([a, b], 0.022, seg=5))
        A.add("battle", "MatMetal_rust", paint(xf(K.box(0.2, 0.03, 0.26, bev=0.004), (a[0], a[1], a[2] - 0.22), (0, ang, 0)), (0.34, 0.30, 0.26), ao=0.0))
    A.contact(x0, y0, 1.2, 0.3)
    A.contact(hx, hy, 0.9, 0.3)
    sx, sy = -5.7, -4.6
    for k in range(2):  # round sieves (ayak) leaning on a bucket
        q = K.lathe([(0.0, 0.0), (0.26, 0.0), (0.27, 0.08), (0.25, 0.08), (0.24, 0.02), (0.0, 0.02)], seg=16)
        A.add("battle", "MatWood_timber", tint(paint(xf(q, (sx + 0.2 * k, sy, terrace_h(sx, sy) + 0.18), (1.2, 0, 0.4 + 0.5 * k)), (0.50, 0.40, 0.28), ao=0.2, ground=0),
                                               lambda v, c: c * (0.8 + 0.2 * ((np.floor(v[:, 0] * 30) + np.floor(v[:, 1] * 30)) % 2))[:, None]))
    bk = K.lathe([(0.0, 0.0), (0.13, 0.0), (0.16, 0.28), (0.15, 0.28), (0.12, 0.02), (0.0, 0.02)], seg=12)
    A.add("battle", "MatMetal_rust", paint(xf(bk, (sx + 0.15, sy + 0.35, terrace_h(sx, sy))), (0.40, 0.38, 0.34), ao=0.3, ao_h=0.2, ground=0, top=0.2))
    for k, (dx, dy) in enumerate(((-0.6, 0.3), (-0.9, -0.1))):
        A.add("battle", "MatCloth_haze", paint(xf(pillow(0.5, 0.34, 0.28, seed=50 + k), (sx + dx, sy + dy, terrace_h(sx, sy) - 0.02), (0, 0, 0.6 * k)), (0.55, 0.47, 0.35), var=0.05, ao=0.4, ao_h=0.3, ground=0, top=0.2))
    A.contact(sx - 0.3, sy, 1.1, 0.3)
    A.add("battle", "MatWood_timber", [paint(q, TIMBER if i % 2 else TIMBER_DK, var=0.08, ao=0.35, ao_h=0.3, ground=0, namp=0.1, ns=4) for i, q in enumerate(wood)])


def uphill_props(A):
    """above the crib wall: ore sacks, tool rack, a wheelbarrow on the terrace near the wall."""
    rng = random.Random(9)
    for k, (x, y) in enumerate(((-7.6, -0.8), (-7.9, -0.2), (-7.4, 0.4))):
        gz = ground(x, y)
        A.add("battle", "MatCloth_haze", paint(xf(pillow(0.55, 0.36, 0.3, seed=30 + k), (x, y, gz - 0.03), (0.0, 0.0, 1.5 + rng.uniform(-0.3, 0.3))), (0.56, 0.48, 0.36), var=0.06, ao=0.4, ao_h=0.3, ground=gz, top=0.2))
    A.contact(-7.6, -0.2, 1.0, 0.3)
    # tool rack: two posts + rail with shovels hanging
    x0, y0 = -7.5, 3.4
    gz = ground(x0, y0)
    wood = [xf(K.post(1.1, 0.05, seed=k), (x0, y0 + k * 1.2, gz - 0.1)) for k in range(2)]
    wood.append(K.tube([(x0, y0 - 0.1, gz + 0.95), (x0, y0 + 1.3, gz + 0.95)], 0.035, seg=5))
    for k in range(3):
        wood.append(K.tube([(x0 + 0.04, y0 + 0.2 + k * 0.35, gz + 0.98), (x0 + 0.1, y0 + 0.2 + k * 0.35, gz + 0.15)], 0.02, seg=4))
        A.add("battle", "MatMetal_rust", paint(xf(K.box(0.03, 0.22, 0.28, bev=0.005), (x0 + 0.1, y0 + 0.2 + k * 0.35, gz)), (0.36, 0.30, 0.26), ao=0.0))
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, var=0.1, ao=0.3, ao_h=0.5, ground=gz) for q in wood])
    # wheelbarrow on the terrace (near strip foreground in the vista)
    wx, wy = -4.3, -6.3
    gz = ground(wx, wy)
    tray = xf(K.box(0.62, 0.5, 0.26, bev=0.03), (0, 0, 0.3))
    tray.v[:, 0] *= 1 + 0.25 * (tray.v[:, 2] - 0.3) / 0.26
    parts = [tray]
    for sy in (-1, 1):
        parts.append(K.tube([(-0.45, sy * 0.2, 0.32), (0.75, sy * 0.25, 0.48)], 0.02, seg=4))
        parts.append(K.tube([(0.3, sy * 0.2, 0.0), (0.25, sy * 0.2, 0.3)], 0.02, seg=4))
    whl = xf(K.wheel(0.17, 0.03, spokes=5), (-0.55, 0, 0.17))
    A.add("battle", "MatMetal_rust", [paint(xf(q, (wx, wy, gz), (0, 0, 2.3)), RUST, var=0.05, ao=0.3, ao_h=0.3, ground=0) for q in parts + [whl]])
    A.add("battle", "MatSand_tailing", paint(xf(K.lathe([(0.0, 0.0), (0.28, 0.0), (0.1, 0.1), (0.0, 0.12)], seg=10), (wx, wy, gz + 0.5), s=(1.1, 0.9, 1)), TAIL, ao=0.0, top=0.3))
    A.contact(wx, wy, 0.8, 0.3)


def rail(A):
    """narrow-gauge mine rail along the downhill edge of the terrace, with a tipping skip (lori) and buffer stop."""
    xr = 6.05
    wood, met = [], []
    for y in np.arange(-13.0, 2.9, 0.55):
        wood.append(xf(K.box(0.18, 0.95, 0.07, bev=0.0), (xr, y, terrace_h(xr, y) - 0.04), (0, 0, math.pi / 2 + 0.06 * math.sin(y * 3))))
    for sy in (-0.3, 0.3):
        met.append(K.tube([(xr + sy, y, terrace_h(xr, y) + 0.05) for y in np.arange(-13.0, 3.0, 2.0)], 0.03, seg=4))
    wood.append(xf(K.box(0.9, 0.25, 0.4, bev=0.03), (xr, 3.05, terrace_h(xr, 3.0) - 0.02)))    # buffer stop
    wx, wy = xr, 2.3
    gz = terrace_h(wx, wy)
    body = K.lathe([(0.0, 0.0), (0.05, 0.0), (0.45, 0.45), (0.47, 0.5), (0.0, 0.5)], seg=4, phase=math.pi / 4)
    body = xf(body, (0, 0, 0.0), s=(0.85, 0.75, 1.0))
    met.append(xf(body, (wx, wy, gz + 0.36), (0, 0, math.pi / 2)))
    met.append(xf(K.box(0.62, 0.95, 0.1, bev=0.02), (wx, wy, gz + 0.2)))
    for sx in (-0.3, 0.3):
        for sy in (-0.32, 0.32):
            met.append(xf(xf(K.wheel(0.13, 0.025, spokes=4), rot=(0, 0, math.pi / 2)), (wx + sx, wy + sy, gz + 0.16)))
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_DK, var=0.12, ao=0.3, ao_h=0.1, ground=-0.05) for q in wood])
    A.add("battle", "MatMetal_rust", [tint(paint(q, RUST, var=0.06, ao=0.35, ao_h=0.5, ground=gz, top=0.2, namp=0.15, ns=6),
                                           lambda v, c: c + (np.array([*RUST_DK, 1]) - c) * (0.5 * smooth01(-0.2, 0.6, K.nfield(v, 3.0, 5)))[:, None]) for q in met])
    A.add("battle", "MatSand_tailing", paint(xf(K.lathe([(0.0, 0.0), (0.4, 0.0), (0.15, 0.14), (0.0, 0.16)], seg=10), (wx, wy, gz + 0.8), s=(0.9, 1.0, 1)), TAIL_FAN, ao=0.0, top=0.3, namp=0.1, ns=10))
    A.contact(wx, wy, 0.9, 0.35)


def downhill_props(A):
    """on the falling ground: a jig box (sieve) beside a rill, scattered planks, reeds on the shore."""
    x, y = 9.2, 0.6
    gz = ground(x, y)
    box = xf(K.box(1.0, 0.7, 0.32, bev=0.03), (x, y, gz - 0.04), (0, 0.12, 0.3))
    A.add("battle", "MatWood_timber", paint(box, TIMBER, var=0.06, ao=0.4, ao_h=0.3, ground=gz))
    A.add("battle", "MatMetal_rust", paint(xf(K.grid(0.85, 0.55, 8, 6), (x, y, gz + 0.22), (0, 0.12, 0.3)), (0.30, 0.26, 0.22), ao=0.0))
    A.contact(x, y, 1.0, 0.3)
    for k, (px, py, rz) in enumerate(((8.0, -2.4, 0.3), (10.6, 2.4, 1.9))):
        gz = ground(px, py)
        A.add("battle", "MatWood_timber", paint(xf(K.plank(1.4, 0.22, 0.05, warp=0.02), (px, py, gz + 0.01), (0, -0.2, rz)), TIMBER_DK, var=0.08, ao=0.3, ao_h=0.1, ground=gz))
    rng = random.Random(5)
    for k in range(14):
        yy = rng.uniform(-6.0, 12.0)
        xx = shore(yy) + rng.uniform(-0.6, 0.2)
        A.scatter_patch("Reed", 10, xx, yy, rng.uniform(0.35, 0.7), lambda a, b: max(ground(a, b), POOL_Z), (0.44, 0.48, 0.26), seed=200 + k)


# ---------------------------------------------------------------- far set
def far_set(A):
    # second dredge (hero of the vista) + stacker, in the flooded valley
    dredge(A, 18.5, 44.0, 2.9, s=1.25, set_="far", stacker=True)
    # miners' huts on a tailings bank
    for k, (yaw, d) in enumerate(((2, 62), (6, 66), (-4, 70))):
        hx, hy = vpt(yaw, d)
        gz = max(nat_h(hx, hy), POOL_Z)
        body = xf(K.box(4.0, 3.0, 2.2, bev=0.05), (hx, hy, gz - 0.1), (0, 0, 0.2 * k))
        roof = xf(K.box(4.6, 3.6, 0.1, bev=0.03), (hx, hy, gz + 2.1), (0, 0, 0.2 * k))
        roof.v[:, 2] += 0.9 * (1 - np.abs((roof.v[:, :2] - (hx, hy)) @ np.array([-math.sin(0.2 * k), math.cos(0.2 * k)])) / 1.8)
        A.add("far", "MatMetal_rust", paint(body, (0.52, 0.46, 0.40), var=0.05, ao=0.3, ao_h=2, ground=gz))
        A.add("far", "MatMetal_rust", paint(roof, RUST, var=0.05, ao=0, top=0.2))
    rng = random.Random(21)
    for k in range(9):   # scrub trees on the far banks
        yaw, d = rng.uniform(-14, 30), rng.uniform(55, 120)
        x, y = vpt(yaw, d)
        gz = nat_h(x, y)
        if gz < POOL_Z + 0.1:
            continue
        h = rng.uniform(4, 7)
        A.add("far", "MatLeaf_shrub", paint(xf(blob((h * 0.45, h * 0.4, h * 0.35), sub=2, seed=90 + k, amp=0.2, freq=2.3), (x, y, gz + h * 0.6)), LEAF_DK if k % 2 else LEAF, var=0.08, ao=0.4, ao_h=h, ground=gz, top=0.45))
    # karst layers: cliff massif continuing far left, isolated towers, a far range
    for k, (yaw, d, h, r) in enumerate(((-6, 150, 48, 16), (9, 175, 62, 18), (24, 140, 40, 12), (34, 210, 58, 16), (-20, 230, 66, 20), (15, 300, 80, 24))):
        x, y = vpt(yaw, d)
        # Kinta tower karsts: fluted walls with vertical water staining, vegetated crown + a green ledge every ~4 m
        p = K.smooth_karst(h, r, seed=500 + k, seg=34, rings=18, cliff=0.25, taper=0.18, ledges=max(2, int(h * 0.34 / 4.0)),
                           rock=(0.66, 0.65, 0.60), streak=(0.34, 0.34, 0.32), stain=(0.62, 0.50, 0.38), veg=(0.17, 0.27, 0.12), veg2=(0.29, 0.39, 0.17))
        A.add("far", "MatRock_lime", K.cull_back(xf(p, (x, y, POOL_Z), (0, 0, k * 0.9))))
    tower = lambda yaw: 30 + 34 * abs(math.sin(math.radians(yaw) * 11 + 0.7)) ** 3 + 22 * abs(math.sin(math.radians(yaw) * 5.3)) ** 4 + 5 * KD.nz(yaw * 0.2, 1, 0, 1, 3)
    A.add("far", "MatRock_lime", paint_band(band(420, -52, 46, tower, 70, n=130), (0.28, 0.36, 0.30), (0.46, 0.48, 0.45), 0, 70, seed=6))
    for k, (yaw, d, z, w, h) in enumerate(((10, 560, 120, 160, 46), (-18, 520, 96, 120, 36), (32, 500, 84, 90, 30), (-40, 600, 130, 140, 44))):
        A.add("far", "MatCloth_haze", relief_cloud(yaw, d, z, w, h, seed=k + 20, top=(0.97, 0.96, 0.93), bot=(0.74, 0.76, 0.80)))
    A.add("far", "MatSand_tailing", skirt(250, 1100, -56, 48, POOL_Z + 0.1, (0.70, 0.70, 0.66)))


# ---------------------------------------------------------------- build
def build(A):
    for name in ("MatSand_tailing", "MatMud_wet", "MatGround_laterite", "MatWater_pool", "MatRock_lime", "MatWood_timber",
                 "MatMetal_rust", "MatLeaf_shrub", "MatThatch_atap", "MatCloth_haze"):
        A.mat(name)

    crib_wall(A)
    palong(A)
    dredge(A, 15.6, 3.6, 0.12)
    cliff(A)
    apron(A)
    uphill_props(A)
    terrace_clutter(A)
    downhill_props(A)
    rail(A)
    for (px, py, rx, ry) in PUDDLES:   # milky ore puddles on the terrace
        n = 12
        rng = random.Random(int(px * 10))
        z = terrace_h(px, py) - 0.025
        v = [(px, py, z)] + [(px + rx * rng.uniform(0.85, 1.05) * math.cos(2 * math.pi * i / n), py + ry * rng.uniform(0.85, 1.05) * math.sin(2 * math.pi * i / n), z) for i in range(n)]
        p = P(v, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)])
        p.c = np.array([[0.40, 0.58, 0.56, 1.0]] + [[0.50, 0.56, 0.52, 0.8]] * n)
        A.add("battle", "MatWater_pool", p)
    # rill trickles on the downhill slope
    for (y0, amp, ph) in RILLS:
        pts = [(x, y0 + amp * math.sin(0.55 * x + ph)) for x in np.arange(7.4, shore(y0) + 0.3, 0.5)]
        if len(pts) < 2:
            continue
        v, f = [], []
        for i, (x, y) in enumerate(pts):
            w = 0.07 + 0.03 * i
            v += [(x, y - w, ground(x, y) + 0.015), (x, y + w, ground(x, y) + 0.015)]
        for i in range(len(pts) - 1):
            f.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
        p = P(v, f)
        p.c = np.array([[0.42, 0.56, 0.54, 0.55]] * len(v))
        A.add("battle", "MatWater_pool", p)

    sp = lambda r: 0.3 if r < 12 else (0.3 + 0.07 * (r - 12) if r < 22 else (1.2 + 0.09 * (r - 22) if r < 80 else min(16.0, 6.4 + 0.2 * (r - 80))))
    A.terrain(ground, gcolor, kind=gkind, rin=4.5, rout=250.0, split=23.0, spacing=sp, cull=gcull, seed=2)

    # pool / flooded valley water: battle strip + far sheet (covers every culled face below POOL_Z)
    for (ya, yb, set_, x1) in ((-14.0, 22.0, "battle", 40.0), (22.0, 300.0, "far", 400.0)):
        ys = np.arange(ya, yb + 0.01, 2.0 if set_ == "battle" else 8.0)
        v, f = [], []
        for y in ys:
            s = shore(y) if y < 30 else 9.0
            v += [(s - 0.8, y, POOL_Z), (s + 2.0, y, POOL_Z), (x1, y, POOL_Z)]
        for i in range(len(ys) - 1):
            a = 3 * i
            f += [(a, a + 1, a + 4, a + 3), (a + 1, a + 2, a + 5, a + 4)]
        p = P(v, f)
        p.c = np.array([list(POOL_MILK) + [0.75], list(POOL) + [1.0], list(POOL_DEEP) + [1.0]] * len(ys))
        A.add(set_, "MatWater_pool", p)
    p = P([(40.0, -14.0, POOL_Z), (400.0, -14.0, POOL_Z), (400.0, 22.0, POOL_Z), (40.0, 22.0, POOL_Z)], [(0, 1, 2, 3)])
    p.c = np.tile(list(POOL_DEEP) + [1.0], (4, 1))
    A.add("far", "MatWater_pool", p)
    p = P([(-60.0, 30.0, POOL_Z), (9.0, 30.0, POOL_Z), (9.0, 300.0, POOL_Z), (-60.0, 300.0, POOL_Z)], [(0, 1, 2, 3)])
    p.c = np.tile(list(POOL) + [1.0], (4, 1))
    A.add("far", "MatWater_pool", p)

    # scatter: lalang on the uphill strip, tufts on the terrace edges and mounds
    rng = random.Random(3)
    for k in range(40):
        y = rng.uniform(-6.0, 12.0)
        x = rng.uniform(cliff_x(y) + 0.4, -6.9)
        A.scatter_patch("Grass", 26, x, y, rng.uniform(0.4, 0.9), ground, (0.52, 0.54, 0.28), seed=k)
    for k in range(30):
        y = rng.uniform(-6.0, 6.0)
        x = rng.choice((-1, 1)) * rng.uniform(5.7, 6.3)
        if math.hypot(x, y) < 5.8:
            continue
        A.scatter_patch("Grass", 22, x, y, rng.uniform(0.25, 0.5), ground, (0.56, 0.56, 0.32), seed=60 + k)
    for (mx, my, mr, mh) in MOUNDS:
        if visible(mx, my):
            A.scatter_patch("Grass", 18, mx, my, mr * 0.8, ground, (0.54, 0.55, 0.30), seed=int(mx * 7))
    far_set(A)


if __name__ == "__main__":
    KD.flatten_preview_ground()
    K.main("perak", build, MOOD)
