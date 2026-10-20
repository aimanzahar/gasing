"""Pahang arena -- a misty highland tea estate (design_art.md section c, USER_SPEC Pahang). SLOPE arena:
the hill falls toward -x (ARENA_DEFS.pahang.hazard.dir = (-1, 0)); the dish sits level on a terrace cut into
the hillside, with a dry-stone retaining wall uphill (+x) and a grassy embankment dropping downhill (-x).
Ground: red laterite paths between contour tea hedges (geometry) that curve around the spur.
Apron: raga tea baskets, cabbage crates, terendak hat. Far band: curving tea rows climbing across the frame,
a red footpath slanting up through them. Left flank (downhill): hill-farm shed on long stilts over the slope,
cabbage beds below. Right flank (uphill): tea rows above the wall, tree ferns, a silver-oak shade tree.
Far set (vista): the tea hill climbing to the right, a white tea factory, layered misty ridges, mist banks, clouds.

NOTE main.gd: the terrain drops below y=-0.5 here, so the legacy "Ground" plane must be hidden for this arena.

  blender -b --factory-startup -P art_src/arena_pahang.py -- --export --render game,vista --out <dir>
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

MOOD = {"sky_top": (0.46, 0.57, 0.62), "sky_horizon": (0.82, 0.86, 0.82), "fog": (0.66, 0.74, 0.70),
        "fog_density": 0.0045, "sun_color": (0.98, 0.95, 0.86), "sun_energy": 0.9,
        "lantern": (1.0, 0.78, 0.50), "lantern_energy": 1.2, "exposure": 0.85, "ambient": 0.55,
        "b_sun": 3.2, "b_world": 1.0, "b_fill": 0.45, "b_lantern": 6.0}

# ---------------------------------------------------------------- palette (sRGB)
RED = (0.50, 0.31, 0.21)        # laterite
RED_DK = (0.38, 0.23, 0.16)
RED_PALE = (0.56, 0.42, 0.32)
GRASSY = (0.34, 0.44, 0.18)
TEA_TOP = (0.38, 0.54, 0.18)
TEA_SIDE = (0.15, 0.28, 0.11)
STONE = (0.62, 0.60, 0.55)
MOSS = (0.30, 0.38, 0.16)
TIMBER = (0.45, 0.36, 0.27)
TIMBER_DK = (0.29, 0.22, 0.16)
ZINC = (0.50, 0.52, 0.52)
RATTAN = (0.60, 0.48, 0.30)
CABBAGE = (0.46, 0.62, 0.32)
FERN = (0.24, 0.40, 0.14)

# ---------------------------------------------------------------- layout
SLOPE = 0.24
TX, TY0, TYR = 6.5, 3.5, 2.7     # terrace half-width, start of the rounded far end, its depth
ROW = 1.45                       # tea row spacing (contour)


def bow(y):
    """contours bow around the spur near the dish, then run straight up the valley (vista)."""
    return 2.6 * math.tanh(((y - 2.0) / 9.0) ** 2)


def u_of(x, y):
    """contour coordinate: the hillside's iso-height lines bow around the spur (curving tea rows)."""
    return x - bow(y)


def smax(a, b, k):
    return k * math.log(math.exp(a / k) + math.exp(b / k))


def nat_h(x, y):
    """natural hillside before the terrace cut: rises toward +x and away (+y), valley floor far left."""
    u = u_of(x, y)
    h = SLOPE * u + 0.05 * max(0.0, y - 8.0) + 0.05 * nz(x, y, 0, 0.3, 2) + 0.02 * nz(x, y, 0, 1.3, 3)
    h = smax(h, -4.2 + 0.4 * nz(x, y, 0, 0.05, 4), 0.6)            # valley floor far left
    return -smax(-h, -(12.0 + 2.0 * nz(x, y, 0, 0.03, 5)), 1.5)      # rounded hill crest far right


def smooth_cut(x, y):
    return SLOPE * u_of(x, y) + 0.05 * max(0.0, y - 8.0)


def terrace_d(x, y):
    if y <= TY0:
        return abs(x) - TX
    e = math.hypot(x / TX, (y - TY0) / TYR)
    return (e - 1.0) * (TX if abs(x) > (y - TY0) else TYR) * 0.75


def terrace_h(x, y):
    return 0.02 + 0.012 * nz(x, y, 0, 1.1, 5) + 0.002 * x


def ground(x, y):
    t = terrace_h(x, y)
    d = terrace_d(x, y)
    if d <= 0:
        return t
    hn = nat_h(x, y)
    if hn >= t:   # uphill: dry-stone wall holds the cut
        return t + (hn - t) * smooth01(0.14, 0.3, d)
    w = 0.4 + 1.0 * (t - hn)   # downhill: grassy embankment ~1:1
    return t + (hn - t) * smooth01(0.0, w, d)


