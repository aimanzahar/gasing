"""Negeri Sembilan: Minang horned roofs among the hills, a musyawarah under the
balai, rendang simmering in the kawah, Mak Cik Ramlah with her woven Adat sash."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props: Minangkabau architecture
# =====================================================================

def gonjong(cx, y, w, h, sag=0.6, horn=0.8):
    """Minang saddle roof, side-on: ridge and eaves sag in the middle and sweep
    up at both ends, tapering into slender buffalo-horn tips (gonjong). y is the
    eave at the middle, w the half-width at the eaves, h the thatch depth there,
    sag the rise of the roof ends, horn the length of the tips."""
    ridge = [(cx + w * 0.97 * u, y + h + sag * abs(u) ** 3.2) for u in (-1 + 2 * i / 24 for i in range(25))]
    eave = [(cx + w * u, y + (sag + 0.6 * h) * abs(u) ** 5) for u in (1 - 2 * i / 24 for i in range(25))]
    r, e = ridge[-1], eave[0]
    tip = (cx + w + 0.3 * horn, r[1] + horn)
    right = _open([r, (r[0] + 0.1 * horn, r[1] + 0.5 * horn), tip], 5)[1:] +         _open([tip, (e[0] + 0.3 * horn, e[1] + 0.55 * horn), e], 5)[1:-1]
    left = [(2 * cx - px, py) for px, py in reversed(right)]
    return ridge + right + eave + left

def rumah_gadang(cv, x, y, s=1.0, layer='mid', flip=False, seed=1):
    """Rumah gadang: flared carved walls on stilts, a long horned roof and two
    lower horned anjung at the ends, a stair to the door in the middle."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    cv.add([P(ribbon([(px, 0.0), (px * 1.02, 1.05)], 0.05)) for px in (-1.55, -0.95, -0.35, 0.35, 0.95, 1.55)] +
           [P(rect(-1.75, 0.98, 1.75, 1.12))], 'solid', layer)
    wall = [(-1.62, 1.1), (1.62, 1.1), (1.95, 2.42), (-1.95, 2.42)]
    wins = [rect(-1.45 + 0.62 * i, 1.45, -1.13 + 0.62 * i, 2.08) for i in range(5)]
    cv.add_eo([P(wall)] + [P(wn) for wn in wins], 'flower', layer)
    cv.add([P(rect(-2.0, 2.36, 2.0, 2.48))], 'solid', layer)
    for sx in (-1, 1):                                  # anjung wings, lower, with their own horns
        cv.add([P(gonjong(sx * 2.25, 1.95, 0.75, 0.3, sag=0.5, horn=1.05))], 'scales', layer)
        cv.add_eo([P(rect(sx * 2.25 - 0.55, 1.1, sx * 2.25 + 0.55, 1.98)), P(rect(sx * 2.25 - 0.25, 1.35, sx * 2.25 + 0.25, 1.8))],
                  'grid', layer)
        cv.add([P(ribbon([(sx * 2.25 + dx, 0.0), (sx * 2.25 + dx, 1.12)], 0.045)) for dx in (-0.45, 0.45)], 'solid', layer)
    cv.add([P(gonjong(0.0, 2.42, 2.25, 0.55, sag=0.9, horn=1.3))], 'scales', layer)
    cv.add([P(ribbon([(-0.3, 1.05), (-0.55, 0.0)], 0.035)), P(ribbon([(0.3, 1.05), (0.05, 0.0)], 0.035))] +
           [P(ribbon([(-0.3 - 0.25 * t, 1.05 - t), (0.3 - 0.25 * t, 1.05 - t)], 0.025)) for t in (0.25, 0.5, 0.75)],
           'solid', layer)

