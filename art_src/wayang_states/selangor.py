"""Selangor: city towers rising beside an old kampung house, Danial training
alone, his grandmother's nasi lemak, and Danial himself with his batik wrap."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box, _obj   # private kit helpers

# =====================================================================
# props
# =====================================================================

def tower(cv, x, y, w, h, kind=0, layer='mid', seed=1):
    """A modern high-rise, base centred at x: stepped setbacks, banded windows
    cut in rows, a crown (spire, pinnacle or plant room)."""
    rnd = random.Random(seed)
    if kind == 0:                                           # stepped tower with a spire
        tiers = [(w, 0.0, 0.62), (w * 0.78, 0.62, 0.84), (w * 0.55, 0.84, 0.95)]
        crown = [ribbon([(x, y + h * 0.95), (x, y + h * 1.12)], w * 0.035, w * 0.008)]
    elif kind == 1:                                         # slab with a sloped top
        tiers = [(w, 0.0, 0.9)]
        crown = [[(x - w / 2, y + h * 0.9), (x + w / 2, y + h * 0.9), (x + w / 2, y + h)]]
    else:                                                   # round-shouldered tower, a pinnacle
        tiers = [(w, 0.0, 0.8), (w * 0.82, 0.8, 0.9)]
        crown = [arc_pts(x, y + h * 0.9, w * 0.41, 0, 180, 16, ry=h * 0.06) + [(x - w * 0.41, y + h * 0.9)],
                 ribbon([(x, y + h * 0.95), (x, y + h * 1.06)], w * 0.03, w * 0.006)]
    polys = [rect(x - tw / 2, y + h * a, x + tw / 2, y + h * b + 0.01) for tw, a, b in tiers] + crown
    pid = cv.add(polys, 'edge', layer)
    if layer == 'back':
        return pid
    cuts = []
    for tw, a, b in tiers:                                  # window bands, a vertical fin every few bays
        y0, y1 = y + h * a + 0.18, y + h * b - 0.12
        n = int((y1 - y0) / 0.2)
        for k in range(n):
            yy = y0 + k * 0.2
            cuts.append(rect(x - tw / 2 + 0.09, yy, x + tw / 2 - 0.09, yy + 0.07))
        cuts.append(rect(x - 0.012, y0, x + 0.012, y1))
    cv.carve(cuts, layer)
    return pid

def crane(cv, x, y, h, jib=2.4, layer='mid', flip=False):
    """Tower crane: a lattice mast, the jib and counter-jib, hook on its line."""
    P = lambda pts: xf(pts, x, y, flip=flip)
    w = 0.22
    polys = [rect(-w / 2, 0.0, w / 2, h), rect(-0.6, h, jib, h + 0.12), rect(-0.6, h - 0.3, -0.2, h),
             [(-0.05, h + 0.12), (0.05, h + 0.12), (0.0, h + 0.55)], ribbon([(0.0, h + 0.55), (jib * 0.8, h + 0.12)], 0.012),
             ribbon([(0.0, h + 0.55), (-0.55, h + 0.12)], 0.012), ribbon([(jib * 0.7, h), (jib * 0.7, h - 1.1)], 0.008),
             [(jib * 0.7 - 0.06, h - 1.1), (jib * 0.7 + 0.06, h - 1.1), (jib * 0.7, h - 1.2)]]
    cv.add([P(p) for p in polys], 'solid', layer)
    cuts = []
    for k in range(int(h / 0.25)):
        y0 = 0.12 + k * 0.25
        cuts.append([(-w / 2 + 0.04, y0), (w / 2 - 0.04, y0), (0.0, y0 + 0.1)])
        cuts.append([(-w / 2 + 0.04, y0 + 0.21), (w / 2 - 0.04, y0 + 0.21), (0.0, y0 + 0.11)])
    for k in range(int(jib / 0.3)):
        cuts.append([(0.15 + k * 0.3, h + 0.03), (0.4 + k * 0.3, h + 0.03), (0.275 + k * 0.3, h + 0.095)])
    cv.carve([P(c) for c in cuts], layer)

def flyover(cv, x0, x1, y, layer='mid', seed=1):
    """An elevated highway on round piers, cars streaming along it."""
    rnd = random.Random(seed)
    cv.add([rect(x0, y, x1, y + 0.26), rect(x0, y + 0.26, x1, y + 0.34)] +
           [rect(px - 0.12, G - 0.1, px + 0.12, y) for px in [x0 + 0.8 + 2.4 * k for k in range(int((x1 - x0 - 0.8) / 2.4) + 1)]] +
           [[(px - 0.3, y), (px + 0.3, y), (px + 0.12, y - 0.2), (px - 0.12, y - 0.2)] for px in
            [x0 + 0.8 + 2.4 * k for k in range(int((x1 - x0 - 0.8) / 2.4) + 1)]], 'edge', layer)
    cars = []
    cx = x0 + 0.3
    while cx < x1 - 0.8:
        L = rnd.uniform(0.45, 0.75)
        tall = rnd.random() < 0.3
        hh = 0.32 if tall else 0.2
        cars.append([(cx, y + 0.36), (cx + L, y + 0.36), (cx + L, y + 0.36 + hh * 0.6), (cx + L * 0.8, y + 0.36 + hh),
                     (cx + L * 0.25, y + 0.36 + hh), (cx + L * 0.1, y + 0.36 + hh * 0.6)])
        cars += [ellipse(cx + L * 0.22, y + 0.37, 0.055, n=10), ellipse(cx + L * 0.78, y + 0.37, 0.055, n=10)]
        cx += L + rnd.uniform(0.25, 0.9)
    cv.add(cars, 'solid', layer)
    cv.carve([rect(x0 + 0.1, y + 0.12, x1 - 0.1, y + 0.15)], layer)

def gasing_shape(cx, cy, s=1.0, rot=0.0):
    """Pangkah top in profile: a broad shoulder, a knob, and the iron spike (polys)."""
    body = _open([(-0.5, 0.05), (-0.42, 0.22), (-0.2, 0.32), (-0.12, 0.42), (0.12, 0.42), (0.2, 0.32), (0.42, 0.22),
                  (0.5, 0.05)], 4) + [(0.3, -0.12), (0.05, -0.28), (0.0, -0.42), (-0.05, -0.28), (-0.3, -0.12)]
    knob = rect(-0.07, 0.4, 0.07, 0.55)
    return [xf(p, cx, cy, s=s, rot=rot, ox=0, oy=0) for p in (body, knob)]

def burst(cx, cy, r, n=10, seed=1):
    """Impact star: alternating long and short spikes (polys)."""
    rnd = random.Random(seed)
    out = []
    for k in range(n):
        a = 360 * k / n + rnd.uniform(-8, 8)
        L = r * (1.0 if k % 2 == 0 else 0.55) * rnd.uniform(0.8, 1.1)
        out.append(leaf(cx + 0.15 * r * math.cos(math.radians(a)), cy + 0.15 * r * math.sin(math.radians(a)), a, L, r * 0.09))
    return out

def coconut_half(cv, x, y, s=1.0, layer='mid'):
    """A split coconut, the white flesh cut out of the shell."""
    shell = [(x - 0.32 * s, y + 0.3 * s)] + arc_pts(x, y + 0.3 * s, 0.32 * s, 180, 360, 16)[1:-1] + [(x + 0.32 * s, y + 0.3 * s)]
    cv.add([shell], 'edge', layer)
    cv.carve([ribbon(arc_pts(x, y + 0.3 * s, 0.25 * s, 195, 345, 12), 0.03 * s)], layer)

def city_back(cv, seed=1, x0=0.0, x1=12.0):
    """Blurred skyline: a run of towers of mixed heights and a hill line."""
    rnd = random.Random(seed)
    x = x0 + 0.4
    i = 0
    while x < x1:
        w = rnd.uniform(0.7, 1.3)
        h = rnd.uniform(2.4, 5.6) * (1.0 if x < 6.8 else 0.75)
        tower(cv, x, G + 0.6, w, h, kind=i % 3, layer='back', seed=seed + i)
        x += w + rnd.uniform(0.15, 0.5)
        i += 1

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def selangor_land(cv):
    """New towers crowd right up to an old kampung house: the city on the
    left with a crane and a highway, the stilt house, palms and rain tree on
    the right."""
    city_back(cv, seed=5, x0=-0.4, x1=12.5)
    hills(cv, 11.0, 21.0, G + 0.6, 0.9, seed=6)
    cloud(cv, 15.8, 7.0, 0.65, 'back', flip=True, seed=4)
    birds(cv, 14.2, 6.2, 3, 0.5, seed=7, layer='back', flip=True)
    for x, w, h, k in ((0.9, 1.5, 6.1, 0), (2.7, 1.25, 4.9, 1), (4.4, 1.6, 6.5, 2), (6.15, 1.2, 4.6, 0), (7.7, 1.3, 3.9, 1),
                       (9.3, 1.1, 3.1, 2)):
        tower(cv, x, G, w, h, kind=k, seed=int(x * 10))
    crane(cv, 10.6, G, 3.9, jib=1.9, flip=True)
    flyover(cv, -0.3, 11.6, G + 1.15, seed=3)
    raintree(cv, 12.6, G, 3.3, seed=8)
    rumah(cv, 15.4, G + 0.02, 0.9)
    palm(cv, 18.6, G, 4.4, lean=0.06, seed=31, fronds=8)
    palm(cv, 19.7, G, 3.6, lean=-0.1, seed=32, fronds=7)
    fence(cv, 12.0, 20.6, G, 0.5)
    ground(cv, 'earth', seed=9)
    frame_edges(cv, seed=10, left='none', right='banana')

def selangor_people(cv):
    """Danial trains alone in the kampung yard: his top flies off the cord and
    smashes into the target top spinning in the ring, the city behind him."""
    city_back(cv, seed=21, x0=0.5, x1=11.0)
    rumah(cv, 15.6, G + 0.6, 0.75, layer='back')
    raintree(cv, 2.2, G, 4.4, seed=22)
    cv.add([ribbon([(1.8, G + 3.0), (1.8, G + 1.0)], 0.012)], 'solid')          # tyre swing
    cv.add_eo([ellipse(1.8, G + 0.8, 0.34, 0.38, n=32), ellipse(1.8, G + 0.8, 0.18, 0.22, n=24)], 'edge')
    W.place_figure(cv, dict(head='young', hat='selangor_hair', costume='selangor_modern', pose='selangor_throw',
                            legs='selangor_lunge', item_f='selangor_cord', rod_to=-0.25), 6.4, G, 3.6)
    # the throw: speed lines and the flying top, the hit, the target flung up
    fly = (12.2, G + 1.3)
    cv.add(gasing_shape(*fly, s=0.95, rot=-28), 'edge')
    cv.carve([xf(ribbon([(-0.38, 0.15 - 0.1 * k), (0.38, 0.15 - 0.1 * k)], 0.02), fly[0], fly[1], s=0.95, rot=-28, ox=0, oy=0)
              for k in range(2)])
    lines = [ribbon(_open([(8.4, G + 2.35 - 0.25 * k), (10.2, G + 1.9 - 0.2 * k), (fly[0] - 0.45, fly[1] + 0.3 - 0.2 * k)]),
                    0.0, wf=lambda t: 0.035 * t) for k in range(3)]
    cv.add(lines, 'solid')
    cv.add(burst(13.2, G + 0.85, 1.0, 12, seed=3), 'solid')
    cv.add(gasing_shape(14.35, G + 1.55, 0.95, rot=38), 'edge')
    cv.carve([xf(ribbon([(-0.38, 0.15 - 0.1 * k), (0.38, 0.15 - 0.1 * k)], 0.02), 14.35, G + 1.55, s=0.95, rot=38, ox=0, oy=0)
              for k in range(2)])
    cv.add([ribbon(arc_pts(14.35, G + 1.55, 0.75, 140, 230, 10), 0.024, 0.006), ribbon(arc_pts(14.35, G + 1.55, 0.95, 150, 215, 10), 0.018, 0.005)],
           'solid')
    cv.add([ellipse(13.3 + 0.32 * k, G + 1.9 + 0.35 * (k % 2) + 0.12 * k, 0.045 + 0.012 * (k % 2), n=8) for k in range(5)], 'solid')
    cv.add([ribbon(arc_pts(13.4, G + 0.08, 1.9, 172, 188, 6, ry=0.2), 0.025), ribbon(arc_pts(13.4, G + 0.08, 1.9, -8, 8, 6, ry=0.2), 0.025)],
           'solid')
    for gx in (16.4, 17.3):                                 # spare tops waiting by the ring
        cv.add(gasing_shape(gx, G + (0.3 if gx < 17 else 0.42), 0.6, rot=80 if gx < 17 else 0), 'edge')
    fence(cv, 15.5, 20.6, G, 0.55)
    grass(cv, 17.5, 20.6, G, 0.6, seed=4, layer='mid')
    ground(cv, 'earth', seed=19)
    frame_edges(cv, seed=20, left='none', right='banana')

def selangor_food(cv):
    """His grandmother prepares nasi lemak: rice steamed with pandan in the
    periuk, sambal spooned over it on an opened daun pisang bungkus at the low
    table, more bungkus folded and stacked beside it."""
    cv.add_eo([rect(0.8, 2.2, 5.6, 6.6), rect(1.1, 2.5, 5.3, 6.3)], 'edge', 'back')     # window, the city beyond it
    for k, (tx, th) in enumerate(((1.6, 3.4), (2.5, 2.6), (3.4, 3.8), (4.4, 2.9))):
        cv.add([rect(tx - 0.3, 2.5, tx + 0.3, 2.5 + th)], 'solid', 'back')
    cv.add([ribbon([(1.1 + 1.05 * i, 2.5), (1.1 + 1.05 * i, 6.3)], 0.03) for i in range(1, 4)] +
           [ribbon([(1.1, 4.4), (5.3, 4.4)], 0.04)], 'solid', 'back')
    cv.add([rect(14.6, 4.95, 19.6, 5.1)], 'solid', 'back')
    for i, x in enumerate((15.2, 16.4, 17.7, 18.9)):
        periuk(cv, x, 5.1, 0.7 + 0.15 * (i % 2), 'back', lid=i % 2 == 0)
    jar(cv, 17.6, G, 1.6, 'back')
    for x in (7.0, 13.4):
        cv.add([ribbon([(x, 8.3), (x, 7.4)], 0.02)] + [leaf(x, 7.45, -90 + k * 12, 0.7, 0.07) for k in (-1, 0, 1)], 'solid', 'back')
    dapur(cv, 3.2, G + 0.05, 1.2)
    for k in range(4):                                      # pandan knotted in the rice pot
        cv.add([leaf(3.0 + 0.12 * k, G + 2.3, 70 + 14 * k, 0.6, 0.05, bend=0.08)], 'solid')
    steam(cv, 3.0, G + 2.5, 2.0, cw=False, seed=3)
    low_table(cv, 10.8, G + 0.02, 4.4, 0.85)
    top = nasi_lemak(cv, 10.4, G + 0.87, 2.3)
    for k, (bx, bs) in enumerate(((12.35, 0.75), (12.95, 0.68), (12.62, 0.6))):
        bungkus(cv, bx, G + 0.87 + 0.42 * (k == 2), bs)
    for i, (dx, hh, cw) in enumerate(((-0.4, 1.4, False), (0.25, 1.65, True))):
        steam(cv, 10.4 + dx, top + 0.15, hh, cw=cw, seed=10 + i)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kurung', pose='selangor_spoon', item_f='selangor_sambal',
                            lean=8, cls={'lower': 'flower'}, rod_to=-0.25), 8.0, G, 3.6)
    for sx in (-1, 1):                                      # trimmings mirrored about the table
        coconut_half(cv, 10.8 + sx * 3.4, G, 1.1)
    cuc = []
    for k in range(3):
        cuc += [ellipse(4.9 + 0.3 * k, G + 0.13, 0.13, 0.13, n=16)]
    cv.add(cuc, 'edge')
    cv.carve([ellipse(4.9 + 0.3 * k, G + 0.13, 0.07, 0.07, n=12) for k in range(3)])
    chillies(cv, 16.6, G + 0.05, 1.0)
    serai(cv, 18.4, G, 1.8)
    for k in range(5):                                      # a bundle of pandan
        cv.add([leaf(19.6 + 0.04 * k, G, 80 + 6 * k, 1.6 - 0.1 * abs(k - 2), 0.07, bend=0.12)], 'solid')
    ground(cv, 'earth', seed=29)
    frame_edges(cv, seed=30, left='none', right='none')

def low_table(cv, cx, y, w, h, layer='mid'):
    """A low kampung table: a thick plank top, a pierced apron and two turned legs."""
    P = lambda pts: xf(pts, cx, y)
    top = [(-0.5 * w, h - 0.12), (0.5 * w, h - 0.12), (0.52 * w, h - 0.04), (0.5 * w, h), (-0.5 * w, h), (-0.52 * w, h - 0.04)]
    legs = []
    for sx in (-1, 1):
        lx = sx * 0.42 * w
        legs.append(_open([(lx - 0.07, h - 0.12), (lx - 0.05, h * 0.6), (lx - 0.08, h * 0.45), (lx - 0.045, h * 0.2),
                           (lx - 0.06, 0.0)], 3) + _open([(lx + 0.06, 0.0), (lx + 0.045, h * 0.2), (lx + 0.08, h * 0.45),
                                                          (lx + 0.05, h * 0.6), (lx + 0.07, h - 0.12)], 3))
    apron = rect(-0.4 * w, h - 0.34, 0.4 * w, h - 0.1)
    cv.add([P(top), P(apron)] + [P(l) for l in legs], 'edge', layer)
    cv.carve([P(ellipse(x * w, h - 0.22, 0.1, 0.045)) for x in (-0.3, -0.15, 0.0, 0.15, 0.3)], layer)

def bungkus(cv, x, y, s=1.0, layer='mid'):
    """Nasi lemak bungkus: a banana-leaf pyramid packet, the folds creased and
    a rubber band round its waist."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P([(-0.5, 0.0), (0.5, 0.0), (0.42, 0.12), (0.06, 0.66), (-0.02, 0.7), (-0.08, 0.64), (-0.42, 0.12)])], 'edge', layer)
    cv.carve([P(ribbon([(-0.3, 0.27), (0.3, 0.27)], 0.016)), P(ribbon([(-0.02, 0.62), (0.12, 0.08)], 0.008)),
              P(ribbon([(-0.06, 0.6), (-0.3, 0.1)], 0.008))], layer)

