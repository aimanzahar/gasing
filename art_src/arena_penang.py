"""Penang arena -- George Town night hawker street on the waterfront (design_art.md section c).
Ground: wet asphalt street with puddles, gutters + drain grates, five-foot-way tiles under the shophouse arcade.
Apron: wooden stools + marble tables (low), plates, crates.
Left flank: two-storey shophouse row (arcade, lit shopfronts, signboards, red lanterns).
Far band: hawker carts with zinc canopies and glowing woks, umbrellas, table clusters.
Right flank: trishaw, heritage lamp post with a lantern string, seawall promenade.
Far set (vista): street receding under lantern strings, clan jetty on stilts, Kek Lok Si pagoda lit on a hill
across the channel, Penang Hill ridge with lights, night clouds.

This file also holds the shared helpers used by arena_melaka.py and arena_johor.py (same owner).
  blender -b --factory-startup -P art_src/arena_penang.py -- --export --render game,vista --out <dir>
"""
import sys, os, math, random
sys.dont_write_bytecode = True  # no art_src/__pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)  # blender-mcp re-runs
import numpy as np
from arenakit import P, xf, join, paint, tint, nz, smooth01

# Godot ARENA_DEFS["penang"] recommendation (+ b_* = Blender preview factors only)
MOOD = {"sky_top": (0.05, 0.06, 0.16), "sky_horizon": (0.40, 0.22, 0.30), "fog": (0.22, 0.15, 0.22),
        "fog_density": 0.007, "sun_color": (0.62, 0.70, 1.0), "sun_energy": 0.35,
        "lantern": (1.0, 0.50, 0.28), "lantern_energy": 1.9, "exposure": 1.0, "ambient": 0.5,
        "b_sun": 1.0, "b_world": 0.6, "b_fill": 0.25, "b_lantern": 14.0}


# ================================================================ shared helpers (melaka / johor import these)
def in_vista(x, y):
    dx, dy = x + 1.5, y + 12.5
    return dy > 2 and -58 < math.degrees(math.atan2(dx, dy)) < 44


def visible(x, y, pad=0.0):
    """inside the battle frame or the vista frustum (nothing else is ever seen)."""
    return (y > -6.5 - pad and abs(x) < 11 + 0.55 * (y + 6.5) + pad) or in_vista(x, y)


def scale(rgb, k):
    """uniform brightness jitter (one factor for all channels: no hue shift)."""
    return tuple(c * k for c in rgb)


class Kit(dict):
    """material -> [pieces] in a local frame; place() transforms the whole prop."""

    def put(self, mat, *ps):
        self.setdefault(mat, []).extend(p for p in K._flat(ps) if p is not None)
        return self


def place(A, set_, kit, loc, rz=0.0, s=1.0):
    for mat, ps in kit.items():
        A.add(set_, mat, [xf(p, loc, (0, 0, rz), s) for p in ps])


def bx(sx, sy, sz, loc=(0, 0, 0), bev=0.02, rot=(0, 0, 0)):
    """bevelled box with its base centre at loc."""
    return xf(K.box(sx, sy, sz, bev=bev), loc, rot)


def corrugated(w, d, period=0.14, amp=0.018, ny=1, per=2):
    """corrugated sheet (zinc / clay tile) spanning x in [-w/2,w/2], y in [-d/2,d/2], waves along x.
    per = verts per wave (2 = zig-zag, cheap; 4 = rounded)."""
    nx = max(4, int(round(w / period * per)))
    v, f = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = (i / nx - 0.5) * w
            v.append((x, (j / ny - 0.5) * d, amp * math.sin(2 * math.pi * x / period + 0.5 * math.pi * (per == 2))))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            f.append((a, a + 1, a + nx + 2, a + nx + 1))
    return P(v, f)


def stripes(axis, freq, lo=0.8, hi=1.0, off=0.0):
    """vertex-colour banding along a world axis (louvres, planks, tile courses)."""
    return lambda v, c: c * np.where(np.floor(v[:, axis] * freq + off) % 2 == 0, hi, lo)[:, None]


def catenary(a, b, sag, n=10):
    return [tuple(np.add(a, np.subtract(b, a) * (i / n)) - np.array((0, 0, sag * 4 * (i / n) * (1 - i / n)))) for i in range(n + 1)]


def lantern(z_top=0.0, r=0.15, h=0.30, seg=6, caps=True):
    """Chinese paper lantern hanging from z_top: (glow body, dark caps+tassel)."""
    zc = z_top - 0.05 - h / 2
    prof = ([(0.0, -h / 2), (r * 0.7, -h * 0.4), (r, 0.0), (r * 0.7, h * 0.4), (0.0, h / 2)] if seg > 4 else
            [(0.0, -h / 2), (r, 0.0), (0.0, h / 2)])
    body = xf(K.lathe(prof, seg=seg), (0, 0, zc))
    if not caps:
        return body, None
    cap = [xf(K.lathe([(r * 0.5, 0), (r * 0.5, 0.045), (0, 0.045)], seg=4), (0, 0, zc + h / 2 - 0.01)),
           xf(K.lathe([(0, 0), (r * 0.5, 0), (r * 0.5, 0.04)], seg=4), (0, 0, zc - h / 2 - 0.03)),
           K.tube([(0, 0, zc - h / 2 - 0.03), (0, 0, zc - h / 2 - 0.2)], 0.012, seg=3, cap=False)]
    return body, join(cap)


def lantern_string(A, set_, a, b, n, sag, glow_mat, cap_mat, wire_mat, r=0.15, rgb=(0.95, 0.22, 0.12), seg=6, caps=True,
                   wire_rgb=(0.12, 0.11, 0.1)):
    pts = catenary(a, b, sag, 12)
    A.add(set_, wire_mat, paint(K.tube(pts, 0.008, seg=3, cap=False), wire_rgb, ao=0))
    for i in range(n):
        t = (i + 0.5) / n
        p = np.add(a, np.subtract(b, a) * t) - np.array((0, 0, sag * 4 * t * (1 - t)))
        body, cap = lantern(0.0, r, r * 2.0, seg=seg, caps=caps)
        A.add(set_, glow_mat, paint(xf(body, tuple(p)), rgb, var=0.08, ao=0.0, top=0.0))
        if cap is not None:
            A.add(set_, cap_mat, paint(xf(cap, tuple(p)), (0.20, 0.12, 0.06), ao=0.0, top=0.2))


def hill(x0, x1, y0, y1, hfn, nx=60, ny=8, base=-2.0):
    """heightfield patch (smooth far hill); hfn(x, y) -> z; edges drop to `base`."""
    v, f = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            y = y0 + (y1 - y0) * j / ny
            edge = min(i, nx - i, j, ny - j)
            v.append((x, y, hfn(x, y) if edge else base))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            f.append((a, a + 1, a + nx + 2, a + nx + 1))
    return P(v, f)


def paint_hill(p, low, high, seed=0, top=0.25):
    n = K.vnormals(p)
    z = p.v[:, 2]
    zt = (z - z.min()) / max(1e-6, z.max() - z.min())
    nn = K.nfield(p.v, 0.08, seed)
    c = np.asarray(low)[None, :] * (1 - zt[:, None]) + np.asarray(high)[None, :] * zt[:, None]
    c = c * (1 + 0.18 * nn[:, None]) * (1 + top * n[:, 2:3] - top)
    p.c = np.ones((len(p.v), 4))
    p.c[:, :3] = np.clip(c, 0, 1)
    return p


def cloud(x, y, z, w, h, seed, rgb, under=None):
    """flat-bottomed cumulus bank (smooth blobs, far set). under = darker underside colour."""
    rng = random.Random(seed)
    ps = []
    n = max(3, int(w / (h * 1.9)))
    for i in range(n):
        t = (i + 0.5) / n - 0.5
        rr = h * rng.uniform(0.7, 1.15) * (1.0 - 0.5 * abs(t) * 2) ** 0.5
        b = K.rock(rr, seed=seed * 13 + i, sub=2, amp=0.12, freq=1.2, squash=(1.5, 0.7, 0.75), flat=0.05)
        ps.append(xf(b, (x + t * w, y + rng.uniform(-0.15, 0.15) * h, z + rng.uniform(-0.1, 0.25) * h)))
    p = join(ps)
    zt = smooth01(z, z + h * 1.2, p.v[:, 2])
    lo = np.asarray(under if under else rgb)
    c = lo[None, :] * (1 - zt[:, None]) + np.asarray(rgb)[None, :] * zt[:, None]
    p.c = np.ones((len(p.v), 4))
    p.c[:, :3] = np.clip(c, 0, 1)
    return p


def wheel(R=0.3, r=0.014, spokes=6, rim=12):
    """light spoked wheel in the XZ plane (axle along y), centred at the origin."""
    ring = [(R * math.cos(2 * math.pi * i / rim), 0, R * math.sin(2 * math.pi * i / rim)) for i in range(rim + 1)]
    ps = [K.tube(ring, r * 1.6, seg=3, cap=False)]
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        ps.append(K.tube([(0, 0, 0), (R * math.cos(a), 0, R * math.sin(a))], r * 0.6, seg=3, cap=False))
    ps.append(xf(K.lathe([(0, -0.035), (0.04, -0.035), (0.04, 0.035), (0, 0.035)], seg=6), rot=(math.pi / 2, 0, 0)))
    return join(ps)


def dot(x, y, z, s=0.5, face=(-1.5, -12.5, 3.2)):
    """tiny quad facing the vista camera (distant window / lamp light; 4 verts)."""
    d = np.subtract(face, (x, y, z))
    d[2] = 0.0
    d /= max(1e-6, np.linalg.norm(d))
    sx, sy = -d[1] * s / 2, d[0] * s / 2
    return P([(x - sx, y - sy, z), (x + sx, y + sy, z), (x + sx, y + sy, z + s), (x - sx, y - sy, z + s)], [(0, 1, 2, 3)])