def rangkiang(cv, x, y, s=1.0, layer='mid', flip=False):
    """Rangkiang rice barn: short stilts, a body flaring out to the roof, a high
    hatch, a horned roof."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    cv.add([P(ribbon([(px, 0.0), (px * 0.9, 0.55)], 0.05)) for px in (-0.45, 0.45)] + [P(rect(-0.6, 0.5, 0.6, 0.62))],
           'solid', layer)
    cv.add_eo([P([(-0.5, 0.6), (0.5, 0.6), (0.8, 2.1), (-0.8, 2.1)]), P(rect(-0.18, 1.45, 0.18, 1.85))], 'flower', layer)
    cv.add([P(gonjong(0.0, 2.05, 0.95, 0.36, sag=0.5, horn=0.95))], 'scales', layer)
    cv.add([P(ribbon([(-0.75, 0.0), (-0.2, 1.4)], 0.025))], 'solid', layer)   # notched log ladder

def istana(cv, x, y, s=1.0, layer='back'):
    """Istana Lama Seri Menanti: a tall timber palace, tiered roofs and a tower."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P(rect(-2.2, 0.0, 2.2, 1.6)), P(rect(-1.4, 1.5, 1.4, 2.6)), P(rect(-0.5, 2.5, 0.5, 4.0))], 'edge', layer)
    for yy, w in ((1.5, 2.6), (2.5, 1.75), (3.9, 0.85)):
        cv.add([P([(-w, yy), (w, yy), (w * 0.6, yy + 0.7), (-w * 0.6, yy + 0.7)])], 'edge', layer)
    cv.add([P([(-0.25, 4.6), (0.25, 4.6), (0.0, 5.2)])], 'edge', layer)

def balai(cv, x0, x1, y, h, layer='mid'):
    """Balai adat: an open pavilion, carved posts under a horned roof."""
    cx, w = (x0 + x1) / 2, (x1 - x0) / 2
    posts = [ribbon([(px, y), (px, y + h)], 0.07, 0.06) for px in (x0 + 0.2, x1 - 0.2)]
    cv.add(posts + [rect(x0 - 0.1, y + h - 0.05, x1 + 0.1, y + h + 0.12)], 'edge', layer)
    cv.carve([ellipse(px, y + h * fr, 0.03, 0.06) for px in (x0 + 0.2, x1 - 0.2) for fr in (0.3, 0.5, 0.7)], layer)
    cv.add([gonjong(cx, y + h + 0.1, w + 0.45, 0.85, sag=0.55, horn=0.95)], 'scales', layer)
    cv.add([ribbon([(x0 + 0.5 + i * (2 * w - 1.0) / 8, y + h + 0.12), (x0 + 0.5 + i * (2 * w - 1.0) / 8, y + h - 0.25)], 0.02)
            for i in range(9)], 'solid', layer)                                 # fringe of carved pendants

# =====================================================================
# props: kitchen
# =====================================================================

def kawah(cv, cx, y, w, layer='mid', heap=True, seed=1):
    """Kawah: wide shallow iron cauldron with ring handles, heaped with dark
    rendang (meat lumps in thick gravy). Returns the rim height."""
    rnd = random.Random(seed)
    h = w * 0.3
    left = _open([(-0.52 * w, h), (-0.5 * w, h * 0.8), (-0.42 * w, h * 0.4), (-0.25 * w, h * 0.1), (0.0, 0.0)], 5)[:-1]
    body = xf(mirror_pts(left), cx, y)
    lumps = []
    if heap:
        lumps.append(xf(_open([(-0.44 * w, h * 0.95), (-0.3 * w, h * 1.12), (0.0, h * 1.2), (0.3 * w, h * 1.12),
                               (0.44 * w, h * 0.95)], 5), cx, y))
        for i in range(9):
            lx = (-0.36 + 0.09 * i) * w + rnd.uniform(-0.02, 0.02) * w
            ly = h * (1.1 + 0.08 * math.sin(math.pi * (i + 0.5) / 9)) + rnd.uniform(0, 0.04) * w
            lumps.append(ellipse(cx + lx, y + ly, 0.05 * w * rnd.uniform(0.8, 1.2), 0.035 * w, rot=rnd.uniform(-30, 30), n=16))
        cv.add(lumps, 'edge', layer)
        cv.carve([ellipse(cx + (-0.3 + 0.12 * i) * w, y + h * 1.06 + 0.012 * w * (i % 2), 0.012 * w, 0.008 * w, n=10)
                  for i in range(6)], layer)
    pid = cv.add([body, xf(rect(-0.54 * w, h * 0.94, 0.54 * w, h * 1.04), cx, y)], 'lace', layer)
    cv.add([xf(ribbon(arc_pts(sx * 0.55 * w, h * 1.02, 0.035 * w, 0, 360, 18, ry=0.05 * w), 0.008 * w), cx, y)
            for sx in (-1, 1)], 'solid', layer, pid=pid)
    return y + h

