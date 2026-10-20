"""Sabah: Guntor's mountain -- Kinabalu's granite crown above the rainforest,
villagers readying packs and rope for the climb, hinava tossed with lime, and
the guide with his staff and charm."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props
# =====================================================================

# Kinabalu's skyline, left to right: the western shoulder, the summit plateau
# with its granite spires (St John's, Low's Peak, the Donkey's Ears, South
# Peak), then the long eastern ridge falling away.
KINABALU = [(-0.4, 1.9), (0.6, 2.6), (1.6, 3.5), (2.4, 4.5), (2.95, 5.25), (3.2, 5.55), (3.32, 5.95), (3.45, 5.78),
            (3.6, 6.3), (3.74, 6.08), (3.92, 6.55), (4.06, 6.28), (4.26, 6.72), (4.42, 6.46), (4.66, 7.02), (4.8, 6.66),
            (4.98, 6.82), (5.08, 6.55), (5.2, 6.88), (5.3, 6.6), (5.4, 6.92), (5.52, 6.55), (5.74, 6.42), (5.96, 6.74),
            (6.1, 6.3), (6.36, 6.05), (6.75, 5.62), (7.4, 5.15), (8.3, 4.58), (9.5, 3.98), (11.0, 3.32), (12.6, 2.72),
            (14.2, 2.25), (15.5, 1.9)]

def _cross(prof, y):
    """x where the skyline first and last crosses height y."""
    xs = []
    for (x0, y0), (x1, y1) in zip(prof, prof[1:]):
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    return xs[0], xs[-1]

def kinabalu(cv, dx=0.0, dy=0.0, s=1.0, layer='mid', cloud_y=None, seed=5):
    """Gunung Kinabalu. In the back layer: the whole massif, faint. In the
    mid layer: only the granite crown above a scalloped bank of cloud at
    cloud_y, gullies streaking its slabs, so the summit floats over the haze."""
    P = lambda pts: xf(pts, dx, dy, s=s)
    if cloud_y is None:
        return cv.add([P(KINABALU + [(KINABALU[-1][0], 0.6), (KINABALU[0][0], 0.6)])], 'edge', layer)
    xl, xr = _cross(KINABALU, cloud_y)
    top = [(xl, cloud_y)] + [p for p in KINABALU if xl < p[0] < xr and p[1] > cloud_y] + [(xr, cloud_y)]
    n = max(3, int((xr - xl) / 0.9))
    foot = []
    for k in range(n, 0, -1):                           # cloud lobes biting up into the rock
        a, b = xl + (xr - xl) * k / n, xl + (xr - xl) * (k - 1) / n
        foot += arc_pts((a + b) / 2, cloud_y, (a - b) / 2, 0, 180, 10, ry=0.24 * math.sin(math.pi * (k - 0.5) / n))[1:-1]
    pid = cv.add([P(top + foot)], 'edge', layer)
    rnd = random.Random(seed)
    cuts = []
    for x0, y0, L in ((3.2, 5.2, 1.0), (3.7, 5.6, 1.2), (4.2, 5.9, 1.1), (4.7, 6.2, 1.5), (5.2, 6.0, 1.3), (5.75, 5.85, 1.3),
                      (6.3, 5.5, 0.9), (2.9, 4.8, 0.5), (7.0, 4.95, 0.5)):
        y1 = max(y0 - L, cloud_y + 0.35)
        if y1 >= y0 - 0.2:
            continue
        path = [(x0 + rnd.uniform(-0.03, 0.03) + 0.08 * math.sin(t * 3 + x0), y0 + (y1 - y0) * t) for t in (i / 6 for i in range(7))]
        cuts.append(ribbon(path, 0.004, wf=lambda t: 0.005 + 0.013 * math.sin(math.pi * t)))
    for k in range(n):                                  # a curl in each cloud lobe
        cx = xl + (xr - xl) * (k + 0.5) / n
        cuts.append(scroll(cx, cloud_y + 0.08, 0.1, 0.03, 1.2, a0=180, cw=k % 2 == 0))
    cv.carve([P(c) for c in cuts], layer)
    return pid

def rainforest(cv, x0, x1, y, h, seed=1, layer='mid', emergent=()):
    """Dipterocarp forest edge: two tiers of overlapping cauliflower crowns,
    an understory of ferns and saplings hiding the trunks, and tall emergents
    whose crowns break above the canopy on long bare boles."""
    rnd = random.Random(seed)
    tall, low, trunks = [], [], []
    for ex, eh in emergent:
        trunks.append(ribbon(_open([(ex, y), (ex + 0.05, y + eh * 0.5), (ex - 0.03, y + eh * 0.9)]), 0.075, 0.045))
        for a in (150, 115, 65, 30):
            e = (ex + 0.45 * math.cos(math.radians(a)), y + eh * 0.86 + 0.28 * math.sin(math.radians(a)))
            trunks.append(ribbon([(ex, y + eh * 0.82), e], 0.03, 0.012))
        tall += canopy(ex, y + eh * 0.98, 0.62, seed + int(ex * 7), 8)
    x = x0
    while x < x1:                                       # upper tier
        hh = h * rnd.uniform(0.78, 1.0)
        r = h * rnd.uniform(0.3, 0.42)
        tall += canopy(x, y + hh, r, seed + int(x * 10), 7)
        trunks.append(ribbon([(x + rnd.uniform(-0.05, 0.05), y), (x, y + hh)], 0.04 * h ** 0.5, 0.025 * h ** 0.5))
        x += r * rnd.uniform(1.0, 1.35)
    x = x0 + 0.4
    while x < x1:                                       # lower tier, offset
        hh = h * rnd.uniform(0.45, 0.6)
        r = h * rnd.uniform(0.24, 0.32)
        low += canopy(x, y + hh, r, seed + 500 + int(x * 10), 6)
        x += r * rnd.uniform(1.3, 1.8)
    under = []
    for i in range(int((x1 - x0) / 0.35)):              # ferns and saplings
        ux = x0 + i * 0.35 + rnd.uniform(-0.1, 0.1)
        for k in range(5):
            under.append(leaf(ux, y, 90 + (k - 2) * 28 + rnd.uniform(-8, 8), h * rnd.uniform(0.18, 0.3), 0.03,
                              bend=0.03 * (k - 2)))
    cv.add(trunks, 'solid', layer)
    cv.add(tall, 'scales', layer)
    cv.add(under, 'solid', layer)
    return cv.add(low, 'scales', layer)

def tree_fern(cv, x, y, h, seed=1, layer='mid', flip=False):
    """Paku gajah (tree fern): a slim shaggy trunk, arching lacy fronds and a
    fiddlehead uncurling at the crown."""
    rnd = random.Random(seed)
    P = lambda pts: xf(pts, x, y, flip=flip)
    top = (0.06 * h, h)
    trunk = _open([(0, 0), (0.05 * h, 0.5 * h), top])
    parts = [ribbon(trunk, 0.035 * h ** 0.5, 0.028 * h ** 0.5)]
    for i in range(9):
        a = math.radians(-15 + 210 * i / 8 + rnd.uniform(-6, 6))
        L = h * rnd.uniform(0.42, 0.55)
        d = (math.cos(a), math.sin(a))
        path = _open([top, (top[0] + d[0] * L * 0.4, top[1] + d[1] * L * 0.4 + 0.08),
                      (top[0] + d[0] * L * 0.8, top[1] + d[1] * L * 0.5 - L * 0.15),
                      (top[0] + d[0] * L, top[1] + d[1] * L * 0.3 - L * 0.42)])
        parts.append(ribbon(path, 0.012 * h ** 0.5, 0.003))
        for k in range(3, len(path) - 1):
            p, q = path[k], path[k + 1]
            ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
            ll = h * 0.06 * (1 - 0.7 * k / len(path))
            parts.append(leaf(p[0], p[1], ang + 75, ll, 0.008 * h ** 0.5))
            parts.append(leaf(p[0], p[1], ang - 75, ll, 0.008 * h ** 0.5))
    parts.append(scroll(top[0] + 0.1 * h ** 0.5, top[1] + 0.22 * h ** 0.5, 0.07 * h ** 0.5, 0.02 * h ** 0.5, 1.4, a0=200,
                        cw=True, tail=[top, (top[0] + 0.02, top[1] + 0.12 * h ** 0.5)]))
    cv.add([P(p) for p in parts], 'solid', layer)
    cv.carve([P(ribbon([(0.05 * h * t - 0.04, h * t), (0.05 * h * t + 0.04, h * t + 0.03)], 0.006)) for t in (0.2, 0.32, 0.44, 0.56, 0.68, 0.8)],
             layer)

def kadazan_house(cv, x, y, s=1.0, layer='mid', flip=False):
    """Bamboo house on stilts, a steep thatched roof and a notched-log ladder."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    cv.add([P(ribbon([(px, 0.0), (px, 1.0)], 0.045)) for px in (-1.0, -0.35, 0.35, 1.0)] + [P(rect(-1.15, 0.95, 1.15, 1.06))],
           'solid', layer)
    cv.add_eo([P(rect(-1.0, 1.06, 1.0, 1.8)), P(rect(-0.2, 1.2, 0.25, 1.62))], 'grid', layer)
    cv.add([P([(-1.4, 1.7), (-0.25, 3.0), (0.25, 3.0), (1.4, 1.7), (1.2, 1.74), (-1.2, 1.74)])], 'scales', layer)
    cv.add([P(ribbon([(-0.4, 2.85), (-0.1, 3.3)], 0.03)), P(ribbon([(0.4, 2.85), (0.1, 3.3)], 0.03)),
            P(ribbon([(1.15, 1.0), (1.45, 0.0)], 0.05))], 'solid', layer)
    cv.carve([P(ribbon([(1.18 + 0.075 * k, 0.86 - 0.25 * k), (1.3 + 0.075 * k, 0.86 - 0.25 * k)], 0.018)) for k in range(4)],
             layer)

