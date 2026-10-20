"""Wayang kulit cutscene art: the prop kit, the colour-icon kit and the CLI.
The art itself lives in art_src/wayang_states/<id>.py (one module per state:
PUPPET, BEATS, ICONS) and art_src/wayang_states/journey.py (JOURNEY: rides,
strips, prologue, endings, sailor). Template: wayang_states/perlis.py.

  blender -b --factory-startup -P art_src/wayang_scenes.py -- state perlis [kedah ...]
  blender -b --factory-startup -P art_src/wayang_scenes.py -- state perlis:land perlis:puppet
  blender -b --factory-startup -P art_src/wayang_scenes.py -- journey [prologue sailor strip_road ride_perlis]
  blender -b --factory-startup -P art_src/wayang_scenes.py -- icons [perlis]
  blender -b --factory-startup -P art_src/wayang_scenes.py -- puppet perlis sailor
  blender -b --factory-startup -P art_src/wayang_scenes.py -- selftest [perlis journey ...]

Beat canvases are 2048x820 in scene units of 100 px (x 0..20.48, y 0..8.2),
ground line at G (12%). Layers: 'back' is blurred to ~45%, 'mid' carries the
carved lace, 'front' frames the edges. Keep the top centre (x 7..13, y > 5.6)
open for the blencong glow, and keep the right third calmer on any art a
puppet slides over. Puppets: wayang_lib.figure() specs. Ride canvases are
RIDE-sized, facing right, wheels on RIDE_Y. Output is black on transparent
(indexed PNG); main.gd tints it HT.INK over the kelir. Icons are colour EEVEE.
"""
import bpy, math, os, sys, random, time, importlib

sys.dont_write_bytecode = True          # no __pycache__ in art_src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.modules.setdefault('wayang_scenes', sys.modules[__name__])   # state modules get this run, not a re-import
import wayang_lib as W
from wayang_lib import ribbon, leaf, ellipse, xf, catmull, scroll, spiral, rect, arc_pts, noise1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'wayang')
OUT_UI = os.path.join(ROOT, 'assets', 'ui')
WIDE = (2048, 820, 20.48)
G = 0.98   # ground line

def _open(ctrl, seg=6):
    return catmull(ctrl, closed=False, seg=seg)

# =====================================================================
# prop kit: landscape
# =====================================================================

def frieze(y0, y1, x0=0.0, x1=20.48, step=0.62):
    """Pucuk rebung border: a run of bamboo-shoot triangles cut as outlines,
    each with a diamond eye, alternating with small inverted teeth."""
    cuts = []
    n = int((x1 - x0) / step)
    for i in range(n):
        a = x0 + i * step
        b, c = a + step, a + step / 2
        tri = [(a + 0.05, y0), (c, y1), (b - 0.05, y0)]
        cuts.append(ribbon(tri, 0.012))
        cuts.append(W.diamond(c, y0 + (y1 - y0) * 0.38, step * 0.22, (y1 - y0) * 0.3)[0])
        cuts.append([(b - 0.1, y1), (b + 0.1, y1), (b, y1 - (y1 - y0) * 0.35)])
    return cuts

def ground(cv, kind='earth', seed=1, y=G, layer='mid'):
    """Bottom band the scene stands on: a carved pucuk-rebung frieze under a top
    edge of grass tufts ('earth'), wavelets ('water') or wheel ruts ('road')."""
    rnd = random.Random(seed)
    f = noise1(seed, 9)
    top = [(x / 40 * 20.6 - 0.06, y + 0.06 * f(x / 40)) for x in range(41)]
    band = [(-0.1, -0.1)] + top + [(20.6, -0.1)]
    if kind == 'water':
        pid = cv.add([band], 'edge', layer)
        crest = []
        for i in range(17):
            x = 0.3 + i * 1.25 + rnd.uniform(-0.1, 0.1)
            crest.append(scroll(x, y + 0.2, 0.18, 0.06, 1.15, a0=180, cw=True,
                                tail=[(x - 0.55, y - 0.02), (x - 0.35, y + 0.12)]))
        cv.add(crest, 'solid', layer, pid=pid)
        cv.carve(frieze(0.12, y - 0.2), layer)
        return pid
    pid = cv.add([band], 'edge', layer)
    tufts = []
    for i in range(30):
        x = rnd.uniform(0, 20.48)
        h = rnd.uniform(0.15, 0.32)
        for j in range(5):
            tufts.append(leaf(x + j * 0.03, y + 0.02, 90 + (j - 2) * 18 + rnd.uniform(-6, 6), h, 0.022,
                              bend=0.04 * (j - 2)))
    cv.add(tufts, 'solid', layer, pid=pid)
    if kind == 'road':
        cv.carve([ribbon(_open([(x0, y - 0.18), (x0 + 1.5, y - 0.15), (x0 + 3.2, y - 0.19)]), 0.012, 0.004)
                  for x0 in (0.6, 5.0, 9.4, 13.8, 17.6)], layer)
        cv.carve(frieze(0.1, y - 0.3), layer)
    else:
        cv.carve(frieze(0.12, y - 0.2), layer)
    return pid

def canopy(cx, cy, r, seed=1, n=7):
    """Bumpy broccoli crown: overlapping discs for a tree clump."""
    rnd = random.Random(seed)
    out = [ellipse(cx, cy, r * 0.8, r * 0.55)]
    for i in range(n):
        a = math.radians(180 * i / (n - 1))
        rr = r * rnd.uniform(0.32, 0.45)
        out.append(ellipse(cx + r * 0.72 * math.cos(a), cy + r * 0.45 * math.sin(a) + rr * 0.3, rr, rr * 0.85, n=20))
    return out

def karst(cv, x, base, w, h, seed=1, layer='mid', cls='edge', moss=True, cave=False):
    """Perlis/Perak limestone tower: sheer fluted cliffs with an overhang, a
    tree-clad crown with hanging vines, optionally a cave mouth at the foot."""
    rnd = random.Random(seed)
    f = noise1(seed, 7)
    g = noise1(seed + 50, 3)
    lean = rnd.uniform(-0.08, 0.08) * w
    L, R = [], []
    for i in range(13):
        t = i / 12
        bulge = 0.09 * w * math.sin(t * math.pi * 1.3 + seed) + 0.05 * w * f(t)
        L.append((x - w * 0.5 + w * 0.13 * t ** 1.6 - bulge + lean * t, base + h * 0.86 * t))
        R.append((x + w * 0.5 - w * 0.16 * t ** 1.4 + 0.07 * w * g(t) + lean * t, base + h * 0.8 * t))
    tops = []
    k = rnd.randint(3, 4)
    for i in range(k + 1):
        t = i / k
        tops.append((L[-1][0] + (R[-1][0] - L[-1][0]) * t,
                     base + h * (0.86 + (0.8 - 0.86) * t) + h * 0.14 * math.sin(math.pi * t) * rnd.uniform(0.6, 1.2)))
    poly = _open(L + tops[1:-1] + R[::-1], 4)
    rings = [poly]
    if cave:
        cx = x + rnd.uniform(-0.15, 0.15) * w
        cw, ch = w * 0.22, h * 0.16
        rings.append([(cx - cw, base)] + arc_pts(cx, base + ch * 0.4, cw, 180, 0, 16, ry=ch * 0.75)[1:-1] +
                     [(cx + cw, base)] + [(cx + cw * (0.6 - 0.3 * i), base + 0.02) for i in range(5)])
    pid = cv.add_eo(rings, cls, layer)
    if layer == 'back':
        return pid
    cuts = []
    for i in range(int(w / 0.26)):                     # long rain-cut flutes, never crossing
        cx = x - w * 0.38 + (i + 0.5) * 0.26 + rnd.uniform(-0.06, 0.06) + lean * 0.5
        y0 = base + h * rnd.uniform(0.08, 0.35)
        y1 = y0 + h * rnd.uniform(0.18, 0.42)
        if y1 > base + h * 0.76:
            continue
        wob = rnd.uniform(-0.05, 0.05)
        cuts.append(ribbon(_open([(cx, y0), (cx + wob, (y0 + y1) / 2), (cx - wob * 0.5, y1)]),
                           0.004, wf=lambda t: 0.004 + 0.012 * math.sin(math.pi * t)))
    cv.carve(cuts, layer)
    if moss:
        crown, vines = [], []
        for i, (px, py) in enumerate(tops):
            crown += canopy(px, py + 0.05, 0.32 * min(1.2, w / 2.0) * rnd.uniform(0.8, 1.15), seed + i)
            if rnd.random() < 0.6:
                tx = px + rnd.uniform(-0.1, 0.1)
                crown.append(ribbon([(tx, py), (tx + 0.02, py + 0.5)], 0.025, 0.018))
                crown += canopy(tx + 0.02, py + 0.55, 0.28, seed + 9 + i, 6)
        for side, pts in ((-1, L), (1, R)):
            for i in (5, 8, 11):
                px, py = pts[i]
                crown += canopy(px + side * 0.05, py, 0.16 * rnd.uniform(0.8, 1.3), seed + i * side, 5)
                vx = px + side * 0.04
                vines.append(ribbon(_open([(vx, py), (vx + side * 0.04, py - 0.25), (vx, py - 0.5 - rnd.uniform(0, 0.3))]),
                                    0.012, 0.004))
        cv.add(vines, 'solid', layer)
        cv.add(crown, 'edge', layer)
    return pid