def tungku(cv, cx, y, w, layer='mid', seed=1):
    """Tungku: two rough hearth stones, firewood pushed in from both sides and
    tall flames licking up between them."""
    rnd = random.Random(seed)
    stones = []
    for sx in (-1, 1):
        ctrl = [(sx * (0.33 + 0.15 * math.cos(a)) * w + rnd.uniform(-0.015, 0.015) * w,
                 (0.07 + 0.09 * math.sin(a)) * w + rnd.uniform(-0.012, 0.012) * w) for a in (TAU * k / 7 for k in range(7))]
        stones.append(xf(catmull(ctrl, True, 5), cx, max(y, y)))
    stones = [[(px, max(py, y)) for px, py in st] for st in stones]
    logs = [ribbon([(cx - 0.75 * w + 0.06 * w * i, y + 0.03 * w + 0.025 * w * i), (cx - 0.05 * w, y + 0.06 * w + 0.01 * w * i)],
                   0.028 * w, 0.024 * w) for i in range(2)]
    logs += [ribbon([(cx + 0.75 * w - 0.06 * w * i, y + 0.03 * w + 0.025 * w * i), (cx + 0.05 * w, y + 0.06 * w + 0.01 * w * i)],
                    0.028 * w, 0.024 * w) for i in range(2)]
    cv.add(logs, 'edge', layer)
    cv.carve([ellipse(cx + sx * (0.75 - 0.06 * i) * w, y + (0.03 + 0.025 * i) * w, 0.012 * w, 0.016 * w, n=10)
              for sx in (-1, 1) for i in range(2)], layer)
    cv.add(flame(cx, y + 0.04 * w, 0.3 * w, 7, seed), 'solid', layer)
    cv.add(stones, 'dots', layer)

def coconut(cv, x, y, s, layer='mid', half=False):
    if half:
        cv.add([xf([(-0.3, 0.3)] + arc_pts(0, 0.3, 0.3, 180, 360, 20)[1:-1] + [(0.3, 0.3)], x, y, s=s)], 'edge', layer)
        cv.carve([xf(ribbon(arc_pts(0, 0.3, 0.22, 200, 340, 14), 0.02), x, y, s=s)], layer)
    else:
        cv.add([ellipse(x, y + 0.3 * s, 0.32 * s, 0.3 * s)], 'edge', layer)
        cv.carve([ellipse(x + (i - 1) * 0.08 * s, y + 0.42 * s, 0.025 * s, n=10) for i in range(3)], layer)

def lengkuas(cv, x, y, s, layer='mid'):
    """Galangal and turmeric knobs with a turmeric leaf."""
    polys = [ellipse(x + dx * s, y + 0.08 * s + dy * s, 0.13 * s, 0.07 * s, rot=r) for dx, dy, r in
             ((0, 0, 0), (0.18, 0.06, 30), (-0.16, 0.05, -25), (0.05, 0.13, 70))]
    polys.append(leaf(x - 0.1 * s, y + 0.15 * s, 105, 0.9 * s, 0.12 * s, bend=0.1 * s))
    cv.add(polys, 'edge', layer)

