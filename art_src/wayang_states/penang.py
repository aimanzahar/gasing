"""Penang: George Town's night market, three vendors cooking side by side, a
bowl of asam laksa at a kopitiam table, and Ah Kow ringing his vendor's bell."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props
# =====================================================================

def moon(cv, cx, cy, r, layer='back'):
    """Crescent moon, horns to the right."""
    outer = arc_pts(cx, cy, r, 112, 248, 24)
    inner = arc_pts(cx - 0.42 * r, cy, r * 0.93, 232, 128, 24)
    return cv.add([outer + inner], 'edge', layer)

def lantern(cx, cy, r):
    """Tanglung: ribbed oval with caps, a hanger and a tassel. Returns (polys, cuts)."""
    polys = [ellipse(cx, cy, r, r * 1.15, n=28), rect(cx - 0.45 * r, cy + 1.05 * r, cx + 0.45 * r, cy + 1.3 * r),
             rect(cx - 0.45 * r, cy - 1.3 * r, cx + 0.45 * r, cy - 1.05 * r),
             ribbon([(cx, cy + 1.3 * r), (cx, cy + 1.75 * r)], 0.05 * r),
             ribbon([(cx, cy - 1.3 * r), (cx, cy - 2.2 * r)], 0.09 * r, 0.16 * r)]
    cuts = [ribbon(_open([(cx + k * r * 0.62, cy - r * 0.9), (cx + k * r, cy), (cx + k * r * 0.62, cy + r * 0.9)], 4), 0.035 * r)
            for k in (-0.55, 0.0, 0.55)]
    return polys, cuts

def lantern_string(cv, x0, x1, y, sag, n, r=0.16, layer='mid', seed=1):
    """A sagging cord strung with lanterns."""
    rnd = random.Random(seed)
    path = [(x0 + (x1 - x0) * t, y - sag * 4 * t * (1 - t)) for t in (k / 24 for k in range(25))]
    polys, cuts = [ribbon(path, 0.012)], []
    for i in range(n):
        t = (i + 0.5) / n
        px, py = x0 + (x1 - x0) * t, y - sag * 4 * t * (1 - t)
        rr = r * rnd.uniform(0.85, 1.1)
        p, c = lantern(px, py - 1.75 * rr, rr)
        polys += p
        cuts += c
    cv.add(polys, 'edge', layer)
    cv.carve(cuts, layer)

def shophouse(cv, x, y, s=1.0, bays=2, layer='mid', seed=1, storeys=2):
    """George Town shophouse row: five-foot-way arches lit below, shuttered
    windows lit above with carved transoms, pilasters, a curled pediment and a
    tiled roof. x is the left end."""
    rnd = random.Random(seed)
    P = lambda pts: xf(pts, x, y, s=s)
    bw = 1.7
    w = bw * bays
    top = 1.75 + 1.4 * (storeys - 1) + 0.15
    rings = [P(rect(0.0, 0.0, w, top))]
    lit = []
    for b in range(bays):
        bx = bw * (b + 0.5)
        rings.append(P([(bx - 0.58, 0.0), (bx + 0.58, 0.0), (bx + 0.58, 1.05)] + arc_pts(bx, 1.05, 0.58, 0, 180, 14)[1:-1] +
                       [(bx - 0.58, 1.05)]))
        for f in range(storeys - 1):
            fy = 1.95 + 1.4 * f
            for wx in (-0.38, 0.38):
                rings.append(P([(bx + wx - 0.2, fy), (bx + wx + 0.2, fy), (bx + wx + 0.2, fy + 0.78)] +
                               arc_pts(bx + wx, fy + 0.78, 0.2, 0, 180, 8)[1:-1] + [(bx + wx - 0.2, fy + 0.78)]))
                lit.append((bx + wx, fy))
        lit.append((bx, -1.0))
    pid = cv.add_eo(rings, 'edge', layer)
    detail = []
    for b in range(bays + 1):                               # pilasters with capitals
        px = bw * b
        detail.append(P(rect(px - 0.09, 0.0, px + 0.09, top)))
        detail.append(P(rect(px - 0.14, 1.62, px + 0.14, 1.76)))
    detail.append(P(rect(-0.1, 1.68, w + 0.1, 1.86)))       # floor cornice / balcony band
    detail.append(P(rect(-0.12, top - 0.06, w + 0.12, top + 0.08)))
    for wx, fy in lit:                                       # mullions, half-open shutters, lanterns under the arches
        if fy < 0:
            p, c = lantern(wx, 0.88, 0.12)
            detail += [P(q) for q in p]
            cv.carve([P(q) for q in c], layer)
            detail.append(P(rect(wx - 0.5, 1.3, wx + 0.5, 1.55)))           # signboard
            continue
        detail.append(P(rect(wx - 0.012, fy, wx + 0.012, fy + 0.95)))
        detail.append(P(rect(wx - 0.2, fy + 0.5, wx + 0.2, fy + 0.53)))
        detail.append(P([(wx - 0.2, fy), (wx - 0.36, fy + 0.06), (wx - 0.36, fy + 0.72), (wx - 0.2, fy + 0.78)]))
    cv.add(detail, 'solid', layer, pid=pid)
    cv.carve([P(rect(bw * (b + 0.5) - 0.42, 1.36, bw * (b + 0.5) - 0.42 + 0.84 * t, 1.49))
              for b in range(bays) for t in (0.18,)] +
             [P(rect(bw * (b + 0.5) - 0.42 + 0.84 * k / 5 + 0.03, 1.36, bw * (b + 0.5) - 0.42 + 0.84 * (k + 1) / 5 - 0.03, 1.49))
              for b in range(bays) for k in range(1, 5)], layer)
    roof = P([(-0.25, top + 0.05), (w + 0.25, top + 0.05), (w - 0.1, top + 0.62), (0.1, top + 0.62)])
    cv.add([roof], 'scales', layer)
    ped = [P(scroll(w / 2 + sd * 0.55, top + 0.42, 0.16, 0.05, 1.2, a0=0 if sd < 0 else 180, cw=sd > 0,
                    tail=[(w / 2 + sd * 0.12, top + 0.72), (w / 2 + sd * 0.4, top + 0.6)])) for sd in (-1, 1)]
    ped.append(P([(w / 2 - 0.3, top + 0.55), (w / 2, top + 0.85), (w / 2 + 0.3, top + 0.55)]))
    cv.add(ped, 'solid', layer)

def pagoda(cv, x, y, s=1.0, layer='back', tiers=7):
    """Kek Lok Si's tower: stacked tiers with upswept eaves and a spire."""
    polys = []
    yy = 0.0
    for i in range(tiers):
        w = 0.62 - 0.055 * i
        h = 0.42 - 0.02 * i
        polys.append(rect(-w * 0.75, yy, w * 0.75, yy + h))
        polys.append([(-w - 0.12, yy + h + 0.06), (-w, yy + h), (w, yy + h), (w + 0.12, yy + h + 0.06),
                      (w * 0.7, yy + h + 0.14), (-w * 0.7, yy + h + 0.14)])
        yy += h + 0.12
    polys.append(ribbon([(0, yy), (0, yy + 0.45)], 0.045, 0.012))
    polys += [ellipse(0, yy + 0.12 * k, 0.07 - 0.012 * k, 0.03) for k in range(4)]
    cv.add([xf(p, x, y, s=s) for p in polys], 'edge', layer)

