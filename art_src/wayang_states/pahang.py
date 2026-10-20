"""Pahang: misty highland ridges and contour tea terraces, a farmer walking the
slope, hill vegetables tossed in the kuali, Along under his woven terendak."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props: highland
# =====================================================================

def ridge(cv, x0, x1, top, h, bot, seed=1, layer='mid', n=4, cls='dots'):
    """A mountain ridge floating on mist: a soft skyline from `top` rising by up
    to h, its foot dissolving into a scalloped cloud line around `bot`, so the
    kelir light shows between one ridge and the next."""
    f, g = noise1(seed, n * 2), noise1(seed + 9, n * 5)
    sky = [(x0 + (x1 - x0) * t, top + h * (0.5 + 0.4 * f(t) + 0.1 * g(t))) for t in (i / 60 for i in range(61))]
    foot = []
    for i in range(41):                                 # scalloped awan along the foot
        t = 1 - i / 40
        foot.append((x0 + (x1 - x0) * t, bot + 0.12 * abs(math.sin(t * 31 + seed)) + 0.15 * f(t)))
    return cv.add([sky + foot], cls, layer)

def tea_hill(cv, cx, base, w, h, rows=5, seed=1, layer='mid', cls='solid', r=0.07):
    """Tea estate hill: a dome striped by rows of clipped tea bushes that wrap
    its contours. Each row's top edge is a string of round bush tops (radius
    r); the walk above it is cut through, so each row reads as a hedge."""
    top = lambda x: base + h * max(0.0, 1 - ((x - cx) / w) ** 2) ** 0.8
    def bushes(x0, x1, line):
        """Bump line left to right: half circles of radius r sitting on line(x)."""
        n = max(2, int((x1 - x0) / (2 * r)))
        step = (x1 - x0) / n
        out = []
        for i in range(n):
            bx = x0 + step * (i + 0.5)
            out += arc_pts(bx, line(bx), step / 2, 180, 0, 8)[:-1]
        return out + [(x1, line(x1))]
    sky = bushes(cx - w, cx + w, lambda x: top(x) - r)
    pid = cv.add([[(cx - w, base - 0.2)] + sky + [(cx + w, base - 0.2)]], cls, layer)
    cuts, gap = [], r + 0.06
    for k in range(rows):
        fr = (k + 1) / (rows + 0.6)
        yc = base + h * fr
        half = w * (1 - fr) ** 0.62 * 0.97
        sag = 0.35 * h / rows
        line = lambda x, yc=yc, half=half, sag=sag: yc - sag * (1 - ((x - cx) / half) ** 2)
        lo = bushes(cx - half, cx + half, line)
        hi = [(x, line(x) + gap) for x, _ in reversed(lo[::3])]
        cuts.append(lo + hi)
    cv.carve(cuts, layer)
    return pid

def tree_fern(cv, x, y, h, layer='mid', lean=0.05, seed=1, fronds=9):
    """Paku gajah: a slim shaggy trunk under a parasol of arching pinnate
    fronds, a fiddlehead uncurling at the crown."""
    rnd = random.Random(seed)
    top = (x + lean * h, y + h)
    trunk = _open([(x, y), (x + lean * h * 0.3, y + h * 0.5), top])
    cv.add([ribbon(trunk, 0.045 * h ** 0.5, 0.035 * h ** 0.5)], 'edge', layer)
    cv.carve([ribbon([(p[0] - 0.03 * h ** 0.5, p[1]), (p[0] + 0.03 * h ** 0.5, p[1] + 0.03)], 0.006) for p in trunk[2:-2:2]], layer)
    crown = []
    for i in range(fronds):
        a = math.radians(-15 + 210 * i / (fronds - 1) + rnd.uniform(-6, 6))
        L = h * rnd.uniform(0.42, 0.55)
        d = (math.cos(a), math.sin(a))
        droop = L * (0.25 + 0.3 * abs(math.cos(a)))
        path = _open([top, (top[0] + d[0] * L * 0.35, top[1] + d[1] * L * 0.35 + 0.08),
                      (top[0] + d[0] * L * 0.75, top[1] + d[1] * L * 0.5 - droop * 0.35),
                      (top[0] + d[0] * L, top[1] + d[1] * L * 0.35 - droop)])
        crown.append(ribbon(path, 0.016 * h ** 0.5, 0.004))
        for k in range(3, len(path) - 1):
            p, q = path[k], path[k + 1]
            ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
            ll = h * 0.075 * (1 - 0.7 * k / len(path))
            for sd in (1, -1):
                crown.append(leaf(p[0], p[1], ang + 62 * sd, ll, 0.011 * h ** 0.5))
    crown.append(scroll(top[0] + 0.12, top[1] + 0.3, 0.11, 0.03, 1.2, a0=0, cw=False,
                        tail=[(top[0], top[1]), (top[0] + 0.1, top[1] + 0.18)]))
    cv.add(crown, 'solid', layer)

def hill_shed(cv, x, y, s=1.0, layer='mid', flip=False):
    """Highland farm shed: plank walls, a corrugated lean-to roof, a rain tank."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    cv.add_eo([P(rect(-1.0, 0.0, 1.0, 1.25)), P(rect(-0.65, 0.0, -0.15, 0.95)), P(rect(0.3, 0.5, 0.75, 0.9))], 'slits', layer)
    cv.add([P([(-1.25, 1.15), (1.3, 1.6), (1.3, 1.75), (-1.25, 1.32)])], 'slits', layer)
    cv.add([P(rect(1.1, 0.0, 1.55, 0.95)), P(ellipse(1.325, 0.95, 0.225, 0.06))], 'edge', layer)
    cv.add([P(ribbon([(0.6, 1.55), (0.6, 1.95)], 0.03)), P(ribbon(arc_pts(0.6, 2.1, 0.12, 270, 450, 10), 0.01))], 'solid', layer)

