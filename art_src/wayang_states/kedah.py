"""Kedah: padi terraces under Gunung Jerai, the gate-keepers timing the water,
nasi ulam mixed at the field's edge, and Mak Semah with her gate-key staff."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props
# =====================================================================

def jerai(cv, x, base, w, h, seed=1, layer='back'):
    """Gunung Jerai: a long massif, steep on the sea side, a rounded summit
    and a shoulder ridge running inland."""
    f = noise1(seed, 11)
    pts = [(x - w * 0.5, base - 0.2)]
    for i in range(49):
        t = i / 48
        prof = max(math.exp(-((t - 0.36) / 0.16) ** 2), 0.62 * math.exp(-((t - 0.62) / 0.2) ** 2),
                   0.35 * math.exp(-((t - 0.86) / 0.12) ** 2))
        pts.append((x - w * 0.5 + w * t, base + h * (0.08 + 0.92 * prof) + 0.06 * h * f(t) * prof))
    pts.append((x + w * 0.5, base - 0.2))
    return cv.add([_open(pts, 3)], 'edge', layer)

def jelapang(cv, x, y, s=1.0, layer='mid'):
    """Kedah rice barn: stilts with rat-guard discs, slatted store, steep attap
    roof with flared eaves and crossed gable boards, a notched-log ladder."""
    P = lambda pts: xf(pts, x, y, s=s)
    posts = [P(ribbon([(px, 0.0), (px, 0.8)], 0.045)) for px in (-0.55, -0.18, 0.18, 0.55)]
    posts += [P(ellipse(px, 0.66, 0.11, 0.035)) for px in (-0.55, -0.18, 0.18, 0.55)]
    cv.add(posts + [P(rect(-0.72, 0.78, 0.72, 0.88))], 'solid', layer)
    cv.add_eo([P(rect(-0.62, 0.88, 0.62, 1.72)), P(rect(-0.16, 1.02, 0.16, 1.5))], 'grid', layer)
    roof = P(_open([(-1.05, 1.74), (-0.92, 1.66), (-0.8, 1.68)], 4) + [(-0.36, 2.78), (0.36, 2.78)] +
             _open([(0.8, 1.68), (0.92, 1.66), (1.05, 1.74)], 4) + [(0.7, 1.62), (-0.7, 1.62)])
    cv.add([roof], 'scales', layer)
    cv.add([P(ribbon([(-0.46, 2.6), (-0.2, 3.05)], 0.028, 0.012)), P(ribbon([(-0.26, 2.6), (-0.52, 3.05)], 0.028, 0.012)),
            P(ribbon([(0.46, 2.6), (0.2, 3.05)], 0.028, 0.012)), P(ribbon([(0.26, 2.6), (0.52, 3.05)], 0.028, 0.012)),
            P(ribbon([(-0.36, 2.78), (0.36, 2.78)], 0.03)),
            P(ribbon([(0.62, 0.88), (0.98, 0.0)], 0.045, 0.06))], 'solid', layer)
    cv.carve([P(ribbon([(0.66 + 0.09 * t, 0.7 - t * 0.88), (0.76 + 0.09 * t, 0.68 - t * 0.88)], 0.012)) for t in (0.2, 0.45, 0.7)],
             layer)

def kerbau(cv, x, y, s=1.0, flip=False, layer='mid', egret_on=True):
    """Water buffalo, head low: barrel body, swept crescent horns, tail tuft."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    legs = []
    for hx, kx, fx in ((0.78, 0.86, 0.84), (0.5, 0.52, 0.44), (-0.95, -1.08, -1.02), (-1.22, -1.16, -1.26)):
        legs.append(P(ribbon(_open([(hx, 1.05), (kx, 0.48), (fx, 0.1)]), 0.14, 0.06)))
        legs.append(P([(fx - 0.09, 0.0), (fx + 0.11, 0.0), (fx + 0.07, 0.12), (fx - 0.07, 0.12)]))
    cv.add(legs[0:2] + legs[4:6], 'solid', layer)                # far legs
    body = _open([(-1.5, 1.22), (-1.42, 1.56), (-0.9, 1.72), (0.0, 1.68), (0.55, 1.86), (0.95, 1.72),
                  (1.3, 1.5), (1.55, 1.28), (1.76, 0.98), (1.7, 0.88), (1.5, 0.9), (1.16, 1.08),
                  (0.86, 0.94), (0.55, 0.84), (0.0, 0.78), (-0.8, 0.84), (-1.28, 0.95)], 5)
    horn = _open([(1.32, 1.5), (1.0, 1.66), (0.66, 1.9), (0.58, 2.2), (0.74, 2.42)], 5)
    parts = [P(body), P(ribbon(horn, 0.095, 0.014)), P(ribbon(xf(horn, 0.16, -0.06), 0.07, 0.012)),
             P(leaf(1.18, 1.42, 205, 0.26, 0.06, bend=-0.03)),
             P(ribbon(_open([(-1.46, 1.5), (-1.58, 1.1), (-1.56, 0.62)]), 0.028, 0.018)), P(leaf(-1.56, 0.66, -92, 0.26, 0.06))]
    cv.add(parts + legs[2:4] + legs[6:8], 'lace', layer)
    cv.carve([P(ellipse(1.43, 1.26, 0.045, 0.03)),
              P(ribbon(_open([(1.0, 1.55), (0.95, 1.3), (1.02, 1.1)]), 0.008)),
              P(ribbon(_open([(0.88, 1.6), (0.82, 1.34), (0.88, 1.12)]), 0.008))], layer)
    if egret_on:
        egret(cv, *P([(-0.35, 1.68)])[0], 0.9 * s, flip=not flip, layer=layer)

