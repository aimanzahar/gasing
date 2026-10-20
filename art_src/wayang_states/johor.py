"""Johor: a busy port of cranes and cargo ships, porters loading in rhythm up the
gangplank, a plate of Laksa Johor, Pak Zaid with his cargo hook and rope."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props: the port
# =====================================================================

def jib_crane(cv, x, y, s=1.0, layer='mid', flip=False, reach=3.6, lift=0.9, load=True, seed=1):
    """Lattice jib crane on the wharf: tapered truss tower, machinery house,
    an A-frame, a raking truss jib, the hook and a sling of crates."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    cv.add([P([(-0.55, 0.0), (0.55, 0.0), (0.32, 3.4), (-0.32, 3.4)])], 'grid', layer)
    cv.add([P(rect(-0.7, -0.05, 0.7, 0.18)), P(rect(-0.45, 3.35, 0.7, 4.0)), P(rect(-0.95, 3.4, -0.45, 3.85))], 'edge', layer)
    cv.carve([P(rect(-0.25, 3.55, 0.05, 3.8)), P(rect(0.18, 3.55, 0.48, 3.8))], layer)
    cv.add([P(ribbon([(-0.3, 4.0), (0.0, 4.75)], 0.04)), P(ribbon([(0.3, 4.0), (0.0, 4.75)], 0.04))], 'solid', layer)
    a = math.atan2(lift, reach)
    tip = (0.6 + reach, 3.7 + lift)
    nx, ny = -math.sin(a), math.cos(a)
    jib = [(0.55, 3.6), (0.55 + 0.35 * nx, 3.6 + 0.35 * ny), (tip[0] + 0.05 * nx, tip[1] + 0.05 * ny), (tip[0], tip[1] - 0.05)]
    cv.add([P(jib)], 'grid', layer)
    cv.add([P(ribbon([(0.0, 4.75), tip], 0.016)), P(ribbon([(0.0, 4.75), (-0.9, 3.85)], 0.016)),
            P(ribbon([(tip[0] - 0.05, tip[1] - 0.05), (tip[0] - 0.05, 1.6)], 0.014))], 'solid', layer)
    hook = [ellipse(tip[0] - 0.05, 1.55, 0.07, 0.09, n=14),
            ribbon(arc_pts(tip[0] - 0.02, 1.32, 0.08, 120, 380, 16), 0.022, 0.008)]
    cv.add([P(h) for h in hook], 'solid', layer)
    if load:                                            # a sling of crates swinging under the hook
        cx = tip[0] - 0.05
        cv.add([P(ribbon([(cx, 1.3), (cx - 0.5, 0.75)], 0.012)), P(ribbon([(cx, 1.3), (cx + 0.5, 0.75)], 0.012))], 'solid', layer)
        cv.add([P(rect(cx - 0.6, 0.15, cx, 0.75)), P(rect(cx, 0.15, cx + 0.6, 0.75)), P(rect(cx - 0.32, 0.75, cx + 0.32, 1.05))],
               'edge', layer)
        cv.carve([P(ribbon([(cx - 0.55, 0.2), (cx - 0.05, 0.7)], 0.014)), P(ribbon([(cx + 0.05, 0.2), (cx + 0.55, 0.7)], 0.014)),
                  P(ribbon([(cx - 0.27, 0.9), (cx + 0.27, 0.9)], 0.014))], layer)