def wok(cx, y, w, tilt=0.0):
    """Kuali side-on with loop handles (polys)."""
    body = arc_pts(cx, y + 0.42 * w, 0.5 * w, 190, 350, 16, ry=0.42 * w)
    body = [(cx - 0.5 * w, y + 0.42 * w)] + body + [(cx + 0.5 * w, y + 0.42 * w)]
    out = [body] + [ribbon(arc_pts(cx + sd * 0.56 * w, y + 0.4 * w, 0.07 * w, 0, 360, 10), 0.016 * w) for sd in (-1, 1)]
    return [xf(p, rot=tilt, ox=cx, oy=y + 0.3 * w) for p in out]

def stall(cv, x, y, s=1.0, layer='mid', cook='wok', seed=1, canopy=True, lamp=True):
    """Hawker cart: spoked wheels, a slatted cabinet, a counter with jars, a
    zinc canopy on posts with a scalloped valance, a stove at one end."""
    rnd = random.Random(seed)
    P = lambda pts: xf(pts, x, y, s=s)
    for wx in (-0.75, 0.75):
        wheel(cv, x + wx * s, y + 0.33 * s, 0.33 * s, 8, layer, knobs=False)
    cv.add_eo([P(rect(-1.15, 0.45, 1.15, 1.25)), P(rect(-0.95, 0.6, -0.1, 1.1)), P(rect(0.1, 0.6, 0.95, 1.1))], 'edge', layer)
    cv.add([P(rect(-0.95 + 0.12 * k, 0.6, -0.9 + 0.12 * k, 1.1)) for k in range(8)] +
           [P(rect(0.15 + 0.12 * k, 0.6, 0.2 + 0.12 * k, 1.1)) for k in range(7)] +
           [P(rect(-1.3, 1.22, 1.3, 1.32)), P(ribbon([(-1.15, 0.9), (-1.6, 0.95)], 0.03))], 'solid', layer)
    jars = []
    for k in range(3):
        jx = -0.95 + 0.32 * k
        jars += [P(rect(jx - 0.1, 1.32, jx + 0.1, 1.62)), P(rect(jx - 0.12, 1.62, jx + 0.12, 1.67))]
    cv.add(jars, 'solid', layer)
    if canopy:
        cv.add([P(rect(-1.22, 1.3, -1.16, 2.65)), P(rect(1.16, 1.3, 1.22, 2.65))], 'solid', layer)
        roof = P([(-1.6, 2.55), (1.28, 2.7), (1.16, 2.93), (-1.45, 2.78)])
        val = []
        for k in range(9):
            vx = -1.58 + 0.31 * k
            val.append(P(arc_pts(vx + 0.155, 2.58 + 0.016 * k, 0.155, 180, 360, 8)))
        cv.add([roof] + val, 'slits', layer)
        if lamp:
            p, c = lantern(0.0, 2.15, 0.15)
            cv.add([P(q) for q in p] + [P(ribbon([(0.0, 2.6), (0.0, 2.45)], 0.01))], 'edge', layer)
            cv.carve([P(q) for q in c], layer)
    if cook == 'wok':                                        # stove at the right end, flames and a steaming wok
        cv.add_eo([P(rect(1.3, 0.0, 2.05, 1.05)), P([(1.48, 0.0), (1.87, 0.0), (1.87, 0.45)] + arc_pts(1.675, 0.45, 0.195, 0, 180, 8)[1:-1] +
                                                    [(1.48, 0.45)])], 'grid', layer)
        cv.add([P(f) for f in flame(1.675, 1.0, 0.36, 5, seed)] + [P(p) for p in wok(1.675, 1.08, 0.9)], 'solid', layer)
        for i in range(2):
            steam(cv, x + (1.5 + 0.35 * i) * s, y + 1.55 * s, 1.5 * s, cw=i == 0, seed=seed + i, w=0.06 * s)

