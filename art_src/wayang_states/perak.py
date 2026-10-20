"""Perak: an old Kinta tin-mining town with its dredge, miners digging and
panning, a bowl of Ipoh hor fun, and Uncle Chandran with his carbide lamp."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers
from wayang_states.penang import shophouse, kopi_table, stool, lantern     # same author (wayang-W1)

# =====================================================================
# props
# =====================================================================

def dredge(cv, x, y, s=1.0, layer='mid'):
    """Kapal korek: pontoon hull, a two-storey corrugated house with gable
    roofs and a stack, the gantry and its bucket ladder dipping into the pool
    at the bow, the tailings stacker reaching out astern."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P([(-2.5, 0.42), (-2.3, -0.12), (2.3, -0.12), (2.5, 0.42)])], 'edge', layer)
    cv.add_eo([P(rect(-2.0, 0.42, 1.45, 1.42))] + [P(rect(-1.75 + 0.55 * k, 0.72, -1.45 + 0.55 * k, 1.15)) for k in range(6)],
              'slits', layer)
    cv.add_eo([P(rect(-1.6, 1.42, 0.95, 2.28))] + [P(rect(-1.35 + 0.6 * k, 1.66, -1.05 + 0.6 * k, 2.02)) for k in range(4)],
              'slits', layer)
    roofs = [P([(-2.2, 1.38), (1.65, 1.38), (1.35, 1.6), (-1.9, 1.6)]), P([(-1.8, 2.24), (1.15, 2.24), (0.7, 2.7), (-1.35, 2.7)]),
             P(rect(0.0, 2.6, 0.2, 3.35)), P(rect(-0.05, 3.3, 0.25, 3.42))]
    cv.add(roofs, 'scales', layer)
    frame = [P(ribbon([(1.25, 0.42), (2.05, 3.3)], 0.06)), P(ribbon([(2.75, 0.3), (2.05, 3.3)], 0.06)),
             P(ribbon([(1.55, 1.5), (2.5, 1.4)], 0.04)), P(ribbon([(1.8, 2.4), (2.3, 2.35)], 0.035)),
             P(ribbon([(1.45, 1.2), (2.6, 2.1)], 0.025)), P(ribbon([(2.6, 1.2), (1.6, 2.1)], 0.025))]
    cv.add(frame, 'solid', layer)
    wheel(cv, *P([(2.05, 3.3)])[0], 0.22 * s, 6, layer, knobs=False)
    # bucket ladder: the long beam from the gantry top down into the water
    a, b = (2.05, 3.2), (4.6, -0.35)
    L = math.dist(a, b)
    d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (-d[1], d[0])
    beam = [P(ribbon([a, b], 0.09))]
    buckets = []
    for k in range(11):
        t = 0.06 + k * 0.085
        c = (a[0] + d[0] * L * t, a[1] + d[1] * L * t)
        q = [(c[0] + n[0] * 0.09, c[1] + n[1] * 0.09), (c[0] + n[0] * 0.26 + d[0] * 0.05, c[1] + n[1] * 0.26 + d[1] * 0.05),
             (c[0] + n[0] * 0.28 + d[0] * 0.22, c[1] + n[1] * 0.28 + d[1] * 0.22), (c[0] + n[0] * 0.09 + d[0] * 0.2, c[1] + n[1] * 0.09 + d[1] * 0.2)]
        buckets.append(P(q))
    cv.add(beam + buckets, 'solid', layer)
    cv.carve([P(ribbon([(a[0] + d[0] * L * (0.04 + 0.085 * k), a[1] + d[1] * L * (0.04 + 0.085 * k)),
                        (a[0] + d[0] * L * (0.08 + 0.085 * k), a[1] + d[1] * L * (0.08 + 0.085 * k))], 0.022)) for k in range(11)],
             layer)
    # stacker astern
    st = [P(ribbon([(-1.9, 1.7), (-4.1, 2.85)], 0.07)), P(ribbon([(-2.4, 0.42), (-3.2, 2.42)], 0.04)),
          P(ribbon([(-2.0, 0.42), (-3.2, 2.42)], 0.04)), P(ribbon([(-1.9, 2.05), (-3.25, 2.5)], 0.02))]
    st += [P(ribbon([(-2.1 - 0.4 * k, 1.8 + 0.21 * k), (-2.1 - 0.4 * k, 1.66 + 0.21 * k)], 0.035)) for k in range(5)]
    cv.add(st, 'solid', layer)
    cv.add([P(ellipse(-4.15 - 0.15 * k, 2.6 - 0.35 * k, 0.05 + 0.02 * k, n=10)) for k in range(4)], 'solid', layer)

