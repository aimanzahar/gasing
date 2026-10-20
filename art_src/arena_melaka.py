"""Melaka arena -- Dutch Square on the Melaka River at blue hour (design_art.md section c).
Ground: red laterite plaza, concentric brick courses around the dish, river-walk pavers, embankment.
Apron: beaded slippers + kamcheng jars on a low bench; jar stack and baskets (all low).
Left flank: Stadthuys red facade (louvred windows, portico steps) with flowered trishaws parked in front.
Far band: river walk railing + lamps, the Melaka River with a sampan tour boat.
Right flank: Peranakan shophouses (glazed tile panels, pintu pagar, lanterns), flowered trishaw.
Far set (vista): far bank -- Christ Church, clock tower, Dutch windmill, riverside houses; St Paul's Hill with the ruin
and lighthouse; the harbour with ships of different origins (galleon, junk, pinisi); blue-hour clouds.
Shared helpers live in arena_penang.py (same owner).
  blender -b --factory-startup -P art_src/arena_melaka.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)
import arena_penang as H
importlib.reload(H)
import numpy as np
from arenakit import P, xf, join, paint, tint, nz, smooth01
from arena_penang import Kit, place_kit, bx, stripes, visible, in_vista, dot, lantern, lantern_string, hill, paint_hill, cloud, glow_grad

MOOD = {"sky_top": (0.06, 0.12, 0.38), "sky_horizon": (0.72, 0.56, 0.64), "fog": (0.40, 0.44, 0.62),
        "fog_density": 0.006, "sun_color": (0.74, 0.76, 1.0), "sun_energy": 0.55,
        "lantern": (1.0, 0.66, 0.40), "lantern_energy": 1.7, "exposure": 0.95, "ambient": 0.6,
        "b_sun": 1.4, "b_world": 0.8, "b_fill": 0.3, "b_lantern": 12.0}

NAMES = {"Plaster": "MatPlaster_wall", "Wood": "MatWood_timber", "Tile": "MatTile_brick", "Glow": "MatGlow_warm",
         "Lantern": "MatGlow_lantern", "Metal": "MatMetal_iron", "Cloth": "MatCloth_bunting", "Fire": "MatGlow_warm",
         "Leaf": "MatLeaf_canopy", "Rock": "MatRock_stone"}
NAMES_FAR = dict(NAMES, Wood="MatPlaster_wall", Metal="MatPlaster_wall", Cloth="MatPlaster_wall", Rock="MatPlaster_wall",
                 Lantern="MatGlow_warm")

LATERITE = (0.48, 0.24, 0.17)
LATERITE_DK = (0.36, 0.17, 0.13)
BRICK = [(0.58, 0.26, 0.18), (0.50, 0.22, 0.16), (0.64, 0.32, 0.22), (0.45, 0.20, 0.15)]
PAVER = (0.52, 0.48, 0.44)
STADT_RED = (0.55, 0.15, 0.12)
RIVER = (0.16, 0.22, 0.26)
PASTEL = [(0.58, 0.74, 0.66), (0.62, 0.70, 0.82), (0.86, 0.72, 0.56), (0.80, 0.62, 0.66), (0.70, 0.78, 0.60)]

RIVER_Y0, RIVER_Y1 = 7.45, 12.6     # embankment faces (near / far bank)
WALK_Y = 5.7                        # river walk paving starts
RIVER_Z = -1.05
STADT_X = -9.0                      # Stadthuys plinth front (faces +x)
PERA_X = 8.7                        # Peranakan row column line (faces -x)


def bars(w, h, y=-0.03, t=0.04):
    """0.04 m frame, centre mullion and transom in front of a lit pane (local: facing -y, base-centre at origin)."""
    return join(bx(w + t, t, t, (0, y, -t / 2), bev=0.0), bx(w + t, t, t, (0, y, h - t / 2), bev=0.0), bx(t, t, h, (-w / 2, y, 0), bev=0.0),
                bx(t, t, h, (w / 2, y, 0), bev=0.0), bx(t, t, h, (0, y, 0), bev=0.0), bx(w, t, t, (0, y, 0.62 * h), bev=0.0))


def quad_y(x, y, z, w, h):
    """flat quad facing -y (lit window / clock face); base-centre at (x, y, z)."""
    return P([(x - w / 2, y, z), (x + w / 2, y, z), (x + w / 2, y, z + h), (x - w / 2, y, z + h)], [(0, 1, 2, 3)])


def far_land(x, y):
    """far banks: the river mouth widens like a funnel into the harbour (centre of the vista);
    right bank = Christ Church + clock tower, left bank = windmill."""
    if y <= RIVER_Y1 or y > 95:
        return False
    d = y - RIVER_Y1
    return x > 3.0 + 0.35 * d or x < -4.0 - 0.45 * d


def ground(x, y):
    if RIVER_Y0 < y < RIVER_Y1 or (y >= RIVER_Y1 and not far_land(x, y)):
        return RIVER_Z - 0.7
    z = 0.015 * nz(x, y, 0, 0.5, 3)
    if y >= RIVER_Y1:
        z += 0.25 + 0.6 * smooth01(40, 75, y) * smooth01(-10, -40, x)
    return z


def gcolor(x, y, z):
    if z < RIVER_Z:
        return (0.10, 0.10, 0.10)
    n1, n2, n3 = nz(x, y, 0, 0.4, 11), nz(x, y, 0, 1.8, 12), nz(x, y, 0, 5.0, 13)
    if WALK_Y < y < RIVER_Y0:  # river walk pavers
        c = np.array(PAVER) * (1 + 0.1 * n1 + 0.06 * n3)
        c = c * (0.86 + 0.14 * ((math.floor(x / 0.6) + math.floor(y / 0.6)) % 2))
        return tuple(np.clip(c, 0, 1))
    c = np.array(LATERITE) * (1 + 0.14 * n1 + 0.08 * n2 + 0.06 * n3)
    c = c + (np.array(LATERITE_DK) - c) * 0.6 * smooth01(0.1, 0.5, nz(x, y, 0, 0.25, 14))
    # worn brick-band pattern: broad diagonal herringbone hint
    c = c * (0.92 + 0.08 * ((math.floor((x + y) / 0.9) + math.floor((x - y) / 0.9)) % 2))
    r = math.hypot(x, y)
    c = c * (1 - 0.25 * smooth01(WALK_Y - 0.4, WALK_Y, y) * (1 - smooth01(WALK_Y, WALK_Y + 0.1, y)))  # walk kerb shadow
    c = c * (1 - 0.2 * (1 - smooth01(0.0, 1.2, abs(x - STADT_X - 0.6))))                            # damp foot of the Stadthuys
    return tuple(np.clip(c, 0, 1))


def gcull(cx, cy, zmax):
    if zmax < RIVER_Z:
        return True
    if math.hypot(cx, cy) < 7.15:   # under the brick courses
        return True
    if cx < STADT_X - 0.1 and cy < RIVER_Y0:
        return True
    if cx > PERA_X + 0.3 and cy < 5.6 and cy > -14:
        return True
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def brick_rings(A, r0=4.5, r1=7.38, course=0.22, length=0.42):
    """concentric brick courses around the dish (crisp per-brick colour), half-bond offset per course."""
    rng = random.Random(5)
    v, f, c = [], [], []
    r = r0
    k = 0
    while r < r1 - 1e-6:
        ra, rb = r + 0.008, min(r1, r + course) - 0.008
        n = max(24, int(round(2 * math.pi * (r + course / 2) / length)))
        off = (0.5 if k % 2 else 0.0) * 2 * math.pi / n
        for i in range(n):
            a0 = off + 2 * math.pi * i / n + 0.004
            a1 = off + 2 * math.pi * (i + 1) / n - 0.004
            col = np.array(BRICK[rng.randrange(len(BRICK))]) * rng.uniform(0.9, 1.08)
            if k in (0, 4, 9):
                col = col * 0.78   # soldier courses read as bands
            if k >= 12:
                col = np.array((0.50, 0.47, 0.44)) * rng.uniform(0.9, 1.06)   # granite border course
            b = len(v)
            for (rr, aa) in ((ra, a0), (rb, a0), (rb, a1), (ra, a1)):
                x, y = rr * math.cos(aa), rr * math.sin(aa)
                v.append((x, y, ground(x, y) + 0.018 + 0.006 * rng.random()))
            f.append((b, b + 1, b + 2, b + 3))
            c += [list(col) + [1.0]] * 4
        r += course
        k += 1
    p = P(v, f)
    p.c = np.clip(np.array(c), 0, 1)
    A.add("battle", "MatTile_brick", p)


def facade(W, Hgt, wall, win_rgb, bays, lit, plinth=0.55, roof=(0.42, 0.20, 0.15), trim=(0.86, 0.82, 0.76), door_bay=None, lod=0, seed=0):
    """long colonial facade (Stadthuys / church sides). Local: front at y=0 facing -y, x across [-W/2, W/2]."""
    rng = random.Random(seed)
    k = Kit()
    bw = W / bays
    pl, tr = [], []
    k.put("Rock", paint(bx(W + 0.2, 0.5, plinth, (0, 0.1, 0), bev=0.02 if lod == 0 else 0.0), (0.56, 0.50, 0.46), ao=0.3, ao_h=0.5, top=0.2))
    pl.append(bx(W, 0.4, Hgt - plinth, (0, 0.25, plinth), bev=0.0))
    for i in range(bays):
        x = -W / 2 + bw * (i + 0.5)
        for fl, (z0, wh) in enumerate(((plinth + 0.7, 2.0), (Hgt * 0.56 + 0.4, 1.8))):
            if door_bay is not None and i == door_bay and fl == 0:
                continue
            l = lit[(i + fl) % len(lit)]
            if lod == 0:
                tr.append(bx(1.25, 0.12, 0.12, (x, -0.02, z0 - 0.12), bev=0.01))
                tr.append(bx(1.3, 0.14, 0.18, (x, -0.03, z0 + wh), bev=0.01))
            if l:
                k.put("Glow", glow_grad(paint(bx(0.95, 0.05, wh, (x, -0.02, z0), bev=0.0), (1.0, 0.82, 0.55), ao=0.0, top=0.0)))
                k.put("Wood", tint(paint(join(bx(0.08, 0.06, wh, (x, -0.06, z0), bev=0.0), bx(0.95, 0.06, 0.06, (x, -0.06, z0 + wh * 0.6), bev=0.0)),
                                         win_rgb, ao=0.0), lambda v, c: c))
            else:
                k.put("Wood", tint(paint(bx(0.98, 0.06, wh, (x, -0.04, z0), bev=0.0), win_rgb, ao=0.0, top=0.2), stripes(2, 12, 0.72, 1.0)))
    tr.append(bx(W + 0.3, 0.5, 0.3, (0, 0.05, Hgt), bev=0.02 if lod == 0 else 0.0))
    tr.append(bx(W + 0.1, 0.3, 0.16, (0, 0.05, Hgt * 0.56), bev=0.0))
    rf = xf(H.corrugated(W + 0.6, 4.2, 0.32, 0.05, ny=1, per=2), (0, 2.2, 0))
    rf.v[:, 2] += Hgt + 0.3 + (rf.v[:, 1] - 0.1) * 0.5
    k.put("Tile", tint(paint(K.dbl(rf), roof, var=0.05, ao=0.0, top=0.3, namp=0.15, ns=1.0), stripes(1, 2.0, 0.85, 1.0)))
    k.put("Plaster", paint(join(pl), wall, var=0.03, ao=0.35, ao_h=1.5, top=0.1, namp=0.08, ns=0.8),
          paint(join(tr), trim, ao=0.0, top=0.15))
    return k


def stadthuys(A):
    """long red Stadthuys facade facing the dish (left flank), with a portico + steps at the central bay."""
    W, Hgt = 26.0, 7.4
    kit = facade(W, Hgt, STADT_RED, (0.26, 0.10, 0.08), bays=7, lit=(False, True, False, False, True), door_bay=3, seed=1)
    # portico: projecting gable bay with an arched opening, steps
    pk = Kit()
    pw = 4.2
    pk.put("Plaster", paint(join(bx(0.7, 1.6, 4.2, (-pw / 2 + 0.35, -0.8, 0.55), bev=0.02), bx(0.7, 1.6, 4.2, (pw / 2 - 0.35, -0.8, 0.55), bev=0.02),
                                 bx(pw, 1.6, 1.0, (0, -0.8, 4.75), bev=0.02)), STADT_RED, ao=0.35, ao_h=1.5, top=0.1))
    arch = [(1.4 * math.cos(a), -1.62, 3.3 + 1.4 * math.sin(a)) for a in np.linspace(0, math.pi, 9)]
    pk.put("Plaster", paint(K.tube(arch, 0.12, seg=4, cap=True), (0.86, 0.82, 0.76), ao=0.0, top=0.2))
    pk.put("Plaster", paint(K.dbl(P([(-1.4, -0.05, 3.3)] + [(1.4 * math.cos(a), -0.05, 3.3 + 1.4 * math.sin(a)) for a in np.linspace(0, math.pi, 9)] +
                                  [(-1.4, -0.05, 5.75), (1.4, -0.05, 5.75)], [(0, 1, 2), (0, 2, 3)] + [(9, i, i + 1) for i in range(1, 9)])), STADT_RED, ao=0.0))
    gab = K.dbl(P([(-pw / 2 - 0.15, -1.62, 5.75), (pw / 2 + 0.15, -1.62, 5.75), (0, -1.62, 7.1)], [(0, 1, 2)]))
    pk.put("Plaster", paint(gab, STADT_RED, ao=0.0), paint(xf(K.box(pw + 0.5, 0.2, 0.18), (0, -1.6, 5.7)), (0.86, 0.82, 0.76), ao=0.0))
    pk.put("Wood", tint(paint(bx(2.2, 0.08, 2.9, (0, 0.18, 0.55), bev=0.0), (0.24, 0.12, 0.08), ao=0.3, ao_h=1.0), stripes(0, 4, 0.8, 1.0)))
    for s in range(4):
        pk.put("Rock", paint(bx(3.2 - 0.2 * s, 0.32, 0.14, (0, -1.8 - 0.3 * (3 - s), 0.14 * s), bev=0.015), (0.44, 0.30, 0.25), ao=0.2, ao_h=0.5, top=0.2))
    yc = 0.6
    place_kit(A, "battle", kit, (STADT_X, yc, 0.0), math.pi / 2, NAMES)
    place_kit(A, "battle", pk, (STADT_X, yc, 0.0), math.pi / 2, NAMES)
    # wall lamps (glow) either side of the portico
    for dy in (-3.0, 3.0):
        A.add("battle", "MatGlow_warm", paint(bx(0.22, 0.22, 0.34, (STADT_X + 0.2, yc + dy, 2.9), bev=0.0), (1.0, 0.86, 0.6), ao=0.0, top=0.0))
        A.add("battle", "MatMetal_iron", paint(bx(0.3, 0.3, 0.06, (STADT_X + 0.2, yc + dy, 3.24), bev=0.0), (0.1, 0.1, 0.1), ao=0.0))
    A.contact(STADT_X + 1.0, yc, 3.0, 0.2)


def flower_trishaw(seed, palette):
    """Melaka flowered trishaw: beca with a canopy smothered in plastic flowers + fairy lights. Kit keys like trishaw()."""
    rng = random.Random(seed)
    k = H.trishaw(seat_rgb=palette[0], frame_rgb=(0.85, 0.82, 0.78))
    fl, lights = [], []
    for i in range(26):  # flowers on the hood arch and seat rim
        a = rng.uniform(0, math.pi)
        p = (0.5 * math.cos(a) * rng.uniform(0.8, 1.05), 0.56 + 0.22 * math.sin(a) + rng.uniform(-0.1, 0.1), 0.78 + 0.36 * math.sin(a) + rng.uniform(0, 0.08))
        if i > 18:
            p = (rng.uniform(-0.5, 0.5), rng.uniform(-0.2, 0.4), 0.8)
        b = K.rock(rng.uniform(0.06, 0.09), seed=seed * 50 + i, sub=0, amp=0.1)
        fl.append(paint(xf(b, p), palette[1 + i % (len(palette) - 1)], var=0.1, ao=0.0, top=0.3))
    for i in range(9):
        a = math.pi * i / 8
        lights.append(H.dot(0.52 * math.cos(a), 0.5 + 0.22 * math.sin(a), 0.8 + 0.38 * math.sin(a), 0.05))
    k.put("Cloth", fl)
    k.put("Glow", K.dbl(paint(join(lights), (1.0, 0.9, 0.7), ao=0.0, top=0.0)))
    # tall flower spray + umbrella-ish parasol over the passenger seat
    k.put("Cloth", paint(xf(K.lathe([(0.0, 0.0), (0.45, -0.18), (0.42, -0.22)], seg=10, cap0=False, cap1=False), (0, 0.15, 1.7)), palette[2], ao=0.0, top=0.3))
    k.put("Metal", paint(K.tube([(0, 0.15, 0.7), (0, 0.15, 1.7)], 0.015, seg=3, cap=False), (0.8, 0.8, 0.78), ao=0.0))
    return k


def kamcheng(r=0.13, h=0.2, body=(0.86, 0.50, 0.62), band=(0.28, 0.56, 0.40)):
    """lidded Peranakan porcelain jar with colour bands. base z=0."""
    j = K.lathe([(0.0, 0.0), (r * 0.6, 0.0), (r, h * 0.35), (r * 0.95, h * 0.75), (r * 0.7, h), (r * 0.72, h * 1.08), (r * 0.25, h * 1.25),
                 (r * 0.18, h * 1.38), (0.0, h * 1.42)], seg=10)
    paint(j, body, ao=0.25, ao_h=0.1, top=0.3)
    zz = j.v[:, 2]
    j.c[:, :3] = np.where(((np.abs(zz - h * 0.5) < h * 0.12) | (zz > h * 1.06))[:, None], np.asarray(band) * 1.0, j.c[:, :3])
    return j


def slipper_bench(seed=0):
    """low wooden bench with beaded slippers (kasut manek), a beading tray and two kamcheng jars. Kit keys."""
    rng = random.Random(seed)
    k = Kit()
    k.put("Wood", paint(join(bx(1.3, 0.42, 0.06, (0, 0, 0.32), bev=0.012),
                             *[bx(0.06, 0.36, 0.32, (sx, 0, 0), bev=0.0) for sx in (-0.55, 0.55)]), (0.36, 0.22, 0.13), ao=0.3, ao_h=0.4, top=0.2))
    cols = [(0.86, 0.30, 0.42), (0.30, 0.62, 0.52), (0.92, 0.76, 0.30), (0.40, 0.46, 0.80)]
    for i in range(3):  # pairs of beaded slippers
        for s in (-1, 1):
            sl = bx(0.1, 0.24, 0.045, (-0.4 + 0.3 * i + s * 0.06, rng.uniform(-0.05, 0.05), 0.38), bev=0.02)
            k.put("Cloth", paint(sl, cols[(i + (s > 0)) % 4], ao=0.0, top=0.3))
    k.put("Wood", paint(bx(0.28, 0.2, 0.03, (0.45, 0.05, 0.38), bev=0.0), (0.5, 0.36, 0.2), ao=0.0))
    k.put("Cloth", paint(join([xf(K.rock(0.012, seed=i, sub=0), (0.36 + 0.03 * (i % 6), 0.0 + 0.03 * (i // 6), 0.41)) for i in range(12)]),
                         (0.9, 0.85, 0.7), ao=0.0))
    for i, (x, y, b) in enumerate(((-0.2, -0.45, (0.86, 0.50, 0.62)), (0.25, -0.5, (0.50, 0.72, 0.58)))):
        k.put("Tile", xf(kamcheng(0.12, 0.18, b), (x, y, 0)))
    return k


def river_boat(seed=0, canopy_rgb=(0.20, 0.40, 0.50)):
    """sampan tour boat: hull + flat canopy on posts + bench. Kit keys: Wood, Cloth, Metal, Glow."""
    k = Kit()
    hull = K.perahu(L=5.6, W=1.3, H=0.6, seed=seed)
    k.put("Wood", tint(paint(hull, (0.30, 0.38, 0.52), ao=0.0, top=0.15),
                       lambda v, c: np.where((v[:, 2] > 0.5)[:, None], c * np.array([1.6, 1.4, 1.1, 1]), c)))
    for sx in (-1.6, -0.2, 1.2):
        for sy in (-0.5, 0.5):
            k.put("Metal", paint(K.tube([(sx, sy, 0.5), (sx, sy, 1.75)], 0.025, seg=3, cap=False), (0.8, 0.8, 0.78), ao=0.0))
    k.put("Cloth", tint(paint(bx(3.4, 1.3, 0.06, (-0.2, 0, 1.75), bev=0.02), canopy_rgb, ao=0.0, top=0.25), stripes(0, 2.5, 0.8, 1.0)))
    k.put("Wood", paint(join(bx(3.0, 0.3, 0.06, (-0.2, -0.35, 0.62), bev=0.0), bx(3.0, 0.3, 0.06, (-0.2, 0.35, 0.62), bev=0.0)), (0.45, 0.3, 0.2), ao=0.0))
    for sx in (-1.6, 1.2):
        k.put("Glow", paint(bx(0.12, 0.12, 0.16, (sx, 0, 1.58), bev=0.0), (1.0, 0.85, 0.6), ao=0.0, top=0.0))
    return k


def peranakan_row(A):
    """right flank: two Peranakan shophouses facing the dish (glazed tile panels, pintu pagar, red lanterns)."""
    W = 4.6
    for i, (yc, wall, sh) in enumerate(((-4.0, PASTEL[0], (0.18, 0.36, 0.30)), (0.6, PASTEL[1], (0.20, 0.30, 0.48)), (5.2, PASTEL[2], (0.42, 0.20, 0.14)))):
        kit = H.shophouse(W=W, wall=wall, shutter=sh, lit=((True, False), (False, True), (True, True))[i], shop_open=(i != 1), seed=20 + i,
                          sign=(0.12, 0.10, 0.08), sign_text=(0.92, 0.76, 0.32), last_col=(i == 2))
        # glazed tile panels under the upper windows + on the piers (Peranakan)
        tk = []
        for x in (-W / 4, W / 4):
            tk.append(tint(paint(bx(1.1, 0.04, 0.42, (x, -0.04, 3.5 + 0.08), bev=0.0), (1, 1, 1), ao=0.0, top=0.0),
                           lambda v, c: c * np.where(((np.floor(v[:, 0] * 7) + np.floor(v[:, 2] * 7)) % 2 == 0)[:, None], np.array([0.30, 0.52, 0.62, 1]), np.array([0.86, 0.80, 0.60, 1]))))
        for sx in (-0.95, 0.95):  # tiles on the shopfront dado
            tk.append(tint(paint(bx(0.55 if abs(sx) > 0 else 0.5, 0.04, 0.9, (sx * 1.3, 1.78, 0.0), bev=0.0), (1, 1, 1), ao=0.0, top=0.0),
                           lambda v, c: c * np.where(((np.floor(v[:, 0] * 8) + np.floor(v[:, 2] * 8)) % 2 == 0)[:, None], np.array([0.62, 0.30, 0.34, 1]), np.array([0.40, 0.62, 0.50, 1]))))
        kit.put("Tile", tk)
        if i != 1:  # pintu pagar: carved half doors in the open doorway
            for s in (-1, 1):
                kit.put("Wood", tint(paint(bx(0.9, 0.05, 1.3, (s * 0.5, 1.72, 0.25), bev=0.01), (0.30, 0.14, 0.08), ao=0.0, top=0.2),
                                     lambda v, c: np.where((v[:, 2] > 1.25)[:, None], np.array([0.80, 0.62, 0.24, 1]), c)))
        place_kit(A, "battle", kit, (PERA_X + 0.15, yc, 0.0), -math.pi / 2, NAMES)
    # encaustic five-foot-way tiles
    A.add("battle", "MatTile_brick", H.tile_floor(PERA_X - 0.45, PERA_X + 2.0, -6.3, 7.5, 0.16, 0.3,
                                                  cols=((0.62, 0.58, 0.50), (0.36, 0.44, 0.42), (0.56, 0.32, 0.28)), seed=7,
                                                  cull=lambda x, y: not visible(x, y, 2.0)))
    kerb = K.extrude([(PERA_X - 0.45, -6.3), (PERA_X - 0.45, 7.5)], [(-0.06, -0.12), (-0.05, 0.12), (0.0, 0.16), (0.16, 0.16)], step=1.5)
    A.add("battle", "MatRock_stone", paint(kerb, (0.56, 0.52, 0.48), ao=0.0, top=0.2))
    for k, y in enumerate((-2.0, 2.9)):
        place_kit(A, "battle", H.potted_plant(k + 3, 0.8, leaf_rgb=(0.22, 0.40, 0.18)), (PERA_X + 0.1, y, 0.16), 0.0, NAMES)


def river(A):
    """river walk railing + lamps, embankment, river water, boats."""
    for y0, face in ((RIVER_Y0, 1), (RIVER_Y1, -1)):
        wall = K.extrude([(-60.0, y0), (60.0, y0)], [(-0.3 * face, 0.02), (0.0, 0.06), (0.08 * face, 0.0), (0.12 * face, RIVER_Z - 0.4)], step=2.0)
        A.add("battle" if y0 == RIVER_Y0 else "far", "MatRock_stone" if y0 == RIVER_Y0 else "MatPlaster_wall",
              tint(paint(wall, (0.46, 0.40, 0.36), ao=0.0, top=0.25, namp=0.15, ns=1.5),
                   lambda v, c: c * (0.82 + 0.18 * ((np.floor(v[:, 0] / 0.8) + np.floor(v[:, 2] * 3.3)) % 2))[:, None] *
                   (1 - 0.35 * smooth01(-0.3, RIVER_Z, v[:, 2]))[:, None]))
    rail_y = RIVER_Y0 - 0.25
    posts, rails = [], []
    for x in np.arange(-15.0, 16.0, 1.6):
        if visible(x, rail_y, 2.0):
            posts.append(K.tube([(x, rail_y, 0.0), (x, rail_y, 0.95)], 0.03, seg=4, cap=True))
    xs = [x for x in np.arange(-15.0, 16.0, 1.6) if visible(x, rail_y, 2.0)]
    for z in (0.5, 0.95):
        rails.append(K.tube([(xs[0], rail_y, z), (xs[-1], rail_y, z)], 0.02 if z < 0.9 else 0.03, seg=4, cap=False))
    A.add("battle", "MatMetal_iron", paint(join(posts, rails), (0.10, 0.10, 0.11), ao=0.0, top=0.3))
    for x in (-5.5, 4.5, 13.0):
        place_kit(A, "battle", H.heritage_lamp(3.3), (x, rail_y - 0.35, 0.0), 0.0, NAMES)
    # water: battle strip + far sheet (river widens into the harbour)
    v = [(-60, RIVER_Y0 + 0.05, RIVER_Z), (60, RIVER_Y0 + 0.05, RIVER_Z), (60, RIVER_Y1 - 0.05, RIVER_Z), (-60, RIVER_Y1 - 0.05, RIVER_Z)]
    p = P(v, [(0, 1, 2, 3)])
    p.c = np.array([list(RIVER) + [0.85], list(RIVER) + [0.85], list(RIVER) + [1.0], list(RIVER) + [1.0]])
    A.add("battle", "MatWater_river", p)
    v = [(-400, RIVER_Y1 - 0.05, RIVER_Z), (400, RIVER_Y1 - 0.05, RIVER_Z), (400, 420, RIVER_Z), (-400, 420, RIVER_Z)]
    p = P(v, [(0, 1, 2, 3)])
    p.c = np.tile([0.18, 0.24, 0.32, 1.0], (len(v), 1))
    A.add("far", "MatWater_river", p)
    place_kit(A, "battle", river_boat(1), (1.6, 9.4, RIVER_Z - 0.1), 0.06, NAMES)
    place_kit(A, "battle", river_boat(2, (0.62, 0.20, 0.16)), (-11.0, 10.6, RIVER_Z - 0.1), -0.08, NAMES)


def far_bank(A):
    """Christ Church, clock tower, windmill, riverside houses, St Paul's Hill, harbour ships, clouds."""
    rng = random.Random(9)
    # Christ Church: red hall, front gable with white cross, lit windows; clock tower beside it
    cx, cy, cz = 16.0, 32.0, ground(16.0, 32.0)
    hall = Kit()
    hall.put("Plaster", paint(bx(9.0, 20.0, 7.5, (0, 10.0, -1.0), bev=0.0), STADT_RED, ao=0.0, top=0.1))
    gab = P([(-4.5, -0.02, 6.5), (4.5, -0.02, 6.5), (0, -0.02, 11.0)], [(0, 1, 2)])
    hall.put("Plaster", paint(K.dbl(gab), STADT_RED, ao=0.0), paint(join(bx(9.4, 0.3, 0.4, (0, -0.1, 6.3), bev=0.0), bx(0.5, 0.2, 2.2, (0, -0.15, 8.0), bev=0.0),
                                                                       bx(1.6, 0.2, 0.45, (0, -0.15, 9.1), bev=0.0)), (0.88, 0.86, 0.82), ao=0.0))
    rf = P([(-5.0, -0.2, 6.5), (0, -0.2, 11.2), (0, 20.2, 11.2), (-5.0, 20.2, 6.5), (5.0, -0.2, 6.5), (5.0, 20.2, 6.5)], [(0, 3, 2, 1), (1, 2, 5, 4)])
    hall.put("Tile", paint(K.dbl(rf), (0.40, 0.20, 0.15), ao=0.0, top=0.3))
    hall.put("Plaster", paint(join(bx(4.2, 2.4, 3.6, (0, -1.2, -0.5), bev=0.0)), STADT_RED, ao=0.0),
             paint(P([(-2.3, -2.5, 3.1), (2.3, -2.5, 3.1), (0, -2.5, 4.6)], [(0, 1, 2)]), STADT_RED, ao=0.0))
    frames = []
    for x in (-2.8, 2.8):
        hall.put("Glow", glow_grad(paint(quad_y(x, -0.03, 1.4, 0.9, 2.0), (1, 0.82, 0.55), ao=0.0)))
        frames.append(xf(bars(0.9, 2.0), (x, -0.03, 1.4)))
    hall.put("Glow", glow_grad(paint(P([(-0.8, -2.52, 0.0), (0.8, -2.52, 0.0), (0.8, -2.52, 2.4), (-0.8, -2.52, 2.4)], [(0, 1, 2, 3)]), (1, 0.85, 0.6), ao=0.0)))
    frames.append(xf(bars(1.6, 2.4), (0, -2.52, 0.0)))
    trim = [K.tube([(-4.7, -0.15, 6.4), (0, -0.15, 11.15), (4.7, -0.15, 6.4)], 0.14, seg=4, cap=True),
            K.tube([(-2.4, -2.6, 3.0), (0, -2.6, 4.7), (2.4, -2.6, 3.0)], 0.1, seg=4, cap=True)]
    belfry = [bx(1.6, 1.4, 1.8, (0, 0.8, 10.4), bev=0.0)]
    hall.put("Plaster", paint(join(trim), (0.90, 0.88, 0.84), ao=0.0, top=0.2), paint(join(belfry), STADT_RED, ao=0.0, top=0.15))
    hall.put("Tile", paint(K.lathe([(1.2, 12.2), (0.0, 13.4)], seg=4, phase=math.pi / 4, cap0=True), (0.40, 0.20, 0.15), ao=0.0, top=0.3))
    rose = P([(0.0, -0.04, 7.9)] + [(0.7 * math.cos(a), -0.04, 7.9 + 0.7 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)[:-1]],
             [(0, 1 + i, 1 + (i + 1) % 8) for i in range(8)])
    hall.put("Glow", glow_grad(paint(rose, (1.0, 0.8, 0.5), ao=0.0), lo=0.75))
    frames += [xf(bx(1.4, 0.04, 0.04, (0, 0, -0.02), bev=0.0), (0, -0.07, 7.9), (0, a, 0)) for a in np.linspace(0, math.pi, 4, endpoint=False)]
    frames.append(K.tube([(0.7 * math.cos(a), -0.07, 7.9 + 0.7 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)], 0.035, seg=3, cap=False))
    for yy in (3.0, 7.0, 11.0, 15.0):  # lit side windows (left wall faces the town)
        hall.put("Glow", glow_grad(paint(P([(-4.52, yy - 0.5, 2.0), (-4.52, yy + 0.5, 2.0), (-4.52, yy + 0.5, 4.4), (-4.52, yy - 0.5, 4.4)], [(0, 3, 2, 1)]),
                                         (1.0, 0.8, 0.5), ao=0.0)))
        frames.append(xf(bars(1.0, 2.4), (-4.52, yy, 2.0), (0, 0, -math.pi / 2)))
    hall.put("Wood", paint(join(frames), (0.16, 0.10, 0.07), ao=0.0, top=0.0))
    place_kit(A, "far", hall, (cx, cy, cz), 0.12, NAMES_FAR)
    tx, ty = 10.0, 24.0
    tw = Kit()
    tw.put("Plaster", paint(join(bx(3.4, 3.4, 9.5, (0, 0, -1.0), bev=0.0), bx(3.9, 3.9, 0.4, (0, 0, 8.5), bev=0.0), bx(2.6, 2.6, 2.0, (0, 0, 8.9), bev=0.0)),
                            STADT_RED, ao=0.0, top=0.15))
    tw.put("Tile", paint(K.lathe([(2.2, 10.9), (1.2, 11.9), (0.2, 12.9), (0, 13.3)], seg=4, phase=math.pi / 4, cap0=True), (0.40, 0.20, 0.15), ao=0.0, top=0.3))
    face = P([(0.0, -1.33, 9.9)] + [(0.65 * math.cos(a), -1.33, 9.9 + 0.65 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)[:-1]],
             [(0, 1 + i, 1 + (i + 1) % 8) for i in range(8)])
    tw.put("Glow", [glow_grad(paint(xf(face, (0, 0, 0), (0, 0, a * math.pi / 2)), (1.0, 0.95, 0.85), ao=0.0), lo=0.8) for a in range(4)])
    dial = join(K.tube([(0.67 * math.cos(t), -1.37, 9.9 + 0.67 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 13)], 0.05, seg=3, cap=False),
                bx(0.05, 0.03, 0.5, (0, -1.38, 9.9), bev=0.0), xf(bx(0.05, 0.03, 0.36, (0, 0, 0), bev=0.0), (0, -1.38, 9.9), (0, 2.1, 0)))
    tw.put("Wood", [paint(xf(dial, (0, 0, 0), (0, 0, a * math.pi / 2)), (0.16, 0.10, 0.07), ao=0.0, top=0.0) for a in range(4)])
    place_kit(A, "far", tw, (tx, ty, ground(tx, ty)), 0.1, NAMES_FAR)
    # Dutch windmill on the far bank (left-centre)
    wx, wy = -8.6, 19.0
    wm = Kit()
    wm.put("Plaster", paint(K.lathe([(2.0, -0.5), (1.9, 1.0), (1.45, 6.5), (1.5, 6.6), (1.4, 6.8)], seg=8, phase=math.pi / 8, cap0=False), (0.86, 0.84, 0.80), ao=0.0, top=0.1),
            paint(K.lathe([(2.05, 0.9), (2.05, 1.2), (1.95, 1.2)], seg=8, phase=math.pi / 8, cap0=False, cap1=False), STADT_RED, ao=0.0))
    wm.put("Tile", paint(K.lathe([(1.6, 6.8), (1.4, 7.6), (0.6, 8.2), (0.0, 8.4)], seg=8, cap0=True), (0.30, 0.22, 0.20), ao=0.0, top=0.3))
    hub = np.array((0.0, -1.6, 7.6))
    for i in range(4):
        a = math.radians(20 + 90 * i)
        d = np.array((math.cos(a), 0.0, math.sin(a)))
        side = np.array((-math.sin(a), 0.0, math.cos(a)))
        wm.put("Plaster", paint(K.tube([tuple(hub), tuple(hub + d * 6.0)], 0.08, seg=3, cap=False), (0.30, 0.20, 0.15), ao=0.0))
        lat = []
        for t in np.linspace(0.18, 1.0, 6):
            a0, b0 = hub + d * 6.0 * t, hub + d * 6.0 * t + side * 1.1
            lat.append(K.tube([tuple(a0), tuple(b0)], 0.03, seg=3, cap=False))
        lat.append(K.tube([tuple(hub + d * 1.1 + side * 1.1), tuple(hub + d * 6.0 + side * 1.1)], 0.035, seg=3, cap=False))
        wm.put("Plaster", paint(join(lat), (0.86, 0.84, 0.80), ao=0.0))
    wm.put("Glow", glow_grad(paint(quad_y(0.0, -2.0, 0.6, 0.9, 1.6), (1, 0.82, 0.55), ao=0.0)))
    wm.put("Wood", paint(xf(bars(0.9, 1.6), (0.0, -2.0, 0.6)), (0.16, 0.10, 0.07), ao=0.0, top=0.0))
    place_kit(A, "far", wm, (wx, wy, ground(wx, wy)), 0.0, NAMES_FAR)
    # riverside houses along the far bank (colourful backs facing the river)
    for i, x in enumerate(np.arange(-46.0, -13.0, 4.4)):
        if not in_vista(x, 16):
            continue
        kit = H.shophouse(W=4.4, wall=PASTEL[i % 5], shutter=(0.25, 0.20, 0.16), lit=((True, False), (False, True), (True, True))[i % 3],
                          shop_open=(i % 2 == 0), seed=60 + i, lod=2)
        place_kit(A, "far", kit, (x, RIVER_Y1 + 0.8, ground(x, 14.0)), 0.0, NAMES_FAR)
    # trees on the far bank
    for k in range(14):
        x, y = rng.uniform(-30, 22), rng.uniform(18, 50)
        if not far_land(x, y) or abs(x - cx) < 6 and abs(y - cy - 8) < 13 or math.hypot(x - tx, y - ty) < 4 or math.hypot(x - wx, y - wy) < 6:
            continue
        b = K.canopy(rng.uniform(2.2, 3.4), seed=300 + k, lumps=3, sub=1, squash=0.75, spread=0.6)
        A.add("far", "MatLeaf_canopy", paint(xf(b, (x, y, ground(x, y) + 2.0)), (0.14, 0.24, 0.16), var=0.12, ao=0.0, top=0.35))
        A.add("far", "MatPlaster_wall", paint(K.tube([(x, y, ground(x, y) - 0.2), (x, y, ground(x, y) + 2.4)], 0.2, seg=4, cap=False), (0.22, 0.16, 0.12), ao=0.0))

    # St Paul's Hill: ruined church + lighthouse on top (left-centre, behind the houses)
    def sh(x, y):
        return 20.0 * math.exp(-(((x + 22) / 20.0) ** 2 + ((y - 72) / 14.0) ** 2)) + 1.2 * nz(x, y, 0, 0.06, 4) - 1.2
    A.add("far", "MatLeaf_canopy", paint_hill(hill(-60, 10, 50, 96, sh, nx=50, ny=8, base=-1.5), (0.10, 0.16, 0.12), (0.16, 0.24, 0.16), seed=4))
    rx, ry = -20.0, 71.0
    rz = sh(rx, ry)
    ruin = [bx(0.8, 14.0, 7.0, (-3.6, 0, rz - 1.0), bev=0.0), bx(0.8, 14.0, 6.5, (3.6, 0, rz - 1.0), bev=0.0), bx(8.0, 0.8, 9.5, (0, -7.0, rz - 1.0), bev=0.0)]
    A.add("far", "MatPlaster_wall", paint(join([xf(q, (rx, ry, 0)) for q in ruin]), (0.52, 0.40, 0.34), ao=0.0, top=0.2))
    lx, ly = rx + 5.0, ry - 1.0
    lz = sh(lx, ly) - 0.5
    A.add("far", "MatPlaster_wall", paint(xf(K.lathe([(0.9, -1.0), (0.7, 5.0), (0.95, 5.2), (0.0, 5.4)], seg=8), (lx, ly, lz)), (0.9, 0.9, 0.88), ao=0.0))
    A.add("far", "MatGlow_warm", paint(xf(K.lathe([(0.6, 5.4), (0.6, 6.2), (0.0, 6.4)], seg=6), (lx, ly, lz)), (1, 0.9, 0.7), ao=0.0))
    # ships of different origins in the harbour: galleon (Flor de la Mar), Chinese junk, Bugis pinisi
    ship(A, 2.0, 50.0, -0.75, "galleon")
    ship(A, -9.0, 78.0, -0.15, "junk")
    ship(A, 14.0, 92.0, 0.1, "pinisi")
    ship(A, 30.0, 120.0, 0.0, "pinisi")
    # distant shore + hills (layered silhouettes)
    def dh(x, y):
        return (14.0 * math.exp(-(((x - 60) / 70.0) ** 2)) + 9.0 * math.exp(-(((x + 60) / 50.0) ** 2)) + 3.0 * nz(x, y, 0, 0.03, 6)) * math.exp(-(((y - 230) / 25.0) ** 2))
    A.add("far", "MatLeaf_canopy", paint_hill(hill(-160, 200, 200, 260, dh, nx=70, ny=5, base=-2), (0.20, 0.24, 0.34), (0.26, 0.30, 0.40), seed=6, top=0.1))
    for k, (x, y, z, w, h) in enumerate(((-40, 260, 46, 110, 12), (50, 280, 62, 140, 15), (120, 250, 40, 80, 9), (5, 230, 34, 70, 8), (-110, 270, 55, 100, 12))):
        A.add("far", "MatPlaster_wall", cloud(x, y, z, w, h, 70 + k, (0.62, 0.50, 0.62), under=(0.92, 0.62, 0.52)))