def cabbage(cv, x, y, s, layer='mid'):
    """Kubis: a round head cupped by big flaring veined outer leaves."""
    head = ellipse(x, y + 0.45 * s, 0.36 * s, 0.34 * s, n=32)
    outer = [leaf(x + sx * 0.06 * s, y + 0.05 * s, 90 + sx * a, ln * s, wd * s, bend=-sx * 0.1 * s)
             for sx in (-1, 1) for a, ln, wd in ((70, 0.72, 0.26), (35, 0.78, 0.24))]
    cv.add(outer + [head], 'edge', layer)
    cv.carve([ribbon(_open([(x + sx * 0.03 * s, y + 0.15 * s), (x + sx * 0.18 * s, y + 0.45 * s), (x + sx * 0.08 * s, y + 0.74 * s)]),
                     0.012 * s, 0.004 * s) for sx in (-1, 1)] +
             [ribbon(_open([(x + sx * 0.1 * s, y + 0.08 * s), (x + sx * 0.45 * s, y + 0.3 * s), (x + sx * 0.66 * s, y + 0.3 * s)]),
                     0.01 * s, 0.004 * s) for sx in (-1, 1)], layer)

def tomatoes(cv, x, y, s, layer='mid', n=3):
    polys = []
    for i in range(n):
        cx, cy = x + (i - (n - 1) / 2) * 0.36 * s, y + (0.16 + (0.14 if i == 1 else 0)) * s
        polys.append(ellipse(cx, cy, 0.19 * s, 0.16 * s, n=20))
        polys += [leaf(cx, cy + 0.14 * s, 90 + a, 0.12 * s, 0.025 * s) for a in (-60, 0, 60)]
    cv.add(polys, 'edge', layer)

def greens(cv, x, y, s, layer='mid'):
    """A tied bunch of sawi: long stalks fanning into broad leaves."""
    polys = []
    for i in range(6):
        a = 90 + (i - 2.5) * 13
        base = (x + (i - 2.5) * 0.04 * s, y)
        tip = (base[0] + 0.55 * s * math.cos(math.radians(a)), y + 0.55 * s * math.sin(math.radians(a)))
        polys.append(ribbon([base, tip], 0.022 * s, 0.018 * s))
        polys.append(leaf(tip[0], tip[1] - 0.05 * s, a, 0.55 * s, 0.13 * s, bend=0.04 * s * (i - 2.5)))
    cv.add(polys, 'edge', layer)
    cv.carve([ribbon([(x - 0.15 * s, y + 0.18 * s), (x + 0.15 * s, y + 0.18 * s)], 0.012 * s)], layer)