def pool(cv, x0, x1, y, h=0.35, seed=1, layer='mid'):
    """A still mining pool: a scaled band with a few lazy curls and reeds."""
    rnd = random.Random(seed)
    pid = cv.add([[(x0, y - 0.15), (x1, y - 0.15), (x1 - 0.2, y + h), (x0 + 0.2, y + h)]], 'scales', layer)
    curls = []
    for i in range(int((x1 - x0) / 1.1)):
        cx = x0 + 0.6 + i * 1.1 + rnd.uniform(-0.2, 0.2)
        curls.append(scroll(cx, y + h + 0.1, 0.1, 0.035, 1.1, a0=180, cw=True, tail=[(cx - 0.35, y + h), (cx - 0.15, y + h + 0.06)]))
    cv.add(curls, 'solid', layer, pid=pid)
    return pid

def mound(cv, x, y, w, h, seed=1, layer='mid', cls='dots'):
    """A heap of tailings sand, lumpy along its crest."""
    f = noise1(seed, 6)
    pts = [(x - w / 2 + w * t, y + h * math.sin(math.pi * t) ** 0.8 * (1 + 0.12 * f(t))) for t in (k / 20 for k in range(21))]
    return cv.add([[(x - w / 2, y - 0.1)] + pts + [(x + w / 2, y - 0.1)]], cls, layer)

def palong(cv, x0, y0, x1, y1, layer='mid', seed=1, water=True):
    """Wooden sluice chute on X-trestles, high end left; water runs down it."""
    rnd = random.Random(seed)
    L = math.dist((x0, y0), (x1, y1))
    d = ((x1 - x0) / L, (y1 - y0) / L)
    trough = [(x0, y0), (x1, y1), (x1 - 0.02, y1 - 0.2), (x0 - 0.02, y0 - 0.2)]
    cv.add([trough], 'edge', layer)
    legs = []
    n = max(2, int(L / 1.2))
    for k in range(n + 1):
        t = k / n
        px, py = x0 + d[0] * L * t, y0 + d[1] * L * t - 0.2
        if py - G < 0.15:
            continue
        legs += [ribbon([(px - 0.25, G), (px + 0.03, py)], 0.03), ribbon([(px + 0.25, G), (px - 0.03, py)], 0.03),
                 ribbon([(px - 0.17, G + (py - G) * 0.35), (px + 0.17, G + (py - G) * 0.35)], 0.02)]
    cv.add(legs, 'solid', layer)
    cv.carve([ribbon([(x0 + d[0] * L * t, y0 + d[1] * L * t - 0.1), (x0 + d[0] * L * (t + 0.02), y0 + d[1] * L * (t + 0.02) - 0.1)], 0.02)
              for t in (k / 14 for k in range(1, 14))], layer)
    if water:
        curls = []
        for k in range(int(L / 0.8)):
            t = (k + 0.5) / int(L / 0.8)
            px, py = x0 + d[0] * L * t, y0 + d[1] * L * t
            curls.append(xf(scroll(0.1, 0.12, 0.08, 0.028, 1.1, a0=180, cw=True, tail=[(-0.18, 0.0), (-0.05, 0.08)]),
                            px, py, rot=math.degrees(math.atan2(d[1], d[0]))))
        curls.append(ribbon(_open([(x1, y1 - 0.05), (x1 + 0.18, y1 - 0.15), (x1 + 0.26, y1 - 0.5), (x1 + 0.28, G + 0.05)]), 0.05, 0.035))
        cv.add(curls, 'solid', layer)

def pickaxe(x, y, s=1.0, rot=0.0):
    """Beliung leaning on its head (polys)."""
    out = [ribbon([(0.0, 0.0), (0.0, 0.9)], 0.03, 0.025),
           ribbon(_open([(-0.36, 0.86), (-0.15, 0.94), (0.0, 0.95), (0.15, 0.94), (0.36, 0.86)]), 0.035, 0.012)]
    return [xf(p, x, y, s=s, rot=rot, ox=0, oy=0) for p in out]

def shovel(x, y, s=1.0, rot=0.0):
    out = [ribbon([(0.0, 0.25), (0.0, 1.05)], 0.025), ribbon([(-0.08, 1.05), (0.08, 1.05)], 0.02),
           [(-0.12, 0.27), (0.12, 0.27), (0.1, 0.05), (0.0, -0.02), (-0.1, 0.05)]]
    return [xf(p, x, y, s=s, rot=rot, ox=0, oy=0) for p in out]