def terraces(cv, levels, seed=1, layer='mid'):
    """Flooded padi levels stepping down to the right, back (highest) first.
    levels: [(top_y, lip_x, padi_h)]; each band runs from the left edge to a
    rounded lip, carries a row of young padi and water-shine cuts, its water
    curling toward the lip and spilling over onto the next level down."""
    rnd = random.Random(seed)
    for i, (ty, lx, ph) in enumerate(levels):
        nxt = levels[i + 1][0] if i + 1 < len(levels) else G - 0.3
        f = noise1(seed + i, 5)
        top = [(-0.4 + (lx + 0.4) * t, ty + 0.05 * f(t)) for t in (k / 16 for k in range(17))]
        lip = _open([top[-1], (lx + 0.16, ty - 0.06), (lx + 0.3, ty - 0.3), (lx + 0.36, nxt - 0.15)], 5)[1:]
        cv.add([[(-0.4, nxt - 0.15)] + top + lip], 'scales', layer)
        cv.add([ribbon([(px, py - 0.05) for px, py in top] + [(lx + 0.14, ty - 0.1)], 0.055)], 'solid', layer)   # the bund
        cuts = []
        for row, yy in enumerate((ty - 0.2, ty - 0.47)):         # sky caught in the flooded plots
            xx = -0.2 + rnd.uniform(0, 0.6) + row * 0.45
            while xx < lx - 0.5:
                L = min(rnd.uniform(0.6, 1.5), lx - 0.3 - xx)
                if L > 0.3 and yy > nxt + 0.12:
                    cuts.append(ribbon([(xx, yy), (xx + L, yy + rnd.uniform(-0.01, 0.01))], 0,
                                       wf=lambda t: 0.03 * math.sin(math.pi * t) ** 0.5))
                xx += L + rnd.uniform(0.35, 0.8)
        cv.carve(cuts, layer)
        padi_row(cv, -0.2, lx - 1.35, ty + 0.01, ph, seed + 10 + i, layer, gap=0.3 * ph / 0.5)
        curls = []                                           # the water running for the lip
        for k in range(3):
            cx = lx - 1.1 + k * 0.42
            r = 0.09 + 0.02 * k
            curls.append(scroll(cx + r * 0.4, ty + r + 0.02, r, r * 0.34, 1.2, a0=180, cw=True,
                                tail=[(cx - r * 1.8, ty), (cx - r * 0.8, ty + 0.06)]))
        cv.add(curls, 'solid', layer)
        if i + 1 < len(levels) or nxt > G:
            spill(cv, lx + 0.1, ty - 0.02, max(nxt, G) + 0.02, seed=seed + 20 + i, layer=layer)

def spill(cv, x, y0, y1, w=0.065, seed=1, layer='mid'):
    """Water pouring off a lip at (x, y0) in three arcing strands, landing at y1
    in a pair of curls and a few drops."""
    rnd = random.Random(seed)
    polys = []
    for k in range(3):
        d = k * 0.12
        path = _open([(x - 0.14 + d, y0 + 0.03), (x + 0.2 + d * 1.5, y0 - 0.02),
                      (x + 0.44 + d * 2, y0 - (y0 - y1) * 0.4), (x + 0.52 + d * 2.3, y1 + 0.04)], 6)
        polys.append(ribbon(path, w * (1 - 0.25 * k), w * (0.7 - 0.15 * k)))
    sx = x + 0.7
    polys.append(scroll(sx + 0.26, y1 + 0.22, 0.14, 0.045, 1.2, a0=180, cw=True, tail=[(sx - 0.02, y1), (sx + 0.1, y1 + 0.14)]))
    polys.append(scroll(sx - 0.22, y1 + 0.17, 0.1, 0.035, 1.2, a0=0, cw=False, tail=[(sx + 0.02, y1), (sx - 0.1, y1 + 0.12)]))
    for i in range(4):
        polys.append(ellipse(sx + rnd.uniform(-0.35, 0.35), y1 + rnd.uniform(0.3, 0.5), 0.025, 0.032, n=10))
    return cv.add(polys, 'solid', layer)

def gong(cv, x, y, s=1.0, layer='mid'):
    """Tetawak on a carved frame: two posts, a beam with curled ends, the gong
    hung on cords, its boss and rings cut out."""
    P = lambda pts: xf(pts, x, y, s=s)
    frame = [P(rect(-0.68, 0.0, -0.58, 2.3)), P(rect(0.58, 0.0, 0.68, 2.3)),
             P(ribbon([(-0.85, 2.3), (0.85, 2.3)], 0.06)),
             P(scroll(-0.95, 2.42, 0.13, 0.04, 1.2, a0=0, cw=False, tail=[(-0.8, 2.34), (-0.86, 2.36)])),
             P(scroll(0.95, 2.42, 0.13, 0.04, 1.2, a0=180, cw=True, tail=[(0.8, 2.34), (0.86, 2.36)])),
             P(rect(-0.82, 0.0, -0.44, 0.1)), P(rect(0.44, 0.0, 0.82, 0.1)),
             P(ribbon([(-0.2, 2.26), (-0.12, 1.9)], 0.012)), P(ribbon([(0.2, 2.26), (0.12, 1.9)], 0.012))]
    cv.add(frame, 'solid', layer)
    cv.add([P(ellipse(0.0, 1.42, 0.5, 0.52, n=48))], 'dots', layer)
    cv.carve([P(ribbon(arc_pts(0.0, 1.42, 0.36, 0, 360, 40), 0.012)), P(ribbon(arc_pts(0.0, 1.42, 0.17, 0, 360, 24), 0.03))],
             layer)
    cv.add([P(ellipse(0.0, 1.42, 0.09, n=20))], 'solid', layer)
    cv.add([P(ribbon(arc_pts(0.0, 1.42, r, -38, 38, 12), 0.022, 0.006)) for r in (0.78, 0.98)] +
           [P(ribbon(arc_pts(0.0, 1.42, 0.98, 142, 218, 12), 0.006, 0.02))], 'solid', layer)