def row_phase(x, y):
    """0 at a hedge centre line, 0.5 mid-path."""
    q = (u_of(x, y) - 0.35) / ROW
    return abs(q - round(q))


def gcolor(x, y, z):
    n1 = nz(x, y, 0, 0.4, 11)
    n2 = nz(x, y, 0, 2.0, 12)
    n3 = nz(x, y, 0, 5.5, 13)
    d = terrace_d(x, y)
    c = np.array(RED) * (1 + 0.08 * n1 + 0.06 * n2 + 0.03 * n3)
    c = mix(c, RED_DK, 0.4 * smooth01(0.2, 0.6, nz(x, y, 0, 0.8, 14)))
    if d <= 0:
        c = mix(c, RED_PALE, 0.35 * smooth01(0.0, 0.5, nz(x, y, 0, 0.45, 15)))     # trodden dry patches
        c = mix(c, np.array(GRASSY) * 0.9, 0.5 * smooth01(0.35, 0.7, nz(x, y, 0, 0.6, 16)) * smooth01(5.2, 6.0, math.hypot(x, y)))
        c = mix(c, GRASSY, 0.55 * smooth01(5.6, 6.4, abs(x)) * smooth01(-0.1, 0.4, n1))  # grassy rim at the edges
        c = mix(c, np.array(RED) * 1.03, 0.5 * (1 - smooth01(4.6, 5.6, math.hypot(x, y))))
    else:
        hn = nat_h(x, y)
        if hn < terrace_h(x, y) and d < 0.4 + 1.0 * (terrace_h(x, y) - hn):
            c = mix(c, GRASSY, 0.8)                                                     # grassy embankment
        else:
            c = mix(c, (0.20, 0.30, 0.13), 0.55 * (1 - smooth01(0.18, 0.32, row_phase(x, y))))  # shade under hedges
    if math.hypot(x, y) > 23:
        u = u_of(x, y)
        if u > 6.0:   # tea on the hill: hedge bands
            c = mix(c, (0.30, 0.42, 0.18), 0.75 * (1 - smooth01(0.2, 0.4, row_phase(x, y))))
        else:         # jungle valley floor
            c = mix(c, (0.16, 0.26, 0.13), 0.85 * smooth01(-2.0, -6.0, u) + 0.3)
    return tuple(np.clip(c, 0, 1))


def gkind(x, y, z):
    if math.hypot(x, y) > 23:
        return "MatGround_redsoil"
    d = terrace_d(x, y)
    if d > 0 and nat_h(x, y) < terrace_h(x, y) and d < 0.4 + 1.0 * (terrace_h(x, y) - nat_h(x, y)):
        return "MatGrass_bank"
    return "MatGround_redsoil"


def visible(x, y, pad=0.0):
    """battle footprint widened for the lower downhill ground (seen further out) + vista."""
    return in_battle(x + 0.12 * min(0.0, x), y, pad) or in_vista(x, y)


def gcull(cx, cy, zmax):
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