def chili_pile(cv, x, y, s, layer='mid', seed=1):
    """A heap of cili api on the tray: curved pods stacked, stalks up."""
    rnd = random.Random(seed)
    polys = []
    for row, n in enumerate((4, 3, 2)):
        for i in range(n):
            bx = x + (i - (n - 1) / 2) * 0.36 * s + rnd.uniform(-0.04, 0.04) * s
            by = y + (0.06 + 0.13 * row) * s
            fl = (i + row) % 2
            polys.append(leaf(bx + (0.2 if fl else -0.2) * s, by, 180 if fl else 0, 0.42 * s, 0.055 * s,
                              bend=0.05 * s * (1 if fl else -1), wide_at=0.25))
            polys.append(ribbon(_open([(bx + (0.2 if fl else -0.2) * s, by), (bx + (0.24 if fl else -0.24) * s, by + 0.06 * s),
                                       (bx + (0.22 if fl else -0.22) * s, by + 0.1 * s)]), 0.012 * s))
    cv.add(polys, 'edge', layer)

def shallots(cv, x, y, s, layer='mid', n=3):
    polys = []
    for i in range(n):
        bx = x + i * 0.22 * s
        polys += [ellipse(bx, y + 0.12 * s, 0.1 * s, 0.12 * s, n=18), leaf(bx, y + 0.22 * s, 90, 0.12 * s, 0.03 * s)]
    cv.add(polys, 'edge', layer)

# =====================================================================
# rig parts: Mak Cik Ramlah and the villagers
# =====================================================================

def _hat_tengkuluk():
    """Tengkuluk tanduk: the Minang head-cloth folded into two buffalo horns."""
    p = [(0.058, 0.898), (0.07, 0.925), (0.088, 0.948), (0.104, 0.975), (0.116, 1.022), (0.09, 0.99),
         (0.062, 0.968), (0.03, 0.957), (0.0, 0.953), (-0.03, 0.957), (-0.062, 0.968), (-0.09, 0.99), (-0.116, 1.022),
         (-0.106, 0.975), (-0.09, 0.948), (-0.076, 0.925), (-0.07, 0.88), (-0.07, 0.83), (-0.05, 0.805), (-0.03, 0.85),
         (-0.02, 0.89), (0.02, 0.895)]
    carves = [ribbon([(0.022 * i, 0.918 + 0.006 * abs(i)), (0.007 + 0.022 * i, 0.94 + 0.006 * abs(i))], 0.002)
              for i in range(-3, 4)]
    carves += [W.diamond(-0.05, 0.9, 0.018, 0.026)[0], W.diamond(-0.055, 0.855, 0.016, 0.022)[0]]
    return [p], 'lace', carves

def _hat_destar():
    """Destar of a Datuk: a stiff folded head-cloth with a tall peak at the back."""
    p = [(0.058, 0.902), (0.06, 0.94), (0.04, 0.975), (0.0, 0.99), (-0.035, 1.02), (-0.06, 1.085), (-0.07, 1.02),
         (-0.072, 0.95), (-0.062, 0.89), (0.0, 0.9)]
    return [p], 'lace', [ribbon([(-0.05, 0.94), (-0.055, 1.03)], 0.0022)]

def _sash_extra(spec):
    """Selempang tenun: a woven sash over the front shoulder down to the back hip."""
    path = _open([(0.055, 0.785), (0.02, 0.7), (-0.03, 0.6), (-0.06, 0.55)], 6)
    band = ribbon(path, 0.022, 0.02)
    tail = [(-0.075, 0.57), (-0.04, 0.545), (-0.06, 0.42), (-0.1, 0.43)]
    fringe = [ribbon([(-0.1 + 0.008 * i, 0.43), (-0.104 + 0.008 * i, 0.395)], 0.0018) for i in range(6)]
    carves = [W.diamond(0.04 - 0.024 * i, 0.758 - 0.05 * i, 0.016, 0.02)[0] for i in range(4)]
    carves += [W.diamond(-0.07, 0.5 - 0.03 * i, 0.014, 0.018)[0] for i in range(2)]
    return [([band, tail] + fringe, 'edge', carves)]