def stool(seed=0, h=0.45, r=0.16):
    """round wooden kopitiam stool: seat disc + 4 splayed legs. base z=0."""
    seat = xf(K.lathe([(r * 0.9, 0), (r, 0.03), (r * 0.95, 0.045), (0, 0.045)], seg=8, cap0=False), (0, 0, h - 0.045))
    legs = []
    for k in range(3):
        a = math.pi / 6 + k * 2 * math.pi / 3
        legs.append(K.tube([(r * 0.95 * math.cos(a), r * 0.95 * math.sin(a), 0), (r * 0.55 * math.cos(a), r * 0.55 * math.sin(a), h - 0.04)],
                           0.02, seg=3, cap=False))
    return join(seat, legs)


def marble_table(r=0.38, h=0.74):
    """(marble top, iron pedestal) base z=0."""
    top = K.lathe([(r * 0.9, h - 0.04), (r, h - 0.03), (r * 1.01, h - 0.012), (r * 0.97, h), (0, h)], seg=14, cap0=False)
    ped = K.lathe([(0.22, 0), (0.2, 0.03), (0.05, 0.08), (0.04, h - 0.06), (0.12, h - 0.04)], seg=6, cap0=False, cap1=False)
    return top, ped


def table_set(seed, n=4, stool_rgb=(0.40, 0.26, 0.15)):
    rng = random.Random(seed)
    k = Kit()
    top, ped = marble_table()
    k.put("Plaster", tint(paint(top, (0.66, 0.64, 0.60), ao=0.0, top=0.2), lambda v, c: c * (0.9 + 0.1 * K.nfield(v, 6.0, seed))[:, None]))
    k.put("Metal", paint(ped, (0.16, 0.15, 0.14), ao=0.2, ao_h=0.3))
    a0 = rng.uniform(0, 6.28)
    for i in range(n):
        a = a0 + 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        d = rng.uniform(0.55, 0.72)
        k.put("Wood", paint(xf(stool(seed + i), (d * math.cos(a), d * math.sin(a), 0), (0, 0, rng.uniform(0, 3))),
                            scale(stool_rgb, rng.uniform(0.85, 1.12)), var=0.05, ao=0.3, ao_h=0.4))
    return k


def umbrella(r=1.25, h=2.3, cols=((0.78, 0.16, 0.12), (0.86, 0.82, 0.74)), panels=8):
    """hawker umbrella: alternating panels, pole + weighted base. returns Kit (Cloth, Metal)."""
    seg = panels * 2
    can = K.lathe([(0.0, h + 0.02), (r * 0.15, h - 0.04), (r * 0.6, h - 0.32), (r, h - 0.62), (r * 0.98, h - 0.68)], seg=seg,
                  cap0=False, cap1=False, phase=math.pi / seg)
    paint(can, (1, 1, 1), ao=0.0, top=0.25)
    ang = np.arctan2(can.v[:, 1], can.v[:, 0])
    pid = np.floor((ang + math.pi) / (2 * math.pi) * panels + 1e-4).astype(int) % 2
    can.c[:, :3] *= np.where(pid[:, None] == 0, np.asarray(cols[0]), np.asarray(cols[1]))
    k = Kit()
    k.put("Cloth", can)
    k.put("Metal", paint(join(K.tube([(0, 0, 0.05), (0, 0, h)], 0.025, seg=5),
                              K.lathe([(0, 0), (0.22, 0), (0.2, 0.08), (0.05, 0.1), (0, 0.1)], seg=8)), (0.2, 0.2, 0.21), ao=0.3))
    return k


def wok_flames(r=0.3, n=9, h=0.16, seed=0):
    """ring of flame tongues around a wok rim (glow, double sided)."""
    rng = random.Random(seed)
    ps = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.2, 0.2)
        hh = h * rng.uniform(0.6, 1.3)
        path = [((r * 0.9) * math.cos(a), (r * 0.9) * math.sin(a), -0.06),
                ((r * 1.02) * math.cos(a), (r * 1.02) * math.sin(a), hh * 0.5),
                ((r * 0.95) * math.cos(a + 0.15), (r * 0.95) * math.sin(a + 0.15), hh)]
        ps.append(K.dbl(K.strip_mesh(path, [0.05, 0.035, 0.003], up=(math.cos(a), math.sin(a), 0), seed=seed + i)))
    return join(ps)


def hawker_cart(body_rgb, sign_rgb, seed=0, wok=True, canopy=True, valance=((0.75, 0.14, 0.1), (0.9, 0.86, 0.76)), lod=0):
    """mobile hawker stall, serving side facing -y. Kit keys: Wood, Metal, Cloth, Glow, Plaster, Fire."""
    rng = random.Random(seed)
    k = Kit()
    # body on legs + bicycle wheels
    body = bx(1.7, 0.8, 0.8, (0, 0, 0.22), bev=0.03)
    body = tint(paint(body, body_rgb, var=0.05, ao=0.35, ao_h=0.6, top=0.15),
                lambda v, c: np.where(((v[:, 2] > 0.86) & (v[:, 2] < 0.94))[:, None], np.array([0.92, 0.88, 0.8, 1.0]), c))
    k.put("Wood", body, paint(bx(1.8, 0.9, 0.05, (0, 0, 1.0), bev=0.015), (0.42, 0.30, 0.2), ao=0.0))
    for sx in (0.75,):
        for sy in (-0.32, 0.32):
            k.put("Metal", paint(bx(0.06, 0.06, 0.24, (sx, sy, 0.0), bev=0.0), (0.18, 0.18, 0.18), ao=0.0))
    if lod == 0:
        for sy in (-0.47, 0.47):
            k.put("Metal", paint(xf(wheel(0.3, 0.014), (-0.6, sy, 0.3)), (0.12, 0.12, 0.12), ao=0.0))
    # glass food case (lit) + frame + sign
    k.put("Glow", glow_grad(paint(bx(1.36, 0.52, 0.42, (0, 0.04, 1.05), bev=0.0), (0.82, 0.60, 0.34), ao=0.0, top=0.0)))
    frame = []
    for sx in (-0.7, 0.7):
        for sy in (-0.24, 0.32):
            frame.append(bx(0.035, 0.035, 0.48, (sx, sy, 1.03), bev=0.0))
    frame.append(bx(1.46, 0.62, 0.035, (0, 0.04, 1.49), bev=0.0))
    k.put("Metal", paint(join(frame), (0.62, 0.6, 0.55), ao=0.0, top=0.3))
    sign = bx(1.62, 0.06, 0.3, (0, -0.24, 1.53), bev=0.012)
    k.put("Wood", tint(paint(sign, sign_rgb, ao=0.0, top=0.1),
                       lambda v, c: np.where(((np.abs(v[:, 0]) < 0.62) & (v[:, 2] > 1.6) & (v[:, 2] < 1.76) & (np.floor(v[:, 0] * 9) % 2 == 0))[:, None],
                                             np.array([0.95, 0.82, 0.35, 1.0]), c)))
    # zinc canopy on posts + cloth valance
    if canopy:
        for sx in (-0.82, 0.82):
            for sy in (-0.36, 0.38):
                k.put("Metal", paint(K.tube([(sx, sy, 1.0), (sx * 1.02, sy * 1.05, 2.18)], 0.02, seg=4), (0.3, 0.3, 0.3), ao=0.0))
        roof = xf(corrugated(2.3, 1.75, 0.13, 0.02), (0.15, 0.0, 2.2), (0.09, 0, 0))
        zc = (0.46, 0.47, 0.47) if rng.random() < 0.6 else (0.52, 0.40, 0.30)
        k.put("Metal", tint(paint(K.dbl(roof), zc, var=0.05, ao=0.0, top=0.25, namp=0.25, ns=2.0),
                            lambda v, c: c * (0.85 + 0.25 * smooth01(-0.4, 0.6, np.array([nz(a, b, 0, 1.6, seed) for a, b, _ in v])))[:, None]))
        val = K.grid(2.3, 0.26, 12, 1)
        val = xf(val, (0.15, -0.88, 2.0), (math.pi / 2, 0, 0))
        val.c = None
        paint(val, (1, 1, 1), ao=0.0, top=0.0)
        sid = np.floor((val.v[:, 0] + 1.2) / 0.19).astype(int) % 2
        val.c[:, :3] *= np.where(sid[:, None] == 0, np.asarray(valance[0]), np.asarray(valance[1]))
        k.put("Cloth", val)
        k.put("Glow", paint(xf(K.lathe([(0, -0.07), (0.045, -0.05), (0.05, 0.0), (0.02, 0.04), (0, 0.05)], seg=6), (0.2, 0.0, 1.88)), (1, 0.9, 0.7), ao=0))
        k.put("Metal", paint(K.tube([(0.2, 0.0, 1.93), (0.2, 0.0, 2.2)], 0.006, seg=3), (0.1, 0.1, 0.1), ao=0))
    # wok station: stove, wok, flames, gas tank
    if wok and lod == 0:
        k.put("Metal", paint(bx(0.62, 0.62, 0.74, (1.22, -0.02, 0.0), bev=0.02), (0.22, 0.21, 0.2), ao=0.4, ao_h=0.5, namp=0.15, ns=6))
        wk = K.lathe([(0, 0.0), (0.12, 0.005), (0.24, 0.04), (0.32, 0.11), (0.335, 0.125), (0.3, 0.11), (0.22, 0.05), (0.1, 0.02), (0, 0.016)], seg=14)
        k.put("Metal", tint(paint(xf(wk, (1.22, -0.02, 0.8)), (0.12, 0.11, 0.1), ao=0.0, top=0.0),
                            lambda v, c: np.where((v[:, 2] > 0.81)[:, None] & (np.hypot(v[:, 0] - 1.22, v[:, 1] + 0.02) < 0.27)[:, None],
                                                  np.array([0.62, 0.40, 0.18, 1.0]), c)))
        k.put("Fire", paint(xf(wok_flames(0.31, 9, 0.17, seed), (1.22, -0.02, 0.8)), (1.0, 0.62, 0.22), ao=0.0, top=0.0))
        k.put("Metal", paint(K.tube([(1.5, -0.02, 0.85), (1.85, -0.1, 0.95)], 0.012, seg=4), (0.4, 0.3, 0.2), ao=0))
        tank = K.lathe([(0, 0), (0.15, 0), (0.15, 0.42), (0.1, 0.52), (0.04, 0.55), (0.04, 0.6), (0, 0.6)], seg=10)
        k.put("Metal", paint(xf(tank, (1.25, 0.52, 0.0)), (0.72, 0.30, 0.14), ao=0.35, ao_h=0.3, top=0.2))
    if lod:
        return k
    # bowls + tray on the counter edge
    bowl = K.lathe([(0, 0), (0.06, 0), (0.09, 0.05), (0.08, 0.05), (0.05, 0.012), (0, 0.012)], seg=8)
    for i in range(4):
        k.put("Plaster", paint(xf(bowl, (-0.62 + 0.03 * (i % 2), -0.3, 1.03 + 0.045 * i)), (0.88, 0.87, 0.82), ao=0.0, top=0.2))
    return k