def steamer(cv, x, y, s=1.0, layer='mid', flip=False):
    """Cargo steamer broadside, bow to +x: raked stem, bridge house amidships, a
    tall banded funnel, two masts with derricks, portholes and hatches."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    hull = [(-4.0, 1.75), (-3.2, 1.6), (0.0, 1.55), (3.0, 1.6), (4.3, 1.95), (3.85, 0.55), (3.3, 0.12), (-3.4, 0.12),
            (-3.9, 0.5), (-4.1, 1.2)]
    cv.add([P(hull)], 'slits', layer)
    cv.carve([P(ribbon([(-3.8, 0.55), (3.75, 0.55)], 0.03))] +
             [P(W.circle(-3.0 + 0.48 * i, 1.22, 0.07, 12)[0]) for i in range(14)] +
             [P(ribbon(_open([(3.6, 1.5), (3.85, 1.25), (3.75, 1.0)]), 0.03))], layer)
    # bridge house and funnel
    cv.add_eo([P(rect(-1.2, 1.55, 1.0, 2.55)), P(rect(-1.4, 2.5, 1.2, 2.65))] +
              [P(rect(-1.0 + 0.4 * i, 1.85, -0.75 + 0.4 * i, 2.25)) for i in range(5)], 'edge', layer)
    cv.add([P(rect(-0.6, 2.65, 0.6, 3.15)), P(rect(-0.75, 3.1, 0.75, 3.22))], 'edge', layer)
    cv.add([P([(-0.6, 2.6), (-0.05, 2.6), (0.15, 4.55), (-0.45, 4.55)])], 'edge', layer)
    cv.carve([P([(-0.53, 3.95), (0.07, 3.95), (0.1, 4.2), (-0.5, 4.2)])], layer)
    # masts, derricks and hatches fore and aft
    for mx, sg in ((-2.6, 1), (2.4, -1)):
        cv.add([P(ribbon([(mx, 1.55), (mx, 4.5)], 0.05, 0.035)), P(ribbon([(mx - 0.4, 3.9), (mx + 0.4, 3.9)], 0.03)),
                P(ribbon([(mx, 1.75), (mx + sg * 1.4, 3.2)], 0.03, 0.02)),
                P(ribbon([(mx, 4.3), (mx + sg * 1.4, 3.2)], 0.012)),
                P(rect(mx + sg * 0.45 - 0.45, 1.55, mx + sg * 0.45 + 0.45, 1.85))], 'solid', layer)
    cv.add([P(ribbon([(-2.6, 4.5), (0.0, 3.4)], 0.012)), P(ribbon([(2.4, 4.5), (0.1, 4.0)], 0.012)),
            P(ribbon([(2.4, 4.5), (4.25, 2.0)], 0.012)), P(ribbon([(-2.6, 4.5), (-4.0, 1.85)], 0.012))], 'solid', layer)

def mosque(cv, x, y, s=1.0, layer='back'):
    """Masjid Sultan Abu Bakar across the strait: a long hall, corner turrets
    and the tall clock-tower minaret."""
    P = lambda pts: xf(pts, x, y, s=s)
    polys = [rect(-2.6, 0.0, 2.6, 1.3), [(-2.8, 1.3), (2.8, 1.3), (2.4, 1.75), (-2.4, 1.75)]]
    for tx in (-2.5, 2.5, -1.0):
        polys += [rect(tx - 0.2, 0.0, tx + 0.2, 2.1), ellipse(tx, 2.2, 0.2, 0.22, n=16), ribbon([(tx, 2.3), (tx, 2.6)], 0.02)]
    polys += [rect(0.6, 0.0, 1.3, 3.2), rect(0.5, 3.1, 1.4, 3.3), rect(0.7, 3.3, 1.2, 3.9), ellipse(0.95, 4.05, 0.3, 0.32, n=20),
              ribbon([(0.95, 4.3), (0.95, 4.7)], 0.025)]
    cv.add([P(p) for p in polys], 'edge', layer)

def wharf(cv, x0, x1, y, h=0.42, layer='mid'):
    """Timber wharf on piles: deck planks over cross-braced piles."""
    cv.add([rect(x0, y + h - 0.16, x1, y + h)] + [ribbon([(px, y - 0.3), (px, y + h - 0.1)], 0.06)
                                                  for px in [x0 + 0.3 + 0.9 * i for i in range(int((x1 - x0) / 0.9) + 1)]] +
           [ribbon([(x0 + 0.3 + 0.9 * i, y - 0.1), (x0 + 1.2 + 0.9 * i, y + h - 0.18)], 0.02)
            for i in range(int((x1 - x0) / 0.9))], 'edge', layer)
    return y + h

def bollard(cv, x, y, s=1.0, layer='mid', rope=True):
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P([(-0.16, 0.0), (0.16, 0.0), (0.12, 0.3), (0.2, 0.36), (0.18, 0.44), (-0.18, 0.44), (-0.2, 0.36), (-0.12, 0.3)])],
           'edge', layer)
    if rope:
        cv.add([P(ribbon(_open([(0.0, 0.25), (0.6, 0.18), (1.3, 0.24), (2.0, 0.6)]), 0.022))], 'solid', layer)

def rope_coil(cv, x, y, s=1.0, layer='mid'):
    """Coiled mooring rope lying on the planks: stacked flat rings."""
    rings = [ribbon(arc_pts(x, y + (0.08 + 0.07 * k) * s, (0.42 - 0.04 * k) * s, 0, 360, 36, ry=0.1 * s), 0.035 * s)
             for k in range(4)]
    cv.add(rings + [ellipse(x, y + 0.12 * s, 0.42 * s, 0.1 * s)], 'solid', layer)
    cv.carve([ribbon([(x + (-0.36 + 0.09 * i) * s, y + 0.08 * s), (x + (-0.33 + 0.09 * i) * s, y + 0.3 * s)], 0.008 * s)
              for i in range(9)], layer)

def crates(cv, x, y, s=1.0, layer='mid', stack=((0, 0), (1, 0), (0.5, 1))):
    boxes, cuts = [], []
    for cx, cy in stack:
        x0, y0 = x + cx * 0.75 * s, y + cy * 0.6 * s
        boxes.append(rect(x0, y0, x0 + 0.72 * s, y0 + 0.58 * s))
        cuts += [ribbon([(x0 + 0.08 * s, y0 + 0.08 * s), (x0 + 0.64 * s, y0 + 0.5 * s)], 0.018 * s),
                 ribbon([(x0 + 0.08 * s, y0 + 0.5 * s), (x0 + 0.64 * s, y0 + 0.08 * s)], 0.018 * s)]
    cv.add(boxes, 'edge', layer)
    cv.carve(cuts, layer)

def sacks(cv, x, y, s=1.0, layer='mid', n=(4, 3, 2)):
    """Guni sacks piled in a pyramid, ears tied, stitched seams."""
    polys, cuts = [], []
    for row, k in enumerate(n):
        for i in range(k):
            cx = x + (i - (k - 1) / 2) * 0.62 * s
            cy = y + (0.17 + row * 0.3) * s
            polys.append(ellipse(cx, cy, 0.34 * s, 0.17 * s, n=24))
            polys += [leaf(cx + sx * 0.32 * s, cy + 0.05 * s, 90 - sx * 50, 0.1 * s, 0.03 * s) for sx in (-1, 1)]
            cuts.append(ribbon([(cx - 0.22 * s, cy + 0.02 * s), (cx + 0.22 * s, cy + 0.02 * s)], 0.008 * s))
    cv.add(polys, 'edge', layer)
    cv.carve(cuts, layer)

def tongkang(cv, x, y, s=1.0, layer='mid', flip=False):
    """Tongkang lighter: a beamy barge with a tanja sail."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    cv.add([P(_open([(-1.6, 0.85), (0.0, 0.75), (1.7, 0.95)], 4) + [(1.5, 0.3), (1.1, 0.1), (-1.2, 0.1), (-1.6, 0.4)])], 'slits', layer)
    cv.add([P(ribbon([(0.0, 0.8), (0.0, 2.6)], 0.035))], 'solid', layer)
    cv.add([P([(0.1, 2.75), (1.3, 2.1), (1.15, 1.0), (0.1, 1.05)])], 'dots', layer)
    sacks(cv, x - 0.7 * s * (-1 if flip else 1), y + 0.75 * s, 0.6 * s, layer, n=(2, 1))