def ulam_raja(cv, x, y, h, seed=1, layer='mid', n=6):
    """Ulam raja: thin stems carrying feathery leaves and small daisy flowers."""
    rnd = random.Random(seed)
    polys = []
    for i in range(n):
        a = math.radians(90 + (i - (n - 1) / 2) * 13 + rnd.uniform(-5, 5))
        L = h * rnd.uniform(0.75, 1.0)
        tip = (x + L * math.cos(a), y + L * math.sin(a))
        stem = _open([(x, y), (x + L * 0.45 * math.cos(a) + 0.03, y + L * 0.5 * math.sin(a)), tip], 5)
        polys.append(ribbon(stem, 0.012 * h ** 0.5, 0.006))
        for k in range(2, len(stem) - 1, 2):
            px, py = stem[k]
            side = 1 if k % 4 else -1
            base_a = math.degrees(a) + side * 50
            rach = (px + 0.12 * h * math.cos(math.radians(base_a)), py + 0.12 * h * math.sin(math.radians(base_a)))
            polys.append(ribbon([(px, py), rach], 0.004))
            for j in range(4):
                t = (j + 1) / 5
                q = (px + (rach[0] - px) * t, py + (rach[1] - py) * t)
                for sd in (-1, 1):
                    polys.append(leaf(q[0], q[1], base_a + sd * 55, 0.05 * h, 0.006 * h ** 0.5))
        for k in range(8):                                  # flower: petals round a disc
            polys.append(leaf(tip[0], tip[1], 45 * k, 0.045 * h ** 0.8, 0.012 * h ** 0.6))
        polys.append(ellipse(tip[0], tip[1], 0.022 * h ** 0.7, n=12))
    return cv.add(polys, 'solid', layer)

def kesum(cv, x, y, h, seed=1, layer='mid', n=5):
    """Daun kesum: a bunch of jointed stems with long pointed leaves."""
    rnd = random.Random(seed)
    polys = []
    for i in range(n):
        a = math.radians(90 + (i - (n - 1) / 2) * 15 + rnd.uniform(-5, 5))
        L = h * rnd.uniform(0.8, 1.0)
        stem = _open([(x, y), (x + L * 0.5 * math.cos(a), y + L * 0.5 * math.sin(a)), (x + L * math.cos(a), y + L * math.sin(a))], 4)
        polys.append(ribbon(stem, 0.009 * h ** 0.5, 0.005))
        for k in range(1, len(stem), 2):
            px, py = stem[k]
            sd = 1 if k % 4 == 1 else -1
            polys.append(leaf(px, py, math.degrees(a) + sd * 38, 0.3 * h * (1 - 0.06 * k), 0.022 * h, bend=-0.02 * h * sd))
    return cv.add(polys, 'solid', layer)

def bakul(cv, x, y, w, h, layer='mid'):
    """A woven basket, flared, with a rolled rim."""
    body = [(x - 0.4 * w, y), (x + 0.4 * w, y), (x + 0.5 * w, y + h), (x - 0.5 * w, y + h)]
    cv.add([body], 'grid', layer)
    cv.add([ribbon([(x - 0.53 * w, y + h), (x + 0.53 * w, y + h)], 0.05 * h + 0.02)], 'solid', layer)

def kunyit(cv, x, y, h, layer='mid', flip=False):
    """Turmeric leaves: broad blades with a carved midrib and veins."""
    polys, cuts = [], []
    for i, (a, L) in enumerate(((112, 1.0), (92, 1.1), (72, 0.95), (128, 0.75), (55, 0.8))):
        a = 180 - a if flip else a
        polys.append(leaf(x, y, a, h * L, h * 0.13, bend=h * 0.08 * (1 if a < 90 else -1)))
        d = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        cuts.append(ribbon([(x + d[0] * h * 0.2 * L, y + d[1] * h * 0.2 * L), (x + d[0] * h * 0.85 * L, y + d[1] * h * 0.85 * L)],
                           0.006))
    cv.add(polys, 'edge', layer)
    cv.carve(cuts, layer)