def trishaw(seat_rgb=(0.55, 0.12, 0.10), frame_rgb=(0.14, 0.13, 0.12)):
    """Penang beca: passenger seat in front (-y), rider behind. Kit keys: Metal, Cloth, Wood."""
    k = Kit()
    whl = []
    for sx in (-0.5, 0.5):
        whl.append(xf(wheel(0.33, 0.016, 10), (sx, -0.1, 0.33), (0, 0, math.pi / 2)))
    whl.append(xf(wheel(0.33, 0.016, 10), (0, 1.35, 0.33), (0, 0, math.pi / 2)))
    k.put("Metal", paint(join(whl), (0.10, 0.10, 0.10), ao=0.0))
    fr = [K.tube([(-0.5, -0.1, 0.33), (0.5, -0.1, 0.33)], 0.022, seg=5),
          K.tube([(-0.45, -0.1, 0.33), (-0.42, 0.3, 0.62), (0, 0.55, 0.62), (0, 1.0, 0.95), (0, 1.35, 0.33)], 0.025, seg=5),
          K.tube([(0.45, -0.1, 0.33), (0.42, 0.3, 0.62), (0, 0.55, 0.62)], 0.025, seg=5),
          K.tube([(0, 1.0, 0.95), (0, 1.02, 1.08)], 0.02, seg=4),
          K.tube([(-0.28, 0.72, 1.12), (0, 0.78, 1.0), (0.28, 0.72, 1.12)], 0.016, seg=4),
          K.tube([(0, 1.35, 0.33), (0.0, 1.1, 0.3)], 0.03, seg=4)]
    k.put("Metal", paint(join(fr), frame_rgb, ao=0.0, top=0.3))
    k.put("Cloth", paint(bx(0.26, 0.12, 0.06, (0, 1.02, 1.06), bev=0.02), (0.1, 0.09, 0.08), ao=0))  # rider saddle
    # passenger seat tub
    tub = [bx(0.96, 0.55, 0.12, (0, 0.18, 0.6), bev=0.03), bx(0.96, 0.1, 0.5, (0, 0.44, 0.66), bev=0.03)]
    for sx in (-0.5, 0.5):
        tub.append(bx(0.06, 0.6, 0.32, (sx, 0.16, 0.62), bev=0.02))
    k.put("Wood", paint(join(tub), (0.35, 0.10, 0.08), var=0.03, ao=0.2, ao_h=0.8, top=0.25))
    k.put("Cloth", paint(bx(0.86, 0.46, 0.08, (0, 0.16, 0.72), bev=0.035), seat_rgb, ao=0.0, top=0.3))
    k.put("Metal", paint(bx(0.8, 0.32, 0.03, (0, -0.32, 0.36), bev=0.01), (0.55, 0.55, 0.52), ao=0.0, top=0.3))  # footboard
    # folded hood: arched ribs + cloth over the back of the seat
    arch = [(0.5 * math.cos(a), 0.56 + 0.22 * math.sin(a), 0.78 + 0.34 * math.sin(a)) for a in np.linspace(0, math.pi, 9)]
    hood = K.dbl(K.strip_mesh(arch, [0.16] * len(arch), up=(0, 1, 0), seed=3))
    k.put("Cloth", tint(paint(hood, (0.30, 0.08, 0.08), ao=0.0, top=0.2), stripes(1, 14, 0.7, 1.0)))
    for dy in (-0.08, 0.1):
        k.put("Metal", paint(K.tube([(p[0], p[1] + dy, p[2]) for p in arch], 0.008, seg=3, cap=False), (0.5, 0.5, 0.48), ao=0))
    return k


def satay_grill(seed=0):
    """low charcoal trough on legs with glowing coals and skewers. Kit keys: Metal, Glow, Wood. base z=0, long axis x."""
    k = Kit()
    k.put("Metal", paint(join(bx(1.2, 0.34, 0.16, (0, 0, 0.5), bev=0.015),
                              *[K.tube([(sx, sy, 0.0), (sx * 0.95, sy * 0.9, 0.52)], 0.016, seg=3, cap=False) for sx in (-0.55, 0.55) for sy in (-0.13, 0.13)]),
                         (0.16, 0.15, 0.14), ao=0.2, ao_h=0.6, namp=0.2, ns=8))
    k.put("Glow", paint(bx(1.1, 0.26, 0.015, (0, 0, 0.655), bev=0.0), (1.0, 0.55, 0.2), ao=0.0, top=0.0))
    rng = random.Random(seed)
    sticks = []
    for i in range(14):
        x, y0 = -0.5 + 0.075 * i, rng.uniform(-0.03, 0.03)
        q = P([(x - 0.012, y0 - 0.21, 0.672), (x + 0.012, y0 - 0.21, 0.672), (x + 0.012, y0 + 0.21, 0.672), (x - 0.012, y0 + 0.21, 0.672),
               (x - 0.03, y0 - 0.06, 0.68), (x + 0.03, y0 - 0.06, 0.68), (x + 0.03, y0 + 0.06, 0.68), (x - 0.03, y0 + 0.06, 0.68)],
              [(0, 1, 2, 3), (4, 5, 6, 7)])
        q.c = np.array([[0.50, 0.30, 0.14, 1]] * 4 + [[0.42, 0.20, 0.08, 1]] * 4)
        sticks.append(q)
    k.put("Wood", join(sticks))
    return k


def bicycle(frame_rgb=(0.12, 0.26, 0.30)):
    """old roadster on its stand. Kit keys: Metal, Cloth. base z=0, long axis y."""
    k = Kit()
    k.put("Metal", paint(join(xf(wheel(0.34, 0.012, 8), (0, -0.55, 0.34), (0, 0, math.pi / 2)),
                              xf(wheel(0.34, 0.012, 8), (0, 0.55, 0.34), (0, 0, math.pi / 2))), (0.08, 0.08, 0.08), ao=0.0))
    fr = [K.tube([(0, -0.55, 0.34), (0, -0.05, 0.36), (0, 0.1, 0.92), (0, -0.45, 0.88), (0, -0.55, 0.34)], 0.018, seg=4),
          K.tube([(0, -0.05, 0.36), (0, 0.48, 0.86), (0, 0.55, 0.34)], 0.018, seg=4),
          K.tube([(0, 0.48, 0.86), (0, 0.5, 1.02)], 0.016, seg=4),
          K.tube([(-0.26, 0.45, 1.04), (0, 0.5, 1.02), (0.26, 0.45, 1.04)], 0.012, seg=4),
          K.tube([(0, -0.45, 0.88), (0, -0.47, 0.98)], 0.014, seg=4)]
    k.put("Metal", paint(join(fr), frame_rgb, ao=0.0, top=0.3))
    k.put("Cloth", paint(bx(0.12, 0.24, 0.05, (0, -0.48, 0.98), bev=0.02), (0.1, 0.08, 0.06), ao=0.0))
    k.put("Metal", paint(bx(0.26, 0.3, 0.03, (0, -0.72, 0.62), bev=0.0), (0.4, 0.4, 0.38), ao=0.0))  # rear rack
    return k


def potted_plant(seed=0, h=0.7, pot_rgb=(0.55, 0.30, 0.20), leaf_rgb=(0.20, 0.36, 0.16)):
    """clay pot + leafy mass. Kit keys: Tile, Leaf."""
    rng = random.Random(seed)
    k = Kit()
    r = 0.18 * rng.uniform(0.85, 1.15)
    k.put("Tile", paint(K.lathe([(r * 0.7, 0), (r, 0.3), (r * 1.08, 0.33), (r * 1.05, 0.36), (r * 0.92, 0.34)], seg=8, cap0=False, cap1=False),
                        pot_rgb, ao=0.3, ao_h=0.3, top=0.2))
    lv = [xf(K.rock(h * rng.uniform(0.22, 0.32), seed=seed * 5 + i, sub=2, amp=0.35, freq=2.2, squash=(1, 1, 1.1), flat=0.6),
             (rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), 0.3 + 0.12 * i)) for i in range(2)]
    k.put("Leaf", paint(join(lv), leaf_rgb, var=0.1, ao=0.4, ao_h=h, top=0.4, namp=0.2, ns=6))
    return k


