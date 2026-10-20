"""Kelantan: Cik Zainab's country -- a great wau bulan climbing the wind, the
carver and the mat weaver at work while two dikir barat groups answer each
other, a plate of blue nasi kerabu, and the wau maker herself."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props
# =====================================================================

def wau_outline(w=1.0):
    """The wau bulan as polygons in units of its wingspan w, centred on the
    waist: a small pointed head, deep broad wings swept out to drooping tips,
    a short narrow waist, and the crescent-moon tail hung right under it with
    its horns swept up toward the wings."""
    R = [(0.0, 0.76), (0.022, 0.74), (0.04, 0.7), (0.046, 0.645), (0.04, 0.6),
         (0.12, 0.615), (0.22, 0.635), (0.32, 0.63), (0.42, 0.6), (0.49, 0.545), (0.545, 0.46),
         (0.51, 0.42), (0.44, 0.37), (0.35, 0.3), (0.25, 0.24), (0.16, 0.2), (0.1, 0.16), (0.07, 0.1),
         (0.05, 0.05)]
    wings = _open(R[:5], 3) + _open(R[4:12], 4)[1:] + _open(R[11:], 4)[1:]
    wings = wings + [(-x, y) for x, y in reversed(wings[1:])]
    waist = mirror_pts(_open([(-0.06, 0.12), (-0.045, 0.04), (-0.04, -0.03), (-0.06, -0.13)], 4))
    moon = arc_pts(0.0, -0.05, 0.27, 155, 385, 40) + arc_pts(0.0, 0.165, 0.265, -22.4, -157.6, 30)[1:-1]
    return [xf(p, s=w) for p in (wings, waist, moon)]

def wau_bow(w=1.0):
    """The humming busur: a long flat bow behind the head, wider than the
    wings, and its string."""
    a = arc_pts(0.0, 0.62 * w, 0.62 * w, 172, 8, 24, ry=0.1 * w)
    return [ribbon(a, 0.011 * w, 0.011 * w), ribbon([a[0], a[-1]], 0.004 * w)]

def wau(cv, cx, cy, w, rot=20.0, layer='mid', bow=True, tassels=True, cls='flower', line=None):
    """Wau bulan, face on and tilted back into the wind: floral cut wings, the
    crescent tail, the humming bow (busur) on its neck, and tassels streaming
    downwind (to -x). `line`: (x, y) to run the flying string to."""
    P = lambda pts: xf(pts, cx, cy, rot=rot)
    pid = cv.add([P(p) for p in wau_outline(w)], cls, layer)
    extra = wau_bow(w) if bow else []
    if tassels:
        for (tx, ty, L) in ((-0.545, 0.46, 1.0), (0.545, 0.46, 0.9), (-0.245, 0.064, 0.6), (0.245, 0.064, 0.5)):
            pts = [(tx, ty), (tx - 0.05 * L, ty - 0.12 * L), (tx - 0.13 * L, ty - 0.22 * L), (tx - 0.11 * L, ty - 0.33 * L)]
            extra.append(ribbon(_open([(x * w, y * w) for x, y in pts]), 0.009 * w, 0.004 * w))
            extra.append(leaf(pts[-1][0] * w, pts[-1][1] * w, -100, 0.07 * w, 0.016 * w))
    cv.add([P(p) for p in extra], 'solid', layer, pid=pid)
    bridle = P([(0.0, 0.3 * w)])[0]                     # where the flying string ties on
    if line:
        lx, ly = line
        sag = 0.12 * math.dist(bridle, line)
        path = [(bridle[0] + (lx - bridle[0]) * t, bridle[1] + (ly - bridle[1]) * t - sag * math.sin(math.pi * t))
                for t in (i / 24 for i in range(25))]
        cv.add([ribbon(path, 0.004 + 0.003 * w, 0.006 + 0.003 * w)], 'solid', layer)
    if layer != 'back':
        cuts = []
        for sx in (-1, 1):                              # an awan larat spiral and a budding vine in each wing
            cuts.append(xf(ribbon(spiral(0.36 * w, 0.49 * w, 0.06 * w, 1.3, a0=200, cw=True), 0.0065 * w), flip=sx < 0))
            vine = _open([(0.07 * w, 0.3 * w), (0.15 * w, 0.38 * w), (0.26 * w, 0.42 * w), (0.38 * w, 0.43 * w), (0.48 * w, 0.46 * w)])
            cuts.append(xf(ribbon(vine, 0.006 * w, 0.003 * w), flip=sx < 0))
            for (lx, ly, la) in ((0.14 * w, 0.37 * w, 150), (0.22 * w, 0.41 * w, -40), (0.3 * w, 0.43 * w, 140),
                                 (0.42 * w, 0.44 * w, -30)):
                cuts.append(xf(leaf(lx, ly, la, 0.07 * w, 0.014 * w), flip=sx < 0))
        cuts.append(ellipse(0, 0.665 * w, 0.018 * w, 0.035 * w))
        cuts.append(ribbon(arc_pts(0.0, 0.0, 0.21 * w, 203, 337, 24), 0.005 * w))
        cuts.append(ribbon([(0, 0.2 * w), (0, -0.02 * w)], 0.006 * w))
        cv.carve([P(c) for c in cuts], layer)
    return bridle

def wind_streak(cv, x, y, L, layer='back', seed=1):
    """A gust: a long thin awan larat line ending in a curl, blowing to -x."""
    rnd = random.Random(seed)
    path = [(x - L * t, y + 0.12 * math.sin(t * 5 + seed)) for t in (i / 12 for i in range(13))]
    cv.add([scroll(path[-1][0] - 0.12, path[-1][1] + 0.12, 0.14, 0.03, 1.1, a0=270, cw=False, tail=path[:-1], wt=0.012)],
           'solid', layer)

def carved_panel(cv, x, y, w, h, layer='mid', seed=1):
    """A carver's panel (ukiran): a frame of timber pierced with awan larat
    scrolls and a flower at the centre, standing on two feet."""
    rnd = random.Random(seed)
    pid = cv.add([rect(x - w / 2, y + 0.12, x + w / 2, y + h)], 'edge', layer)
    cv.add([rect(x - w / 2 + 0.05, y, x - w / 2 + 0.2, y + 0.15), rect(x + w / 2 - 0.2, y, x + w / 2 - 0.05, y + 0.15)],
           'solid', layer, pid=pid)
    cx, cy = x, y + 0.12 + (h - 0.12) / 2
    cuts = [W.circle(cx, cy, 0.09 * w, 16)[0]]
    for k in range(8):
        a = 45 * k + 22
        cuts.append(leaf(cx + 0.1 * w * math.cos(math.radians(a)), cy + 0.1 * w * math.sin(math.radians(a)), a, 0.16 * w, 0.035 * w))
    for sx in (-1, 1):
        for sy in (-1, 1):
            ox, oy = cx + sx * 0.27 * w, cy + sy * (h - 0.12) * 0.25
            cuts.append(ribbon(spiral(ox, oy, 0.13 * w, 1.4, a0=90 + 90 * sx, cw=sx * sy > 0), 0.014 * w, 0.004 * w))
            cuts.append(leaf(ox - sx * 0.05 * w, oy - sy * 0.12 * w, -90 * sy + sx * 20, 0.16 * w, 0.03 * w, bend=0.02 * sx))
    cuts.append(ribbon(rect(x - w / 2 + 0.1, y + 0.22, x + w / 2 - 0.1, y + h - 0.1) + [(x - w / 2 + 0.1, y + 0.22)], 0.012))
    cv.carve(cuts, layer)

def mat_weaving(cv, x, y, s=1.0, layer='mid'):
    """A mengkuang mat half woven: the finished part spread toward the viewer
    (diagonal plait), loose strips fanning from the working edge."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P([(0.5, 0.0), (2.2, 0.0), (1.95, 0.5), (0.72, 0.5)])], 'grid', layer)
    strips = []
    for k in range(9):                                  # loose ends rising from the working edge to her hands
        t = k / 8
        bx, by = 0.5 + 0.22 * t, 0.5 * t
        strips.append(P(ribbon(_open([(bx, by), (bx - 0.18, by + 0.22 + 0.04 * k), (bx - 0.2 - 0.03 * k, by + 0.45 + 0.03 * k)]),
                               0.016, 0.01)))
    cv.add(strips, 'solid', layer)
    cv.add([P(ellipse(2.05, 0.14, 0.14, 0.14))], 'edge', layer)        # a rolled bundle of dried strips