def stool(cv, x, y, s=1.0, layer='mid'):
    """Round kopitiam stool, four splayed legs."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P(rect(-0.3, 0.72, 0.3, 0.82)), P(ribbon([(-0.2, 0.74), (-0.3, 0.0)], 0.03)), P(ribbon([(0.2, 0.74), (0.3, 0.0)], 0.03)),
            P(ribbon([(-0.07, 0.74), (-0.1, 0.0)], 0.025)), P(ribbon([(0.07, 0.74), (0.1, 0.0)], 0.025)),
            P(rect(-0.26, 0.3, 0.26, 0.34))], 'solid', layer)

def kopi_table(cv, x, y, s=1.0, layer='mid'):
    """Marble-topped kopitiam table on a cast-iron pedestal with scroll feet."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P(_open([(-1.35, 1.42), (-1.38, 1.5), (-1.3, 1.6)], 3) + [(1.3, 1.6)] + _open([(1.3, 1.6), (1.38, 1.5), (1.35, 1.42)], 3)[1:])],
           'grid', layer)
    legs = [P(ribbon([(0.0, 1.42), (0.0, 0.25)], 0.07, 0.06)), P(ellipse(0.0, 0.85, 0.12, 0.08)), P(rect(-0.45, 1.3, 0.45, 1.42))]
    for sd in (-1, 1):
        legs.append(P(ribbon(_open([(0.0, 0.3), (sd * 0.35, 0.12), (sd * 0.62, 0.05)]), 0.05, 0.03)))
        legs.append(P(scroll(sd * 0.65, 0.15, 0.1, 0.035, 1.1, a0=180 if sd > 0 else 0, cw=sd > 0)))
        legs.append(P(scroll(sd * 0.25, 1.15, 0.12, 0.035, 1.2, a0=270, cw=sd < 0, tail=[(0.0, 1.32), (sd * 0.12, 1.3)])))
    cv.add(legs, 'solid', layer)

def pineapple(cv, x, y, s=1.0, layer='mid'):
    """Nanas: a scaled fruit and a spiky crown."""
    P = lambda pts: xf(pts, x, y, s=s)
    pid = cv.add([P(ellipse(0.0, 0.42, 0.3, 0.42, n=32))] + [P(leaf(0.0, 0.8, 90 + a, 0.42 - abs(a) * 0.004, 0.05, bend=a * 0.002))
                                                            for a in (-50, -30, -14, 0, 14, 30, 50)], 'scales', layer)
    return pid

def tamarind(cv, x, y, s=1.0, layer='mid'):
    """Asam jawa pods: three knobbly curved pods."""
    polys = []
    for k in range(3):
        path = _open([(x + (-0.3 + 0.06 * k) * s, y + 0.05 * s + 0.07 * k * s), (x + 0.0, y + (0.16 + 0.06 * k) * s),
                      (x + (0.35 - 0.05 * k) * s, y + (0.08 + 0.06 * k) * s)], 6)
        polys.append(ribbon(path, 0.0, wf=lambda t: s * (0.045 + 0.012 * math.sin(t * 5 * math.pi) ** 2)))
    return cv.add(polys, 'solid', layer)