# ---------------------------------------------------------------- props
def stone_wall(A):
    """dry-stone retaining wall along the uphill edge: coursed stones bulging out of a displaced grid."""
    pts = [(TX + 0.04, y) for y in np.arange(-14.0, TY0, 0.2)]
    for k in range(1, 28):
        a = math.pi / 2 * k / 28
        pts.append(((TX + 0.04) * math.cos(a), TY0 + (TYR + 0.04) * math.sin(a)))
    s = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        s.append(s[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    rng = random.Random(3)
    courses = []
    for c in range(9):  # stone boundaries per course (staggered)
        b, cur = [], -rng.uniform(0.0, 0.5)
        while cur < s[-1] + 1:
            b.append(cur)
            cur += rng.uniform(0.32, 0.62)
        courses.append(np.array(b))
    CH = 0.25
    v, f, col = [], [], []
    nz_rows = 14
    for i, (x, y) in enumerate(pts):
        hgt = max(0.0, smooth_cut(x + 0.25, y) - terrace_h(x, y) + 0.06)
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty)
        nx_, ny_ = -ty / l, tx / l          # outward normal: toward the terrace
        for k in range(nz_rows + 1):
            z = -0.12 + (hgt + 0.12) * k / nz_rows
            c = int(max(0.0, z) // CH)
            bnd = courses[min(c, 8)]
            j = np.searchsorted(bnd, s[i])
            e_s = min(s[i] - bnd[max(0, j - 1)], bnd[min(j, len(bnd) - 1)] - s[i])
            e_z = min(z - c * CH, (c + 1) * CH - z) if z > 0 else 0.1
            e = min(abs(e_s), abs(e_z))
            bulge = 0.07 * smooth01(0.0, 0.07, e) * (0.7 + 0.3 * math.sin(c * 7.1 + j * 3.3))
            v.append((x + nx_ * bulge, y + ny_ * bulge, terrace_h(x, y) + z))
            r = random.Random(c * 1000 + int(j)).random()
            base = np.array(STONE) * (0.8 + 0.35 * r)
            base = mix(base, (0.50, 0.40, 0.32), 0.4 * (r > 0.7))
            base = mix(base, MOSS, 0.6 * smooth01(0.35, 0.75, nz(x, y, z, 0.9, 7)) + 0.5 * smooth01(hgt - 0.3, hgt, z))
            col.append(base * (0.62 + 0.38 * smooth01(0.0, 0.04, e)))
    m = nz_rows + 1
    for i in range(len(pts) - 1):
        for k in range(m - 1):
            a = i * m + k
            f.append((a, a + 1, a + m + 1, a + m))
    p = P(v, f)
    p.c = np.ones((len(v), 4))
    p.c[:, :3] = np.clip(np.array(col), 0, 1)
    A.add("battle", "MatRock_stone", p)
    # grass verge along the wall top
    for i in range(0, len(pts) - 6, 6):
        (x0, y0), (x1, y1) = pts[i], pts[i + 6]
        if smooth_cut(x0 + 0.25, y0) - terrace_h(x0, y0) > 0.25:
            A.scatter_strip("Grass", 34, (x0 + 0.35, y0), (x1 + 0.35, y1), 0.4, nat_h, (0.40, 0.50, 0.21), step=0.6)


def path_d(x, y):
    """distance to the red footpath slanting up through the uphill rows."""
    ax, ay, bx, by = 4.2, 6.4, 11.2, 8.8
    t = max(0.0, min(1.0, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)))
    return math.hypot(x - ax - t * (bx - ax), y - ay - t * (by - ay))


def tea_rows(A):
    """contour tea hedges on both sides of the cut; clipped from the terrace/apron. Near (battle-set) rows are
    sampled every 0.25 m and lumped into bushes ~0.5 m apart with darker creases, plus a sprig strip
    (EnvScatterGrass_28) on top to break the silhouette; far rows stay smooth extruded domes."""
    prof = [(-0.5, -0.12), (-0.42, 0.5), (-0.17, 0.74), (0.17, 0.75), (0.42, 0.52), (0.5, -0.12)]
    prof_far = [(-0.55, -0.2), (-0.35, 0.65), (0.35, 0.68), (0.55, -0.2)]
    for k in range(-30, 40):
        uk = 0.35 + k * ROW
        for (ya, yb, far) in ((-16.0, 30.0, False), (30.0, 43.0, True), (43.0, 140.0, True)):
            step = 0.5 if not far else (1.0 if ya < 40 else 2.5)
            run, runs = [], []
            for y in np.arange(ya, yb + 0.01, step):
                x = uk + bow(y)
                r = math.hypot(x, y)
                ok = (terrace_d(x, y) > 0.9 and r > 6.7 and visible(x, y, pad=1.5) and (far == (r > 23)) and r < 95 and path_d(x, y) > 0.55
                      and (x < 6.0 or nat_h(x, y) > terrace_h(x, y) + 0.4 or terrace_d(x, y) > 1.6)
                      and not (x < -7.0 and nat_h(x, y) < -3.6))
                if ok:
                    run.append((x, y))
                else:
                    if len(run) > 1:
                        runs.append(run)
                    run = []
            if len(run) > 1:
                runs.append(run)
            for rn in runs:
                p = K.extrude(rn, prof_far if far else prof, zfn=nat_h, step=step if far else 0.25,
                              jitter=0.0 if far else 0.12, seed=k * 7 + int(ya))
                z_rel = np.array([vz - nat_h(vx, vy) for vx, vy, vz in p.v])
                t = smooth01(0.3, 0.72, z_rel)
                if not far:
                    lobe = 0.10 * K.nfield(p.v, 3.5, k) + 0.06 * np.abs(np.sin(p.v[:, 1] * 6.5))
                    p.v[:, 2] += t * lobe
                elif step < 2:   # first far band (mid-vista): coarser 2 m bush lumps
                    p.v[:, 2] += t * (0.06 * K.nfield(p.v, 0.9, k) + 0.14 * np.abs(np.sin(p.v[:, 1] * math.pi / 2)))
                c = np.asarray(TEA_SIDE)[None, :] * (1 - t[:, None]) + np.asarray(TEA_TOP)[None, :] * t[:, None]
                c *= (1 + 0.14 * K.nfield(p.v, 2.2, k))[:, None]
                if not far:   # creases between the bushes
                    c += (np.asarray(TEA_SIDE)[None, :] - c) * (0.3 * (lobe < 0.02))[:, None]
                p.c = np.ones((len(p.v), 4))
                p.c[:, :3] = np.clip(c, 0, 1)
                A.add("far" if far else "battle", "MatLeaf_tea", p)
                if not far:
                    for i in range(0, len(rn) - 1, 2):
                        A.scatter_strip("Grass", 28, rn[i], rn[min(i + 2, len(rn) - 1)], 0.5, lambda x, y: nat_h(x, y) + 0.74, (0.44, 0.60, 0.22), step=1.0)


def farm_shed(A, x, y):
    """hill-farm shed: deck level with the terrace, stilts growing longer down the slope (-x), zinc roof."""
    W, D, FZ, H = 3.4, 2.7, 0.06, 2.1
    wood, zinc, dark = [], [], []
    for sx in (-W / 2, 0.0, W / 2):
        for sy in (-D / 2, D / 2):
            g = ground(x + sx, y + sy)
            wood.append(K.tube([(x + sx, y + sy, g - 0.15), (x + sx, y + sy, FZ)], [0.09, 0.08], seg=6))
            if FZ - g > 0.8:   # diagonal braces on the long downhill stilts
                wood.append(K.tube([(x + sx, y + sy, g + 0.2), (x + sx + 0.7 * (1 if sx < 0 else -1) * (sx != 0), y + sy, FZ - 0.1)], 0.04, seg=5))
            wood.append(K.tube([(x + sx, y + sy, FZ), (x + sx, y + sy, FZ + H + (0.35 if sx > 0 else 0.0))], 0.07, seg=6))
    wood.append(xf(K.box(W + 0.3, D + 0.3, 0.08, bev=0.015), (x, y, FZ)))
    for k in range(int(D / 0.2)):   # plank walls on the back (-x, downhill) and the two sides
        yy = y - D / 2 + 0.1 + k * 0.2
        wood.append(xf(K.box(0.04, 0.19, H - 0.1, bev=0.006), (x - W / 2 - 0.02, yy, FZ + 0.08)))
    for sy in (-1, 1):
        for k in range(int(W / 0.2)):
            xx = x - W / 2 + 0.1 + k * 0.2
            hh = H - 0.1 + 0.35 * (xx - (x - W / 2)) / W
            if sy < 0 and xx > x + 0.3:
                continue   # open front corner toward the camera
            wood.append(xf(K.box(0.19, 0.04, hh, bev=0.006), (xx, y + sy * (D / 2 + 0.02), FZ + 0.08)))
    rail = [K.tube([(x + W / 2 + 0.1, y - D / 2, FZ + 0.85), (x + W / 2 + 0.1, y + D / 2, FZ + 0.85)], 0.03, seg=5)]
    # monopitch corrugated roof, high side uphill (+x)
    nc = 26
    rv, rf = [], []
    for i in range(nc + 1):
        yy = y - D / 2 - 0.4 + (D + 0.8) * i / nc
        off = 0.03 * (i % 2)
        for t in (0.0, 1.0):
            rv.append((x - W / 2 - 0.45 + (W + 0.9) * t, yy, FZ + H - 0.05 + 0.5 * t + off))
    for i in range(nc):
        a = 2 * i
        rf.append((a, a + 2, a + 3, a + 1))
    zinc.append(K.dbl(P(rv, rf)))
    # cabbage crates on the deck, a hanging lamp
    crates = []
    for k, (cx, cy, cz) in enumerate(((x - 0.9, y + 0.6, FZ + 0.08), (x - 0.9, y - 0.05, FZ + 0.08), (x - 0.9, y + 0.6, FZ + 0.46), (x + 0.1, y + 0.8, FZ + 0.08))):
        crates.append((cx, cy, cz, k))
    for (cx, cy, cz, k) in crates:
        for sx in (-1, 1):
            wood.append(xf(K.box(0.03, 0.42, 0.36, bev=0.005), (cx + sx * 0.28, cy, cz)))
        for sy in (-1, 1):
            for lv in range(3):
                wood.append(xf(K.box(0.56, 0.02, 0.08, bev=0.003), (cx, cy + sy * 0.2, cz + 0.04 + lv * 0.12)))
        for j, (dx, dy) in enumerate(((-0.13, -0.09), (0.13, -0.09), (-0.13, 0.1), (0.13, 0.1))):
            A.add("battle", "MatLeaf_tea", paint(xf(blob((0.12, 0.12, 0.11), sub=2, seed=k * 4 + j, amp=0.15, freq=3), (cx + dx, cy + dy, cz + 0.3)), CABBAGE, var=0.08, ao=0.3, ao_h=0.15, ground=cz + 0.2, top=0.35))
    A.add("battle", "MatWood_timber", [paint(q, TIMBER if i % 3 else TIMBER_DK, var=0.1, ao=0.45, ao_h=1.0, ground=FZ, namp=0.1, ns=3, stretch=(1, 1, 0.2)) for i, q in enumerate(wood + rail)])
    A.add("battle", "MatMetal_zinc", [tint(paint(q, ZINC, var=0.04, ao=0.0, top=0.25),
                                            lambda v, c: c + (np.array([0.50, 0.32, 0.20, 1]) - c) * (0.6 * smooth01(0.0, 0.6, K.nfield(v, 1.3, 4, (1, 0.3, 1))))[:, None]) for q in zinc])
    A.contact(x, y, 2.4, 0.3)


def tree_fern(A, x, y, h, seed, set_="battle"):
    rng = random.Random(seed)
    g = ground(x, y) if set_ == "battle" else nat_h(x, y)
    lean = (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25))
    top = (x + lean[0], y + lean[1], g + h)
    trunk = K.tube([(x, y, g - 0.1), (x + lean[0] * 0.4, y + lean[1] * 0.4, g + h * 0.5), top], [0.13, 0.11, 0.1], seg=7)
    fr = []
    n = 11 if set_ == "battle" else 8
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.15, 0.15)
        L = rng.uniform(1.6, 2.1) * (h / 3.2) ** 0.5
        up = rng.uniform(0.25, 0.55)
        pth, w = [], []
        for i in range(7):
            t = i / 6
            pth.append((top[0] + L * t * math.cos(a), top[1] + L * t * math.sin(a), top[2] + 0.1 + up * L * t - 0.9 * L * t * t))
            w.append(0.04 + 0.26 * math.sin(math.pi * min(1.0, t * 1.1)))
        fr.append(K.strip_mesh(pth, w, fold=0.15, tears=0.55, seed=seed * 13 + k))
    A.add(set_, "MatWood_timber" if set_ == "battle" else "MatMetal_zinc", tint(paint(trunk, (0.24, 0.18, 0.13), var=0.05, ao=0.3, ao_h=1.0, ground=g, namp=0.25, ns=9),
                                                                              lambda v, c: c * (0.85 + 0.15 * (np.floor(v[:, 2] * 9) % 2))[:, None]))
    A.add(set_, "MatLeaf_tea", paint(join(fr), FERN, var=0.08, ao=0.2, ao_h=1.0, ground=top[2] - 1, top=0.4, namp=0.15, ns=2))
    if set_ == "battle":
        A.contact(x, y, 1.0, 0.25)