def gong_frame(cv, x, y, s=1.0, layer='mid'):
    """Tetawak: a big bossed gong hung in a carved frame, its beater leaning on it."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P(rect(-0.95, 0.0, -0.8, 2.6)), P(rect(0.8, 0.0, 0.95, 2.6)), P(rect(-1.15, 2.5, 1.15, 2.68)),
            P([(-1.15, 2.68), (-1.35, 2.95), (-1.0, 2.68)]), P([(1.15, 2.68), (1.35, 2.95), (1.0, 2.68)]),
            P(ribbon([(-0.25, 2.5), (-0.12, 1.95)], 0.012)), P(ribbon([(0.25, 2.5), (0.12, 1.95)], 0.012)),
            P(ribbon([(0.5, 0.0), (0.2, 0.95)], 0.025)), P(ellipse(0.17, 1.05, 0.1, 0.12))], 'edge', layer)
    cv.add([P(ellipse(0.0, 1.35, 0.62, n=48))], 'lace', layer)
    cv.carve([P(ribbon(arc_pts(0.0, 1.35, 0.5, 0, 360, 48), 0.012)), P(ribbon(arc_pts(0.0, 1.35, 0.2, 0, 360, 24), 0.012))],
             layer)
    cv.add([P(ellipse(0.0, 1.35, 0.14, n=24))], 'solid', layer)

def rebana(cv, x, y, s=1.0, layer='mid'):
    """Rebana ubi: the great dikir drum on its side, laced with rattan pegs."""
    P = lambda pts: xf(pts, x, y, s=s)
    body = [(-0.55, 0.0), (0.45, 0.0), (0.62, 0.35), (0.65, 0.8), (0.55, 1.1), (-0.5, 1.1), (-0.6, 0.6)]
    cv.add([P(body)], 'scales', layer)
    cv.add([P(ellipse(0.62, 0.58, 0.14, 0.55))], 'edge', layer)
    cv.carve([P(ribbon([(-0.45 + 0.13 * k, 1.05), (-0.5 + 0.13 * k, 0.05)], 0.008)) for k in range(7)], layer)

def telang(cv, x, y, h, lean=0.0, seed=1, layer='mid', flip=False):
    """Bunga telang vine climbing a stake: wavy stem, trefoil leaves and the
    butterfly-pea flowers whose petals turn the rice blue."""
    rnd = random.Random(seed)
    P = lambda pts: xf(pts, x, y, flip=flip)
    stake = ribbon([(0.0, 0.0), (0.05, h * 1.02)], 0.03, 0.02)
    stem = [(0.12 * math.sin(t * 9 + seed) + lean * t * h, h * t) for t in (i / 30 for i in range(31))]
    parts, flowers = [stake, ribbon(stem, 0.016, 0.008)], []
    for i in range(3, 30, 3):
        px, py = stem[i]
        sg = 1 if (i // 3) % 2 else -1
        for k in (-1, 0, 1):
            parts.append(leaf(px, py, 90 - sg * 55 + k * 32, 0.32 + 0.08 * (k == 0), 0.07))
        if i % 6 == 3:                                  # a flower: a broad standard petal over a little keel
            fx, fy = px - sg * 0.32, py + 0.08
            petal = arc_pts(0.0, 0.17, 0.17, -60, 75, 14) + [(0.0, 0.3)] + arc_pts(0.0, 0.17, 0.17, 105, 240, 14)
            flowers.append([xf(petal, fx, fy, rot=sg * 25), xf(leaf(0, 0.0, 90, 0.12, 0.05), fx, fy, rot=sg * 25),
                            ribbon([(fx, fy), (px, py)], 0.012)])
    cv.add([P(p) for p in parts], 'solid', layer)
    for fl in flowers:
        cv.add([P(p) for p in fl], 'edge', layer)
        c = fl[0]
        cx, cy = sum(q[0] for q in c) / len(c), sum(q[1] for q in c) / len(c)
        cv.carve([P(leaf(cx, cy - 0.08, 90, 0.17, 0.035))], layer)

def carved_table(cv, cx, y, w, h, layer='mid'):
    """A low Kelantan table: a plank top over an apron pierced with awan larat
    scrolls, on four short turned legs (two seen)."""
    P = lambda pts: xf(pts, cx, y)
    legs = [_open([(sx * 0.44 * w - 0.07, h - 0.3), (sx * 0.44 * w - 0.09, h * 0.4), (sx * 0.44 * w - 0.05, h * 0.15),
                   (sx * 0.44 * w - 0.07, 0.0)], 3) + _open([(sx * 0.44 * w + 0.07, 0.0), (sx * 0.44 * w + 0.05, h * 0.15),
                                                             (sx * 0.44 * w + 0.09, h * 0.4), (sx * 0.44 * w + 0.07, h - 0.3)], 3)
            for sx in (-1, 1)]
    cv.add([P([(-0.52 * w, h - 0.1), (0.52 * w, h - 0.1), (0.5 * w, h), (-0.5 * w, h)]), P(rect(-0.47 * w, h - 0.42, 0.47 * w, h - 0.1))] +
           [P(l) for l in legs], 'edge', layer)
    cuts = []
    for k in range(-2, 3):
        cuts.append(P(ribbon(spiral(k * 0.17 * w, h - 0.26, 0.1, 1.2, a0=90, cw=k % 2 == 0), 0.016, 0.004)))
    cv.carve(cuts, layer)

def nasi_plate(cv, cx, y, w, layer='mid'):
    """Nasi kerabu on a wide plate: the dome of blue rice crowned with telang
    flowers, shredded ulam heaped beside it, a fried fish in front, half a
    salted egg, and a big fish cracker standing behind."""
    plate(cv, cx, y, w * 1.3, layer)
    base = y + 0.1 * w
    kp = cv.add([xf([(0.2 * w * math.cos(math.radians(a)) * (1 + 0.06 * (k % 2)),
                      0.2 * w * math.sin(math.radians(a)) * (1 + 0.06 * (k % 2))) for k, a in enumerate(range(0, 360, 12))],
                    cx + 0.36 * w, base + 0.32 * w)], 'dots', layer)   # keropok: a crinkled disc behind
    cv.add([[(cx - 0.3 * w, base)] + arc_pts(cx, base, 0.3 * w, 180, 0, 30, ry=0.3 * w)[1:-1] + [(cx + 0.3 * w, base)]],
           'flower', layer)                                             # the blue rice
    fx, fy = cx - 0.02 * w, base + 0.29 * w                             # a telang sprig on top
    petal = arc_pts(0.0, 0.17, 0.17, -60, 75, 14) + [(0.0, 0.3)] + arc_pts(0.0, 0.17, 0.17, 105, 240, 14)
    cv.add([ribbon(_open([(fx, fy), (fx + 0.02 * w, fy + 0.06 * w), (fx + 0.07 * w, fy + 0.1 * w)]), 0.005 * w),
            leaf(fx + 0.01 * w, fy + 0.03 * w, 150, 0.1 * w, 0.022 * w), leaf(fx + 0.02 * w, fy + 0.05 * w, 30, 0.09 * w, 0.02 * w),
            xf(petal, fx + 0.07 * w, fy + 0.08 * w, s=0.32 * w, rot=-30), xf(petal, fx - 0.04 * w, fy + 0.07 * w, s=0.26 * w, rot=35)],
           'edge', layer)
    herbs = []
    for k in range(14):                                 # shredded ulam heaped left of the rice
        a = 25 + 130 * k / 13
        herbs.append(leaf(cx - 0.42 * w, base, a, 0.2 * w * (0.8 + 0.25 * (k % 3) / 2), 0.016 * w, bend=0.01 * w))
    cv.add(herbs, 'solid', layer)
    cv.add([[(cx + 0.3 * w, base)] + arc_pts(cx + 0.44 * w, base, 0.14 * w, 180, 0, 16, ry=0.13 * w)[1:-1] +
            [(cx + 0.58 * w, base)]], 'edge', layer)                    # salted egg half
    cv.carve([arc_pts(cx + 0.44 * w, base + 0.01, 0.07 * w, 180, 0, 12, ry=0.065 * w)], layer)
    fish(cv, cx - 0.2 * w, base + 0.06 * w, 0.42 * w, ang=4)

# =====================================================================
# rig parts (registered once, keys prefixed with the state id)
# =====================================================================

def _it_wau(g, ang, fig):
    """A miniature wau bulan held up on its spine."""
    w, ox, oy = 0.32, g[0] + 0.01, g[1] + 0.12
    polys = [xf(p, ox, oy) for p in wau_outline(w) + wau_bow(w)]
    polys.append(ribbon([(ox, g[1] + 0.04), (ox, g[1] - 0.03)], 0.006))
    cuts = [xf(ribbon(spiral(0.37 * w, 0.5 * w, 0.065 * w, 1.2, a0=200, cw=True), 0.014 * w, 0.006 * w), ox, oy, flip=sx < 0)
            for sx in (-1, 1)]
    cuts.append(xf(ribbon(arc_pts(0.0, 0.0, 0.21 * w, 203, 337, 16), 0.014 * w), ox, oy))
    return polys, 'lace', cuts

def _it_reel(g, ang, fig):
    """Gelendong: the string reel, a spool between two handles."""
    x, y = g
    return [rect(x - 0.012, y - 0.07, x + 0.012, y + 0.07), ellipse(x, y + 0.075, 0.045, 0.012), ellipse(x, y - 0.075, 0.045, 0.012),
            rect(x - 0.03, y - 0.065, x + 0.03, y + 0.065)], 'edge', [ribbon([(x - 0.03, y - 0.04 + 0.02 * k), (x + 0.03, y - 0.03 + 0.02 * k)], 0.002)
                                                                   for k in range(4)]

def _it_mallet(g, ang, fig):
    """Pemukul: the carver's wooden mallet."""
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.12 * d[0], g[1] + 0.12 * d[1])
    head = xf(rect(-0.03, -0.045, 0.03, 0.045), end[0], end[1], rot=ang)
    return [ribbon([(g[0] - 0.03 * d[0], g[1] - 0.03 * d[1]), end], 0.006), head], 'solid', []