def trail_post(cv, x, y, s=1.0, layer='mid'):
    """A trailhead post with an arrow board pointing up the mountain path."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P(rect(-0.07, 0.0, 0.07, 1.9)), P([(-0.6, 1.45), (0.55, 1.45), (0.8, 1.6), (0.55, 1.75), (-0.6, 1.75)]),
            P([(-0.1, 1.9), (0.0, 2.02), (0.1, 1.9)])], 'edge', layer)
    cv.carve([P(rect(-0.45 + 0.17 * k, 1.53, -0.36 + 0.17 * k, 1.67)) for k in range(5)], layer)

def steps(cv, x, y, n=6, w=0.55, rise=0.32, layer='mid'):
    """Timber trail steps climbing to the right, held by stakes."""
    slope = [(x - 0.3, y - 0.05)] + [(x + k * w + 0.05, y + k * rise - 0.04 + 0.05 * math.sin(k * 2.1)) for k in range(n + 1)] +             [(x + n * w + 0.6, y + n * rise), (x + n * w + 0.6, y - 0.05)]
    cv.add([slope], 'scales', layer)
    polys = []
    for k in range(n):
        x0, y0 = x + k * w, y + k * rise
        polys += [rect(x0, y0 + 0.02, x0 + w * 0.9, y0 + 0.13), ribbon([(x0 + 0.08, y0 - 0.2), (x0 + 0.08, y0 + 0.2)], 0.028),
                  ribbon([(x0 + w * 0.85, y0 - 0.2), (x0 + w * 0.85, y0 + 0.18)], 0.028)]
    cv.add(polys, 'edge', layer)

def lime_half(x, y, r, rot=0.0):
    """A cut limau kapas: the outline plus its segment cuts (polys, cuts)."""
    half = [(x - r, y)] + arc_pts(x, y, r, 180, 360, 16)[1:-1] + [(x + r, y)]
    half = xf(half, rot=rot, ox=x, oy=y)
    cuts = [xf(leaf(x, y - 0.12 * r, a, 0.72 * r, 0.12 * r), rot=rot, ox=x, oy=y) for a in (-150, -120, -90, -60, -30)]
    return half, cuts

def hinava_bowl(cv, cx, y, w, layer='mid'):
    """Hinava in a shallow wooden bowl: translucent fish slivers heaped low
    with chilli and shallot rings and ginger shreds, a squeezed lime half
    on the rim. Returns the heap's top y."""
    h = 0.17 * w
    body = _open([(-0.5 * w, h), (-0.47 * w, 0.55 * h), (-0.36 * w, 0.18 * h), (-0.2 * w, 0.0)], 4)
    body = mirror_pts(body + [(-0.2 * w, -0.02 * w)])
    cv.add([xf(body, cx, y)], 'grid', layer)
    mound = _open([(-0.44 * w, h * 0.95), (-0.32 * w, h * 1.3), (-0.14 * w, h * 1.55), (0.0, h * 1.6), (0.16 * w, h * 1.52),
                   (0.33 * w, h * 1.28), (0.44 * w, h * 0.95)], 5)
    polys = [xf(mound, cx, y)]
    rnd = random.Random(3)
    for k in range(13):                                 # fish slivers lying every which way over the heap
        bx = (-0.38 + 0.063 * k) * w
        by = h * (1.0 + 0.55 * (1 - (bx / (0.44 * w)) ** 2))
        a = 90 + (k - 6) * 13 + rnd.uniform(-25, 25)
        polys.append(leaf(cx + bx, y + by - 0.03 * w, a, rnd.uniform(0.13, 0.2) * w, 0.026 * w, bend=rnd.uniform(-0.02, 0.02) * w))
    for k in range(5):                                  # ginger shreds
        polys.append(xf(ribbon([(0, 0), (0.09 * w, 0.0)], 0.006 * w), cx + rnd.uniform(-0.25, 0.2) * w,
                        y + h * rnd.uniform(1.45, 1.65), rot=rnd.uniform(-50, 50)))
    lw, lc = lime_half(cx + 0.47 * w, y + h * 1.0, 0.085 * w, rot=-35)
    polys.append(lw)
    cv.add(polys, 'edge', layer)
    rings = [ribbon(arc_pts(cx + px * w, y + h * py, 0.019 * w, 0, 360, 10), 0.005 * w)      # chilli and shallot rings
             for px, py in ((-0.3, 1.12), (-0.13, 1.5), (0.05, 1.28), (0.2, 1.52), (0.3, 1.15), (-0.02, 1.62))]
    cv.carve(rings + lc + [ribbon(_open([(cx - 0.42 * w, y + 0.65 * h), (cx, y + 0.6 * h), (cx + 0.42 * w, y + 0.65 * h)]),
                                  0.006 * w)], layer)
    return y + h * 1.6