# =====================================================================
# props: the laksa table
# =====================================================================

def laksa_plate(cv, cx, y, w, layer='mid', seed=1):
    """Pinggan of Laksa Johor: a low nest of spaghetti in thick fish gravy,
    strands slipping over the rim, crowned with cucumber, onion rings, bean
    sprouts, mint and a dab of sambal."""
    rnd = random.Random(seed)
    mound = _open([(-0.46 * w, 0.07 * w), (-0.38 * w, 0.15 * w), (-0.2 * w, 0.21 * w), (0.0, 0.23 * w), (0.2 * w, 0.2 * w),
                   (0.38 * w, 0.14 * w), (0.46 * w, 0.07 * w)], 5)
    tops = [xf(mound, cx, y)]
    for i in range(9):                                  # garnish sprigs, cucumber sticks and onion rings on the crown
        bx = (-0.32 + 0.08 * i) * w
        by = (0.2 - 0.25 * (bx / w) ** 2) * w
        if i % 3 == 0:
            tops += [leaf(cx + bx, y + by, 90 + (j - 1.5) * 26, 0.15 * w, 0.03 * w, bend=0.012 * w * (j - 1.5)) for j in range(4)]
        elif i % 3 == 1:
            tops.append(xf(ribbon([(0, 0), (0, 0.15 * w)], 0.014 * w), cx + bx, y + by, rot=rnd.uniform(-35, 35)))
        else:
            tops.append(ribbon(arc_pts(cx + bx, y + by + 0.05 * w, 0.045 * w, 0, 360, 16), 0.009 * w))
    tops.append(ellipse(cx + 0.06 * w, y + 0.25 * w, 0.065 * w, 0.045 * w))                  # sambal
    for sx in (-1, 1):                                  # strands slipping over the rim
        for k in range(3):
            tops.append(ribbon(_open([(cx + sx * (0.34 + 0.03 * k) * w, y + 0.12 * w), (cx + sx * (0.47 + 0.02 * k) * w, y + 0.09 * w),
                                      (cx + sx * (0.5 + 0.02 * k) * w, y + 0.02 * w),
                                      (cx + sx * (0.48 + 0.03 * k) * w, y - (0.06 + 0.04 * k) * w)]), 0.008 * w, 0.006 * w))
    cv.add(tops, 'edge', layer)
    loops = []                                          # spaghetti twirls cut through the nest
    for k in range(12):
        a0 = rnd.uniform(0, 360)
        ccx = cx + (-0.36 + 0.065 * k) * w
        ccy = y + (0.06 + 0.07 * (1 - abs(ccx - cx) / (0.4 * w))) * w
        loops.append(ribbon(arc_pts(ccx, ccy, 0.045 * w, a0, a0 + 280, 18, ry=0.025 * w), 0.005 * w))
    cv.carve(loops, layer)
    plate_ = [(-0.56 * w, 0.06 * w), (-0.48 * w, 0.0), (-0.2 * w, -0.03 * w), (0.2 * w, -0.03 * w), (0.48 * w, 0.0),
              (0.56 * w, 0.06 * w), (0.5 * w, 0.07 * w), (-0.5 * w, 0.07 * w)]
    cv.add([xf(plate_, cx, y), xf(rect(-0.18 * w, -0.07 * w, 0.18 * w, -0.02 * w), cx, y)], 'edge', layer)