def shade_tree(A, x, y, h, seed, set_="battle"):
    """silver oak (Grevillea) shade tree: tall slim trunk, a few loose foliage clouds high up."""
    rng = random.Random(seed)
    g = nat_h(x, y)
    wood = [K.tube([(x, y, g - 0.2), (x + 0.2, y, g + h * 0.55), (x + 0.1, y + 0.2, g + h)], [0.18, 0.13, 0.08], seg=6)]
    leaf = []
    for k in range(4):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.4, 0.4)
        cz = g + h * rng.uniform(0.62, 0.95)
        cx, cy = x + 1.3 * math.cos(a), y + 1.3 * math.sin(a)
        wood.append(K.tube([(x + 0.15, y + 0.1, cz - 1.2), (cx, cy, cz)], [0.06, 0.03], seg=5))
        leaf.append(xf(blob((1.3, 1.0, 0.6), sub=2, seed=seed * 5 + k, amp=0.35, freq=2.6), (cx, cy, cz), (0, 0, a)))
    A.add(set_, "MatWood_timber" if set_ == "battle" else "MatMetal_zinc", [paint(q, (0.36, 0.30, 0.25), ao=0.2, ao_h=2, ground=g) for q in wood])
    A.add(set_, "MatLeaf_tea", [paint(q, (0.24, 0.36, 0.18), var=0.1, ao=0.3, ao_h=1.0, ground=g + h * 0.5, top=0.45) for q in leaf])