def papan(cv, x0, x1, y, h=0.6, layer='mid'):
    """A thick plank laid across two log stumps: the kitchen work board."""
    stumps = [[(x - 0.28, y), (x + 0.28, y), (x + 0.24, y + h - 0.15), (x - 0.24, y + h - 0.15)] for x in (x0 + 0.6, x1 - 0.6)]
    cv.add([rect(x0, y + h - 0.16, x1, y + h)] + stumps, 'edge', layer)
    cv.carve([ribbon([(x + dx, y + 0.08), (x + dx * 0.9, y + h - 0.22)], 0.012) for x in (x0 + 0.6, x1 - 0.6) for dx in (-0.1, 0.08)] +
             [ribbon([(x0 + 0.2, y + h - 0.08), (x1 - 0.2, y + h - 0.08)], 0.008)], layer)
    return y + h

def bambangan(cv, x, y, s=1.0, layer='mid'):
    """The bambangan: a big mango-like wild fruit, rough skinned, on its stalk."""
    cv.add([xf(ellipse(0, 0.32, 0.27, 0.34, rot=-20), x, y, s=s), xf(ribbon([(0.06, 0.64), (0.14, 0.82)], 0.02), x, y, s=s),
            xf(leaf(0.12, 0.78, 20, 0.35, 0.08), x, y, s=s)], 'dots', layer)