def heritage_lamp(h=3.4):
    """black cast-iron post with a lantern head. Kit keys: Metal, Glow. base z=0."""
    k = Kit()
    post = K.lathe([(0, 0), (0.2, 0), (0.18, 0.12), (0.1, 0.2), (0.11, 0.55), (0.07, 0.62), (0.055, h - 0.4), (0.08, h - 0.36),
                    (0.08, h - 0.3), (0, h - 0.3)], seg=8)
    head = K.lathe([(0, h - 0.3), (0.1, h - 0.3), (0.17, h - 0.02), (0.13, h + 0.02), (0, h + 0.02)], seg=4, phase=math.pi / 4)
    cap = K.lathe([(0, h + 0.02), (0.2, h + 0.02), (0.12, h + 0.14), (0.02, h + 0.22), (0, h + 0.26)], seg=4, phase=math.pi / 4)
    k.put("Metal", paint(join(post, cap), (0.08, 0.08, 0.09), ao=0.2, ao_h=0.5, top=0.3))
    k.put("Glow", paint(head, (1.0, 0.92, 0.72), ao=0.0, top=0.0))
    return k


def tile_floor(x0, x1, y0, y1, z, size=0.3, cols=((0.55, 0.30, 0.20), (0.62, 0.36, 0.24), (0.48, 0.26, 0.18)), border=None, seed=0,
               cull=None):
    """grid of separate square tiles (crisp vertex-colour pattern) on a flat plane."""
    rng = random.Random(seed)
    v, f, c = [], [], []
    nx_, ny_ = max(1, int(round((x1 - x0) / size))), max(1, int(round((y1 - y0) / size)))
    sx, sy = (x1 - x0) / nx_, (y1 - y0) / ny_
    for j in range(ny_):
        for i in range(nx_):
            ax, ay = x0 + i * sx, y0 + j * sy
            if cull and cull(ax + sx / 2, ay + sy / 2):
                continue
            col = np.asarray(cols[(i + j) % 2] if len(cols) < 3 or (i + j) % 5 else cols[2]) * rng.uniform(0.88, 1.08)
            if border is not None and (i == 0 or i == nx_ - 1):
                col = np.asarray(border) * rng.uniform(0.9, 1.05)
            g = 0.012
            b = len(v)
            v += [(ax + g, ay + g, z), (ax + sx - g, ay + g, z), (ax + sx - g, ay + sy - g, z), (ax + g, ay + sy - g, z)]
            f.append((b, b + 1, b + 2, b + 3))
            c += [list(col) + [1.0]] * 4
    p = P(v, f)
    p.c = np.clip(np.array(c), 0, 1)
    return p


def window_sash(w, h, lit, shutter_rgb, glow_rgb=(1.0, 0.8, 0.5), louvre=True):
    """recessed window: lit pane (Glow) or closed louvred shutters (Wood). local: bottom-centre, faces -y."""
    k = Kit()
    if lit:
        k.put("Glow", paint(bx(w, 0.04, h, (0, 0.12, 0), bev=0.0), glow_rgb, ao=0.0, top=0.0))
        mull = [bx(0.05, 0.05, h, (0, 0.06, 0), bev=0.0), bx(w, 0.05, 0.05, (0, 0.06, h * 0.62), bev=0.0)]
        half = 0.5 * w
        for sx in (-1, 1):  # shutters folded open against the reveal
            mull.append(bx(0.05, half, h * 0.98, (sx * (w / 2 + 0.04), -half / 2 + 0.02, 0.01), bev=0.0))
        k.put("Wood", tint(paint(join(mull), shutter_rgb, ao=0.0, top=0.2), stripes(2, 14, 0.78, 1.0)))
    else:
        sh = join(bx(w / 2 - 0.01, 0.05, h, (-w / 4, 0.06, 0), bev=0.0), bx(w / 2 - 0.01, 0.05, h, (w / 4, 0.06, 0), bev=0.0))
        k.put("Wood", tint(paint(sh, shutter_rgb, ao=0.0, top=0.2), stripes(2, 14, 0.72, 1.0) if louvre else (lambda v, c: c)))
    return k


def shophouse(W=4.4, D=6.0, GF=3.5, UF=3.2, wall=(0.62, 0.74, 0.66), trim=(0.88, 0.86, 0.80), shutter=(0.22, 0.42, 0.36),
              lit=(True, False), shop_open=True, sign=(0.12, 0.10, 0.09), sign_text=(0.92, 0.74, 0.30), seed=0, lod=0,
              lanterns=True, roof_rgb=(0.52, 0.28, 0.20), last_col=False, tiles_rgb=None):
    """Straits-eclectic two-storey shophouse. Local frame: facade (column line) at y=0 facing -y, x across,
    five-foot-way arcade y 0..FW, shop interior beyond. Kit keys: Plaster, Wood, Tile, Glow, Lantern, Metal."""
    rng = random.Random(seed)
    k = Kit()
    FW = 1.8
    bev = 0.025 if lod == 0 else 0.0
    H = GF + UF
    wall_c = scale(wall, rng.uniform(0.94, 1.04))
    if lod >= 2:  # distant block: upper facade, recessed arcade, one column, lit openings, roof plane
        k.put("Plaster", paint(join(bx(W, 0.3, UF + 0.6, (0, 0.0, GF), bev=0.0), bx(0.36, 0.36, GF, (-W / 2, 0.15, 0), bev=0.0)), wall_c, ao=0.0, top=0.1),
              paint(bx(W, 0.2, GF, (0, FW, 0), bev=0.0), tuple(c * 0.55 for c in wall_c), ao=0.0))
        for i, x in enumerate((-W / 4, W / 4)):
            q = P([(x - 0.45, -0.02, GF + 0.6), (x + 0.45, -0.02, GF + 0.6), (x + 0.45, -0.02, GF + 2.5), (x - 0.45, -0.02, GF + 2.5)], [(0, 1, 2, 3)])
            k.put("Glow" if lit[i % len(lit)] else "Wood", paint(q, (1.0, 0.8, 0.5) if lit[i % len(lit)] else shutter, ao=0.0, top=0.0))
        if shop_open:
            k.put("Glow", paint(P([(-1, FW - 0.02, 0), (1, FW - 0.02, 0), (1, FW - 0.02, 2.6), (-1, FW - 0.02, 2.6)], [(0, 1, 2, 3)]), (1.0, 0.82, 0.55), ao=0.0, top=0.0))
        k.put("Tile", paint(P([(-W / 2, 0.3, H + 0.6), (W / 2, 0.3, H + 0.6), (W / 2, D * 0.6, H + 2.2), (-W / 2, D * 0.6, H + 2.2)], [(0, 1, 2, 3)]),
                            roof_rgb, ao=0.0, top=0.3))
        return k
    pl = []  # plaster pieces (wall colour)
    tr = []  # plaster trim (cream)
    # arcade columns
    for sx in ((-W / 2, W / 2) if last_col else (-W / 2,)):
        if lod == 0:
            tr.append(bx(0.46, 0.46, 0.3, (sx, 0.15, 0.0), bev=bev))
            pl.append(bx(0.34, 0.34, GF - 0.5, (sx, 0.15, 0.3), bev=bev))
            tr.append(bx(0.46, 0.46, 0.2, (sx, 0.15, GF - 0.42), bev=bev))
        else:
            pl.append(bx(0.36, 0.36, GF, (sx, 0.15, 0.0), bev=0.0))
    # shopfront wall with a door opening
    dw = 2.0 if shop_open else 1.9
    pl.append(bx(W / 2 - dw / 2, 0.2, GF, (-(W / 2 + dw / 2) / 2, FW + 0.1, 0), bev=0.0))
    pl.append(bx(W / 2 - dw / 2, 0.2, GF, ((W / 2 + dw / 2) / 2, FW + 0.1, 0), bev=0.0))
    pl.append(bx(dw, 0.2, GF - 2.7, (0, FW + 0.1, 2.7), bev=0.0))
    if shop_open:
        k.put("Glow", paint(bx(dw, 0.05, 2.7, (0, FW + 1.1, 0), bev=0.0), (1.0, 0.82, 0.55), ao=0.0, top=0.0))
        if lod == 0:  # counter + shelves silhouettes inside
            k.put("Wood", paint(join(bx(dw * 0.7, 0.45, 0.95, (0.15, FW + 0.6, 0), bev=0.02),
                                     bx(0.08, 0.3, 2.2, (-dw / 2 + 0.25, FW + 0.85, 0), bev=0.0),
                                     bx(0.9, 0.3, 0.05, (-dw / 2 + 0.7, FW + 0.85, 1.4), bev=0.0),
                                     bx(0.9, 0.3, 0.05, (-dw / 2 + 0.7, FW + 0.85, 1.9), bev=0.0)), (0.30, 0.20, 0.13), ao=0.3, ao_h=1.0))
    else:  # folding timber doors
        k.put("Wood", tint(paint(bx(dw, 0.06, 2.7, (0, FW + 0.12, 0), bev=0.0), shutter, ao=0.3, ao_h=1.0), stripes(0, 3.5, 0.8, 1.0)))
    # side windows on the shopfront (grilled)
    if lod == 0:
        for sx in (-1, 1):
            k.put("Wood", tint(paint(bx(0.6, 0.05, 1.0, (sx * (W / 2 + dw / 2) / 2, FW - 0.01, 1.0), bev=0.0), (0.16, 0.14, 0.12), ao=0.0),
                               stripes(0, 12, 0.6, 1.0)))
    # signboard over the door
    sg = bx(dw + 0.6, 0.08, 0.5, (0, FW - 0.05, 2.82), bev=0.015)
    k.put("Wood", tint(paint(sg, sign, ao=0.0, top=0.1),
                       lambda v, c: np.where(((np.abs(np.abs(v[:, 0]) - (dw + 0.6) / 2) < 0.05) | (v[:, 2] < 2.86) | (v[:, 2] > 3.28)
                                              | ((np.abs(v[:, 0]) < dw * 0.4) & (v[:, 2] > 2.96) & (v[:, 2] < 3.18) & (np.floor(v[:, 0] * 5.5) % 2 == 0)))[:, None],
                                             np.array(list(sign_text) + [1.0]), c)))
    # arcade ceiling slab (front face = band between floors)
    pl.append(bx(W, FW + 0.25, 0.3, (0, FW / 2 - 0.05, GF - 0.3), bev=0.0))
    tr.append(bx(W + 0.06, 0.32, 0.22, (0, -0.1, GF - 0.08), bev=bev))
    # upper floor facade with two windows
    ww, wh, wz = 0.95, 1.95, GF + 0.55
    xs = (-W / 4, W / 4)
    edges = [-W / 2, xs[0] - ww / 2, xs[0] + ww / 2, xs[1] - ww / 2, xs[1] + ww / 2, W / 2]
    for a, b in ((edges[0], edges[1]), (edges[2], edges[3]), (edges[4], edges[5])):
        pl.append(bx(b - a, 0.25, UF, ((a + b) / 2, 0.05, GF), bev=0.0))
    for x in xs:
        pl.append(bx(ww, 0.25, 0.55, (x, 0.05, GF), bev=0.0))
        pl.append(bx(ww, 0.25, UF - 0.55 - wh, (x, 0.05, wz + wh), bev=0.0))
        if lod == 0:
            tr.append(bx(ww + 0.24, 0.16, 0.12, (x, -0.07, wz + wh + 0.06), bev=0.02))   # window hood
            tr.append(bx(ww + 0.12, 0.12, 0.07, (x, -0.04, wz - 0.06), bev=0.01))       # sill
            fan = K.lathe([(0, 0), (ww * 0.42, 0), (0, 0.001)], seg=10, cap0=False, cap1=False)  # fanlight half disc
            fan = xf(P([(0, 0, 0)] + [(ww * 0.42 * math.cos(a), 0, ww * 0.42 * math.sin(a)) for a in np.linspace(0, math.pi, 7)],
                       [(0, i + 1, i + 2) for i in range(6)]), (x, -0.08, wz + wh + 0.2))
            tr.append(K.dbl(fan))
    for i, x in enumerate(xs):
        if lod:
            lt = lit[i % len(lit)]
            k.put("Glow" if lt else "Wood", paint(bx(ww, 0.04, wh, (x, 0.12, wz), bev=0.0), (1.0, 0.8, 0.5) if lt else shutter, ao=0.0, top=0.0))
            continue
        ws = window_sash(ww, wh, lit[i % len(lit)], shutter)
        for mat, ps in ws.items():
            k.put(mat, [xf(p, (x, 0.0, wz)) for p in ps])
    # pilasters + cornices + parapet
    for sx in (-W / 2, W / 2):
        tr.append(bx(0.28, 0.14, UF, (sx, -0.06, GF), bev=0.0))
    tr.append(bx(W + 0.16, 0.42, 0.24, (0, -0.06, H - 0.04), bev=bev))
    pl.append(bx(W, 0.22, 0.42, (0, 0.04, H + 0.2), bev=0.0))
    tr.append(bx(W + 0.1, 0.3, 0.07, (0, 0.04, H + 0.62), bev=0.01))
    # roof: clay tile front slope behind the parapet + side walls hint
    roof = xf(corrugated(W + 0.1, D * 0.62, 0.3, 0.05, ny=1 if lod else 2), (0, 0.3 + D * 0.31, 0), (0, 0, 0))
    roof.v[:, 2] += H + 0.35 + (roof.v[:, 1] - 0.3) * 0.42
    rr = scale(roof_rgb, rng.uniform(0.9, 1.08))
    k.put("Tile", tint(paint(K.dbl(roof), rr, var=0.06, ao=0.0, top=0.3, namp=0.2, ns=1.2), stripes(1, 2.2, 0.82, 1.0)))
    pl.append(bx(W, 0.2, H + 1.0, (0, D * 0.62 + 0.3, 0), bev=0.0))   # rear party wall (hides the void)
    if lod == 0:  # party walls between houses (fire walls with stepped tops)
        pl.append(bx(0.2, D * 0.62, 1.2, (-W / 2, 0.3 + D * 0.31, H + 0.2), bev=0.02))
    k.put("Plaster", tint(paint(join(pl), wall_c, var=0.02, ao=0.35, ao_h=1.2, top=0.1, namp=0.08, ns=0.9),
                          lambda v, c: c * (1 - 0.18 * smooth01(0.4, 0.0, v[:, 2]))[:, None]))
    k.put("Plaster", paint(join(tr), trim, var=0.02, ao=0.2, ao_h=0.6, top=0.15))
    if lanterns and lod == 0:  # pair of red lanterns in the arcade
        for sx in (-W / 4, W / 4):
            body, cap = lantern(GF - 0.32, 0.16, 0.32)
            k.put("Lantern", paint(xf(body, (sx, 0.55, 0)), (0.95, 0.22, 0.12), ao=0.0, top=0.0))
            k.put("Wood", paint(xf(cap, (sx, 0.55, 0)), (0.25, 0.16, 0.07), ao=0.0))
            k.put("Metal", paint(K.tube([(sx, 0.55, GF - 0.3), (sx, 0.55, GF - 0.32)], 0.006, seg=3), (0.1, 0.1, 0.1), ao=0))
    if lod == 0:  # vertical signboard on the column
        vs = bx(0.34, 0.05, 1.3, (-W / 2 + 0.03, -0.12, 1.25), bev=0.01)
        k.put("Wood", tint(paint(vs, (0.62, 0.10, 0.08), ao=0.0, top=0.1),
                           lambda v, c: np.where(((np.abs(v[:, 0] + W / 2 - 0.03) < 0.08) & (np.floor(v[:, 2] * 4.5) % 2 == 0))[:, None],
                                                 np.array([0.95, 0.8, 0.35, 1.0]), c)))
    return k