def _it_sash(g, ang, fig):
    """The folded Adat sash hanging from the hand: woven bands and a fringe."""
    x, y = g[0] + 0.004, g[1] + 0.012
    cloth = [(x - 0.03, y), (x + 0.03, y), (x + 0.034, y - 0.2), (x - 0.026, y - 0.2)]
    fringe = [ribbon([(x - 0.022 + 0.0095 * i, y - 0.2), (x - 0.024 + 0.0095 * i, y - 0.24)], 0.0022) for i in range(6)]
    carves = [W.diamond(x + 0.002, y - 0.045 - 0.05 * i, 0.026, 0.03)[0] for i in range(3)]
    carves += [ribbon([(x - 0.024, y - 0.02 - 0.05 * i), (x + 0.026, y - 0.02 - 0.05 * i)], 0.002) for i in range(4)]
    return [cloth] + fringe, 'solid', carves

def _it_paddle(g, ang, fig):
    """Pengacau: the long wooden paddle that turns the rendang, blade down."""
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    top = (g[0] - 0.12 * d[0], g[1] - 0.12 * d[1])
    end = (g[0] + 0.42 * d[0], g[1] + 0.42 * d[1])
    blade = xf(ellipse(0, 0, 0.05, 0.022), end[0] + 0.03 * d[0], end[1] + 0.03 * d[1], rot=ang)
    return [ribbon([top, end], 0.0065), blade], 'solid', []

def _it_stirrer(g, ang, fig):
    """The paddle held two-handed, its blade driven down into the pot."""
    a = math.radians(-40)
    d = (math.cos(a), math.sin(a))
    top = (g[0] - 0.2 * d[0], g[1] - 0.2 * d[1])
    end = (g[0] + 0.6 * d[0], g[1] + 0.6 * d[1])
    blade = xf(ellipse(0, 0, 0.06, 0.024), end[0] + 0.04 * d[0], end[1] + 0.04 * d[1], rot=-40)
    return [ribbon([top, end], 0.0075), blade], 'solid', []

