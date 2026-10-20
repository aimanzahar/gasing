"""Terengganu arena -- a windy east-coast fishing beach in bright late-afternoon light, boats coming home
(design_art.md section c; USER_SPEC: "fishing boats returning, nets being pulled in, keropok lekor being fried").
WIND hazard: the sea breeze blows onshore, from the sea at the far side toward the camera (Godot +z,
Blender -y). Everything that can lean or stream does so toward -y: casuarina trunks and flagged crowns, flags,
pennants, sarongs on the line, beach grass; sand ripples run across the wind and sand drifts tail downwind.
Ground: wind-rippled pale sand, a seaweed tide line, dark wet sand, swash foam, turquoise shallows.
Apron: fish-drying racks, a heap of green net with floats, raga baskets of fish.
Far band: tide line + foam + a beached perahu with its anchor. Left flank: perahu besar on log rollers with a
carved bangau and a painted prow. Right flank: wind-swept casuarinas, keropok lekor stall, sarongs on a line.
Far set (vista): the bay curving to a casuarina headland with a stilt village, boats returning, Pulau Kapas
and Pulau Gemia on the horizon, cloud flats streaming in the breeze.

  blender -b --factory-startup -P art_src/arena_terengganu.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)
import numpy as np
from arenakit import P, xf, aim, join, paint, tint, nz, smooth01
import arena_selangor as S
from arena_selangor import VCAM, in_vista, visible, mix, face_vista, cloud_flat, ridge_layer, dome, write_mood

MOOD = {"sky_top": (0.16, 0.40, 0.80), "sky_horizon": (0.98, 0.86, 0.66), "fog": (0.80, 0.86, 0.88),
        "fog_density": 0.0024, "sun_color": (1.0, 0.86, 0.64), "sun_energy": 1.15,
        "lantern": (1.0, 0.72, 0.42), "lantern_energy": 1.2, "exposure": 0.82, "ambient": 0.5,
        "b_sun": 3.6, "b_world": 1.0, "b_fill": 0.45, "b_lantern": 8.0}
HAZARD = {"kind": "wind", "strength": 0.9, "period": 8.0, "gust": 2.0, "mode": "flip", "dir": [0.0, 1.0]}  # Godot +z

# ---------------------------------------------------------------- palette (sRGB)
SAND = (0.88, 0.80, 0.64)
SAND_LT = (0.94, 0.88, 0.74)
SAND_WET = (0.64, 0.56, 0.45)
SAND_DK = (0.52, 0.45, 0.36)
WRACK = (0.30, 0.27, 0.18)
DUNE_G = (0.56, 0.58, 0.34)
RHU = (0.32, 0.42, 0.28)
TIMBER = (0.50, 0.38, 0.26)
DRIFT = (0.70, 0.66, 0.58)
SHALLOW = (0.30, 0.66, 0.64)
TEAL = (0.14, 0.42, 0.52)
DEEP = (0.12, 0.32, 0.46)
BOAT = {"red": (0.74, 0.16, 0.12), "yellow": (0.95, 0.76, 0.18), "green": (0.16, 0.52, 0.30), "blue": (0.14, 0.34, 0.70),
        "white": (0.92, 0.90, 0.84), "black": (0.10, 0.10, 0.10)}

# ---------------------------------------------------------------- layout
WZ = -0.42          # sea level (main.tscn's dark Ground plane sits at -0.5 out to 22 m)
PERAHU = (-8.6, 0.6)
BEACHED = (3.2, 6.55)
STALL = (8.6, 1.4)
RHUS = [(10.6, 4.8, 9.5), (12.6, 1.0, 11.0), (9.6, -2.6, 8.0), (-11.8, 5.6, 10.0), (14.0, 7.0, 9.0)]
DRIFTS = []         # (x, y, r): props that shed a downwind (-y) sand drift; filled by the prop builders


def shore_y(x):
    """waterline: straight beach in front, curving seaward into a bay on the right (the headland) and left."""
    return 7.8 + 0.25 * math.sin(0.21 * x + 0.7) + 0.12 * max(0.0, x - 11.0) ** 2 + 0.03 * max(0.0, -x - 13.0) ** 2


def drift(x, y):
    """downwind sand tails behind props: low mounds stretching from each footprint toward -y."""
    h = 0.0
    for (dx, dy, r) in DRIFTS:
        ty = dy - y
        if -0.3 * r < ty < 4.0 * r:
            w = math.exp(-((x - dx) / (0.55 * r + 0.08 * max(0.0, ty))) ** 2)
            h += 0.07 * w * math.exp(-max(0.0, ty) / (1.6 * r)) * smooth01(-0.3 * r, 0.3 * r, ty)
    return h


def ground(x, y):
    s = shore_y(x)
    rip = 0.016 * math.sin(y * 7.2 + 1.1 * nz(x, y, 0, 0.45, 3)) * smooth01(-1.0, 1.5, s - 1.5 - y)
    base = 0.02 * nz(x, y, 0, 0.35, 4) + rip
    back = 0.35 * smooth01(-6.0, -11.0, y) + 0.45 * smooth01(s - 6.0, s - 14.0, y) * smooth01(10.0, 16.0, x)  # dunes behind / on the headland
    h = base + back + drift(x, y)
    h = h + (WZ - 0.04 - h) * smooth01(s - 3.0, s, y)          # beach face down to the waterline
    h = h + (WZ - 0.55 - h) * smooth01(s, s + 3.0, y)          # under water (culled)
    if math.hypot(x, y) < 5.2:
        h = h * smooth01(4.5, 5.2, math.hypot(x, y))
    return float(h)


def gcolor(x, y, z):
    s = shore_y(x)
    n1 = nz(x, y, 0, 0.45, 11)
    n2 = nz(x, y, 0, 2.3, 12)
    n3 = nz(x, y, 0, 6.0, 13)
    c = np.array(SAND) * (1 + 0.05 * n1 + 0.04 * n2 + 0.03 * n3)
    c = mix(c, SAND_LT, 0.45 * smooth01(0.0, 0.5, nz(x * 0.4, y * 2.2, 0, 0.6, 14)))  # blown streaks along the wind
    rip = 0.5 + 0.5 * math.sin(y * 7.2 + 1.1 * nz(x, y, 0, 0.45, 3))
    c = c * (0.96 + 0.06 * rip)
    c = mix(c, SAND_LT, 0.6 * min(1.0, drift(x, y) / 0.05))
    wrack = math.exp(-((y - (s - 2.0 + 0.25 * nz(x, 0, 0, 0.5, 15))) / 0.12) ** 2) * smooth01(-0.2, 0.4, nz(x, y, 0, 1.5, 16))
    c = mix(c, WRACK, 0.75 * wrack)
    wet = smooth01(s - 2.3, s - 0.9, y)
    c = mix(c, mix(SAND_WET, SAND_DK, smooth01(s - 0.8, s, y)), wet)
    veg = max(smooth01(-6.0, -8.0, y), smooth01(s - 5.0, s - 8.0, y) * smooth01(11.0, 14.0, x))
    c = mix(c, np.array(DUNE_G) * (1 + 0.1 * n2), 0.55 * veg * smooth01(-0.1, 0.4, n1))
    r = math.hypot(x, y)  # trodden, damp ring round the gelanggang: frames the dish instead of out-shining it
    c = mix(c, np.array((0.72, 0.64, 0.50)) * (1 + 0.04 * n2), 0.7 * (1 - smooth01(5.0, 6.6, r + 0.4 * n1)))
    return tuple(c)


def gcull(cx, cy, zmax):
    if cy > shore_y(cx) - 0.5 and zmax < WZ - 0.04:
        return True
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


# ================================================================ props
def pennant(x0, y0, z0, L, w, cols, seed, droop=0.15):
    """cloth streaming downwind (-y) from (x0,y0,z0): length L, width w at the hoist, vertical colour bands."""
    rng = random.Random(seed)
    n = 10
    v, c, f = [], [], []
    ph = rng.uniform(0, 6.28)
    for i in range(n + 1):
        t = i / n
        y = y0 - L * t
        x = x0 + 0.12 * L * t * math.sin(ph + t * 5.0)
        z = z0 - droop * L * t * t
        ww = w * (1 - 0.6 * t)
        col = cols[min(len(cols) - 1, int(t * len(cols)))]
        for side in (0.0, 1.0):
            v.append((x + 0.03 * math.sin(ph + t * 7 + side), y, z - side * ww))
            c.append(list(col) + [1.0])
    for i in range(n):
        a = 2 * i
        f.append((a, a + 2, a + 3, a + 1))
    return P(v, f, c)


def hull(L, W, H, bands, n=15, rows_per=2, inner=(0.42, 0.32, 0.22), rail=(0.20, 0.16, 0.12)):
    """east-coast hull along X: pointed upswept ends, rounded V section; painted strakes are crisp because
    every band edge is a duplicated row. bands = [(s0, s1, rgb)] with s = keel(0)..gunwale(1).
    Outer shell + inner (bare timber) shell + gunwale cap. Base (keel mid) at z=0."""
    v, f, c = [], [], []

    def pt(t, s_, side, inset=0.0):
        x = (t - 0.5) * L
        w = W / 2 * max(0.02, math.sin(math.pi * t) ** 0.55)
        zg = H + 0.5 * H * (2 * t - 1) ** 4
        zk = 0.28 * H * (2 * t - 1) ** 6
        a = s_ * math.pi / 2
        y = side * (max(0.0, w * math.sin(a) ** 0.75 - inset))
        z = zk + (zg - zk) * (1 - math.cos(a)) ** 0.85 + (inset * 0.6 if s_ < 0.05 else 0.0)
        return (x, y, z)
    ts = [i / (n - 1) for i in range(n)]
    for side in (-1, 1):
        for (s0, s1, col) in bands:  # outer shell, one strip per band (crisp colours)
            ss = [s0 + (s1 - s0) * k / rows_per for k in range(rows_per + 1)]
            base = len(v)
            for t in ts:
                for s_ in ss:
                    v.append(pt(t, s_, side))
                    c.append(list(col) + [1.0])
            R = len(ss)
            for i in range(n - 1):
                for j in range(R - 1):
                    a = base + i * R + j
                    f.append((a, a + 1, a + R + 1, a + R) if side > 0 else (a, a + R, a + R + 1, a + 1))
        base = len(v)  # inner shell
        ss = [k / 4 for k in range(5)]
        for t in ts:
            for s_ in ss:
                v.append(pt(t, s_, side, inset=0.045))
                c.append(list(np.asarray(inner) * (0.75 + 0.25 * s_)) + [1.0])
        R = len(ss)
        for i in range(n - 1):
            for j in range(R - 1):
                a = base + i * R + j
                f.append((a, a + R, a + R + 1, a + 1) if side > 0 else (a, a + 1, a + R + 1, a + R))
        base = len(v)  # gunwale cap
        for t in ts:
            v.append(pt(t, 1.0, side))
            v.append(pt(t, 1.0, side, inset=0.045))
            c += [list(rail) + [1.0]] * 2
        for i in range(n - 1):
            a = base + 2 * i
            f.append((a, a + 1, a + 3, a + 2) if side > 0 else (a, a + 2, a + 3, a + 1))
    return P(v, f, c)


def perahu_besar(A, x, y, rz, L=7.2, W=1.9, H=1.0, set_="battle", rollers=True, bangau=True, flag=True, n=15):
    """east-coast perahu: crisp painted strakes in boat primaries, tall curled bow post, a carved bangau
    (bird-head mast crutch) on the gunwale, furled sail on the mast, pennants streaming downwind (-y)."""
    rng = random.Random(int(abs(x * 13 + y * 7)))
    z0 = 0.2 if rollers else -0.18
    bottom = BOAT["red"] if rng.random() < 0.6 else BOAT["blue"]
    mid = [BOAT["green"], BOAT["blue"], BOAT["yellow"]][int(abs(x * 3)) % 3]
    bands = [(0.0, 0.42, bottom), (0.42, 0.62, BOAT["white"]), (0.62, 0.82, mid), (0.82, 0.92, BOAT["yellow"]), (0.92, 1.0, BOAT["red"])]
    hl = xf(hull(L, W, H, bands, n=n, rows_per=2 if set_ == "battle" else 1), (0, 0, z0))
    wood, cloth = [hl], []
    for side in (-1, 1):  # stem and stern posts sweeping up from the hull ends, bow curled
        e = side * L / 2
        pts = [(e - side * 0.15, 0, z0 + H * 1.3), (e + side * 0.1, 0, z0 + H * 1.85), (e + side * 0.25, 0, z0 + H * 2.3)]
        if side > 0:
            pts += [(e + side * 0.36, 0, z0 + H * 2.55), (e + side * 0.22, 0, z0 + H * 2.68), (e + side * 0.1, 0, z0 + H * 2.55)]
        wood.append(paint(K.tube(pts, [0.07, 0.06, 0.05, 0.045, 0.04, 0.03][:len(pts)], seg=6), BOAT["yellow"] if side > 0 else BOAT["red"], ao=0.0, top=0.2))
    if bangau:  # bird-head crutch on the port gunwale, carved and painted
        neck = [(L * 0.2 + 0.22 * math.sin(t * 2.2), -W * 0.46, z0 + H * (1.0 + 0.95 * t)) for t in np.linspace(0, 1, 7)]
        b = K.strip_mesh(neck, [0.09, 0.11, 0.12, 0.12, 0.13, 0.16, 0.12], up=(0, 1, 0), seed=5)
        head = xf(K.rock(0.16, seed=9, sub=2, squash=(1.8, 0.35, 0.8)), (L * 0.2 + 0.45, -W * 0.46, z0 + H * 1.92))
        beak = K.tube([(L * 0.2 + 0.6, -W * 0.46, z0 + H * 1.98), (L * 0.2 + 1.0, -W * 0.46, z0 + H * 1.9)], [0.04, 0.005], seg=5)
        wood.append(tint(paint(K.dbl(b), BOAT["red"], ao=0.0), lambda v, c: np.where((((v[:, 2] * 8).astype(int)) % 2 == 0)[:, None], np.array([*BOAT["yellow"], 1]), c)))
        wood.append(paint(head, BOAT["green"], ao=0.0, top=0.3))
        wood.append(paint(beak, BOAT["yellow"], ao=0.0))
        mast_b = (L * 0.2 + 0.4, -W * 0.46, z0 + H * 1.9)
    else:
        mast_b = (L * 0.25, 0.0, z0 + H * 1.2)
    mast_a = (-L * 0.4, 0.0, z0 + H * 1.05)
    wood.append(paint(K.tube([mast_a, mast_b], [0.055, 0.04], seg=6), TIMBER, ao=0.0, namp=0.1, ns=4))
    sa = np.add(mast_a, (0.5, 0.0, 0.07))
    sb = np.add(mast_b, (-0.7, 0.0, 0.05))
    sail = K.tube([tuple(sa), tuple(sa + (sb - sa) * 0.3 + (0, 0, 0.03)), tuple(sa + (sb - sa) * 0.7), tuple(sb)], [0.06, 0.09, 0.08, 0.05], seg=7)
    cloth.append(tint(paint(sail, (0.84, 0.76, 0.60), var=0.05, ao=0.2, ao_h=0.3, ground=z0 + H, namp=0.25, ns=5),
                      lambda v, c: c * (0.8 + 0.2 * (np.floor(v[:, 0] * 2.2) % 2))[:, None]))
    sp = (-L / 2 + 0.35, 0.0, z0 + H * 1.1)
    for k in range(3):
        wood.append(paint(xf(K.box(0.14, W * 0.9, 0.05, bev=0.01), (-L * 0.25 + L * 0.22 * k, 0, z0 + H * 0.78)), TIMBER, ao=0.0))
    if rollers:
        for k in range(3):
            wood.append(paint(K.tube([(-L * 0.3 + L * 0.28 * k, -W * 0.8, 0.12), (-L * 0.3 + L * 0.28 * k, W * 0.8, 0.12)], 0.12, seg=8), (0.56, 0.48, 0.38),
                              ao=0.3, ao_h=0.2, ground=0.0, namp=0.15, ns=4))
    if flag:
        wood.append(paint(K.tube([sp, (sp[0], sp[1], sp[2] + 1.5)], 0.025, seg=5), TIMBER, ao=0.0))
    gz = ground(x, y)
    put = lambda lst: [xf(p, (x, y, gz), (0, 0, rz)) for p in lst]
    A.add(set_, "MatWood_boat", put(wood))
    A.add(set_, "MatCloth_net" if set_ == "battle" else "MatWood_boat", put(cloth))
    if flag:  # pennant streams toward -y in world space (built after placement)
        top = xf(P([(sp[0], sp[1], sp[2] + 1.45)], []), (x, y, gz), (0, 0, rz)).v[0]
        A.add(set_, "MatCloth_net" if set_ == "battle" else "MatWood_boat", pennant(top[0], top[1], top[2], 1.0, 0.3, (BOAT["red"], BOAT["yellow"], BOAT["green"]), seed=int(x)))
    if set_ == "battle":
        A.contact(x, y, max(L, W) * 0.45, 0.3)


def rhu(A, x, y, h, seed, set_="battle", lean=0.2, lumps=9):
    """casuarina (rhu) bent by the onshore wind: trunk leans downwind (-y), branches and the flagged crown
    stream toward -y, upwind side bare."""
    rng = random.Random(seed)
    gz = ground(x, y)
    pts = []
    for t in np.linspace(0, 1, 6):
        pts.append((0.15 * math.sin(t * 2.5 + seed) * h * 0.1, -lean * h * t ** 1.4, h * 0.92 * t - 0.2))
    wood = [K.tube(pts, [0.2 * h / 10, 0.17 * h / 10, 0.15 * h / 10, 0.12 * h / 10, 0.09 * h / 10, 0.06 * h / 10], seg=7)]
    leaf, curtains = [], []
    nb = lumps if set_ == "battle" else max(3, lumps // 2)
    sub_l = 2 if set_ == "battle" else 1
    for k in range(nb):
        t = 0.38 + 0.6 * (k / max(1, nb - 1))
        i = min(len(pts) - 2, int(t * (len(pts) - 1)))
        a = np.array(pts[i]) + (np.array(pts[i + 1]) - np.array(pts[i])) * (t * (len(pts) - 1) - i)
        side = rng.uniform(-1, 1)
        L = h * rng.uniform(0.12, 0.24) * (1.25 - 0.5 * t)
        d = np.array((side * 0.9, -1.0 - rng.uniform(0, 0.6), rng.uniform(0.15, 0.55)))
        d /= np.linalg.norm(d)
        e = a + d * L
        wood.append(K.tube([tuple(a), tuple(e)], [0.05 * h / 10, 0.02 * h / 10], seg=5))
        r = h * rng.uniform(0.07, 0.1)
        if set_ != "battle":
            r *= 1.35
        lump = K.canopy(r, seed=seed * 17 + k, lumps=2 if set_ == "battle" else 1, sub=2, squash=0.8, spread=0.55)
        c0 = e + np.array((0, -r * 0.6, -r * 0.2))
        leaf.append(xf(xf(lump, (0, 0, 0), (0, 0, 0), (1.0, 1.6, 0.95)), tuple(c0)))
        if True:  # drooping needle curtains, combed downwind
            for j in range(4 if set_ == "battle" else 2):
                a0 = c0 + np.array((rng.uniform(-r, r), rng.uniform(-1.4 * r, 0.6 * r), -0.3 * r))
                Ld = rng.uniform(0.5, 1.0) * r * 2.4
                pts_ = [tuple(a0), tuple(a0 + (0.0, -0.35 * Ld, -0.4 * Ld)), tuple(a0 + (0.03, -0.75 * Ld, -0.75 * Ld)), tuple(a0 + (0.0, -1.0 * Ld, -1.0 * Ld))]
                curtains.append(K.strip_mesh(pts_, [0.16 * r * 4, 0.14 * r * 4, 0.1 * r * 4, 0.02], up=(0, -1, 1), tears=0.55, seed=seed * 31 + k * 4 + j))
    top = np.array(pts[-1])
    lump = K.canopy(h * 0.1, seed=seed * 17 + 99, lumps=2, sub=2, squash=0.5, spread=0.6)
    leaf.append(xf(xf(lump, (0, 0, 0), (0, 0, 0), (1.0, 2.0, 0.7)), tuple(top + np.array((0, -h * 0.08, 0.05)))))
    A.add(set_, "MatWood_boat", [paint(xf(q, (x, y, gz)), (0.36, 0.30, 0.25), var=0.06, ao=0.3, ao_h=1.5, ground=gz, namp=0.2, ns=3, stretch=(1, 1, 0.2)) for q in wood])
    A.add(set_, "MatLeaf_rhu", [tint(paint(xf(q, (x, y, gz)), RHU, var=0.1, ao=0.45, ao_h=h, ground=gz, top=0.5, namp=0.3, ns=1.6),
                                     lambda v, c: c * (1.0 + 0.15 * np.clip(-(v[:, 1] - y) / h, 0, 1))[:, None]) for q in leaf])
    if curtains:
        A.add(set_, "MatLeaf_rhu", [paint(xf(q, (x, y, gz)), (0.38, 0.48, 0.32), var=0.12, ao=0.3, ao_h=h, ground=gz, top=0.2) for q in curtains])
    if set_ == "battle":
        A.contact(x, y, 1.0, 0.3)


def fish_rack(A, x, y, rz, seed):
    """para ikan: low trestle with a mesh bed and rows of salted fish (<=0.6 m)."""
    rng = random.Random(seed)
    Lr, Wr, Hr = 2.0, 0.8, 0.5
    wood, net, fish = [], [], []
    for sx in (-0.9, 0.9):
        for sy in (-0.35, 0.35):
            wood.append(K.tube([(sx, sy, -0.05), (sx * 0.98, sy * 0.95, Hr)], 0.03, seg=5))
    for sy in (-0.37, 0.37):
        wood.append(K.tube([(-1.0, sy, Hr), (1.0, sy, Hr)], 0.025, seg=5))
    mesh = K.grid(Lr, Wr, 12, 5, z=Hr + 0.01)
    mesh.v[:, 2] -= 0.03 * (1 - (2 * mesh.v[:, 0] / Lr) ** 2)
    net.append(tint(paint(K.dbl(mesh), (0.30, 0.42, 0.36), ao=0.0, top=0.0),
                    lambda v, c: c * (0.7 + 0.3 * ((np.floor(v[:, 0] * 12) + np.floor(v[:, 1] * 12)) % 2))[:, None]))
    for i in range(10):
        for j in range(4):
            fx, fy = -0.85 + 0.19 * i + rng.uniform(-0.02, 0.02), -0.27 + 0.18 * j
            s = rng.uniform(0.07, 0.09)
            fz = Hr + 0.02 - 0.03 * (1 - (2 * fx / Lr) ** 2)
            fish.append(P([(fx - s, fy, fz), (fx, fy - 0.025, fz + 0.01), (fx + s * 0.8, fy, fz), (fx, fy + 0.025, fz + 0.01), (fx + s * 1.2, fy - 0.025, fz), (fx + s * 1.2, fy + 0.025, fz)],
                          [(0, 1, 3), (1, 2, 3), (2, 4, 5)]))
    gz = ground(x, y)
    put = lambda lst: [xf(p, (x, y, gz), (0, 0, rz)) for p in lst]
    A.add("battle", "MatWood_boat", [paint(q, (0.58, 0.50, 0.40), ao=0.3, ao_h=0.4, ground=gz) for q in put(wood)])
    A.add("battle", "MatCloth_net", put(net))
    A.add("battle", "MatMetal_zinc", [paint(q, (0.78, 0.74, 0.66), var=0.08, ao=0.0, top=0.3) for q in put(fish)])
    A.contact(x, y, 1.1, 0.2)


def net_heap(A, x, y, seed):
    gz = ground(x, y)
    heap = K.rock(0.55, seed=seed, sub=3, amp=0.22, freq=2.2, squash=(1.5, 1.0, 0.42), flat=0.95)
    heap = paint(xf(heap, (x, y, gz - 0.04)), (0.20, 0.46, 0.40), var=0.0, ao=0.4, ao_h=0.3, ground=gz, top=0.3)
    heap = tint(heap, lambda v, c: c * (0.72 + 0.28 * ((np.floor(v[:, 0] * 16 + v[:, 2] * 9) + np.floor(v[:, 1] * 16 - v[:, 2] * 9)) % 2))[:, None])
    A.add("battle", "MatCloth_net", heap)
    rng = random.Random(seed)
    floats = []
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.2, 0.75)
        fx, fy = x + d * math.cos(a) * 1.4, y + d * math.sin(a)
        fz = ground(fx, fy) + max(0.0, 0.22 * (1 - d)) + 0.06
        floats.append(paint(xf(K.rock(0.07, seed=seed + k, sub=2, amp=0.02), (fx, fy, fz - 0.05)), (0.95, 0.45, 0.10) if k % 3 else (0.92, 0.90, 0.84), ao=0.0, top=0.3))
    A.add("battle", "MatCloth_net", floats)
    rope = K.tube(K.arc((x + 0.8, y, gz + 0.1), (x + 1.7, y - 0.6, gz + 0.02), 0.05, n=6), 0.018, seg=4)
    A.add("battle", "MatCloth_net", paint(rope, (0.85, 0.80, 0.62), ao=0.0))
    A.contact(x, y, 0.9, 0.3)


def raga(A, x, y, seed):
    gz = ground(x, y)
    A.add("battle", "MatThatch_atap", tint(paint(on_ground(K.basket(0.2, 0.22), x, y), (0.64, 0.52, 0.32), ao=0.4, ao_h=0.2, ground=gz),
                                           lambda v, c: c * (0.84 + 0.16 * ((np.floor(v[:, 2] * 40) + np.floor(np.arctan2(v[:, 1] - y, v[:, 0] - x) * 5)) % 2))[:, None]))
    rng = random.Random(seed)
    fish = []
    for k in range(6):
        a = rng.uniform(0, 6.28)
        fx, fy = x + 0.08 * math.cos(a), y + 0.08 * math.sin(a)
        fish.append(xf(K.rock(0.06, seed=seed + k, sub=1, squash=(2.2, 0.8, 0.6)), (fx, fy, gz + 0.19), (0, 0, a)))
    A.add("battle", "MatMetal_zinc", [paint(q, (0.70, 0.74, 0.78), ao=0.0, top=0.4) for q in fish])
    A.contact(x, y, 0.35, 0.3)


def keropok_stall(A, x, y, rz):
    """keropok lekor gerai: timber counter, zinc roof, wok on a stove with gas tank, trays of keropok sticks,
    chilli sauce, plastic stools, pressure lamp, a flag streaming downwind."""
    wood, metal, glow, food, plast = [], [], [], [], []
    for sx in (-0.8, 0.8):
        for sy in (-0.32, 0.32):
            wood.append(xf(K.box(0.07, 0.07, 0.82, bev=0.01), (sx, sy, 0)))
    for k in range(5):
        wood.append(xf(K.plank(1.8, 0.14, 0.03), (0, -0.3 + 0.15 * k, 0.82)))
    wood.append(xf(K.box(1.7, 0.03, 0.55, bev=0.008), (0, -0.36, 0.25)))  # front panel
    for sx in (-1.0, 1.0):
        for sy, dh in ((-0.6, 0.0), (0.6, -0.25)):
            wood.append(xf(K.post(2.15 + dh, 0.035, seed=int(sx * 10 + sy * 7), seg=6), (sx, sy, 0)))
    metal.append(xf(S.zinc_sheet(2.4, 1.5), (0, 0, 2.1), (math.atan2(0.25, 1.2), 0, 0)))
    # stove + wok + oil + keropok frying
    metal.append(xf(K.box(0.42, 0.42, 0.12, bev=0.01), (-0.45, 0.05, 0.85)))
    metal.append(xf(K.lathe([(0, 0), (0.12, 0.0), (0.26, 0.07), (0.32, 0.14), (0.33, 0.15), (0.3, 0.15), (0.0, 0.09)], seg=18, cap0=False, cap1=False), (-0.45, 0.05, 0.98)))
    food.append(xf(K.lathe([(0, 0), (0.27, 0.0)], seg=18, cap0=False, cap1=False), (-0.45, 0.05, 1.1)))
    plast.append(xf(K.lathe([(0, 0), (0.14, 0), (0.15, 0.4), (0.1, 0.45), (0.03, 0.47), (0, 0.47)], seg=12), (-0.75, 0.55, 0.0)))  # gas tank
    for k in range(12):  # keropok lekor sticks on a tray
        fx = 0.15 + 0.06 * (k % 6)
        fy = -0.18 + 0.12 * (k // 6)
        food.append(K.tube([(fx, fy - 0.05, 0.875), (fx + 0.01, fy + 0.07, 0.875)], 0.022, seg=6))
    metal.append(xf(K.box(0.5, 0.36, 0.02, bev=0.005), (0.32, -0.12, 0.85)))
    food.append(xf(K.lathe([(0, 0), (0.07, 0.0), (0.09, 0.05), (0.0, 0.045)], seg=10), (0.65, 0.15, 0.85)))
    glow.append(xf(K.lathe([(0, 0), (0.06, 0.0), (0.075, 0.08), (0.05, 0.17), (0, 0.18)], seg=10), (0.3, -0.4, 1.6)))
    metal.append(K.tube([(0.3, -0.4, 1.78), (0.3, -0.4, 2.05)], 0.006, seg=3))
    gz = ground(x, y)
    put = lambda lst: [xf(p, (x, y, gz), (0, 0, rz)) for p in lst]
    A.add("battle", "MatWood_boat", [paint(q, (0.30, 0.48, 0.62) if i == 9 else TIMBER, var=0.08, ao=0.4, ao_h=0.8, ground=gz, namp=0.12, ns=3, stretch=(1, 1, 0.2)) for i, q in enumerate(put(wood))])
    A.add("battle", "MatMetal_zinc", [tint(paint(q, (0.62, 0.63, 0.64), var=0.04, ao=0.0, top=0.1), lambda v, c: c * np.where(
        (np.array([nz(a, b, cc, 1.6, 21) for a, b, cc in v]) > 0.2)[:, None], np.array([0.95, 0.62, 0.42, 1]), 1.0)) for q in put(metal[:1])])
    A.add("battle", "MatMetal_zinc", [paint(q, (0.22, 0.22, 0.22), ao=0.2, ao_h=0.2, ground=gz + 0.8) for q in put(metal[1:])])
    A.add("battle", "MatWood_boat", [paint(q, (0.62, 0.46, 0.26) if i else (0.74, 0.56, 0.20), var=0.06, ao=0.0, top=0.3) for i, q in enumerate(put(food))])
    A.add("battle", "MatWood_boat", [paint(q, BOAT["red"], ao=0.2, ao_h=0.3, ground=gz) for q in put(plast)])
    A.add("battle", "MatGlow_lamp", [paint(q, (1.0, 0.85, 0.55), ao=0.0) for q in put(glow)])
    lp = xf(P([(0.3, -0.4, 1.68)], []), (x, y, gz), (0, 0, rz)).v[0]
    A.light(tuple(lp), 14.0, (1.0, 0.72, 0.42), range_m=4.5)
    for k, (dx, dy, col) in enumerate(((-1.25, -0.6, BOAT["red"]), (-1.35, 0.5, BOAT["blue"]), (0.2, -1.1, BOAT["yellow"]))):
        p = xf(P([(dx, dy, 0)], []), (x, y, 0), (0, 0, rz)).v[0]
        A.add("battle", "MatWood_boat", paint(on_ground(S.stool(), p[0], p[1]), col, var=0.04, ao=0.3, ao_h=0.3, ground=ground(p[0], p[1]), top=0.2))
    # flag on a bamboo pole by the stall: black field with a white border (Terengganu), streaming toward -y
    fp = xf(P([(1.15, 0.75, 0)], []), (x, y, 0), (0, 0, rz)).v[0]
    pg = ground(fp[0], fp[1])
    A.add("battle", "MatWood_boat", paint(K.tube([(fp[0], fp[1], pg - 0.2), (fp[0], fp[1], pg + 3.6)], [0.04, 0.025], seg=6), (0.68, 0.60, 0.36), ao=0.0))
    fl = pennant(fp[0], fp[1], pg + 3.55, 1.2, 0.7, (BOAT["white"], BOAT["black"], BOAT["black"], BOAT["black"], BOAT["white"]), seed=4, droop=0.08)
    A.add("battle", "MatCloth_net", fl)
    A.contact(x, y, 1.6, 0.3)


def clothesline(A, a, b, seed):
    """sarongs pegged on a rope between two casuarinas, billowing downwind (-y)."""
    rng = random.Random(seed)
    pts = K.arc(a, b, -0.25, n=10)
    A.add("battle", "MatCloth_net", paint(K.tube(pts, 0.012, seg=3, cap=False), (0.80, 0.76, 0.62), ao=0.0))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(L / 1.15))
    for k in range(n):
        t = (k + 0.5) / n
        i = int(t * 10)
        p = np.array(pts[i]) + (np.array(pts[min(10, i + 1)]) - np.array(pts[i])) * (t * 10 - i)
        pnl = S.batik_panel(0.85, 1.1, (k + seed) % 5, seed * 10 + k, sway=0.0, nxs=6, nzs=10)
        # billow: push the lower cloth downwind (-y) as it hangs
        pnl.v[:, 1] -= 0.55 * (-pnl.v[:, 2] / 1.1) ** 1.3 + 0.05 * np.sin(pnl.v[:, 0] * 6)
        pnl.v[:, 2] *= 0.85
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        A.add("battle", "MatCloth_net", xf(pnl, tuple(p), (0, 0, ang)))


def beached_perahu(A):
    x, y = BEACHED
    perahu_besar(A, x, y, 0.08, L=5.6, W=1.4, H=0.72, rollers=False, bangau=False, flag=False)
    gz = ground(x, y)
    anchor = [K.tube([(x - 3.6, y - 0.4, ground(x - 3.6, y - 0.4) + 0.02), (x - 3.0, y - 0.7, ground(x - 3.0, y - 0.7) + 0.05)], 0.03, seg=5),
              K.tube(K.arc((x - 3.75, y - 0.25, ground(x - 3.7, y) + 0.02), (x - 3.45, y - 0.65, ground(x - 3.4, y - 0.6) + 0.02), 0.06, n=5), 0.025, seg=4)]
    A.add("battle", "MatMetal_zinc", [paint(q, (0.25, 0.22, 0.20), ao=0.0) for q in anchor])
    A.add("battle", "MatCloth_net", paint(K.tube(K.arc((x - 2.7, y, gz + 0.5), (x - 3.0, y - 0.7, ground(x - 3.0, y - 0.7) + 0.06), 0.02, n=6), 0.02, seg=4), (0.85, 0.80, 0.62), ao=0.0))


def litter(A):
    """shells, driftwood, coconut husks; denser along the wrack line."""
    rng = random.Random(41)
    n = 0
    while n < 70:
        x = rng.uniform(-11, 11)
        if n % 2:
            y = shore_y(x) - 2.0 + rng.uniform(-0.25, 0.25)
        else:
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(5.8, 8.0)
            x, y = r * math.cos(a), r * math.sin(a)
            if y > shore_y(x) - 1.2:
                continue
        n += 1
        gz = ground(x, y)
        k = n % 5
        if k == 0:  # driftwood
            L = rng.uniform(0.6, 1.4)
            a = rng.uniform(0, 3.14)
            A.add("battle", "MatWood_boat", paint(K.tube([(x - L / 2 * math.cos(a), y - L / 2 * math.sin(a), gz + 0.03), (x + L / 2 * math.cos(a), y + L / 2 * math.sin(a), gz + 0.04)],
                                                         [0.05, 0.035], seg=5), DRIFT, ao=0.2, ao_h=0.05, ground=gz, namp=0.2, ns=6))
        elif k == 1:  # coconut husk
            A.add("battle", "MatWood_boat", paint(xf(K.rock(0.1, seed=600 + n, sub=2, squash=(1.2, 1, 0.8)), (x, y, gz - 0.02)), (0.48, 0.34, 0.20), ao=0.3, ao_h=0.1, ground=gz, top=0.2))
        else:  # shells
            A.add("battle", "MatMetal_zinc", paint(xf(K.rock(rng.uniform(0.025, 0.045), seed=900 + n, sub=1, squash=(1, 0.8, 0.4)), (x, y, gz - 0.005)),
                                                   (0.96, 0.90, 0.82) if k == 2 else (0.85, 0.62, 0.52), ao=0.0, top=0.3))


def vines(A):
    """tapak kuda (beach morning glory) runners on the back beach: low leaf rosettes + lilac flowers."""
    rng = random.Random(7)
    lv, fl = [], []
    for (cx, cy, n) in ((-3.8, -6.6, 9), (3.4, -6.3, 8), (-6.8, -5.0, 7), (6.6, -5.4, 7), (0.2, -7.4, 8)):
        x, y = cx, cy
        a = rng.uniform(0, 6.28)
        for k in range(n):
            a += rng.uniform(-0.7, 0.7)
            x, y = x + 0.35 * math.cos(a), y + 0.35 * math.sin(a)
            gz = ground(x, y)
            for j in range(2):
                b = a + (j - 0.5) * 2.2
                tip = (x + 0.2 * math.cos(b), y + 0.2 * math.sin(b), gz + 0.06)
                lv.append(K.strip_mesh([(x, y, gz + 0.02), ((x + tip[0]) / 2, (y + tip[1]) / 2, gz + 0.08), tip], [0.02, 0.09, 0.03], fold=-0.2, seed=k * 5 + j))
            if k % 3 == 1:
                fl.append(xf(K.lathe([(0, 0), (0.03, 0.03), (0.07, 0.07), (0.0, 0.05)], seg=6), (x, y, gz + 0.04)))
    A.add("battle", "MatLeaf_rhu", [paint(q, (0.28, 0.48, 0.20), var=0.1, ao=0.0, top=0.3) for q in lv])
    A.add("battle", "MatLeaf_rhu", [paint(q, (0.82, 0.48, 0.80), ao=0.0, top=0.3) for q in fl])


# ---------------------------------------------------------------- sea
def sea(A):
    """shore-following water grid: swash foam (low alpha) over the wet sand, turquoise shallows, two breaker
    lines, teal to deep blue offshore, then out to the horizon. Rows are offsets from the waterline."""
    xs = [-3000.0, -400.0, -150.0] + [float(x) for x in np.arange(-70.0, 70.01, 1.5)] + [150.0, 400.0, 3000.0]
    rows = [(-0.9, SAND_WET, 1.0), (-0.45, (0.80, 0.84, 0.80), 0.12), (-0.05, SHALLOW, 0.25), (0.5, SHALLOW, 0.75), (1.1, SHALLOW, 1.0), (2.6, SHALLOW, 1.0),
            (3.4, (0.26, 0.60, 0.62), 0.5), (3.9, (0.26, 0.58, 0.62), 0.95), (6.5, TEAL, 1.0), (7.6, TEAL, 0.55), (8.3, TEAL, 1.0),
            (14.0, TEAL, 1.0), (40.0, DEEP, 1.0), (160.0, DEEP, 1.0), (None, (0.40, 0.55, 0.62), 1.0)]
    for k, (r0, r1) in enumerate(zip(rows[:-1], rows[1:])):
        set_ = "battle" if k < 10 else "far"
        v, c, f = [], [], []
        for x in xs:
            sy = shore_y(max(-60.0, min(60.0, x)))
            for (off, col, al) in (r0, r1):
                v.append((x, 3000.0 if off is None else sy + off, WZ))
                c.append(list(col) + [al])
        for i in range(len(xs) - 1):
            a = 2 * i
            f.append((a, a + 2, a + 3, a + 1))
        A.add(set_, "MatWater_sea", P(v, f, c))


# ---------------------------------------------------------------- far set
def stilt_house(A, x, y, rz, seed):
    rng = random.Random(seed)
    W, D, FH = rng.uniform(4.0, 5.0), rng.uniform(3.0, 3.6), 1.4
    gz = ground(x, y)
    wood = [xf(K.box(0.16, 0.16, FH + 0.3, bev=0.0), (sx * W, sy * D, -0.3)) for sx in (-0.45, 0.45) for sy in (-0.45, 0.45)]
    wood.append(xf(K.box(W, D, 2.0, bev=0.0), (0, 0, FH)))
    roof = xf(K.thatch_roof(W, D, 1.4, courses=1, over=0.4, seed=seed, tooth=0.0, cw=2.5), (0, 0, FH + 2.0))
    wall = [(0.62, 0.70, 0.74), (0.86, 0.80, 0.62), (0.56, 0.72, 0.58), (0.90, 0.88, 0.82)][seed % 4]
    A.add("far", "MatWood_boat", [paint(xf(q, (x, y, gz), (0, 0, rz)), wall if i == 4 else TIMBER, ao=0.3, ao_h=2, ground=gz) for i, q in enumerate(wood)])
    A.add("far", "MatWood_boat", paint(xf(roof, (x, y, gz), (0, 0, rz)), (0.62, 0.30, 0.22) if seed % 2 else (0.58, 0.58, 0.60), top=0.3))


def headland(A):
    """casuarina-lined headland curving round the bay, with a fishing village and boats drawn up."""
    rng = random.Random(19)
    for k in range(11):
        xx = 13.5 + 3.4 * k + rng.uniform(-0.8, 0.8)
        yy = shore_y(xx) - rng.uniform(4.0, 9.0)
        if not in_vista(xx, yy, pad=4):
            continue
        rhu(A, xx, yy, rng.uniform(10, 14), seed=500 + k, set_="far", lean=0.16, lumps=12)
    for k, xx in enumerate((15.5, 19.0, 22.5)):
        stilt_house(A, xx, shore_y(xx) - 12.0 - 1.5 * k, rng.uniform(-0.3, 0.3), k)
    for k, xx in enumerate((14.2, 17.0)):
        perahu_besar(A, xx, shore_y(xx) - 2.6, 1.2 + 0.2 * k, L=6.0, W=1.5, H=0.8, set_="far", rollers=False, bangau=False, flag=False, n=9)


def boats_out(A):
    """boats coming home across the bay."""
    for k, (x, y, rz, L) in enumerate(((-4.0, 34.0, 0.25, 6.5), (9.0, 52.0, -0.3, 7.0), (-12.0, 82.0, 0.5, 7.5))):
        perahu_besar(A, x, y, rz, L=L, W=1.6, H=0.85, set_="far", rollers=False, bangau=k % 2 == 0, n=9)


def islands(A):
    for (yaw, dist, R, H, seed) in ((-4.0, 360.0, 70.0, 26.0, 1), (4.0, 330.0, 26.0, 12.0, 2)):
        a = math.radians(yaw)
        x, y = VCAM[0] + dist * math.sin(a), VCAM[1] + dist * math.cos(a)
        d = dome(R, H, seed=seed, seg=48, rings=10, base=-3.0, lump=2.5, lump_s=0.06, squash=(1.0, 0.6), power=1.2)
        d = xf(d, (x, y, WZ))
        zt = np.clip((d.v[:, 2] - WZ) / H, 0, 1)
        beach = smooth01(0.08, 0.02, zt)
        c = mix(np.tile((0.20, 0.34, 0.20), (len(d.v), 1)) * (0.9 + 0.2 * zt[:, None]), np.tile((0.92, 0.88, 0.76), (len(d.v), 1)), beach[:, None])
        d.c = np.column_stack([c, np.ones(len(d.v))])
        A.add("far", "MatLeaf_rhu", d)
        for k in range(5):  # granite boulders at the waterline
            aa = math.radians(150 + 25 * k + seed * 10)
            bx, by = x + R * 0.95 * math.cos(aa), y + R * 0.95 * 0.6 * math.sin(aa)
            A.add("far", "MatRock_granite", paint(xf(K.rock(R * 0.08, seed=seed * 10 + k, sub=2, squash=(1.3, 1, 0.7)), (bx, by, WZ - 0.5)), (0.62, 0.58, 0.54), ao=0.0, top=0.3))


def backdrop(A):
    A.add("far", "MatLeaf_rhu", ridge_layer(420, 14, 60, WZ - 12.0, 6.0, 18.0, 81, (0.40, 0.52, 0.58), (0.34, 0.46, 0.52), n=60, freq=2.6, crowns=0.8))
    for k, (yaw, dist, el, w, h) in enumerate(((-40, 260, 9.0, 110, 18), (-16, 300, 12.0, 150, 22), (8, 270, 9.5, 100, 18), (28, 240, 13.0, 90, 16),
                                                (-28, 220, 15.5, 70, 11), (18, 330, 5.0, 150, 14), (-6, 340, 4.2, 140, 12), (42, 200, 7.0, 60, 10))):
        a = math.radians(yaw)
        x, y = VCAM[0] + dist * math.sin(a), VCAM[1] + dist * math.cos(a)
        z = 3.2 + dist * math.tan(math.radians(el))
        cl = cloud_flat(w, h * 0.8, seed=260 + k, lit=(1.0, 0.98, 0.92), shade=(0.66, 0.74, 0.86), n=30, rim=h * 0.08)
        cl.v[:, 0] += 0.12 * cl.v[:, 2] * (1 if k % 2 else -1)  # sheared by the wind
        A.add("far", "MatPlaster_cloud", face_vista(cl, x, y, z))


# ================================================================ build
def build(A):
    DRIFTS[:] = [(PERAHU[0], PERAHU[1] - 2.6, 1.1), (PERAHU[0] - 0.4, PERAHU[1] + 1.5, 0.8), (BEACHED[0], BEACHED[1], 0.8), (STALL[0], STALL[1], 1.0),
                 (-4.9, -2.6, 0.6), (4.2, 3.6, 0.6), (-2.6, 5.15, 0.6)] + [(x, y, 0.5) for (x, y, h) in RHUS]
    for name in ("MatSand_beach", "MatWater_sea", "MatWood_boat", "MatLeaf_rhu", "MatMetal_zinc", "MatCloth_net",
                 "MatThatch_atap", "MatRock_granite", "MatPlaster_cloud"):
        A.mat(name)
    A.mat("MatGlow_lamp", emit=(1.0, 0.78, 0.45), estr=3.0)

    # ---- left flank: perahu besar on rollers, oars, nets drying on its gunwale
    perahu_besar(A, PERAHU[0], PERAHU[1], math.pi / 2 + 0.06)
    for k, (ox, oy) in enumerate(((-6.6, -2.8), (-6.4, -2.2))):
        A.add("battle", "MatWood_boat", paint(K.tube([(ox, oy, ground(ox, oy) - 0.1), (ox + 0.15, oy + 0.25, ground(ox, oy) + 1.05)], 0.03, seg=5), TIMBER, ao=0.2, ao_h=0.3, ground=ground(ox, oy)))
        A.add("battle", "MatWood_boat", paint(xf(K.box(0.14, 0.03, 0.42, bev=0.01), (ox + 0.16, oy + 0.27, ground(ox, oy) + 0.95)), (0.86, 0.66, 0.24), ao=0.0))
    # ---- right flank: keropok stall, casuarinas, sarongs on the line
    keropok_stall(A, STALL[0], STALL[1], -math.pi / 2 - 0.1)
    for k, (x, y, h) in enumerate(RHUS):
        rhu(A, x, y, h, seed=10 + k)
    clothesline(A, (10.6, 4.8, ground(10.6, 4.8) + 2.1), (12.6, 1.0, ground(12.6, 1.0) + 2.2), seed=2)
    # ---- apron: drying racks, net heap + floats, raga baskets
    fish_rack(A, -4.9, -2.6, 0.55, seed=1)
    fish_rack(A, 4.2, 3.6, -0.75, seed=2)
    net_heap(A, -2.6, 5.15, seed=5)
    raga(A, 5.25, -1.6, seed=3)
    raga(A, 5.0, -2.2, seed=4)
    # ---- far band: tide line, beached perahu, litter; near strip vines
    beached_perahu(A)
    litter(A)
    vines(A)

    # ---- terrain + sea
    A.terrain(ground, gcolor, kind=lambda x, y, z: "MatSand_beach", rin=4.5, rout=200.0, split=23.0, cull=gcull, seed=1)
    sea(A)

    # ---- scatter: dune grass on the back beach and between casuarinas (sways hard in the gusts)
    rng = random.Random(3)
    for k in range(260):
        x = rng.uniform(-14, 15)
        y = rng.uniform(-8.5, 6.0)
        r = math.hypot(x, y)
        back = y < -4.6 or (x > 6.8 and y < shore_y(x) - 2.8) or (x < -6.4 and y < 4.0 and not (-10.6 < x < -6.6 and -3.5 < y < 4.6))
        if r < 6.2 or not back or not visible(x, y):
            continue
        A.scatter_patch("Grass", 34 if y < -5.5 else 26, x, y, rng.uniform(0.4, 1.1), ground, (0.62, 0.62, 0.34), seed=k)
    for k in range(40):  # tall seaside grass at the flanks: the most visible gust cue
        x = rng.choice((rng.uniform(-13.5, -11.0), rng.uniform(7.0, 14.0)))
        y = rng.uniform(-4.5, 5.0)
        if not visible(x, y) or (x > 0 and math.hypot(x - STALL[0], y - STALL[1]) < 1.8):
            continue
        A.scatter_patch("Reed", 7, x, y, rng.uniform(0.4, 0.8), ground, (0.66, 0.64, 0.38), seed=500 + k)
    for k in range(30):
        x = rng.uniform(12, 24)
        y = shore_y(x) - rng.uniform(3.5, 8.0)
        if not visible(x, y):
            continue
        A.scatter_patch("Reed", 8, x, y, rng.uniform(0.6, 1.2), ground, (0.60, 0.60, 0.34), seed=200 + k)

    # ---- far set
    headland(A)
    boats_out(A)
    islands(A)
    backdrop(A)


if __name__ == "__main__":
    K.main("terengganu", build, MOOD)
    write_mood("terengganu", MOOD, {"hazard": HAZARD})