def glow_grad(p, lo=0.62):
    """vertical vertex-colour gradient on a lit pane: full colour at the sill fading toward the head (no flat slab)."""
    z = p.v[:, 2]
    t = (z - z.min()) / max(1e-6, float(np.ptp(z)))
    return tint(p, lambda v, c: c * (1.0 - (1.0 - lo) * t)[:, None])


def place_kit(A, set_, kit, loc, rz, names):
    for key, ps in kit.items():
        A.add(set_, names[key], [xf(p, loc, (0, 0, rz)) for p in ps])


# ================================================================ Penang layout
ASPH = (0.17, 0.17, 0.19)
ASPH_LT = (0.26, 0.25, 0.26)
WETDK = (0.10, 0.10, 0.12)
POOL = (0.50, 0.36, 0.24)
LINE_Y = (0.62, 0.52, 0.22)
KERB = (0.46, 0.44, 0.42)
SEA = (0.10, 0.13, 0.17)
PASTELS = [(0.60, 0.74, 0.66), (0.82, 0.62, 0.58), (0.86, 0.76, 0.50), (0.58, 0.66, 0.80), (0.82, 0.80, 0.72), (0.70, 0.58, 0.74)]
SHUTTERS = [(0.20, 0.40, 0.34), (0.40, 0.18, 0.14), (0.18, 0.28, 0.42), (0.30, 0.22, 0.14)]

ARC_X = -8.2        # arcade column line (left row facades face +x)
FW = 1.8
SEAWALL_X = 12.6
SEA_Z = -0.95
STREET_END = 64.0   # land ends (water beyond)
GF_LAN = 3.25       # lantern-string anchor height on the arcade
NAMES = {"Plaster": "MatPlaster_wall", "Wood": "MatWood_timber", "Tile": "MatTile_clay", "Glow": "MatGlow_warm",
         "Lantern": "MatGlow_lantern", "Metal": "MatMetal_zinc", "Cloth": "MatCloth_awning", "Fire": "MatGlow_warm",
         "Leaf": "MatLeaf_canopy"}
NAMES_FAR = dict(NAMES, Wood="MatPlaster_wall", Metal="MatPlaster_wall", Cloth="MatPlaster_wall")
# warm light pools painted into the asphalt (x, y, r, k)
POOLS = [(-7.6, -3.0, 2.6, 0.7), (-7.6, 1.6, 2.6, 0.7), (-7.6, 6.2, 2.6, 0.7), (-3.2, 7.9, 2.4, 0.8), (2.6, 7.9, 2.4, 0.8),
         (8.4, 5.2, 2.4, 0.8), (10.4, -0.2, 3.0, 0.6), (10.6, 12.0, 3.0, 0.5), (-7.6, 10.8, 2.6, 0.6), (-7.6, 15.4, 2.6, 0.6),
         (6.5, 15.5, 2.6, 0.6), (-1.0, 14.0, 2.5, 0.6)]
PUDDLES = [(-6.4, -2.2, 0.9, 0.45), (6.6, 2.6, 0.8, 0.4), (-2.4, 9.6, 1.0, 0.5), (9.4, 8.4, 0.8, 0.4), (5.6, 10.6, 1.2, 0.5)]


def seawall_x(y):
    return SEAWALL_X + 0.25 * math.sin(0.07 * y)


def is_land(x, y):
    return x < seawall_x(y) and y < STREET_END and x > -40


def ground(x, y):
    if not is_land(x, y):
        return SEA_Z - 0.8
    z = 0.012 * nz(x, y, 0, 0.6, 3)
    z -= 0.05 * (1 - smooth01(0.0, 0.5, abs(x - (ARC_X + 0.55))))   # gutter in front of the kerb
    z += 0.035 * smooth01(4.0, 9.0, abs(x - 2.0))                      # street camber
    return z