def cabbage_beds(A):
    """raised cabbage beds on the downhill shelf below the shed (left flank)."""
    rng = random.Random(6)
    for row in range(3):
        for k in range(6):
            x = -8.3 - row * 0.75 + rng.uniform(-0.05, 0.05)
            y = -4.6 + k * 0.62 + rng.uniform(-0.06, 0.06)
            g = ground(x, y)
            outer = blob((0.24, 0.24, 0.1), sub=2, seed=row * 10 + k, amp=0.25, freq=3)
            head = blob((0.15, 0.15, 0.14), sub=1, seed=row * 10 + k + 50)
            A.add("battle", "MatLeaf_tea", paint(xf(outer, (x, y, g + 0.06)), (0.36, 0.52, 0.26), var=0.1, ao=0.35, ao_h=0.12, ground=g, top=0.3))
            A.add("battle", "MatLeaf_tea", paint(xf(head, (x, y, g + 0.14)), CABBAGE, var=0.06, ao=0.2, ao_h=0.2, ground=g, top=0.4))


def apron(A):
    """raga tea baskets, cabbage crate, terendak hat (<=0.6 m, nothing bright by the rope)."""
    weave = lambda cx, cy: (lambda v, c: c * (0.82 + 0.18 * ((np.floor(v[:, 2] * 30) + np.floor(np.arctan2(v[:, 1] - cy, v[:, 0] - cx) * 6)) % 2))[:, None])
    for k, (x, y, s, tilt) in enumerate(((-4.4, 2.9, 1.0, 0.0), (-4.95, 2.25, 0.9, 0.0), (-3.75, 3.55, 0.85, 1.2))):
        g = ground(x, y)
        raga = K.lathe([(0.0, 0.0), (0.12, 0.0), (0.2, 0.1), (0.24, 0.4), (0.25, 0.48), (0.23, 0.48), (0.21, 0.12), (0.11, 0.02), (0.0, 0.02)], seg=14)
        q = xf(xf(raga, s=s), (x, y, g + (0.2 if tilt else 0.0)), (tilt, 0, k))
        A.add("battle", "MatThatch_rattan", tint(paint(q, RATTAN, var=0.05, ao=0.4, ao_h=0.3, ground=g, top=0.2), weave(x, y)))
        if not tilt:  # fresh tea leaves heaped in the basket
            A.add("battle", "MatLeaf_tea", paint(xf(blob((0.2 * s, 0.2 * s, 0.07), sub=2, seed=k, amp=0.3, freq=4), (x, y, g + 0.45 * s)), (0.30, 0.46, 0.16), var=0.05, ao=0.0, top=0.3))
        A.contact(x, y, 0.5, 0.35)
    # terendak (conical hat) + flask
    hx, hy = 4.65, 2.35
    A.add("battle", "MatThatch_rattan", tint(paint(xf(K.caping(0.27, 0.13), (hx, hy, ground(hx, hy) + 0.02), (0.0, 0, 0.5)), (0.66, 0.54, 0.34), var=0.04, ao=0.3, ao_h=0.12, ground=ground(hx, hy), top=0.2),
                                             lambda v, c: c * (0.84 + 0.16 * ((np.floor(np.arctan2(v[:, 1] - hy, v[:, 0] - hx) * 6) + np.floor(np.hypot(v[:, 0] - hx, v[:, 1] - hy) * 40)) % 2))[:, None]))
    fx, fy = 5.1, 1.75
    A.add("battle", "MatMetal_zinc", paint(on_ground(K.lathe([(0.0, 0.0), (0.06, 0.0), (0.065, 0.2), (0.03, 0.25), (0.035, 0.29), (0.0, 0.29)], seg=10), fx, fy), (0.30, 0.40, 0.46), ao=0.3, ao_h=0.1, ground=ground(fx, fy), top=0.3))
    A.contact(hx, hy, 0.5, 0.3)
    # near-right: cabbage crate + loose cabbages + a hoe
    cx, cy = 4.4, -3.3
    g = ground(cx, cy)
    wood = []
    for sx in (-1, 1):
        wood.append(xf(K.box(0.03, 0.42, 0.34, bev=0.005), (cx + sx * 0.28, cy, g)))
    for sy in (-1, 1):
        for lv in range(3):
            wood.append(xf(K.box(0.56, 0.02, 0.08, bev=0.003), (cx, cy + sy * 0.2, g + 0.04 + lv * 0.11)))
    A.add("battle", "MatWood_timber", [paint(q, (0.56, 0.45, 0.32), var=0.08, ao=0.4, ao_h=0.3, ground=g) for q in wood])
    for j, (dx, dy, dz) in enumerate(((-0.13, -0.09, 0.3), (0.13, -0.09, 0.3), (-0.13, 0.1, 0.3), (0.13, 0.1, 0.3), (0.55, -0.35, 0.1), (0.4, 0.3, 0.1))):
        A.add("battle", "MatLeaf_tea", paint(xf(blob((0.12, 0.12, 0.11), sub=2, seed=20 + j, amp=0.15, freq=3), (cx + dx, cy + dy, g + dz)), CABBAGE, var=0.08, ao=0.3, ao_h=0.15, ground=g, top=0.35))
    A.contact(cx, cy, 0.8, 0.35)
    A.add("battle", "MatWood_timber", paint(K.tube([(cx - 0.9, cy - 0.6, g + 0.03), (cx - 0.1, cy - 0.9, g + 0.05)], 0.02, seg=5), (0.52, 0.40, 0.27), ao=0.0))


