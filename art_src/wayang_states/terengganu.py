"""Terengganu: Pak Ngah's coast -- boats home at dusk while the seine is hauled
in, a weaver at the songket loom, keropok lekor in the wok, and the old fisherman
with his cast net and paddle."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props
# =====================================================================

def sunset(cv, cx, cy, r, layer='mid'):
    """Matahari terbenam: half a carved sun on the horizon, flame rays above it,
    and its glitter breaking up on the water below."""
    fl = []
    for i in range(11):
        a = 180 * (i + 0.5) / 11
        long = i % 2 == 0
        fl.append(leaf(cx + r * 0.9 * math.cos(math.radians(a)), cy + r * 0.9 * math.sin(math.radians(a)),
                       a + (7 if long else -7), r * (0.72 if long else 0.42), r * (0.12 if long else 0.09),
                       bend=r * 0.07 * (1 if long else -1)))
    cv.add(fl, 'solid', layer)
    cv.add([arc_pts(cx, cy, r, 180, 0, 40)], 'lace', layer)
    cv.carve([ribbon(arc_pts(cx, cy, r * 0.58, 175, 5, 30), r * 0.025)] +
             [leaf(cx, cy + 0.03, a, r * 0.42, r * 0.065) for a in (25, 55, 90, 125, 155)], layer)
    dashes = []
    for k in range(5):
        y = cy - 0.2 - k * 0.2
        w = r * (1.0 - 0.15 * k)
        for j in (-1, 1):
            x0 = cx + j * (0.12 + 0.08 * k)
            dashes.append(ribbon([(x0, y), (cx + j * w, y)], 0.028 - 0.003 * k, 0.008))
    cv.add(dashes, 'solid', layer)

def perahu(cv, x, y, s=1.0, layer='mid', flip=False, sail='set'):
    """Perahu besar of the Terengganu coast, broadside, bow to +x: a long low hull
    whose sheer sweeps up into the carved bangau figurehead at the bow and the
    okok at the stern, painted bands, and a canted tanja sail ('set'), a sail
    furled along its yard ('furled') or bare (None). Returns the hull's part id."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    if sail == 'set':
        cv.add([P(ribbon([(0.05, 0.35), (0.22, 3.75)], 0.05, 0.03))], 'solid', layer)
        sl = (_open([(-1.25, 1.05), (0.0, 1.1), (1.25, 1.3)], 4) +
              _open([(1.25, 1.3), (1.32, 2.4), (0.75, 3.55)], 4)[1:] +
              _open([(0.75, 3.55), (-0.4, 3.33), (-1.55, 3.0)], 4)[1:] +
              _open([(-1.55, 3.0), (-1.5, 2.0), (-1.25, 1.05)], 4)[1:-1])
        cv.add([P(sl)], 'dots', layer)
        cv.add([P(ribbon([(-1.4, 1.02), (1.38, 1.33)], 0.04)), P(ribbon([(-1.7, 2.97), (0.9, 3.61)], 0.04)),
                P(ribbon([(1.3, 1.32), (1.9, 0.72)], 0.012)), P(ribbon([(0.22, 3.75), (2.05, 1.15)], 0.01)),
                P(leaf(0.22, 3.72, 160, 0.55, 0.06, bend=-0.08))], 'solid', layer)      # pennant
        cv.carve([P(ribbon([(-1.42 + 0.03 * k, 1.48 + 0.4 * k), (1.22 - 0.1 * k, 1.68 + 0.42 * k)], 0.012))
                  for k in range(4)], layer)
    elif sail == 'furled':
        bundle = _open([(-1.2, 1.0), (-0.4, 1.22), (0.4, 1.42), (0.95, 1.58)])
        cv.add([P(ribbon([(0.05, 0.35), (0.12, 2.3)], 0.05, 0.03)), P(ribbon(bundle, 0.11, 0.06)),
                P(ribbon([(0.95, 1.58), (1.1, 1.64)], 0.025)), P(ribbon([(0.12, 2.3), (0.95, 1.6)], 0.012))], 'edge', layer)
        cv.carve([P(ribbon([(bx - 0.06, by + 0.1), (bx + 0.06, by - 0.1)], 0.012)) for bx, by in bundle[3:-3:4]], layer)
    sheer = _open([(-2.0, 0.92), (-1.75, 0.66), (-1.1, 0.52), (0.0, 0.48), (1.1, 0.52), (1.75, 0.68), (2.05, 0.98)], 5)
    keel = _open([(1.98, 0.6), (1.65, 0.24), (0.9, 0.05), (0.0, 0.0), (-0.9, 0.05), (-1.6, 0.22), (-1.92, 0.55)], 5)
    pid = cv.add([P(sheer + keel)], 'lace', layer)
    bow = [ribbon(_open([(1.88, 0.66), (2.06, 1.02), (2.1, 1.38), (2.24, 1.66)]), 0.075, 0.045),
           ellipse(2.3, 1.72, 0.1, 0.08),
           leaf(2.36, 1.74, -8, 0.46, 0.055),                                        # the bangau's beak
           leaf(2.22, 1.8, 120, 0.42, 0.05, bend=0.1), leaf(2.2, 1.78, 150, 0.36, 0.04, bend=0.08),   # crest plumes
           ribbon(_open([(2.12, 1.3), (2.32, 1.22), (2.4, 1.05)]), 0.02, 0.008)]   # hanging tassel
    stern = [ribbon(_open([(-1.88, 0.66), (-2.06, 0.98), (-2.16, 1.28)]), 0.065, 0.04),
             scroll(-2.02, 1.4, 0.14, 0.04, 1.2, a0=200, cw=True, tail=[(-2.16, 1.26), (-2.17, 1.36)])]
    cv.add([P(p) for p in bow + stern], 'edge', layer, pid=pid)
    cuts = [P(ribbon(_open([(-1.72, 0.62), (-1.0, 0.41), (0.0, 0.37), (1.0, 0.41), (1.72, 0.64)]), 0.013))]
    cuts += [P(W.diamond(-1.2 + 0.3 * i, 0.24 + 0.012 * abs(i - 4), 0.13, 0.1)[0]) for i in range(9)]
    cuts.append(P(W.circle(2.3, 1.73, 0.025, 10)[0]))                             # the bird's eye
    cv.carve(cuts, layer)
    return pid

