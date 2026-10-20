"""Sarawak arena -- Gawai night on the tanju of an Iban longhouse by the river (design_art.md section c;
USER_SPEC: a long communal longhouse on stilts, families gathered along its length, harvest preparations).
Ground: tanju deck of belian planks with dark gaps around the dish (collar beam hides the plank ends).
Apron: padi heap on a tikai mat + winnowing tray, small gongs + pansoh bamboo, folded pua + rice cakes + tuak jar.
Far band: the longhouse ruai running across the whole band (posts, pua kumbu hangings, lit bilik doors,
atap roof), padi drying on mats, tajau jars.
Left flank: kenyalang (hornbill) carved pole + tajau cluster. Right flank: gong rack + bamboo torches
(Glow + KHR point lights), flames and hangings leaning downwind (+x, mild gust hazard).
Far set (vista): longhouse continuing on stilts with lamp-lit windows, sago palms, layered rainforest
ridges with emergent crowns, moon + night clouds.

  blender -b --factory-startup -P art_src/arena_sarawak.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)
import numpy as np
from arenakit import P, xf, join, paint, tint, nz, smooth01

# Godot ARENA_DEFS["sarawak"] recommendation (+ b_* = Blender preview factors only)
MOOD = {"sky_top": (0.03, 0.05, 0.13), "sky_horizon": (0.16, 0.22, 0.38), "fog": (0.10, 0.14, 0.24),
        "fog_density": 0.006, "sun_color": (0.58, 0.68, 1.0), "sun_energy": 0.4,
        "lantern": (1.0, 0.58, 0.28), "lantern_energy": 2.0, "exposure": 1.15, "ambient": 0.35,
        "b_sun": 1.0, "b_world": 0.5, "b_fill": 0.15, "b_lantern": 14.0}

# ---------------------------------------------------------------- palette (sRGB)
BELIAN = (0.40, 0.31, 0.23)
BELIAN_LT = (0.50, 0.39, 0.28)
BELIAN_DK = (0.24, 0.18, 0.13)
BAMBOO = (0.62, 0.55, 0.35)
ATAP = (0.42, 0.34, 0.24)
EARTH = (0.24, 0.20, 0.16)
GRASS_T = (0.30, 0.40, 0.20)
FOREST = (0.10, 0.17, 0.14)
BRASS = (0.74, 0.56, 0.26)
GLAZE = (0.30, 0.24, 0.14)
PADI = (0.78, 0.62, 0.30)
MAT = (0.62, 0.52, 0.34)
PUA_COLS = ((0.52, 0.10, 0.07), (0.08, 0.06, 0.05), (0.72, 0.46, 0.18), (0.84, 0.78, 0.64))   # red, black, ochre, cream

# ---------------------------------------------------------------- layout
DECK_Z = -0.01
DECK = (-15.0, 15.0, -6.6, 6.3)      # x0, x1, y0, y1 (tanju)
RUAI_Y0, RUAI_Y1, RUAI_Z = 6.3, 10.9, 0.28
ROOF_EAVE, ROOF_RISE = 2.55, 3.1
LH_X = (-23.0, 6.0)                  # battle-set longhouse span: its carved gable end at x=6 opens the vista's right
PLANE = 22.5                         # main.tscn Ground plane at y=-0.5 covers +-22 m: stay above it inside
RIVER_Y = (15.0, 24.2)               # moonlit river behind the longhouse (seen past the gable end in the vista)
WZ = -0.40                           # river surface (above the Ground plane, which it hides)
FAR_RUN = (9.0, 40.0, 18.7, 1.9)     # far longhouse run on stilts across the river: x0, x1, y offset, lift
MOON = (44.0, 96.0, 27.0, 4.2)       # its path on the river falls right of the gable end
VEYE = K.VISTA_EYE


def in_vista(x, y):
    dx, dy = x + 1.5, y + 12.5
    return dy > 2 and -58 < math.degrees(math.atan2(dx, dy)) < 44


def visible(x, y, pad=0.0):
    return (y > -6.5 - pad and abs(x) < 11 + 0.55 * (y + 6.5) + pad) or in_vista(x, y)


def ground(x, y):
    h = -0.45 + 0.03 * nz(x, y, 0, 0.5, 3)
    if y > RIVER_Y[0]:   # river channel (under the water sheet), then the far bank rising into the forest
        b = smooth01(RIVER_Y[1] - 0.6, RIVER_Y[1] + 2.5, y)
        return (h - 0.35 * smooth01(RIVER_Y[0] + 0.2, RIVER_Y[0] + 1.0, y) + 1.2 * b + 0.03 * max(0.0, y - RIVER_Y[1] - 2.5)
                + 0.3 * b * nz(x, y, 0, 0.08, 4))
    if abs(x) < PLANE and abs(y) < PLANE:
        return max(h, -0.44)
    # outside the plane square: down toward the river on the right, gentle forest floor elsewhere
    d = max(abs(x), abs(y)) - PLANE
    h -= 1.6 * smooth01(0.0, 8.0, d) + 0.4 * nz(x, y, 0, 0.06, 4)
    return h


def gcolor(x, y, z):
    n1 = nz(x, y, 0, 0.5, 11)
    n2 = nz(x, y, 0, 2.0, 12)
    c = np.array(EARTH) * (1 + 0.15 * n1 + 0.08 * n2)
    g = smooth01(-0.1, 0.5, nz(x, y, 0, 0.3, 13))
    c = c * (1 - 0.6 * g) + np.array(GRASS_T) * 0.6 * g
    if y > RIVER_Y[0] - 1.5:   # wet, dark river banks
        c = c * (1 - 0.35 * smooth01(1.8, 0.0, min(abs(y - RIVER_Y[0]), abs(y - RIVER_Y[1]))))
    return tuple(c)


def gcull(cx, cy, zmax):
    if DECK[0] + 0.4 < cx < DECK[1] - 0.4 and DECK[2] + 0.4 < cy < DECK[3] - 0.2:   # hidden under the deck
        return True
    if DECK[0] + 0.4 < cx < LH_X[1] - 0.4 and DECK[3] - 0.4 < cy < RUAI_Y1 - 0.2:   # ... and the ruai
        return True
    if -30 < cx < 46 and RIVER_Y[0] + 0.6 < cy < RIVER_Y[1] - 0.4 and zmax < WZ:   # under the river sheet
        return True
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def mix(a, b, t):
    return np.asarray(a, dtype=float) * (1 - t) + np.asarray(b, dtype=float) * t


def face_cam(p, x, y, z, cam=(-1.5, -12.5)):
    rz = math.atan2(x - cam[0], y - cam[1])
    return xf(p, (x, y, z), (0, 0, -rz))


# ---------------------------------------------------------------- local helpers (kit is frozen)
def cells(grid, colfn):
    """per-face quads (unique verts -> crisp woven-motif colours). grid[i][j] = (x, y, z)."""
    v, f, c = [], [], []
    R, C = len(grid) - 1, len(grid[0]) - 1
    for i in range(R):
        for j in range(C):
            b = len(v)
            v += [grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]]
            f.append((b, b + 1, b + 2, b + 3))
            c += [list(colfn(i, j, R, C)) + [1.0]] * 4
    return P(v, f, c)


def pua_motif(i, j, R, C, seed=0):
    """pua kumbu: 2-cell black outline, red/ochre tooth band, then nested hooked lozenges drawn in continuous
    u,v (three stacked per hanging): d = |u-.5|*2 + |frac(3v)-.5|*2 quantised into 5 bands."""
    red, blk, och, crm = PUA_COLS
    e = min(i, j, R - 1 - i, C - 1 - j)
    if e < 2:
        return blk
    if e == 2:
        return och if (i + j + seed) % 2 else red
    u, v = (j + 0.5) / C, (i + 0.5) / R
    d = abs(u - 0.5) * 2 + abs((v * 3 + 0.5 * (seed % 2)) % 1.0 - 0.5) * 2
    b = min(4, int(d * 2.5))
    if b in (2, 4) and (d * 2.5) % 1.0 < 0.3 and (i + 2 * j + seed) % 4 == 0:
        b -= 1   # hooks: dark spurs off each outline
    return (crm, blk, red, blk, och)[b]


def pua(w, h, seed=0, nx=24, ny=36, sway=0.25):
    """pua kumbu hanging from a beam: top edge at z=0 along x, hangs down, bellies downwind (+x) and toward -y."""
    g = []
    for i in range(ny + 1):
        t = i / ny
        row = []
        for j in range(nx + 1):
            u = j / nx
            x = (u - 0.5) * w + sway * t * t
            y = -0.06 * math.sin(math.pi * u) * t - 0.05 * math.sin(u * 7 + seed) * t
            row.append((x, y, -h * t))
        g.append(row)
    g = g[::-1]  # rows bottom -> top so faces point -y
    return cells(g, lambda i, j, R, C: pua_motif(i, j, R, C, seed))


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
            v.append((x, -puff * (top - bot) * math.sin(math.pi * (0.2 + 0.8 * t)) * (1 - e * e), bot + (top - bot) * t))
    for j in range(cols):
        for i in range(rows):
            a_ = j * (rows + 1) + i
            f.append((a_, a_ + rows + 1, a_ + rows + 2, a_ + 1))
    return P(v, f)


def ridge(x0, x1, yc_fn, crest_fn, depth=40.0, foot=-15.0, cols=64, seed=0):
    """layered backdrop ridge with a tree-crown bumpy crest (heightfield strip across x)."""
    v, f = [], []
    prof = [(-0.5, 0.0), (-0.22, 0.72), (0.0, 1.0), (0.2, 0.8), (0.5, 0.0)]
    for j in range(cols + 1):
        x = x0 + (x1 - x0) * j / cols
        yc = yc_fn(x)
        zc = crest_fn(x) + 1.6 * abs(math.sin(x * 0.45 + seed)) + 1.0 * abs(math.sin(x * 1.1 + 2 * seed))
        for (o, k) in prof:
            v.append((x, yc + o * depth, foot + (zc - foot) * (k ** 0.8)))
    m = len(prof)
    for j in range(cols):
        for i in range(m - 1):
            a = j * m + i
            f.append((a, a + m, a + m + 1, a + 1))
    return P(v, f)


def smooth_blob(r, seed=0, seg=16, rings=9, amp=0.1, squash=0.72):
    o = seed * 1.37
    prof = [(r * math.sin(math.pi * k / (rings - 1)), -r * squash * math.cos(math.pi * k / (rings - 1))) for k in range(rings)]
    p = K.lathe(prof, seg=seg, cap0=False, cap1=False,
                rfn=lambda a, t: 1.0 + amp * math.sin(a * 3 + o) * math.sin(t * 5 + o) + amp * 0.6 * math.sin(a * 5 - o * 2))
    p.v[:, 2] += r * squash * 0.55
    return p


# ---------------------------------------------------------------- the tanju deck
def deck(A):
    """belian plank deck with dark gaps, staggered joints, clipped around the dish + a collar beam."""
    rng = random.Random(7)
    pw, gap = 0.2, 0.035
    x0, x1, y0, y1 = DECK
    boards = []
    y = y0 + pw / 2
    row = 0
    while y < y1:
        ya, yb = y - pw / 2, y + pw / 2
        near = min(abs(ya), abs(yb)) if ya * yb > 0 else 0.0
        hole = math.sqrt(max(0.0, 4.56 ** 2 - near ** 2)) if near < 4.56 else 0.0
        spans = [(x0, -hole), (hole, x1)] if hole > 0 else [(x0, x1)]
        for (a, b) in spans:
            x = a - rng.uniform(0.0, 3.0) * (row % 2)
            while x < b - 0.05:
                L = rng.uniform(2.4, 4.6)
                xa, xb = max(x, a), min(x + L, b)
                if xb - xa > 0.15 and (visible((xa + xb) / 2, y, pad=3.0) or visible(xa, y, pad=3.0)):
                    p = K.box(xb - xa - 0.02, pw, 0.05, bev=0.0)
                    p = xf(p, ((xa + xb) / 2, y, DECK_Z - 0.05 + rng.uniform(-0.006, 0.006)), (rng.uniform(-0.004, 0.004), 0, rng.uniform(-0.002, 0.002)))
                    k = rng.uniform(0.8, 1.15)
                    col = BELIAN_LT if rng.random() < 0.18 else (BELIAN_DK if rng.random() < 0.12 else BELIAN)
                    paint(p, tuple(np.array(col) * k), var=0.0, ao=0.0, top=0.0, namp=0.12, ns=2.5, stretch=(0.15, 1, 1))
                    boards.append(p)
                x += L
        y += pw + gap
        row += 1
    A.add("battle", "MatWood_belian", boards)
    # collar beam around the dish (hides the clipped plank ends)
    col = K.lathe([(4.95, -0.12), (4.95, 0.0), (4.86, 0.03), (4.6, 0.03), (4.52, 0.0), (4.52, -0.12)], seg=96, cap0=False, cap1=False)
    A.add("battle", "MatWood_belian", paint(col, BELIAN_DK, var=0.0, ao=0.0, top=0.2, namp=0.15, ns=3))
    # joists + edge beams + posts along the visible deck edges
    wood = []
    for xx in np.arange(x0 + 0.6, x1, 2.4):
        wood.append(xf(K.box(0.14, y1 - y0 + 0.2, 0.16, bev=0.0), (xx, (y0 + y1) / 2, DECK_Z - 0.22)))
    wood.append(xf(K.box(x1 - x0 + 0.3, 0.16, 0.2, bev=0.02), ((x0 + x1) / 2, y0 - 0.06, DECK_Z - 0.2)))
    wood.append(xf(K.box(x1 - LH_X[1] + 0.2, 0.16, 0.2, bev=0.02), ((LH_X[1] + x1) / 2, y1 + 0.02, DECK_Z - 0.2)))  # open back edge past the gable
    for xx in np.arange(LH_X[1] + 1.0, x1, 2.4):
        wood.append(xf(K.post(0.6, 0.09, seed=int(xx * 5), seg=6, lean=0.01), (xx, y1 - 0.05, -0.5)))
    for xx in np.arange(x0 + 0.4, x1, 2.4):
        wood.append(xf(K.post(0.6, 0.09, seed=int(xx * 3), seg=6, lean=0.01), (xx, y0 + 0.05, -0.5)))
    A.add("battle", "MatWood_belian", [paint(q, BELIAN_DK, var=0.08, ao=0.4, ao_h=0.3, ground=-0.45) for q in wood])


def tangga(A, x, y):
    """notched-log ladder from the tanju edge down to the courtyard (camera side)."""
    p = K.tube([(x, y - 1.3, -0.48), (x, y - 0.1, DECK_Z + 0.02)], [0.16, 0.14], seg=8)
    paint(p, BELIAN, var=0.0, ao=0.3, ao_h=0.4, ground=-0.45, namp=0.2, ns=3)
    tint(p, lambda v, c: c * (0.7 + 0.3 * (np.floor((v[:, 2] + 0.5) * 7) % 2))[:, None])  # notches
    A.add("battle", "MatWood_belian", p)


# ---------------------------------------------------------------- longhouse
def longhouse(A, xa, xb, set_="battle", oy=0.0, lift=0.0):
    """ruai gallery + bilik wall + atap roof running along x, carved upturned finials at both gable ends.
    Battle part: detailed (framed bilik doors opening on lamp-lit rooms, pelita under the eave); far part:
    lighter, on stilts. oy/lift move a far run back/up (stilts reach the ground at the moved spot)."""
    battle = set_ == "battle"
    out = []                      # (material, piece) in local coords; moved by (0, oy, lift) at the end
    wood, glow, metal = [], [], []
    L = xb - xa
    xm = (xa + xb) / 2
    floor_z = RUAI_Z
    # ruai floor (raised step above the tanju) + front sill beam
    wood.append(xf(K.box(L, RUAI_Y1 - RUAI_Y0 + 0.2, 0.12, bev=0.02), (xm, (RUAI_Y0 + RUAI_Y1) / 2, floor_z - 0.12)))
    wood.append(xf(K.box(L, 0.2, 0.3, bev=0.025), (xm, RUAI_Y0, DECK_Z - 0.02)))
    # front posts + eave beam; a pelita hangs under the eave between every pair of posts
    step = 2.4
    for xx in np.arange(xa + 0.6, xb, step):
        wood.append(xf(K.box(0.2, 0.2, ROOF_EAVE - floor_z + 0.1, bev=0.025), (xx, RUAI_Y0 + 0.25, floor_z - 0.05)))
    wood.append(xf(K.box(L, 0.18, 0.2, bev=0.02), (xm, RUAI_Y0 + 0.25, ROOF_EAVE - 0.15)))
    for xx in np.arange(xa + 1.8, xb - 0.5, step):
        glow.append(xf(K.lathe([(0, 0), (0.06, 0.0), (0.075, 0.07), (0.035, 0.13), (0, 0.14)], seg=6), (xx, RUAI_Y0 - 0.12, ROOF_EAVE - 0.62)))
        if battle:
            metal.append(K.tube([(xx, RUAI_Y0 - 0.12, ROOF_EAVE - 0.48), (xx, RUAI_Y0 - 0.12, ROOF_EAVE + 0.1)], 0.006, seg=3))
    # bilik wall, cut around the doors
    wall_h = ROOF_EAVE + 0.9 - floor_z
    DW, DH = 0.9, 1.75
    doors = list(np.arange(xa + 3.0, xb - 1.0, 6.0))
    edges = [xa] + [e for d in doors for e in (d - DW / 2 - 0.06, d + DW / 2 + 0.06)] + [xb]
    walls = [xf(K.box(e1 - e0, 0.12, wall_h, bev=0.01), ((e0 + e1) / 2, RUAI_Y1, floor_z)) for e0, e1 in zip(edges[::2], edges[1::2]) if e1 - e0 > 0.05]
    walls += [xf(K.box(DW + 0.12, 0.12, wall_h - DH - 0.06, bev=0.01), (d, RUAI_Y1, floor_z + DH + 0.06)) for d in doors]
    stripes = lambda v, c: c * (0.86 + 0.14 * (np.floor((v[:, 0] + 100) * 4.2) % 2))[:, None]
    out += [("MatWood_belian", tint(paint(w, BELIAN, var=0.0, ao=0.45, ao_h=2.5, ground=floor_z), stripes)) for w in walls]
    room, frame, bilik = [], [], []
    lamp_z = floor_z + 1.3
    for d in doors:
        # carved frame (jambs, lintel, sill) + a dark leaf swung half open into the bilik
        frame += [xf(K.box(0.09, 0.16, DH + 0.1, bev=0.012), (d + sx * (DW / 2 + 0.03), RUAI_Y1 - 0.03, floor_z)) for sx in (-1, 1)]
        frame.append(xf(K.box(DW + 0.3, 0.18, 0.12, bev=0.015), (d, RUAI_Y1 - 0.04, floor_z + DH)))
        frame.append(xf(K.box(DW + 0.1, 0.2, 0.05, bev=0.01), (d, RUAI_Y1 - 0.03, floor_z)))
        leaf = xf(K.box(DW - 0.04, 0.05, DH - 0.04, bev=0.008), (-(DW - 0.04) / 2, 0, 0))
        out.append(("MatWood_belian", paint(xf(leaf, (d + DW / 2, RUAI_Y1 + 0.03, floor_z + 0.02), (0, 0, -0.95)), (0.11, 0.08, 0.06), var=0.0, ao=0.0, top=0.0)))
        if battle:  # a dim room 2 m deep, lit by a pelita hanging ~1.6 m in
            back = xf(K.grid(1.8, 2.1, 6, 6), (d, RUAI_Y1 + 1.97, floor_z + 1.05), (math.pi / 2, 0, 0))   # faces the door
            bilik.append(tint(paint(back, (0.62, 0.34, 0.15), ao=0.0, top=0.0),   # warm pool of lamplight on the back wall
                              lambda v, c, d=d: c * (0.3 + 0.7 * np.exp(-((v[:, 2] - lamp_z) ** 2 + (v[:, 0] - d + 0.15) ** 2) / 0.5))[:, None]))
            for q in (xf(K.box(0.06, 2.0, 2.1, bev=0.0), (d - 0.9, RUAI_Y1 + 1.0, floor_z)), xf(K.box(0.06, 2.0, 2.1, bev=0.0), (d + 0.9, RUAI_Y1 + 1.0, floor_z)),
                      xf(K.box(1.8, 2.0, 0.04, bev=0.0), (d, RUAI_Y1 + 1.0, floor_z - 0.04)), xf(K.box(1.8, 2.0, 0.04, bev=0.0), (d, RUAI_Y1 + 1.0, floor_z + 2.1))):
                room.append(tint(paint(q, (0.34, 0.20, 0.11), var=0.0, ao=0.0, top=0.0),
                                 lambda v, c: c * (0.3 + 0.7 * smooth01(RUAI_Y1, RUAI_Y1 + 1.9, v[:, 1]))[:, None]))
            glow.append(xf(K.lathe([(0, 0), (0.07, 0.0), (0.09, 0.09), (0.045, 0.17), (0, 0.18)], seg=8), (d - 0.15, RUAI_Y1 + 1.6, lamp_z)))
            metal.append(K.tube([(d - 0.15, RUAI_Y1 + 1.6, lamp_z + 0.17), (d - 0.15, RUAI_Y1 + 1.6, floor_z + 2.1)], 0.006, seg=3))
        else:       # far run: the lit doorway itself
            glow.append(xf(K.box(DW, 0.06, DH, bev=0.0), (d, RUAI_Y1 + 0.02, floor_z + 0.02)))
    out += [("MatWood_belian", paint(q, BELIAN_LT, var=0.06, ao=0.3, ao_h=1.0, ground=floor_z, namp=0.1, ns=4)) for q in frame]
    out += [("MatWood_belian", q) for q in room] + [("MatGlow_bilik", q) for q in bilik]
    # roof: atap over the ruai + bilik, ridge along x
    depth = RUAI_Y1 - RUAI_Y0 + 4.6
    yc = RUAI_Y0 + depth / 2 + 0.1
    over = 0.3 if battle else 0.5
    if battle:
        roof = xf(K.thatch_roof(L, depth, ROOF_RISE, courses=7, over=over, seed=11, tooth=0.07, cw=0.28), (xm, yc, ROOF_EAVE))
        course = lambda v, c: c * (0.8 + 0.24 * (np.floor((v[:, 2] - ROOF_EAVE) * 7.0 / ROOF_RISE + 0.5) % 2))[:, None]
        out.append(("MatThatch_atap", tint(paint(roof, ATAP, var=0.04, ao=0.0, top=0.3, namp=0.25, ns=2.5, stretch=(6, 6, 0.4)), course)))
    else:
        roof = xf(K.thatch_roof(L, depth, ROOF_RISE, courses=2, over=over, seed=12, tooth=0.05, cw=1.2), (xm, yc, ROOF_EAVE))
        out.append(("MatWood_belian", paint(roof, (0.30, 0.25, 0.19), var=0.04, ao=0.0, top=0.3, namp=0.2, ns=0.5)))
    # gable/back: dark infill under the roof behind the eave beam (no see-through) + gable end triangles
    dark = [P([(xa, RUAI_Y0 + 0.3, ROOF_EAVE), (xb, RUAI_Y0 + 0.3, ROOF_EAVE), (xb, yc, ROOF_EAVE + ROOF_RISE - 0.1), (xa, yc, ROOF_EAVE + ROOF_RISE - 0.1)], [(0, 1, 2, 3)])]
    half = depth / 2 + over
    rz_ = ROOF_EAVE + ROOF_RISE
    finials = []
    for sx, xe in ((-1, xa - over), (1, xb + over)):
        xw = xe - sx * (over + 0.02)
        dark.append(P([(xw, yc - half + over, ROOF_EAVE), (xw, yc + half - over, ROOF_EAVE), (xw, yc, rz_ - 0.05)], [(0, 1, 2)]))
        # carved barge boards along both rakes, crossing at the ridge and curling up and out (upturned horns)
        for side in (-1, 1):
            path = [(xe, yc + side * half, ROOF_EAVE - 0.06), (xe, yc + side * half * 0.5, ROOF_EAVE + ROOF_RISE * 0.5 + 0.04), (xe, yc, rz_ + 0.08),
                    (xe + sx * 0.1, yc - side * 0.32, rz_ + 0.5), (xe + sx * 0.26, yc - side * 0.5, rz_ + 0.95), (xe + sx * 0.4, yc - side * 0.34, rz_ + 1.3)]
            finials.append(K.tube(path, [0.09, 0.09, 0.09, 0.08, 0.06, 0.02], seg=6))
    out.append(("MatWood_belian", paint(K.dbl(join(dark)), (0.06, 0.05, 0.04), var=0.0, ao=0.0, top=0.0)))
    carve = lambda v, c: np.where(((v[:, 2] - ROOF_EAVE) % 0.45 < 0.09)[:, None], np.array([[0.62, 0.14, 0.08, 1]]), c)
    out += [("MatWood_belian", tint(paint(q, BELIAN_DK, var=0.0, ao=0.0, top=0.3, namp=0.1, ns=4), carve)) for q in finials]
    if not battle:  # stilts (down to the ground at the moved spot) + lit windows
        for xx in np.arange(xa + 1.0, xb, 3.0):
            for yy in (RUAI_Y0 + 0.2, RUAI_Y1, RUAI_Y1 + 4.0):
                gz = ground(xx, yy + oy) - lift
                wood.append(K.tube([(xx, yy, gz - 0.2), (xx, yy, floor_z)], 0.1, seg=4))
        for xx in np.arange(xa + 1.5, xb - 0.5, 4.0):
            glow.append(xf(K.box(0.7, 0.06, 0.6, bev=0.0), (xx, RUAI_Y0 + 0.15, floor_z + 1.0)))
    out += [("MatWood_belian", paint(q, BELIAN if i % 3 else BELIAN_DK, var=0.08, ao=0.4, ao_h=1.5, ground=floor_z, namp=0.1, ns=3, stretch=(1, 1, 0.2)))
            for i, q in enumerate(wood)]
    out += [("MatGlow_torch", q if q.c is not None else paint(q, (0.80, 0.50, 0.24), ao=0.0, top=0.0)) for q in glow]
    out += [("MatMetal_brass", paint(q, (0.3, 0.3, 0.3), ao=0.0)) for q in metal]
    for name, q in out:
        A.add(set_, name, xf(q, (0, oy, lift)) if (oy or lift) else q)


def ruai_dressing(A):
    """pua kumbu hangings on the eave beam (bellying downwind), gongs, padi mats, baskets, tajau in the ruai."""
    rng = random.Random(21)
    for k, xx in enumerate((-9.6, -4.8, 2.4)):
        w = rng.uniform(1.3, 1.7)
        p = pua(w, rng.uniform(1.4, 1.8), seed=k, sway=0.18 + 0.1 * k % 2)
        A.add("battle", "MatCloth_pua", xf(p, (xx + 1.2, RUAI_Y0 + 0.12, ROOF_EAVE - 0.26)))
    # padi drying on mats along the tanju edge of the ruai (Gawai preparations)
    for k, (x, y, rz) in enumerate(((-5.6, 5.0, 0.05), (-1.8, 5.3, -0.04), (5.4, 5.1, 0.08))):
        m = xf(K.box(2.4, 1.3, 0.02, bev=0.004), (x, y, DECK_Z), (0, 0, rz))
        paint(m, MAT, var=0.03, ao=0.0, top=0.0)
        tint(m, lambda v, c: c * (0.86 + 0.14 * ((np.floor(v[:, 0] * 11) + np.floor(v[:, 1] * 11)) % 2))[:, None])
        A.add("battle", "MatThatch_atap", m)
        heap = K.lathe([(0.0, 0.0), (0.95, 0.0), (0.7, 0.04), (0.3, 0.07), (0.0, 0.075)], seg=16,
                       rfn=lambda a, t: 1.0 + 0.12 * math.sin(a * 3 + k))
        heap.v[:, 1] *= 0.48
        A.add("battle", "MatThatch_atap", paint(xf(heap, (x, y, DECK_Z + 0.02), (0, 0, rz)), PADI, var=0.04, ao=0.0, top=0.3, namp=0.1, ns=6))
    for k, (x, y) in enumerate(((3.6, 5.5), (-7.6, 5.4))):
        A.add("battle", "MatThatch_atap", paint(xf(K.basket(0.22, 0.32), (x, y, DECK_Z)), (0.52, 0.40, 0.25), ao=0.4, ao_h=0.3, ground=DECK_Z))
    # tajau in the ruai, against the bilik wall
    for k, x in enumerate((-12.4, -6.9, 5.2, -0.6)):
        tajau(A, x, RUAI_Y1 - 0.55, RUAI_Z, 0.62 + 0.08 * (k % 2), seed=k)


def tajau(A, x, y, z, h=0.75, seed=0):
    """glazed dragon jar: dark brown-green glaze, lighter dragon band, lug ring at the shoulder."""
    r = h * 0.36
    prof = [(0.0, 0.0), (r * 0.62, 0.0), (r * 0.95, h * 0.3), (r, h * 0.55), (r * 0.82, h * 0.78), (r * 0.48, h * 0.9),
            (r * 0.5, h), (r * 0.42, h), (r * 0.38, h * 0.93), (0.0, h * 0.9)]
    p = K.lathe(prof, seg=18, cap0=False, cap1=False)
    p = xf(p, (x, y, z))
    paint(p, GLAZE, var=0.06, ao=0.35, ao_h=0.25, ground=z, top=0.35)
    band = lambda v, c: c * np.where(((v[:, 2] - z) > h * 0.42) & ((v[:, 2] - z) < h * 0.7), 1.0 + 0.55 * (0.5 + 0.5 * np.sin(np.arctan2(v[:, 1] - y, v[:, 0] - x) * 5 + (v[:, 2] - z) * 14)), 1.0)[:, None]
    A.add("battle", "MatTile_glaze", tint(p, band))
    lugs = [xf(K.box(0.07, 0.04, 0.05, bev=0.012), (x + r * 0.86 * math.cos(a), y + r * 0.86 * math.sin(a), z + h * 0.74), (0, 0, a)) for a in np.linspace(0, 2 * math.pi, 5)[:4]]
    A.add("battle", "MatTile_glaze", paint(join(lugs), (0.36, 0.30, 0.18), ao=0.0))


def gong(r=0.32, boss=0.08, depth=0.09):
    """bossed gong (tawak/bebendai) facing -y, centred at origin."""
    p = K.lathe([(0.0, boss * 0.9), (boss, boss * 0.6), (boss * 1.2, 0.02), (r * 0.9, 0.0), (r, -depth * 0.3), (r, -depth), (r * 0.94, -depth)], seg=20, cap0=False, cap1=False)
    return xf(p, (0, 0, 0), (math.pi / 2, 0, 0))


def gong_rack(A, x, y, rz):
    """gong rack on the right flank: two carved posts + crossbeam, three hanging tawak, a row of engkerumong."""
    wood, metal, rope = [], [], []
    W, H = 2.6, 1.9
    for sx in (-1, 1):
        wood.append(xf(K.box(0.14, 0.14, H, bev=0.02), (sx * W / 2, 0, DECK_Z)))
        wood.append(xf(K.lathe([(0, 0), (0.1, 0), (0.12, 0.08), (0.05, 0.2), (0, 0.24)], seg=8), (sx * W / 2, 0, DECK_Z + H)))
        wood.append(xf(K.box(0.5, 0.4, 0.08, bev=0.02), (sx * W / 2, 0, DECK_Z)))
    wood.append(xf(K.box(W + 0.4, 0.12, 0.14, bev=0.02), (0, 0, DECK_Z + H - 0.2)))
    for k, (gx, gr) in enumerate(((-0.8, 0.3), (0.0, 0.36), (0.82, 0.28))):
        cz = DECK_Z + H - 0.55 - gr
        metal.append(xf(gong(gr, 0.08, 0.1), (gx, -0.02, cz)))
        rope.append(K.tube([(gx - 0.1, 0, DECK_Z + H - 0.2), (gx, -0.02, cz + gr), (gx + 0.1, 0, DECK_Z + H - 0.2)], 0.008, seg=3))
    # engkerumong: a low frame with a row of small bossed gongs (facing up)
    wood.append(xf(K.box(1.8, 0.4, 0.22, bev=0.02), (0.2, -1.0, DECK_Z)))
    for k in range(6):
        metal.append(xf(xf(gong(0.12, 0.04, 0.05), (0, 0, 0), (-math.pi / 2, 0, 0)), (-0.45 + 0.26 * k, -1.0, DECK_Z + 0.32)))
    A.add("battle", "MatWood_belian", [paint(xf(q, (x, y, 0), (0, 0, rz)), BELIAN_DK if i % 2 else BELIAN, var=0.08, ao=0.4, ao_h=0.6, ground=DECK_Z, namp=0.1, ns=3) for i, q in enumerate(wood)])
    A.add("battle", "MatMetal_brass", [paint(xf(q, (x, y, 0), (0, 0, rz)), BRASS, var=0.06, ao=0.0, top=0.15) for q in metal])
    A.add("battle", "MatCloth_pua", [paint(xf(q, (x, y, 0), (0, 0, rz)), (0.52, 0.10, 0.07), ao=0.0) for q in rope])


def torch(A, x, y, h=2.2, watts=36.0, lean=0.12, light=True):
    """bamboo torch: pole, woven cup, flame leaning downwind (+x); Glow + optional KHR point light."""
    gz = DECK_Z
    A.add("battle", "MatWood_belian", paint(K.tube([(x, y, gz), (x + 0.02, y, gz + h * 0.6), (x, y, gz + h)], [0.05, 0.045, 0.04], seg=6), BAMBOO, ao=0.3, ao_h=0.6, ground=gz))
    cup = K.lathe([(0.03, 0.0), (0.09, 0.08), (0.12, 0.2), (0.1, 0.22)], seg=10, cap0=True, cap1=False)
    A.add("battle", "MatThatch_atap", paint(xf(cup, (x, y, gz + h)), (0.36, 0.28, 0.18), ao=0.0))
    fl = K.lathe([(0.0, 0.0), (0.1, 0.04), (0.11, 0.14), (0.07, 0.3), (0.03, 0.42), (0.0, 0.5)], seg=10)
    fl.v[:, 0] += lean * fl.v[:, 2] ** 1.5 * 3.0
    A.add("battle", "MatGlow_torch", paint(xf(fl, (x, y, gz + h + 0.16)), (1.0, 0.78, 0.40), ao=0.0, top=0.0))
    if light:
        A.light((x + 0.1, y, gz + h + 0.4), watts, (1.0, 0.56, 0.24), range_m=7)


def kenyalang_pole(A, x, y, rz=0.3):
    """kenyalang: carved, painted ironwood pole topped with a hornbill (big upturned casque, long tail)."""
    H = 3.1
    gz = DECK_Z
    pole = K.lathe([(0.17, 0.0), (0.15, 0.4), (0.17, 0.45), (0.14, 0.5), (0.13, 1.4), (0.16, 1.45), (0.12, 1.5), (0.11, H - 0.15), (0.2, H - 0.12), (0.2, H), (0.0, H)], seg=12)
    bands = lambda v, c: np.where(((v[:, 2] - gz) % 0.5 < 0.08)[:, None], np.array([[0.62, 0.12, 0.08, 1]]), c)
    A.add("battle", "MatWood_belian", tint(paint(xf(pole, (x, y, gz)), (0.20, 0.15, 0.11), var=0.0, ao=0.3, ao_h=0.8, ground=gz, namp=0.1, ns=4), bands))
    A.add("battle", "MatWood_belian", paint(xf(K.box(0.8, 0.8, 0.12, bev=0.03), (x, y, gz - 0.02)), BELIAN_DK, ao=0.3, ao_h=0.2, ground=gz))
    # the hornbill: local frame, looking along +x (toward the ring), standing on the pole top
    bird = []
    body = smooth_blob(0.32, seed=3, seg=14, rings=8, amp=0.04, squash=0.72)
    body.v[:, 0] *= 1.7
    bird.append(("body", xf(body, (0, 0, 0.08))))
    bird.append(("head", xf(smooth_blob(0.16, seed=4, seg=12, rings=7, amp=0.02, squash=1.0), (0.5, 0, 0.42))))
    beak = K.tube([(0.6, 0, 0.55), (0.85, 0, 0.5), (1.05, 0, 0.36), (1.18, 0, 0.18)], [0.09, 0.075, 0.05, 0.012], seg=8)
    casque = K.tube([(0.6, 0, 0.66), (0.78, 0, 0.72), (0.95, 0, 0.75), (1.06, 0, 0.84), (1.08, 0, 0.92)], [0.07, 0.07, 0.06, 0.035, 0.01], seg=8)
    bird.append(("beak", beak))
    bird.append(("casque", casque))
    tail = K.strip_mesh([(-0.45, 0, 0.3), (-0.8, 0, 0.18), (-1.2, 0, 0.0), (-1.45, 0, -0.18)], [0.16, 0.2, 0.22, 0.2], up=(0, 0, 1))
    bird.append(("tail", tail))
    for s in (-1, 1):
        wing = K.strip_mesh([(0.35, s * 0.25, 0.35), (0.0, s * 0.55, 0.5), (-0.4, s * 0.75, 0.62), (-0.7, s * 0.85, 0.7)], [0.16, 0.22, 0.2, 0.1], up=(0, 0, 1))
        bird.append(("wing", wing))
    cols = {"body": (0.12, 0.10, 0.10), "head": (0.88, 0.84, 0.74), "beak": (0.95, 0.74, 0.18), "casque": (0.88, 0.26, 0.10),
            "tail": (0.90, 0.86, 0.78), "wing": (0.16, 0.12, 0.10)}
    for part, p in bird:
        q = xf(xf(p, (0, 0, 0), (0, 0, rz), s=1.5), (x, y, gz + H))
        if part in ("tail", "wing"):
            q = K.dbl(q)
            paint(q, cols[part], var=0.0, ao=0.0, top=0.2)
            if part == "tail":  # black band across the white tail
                tint(q, lambda v, c: np.where((np.abs(np.hypot(v[:, 0] - x, v[:, 1] - y) - 1.0) < 0.12)[:, None], np.array([[0.08, 0.07, 0.07, 1]]), c))
            A.add("battle", "MatCloth_pua", q)
        else:
            paint(q, cols[part], var=0.0, ao=0.0, top=0.25)
            if part == "body":  # painted red bands
                tint(q, lambda v, c: np.where((((v[:, 0] - x) * math.cos(rz) + (v[:, 1] - y) * math.sin(rz)) % 0.36 < 0.1)[:, None],
                                              np.array([[0.74, 0.14, 0.08, 1]]), c))
            A.add("battle", "MatWood_belian", q)
    A.contact(x, y, 0.8, 0.2)


def apron(A):
    """three small clusters (<= 0.6 m, muted near the rope)."""
    # (1) near-left: padi heap on a tikai mat + chapan winnowing tray + a basket
    mx, my, rz = -5.3, -1.9, 0.3
    m = xf(K.box(1.6, 1.2, 0.02, bev=0.004), (mx, my, DECK_Z), (0, 0, rz))
    A.add("battle", "MatThatch_atap", tint(paint(m, MAT, var=0.03, ao=0.0, top=0.0), lambda v, c: c * (0.86 + 0.14 * ((np.floor(v[:, 0] * 11) + np.floor(v[:, 1] * 11)) % 2))[:, None]))
    heap = K.lathe([(0.0, 0.0), (0.45, 0.0), (0.3, 0.07), (0.1, 0.12), (0.0, 0.125)], seg=14)
    A.add("battle", "MatThatch_atap", paint(xf(heap, (mx - 0.2, my + 0.1, DECK_Z + 0.02)), PADI, var=0.04, ao=0.0, top=0.3, namp=0.1, ns=6))
    tray = K.lathe([(0.0, 0.0), (0.32, 0.02), (0.36, 0.06), (0.34, 0.065), (0.0, 0.025)], seg=16)
    A.add("battle", "MatThatch_atap", paint(xf(tray, (mx + 0.45, my - 0.25, DECK_Z + 0.02), (0.1, 0, 0)), (0.58, 0.46, 0.28), ao=0.0, top=0.2))
    A.contact(mx, my, 1.1, 0.2)
    # (2) far-right: small gongs lying face-up + beater + pansoh bamboo tubes
    for k, (gx, gy) in enumerate(((4.4, 3.4), (4.85, 2.8))):
        A.add("battle", "MatMetal_brass", paint(xf(xf(gong(0.16, 0.05, 0.06), (0, 0, 0), (-math.pi / 2, 0, 0)), (gx, gy, DECK_Z + 0.06)), BRASS, ao=0.0, top=0.15))
    A.add("battle", "MatWood_belian", paint(K.tube([(4.0, 2.7, DECK_Z + 0.03), (4.4, 2.4, DECK_Z + 0.03)], 0.015, seg=4), BELIAN_LT, ao=0.0))
    for k in range(3):
        A.add("battle", "MatWood_belian", paint(K.tube([(3.7 + 0.1 * k, 4.4, DECK_Z + 0.05), (4.4 + 0.1 * k, 4.75, DECK_Z + 0.05)], 0.045, seg=7), BAMBOO, ao=0.0, top=0.2))
    A.contact(4.4, 3.4, 0.8, 0.2)
    # (3) far-left: folded pua stack, tray of rice cakes, small tuak jar
    for k in range(3):
        p = K.box(0.55, 0.4, 0.05, bev=0.012)
        A.add("battle", "MatCloth_pua", paint(xf(p, (-3.4, 4.6, DECK_Z + 0.05 * k), (0, 0, 0.2 + 0.08 * k)), PUA_COLS[k % 3], ao=0.0, top=0.2))
    A.add("battle", "MatThatch_atap", paint(xf(K.lathe([(0, 0), (0.24, 0), (0.26, 0.04), (0, 0.02)], seg=14), (-2.7, 5.0, DECK_Z)), (0.54, 0.42, 0.26), ao=0.0))
    for k in range(5):
        A.add("battle", "MatCloth_pua", paint(xf(K.box(0.07, 0.07, 0.04, bev=0.012), (-2.8 + 0.08 * (k % 3), 4.95 + 0.08 * (k // 3), DECK_Z + 0.04)), (0.80, 0.66, 0.40), ao=0.0))
    tajau(A, -4.2, 4.3, DECK_Z, 0.42, seed=9)
    A.contact(-3.4, 4.7, 0.9, 0.2)


# ---------------------------------------------------------------- far set
def river(A):
    """moonlit river behind the longhouse, seen past its gable end: water sheet with the moon's path painted in,
    a landing on the far bank and two longboats (far set: vista only)."""
    wy0, wy1 = RIVER_Y
    xs = np.concatenate([np.arange(-30.0, 6.0, 4.0), np.arange(6.0, 46.01, 0.5)])
    ys = np.linspace(wy0, wy1, 12)
    v, f, c = [], [], []
    tz = math.tan(math.atan2(MOON[0] - VEYE[0], MOON[1] - VEYE[1]))
    for y in ys:
        xl = VEYE[0] + (y - VEYE[1]) * tz          # the moon's screen column, projected onto the water
        w = 0.35 + 0.04 * (y - wy0)
        for x in xs:
            g = math.exp(-((x - xl) / w) ** 2) * (0.75 + 0.25 * nz(x, y, 0, 1.7, 51))
            edge = smooth01(0.0, 1.2, min(y - wy0, wy1 - y))
            col = mix((0.10, 0.11, 0.12), (0.05, 0.08, 0.13), edge) * (1 - g) + np.array((0.50, 0.56, 0.70)) * g
            v.append((x, y, WZ))
            c.append(list(col) + [1.0])
    n = len(xs)
    for i in range(len(ys) - 1):
        for j in range(n - 1):
            a = i * n + j
            f.append((a, a + 1, a + n + 1, a + n))
    A.add("far", "MatWater_river", P(v, f, c))
    # landing stage on the far bank: plank deck on posts + notched-log ladder up to the longhouse
    x0, y0 = 13.2, wy1 - 0.9
    wood = [xf(K.box(2.6, 1.3, 0.06, bev=0.01), (x0, y0, WZ + 0.22))]
    wood += [K.tube([(x0 + sx * 1.15, y0 + sy * 0.5, WZ - 0.4), (x0 + sx * 1.15, y0 + sy * 0.5, WZ + 0.5)], 0.06, seg=4) for sx in (-1, 1) for sy in (-1, 1)]
    wood.append(K.tube([(x0 + 0.6, y0 + 0.6, WZ + 0.25), (x0 + 0.6, RUAI_Y0 + FAR_RUN[2] - 0.1, RUAI_Z + FAR_RUN[3])], [0.11, 0.09], seg=6))
    A.add("far", "MatWood_belian", [paint(q, BELIAN_DK, var=0.08, ao=0.3, ao_h=0.5, ground=WZ, namp=0.1, ns=3) for q in wood])
    # two Iban longboats moored at the landing, painted bow bands
    for k, (x, y, rz, L) in enumerate(((11.4, wy1 - 2.6, 0.06, 8.0), (16.8, wy1 - 1.9, -0.1, 7.0))):
        hull = xf(K.perahu(L=L, W=0.62, H=0.34, seed=k), (x, y, WZ - 0.1), (0, 0, rz))
        paint(hull, (0.20, 0.15, 0.11), var=0.05, ao=0.0, top=0.25, namp=0.1, ns=2)
        tint(hull, lambda v, c, x=x: np.where((np.abs(v[:, 0] - x) > L * 0.36)[:, None] & ((v[:, 2] - WZ) > 0.1)[:, None],
                                             np.array([[0.70, 0.62, 0.48, 1]]), c))
        A.add("far", "MatWood_belian", hull)
        A.add("far", "MatWood_belian", paint(K.tube([(x + 0.3, y + 0.5, WZ - 0.6), (x + 0.5, y + 0.6, WZ + 1.6)], 0.035, seg=4), BAMBOO, ao=0.0))


def jungle(A):
    """layered rainforest ridges + emergent tree flats + palms along the river."""
    specs = [(lambda x: 60 + 8 * math.sin(x * 0.04), lambda x: 9 + 5 * math.sin(x * 0.05 + 1) + 3 * nz(x, 0, 0, 0.08, 41), 36.0, 1, (0.09, 0.15, 0.12)),
             (lambda x: 105 + 10 * math.sin(x * 0.025 + 2), lambda x: 16 + 7 * math.sin(x * 0.03 + 2.4) + 4 * nz(x, 0, 0, 0.06, 42), 44.0, 2, (0.10, 0.15, 0.17)),
             (lambda x: 160 + 10 * math.sin(x * 0.02 + 4), lambda x: 24 + 9 * math.sin(x * 0.022 + 0.6) + 5 * nz(x, 0, 0, 0.05, 43), 50.0, 3, (0.12, 0.16, 0.22))]
    for (ycf, crf, dep, seed, base) in specs:
        p = ridge(-240, 260, ycf, crf, depth=dep, foot=-8.0, cols=110 if seed == 1 else 80, seed=seed)
        n = np.array([nz(a, b, c_, 0.15, seed * 5) for a, b, c_ in p.v])
        zt = (p.v[:, 2] - p.v[:, 2].min()) / max(1e-6, np.ptp(p.v[:, 2]))
        col = np.asarray(base)[None, :] * (0.75 + 0.3 * n[:, None] + 0.35 * zt[:, None])
        p.c = np.ones((len(p.v), 4))
        p.c[:, :3] = np.clip(col, 0, 1)
        A.add("far", "MatLeaf_forest", p)
    rng = random.Random(31)
    for k in range(30):  # emergent trees (tapang/dipterocarp crowns) in front of the first ridge
        x = rng.uniform(-90, 100)
        y = rng.uniform(48, 70)
        if not in_vista(x, y):
            continue
        h = rng.uniform(10, 17)
        gz = ground(x, y)
        circ = [(rng.uniform(-0.3, 0.3) * h * 0.5, h * (0.78 + 0.12 * t), h * (0.22 - 0.05 * t) * rng.uniform(0.8, 1.2)) for t in (0.0, 0.5, 1.0)]
        circ += [(c[0] + rng.uniform(-1, 1) * h * 0.25, c[1] - h * 0.05, c[2] * 0.8) for c in circ[:2]]
        card = lobed_card(circ, cols=12, rows=3, puff=0.25, flat_base=0.45)
        z = card.v[:, 2]
        kk = 0.55 + 0.55 * smooth01(z.min(), z.max(), z)
        card.c = np.ones((len(card.v), 4))
        card.c[:, :3] = np.asarray((0.10, 0.17, 0.13))[None, :] * kk[:, None] * rng.uniform(0.85, 1.2)
        A.add("far", "MatLeaf_forest", face_cam(card, x, y, gz))
        A.add("far", "MatWood_belian", paint(K.tube([(x, y, gz - 0.3), (x, y, gz + h * 0.72)], [0.5, 0.3], seg=4, cap=False), (0.30, 0.28, 0.24), ao=0.0))
    for k in range(10):  # sago / nipah palms on the far bank of the river, around and behind the far run
        y = RIVER_Y[1] + 0.8 + rng.uniform(0, 1.2) if k % 4 == 0 else rng.uniform(35, 46)
        x = rng.uniform(2, 46)
        if not in_vista(x, y):
            continue
        tr, lf = K.coconut_palm(rng.uniform(5.0, 7.0), seed=900 + k, fronds=8)
        gz = ground(x, y)
        A.add("far", "MatWood_belian", paint(xf(tr, (x, y, gz - 0.1)), (0.30, 0.26, 0.20), ao=0.0))
        A.add("far", "MatLeaf_forest", paint(xf(lf, (x, y, gz - 0.1)), (0.16, 0.26, 0.15), var=0.1, ao=0, top=0.35))


def sky(A):
    """moon disc (Glow) + night cloud flats (moon-rimmed) at two depths."""
    mx, my, mz, mr = MOON
    disc = K.lathe([(mr, 0.0), (0.0, 0.0)], seg=40, cap0=False, cap1=False)
    disc = xf(disc, (0, 0, 0), (math.pi / 2, 0, 0))
    A.add("far", "MatGlow_moon", paint(face_cam(disc, mx, my, mz), (0.92, 0.94, 1.0), ao=0.0, top=0.0))
    rng = random.Random(5)
    for k, (x, y, z, w, h) in enumerate(((10, 100, 22, 30, 5), (52, 104, 31, 34, 6), (-30, 120, 30, 40, 7), (80, 130, 26, 36, 6), (-70, 140, 38, 44, 8),
                                         (120, 150, 40, 40, 7))):
        circ = [((-0.4 + 0.8 * (i + rng.uniform(0.2, 0.8)) / 5) * w, h * rng.uniform(0.0, 0.3), h * rng.uniform(0.35, 0.6)) for i in range(5)]
        card = lobed_card(circ, cols=18, rows=3, puff=0.2, flat_base=0.3)
        z_ = card.v[:, 2]
        t = smooth01(z_.min(), z_.max(), z_)
        card.c = np.ones((len(card.v), 4))
        card.c[:, :3] = np.asarray((0.08, 0.10, 0.16))[None, :] * (1 - t[:, None]) + np.asarray((0.24, 0.28, 0.40))[None, :] * t[:, None]
        A.add("far", "MatLeaf_forest", face_cam(card, x, y, z))


# ---------------------------------------------------------------- build
def build(A):
    for name in ("MatWood_belian", "MatThatch_atap", "MatCloth_pua", "MatTile_glaze", "MatMetal_brass", "MatGround_earth"):
        A.mat(name)
    A.mat("MatLeaf_forest", rough=1.0)  # matte night foliage: no moonlight specular streak on the ridge crests
    A.mat("MatGlow_torch", emit=(1.0, 0.55, 0.22), estr=0.45)
    A.mat("MatGlow_bilik", emit=(1.0, 0.50, 0.18), estr=0.2)   # dim lamp-lit room interiors seen through the bilik doors
    A.mat("MatWater_river")
    A.mat("MatGlow_moon", emit=(0.80, 0.86, 1.0), estr=3.0)

    deck(A)
    tangga(A, -2.6, DECK[2])
    longhouse(A, LH_X[0], LH_X[1], "battle")
    ruai_dressing(A)
    kenyalang_pole(A, -8.4, 1.0, rz=0.25)
    for k, (x, y, h) in enumerate(((-7.1, -2.6, 0.78), (-7.9, -1.7, 0.66), (-6.6, -3.5, 0.55), (-9.3, 2.9, 0.72))):
        tajau(A, x, y, DECK_Z, h, seed=k + 4)
    gong_rack(A, 8.6, 2.2, -0.35)
    torch(A, 7.0, -0.6, 2.3, watts=40.0)
    torch(A, 10.6, 4.6, 2.5, watts=36.0)
    torch(A, -6.6, 2.4, 2.2, watts=30.0)
    apron(A)
    # longhouse lamps (pelita) hanging in the ruai
    for k, x in enumerate((-8.0, 0.8, 4.4)):
        A.add("battle", "MatGlow_torch", paint(xf(K.lathe([(0, 0), (0.08, 0.0), (0.1, 0.1), (0.05, 0.18), (0, 0.19)], seg=8), (x, RUAI_Y0 + 1.6, ROOF_EAVE - 0.7)), (1.0, 0.8, 0.5), ao=0.0, top=0.0))
        A.add("battle", "MatMetal_brass", paint(K.tube([(x, RUAI_Y0 + 1.6, ROOF_EAVE - 0.5), (x, RUAI_Y0 + 1.6, ROOF_EAVE + 0.4)], 0.006, seg=3), (0.3, 0.3, 0.3), ao=0.0))
        if k != 1:
            A.light((x, RUAI_Y0 + 1.6, ROOF_EAVE - 0.8), 34.0, (1.0, 0.62, 0.30), range_m=8)

    # ---- terrain (courtyard below the deck + forest floor)
    A.terrain(ground, gcolor, kind=lambda x, y, z: "MatGround_earth", rin=4.5, rout=135.0, split=23.0, cull=gcull, seed=4)
    # grass at the deck edges + reeds along the riverbank (wind cue)
    rng = random.Random(3)
    for k in range(70):
        x = rng.uniform(-20, 20)
        y = rng.uniform(-14, -6.9) if k % 2 else rng.uniform(-14, 14)
        if DECK[0] - 0.2 < x < DECK[1] + 0.2 and DECK[2] - 0.2 < y < (RUAI_Y1 + 4.0 if x < LH_X[1] + 0.3 else DECK[3] + 0.3):
            continue
        if not visible(x, y):
            continue
        A.scatter_patch("Grass", 32, x, y, rng.uniform(0.5, 1.2), ground, GRASS_T, seed=k)
    for k in range(28):
        y = rng.uniform(-16, -7.2)
        x = rng.uniform(-14, 18)
        if visible(x, y) and abs(x) > 4.0:
            A.scatter_patch("Reed", 10, x, y, 1.0, ground, (0.30, 0.38, 0.20), seed=100 + k)

    # ---- far set
    longhouse(A, -45.0, LH_X[0], "far")   # only its last ~20 m can reach the vista frame (behind the hub plaque)
    longhouse(A, FAR_RUN[0], FAR_RUN[1], "far", oy=FAR_RUN[2], lift=FAR_RUN[3])
    river(A)
    jungle(A)
    sky(A)


if __name__ == "__main__":
    K.main("sarawak", build, MOOD)