def bamboo_wall(cv):
    """Blurred hut wall behind the food: woven bamboo, a window, gourds and a
    carrying basket hung on pegs."""
    cv.add_eo([rect(13.4, 2.6, 17.6, 6.0), rect(13.65, 2.85, 17.35, 5.75)], 'edge', 'back')
    cv.add([ribbon([(13.65 + 0.62 * i, 2.85), (13.65 + 0.62 * i, 5.75)], 0.035) for i in range(1, 6)], 'solid', 'back')
    for x, s in ((3.0, 1.0), (3.9, 0.8), (5.0, 0.9)):
        cv.add([ribbon([(x, 7.2), (x, 6.6)], 0.02), ellipse(x, 6.25, 0.22 * s, 0.32 * s), ellipse(x, 5.75, 0.32 * s, 0.38 * s)],
               'solid', 'back')
    cv.add([[(17.9, 6.8), (19.5, 6.8), (19.2, 4.6), (18.2, 4.6)], ribbon([(18.7, 7.4), (17.9, 6.8)], 0.03)], 'solid', 'back')

# =====================================================================
# rig parts (registered once, keys prefixed with the state id)
# =====================================================================

def _siga():
    """Siga: the Kadazan-Dusun woven headcloth, tied so a stiff peak stands up
    over the brow."""
    band = _open([(0.062, 0.895), (0.064, 0.93), (0.046, 0.958), (0.0, 0.972), (-0.042, 0.962), (-0.06, 0.928),
                  (-0.058, 0.888)]) + [(0.0, 0.9)]
    peak = [(0.05, 0.95), (0.034, 1.0), (0.018, 1.064), (0.006, 1.07), (-0.004, 1.02), (-0.02, 0.965)]
    tail = [(-0.05, 0.93), (-0.085, 0.9), (-0.098, 0.86), (-0.078, 0.872), (-0.055, 0.9)]
    carves = [ribbon([(-0.05, 0.915), (0.055, 0.925)], 0.0022), ribbon([(-0.046, 0.94), (0.045, 0.948)], 0.0022),
              W.diamond(0.02, 1.005, 0.012, 0.03)[0]]
    return [band, peak, tail], 'grid', carves