def rhu(cv, x, y, h, lean=0.0, seed=1, layer='mid'):
    """Pokok rhu (casuarina): a slim kinked trunk, upswept limbs, and weeping
    tufts of needles hanging off every limb like grey-green hair."""
    rnd = random.Random(seed)
    f = noise1(seed, 4)
    trunk = [(x + lean * h * t + 0.06 * h * f(t) * t, y + h * t) for t in (i / 10 for i in range(11))]
    cv.add([ribbon(trunk, 0.035 * h ** 0.5, 0.012 * h ** 0.5)], 'edge', layer)
    limbs, tufts = [], []
    for i in range(9):
        t = 0.32 + 0.075 * i
        bx, by = trunk[int(t * 10)][0], y + h * t
        side = 1 if i % 2 else -1
        L = h * (0.3 - 0.22 * (t - 0.32)) * rnd.uniform(0.8, 1.15)
        tip = (bx + side * L, by + L * 0.35)
        limbs.append(ribbon(_open([(bx, by), (bx + side * L * 0.5, by + L * 0.28), tip]), 0.012 * h ** 0.5, 0.004))
        for k in range(24):
            u = k / 23
            px = bx + side * L * (0.2 + 0.8 * u)
            py = by + L * 0.35 * (0.2 + 0.8 * u) - 0.02
            limbs.append(leaf(px, py, -90 + side * rnd.uniform(-5, 30), h * rnd.uniform(0.06, 0.15) * (1.2 - 0.5 * u),
                              0.006 * h ** 0.5, bend=side * 0.012 * h))
    cv.add(limbs, 'solid', layer)
    top = trunk[-1]
    cv.add([leaf(top[0], top[1], 90 + rnd.uniform(-40, 40), h * rnd.uniform(0.05, 0.1), 0.007 * h ** 0.5) for _ in range(12)],
           'solid', layer)

def para(cv, x, y, s=1.0, layer='mid'):
    """Fish-drying rack: two trestles, a pole, and a row of split fish hung to dry."""
    P = lambda pts: xf(pts, x, y, s=s)
    legs = []
    for px in (-1.0, 1.0):
        legs += [ribbon([(px - 0.25, 0.0), (px, 1.3)], 0.03), ribbon([(px + 0.25, 0.0), (px, 1.3)], 0.03)]
    legs.append(ribbon([(-1.2, 1.25), (1.2, 1.25)], 0.035))
    cv.add([P(l) for l in legs], 'solid', layer)
    for i in range(7):
        fish(cv, x + (-0.84 + 0.28 * i) * s, y + 0.92 * s, 0.38 * s, ang=-90 + (i % 2) * 8, layer=layer)

def rope_line(pts, w=0.022):
    return ribbon(_open(pts, 8), w)

# ---------------------------------------------------------------------
# the loom, the thread wheel and the house behind them

def kek(cv, x, y, s=1.0, layer='mid'):
    """Kek songket, side-on, weaver's end at x: posts and an overhead beam, the
    reed hung from the beam, the heddles and the comb of songket pattern sticks,
    treadles under the warp, the warp running out to the back beam."""
    P = lambda pts: xf(pts, x, y, s=s)
    frame = [rect(0.86, 0.0, 0.98, 1.95), rect(4.0, 0.0, 4.12, 1.95), rect(0.72, 1.92, 4.3, 2.04),
             rect(0.82, 0.85, 1.02, 0.95), rect(3.92, 0.92, 4.2, 1.02),
             ribbon([(0.92, 0.0), (0.92, 0.5), (1.3, 0.0)], 0.02), ribbon([(4.06, 0.0), (4.06, 0.5), (3.7, 0.0)], 0.02)]
    cv.add([P(p) for p in frame], 'edge', layer)
    warp = [ribbon([(1.0, 0.94 + 0.012 * k), (3.95, 1.0 + 0.02 * k)], 0.006) for k in range(4)]
    cloth = [[(0.95, 0.88), (1.36, 0.9), (1.36, 1.02), (0.95, 1.0)], ellipse(0.94, 0.9, 0.09, 0.08)]   # woven length + roll
    cv.add([P(p) for p in warp + cloth], 'solid', layer)
    reed = [rect(1.32, 0.72, 1.44, 1.38), rect(1.26, 1.35, 1.5, 1.42), rect(1.26, 0.7, 1.5, 0.76),
            ribbon([(1.3, 1.42), (1.25, 1.92)], 0.008), ribbon([(1.46, 1.42), (1.5, 1.92)], 0.008)]
    heddles = []
    for hx in (1.95, 2.3):
        heddles += [rect(hx - 0.03, 0.62, hx + 0.03, 1.28), ribbon([(hx, 1.28), (hx, 1.92)], 0.008),
                    ribbon([(hx, 0.62), (hx + 0.05, 0.12)], 0.008)]
    heddles += [rect(1.75, 0.08, 2.55, 0.13), ellipse(1.78, 0.1, 0.04, 0.04)]      # treadle
    comb = [ribbon([(2.75 + 0.1 * k, 1.04 + 0.002 * k), (2.75 + 0.1 * k, 1.5 + 0.04 * (k % 3))], 0.012) for k in range(11)]
    comb += [rect(2.68, 1.47, 3.85, 1.52), ribbon([(2.7, 1.52), (2.7, 1.92)], 0.008), ribbon([(3.8, 1.52), (3.8, 1.92)], 0.008)]
    spools = [ellipse(1.7 + 0.32 * k, 2.15, 0.08, 0.1) for k in range(5)] + \
             [ribbon([(1.7 + 0.32 * k, 2.04), (1.7 + 0.32 * k, 2.28)], 0.012) for k in range(5)]
    cv.add([P(p) for p in reed + heddles + comb + spools], 'solid', layer)
    cv.carve([P(rect(1.35, 0.8, 1.41, 1.3))] + [P(ellipse(1.7 + 0.32 * k, 2.15, 0.03, 0.05)) for k in range(5)], layer)