def satay_grill(cv, x, y, s=1.0, layer='mid', seed=1):
    """Long charcoal trough on legs, skewers laid across, smoke rising."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P(ribbon([(-0.85, 0.0), (-0.7, 0.85)], 0.04)), P(ribbon([(0.85, 0.0), (0.7, 0.85)], 0.04)),
            P(ribbon([(-0.78, 0.4), (0.78, 0.4)], 0.025))], 'solid', layer)
    cv.add([P([(-1.0, 0.85), (1.0, 0.85), (0.9, 1.15), (-0.9, 1.15)])], 'grid', layer)
    sticks = []
    for k in range(9):
        sx = -0.8 + 0.2 * k
        sticks.append(P(ribbon([(sx - 0.25, 1.18), (sx + 0.15, 1.3)], 0.008)))
        sticks += [P(ellipse(sx - 0.08 + 0.07 * j, 1.22 + 0.02 * j, 0.035, 0.028, n=10)) for j in range(3)]
    cv.add(sticks + [P(f) for f in flame(0.0, 1.12, 0.22, 7, seed)], 'solid', layer)
    for i in range(3):
        steam(cv, x + (-0.6 + 0.6 * i) * s, y + 1.45 * s, 1.6 * s, cw=i % 2 == 0, seed=seed + 3 + i, w=0.07 * s)

def night_street(cv, seed=1):
    """Blurred backdrop: a moon, Kek Lok Si on its hill, a far shophouse row."""
    moon(cv, 2.2, 7.0, 0.42)
    hills(cv, -0.5, 9.0, G + 2.2, 1.1, seed=seed, n=2)
    pagoda(cv, 4.2, G + 3.1, 0.95)
    for i, (x0, b, st) in enumerate(((7.0, 2, 3), (12.8, 2, 2), (17.2, 2, 3))):
        shophouse(cv, x0, G + 0.2, 0.75, b, 'back', seed + i, st)

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def penang_land(cv):
    """A busy night-market street: lit shophouses, lantern strings, three
    hawker carts with steam rising from their woks, the crowd moving through."""
    moon(cv, 2.0, 7.1, 0.4)
    hills(cv, -0.5, 9.5, G + 1.9, 1.0, seed=3, n=2)
    pagoda(cv, 4.6, G + 2.6, 0.92)
    cloud(cv, 15.8, 7.0, 0.6, 'back', flip=True, seed=4)
    shophouse(cv, 15.0, G + 0.2, 0.8, 3, 'back', 9, 2)
    for i, (x0, sx) in enumerate(((5.6, 1.0), (8.0, 1.0), (11.6, 1.0))):
        W.place_figure(cv, dict(head='young' if i % 2 else 'refined', hat=('songkok', None, 'tudung')[i],
                                body='female' if i == 2 else 'male', costume='kurung' if i == 2 else 'baju',
                                pose='stand' if i != 1 else 'gesture', rods=False), x0, G + 0.15, 1.9, flip=i == 1, layer='back')
    shophouse(cv, -0.3, G, 1.0, 2, 'mid', 1, 3)
    shophouse(cv, 3.1, G, 0.95, 2, 'mid', 2, 2)
    lantern_string(cv, 0.2, 6.6, 5.6, 0.7, 6, 0.15, seed=3)
    lantern_string(cv, 13.4, 19.6, 5.2, 0.6, 5, 0.15, seed=4)
    stall(cv, 8.0, G + 0.02, 1.05, seed=11)
    stall(cv, 12.6, G + 0.02, 1.0, seed=12)
    stall(cv, 17.1, G + 0.02, 0.9, seed=13, lamp=False)
    for i, sx in enumerate((6.5, 11.1, 15.6, 19.7)):
        stool(cv, sx, G, 0.8)
    ground(cv, 'road', seed=7)

def penang_people(cv):
    """Malay, Chinese and Indian vendors cook side by side: satay fanned over
    coals, kuey teow tossed in a flaming wok, teh tarik pulled high."""
    night_street(cv, seed=20)
    cv.add([rect(-0.3, 4.95, 20.8, 5.08)], 'solid', 'mid')          # the shared canopy beam
    val = [arc_pts(-0.2 + 0.42 * k + 0.21, 4.97, 0.21, 180, 360, 8) for k in range(50)]
    cv.add([[(-0.3, 4.95), (20.8, 4.95), (20.8, 5.35), (-0.3, 5.35)]] + val, 'slits', 'mid')
    for px in (0.4, 6.7, 13.6, 20.1):
        cv.add([rect(px - 0.06, G, px + 0.06, 4.96)], 'solid', 'mid')
    for i, lx in enumerate((3.4, 10.2, 16.9)):
        p, c = lantern(lx, 4.25, 0.2)
        cv.add(p + [ribbon([(lx, 4.95), (lx, 4.6)], 0.012)], 'edge', 'mid')
        cv.carve(c, 'mid')
    # Malay: satay over the coals, fanned
    satay_grill(cv, 4.4, G + 0.02, 1.1, seed=4)
    W.place_figure(cv, dict(head='refined', hat='songkok', costume='baju', pose='penang_fan', item_f='penang_kipas',
                            rod_to=-0.25), 2.25, G, 3.2)
    # Chinese: kuey teow tossed over a roaring flame
    cv.add_eo([rect(9.2, G, 10.9, G + 1.1), [(9.75, G), (10.35, G), (10.35, G + 0.45)] + arc_pts(10.05, G + 0.45, 0.3, 0, 180, 8)[1:-1] +
               [(9.75, G + 0.45)]], 'grid', 'mid')
    cv.add(flame(10.05, G + 1.05, 0.75, 7, seed=5), 'solid', 'mid')
    noodles = [ribbon(_open([(9.55 + 0.1 * k, G + 1.95), (9.85 + 0.12 * k, G + 2.55 + 0.1 * k), (10.3 + 0.1 * k, G + 2.25)]), 0.022, 0.012)
               for k in range(4)]
    cv.add(noodles + [ellipse(9.7 + 0.25 * k, G + 2.6 + 0.12 * (k % 2), 0.04, 0.025, n=10) for k in range(4)], 'solid', 'mid')
    W.place_figure(cv, dict(head='refined', hat='penang_band', costume='penang_hawker', pose='penang_toss', item_f='penang_wok',
                            item_b='penang_chan', rod_to=-0.25), 8.0, G, 3.2)
    for i in range(2):
        steam(cv, 9.9 + 0.5 * i, G + 2.9, 1.3, cw=i == 0, seed=30 + i)
    # Indian: teh tarik pulled in a long arc above a tin tray of glasses
    cv.add([rect(15.3, G, 15.4, G + 1.0), rect(17.6, G, 17.7, G + 1.0), rect(15.1, G + 0.95, 17.9, G + 1.1)], 'solid', 'mid')
    cv.add([[(15.25, G + 1.1), (17.75, G + 1.1), (17.6, G + 1.5), (15.4, G + 1.5)]], 'grid', 'mid')
    cups = []
    for k in range(5):
        cx = 15.65 + 0.35 * k
        cups += [[(cx - 0.11, G + 1.5), (cx + 0.11, G + 1.5), (cx + 0.14, G + 1.86), (cx - 0.14, G + 1.86)]]
    cv.add(cups, 'solid', 'mid')
    cv.carve([rect(15.65 + 0.35 * k - 0.07, G + 1.62, 15.65 + 0.35 * k + 0.07, G + 1.78) for k in range(5)], 'mid')
    W.place_figure(cv, dict(head='old', beard='penang_misai', hat=None, costume='penang_mamak', pose='penang_tarik',
                            item_f='penang_pour', item_b='penang_mug', pour=0.4, rod_to=-0.25), 18.5, G, 3.2, flip=True)
    ground(cv, 'road', seed=17)
    stool(cv, 6.6, G, 0.85, layer='front')
    stool(cv, 13.2, G, 0.85, layer='front')

def penang_food(cv):
    """A bowl of asam laksa served at the hawker cart: the cook reaches across
    her counter and hands the steaming bowl to a customer, her stockpot
    simmering behind her, the toppings laid out either side."""
    night_street(cv, seed=40)
    for lx, ly in ((6.2, 6.4), (14.6, 6.5)):
        p, c = lantern(lx, ly, 0.24)
        cv.add(p + [ribbon([(lx, 8.3), (lx, ly + 0.4)], 0.012)], 'edge', 'mid')
        cv.carve(c, 'mid')
    # stockpot on a charcoal stove behind the cook
    cv.add_eo([[(2.1, G), (3.5, G), (3.35, G + 0.95), (2.25, G + 0.95)],
               [(2.5, G), (3.1, G), (3.1, G + 0.4)] + arc_pts(2.8, G + 0.4, 0.3, 0, 180, 8)[1:-1] + [(2.5, G + 0.4)]], 'grid', 'mid')
    cv.add(flame(2.8, G + 0.9, 0.35, 5, seed=3), 'solid', 'mid')
    pot = _open([(1.95, G + 2.15), (1.98, G + 1.4), (2.05, G + 1.12), (2.25, G + 1.02), (2.8, G + 1.0)], 4)
    cv.add([mirror_pts(pot, 2.8)], 'scales', 'mid')
    cv.add([_open([(1.9, G + 2.12), (2.3, G + 2.32), (2.8, G + 2.38), (3.3, G + 2.32), (3.7, G + 2.12)], 4),
            ellipse(2.8, G + 2.44, 0.12, 0.08)] +
           [ribbon(arc_pts(sx, G + 1.9, 0.13, 0, 360, 12), 0.03) for sx in (1.84, 3.76)], 'solid', 'mid')
    cv.carve([ribbon(_open([(2.0, G + 1.55), (2.8, G + 1.5), (3.6, G + 1.55)]), 0.02)], 'mid')
    for i in range(2):
        steam(cv, 2.5 + 0.55 * i, G + 2.5, 1.6, cw=i == 0, seed=50 + i)
    # the hawker reaches across her cart's counter and hands a bowl to a customer
    W.place_figure(cv, dict(body='female', hat='penang_bun', costume='penang_samfu', pose='penang_give',
                            rod_to=-0.25), 9.55, G, 3.55)
    stall(cv, 8.9, G, 1.2, cook=None, seed=6)
    W.place_figure(cv, dict(head='young', hat='songkok', costume='baju', pose='penang_take', rod_to=-0.25),
                   13.0, G, 3.4, flip=True)
    rim = bowl(cv, 11.35, G + 2.12, 0.78, cls='flower', seed=3)
    for i, (dx, hh, cw) in enumerate(((-0.12, 1.1, False), (0.16, 1.35, True))):
        steam(cv, 11.35 + dx, rim + 0.2, hh, cw=cw, seed=60 + i, w=0.06)
    stool(cv, 14.6, G, 0.85)
    kopi_table(cv, 16.0, G, 0.72)
    pineapple(cv, 4.6, G, 1.3)
    jar(cv, 17.7, G, 0.75, cls='edge')
    for k, lean in enumerate((-0.12, 0.0, 0.14)):
        kantan(cv, 17.62 + 0.08 * k, G + 0.55, 1.8 + 0.25 * (k == 1), lean=lean)
    fish(cv, 19.0, G + 0.35, 1.2, flip=True, ang=8)
    plate(cv, 18.9, G, 1.4)
    tamarind(cv, 15.4, G + 0.02, 0.9)
    chillies(cv, 6.0, G + 0.05, 0.9)
    ground(cv, 'road', seed=27)

# =====================================================================
# rig parts (registered once, prefixed penang_)
# =====================================================================

def _hat_band():
    """Short-cropped hair under a towel tied round the head, knot and tails behind."""
    hair = _open([(-0.04, 0.89), (-0.042, 0.925), (-0.02, 0.952), (0.012, 0.958), (0.04, 0.948), (0.056, 0.925)], 4) + \
        [(0.05, 0.915), (0.0, 0.93), (-0.03, 0.9)]
    band = ribbon(_open([(-0.044, 0.902), (0.0, 0.914), (0.058, 0.922)]), 0.011)
    knot = ellipse(-0.048, 0.903, 0.014, 0.012)
    tails = [ribbon(_open([(-0.05, 0.905), (-0.085, 0.89), (-0.11, 0.862), (-0.13, 0.85)]), 0.009, 0.004),
             ribbon(_open([(-0.05, 0.9), (-0.075, 0.872), (-0.09, 0.842)]), 0.008, 0.004)]
    return [hair, band, knot] + tails, 'edge', [ribbon([(-0.03, 0.903), (0.04, 0.917)], 0.0016)]

def _hat_bun():
    """Hair drawn back into a bun, a pin through it."""
    hair = _open([(0.05, 0.915), (0.03, 0.948), (-0.005, 0.958), (-0.035, 0.945), (-0.05, 0.915), (-0.052, 0.87),
                  (-0.04, 0.83)], 4) + [(-0.025, 0.85), (-0.01, 0.9), (0.02, 0.92)]
    bun = ellipse(-0.064, 0.93, 0.026, 0.024)
    pin = ribbon([(-0.1, 0.955), (-0.03, 0.905)], 0.0028)
    return [hair, bun, pin], 'edge', [ribbon(arc_pts(-0.064, 0.93, 0.013, 0, 300, 10), 0.0018)]

def _apron(spec):
    """Hawker's apron hung from the neck, tied at the waist."""
    bib = [(0.02, 0.75), (0.08, 0.745), (0.072, 0.62), (0.078, 0.54), (0.1, 0.42), (0.11, 0.33), (-0.01, 0.33), (-0.03, 0.54)]
    tie = [ribbon([(-0.075, 0.55), (0.06, 0.555)], 0.008), ribbon(_open([(-0.07, 0.55), (-0.1, 0.5), (-0.105, 0.44)]), 0.007, 0.004)]
    strap = ribbon([(0.03, 0.75), (-0.01, 0.8)], 0.006)
    return [([bib], 'grid', [ribbon([(0.0, 0.45), (0.09, 0.45)], 0.003)]), (tie + [strap], 'solid', [])]