def gcolor(x, y, z):
    if not is_land(x, y):
        return (0.08, 0.08, 0.09)
    n1 = nz(x, y, 0, 0.35, 11)
    n2 = nz(x, y, 0, 1.6, 12)
    n3 = nz(x, y, 0, 5.0, 13)
    c = np.array(ASPH) * (1 + 0.16 * n1 + 0.08 * n2 + 0.05 * n3)
    c = c * (1 - 0.3 * smooth01(0.25, 0.6, nz(x, y, 0, 0.22, 14)))                 # wet dark patches
    patch = abs(nz(math.floor(x / 1.7) * 1.7, math.floor(y / 2.3) * 2.3, 0, 0.7, 15))  # tar repair patches
    if patch > 0.42:
        c = c * 0.78
    c = c * (1 - 0.35 * (1 - smooth01(0.0, 0.5, abs(x - (ARC_X + 0.55)))))          # wet gutter
    for (px, py, pr, pk) in PUDDLES:
        d = math.hypot(x - px, (y - py) * 1.3)
        c = c * (1 - 0.45 * (1 - smooth01(pr, pr * 2.0, d)))
    for (px, py, pr, pk) in POOLS:
        d = math.hypot(x - px, y - py)
        t = pk * (1 - smooth01(pr * 0.2, pr, d))
        c = c + (np.array(POOL) - c) * t * 0.8
    # faded double yellow line along the kerb + a worn white chalk ring around the dish
    if 0.15 < x - (ARC_X + 0.55) < 0.42 and (abs(x - ARC_X - 0.55 - 0.2) > 0.05):
        c = c * 0.35 + np.array(LINE_Y) * 0.65 * (0.75 + 0.25 * n3)
    r = math.hypot(x, y)
    c = c + (np.array(ASPH_LT) - c) * 0.6 * (1 - smooth01(4.6, 6.0, r))           # swept apron
    c = c * (1 - 0.18 * smooth01(seawall_x(y) - 1.0, seawall_x(y), x))              # wet promenade edge
    return tuple(np.clip(c, 0, 1))


def gcull(cx, cy, zmax):
    if not is_land(cx, cy):
        return True
    if cx < ARC_X + 0.05 and cy > -16:   # under the arcade floor / inside the shophouses
        return True
    return not visible(cx, cy, pad=4.0) and math.hypot(cx, cy) > 12


def on_ground(p, x, y, sink=0.0):
    return xf(p, (x, y, ground(x, y) - sink))


def street(A):
    """shophouse row (left), arcade tiles, kerb, drain grates."""
    rng = random.Random(4)
    W = 4.4
    y = -8.6
    i = 0
    while y < STREET_END - 2:
        yc = y + W / 2
        far = yc > 21
        lod = 0 if yc < 12 else (1 if yc < 34 else 2)
        if far and not in_vista(ARC_X, yc):
            y += W
            i += 1
            continue
        kit = shophouse(W=W, wall=PASTELS[(i * 4 + 1) % len(PASTELS)], shutter=SHUTTERS[i % len(SHUTTERS)],
                        lit=((True, False), (False, True), (True, True), (False, False))[i % 4], shop_open=(i % 3 != 1),
                        sign=((0.10, 0.09, 0.08), (0.55, 0.08, 0.06), (0.10, 0.20, 0.16))[i % 3], seed=i, lod=lod,
                        last_col=(y + W >= STREET_END - 2))
        place_kit(A, "far" if far else "battle", kit, (ARC_X - 0.15, yc, 0.0), math.pi / 2, NAMES_FAR if far else NAMES)
        y += W
        i += 1
    # arcade floor tiles (raised) + granite kerb + drain grates
    A.add("battle", "MatTile_clay", tile_floor(ARC_X - FW - 0.1, ARC_X + 0.45, -8.6, 14.0, 0.16, 0.3,
                                               cols=((0.56, 0.30, 0.20), (0.66, 0.40, 0.26), (0.30, 0.42, 0.40)), seed=3,
                                               cull=lambda x, y: not visible(x, y, 2.0)))
    A.add("battle", "MatTile_clay", paint(P([(ARC_X - FW - 0.1, 14.0, 0.16), (ARC_X + 0.45, 14.0, 0.16), (ARC_X + 0.45, STREET_END - 2, 0.16),
                                             (ARC_X - FW - 0.1, STREET_END - 2, 0.16)], [(0, 1, 2, 3)]), (0.5, 0.3, 0.2), ao=0))
    kerb = K.extrude([(ARC_X + 0.45, -8.6), (ARC_X + 0.45, STREET_END - 2)], [(-0.16, 0.16), (0.0, 0.16), (0.05, 0.12), (0.06, -0.12)], step=1.5)
    A.add("battle", "MatRock_granite", tint(paint(kerb, KERB, ao=0.0, top=0.2, namp=0.15, ns=3), stripes(1, 1.1, 0.85, 1.0)))
    for k in range(-8, 14, 3):
        g = bx(0.5, 0.95, 0.03, (ARC_X + 0.85, k + 0.5, ground(ARC_X + 0.85, k + 0.5) - 0.005), bev=0.0)
        A.add("battle", "MatMetal_zinc", tint(paint(g, (0.30, 0.29, 0.27), ao=0.0, top=0.0), stripes(1, 9, 0.45, 1.0)))


def promenade(A):
    """seawall, railing posts, heritage lamps along the waterfront, bollards."""
    ys = np.arange(-16.0, STREET_END + 0.01, 1.0)
    wall = K.extrude([(seawall_x(y), y) for y in ys], [(-0.4, 0.06), (0.0, 0.08), (0.06, 0.02), (0.15, -0.5), (0.22, -1.6)], step=1.0)
    A.add("battle", "MatRock_granite", tint(paint(wall, (0.40, 0.38, 0.36), ao=0.0, top=0.25, namp=0.15, ns=1.5),
                                            lambda v, c: c * (0.8 + 0.2 * (np.floor(v[:, 1] / 0.9 + np.floor(v[:, 2] * 3) * 0.5) % 2))[:, None]))
    for y in np.arange(-12.0, STREET_END - 2, 2.2):
        set_ = "battle" if y < 21 else "far"
        if not visible(seawall_x(y), y, 2.0):
            continue
        x = seawall_x(y) - 0.25
        A.add(set_, "MatMetal_zinc" if set_ == "battle" else "MatPlaster_wall",
              paint(xf(K.lathe([(0, 0), (0.07, 0), (0.06, 0.62), (0.08, 0.66), (0.0, 0.74)], seg=6), (x, y, 0.06)), (0.1, 0.1, 0.11), ao=0, top=0.3))
    rail = [(seawall_x(y) - 0.25, y, 0.72) for y in np.arange(-12.0, 21.0, 1.1) if visible(seawall_x(y), y, 2.0)]
    A.add("battle", "MatMetal_zinc", paint(K.tube(rail, 0.02, seg=4, cap=False), (0.1, 0.1, 0.11), ao=0))
    lamps = [(10.6, -1.0), (10.9, 10.0), (10.9, 21.0), (10.9, 32.0), (10.9, 43.0), (10.9, 54.0)]
    for k, (x, y) in enumerate(lamps):
        set_ = "battle" if y < 22 else "far"
        place_kit(A, set_, heritage_lamp(3.4), (x, y, 0.0), 0.3, NAMES if set_ == "battle" else NAMES_FAR)
    return lamps