def hills(cv, x0, x1, base, h, seed=1, layer='back', n=5):
    rnd = random.Random(seed)
    pts = [(x0, base - 0.2)]
    for i in range(n * 4 + 1):
        t = i / (n * 4)
        pts.append((x0 + (x1 - x0) * t, base + h * (0.55 + 0.45 * math.sin(t * n * math.pi + seed) ** 2)
                    * (0.8 + 0.2 * rnd.random())))
    pts.append((x1, base - 0.2))
    return cv.add([_open(pts, 4)], 'edge', layer)

def sun(cv, cx, cy, r, layer='mid', rays=18):
    """Matahari: alternating flame rays round a carved disc."""
    fl = []
    for i in range(rays):
        a = 360 * i / rays
        long = i % 2 == 0
        fl.append(leaf(cx + r * 0.9 * math.cos(math.radians(a)), cy + r * 0.9 * math.sin(math.radians(a)),
                       a + (8 if long else -8), r * (0.75 if long else 0.45), r * (0.13 if long else 0.1),
                       bend=r * 0.08 * (1 if long else -1)))
    cv.add(fl, 'solid', layer)
    cv.add([ellipse(cx, cy, r, n=64)], 'lace', layer)
    cv.carve([ribbon(arc_pts(cx, cy, r * 0.55, 0, 360, 48), r * 0.025)] +
             [leaf(cx, cy, a, r * 0.42, r * 0.07) for a in range(0, 360, 45)], layer)

def cloud(cv, cx, cy, s, layer='back', flip=False, seed=1):
    """Awan larat: a flat-bottomed lobe topped by curling scrolls."""
    rnd = random.Random(seed)
    body = _open([(-1.6, 0.0), (-1.3, 0.25), (-0.6, 0.42), (0.2, 0.46), (0.9, 0.38), (1.5, 0.18), (1.7, 0.0)], 5) + \
        [(1.2, -0.12), (-1.2, -0.12)]
    polys = [body]
    for (px, py, r, cw) in ((-0.9, 0.45, 0.42, False), (0.05, 0.62, 0.55, True), (0.95, 0.45, 0.38, True)):
        r *= 1 + rnd.uniform(-0.1, 0.1)
        polys.append(scroll(px, py, r, r * 0.3, 1.2, a0=270, cw=cw))
        polys.append(ellipse(px, py - r * 0.2, r * 0.82, r * 0.6))
    polys.append(scroll(2.05, 0.3, 0.3, 0.07, 1.1, a0=180, cw=True, tail=[(1.4, 0.0), (1.8, 0.08)]))
    polys = [xf(p, cx, cy, s=s, flip=flip) for p in polys]
    return cv.add(polys, 'edge', layer)

def egret(cv, x, y, s, flip=False, pose='stand', layer='mid'):
    """Burung bangau: standing S-neck heron or flying with wings raised."""
    if pose == 'fly':
        polys = [ellipse(0, 0, 0.28, 0.07, rot=8),
                 ribbon(_open([(0.22, 0.03), (0.34, 0.12), (0.42, 0.1)]), 0.03, 0.022),
                 [(0.42, 0.13), (0.62, 0.08), (0.42, 0.08)],
                 leaf(-0.02, 0.03, 112, 0.6, 0.11, bend=-0.08),
                 leaf(0.04, 0.03, 70, 0.48, 0.08, bend=0.06),
                 ribbon([(-0.25, -0.02), (-0.55, -0.06)], 0.012, 0.008)]
    else:
        polys = [ellipse(0, 0.62, 0.22, 0.1, rot=18),
                 [(-0.2, 0.56), (-0.36, 0.5), (-0.18, 0.62)],
                 ribbon(_open([(0.16, 0.68), (0.2, 0.8), (0.14, 0.9), (0.18, 1.0)]), 0.032, 0.026),
                 ellipse(0.19, 1.01, 0.05, 0.04),
                 [(0.22, 1.03), (0.45, 0.98), (0.22, 0.99)],
                 ribbon([(0.0, 0.55), (0.02, 0.0)], 0.012), ribbon([(0.06, 0.55), (0.12, 0.25), (0.08, 0.0)], 0.012)]
        if pose == 'peck':
            polys = [xf(p, rot=-75, ox=0.16, oy=0.68) if 2 <= i <= 4 else p for i, p in enumerate(polys)]
    return cv.add([xf(p, x, y, s=s, flip=flip) for p in polys], 'solid', layer)

def birds(cv, x, y, n=5, s=0.5, seed=1, layer='back', flip=False):
    rnd = random.Random(seed)
    for i in range(n):
        egret(cv, x + i * 0.9 * s + rnd.uniform(-0.3, 0.3) * s, y + rnd.uniform(-0.5, 0.5) * s,
              s * rnd.uniform(0.7, 1.0), flip, 'fly', layer)

def palm(cv, x, y, h, lean=0.12, seed=1, layer='mid', fronds=9):
    """Coconut palm: ringed curving trunk, drooping pinnate fronds, nut cluster."""
    rnd = random.Random(seed)
    top = (x + lean * h, y + h)
    trunk = _open([(x, y), (x + lean * h * 0.15, y + h * 0.35), (x + lean * h * 0.55, y + h * 0.75), top])
    cv.add([ribbon(trunk, 0.055 * h ** 0.5 * 0.8, 0.035 * h ** 0.5 * 0.8)], 'edge', layer)
    cv.carve([ribbon([(p[0] - 0.035 * h ** 0.5, p[1] - 0.004), (p[0] + 0.035 * h ** 0.5, p[1] + 0.012)], 0.006)
              for p in trunk[3:-3:2]], layer)
    crown = []
    for i in range(fronds):
        a = math.radians(-20 + 220 * i / (fronds - 1) + rnd.uniform(-8, 8))
        L = h * rnd.uniform(0.32, 0.42)
        d = (math.cos(a), math.sin(a))
        droop = L * (0.35 + 0.25 * abs(math.cos(a)))
        path = _open([top, (top[0] + d[0] * L * 0.4, top[1] + d[1] * L * 0.4 + 0.05),
                      (top[0] + d[0] * L * 0.75, top[1] + d[1] * L * 0.6 - droop * 0.4),
                      (top[0] + d[0] * L, top[1] + d[1] * L * 0.5 - droop)])
        crown.append(ribbon(path, 0.022 * h ** 0.5, 0.006))
        for k in range(4, len(path) - 1):
            p, q = path[k], path[k + 1]
            ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
            t = k / len(path)
            ll = h * 0.11 * (1 - 0.6 * t)
            side = 1 if math.cos(a) >= 0 else -1
            crown.append(leaf(p[0], p[1], ang - 70 * side, ll, 0.012 * h ** 0.5, bend=-0.02 * side))
            crown.append(leaf(p[0], p[1], ang - 35 * side, ll * 0.8, 0.011 * h ** 0.5, bend=-0.02 * side))
    for k in range(4):
        crown.append(ellipse(top[0] - 0.08 + k * 0.06 * h ** 0.5, top[1] - 0.1 - (k % 2) * 0.06, 0.07 * h ** 0.5, 0.08 * h ** 0.5))
    cv.add(crown, 'solid', layer)