def weighing_post(A, x, y):
    """leaf-weighing tripod with a hanging dacing balance and a basket (vista foreground, <=1.2 m)."""
    g = ground(x, y)
    wood, met = [], []
    top = (x, y, g + 1.15)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        wood.append(K.tube([(x + 0.55 * math.cos(a), y + 0.45 * math.sin(a), g - 0.02), top], [0.035, 0.028], seg=5))
    wood.append(K.tube([(x - 0.42, y, g + 0.92), (x + 0.42, y, g + 0.92)], 0.016, seg=4))       # steelyard beam
    met.append(K.tube([top, (x, y, g + 0.93)], 0.006, seg=3))
    met.append(xf(K.lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.06), (0.0, 0.06)], seg=8), (x + 0.38, y, g + 0.74)))   # counterweight
    for sgn in (-1, 1):
        met.append(K.tube([(x - 0.3, y, g + 0.92), (x - 0.3 + sgn * 0.13, y, g + 0.55)], 0.005, seg=3))
    raga = K.lathe([(0.0, 0.0), (0.1, 0.0), (0.17, 0.08), (0.2, 0.33), (0.0, 0.33)], seg=12, cap1=False)
    A.add("battle", "MatThatch_rattan", paint(xf(raga, (x - 0.3, y, g + 0.22)), RATTAN, var=0.04, ao=0.3, ao_h=0.3, ground=g))
    A.add("battle", "MatLeaf_tea", paint(xf(blob((0.17, 0.17, 0.06), sub=2, seed=3, amp=0.3, freq=4), (x - 0.3, y, g + 0.55)), (0.30, 0.46, 0.16), ao=0.0, top=0.3))
    A.add("battle", "MatWood_timber", [paint(q, TIMBER, var=0.08, ao=0.3, ao_h=0.8, ground=g) for q in wood])
    A.add("battle", "MatMetal_zinc", [paint(q, (0.30, 0.28, 0.25), ao=0.0) for q in met])
    A.contact(x, y, 0.8, 0.3)