def nasi_lemak(cv, cx, y, w, seed=1):
    """Nasi lemak on a banana leaf: the rice moulded into a dome, sambal over
    its crown, half an egg, cucumber slices, ikan bilis and peanuts. Returns
    the heap's top y."""
    rnd = random.Random(seed)
    leafp = [(cx - 0.55 * w, y + 0.05 * w), (cx - 0.48 * w, y), (cx + 0.48 * w, y), (cx + 0.58 * w, y + 0.06 * w),
             (cx + 0.45 * w, y + 0.04 * w), (cx - 0.45 * w, y + 0.035 * w)]
    cv.add([leafp], 'solid')
    cv.carve([ribbon([(cx - 0.45 * w, y + 0.018 * w), (cx + 0.5 * w, y + 0.024 * w)], 0.004 * w)] +
             [ribbon([(cx + t * w, y + 0.02 * w), (cx + (t + 0.04) * w, y + 0.045 * w)], 0.003 * w) for t in (-0.35, -0.2, 0.2, 0.35)])
    hh = 0.3 * w
    dome = [(cx + 0.2 * w * math.cos(math.radians(a)), y + 0.04 * w + hh * math.sin(math.radians(a))) for a in range(0, 181, 10)]
    cv.add([dome], 'dots')
    sambal = _open([(cx - 0.17 * w, y + 0.04 * w + hh * 0.62), (cx - 0.08 * w, y + 0.04 * w + hh * 1.05), (cx + 0.06 * w, y + 0.04 * w + hh * 1.08),
                    (cx + 0.17 * w, y + 0.04 * w + hh * 0.66)], 5) + \
        [(cx + 0.12 * w, y + 0.04 * w + hh * 0.5), (cx + 0.08 * w, y + 0.04 * w + hh * 0.72), (cx - 0.02 * w, y + 0.04 * w + hh * 0.6),
         (cx - 0.1 * w, y + 0.04 * w + hh * 0.75)]
    egg = ellipse(cx + 0.32 * w, y + 0.11 * w, 0.1 * w, 0.075 * w, n=24)
    polys = [sambal, egg]
    for k in range(4):                                      # cucumber slices leaning on the rice
        polys.append(ellipse(cx - 0.3 * w + 0.05 * k * w, y + (0.07 + 0.012 * k) * w, 0.045 * w, 0.06 * w, n=14, rot=-10))
    for k in range(9):                                      # ikan bilis and kacang
        if k % 2:
            polys.append(ellipse(cx + 0.18 * w + 0.03 * k * w, y + 0.02 * w, 0.016 * w, 0.012 * w, n=8))
        else:
            polys.append(leaf(cx - 0.45 * w + 0.025 * k * w, y + 0.03 * w, rnd.uniform(-20, 20), 0.06 * w, 0.008 * w))
    cv.add(polys, 'solid')
    cv.carve([ellipse(cx + 0.32 * w, y + 0.11 * w, 0.045 * w, 0.035 * w, n=16)] +
             [ellipse(cx - 0.3 * w + 0.05 * k * w, y + (0.07 + 0.012 * k) * w, 0.02 * w, 0.03 * w, n=10, rot=-10) for k in range(4)] +
             [ellipse(cx + rnd.uniform(-0.1, 0.1) * w, y + 0.04 * w + hh * rnd.uniform(0.75, 0.95), 0.012 * w, n=8) for _ in range(5)])
    return y + 0.04 * w + hh * 1.08