def barrow(cv, x, y, s=1.0, layer='mid'):
    """Kereta sorong: a deep tray on one wheel, handles and a leg."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P([(-0.55, 0.62), (0.6, 0.62), (0.4, 0.28), (-0.3, 0.28)]), P(ribbon([(0.3, 0.32), (-1.05, 0.5)], 0.03)),
            P(ribbon([(-0.4, 0.3), (-0.45, 0.0)], 0.03))], 'edge', layer)
    wheel(cv, x + 0.45 * s, y + 0.2 * s, 0.2 * s, 6, layer, knobs=False)

def tin_can(cv, x, y, s=1.0, layer='mid'):
    cv.add([xf(rect(-0.18, 0.0, 0.18, 0.5), x, y, s=s), xf(ribbon(arc_pts(0.0, 0.5, 0.14, 0, 180, 10), 0.015), x, y, s=s)], 'edge', layer)

def dulang_flat(cv, x, y, s=1.0, layer='mid', rot=0.0):
    """A wooden dulang lying tilted: a shallow cone in profile."""
    p = _open([(-0.5, 0.12), (-0.25, 0.04), (0.0, 0.0), (0.25, 0.04), (0.5, 0.12)], 4) + [(0.0, 0.16)]
    cv.add([xf(p, x, y, s=s, rot=rot, ox=0, oy=0)], 'edge', layer)

def kinta_back(cv, seed=1, n=6):
    """Blurred Kinta valley: a run of karst towers and a far dredge."""
    rnd = random.Random(seed)
    for i in range(n):
        x = 1.0 + i * 20.0 / n + rnd.uniform(-0.6, 0.6)
        karst(cv, x, G + 0.8, rnd.uniform(1.6, 2.6), rnd.uniform(2.0, 3.6), seed=seed + i, layer='back', moss=False)

def chicken_board(cv, x, y, s=1.0, layer='mid'):
    """A whole poached chicken on a log-slice chopping board, the cleaver
    standing in the board beside it."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P(rect(-1.0, 0.0, 1.0, 0.32))], 'grid', layer)
    body = _open([(-0.62, 0.42), (-0.7, 0.6), (-0.58, 0.82), (-0.3, 0.98), (0.05, 1.02), (0.36, 0.94), (0.55, 0.78),
                  (0.6, 0.55), (0.5, 0.38), (0.0, 0.32), (-0.45, 0.33)], 5)
    leg = _open([(0.2, 0.62), (0.42, 0.78), (0.62, 0.98), (0.72, 1.08)], 4)
    parts = [P(body), P(ribbon(leg, 0.16, 0.05)), P(ellipse(0.75, 1.1, 0.06, n=12)), P(ellipse(0.82, 1.08, 0.05, n=12)),
             P([(-0.62, 0.62), (-0.86, 0.72), (-0.8, 0.56)])]
    cv.add(parts, 'dots', layer)
    cv.carve([P(ribbon(_open([(-0.35, 0.78), (-0.1, 0.84), (0.12, 0.72), (0.08, 0.55)]), 0.022)),
              P(ribbon(_open([(-0.25, 0.68), (-0.05, 0.7)]), 0.015))], layer)
    cv.add([P([(1.15, 0.3), (1.6, 0.3), (1.62, 0.92), (1.2, 0.95)]), P(ribbon([(1.4, 0.95), (1.42, 1.45)], 0.05, 0.045))], 'solid', layer)
    cv.carve([P(ellipse(1.47, 0.78, 0.04, n=10))], layer)

def prawn(x, y, s=1.0, flip=False):
    """Udang: a curled segmented body and fanned tail (polys)."""
    body = ribbon(arc_pts(0.0, 0.0, 0.18, 200, 20, 12), 0.0, wf=lambda t: 0.09 * (1 - 0.6 * t) + 0.015)
    tail = [(0.17, 0.06), (0.32, 0.16), (0.3, 0.02)]
    head = [leaf(-0.17, -0.06, 220, 0.25, 0.012), leaf(-0.17, -0.06, 200, 0.3, 0.01)]
    return [xf(p, x, y, s=s, flip=flip, ox=0, oy=0) for p in [body, tail] + head]

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def perak_land(cv):
    """An old mining town on uneven ground: the dredge in its pool under the
    karsts, a palong on trestles, tailings heaps, tools left lying about and
    the shophouse row of the town."""
    kinta_back(cv, seed=3)
    cloud(cv, 3.0, 7.2, 0.75, 'back', seed=2)
    cloud(cv, 15.8, 6.9, 0.6, 'back', flip=True, seed=6)
    birds(cv, 13.6, 6.0, 3, 0.5, seed=4, layer='back', flip=True)
    karst(cv, 1.1, G + 0.5, 2.4, 4.6, seed=21, cave=True)
    pool(cv, 1.6, 9.6, G + 0.05, 0.4, seed=5)
    dredge(cv, 5.4, G + 0.4, 0.95)
    shophouse(cv, 14.3, G, 0.72, 3, 'mid', 4, 2)
    mound(cv, 11.2, G, 3.0, 1.2, seed=7)
    mound(cv, 13.4, G, 1.8, 0.65, seed=8)
    palong(cv, 9.4, G + 2.3, 13.1, G + 1.15, seed=2)
    mound(cv, 18.9, G, 3.4, 0.55, seed=9)
    tools = pickaxe(9.6, G + 0.02, 1.5, rot=24) + shovel(16.3, G + 0.3, 1.4, rot=-30) + shovel(12.4, G + 0.6, 1.1, rot=32)
    cv.add(tools, 'solid')
    barrow(cv, 17.6, G + 0.02, 0.95)
    tin_can(cv, 8.7, G, 1.1)
    dulang_flat(cv, 15.4, G + 0.06, 1.1, rot=-6)
    dulang_flat(cv, 19.6, G + 0.5, 0.9, rot=12)
    ground(cv, 'earth', seed=17)
    frame_edges(cv, seed=18, left='none', right='none')