def garlic(cv, x, y, s, layer='mid'):
    polys = [_open([(-0.2, 0.05), (-0.24, 0.2), (-0.12, 0.34), (0.0, 0.4)], 4) + _open([(0.0, 0.4), (0.12, 0.34), (0.24, 0.2),
                                                                                       (0.2, 0.05)], 4)[1:] + [(0.0, 0.0)],
             ribbon([(0.0, 0.38), (0.02, 0.55)], 0.02, 0.012)]
    cv.add([xf(p, x, y, s=s) for p in polys], 'edge', layer)
    cv.carve([xf(ribbon(_open([(sx * 0.03, 0.05), (sx * 0.1, 0.2), (sx * 0.04, 0.34)]), 0.008), x, y, s=s) for sx in (-1, 1)], layer)

def raga(cv, x, y, s, layer='mid'):
    """Raga: a woven rattan basket, flaring, with a rim and loops."""
    cv.add([xf([(-0.38, 0.0), (0.38, 0.0), (0.5, 0.75), (-0.5, 0.75)], x, y, s=s), xf(rect(-0.54, 0.72, 0.54, 0.82), x, y, s=s)],
           'grid', layer)

def kuali(cv, cx, y, w, layer='mid', seed=1):
    """Kuali: a wide black wok with loop handles, vegetables tossed above it."""
    rnd = random.Random(seed)
    h = w * 0.24
    left = _open([(-0.5 * w, h), (-0.44 * w, h * 0.55), (-0.3 * w, h * 0.18), (0.0, 0.0)], 5)[:-1]
    heap = _open([(-0.42 * w, h * 0.9), (-0.25 * w, h * 1.2), (0.0, h * 1.32), (0.25 * w, h * 1.18), (0.42 * w, h * 0.9)], 5)
    cv.add([xf(heap, cx, y)], 'edge', layer)
    tossed = []                                         # cabbage leaves, chilli and garlic leaping from the wok
    for i in range(7):
        a = 90 + (i - 3) * 22
        r = w * rnd.uniform(0.32, 0.5)
        px, py = cx + r * math.cos(math.radians(a)) * 0.9, y + h * 1.2 + r * math.sin(math.radians(a)) * 0.55
        if i % 3 == 0:
            tossed.append(leaf(px, py, rnd.uniform(0, 360), 0.32 * w * 0.35, 0.1 * w * 0.35, bend=0.04))
        elif i % 3 == 1:
            tossed.append(ellipse(px, py, 0.05 * w * 0.5, 0.04 * w * 0.5, rot=rnd.uniform(0, 180), n=14))
        else:
            tossed.append(leaf(px, py, rnd.uniform(0, 360), 0.22 * w * 0.35, 0.04 * w * 0.35, bend=0.03, wide_at=0.25))
    cv.add(tossed, 'solid', layer)
    pid = cv.add([xf(mirror_pts(left), cx, y), xf(rect(-0.52 * w, h * 0.95, 0.52 * w, h * 1.04), cx, y)], 'lace', layer)
    cv.add([xf(ribbon(arc_pts(sx * 0.58 * w, h * 0.98, 0.07 * w, 0, 360, 18, ry=0.045 * w), 0.012 * w), cx, y) for sx in (-1, 1)],
           'solid', layer, pid=pid)
    return y + h

# =====================================================================
# rig parts: Along and the hill farmers
# =====================================================================

def _hat_terendak():
    """Terendak: a broad, shallow domed hat of woven bamboo with a knob, its brim
    lifting a little at the edges."""
    B, F = (-0.22, 0.912), (0.235, 0.905)
    dome = _open([B, (-0.17, 0.935), (-0.09, 0.972), (0.0, 0.99), (0.09, 0.975), (0.17, 0.94), F], 6)
    under = _open([F, (0.2, 0.893), (0.08, 0.884), (-0.06, 0.886), (-0.19, 0.895), B], 6)[1:-1]
    knob = [(-0.014, 0.985), (0.014, 0.985), (0.008, 1.012), (0.0, 1.02), (-0.008, 1.012)]
    carves = [ribbon(arc_pts(0.006, 0.89, r, 15, 165, 20, ry=r * 0.38), 0.0022) for r in (0.07, 0.13, 0.19)]
    return [dome + under, knob], 'grid', carves