def ship(A, x, y, rz, kind):
    k = Kit()
    if kind == "galleon":
        hull = K.perahu(L=16.0, W=4.2, H=2.6, seed=3)
        k.put("Wood", paint(hull, (0.30, 0.18, 0.12), ao=0.0, top=0.2))
        k.put("Wood", paint(join(bx(4.0, 3.6, 3.0, (-5.6, 0, 2.0), bev=0.0), bx(2.6, 3.0, 1.6, (6.4, 0, 2.2), bev=0.0)), (0.36, 0.22, 0.14), ao=0.0, top=0.2))
        masts = [(-2.5, 15.0), (2.0, 17.0), (6.4, 12.0)]
        sail = (0.86, 0.82, 0.72)
    elif kind == "junk":
        hull = K.perahu(L=11.0, W=3.4, H=2.0, seed=4)
        k.put("Wood", paint(hull, (0.32, 0.20, 0.12), ao=0.0, top=0.2))
        k.put("Wood", paint(bx(3.0, 3.0, 1.8, (-4.0, 0, 1.6), bev=0.0), (0.55, 0.16, 0.10), ao=0.0))
        masts = [(-1.5, 10.0), (2.5, 8.0)]
        sail = (0.62, 0.30, 0.18)
    else:
        hull = K.perahu(L=10.0, W=2.6, H=1.6, seed=5)
        k.put("Wood", paint(hull, (0.42, 0.30, 0.20), ao=0.0, top=0.2))
        masts = [(-1.0, 11.0), (2.0, 9.0)]
        sail = (0.80, 0.76, 0.66)
    for mx, mh in masts:
        k.put("Wood", paint(K.tube([(mx, 0, 1.0), (mx, 0, mh)], 0.15, seg=4, cap=False), (0.24, 0.16, 0.10), ao=0.0))
        if kind == "galleon":
            for z0, w in ((mh * 0.42, 3.2), (mh * 0.72, 2.4)):
                q = P([(mx, -w, z0), (mx, w, z0), (mx + 0.3, w * 0.9, z0 + mh * 0.24), (mx + 0.3, -w * 0.9, z0 + mh * 0.24)], [(0, 1, 2, 3)])
                k.put("Cloth", paint(K.dbl(q), sail, ao=0.0, top=0.0))
        elif kind == "junk":
            q = P([(mx - 2.4, 0, mh * 0.3), (mx + 1.6, 0, mh * 0.3), (mx + 1.2, 0, mh * 0.95), (mx - 1.6, 0, mh * 0.95)], [(0, 1, 2, 3)])
            k.put("Cloth", tint(paint(K.dbl(q), sail, ao=0.0, top=0.0), stripes(2, 1.2, 0.75, 1.0)))
        else:
            q = P([(mx - 0.2, 0, 1.8), (mx + 3.2, 0, 2.2), (mx, 0, mh)], [(0, 1, 2)])
            k.put("Cloth", paint(K.dbl(q), sail, ao=0.0, top=0.0))
    k.put("Glow", paint(K.dbl(quad_y(0.0, 0.0, 3.0, 0.6, 0.6)), (1, 0.85, 0.6), ao=0.0))
    place_kit(A, "far", k, (x, y, RIVER_Z - 0.3), rz, NAMES_FAR)