W.register(W.HATS, 'nsembilan_tengkuluk', _hat_tengkuluk)
W.register(W.HATS, 'nsembilan_destar', _hat_destar)
W.register(W.COSTUMES, 'nsembilan_kurung', dict(W.COSTUMES['kurung'], extra=_sash_extra,
                                                 cls={'top': 'flower', 'lower': 'scales', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.ITEMS2, 'nsembilan_sash', _it_sash)
W.register(W.ITEMS2, 'nsembilan_paddle', _it_stirrer)
W.register(W.POSES, 'nsembilan_mirror', {'f': (88, 30), 'b': (-38, -16), 'lean': -2, 'legs': 'stand', 'hf': 'open', 'hb': 'grip'})
W.register(W.POSES, 'nsembilan_stir', {'f': (95, 30), 'b': (80, 45), 'lean': 8, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'nsembilan_talk', {'f': (62, 52), 'b': (12, 40), 'lean': 4, 'legs': 'sit', 'hf': 'open', 'hb': 'open'})

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def nsembilan_land(cv):
    """Houses with curved, horn-like roofs stand among the hills."""
    hills(cv, -0.5, 21, G + 1.4, 1.5, seed=11, n=3)
    hills(cv, -0.5, 21, G + 0.7, 0.9, seed=12, n=5)
    istana(cv, 15.6, G + 2.2, 0.55)
    for x, sc, fl in ((8.6, 0.32, False), (19.2, 0.3, True), (12.6, 0.26, True)):
        rumah_gadang(cv, x, G + 1.75, sc, 'back', flip=fl)
    cloud(cv, 3.0, 7.0, 0.85, 'back', seed=13)
    cloud(cv, 15.4, 7.2, 0.7, 'back', flip=True, seed=14)
    birds(cv, 9.0, 6.7, 4, 0.55, seed=15, layer='back', flip=True)
    # mid: the great house on the left third, its rice barn, a smaller house beyond
    raintree(cv, 1.4, G + 0.6, 4.0, seed=16)
    rumah_gadang(cv, 5.4, G + 0.55, 0.95, seed=17)
    rangkiang(cv, 9.6, G + 0.55, 0.85)
    palm(cv, 11.4, G + 0.6, 3.4, lean=0.1, seed=18)
    palm(cv, 12.1, G + 0.6, 2.7, lean=-0.14, seed=19, fronds=8)
    rumah_gadang(cv, 15.9, G + 0.6, 0.62, flip=True, seed=20)
    banana(cv, 18.9, G + 0.6, 2.2, seed=21, layer='mid', flip=True)
    field(cv, 0.0, 20.5, G + 0.12, h=0.5, rows=2, seed=22)
    ground(cv, 'earth', seed=23)
    frame_edges(cv, seed=24, left='banana', right='none')

def nsembilan_people(cv):
    """Villagers gather under the balai to talk a matter through together."""
    hills(cv, -0.5, 21, G + 1.1, 1.3, seed=31, n=3)
    rumah_gadang(cv, 3.2, G + 0.9, 0.55, 'back', seed=32)
    rumah_gadang(cv, 17.6, G + 0.9, 0.5, 'back', flip=True, seed=33)
    cloud(cv, 10.2, 7.3, 0.7, 'back', seed=34)
    balai(cv, 6.3, 14.1, G, 3.55)
    # the bench they sit on, the betel tray between them
    seat = G + 0.38 * 3.2
    cv.add([rect(6.9, seat - 0.12, 13.5, seat), ribbon([(7.2, G), (7.2, seat)], 0.05), ribbon([(13.2, G), (13.2, seat)], 0.05)],
           'edge')
    cv.add([xf(mirror_pts(_open([(-0.55, 1.05), (-0.5, 0.95), (-0.18, 0.88), (-0.12, 0.55), (-0.2, 0.1), (-0.32, 0.0)], 4)),
               10.2, G)], 'lace')
    cv.add([rect(9.75, G + 1.05, 10.65, G + 1.45), [(9.7, G + 1.45), (10.7, G + 1.45), (10.55, G + 1.62), (9.85, G + 1.62)]],
           'grid')
    W.place_figure(cv, dict(head='old', beard='full', hat='nsembilan_destar', costume='baju', pose='nsembilan_talk',
                            rod_to=-0.25), 7.6, G, 3.2)
    W.place_figure(cv, dict(body='female', hat='nsembilan_tengkuluk', costume='nsembilan_kurung', pose='teach',
                            rod_to=-0.25), 4.6, G, 3.2)
    W.place_figure(cv, dict(head='refined', hat='songkok', costume='baju', pose='nsembilan_talk', rod_to=-0.25),
                   12.8, G, 3.2, flip=True)
    W.place_figure(cv, dict(head='young', hat='tanjak', costume='farmer', pose='gesture', rod_to=-0.25),
                   15.8, G, 3.2, flip=True)
    ground(cv, 'earth', seed=35)
    frame_edges(cv, seed=36, left='banana', right='banana')

def nsembilan_food(cv):
    """A pot of rendang simmers slowly over the fire, stirred without rest."""
    # back: a Minang kitchen wall, carved window, strings of chillies and onions
    cv.add_eo([rect(13.4, 2.4, 17.6, 6.4), rect(13.7, 2.7, 17.3, 6.1)], 'edge', 'back')
    cv.add([ribbon([(13.7 + 0.6 * i, 2.7), (13.7 + 0.6 * i, 6.1)], 0.03) for i in range(1, 6)], 'solid', 'back')
    for x in (2.0, 3.1, 18.6):
        cv.add([ribbon([(x, 8.3), (x, 6.2)], 0.02)] + [leaf(x + 0.04 * (k % 2), 6.3 - 0.28 * k, -90 + 30 * (-1) ** k, 0.35, 0.05)
                                                         for k in range(6)], 'solid', 'back')
    jar(cv, 1.8, G, 1.8, 'back')
    jar(cv, 4.6, G, 1.3, 'back')
    # hero: the kawah on its hearth at ~40% height, steam rising
    tungku(cv, 10.9, G, 4.2, seed=3)
    W.place_figure(cv, dict(body='female', hat='nsembilan_tengkuluk', costume='nsembilan_kurung', pose='nsembilan_stir',
                            item_f='nsembilan_paddle', rod_to=-0.25), 6.8, G, 3.5)
    rim = kawah(cv, 10.9, G + 0.42, 4.4, seed=4)
    for i, (dx, hh, cw) in enumerate(((-1.2, 2.0, False), (-0.15, 2.5, True), (0.9, 2.2, False), (1.8, 1.7, True))):
        steam(cv, 10.9 + dx, rim + 0.55, hh, cw=cw, seed=40 + i)
    for sx in (-1, 1):                                  # trays of spices, mirrored about the dish
        plate(cv, 10.9 + sx * 6.9, G, 2.3)
    coconut(cv, 3.5, G + 0.2, 1.3, half=True)
    coconut(cv, 4.6, G + 0.2, 1.1)
    chili_pile(cv, 16.7, G + 0.1, 1.3)
    shallots(cv, 17.9, G + 0.18, 1.3)
    lengkuas(cv, 1.6, G, 1.4)
    serai(cv, 19.3, G, 2.3)
    ground(cv, 'earth', seed=47)
    frame_edges(cv, seed=48, left='banana', right='banana')

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def icon_food_rendang(seed=1):
    """Rendang: dark caramelised beef chunks in a thick dry gravy flecked with
    kerisik, a twist of turmeric leaf and red chilli, in a deep brass bowl."""
    rnd = random.Random(seed)
    brass = _mat('Brass', (0.72, 0.5, 0.18), 0.3, metal=1.0)
    w, h = 2.2, 2.2 * BOWL_DEPTH
    outer = [(-x * w, y * h) for x, y in reversed(BOWL_PROFILE)]
    rim = outer[-1]
    inner = [(r - 0.05, z) for r, z in reversed(outer) if z > 0.2 * h]
    _lathe('Bowl', [(0.0, 0.0)] + outer + [(rim[0] - 0.025, rim[1] + 0.02)] + inner + [(0.0, inner[-1][1])], brass, 72)
    _torus('Rim', (0, 0, rim[1]), rim[0] - 0.01, 0.03, brass, seg=64)
    gravy = _mat('Gravy', (0.075, 0.028, 0.01), 0.75)
    _blob('Gravy', (0, 0, 0.8 * h), (0.98, 0.98, 0.16), (0, 0, 0), gravy, seg=32)
    beef = [_mat('Beef%d' % i, c, 0.75) for i, c in enumerate(((0.07, 0.025, 0.01), (0.13, 0.05, 0.018), (0.19, 0.075, 0.025)))]
    for i in range(16):
        a = TAU * i / 16 * 2.618 + rnd.uniform(-0.3, 0.3)
        r = 0.72 * math.sqrt((i + 0.5) / 16)
        sc = (rnd.uniform(0.17, 0.24), rnd.uniform(0.13, 0.18), rnd.uniform(0.1, 0.14))
        _blob('Beef%d' % i, (r * math.cos(a), r * math.sin(a), 0.93 * h + 0.18 * (1 - r) + rnd.uniform(0, 0.04)), sc,
              (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, TAU)), beef[i % 3], seg=8)
        _blob('BeefB%d' % i, (r * math.cos(a) + 0.07, r * math.sin(a) - 0.05, 0.97 * h + 0.18 * (1 - r)),
              (sc[0] * 0.6, sc[1] * 0.7, sc[2] * 0.8), (0.4, -0.3, rnd.uniform(0, TAU)), beef[(i + 1) % 3], seg=7)
    fleck = _mat('Kerisik', (0.42, 0.22, 0.08), 0.8)
    for i in range(70):
        a, r = rnd.uniform(0, TAU), rnd.uniform(0.0, 0.85)
        _blob('Fleck%d' % i, (r * math.cos(a), r * math.sin(a), 0.98 * h + 0.2 * (1 - r)), (0.03, 0.025, 0.015), (0, 0, a),
              fleck, seg=5)
    leafm = _mat('Leaf', (0.2, 0.45, 0.08), 0.45)
    for k in range(5):
        a = 0.6 + 0.45 * k
        _box('Leaf%d' % k, (0.08 * math.cos(a) - 0.1, 0.08 * math.sin(a), 1.25 * h + 0.03 * k), (0.42, 0.03, 0.01),
             (0.15, 0.1, a), leafm)
    chili = _mat('Chilli', (0.82, 0.05, 0.03), 0.3)
    for k in range(4):
        _lathe('Chili%d' % k, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.015), (0.0, 0.015)], chili, 16).location =             (0.22 + 0.11 * k, -0.25 + 0.06 * k, 1.24 * h + 0.01 * k)
    return (0, -4.9, 4.3), (0, 0, 0.45)