def _basket_extra(spec):
    """A tall raga strapped on the back for the tea leaves, a strap over the shoulder."""
    basket = [(-0.085, 0.5), (-0.17, 0.5), (-0.205, 0.86), (-0.07, 0.86)]
    rim = rect(-0.212, 0.85, -0.064, 0.88)
    strap = ribbon(_open([(-0.08, 0.84), (-0.02, 0.8), (0.05, 0.78), (0.07, 0.7), (0.05, 0.6)]), 0.008)
    return [([basket, rim], 'grid', []), ([strap], 'solid', [])]

def _it_staff(g, ang, fig):
    """A tall bamboo staff planted at the foot, nodes cut through."""
    bot, top = (g[0] + 0.03, 0.0), (g[0] - 0.025, g[1] + 0.34)
    nodes = [ribbon([(bot[0] + (top[0] - bot[0]) * t - 0.009, bot[1] + (top[1] - bot[1]) * t),
                     (bot[0] + (top[0] - bot[0]) * t + 0.009, bot[1] + (top[1] - bot[1]) * t + 0.002)], 0.0016)
             for t in (0.12, 0.3, 0.5, 0.7, 0.88)]
    return [ribbon([bot, top], 0.0085, 0.0075)], 'solid', nodes

def _it_sudip(g, ang, fig):
    """Sudip: a long iron wok turner, its blade dipping into the kuali."""
    a = math.radians(-30)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.3 * d[0], g[1] + 0.3 * d[1])
    blade = xf([(0.0, -0.022), (0.07, -0.028), (0.075, 0.028), (0.0, 0.022)], end[0], end[1], rot=-55)
    return [ribbon([(g[0] - 0.05 * d[0], g[1] - 0.05 * d[1]), end], 0.0055), blade], 'solid', []