def perak_people(cv):
    """Workers dig the earth and sift it for tin: a miner hoeing the face, a
    carrier with baskets on his pole, the slurry down the palong, and a woman
    panning the tail-water with her dulang."""
    kinta_back(cv, seed=31, n=5)
    dredge(cv, 16.6, G + 0.9, 0.5, layer='back')
    cloud(cv, 5.6, 7.1, 0.6, 'back', seed=4)
    mound(cv, 2.3, G, 4.4, 2.0, seed=11, cls='dots')
    W.place_figure(cv, dict(head='young', hat='caping', costume='farmer', pose='hoe', item_f='hoe', rod_to=-0.25), 5.4, G, 3.2,
                   flip=True)
    palong(cv, 6.6, G + 2.4, 14.4, G + 0.75, seed=3)
    W.place_figure(cv, dict(head='refined', hat='perak_turban', costume='farmer', pose='perak_carry', item_f='perak_kandar',
                            rod_to=-0.25), 9.2, G, 3.2)
    pool(cv, 14.2, 20.6, G + 0.03, 0.3, seed=12)
    W.place_figure(cv, dict(body='female', hat='perak_terendak', costume='penang_samfu', pose='plant', item_f='perak_pan',
                            rod_to=-0.25), 17.0, G + 0.05, 3.3, flip=True)
    tools = pickaxe(1.0, G + 0.1, 1.0, rot=-20) + shovel(12.6, G + 0.02, 0.9, rot=8)
    cv.add(tools, 'solid')
    tin_can(cv, 13.4, G, 0.8)
    ground(cv, 'earth', seed=27)
    frame_edges(cv, seed=28, left='none', right='none')

def perak_food(cv):
    """A bowl of Ipoh hor fun at an old kopitiam: poached chickens hang in the
    window, the hawker blanches noodles in his strainer, prawns and bean
    sprouts laid out, the karsts beyond."""
    kinta_back(cv, seed=41, n=5)
    cv.add_eo([rect(0.6, 2.2, 6.2, 6.8), rect(0.85, 2.45, 5.95, 6.55)], 'edge', 'back')
    cv.add([ribbon([(0.85 + 1.02 * i, 2.45), (0.85 + 1.02 * i, 6.55)], 0.03) for i in range(1, 5)], 'solid', 'back')
    cv.add([rect(14.6, 5.0, 19.8, 5.12)], 'solid', 'back')
    for x in (15.2, 16.4, 17.6, 18.8):
        jar(cv, x, 5.12, 0.6, 'back')
    # the noodle pot on its stove, the hawker dipping the strainer
    cv.add_eo([[(1.9, G), (3.7, G), (3.55, G + 1.0), (2.05, G + 1.0)],
               [(2.5, G), (3.1, G), (3.1, G + 0.4)] + arc_pts(2.8, G + 0.4, 0.3, 0, 180, 8)[1:-1] + [(2.5, G + 0.4)]], 'grid', 'mid')
    cv.add(flame(2.8, G + 0.95, 0.35, 5, seed=3), 'solid', 'mid')
    pot = _open([(1.95, G + 2.0), (1.97, G + 1.35), (2.05, G + 1.12), (2.25, G + 1.02), (2.8, G + 1.0)], 4)
    cv.add([mirror_pts(pot, 2.8)] + [ribbon(arc_pts(sx, G + 1.8, 0.12, 0, 360, 12), 0.03) for sx in (1.84, 3.76)], 'scales', 'mid')
    for i in range(3):
        steam(cv, 2.2 + 0.55 * i, G + 2.15, 1.5, cw=i % 2 == 0, seed=50 + i)
    W.place_figure(cv, dict(head='old', hat=None, costume='penang_hawker', pose='perak_dip', item_f='perak_strainer',
                            scarf=True, rod_to=-0.25), 5.5, G, 3.5, flip=True)
    # chickens hung on a rail
    for lx, ly in ((13.4, 6.3), (17.4, 6.1)):
        p, c = lantern(lx, ly, 0.22)
        cv.add(p + [ribbon([(lx, 8.3), (lx, ly + 0.38)], 0.012)], 'edge', 'mid')
        cv.carve(c, 'mid')
    kopi_table(cv, 10.4, G, 0.85)
    rim = soup_bowl(cv, 10.4, G + 1.36, 1.7)
    hor_fun_heap(cv, 10.4, G + 1.36, 1.7)
    for i, (dx, hh, cw) in enumerate(((-0.4, 1.4, False), (0.1, 1.7, True), (0.5, 1.3, True))):
        steam(cv, 10.4 + dx, rim + 0.4, hh, cw=cw, seed=60 + i)
    stool(cv, 7.6, G, 0.85)
    stool(cv, 13.2, G, 0.85)
    cv.add([rect(14.3, G + 1.25, 19.3, G + 1.38), rect(14.5, G, 14.62, G + 1.25), rect(19.0, G, 19.12, G + 1.25)], 'solid', 'mid')
    chicken_board(cv, 16.2, G + 1.38, 1.1)
    plate(cv, 18.5, G + 1.38, 1.2)
    cv.add(sum((prawn(18.15 + 0.32 * k, G + 1.6 + 0.06 * (k % 2), 0.9, flip=k % 2 == 1) for k in range(3)), []), 'solid', 'mid')
    plate(cv, 15.5, G, 1.5)
    sprouts = [leaf(14.85 + 0.05 * k, G + 0.1 + 0.03 * (k % 3), 20 + (k * 37) % 140, 0.32, 0.018, bend=0.05) for k in range(22)]
    cv.add(sprouts, 'solid', 'mid')
    serai(cv, 19.8, G, 1.4, n=6)
    ground(cv, 'earth', seed=47)