def _it_chisel(g, ang, fig):
    """Pahat: a chisel held to the panel."""
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.13 * d[0], g[1] + 0.13 * d[1])
    return [ribbon([(g[0] - 0.035 * d[0], g[1] - 0.035 * d[1]), (g[0] + 0.05 * d[0], g[1] + 0.05 * d[1])], 0.009),
            ribbon([(g[0] + 0.05 * d[0], g[1] + 0.05 * d[1]), end], 0.004, 0.0015)], 'solid', []

def _it_line(g, ang, fig):
    """The kite string paid out from a stick held in both hands."""
    return [ribbon([(g[0] - 0.03, g[1] - 0.03), (g[0] + 0.03, g[1] + 0.03)], 0.008)], 'solid', []

def _selendang(spec):
    """A songket shoulder cloth falling over the back."""
    return [([ribbon(_open([(-0.06, 0.78), (-0.09, 0.7), (-0.1, 0.58), (-0.095, 0.45)]), 0.018, 0.026)], 'flower', [])]

W.register(W.LEGS, 'kelantan_kneel', ((0.17, 0.065), (-0.1, 0.045), (0.14, 0.065), (-0.12, 0.05), 0.3))
W.register(W.POSES, 'kelantan_clap', {'f': (118, 38), 'b': (104, 58), 'lean': 3, 'legs': 'kelantan_kneel', 'hf': 'open', 'hb': 'open'})
W.register(W.POSES, 'kelantan_sway', {'f': (96, 70), 'b': (130, 30), 'lean': -4, 'legs': 'kelantan_kneel', 'hf': 'open', 'hb': 'open'})
W.register(W.POSES, 'kelantan_carve', {'f': (72, 24), 'b': (95, 110), 'lean': 6, 'legs': 'kelantan_kneel', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'kelantan_plait', {'f': (40, 30), 'b': (30, 40), 'lean': 26, 'legs': 'kelantan_kneel', 'hf': 'open', 'hb': 'open'})
W.register(W.POSES, 'kelantan_fly', {'f': (70, 50), 'b': (52, 60), 'lean': -10, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'kelantan_point', {'f': (128, 10), 'b': (-20, -10), 'lean': -4, 'legs': 'walk', 'hf': 'open', 'hb': 'open'})
W.register(W.POSES, 'kelantan_zainab', {'f': (70, 62), 'b': (18, 52), 'lean': 0, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})
W.register(W.ITEMS2, 'kelantan_wau', _it_wau)
W.register(W.ITEMS2, 'kelantan_reel', _it_reel)
W.register(W.ITEMS2, 'kelantan_mallet', _it_mallet)
W.register(W.ITEMS2, 'kelantan_chisel', _it_chisel)
W.register(W.ITEMS2, 'kelantan_line', _it_line)
W.register(W.COSTUMES, 'kelantan_kurung', dict(W.COSTUMES['kurung'], extra=_selendang))
W.register(W.COSTUMES, 'kelantan_kurung_kneel', dict(W.COSTUMES['kurung'], legs='trousers'))

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def kelantan_land(cv):
    """A great wau bulan climbs the wind over the harvested fields; on the
    ground the flyer pays out the line while a boy points up at it."""
    hills(cv, -0.5, 21, G + 0.5, 0.8, seed=13)
    rumah(cv, 10.6, G + 0.6, 0.55, layer='back')
    for i, x in enumerate((8.4, 13.2, 14.4)):
        palm(cv, x, G + 0.6, 2.4 + 0.4 * (i % 2), lean=-0.2, seed=50 + i, layer='back')
    wau(cv, 16.6, 6.2, 1.1, rot=18, layer='back', bow=False, tassels=False, line=(20.6, 3.0))
    for i, (x, y, L) in enumerate(((15.5, 7.4, 3.2), (19.8, 5.1, 3.6), (9.2, 4.2, 2.6), (12.4, 7.0, 2.2), (6.6, 2.9, 2.4))):
        wind_streak(cv, x, y, L, seed=i)
    cloud(cv, 2.2, 7.4, 0.6, 'back', flip=True, seed=3)
    # the great wau on the left third, its line sagging down to the flyer
    wau(cv, 4.7, 4.55, 3.9, rot=20, line=(13.05, G + 1.72))
    W.place_figure(cv, dict(head='refined', hat='tengkolok', costume='baju', pose='kelantan_fly', item_f='kelantan_line',
                            rod_to=-0.25), 13.9, G, 2.9, flip=True)
    W.place_figure(cv, dict(head='young', hat='songkok', costume='baju', pose='kelantan_point', rod_to=-0.25, scale=0.85),
                   15.6, G, 2.9, flip=True)
    palm(cv, 18.6, G + 0.05, 5.2, lean=-0.22, seed=57)
    grass(cv, -0.2, 20.7, G + 0.02, 0.55, seed=12, layer='mid', lean=22)
    ground(cv, 'earth', seed=7)
    frame_edges(cv, seed=8, left='none', right='none')

def kelantan_people(cv):
    """Village crafts and song: a carver chisels a pierced panel, a woman
    plaits a mengkuang mat, and two dikir barat groups clap and sing at each
    other across the gong."""
    rumah(cv, 4.0, G + 0.3, 0.75, layer='back')
    wau(cv, 15.6, 5.6, 1.7, rot=18, layer='back', bow=False, tassels=False, line=(20.6, 3.4))
    palm(cv, 19.0, G + 0.6, 3.6, lean=-0.1, seed=61, layer='back')
    cloud(cv, 11.2, 7.2, 0.6, 'back', flip=True, seed=7)
    # crafts on the left
    carved_panel(cv, 2.85, G, 1.7, 2.5)
    W.place_figure(cv, dict(head='old', beard='tuft', hat='songkok', costume='baju', pose='kelantan_carve',
                            item_f='kelantan_chisel', item_b='kelantan_mallet', rod_to=-0.25), 1.3, G, 3.2)
    mat_weaving(cv, 4.75, G + 0.02, 1.0)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kelantan_kurung_kneel', pose='kelantan_plait',
                            rod_to=-0.25), 4.6, G, 3.3)
    # dikir barat: two groups face each other across the gong
    for i, (x, pose, sc) in enumerate(((8.0, 'kelantan_clap', 3.0), (9.05, 'kelantan_sway', 3.1), (10.1, 'kelantan_clap', 3.2))):
        W.place_figure(cv, dict(head=('refined', 'young', 'refined')[i], hat='tengkolok' if i == 2 else 'songkok',
                                costume='baju', pose=pose, rod_to=-0.25), x, G, sc)
    gong_frame(cv, 12.85, G, 1.0)
    rebana(cv, 12.85, G + 0.02, 0.6)
    for i, (x, pose, sc) in enumerate(((15.6, 'kelantan_clap', 3.2), (16.65, 'kelantan_sway', 3.1), (17.7, 'kelantan_clap', 3.0))):
        W.place_figure(cv, dict(head=('refined', 'young', 'old')[i], hat='tengkolok' if i == 0 else 'songkok',
                                costume='baju', pose=pose, rod_to=-0.25), x, G, sc, flip=True)
    ground(cv, 'earth', seed=17)
    frame_edges(cv, seed=18, left='none', right='none')