def _sunduk():
    """A Kadazan woman's woven hat: a wide shallow cone over a head cloth."""
    brim = [(-0.13, 0.905), (-0.06, 0.95), (0.0, 0.985), (0.06, 0.952), (0.135, 0.908), (0.0, 0.928)]
    knob = ellipse(0.0, 0.99, 0.012, 0.012)
    cloth = _open([(0.055, 0.9), (0.05, 0.93), (0.0, 0.945), (-0.05, 0.93), (-0.062, 0.88), (-0.06, 0.82)]) + [(-0.03, 0.83)]
    return [brim, knob, cloth], 'edge', [ribbon([(-0.1, 0.913), (0.1, 0.915)], 0.002)]

def _sash(spec):
    """Gaung: a sash across the chest and a belt of old silver coins."""
    coins = [W.circle(-0.06 + 0.024 * k, 0.535 + 0.003 * k, 0.011, 10)[0] for k in range(6)]
    return [([ribbon([(-0.06, 0.785), (0.07, 0.56)], 0.016), ribbon([(-0.066, 0.545), (0.07, 0.555)], 0.014)] + coins,
             'edge', [])]

def _wakid_back(spec):
    """Wakid: the tall bamboo back-basket, flaring at the mouth, on its straps."""
    basket = [(-0.075, 0.48), (-0.15, 0.47), (-0.2, 0.88), (-0.06, 0.9)]
    straps = [ribbon([(-0.06, 0.86), (0.03, 0.78), (0.06, 0.66)], 0.006)]
    return [([basket], 'grid', [ribbon([(-0.08, 0.6 + 0.08 * k), (-0.18, 0.62 + 0.08 * k)], 0.003) for k in range(3)]),
            (straps, 'solid', [])]

def _it_staff(g, ang, fig):
    """The guide's staff, taller than he is, with the walking charm hung near
    its head: a carved pendant on a string of beads."""
    x = g[0] + 0.006
    shaft = ribbon([(x + 0.02, 0.0), (x, 1.08)], 0.0075, 0.0085)
    knob = ellipse(x, 1.095, 0.014, 0.02)
    cord = ribbon(_open([(x, 0.98), (x + 0.03, 0.93), (x + 0.035, 0.87)]), 0.0025)
    beads = [W.circle(x + 0.012 + 0.008 * k, 0.975 - 0.034 * k, 0.0085, 10)[0] for k in range(4)]
    pendant = [(x + 0.035, 0.875), (x + 0.058, 0.84), (x + 0.04, 0.78), (x + 0.015, 0.84)]
    tassel = [ribbon([(x + 0.04, 0.78), (x + 0.03 + 0.01 * k, 0.73)], 0.002) for k in range(3)]
    return [shaft, knob, cord, pendant] + beads + tassel, 'solid', [W.circle(x + 0.037, 0.835, 0.008, 8)[0]]

def _it_bundle(g, ang, fig):
    """Rice wrapped in a leaf parcel, tied with a string, offered forward."""
    x, y = g[0] + 0.035, g[1] + 0.01
    return [ellipse(x, y, 0.05, 0.036), [(x + 0.04, y + 0.02), (x + 0.075, y + 0.05), (x + 0.05, y + 0.005)]], 'edge', \
           [ribbon([(x - 0.01, y - 0.036), (x + 0.005, y + 0.036)], 0.003)]

def _it_lime(g, ang, fig):
    """Half a limau kapas squeezed over the bowl, juice dripping."""
    x, y = g[0] + 0.03, g[1] - 0.02
    half, cuts = lime_half(x, y, 0.042, rot=0)
    drops = [W.teardrop(x - 0.012 + 0.012 * k, y - 0.075 - 0.05 * k, 0.008, ang=math.pi)[0] for k in range(4)]
    return [half] + drops, 'solid', []