# =====================================================================
# rig parts (registered once, prefixed selangor_)
# =====================================================================

def _hat_hair():
    """Spiked-up hair and a batik headband whose tails stream behind."""
    hair = [(0.056, 0.905), (0.072, 0.94), (0.08, 0.968), (0.05, 0.972), (0.02, 0.984), (-0.03, 0.984), (-0.112, 0.972),
            (-0.066, 0.955), (-0.118, 0.936), (-0.068, 0.925), (-0.106, 0.9), (-0.058, 0.893), (-0.05, 0.875),
            (-0.035, 0.89), (0.0, 0.915), (0.03, 0.912)]
    band = ribbon(_open([(-0.046, 0.902), (0.0, 0.912), (0.057, 0.918)]), 0.012)
    tails = [ribbon(_open([(-0.05, 0.905), (-0.1, 0.9), (-0.15, 0.91), (-0.19, 0.89)]), 0.012, 0.006),
             ribbon(_open([(-0.05, 0.9), (-0.09, 0.875), (-0.13, 0.87), (-0.16, 0.845)]), 0.011, 0.005)]
    cuts = [ellipse(-0.01 + 0.02 * k, 0.906 + 0.002 * k, 0.003, n=6) for k in range(3)] + \
        [ellipse(-0.1 - 0.035 * k, 0.902 - 0.004 * k, 0.0035, n=6) for k in range(2)]
    return [hair, band] + tails, 'edge', cuts