def kelantan_food(cv):
    """A plate of blue nasi kerabu set on a carved low table, budu and salted
    eggs on either side, the bunga telang that colours the rice climbing its stake."""
    cv.add_eo([rect(13.6, 2.4, 17.4, 6.4), rect(13.85, 2.65, 17.15, 6.15)], 'edge', 'back')
    cv.add([ribbon([(13.85 + 0.55 * i, 2.65), (13.85 + 0.55 * i, 6.15)], 0.03) for i in range(1, 6)], 'solid', 'back')
    wau(cv, 4.2, 5.4, 1.9, rot=-18, layer='back', bow=False, tassels=False, line=(-0.2, 3.0))
    for x in (6.6, 7.4, 13.0):
        cv.add([ribbon([(x, 8.3), (x, 7.4)], 0.02)] + [leaf(x, 7.45, -90 + k * 12, 0.7, 0.07) for k in (-1, 0, 1)], 'solid', 'back')
    carved_table(cv, 10.6, G + 0.02, 3.6, 1.0)
    nasi_plate(cv, 10.6, G + 1.02, 2.3)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kelantan_kurung', pose='serve', item_f='bowl',
                            rod_to=-0.25), 7.55, G, 3.5)
    jar(cv, 5.9, G, 0.6, cls='edge')                                    # budu
    for k in range(3):                                                  # salted eggs on a saucer
        cv.add([ellipse(13.0 + 0.3 * k, G + 0.22 + 0.06 * (k == 1), 0.15, 0.2)], 'edge')
    plate(cv, 13.3, G + 0.02, 1.2)
    for sx in (-1, 1):
        fish(cv, 10.6 + sx * 5.6, G + 0.32, 1.1, flip=sx > 0, ang=8)
    serai(cv, 18.0, G, 1.8)
    kantan(cv, 18.7, G + 0.3, 1.9, lean=0.05)
    telang(cv, 1.6, G, 5.6, lean=0.02, seed=4)
    telang(cv, 19.6, G, 4.8, lean=-0.02, seed=5, flip=True)
    ground(cv, 'earth', seed=27)
    frame_edges(cv, seed=28, left='none', right='none')

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def _flat(name, polys, z, mat, depth=0.02):
    """Polygons (x, y) filled into a thin extruded slab at height z."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'
    cu.extrude = depth
    for p in polys:
        sp = cu.splines.new('POLY')
        sp.points.add(len(p) - 1)
        for i, (x, y) in enumerate(p):
            sp.points[i].co = (x, y, 0, 1)
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(mat)
    ob.location.z = z
    return ob

def _pivot(rot, loc, scale=1.0):
    pv = bpy.data.objects.new('Pivot', None)
    bpy.context.scene.collection.objects.link(pv)
    for ob in list(bpy.context.scene.objects):
        if ob.type in ('MESH', 'CURVE') and ob.parent is None:
            ob.parent = pv
    pv.rotation_euler, pv.location, pv.scale = rot, loc, (scale,) * 3
    return pv

def icon_item_wau():
    """A miniature wau bulan: red paper body, a yellow and blue cut-paper inlay,
    bamboo spine and bow, and red tassels."""
    red = _mat('Red', (0.72, 0.06, 0.06), 0.6)
    yellow = _mat('Yellow', (0.95, 0.72, 0.12), 0.6)
    blue = _mat('Blue', (0.08, 0.22, 0.6), 0.6)
    white = _mat('Paper', (0.95, 0.92, 0.84), 0.7)
    bamboo = _mat('Bamboo', (0.78, 0.62, 0.36), 0.6)
    w = 2.0
    outl = wau_outline(w)
    _flat('Body', outl, 0.0, red)
    _flat('Inlay', [xf(outl[0], s=0.8, oy=0.42 * w), xf(outl[2], s=0.78, oy=-0.2 * w)], 0.021, yellow)
    _flat('WaistInlay', [rect(-0.032 * w, -0.16 * w, 0.032 * w, 0.3 * w)], 0.021, yellow)
    _flat('Inlay2', [xf(outl[0], s=0.58, oy=0.42 * w), xf(outl[2], s=0.56, oy=-0.2 * w)], 0.042, blue)
    for sx in (-1, 1):
        _flat('Flower%d' % sx, [ellipse(sx * 0.27 * w, 0.44 * w, 0.05 * w)] +
              [leaf(sx * 0.27 * w, 0.44 * w, a, 0.11 * w, 0.03 * w) for a in range(0, 360, 60)], 0.063, white)
    _flat('Bud', [ellipse(0, 0.665 * w, 0.025 * w, 0.045 * w)], 0.063, white)
    _tube('Spine', [(0, 0.76 * w, 0.08), (0, -0.32 * w, 0.08)], 0.018, bamboo)
    _tube('Spar', [(-0.53 * w, 0.48 * w, 0.08), (0, 0.6 * w, 0.1), (0.53 * w, 0.48 * w, 0.08)], 0.014, bamboo)
    _tube('Moonspar', [(0.27 * w * math.cos(math.radians(a)), -0.05 * w + 0.27 * w * math.sin(math.radians(a)), 0.08)
                       for a in range(160, 381, 20)], 0.012, bamboo)
    _tube('Bow', [(0.62 * w * math.cos(math.radians(a)), 0.62 * w + 0.1 * w * math.sin(math.radians(a)), 0.1)
                  for a in range(172, 7, -12)], 0.012, bamboo)
    for sx, (tx, ty) in ((sx, p) for sx in (-1, 1) for p in ((0.545, 0.46), (0.245, 0.064))):
        _tube('Tassel%d_%d' % (sx, ty * 100), [(sx * tx * w, ty * w, 0.0), (sx * (tx + 0.03) * w, (ty - 0.1) * w, -0.04),
                                               (sx * (tx + 0.01) * w, (ty - 0.24) * w, 0.0)], 0.02, red)
    _pivot((math.radians(62), 0, math.radians(14)), (0, 0, 0.42), 0.78)
    return (0, -4.8, 2.0), (0, 0, 0.7)

def icon_food_kerabu():
    """Nasi kerabu: a dome of butterfly-pea blue rice, shredded ulam, salted
    egg, a fried fish, a fish cracker and sambal on a banana leaf."""
    rnd = random.Random(7)
    leafm = _mat('Leaf', (0.12, 0.38, 0.1), 0.45)
    _flat('BananaLeaf', [ellipse(0, 0, 1.58, 1.15, n=48)], 0.0, leafm, 0.01)
    rice = _mat('BlueRice', (0.22, 0.38, 0.8), 0.7)
    dome = _lathe('Rice', [(0.0, 0.0), (0.62, 0.0), (0.6, 0.18), (0.48, 0.38), (0.28, 0.52), (0.0, 0.57)], rice, 48)
    dome.location = (-0.3, 0.15, 0.02)
    grain = _mat('Grain', (0.55, 0.65, 0.95), 0.6)
    for k in range(40):
        a, r = rnd.uniform(0, TAU), rnd.uniform(0.0, 0.55)
        z = 0.57 * (1 - (r / 0.62) ** 2) ** 0.5 + 0.02
        _blob('G%d' % k, (-0.3 + r * math.cos(a), 0.15 + r * math.sin(a), z), (0.04, 0.018, 0.018), (rnd.uniform(0, 3), 0.4, a), grain, 8)
    herb = _mat('Herb', (0.25, 0.6, 0.15), 0.5)
    dark = _mat('DarkHerb', (0.08, 0.3, 0.06), 0.5)
    for k in range(26):
        x, y = 0.55 + rnd.uniform(-0.3, 0.3), 0.35 + rnd.uniform(-0.25, 0.25)
        _box('Herb%d' % k, (x, y, 0.06 + rnd.uniform(0, 0.05)), (0.3, 0.025, 0.012), (0, rnd.uniform(-0.2, 0.2), rnd.uniform(0, 3)),
             herb if k % 3 else dark)
    white = _mat('White', (0.96, 0.95, 0.9), 0.35)
    yolk = _mat('Yolk', (0.95, 0.45, 0.05), 0.4)
    _blob('Egg', (0.65, -0.35, 0.1), (0.28, 0.2, 0.12), (0, 0, 0.4), white)
    _blob('EggYolk', (0.65, -0.35, 0.2), (0.14, 0.11, 0.035), (0, 0, 0.4), yolk)
    fishm = _mat('FriedFish', (0.6, 0.32, 0.1), 0.45)
    f = _blob('Fish', (-0.55, -0.62, 0.1), (0.62, 0.17, 0.1), (0, 0, 0.2), fishm)
    _flat('Tail', [[(-1.12, -0.74), (-1.45, -0.5), (-1.4, -0.98)]], 0.1, fishm, 0.03)
    _blob('FishEye', (0.0, -0.66, 0.17), (0.04, 0.04, 0.03), (0, 0, 0), _mat('Eye', (0.05, 0.04, 0.03), 0.3))
    for k in range(5):
        _box('Score%d' % k, (-0.75 + 0.14 * k, -0.62 + 0.03 * k, 0.19), (0.03, 0.2, 0.02), (0, 0, 0.5), _mat('Score%d' % k, (0.35, 0.16, 0.05), 0.5))
    cracker = _mat('Keropok', (0.93, 0.82, 0.6), 0.6)
    k = _blob('Cracker', (0.95, 0.55, 0.12), (0.42, 0.3, 0.025), (0.3, -0.2, 0.5), cracker)
    sambal = _mat('Sambal', (0.65, 0.1, 0.03), 0.3)
    _blob('Sambal', (0.2, -0.85, 0.06), (0.22, 0.16, 0.07), (0, 0, 0), sambal)
    return (0, -5.4, 4.7), (0, -0.05, 0.12)

# =====================================================================
# registry: what the CLI renders for this state
# =====================================================================

PUPPET = dict(body='female', head='female', hat='tudung', costume='kelantan_kurung', pose='kelantan_zainab',
              item_f='kelantan_wau', item_b='kelantan_reel')                                        # Cik Zainab
BEATS = {'land': kelantan_land, 'people': kelantan_people, 'food': kelantan_food}
ICONS = {'food': icon_food_kerabu, 'item': icon_item_wau}