W.register(W.HATS, 'sabah_siga', _siga)
W.register(W.HATS, 'sabah_sunduk', _sunduk)
W.register(W.COSTUMES, 'sabah_gaung', dict(W.COSTUMES['baju'], lower=None, extra=_sash,
                                           cls={'top': 'lace', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.COSTUMES, 'sabah_porter', dict(W.COSTUMES['farmer'], lower=None, extra=_wakid_back,
                                            cls={'top': 'dots', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.COSTUMES, 'sabah_guide', dict(W.COSTUMES['baju'], lower=None,
                                           extra=lambda sp: _wakid_back(sp) + _sash(sp),
                                           cls={'top': 'lace', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.POSES, 'sabah_guntor', {'f': (30, 42), 'b': (-16, -14), 'lean': 0, 'legs': 'walk', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'sabah_point', {'f': (124, 8), 'b': (20, 30), 'lean': -2, 'legs': 'walk', 'hf': 'open', 'hb': 'grip'})
W.register(W.POSES, 'sabah_strap', {'f': (12, 140), 'b': (-20, 120), 'lean': 6, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'sabah_give', {'f': (68, 18), 'b': (-12, -10), 'lean': 4, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'sabah_coil', {'f': (52, 70), 'b': (40, 80), 'lean': 10, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})
W.register(W.LEGS, 'sabah_kneel', ((0.17, 0.065), (-0.1, 0.045), (0.14, 0.065), (-0.12, 0.05), 0.3))
W.register(W.POSES, 'sabah_squeeze', {'f': (100, 12), 'b': (60, 50), 'lean': 10, 'legs': 'sabah_kneel', 'hf': 'grip', 'hb': 'open'})
W.register(W.COSTUMES, 'sabah_kurung_kneel', dict(W.COSTUMES['kurung'], legs='trousers'))
W.register(W.ITEMS2, 'sabah_staff', _it_staff)
W.register(W.ITEMS2, 'sabah_bundle', _it_bundle)
W.register(W.ITEMS2, 'sabah_lime', _it_lime)

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def sabah_land(cv):
    """Mount Kinabalu's granite crown rising out of cloud, far above the
    rainforest canopy; a Kadazan house at the forest edge."""
    hills(cv, 9.0, 21, G + 1.6, 1.4, seed=21, n=3)
    kinabalu(cv, -0.3, 0.0, 1.1, layer='back')
    for cx, cy, sc, fl in ((1.6, 3.05, 0.75, False), (5.0, 3.2, 0.9, True), (8.6, 3.0, 0.7, False), (11.6, 2.75, 0.6, True),
                           (9.4, 6.5, 0.7, False), (17.2, 6.9, 0.8, True)):
        cloud(cv, cx, cy, sc, 'back', flip=fl, seed=int(cx * 3))
    birds(cv, 9.6, 5.9, 3, 0.5, seed=4, layer='back', flip=True)
    kinabalu(cv, -0.3, 0.0, 1.1, cloud_y=4.15)
    rainforest(cv, -0.3, 20.8, G + 0.25, 1.5, seed=31, emergent=((3.1, 2.6), (10.2, 2.3), (15.9, 2.8)))
    tree_fern(cv, 17.6, G + 0.02, 3.4, seed=3)
    tree_fern(cv, 19.4, G + 0.02, 2.6, seed=4, flip=True)
    ground(cv, 'earth', seed=7)
    frame_edges(cv, seed=8, left='none', right='none')

def sabah_people(cv):
    """At the trailhead the guide points the way up the mountain; a porter
    shoulders the wakid, a woman hands over rice for the climb, and a young
    man coils the rope."""
    kinabalu(cv, 11.4, 1.3, 0.75, layer='back')
    rainforest(cv, -0.3, 20.8, G + 0.3, 1.2, seed=41, layer='back')
    pondok(cv, 2.2, G + 0.1, 0.65, layer='back')
    W.place_figure(cv, dict(head='refined', hat='sabah_siga', costume='sabah_gaung', pose='sabah_point', item_b='stick',
                            rod_to=-0.25), 3.9, G, 3.35)
    W.place_figure(cv, dict(head='young', hat='sabah_siga', costume='sabah_porter', pose='sabah_strap', rod_to=-0.25),
                   7.6, G, 3.25)
    W.place_figure(cv, dict(body='female', hat='sabah_sunduk', costume='kurung', pose='sabah_give', item_f='sabah_bundle',
                            rod_to=-0.25), 10.15, G, 3.3, flip=True)
    W.place_figure(cv, dict(head='young', costume='farmer', pose='sabah_coil', item_f='rope', rod_to=-0.25), 13.6, G, 3.2,
                   flip=True)
    trail_post(cv, 15.4, G, 1.1)
    steps(cv, 16.3, G + 0.05, 7, 0.55, 0.36)
    tree_fern(cv, 19.5, G + 2.05, 2.6, seed=8, flip=True)
    ground(cv, 'earth', seed=17)
    frame_edges(cv, seed=18, left='banana', right='none')

def sabah_food(cv):
    """Hinava made at the hearth side: kneeling at the work board, the cook
    squeezes limau kapas over the raw fish in a shallow wooden bowl; a
    mackerel and shallots on the board, bambangan, limes and chillies about."""
    bamboo_wall(cv)
    dapur(cv, 4.9, G + 0.05, 1.1)
    steam(cv, 4.8, G + 2.6, 1.8, cw=False, seed=29)
    top = papan(cv, 9.4, 15.0, G + 0.02, 0.75)
    hinava_bowl(cv, 10.9, top, 2.6)
    W.place_figure(cv, dict(body='female', hat='sabah_sunduk', costume='sabah_kurung_kneel', pose='sabah_squeeze',
                            item_f='sabah_lime', rod_to=-0.25), 8.65, G, 3.9)
    fish(cv, 13.45, top + 0.2, 0.95, ang=3)
    cv.add([ribbon([(13.8, top + 0.05), (14.0, top + 0.1)], 0.03),
            [(13.98, top + 0.04), (14.6, top + 0.06), (14.57, top + 0.17), (14.0, top + 0.14)]], 'solid')
    for k in range(3):                                                  # shallots and lime halves on the board
        cv.add([ellipse(12.55 + 0.22 * k, top + 0.1, 0.1, 0.1, n=16), leaf(12.55 + 0.22 * k, top + 0.18, 90, 0.1, 0.02)], 'edge')
    for x in (6.6, 7.1):                                                # lime halves, cut face down
        cv.add([lime_half(x, G + 0.03, 0.2, rot=180)[0]], 'edge')
    limes(cv, 15.6, G + 0.05, 0.9)
    chillies(cv, 16.6, G + 0.05, 0.9)
    bambangan(cv, 2.65, G + 0.02, 1.3)
    bambangan(cv, 3.35, G + 0.02, 1.0)
    jar(cv, 1.6, G, 1.2, cls='lace')
    ground(cv, 'earth', seed=27)
    frame_edges(cv, seed=28, left='none', right='banana')

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def _pivot(rot, loc, scale=1.0):
    pv = bpy.data.objects.new('Pivot', None)
    bpy.context.scene.collection.objects.link(pv)
    for ob in list(bpy.context.scene.objects):
        if ob.type in ('MESH', 'CURVE') and ob.parent is None:
            ob.parent = pv
    pv.rotation_euler, pv.location, pv.scale = rot, loc, (scale,) * 3
    return pv

def icon_food_hinava():
    """Hinava in a shallow wooden bowl: translucent slices of raw mackerel
    lying in a dark pool of lime juice, red chilli and shallot rings, ginger
    shreds, and halved limau kasturi perched on the rim."""
    rnd = random.Random(11)
    wood = _mat('Bowl', (0.5, 0.3, 0.13), 0.55, grain=(0.3, 0.16, 0.06))
    _lathe('Bowl', [(0.0, 0.0), (0.62, 0.0), (0.98, 0.08), (1.18, 0.22), (1.25, 0.34), (1.18, 0.35), (1.1, 0.24), (0.88, 0.13),
                    (0.0, 0.1)], wood, 64)
    juice = _mat('Juice', (0.22, 0.17, 0.06), 0.08)
    _lathe('Juice', [(0.0, 0.2), (1.08, 0.2)], juice, 64, sharp=0)
    fish = []
    for name, rgb in (('Fish', (0.94, 0.8, 0.76)), ('FishPink', (0.9, 0.62, 0.6))):
        m = _mat(name, rgb, 0.22)
        bs = m.node_tree.nodes['Principled BSDF']
        bs.inputs['Transmission Weight'].default_value = 0.35
        bs.inputs['Subsurface Weight'].default_value = 0.4
        fish.append(m)
    for k in range(22):                                 # slices lying in the juice, overlapping toward the middle
        a, r = rnd.uniform(0, TAU), 0.75 * rnd.random() ** 0.7
        z = 0.24 + 0.1 * (1 - r / 0.8) + 0.01 * k / 22
        _box('Slice%d' % k, (r * math.cos(a), r * math.sin(a), z), (0.46, 0.11, 0.025),
             (rnd.uniform(-0.15, 0.15), rnd.uniform(-0.25, 0.25), rnd.uniform(0, 3)), fish[k % 2])
    chili = _mat('Chilli', (0.86, 0.05, 0.03), 0.3)
    onion = _mat('Shallot', (0.62, 0.18, 0.4), 0.35)
    ginger = _mat('Ginger', (0.95, 0.8, 0.42), 0.5)
    for k in range(9):
        a, r = rnd.uniform(0, TAU), rnd.uniform(0.1, 0.7)
        _torus('Chilli%d' % k, (r * math.cos(a), r * math.sin(a), 0.38 + rnd.uniform(0, 0.04)), 0.065, 0.026, chili,
               rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0), seg=16)
    for k in range(6):
        a, r = rnd.uniform(0, TAU), rnd.uniform(0.1, 0.65)
        _torus('Shallot%d' % k, (r * math.cos(a), r * math.sin(a), 0.37 + rnd.uniform(0, 0.04)), 0.1, 0.018, onion,
               rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0), seg=20)
    for k in range(10):
        a, r = rnd.uniform(0, TAU), rnd.uniform(0.1, 0.6)
        _box('Ginger%d' % k, (r * math.cos(a), r * math.sin(a), 0.4), (0.2, 0.02, 0.02), (0, 0.2, rnd.uniform(0, 3)), ginger)
    skin = _mat('LimeSkin', (0.2, 0.5, 0.1), 0.4)
    pulp = _mat('LimePulp', (0.85, 0.82, 0.3), 0.25)
    for k, a in enumerate((-0.25, 0.45, 3.5)):                         # halved limau kasturi on the rim, cut face up
        x, y = 1.2 * math.cos(a), 1.2 * math.sin(a)
        h = _lathe('Lime%d' % k, [(0.0, 0.0), (0.1, 0.012), (0.16, 0.07), (0.17, 0.15)], skin, 32)
        c = _lathe('Pulp%d' % k, [(0.0, 0.15), (0.16, 0.15)], pulp, 32, sharp=0)
        for ob in (h, c):
            ob.location, ob.rotation_euler = (x, y, 0.33), (0.45, 0.25 * math.cos(a), 0)
    return (0.0, -4.6, 3.9), (0.1, 0.05, 0.18)

def icon_item_charm():
    """The mountain guide's walking charm: a carved wooden figure-pendant on a
    string of red, yellow, black and white beads, tied to a staff head."""
    wood = _mat('Wood', (0.36, 0.2, 0.09), 0.6, grain=(0.2, 0.1, 0.04))
    dark = _mat('Dark', (0.12, 0.07, 0.04), 0.6)
    cord = _mat('Cord', (0.45, 0.32, 0.18), 0.8)
    cols = [_mat('Bead%d' % i, c, 0.35) for i, c in enumerate(((0.75, 0.08, 0.06), (0.95, 0.75, 0.15), (0.05, 0.05, 0.05),
                                                               (0.92, 0.9, 0.85)))]
    # the head of the staff, laid across the top of the frame
    st = _lathe('Staff', [(0.0, -0.75), (0.075, -0.75), (0.08, 0.5), (0.11, 0.58), (0.11, 0.7), (0.075, 0.8), (0.0, 0.82)], wood, 24)
    st.rotation_euler, st.location = (0, math.pi / 2, 0), (-0.05, 0, 1.25)
    for x in (-0.24, -0.16, 0.16, 0.24):
        _torus('Bind%.2f' % x, (x, 0, 1.25), 0.085, 0.02, cord, rot=(0, math.pi / 2, 0), seg=24)
    # two strands of beads falling in a V to the carved pendant
    for sx in (-1, 1):
        for i in range(11):
            t = i / 10
            p = (sx * 0.2 * (1 - t) + sx * 0.05 * math.sin(math.pi * t), -0.03 * math.sin(math.pi * t), 1.15 - 0.47 * t)
            _blob('B%d_%d' % (sx, i), p, (0.055, 0.055, 0.05), (0, 0, 0), cols[(i + (sx > 0)) % 4], 12)
    _lathe('Pendant', [(0.0, -0.84), (0.18, -0.74), (0.26, -0.44), (0.2, -0.16), (0.25, 0.06), (0.15, 0.22), (0.0, 0.26)],
           wood, 32).location = (0, 0, 0.42)
    _blob('PendantHead', (0, 0, 0.74), (0.11, 0.11, 0.12), (0, 0, 0), wood, 16)
    brass = _mat('Brass', (0.8, 0.6, 0.25), 0.35, metal=1.0)
    for k, z in enumerate((0.44, 0.3, 0.0)):
        _torus('PRing%d' % k, (0, 0, z), 0.24 if k < 2 else 0.25, 0.018, brass if k < 2 else dark, seg=32)
    for k in range(9):
        u = (k - 4) / 4
        _tube('Tassel%d' % k, [(0.03 * u, 0, -0.4), (0.07 * u, -0.01, -0.62), (0.1 * u, -0.02, -0.82)], 0.016, cols[k % 2])
    _pivot((math.radians(-8), 0, math.radians(18)), (0, 0, 0.0), 1.0)
    return (0, -4.9, 1.2), (0.0, 0, 0.25)

# =====================================================================
# registry: what the CLI renders for this state
# =====================================================================

PUPPET = dict(head='refined', hat='sabah_siga', costume='sabah_guide', pose='sabah_guntor', item_f='sabah_staff',
              item_b='rope')                                                                       # Guntor
BEATS = {'land': sabah_land, 'people': sabah_people, 'food': sabah_food}
ICONS = {'food': icon_food_hinava, 'item': icon_item_charm}