def ulam_tray(cv, cx, y, w, seed=1, layer='mid'):
    """A talam of nasi ulam: the rice heaped and flecked with shredded herbs,
    toasted coconut and flaked fish, a sprig on top. Returns the heap's top."""
    rnd = random.Random(seed)
    tray = [(cx - 0.53 * w, y + 0.11 * w), (cx - 0.5 * w, y + 0.05 * w), (cx - 0.32 * w, y), (cx + 0.32 * w, y),
            (cx + 0.5 * w, y + 0.05 * w), (cx + 0.53 * w, y + 0.11 * w), (cx + 0.45 * w, y + 0.085 * w),
            (cx - 0.45 * w, y + 0.085 * w)]
    hh = 0.27 * w
    mound = _open([(-0.44, 0.06), (-0.36, 0.42), (-0.2, 0.8), (0.0, 0.96), (0.22, 0.8), (0.38, 0.4), (0.44, 0.06)], 6)
    cv.add([xf(mound, cx, y + 0.07 * w, s=w, sy=hh)], 'dots', layer)
    shreds = []
    for i in range(22):                                   # herb slivers lying on the heap
        t = rnd.uniform(-0.36, 0.36)
        top = (1 - (abs(t) / 0.44) ** 2.2) * 0.94
        py = y + 0.07 * w + hh * top
        slope = -math.degrees(math.atan(2.2 * hh / w * (abs(t) / 0.44) ** 1.2 * 2.3)) * (1 if t > 0 else -1)
        ang = (slope if i % 2 else slope + 180) + rnd.uniform(-25, 25)
        shreds.append(leaf(cx + t * w, py - 0.005 * w, ang, rnd.uniform(0.05, 0.09) * w, 0.011 * w, bend=0.01 * w))
    for k in range(7):                                    # ulam raja sprig on the crown
        shreds.append(leaf(cx + 0.02 * w, y + 0.07 * w + hh * 0.94, 40 + k * 17, 0.14 * w, 0.014 * w, bend=0.012 * w))
    cv.add([tray] + shreds, 'solid', layer)
    cv.carve([ribbon([(cx - 0.44 * w, y + 0.06 * w), (cx + 0.44 * w, y + 0.06 * w)], 0.006 * w)] +
             [W.diamond(cx + k * 0.08 * w, y + 0.03 * w, 0.03 * w, 0.025 * w)[0] for k in range(-4, 5)] +
             [ellipse(cx + rnd.uniform(-0.3, 0.3) * w, y + 0.07 * w + hh * rnd.uniform(0.15, 0.5), 0.012 * w, 0.008 * w, n=8)
              for _ in range(9)], layer)
    return y + 0.07 * w + hh

def heap_plate(cv, cx, y, w, kind='flakes', seed=1, layer='mid'):
    """A side plate with a small heap: 'flakes' (fish) or 'kerisik' (coconut)."""
    rnd = random.Random(seed)
    plate(cv, cx, y, w, layer)
    polys = []
    for i in range(9 if kind == 'flakes' else 14):
        t = rnd.uniform(-0.3, 0.3)
        hy = 0.16 * w * (1 - (abs(t) / 0.34) ** 2)
        if kind == 'flakes':
            polys.append(ellipse(cx + t * w, y + 0.07 * w + hy * rnd.uniform(0.3, 0.9), 0.06 * w, 0.025 * w, n=12,
                                 rot=rnd.uniform(-40, 40)))
        else:
            polys.append(ellipse(cx + t * w, y + 0.07 * w + hy * rnd.uniform(0.2, 0.9), 0.025 * w, n=8))
    polys.append(_open([(cx - 0.33 * w, y + 0.07 * w), (cx, y + 0.22 * w), (cx + 0.33 * w, y + 0.07 * w)], 4))
    cv.add(polys, 'solid', layer)

def back_fields(cv, seed=1):
    """Blurred backdrop shared by the beats: Jerai, far padi, a barn and palms."""
    jerai(cv, 6.0, G + 0.6, 12.5, 4.6, seed=seed)
    hills(cv, 9.0, 21.0, G + 0.5, 0.7, seed=seed + 1)
    padi_row(cv, -0.2, 20.6, G + 0.75, 0.32, seed + 2, 'back', gap=0.26)

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def kedah_land(cv):
    """Wide padi terraces step down level by level under Gunung Jerai, water
    spilling from each lip to the next; a rice barn up top, a buffalo below."""
    jerai(cv, 5.2, G + 1.8, 13.0, 5.0, seed=3)
    hills(cv, 10.0, 21.0, G + 0.9, 0.9, seed=4)
    cloud(cv, 2.6, 7.15, 0.8, 'back', seed=2)
    cloud(cv, 15.6, 6.9, 0.65, 'back', flip=True, seed=5)
    birds(cv, 14.2, 5.9, 4, 0.55, seed=6, layer='back', flip=True)
    palm(cv, 5.3, 4.25, 2.0, lean=-0.14, seed=31, fronds=8)
    jelapang(cv, 2.6, 4.32, 0.78)
    terraces(cv, [(4.3, 4.6, 0.3), (3.62, 7.3, 0.36), (2.94, 10.0, 0.42), (2.26, 12.7, 0.48), (1.6, 15.3, 0.52)], seed=12)
    pondok(cv, 9.0, 2.98, 0.48)
    palm(cv, 11.2, 2.3, 2.6, lean=0.1, seed=32, fronds=8)
    field(cv, 15.0, 20.6, G + 0.12, h=0.5, rows=2, seed=40)
    kerbau(cv, 17.6, G + 0.04, 0.95)
    egret(cv, 13.6, G + 0.04, 1.1, pose='peck')
    egret(cv, 8.5, 6.2, 0.8, pose='fly', flip=True, layer='back')
    ground(cv, 'earth', seed=7)
    frame_edges(cv, seed=8, left='banana', right='none')

def kedah_people(cv):
    """Farmers time the gates field by field: one winds gate A open and the water
    runs into her plot, a man strikes the gong, the next gate-keeper turns his wheel."""
    back_fields(cv, seed=21)
    for gx, gs in ((7.6, 0.42), (13.6, 0.38), (19.0, 0.34)):
        sluice(cv, gx, G + 0.95, gs, layer='back')
    cloud(cv, 4.4, 7.0, 0.7, 'back', seed=9)
    birds(cv, 15.0, 6.3, 3, 0.5, seed=11, layer='back', flip=True)
    padi_row(cv, 6.1, 10.0, G + 0.42, 0.55, 51, gap=0.3)
    sluice(cv, 5.4, G + 0.05, 1.0, open_h=1.12)
    water_run(cv, 6.25, 9.9, G + 0.02, 0.5, flow=1, seed=3)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kurung', pose='crank', rod_to=-0.25), 3.35, G, 3.3)
    gong(cv, 13.0, G + 0.02, 1.15)
    W.place_figure(cv, dict(head='refined', hat='songkok', costume='baju', pose='kedah_strike', item_f='kedah_mallet',
                            rod_to=-0.25), 10.45, G, 3.3)
    sluice(cv, 15.4, G + 0.05, 1.0, open_h=0.35)
    padi_row(cv, 17.0, 20.6, G + 0.3, 0.5, 52, gap=0.3)
    W.place_figure(cv, dict(head='old', hat='caping', costume='farmer', pose='crank', scarf=True, rod_to=-0.25),
                   17.45, G, 3.3, flip=True)
    egret(cv, 9.3, G + 0.4, 0.9, flip=True, pose='peck')
    ground(cv, 'earth', seed=17)
    frame_edges(cv, seed=18, left='banana', right='none')