def condiment(cv, cx, y, w, kind='sprouts', layer='mid'):
    """Small piring of a garnish: bean sprouts, cucumber sticks or herbs."""
    polys = []
    if kind == 'sprouts':
        polys += [ribbon(_open([(cx + (i - 3) * 0.06 * w, y + 0.1 * w), (cx + (i - 3) * 0.07 * w + 0.03 * w, y + 0.28 * w),
                                (cx + (i - 3) * 0.05 * w + 0.07 * w, y + 0.36 * w)]), 0.012 * w, 0.006 * w) for i in range(7)]
        polys += [ellipse(cx + (i - 3) * 0.05 * w + 0.075 * w, y + 0.37 * w, 0.025 * w, 0.02 * w) for i in range(7)]
    elif kind == 'cucumber':
        polys += [xf(ribbon([(0, 0), (0, 0.32 * w)], 0.022 * w), cx + (i - 2.5) * 0.08 * w, y + 0.08 * w, rot=(i - 2.5) * 9)
                  for i in range(6)]
    else:
        for i in range(3):
            polys += [leaf(cx + (i - 1) * 0.18 * w, y + 0.1 * w, 90 + (j - 2) * 25, 0.26 * w, 0.05 * w,
                           bend=0.02 * w * (j - 2)) for j in range(5)]
    polys.append(_open([(cx - 0.42 * w, y + 0.12 * w), (cx - 0.3 * w, y), (cx + 0.3 * w, y), (cx + 0.42 * w, y + 0.12 * w)], 3))
    cv.add(polys, 'edge', layer)

def meja(cv, cx, y, w, h, layer='mid'):
    """A kedai kopi table: a plank top with a lipped edge, splayed legs and a stretcher."""
    P = lambda pts: xf(pts, cx, y)
    cv.add([P([(-0.5 * w, h - 0.1), (0.5 * w, h - 0.1), (0.52 * w, h - 0.03), (0.5 * w, h), (-0.5 * w, h), (-0.52 * w, h - 0.03)]),
            P(rect(-0.44 * w, h - 0.3, 0.44 * w, h - 0.1))] +
           [P(ribbon([(sx * 0.4 * w, h - 0.1), (sx * 0.45 * w, 0.0)], 0.06, 0.05)) for sx in (-1, 1)] +
           [P(ribbon([(-0.42 * w, 0.35), (0.42 * w, 0.35)], 0.035))], 'edge', layer)
    cv.carve([P(rect(x * w - 0.25, h - 0.24, x * w + 0.25, h - 0.16)) for x in (-0.27, 0.0, 0.27)], layer)

def bangku(cv, x, y, w, h, layer='mid'):
    """A plank bench, two legs."""
    P = lambda pts: xf(pts, x, y)
    cv.add([P(rect(-0.5 * w, h - 0.09, 0.5 * w, h))] + [P(ribbon([(sx * 0.36 * w, h - 0.08), (sx * 0.42 * w, 0.0)], 0.045))
                                                      for sx in (-1, 1)] + [P(ribbon([(-0.38 * w, 0.3), (0.38 * w, 0.3)], 0.025))],
           'solid', layer)