def street_life(A):
    """hawker carts, tables, umbrellas, trishaw, crates, lantern strings."""
    # far band: two carts facing the dish + a third on the right flank
    carts = [(-3.3, 7.6, 0.06, (0.18, 0.40, 0.46), (0.62, 0.10, 0.08)), (2.6, 7.7, -0.05, (0.70, 0.52, 0.16), (0.10, 0.10, 0.10)),
             (8.6, 4.6, -1.4, (0.52, 0.14, 0.12), (0.12, 0.30, 0.20))]
    for k, (x, y, rz, body, sign) in enumerate(carts):
        place_kit(A, "battle", hawker_cart(body, sign, seed=10 + k), (x, y, ground(x, y)), rz, NAMES)
        A.contact(x, y, 1.6, 0.25)
    # vista: more stalls receding along the promenade side
    for k, (x, y, rz) in enumerate(((7.4, 13.5, -1.62), (7.6, 19.5, -1.5), (7.4, 26.0, -1.6), (7.5, 33.0, -1.55), (7.4, 40.0, -1.6), (7.5, 47.0, -1.5))):
        set_ = "battle" if y < 22 else "far"
        kit = hawker_cart(PASTELS[(k * 3) % 6], ((0.62, 0.10, 0.08), (0.1, 0.1, 0.1))[k % 2], seed=30 + k, wok=(k % 2 == 0), lod=k > 0)
        place_kit(A, set_, kit, (x, y, ground(x, y)), rz, NAMES if set_ == "battle" else NAMES_FAR)
    # tables + stools: far band, right flank, near strip, vista mid-ground
    tables = [(-0.6, 8.2), (-5.4, 7.0), (5.4, 6.6), (6.9, 1.2), (6.6, -3.2), (-6.6, -4.0), (-2.8, -6.9), (1.6, -7.2), (4.6, -6.6),
              (2.0, 11.0), (-3.4, 11.4), (0.4, 15.6), (3.8, 18.6)]
    for k, (x, y) in enumerate(tables):
        if math.hypot(x, y) < 6.4:
            continue
        set_ = "battle" if y < 22 else "far"
        kit = table_set(100 + k, n=(3 + k % 2) if y < 9.5 else 2)
        place_kit(A, set_, kit, (x, y, ground(x, y)), 0.0, NAMES if set_ == "battle" else NAMES_FAR)
        if set_ == "battle":
            A.contact(x, y, 0.9, 0.3)
    # apron: a few stools and a crate stack (<=0.6 m), nothing bright near the rope
    for k, (x, y) in enumerate(((5.15, 1.95), (-5.7, -1.2))):
        A.add("battle", "MatWood_timber", paint(xf(stool(k, 0.45), (x, y, ground(x, y)), (0, 0, k)), (0.36, 0.24, 0.15), ao=0.3, ao_h=0.4))
        A.contact(x, y, 0.45, 0.3)
    for k, (x, y, z, rz) in enumerate(((5.6, 1.0, 0.0, 0.3), (5.75, 1.6, 0.0, 0.1), (5.65, 1.3, 0.3, 0.25))):
        cr = bx(0.5, 0.36, 0.28, (x, y, ground(x, y) + z), bev=0.015, rot=(0, 0, rz))
        A.add("battle", "MatWood_timber", tint(paint(cr, (0.48, 0.36, 0.22), ao=0.3, ao_h=0.6), stripes(2, 18, 0.7, 1.0)))
    A.contact(5.65, 1.3, 0.8, 0.35)
    # left: satay grill cluster, bicycle against the kerb, potted plants along the five-foot-way
    place_kit(A, "battle", satay_grill(3), (-6.95, 1.4, ground(-6.95, 1.4)), math.pi / 2 + 0.05, NAMES)
    A.contact(-6.95, 1.4, 1.2, 0.3)
    for k, (x, y) in enumerate(((-6.4, 2.3), (-6.5, 0.4))):
        A.add("battle", "MatWood_timber", paint(xf(stool(k, 0.45), (x, y, ground(x, y)), (0, 0, k)), (0.36, 0.24, 0.15), ao=0.3, ao_h=0.4))
    for k, (x, y, z, rz) in enumerate(((-7.1, -0.4, 0.0, 0.1), (-7.15, -0.35, 0.28, 0.25), (-6.75, -0.6, 0.0, 0.5))):
        cr = bx(0.5, 0.36, 0.28, (x, y, ground(x, y) + z), bev=0.015, rot=(0, 0, rz))
        A.add("battle", "MatWood_timber", tint(paint(cr, (0.44, 0.34, 0.22), ao=0.3, ao_h=0.6), stripes(2, 18, 0.7, 1.0)))
    A.add("battle", "MatWood_timber", paint(on_ground(K.basket(0.2, 0.22), -7.3, 2.5), (0.52, 0.40, 0.24), ao=0.4, ao_h=0.2))
    place_kit(A, "battle", bicycle(), (-7.25, 4.3, ground(-7.25, 4.3)), 0.12, NAMES)
    for k, y in enumerate((-5.6, -1.2, 3.0, 7.4, 11.8)):
        place_kit(A, "battle", potted_plant(k, 0.8), (ARC_X - 0.05, y + 0.7, 0.16), 0.0, NAMES)
    # manhole covers + power cables snaking from the arcade sockets to the stalls
    for (x, y) in ((-3.4, 5.6), (6.3, -0.9), (2.2, 10.2)):
        mh = K.lathe([(0.34, 0.0), (0.33, 0.02), (0.0, 0.025)], seg=12, cap0=False)
        A.add("battle", "MatMetal_zinc", tint(paint(on_ground(mh, x, y, 0.012), (0.12, 0.12, 0.12), ao=0.0, top=0.0),
                                              lambda v, c, x=x, y=y: c * np.where(np.hypot(v[:, 0] - x, v[:, 1] - y) < 0.2, 0.75, 1.0)[:, None]))
    for a, b, lift in (((ARC_X + 0.3, 6.0), (-2.6, 7.0), 0.3), ((ARC_X + 0.3, 6.6), (2.9, 7.2), -0.6), ((ARC_X + 0.3, 1.0), (-6.6, 1.4), 0.2)):
        pts = [(a[0] + (b[0] - a[0]) * t + lift * math.sin(t * math.pi) * 1.5, a[1] + (b[1] - a[1]) * t + lift * math.sin(t * 2 * math.pi), 0.0)
               for t in np.linspace(0, 1, 9)]
        pts = [(x, y, ground(x, y) + 0.015) for x, y, _ in pts]
        A.add("battle", "MatMetal_zinc", paint(K.tube(pts, 0.014, seg=3, cap=False), (0.06, 0.06, 0.06), ao=0.0))
    # trishaw parked on the right flank
    place_kit(A, "battle", trishaw(), (8.8, 0.9, ground(8.8, 0.9)), 2.6, NAMES)
    A.contact(8.8, 0.9, 1.3, 0.3)
    place_kit(A, "battle", trishaw(seat_rgb=(0.18, 0.30, 0.50)), (9.8, 17.0, ground(9.8, 17.0)), 0.4, NAMES)
    # umbrellas over the far band tables
    for k, (x, y, cols) in enumerate(((-0.6, 8.6, ((0.78, 0.16, 0.12), (0.86, 0.82, 0.74))), (5.2, 9.6, ((0.16, 0.36, 0.62), (0.86, 0.82, 0.74))),
                                      (2.0, 11.6, ((0.82, 0.62, 0.16), (0.78, 0.16, 0.12))), (-3.6, 12.0, ((0.20, 0.50, 0.30), (0.86, 0.82, 0.74))))):
        place_kit(A, "battle", umbrella(1.25, 2.3, cols), (x, y, ground(x, y)), k * 0.4, NAMES)
    # lantern strings across the street (vista) + along the right flank (battle)
    for k, y in enumerate((9.5, 15.0, 20.5, 26.0, 31.5, 37.0, 42.5, 48.0, 53.5)):
        a = (ARC_X + 0.1, y - 0.6, GF_LAN)
        b = (10.9, y + 0.6, 3.1)
        lantern_string(A, "battle", a, b, 9, 0.55, "MatGlow_lantern", "MatWood_timber", "MatMetal_zinc",
                       r=0.15 if y < 22 else 0.19, seg=6 if y < 22 else 4, caps=y < 22)
    lantern_string(A, "battle", (10.75, -1.0, 3.1), (10.95, 9.9, 3.1), 7, 0.5, "MatGlow_lantern", "MatWood_timber", "MatMetal_zinc")