def tikar(cv, x0, x1, y, layer='mid'):
    """A mengkuang mat spread on the ground, seen low: a thin plaited band
    with a bound edge and a rolled end."""
    cv.add([[(x0, y), (x1, y), (x1 - 0.3, y + 0.24), (x0 + 0.3, y + 0.24)]], 'grid', layer)
    cv.add([ribbon([(x0, y + 0.015), (x1, y + 0.015)], 0.03), ellipse(x1 - 0.05, y + 0.17, 0.17, 0.16)], 'edge', layer)

def daun_talam(cv, cx, y, w, seed=1, layer='mid'):
    """A banana leaf laid over a low talam, its torn ends hanging past the rim
    (drawn after the heap so the rice sits on it)."""
    rnd = random.Random(seed)
    top = y + 0.09 * w
    edge = [(cx - 0.7 * w, top - 0.13 * w), (cx - 0.6 * w, top - 0.01 * w), (cx - 0.3 * w, top + 0.012 * w),
            (cx + 0.3 * w, top + 0.012 * w), (cx + 0.62 * w, top - 0.01 * w), (cx + 0.74 * w, top - 0.14 * w)]
    up_ = _open(edge, 6)
    lo = [(x, yy - 0.036 * w) for x, yy in reversed(up_)]
    cv.add([up_ + lo], 'edge', layer)
    cuts = [ribbon(up_[2:-2], 0.003 * w)]
    for k in range(9):                                  # torn slits at the leaf's veins
        t = rnd.uniform(0.04, 0.96)
        i = int(t * (len(up_) - 1))
        px, py = up_[i]
        cuts.append([(px - 0.006 * w, py - 0.03 * w), (px + 0.006 * w, py - 0.03 * w), (px + 0.012 * w, py + 0.01 * w)])
    cv.carve(cuts, layer)

def herb_saucer(cv, cx, y, w, kind='kesum', seed=1, layer='mid'):
    """A small piring of one herb: 'kesum' leaves, 'kantan' sliced buds,
    'raja' sprigs."""
    rnd = random.Random(seed)
    plate(cv, cx, y, w, layer)
    base = y + 0.07 * w
    polys = []
    if kind == 'kesum':
        for k in range(9):
            polys.append(leaf(cx + rnd.uniform(-0.25, 0.25) * w, base, rnd.uniform(25, 155), 0.32 * w, 0.045 * w,
                              bend=rnd.uniform(-0.03, 0.03) * w))
    elif kind == 'kantan':
        for k in range(7):
            polys.append(ellipse(cx + (k - 3) * 0.09 * w, base + 0.05 * w + 0.04 * w * (k % 2), 0.07 * w, 0.05 * w, n=14))
    else:
        for k in range(5):
            a = 60 + 15 * k
            tip = (cx + 0.3 * w * math.cos(math.radians(a)), base + 0.36 * w * math.sin(math.radians(a)))
            polys.append(ribbon([(cx, base), tip], 0.008 * w))
            polys += [leaf(tip[0], tip[1], 45 * j, 0.06 * w, 0.02 * w) for j in range(8)]
    cv.add(polys, 'solid', layer)
    if kind == 'kantan':
        cv.carve([ellipse(cx + (k - 3) * 0.09 * w, base + 0.05 * w + 0.04 * w * (k % 2), 0.03 * w, 0.02 * w, n=10)
                  for k in range(7)], layer)

def kedah_food(cv):
    """Nasi ulam mixed on a mat at the field's edge: the cook kneels at a
    banana-leaf tray and folds the herbs through the rice with her senduk,
    saucers of herbs laid out round it, a farmer waiting with his plate."""
    back_fields(cv, seed=31)
    pondok(cv, 16.6, G + 0.9, 0.5, layer='back')
    cloud(cv, 15.4, 7.0, 0.7, 'back', flip=True, seed=12)
    raintree(cv, 1.9, G, 4.7, seed=34)
    tikar(cv, 5.2, 17.3, G + 0.02)
    mat = G + 0.14
    top = ulam_tray(cv, 10.9, mat, 2.9, seed=4)
    daun_talam(cv, 10.9, mat, 2.9, seed=5)
    for i, (dx, hh, cw) in enumerate(((-0.45, 1.3, False), (0.4, 1.55, True))):
        steam(cv, 10.9 + dx, top + 0.25, hh, cw=cw, seed=10 + i)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kedah_kurung_kneel', pose='kedah_kneelmix',
                            item_f='kedah_senduk', rod_to=-0.25), 8.35, mat, 3.6)
    herb_saucer(cv, 6.1, mat, 1.3, 'kesum', seed=2)
    herb_saucer(cv, 7.25, mat, 1.1, 'raja', seed=6)
    herb_saucer(cv, 13.65, mat, 1.2, 'kantan', seed=3)
    heap_plate(cv, 14.7, mat, 1.25, 'kerisik', seed=4)
    W.place_figure(cv, dict(head='old', hat='caping', costume='farmer', pose='kedah_wait', item_f='bowl', scarf=True,
                            legs='kedah_kneel', rod_to=-0.25), 16.5, mat, 3.4, flip=True)
    bakul(cv, 3.8, G, 1.2, 0.6)
    ulam_raja(cv, 3.8, G + 0.55, 2.0, seed=3)
    bakul(cv, 18.2, G, 1.1, 0.55)
    kunyit(cv, 18.2, G + 0.5, 1.8, flip=True)
    kesum(cv, 2.2, G, 1.9, seed=4)
    ground(cv, 'earth', seed=37)
    frame_edges(cv, seed=38, left='none', right='banana')