def ikan_parang(cv, x, y, s, flip=False, layer='mid'):
    """Ikan parang (wolf herring): a long knife-blade fish, jaw jutting up."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    body = _open([(0.85, 0.06), (0.7, 0.14), (0.2, 0.2), (-0.4, 0.12), (-0.7, 0.03)], 5) + \
        _open([(-0.7, -0.02), (-0.4, -0.08), (0.2, -0.15), (0.7, -0.06), (0.88, 0.0)], 5)[1:]
    tail = [(-0.66, 0.0), (-0.95, 0.18), (-0.86, 0.0), (-0.95, -0.15)]
    fins = [[(-0.1, 0.17), (-0.3, 0.25), (-0.32, 0.12)], [(0.1, -0.14), (-0.3, -0.2), (-0.4, -0.07)]]
    cv.add([P(body), P(tail)] + [P(f) for f in fins], 'scales', layer)
    cv.carve([P(W.circle(0.66, 0.07, 0.035, 12)[0]), P(ribbon(_open([(0.55, 0.15), (0.5, 0.03), (0.55, -0.08)]), 0.01))], layer)

# =====================================================================
# rig parts: Pak Zaid and the porters
# =====================================================================

def _hat_headcloth():
    """Ikat kepala: a cloth wound round the head, knotted at the back, two ends flying."""
    p = _open([(0.058, 0.9), (0.06, 0.935), (0.04, 0.958), (0.0, 0.966), (-0.04, 0.958), (-0.062, 0.932),
               (-0.064, 0.895)], 5) + [(0.0, 0.905)]
    knot = ellipse(-0.068, 0.925, 0.016, 0.014, n=12)
    tails = [leaf(-0.072, 0.925, 205, 0.075, 0.012, bend=0.01), leaf(-0.072, 0.922, 232, 0.065, 0.011, bend=-0.008)]
    carves = [ribbon([(-0.04 + 0.022 * i, 0.91), (-0.028 + 0.022 * i, 0.95)], 0.0022) for i in range(5)]
    return [p, knot] + tails, 'edge', carves

def _rope_extra(spec):
    """A coil of heavy rope slung over the front shoulder and across the back."""
    rings = [ribbon(arc_pts(-0.004 + 0.01 * k, 0.645, 0.05 + 0.008 * k, 0, 360, 40, ry=0.2 + 0.006 * k), 0.008)
             for k in range(3)]
    rings = [xf(r, rot=-26, ox=0.0, oy=0.645) for r in rings]
    return [(rings, 'solid', [])]

def _it_hook(g, ang, fig):
    """Cangkuk: a docker's cargo hook, T-handle in the fist, the iron curving out."""
    x, y = g
    bar = ribbon([(x - 0.004, y - 0.03), (x + 0.004, y + 0.03)], 0.007)
    hook = ribbon(_open([(x + 0.01, y), (x + 0.07, y + 0.01), (x + 0.105, y - 0.02), (x + 0.095, y - 0.06), (x + 0.065, y - 0.07),
                         (x + 0.05, y - 0.05)]), 0.0075, 0.0025)
    return [bar, hook], 'solid', []

def _it_sack(g, ang, fig):
    """A guni sack heaved over the shoulder behind the head."""
    cx, cy = g[0] - 0.13, g[1] - 0.025
    sack = xf(ellipse(0.0, 0.0, 0.15, 0.08, n=28), cx, cy, rot=14)
    ears = [xf(leaf(0.0, 0.0, a, 0.055, 0.02), *xf([(sx * 0.15, 0.0)], cx, cy, rot=14)[0]) for a, sx in ((24, 1), (204, -1))]
    seam = [xf(ribbon([(-0.11, 0.02), (0.11, 0.02)], 0.003), cx, cy, rot=14),
            xf(ribbon([(-0.06, -0.035), (0.0, -0.035)], 0.0025), cx, cy, rot=14)]
    return [sack] + ears, 'edge', seam

def _it_sudu(g, ang, fig):
    """Sudu: a spoon dipped toward the plate."""
    a = math.radians(ang - 30)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.12 * d[0], g[1] + 0.12 * d[1])
    return [ribbon([(g[0] - 0.02 * d[0], g[1] - 0.02 * d[1]), end], 0.0045, 0.0035),
            ellipse(end[0] + 0.02 * d[0], end[1] + 0.02 * d[1], 0.026, 0.016, rot=math.degrees(a))], 'solid', []

W.register(W.HATS, 'johor_headcloth', _hat_headcloth)
W.register(W.COSTUMES, 'johor_docker', dict(W.COSTUMES['farmer'], sleeve=0.036, extra=_rope_extra))
W.register(W.COSTUMES, 'johor_porter', dict(W.COSTUMES['farmer'], sleeve=0.034, cls={'top': 'edge', 'lower': 'grid',
                                                                                     'legs': 'edge', 'arm': 'edge'}))