def _wrap(spec):
    """The batik cloth from his grandmother, wrapped round the hips and knotted,
    its ends flying back."""
    wrap = [(-0.075, 0.585), (0.08, 0.59), (0.095, 0.47), (0.085, 0.42), (-0.06, 0.41), (-0.08, 0.47)]
    knot = ellipse(0.075, 0.5, 0.022, 0.026)
    ends = [ribbon(_open([(0.07, 0.5), (0.02, 0.44), (-0.06, 0.4), (-0.15, 0.38)]), 0.018, 0.01),
            ribbon(_open([(0.07, 0.49), (0.04, 0.4), (-0.02, 0.34), (-0.1, 0.31)]), 0.016, 0.008)]
    return [([wrap], 'flower', []), ([knot] + ends, 'edge', [])]

def _it_top(g, ang, spec):
    """A gasing held up and back, its cord wound tight, the tail hanging."""
    x, y = g
    polys = gasing_shape(x + 0.005, y + 0.035, 0.11, rot=-60)
    tail = ribbon(_open([(x - 0.01, y + 0.02), (x + 0.03, y - 0.08), (x - 0.01, y - 0.18), (x + 0.02, y - 0.26)]), 0.0035, 0.0025)
    cuts = [xf(ribbon([(-0.35, 0.15 - 0.09 * k), (0.35, 0.15 - 0.09 * k)], 0.022), x + 0.005, y + 0.035, s=0.11, rot=-60, ox=0, oy=0)
            for k in range(3)]
    return polys + [tail], 'solid', cuts