def _it_bell(g, ang, spec):
    """The market vendor's hand bell, rung high: handle up, bell swinging,
    sound curls round it."""
    x, y = g
    polys = [ribbon([(x, y - 0.035), (x + 0.004, y + 0.05)], 0.009, 0.007), ellipse(x + 0.004, y + 0.055, 0.012, n=12)]
    bell = _open([(x - 0.018, y - 0.035), (x - 0.03, y - 0.07), (x - 0.055, y - 0.11)], 4) + \
        [(x + 0.055, y - 0.11)] + _open([(x + 0.055, y - 0.11), (x + 0.03, y - 0.07), (x + 0.018, y - 0.035)], 4)[1:]
    polys.append(xf(bell, rot=18, ox=x, oy=y - 0.035, s=1.3))
    polys.append(ellipse(*xf([(x + 0.0, y - 0.135)], rot=18, ox=x, oy=y - 0.035, s=1.3)[0], 0.014, n=10))
    for k, r in enumerate((0.1, 0.135)):
        polys.append(ribbon(arc_pts(x + 0.01, y - 0.07, r, 10, 70, 10), 0.005, 0.002))
        polys.append(ribbon(arc_pts(x + 0.01, y - 0.07, r, 120, 170, 10), 0.002, 0.005))
    return polys, 'solid', [ribbon(xf([(x - 0.035, y - 0.088), (x + 0.035, y - 0.088)], rot=18, ox=x, oy=y), 0.003)]