def far_set(A):
    """across the channel: pagoda hill + Kek Lok Si, Penang Hill ridge, clan jetty, clouds."""
    # clan jetty: plank walkway on piles with stilt houses (vista right, mid-ground)
    jy = 30.0
    x0, x1 = SEAWALL_X, 46.0
    piles, deck, walls, roofs, glow = [], [], [], [], []
    deck.append(bx(x1 - x0, 1.6, 0.12, ((x0 + x1) / 2, jy, 0.15), bev=0.0))
    for x in np.arange(x0 + 1.0, x1, 2.5):
        for yy in (jy - 0.7, jy + 0.7):
            piles.append(K.tube([(x, yy, SEA_Z - 0.5), (x, yy, 0.15)], 0.08, seg=3, cap=False))
    rng = random.Random(8)
    for k, x in enumerate(np.arange(x0 + 4.0, x1 - 1, 4.6)):
        for side in (-1, 1):
            if rng.random() < 0.2:
                continue
            w, d = rng.uniform(3.2, 3.9), rng.uniform(3.4, 4.4)
            yc = jy + side * (0.8 + d / 2)
            walls.append(bx(w, d, 2.3, (x, yc, 0.15), bev=0.0))
            for xx in (x - w * 0.4, x + w * 0.4):
                piles.append(K.tube([(xx, yc - d * 0.4, SEA_Z - 0.5), (xx, yc - d * 0.4, 0.15)], 0.08, seg=3, cap=False))
            rf = xf(K.thatch_roof(w, d, 1.0, courses=1, over=0.3, seed=k, tooth=0.0, cw=1.0), (x, yc, 2.45), (0, 0, math.pi / 2))
            roofs.append(rf)
            if rng.random() < 0.8:
                glow.append(dot(x + rng.uniform(-0.8, 0.8), yc - d / 2 - 0.05, 1.0, 0.7))
    A.add("far", "MatPlaster_wall", paint(join(piles, deck), (0.22, 0.17, 0.13), ao=0.0, top=0.2))
    A.add("far", "MatPlaster_wall", [paint(w, (0.38, 0.30, 0.24), var=0.12, ao=0.3, ao_h=2.0, ground=0.15, namp=0.1, ns=1.0) for w in walls])
    A.add("far", "MatTile_clay", [paint(r, (0.30, 0.26, 0.24), var=0.08, ao=0.0, top=0.3) for r in roofs])
    A.add("far", "MatGlow_warm", [paint(g, (1.0, 0.8, 0.5), ao=0.0, top=0.0) for g in glow])
    for k in range(4):  # moored boats
        bx_, by_ = x0 + 6 + 8 * k, jy + (-5.2 if k % 2 else 5.4)
        hull = xf(K.perahu(L=5.0, W=1.0, H=0.55, seed=k), (bx_, by_, SEA_Z - 0.1), (0, 0, rng.uniform(-0.2, 0.2)))
        A.add("far", "MatPlaster_wall", paint(hull, ((0.5, 0.2, 0.15), (0.2, 0.32, 0.45), (0.55, 0.5, 0.4), (0.25, 0.4, 0.3))[k], ao=0.0, top=0.2))
    # pagoda hill across the channel with Kek Lok Si
    hx, hy = 30.0, 92.0

    def hh(x, y):
        return (13.0 * math.exp(-(((x - hx) / 40.0) ** 2 + ((y - hy) / 18.0) ** 2)) + 8.0 * math.exp(-(((x + 22) / 34.0) ** 2 + ((y - 98) / 15.0) ** 2))
                + 4.0 * math.exp(-(((x - 75) / 25.0) ** 2 + ((y - 95) / 14.0) ** 2))
                + 1.6 * nz(x, y, 0, 0.045, 2) + 0.6 * nz(x, y, 0, 0.14, 3) - 0.6)
    p = hill(-60, 95, 76, 116, hh, nx=78, ny=10, base=SEA_Z - 1)
    A.add("far", "MatGround_asphalt", paint_hill(p, (0.07, 0.09, 0.08), (0.12, 0.15, 0.12), seed=3))
    trees = []
    for k in range(70):
        x, y = rng.uniform(-50, 85), rng.uniform(80, 106)
        z = hh(x, y)
        if z < 0.5:
            continue
        b = K.rock(rng.uniform(1.4, 2.6), seed=900 + k, sub=1, amp=0.25, squash=(1, 1, 0.8))
        trees.append(paint(xf(b, (x, y, z - 0.8)), (0.07, 0.10, 0.08), var=0.15, ao=0.0, top=0.35))
    A.add("far", "MatGround_asphalt", trees)
    lights = []
    for cx, cy, n in ((-34, 82, 9), (-8, 84, 7), (50, 80, 10), (70, 86, 6), (12, 98, 5), (-20, 96, 4)):  # hillside villages
        for k in range(n):
            x, y = cx + rng.gauss(0, 4.5), cy + rng.gauss(0, 2.5)
            z = hh(x, y)
            if z > 0.3:
                lights.append(dot(x, y, z + 0.2, rng.uniform(0.4, 0.7)))
    A.add("far", "MatGlow_warm", [paint(q, (1.0, 0.8, 0.5), ao=0.0, top=0.0) for q in lights])
    kek_lok_si(A, hx - 4.0, hy - 5.0, hh(hx - 4.0, hy - 5.0) - 0.3, hh)
    # Penang Hill: big ridge far behind, a few summit lights
    def ph(x, y):
        return (40.0 * math.exp(-(((x + 5) / 95.0) ** 2)) + 14.0 * math.exp(-(((x - 110) / 45.0) ** 2)) + 7.0 * nz(x, y, 0, 0.025, 7)
                + 2.5 * nz(x, y, 0, 0.08, 8) + 6.0) * math.exp(-(((y - 185) / 30.0) ** 2))
    p = hill(-130, 150, 150, 230, ph, nx=90, ny=8, base=-3)
    A.add("far", "MatGround_asphalt", paint_hill(p, (0.06, 0.07, 0.08), (0.09, 0.10, 0.12), seed=5, top=0.3))
    for k in range(18):
        x = rng.uniform(-60, 80)
        y = rng.uniform(170, 190)
        z = ph(x, y)
        if z < 10:
            continue
        A.add("far", "MatGlow_warm", paint(dot(x, y, z, 1.0), (1.0, 0.85, 0.6), ao=0))
    for x in (2.0, 6.0):  # summit mast lights
        A.add("far", "MatGlow_lantern", paint(bx(1.2, 1.2, 1.2, (x, 182, ph(x, 182) + 6), bev=0.0), (1, 0.2, 0.1), ao=0))
        A.add("far", "MatPlaster_wall", paint(K.tube([(x, 182, ph(x, 182) - 1), (x, 182, ph(x, 182) + 6)], 0.4, seg=4), (0.1, 0.1, 0.12), ao=0))
    # night clouds lit from below by the city
    for k, (x, y, z, w, h) in enumerate(((-30, 240, 70, 120, 14), (60, 260, 85, 140, 16), (20, 210, 52, 70, 9), (110, 230, 60, 80, 10),
                                         (-90, 250, 58, 90, 11))):
        A.add("far", "MatPlaster_wall", cloud(x, y, z, w, h, 40 + k, (0.20, 0.17, 0.26), under=(0.34, 0.22, 0.26)))
    # sea to the horizon
    v = [(SEAWALL_X - 0.4, -30, SEA_Z), (400, -30, SEA_Z), (400, 420, SEA_Z), (-400, 420, SEA_Z), (-400, STREET_END - 0.5, SEA_Z),
         (SEAWALL_X - 0.4, STREET_END - 0.5, SEA_Z)]
    p = P(v, [(0, 1, 2, 5), (5, 2, 3, 4)])
    p.c = np.tile(list(SEA) + [1.0], (len(v), 1))
    A.add("far", "MatWater_sea", p)
    # quay edge where the street meets the water
    q = K.extrude([(-40.0, STREET_END), (seawall_x(STREET_END), STREET_END)], [(-0.3, 0.05), (0.0, 0.06), (0.1, -1.4)], step=4.0)
    A.add("far", "MatPlaster_wall", paint(q, (0.30, 0.29, 0.28), ao=0.0, top=0.2))


def kek_lok_si(A, x, y, z0, hfn):
    """Pagoda of Ten Thousand Buddhas (stylised): 7 octagonal tiers, flared eaves outlined in lights,
    golden stupa crown; temple halls at its foot."""
    walls, roofs, glow = [], [], []
    r, zz = 2.6, z0
    for t in range(7):
        h = 2.1 - 0.12 * t
        walls.append(xf(K.lathe([(r, 0), (r * 0.94, h), (0, h)], seg=8, phase=math.pi / 8, cap0=False), (x, y, zz)))
        e = r * 1.45
        roofs.append(xf(K.lathe([(e, h - 0.15), (e * 0.97, h + 0.05), (r * 0.9, h + 0.55), (0, h + 0.55)], seg=8, phase=math.pi / 8, cap0=False), (x, y, zz)))
        ring = [(x + e * math.cos(a), y + e * math.sin(a), zz + h - 0.1) for a in np.linspace(math.pi / 8, 2 * math.pi + math.pi / 8, 9)]
        glow.append(K.tube(ring, 0.16, seg=4, cap=False))
        for k in range(8):  # lit arched openings
            a = math.pi / 8 + k * math.pi / 4 + math.pi / 8
            if math.sin(a) < 0.3:  # only the openings facing the town
                glow.append(dot(x + r * 1.0 * math.cos(a), y + r * 1.0 * math.sin(a), zz + 0.45, 0.55))
        zz += h + 0.25
        r *= 0.86
    crown = K.lathe([(r * 1.2, 0), (r * 1.25, 0.6), (r * 0.9, 1.4), (r * 0.4, 2.6), (0.15, 4.2), (0, 4.6)], seg=10)
    glow.append(xf(crown, (x, y, zz)))
    # octagonal terrace sunk into the slope + a zig-zag stair of lamps down the hill
    walls.append(xf(K.lathe([(4.6, -4.0), (4.6, 0.0), (0, 0.0)], seg=8, phase=math.pi / 8, cap0=False), (x, y, z0)))
    glow.append(xf(K.lathe([(4.75, -0.05), (4.75, 0.12), (4.6, 0.12)], seg=8, phase=math.pi / 8, cap0=False, cap1=False), (x, y, z0)))
    px, py = x, y - 5.0
    for k in range(16):
        px += 2.2 * (1 if (k // 4) % 2 == 0 else -1)
        py -= 1.0
        glow.append(dot(px, py, hfn(px, py) + 0.1, 0.5))
    A.add("far", "MatPlaster_wall", paint(join(walls), (0.80, 0.76, 0.66), ao=0.0, top=0.2))
    A.add("far", "MatTile_clay", paint(join(roofs), (0.26, 0.30, 0.26), ao=0.0, top=0.35))
    A.add("far", "MatGlow_warm", paint(join(glow), (1.0, 0.86, 0.55), ao=0.0, top=0.0))


def build(A):
    for name in ("MatGround_asphalt", "MatTile_clay", "MatPlaster_wall", "MatWood_timber", "MatMetal_zinc", "MatCloth_awning",
                 "MatWater_sea", "MatRock_granite"):
        A.mat(name)
    A.mat("MatMetal_zinc", rough=0.55, metal=0.3)
    A.mat("MatLeaf_canopy")
    A.mat("MatGlow_warm", emit=(1.0, 0.70, 0.38), estr=1.0)
    A.mat("MatGlow_lantern", emit=(1.0, 0.22, 0.10), estr=3.5)

    street(A)
    promenade(A)
    street_life(A)
    rng = random.Random(17)
    # lights (<=6): woks, arcade shopfronts, lamp
    A.light((-3.3 + 0.6, 7.0, 1.5), 110.0, (1.0, 0.58, 0.28), range_m=6)
    A.light((2.6 + 0.6, 7.1, 1.5), 110.0, (1.0, 0.58, 0.28), range_m=6)
    A.light((8.2, 4.2, 1.6), 100.0, (1.0, 0.58, 0.28), range_m=6)
    A.light((-6.9, 1.4, 1.1), 90.0, (1.0, 0.52, 0.24), range_m=5)
    A.light((ARC_X - 0.6, 6.4, 2.6), 100.0, (1.0, 0.62, 0.36), range_m=6)
    A.light((10.6, -1.0, 3.2), 90.0, (1.0, 0.80, 0.55), range_m=7)

    A.terrain(ground, gcolor, kind=None, rin=4.5, rout=80.0, split=23.0, cull=gcull, seed=1)
    # sea strip in front of the seawall (battle) + weeds along the seawall foot
    ys = np.arange(-16.0, 23.0, 2.0)
    v, f = [], []
    for y in ys:
        v += [(seawall_x(y) - 0.2, y, SEA_Z), (30.0, y, SEA_Z)]
    for i in range(len(ys) - 1):
        f.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    p = P(v, f)
    p.c = np.array([[0.09, 0.11, 0.14, 0.75], [0.10, 0.13, 0.17, 1.0]] * len(ys))
    A.add("battle", "MatWater_sea", p)
    for y in np.arange(-6.0, 20.0, 1.3):
        if rng.random() < 0.6:
            A.scatter_patch("Grass", 26, seawall_x(y) - 0.55, y, rng.uniform(0.3, 0.6), ground, (0.26, 0.32, 0.18), seed=int(y * 10) + 500)
    for y in np.arange(-14.0, 20.0, 1.7):
        if rng.random() < 0.4:
            A.scatter_strip("Grass", 22, (ARC_X + 0.62, y), (ARC_X + 0.62, y + rng.uniform(0.4, 1.0)), 0.12, ground, (0.24, 0.30, 0.16), step=99)
    far_set(A)


if __name__ == "__main__":
    K.main("penang", build, MOOD)