def rahat(cv, x, y, s=1.0, layer='mid'):
    """Thread wheel on its stand, a crank on the hub and the bobbin spindle."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P(p) for p in (ribbon([(-0.5, 0.0), (0.0, 0.9)], 0.035), ribbon([(0.5, 0.0), (0.0, 0.9)], 0.035),
                           rect(-0.9, 0.0, 0.9, 0.1), rect(-1.65, 0.0, -1.0, 0.1),
                           ribbon([(-1.5, 0.1), (-1.5, 0.42)], 0.03), ribbon([(-1.1, 0.1), (-1.1, 0.42)], 0.03),
                           ellipse(-1.3, 0.42, 0.17, 0.09), ribbon([(-1.62, 0.42), (-0.98, 0.42)], 0.012),
                           ribbon([(-1.25, 0.5), (-0.2, 1.62)], 0.006), ribbon([(-1.25, 0.34), (0.1, 0.25)], 0.006))],
           'solid', layer)
    wheel(cv, x, y + 0.92 * s, 0.72 * s, 10, layer, knobs=False, rim=0.08)
    cv.add([P(ribbon([(0.0, 0.92), (-0.38, 1.15)], 0.028)), P(ribbon([(-0.38, 1.15), (-0.42, 1.0)], 0.022))], 'solid', layer)

def songket_hang(cv, x, y_top, w, h, layer='mid', seed=1):
    """A length of songket hung over a rail: gold diamonds on the body, a
    pucuk rebung (bamboo-shoot) border at the foot, fringe below."""
    pid = cv.add([rect(x - w / 2, y_top - h, x + w / 2, y_top)], 'flower', layer)
    fr = [ribbon([(x - w / 2 + 0.05 + k * (w - 0.1) / 9, y_top - h), (x - w / 2 + 0.05 + k * (w - 0.1) / 9, y_top - h - 0.18)],
                 0.012, 0.006) for k in range(10)]
    cv.add(fr, 'solid', layer, pid=pid)
    cuts = []
    n = max(2, int(w / 0.28))
    for k in range(n):
        cx = x - w / 2 + (k + 0.5) * w / n
        cuts.append([(cx - w / n * 0.42, y_top - h + 0.06), (cx, y_top - h + 0.42), (cx + w / n * 0.42, y_top - h + 0.06)])
    cuts.append(rect(x - w / 2 + 0.04, y_top - h + 0.48, x + w / 2 - 0.04, y_top - h + 0.51))
    cv.carve(cuts, layer)

def rumah_dalam(cv, seed=1):
    """Blurred house interior: posts, a carved eave panel each side (the top
    centre stays open), a lattice window and songket hung on a line."""
    for px in (0.6, 7.6, 13.3, 19.8):
        cv.add([rect(px - 0.12, G, px + 0.12, 7.4)], 'solid', 'back')
    for x0, x1 in ((-0.2, 6.6), (14.0, 20.7)):
        cv.add_eo([rect(x0, 6.55, x1, 7.35)] + [ellipse(x0 + 0.55 + 1.0 * k, 6.95, 0.32, 0.22) for k in range(int((x1 - x0) / 1.0))],
                  'edge', 'back')
    cv.add_eo([rect(9.2, 2.4, 12.0, 5.2), rect(9.45, 2.65, 11.75, 4.95)], 'edge', 'back')
    cv.add([ribbon([(9.45 + 0.46 * i, 2.65), (9.45 + 0.46 * i, 4.95)], 0.025) for i in range(1, 5)], 'solid', 'back')
    cv.add([ribbon(_open([(13.6, 6.1), (16.5, 5.9), (19.6, 6.1)]), 0.02)], 'solid', 'back')
    for i, (x, w, h) in enumerate(((14.4, 1.0, 2.3), (15.7, 1.1, 2.6), (17.1, 1.0, 2.2), (18.5, 1.2, 2.5))):
        cv.add([rect(x - w / 2, 6.0 - h, x + w / 2, 6.0)], 'solid', 'back')

# ---------------------------------------------------------------------
# the stall and the wok

def kuali(cv, cx, y, w, layer='mid', seed=1):
    """Kuali side-on on its hearth: a wide shallow wok with ear handles, the
    oil just under the rim, lekor rolls jostling in it and bubbles rising."""
    rnd = random.Random(seed)
    h = w * 0.24
    left = _open([(-0.5 * w, h), (-0.47 * w, 0.72 * h), (-0.38 * w, 0.38 * h), (-0.22 * w, 0.1 * h), (0.0, 0.0)], 6)[:-1]
    body = xf(mirror_pts(left), cx, y)
    rolls = []
    for i in range(6):                                  # lekor rolls bobbing in the oil
        rx = cx + (-0.33 + 0.13 * i) * w + rnd.uniform(-0.015, 0.015) * w
        ry = y + h * (1.0 + 0.12 * (i % 2))
        a = (28 if i % 2 else -24) + rnd.uniform(-8, 8)
        L = w * rnd.uniform(0.07, 0.09)
        d = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        r = 0.026 * w
        rolls.append([ribbon([(rx - d[0] * L, ry - d[1] * L), (rx + d[0] * L, ry + d[1] * L)], r)] +
                     [ellipse(rx + sg * d[0] * L, ry + sg * d[1] * L, r, n=16) for sg in (-1, 1)])
    ears = [xf(ribbon(arc_pts(sx * 0.53 * w, 0.9 * h, 0.06 * w, 90 - 90 * sx, 270 - 90 * sx, 10), 0.012 * w), cx, y)
            for sx in (-1, 1)]
    for roll in rolls:
        cv.add(roll, 'edge', layer)
    pid = cv.add([body] + ears, 'dots', layer)
    bubbles = [W.circle(cx + rnd.uniform(-0.44, 0.44) * w, y + h * rnd.uniform(1.05, 1.5), 0.012 * w * rnd.uniform(0.7, 1.3), 12)[0]
               for _ in range(16)]
    cv.add(bubbles, 'solid', layer)
    cv.carve([ribbon(_open([(cx - 0.47 * w, y + h * 0.78), (cx, y + h * 0.74), (cx + 0.47 * w, y + h * 0.78)]), 0.006 * w)] +
             [ribbon([(cx + k * 0.08 * w - 0.01 * w, y + h * 0.2), (cx + k * 0.08 * w + 0.01 * w, y + h * 0.6)], 0.004 * w)
              for k in range(-3, 4)], layer)
    return y + h

def lekor_plate(cv, cx, y, w, layer='mid', sliced=True, seed=1):
    """A plate heaped with keropok lekor: sliced ovals (fried) or whole rolls (raw)."""
    rnd = random.Random(seed)
    if sliced:
        plate(cv, cx, y, w, layer)
    else:                                               # a banana leaf for the raw rolls
        cv.add([[(cx - 0.6 * w, y + 0.06), (cx - 0.45 * w, y), (cx + 0.5 * w, y), (cx + 0.62 * w, y + 0.08)]], 'solid', layer)
    polys = []
    if sliced:
        for row, (n, dy) in enumerate(((6, 0.13), (5, 0.27), (3, 0.4))):
            for i in range(n):
                px = cx + (i - (n - 1) / 2) * 0.13 * w
                polys.append(ellipse(px, y + dy * w * 0.5 + 0.06, 0.06 * w, 0.045 * w, rot=rnd.uniform(-35, 35), n=18))
        for p in polys:
            cv.add([p], 'edge', layer)
    else:
        for k in range(5):
            a = -16 + 8 * k
            d = (math.cos(math.radians(a)), math.sin(math.radians(a)))
            c = (cx + (k - 2) * 0.06 * w, y + 0.09 + 0.05 * w * (1 + (k % 2)))
            r, L = 0.034 * w, 0.33 * w
            cv.add([ribbon([(c[0] - d[0] * L, c[1] - d[1] * L), (c[0] + d[0] * L, c[1] + d[1] * L)], r)] +
                   [ellipse(c[0] + sg * d[0] * L, c[1] + sg * d[1] * L, r, n=14) for sg in (-1, 1)], 'edge', layer)

def sauce_bowl(cv, cx, y, w, layer='mid'):
    """Mangkuk kecil of chilli dipping sauce with a spoon."""
    left = [(-0.5 * w, 0.42 * w), (-0.44 * w, 0.2 * w), (-0.3 * w, 0.05 * w), (-0.2 * w, 0.0)]
    cv.add([xf(mirror_pts(left), cx, y), xf(ribbon([(0.1 * w, 0.3 * w), (0.55 * w, 0.75 * w)], 0.03 * w), cx, y),
            xf(ellipse(0.12 * w, 0.38 * w, 0.1 * w, 0.06 * w, rot=40), cx, y)], 'dots', layer)

def gerai_back(cv):
    """Blurred roadside stall: corner posts, a zinc awning each side with plastic
    bags of keropok hung from it, the sea and a palm beyond."""
    cv.add([rect(-0.2, 2.6, 20.7, 2.66)], 'solid', 'back')
    palm(cv, 12.9, 2.6, 3.0, lean=-0.1, seed=71, layer='back')
    for px in (1.2, 19.3):
        cv.add([rect(px - 0.1, G, px + 0.1, 7.0)], 'solid', 'back')
    for x0, x1, sg in ((-0.3, 6.4, 1), (14.1, 20.8, -1)):
        cv.add([[(x0, 7.0), (x1, 7.0 - 0.12 * sg * 0), (x1, 6.75), (x0, 6.75)]], 'solid', 'back')
        cv.add([ribbon([(x0 + 0.3 * k, 6.75), (x0 + 0.3 * k + 0.05, 6.55)], 0.02) for k in range(int((x1 - x0) / 0.3))],
               'solid', 'back')
    for i, x in enumerate((2.3, 3.0, 3.7, 4.4, 15.6, 16.3, 17.0, 17.7)):
        L = 0.9 + 0.3 * (i % 3)
        cv.add([ribbon([(x, 6.75), (x, 6.75 - L * 0.4)], 0.012),
                ellipse(x, 6.75 - L * 0.4 - 0.32, 0.22, 0.36)], 'solid', 'back')

# =====================================================================
# rig parts (registered once, keys prefixed with the state id)
# =====================================================================

def _semutar():
    """Semutar: the folded head cloth of the east coast, its loose end standing
    up at the back like a cockscomb."""
    band = _open([(0.06, 0.9), (0.062, 0.93), (0.044, 0.962), (0.0, 0.978), (-0.04, 0.968), (-0.06, 0.935),
                  (-0.058, 0.892)]) + [(0.0, 0.904)]
    tail = [(-0.022, 0.962), (-0.05, 1.0), (-0.088, 1.03), (-0.082, 1.006), (-0.066, 0.978), (-0.058, 0.948)]
    knot = ellipse(-0.058, 0.93, 0.016, 0.022)
    carves = [ribbon([(-0.045, 0.912), (0.035, 0.952)], 0.0022), ribbon([(-0.048, 0.936), (0.01, 0.966)], 0.0022),
              ribbon([(-0.05, 0.975), (-0.074, 1.008)], 0.002)]
    return [band, tail, knot], 'lace', carves

def _kain_hitched(body):
    """Kain pelikat hitched up to the knee for wading."""
    return [(0.064, 0.565), (0.074, 0.46), (0.088, 0.35), (0.104, 0.262), (0.05, 0.27), (0.0, 0.262), (-0.06, 0.27),
            (-0.098, 0.26), (-0.084, 0.36), (-0.068, 0.46), (-0.06, 0.565)]

def _waist_knot(spec):
    return [([ribbon([(-0.066, 0.555), (0.066, 0.56)], 0.018), [(0.05, 0.55), (0.082, 0.505), (0.07, 0.49), (0.044, 0.535)]],
             'edge', [])]

def _it_jala(g, ang, fig):
    """Jala: the cast net gathered in the hand, hanging in a cone to its weighted hem."""
    x, y = g
    cone = [(x - 0.008, y + 0.012), (x + 0.012, y + 0.012), (x + 0.05, y - 0.12), (x + 0.1, y - 0.28),
            (x + 0.11, y - 0.33)] + arc_pts(x + 0.0, y - 0.33, 0.11, 0, -180, 12, ry=0.03)[1:-1] + \
           [(x - 0.11, y - 0.33), (x - 0.1, y - 0.27), (x - 0.045, y - 0.12)]
    weights = [W.circle(x - 0.1 + 0.025 * k, y - 0.35 - 0.022 * math.sin(math.pi * k / 8), 0.009, 8)[0] for k in range(9)]
    folds = [ribbon([(x, y - 0.02), (x - 0.07 + 0.035 * k, y - 0.3)], 0.0022) for k in range(5)]
    return [cone] + weights, 'grid', folds

def _it_dayung(g, ang, fig):
    """Dayung: the paddle carried over the shoulder, blade up behind his head."""
    deg = 128
    a = math.radians(deg)
    d = (math.cos(a), math.sin(a))
    p0 = (g[0] - 0.1 * d[0], g[1] - 0.1 * d[1])
    p1 = (g[0] + 0.42 * d[0], g[1] + 0.42 * d[1])
    shaft = ribbon([p0, (p1[0] + 0.05 * d[0], p1[1] + 0.05 * d[1])], 0.009)
    blade = ellipse(p1[0] + 0.16 * d[0], p1[1] + 0.16 * d[1], 0.165, 0.058, rot=deg)
    grip = xf(rect(-0.04, -0.009, 0.04, 0.009), p0[0], p0[1], rot=deg)
    rib = ribbon([(p1[0] + 0.05 * d[0], p1[1] + 0.05 * d[1]), (p1[0] + 0.27 * d[0], p1[1] + 0.27 * d[1])], 0.0045)
    return [shaft, blade, grip], 'edge', [rib]

def _it_strainer(g, ang, fig):
    """Penapis: a long-handled wire scoop held out over the wok."""
    a = math.radians(14)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.34 * d[0], g[1] + 0.34 * d[1])
    r = 0.1
    basket = [(end[0] - 0.005, end[1] + 0.01)] + arc_pts(end[0] + r, end[1] + 0.005, r, 180, 360, 16, ry=0.07)[1:] + \
             [(end[0] + 2 * r, end[1] + 0.012)]
    rolls = [ribbon([(end[0] + 0.02 + 0.05 * k, end[1] + 0.005), (end[0] + 0.07 + 0.05 * k, end[1] + 0.1 - 0.015 * k)], 0.016)
             for k in range(3)]
    holes = [W.diamond(end[0] + 0.04 + 0.03 * k, end[1] - 0.025 - 0.01 * (k % 2), 0.016, 0.022)[0] for k in range(5)]
    return [ribbon([(g[0] - 0.06 * d[0], g[1] - 0.06 * d[1]), end], 0.0065), basket] + rolls, 'solid', holes

def _it_cloth(g, ang, fig):
    """A finished songket length draped over the forearm, falling in a long panel."""
    x, y = g
    panel = rect(x - 0.03, 0.12, x + 0.14, y + 0.02)
    fold = [(x - 0.035, y + 0.03), (x + 0.15, y + 0.03), (x + 0.12, y - 0.05), (x - 0.02, y - 0.04)]
    fringe = [ribbon([(x - 0.02 + 0.02 * k, 0.12), (x - 0.02 + 0.02 * k, 0.085)], 0.003, 0.0015) for k in range(9)]
    cuts = [W.diamond(x + 0.055, yy, 0.07, 0.07)[0] for yy in (y - 0.14, y - 0.27, y - 0.4)]
    cuts += [[(x - 0.01 + 0.04 * k, 0.15), (x + 0.01 + 0.04 * k, 0.24), (x + 0.03 + 0.04 * k, 0.15)] for k in range(4)]
    return [panel, fold] + fringe, 'flower', cuts

W.register(W.HATS, 'terengganu_semutar', _semutar)
W.register(W.LOWERS, 'terengganu_kain', _kain_hitched)
W.register(W.COSTUMES, 'terengganu_nelayan',
           dict(W.COSTUMES['farmer'], lower='terengganu_kain', extra=_waist_knot,
                cls={'top': 'dots', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.COSTUMES, 'terengganu_kurung_sit', dict(W.COSTUMES['kurung'], legs='trousers'))
W.register(W.BEARDS, 'terengganu_janggut', [(0.064, 0.836), (0.066, 0.818), (0.06, 0.796), (0.05, 0.778),
                                            (0.044, 0.79), (0.04, 0.81), (0.046, 0.83)])
W.register(W.POSES, 'terengganu_ngah', {'f': (40, 50), 'b': (-10, 60), 'lean': 4, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'terengganu_haul', {'f': (2, 14), 'b': (-8, 26), 'lean': -22, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'terengganu_weave', {'f': (80, 22), 'b': (66, 40), 'lean': 8, 'legs': 'sit', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'terengganu_wind', {'f': (82, 40), 'b': (30, 60), 'lean': 6, 'legs': 'sit', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'terengganu_show', {'f': (52, 62), 'b': (44, 72), 'lean': 2, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'terengganu_scoop', {'f': (84, 12), 'b': (30, 70), 'lean': 8, 'legs': 'walk', 'hf': 'grip', 'hb': 'open'})
W.register(W.ITEMS2, 'terengganu_jala', _it_jala)
W.register(W.ITEMS2, 'terengganu_dayung', _it_dayung)
W.register(W.ITEMS2, 'terengganu_strainer', _it_strainer)
W.register(W.ITEMS2, 'terengganu_cloth', _it_cloth)

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def terengganu_land(cv):
    """Boats coming home at dusk over the South China Sea; on the beach two men
    haul the seine net in, its floats bobbing in the shallows."""
    hz = 2.75
    cv.add([rect(-0.1, hz - 0.025, 20.6, hz + 0.025)], 'solid', 'back')
    isle = _open([(13.6, hz), (14.3, hz + 0.35), (15.1, hz + 0.72), (15.9, hz + 0.62), (16.9, hz + 0.3), (17.8, hz)], 5)
    cv.add([isle + [(17.8, hz - 0.05), (13.6, hz - 0.05)]] + canopy(15.2, hz + 0.72, 0.35, 81, 5) + canopy(16.0, hz + 0.6, 0.3, 82, 5),
           'edge', 'back')
    perahu(cv, 11.6, hz - 0.05, 0.32, 'back', sail='set')
    perahu(cv, 19.2, hz - 0.05, 0.26, 'back', flip=True, sail='set')
    for row, (y, n, r) in enumerate(((2.25, 9, 0.16), (1.75, 7, 0.2))):
        rnd = random.Random(90 + row)
        cv.add([scroll(0.6 + i * 20.0 / n + rnd.uniform(-0.3, 0.3), y + rnd.uniform(-0.08, 0.08), r, r * 0.3, 1.1, a0=180,
                       cw=True, tail=[(0.6 + i * 20.0 / n - r * 2.4, y - r * 0.6), (0.6 + i * 20.0 / n - r * 1.2, y - r * 0.2)])
                for i in range(n)], 'solid', 'back')
    cloud(cv, 3.2, 6.9, 0.85, 'back', seed=2)
    cloud(cv, 16.6, 6.5, 0.7, 'back', flip=True, seed=5)
    cloud(cv, 19.4, 4.4, 0.45, 'back', seed=8)
    birds(cv, 8.6, 6.3, 4, 0.55, seed=4, layer='back', flip=True)
    # mid: the sun going down into the sea between the two boats
    sunset(cv, 7.6, hz, 0.95)
    perahu(cv, 3.9, G + 0.18, 1.12, sail='set')
    perahu(cv, 9.55, G + 0.42, 0.68, flip=True, sail='furled')
    water_run(cv, -0.1, 13.1, G + 0.04, 0.55, flow=1, seed=3)
    cv.add([[(12.4, G - 0.05), (12.95, G + 0.32), (13.5, G + 0.24), (14.4, G + 0.06), (14.4, G - 0.05)]], 'edge', 'mid')
    # the seine: its float line arcing in the shallows, the net hanging under it
    net = _open([(11.15, G + 0.86), (11.8, G + 0.72), (12.4, G + 0.68), (12.95, G + 0.74)], 6)
    cv.add([net + [(12.95, G + 0.2), (12.2, G + 0.12), (11.15, G + 0.18)]], 'grid', 'mid')
    cv.add([ellipse(px, py + 0.04, 0.075, 0.055) for px, py in net[::3]], 'solid', 'mid')
    rope = rope_line([(12.95, G + 0.74), (13.4, G + 1.12), (13.9, G + 1.46), (14.7, G + 1.5), (15.5, G + 1.42),
                      (16.25, G + 0.95), (16.7, G + 0.18)])
    cv.add([rope], 'solid', 'mid')
    cv.add([ribbon(arc_pts(17.15 + 0.02 * k, G + 0.1, 0.34 - 0.06 * k, 180, 360, 14, ry=0.09), 0.02) for k in range(4)],
           'solid', 'mid')                                                  # rope coiled on the sand
    W.place_figure(cv, dict(head='young', hat='terengganu_semutar', costume='terengganu_nelayan', pose='terengganu_haul',
                            rod_to=-0.25), 14.6, G, 2.75, flip=True)
    W.place_figure(cv, dict(head='old', hat='terengganu_semutar', costume='terengganu_nelayan', pose='terengganu_haul',
                            rod_to=-0.25), 16.2, G, 2.65, flip=True)
    rhu(cv, 18.3, G + 0.05, 4.6, lean=-0.03, seed=41)
    rhu(cv, 19.5, G + 0.05, 3.6, lean=0.04, seed=42)
    ground(cv, 'earth', seed=7)
    frame_edges(cv, seed=8, left='none', right='none')

def terengganu_people(cv):
    """Under the house a weaver works the songket loom; another winds gold
    thread on the wheel, and a third holds up a finished length."""
    rumah_dalam(cv)
    for i, (x, w, h) in enumerate(((1.1, 0.9, 2.6), (2.25, 0.95, 3.0))):
        songket_hang(cv, x, 5.55, w, h, seed=i)
    cv.add([ribbon([(0.3, 5.6), (3.0, 5.6)], 0.035), ribbon([(0.5, 5.6), (0.5, 7.2)], 0.02), ribbon([(2.8, 5.6), (2.8, 7.2)], 0.02)],
           'solid', 'mid')
    wx = 3.55
    kek(cv, wx, G, 1.5)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='terengganu_kurung_sit', pose='terengganu_weave',
                            rod_to=-0.25), wx, G, 3.3)
    cv.add([rect(wx - 0.42, G, wx + 0.22, G + 1.02)], 'edge', 'mid')        # her low bench
    W.place_figure(cv, dict(body='female', head='female', hat='tudung', costume='kurung', pose='terengganu_show',
                            item_f='terengganu_cloth', rod_to=-0.25), 12.0, G, 3.35, flip=True)
    rahat(cv, 16.6, G, 1.25)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='terengganu_kurung_sit', pose='terengganu_wind',
                            rod_to=-0.25), 14.15, G, 3.2)
    cv.add([rect(13.75, G, 14.38, G + 0.98)], 'edge', 'mid')
    ground(cv, 'earth', seed=17)
    frame_edges(cv, seed=18, left='none', right='banana')

def terengganu_food(cv):
    """Keropok lekor at a roadside stall: the hawker lifts a scoop of rolls out
    of the sizzling wok; raw rolls wait on the left, fried slices and chilli
    sauce on the right."""
    gerai_back(cv)
    dapur(cv, 10.6, G + 0.02, 1.35, pot=False, seed=3)
    rim = kuali(cv, 10.6, G + 0.02 + 1.33, 3.3)
    for i, (dx, hh, cw) in enumerate(((-1.0, 2.0, False), (-0.1, 2.5, True), (0.9, 2.1, True))):
        steam(cv, 10.6 + dx, rim + 0.5, hh, cw=cw, seed=20 + i)
    W.place_figure(cv, dict(head='refined', hat='songkok', costume='baju', pose='terengganu_scoop',
                            item_f='terengganu_strainer', rod_to=-0.25), 6.5, G, 3.5)
    lekor_plate(cv, 3.9, G + 0.02, 2.0, sliced=False, seed=5)
    stand(cv, 15.2, G + 0.02, 2.0, 0.85)
    lekor_plate(cv, 15.2, G + 0.87, 2.0, sliced=True, seed=6)
    sauce_bowl(cv, 17.45, G + 0.02, 0.9)
    for sx in (-1, 1):
        fish(cv, 10.6 + sx * 8.6, G + 0.35, 1.2, flip=sx > 0, ang=8)
    limes(cv, 12.75, G + 0.05, 0.85)
    ground(cv, 'earth', seed=27)
    frame_edges(cv, seed=28, left='none', right='none')

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def _matn(name, rgb, rgb2, scale=6.0, rough=0.6, coat=0.0):
    """Principled material mottled between rgb and rgb2 by a noise texture."""
    m = _mat(name, rgb, rough, coat=coat)
    nt = m.node_tree
    bs = nt.nodes['Principled BSDF']
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale
    nz.inputs['Detail'].default_value = 4.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[0].color = (*rgb, 1)
    ramp.color_ramp.elements[1].color = (*rgb2, 1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bs.inputs['Base Color'])
    return m

def icon_food_lekor(seed=3):
    """Keropok lekor on an enamel plate: whole fried rolls, a heap of slices
    showing their pale fish-and-sago centre, and a dish of chilli sauce."""
    rnd = random.Random(seed)
    enamel = _mat('Enamel', (0.92, 0.92, 0.88), 0.25)
    blue = _mat('Blue', (0.1, 0.25, 0.55), 0.3)
    _lathe('Plate', [(0.0, 0.0), (1.0, 0.0), (1.3, 0.1), (1.42, 0.2), (1.4, 0.23), (1.28, 0.14), (0.95, 0.05), (0.0, 0.05)],
           enamel, 72)
    _torus('PlateRim', (0, 0, 0.215), 1.41, 0.022, blue, seg=72)
    skin = _matn('LekorSkin', (0.66, 0.44, 0.2), (0.38, 0.22, 0.08), scale=14.0, rough=0.5)
    core = _matn('LekorCore', (0.86, 0.8, 0.68), (0.74, 0.68, 0.56), scale=30.0, rough=0.7)
    for i, (x, y, a) in enumerate(((-0.55, 0.15, 0.25), (-0.25, 0.5, 0.15), (-0.75, -0.3, 0.35), (-0.3, -0.05, 0.3))):
        _blob('Roll%d' % i, (x * 0.85 - 0.05, y * 0.9, 0.2 + 0.1 * (i == 3)), (0.7, 0.15, 0.15), (0, 0.05 * i, a), skin, seg=24)
    for i in range(9):                                  # slices: short cylinders cut on the bias
        x, y = 0.45 + 0.24 * (i % 3) - 0.08 * (i // 3), -0.55 + 0.27 * (i // 3) + rnd.uniform(-0.04, 0.04)
        z = 0.14 + 0.04 * (i // 3)
        sl = _lathe('Slice%d' % i, [(0.0, -0.05), (0.15, -0.05), (0.15, 0.05), (0.0, 0.05)], skin, 24, sharp=40)
        sl.location, sl.rotation_euler = (x, y, z), (rnd.uniform(0.35, 0.6), rnd.uniform(-0.25, 0.25), rnd.uniform(0, 3))
        cap = _lathe('Core%d' % i, [(0.0, 0.0), (0.135, 0.0)], core, 24, sharp=0)
        cap.parent = sl
        cap.location = (0, 0, 0.052)
    sauce = _mat("Sauce", (0.8, 0.13, 0.04), 0.2)
    _lathe('Dish', [(0.0, 0.0), (0.3, 0.0), (0.42, 0.12), (0.45, 0.2), (0.4, 0.2), (0.3, 0.08), (0.0, 0.08)], enamel, 48).location = (0.62, 0.62, 0.05)
    _lathe("Sauce", [(0.0, 0.185), (0.425, 0.185)], sauce, 48, sharp=0).location = (0.62, 0.62, 0.05)
    seed_m = _mat('Seeds', (0.95, 0.75, 0.35), 0.5)
    for k in range(7):
        _blob('Seed%d' % k, (0.62 + rnd.uniform(-0.2, 0.2), 0.62 + rnd.uniform(-0.2, 0.2), 0.215), (0.025, 0.015, 0.006),
              (0, 0, rnd.uniform(0, 3)), seed_m, seg=8)
    return (0, -4.8, 4.5), (0, 0.0, 0.1)

def icon_item_songket_gelang():
    """Gelang benang songket: a bangle braided from gold, maroon and green
    songket threads, with a small gold tassel."""
    gold = _mat('Gold', (0.9, 0.66, 0.24), 0.32, metal=1.0)
    maroon = _mat('Maroon', (0.45, 0.04, 0.1), 0.55)
    green = _mat('Green', (0.05, 0.3, 0.2), 0.55)
    R, r = 0.9, 0.09
    for k, mt in enumerate((gold, maroon, gold, green)):
        pts = []
        for i in range(241):
            t = TAU * i / 240
            ph = t * 9 + k * TAU / 4
            rr = R + r * math.cos(ph)
            pts.append((rr * math.cos(t), rr * math.sin(t), r * math.sin(ph)))
        _tube('Strand%d' % k, pts, 0.055, mt)
    for k in range(3):                                  # gold binding bands
        a = TAU * (0.62 + 0.04 * k)
        _torus('Bind%d' % k, (R * math.cos(a), R * math.sin(a), 0), 0.16, 0.025, gold,
               rot=(math.pi / 2, 0, a + math.pi / 2), seg=24)
    a = TAU * 0.66
    bx, by = (R + 0.1) * math.cos(a), (R + 0.1) * math.sin(a)
    _blob('TasselHead', (bx, by - 0.05, -0.05), (0.07, 0.07, 0.09), (0, 0, 0), gold)
    for k in range(9):
        u = (k - 4) / 4
        _tube('Tassel%d' % k, [(bx + 0.03 * u, by - 0.05, -0.1), (bx + 0.08 * u, by - 0.15, -0.38), (bx + 0.1 * u, by - 0.2, -0.6)],
              0.014, gold if k % 2 else maroon)
    _pivot((math.radians(12), math.radians(8), math.radians(-8)), (0, 0, 0.4))
    return (0, -4.6, 2.6), (0, 0, 0.35)

def _pivot(rot, loc, scale=1.0):
    """Parent every loose mesh/curve to one empty and turn it as a whole."""
    pv = bpy.data.objects.new('Pivot', None)
    bpy.context.scene.collection.objects.link(pv)
    for ob in list(bpy.context.scene.objects):
        if ob.type in ('MESH', 'CURVE') and ob.parent is None:
            ob.parent = pv
    pv.rotation_euler, pv.location, pv.scale = rot, loc, (scale,) * 3
    return pv

# =====================================================================
# registry: what the CLI renders for this state
# =====================================================================

PUPPET = dict(head='old', beard='terengganu_janggut', hat='terengganu_semutar', costume='terengganu_nelayan',
              pose='terengganu_ngah', item_f='terengganu_jala', item_b='terengganu_dayung', lean=3)   # Pak Ngah
BEATS = {'land': terengganu_land, 'people': terengganu_people, 'food': terengganu_food}
ICONS = {'food': icon_food_lekor, 'item': icon_item_songket_gelang}