def soup_bowl(cv, cx, y, w, layer='mid'):
    """A round kopitiam soup bowl sitting flat on the table (no foot ring), a
    carved band under the rim. Returns the rim's y."""
    h = w * BOWL_DEPTH
    left = _open([(-0.51 * w, 1.02 * h), (-0.49 * w, 0.88 * h), (-0.45 * w, 0.6 * h), (-0.38 * w, 0.3 * h), (-0.28 * w, 0.08 * h),
                  (-0.2 * w, 0.0)], 5)
    cv.add([xf(mirror_pts(left), cx, y)], 'flower', layer)
    cv.carve([W.diamond(cx + x * w, y + h * 0.86, 0.045 * w, 0.06 * h)[0] for x in (-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4)] +
             [ribbon(_open([(cx - 0.47 * w, y + h * 0.75), (cx, y + h * 0.73), (cx + 0.47 * w, y + h * 0.75)]), 0.006 * w)], layer)
    return y + h

def hor_fun_heap(cv, cx, y, w, seed=1):
    """Flat rice noodles in clear soup: ribbons draped over the rim, shredded
    chicken, prawns and a scatter of spring onion on top."""
    rnd = random.Random(seed)
    h = w * BOWL_DEPTH
    mound = _open([(-0.46 * w, h * 0.86), (-0.36 * w, h * 1.04), (-0.18 * w, h * 1.14), (0.0, h * 1.18),
                   (0.2 * w, h * 1.12), (0.36 * w, h * 1.02), (0.46 * w, h * 0.86)], 5)
    polys = [xf(mound, cx, y)]
    for k in range(9):                                      # shredded chicken
        bx = (-0.3 + 0.075 * k) * w
        polys.append(xf(ribbon([(0, 0), (0.12 * w, 0.03 * w)], 0.012 * w, 0.006 * w), cx + bx, y + h * (1.12 + 0.05 * math.sin(k)),
                        rot=rnd.uniform(-30, 40)))
    for k, sx in enumerate((-0.22, 0.2)):
        polys += prawn(cx + sx * w, y + h * 1.2, 0.55 * w / 2.5, flip=sx > 0)
    for k in range(7):                                      # spring onion
        polys.append(ellipse(cx + (-0.3 + 0.1 * k) * w, y + h * (1.18 + 0.04 * (k % 2)), 0.02 * w, 0.014 * w, n=10))
    cv.add(polys, 'edge')
    cv.carve([ellipse(cx + (-0.3 + 0.1 * k) * w, y + h * (1.18 + 0.04 * (k % 2)), 0.009 * w, 0.006 * w, n=8) for k in range(7)])
    nd = []
    for sx in (-1, 1):                                      # wide flat noodles over the rim
        for k in range(3):
            x0 = sx * (0.3 + 0.06 * k) * w
            nd.append(ribbon(_open([(cx + x0, y + h * 1.0), (cx + sx * (0.47 + 0.02 * k) * w, y + h * 1.03),
                                    (cx + sx * (0.5 + 0.015 * k) * w, y + h * (0.8 - 0.1 * k))]), 0.022 * w, 0.018 * w))
    cv.add(nd, 'solid')
    cv.carve([ribbon(_open([(cx + sx * 0.44 * w, y + h * 1.02), (cx + sx * 0.49 * w, y + h * 0.9)]), 0.004 * w) for sx in (-1, 1)])

# =====================================================================
# rig parts (registered once, prefixed perak_)
# =====================================================================

def _hat_turban():
    """A head cloth wound round the head, its folds carved, a short tail."""
    p = _open([(0.058, 0.9), (0.05, 0.93), (0.025, 0.962), (-0.01, 0.97), (-0.045, 0.955), (-0.062, 0.92),
               (-0.06, 0.888)], 4) + [(0.0, 0.894)]
    tail = ribbon(_open([(-0.055, 0.905), (-0.08, 0.88), (-0.088, 0.85)]), 0.01, 0.005)
    folds = [ribbon(_open([(-0.05, 0.9), (0.0, 0.93), (0.05, 0.94)]), 0.0022),
             ribbon(_open([(-0.04, 0.93), (0.0, 0.952), (0.035, 0.955)]), 0.0022),
             ribbon(_open([(-0.03, 0.905), (0.005, 0.92), (0.045, 0.912)]), 0.0018)]
    return [p, tail], 'dots', folds