def _it_chan(g, ang, spec):
    """Wok spatula: a long handle and a flat, slightly cupped blade."""
    a = math.radians(ang - 8)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.19 * d[0], g[1] + 0.19 * d[1])
    blade = xf([(0.0, 0.01), (0.03, 0.035), (0.075, 0.034), (0.085, 0.0), (0.075, -0.034), (0.03, -0.035), (0.0, -0.01)],
               end[0], end[1], rot=math.degrees(a) - 35)
    return [ribbon([(g[0] - 0.05 * d[0], g[1] - 0.05 * d[1]), end], 0.0065), blade], 'solid', []

def _it_wok(g, ang, spec):
    """A wok tossed by its handle, tipped up toward the flying noodles."""
    a = math.radians(ang + 10)
    d = (math.cos(a), math.sin(a))
    c = (g[0] + 0.17 * d[0], g[1] + 0.17 * d[1])
    polys = [ribbon([(g[0] - 0.03 * d[0], g[1] - 0.03 * d[1]), (g[0] + 0.07 * d[0], g[1] + 0.07 * d[1])], 0.009)]
    polys += [xf(p, c[0], c[1] - 0.05, rot=14, ox=0, oy=0) for p in wok(0.0, 0.0, 0.2)[:1]]
    return polys, 'solid', []

def _it_kipas(g, ang, spec):
    """Woven satay fan flapped over the coals."""
    a = math.radians(ang - 20)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.05 * d[0], g[1] + 0.05 * d[1])
    fan = xf([(0, 0), (0.05, 0.05), (0.13, 0.065), (0.16, 0.0), (0.13, -0.065), (0.05, -0.05)], end[0], end[1],
             rot=math.degrees(a))
    cuts = [xf(ribbon([(0.04 + 0.025 * k, -0.045 + 0.005 * k), (0.04 + 0.025 * k, 0.045 - 0.005 * k)], 0.003), end[0], end[1],
               rot=math.degrees(a)) for k in range(4)]
    puffs = [ribbon(arc_pts(end[0] + 0.1 * d[0], end[1] + 0.1 * d[1] - 0.05, r, 210, 330, 8), 0.004, 0.002) for r in (0.1, 0.14)]
    return [ribbon([(g[0] - 0.03 * d[0], g[1] - 0.03 * d[1]), end], 0.006), fan] + puffs, 'solid', cuts

def _mug(x, y):
    return [rect(x - 0.022, y - 0.02, x + 0.022, y + 0.045), ribbon(arc_pts(x - 0.028, y + 0.012, 0.016, 90, 270, 8), 0.004)]

def _it_mug(g, ang, spec):
    return _mug(g[0] + 0.01, g[1] - 0.005), 'solid', []

def _it_pour(g, ang, spec):
    """The upper mug, tipped, pouring a long ribbon of tea that bellies out and
    lands in the lower mug (length spec['pour'])."""
    x, y = g[0] + 0.01, g[1]
    L = spec.get('pour', 0.6)
    mug = [xf(p, rot=-55, ox=x, oy=y) for p in _mug(x, y)]
    lip = xf([(x + 0.022, y + 0.045)], rot=-55, ox=x, oy=y)[0]
    stream = ribbon(_open([lip, (lip[0] + 0.03, lip[1] - 0.05), (lip[0] + 0.04, lip[1] - L * 0.5), (lip[0] + 0.02, lip[1] - L)], 6),
                    0.0065, 0.004)
    foam = [ellipse(lip[0] + 0.02 + 0.012 * math.sin(k), lip[1] - L * (0.3 + 0.1 * k), 0.006, n=8) for k in range(4)]
    return mug + [stream] + foam, 'solid', []