def footpath_steps(A):
    """timber steps up the red footpath that slants through the uphill rows (far band, right)."""
    rng = random.Random(8)
    wood = []
    for k in range(9):
        t = k / 8
        x, y = 4.2 + 7.0 * t, 6.4 + 2.4 * t
        g = nat_h(x, y)
        wood.append(xf(K.box(0.14, 0.8, 0.14, bev=0.02), (x, y, g - 0.06), (0, 0, 0.32 + rng.uniform(-0.1, 0.1))))
    A.add("battle", "MatWood_timber", [paint(q, TIMBER_DK, var=0.1, ao=0.3, ao_h=0.2, ground=-9) for q in wood])


# ---------------------------------------------------------------- far set
def far_set(A):
    # tea factory on the hill (white walls, rusty zinc roof)
    fx, fy = vpt(21, 112)
    g = nat_h(fx, fy)
    body = xf(K.box(16.0, 7.0, 6.5, bev=0.08), (fx, fy, g - 0.6), (0, 0, 0.35))
    roof = xf(K.box(17.0, 8.0, 0.15, bev=0.05), (fx, fy, g + 5.9), (0, 0, 0.35))
    roof.v[:, 2] += 1.8 * (1 - np.abs((roof.v[:, :2] - (fx, fy)) @ np.array([-math.sin(0.35), math.cos(0.35)])) / 4.0)
    wins = [xf(K.box(1.0, 0.1, 0.9, bev=0.02), (fx + (k - 3.5) * 1.9 * math.cos(0.35), fy + (k - 3.5) * 1.9 * math.sin(0.35) - 3.55, g + lv * 2.4 + 1.6), (0, 0, 0.35)) for k in range(8) for lv in range(2)]
    A.add("far", "MatCloth_mist", paint(body, (0.86, 0.85, 0.80), var=0.0, ao=0.3, ao_h=3, ground=g, top=0.1))
    A.add("far", "MatMetal_zinc", paint(roof, (0.54, 0.34, 0.22), var=0.04, ao=0.0, top=0.25))
    A.add("far", "MatMetal_zinc", [paint(q, (0.18, 0.18, 0.18), ao=0.0) for q in wins])
    rng = random.Random(31)
    for k in range(3):   # silver-oak shade trees dotted over the far hill
        yaw, d = rng.uniform(26, 38), rng.uniform(45, 90)
        x, y = vpt(yaw, d)
        if u_of(x, y) < 8:
            continue
        shade_tree(A, x, y, rng.uniform(8, 11), 70 + k, set_="far")
    # layered misty ridges (dark near -> pale far), mist banks lying in the valleys, clouds
    ridge = lambda base, amp, s1, s2, sd: (lambda yaw: base + amp * (0.6 + 0.4 * math.sin(math.radians(yaw) * s1 + sd)) * (0.75 + 0.25 * math.sin(math.radians(yaw) * s2 + 2 * sd)) + 0.08 * amp * nz(yaw * 0.08, sd, 0, 1, 3))
    layers = ((125, -56, 30, ridge(8, 22, 5, 13, 1), (0.10, 0.20, 0.10), (0.16, 0.28, 0.14)),
              (185, -56, 46, ridge(16, 34, 4, 11, 2), (0.14, 0.24, 0.16), (0.22, 0.32, 0.22)),
              (265, -56, 46, ridge(26, 48, 3, 9, 3), (0.22, 0.30, 0.27), (0.30, 0.38, 0.35)),
              (380, -56, 46, ridge(42, 62, 2.5, 7, 4), (0.32, 0.40, 0.42), (0.40, 0.47, 0.50)))
    for k, (rr, a0, a1, fn, lo, hi) in enumerate(layers):
        A.add("far", "MatRock_stone", paint_band(band(rr, a0, a1, fn, 30 + 10 * k, n=70 + 10 * k), lo, hi, -4, 60, seed=k, namp=0.08, ns=0.03))
    for k, (yaw, d, z, w, hh) in enumerate(((-30, 155, 1, 140, 9), (-8, 225, 8, 170, 11), (12, 320, 18, 210, 14), (-40, 330, 16, 180, 12))):
        cx, cy = vpt(yaw, d)
        sheet = blob((w * 0.5, w * 0.16, hh * 0.5), sub=2, seed=40 + k, amp=0.12, freq=2.0)
        sheet.v[:, 2] = np.maximum(sheet.v[:, 2], -hh * 0.15)
        A.add("far", "MatCloth_mist", paint(xf(sheet, (cx, cy, z), (0, 0, math.radians(-yaw))), (0.93, 0.94, 0.92), var=0.02, ao=0.0, top=0.08))
    for k, (yaw, d, z, w, h) in enumerate(((2, 540, 110, 150, 40), (-26, 520, 90, 110, 34), (30, 500, 120, 120, 36))):
        A.add("far", "MatCloth_mist", relief_cloud(yaw, d, z, w, h, seed=k + 40, top=(0.96, 0.96, 0.94), bot=(0.74, 0.78, 0.80)))
    A.add("far", "MatGround_redsoil", skirt(240, 1100, -56, 48, -4.2, (0.24, 0.34, 0.20)))