# =====================================================================
# rig parts (registered once, prefixed kedah_)
# =====================================================================

def _it_gatekey(g, ang, spec):
    """Mak Semah's staff: the long iron gate key, a hand wheel on top and the
    gate charm hanging from it on a cord."""
    x = g[0]
    cy, r = 1.1, 0.068
    polys = [ribbon([(x, 0.0), (x, cy - 0.02)], 0.0078, 0.0068), rect(x - 0.016, -0.004, x + 0.016, 0.03),
             ellipse(x, cy, r, n=40)]
    cuts = []
    for i in range(6):
        a = math.radians(60 * i + 15)
        polys.append(ribbon([(x + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a)),
                             (x + r * 1.32 * math.cos(a), cy + r * 1.32 * math.sin(a))], 0.006, 0.0095))
        a0, a1 = 60 * i + 15 + 11, 60 * i + 75 - 11
        cuts.append(arc_pts(x, cy, r * 0.76, a0, a1, 8) + arc_pts(x, cy, r * 0.26, a1, a0, 4))
    cord = _open([(x + 0.004, cy - r * 0.6), (x + 0.03, cy - 0.12), (x + 0.036, cy - 0.17)], 5)
    polys += [ribbon(cord, 0.0024), rect(x + 0.016, cy - 0.235, x + 0.058, cy - 0.17),
              [(x + 0.012, cy - 0.17), (x + 0.062, cy - 0.17), (x + 0.037, cy - 0.15)]]
    cuts.append(rect(x + 0.024, cy - 0.226, x + 0.05, cy - 0.205))
    return polys, 'solid', cuts

def _it_mallet(g, ang, spec):
    """Gong beater held up, ready to strike: a stick and a padded head."""
    a = math.radians(ang - 4)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.26 * d[0], g[1] + 0.26 * d[1])
    return [ribbon([(g[0] - 0.04 * d[0], g[1] - 0.04 * d[1]), end], 0.0065),
            ellipse(end[0] + 0.02 * d[0], end[1] + 0.02 * d[1], 0.034, n=16)], 'solid', []

def _it_senduk(g, ang, spec):
    """Wooden senduk lifting a scoop of rice: a long handle with a knob and a
    broad oval bowl, a groove carved down the handle."""
    a = math.radians(ang + 52)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.24 * d[0], g[1] + 0.24 * d[1])
    bowl_c = (end[0] + 0.035 * d[0], end[1] + 0.035 * d[1])
    return [ribbon([(g[0] - 0.05 * d[0], g[1] - 0.05 * d[1]), end], 0.0075, 0.006),
            ellipse(g[0] - 0.055 * d[0], g[1] - 0.055 * d[1], 0.011, n=12),
            ellipse(bowl_c[0], bowl_c[1], 0.045, 0.03, rot=math.degrees(a)),
            ellipse(bowl_c[0] - 0.004, bowl_c[1] + 0.022, 0.036, 0.026, n=16)], 'solid',         [ribbon([(g[0] + 0.02 * d[0], g[1] + 0.02 * d[1]), (g[0] + 0.2 * d[0], g[1] + 0.2 * d[1])], 0.0022)]

