"""Johor arena -- overcast working wharf on the Straits of Johor (design_art.md section c).
Ground: concrete wharf apron (slab joints, oil stains, crane rails, a rail siding) + weathered timber deck at the quay edge.
Apron: cast-iron bollards with coiled hawsers, crates, oil drums, pallets (all low).
Left flank: corrugated godown with loading platform, open doors, sack stacks, hand trolley.
Far band: quay edge with fenders + tyres, bollards, a loaded tongkang moored below, mooring lines.
Right flank: portal crane legs on rails (rust + safety yellow), its jib swung over the tongkang with a cargo net.
Far set (vista): the strait -- passenger ferry, container ship at anchor, container-port gantry cranes,
Masjid Sultan Abu Bakar on its hill across the water, layered hills, overcast cloud banks.
Shared helpers live in arena_penang.py (same owner).
  blender -b --factory-startup -P art_src/arena_johor.py -- --export --render game,vista --out <dir>
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
from arena_penang import Kit, place_kit, bx, stripes, corrugated, visible, in_vista, hill, paint_hill, scale

MOOD = {"sky_top": (0.42, 0.49, 0.56), "sky_horizon": (0.78, 0.80, 0.78), "fog": (0.56, 0.61, 0.64),
        "fog_density": 0.005, "sun_color": (0.92, 0.92, 0.90), "sun_energy": 0.8,
        "lantern": (1.0, 0.74, 0.48), "lantern_energy": 1.4, "exposure": 0.85, "ambient": 0.7,
        "b_sun": 2.2, "b_world": 1.0, "b_fill": 0.5, "b_lantern": 8.0}

NAMES = {"Plaster": "MatPlaster_white", "Wood": "MatWood_wharf", "Tile": "MatTile_roof", "Glow": "MatGlow_warm",
         "Metal": "MatMetal_steel", "Cloth": "MatCloth_tarp", "Rope": "MatThatch_rope", "Rock": "MatRock_quay", "Leaf": "MatLeaf_canopy"}
NAMES_FAR = dict(NAMES, Wood="MatPlaster_white", Cloth="MatPlaster_white", Rope="MatPlaster_white", Rock="MatPlaster_white",
                 Glow="MatPlaster_white")

CONC = (0.50, 0.50, 0.48)
CONC_DK = (0.36, 0.36, 0.35)
OIL = (0.20, 0.20, 0.20)
TIMBER = (0.44, 0.40, 0.34)
TIMBER_DK = (0.30, 0.27, 0.23)
RUST = (0.45, 0.24, 0.14)
YELLOW = (0.80, 0.62, 0.14)
WET = (0.27, 0.29, 0.30)
SEA = (0.24, 0.34, 0.33)
BURLAP = (0.56, 0.46, 0.32)

QUAY_Y = 7.4        # far quay edge (water beyond)
QUAY_X = 13.0       # right quay edge
DECK_Y = 4.9        # timber deck strip from here to the quay edge
WATER_Z = -1.25
GOD_X = -8.6        # godown loading-platform front (faces +x)
PLAT_H = 0.9
CRANE = ((8.6, 3.9), (12.2, 3.9), (8.6, 7.0), (12.2, 7.0))   # portal crane leg feet
RAIL_X = (8.6, 12.2)
SIDING_Y = -7.6


def is_land(x, y):
    return y < QUAY_Y and x < QUAY_X and x > -60 and y > -60


def ground(x, y):
    if not is_land(x, y):
        return WATER_Z - 0.8
    return 0.01 * nz(x, y, 0, 0.5, 3) - 0.02 * (1 - smooth01(0.0, 0.6, abs(y - SIDING_Y)))


def gcolor(x, y, z):
    if z < WATER_Z:
        return (0.1, 0.1, 0.1)
    n1, n2, n3 = nz(x, y, 0, 0.3, 11), nz(x, y, 0, 1.5, 12), nz(x, y, 0, 4.5, 13)
    c = np.array(CONC) * (1 + 0.1 * n1 + 0.06 * n2 + 0.05 * n3)
    c = c + (np.array(CONC_DK) - c) * 0.55 * smooth01(0.15, 0.55, nz(x, y, 0, 0.22, 14))          # damp patches
    c = c + (np.array(OIL) - c) * 0.6 * smooth01(0.45, 0.8, nz(x, y, 0, 0.6, 15))                   # oil stains
    c = c + (np.array(OIL) - c) * 0.5 * smooth01(0.35, 0.6, nz(x, y, 0, 1.3, 17))                   # small drips across the joints
    c = c + (np.array(WET) - c) * 0.75 * smooth01(-0.1, 0.3, nz(x, y, 0, 0.45, 18)) * smooth01(QUAY_Y - 6.0, QUAY_Y - 1.5, y)  # wet by the quay
    c = c + (np.array((0.42, 0.30, 0.22)) - c) * 0.5 * smooth01(0.5, 0.85, nz(x, y, 0, 0.9, 16))   # rust bleed
    for rx in RAIL_X:  # rust + grease along the crane rails
        c = c * (1 - 0.3 * (1 - smooth01(0.1, 0.6, abs(x - rx))))
    c = c * (1 - 0.3 * (1 - smooth01(0.0, 1.2, abs(y - SIDING_Y))))
    c = c * (1 - 0.25 * smooth01(QUAY_Y - 0.8, QUAY_Y, y)) * (1 - 0.25 * smooth01(QUAY_X - 0.8, QUAY_X, x))
    r = math.hypot(x, y)
    c = c + (np.array((0.56, 0.55, 0.52)) - c) * 0.35 * (1 - smooth01(4.6, 6.0, r))                 # swept apron
    return tuple(np.clip(c, 0, 1))


def gcull(cx, cy, zmax):
    if zmax < WATER_Z:
        return True
    if DECK_Y + 0.05 < cy < QUAY_Y and cx < QUAY_X - 0.05:   # under the timber deck
        return True
    if cx < GOD_X - 0.1 and -9 < cy < 12:                    # under the godown platform
        return True
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


# ---------------------------------------------------------------- props
def bollard():
    """cast-iron mooring bollard (mushroom head). base z=0."""
    return K.lathe([(0.0, 0.0), (0.26, 0.0), (0.26, 0.05), (0.16, 0.08), (0.13, 0.3), (0.15, 0.4), (0.24, 0.44), (0.25, 0.5), (0.2, 0.55),
                    (0.0, 0.57)], seg=12)


def crate(w=0.6, d=0.5, h=0.45, rgb=(0.50, 0.40, 0.28), seed=0):
    p = bx(w, d, h, (0, 0, 0), bev=0.015)
    paint(p, rgb, var=0.08, ao=0.3, ao_h=h, top=0.2, seed=seed)
    return tint(p, lambda v, c: c * np.where((np.abs(np.abs(v[:, 0]) - w / 2) < 0.05) | (np.abs(np.abs(v[:, 1]) - d / 2) < 0.05), 0.75,
                                             0.9 + 0.1 * (np.floor(v[:, 2] * 9) % 2))[:, None])


def drum(rgb):
    p = K.lathe([(0.0, 0.0), (0.28, 0.0), (0.29, 0.02), (0.29, 0.29), (0.3, 0.3), (0.29, 0.31), (0.29, 0.59), (0.3, 0.6), (0.29, 0.61),
                 (0.29, 0.86), (0.28, 0.88), (0.0, 0.88)], seg=12)
    rgb = tuple(0.55 * c + 0.45 * sum(rgb) / 3 for c in rgb)   # sun-faded paint
    paint(p, rgb, var=0.06, ao=0.3, ao_h=0.3, top=0.2, namp=0.2, ns=5)
    rust = smooth01(0.1, 0.6, K.nfield(p.v, 6.0, int(rgb[0] * 100))) * 0.7 + 0.5 * (1 - smooth01(0.0, 0.15, p.v[:, 2]))
    p.c[:, :3] = p.c[:, :3] * (1 - rust[:, None]) + np.array(RUST)[None, :] * rust[:, None]
    return p


def sack(seed=0):
    rng = random.Random(seed)
    p = K.box(0.62, 0.4, 0.24, bev=0.09, seg=2)
    p.v += np.array([[rng.uniform(-0.02, 0.02) for _ in range(3)] for _ in range(len(p.v))])
    return p


def sack_pile(n, seed=0, rgb=BURLAP):
    """stacked sacks in staggered courses."""
    rng = random.Random(seed)
    ps = []
    layer = 0
    i = 0
    while i < n:
        per = max(1, 3 - layer)
        for j in range(per):
            if i >= n:
                break
            x = (j - (per - 1) / 2) * 0.64 + rng.uniform(-0.05, 0.05)
            ps.append(paint(xf(sack(seed + i), (x, rng.uniform(-0.04, 0.04), layer * 0.22), (0, 0, rng.uniform(-0.12, 0.12))),
                            scale(rgb, rng.uniform(0.88, 1.1)), ao=0.3, ao_h=0.6, top=0.25))
            i += 1
        layer += 1
    return join(ps)


def pallet():
    ps = [bx(1.2, 0.1, 0.1, (0, y, 0), bev=0.0) for y in (-0.45, 0.0, 0.45)]
    ps += [bx(0.12, 1.0, 0.025, (x, 0, 0.1), bev=0.0) for x in np.linspace(-0.54, 0.54, 7)]
    return join(ps)


def tyre(R=0.4, r=0.12):
    ring = [(R * math.cos(a), 0, R * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)]
    return K.tube(ring, r, seg=6, cap=False)


def godown(A):
    """left flank: long corrugated godown facing the dish, raised loading platform with sacks + trolley."""
    k = Kit()
    L = 22.0
    yc = 1.6
    # platform: concrete slab with timber fender edge + steps
    k.put("Rock", paint(bx(2.0, L, PLAT_H, (1.0, 0, 0), bev=0.03), (0.52, 0.51, 0.48), ao=0.35, ao_h=0.9, top=0.2, namp=0.15, ns=1.5))
    k.put("Wood", tint(paint(bx(0.16, L, 0.26, (2.06, 0, PLAT_H - 0.3), bev=0.02), TIMBER_DK, ao=0.0, top=0.2), stripes(1, 0.8, 0.8, 1.0)))
    for s in range(3):
        k.put("Rock", paint(bx(0.32, 1.6, 0.3 * (s + 1), (2.0 + 0.32 * (2 - s) + 0.16, -3.0, 0), bev=0.015), (0.50, 0.49, 0.46), ao=0.2, ao_h=0.6, top=0.2))
    # walls: rendered dado + corrugated zinc above, big door openings (sliding doors)
    wall_h = 5.2
    doors = (-5.5, 3.5)
    dw = 3.2
    segs = [-L / 2]
    for d in doors:
        segs += [d - dw / 2, d + dw / 2]
    segs.append(L / 2)
    for a, b in zip(segs[0::2], segs[1::2]):
        k.put("Plaster", paint(bx(0.3, b - a, 1.2, (0, (a + b) / 2, PLAT_H), bev=0.0), (0.66, 0.64, 0.58), ao=0.3, ao_h=0.6, top=0.1, namp=0.12, ns=1))
        zinc = xf(corrugated(b - a, wall_h - 1.2, 0.16, 0.025, ny=1), (0.0, 0.0, 0.0), (math.pi / 2, 0, math.pi / 2))
        zinc = xf(zinc, (0.05, (a + b) / 2, PLAT_H + 1.2 + (wall_h - 1.2) / 2))
        k.put("Metal", tint(paint(K.dbl(zinc), (0.56, 0.58, 0.58), ao=0.0, top=0.0),
                            lambda v, c: c * (1 - 0.4 * smooth01(0.2, 0.8, np.array([nz(q[1] * 0.4, q[2] * 0.1, 0, 2.0, 5) for q in v])))[:, None] +
                            np.array([0.1, 0.03, -0.02, 0])[None, :] * smooth01(0.3, 0.9, np.array([nz(q[1] * 0.5, q[2] * 0.08, 1, 1.0, 6) for q in v]))[:, None]))
    for d in doors:
        k.put("Plaster", paint(bx(0.3, dw, wall_h - 3.6, (0, d, PLAT_H + 3.6), bev=0.0), (0.62, 0.60, 0.55), ao=0.0, top=0.1))
        k.put("Wood", paint(bx(0.05, dw, 3.6, (-1.6, d, PLAT_H), bev=0.0), (0.10, 0.09, 0.08), ao=0.0))      # dark interior back
        k.put("Metal", tint(paint(bx(0.06, dw * 0.55, 3.5, (0.24, d + dw * 0.72, PLAT_H), bev=0.0), (0.46, 0.50, 0.52), ao=0.3, ao_h=1.5),
                            stripes(1, 6, 0.8, 1.0)))   # slid-open door leaf
    k.put("Glow", paint(bx(0.4, 0.4, 0.12, (-0.8, doors[1], PLAT_H + 3.0), bev=0.0), (1.0, 0.85, 0.6), ao=0.0, top=0.0))
    # canopy over the platform on brackets + roof
    can = xf(corrugated(L + 0.4, 2.6, 0.2, 0.03, ny=1), (1.2, 0, 0), (0, 0, math.pi / 2))
    can.v[:, 2] += PLAT_H + wall_h - 0.3 - (can.v[:, 0] - 0.0) * 0.12
    k.put("Metal", paint(K.dbl(can), (0.50, 0.42, 0.36), var=0.05, ao=0.0, top=0.25, namp=0.3, ns=1.0))
    for y in np.arange(-L / 2 + 1, L / 2, 4.0):
        k.put("Metal", paint(K.tube([(0.15, y, PLAT_H + 3.4), (2.3, y, PLAT_H + wall_h - 0.55)], 0.04, seg=4), (0.25, 0.22, 0.2), ao=0.0))
    roof = xf(corrugated(L + 0.6, 8.0, 0.24, 0.04, ny=1), (0, 0, 0), (0, 0, math.pi / 2))
    roof.v[:, 2] += PLAT_H + wall_h + 0.3 + (-roof.v[:, 0]) * 0.32
    roof.v[:, 0] -= 4.0
    k.put("Metal", paint(K.dbl(roof), (0.44, 0.36, 0.30), var=0.05, ao=0.0, top=0.3, namp=0.35, ns=0.6))
    # cargo on the platform: sacks, crates, drums, hand trolley
    k.put("Cloth", xf(sack_pile(9, 3), (0.9, -7.0, PLAT_H)), xf(sack_pile(6, 9), (0.8, 6.8, PLAT_H), (0, 0, math.pi / 2)),
          xf(sack_pile(5, 21, (0.50, 0.44, 0.36)), (1.1, 0.6, PLAT_H)))
    for i, (x, y) in enumerate(((1.3, -1.2), (1.4, -0.6), (0.9, 9.0))):
        k.put("Wood", xf(crate(0.62, 0.52, 0.5, seed=i), (x, y, PLAT_H)))
    tr = [K.tube([(1.5, 2.6, PLAT_H + 0.05), (1.3, 2.6, PLAT_H + 1.1)], 0.02, seg=4), K.tube([(1.5, 3.0, PLAT_H + 0.05), (1.3, 3.0, PLAT_H + 1.1)], 0.02, seg=4),
          bx(0.3, 0.5, 0.03, (1.62, 2.8, PLAT_H + 0.02), bev=0.0), xf(H.wheel(0.12, 0.01, 6, 10), (1.45, 2.5, PLAT_H + 0.12), (0, 0, 0)),
          xf(H.wheel(0.12, 0.01, 6, 10), (1.45, 3.1, PLAT_H + 0.12))]
    k.put("Metal", paint(join(tr), (0.2, 0.32, 0.5), ao=0.0, top=0.3))
    place_kit(A, "battle", k, (GOD_X - 2.0, yc, 0.0), 0.0, NAMES)
    A.contact(GOD_X + 0.3, yc, 3.0, 0.25)
    for i, (x, y, rgb) in enumerate(((GOD_X + 0.6, -4.2, (0.20, 0.36, 0.56)), (GOD_X + 0.9, -3.6, (0.62, 0.18, 0.12)), (GOD_X + 0.5, -3.3, (0.20, 0.36, 0.56)))):
        A.add("battle", "MatMetal_steel", xf(drum(rgb), (x, y, ground(x, y))))
    A.contact(GOD_X + 0.7, -3.7, 1.0, 0.3)


def portal_crane(A):
    """right flank: portal crane straddling its rails at the quay; jib swung over the tongkang (vista)."""
    k = Kit()
    feet = CRANE
    top_z = 7.0
    legs = []
    for (x, y) in feet:
        a = (x, y, 0.55)
        b = (10.4 + (x - 10.4) * 0.55, 5.45 + (y - 5.45) * 0.7, top_z)
        legs.append(K.tube([a, b], 0.2, seg=4, cap=True))
        legs.append(bx(0.7, 1.4, 0.55, (x, y, 0.0), bev=0.04))     # bogie
    for (p, q) in ((feet[0], feet[1]), (feet[2], feet[3]), (feet[0], feet[2]), (feet[1], feet[3])):
        a = (p[0], p[1], 2.4)
        b = (q[0], q[1], 2.4)
        legs.append(K.tube([a, b], 0.1, seg=4))
    legs.append(K.tube([(feet[0][0], feet[0][1], 0.6), (10.4 + (feet[2][0] - 10.4) * 0.55, 5.45 + (feet[2][1] - 5.45) * 0.7, top_z)], 0.07, seg=4))
    legs.append(bx(3.0, 3.2, 0.6, (10.4, 5.45, top_z - 0.1), bev=0.05))
    k.put("Metal", tint(paint(join(legs), YELLOW, var=0.05, ao=0.3, ao_h=2.0, top=0.25, namp=0.25, ns=1.2),
                        lambda v, c: c + (np.array(list(RUST) + [1]) - c) * (0.6 * smooth01(0.1, 0.7, K.nfield(v, 1.4, 4)) + 0.5 * (1 - smooth01(0.0, 0.8, v[:, 2])))[:, None]))
    for (x, y) in feet:  # black/yellow hazard band on the bogies
        k.put("Metal", tint(paint(bx(0.74, 1.44, 0.16, (x, y, 0.3), bev=0.0), (1, 1, 1), ao=0.0),
                            lambda v, c: c * np.where((np.floor((v[:, 1] + v[:, 2]) * 4) % 2 == 0)[:, None], np.array([0.08, 0.08, 0.08, 1]), np.array([0.85, 0.7, 0.15, 1]))))
    # machinery house + cab + jib
    k.put("Metal", paint(bx(3.4, 2.6, 2.4, (10.6, 5.2, top_z + 0.5), bev=0.05), (0.72, 0.70, 0.64), ao=0.0, top=0.2, namp=0.15, ns=1.0))
    k.put("Glow", paint(bx(0.9, 0.05, 0.6, (9.5, 3.88, top_z + 1.4), bev=0.0), (0.9, 0.85, 0.7), ao=0.0, top=0.0))
    jib0, jib1 = np.array((9.4, 5.6, top_z + 1.6)), np.array((-2.0, 9.8, 16.0))
    side = np.array((0.45, 0.8, 0.0)) / np.linalg.norm((0.45, 0.8, 0.0)) * 0.45
    jib = [K.tube([tuple(jib0 + side), tuple(jib1 + side * 0.3)], 0.12, seg=4), K.tube([tuple(jib0 - side), tuple(jib1 - side * 0.3)], 0.12, seg=4),
           K.tube([tuple(jib0 + (0, 0, 0.6)), tuple(jib1 + (0, 0, 0.25))], 0.1, seg=4)]
    for t in np.linspace(0.1, 0.9, 7):
        p = jib0 + (jib1 - jib0) * t
        jib.append(K.tube([tuple(p + side * (1 - 0.7 * t)), tuple(p - side * (1 - 0.7 * t) + (0, 0, 0.5 * (1 - 0.6 * t)))], 0.05, seg=3, cap=False))
    jib.append(K.tube([tuple(jib0 + (0.6, 0.0, 2.6)), tuple(jib1 + (0, 0, 0.3))], 0.03, seg=3, cap=False))   # luffing stay
    jib.append(K.tube([tuple(jib0 + (0.6, 0.0, 2.6)), tuple(jib0 + (1.0, 0.2, 0.0))], 0.15, seg=4))          # A-frame
    k.put("Metal", paint(join(jib), YELLOW, var=0.04, ao=0.0, top=0.25, namp=0.2, ns=1.0))
    hook_z = 4.6
    k.put("Metal", paint(K.tube([tuple(jib1), (jib1[0], jib1[1], hook_z + 1.2)], 0.02, seg=3, cap=False), (0.1, 0.1, 0.1), ao=0.0),
          paint(bx(0.3, 0.2, 0.4, (jib1[0], jib1[1], hook_z + 0.8), bev=0.02), (0.2, 0.2, 0.2), ao=0.0))
    for a in range(4):  # cargo-net slings
        ang = math.pi / 4 + a * math.pi / 2
        k.put("Rope", paint(K.tube([(jib1[0], jib1[1], hook_z + 0.8), (jib1[0] + 0.55 * math.cos(ang), jib1[1] + 0.45 * math.sin(ang), hook_z)], 0.015, seg=3, cap=False),
                            (0.3, 0.26, 0.2), ao=0.0))
    k.put("Cloth", xf(sack_pile(6, 40), (jib1[0], jib1[1], hook_z - 0.45)))
    place_kit(A, "battle", k, (0, 0, 0), 0.0, NAMES)
    for (x, y) in feet:
        A.contact(x, y, 1.0, 0.35)


def kereta_sorong():
    """wooden two-wheeled push cart (kereta sorong) loaded with rice sacks: plank bed with side boards, spoked
    wheels with iron tyres, long handles + rear legs. Kit keys; handles point -x. base z=0."""
    k = Kit()
    bed = [bx(1.5, 0.86, 0.06, (0.15, 0, 0.5), bev=0.01)]
    bed += [bx(1.5, 0.05, 0.24, (0.15, sy * 0.43, 0.56), bev=0.01) for sy in (-1, 1)] + [bx(0.05, 0.86, 0.24, (0.9, 0, 0.56), bev=0.01)]
    bed += [K.tube([(-1.35, sy * 0.36, 0.62), (-0.55, sy * 0.38, 0.55), (0.9, sy * 0.38, 0.5)], 0.035, seg=5) for sy in (-1, 1)]
    bed += [K.tube([(-0.45, sy * 0.36, 0.52), (-0.5, sy * 0.36, 0.0)], 0.03, seg=4) for sy in (-1, 1)]
    k.put("Wood", tint(paint(join(bed), TIMBER, var=0.05, ao=0.3, ao_h=0.6, top=0.25, namp=0.2, ns=3), stripes(1, 9.0, 0.86, 1.0)))
    hubs = [xf(K.wheel(0.42, 0.03, spokes=8), (0.35, sy * 0.52, 0.42)) for sy in (-1, 1)]
    k.put("Wood", paint(join(hubs), TIMBER_DK, var=0.04, ao=0.0, top=0.2))
    rims = [xf(tyre(0.42, 0.025), (0.35, sy * 0.52, 0.42)) for sy in (-1, 1)] + [K.tube([(0.35, -0.55, 0.42), (0.35, 0.55, 0.42)], 0.025, seg=4)]
    k.put("Metal", paint(join(rims), (0.16, 0.15, 0.14), ao=0.0, top=0.2))
    k.put("Cloth", xf(sack_pile(2, 70), (0.45, 0.0, 0.53)))
    return k


def tongkang(seed=0):
    """loaded wooden lighter: broad hull, sacks under a tarp, stern deckhouse. Kit; long axis x, base at waterline z=0."""
    k = Kit()
    hull = K.perahu(L=9.0, W=2.8, H=1.3, seed=seed)
    hull.v[:, 2] -= 0.5
    k.put("Wood", tint(paint(hull, (0.36, 0.30, 0.24), var=0.05, ao=0.0, top=0.2, namp=0.2, ns=2.0),
                       lambda v, c: c * np.where(v[:, 2] < 0.05, 0.55, np.where(v[:, 2] > 0.65, 1.25, 1.0))[:, None]))
    k.put("Wood", tint(paint(bx(6.6, 2.4, 0.06, (0.0, 0, 0.3), bev=0.0), TIMBER, ao=0.0, top=0.2), stripes(1, 4.5, 0.8, 1.0)))
    k.put("Cloth", xf(sack_pile(9, 7), (-1.6, -0.5, 0.36)), xf(sack_pile(8, 13), (-1.4, 0.5, 0.36)), xf(sack_pile(7, 17), (1.0, 0.0, 0.36), (0, 0, 0.1)))
    tarp = K.grid(2.6, 2.3, 8, 6)
    tarp.v[:, 2] = 0.95 - 0.35 * (np.abs(tarp.v[:, 1]) / 1.15) ** 2 + 0.05 * np.sin(tarp.v[:, 0] * 4)
    k.put("Cloth", paint(K.dbl(xf(tarp, (-1.5, 0, 0))), (0.20, 0.36, 0.44), ao=0.0, top=0.3, namp=0.15, ns=3))
    k.put("Wood", paint(bx(1.5, 1.8, 1.3, (3.2, 0, 0.3), bev=0.03), (0.52, 0.44, 0.34), ao=0.3, ao_h=1.0, top=0.2),
          paint(bx(1.8, 2.1, 0.08, (3.2, 0, 1.6), bev=0.02), (0.30, 0.20, 0.15), ao=0.0))
    k.put("Rope", paint(xf(K.rope_coil(0.35, 0.03, seed=seed), (2.2, 0.8, 0.36)), (0.40, 0.33, 0.22), ao=0.3, ao_h=0.1))
    return k


def quay(A):
    """timber deck strip, quay walls with fenders + tyres, bollards and mooring lines, crane rails, rail siding."""
    # timber deck (planks across)
    planks, rng = [], random.Random(2)
    x = -16.0
    while x < QUAY_X - 0.1:
        w = 0.22
        if visible(x, 6.0, 2.0):
            planks.append(paint(bx(w - 0.012, QUAY_Y - DECK_Y + 0.25, 0.08, (x + w / 2, (DECK_Y + QUAY_Y) / 2 + 0.12, -0.04), bev=0.0),
                                scale(TIMBER, rng.uniform(0.82, 1.12)), ao=0.0, top=0.15, namp=0.2, ns=3.0))
        x += w
    A.add("battle", "MatWood_wharf", planks)
    A.add("battle", "MatWood_wharf", paint(bx(QUAY_X + 16.0, 0.3, 0.12, ((QUAY_X - 16.0) / 2, DECK_Y - 0.05, -0.06), bev=0.02), TIMBER_DK, ao=0.0, top=0.2))
    # quay wall faces (far + right) with timber fenders and tyres
    for path, face in (([(-60.0, QUAY_Y + 0.12), (QUAY_X, QUAY_Y + 0.12)], 1), ([(QUAY_X + 0.12, QUAY_Y), (QUAY_X + 0.12, -60.0)], 1)):
        w = K.extrude(path, [(-0.1, 0.0), (0.0, 0.04), (0.05, -0.1), (0.1, WATER_Z - 0.6)], step=2.0)
        A.add("battle", "MatRock_quay", tint(paint(w, (0.46, 0.46, 0.44), ao=0.0, top=0.2, namp=0.15, ns=1.2),
                                             lambda v, c: c * (1 - 0.5 * smooth01(-0.4, WATER_Z + 0.1, v[:, 2]))[:, None] * np.array([1, 1.02, 1.0, 1])))
    fen = []
    for x in np.arange(-14.0, QUAY_X, 1.6):
        if visible(x, QUAY_Y, 2.0):
            fen.append(bx(0.22, 0.2, 1.5, (x, QUAY_Y + 0.25, WATER_Z - 0.2), bev=0.02))
    for y in np.arange(-6.0, QUAY_Y, 1.6):
        fen.append(bx(0.2, 0.22, 1.5, (QUAY_X + 0.25, y, WATER_Z - 0.2), bev=0.02))
    A.add("battle", "MatWood_wharf", paint(join(fen), (0.28, 0.25, 0.21), ao=0.0, top=0.2, namp=0.2, ns=2))
    tyres = [xf(tyre(), (x, QUAY_Y + 0.45, -0.55), (0.25, 0, 0)) for x in (-6.8, -1.2, 4.0)]
    tyres += [xf(tyre(), (QUAY_X + 0.45, y, -0.55), (0, 0, math.pi / 2)) for y in (-3.0, 2.0)]
    A.add("battle", "MatMetal_steel", paint(join(tyres), (0.08, 0.08, 0.08), ao=0.0, top=0.2))
    # bollards along the edge + mooring lines to the tongkang
    for x in (-6.0, 0.6, 6.4):
        A.add("battle", "MatMetal_steel", paint(xf(bollard(), (x, QUAY_Y - 0.45, 0.04)), (0.14, 0.13, 0.12), ao=0.3, ao_h=0.3, top=0.3, namp=0.2, ns=6))
    for (bx_, tx, ty) in ((-6.0, -4.0, 8.9), (6.4, 4.0, 8.9)):
        pts = H.catenary((bx_, QUAY_Y - 0.45, 0.5), (tx, ty, -0.4), 0.25, 8)
        A.add("battle", "MatThatch_rope", paint(K.tube(pts, 0.03, seg=4, cap=False), (0.42, 0.36, 0.24), ao=0.0))
    # crane rails + rail siding (vista foreground)
    rails = []
    for rx in RAIL_X:
        rails.append(bx(0.12, 22.0, 0.03, (rx, -4.0, -0.01), bev=0.0))
    for ry in (SIDING_Y - 0.72, SIDING_Y + 0.72):
        rails.append(bx(34.0, 0.1, 0.06, (-3.0, ry, -0.02), bev=0.0))
    A.add("battle", "MatMetal_steel", paint(join(rails), (0.42, 0.38, 0.34), ao=0.0, top=0.4))
    sl = [bx(0.24, 2.0, 0.05, (x, SIDING_Y, -0.04), bev=0.0) for x in np.arange(-19.0, 13.0, 0.65) if visible(x, SIDING_Y, 2.0)]
    A.add("battle", "MatWood_wharf", paint(join(sl), (0.30, 0.26, 0.21), ao=0.0, top=0.1, namp=0.2, ns=3))
    # concrete slab joints (dark sealant lines)
    lines = []
    for x in np.arange(-20.0, QUAY_X, 4.0):
        lines.append(P([(x - 0.02, -20, 0.012), (x + 0.02, -20, 0.012), (x + 0.02, DECK_Y - 0.2, 0.012), (x - 0.02, DECK_Y - 0.2, 0.012)], [(0, 1, 2, 3)]))
    for y in np.arange(-20.0, DECK_Y - 0.5, 4.0):
        lines.append(P([(-20, y - 0.02, 0.012), (QUAY_X - 0.1, y - 0.02, 0.012), (QUAY_X - 0.1, y + 0.02, 0.012), (-20, y + 0.02, 0.012)], [(0, 1, 2, 3)]))
    out = []  # split the lines that cross the dish
    for q in lines:
        xs, ys = q.v[:, 0], q.v[:, 1]
        if abs(xs.mean()) < 4.6 and ys.min() < 4.6 and ys.max() > -4.6 and xs.max() - xs.min() < 1:
            # vertical line crossing the dish: two halves
            h = math.sqrt(max(0.0, 4.6 ** 2 - xs.mean() ** 2))
            for (y0, y1) in ((ys.min(), -h), (h, ys.max())):
                if y1 - y0 > 0.1:
                    out.append(P([(xs.min(), y0, 0.012), (xs.max(), y0, 0.012), (xs.max(), y1, 0.012), (xs.min(), y1, 0.012)], [(0, 1, 2, 3)]))
        elif abs(ys.mean()) < 4.6 and xs.min() < 4.6 and xs.max() > -4.6 and ys.max() - ys.min() < 1:
            h = math.sqrt(max(0.0, 4.6 ** 2 - ys.mean() ** 2))
            for (x0, x1) in ((xs.min(), -h), (h, xs.max())):
                if x1 - x0 > 0.1:
                    out.append(P([(x0, ys.min(), 0.012), (x1, ys.min(), 0.012), (x1, ys.max(), 0.012), (x0, ys.max(), 0.012)], [(0, 1, 2, 3)]))
        else:
            out.append(q)
    p = join(out)
    p.c = np.tile([0.26, 0.26, 0.25, 1.0], (len(p.v), 1))
    A.add("battle", "MatPlaster_concrete", p)
    # worn safety-yellow paint: quay-edge line + crane-track margins (dashed, broken where the paint wore off)
    paint_ = []
    rng = random.Random(12)
    for (x0, y0, x1, y1, w) in [(-16.0, DECK_Y - 0.3, QUAY_X - 0.6, DECK_Y - 0.3, 0.14)] +                                [(rx + s * 0.6, -14.0, rx + s * 0.6, DECK_Y - 0.7, 0.1) for rx in RAIL_X for s in (-1, 1)]:
        L = math.hypot(x1 - x0, y1 - y0)
        n = int(L / 0.9)
        tx, ty = (x1 - x0) / L, (y1 - y0) / L
        for i in range(n):
            mx_, my_ = x0 + tx * (i * 0.9 + 0.3), y0 + ty * (i * 0.9 + 0.3)
            if rng.random() < 0.18 or not visible(mx_, my_, 2.0) or math.hypot(mx_, my_) < 5.9:
                continue
            a0, a1 = i * 0.9, i * 0.9 + 0.6
            ax, ay, bx2, by2 = x0 + tx * a0, y0 + ty * a0, x0 + tx * a1, y0 + ty * a1
            nx_, ny_ = -ty * w / 2, tx * w / 2
            q = P([(ax - nx_, ay - ny_, 0.014), (bx2 - nx_, by2 - ny_, 0.014), (bx2 + nx_, by2 + ny_, 0.014), (ax + nx_, ay + ny_, 0.014)], [(0, 1, 2, 3)])
            q.c = np.tile(list(scale((0.78, 0.62, 0.18), rng.uniform(0.75, 1.0))) + [1.0], (4, 1))
            paint_.append(q)
    A.add("battle", "MatPlaster_concrete", paint_)


def apron(A):
    """bollard + hawser coils, crates, pallets, drums -- low clusters."""
    # left: spare bollard bed with a coiled hawser
    A.add("battle", "MatMetal_steel", paint(xf(bollard(), (-5.4, -1.7, 0.0)), (0.14, 0.13, 0.12), ao=0.3, ao_h=0.3, top=0.3, namp=0.2, ns=6))
    A.add("battle", "MatThatch_rope", paint(xf(K.rope_coil(0.5, 0.045, turns=3.6, layers=3, seed=4), (-4.9, -2.9, 0.0)), (0.46, 0.38, 0.24), ao=0.4, ao_h=0.2, top=0.2, namp=0.2, ns=8))
    A.contact(-5.2, -2.3, 1.1, 0.35)
    # right: crate stack on a pallet + loose pallet
    A.add("battle", "MatWood_wharf", paint(xf(pallet(), (5.3, 2.2, 0.0), (0, 0, 0.3)), (0.50, 0.42, 0.30), ao=0.2, ao_h=0.2, top=0.2))
    for i, (x, y, z, rz) in enumerate(((5.1, 2.0, 0.125, 0.3), (5.6, 2.35, 0.125, 0.35))):
        A.add("battle", "MatWood_wharf", xf(crate(0.55, 0.5, 0.45, seed=i + 5), (x, y, z), (0, 0, rz)))
    A.add("battle", "MatWood_wharf", paint(xf(pallet(), (6.3, 0.6, 0.0), (0, 0, 1.2)), (0.46, 0.38, 0.28), ao=0.2, ao_h=0.2, top=0.2))
    A.add("battle", "MatWood_wharf", paint(xf(pallet(), (6.3, 0.6, 0.125), (0, 0, 1.25)), (0.50, 0.42, 0.30), ao=0.2, ao_h=0.2, top=0.2))
    A.contact(5.6, 1.6, 1.4, 0.35)
    # far-band edge: sack pile waiting to be loaded + drums
    A.add("battle", "MatCloth_tarp", xf(sack_pile(8, 50), (-2.6, 6.0, 0.04)))
    A.add("battle", "MatCloth_tarp", xf(sack_pile(6, 60), (3.2, 6.2, 0.04), (0, 0, 0.2)))
    A.contact(-2.6, 6.0, 1.2, 0.3)
    A.contact(3.2, 6.2, 1.1, 0.3)
    # near strip: drums + pallets (vista foreground, low)
    for i, (x, y, rgb) in enumerate(((-4.6, -6.3, (0.62, 0.18, 0.12)), (-4.0, -6.5, (0.20, 0.36, 0.56)))):
        A.add("battle", "MatMetal_steel", xf(drum(rgb), (x, y, 0.0)))
    A.contact(-4.3, -6.4, 1.0, 0.35)
    A.add("battle", "MatWood_wharf", paint(xf(pallet(), (3.6, -6.4, 0.0), (0, 0, 0.1)), (0.50, 0.42, 0.30), ao=0.2, ao_h=0.2, top=0.2))
    A.add("battle", "MatWood_wharf", xf(crate(0.7, 0.6, 0.55, (0.40, 0.46, 0.36), seed=9), (3.6, -6.4, 0.125), (0, 0, 0.15)))


def far_set(A):
    rng = random.Random(9)
    # water: battle strip + far sheet
    v = [(-400, QUAY_Y + 0.1, WATER_Z), (400, QUAY_Y + 0.1, WATER_Z), (400, 420, WATER_Z), (-400, 420, WATER_Z)]
    p = P(v, [(0, 1, 2, 3)])
    p.c = np.tile(list(SEA) + [1.0], (4, 1))
    A.add("far", "MatWater_sea", p)
    v = [(QUAY_X + 0.1, -60, WATER_Z), (60, -60, WATER_Z), (60, QUAY_Y + 0.1, WATER_Z), (QUAY_X + 0.1, QUAY_Y + 0.1, WATER_Z)]
    p = P(v, [(0, 1, 2, 3)])
    p.c = np.tile(list(SEA) + [1.0], (4, 1))
    A.add("battle", "MatWater_sea", p)
    # ferry crossing (left-centre) + container ship at anchor (right) + container-port gantries (far left)
    place_kit(A, "far", ferry_kit(), (-6.0, 34.0, WATER_Z - 0.9), 0.15, NAMES_FAR)
    ship = Kit()
    hull = K.perahu(L=44.0, W=8.0, H=4.2, seed=22)
    ship.put("Metal", tint(paint(hull, (0.18, 0.20, 0.22), ao=0.0, top=0.2), lambda v, c: np.where((v[:, 2] < 1.4)[:, None], np.array([0.50, 0.16, 0.12, 1]), c)))
    cols = [(0.62, 0.20, 0.14), (0.20, 0.38, 0.58), (0.80, 0.66, 0.24), (0.28, 0.50, 0.36), (0.70, 0.70, 0.66), (0.50, 0.26, 0.40)]
    boxes = []
    for i in range(7):
        for j in range(3):
            for kz in range(rng.randint(1, 3)):
                b = bx(5.6, 2.3, 2.3, (-14 + i * 5.9, (j - 1) * 2.4, 4.2 + kz * 2.35), bev=0.0)
                boxes.append(tint(paint(b, cols[rng.randrange(6)], ao=0.0, top=0.2), stripes(0, 3.0, 0.85, 1.0)))
    ship.put("Metal", boxes)
    ship.put("Plaster", paint(join(bx(5.0, 7.0, 7.0, (17.5, 0, 3.8), bev=0.0), bx(6.4, 8.0, 0.4, (17.5, 0, 10.4), bev=0.0)), (0.88, 0.88, 0.86), ao=0.0, top=0.2))
    ship.put("Metal", paint(K.lathe([(0.9, 10.8), (0.9, 13.5), (0, 13.5)], seg=6), (0.25, 0.25, 0.25), ao=0.0))
    place_kit(A, "far", ship, (44.0, 56.0, WATER_Z - 1.2), -0.32, NAMES_FAR)
    for k, x in enumerate((-34.0, -22.0, -10.0)):  # ship-to-shore gantries on the far shore
        g = Kit()
        legs = [K.tube([(sx, sy, 0), (sx, sy, 22)], 0.5, seg=4) for sx in (-4, 4) for sy in (-3, 3)]
        legs += [K.tube([(-14, 0, 22), (26, 0, 22)], 0.7, seg=4), K.tube([(-4, 0, 22), (0, 0, 30), (4, 0, 22)], 0.4, seg=4),
                 K.tube([(0, 0, 30), (-14, 0, 22.5)], 0.2, seg=3), K.tube([(0, 0, 30), (26, 0, 22.5)], 0.2, seg=3)]
        g.put("Metal", tint(paint(join(legs), (0.82, 0.80, 0.78), ao=0.0, top=0.2), lambda v, c: np.where((v[:, 2] > 21)[:, None], np.array([0.75, 0.2, 0.14, 1]), c)))
        place_kit(A, "far", g, (x, 92.0 + 3 * k, 0.5), math.pi / 2 + 0.05, NAMES_FAR)
    # far shore: low hills + Masjid Sultan Abu Bakar on its rise
    mx, my = 23.0, 82.0

    def sh(x, y):
        return (6.0 * math.exp(-(((x - mx) / 30.0) ** 2 + ((y - my - 6) / 14.0) ** 2)) + 5.0 * math.exp(-(((x - 60) / 30.0) ** 2 + ((y - 95) / 14.0) ** 2))
                + 1.0 * nz(x, y, 0, 0.05, 2) + 0.4 + 2.0 * smooth01(84, 100, y))
    A.add("far", "MatLeaf_canopy", paint_hill(hill(-80, 110, 78, 112, sh, nx=70, ny=8, base=WATER_Z - 1), (0.26, 0.32, 0.24), (0.32, 0.38, 0.28), seed=3))
    for k in range(40):
        x, y = rng.uniform(-70, 100), rng.uniform(84, 106)
        if math.hypot(x - mx, y - my) < 14:
            continue
        b = K.canopy(rng.uniform(1.6, 2.8), seed=500 + k, lumps=3, sub=1, squash=0.7, spread=0.6)
        A.add("far", "MatLeaf_canopy", paint(xf(b, (x, y, sh(x, y) + 0.6)), (0.22, 0.30, 0.20), var=0.12, ao=0.0, top=0.35))
    for k in range(12):  # shophouse / office blocks on the far shore
        x = rng.uniform(-60, 90)
        if abs(x - mx) < 18:
            continue
        y = rng.uniform(86, 100)
        w, d, h = rng.uniform(6, 14), rng.uniform(6, 10), rng.uniform(5, 12)
        A.add("far", "MatPlaster_white", tint(paint(bx(w, d, h, (x, y, sh(x, y) - 1.0), bev=0.0), (0.78, 0.78, 0.74) if k % 3 else (0.66, 0.70, 0.72), ao=0.0, top=0.2),
                                              stripes(2, 0.33, 0.82, 1.0)))
    mosque(A, mx, my, sh(mx, my) - 0.2)
    # distant ridge + cloud banks
    def dh(x, y):
        return (22.0 * math.exp(-(((x - 40) / 80.0) ** 2)) + 14.0 * math.exp(-(((x + 70) / 50.0) ** 2)) + 4.0 * nz(x, y, 0, 0.025, 6)) * math.exp(-(((y - 210) / 25.0) ** 2))
    A.add("far", "MatLeaf_canopy", paint_hill(hill(-170, 220, 180, 240, dh, nx=70, ny=5, base=-2), (0.46, 0.52, 0.54), (0.52, 0.58, 0.60), seed=6, top=0.1))
    # overcast cumulus: lobed painted cards (MatSky: unshaded + fog-free, haze painted in toward the horizon grey)
    K.cloud_bank(A, n=7, dist=(260, 420), az=(-44, 32), el=(5.0, 12.0), size=(80, 140), seed=7, mat="MatSky_cloud",
                 top=(0.90, 0.91, 0.90), mid=(0.80, 0.82, 0.82), base=(0.66, 0.70, 0.72))
    K.cloud_bank(A, n=3, dist=(180, 220), az=(-20, 30), el=(10.0, 14.0), size=(50, 80), seed=8, mat="MatSky_cloud",
                 top=(0.92, 0.93, 0.92), mid=(0.82, 0.84, 0.84), base=(0.68, 0.72, 0.74))


def arch(wx, y, z0, z1, w, n=6):
    """arched window/door panel in the XZ plane at depth y: rectangle z0..z1 under a semicircle (fan)."""
    r = w / 2
    v = [(wx - r, y, z0), (wx + r, y, z0), (wx + r, y, z1), (wx - r, y, z1), (wx, y, z1)]
    v += [(wx + r * math.cos(math.pi * i / n), y, z1 + r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    f = [(0, 1, 2, 3)] + [(4, 5 + i, 6 + i) for i in range(n)]
    return P(v, f)


def ferry_kit():
    """passenger ferry: blue hull with white sheer, three white decks with window rows and railings, banded funnel."""
    k = Kit()
    hull = K.perahu(L=16.0, W=4.6, H=1.6, seed=21)
    k.put("Metal", tint(paint(hull, (0.18, 0.30, 0.50), ao=0.0, top=0.2), lambda v, c: np.where((v[:, 2] > 1.2)[:, None], np.array([0.85, 0.85, 0.82, 1]), c)))
    decks = ((10.0, 4.0, 1.6, -0.5, 1.3), (6.0, 3.6, 1.4, -1.0, 2.9), (2.6, 3.0, 1.0, 0.5, 4.3))   # w, d, h, x, z0
    k.put("Plaster", paint(join([bx(w, d, h, (x, 0, z0), bev=0.0) for w, d, h, x, z0 in decks]), (0.86, 0.86, 0.84), ao=0.0, top=0.2))
    wins, rails = [], []
    for i, (w, d, h, x, z0) in enumerate(decks):
        pw = 1.1 if i == 2 else 0.6
        for wx in np.arange(x - w / 2 + 0.6, x + w / 2 - 0.4, pw + 0.35):
            for sy in (-1, 1):
                y = sy * (d / 2 + 0.02)
                q = [(wx, y, z0 + h * 0.35), (wx + pw, y, z0 + h * 0.35), (wx + pw, y, z0 + h * 0.75), (wx, y, z0 + h * 0.75)]
                wins.append(P(q if sy < 0 else q[::-1], [(0, 1, 2, 3)]))
        if i < 2:   # railing round the open deck above this one
            zt = z0 + h
            for sy in (-1, 1):
                rails.append(K.tube([(x - w / 2 + 0.1, sy * (d / 2 - 0.1), zt + 0.8), (x + w / 2 - 0.1, sy * (d / 2 - 0.1), zt + 0.8)], 0.05, seg=3, cap=False))
                rails += [K.tube([(px, sy * (d / 2 - 0.1), zt), (px, sy * (d / 2 - 0.1), zt + 0.8)], 0.035, seg=3, cap=False) for px in np.arange(x - w / 2 + 0.1, x + w / 2, 0.9)]
    k.put("Metal", paint(join(wins), (0.10, 0.13, 0.17), ao=0.0, top=0.0))
    k.put("Plaster", paint(join(rails), (0.92, 0.92, 0.90), ao=0.0, top=0.0))
    funnel = K.lathe([(0.5, 5.3), (0.5, 5.98), (0.5, 6.02), (0.5, 6.28), (0.5, 6.32), (0.5, 6.53), (0.5, 6.57), (0.5, 6.9), (0.42, 7.0), (0, 7.0)], seg=8)
    k.put("Metal", tint(paint(funnel, (0.75, 0.2, 0.15), ao=0.0),
                        lambda v, c: np.where((v[:, 2] > 6.55)[:, None], np.array([0.08, 0.08, 0.08, 1]),
                                              np.where(((v[:, 2] > 6.0) & (v[:, 2] < 6.3))[:, None], np.array([0.92, 0.90, 0.86, 1]), c))))
    return k


def mosque(A, x, y, z0):
    """Masjid Sultan Abu Bakar (stylised): long white hall with dark arched windows in pale frames, blue two-tier
    hipped roofs with dark eave lines over a white clerestory band, four banded corner minarets with balconies and
    domes, a taller banded clock-tower minaret at the front."""
    k = Kit()
    W, D, Hh = 22.0, 12.0, 7.0
    walls = [bx(W, D, Hh + 2.0, (0, 0, -2.0), bev=0.0), bx(10.0, 4.0, Hh - 1.5, (0, -D / 2 - 1.8, -2.0), bev=0.0)]
    win, frame = [], []
    for i in range(9):
        wx = -W / 2 + 1.6 + i * (W - 3.2) / 8
        frame.append(arch(wx, -D / 2 - 0.02, 1.0, 3.9, 1.3))
        win.append(arch(wx, -D / 2 - 0.05, 1.3, 3.8, 0.85))
    for i in range(4):
        wx = -3.6 + i * 2.4
        frame.append(arch(wx, -D / 2 - 3.82, 0.3, 3.0, 1.5))
        win.append(arch(wx, -D / 2 - 3.85, 0.6, 2.9, 1.0))

    def tiered(r0, rise):   # two-tier hipped roof (base at z=0) + its colour bands
        prof = [(r0, 0.0), (r0, 0.22), (r0 * 0.99, 0.25), (r0 * 0.63, rise * 0.375), (r0 * 0.5, rise * 0.38), (r0 * 0.5, rise * 0.385),
                (r0 * 0.5, rise * 0.515), (r0 * 0.56, rise * 0.52), (r0 * 0.56, rise * 0.57), (r0 * 0.55, rise * 0.575), (r0 * 0.08, rise * 0.97), (0, rise)]
        p = K.lathe(prof, seg=4, phase=math.pi / 4, cap0=True)
        z = p.v[:, 2]
        eave = (z < 0.235) | ((z > rise * 0.5175) & (z < rise * 0.5725))
        clere = (z > rise * 0.3825) & (z < rise * 0.5175)
        p.c = np.ones((len(p.v), 4))
        p.c[:, :3] = np.where(eave[:, None], (0.10, 0.18, 0.28), np.where(clere[:, None], (0.90, 0.90, 0.87), (0.26, 0.48, 0.70)))
        return p
    roofs = [xf(tiered(W * 0.78, 6.0), (0, 0, Hh), s=(1.0, D / W * 1.05, 1.0)),
             xf(tiered(6.0, 3.6), (0, -D / 2 - 1.8, Hh - 3.5), s=(1.25, 0.55, 1.0))]
    mins, trim, domes = [], [], []
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (W / 2 - 0.4), sy * (D / 2 - 0.4)
            mins.append(bx(2.2, 2.2, Hh + 6.0, (cx, cy, -2.0), bev=0.0))
            trim += [bx(2.8, 2.8, 0.3, (cx, cy, z), bev=0.0) for z in (Hh + 0.2, Hh + 3.6)]
            trim += [bx(2.3, 2.3, 0.14, (cx, cy, z), bev=0.0) for z in np.arange(0.0, Hh, 1.6)]
            mins.append(xf(K.lathe([(1.0, 0), (1.0, 1.4), (1.15, 1.5), (0, 1.5)], seg=8, phase=math.pi / 8), (cx, cy, Hh + 4.0)))
            domes.append(xf(K.lathe([(1.05, 0), (1.2, 0.6), (0.9, 1.5), (0.3, 2.2), (0.06, 2.9), (0, 3.1)], seg=8), (cx, cy, Hh + 5.5)))
    # front clock tower
    tx, ty = 0.0, -D / 2 - 3.0
    mins.append(bx(3.0, 3.0, Hh + 11.0, (tx, ty, -2.0), bev=0.0))
    trim += [bx(3.6, 3.6, 0.35, (tx, ty, z), bev=0.0) for z in (Hh + 1.0, Hh + 5.2, Hh + 8.6)]
    trim += [bx(3.1, 3.1, 0.16, (tx, ty, z), bev=0.0) for z in np.arange(-0.4, Hh + 1.0, 1.6)]
    mins.append(xf(K.lathe([(1.4, 0), (1.4, 2.0), (1.6, 2.1), (0, 2.1)], seg=8, phase=math.pi / 8), (tx, ty, Hh + 9.0)))
    domes.append(xf(K.lathe([(1.5, 0), (1.7, 0.9), (1.3, 2.0), (0.4, 3.0), (0.08, 3.8), (0, 4.1)], seg=10), (tx, ty, Hh + 11.0)))
    face = P([(tx, ty - 1.52, Hh + 6.6)] + [(tx + 0.8 * math.cos(a), ty - 1.52, Hh + 6.6 + 0.8 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)[:-1]],
             [(0, 1 + i, 1 + (i + 1) % 8) for i in range(8)])
    k.put("Plaster", paint(join(walls, mins), (0.92, 0.91, 0.88), ao=0.0, top=0.2), paint(face, (0.96, 0.94, 0.86), ao=0.0))
    k.put("Plaster", paint(join(frame), (0.60, 0.70, 0.76), ao=0.0, top=0.0), paint(join(win), (0.08, 0.10, 0.13), ao=0.0, top=0.0))
    k.put("Tile", join(roofs), paint(join(trim), (0.22, 0.36, 0.50), ao=0.0, top=0.3), paint(join(domes), (0.28, 0.50, 0.66), ao=0.0, top=0.3))
    place_kit(A, "far", k, (x, y, z0), -0.05, NAMES_FAR)


def build(A):
    for name in ("MatPlaster_concrete", "MatWood_wharf", "MatThatch_rope", "MatCloth_tarp", "MatWater_sea", "MatPlaster_white",
                 "MatTile_roof", "MatRock_quay", "MatLeaf_canopy", "MatSky_cloud"):
        A.mat(name)
    A.mat("MatMetal_steel", rough=0.6, metal=0.35)
    A.mat("MatGlow_warm", emit=(1.0, 0.76, 0.48), estr=2.0)

    godown(A)
    portal_crane(A)
    quay(A)
    apron(A)
    place_kit(A, "battle", tongkang(3), (0.2, 9.15, WATER_Z + 0.15), 0.03, NAMES)
    place_kit(A, "battle", kereta_sorong(), (7.9, 0.0, 0.0), 0.5, NAMES)
    A.add("battle", "MatCloth_tarp", xf(sack_pile(6, 80), (9.0, 1.7, 0.0), (0, 0, 0.4)))
    A.contact(8.3, 0.7, 1.5, 0.35)
    place_kit(A, "battle", tongkang(4), (-11.5, 10.6, WATER_Z + 0.1), -0.06, NAMES)
    A.light((GOD_X - 3.0, 5.1, 3.6), 60.0, (1.0, 0.78, 0.5), range_m=5)
    A.light((9.5, 3.6, 8.4), 40.0, (1.0, 0.85, 0.6), range_m=4)

    A.terrain(ground, gcolor, kind=lambda x, y, z: "MatPlaster_concrete", rin=4.5, rout=90.0, split=23.0, cull=gcull, seed=1)
    rng = random.Random(4)
    for k in range(22):  # weeds in slab joints, along the godown wall and the siding
        if k < 8:
            x, y = rng.uniform(-7.5, 12.0), SIDING_Y + rng.choice((-1.1, 1.1))
        elif k < 14:
            x, y = GOD_X + 0.25, rng.uniform(-7, 9)
        else:
            x, y = rng.choice((-12.0, -8.0, -4.0, 4.0, 8.0, 12.0)) + rng.uniform(-0.1, 0.1), rng.uniform(-7, 4)
        if math.hypot(x, y) < 6.0 or not is_land(x, y):
            continue
        A.scatter_patch("Grass", 24, x, y, rng.uniform(0.15, 0.35), ground, (0.34, 0.40, 0.22), seed=800 + k)
    far_set(A)


if __name__ == "__main__":
    K.main("johor", build, MOOD)