def strap_leaf(base, ang, L, W, droop=0.25, tip=0.12, cuts=6, seed=1):
    """Broad pisang leaf: arching midrib, near-constant width, blunt tip, and
    tears cut from the edge along the veins. Returns (polygon, cuts)."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    d, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    side = 1 if d[0] >= 0 else -1
    path = []
    for i in range(17):
        t = i / 16
        along = L * t
        drop = L * droop * t * t
        path.append((base[0] + d[0] * along, base[1] + d[1] * along - drop))
    wf = lambda t: W * min(1.0, t / 0.12) ** 0.6 * (1 - max(0.0, (t - (1 - tip)) / tip) ** 2) ** 0.5
    poly = ribbon(path, 0, wf=wf)
    tears = []
    for k in range(cuts):
        t = 0.2 + 0.7 * (k + rnd.uniform(-0.3, 0.3)) / cuts
        i = min(int(t * 16), 15)
        p, q = path[i], path[i + 1]
        tx, ty = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(tx, ty) or 1
        tx, ty = tx / ln, ty / ln
        nx, ny = -ty, tx
        sg = 1 if k % 2 else -1
        w = wf(t)
        e = (p[0] + nx * sg * w * 1.2 + tx * w * 0.5, p[1] + ny * sg * w * 1.2 + ty * w * 0.5)
        m = (p[0] + nx * sg * w * 0.18, p[1] + ny * sg * w * 0.18)
        tears.append(ribbon([m, e], W * 0.025, W * 0.07))
    return poly, tears

def banana(cv, x, y, h, seed=1, layer='front', flip=False):
    """Pisang clump: tapered pseudostem, arching torn leaves, a hanging heart."""
    rnd = random.Random(seed)
    polys, cuts = [ribbon(_open([(0, 0), (0.03 * h, h * 0.3), (0.02 * h, h * 0.55)]), 0.075 * h, 0.04 * h)], []
    for i, (a, L) in enumerate(((160, 0.62), (128, 0.7), (96, 0.62), (62, 0.72), (30, 0.64), (110, 0.4))):
        a += rnd.uniform(-5, 5)
        base = (0.02 * h, h * (0.5 + 0.035 * i))
        lf, tr = strap_leaf(base, a, L * h, 0.085 * h, droop=0.32 if 40 < a < 140 else 0.22, seed=seed + i)
        polys.append(ribbon([base, (base[0] + 0.05 * h * math.cos(math.radians(a)), base[1] + 0.05 * h * math.sin(math.radians(a)))],
                            0.012 * h, 0.009 * h))
        polys.append(lf)
        cuts += tr
    stalk = _open([(0.02 * h, h * 0.55), (0.12 * h, h * 0.5), (0.16 * h, h * 0.38)])
    polys += [ribbon(stalk, 0.008 * h), leaf(0.16 * h, h * 0.4, -95, 0.14 * h, 0.035 * h)]
    polys = [xf(p, x, y, flip=flip) for p in polys]
    cv.add(polys, 'edge', layer)
    cv.carve([xf(c, x, y, flip=flip) for c in cuts], layer)

def padi_row(cv, x0, x1, y, h, seed=1, layer='mid', gap=0.32, young=True, pid=None):
    """A planted row of padi clumps (fan of blades; ripe ones droop grain heads)."""
    rnd = random.Random(seed)
    polys = []
    x = x0
    while x < x1:
        hh = h * rnd.uniform(0.8, 1.1)
        n = 7
        for j in range(n):
            a = 90 + (j - (n - 1) / 2) * 13 + rnd.uniform(-4, 4)
            polys.append(leaf(x + (j - 3) * 0.008, y, a, hh * (1 - abs(j - 3) * 0.07), 0.016 * h ** 0.3,
                              bend=-0.03 * (j - 3) * hh))
        if not young:
            for j in (-1, 1):
                tip = (x + j * hh * 0.35, y + hh * 0.8)
                polys.append(ribbon(_open([(x, y + hh * 0.5), (x + j * hh * 0.2, y + hh * 1.0), tip]), 0.01, 0.004))
                polys.append(leaf(tip[0], tip[1], -90 + j * 30, hh * 0.3, 0.03, bend=0.02 * j))
        x += gap * rnd.uniform(0.85, 1.15)
    return cv.add(polys, 'solid', layer, pid=pid)

def field(cv, x0, x1, y, h=0.7, rows=4, seed=1, layer='mid', young=True):
    """Receding flooded paddy: bunds as thin lines, rows shrinking with distance."""
    for k in range(rows - 1, -1, -1):
        s = 1 - 0.2 * k
        yy = y + k * 0.42
        cv.add([ribbon(_open([(x0, yy - 0.02), ((x0 + x1) / 2, yy + 0.03), (x1, yy - 0.01)]), 0.03 * s)], 'solid', layer)
        padi_row(cv, x0 + 0.1, x1, yy, h * s, seed + k, layer, gap=0.34 * s, young=young)

def pondok(cv, x, y, s=1.0, layer='mid', flip=False):
    """Pondok padi: stilt hut, attap roof with crossed gable boards, bamboo walls, ladder."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    posts = [P(ribbon([(px, 0.0), (px, 1.05)], 0.045)) for px in (-0.8, -0.25, 0.3, 0.8)]
    cv.add(posts + [P(rect(-0.95, 0.95, 0.95, 1.08))], 'solid', layer)
    cv.add_eo([P(rect(-0.85, 1.08, 0.85, 1.75)), P(rect(-0.25, 1.22, 0.3, 1.6))], 'grid', layer)
    roof = P([(-1.3, 1.62), (-0.95, 2.45), (0.95, 2.45), (1.3, 1.62), (1.1, 1.66), (0.0, 1.7), (-1.1, 1.66)])
    cv.add([roof], 'scales', layer)
    cv.add([P(ribbon([(-1.05, 2.25), (-0.75, 2.75)], 0.03, 0.015)), P(ribbon([(-0.85, 2.25), (-1.15, 2.75)], 0.03, 0.015)),
            P(ribbon([(1.05, 2.25), (0.75, 2.75)], 0.03, 0.015)), P(ribbon([(0.85, 2.25), (1.15, 2.75)], 0.03, 0.015)),
            P(ribbon([(-0.95, 2.45), (0.95, 2.45)], 0.035))], 'solid', layer)
    rungs = [P(ribbon([(1.05 + 0.1 * t, 0.1 + t), (1.35 + 0.1 * t, 0.1 + t)], 0.02)) for t in (0.2, 0.45, 0.7)]
    cv.add([P(ribbon([(0.95, 1.0), (1.25, 0.0)], 0.03)), P(ribbon([(1.25, 1.0), (1.55, 0.0)], 0.03))] +
           [P(ribbon([(1.0 + 0.3 * t, 1.0 - t), (1.3 + 0.3 * t, 1.0 - t)], 0.018)) for t in (0.25, 0.5, 0.75)], 'solid', layer)

def grass(cv, x0, x1, y, h, seed=1, layer='front', n=None, lean=0.0):
    rnd = random.Random(seed)
    polys = []
    for i in range(n or int((x1 - x0) / 0.12)):
        x = rnd.uniform(x0, x1)
        hh = h * rnd.uniform(0.5, 1.0)
        polys.append(leaf(x, y, 90 + rnd.uniform(-25, 25) + lean, hh, 0.035 * h ** 0.5, bend=rnd.uniform(-0.25, 0.25) * hh))
    return cv.add(polys, 'solid', layer)