def _it_sheaf(g, ang, spec):
    """A sheaf of ripe padi held upright, tied at the hand, heads bowing out."""
    rnd = random.Random(7)
    polys = [ellipse(g[0], g[1] + 0.005, 0.016, 0.03)]
    for i in range(9):
        sd = (i - 4) / 4
        base = (g[0] + sd * 0.006, g[1] - 0.09)
        top = (g[0] + sd * 0.05, g[1] + 0.2 + 0.03 * (1 - abs(sd)))
        bow = (top[0] + sd * 0.06 + (0.02 if sd == 0 else 0), top[1] - 0.06 - rnd.uniform(0, 0.03))
        path = _open([base, (g[0] + sd * 0.025, g[1] + 0.08), top, bow], 5)
        polys.append(ribbon(path, 0.0034, 0.0016))
        for k in range(len(path) // 2, len(path)):
            px, py = path[k]
            polys.append(ellipse(px + 0.004 * (1 if sd >= 0 else -1), py, 0.0055, 0.0085, n=8))
    for i in range(4):
        polys.append(leaf(g[0], g[1] + 0.02, 70 + i * 13, 0.15, 0.007, bend=0.01))
    return polys, 'solid', [ribbon([(g[0] - 0.014, g[1] + 0.012), (g[0] + 0.014, g[1] + 0.012)], 0.0025)]

W.register(W.ITEMS2, 'kedah_gatekey', _it_gatekey)
W.register(W.ITEMS2, 'kedah_sheaf', _it_sheaf)
W.register(W.ITEMS2, 'kedah_mallet', _it_mallet)
W.register(W.ITEMS2, 'kedah_senduk', _it_senduk)
W.register(W.POSES, 'kedah_staff', {'f': (30, 70), 'b': (-50, 50), 'lean': 2, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'kedah_strike', {'f': (64, 18), 'b': (-14, -18), 'lean': 6, 'legs': 'walk', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'kedah_mix', {'f': (62, 34), 'b': (48, 46), 'lean': 9, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'})
W.register(W.LEGS, 'kedah_kneel', ((0.17, 0.065), (-0.1, 0.045), (0.14, 0.065), (-0.12, 0.05), 0.3))
W.register(W.POSES, 'kedah_kneelmix', {'f': (78, 4), 'b': (52, 62), 'lean': 12, 'legs': 'kedah_kneel', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'kedah_wait', {'f': (52, 60), 'b': (30, 50), 'lean': 4, 'legs': 'kedah_kneel', 'hf': 'grip', 'hb': 'open'})
W.register(W.COSTUMES, 'kedah_kurung_kneel', dict(W.COSTUMES['kurung'], legs='trousers'))

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def _wood(name, rgb, dark, rough=0.62, axis='X', scale=7.0):
    """Matte carved wood: soft grain lines running along `axis`' normal plane,
    broken up by noise (no clearcoat)."""
    m = _mat(name, rgb, rough)
    nt = m.node_tree
    bs = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = axis
    wv.inputs['Scale'].default_value = scale
    wv.inputs['Distortion'].default_value = 1.6
    wv.inputs['Detail'].default_value = 4.0
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].color = (*rgb, 1)
    ramp.color_ramp.elements[0].position = 0.25
    mix = nt.nodes.new('ShaderNodeMath')
    mix.operation = 'MULTIPLY_ADD'
    mix.inputs[1].default_value = 0.75
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(wv.outputs['Fac'], mix.inputs[0])
    nt.links.new(nz.outputs['Fac'], mix.inputs[2])
    nt.links.new(mix.outputs[0], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bs.inputs['Base Color'])
    return m

def _speckle(name, base, flecks, scale=26.0):
    """Rice flecked with herbs: noise bands mapped to a constant colour ramp."""
    m = _mat(name, base, 0.7)
    nt = m.node_tree
    bs = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale
    nz.inputs['Detail'].default_value = 2.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    els[0].color = (*base, 1)
    els[1].position = 0.999
    els[1].color = (*base, 1)
    for pos, col in flecks:
        e = els.new(pos)
        e.color = (*col, 1)
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bs.inputs['Base Color'])
    return m

def icon_food_nasi_ulam(seed=2):
    """Nasi ulam: a heap of rice flecked green with shredded kesum, ulam raja and
    turmeric leaf and brown with kerisik, on a banana leaf on a plate, an ulam
    raja sprig on top, lime and chilli beside it."""
    rnd = random.Random(seed)
    porcelain = _mat('Porcelain', (0.93, 0.91, 0.86), 0.35)
    green = _mat('Green', (0.08, 0.32, 0.08), 0.4)
    _lathe('Plate', [(0.0, 0.0), (0.7, 0.0), (0.74, 0.03), (1.25, 0.1), (1.42, 0.2), (1.44, 0.23), (1.38, 0.22),
                     (1.2, 0.14), (0.7, 0.08), (0.0, 0.08)], porcelain, 72)
    _torus('Rim', (0, 0, 0.215), 1.41, 0.014, green)
    _blob('BananaLeaf', (0, 0, 0.09), (1.15, 1.0, 0.012), (0, 0, 0.4), _mat('Leaf', (0.1, 0.36, 0.08), 0.45), 32)
    rice = _speckle('Rice', (0.95, 0.93, 0.84), ((0.56, (0.1, 0.42, 0.08)), (0.6, (0.32, 0.55, 0.12)),
                                                (0.64, (0.95, 0.93, 0.84)), (0.68, (0.5, 0.3, 0.1)), (0.71, (0.95, 0.93, 0.84))))
    R, H = 0.85, 0.5
    prof = [(R * (1 - k / 14) ** 0.8 if k < 14 else 0.0, 0.1 + H * (1 - (1 - k / 14) ** 2.0)) for k in range(15)]
    heap = _lathe('Heap', [(R, 0.1)] + prof[1:], rice, 48)
    for v in heap.data.vertices:                            # lumpy, not turned
        x, y, z = v.co
        k = 1 + 0.07 * math.sin(5 * math.atan2(y, x) + 3 * z) * math.sin(9 * z + 1.3)
        v.co = (x * k, y * k, z * (1 + 0.04 * math.sin(4 * math.atan2(y, x))))
    herb = [_mat('Kesum', (0.1, 0.42, 0.1), 0.55), _mat('Raja', (0.2, 0.55, 0.12), 0.55),
            _mat('Turmeric', (0.55, 0.62, 0.15), 0.55)]
    kerisik = _mat('Kerisik', (0.48, 0.28, 0.1), 0.75)
    for i in range(110):
        r = R * math.sqrt(rnd.uniform(0.0, 0.9))
        a = rnd.uniform(0, TAU)
        z = 0.1 + H * (1 - (r / R) ** 2.2)
        if i % 4 == 3:
            _blob('Ker%d' % i, (r * math.cos(a), r * math.sin(a), z + 0.008), (0.028, 0.022, 0.014), (0, 0, a), kerisik, 8)
        else:
            _box('Herb%d' % i, (r * math.cos(a), r * math.sin(a), z + 0.01), (0.15, 0.024, 0.01),
                 (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), rnd.uniform(0, TAU)), herb[i % 3])
    sprig = _mat('Sprig', (0.14, 0.48, 0.12), 0.5)
    for k in range(7):
        a = TAU * k / 7
        _blob('Leaf%d' % k, (0.12 * math.cos(a), 0.12 * math.sin(a), 0.1 + H + 0.03), (0.17, 0.05, 0.012),
              (0.5 * math.sin(a), -0.5 * math.cos(a), a), sprig, 12)
    _blob('Bloom', (0, 0, 0.1 + H + 0.08), (0.06, 0.06, 0.03), (0, 0, 0), _mat('Bloom', (0.9, 0.45, 0.6), 0.5), 12)
    lime = _mat('Lime', (0.3, 0.6, 0.1), 0.45)
    flesh = _mat('LimeFlesh', (0.75, 0.85, 0.35), 0.55)
    _blob('Lime', (0.95, -0.55, 0.2), (0.17, 0.17, 0.12), (0, 0, 0), lime, 20)
    _blob('LimeCut', (0.95, -0.55, 0.27), (0.15, 0.15, 0.02), (0, 0, 0), flesh, 20)
    chili = _mat('Chilli', (0.8, 0.07, 0.04), 0.35)
    _tube('Chilli', [(-1.05, -0.4, 0.17), (-0.85, -0.6, 0.2), (-0.62, -0.72, 0.18), (-0.45, -0.76, 0.15)], 0.045, chili)
    _tube('Stalk', [(-1.05, -0.4, 0.17), (-1.12, -0.32, 0.22)], 0.018, sprig)
    return (0, -5.3, 4.1), (0, 0, 0.22)

def icon_item_gate_charm():
    """Irrigation-gate charm: a carved merbau sluice gate in miniature, its
    brass hand wheel on the spindle, hung on a red cord with a tassel."""
    from mathutils import Euler
    wood = _wood('Wood', (0.4, 0.19, 0.08), (0.2, 0.08, 0.03), axis='X')
    dark = _wood('Plank', (0.27, 0.12, 0.05), (0.13, 0.05, 0.02), 0.7, axis='Z', scale=9.0)
    brass = _mat('Brass', (0.8, 0.58, 0.22), 0.38, metal=1.0)
    cord = _mat('Cord', (0.62, 0.08, 0.06), 0.8)
    parts = []
    for sx in (-1, 1):
        parts.append(_box('Post%d' % sx, (sx * 0.52, 0, 0.62), (0.18, 0.2, 1.24), (0, 0, 0), wood))
        parts.append(_lathe('Cap%d' % sx, [(0.0, 1.24), (0.15, 1.24), (0.15, 1.28), (0.08, 1.38), (0.0, 1.44)], wood, 4,
                            smooth=False))
        parts[-1].location = (sx * 0.52, 0, 0)
        parts[-1].rotation_euler = (0, 0, math.radians(45))
    parts.append(_box('Beam', (0, 0, 1.08), (1.3, 0.16, 0.14), (0, 0, 0), wood))
    for k in range(4):                                    # the plank gate, raised a little
        parts.append(_box('Plank%d' % k, (0, 0.02, 0.32 + 0.17 * k), (0.84, 0.08, 0.15), (0, 0, 0), dark))
    parts.append(_box('Sill', (0, 0, 0.06), (1.3, 0.24, 0.12), (0, 0, 0), wood))
    parts.append(_lathe('Spindle', [(0.0, 0.85), (0.03, 0.85), (0.03, 1.5), (0.0, 1.5)], brass, 16))
    wh = [_torus('Wheel', (0, 0, 0), 0.3, 0.028, brass, seg=48)]
    for k in range(6):
        a = TAU * k / 6
        wh.append(_box('Spoke%d' % k, (0.15 * math.cos(a), 0.15 * math.sin(a), 0), (0.3, 0.03, 0.03), (0, 0, a), brass))
        wh.append(_blob('Knob%d' % k, (0.36 * math.cos(a), 0.36 * math.sin(a), 0), (0.045, 0.045, 0.045), (0, 0, 0), brass, 12))
    wh.append(_blob('Hub', (0, 0, 0), (0.07, 0.07, 0.05), (0, 0, 0), brass, 16))
    hub = bpy.data.objects.new('WheelPivot', None)
    bpy.context.scene.collection.objects.link(hub)
    for ob in wh:
        ob.parent = hub
    hub.location = (0, 0, 1.5)
    hub.rotation_euler = Euler((math.radians(90), 0, 0))
    parts.append(hub)
    loop = [(0.0, 0.0, 1.5 + 0.36)] + [(0.22 * math.sin(TAU * k / 16), 0.0, 1.86 + 0.5 * (1 - math.cos(TAU * k / 16)) * 0.5)
                                       for k in range(1, 16)] + [(0.0, 0.0, 1.86)]
    parts.append(_tube('Cord', loop, 0.022, cord))
    tassel = _tube('Tail', [(0.52, 0, 1.44), (0.6, -0.05, 1.2), (0.66, -0.1, 0.95)], 0.02, cord)
    parts.append(tassel)
    parts.append(_lathe('Tassel', [(0.0, 0.62), (0.07, 0.66), (0.05, 0.9), (0.02, 0.95), (0.0, 0.95)], cord, 16))
    parts[-1].location = (0.66, -0.1, 0.0)
    pivot = bpy.data.objects.new('Pivot', None)
    bpy.context.scene.collection.objects.link(pivot)
    for ob in parts:
        if ob.parent is None:
            ob.parent = pivot
    pivot.rotation_euler = Euler((0, 0, math.radians(-28)))
    pivot.scale = (1.15, 1.15, 1.15)
    return (0.9, -6.6, 3.8), (0.05, 0, 1.25)

# =====================================================================
# registry: what the CLI renders for this state
# =====================================================================

PUPPET = dict(body='female', hat='tudung', costume='kurung', pose='kedah_staff', item_f='kedah_gatekey',
              item_b='kedah_sheaf', cls={'top': 'lace'})              # Mak Semah
BEATS = {'land': kedah_land, 'people': kedah_people, 'food': kedah_food}
ICONS = {'food': icon_food_nasi_ulam, 'item': icon_item_gate_charm}