W.register(W.ITEMS2, 'johor_hook', _it_hook)
W.register(W.ITEMS2, 'johor_sack', _it_sack)
W.register(W.ITEMS2, 'johor_sudu', _it_sudu)
W.register(W.POSES, 'johor_eat', {'f': (74, 52), 'b': (40, 70), 'lean': 6, 'legs': 'sit', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'johor_haul', {'f': (58, 68), 'b': (-24, -12), 'lean': 4, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'johor_shoulder', {'f': (149, 139), 'b': (-18, -14), 'lean': 9, 'legs': 'walk', 'hf': 'grip', 'hb': 'open'})

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def johor_land(cv):
    """Cranes tower over a busy port full of cargo ships."""
    hills(cv, -0.5, 21, G + 0.55, 0.55, seed=61, n=4)
    mosque(cv, 9.6, G + 0.75, 0.62)
    steamer(cv, 16.8, G + 0.4, 0.42, 'back', flip=True)
    cloud(cv, 12.6, 7.2, 0.7, 'back', seed=62)
    cloud(cv, 2.8, 7.4, 0.6, 'back', flip=True, seed=63)
    birds(cv, 14.2, 6.3, 3, 0.45, seed=64, layer='back')
    # mid: the hero crane on the left wharf, the steamer alongside, a second crane right
    deck = wharf(cv, -0.2, 7.0, G)
    jib_crane(cv, 2.5, deck, 1.05, reach=3.3, lift=0.75)
    crates(cv, -0.1, deck, 0.9)
    sacks(cv, 4.6, deck, 0.8, n=(3, 2, 1))
    bollard(cv, 6.75, deck, 0.9, rope=False)
    steamer(cv, 11.6, G - 0.25, 0.88)
    deck2 = wharf(cv, 16.2, 20.7, G)
    jib_crane(cv, 18.4, deck2, 0.9, flip=True, reach=2.6, lift=0.6, load=False)
    rope_coil(cv, 16.9, deck2, 0.9)
    ground(cv, 'water', seed=65)
    frame_edges(cv, seed=66, left='none', right='none')

def johor_people(cv):
    """Dock workers load goods up the gangplank in a steady rhythm."""
    hills(cv, -0.5, 21, G + 0.7, 0.6, seed=71, n=4)
    jib_crane(cv, 3.0, G + 1.0, 0.75, 'back', reach=3.0, lift=0.8)
    cloud(cv, 9.4, 7.3, 0.7, 'back', seed=72)
    # the ship's side on the right, the gangplank up to her rail
    hull = [(12.8, 2.95), (20.7, 2.95), (20.7, G - 0.2), (13.4, G - 0.2), (12.9, 1.4)]
    cv.add([hull], 'slits')
    cv.carve([W.circle(14.0 + 0.62 * i, 2.15, 0.09, 14)[0] for i in range(10)] + [ribbon([(13.2, 1.45), (20.6, 1.45)], 0.03)])
    cv.add([ribbon([(13.0 + 0.5 * i, 2.95), (13.0 + 0.5 * i, 3.45)], 0.025) for i in range(16)] +
           [ribbon([(12.9, 3.45), (20.7, 3.45)], 0.04), ribbon([(16.4, 3.4), (16.4, 6.2)], 0.06, 0.045),
            ribbon([(16.4, 3.5), (13.6, 5.5)], 0.035, 0.025), ribbon([(16.4, 6.0), (13.6, 5.5)], 0.012)], 'solid')
    p0, p1 = (6.4, G + 0.42), (13.1, 2.95)
    slope = (p1[1] - p0[1]) / (p1[0] - p0[0])
    on = lambda x: p0[1] + (x - p0[0]) * slope
    cv.add([ribbon([p0, p1], 0.07)] + [ribbon([(p0[0] + 0.55 * i, on(p0[0] + 0.55 * i) + 0.05),
                                              (p0[0] + 0.55 * i + 0.04, on(p0[0] + 0.55 * i) + 0.13)], 0.025)
                                      for i in range(12)], 'solid')
    deck = wharf(cv, -0.2, 7.2, G)
    # porters in step, sacks on their shoulders; the tally man calls the beat
    for x in (5.0, 8.4, 11.2):
        W.place_figure(cv, dict(head='refined', hat='johor_headcloth', costume='johor_porter', pose='johor_shoulder',
                                item_f='johor_sack', rod_to=-0.25), x, on(x) + 0.06 if x > p0[0] else deck, 3.0)
    W.place_figure(cv, dict(head='old', hat='songkok', costume='baju', pose='gesture', rod_to=-0.25),
                   2.2, deck, 3.0)
    sacks(cv, 3.6, deck, 0.75, n=(3, 2, 1))
    crates(cv, 0.0, deck, 0.7, stack=((0, 0), (0, 1)))
    ground(cv, 'water', seed=73)
    frame_edges(cv, seed=74, left='none', right='none')

def johor_food(cv):
    """A plate of Laksa Johor at the kedai table: spaghetti under thick fish
    gravy, two diners on their benches reaching in with their spoons."""
    # back: a coffee-shop wall, tiled shelf, a ceiling fan and a hanging sign board
    cv.add_eo([rect(1.2, 2.6, 5.2, 6.6), rect(1.5, 2.9, 4.9, 6.3)], 'edge', 'back')
    cv.add([ribbon([(1.5, 4.6), (4.9, 4.6)], 0.04), ribbon([(3.2, 2.9), (3.2, 6.3)], 0.04)], 'solid', 'back')
    cv.add([rect(14.8, 4.9, 19.4, 5.05)], 'solid', 'back')
    for i, x in enumerate((15.3, 16.5, 17.7, 18.8)):
        periuk(cv, x, 5.05, 0.6 + 0.15 * (i % 2), 'back', lid=i % 2 == 0)
    cv.add([ribbon([(10.6, 8.3), (10.6, 7.6)], 0.02), ellipse(10.6, 7.55, 0.15, 0.06)] +
           [xf(leaf(0, 0, a, 1.2, 0.12), 10.6, 7.55) for a in (0, 180)], 'solid', 'back')
    # hero: the plate on the kedai table between two diners on their benches
    dapur(cv, 5.1, G + 0.05, 1.2)
    steam(cv, 5.0, 3.9, 2.0, cw=False, seed=85)
    for bx in (8.25, 13.0):
        bangku(cv, bx, G, 1.1, 1.18)
    W.place_figure(cv, dict(head='refined', hat='songkok', costume='baju', pose='johor_eat', item_f='johor_sudu',
                            legs='sit', rod_to=-0.25), 8.15, G, 3.4)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kurung', pose='johor_eat', item_f='johor_sudu',
                            legs='sit', rod_to=-0.25), 13.1, G, 3.55, flip=True)
    meja(cv, 10.6, G, 3.4, 1.62)
    plate_y = G + 1.66
    laksa_plate(cv, 10.6, plate_y, 1.75)
    for i, (dx, hh, cw) in enumerate(((-0.35, 1.3, False), (0.3, 1.55, True))):
        steam(cv, 10.6 + dx, plate_y + 0.55, hh, cw=cw, seed=80 + i)
    condiment(cv, 9.45, plate_y, 0.75, 'sprouts')
    condiment(cv, 11.8, plate_y, 0.75, 'cucumber')
    for sx in (-1, 1):                                  # fish mirrored about the table
        ikan_parang(cv, 10.6 + sx * 7.7, G + 0.3, 1.25, flip=sx > 0)
    condiment(cv, 15.6, G, 1.4, 'herbs')
    limes(cv, 16.7, G + 0.05, 0.9)
    ground(cv, 'earth', seed=87)
    frame_edges(cv, seed=88, left='banana', right='none')

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def icon_food_laksa_johor(seed=3):
    """Laksa Johor: spaghetti on a plate under thick brown fish gravy, topped
    with cucumber, red onion, bean sprouts, mint, daun kesum, sambal and lime."""
    rnd = random.Random(seed)
    plate_prof = [(0.0, 0.0), (0.7, 0.0), (0.75, 0.04), (1.5, 0.12), (1.85, 0.26), (1.9, 0.3), (1.84, 0.3), (1.45, 0.18),
                  (0.0, 0.14)]
    _lathe('Plate', plate_prof, _mat('Porcelain', (0.95, 0.94, 0.9), 0.2, coat=0.3), 72)
    _torus('RimLine', (0, 0, 0.29), 1.8, 0.016, _mat('Green', (0.12, 0.42, 0.25), 0.3))
    pasta = _mat('Spaghetti', (0.93, 0.8, 0.5), 0.4)
    for i in range(18):                                 # a nest of pasta strands
        a0 = rnd.uniform(0, TAU)
        r0 = rnd.uniform(0.2, 1.0)
        pts = [((r0 + 0.25 * math.sin(t * 7 + i)) * math.cos(a0 + t * 2.2), (r0 + 0.25 * math.sin(t * 7 + i)) * math.sin(a0 + t * 2.2),
                0.2 + 0.32 * (1 - (r0 / 1.2) ** 2) + 0.05 * math.sin(t * 9 + i)) for t in (k / 29 for k in range(30))]
        _tube('Pasta%d' % i, pts, 0.03, pasta)
    gravy = _mat('Gravy', (0.42, 0.22, 0.08), 0.35, coat=0.2)
    _blob('Gravy', (0.0, 0.0, 0.36), (1.0, 0.95, 0.22), (0, 0, 0), gravy, seg=32)
    cuc, cucs = _mat('Cucumber', (0.65, 0.84, 0.4), 0.45), _mat('CucSkin', (0.12, 0.38, 0.1), 0.45)
    for i in range(9):
        _box('Cuc%d' % i, (-0.5 + 0.05 * i, 0.3 - 0.04 * (i % 4), 0.62 + 0.02 * (i % 3)), (0.5, 0.05, 0.05),
             (0.1 * (i % 2), 0.1, rnd.uniform(-0.6, 0.6)), cuc if i % 3 else cucs)
    onion = _mat('Onion', (0.62, 0.25, 0.48), 0.35)
    for i in range(4):
        _torus('Onion%d' % i, (0.4 + 0.1 * (i % 2), -0.3 + 0.14 * i, 0.62), 0.1, 0.016, onion, rot=(0.2, 0.1, 0))
    sprout = _mat('Sprout', (0.97, 0.95, 0.8), 0.4)
    for k in range(12):
        a = rnd.uniform(-0.8, 0.8)
        _tube('Sprout%d' % k, [(-0.1 + 0.03 * k, -0.5, 0.6), (0.1 + 0.03 * k + 0.2 * math.sin(a), -0.35, 0.68)], 0.014, sprout)
    mint = _mat('Mint', (0.12, 0.45, 0.12), 0.5)
    for i in range(8):
        a = TAU * i / 8
        _blob('Mint%d' % i, (0.1 + 0.14 * math.cos(a), 0.05 + 0.12 * math.sin(a), 0.72 + 0.03 * (i % 2)), (0.13, 0.06, 0.014),
              (0.4 * math.cos(a), 0.4 * math.sin(a), a), mint, seg=8)
    _blob('Sambal', (-0.45, -0.25, 0.64), (0.16, 0.13, 0.07), (0, 0, 0), _mat('Sambal', (0.62, 0.06, 0.03), 0.4), seg=12)
    lime = _mat('Lime', (0.42, 0.7, 0.15), 0.35)
    _lathe('Lime', [(0.0, 0.0), (0.2, 0.0), (0.21, 0.05), (0.0, 0.06)], _mat('LimeFlesh', (0.78, 0.88, 0.45), 0.3), 32) \
        .location = (1.3, -0.5, 0.22)
    _blob('LimeSkin', (1.3, -0.5, 0.2), (0.21, 0.21, 0.1), (0, 0, 0), lime, seg=16)
    return (0, -6.4, 6.0), (0, 0, 0.25)