def apron(A):
    place_kit(A, "battle", slipper_bench(1), (-5.7, 3.0, ground(-5.7, 3.0)), -0.9, NAMES)
    A.contact(-5.7, 3.0, 1.0, 0.3)
    # kamcheng jar stack + rattan basket + crate (right, near strip edge)
    for i, (x, y, z, b) in enumerate(((5.6, -3.0, 0.0, (0.86, 0.50, 0.62)), (5.95, -2.7, 0.0, (0.50, 0.72, 0.58)), (5.8, -2.9, 0.24, (0.92, 0.78, 0.40)))):
        A.add("battle", "MatTile_brick", xf(kamcheng(0.13, 0.19, b), (x, y, ground(x, y) + z)))
    A.add("battle", "MatWood_timber", tint(paint(bx(0.48, 0.48, 0.24, (5.8, -2.9, ground(5.8, -2.9)), bev=0.015), (0.42, 0.30, 0.18), ao=0.3, ao_h=0.5), stripes(2, 18, 0.75, 1.0)))
    A.add("battle", "MatWood_timber", paint(xf(K.basket(0.2, 0.24), (6.3, -3.5, ground(6.3, -3.5))), (0.56, 0.42, 0.24), ao=0.35, ao_h=0.25))
    A.contact(5.9, -3.0, 1.0, 0.3)
    # bougainvillea planters (vista foreground, low)
    for k, (x, y, L) in enumerate(((-3.6, -7.2, 3.2), (3.4, -7.4, 2.8), (-9.8, -5.4, 2.0))):
        pl = bx(L, 0.8, 0.45, (x, y, ground(x, y)), bev=0.03)
        A.add("battle", "MatTile_brick", tint(paint(pl, (0.56, 0.24, 0.16), ao=0.3, ao_h=0.4, top=0.2), stripes(2, 11, 0.85, 1.0)))
        rng = random.Random(k)
        g0 = ground(x, y)
        prof = [(0.46 * math.cos(t), 0.42 + 0.42 * math.sin(t)) for t in np.linspace(math.pi, 0, 13)]
        hedge = K.extrude([(x - L / 2 + 0.1, y), (x + L / 2 - 0.1, y)], prof, zfn=lambda a_, b_: g0, step=0.07, jitter=0.0, seed=k)
        up = smooth01(g0 + 0.42, g0 + 0.55, hedge.v[:, 2])[:, None]
        cx_ = np.column_stack([np.zeros(len(hedge.v)), hedge.v[:, 1] - y, hedge.v[:, 2] - g0 - 0.42])
        cx_ /= np.maximum(np.linalg.norm(cx_, axis=1, keepdims=True), 1e-6)
        bump = 0.16 * K.nfield(hedge.v, 2.6, k) + 0.07 * K.nfield(hedge.v, 7.0, k + 3) + 0.06
        hedge.v += cx_ * (bump[:, None] * up)
        p = hedge
        paint(p, (0.15, 0.27, 0.12), var=0.06, ao=0.35, ao_h=0.9, ground=g0 + 0.3, top=0.3, namp=0.2, ns=6)
        A.add("battle", "MatLeaf_canopy", p)
        nn = K.vnormals(p)
        tops = np.flatnonzero(nn[:, 2] > 0.55)
        flowers = []   # sparse bougainvillea bract clusters on the leaf mass
        for i in [int(tops[j]) for j in sorted(rng.sample(range(len(tops)), min(len(tops), int(4 * L))))]:
            for m in range(3):
                q = K.rock(rng.uniform(0.03, 0.05), seed=k * 100 + i + m, sub=1, squash=(1, 1, 0.6))
                flowers.append(paint(xf(q, tuple(p.v[i] + nn[i] * 0.03 + np.array((rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), 0)))),
                                     (0.74, 0.16, 0.44) if rng.random() < 0.8 else (0.90, 0.62, 0.78), var=0.1, ao=0.0, top=0.25))
        A.add("battle", "MatLeaf_canopy", flowers)