def icon_item_sash():
    """The woven Adat sash: a folded length of red tenun shot with gold, pucuk
    rebung borders at the ends, the loose end draped forward with its fringe."""
    red = _mat('Tenun', (0.36, 0.025, 0.035), 0.7)
    gold = _mat('Gold', (0.88, 0.64, 0.22), 0.32, metal=0.85)
    L, Wd = 2.3, 0.82
    for k in range(3):                                  # three soft folded layers
        z = 0.07 * k
        _box('Fold%d' % k, (0.0, -0.015 * k, 0.04 + z), (L - 0.1 * k, Wd, 0.05), (0, 0, 0), red)
        _tube('Edge%d' % k, [(-(L - 0.1 * k) / 2, -Wd / 2 - 0.015 * k, 0.04 + z), (-(L - 0.1 * k) / 2, Wd / 2 - 0.015 * k, 0.04 + z)],
              0.035, red)
    zt = 0.04 + 0.14 + 0.026
    for i in range(9):                                  # gold songket diamonds over the top fold
        for j in range(3):
            _box('Dia%d_%d' % (i, j), (-0.9 + 0.225 * i, -0.24 + 0.24 * j, zt), (0.1, 0.1, 0.008), (0, 0, math.pi / 4), gold)
    for sy in (-1, 1):                                  # gold selvedge stripes
        _box('Stripe%d' % sy, (0.0, sy * (Wd / 2 - 0.06), zt), (L - 0.3, 0.035, 0.008), (0, 0, 0), gold)
    end = [(0.95 + 0.55 * t, -0.15 - 0.95 * t, 0.2 - 0.18 * t + 0.06 * math.sin(t * 5)) for t in (i / 10 for i in range(11))]
    for k in range(9):                                  # the loose end: a ribbon of strands, a gold band near the tip
        _tube('End%d' % k, [(x + 0.045 * (k - 4), y + 0.02 * (k - 4), z) for x, y, z in end], 0.03,
              gold if k in (0, 8) else red)
    tip = end[-1]
    for k in range(9):
        _tube('Fringe%d' % k, [(tip[0] + 0.045 * (k - 4), tip[1] + 0.02 * (k - 4), tip[2]),
                               (tip[0] + 0.045 * (k - 4) + 0.04, tip[1] + 0.02 * (k - 4) - 0.22, tip[2] - 0.03)], 0.012, gold)
    for k in range(14):                                 # fringe on the folded end
        y = -Wd / 2 + 0.06 + k * (Wd - 0.12) / 13
        _tube('FrA%d' % k, [(-L / 2 - 0.03, y, 0.05), (-L / 2 - 0.2, y - 0.02, 0.0)], 0.011, gold)
    return (0.5, -5.7, 3.7), (0.38, -0.32, 0.0)

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

PUPPET = dict(body='female', hat='nsembilan_tengkuluk', costume='nsembilan_kurung', pose='nsembilan_mirror',
              item_b='nsembilan_sash', feet=0.03)                                      # Mak Cik Ramlah
BEATS = {'land': nsembilan_land, 'people': nsembilan_people, 'food': nsembilan_food}
ICONS = {'food': icon_food_rendang, 'item': icon_item_sash}