W.register(W.HATS, 'pahang_terendak', _hat_terendak)
W.register(W.COSTUMES, 'pahang_hill', dict(W.COSTUMES['baju'], extra=_basket_extra,
                                           cls={'top': 'dots', 'lower': 'scales', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.COSTUMES, 'pahang_picker', dict(W.COSTUMES['kurung'], extra=_basket_extra))
W.register(W.ITEMS2, 'pahang_staff', _it_staff)
W.register(W.ITEMS2, 'pahang_sudip', _it_sudip)
W.register(W.POSES, 'pahang_calm', {'f': (26, 34), 'b': (-14, -10), 'lean': 2, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'pahang_climb', {'f': (34, 38), 'b': (-20, -12), 'lean': 9, 'legs': 'walk', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'pahang_toss', {'f': (95, 30), 'b': (40, 60), 'lean': 8, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'pahang_pluck', {'f': (78, 30), 'b': (55, 45), 'lean': 14, 'legs': 'walk', 'hf': 'open', 'hb': 'open'})

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def pahang_land(cv):
    """Misty hill terraces roll away, covered in rows of clipped tea; pickers
    with baskets on their backs work the rows, a shade tree on the crest."""
    ridge(cv, -0.5, 21, G + 3.3, 1.6, G + 2.4, seed=91, layer='back', n=3, cls='edge')
    cloud(cv, 4.2, 7.3, 0.7, 'back', seed=92)
    cloud(cv, 15.6, 7.1, 0.75, 'back', flip=True, seed=93)
    birds(cv, 10.6, 6.6, 3, 0.5, seed=94, layer='back', flip=True)
    # mid: two ridges floating on mist, then the tea hills in front
    ridge(cv, -0.5, 21, G + 2.55, 1.3, G + 1.85, seed=95, n=4, cls='dots')
    ridge(cv, -0.5, 21, G + 1.6, 1.0, G + 0.9, seed=96, n=5, cls='scales')
    wisps = []                                          # mist curling through the far ridges
    for x0, x1, y, cw in ((7.6, 11.4, G + 2.25, True), (12.4, 17.2, G + 2.55, False), (15.6, 19.8, G + 2.2, True),
                          (8.6, 12.0, G + 1.55, False)):
        path = [(x0 + (x1 - x0) * t, y + 0.06 * math.sin(t * 7 + x0)) for t in (i / 30 for i in range(31))]
        wisps.append(ribbon(path, 0.0, wf=lambda t: 0.006 + 0.03 * math.sin(math.pi * t) ** 0.7))
        wisps.append(scroll(x1 + 0.12 if cw else x0 - 0.12, y + 0.12, 0.12, 0.025, 1.1, a0=270, cw=not cw))
    cv.carve(wisps)
    tea_hill(cv, 16.6, G + 0.1, 4.8, 2.0, rows=4, seed=97, cls='scales')
    raintree(cv, 18.3, G + 1.85, 2.4, seed=106)                          # a shade tree on the crest
    W.place_figure(cv, dict(body='female', hat='caping', costume='pahang_picker', pose='pahang_pluck', rods=False),
                   14.6, G + 1.8, 1.8)
    tea_hill(cv, 5.0, G + 0.05, 5.6, 3.3, rows=7, seed=98, cls='dots')
    hill_shed(cv, 6.4, G + 3.12, 0.5)
    for x, y, sc, fl in ((3.3, G + 3.05, 1.35, False), (8.25, G + 2.38, 1.55, True)):
        W.place_figure(cv, dict(body='female', hat='caping', costume='pahang_picker', pose='pahang_pluck', rods=False),
                       x, y, sc, flip=fl)
    tree_fern(cv, 10.2, G + 0.15, 3.2, lean=0.06, seed=99)
    tree_fern(cv, 11.3, G + 0.15, 2.2, lean=-0.08, seed=100, fronds=8)
    ground(cv, 'earth', seed=102)
    tree_fern(cv, 0.4, 0.1, 5.0, layer='front', lean=0.07, seed=103, fronds=10)
    grass(cv, -0.2, 3.0, 0.0, 1.2, seed=104)
    grass(cv, 17.6, 20.7, 0.0, 1.1, seed=105)

def pahang_people(cv):
    """A farmer walks the steep tea slope calmly, a picker at work above."""
    ridge(cv, -0.5, 21, G + 3.0, 1.5, G + 2.2, seed=111, layer='back', n=3, cls='edge')
    cloud(cv, 9.6, 7.3, 0.7, 'back', seed=112)
    ridge(cv, -0.5, 21, G + 1.9, 1.2, G + 1.25, seed=113, n=4, cls='dots')
    hill_shed(cv, 3.4, G + 2.05, 0.5)
    # the slope: rising left to right, a band of tea above the path
    slope = lambda x: G + 2.3 * (max(x, 0.0) / 20.6) ** 1.2
    xs = [x / 4 for x in range(0, 84)]
    upper = [(-0.2, G - 0.1)] + [(x, slope(x) + 0.75 + 0.06 * math.sin(x * 1.3)) for x in xs] + [(20.8, G - 0.1)]
    cv.add([upper], 'solid')
    cv.carve([ribbon([(x, slope(x) + 0.36 + 0.06 * abs(math.sin(math.pi * x / 0.26))) for x in [i / 16 for i in range(330)]],
                     0.022, 0.022)])
    bank = [(-0.2, G - 0.1)] + [(x, slope(x)) for x in xs] + [(20.8, slope(20.8)), (20.8, G - 0.1)]
    cv.add([bank], 'scales')
    W.place_figure(cv, dict(head='young', hat='pahang_terendak', costume='pahang_hill', pose='pahang_climb',
                            item_f='pahang_staff', rod_to=-0.25 - (slope(8.6) - G) / 3.3), 8.6, slope(8.6), 3.3)
    W.place_figure(cv, dict(body='female', hat='caping', costume='pahang_picker', pose='pahang_pluck',
                            rod_to=-0.25 - (slope(14.6) - G) / 3.2), 14.6, slope(14.6), 3.2)
    tree_fern(cv, 18.6, slope(18.6) - 0.05, 3.4, lean=-0.06, seed=114, fronds=9)
    ground(cv, 'earth', seed=115)
    tree_fern(cv, 0.6, 0.1, 4.8, layer='front', lean=0.08, seed=116, fronds=10)
    grass(cv, -0.2, 3.0, 0.0, 1.2, seed=117)

def pahang_food(cv):
    """A simple dish of hill vegetables is cooked: greens tossed in the kuali."""
    # back: plank wall of the farm kitchen, a window on misty hills, hanging baskets
    cv.add_eo([rect(13.6, 2.5, 18.2, 6.3), rect(13.9, 2.8, 17.9, 6.0)], 'edge', 'back')
    ridge(cv, 13.9, 17.9, 3.4, 1.4, 2.8, seed=121, layer='back', n=2, cls='edge')
    for x in (2.6, 5.0):
        cv.add([ribbon([(x, 8.3), (x, 6.6)], 0.02)], 'solid', 'back')
        raga(cv, x, 5.9, 0.9, 'back')
    # hero: the kuali on the clay stove, the cook turning the greens, steam
    dapur(cv, 10.6, G + 0.05, 1.35, pot=False, seed=4)
    rim = kuali(cv, 10.6, G + 1.38, 3.6, seed=5)
    for i, (dx, hh, cw) in enumerate(((-1.1, 1.8, False), (0.0, 2.2, True), (1.1, 1.9, False))):
        steam(cv, 10.6 + dx, rim + 1.25, hh, cw=cw, seed=130 + i)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kurung', pose='pahang_toss', item_f='pahang_sudip',
                            rod_to=-0.25), 6.8, G, 3.5)
    for sx in (-1, 1):                                  # baskets of hill vegetables, mirrored about the wok
        raga(cv, 10.6 + sx * 5.6, G, 1.1)
        cabbage(cv, 10.6 + sx * 5.6, G + 0.9, 0.9)
    tomatoes(cv, 18.3, G, 1.1)
    greens(cv, 2.4, G, 1.6)
    garlic(cv, 13.6, G, 1.0)
    garlic(cv, 14.05, G, 0.8)
    ground(cv, 'earth', seed=137)
    frame_edges(cv, seed=138, left='banana', right='none')

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def icon_food_hill_greens(seed=4):
    """Tumis sayur bukit: cabbage, choy sum, carrot coins and cherry tomatoes
    glossy with garlic oil on an enamel plate."""
    rnd = random.Random(seed)
    plate = [(0.0, 0.0), (0.7, 0.0), (0.75, 0.04), (1.5, 0.12), (1.85, 0.26), (1.9, 0.3), (1.84, 0.3), (1.45, 0.18), (0.0, 0.14)]
    _lathe('Plate', plate, _mat('Enamel', (0.94, 0.95, 0.92), 0.2, coat=0.3), 72)
    _torus('RimLine', (0, 0, 0.29), 1.8, 0.02, _mat('BlueRim', (0.1, 0.25, 0.6), 0.3))
    cab = [_mat('Cabbage%d' % i, c, 0.35, coat=0.2) for i, c in enumerate(((0.75, 0.88, 0.5), (0.55, 0.78, 0.35), (0.88, 0.92, 0.7)))]
    for i in range(16):                                 # torn cabbage leaves, curled
        a, r = rnd.uniform(0, TAU), rnd.uniform(0.1, 1.1)
        _blob('Cab%d' % i, (r * math.cos(a), r * math.sin(a), 0.22 + 0.12 * (1 - r) + rnd.uniform(0, 0.08)),
              (0.32, 0.22, 0.04), (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), a), cab[i % 3], seg=12)
    stem, lf = _mat('Stem', (0.72, 0.86, 0.5), 0.35), _mat('Choy', (0.12, 0.42, 0.1), 0.35, coat=0.2)
    for i in range(7):                                  # choy sum stalks with dark leaves
        a = rnd.uniform(0, TAU)
        p0 = (0.9 * math.cos(a) * rnd.uniform(0.3, 1), 0.9 * math.sin(a) * rnd.uniform(0.3, 1), 0.38)
        d = (math.cos(a + 1.3), math.sin(a + 1.3))
        _tube('Stalk%d' % i, [p0, (p0[0] + 0.5 * d[0], p0[1] + 0.5 * d[1], 0.42)], 0.045, stem)
        _blob('ChoyLeaf%d' % i, (p0[0] + 0.7 * d[0], p0[1] + 0.7 * d[1], 0.44), (0.3, 0.16, 0.03), (0.2, 0.1, a + 1.3), lf, seg=10)
    carrot = _mat('Carrot', (0.95, 0.45, 0.08), 0.35)
    for i in range(8):
        a, r = rnd.uniform(0, TAU), rnd.uniform(0.2, 1.0)
        _lathe('Carrot%d' % i, [(0.0, 0.0), (0.13, 0.0), (0.13, 0.04), (0.0, 0.04)], carrot, 20).location = \
            (r * math.cos(a), r * math.sin(a), 0.42 + rnd.uniform(0, 0.08))
    tomato = _mat('Tomato', (0.85, 0.08, 0.04), 0.25, coat=0.4)
    for i, (x, y) in enumerate(((0.55, -0.35), (-0.6, -0.2), (0.15, 0.55), (-0.15, -0.6))):
        _blob('Tom%d' % i, (x, y, 0.5), (0.15, 0.15, 0.13), (0, 0, 0), tomato)
    garlic_m = _mat('Garlic', (0.98, 0.9, 0.7), 0.4)
    for i in range(10):
        a, r = rnd.uniform(0, TAU), rnd.uniform(0.1, 1.0)
        _blob('Garl%d' % i, (r * math.cos(a), r * math.sin(a), 0.5), (0.05, 0.04, 0.02), (0, 0, a), garlic_m, seg=6)
    return (0, -6.4, 6.0), (0, 0, 0.25)

def icon_item_terendak():
    """The hill farmer's woven hat: a broad domed terendak of split bamboo in a
    twill weave, a rattan rim, a turned knob and a cloth chin tie."""
    rnd = random.Random(7)
    straw = _mat('Bamboo', (0.82, 0.62, 0.32), 0.6, grain=(0.6, 0.42, 0.2))
    dark = _mat('Weave', (0.45, 0.28, 0.12), 0.65)
    prof = [(0.0, 0.62), (0.12, 0.6), (0.4, 0.5), (0.8, 0.32), (1.2, 0.16), (1.55, 0.06), (1.62, 0.04)]
    _lathe('Hat', prof, straw, 96)
    for k in range(24):                                 # radial twill ribs over the dome
        a = TAU * k / 24
        pts = [(r * math.cos(a + 0.12 * r), r * math.sin(a + 0.12 * r), z + 0.012) for r, z in prof[1:]]
        _tube('Rib%d' % k, pts, 0.018, dark)
    for r, z in ((0.45, 0.48), (0.85, 0.31), (1.25, 0.15)):
        _torus('Ring%.2f' % r, (0, 0, z + 0.01), r, 0.022, dark, seg=64)
    _torus('Rim', (0, 0, 0.04), 1.62, 0.05, _mat('Rattan', (0.5, 0.3, 0.12), 0.5), seg=96)
    _lathe('Knob', [(0.0, 0.6), (0.1, 0.62), (0.08, 0.72), (0.04, 0.78), (0.0, 0.8)], _mat('Wood', (0.36, 0.18, 0.07), 0.45), 24)
    tie = _mat('Tie', (0.15, 0.32, 0.28), 0.7)
    _tube('TieL', [(-1.0, -0.3, 0.12), (-0.9, -0.8, -0.1), (-0.5, -1.4, -0.25), (-0.1, -1.7, -0.3)], 0.03, tie)
    _tube('TieR', [(1.0, -0.3, 0.12), (0.9, -0.8, -0.1), (0.5, -1.4, -0.25), (0.15, -1.75, -0.32)], 0.03, tie)
    return (0.0, -7.0, 5.0), (0.0, -0.25, 0.05)

# =====================================================================
# registry
# =====================================================================

def _feet_aware(base):
    """W.render_puppet_v2, but a spec may carry 'feet' (the frozen sheet puts every puppet's
    feet at 0.14, 32 px above the kelir ground). Specs without 'feet' render unchanged."""
    def render(spec, path):
        keep = W.PUPPET_SHEET['feet']
        W.PUPPET_SHEET['feet'] = spec.get('feet', keep)
        try:
            return base(spec, path)
        finally:
            W.PUPPET_SHEET['feet'] = keep
    render.feet_aware = True
    return render
# ponytail: same patch as perlis.py / journey.py; drop it once the lib's PUPPET_SHEET['feet'] is 0.03
if not getattr(W.render_puppet_v2, 'feet_aware', False):
    W.render_puppet_v2 = _feet_aware(W.render_puppet_v2)

PUPPET = dict(head='young', hat='pahang_terendak', costume='pahang_hill', pose='pahang_calm',
              item_f='pahang_staff', feet=0.03)                                         # Along
BEATS = {'land': pahang_land, 'people': pahang_people, 'food': pahang_food}
ICONS = {'food': icon_food_hill_greens, 'item': icon_item_terendak}