def build(A):
    for name in ("MatGround_laterite", "MatTile_brick", "MatPlaster_wall", "MatWood_timber", "MatCloth_bunting", "MatWater_river",
                 "MatRock_stone", "MatLeaf_canopy"):
        A.mat(name)
    A.mat("MatMetal_iron", rough=0.5, metal=0.35)
    A.mat("MatGlow_warm", emit=(1.0, 0.72, 0.42), estr=1.2)
    A.mat("MatGlow_lantern", emit=(1.0, 0.22, 0.10), estr=3.2)

    stadthuys(A)
    peranakan_row(A)
    for k, (x, y, rz, pal) in enumerate(((-7.3, -2.6, 1.75, ((0.80, 0.22, 0.40), (0.95, 0.45, 0.70), (0.98, 0.85, 0.30), (0.62, 0.40, 0.85))),
                                         (-7.0, 3.8, 1.35, ((0.25, 0.55, 0.80), (0.98, 0.82, 0.20), (0.95, 0.40, 0.55), (0.50, 0.85, 0.60))),
                                         (7.6, 3.6, -1.5, ((0.95, 0.55, 0.15), (0.98, 0.35, 0.55), (0.40, 0.75, 0.95), (0.98, 0.95, 0.60))))):
        place_kit(A, "battle", flower_trishaw(k, pal), (x, y, ground(x, y)), rz, NAMES)
        A.contact(x, y, 1.3, 0.3)
    river(A)
    apron(A)
    # lantern strings: Stadthuys forecourt + Peranakan row
    lantern_string(A, "battle", (STADT_X + 0.3, -6.0, 3.4), (STADT_X + 0.3, 6.5, 3.4), 9, 0.5, "MatGlow_lantern", "MatWood_timber", "MatMetal_iron")
    lantern_string(A, "battle", (PERA_X - 0.6, -6.0, 3.3), (PERA_X - 0.6, 7.0, 3.3), 8, 0.45, "MatGlow_lantern", "MatWood_timber", "MatMetal_iron")
    # lights (<=6)
    A.light((STADT_X + 1.2, -2.4, 2.8), 90.0, (1.0, 0.66, 0.40), range_m=6)
    A.light((STADT_X + 1.2, 3.6, 2.8), 90.0, (1.0, 0.66, 0.40), range_m=6)
    A.light((PERA_X - 0.6, -1.6, 2.8), 80.0, (1.0, 0.62, 0.38), range_m=6)
    A.light((PERA_X - 0.6, 4.4, 2.8), 80.0, (1.0, 0.62, 0.38), range_m=6)
    A.light((-5.5, RIVER_Y0 - 0.6, 3.2), 70.0, (1.0, 0.82, 0.58), range_m=6)
    A.light((4.5, RIVER_Y0 - 0.6, 3.2), 70.0, (1.0, 0.82, 0.58), range_m=6)

    A.terrain(ground, gcolor, kind=None, rin=4.5, rout=90.0, split=23.0, cull=gcull, seed=1)
    brick_rings(A)
    rng = random.Random(3)
    for k in range(10):  # weeds in the plaza joints near the walls and the river walk
        x, y = rng.uniform(-8.5, 8.0), rng.uniform(WALK_Y - 0.6, WALK_Y + 0.2)
        A.scatter_patch("Grass", 22, x, y, rng.uniform(0.2, 0.4), ground, (0.26, 0.32, 0.18), seed=600 + k)
    for k in range(8):
        y = rng.uniform(-6, 6)
        A.scatter_patch("Grass", 22, STADT_X + 0.35, y, rng.uniform(0.2, 0.35), ground, (0.26, 0.32, 0.18), seed=700 + k)
    far_bank(A)


if __name__ == "__main__":
    K.main("melaka", build, MOOD)