# ---------------------------------------------------------------- build
def build(A):
    for name in ("MatGround_redsoil", "MatGrass_bank", "MatLeaf_tea", "MatRock_stone", "MatWood_timber", "MatMetal_zinc",
                 "MatThatch_rattan", "MatCloth_mist"):
        A.mat(name)

    stone_wall(A)
    farm_shed(A, -9.0, 1.6)
    cabbage_beds(A)
    apron(A)
    footpath_steps(A)
    weighing_post(A, 0.6, -7.2)
    for k, (x, y, h) in enumerate(((8.6, 2.6, 3.3), (10.6, -0.4, 2.7), (12.4, 4.6, 3.6), (9.4, 8.6, 3.0))):
        tree_fern(A, x, y, h, seed=10 + k)
    shade_tree(A, 8.0, 11.5, 9.5, seed=3)

    sp = lambda r: 0.3 if r < 12 else (0.3 + 0.07 * (r - 12) if r < 22 else (1.2 + 0.09 * (r - 22) if r < 80 else min(16.0, 6.4 + 0.2 * (r - 80))))
    A.terrain(ground, gcolor, kind=gkind, rin=4.5, rout=240.0, split=23.0, spacing=sp, cull=gcull, seed=3)
    tea_rows(A)

    # scatter: grass on the embankment + terrace rim + path verges
    rng = random.Random(3)
    for k in range(60):
        y = rng.uniform(-8.0, 6.0)
        x = -TX - rng.uniform(0.3, 1.6)
        A.scatter_patch("Grass", 30, x, y, rng.uniform(0.4, 0.8), ground, (0.40, 0.50, 0.22), seed=k)
    for k in range(30):
        y = rng.uniform(-6.0, 4.0)
        x = rng.choice((-1, 1)) * rng.uniform(5.8, 6.3)
        if math.hypot(x, y) < 5.8:
            continue
        A.scatter_patch("Grass", 24, x, y, rng.uniform(0.25, 0.5), ground, (0.42, 0.52, 0.22), seed=60 + k)
    for k in range(12):   # grass along the footpath through the rows
        t = rng.uniform(0, 1)
        A.scatter_patch("Grass", 20, 4.2 + 7.0 * t + 0.5, 6.4 + 2.4 * t - 0.3, 0.35, ground, (0.40, 0.50, 0.22), seed=100 + k)
    far_set(A)


if __name__ == "__main__":
    KD.flatten_preview_ground()
    K.main("pahang", build, MOOD)