def rumah(cv, x, y, s=1.0, layer='mid', flip=False):
    """Rumah kampung: house on stilts, tall gabled roof with crossed gable boards
    and finial, a lower serambi roof, carved window openings, front stair."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    cv.add([P(ribbon([(px, 0.0), (px, 1.0)], 0.05)) for px in (-1.4, -0.7, 0.0, 0.7, 1.4, 2.1)], 'solid', layer)
    cv.add_eo([P(rect(-1.55, 0.95, 1.55, 2.25))] + [P(rect(-1.25 + 0.85 * i, 1.3, -0.85 + 0.85 * i, 1.95)) for i in range(3)],
              'grid', layer)
    cv.add([P([(-2.05, 2.05), (-1.15, 3.55), (1.15, 3.55), (2.05, 2.05), (1.7, 2.12), (-1.7, 2.12)])], 'scales', layer)
    cv.add([P(ribbon([(-1.35, 3.25), (-0.95, 3.95)], 0.04, 0.02)), P(ribbon([(-0.95, 3.25), (-1.35, 3.95)], 0.04, 0.02)),
            P(ribbon([(1.35, 3.25), (0.95, 3.95)], 0.04, 0.02)), P(ribbon([(0.95, 3.25), (1.35, 3.95)], 0.04, 0.02)),
            P(ribbon([(-1.15, 3.55), (1.15, 3.55)], 0.045))], 'solid', layer)
    cv.add_eo([P(rect(1.55, 0.95, 2.55, 1.7)), P(rect(1.75, 1.15, 2.35, 1.55))], 'grid', layer)
    cv.add([P([(1.45, 1.95), (2.85, 1.55), (2.75, 1.48), (1.45, 1.8)])], 'scales', layer)
    cv.add([P(ribbon([(2.55, 1.0), (2.95, 0.0)], 0.035)), P(ribbon([(2.25, 1.0), (2.65, 0.0)], 0.035))] +
           [P(ribbon([(2.3 + 0.4 * t, 1.0 - t), (2.6 + 0.4 * t, 1.0 - t)], 0.025)) for t in (0.25, 0.5, 0.75)], 'solid', layer)

def raintree(cv, x, y, h, layer='mid', seed=1, flip=False):
    """Pokok hujan-hujan: stout trunk forking into limbs that hold up a wide,
    lumpy umbrella crown."""
    rnd = random.Random(seed)
    P = lambda pts: xf(pts, x, y, flip=flip)
    trunk = [ribbon(_open([(0, 0), (0.05 * h, 0.25 * h), (0.0, 0.45 * h)]), 0.1 * h, 0.065 * h)]
    tips = []
    for a, L in ((150, 0.55), (120, 0.4), (88, 0.32), (60, 0.42), (28, 0.55)):
        e = (L * h * math.cos(math.radians(a)), 0.45 * h + L * h * 0.62 * math.sin(math.radians(a)) + 0.06 * h)
        trunk.append(ribbon(_open([(0, 0.42 * h), (e[0] * 0.45, 0.45 * h + (e[1] - 0.45 * h) * 0.75), e]), 0.045 * h, 0.014 * h))
        tips.append(e)
    cv.add([P(t) for t in trunk], 'edge', layer)
    can = []
    for i, (ex, ey) in enumerate(tips):
        can += canopy(ex, ey + 0.08 * h, 0.2 * h * rnd.uniform(0.9, 1.2), seed + i, 7)
    for i in range(6):
        t = (i + 0.5) / 6
        can += canopy((-0.62 + 1.24 * t) * h, h * (0.88 + 0.1 * math.sin(math.pi * t)), 0.15 * h, seed + 20 + i, 5)
    cv.add([P(c) for c in can], 'scales', layer)

def fence(cv, x0, x1, y, h=0.6, layer='mid', gap=0.42):
    posts = []
    x = x0
    while x <= x1:
        posts.append([(x - 0.045, y), (x + 0.045, y), (x + 0.045, y + h), (x, y + h + 0.08), (x - 0.045, y + h)])
        x += gap
    posts += [ribbon([(x0, y + h * k), (x1, y + h * k)], 0.022) for k in (0.35, 0.75)]
    return cv.add(posts, 'solid', layer)

def milestone(cv, x, y, s=1.0, layer='mid'):
    """Batu tanda: rounded white road stone with a carved number band."""
    poly = [(-0.3, 0.0), (0.3, 0.0), (0.3, 0.7)] + arc_pts(0.0, 0.7, 0.3, 0, 180, 12)[1:-1] + [(-0.3, 0.7)]
    cv.add([xf(poly, x, y, s=s)], 'edge', layer)
    cv.carve([xf(rect(-0.18, 0.5, 0.18, 0.56), x, y, s=s), xf(rect(-0.12, 0.3, 0.12, 0.42), x, y, s=s)], layer)

# =====================================================================
# prop kit: water works and machines
# =====================================================================

def wheel(cv, cx, cy, r, spokes=8, layer='mid', knobs=True, rim=0.13, cls='edge'):
    """Spoked wheel: rim ring, turned spokes, hub; knobs make it a hand wheel."""
    pid = cv.add_eo([ellipse(cx, cy, r, n=64), ellipse(cx, cy, r * (1 - rim), n=64)], cls, layer)
    polys = [ellipse(cx, cy, r * 0.16, n=24)]
    for i in range(spokes):
        a = math.radians(360 * i / spokes + 11)
        d = (math.cos(a), math.sin(a))
        polys.append(ribbon([(cx + d[0] * r * 0.1, cy + d[1] * r * 0.1), (cx + d[0] * r * 0.92, cy + d[1] * r * 0.92)],
                            r * 0.035, r * 0.05))
        if knobs:
            polys.append(ribbon([(cx + d[0] * r * 0.95, cy + d[1] * r * 0.95), (cx + d[0] * r * 1.22, cy + d[1] * r * 1.22)],
                                r * 0.045, r * 0.07))
    cv.add(polys, 'solid', layer, pid=pid)
    cv.carve([ellipse(cx, cy, r * 0.06, n=12)], layer)
    return pid

def water_run(cv, x0, x1, y, h=0.45, layer='mid', flow=1, seed=1):
    """Running water: a band whose top breaks into curling wavelets (ombak)."""
    rnd = random.Random(seed)
    n = max(2, int((x1 - x0) / 0.7))
    pid = cv.add([[(x0, y - 0.1), (x1, y - 0.1), (x1, y + h * 0.5), (x0, y + h * 0.5)]], 'scales', layer)
    curls = []
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        r = h * rnd.uniform(0.3, 0.42)
        curls.append(scroll(x + flow * r * 0.4, y + h * 0.5 + r, r, r * 0.32, 1.2, a0=180 if flow > 0 else 0, cw=flow > 0,
                            tail=[(x - flow * r * 1.6, y + h * 0.42), (x - flow * r * 0.8, y + h * 0.55)]))
    cv.add(curls, 'edge', layer, pid=pid)
    return pid

def sluice(cv, x, y, s=1.0, layer='mid', open_h=0.55):
    """Pintu air: two capped posts, a raised plank gate, spindle and hand wheel."""
    P = lambda pts: xf(pts, x, y, s=s)
    posts = []
    for px in (-0.9, 0.9):
        posts.append(P(rect(px - 0.13, -0.2, px + 0.13, 1.9)))
        posts.append(P([(px - 0.2, 1.9), (px + 0.2, 1.9), (px + 0.15, 2.0), (px, 2.12), (px - 0.15, 2.0)]))
    cv.add(posts, 'edge', layer)
    cv.add([P(rect(-1.05, 1.62, 1.05, 1.82))], 'edge', layer)
    cv.add([P(rect(-0.77, open_h, 0.77, 1.5))], 'slits', layer)
    cv.add([P(ribbon([(0.0, 1.45), (0.0, 2.25)], 0.05)), P(rect(-0.2, 1.82, 0.2, 1.95))], 'solid', layer)
    wheel(cv, x, y + 2.25 * s, 0.42 * s, 8, layer)

# =====================================================================
# prop kit: kitchen, dishes and ingredients
# =====================================================================

def mirror_pts(left, cx=0.0):
    """Close a left half-profile (top to bottom) with its mirror image."""
    return left + [(2 * cx - x, y) for x, y in reversed(left)]

# left half-profile of the mangkuk, rim to foot, in (x / width, y / depth); the
# silhouette and the colour icon lathe both use it
BOWL_PROFILE = [(-0.51, 1.02), (-0.49, 0.88), (-0.44, 0.6), (-0.34, 0.32), (-0.22, 0.14), (-0.17, 0.1),
                (-0.19, 0.08), (-0.2, 0.0)]
BOWL_DEPTH = 0.48

def bowl(cv, cx, y, w, layer='mid', cls='flower', heap='laksa', seed=1):
    """Mangkuk side-on: flared porcelain bowl on a foot ring with a carved rim
    band, heaped with the dish ('laksa': noodles and toppings; 'rice'; None)."""
    rnd = random.Random(seed)
    h = w * BOWL_DEPTH
    if heap:
        mound = _open([(-0.45 * w, h * 0.85), (-0.38 * w, h * 1.08), (-0.2 * w, h * 1.24), (0.0, h * 1.3),
                       (0.22 * w, h * 1.22), (0.38 * w, h * 1.06), (0.45 * w, h * 0.85)], 5)
        polys = [xf(mound, cx, y)]
        if heap == 'laksa':
            for i in range(7):                          # cucumber batons and herb sprigs
                bx = (-0.3 + 0.1 * i) * w + rnd.uniform(-0.02, 0.02) * w
                by = h * (1.15 + 0.08 * math.sin(i))
                a = 90 + rnd.uniform(-35, 35)
                if i % 2:
                    polys.append(xf(ribbon([(0, 0), (0.0, 0.16 * w)], 0.012 * w), cx + bx, y + by, rot=a - 90))
                else:
                    for j in range(4):
                        polys.append(leaf(cx + bx, y + by, a + (j - 1.5) * 28, 0.12 * w, 0.03 * w, bend=0.02 * w * (j - 1.5)))
            polys.append(ellipse(cx + 0.1 * w, y + h * 1.32, 0.09 * w, 0.065 * w))   # egg half
            polys.append(leaf(cx - 0.12 * w, y + h * 1.3, 75, 0.2 * w, 0.025 * w, bend=0.04 * w))  # chilli
        cv.add(polys, 'edge', layer)
        if heap == 'laksa':
            cv.carve([ellipse(cx + 0.1 * w, y + h * 1.32, 0.04 * w, 0.03 * w)] +
                     [W.circle(cx + (0.05 - 0.13 * i) * w, y + h * (1.2 + 0.05 * (i % 2)), 0.018 * w, 12)[0] for i in range(4)],
                     layer)
    left = _open([(x * w, yy * h) for x, yy in BOWL_PROFILE[:6]], 5) + [(x * w, yy * h) for x, yy in BOWL_PROFILE[6:]]
    body = xf(mirror_pts(left), cx, y)
    cv.add([body], cls, layer)
    band = [W.diamond(cx + x * w, y + h * 0.86, 0.045 * w, 0.06 * h)[0] for x in (-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4)]
    cv.carve(band + [ribbon(_open([(cx - 0.47 * w, y + h * 0.75), (cx, y + h * 0.73), (cx + 0.47 * w, y + h * 0.75)]), 0.006 * w),
                     ribbon([(cx - 0.18 * w, y + h * 0.13), (cx + 0.18 * w, y + h * 0.13)], 0.005 * w)], layer)
    if heap == 'laksa':                                 # noodles slipping over the rim
        nd = [ribbon(_open([(cx + sx * 0.36 * w, y + h * 1.06), (cx + sx * 0.48 * w, y + h * 1.04),
                            (cx + sx * 0.5 * w, y + h * 0.9), (cx + sx * (0.47 + 0.02 * k) * w, y + h * (0.72 - 0.06 * k))]),
                     0.011 * w, 0.008 * w) for sx in (-1, 1) for k in range(2)]
        cv.add(nd, 'solid', layer)
    return y + h

def stand(cv, cx, y, w, h, layer='mid'):
    """Dulang berkaki: footed serving tray, lathe-turned waist."""
    left = _open([(-0.56 * w, h), (-0.5 * w, h * 0.86), (-0.18 * w, h * 0.78), (-0.1 * w, h * 0.6), (-0.13 * w, h * 0.42),
                  (-0.09 * w, h * 0.3), (-0.2 * w, h * 0.12), (-0.38 * w, 0.0)], 4)
    cv.add([xf(mirror_pts(left), cx, y)], 'lace', layer)

def steam(cv, x, y, h, cw=True, layer='mid', w=0.075, seed=1):
    """A rising wisp that sways and ends in a curl."""
    ph = random.Random(seed).uniform(0, 6)
    tail = [(x + 0.16 * math.sin(t * 2.4 * math.pi + ph) * (0.3 + t), y + h * 0.78 * t) for t in (i / 14 for i in range(15))]
    r = h * 0.12
    a0 = 180 if cw else 0
    ex, ey = tail[-1]
    return cv.add([scroll(ex + r, ey, r, w, 1.35, a0=a0, cw=cw, tail=tail, wt=w * 0.35) if cw else
                   scroll(ex - r, ey, r, w, 1.35, a0=a0, cw=cw, tail=tail, wt=w * 0.35)], 'edge', layer)

def flame(cx, y, h, n=5, seed=1):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        x = cx + (i - (n - 1) / 2) * h * 0.22
        hh = h * (1 - abs(i - (n - 1) / 2) * 0.22) * rnd.uniform(0.85, 1.1)
        out.append(leaf(x, y, 90 + (i - (n - 1) / 2) * 9, hh, h * 0.12, bend=h * 0.12 * (1 if i % 2 else -1)))
    return out

def periuk(cv, cx, y, s, layer='mid', lid=True):
    """Clay pot: round belly, neck, rolled rim, lid with a knob, lug handles."""
    left = _open([(-0.42 * s, 0.82 * s), (-0.4 * s, 0.76 * s), (-0.46 * s, 0.6 * s), (-0.52 * s, 0.38 * s),
                  (-0.45 * s, 0.14 * s), (-0.26 * s, 0.01 * s), (0.0, 0.0)], 5)[:-1]
    polys = [xf(mirror_pts(left), cx, y)]
    polys += [xf(ribbon(arc_pts(sx * 0.5 * s, 0.6 * s, 0.07 * s, 90 + 90 * sx, 270 + 90 * sx, 10), 0.022 * s), cx, y)
              for sx in (-1, 1)]
    if lid:
        polys += [xf(_open([(-0.4 * s, 0.84 * s), (-0.25 * s, 0.95 * s), (0.0, 0.99 * s), (0.25 * s, 0.95 * s),
                            (0.4 * s, 0.84 * s)], 5), cx, y), xf(ellipse(0, 1.03 * s, 0.07 * s, 0.05 * s), cx, y)]
    cv.add(polys, 'dots', layer)
    cv.carve([xf(ribbon(_open([(-0.44 * s, 0.5 * s), (0.0, 0.47 * s), (0.44 * s, 0.5 * s)]), 0.01 * s), cx, y)], layer)

def dapur(cv, cx, y, s, layer='mid', pot=True, seed=1):
    """Dapur kayu: clay hearth with a fire arch, burning sticks and a pot on top."""
    P = lambda pts: xf(pts, cx, y, s=s)
    body = [(-0.85, 0.0), (0.85, 0.0), (0.72, 0.9), (-0.72, 0.9)]
    arch = [(-0.42, 0.0)] + arc_pts(0.0, 0.32, 0.42, 180, 0, 16)[1:-1] + [(0.42, 0.0)]
    cv.add_eo([P(body), P(arch)], 'grid', layer)
    cv.add([P(rect(-0.9, 0.86, 0.9, 0.98))], 'edge', layer)
    cv.add([P(f) for f in flame(0.0, 0.05, 0.62, 5, seed)] +
           [P(ribbon([(-0.15 + 0.15 * i, 0.08 + 0.02 * i), (-1.05 + 0.25 * i, -0.02 + 0.12 * i)], 0.045, 0.04)) for i in range(3)],
           'solid', layer)
    if pot:
        periuk(cv, cx, y + 0.97 * s, 1.15 * s, layer)

def fish(cv, x, y, s, flip=False, layer='mid', ang=0.0):
    """Ikan kembung: spindle body with scales, forked tail, fins and finlets."""
    P = lambda pts: xf(pts, x, y, s=s, rot=ang, flip=flip)
    body = _open([(0.62, 0.02), (0.5, 0.14), (0.2, 0.22), (-0.2, 0.19), (-0.48, 0.07), (-0.56, 0.02)], 5) +         _open([(-0.56, -0.02), (-0.48, -0.06), (-0.2, -0.17), (0.2, -0.18), (0.5, -0.1), (0.62, 0.02)], 5)[1:]
    tail = [(-0.5, 0.0), (-0.78, 0.2), (-0.72, 0.03), (-0.78, -0.17)]
    fins = [[(0.02, 0.2), (-0.12, 0.34), (-0.18, 0.19)], [(-0.22, 0.17), (-0.3, 0.26), (-0.36, 0.13)],
            [(-0.1, -0.16), (-0.22, -0.27), (-0.26, -0.13)], leaf(0.22, -0.04, -150, 0.2, 0.04)]
    fins += [[(-0.38 - 0.04 * i, 0.1 - 0.012 * i), (-0.41 - 0.04 * i, 0.16 - 0.012 * i), (-0.42 - 0.04 * i, 0.09 - 0.012 * i)]
             for i in range(3)]
    cv.add([P(body)] + [P(t) for t in (tail,)] + [P(f) for f in fins], 'scales', layer)
    cv.carve([P(W.circle(0.47, 0.05, 0.035, 14)[0]),
              P(ribbon(_open([(0.34, 0.15), (0.3, 0.02), (0.34, -0.11)]), 0.012))], layer)

def chillies(cv, x, y, s, layer='mid', n=3, seed=1):
    rnd = random.Random(seed)
    polys = []
    for i in range(n):
        a = 160 + i * 14 + rnd.uniform(-6, 6)
        bx = x + i * 0.1 * s
        polys.append(leaf(bx, y + 0.06 * s, a, 0.62 * s, 0.05 * s, bend=0.1 * s, wide_at=0.2))
        polys.append(ribbon(_open([(bx, y + 0.06 * s), (bx + 0.06 * s, y + 0.12 * s), (bx + 0.08 * s, y + 0.18 * s)]), 0.012 * s))
    return cv.add(polys, 'solid', layer)

def limes(cv, x, y, s, layer='mid', n=3):
    polys = [ellipse(x + i * 0.27 * s, y + 0.12 * s + (0.12 * s if i == 1 else 0), 0.13 * s, 0.12 * s) for i in range(n)]
    polys.append(leaf(x + 0.27 * s, y + 0.36 * s, 50, 0.3 * s, 0.07 * s))
    cv.add(polys, 'edge', layer)
    cv.carve([ellipse(x + i * 0.27 * s, y + 0.12 * s + (0.12 * s if i == 1 else 0), 0.035 * s, 0.03 * s) for i in range(n)], layer)

def kantan(cv, x, y, h, layer='mid', lean=0.0):
    """Bunga kantan (torch ginger): tall stalk and a waxy torch of bracts."""
    top = (x + lean * h, y + h * 0.72)
    bud = []
    for i in range(7):
        a = 90 + (i - 3) * 22
        bud.append(leaf(top[0], top[1] - 0.04 * h, a, h * (0.24 - abs(i - 3) * 0.025), h * 0.06))
    bud.append(ellipse(top[0], top[1] + h * 0.1, h * 0.09, h * 0.13))
    cv.add([ribbon(_open([(x, y), (x + lean * h * 0.4, y + h * 0.4), top]), h * 0.018, h * 0.014)] + bud, 'edge', layer)

def serai(cv, x, y, h, layer='mid', n=5):
    """Lemongrass bundle: stalks tied together, leaves fanning out."""
    polys = []
    for i in range(n):
        dx = (i - (n - 1) / 2) * 0.05 * h
        polys.append(ribbon([(x + dx, y), (x + dx * 1.3, y + h * 0.55)], 0.03 * h, 0.022 * h))
        polys.append(leaf(x + dx * 1.3, y + h * 0.5, 90 + dx * 160, h * 0.55, 0.018 * h, bend=dx * 1.5))
    cv.add(polys, 'solid', layer)
    cv.carve([ribbon([(x - 0.15 * h, y + h * 0.18), (x + 0.15 * h, y + h * 0.18)], 0.008 * h)], layer)

def jar(cv, x, y, s, layer='mid', cls='lace'):
    """Tempayan / tajau: big-shouldered storage jar with lugs."""
    left = _open([(-0.22 * s, 1.0 * s), (-0.2 * s, 0.9 * s), (-0.3 * s, 0.82 * s), (-0.46 * s, 0.6 * s),
                  (-0.42 * s, 0.25 * s), (-0.26 * s, 0.02 * s), (-0.2 * s, 0.0)], 5)
    cv.add([xf(mirror_pts(left), x, y)] + [ellipse(x + sx * 0.38 * s, y + 0.72 * s, 0.06 * s, 0.05 * s) for sx in (-1, 1)],
           cls, layer)

def plate(cv, cx, y, w, layer='mid'):
    left = [(-0.5 * w, 0.09 * w), (-0.42 * w, 0.03 * w), (-0.2 * w, 0.0)]
    return cv.add([xf(mirror_pts(left), cx, y)], 'solid', layer)

def kitchen_back(cv, seed=1):
    """Blurred kampung kitchen behind a dish: lattice window, jars, a shelf of pots."""
    cv.add_eo([rect(0.8, 2.2, 4.6, 6.6), rect(1.1, 2.5, 4.3, 6.3)], 'edge', 'back')
    cv.add([ribbon([(1.1 + 0.53 * i, 2.5), (1.1 + 0.53 * i, 6.3)], 0.03) for i in range(1, 6)] +
           [ribbon([(1.1, 4.4), (4.3, 4.4)], 0.04)], 'solid', 'back')
    cv.add([rect(14.6, 4.95, 19.6, 5.1)], 'solid', 'back')
    for i, x in enumerate((15.2, 16.4, 17.7, 18.9)):
        periuk(cv, x, 5.1, 0.7 + 0.15 * (i % 2), 'back', lid=i % 2 == 0)
    jar(cv, 15.6, G, 2.0, 'back')
    jar(cv, 17.6, G, 1.6, 'back')
    for x in (6.0, 7.0, 13.4):
        cv.add([ribbon([(x, 8.3), (x, 7.4)], 0.02)] + [leaf(x, 7.45, -90 + k * 12, 0.7, 0.07) for k in (-1, 0, 1)], 'solid', 'back')

# =====================================================================
# prop kit: sea, storm and ships
# =====================================================================

def wave(cv, x, base, w, h, flip=False, layer='mid', seed=1, claws=5):
    """Ombak: a wayang breaker. Rising back, a crest curling over into a
    spiral, foam claws on the lip, flow lines cut into the body."""
    rnd = random.Random(seed)
    P = lambda pts: xf(pts, x, base, flip=flip)
    r = 0.3 * h
    c = (0.2 * w, 0.66 * h)
    body = _open([(-0.5 * w, 0.0), (-0.36 * w, 0.18 * h), (-0.18 * w, 0.52 * h), (0.0, 0.86 * h),
                  (c[0] - r * 0.75, c[1] + r * 0.72)], 5) + \
        _open([(c[0] + r * 0.1, c[1] - r * 0.55), (c[0] - 0.02 * w, 0.3 * h), (c[0] + 0.06 * w, 0.1 * h), (0.42 * w, 0.0)], 5)
    curl = scroll(c[0], c[1], r, r * 0.42, 1.3, a0=140, cw=True)
    polys = [P(body + [(0.42 * w, -0.05), (-0.5 * w, -0.05)]), P(curl)]
    for i in range(claws):
        along = 12 + i * 130 / max(claws - 1, 1)          # degrees wound from the spiral start
        a = math.radians(140 - along + rnd.uniform(-4, 4))
        rr = r * (1 - 0.85 * along / 468) + r * 0.22
        px, py = c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)
        tang = math.degrees(a) - 90
        polys.append(P(leaf(px - 0.05 * r * math.cos(a), py - 0.05 * r * math.sin(a), tang + 25, r * 0.55, r * 0.11,
                            bend=-r * 0.12)))
    pid = cv.add(polys, 'scales', layer)
    cuts = []
    for k in range(3):
        t = 0.25 + 0.22 * k
        y0 = h * (0.12 + 0.2 * k)
        cuts.append(P(ribbon(_open([(-0.42 * w + 0.12 * w * k, y0 * 0.4), (-0.25 * w + 0.1 * w * k, y0),
                                    (-0.08 * w + 0.08 * k * w, y0 * 1.25 + 0.1 * h)]), 0.006, 0.016)))
    cv.carve(cuts, layer)
    return pid

def spray(cv, x, y, s, flip=False, layer='mid', seed=1):
    """Flying foam: a fan of small curls and droplets."""
    rnd = random.Random(seed)
    polys = []
    for i in range(5):
        a = math.radians(30 + i * 28)
        L = s * rnd.uniform(0.6, 1.0)
        tip = (x + L * math.cos(a), y + L * math.sin(a))
        polys.append(scroll(tip[0], tip[1], 0.12 * s, 0.035 * s, 1.1, a0=180 + math.degrees(a) - 90, cw=i % 2 == 0,
                            tail=[(x, y), (x + L * 0.6 * math.cos(a), y + L * 0.6 * math.sin(a))]))
        polys.append(ellipse(tip[0] + 0.25 * s * math.cos(a), tip[1] + 0.25 * s * math.sin(a), 0.05 * s, n=10))
    polys = [xf(p, flip=flip, ox=x) for p in polys]
    return cv.add(polys, 'solid', layer)

def lightning(cv, x, y_top, y_bot, w=0.2, layer='mid', seed=1):
    """Petir: a hard zigzag bolt with a forked branch."""
    rnd = random.Random(seed)
    n = 7
    pts = [(x, y_top)]
    for i in range(1, n + 1):
        t = i / n
        pts.append((x + (0.45 if i % 2 else -0.15) + rnd.uniform(-0.1, 0.1) + t * 0.5, y_top + (y_bot - y_top) * t))
    pid = cv.add([ribbon(pts, w * 0.5, w * 0.06)], 'solid', layer)
    f = pts[3]
    cv.add([ribbon([f, (f[0] - 0.45, f[1] - 0.35), (f[0] - 0.3, f[1] - 0.7), (f[0] - 0.8, f[1] - 1.2)], w * 0.25, w * 0.03)],
           'solid', layer, pid=pid)

def rain(cv, x0, x1, y0, y1, n=60, layer='back', slant=0.35, seed=1):
    rnd = random.Random(seed)
    polys = []
    for i in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        L = rnd.uniform(0.5, 1.1)
        polys.append(ribbon([(x, y), (x - slant * L, y - L)], 0.018, 0.008))
    return cv.add(polys, 'solid', layer)

def barrel(x, y, s, rot=0.0):
    body = [(-0.3, -0.42), (0.3, -0.42), (0.36, -0.2), (0.38, 0.0), (0.36, 0.2), (0.3, 0.42), (-0.3, 0.42),
            (-0.36, 0.2), (-0.38, 0.0), (-0.36, -0.2)]
    return xf(body, x, y, s=s, rot=rot), [xf(ribbon([(-0.37, k), (0.37, k)], 0.025), x, y, s=s, rot=rot) for k in (-0.24, 0.24)]

# hull profile of a three-masted foreign ship, stern at -x, bow at +x (deck to keel)
SHIP_TOP = [(-3.45, 2.6), (-2.6, 2.52), (-1.95, 2.45), (-1.85, 1.95), (-0.5, 1.78), (1.0, 1.75), (2.0, 1.85),
            (2.15, 2.2), (3.0, 2.3), (3.8, 2.5)]
SHIP_BOT = [(3.8, 2.5), (3.72, 1.7), (3.45, 1.0), (2.8, 0.48), (1.5, 0.16), (0.0, 0.06), (-1.6, 0.14),
            (-2.75, 0.45), (-3.2, 0.95), (-3.38, 1.6), (-3.45, 2.6)]

def _interp(prof, x):
    """y of a polyline (sorted by x either way) at x."""
    pts = sorted(prof)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)
    return pts[0][1] if x < pts[0][0] else pts[-1][1]

def _sail(x0, x1, ytop, ybot, belly=0.18, torn=0, seed=1):
    """Square sail hung from a yard; torn > 0 rips the foot into tatters."""
    rnd = random.Random(seed)
    w = x1 - x0
    top = [(x0, ytop), (x0 + w / 2, ytop + 0.04), (x1, ytop)]
    right = _open([(x1, ytop), (x1 + belly * w * 0.3, (ytop + ybot) / 2), (x1 - 0.02 * w, ybot)], 5)[1:]
    foot = []
    n = 7
    for i in range(1, n):
        t = i / n
        yy = ybot - belly * 0.5 * math.sin(math.pi * t)
        if torn and i % 2 == 0:
            yy += (ytop - ybot) * rnd.uniform(0.15, 0.45) * torn
        foot.append((x1 - 0.02 * w - (w - 0.04 * w) * t, yy))
    left = _open([(x0 + 0.02 * w, ybot), (x0 - belly * w * 0.3, (ytop + ybot) / 2), (x0, ytop)], 5)
    return top + right + foot + left

def ship(cv, x, y, s=1.0, layer='mid', breaks=None, seed=1):
    """Three-masted ship, broadside, bow to +x. With breaks=(xb, a_stern, a_bow)
    the hull splits at xb: the two halves tilt into a V, the mainmast snaps."""
    rnd = random.Random(seed)
    xb, a_st, a_bw = breaks if breaks else (99.0, 0.0, 0.0)
    top = _open(SHIP_TOP, 6)
    bot = _open(SHIP_BOT, 6)
    halves = []
    for side in (-1, 1):
        if breaks is None and side > 0:
            break
        if breaks is None:
            hull = top + bot[1:]
            pivot, ang, shift = (0, 0), 0.0, 0.0
        else:
            keep = (lambda px: px < xb - 0.08) if side < 0 else (lambda px: px > xb + 0.08)
            T = [p for p in top if keep(p[0])]
            B = [p for p in bot if keep(p[0])]
            yt, yb = _interp(SHIP_TOP, xb), _interp(SHIP_BOT, xb)
            jag = [(xb + side * (0.08 + 0.22 * rnd.random()), yb + (yt - yb) * k / 7) for k in range(8)]
            hull = (T + jag[::-1] + B) if side < 0 else (jag + T + B)
            pivot, ang, shift = (xb, 0.2), (a_st if side < 0 else a_bw), side * 0.3
        halves.append((side, hull, pivot, ang, shift))
    for side, hull, pivot, ang, shift in halves:
        own = (lambda px: True) if breaks is None else ((lambda px: px < xb) if side < 0 else (lambda px: px > xb))
        P = lambda pts: xf(xf(pts, rot=ang, ox=pivot[0], oy=pivot[1]), x + shift * s, y, s=s, ox=0.0, oy=0.0)
        Q = lambda pts: xf(pts, x + shift * s, y, s=s)
        R = lambda pts: Q(xf(pts, rot=ang, ox=pivot[0], oy=pivot[1]))
        # masts, yards, sails (behind the hull's rail)
        for mx, mh, nyard, torn in ((-2.25, 4.6, 2, 1), (0.25, 5.8, 3, 0), (2.25, 5.0, 3, 1)):
            if not own(mx):
                continue
            deck = _interp(SHIP_TOP, mx)
            snapped = breaks is not None and abs(mx - 0.25) < 0.01
            top_y = deck + (1.7 if snapped else mh)
            mast = [ribbon([(mx, deck - 0.3), (mx, top_y)], 0.075, 0.05)]
            if snapped:
                mast.append([(mx - 0.08, top_y), (mx - 0.02, top_y + 0.35), (mx + 0.03, top_y + 0.12), (mx + 0.08, top_y + 0.28),
                             (mx + 0.08, top_y)])
            cv.add([R(m) for m in mast], 'solid', layer)
            if snapped:
                continue
            sails, yards = [], []
            for k in range(nyard):
                yy = deck + mh * (0.95 - k * 0.3)
                half = 0.75 + 0.22 * k
                yards.append(ribbon([(mx - half, yy), (mx + half, yy + 0.05)], 0.035))
                yb_ = yy - mh * 0.27
                if k < nyard - 1 or nyard == 2:
                    sails.append(_sail(mx - half + 0.05, mx + half - 0.05, yy - 0.03, yb_, torn=torn, seed=seed + k))
            for sl in sails:
                cv.add([R(sl)], 'dots', layer)
            cv.add([R(yd) for yd in yards] + [R(ribbon([(mx, deck + mh), (mx + 0.55, deck + mh - 0.12), (mx + 0.95, deck + mh + 0.05)], 0.05, 0.012))],
                   'solid', layer)
        # rigging: stays and shrouds as thin lines
        lines = []
        for mx, mh in ((-2.25, 4.6), (0.25, 5.8), (2.25, 5.0)):
            if not own(mx) or (breaks is not None and abs(mx - 0.25) < 0.01):
                continue
            deck = _interp(SHIP_TOP, mx)
            for dx in (-0.6, -0.3, 0.3, 0.6):
                lines.append(ribbon([(mx + dx, deck + 0.05), (mx, deck + mh * 0.72)], 0.012))
        if own(3.5):
            lines.append(ribbon([(2.25, _interp(SHIP_TOP, 2.25) + 5.0), (4.6, 2.85)], 0.014))
            lines.append(ribbon([(3.6, 2.45), (5.2, 3.2)], 0.06, 0.035))     # bowsprit
        if own(-3.0):
            lines.append(ribbon([(-2.25, _interp(SHIP_TOP, -2.25) + 4.6), (-3.4, 2.65)], 0.014))
        cv.add([R(l) for l in lines], 'solid', layer)
        # rail with balusters, then the planked hull in front
        rail = [p for p in _open([(-3.4, 2.95), (-1.95, 2.85), (-1.9, 2.25), (1.0, 2.1), (2.1, 2.5), (3.75, 2.8)], 6) if own(p[0])]
        if len(rail) > 2:
            posts = [ribbon([(px, _interp(SHIP_TOP, px)), (px, py)], 0.025) for px, py in rail[::3]]
            cv.add([R(ribbon(rail, 0.03))] + [R(pp) for pp in posts], 'solid', layer)
        cv.add([R(hull)], 'slits', layer)
        ports = [rect(px - 0.11, 1.18 + 0.03 * px / 3, px + 0.11, 1.4 + 0.03 * px / 3) for px in
                 (-1.4, -0.9, -0.4, 0.1, 0.6, 1.1, 1.6, 2.1, 2.6) if own(px)]
        wale = [p for p in _open([(-3.3, 1.85), (-1.0, 1.0), (1.0, 0.95), (3.5, 1.5)], 8) if own(p[0])]
        cuts = [R(pp) for pp in ports]
        if len(wale) > 2:
            cuts.append(R(ribbon(wale, 0.03)))
        if own(-3.0):
            cuts += [R(rect(-3.25 + 0.32 * i, 2.0, -3.08 + 0.32 * i, 2.3)) for i in range(3)]
        cv.carve(cuts, layer)
    if breaks is not None:                              # the snapped main topmast falling astern
        deck = _interp(SHIP_TOP, 0.25)
        stub = [ribbon([(0.0, 0.0), (0.0, 4.0)], 0.06, 0.045),
                ribbon([(-0.9, 3.0), (0.9, 3.05)], 0.035), ribbon([(-1.1, 2.0), (1.1, 2.05)], 0.035)]
        sl = _sail(-0.85, 0.85, 2.95, 2.1, torn=1, seed=seed + 9)
        T = lambda pts: xf(pts, x + (0.25 - 0.9) * s, y + (deck + 1.9) * s, s=s, rot=58)
        cv.add([T(p) for p in stub], 'solid', layer)
        cv.add([T(sl)], 'dots', layer)

# =====================================================================
# prop kit: vehicles (ride canvases are 1536x640 = 15.36 x 6.4 units, road at RIDE_Y)
# =====================================================================

RIDE = (1536, 640, 15.36)
RIDE_Y = 0.3

def bullock(cv, x, y, s=1.0, layer='mid', saddle=True):
    """Lembu (humped zebu) walking right: hump, dewlap, swept horns, tufted tail."""
    P = lambda pts: xf(pts, x, y, s=s)
    legs = []
    for hx, hy, kx, fx, near in ((0.72, 1.4, 0.95, 1.12, False), (0.55, 1.4, 0.48, 0.32, True),
                                 (-1.05, 1.5, -1.2, -1.3, False), (-1.25, 1.5, -1.0, -0.9, True)):
        knee = (kx, 0.62)
        legs.append(P(ribbon([(hx, hy), knee], 0.16, 0.08)))
        legs.append(P(ribbon([knee, (fx, 0.1)], 0.07, 0.055)))
        legs.append(P([(fx - 0.09, 0.0), (fx + 0.12, 0.0), (fx + 0.06, 0.13), (fx - 0.07, 0.13)]))
    cv.add(legs[:3] + legs[6:9], 'solid', layer)
    torso = _open([(-1.55, 1.55), (-1.5, 2.05), (-1.2, 2.2), (-0.3, 2.12), (0.35, 2.2), (0.55, 2.55), (0.78, 2.86),
                   (1.0, 2.8), (1.1, 2.45), (1.38, 2.3)], 5) + \
        [(1.55, 2.28), (1.68, 2.22), (2.05, 1.72), (2.18, 1.5), (2.08, 1.4), (1.9, 1.44), (1.7, 1.52)] + \
        _open([(1.62, 1.45), (1.42, 1.08), (1.12, 0.92), (0.85, 1.12), (0.2, 1.2), (-0.5, 1.18), (-1.1, 1.3),
               (-1.4, 1.38), (-1.55, 1.55)], 5)
    horn = _open([(1.55, 2.25), (1.5, 2.55), (1.58, 2.78), (1.76, 2.9), (1.86, 2.86)], 5)
    body = [P(torso), P(ribbon(horn, 0.055, 0.012)), P(ribbon(xf(horn, -0.13, -0.02), 0.045, 0.01)),
            P(leaf(1.56, 2.12, 200, 0.32, 0.075, bend=-0.05)),
            P(ribbon(_open([(-1.5, 2.0), (-1.62, 1.6), (-1.6, 1.0)]), 0.03, 0.02)), P(leaf(-1.6, 1.05, -95, 0.32, 0.07))]
    pid = cv.add(body + legs[3:6] + legs[9:], 'lace', layer)
    cv.carve([P(leaf(1.72, 2.02, -35, 0.1, 0.024))], layer)
    if saddle:
        cv.add([P(_open([(-0.75, 2.1), (-0.2, 2.2), (0.35, 2.15)], 4) + [(0.3, 1.55), (-0.7, 1.55)])], 'flower', layer)
        cv.add([P(leaf(-0.7 + 0.2 * i, 1.55, -90, 0.2, 0.035)) for i in range(6)], 'solid', layer)
    return pid

# =====================================================================
# shared framing (used by the state compositions)
# =====================================================================

def frame_edges(cv, seed=1, left='banana', right='palm'):
    """Front-layer framing at the canvas edges, low so the centre stays open."""
    for side, kind in ((-1, left), (1, right)):
        x = 0.6 if side < 0 else 19.9
        if kind == 'banana':
            banana(cv, x, 0.2, 4.5, seed + (side > 0), 'front', flip=side > 0)
        elif kind == 'palm':
            palm(cv, x + side * 0.2, 0.0, 7.2, lean=-0.18 * side, seed=seed + 2, layer='front', fronds=8)
    grass(cv, -0.2, 3.0, 0.0, 1.3, seed + 3)
    grass(cv, 17.6, 20.7, 0.0, 1.2, seed + 4)

# =====================================================================
# colour icons (EEVEE, 256x256): soft key light, transparent, merbau-icon style
# =====================================================================

TAU = math.tau

def _icon_scene():
    W.wipe()
    for co in list(bpy.data.collections):
        bpy.data.collections.remove(co)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.eevee.taa_render_samples = 64
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    st = sc.render.image_settings
    st.file_format, st.color_mode, st.color_depth, st.compression = 'PNG', 'RGBA', '8', 0
    wd = bpy.data.worlds.new('IconWorld')
    wd.use_nodes = True
    bg = wd.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.42, 0.4, 0.38, 1)
    bg.inputs[1].default_value = 0.3
    sc.world = wd
    for name, loc, energy, size, col in (('Key', (-3.2, -3.6, 5.0), 420, 3.0, (1.0, 0.93, 0.82)),
                                         ('Fill', (4.0, -2.5, 2.0), 90, 4.0, (0.85, 0.9, 1.0)),
                                         ('Rim', (0.5, 4.5, 3.5), 300, 2.0, (1.0, 0.95, 0.9))):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy, ld.size, ld.color = energy, size, col
        ob = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(ob)
        ob.location = loc
        _aim(ob, (0, 0, 0.4))
    return sc

def _aim(ob, target):
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def _icon_cam(sc, loc, target, lens=70):
    cd = bpy.data.cameras.new('IconCam')
    cd.lens = lens
    cam = bpy.data.objects.new('IconCam', cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    _aim(cam, target)
    sc.camera = cam

def _mat(name, rgb, rough=0.45, metal=0.0, coat=0.0, grain=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*rgb, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    if coat:
        bs.inputs['Coat Weight'].default_value = coat
    if grain:                                          # stretched wood grain between rgb and grain
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1.0, 1.0, 0.25)
        wv = nt.nodes.new('ShaderNodeTexWave')
        wv.wave_type = 'BANDS'
        wv.bands_direction = 'Z'
        wv.inputs['Scale'].default_value = 9.0
        wv.inputs['Distortion'].default_value = 5.0
        wv.inputs['Detail'].default_value = 3.0
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (*grain, 1)
        ramp.color_ramp.elements[1].color = (*rgb, 1)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
        nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], bs.inputs['Base Color'])
    return m

def _obj(name, me, mat):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob

def _lathe(name, prof, mat, segs=64, smooth=True, sharp=35):
    """Revolve a (r, z) profile (open, bottom to top) about Z."""
    verts, faces = [], []
    for r, z in prof:
        for k in range(segs):
            a = TAU * k / segs
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(len(prof) - 1):
        for k in range(segs):
            a, b = i * segs + k, i * segs + (k + 1) % segs
            faces.append((a, b, b + segs, a + segs))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if smooth:
        me.shade_smooth()
        if sharp:
            me.set_sharp_from_angle(angle=math.radians(sharp))
    return _obj(name, me, mat)

def _tube(name, pts, r, mat, res=6):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    return _obj(name, cu, mat)

def _blob(name, loc, scale, rot, mat, seg=16):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    ob = _obj(name, me, mat)
    ob.location, ob.scale, ob.rotation_euler = loc, scale, rot
    return ob

def _box(name, loc, size, rot, mat):
    me = bpy.data.meshes.new(name)
    sx, sy, sz = (v / 2 for v in size)
    me.from_pydata([(x * sx, y * sy, z * sz) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    ob = _obj(name, me, mat)
    ob.location, ob.rotation_euler = loc, rot
    return ob

def _torus(name, loc, R, r, mat, rot=(0, 0, 0), seg=40):
    prof = [(R + r * math.cos(TAU * i / 12), r * math.sin(TAU * i / 12)) for i in range(13)]
    ob = _lathe(name, prof, mat, seg, sharp=0)
    ob.location, ob.rotation_euler = loc, rot
    return ob

def render_icon(builder, path):
    sc = _icon_scene()
    cam, target = builder()
    _icon_cam(sc, cam, target)
    os.makedirs(W.TMP, exist_ok=True)
    tmp = os.path.join(W.TMP, 'icon_%d.png' % os.getpid())
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp, check_existing=False)
    px = W.np.empty(512 * 512 * 4, W.np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    os.remove(tmp)
    a = px.reshape(512, 512, 4)[::-1]
    pm = a[..., :3] * a[..., 3:]                         # premultiplied 2x box downsample
    pm = pm.reshape(256, 2, 256, 2, 3).mean((1, 3))
    al = a[..., 3].reshape(256, 2, 256, 2).mean((1, 3))
    rgb = pm / W.np.maximum(al[..., None], 1e-6)
    out = W.np.dstack([rgb, al])
    n = W.save_rgba_png(W.np.clip(W.np.rint(out * 255), 0, 255).astype(W.np.uint8), path)
    print('WROTE %s %d bytes' % (os.path.relpath(path, ROOT), n))

# =====================================================================
# state modules + CLI
# =====================================================================
# wayang_states/<id>.py (id = story_data id) defines PUPPET (figure spec),
# BEATS {beat: fn(cv)} and ICONS {kind: builder() -> (cam_loc, target)}.
# wayang_states/journey.py defines JOURNEY {name: fn(cv) | puppet spec}.
# Modules are imported only when a command needs them, so one state's
# half-written module can't break another state's renders.

STATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wayang_states')

def load(name):
    """The module wayang_states/<name>.py (imported once per run)."""
    return importlib.import_module('wayang_states.' + name)

def state_ids():
    return sorted(f[:-3] for f in os.listdir(STATES_DIR)
                  if f.endswith('.py') and not f.startswith('_') and f != 'journey.py')

def render_wide(fn, path, size=WIDE):
    cv = W.Canvas(*size)
    fn(cv)
    t = time.time()
    a = cv.render()
    n = W.save_alpha_png(a, path)
    print('WROTE %s %d bytes (%d parts, %.1fs)' % (os.path.relpath(path, ROOT), n, cv.pid, time.time() - t))

def render_puppet(spec, name):
    n = W.render_puppet_v2(spec, os.path.join(OUT, 'wayang_%s.png' % name))
    print('WROTE assets/wayang/wayang_%s.png %d bytes' % (name, n))

def cmd_icons(ids):
    for sid in ids or state_ids():
        for kind, builder in getattr(load(sid), 'ICONS', {}).items():
            render_icon(builder, os.path.join(OUT_UI, 'icon_%s_%s.png' % (kind, sid)))

def cmd_puppet(ids):
    for pid in ids or state_ids():
        render_puppet(load(pid).PUPPET if pid in state_ids() else load('journey').JOURNEY[pid], pid)

def cmd_state(ids):
    for sid in ids:
        sid, _, only = sid.partition(':')
        m = load(sid)
        if not only or only == 'puppet':
            render_puppet(m.PUPPET, sid)
        for beat, fn in m.BEATS.items():
            if not only or only == beat:
                render_wide(fn, os.path.join(OUT, 'wayang_%s_%s.png' % (sid, beat)))

def cmd_journey(ids):
    J = load('journey').JOURNEY
    for jid in ids or list(J):
        job = J[jid]
        if isinstance(job, dict):                       # a puppet spec
            render_puppet(job, jid)
        else:
            render_wide(job, os.path.join(OUT, 'wayang_%s.png' % jid), getattr(job, 'size', WIDE))

def check_module(name):
    """Build (no render) everything a module defines: catches NameErrors, bad
    rig keys and empty compositions in seconds, before a long render."""
    m = load(name)
    jobs = dict(getattr(m, 'BEATS', {}))
    jobs.update(getattr(m, 'JOURNEY', {}))
    if hasattr(m, 'PUPPET'):
        jobs['puppet'] = m.PUPPET
    assert jobs, '%s defines no PUPPET, BEATS or JOURNEY' % name
    for key, job in jobs.items():
        if isinstance(job, dict):
            assert W.figure(job), '%s:%s puppet has no parts' % (name, key)
        else:
            cv = W.Canvas(*getattr(job, 'size', WIDE))
            job(cv)
            assert cv.parts, '%s:%s drew nothing' % (name, key)
    icons = getattr(m, 'ICONS', {})
    for kind, builder in icons.items():
        _icon_scene()
        cam, target = builder()
        assert len(bpy.context.scene.objects) > 3, '%s icon %s built no objects' % (name, kind)
    print('CHECK %s OK: %s' % (name, ', '.join(list(jobs) + ['icon_' + k for k in icons])))

def cmd_selftest(ids):
    """Smallest check of the pipeline: lace cut inside the part, carve open,
    outside empty, and the indexed PNG decodes as black RGBA. Then builds every
    listed module (default: every state and journey) without rendering it."""
    np = W.np
    cv = W.Canvas(256, 128, 2.56)
    cv.add([ellipse(1.28, 0.64, 1.0, 0.5)], 'lace')
    cv.carve([ellipse(1.28, 0.64, 0.1)])
    a = cv.render()
    inside = a[40:88, 60:200]
    assert a[0, 0] == 0 and a[64, 128] < 0.05, 'outside or carve not empty'
    assert (inside > 0.95).mean() > 0.5 and (inside < 0.5).mean() > 0.02, 'no lace holes cut'
    path = os.path.join(W.TMP, 'selftest.png')
    W.save_alpha_png(a, path)
    img = bpy.data.images.load(path, check_existing=False)
    px = np.empty(256 * 128 * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(128, 256, 4)
    assert px[..., :3].max() == 0 and px[..., 3].max() > 0.99, 'png is not black-on-alpha'
    hit, sq = set(), [(-0.05, 0.9), (0.05, 0.9), (0.0, 1.0)]     # rig registry hooks reach figure()
    W.register(W.HATS, '_selftest', lambda: hit.add('hat') or ([sq], 'edge', []))
    W.register(W.LOWERS, '_selftest', lambda body: hit.add('lower') or sq)
    W.register(W.COSTUMES, '_selftest', dict(W.COSTUMES['baju'], lower='_selftest', long=True,
                                             extra=lambda sp: hit.add('extra') or [([sq], 'solid', [])]))
    W.figure(dict(costume='_selftest', hat='_selftest'))
    assert hit == {'hat', 'lower', 'extra'}, 'registered rig parts not used: %s' % hit
    try:
        W.register(W.POSES, 'stand', {})
        raise AssertionError('register() replaced an existing part')
    except KeyError:
        pass
    for name in ids or state_ids() + ['journey']:
        check_module(name)
    print('SELFTEST OK')

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if not argv:
        print(__doc__ or 'usage: -- state|journey|icons|puppet|selftest [ids]')
        return
    cmd, ids = argv[0], argv[1:]
    if cmd == 'state':
        cmd_state(ids or state_ids())
    elif cmd == 'icons':
        cmd_icons(ids)
    elif cmd == 'journey':
        cmd_journey(ids)
    elif cmd == 'puppet':
        cmd_puppet(ids)
    elif cmd == 'selftest':
        cmd_selftest(ids)
    else:
        print('unknown command', cmd)

if __name__ == '__main__':
    main()