def _hat_terendak():
    """Wide shallow terendak with a cloth hanging behind (dulang washer's hat)."""
    A, F, B = (0.0, 1.0), (0.2, 0.9), (-0.2, 0.9)
    top = _open([B, (-0.1, 0.95), A, (0.1, 0.95), F], 6) + [(F[0], F[1] - 0.012), (0.0, 0.89), (B[0], B[1] - 0.012)]
    cloth = [(-0.06, 0.9), (-0.11, 0.9), (-0.12, 0.8), (-0.075, 0.79)]
    carves = [ribbon([(A[0] + (px - A[0]) * 0.2, A[1] + (0.92 - A[1]) * 0.2), (px, 0.915)], 0.0012, 0.003)
              for px in (-0.15, -0.08, 0.0, 0.08, 0.15)]
    return [top, cloth], 'edge', carves

def _it_carbide(g, ang, spec):
    """Carbide lamp held up by its hook: brass body, round reflector, a jet of flame."""
    return [xf(p, s=1.6, ox=g[0], oy=g[1]) for p in _carbide(g)[0]], 'solid', [xf(p, s=1.6, ox=g[0], oy=g[1]) for p in _carbide(g)[1]]

def _carbide(g):
    x, y = g
    polys = [ribbon(arc_pts(x, y + 0.015, 0.018, 180, 360, 8), 0.004), rect(x - 0.018, y - 0.075, x + 0.018, y),
             rect(x - 0.022, y - 0.08, x + 0.022, y - 0.068), rect(x - 0.016, y, x + 0.016, y + 0.012),
             ribbon([(x + 0.018, y - 0.03), (x + 0.045, y - 0.02)], 0.004), ellipse(x + 0.06, y - 0.02, 0.012, 0.042, n=20),
             leaf(x + 0.068, y - 0.02, 0, 0.05, 0.01)]
    rays = [ribbon([(x + 0.08 + 0.01 * math.cos(math.radians(a)), y - 0.02 + 0.01 * math.sin(math.radians(a))),
                    (x + 0.08 + 0.04 * math.cos(math.radians(a)), y - 0.02 + 0.04 * math.sin(math.radians(a)))], 0.003, 0.001)
            for a in (-40, -20, 20, 40)]
    return polys + rays, [rect(x - 0.01, y - 0.06, x + 0.01, y - 0.012)]

def _it_dulang(g, ang, spec):
    """A wooden dulang held by its rim, hanging at his side."""
    x, y = g
    T = lambda pts: xf(pts, x, y, rot=-28, ox=0, oy=0)
    pan = T(ellipse(-0.02, -0.15, 0.17, 0.075, n=36))
    cuts = [T(ribbon(arc_pts(-0.02, -0.15, 0.13, 200, 340, 14, ry=0.05), 0.0035)), T(ellipse(-0.02, -0.19, 0.012, 0.007, n=10))]
    return [pan], 'solid', cuts

def _it_pan(g, ang, spec):
    """A dulang tilted in the water, swirling the sand (for the washer)."""
    x, y = g
    pan = _open([(x - 0.05, y + 0.02), (x + 0.04, y - 0.02), (x + 0.14, y - 0.035), (x + 0.24, y - 0.02), (x + 0.33, y + 0.02)], 4) + \
        [(x + 0.14, y + 0.03)]
    swirl = [ribbon(arc_pts(x + 0.14, y + 0.06, 0.08, 20, 160, 10), 0.004, 0.002)]
    return [pan] + swirl, 'solid', []

def _it_kandar(g, ang, spec):
    """Shoulder pole with a basket of ore slung from each end."""
    y = g[1] + 0.005
    polys = [ribbon(_open([(-0.4, y - 0.01), (0.0, y + 0.01), (0.42, y - 0.01)]), 0.008)]
    for bx in (-0.38, 0.4):
        polys += [ribbon([(bx, y), (bx - 0.06, y - 0.36)], 0.0025), ribbon([(bx, y), (bx + 0.06, y - 0.36)], 0.0025),
                  [(bx - 0.09, y - 0.36), (bx + 0.09, y - 0.36), (bx + 0.07, y - 0.5), (bx - 0.07, y - 0.5)],
                  _open([(bx - 0.08, y - 0.36), (bx, y - 0.32), (bx + 0.08, y - 0.36)], 3)]
    return polys, 'solid', [rect(bx - 0.06, y - 0.46 + 0.04 * k, bx + 0.06, y - 0.45 + 0.04 * k) for bx in (-0.38, 0.4) for k in range(2)]