W.register(W.HATS, 'penang_band', _hat_band)
W.register(W.HATS, 'penang_bun', _hat_bun)
W.register(W.BEARDS, 'penang_misai', [(0.072, 0.846), (0.082, 0.84), (0.09, 0.826), (0.078, 0.83), (0.062, 0.834),
                                      (0.048, 0.83), (0.04, 0.836), (0.055, 0.845)])
W.register(W.COSTUMES, 'penang_hawker', dict(W.COSTUMES['farmer'], lower=None, legs='rolled', hem=0.46, extra=_apron,
                                             cls={'top': 'dots', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.COSTUMES, 'penang_samfu', dict(W.COSTUMES['kurung'], lower=None, legs='trousers', hem=0.44, flare=0.02,
                                            extra=_apron, cls={'top': 'flower', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.COSTUMES, 'penang_mamak', dict(W.COSTUMES['sarong'], hem=0.47,
                                            cls={'top': 'dots', 'lower': 'slits', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.ITEMS2, 'penang_bell', _it_bell)
W.register(W.ITEMS2, 'penang_chan', _it_chan)
W.register(W.ITEMS2, 'penang_wok', _it_wok)
W.register(W.ITEMS2, 'penang_kipas', _it_kipas)
W.register(W.ITEMS2, 'penang_mug', _it_mug)
W.register(W.ITEMS2, 'penang_pour', _it_pour)
W.register(W.POSES, 'penang_ring', {'f': (118, 20), 'b': (38, 52), 'lean': -5, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'penang_toss', {'f': (58, 52), 'b': (40, 70), 'lean': 4, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'penang_give', {'f': (88, 8), 'b': (78, 22), 'lean': 8, 'legs': 'stand', 'hf': 'open', 'hb': 'open'})
W.register(W.POSES, 'penang_take', {'f': (82, 14), 'b': (70, 34), 'lean': 4, 'legs': 'walk', 'hf': 'open', 'hb': 'open'})
W.register(W.POSES, 'penang_fan', {'f': (52, 64), 'b': (-14, -14), 'lean': 8, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'penang_tarik', {'f': (140, 15), 'b': (55, 25), 'lean': -3, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def icon_food_asam_laksa(seed=3):
    """Penang asam laksa: thick round rice noodles in a red-brown tamarind and
    mackerel broth, flaked fish, pineapple, cucumber, red onion, mint and torch
    ginger, a spoon of black prawn paste on the rim."""
    rnd = random.Random(seed)
    w, h = 2.0, 2.0 * BOWL_DEPTH
    outer = [(-x * w, y * h) for x, y in reversed(BOWL_PROFILE)]
    rim = outer[-1]
    inner = [(r - 0.05, z) for r, z in reversed(outer) if z > 0.2 * h]
    prof = [(0.0, 0.0)] + outer + [(rim[0] - 0.025, rim[1] + 0.02)] + inner + [(0.0, inner[-1][1])]
    porcelain = _mat('Porcelain', (0.94, 0.92, 0.87), 0.32)
    red = _mat('Red', (0.62, 0.06, 0.05), 0.4)
    _lathe('Bowl', prof, porcelain, 72)
    _torus('RimLine', (0, 0, rim[1] - 0.06), rim[0] - 0.012, 0.018, red)
    _torus('Band', (0, 0, 0.55 * h), 0.86, 0.016, red)
    soup_z = 0.84 * h
    _lathe('Soup', [(0.0, soup_z), (0.9, soup_z)], _mat('Kuah', (0.42, 0.12, 0.04), 0.3), 64, sharp=0)
    noodle = _mat('Noodle', (0.94, 0.9, 0.78), 0.5)
    for i in range(12):
        a0 = rnd.uniform(0, TAU)
        pts = []
        for k in range(28):
            t = k / 27
            a = a0 + t * rnd.uniform(1.0, 2.0)
            r = 0.15 + 0.62 * abs(math.sin(t * math.pi + i))
            pts.append((r * math.cos(a), r * math.sin(a), soup_z + 0.025 + 0.05 * math.sin(t * 5 + i)))
        _tube('Noodle%d' % i, pts, 0.05, noodle)
    pine = _mat('Pineapple', (0.98, 0.78, 0.18), 0.4)
    for i in range(8):
        _box('Pine%d' % i, (0.3 + 0.1 * (i % 3), -0.4 + 0.11 * (i // 3) + 0.03 * i, soup_z + 0.13 + 0.02 * (i % 2)),
             (0.11, 0.11, 0.08), (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), rnd.uniform(0, 1.5)), pine)
    cuc = _mat('Cucumber', (0.62, 0.82, 0.38), 0.45)
    cucs = _mat('CucSkin', (0.12, 0.38, 0.1), 0.45)
    for i in range(9):
        _box('Cuc%d' % i, (-0.45 + 0.04 * i, 0.12 + 0.05 * (i % 3), soup_z + 0.14 + 0.02 * (i % 3)), (0.5, 0.05, 0.05),
             (0.12 * (i % 2), 0.1, rnd.uniform(-0.5, 0.5)), cuc if i % 3 else cucs)
    fishm = _mat('Fish', (0.72, 0.58, 0.42), 0.6)
    for i in range(7):
        _blob('Flake%d' % i, (-0.3 + 0.09 * i, -0.38 + 0.04 * (i % 2), soup_z + 0.1), (0.08, 0.05, 0.035),
              (0, 0, rnd.uniform(0, 3)), fishm, 10)
    onion = _mat('Onion', (0.62, 0.22, 0.45), 0.35)
    for i in range(4):
        _torus('Onion%d' % i, (0.0 + 0.12 * (i % 2), 0.45 - 0.08 * i, soup_z + 0.13 + 0.02 * i), 0.1, 0.018, onion,
               rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0))
    mint = _mat('Mint', (0.12, 0.45, 0.12), 0.5)
    for i in range(7):
        a = TAU * i / 7
        _blob('Mint%d' % i, (-0.05 + 0.14 * math.cos(a), 0.0 + 0.11 * math.sin(a), soup_z + 0.22 + 0.03 * (i % 2)),
              (0.13, 0.065, 0.015), (0.4 * math.cos(a), 0.4 * math.sin(a), a), mint)
    kant = _mat('Kantan', (0.95, 0.38, 0.55), 0.45)
    for i in range(6):
        _box('Kantan%d' % i, (-0.45 + 0.05 * i, -0.15 - 0.03 * i, soup_z + 0.16), (0.3, 0.03, 0.02), (0.1, 0, 0.6 + 0.3 * i), kant)
    chili = _mat('Chilli', (0.85, 0.07, 0.04), 0.35)
    for i in range(5):
        _torus('Chilli%d' % i, (0.45 + 0.08 * (i % 2), 0.25 - 0.1 * i, soup_z + 0.14), 0.04, 0.018, chili,
               rot=(rnd.uniform(-0.3, 0.3), 0.2, 0))
    steel = _mat('Spoon', (0.75, 0.75, 0.76), 0.3, metal=1.0)
    _blob('SpoonBowl', (0.98, -0.35, h + 0.06), (0.17, 0.11, 0.035), (0.0, 0.25, -0.5), steel, 16)
    _box('SpoonHandle', (1.25, -0.6, h + 0.1), (0.5, 0.05, 0.02), (0, 0.15, -0.8), steel)
    _blob('HehKo', (0.98, -0.35, h + 0.085), (0.13, 0.08, 0.03), (0.0, 0.25, -0.5), _mat('HehKo', (0.08, 0.04, 0.03), 0.25), 16)
    return (0, -4.7, 4.1), (0, 0, 0.55)

def icon_item_vendor_bell():
    """The market vendor's bell: a cast brass hand bell with a turned wooden
    handle, its clapper showing under the lip."""
    from mathutils import Euler
    brass = _mat('Brass', (0.78, 0.55, 0.2), 0.42, metal=1.0)
    dark = _mat('Inside', (0.22, 0.14, 0.06), 0.55, metal=1.0)
    wood = _mat('Handle', (0.32, 0.13, 0.05), 0.6, grain=(0.16, 0.06, 0.02))
    prof = [(0.62, 0.0), (0.66, 0.03), (0.6, 0.1), (0.5, 0.2), (0.43, 0.38), (0.4, 0.6), (0.38, 0.78), (0.3, 0.9),
            (0.18, 0.96), (0.0, 0.98)]
    inner = [(r - 0.04, z) for r, z in prof[::-1][:-1]] + [(0.58, 0.01)]
    parts = [_lathe('Bell', prof + inner[1:], brass, 64)]
    parts.append(_lathe('Inner', [(0.0, 0.9), (0.3, 0.86), (0.4, 0.6), (0.5, 0.2), (0.57, 0.04)], dark, 48))
    for z in (0.25, 0.7):
        parts.append(_torus('Ring%.2f' % z, (0, 0, z), _interp_r(prof, z) + 0.005, 0.012, brass, seg=64))
    parts.append(_lathe('Collar', [(0.0, 0.96), (0.14, 0.96), (0.16, 1.02), (0.1, 1.08), (0.0, 1.08)], brass, 32))
    parts.append(_lathe('Handle', [(0.0, 1.06), (0.09, 1.06), (0.11, 1.15), (0.08, 1.3), (0.1, 1.5), (0.13, 1.62),
                                   (0.12, 1.72), (0.07, 1.78), (0.0, 1.8)], wood, 32))
    parts.append(_tube('Rod', [(0, 0, 0.9), (0.05, 0, 0.25)], 0.018, dark))
    parts.append(_blob('Clapper', (0.06, 0, 0.12), (0.075, 0.075, 0.075), (0, 0, 0), brass, 16))
    pivot = bpy.data.objects.new('Pivot', None)
    bpy.context.scene.collection.objects.link(pivot)
    for ob in parts:
        ob.parent = pivot
    pivot.rotation_euler = Euler((math.radians(-28), math.radians(16), 0.2))
    pivot.location = (0.0, 0.0, 0.25)
    pivot.scale = (1.35, 1.35, 1.35)
    return (0.3, -6.3, 3.2), (0.0, 0, 1.0)

def _interp_r(prof, z):
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / ((z1 - z0) or 1)
    return prof[-1][0]

# =====================================================================
# registry: what the CLI renders for this state
# =====================================================================

PUPPET = dict(head='refined', hat='penang_band', costume='penang_hawker', pose='penang_ring', item_f='penang_bell',
              item_b='penang_chan', scarf=True)                               # Ah Kow
BEATS = {'land': penang_land, 'people': penang_people, 'food': penang_food}
ICONS = {'food': icon_food_asam_laksa, 'item': icon_item_vendor_bell}