def _it_cord(g, ang, spec):
    """The cord just released, whipping out from the hand in loose loops."""
    x, y = g
    path = _open([(x, y), (x + 0.12, y + 0.06), (x + 0.24, y + 0.0), (x + 0.3, y - 0.08), (x + 0.42, y - 0.06),
                  (x + 0.5, y + 0.02)], 6)
    return [ribbon(path, 0.004, 0.0025), ellipse(x + 0.5, y + 0.02, 0.008, n=8)], 'solid', []

def _it_sambal(g, ang, spec):
    """A spoon of sambal tipped over the rice, a dollop falling."""
    a = math.radians(ang - 30)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.17 * d[0], g[1] + 0.17 * d[1])
    return [ribbon([(g[0] - 0.03 * d[0], g[1] - 0.03 * d[1]), end], 0.0055),
            ellipse(end[0] + 0.02 * d[0], end[1] + 0.02 * d[1] - 0.004, 0.026, 0.017, rot=math.degrees(a) - 20),
            ellipse(end[0] + 0.035, end[1] - 0.05, 0.012, 0.015, n=10)], 'solid', []

W.register(W.HATS, 'selangor_hair', _hat_hair)
W.register(W.COSTUMES, 'selangor_modern', dict(W.COSTUMES['baju'], hem=0.5, flare=0.0, lower=None, legs='trousers', sleeve=0.033,
                                               extra=_wrap, cls={'top': 'slits', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.LEGS, 'selangor_lunge', ((0.17, 0.27), (0.25, 0.055), (-0.1, 0.25), (-0.23, 0.06), 0.45))
W.register(W.ITEMS2, 'selangor_top', _it_top)
W.register(W.ITEMS2, 'selangor_cord', _it_cord)
W.register(W.ITEMS2, 'selangor_sambal', _it_sambal)
W.register(W.POSES, 'selangor_aim', {'f': (82, 8), 'b': (-100, -40), 'lean': 10, 'legs': 'selangor_lunge', 'hf': 'open', 'hb': 'grip'})
W.register(W.POSES, 'selangor_throw', {'f': (96, -6), 'b': (-70, -30), 'lean': 22, 'legs': 'selangor_lunge', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'selangor_spoon', {'f': (70, 40), 'b': (36, 60), 'lean': 8, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'})

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def icon_food_nasi_lemak(seed=5):
    """Nasi lemak on a banana leaf: a dome of coconut rice, red sambal, half
    a boiled egg, cucumber, fried ikan bilis and peanuts."""
    rnd = random.Random(seed)
    leafm = _mat('BananaLeaf', (0.12, 0.42, 0.1), 0.38)
    rib = _mat('Midrib', (0.35, 0.55, 0.2), 0.45)
    lf = _blob('Leaf', (0, 0, 0.0), (1.55, 1.1, 0.02), (0, 0, 0.35), leafm, 40)
    _box('Rib', (0, 0, 0.02), (2.9, 0.04, 0.02), (0, 0, 0.35), rib)
    rice = _mat('Rice', (0.97, 0.96, 0.92), 0.6)
    R, H = 0.6, 0.62
    _lathe('Rice', [(R * math.cos(math.radians(a)), 0.02 + H * math.sin(math.radians(a))) for a in range(0, 91, 6)] + [(0.0, 0.02 + H)],
           rice, 48)
    sam = _mat('Sambal', (0.62, 0.08, 0.04), 0.3)
    s = _blob('Sambal', (0.0, -0.02, 0.02 + H * 0.92), (0.4, 0.36, 0.14), (0.15, 0.0, 0.0), sam, 24)
    for v in s.data.vertices:
        x, y, z = v.co
        v.co = (x * (1 + 0.12 * math.sin(4 * math.atan2(y, x))), y, z)
    white = _mat('EggWhite', (0.97, 0.96, 0.92), 0.35)
    yolk = _mat('Yolk', (0.98, 0.62, 0.08), 0.35)
    _blob('Egg', (0.85, -0.25, 0.14), (0.3, 0.22, 0.13), (0, 0, 0.5), white)
    _blob('EggYolk', (0.85, -0.25, 0.25), (0.15, 0.11, 0.03), (0, 0, 0.5), yolk)
    cuc = _mat('Cucumber', (0.7, 0.85, 0.45), 0.45)
    cucs = _mat('CucSkin', (0.12, 0.38, 0.1), 0.45)
    for k in range(4):
        sl = _lathe('Cuc%d' % k, [(0.0, 0.0), (0.16, 0.0), (0.16, 0.035), (0.0, 0.035)], cuc, 24, sharp=30)
        sl.location = (-0.75 + 0.12 * k, -0.55 + 0.06 * k, 0.08 + 0.03 * k)
        sl.rotation_euler = (math.radians(55), 0.0, math.radians(-20))
        _torus('CucRim%d' % k, sl.location, 0.16, 0.012, cucs, rot=sl.rotation_euler, seg=24)
    bilis = _mat('Bilis', (0.62, 0.42, 0.18), 0.5)
    for k in range(18):
        a = rnd.uniform(-0.9, 0.9) + math.pi * 0.62
        r = rnd.uniform(0.7, 1.05)
        _box('Bilis%d' % k, (r * math.cos(a), r * math.sin(a), 0.06), (0.16, 0.03, 0.025), (0, 0, rnd.uniform(0, 3)), bilis)
    nut = _mat('Peanut', (0.72, 0.42, 0.22), 0.45)
    for k in range(16):
        a = rnd.uniform(-0.6, 0.6) + math.pi * 0.25
        r = rnd.uniform(0.65, 0.95)
        _blob('Nut%d' % k, (r * math.cos(a), r * math.sin(a), 0.07), (0.05, 0.035, 0.03), (0, 0, rnd.uniform(0, 3)), nut, 10)
    return (0, -5.3, 4.0), (0.0, 0, 0.25)

def icon_item_batik_wrap():
    """The batik cloth wrap from Danial's grandmother: a length of soga-brown and
    indigo batik hung loose over a wooden rail, folds rippling down to a banded
    hem and a knotted fringe."""
    import bmesh
    cloth = _mat('Batik', (0.42, 0.22, 0.08), 0.8)
    nt = cloth.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vo = nt.nodes.new('ShaderNodeTexVoronoi')
    vo.feature = 'DISTANCE_TO_EDGE'
    vo.inputs['Scale'].default_value = 3.2
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.inputs['Scale'].default_value = 1.8
    wv.inputs['Distortion'].default_value = 4.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    els[0].color = (0.9, 0.8, 0.58, 1)                      # cream canting lines
    els[1].position = 0.1
    els[1].color = (0.45, 0.24, 0.08, 1)                    # soga brown
    els.new(0.48).color = (0.08, 0.1, 0.3, 1)               # indigo
    els.new(0.72).color = (0.22, 0.11, 0.05, 1)             # dark brown
    mx = nt.nodes.new('ShaderNodeMath')
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = 0.6
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    nt.links.new(vo.outputs['Distance'], mx.inputs[0])
    nt.links.new(wv.outputs['Fac'], mul.inputs[0])
    nt.links.new(mul.outputs[0], mx.inputs[1])
    nt.links.new(mx.outputs[0], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    hem = _mat('Hem', (0.07, 0.08, 0.26), 0.8)
    cream = _mat('Fringe', (0.86, 0.76, 0.55), 0.8)
    wood = _mat('Rail', (0.46, 0.28, 0.13), 0.55, grain=(0.28, 0.16, 0.07))
    RZ, R, nu, nv = 1.15, 0.075, 40, 48
    La, Lb = math.pi * R, 0.75
    def drape(x, s):
        """Point on the hanging cloth: s 0 = front hem, 1 = back hem."""
        Lf = 1.05 + 0.22 * (x + 1) / 2                      # hung a little askew: longer on the right
        d = s * (Lf + La + Lb)
        if d < Lf:
            far = Lf - d
            y, z = -R - 0.06 * far, RZ - far
        elif d < Lf + La:
            th = math.pi - (d - Lf) / R
            y, z, far = R * math.cos(th), RZ + R * math.sin(th), 0.0
        else:
            far = d - Lf - La
            y, z = R + 0.05 * far, RZ - far
        y += (0.03 + 0.09 * far) * math.sin(x * 6.5 + 0.8 + 0.6 * far)  # folds deepen toward the hem
        return (x * (1 - 0.04 * far), y, z), far, d < Lf
    me = bpy.data.meshes.new('Cloth')
    bm = bmesh.new()
    grid = [[None] * (nv + 1) for _ in range(nu + 1)]
    hem_band = {}
    for i in range(nu + 1):
        for j in range(nv + 1):
            co, far, front = drape(-1.0 + 2.0 * i / nu, j / nv)
            grid[i][j] = bm.verts.new(co)
            hem_band[i, j] = far > (1.05 + 0.22 * i / nu) - 0.16 if front else far > Lb - 0.12
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
            f.material_index = 1 if hem_band[i, j] and hem_band[i, j + 1] else 0
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    ob = _obj('Cloth', me, cloth)
    me.materials.append(hem)
    ob.modifiers.new('Thick', 'SOLIDIFY').thickness = 0.03
    for i in range(0, nu + 1, 2):                           # knotted fringe off the front hem
        (x, y, z), _, _ = drape(-1.0 + 2.0 * i / nu, 0.0)
        _tube('Fringe%d' % i, [(x, y, z), (x + 0.01, y - 0.01, z - 0.14)], 0.011, cream)
        _blob('Knot%d' % i, (x, y, z - 0.03), (0.018, 0.018, 0.02), (0, 0, 0), cream, 8)
    _tube('Rail', [(-1.28, 0.0, RZ), (1.28, 0.0, RZ)], 0.055, wood)
    for sx in (-1, 1):
        _blob('Knob%d' % sx, (sx * 1.3, 0.0, RZ), (0.08, 0.08, 0.08), (0, 0, 0), wood, 12)
        _tube('Post%d' % sx, [(sx * 1.18, 0.0, RZ - 0.05), (sx * 1.18, 0.0, -0.4)], 0.045, wood)
        _tube('Foot%d' % sx, [(sx * 1.18, -0.32, -0.4), (sx * 1.18, 0.32, -0.4)], 0.045, wood)
    return (1.3, -6.0, 1.9), (0.0, 0.0, 0.42)

# =====================================================================
# registry: what the CLI renders for this state
# =====================================================================

PUPPET = dict(head='young', hat='selangor_hair', costume='selangor_modern', pose='selangor_aim', item_b='selangor_top')   # Danial
BEATS = {'land': selangor_land, 'people': selangor_people, 'food': selangor_food}
ICONS = {'food': icon_food_nasi_lemak, 'item': icon_item_batik_wrap}