def _it_strainer(g, ang, spec):
    """Long-handled noodle strainer dipped toward the pot."""
    a = math.radians(ang - 35)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.24 * d[0], g[1] + 0.24 * d[1])
    basket = xf([(0.0, 0.04), (0.08, 0.035), (0.11, 0.0), (0.08, -0.05), (0.03, -0.06), (0.0, -0.035)], end[0], end[1], rot=math.degrees(a))
    cuts = [xf(ribbon([(0.02 + 0.025 * k, 0.025), (0.02 + 0.025 * k, -0.035)], 0.0025), end[0], end[1], rot=math.degrees(a)) for k in range(3)]
    return [ribbon([(g[0] - 0.04 * d[0], g[1] - 0.04 * d[1]), end], 0.006), basket], 'solid', cuts

W.register(W.HATS, 'perak_turban', _hat_turban)
W.register(W.HATS, 'perak_terendak', _hat_terendak)
W.register(W.BEARDS, 'perak_misai', [(0.074, 0.848), (0.086, 0.842), (0.098, 0.83), (0.095, 0.818), (0.084, 0.828), (0.066, 0.834),
                                     (0.05, 0.828), (0.04, 0.82), (0.036, 0.832), (0.05, 0.846)])
W.register(W.COSTUMES, 'perak_veshti', dict(W.COSTUMES['sarong'], hem=0.46, flare=0.008, sleeve=0.032,
                                            cls={'top': 'dots', 'lower': 'slits', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.ITEMS2, 'perak_carbide', _it_carbide)
W.register(W.ITEMS2, 'perak_dulang', _it_dulang)
W.register(W.ITEMS2, 'perak_pan', _it_pan)
W.register(W.ITEMS2, 'perak_kandar', _it_kandar)
W.register(W.ITEMS2, 'perak_strainer', _it_strainer)
W.register(W.POSES, 'perak_lamp', {'f': (92, 34), 'b': (-12, 4), 'lean': -2, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'perak_carry', {'f': (58, 100), 'b': (-16, -14), 'lean': 6, 'legs': 'walk', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'perak_dip', {'f': (70, 30), 'b': (40, 70), 'lean': 10, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def icon_food_hor_fun(seed=4):
    """Ipoh hor fun: silky flat rice noodles in clear prawn-chicken broth,
    shredded chicken, prawns, chives and fried shallot."""
    rnd = random.Random(seed)
    w, h = 2.0, 2.0 * BOWL_DEPTH
    outer = [(-x * w, y * h) for x, y in reversed(BOWL_PROFILE)]
    rim = outer[-1]
    inner = [(r - 0.05, z) for r, z in reversed(outer) if z > 0.2 * h]
    prof = [(0.0, 0.0)] + outer + [(rim[0] - 0.025, rim[1] + 0.02)] + inner + [(0.0, inner[-1][1])]
    porcelain = _mat('Porcelain', (0.94, 0.93, 0.89), 0.32)
    green = _mat('Celadon', (0.35, 0.55, 0.42), 0.4)
    _lathe('Bowl', prof, porcelain, 72)
    _torus('RimLine', (0, 0, rim[1] - 0.06), rim[0] - 0.012, 0.018, green)
    _torus('Band', (0, 0, 0.55 * h), 0.86, 0.016, green)
    soup_z = 0.84 * h
    _lathe('Soup', [(0.0, soup_z), (0.9, soup_z)], _mat('Broth', (0.78, 0.6, 0.32), 0.15), 64, sharp=0)
    noodle = _mat('HorFun', (0.97, 0.95, 0.9), 0.35)
    for i in range(9):                                    # wide flat ribbons: tubes squashed flat
        a0 = rnd.uniform(0, TAU)
        pts = []
        for k in range(24):
            t = k / 23
            a = a0 + t * rnd.uniform(1.2, 2.0)
            r = 0.15 + 0.6 * abs(math.sin(t * math.pi + i))
            pts.append((r * math.cos(a), r * math.sin(a), 0.1 * math.sin(t * 4 + i)))
        nd = _tube('Noodle%d' % i, pts, 0.075, noodle)
        nd.location.z = soup_z + 0.04 + 0.012 * (i % 3)
        nd.scale.z = 0.22
    chicken = _mat('Chicken', (0.92, 0.85, 0.7), 0.5)
    for i in range(14):
        _box('Ck%d' % i, (-0.25 + rnd.uniform(-0.2, 0.2), 0.1 + rnd.uniform(-0.2, 0.2), soup_z + 0.1 + 0.02 * (i % 3)),
             (0.18, 0.04, 0.035), (rnd.uniform(-0.3, 0.3), 0.2, rnd.uniform(0, 3)), chicken)
    shrimp = _mat('Prawn', (0.95, 0.45, 0.25), 0.4)
    for i, (px, py) in enumerate(((0.32, -0.28), (0.48, 0.05), (0.15, -0.5))):
        pts = [(px + 0.14 * math.cos(math.radians(a)), py + 0.14 * math.sin(math.radians(a)), soup_z + 0.13) for a in range(200, -40, -24)]
        _tube('Prawn%d' % i, pts, 0.05, shrimp)
        _blob('Tail%d' % i, pts[-1], (0.06, 0.035, 0.012), (0, 0, 0.5), shrimp, 10)
    chive = _mat('Chive', (0.25, 0.6, 0.15), 0.45)
    for i in range(18):
        _torus('Chive%d' % i, (rnd.uniform(-0.55, 0.55), rnd.uniform(-0.55, 0.55), soup_z + 0.16), 0.022, 0.009, chive,
               rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0), seg=10)
    shallot = _mat('Shallot', (0.55, 0.32, 0.12), 0.6)
    for i in range(16):
        _blob('Sh%d' % i, (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), soup_z + 0.14), (0.03, 0.018, 0.008), (0, 0, rnd.uniform(0, 3)),
              shallot, 8)
    return (0, -4.7, 4.1), (0, 0, 0.55)

def icon_item_miner_lamp():
    """Miner's lamp trinket: a small brass carbide lamp with its round
    reflector, hung on a chain loop."""
    from mathutils import Euler
    brass = _mat('Brass', (0.8, 0.58, 0.24), 0.4, metal=1.0)
    steel = _mat('Mirror', (0.88, 0.88, 0.86), 0.15, metal=1.0)
    dark = _mat('Dark', (0.18, 0.12, 0.06), 0.6, metal=1.0)
    parts = [_lathe('Base', [(0.0, 0.0), (0.32, 0.0), (0.34, 0.04), (0.32, 0.55), (0.3, 0.6), (0.0, 0.6)], brass, 48)]
    parts.append(_torus('Seam', (0, 0, 0.58), 0.31, 0.025, brass, seg=48))
    parts.append(_lathe('Top', [(0.0, 0.6), (0.3, 0.6), (0.28, 0.9), (0.22, 1.0), (0.0, 1.02)], brass, 48))
    for z in (0.15, 0.4, 0.8):
        parts.append(_torus('Rib%.2f' % z, (0, 0, z), 0.335 if z < 0.6 else 0.29, 0.012, dark, seg=48))
    parts.append(_lathe('Knob', [(0.0, 1.0), (0.07, 1.0), (0.07, 1.12), (0.1, 1.15), (0.0, 1.17)], dark, 16))
    refl = _lathe('Reflector', [(0.0, 0.0), (0.05, 0.0), (0.3, 0.12), (0.34, 0.14), (0.32, 0.15), (0.05, 0.03), (0.0, 0.03)], steel, 48)
    refl.location = (0.0, -0.3, 0.82)
    refl.rotation_euler = (math.radians(90), 0, 0)
    parts.append(refl)
    tip = _lathe('Jet', [(0.0, 0.0), (0.035, 0.0), (0.03, 0.08), (0.0, 0.1)], brass, 16)
    tip.location = (0.0, -0.33, 0.82)
    tip.rotation_euler = (math.radians(90), 0, 0)
    parts.append(tip)
    flame = _blob('Flame', (0.0, -0.5, 0.82), (0.035, 0.09, 0.035), (0, 0, 0), _mat('Flame', (1.0, 0.75, 0.3), 0.5), 12)
    flame.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (1.0, 0.6, 0.2, 1)
    flame.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.5
    parts.append(flame)
    hook = _tube('Hook', [(0.0, 0.25, 0.9)] + [(0.0, 0.25 + 0.2 * math.sin(math.radians(a)), 1.1 + 0.2 * math.cos(math.radians(a)))
                                              for a in range(-180, 1, 20)], 0.02, dark)
    parts.append(hook)
    for k in range(16):                                   # chain loop up from the knob
        a = TAU * k / 16
        px, pz = 0.2 * math.sin(a), 1.47 + 0.3 * (1 - math.cos(a))
        tang = math.atan2(0.3 * math.sin(a), 0.2 * math.cos(a))
        lk = _torus('Link%d' % k, (px, 0.0, pz), 0.05, 0.013, brass,
                    rot=(math.radians(90), -tang, 0.0) if k % 2 else (0.0, math.radians(90), 0.0), seg=16)
        parts.append(lk)
    pivot = bpy.data.objects.new('Pivot', None)
    bpy.context.scene.collection.objects.link(pivot)
    for ob in parts:
        ob.parent = pivot
    pivot.rotation_euler = Euler((0, 0, math.radians(-22)))
    pivot.scale = (1.2, 1.2, 1.2)
    return (0.4, -6.0, 3.3), (0.0, 0, 1.0)

# =====================================================================
# registry: what the CLI renders for this state
# =====================================================================

PUPPET = dict(head='old', beard='perak_misai', hat='perak_turban', costume='perak_veshti', pose='perak_lamp',
              item_f='perak_carbide', item_b='perak_dulang', scarf=True)        # Uncle Chandran
BEATS = {'land': perak_land, 'people': perak_people, 'food': perak_food}
ICONS = {'food': icon_food_hor_fun, 'item': icon_item_miner_lamp}