def icon_item_rope_charm():
    """The dockworker's rope charm: a coil of tarred manila rope bound with
    twine, a brass shackle and a monkey's-fist knot on its tail."""
    rope = _mat('Manila', (0.6, 0.45, 0.25), 0.8)
    dark = _mat('Tarred', (0.24, 0.16, 0.08), 0.7)
    brass = _mat('Brass', (0.85, 0.62, 0.22), 0.28, metal=1.0)
    for k in range(5):                                  # flat coil, each turn twisted with a helix stripe
        r = 0.55 + 0.17 * k
        pts = [(r * math.cos(TAU * t), r * math.sin(TAU * t), 0.08) for t in (i / 63 for i in range(64))]
        _tube('Turn%d' % k, pts + [pts[0]], 0.075, rope)
        stripe = [((r + 0.06 * math.cos(t * 90)) * math.cos(TAU * t), (r + 0.06 * math.cos(t * 90)) * math.sin(TAU * t),
                   0.08 + 0.06 * math.sin(t * 90)) for t in (i / 359 for i in range(360))]
        _tube('Lay%d' % k, stripe, 0.022, dark)
    for a in (0.3, 2.4, 4.3):                           # twine whippings binding the coil
        for j in range(3):
            _torus('Bind%.1f%d' % (a, j), (1.0 * math.cos(a + 0.05 * j), 1.0 * math.sin(a + 0.05 * j), 0.08), 0.12, 0.022,
                   dark, rot=(math.pi / 2, 0, a + math.pi / 2), seg=16)
    tail = [(1.3 + 0.6 * t, -0.2 - 0.9 * t, 0.08 + 0.1 * math.sin(t * 3)) for t in (i / 12 for i in range(13))]
    _tube('Tail', tail, 0.075, rope)
    fist = tail[-1]
    _blob('Fist', fist, (0.22, 0.22, 0.2), (0, 0, 0), rope, seg=16)
    for j in range(3):                                  # the monkey's-fist wraps
        _torus('Wrap%d' % j, fist, 0.2, 0.03, dark, rot=(math.pi / 2 * (j == 1), math.pi / 2 * (j == 2), 0), seg=24)
    _torus('Shackle', (-0.1, 1.45, 0.2), 0.22, 0.045, brass, rot=(math.pi / 2, 0, 0.4), seg=24)
    _box('Pin', (-0.1, 1.45, 0.42), (0.5, 0.06, 0.06), (0, 0, 0.4), brass)
    return (0.4, -5.9, 5.6), (0.3, 0.05, 0.05)

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

PUPPET = dict(head='refined', beard='full', hat='johor_headcloth', costume='johor_docker', pose='johor_haul',
              item_f='johor_hook', item_b='rope', scale=1.03, feet=0.03)                # Pak Zaid
BEATS = {'land': johor_land, 'people': johor_people, 'food': johor_food}
ICONS = {'food': icon_food_laksa_johor, 'item': icon_item_rope_charm}
