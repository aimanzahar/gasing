"""Sarawak: Tuai Rumah Jarat's longhouse -- the rumah panjang on its stilts with
families along the ruai, Gawai preparations (rice pounding, tuak, gongs, pua
kumbu), a bowl of Sarawak laksa, and the longhouse chief himself."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props
# =====================================================================

def rumah_panjang(cv, x0, x1, y, s=1.0, layer='mid', doors=8, wall_layer=None):
    """The longhouse broadside: a forest of stilts, the long floor, the bilik
    wall with its row of doors behind the open ruai gallery, the railing, a
    long thatched roof with carved horned gable boards at both ends.
    Returns the gallery floor height (where families stand)."""
    fl = y + 1.3 * s
    eave, ridge = y + 2.75 * s, y + 3.55 * s
    posts = []
    n = int((x1 - x0) / (0.62 * s))
    for i in range(n + 1):
        px = x0 + (x1 - x0) * i / n
        posts.append(rect(px - 0.045 * s, y, px + 0.045 * s, fl))
        if i % 3 == 1:                                  # cross bracing under the floor
            posts.append(ribbon([(px, y + 0.25 * s), (px + 0.6 * s, fl - 0.12 * s)], 0.018 * s))
    posts.append(rect(x0 - 0.15 * s, fl - 0.1 * s, x1 + 0.15 * s, fl + 0.06 * s))
    cv.add(posts, 'solid', layer)
    wall = [rect(x0, fl, x1, eave)]
    dw = (x1 - x0) / doors
    for k in range(doors):
        cx = x0 + dw * (k + 0.5)
        wall.append(rect(cx - 0.2 * s, fl + 0.1 * s, cx + 0.2 * s, fl + 1.05 * s))
    cv.add_eo(wall, 'grid', wall_layer or layer)
    rail = [ribbon([(x0, fl + 0.5 * s), (x1, fl + 0.5 * s)], 0.03 * s)]
    k = 0
    xx = x0
    while xx <= x1 + 1e-6:
        rail.append(ribbon([(xx, fl), (xx, fl + 0.5 * s)], 0.014 * s))
        xx += 0.22 * s
    cv.add(rail, 'solid', layer)
    roof = [(x0 - 0.55 * s, eave - 0.1 * s), (x0 - 0.1 * s, ridge), (x1 + 0.1 * s, ridge), (x1 + 0.55 * s, eave - 0.1 * s),
            (x1 + 0.3 * s, eave), (x0 - 0.3 * s, eave)]
    cv.add([roof], 'scales', layer)
    horns = []
    for ex, sg in ((x0 - 0.1 * s, -1), (x1 + 0.1 * s, 1)):   # carved gable horns
        horns.append(ribbon(_open([(ex, ridge - 0.1 * s), (ex + sg * 0.15 * s, ridge + 0.25 * s), (ex + sg * 0.05 * s, ridge + 0.5 * s)]),
                            0.035 * s, 0.01 * s))
        horns.append(scroll(ex + sg * 0.12 * s, ridge + 0.55 * s, 0.08 * s, 0.025 * s, 1.2, a0=270, cw=sg < 0))
    horns.append(ribbon([(x0 - 0.1 * s, ridge), (x1 + 0.1 * s, ridge)], 0.04 * s))
    cv.add(horns, 'solid', layer)
    return fl

def tangga(cv, x, y, h, layer='mid', lean=0.25):
    """Tangga: the notched-log ladder leaning up to the deck."""
    top = (x + lean * h, y + h)
    cv.add([ribbon([(x, y), top], 0.07, 0.06)], 'solid', layer)
    cv.carve([xf([(-0.07, 0.0), (0.0, 0.04), (0.0, -0.04)], x + lean * h * t, y + h * t) for t in (0.15, 0.32, 0.49, 0.66, 0.83)],
             layer)

def kenyalang(cv, x, y, h, layer='mid', flip=False):
    """Kenyalang: the carved rhinoceros-hornbill effigy on its tall pole --
    great upturned casque, long beak, scrolling crest and fanned tail."""
    P = lambda pts: xf(pts, x, y, flip=flip)
    pole = [rect(-0.06, 0.0, 0.06, h)]
    pole += [rect(-0.1, h * t, 0.1, h * t + 0.06) for t in (0.3, 0.55, 0.8)]
    cv.add([P(p) for p in pole], 'edge', layer)
    b = h + 0.05                                        # the bird stands on the pole top
    body = ellipse(0.0, b + 0.35, 0.42, 0.24, rot=12)
    neck = ribbon(_open([(0.28, b + 0.45), (0.38, b + 0.65), (0.42, b + 0.85)]), 0.1, 0.09)
    head = ellipse(0.45, b + 0.9, 0.13, 0.11)
    beak = [(0.52, b + 0.95), (1.25, b + 0.82), (1.3, b + 0.76), (0.55, b + 0.8)]
    casque = [(0.5, b + 0.98), (0.75, b + 1.12), (1.0, b + 1.3), (1.04, b + 1.22), (0.95, b + 1.05), (0.6, b + 0.94)]
    tail = [(-0.3, b + 0.3), (-0.95, b + 0.62), (-1.0, b + 0.42), (-0.95, b + 0.18), (-0.35, b + 0.18)]
    crest = [scroll(-0.05 + 0.25 * k, b + 0.7 + 0.04 * k, 0.12, 0.035, 1.2, a0=270, cw=True,
                    tail=[(-0.1 + 0.25 * k, b + 0.5), (-0.08 + 0.25 * k, b + 0.6)]) for k in range(2)]
    legs = [ribbon([(0.0, b + 0.15), (0.0, b - 0.02)], 0.03), rect(-0.12, b - 0.05, 0.14, b + 0.0)]
    pid = cv.add([P(p) for p in (body, neck, head, beak, casque, tail) + tuple(crest) + tuple(legs)], 'lace', layer)
    cuts = [P(W.circle(0.48, b + 0.92, 0.03, 10)[0]), P(ribbon([(0.58, b + 0.88), (1.15, b + 0.8)], 0.008))]
    cuts += [P(ribbon([(-0.4 - 0.13 * k, b + 0.25), (-0.55 - 0.13 * k, b + 0.55)], 0.01)) for k in range(4)]
    cuts.append(P(ribbon(spiral(0.0, b + 0.35, 0.14, 1.4, a0=90), 0.012)))
    cv.carve(cuts, layer)
    return pid

def hornbill_fly(cv, x, y, s, layer='back', flip=False):
    """A hornbill in flight: broad fingered wings, casque and long tail."""
    polys = [ellipse(0, 0, 0.34, 0.085), ellipse(0.36, 0.05, 0.08, 0.065),
             _open([(0.4, 0.07), (0.6, 0.02), (0.8, -0.06)], 4) + [(0.78, -0.08), (0.42, 0.0)],          # down-curved beak
             [(0.38, 0.1), (0.55, 0.16), (0.66, 0.1), (0.5, 0.08)],                                       # casque
             [(-0.3, 0.02), (-0.82, 0.07), (-0.84, -0.04), (-0.3, -0.04)],                                # long tail
             leaf(-0.02, 0.05, 105, 0.62, 0.15, bend=-0.08, wide_at=0.6),                                 # wing up
             leaf(0.02, 0.0, 165, 0.42, 0.1, bend=0.05)]                                                  # far wing
    return cv.add([xf(p, x, y, s=s, flip=flip) for p in polys], 'solid', layer)

def moon(cv, cx, cy, r, layer='mid'):
    """Bulan sabit: a crescent moon with a carved rim line."""
    poly = arc_pts(cx, cy, r, 60, 300, 40) + arc_pts(cx + r * 0.42, cy, r * 0.78, 290, 70, 30)
    cv.add([poly], 'edge', layer)

def lesung(cv, x, y, s=1.0, layer='mid'):
    """Lesung: the heavy wooden rice mortar, waisted, with a carved band."""
    left = _open([(-0.42 * s, 0.82 * s), (-0.38 * s, 0.6 * s), (-0.26 * s, 0.42 * s), (-0.3 * s, 0.2 * s), (-0.44 * s, 0.0)], 4)
    cv.add([xf(mirror_pts(left), x, y)], 'lace', layer)
    cv.carve([xf(ribbon([(-0.34 * s, 0.68 * s), (0.34 * s, 0.68 * s)], 0.012 * s), x, y)] +
             [xf(W.diamond(k * 0.12 * s, 0.25 * s, 0.07 * s, 0.1 * s)[0], x, y) for k in (-2, -1, 0, 1, 2)], layer)

def gong_rack(cv, x, y, s=1.0, layer='mid'):
    """A rack of three hanging gongs (tawak and bebendai) for the Gawai music."""
    P = lambda pts: xf(pts, x, y, s=s)
    cv.add([P(rect(-1.25, 0.0, -1.12, 2.1)), P(rect(1.12, 0.0, 1.25, 2.1)), P(rect(-1.35, 2.02, 1.35, 2.14))], 'edge', layer)
    for gx, r in ((-0.66, 0.42), (0.18, 0.33), (0.82, 0.26)):
        cv.add([P(ribbon([(gx, 2.02), (gx, 1.55 - 0.42 + r)], 0.01))], 'solid', layer)
        cv.add([P(ellipse(gx, 1.55 - 0.42, r, n=32))], 'edge', layer)
        cv.carve([P(ribbon(arc_pts(gx, 1.13, r * 0.68, 0, 360, 24), 0.01))], layer)
        cv.add([P(ellipse(gx, 1.13, r * 0.25, n=16))], 'solid', layer)

def pua(cv, x0, y_top, x1, h, layer='mid'):
    """A pua kumbu hung on a line: ikat lozenges with hooked arms and a
    pucuk rebung border at the foot."""
    pid = cv.add([rect(x0, y_top - h, x1, y_top)], 'edge', layer)
    cv.add([ribbon([(x0 + 0.06 + k * (x1 - x0 - 0.12) / 12, y_top - h), (x0 + 0.06 + k * (x1 - x0 - 0.12) / 12, y_top - h - 0.16)],
                   0.012, 0.006) for k in range(13)], 'solid', layer, pid=pid)
    cuts = []
    nx = max(2, int((x1 - x0) / 0.8))
    ny = max(1, int((h - 0.5) / 0.75))
    for i in range(nx):
        for j in range(ny):
            cx = x0 + (i + 0.5) * (x1 - x0) / nx
            cy = y_top - 0.15 - (j + 0.5) * (h - 0.6) / ny
            ww, hh = (x1 - x0) / nx * 0.36, (h - 0.6) / ny * 0.38
            cuts.append(ribbon([(cx, cy + hh), (cx + ww, cy), (cx, cy - hh), (cx - ww, cy), (cx, cy + hh)], 0.016))
            cuts.append(W.diamond(cx, cy, ww * 0.5, hh * 0.5)[0])
            for sx, sy in ((1, 1), (-1, -1)):
                cuts.append(ribbon(spiral(cx + sx * ww * 0.9, cy + sy * hh * 0.9, ww * 0.25, 1.1, a0=0 if sx > 0 else 180),
                                   0.01))
    k = int((x1 - x0) / 0.3)
    cuts += [[(x0 + 0.05 + i * (x1 - x0 - 0.1) / k, y_top - h + 0.06), (x0 + 0.05 + (i + 0.5) * (x1 - x0 - 0.1) / k, y_top - h + 0.42),
              (x0 + 0.05 + (i + 1) * (x1 - x0 - 0.1) / k, y_top - h + 0.06)] for i in range(k)]
    cv.carve(cuts, layer)

def padi_basket(cv, x, y, s=1.0, layer='mid'):
    """A round harvest basket heaped with cut padi, ears drooping over the rim."""
    cv.add([xf([(-0.45, 0.0), (0.45, 0.0), (0.55, 0.6), (-0.55, 0.6)], x, y, s=s)], 'grid', layer)
    polys = []
    for k in range(11):
        a = 60 + 6 * k
        bx = (-0.4 + 0.08 * k) * s
        polys.append(ribbon(_open([(x + bx, y + 0.55 * s), (x + bx + 0.1 * s * math.cos(math.radians(a)), y + 0.95 * s),
                                   (x + bx + (0.25 if k > 5 else -0.25) * s, y + 1.05 * s)]), 0.012 * s, 0.006 * s))
        polys.append(leaf(x + bx + (0.25 if k > 5 else -0.25) * s, y + 1.05 * s, -70 if k > 5 else -110, 0.22 * s, 0.03 * s))
    cv.add(polys, 'solid', layer)

def laksa_bowl(cv, cx, y, w, layer='mid'):
    """Sarawak laksa: the bowl heaped with vermicelli, three curled prawns on
    top, omelette strips, chicken shreds, coriander and a lime on the rim."""
    rim = bowl(cv, cx, y, w, layer, cls='lace', heap=None)
    h = rim - y
    mound = _open([(-0.45 * w, h * 0.9), (-0.38 * w, h * 1.08), (-0.2 * w, h * 1.18), (0.0, h * 1.22), (0.22 * w, h * 1.17),
                   (0.38 * w, h * 1.06), (0.45 * w, h * 0.9)], 5)
    cv.add([xf(mound, cx, y)] + [ribbon(_open([(cx + sx * 0.36 * w, y + h * 1.04), (cx + sx * 0.5 * w, y + h * 1.0),
                                                (cx + sx * 0.5 * w, y + h * 0.84)]), 0.009 * w, 0.006 * w) for sx in (-1, 1)],
           'edge', layer)
    for k, (dx, a, sc) in enumerate(((-0.22, 20, 1.0), (0.02, -5, 1.1), (0.24, -25, 0.95))):
        prawn(cv, cx + dx * w, y + h * 1.24, 0.26 * w * sc, rot=a, layer=layer)
    herbs = [leaf(cx + (-0.36 + 0.06 * k) * w, y + h * 1.12, 70 + 9 * k, 0.09 * w, 0.025 * w) for k in range(4)]
    herbs += [ribbon([(cx + (0.1 + 0.07 * k) * w, y + h * 1.2), (cx + (0.16 + 0.07 * k) * w, y + h * 1.36)], 0.01 * w) for k in range(3)]
    cv.add(herbs, 'solid', layer)
    half = [(cx + 0.38 * w, y + h * 1.0)] + arc_pts(cx + 0.47 * w, y + h * 1.0, 0.09 * w, 180, 0, 12)[1:-1] + [(cx + 0.56 * w, y + h * 1.0)]
    cv.add([xf(half, rot=25, ox=cx + 0.47 * w, oy=y + h)], 'edge', layer)

def prawn(cv, x, y, s, rot=0.0, layer='mid', flip=False):
    """Udang: a cooked prawn curled into an arch, its shell bands cut across
    the back, a fan tail, a pointed head and one long feeler swept back."""
    P = lambda pts: xf(pts, x, y, s=s, rot=rot, flip=flip)
    arc = arc_pts(0.0, 0.0, 0.4, 200, 25, 24)
    body = ribbon(arc, 0, wf=lambda t: 0.15 - 0.09 * t)
    tip = arc[-1]
    tail = [leaf(tip[0], tip[1], a, 0.24, 0.07) for a in (-35, -70)]
    head = [(-0.5, -0.02), (-0.66, -0.2), (-0.42, -0.1), (-0.3, 0.02)]
    feeler = ribbon(_open([(-0.55, -0.12), (-0.75, 0.15), (-0.55, 0.5), (-0.15, 0.62)]), 0.012, 0.004)
    legs = [ribbon([(-0.2 + 0.12 * k, -0.02 + 0.06 * k), (-0.22 + 0.12 * k, -0.2 + 0.05 * k)], 0.012) for k in range(4)]
    cv.add([P(p) for p in [body, head, feeler] + tail + legs], 'edge', layer)
    bands = []
    for k in range(1, 6):
        a = math.radians(200 - 30 * k)
        c, n = (0.4 * math.cos(a), 0.4 * math.sin(a)), (math.cos(a), math.sin(a))
        w = 0.12 - 0.012 * k
        bands.append(ribbon([(c[0] - n[0] * w * 0.7, c[1] - n[1] * w * 0.7), (c[0] + n[0] * w * 0.7, c[1] + n[1] * w * 0.7)], 0.01))
    cv.carve([P(b) for b in bands] + [P(W.circle(-0.44, -0.04, 0.03, 8)[0])], layer)

def kopitiam_back(cv):
    """Blurred kopitiam wall: shuttered window, a shelf of biscuit tins, a
    hanging lamp each side and the hawker's broth pot steaming on the counter."""
    cv.add_eo([rect(13.8, 2.6, 17.8, 6.2), rect(14.05, 2.85, 15.75, 5.95), rect(15.85, 2.85, 17.55, 5.95)], 'edge', 'back')
    cv.add([rect(1.0, 5.0, 5.4, 5.12)] + [rect(1.2 + 0.85 * k, 5.12, 1.85 + 0.85 * k, 5.85) for k in range(5)], 'solid', 'back')
    for x in (6.2, 15.6):
        cv.add([ribbon([(x, 8.3), (x, 7.4)], 0.02), [(x - 0.45, 6.9), (x + 0.45, 6.9), (x + 0.15, 7.4), (x - 0.15, 7.4)]], 'solid', 'back')
    cv.add([rect(0.4, G, 6.0, 2.5)], 'solid', 'back')
    periuk(cv, 3.2, 2.5, 1.3, 'back')

def kopitiam_table(cv, x, y, w, h, layer='mid'):
    """Marble-topped kopitiam table on its cast-iron pedestal."""
    cv.add([xf([(-0.5 * w, h), (0.5 * w, h), (0.5 * w, h - 0.12), (-0.5 * w, h - 0.12)], x, y),
            xf(ribbon(_open([(0.0, h - 0.1), (0.04, h * 0.6), (-0.03, h * 0.3), (0.0, 0.1)]), 0.06, 0.08), x, y),
            xf([(-0.45, 0.0), (0.45, 0.0), (0.1, 0.12), (-0.1, 0.12)], x, y)], 'edge', layer)

# =====================================================================
# rig parts (registered once, keys prefixed with the state id)
# =====================================================================

def _labong():
    """Labong: the Iban chief's woven cap with hornbill tail feathers swept
    back, barred black and white."""
    cap = _open([(0.06, 0.9), (0.06, 0.935), (0.042, 0.962), (0.0, 0.975), (-0.042, 0.963), (-0.062, 0.93),
                 (-0.06, 0.888)]) + [(0.0, 0.902)]
    feathers, cuts = [], []
    for k, (a, L) in enumerate(((150, 0.25), (162, 0.23), (138, 0.2))):
        base = (-0.03, 0.958 - 0.006 * k)
        d = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        tip = (base[0] + L * d[0], base[1] + L * d[1])
        feathers.append(leaf(base[0], base[1], a, L, 0.016, wide_at=0.7))
        for t in (0.55, 0.7, 0.85):
            cx, cy = base[0] + L * t * d[0], base[1] + L * t * d[1]
            cuts.append(ribbon([(cx - 0.01 * d[1], cy + 0.01 * d[0]), (cx + 0.01 * d[1], cy - 0.01 * d[0])], 0.0035))
    cuts += [ribbon([(-0.05, 0.92 + 0.016 * k), (0.05, 0.925 + 0.016 * k)], 0.0018) for k in range(3)]
    return [cap] + feathers, 'edge', cuts

def _sirat(body):
    """Sirat: the long front flap of the loincloth, hanging to the shins."""
    return [(0.05, 0.56), (0.07, 0.5), (0.085, 0.2), (0.07, 0.16), (0.02, 0.17), (-0.01, 0.2), (-0.05, 0.5), (-0.055, 0.56)]

def _chief(spec):
    """A pua kumbu cloth over the shoulder and the ilang sword at the hip."""
    cloth = ribbon(_open([(0.05, 0.79), (-0.03, 0.76), (-0.085, 0.7), (-0.1, 0.55), (-0.095, 0.4)]), 0.022, 0.03)
    ilang = [ribbon(_open([(-0.04, 0.53), (-0.14, 0.42), (-0.22, 0.36)]), 0.013, 0.01),
             [(-0.02, 0.56), (0.0, 0.53), (-0.04, 0.5), (-0.06, 0.53)]]
    tassels = [ribbon([(-0.03, 0.52), (-0.025 + 0.008 * k, 0.45)], 0.002) for k in range(3)]
    return [([cloth], 'flower', [W.diamond(-0.09, 0.6 - 0.07 * k, 0.018, 0.03)[0] for k in range(3)]),
            (ilang + tassels, 'solid', [])]

def _it_tongkat(g, ang, fig):
    """The chief's staff, its head carved as a kenyalang."""
    x = g[0] + 0.006
    shaft = ribbon([(x + 0.015, 0.0), (x, 0.98)], 0.0075, 0.009)
    b = 0.98
    bird = [ellipse(x, b + 0.03, 0.04, 0.024, rot=12), ellipse(x + 0.042, b + 0.068, 0.016, 0.014),
            [(x + 0.05, b + 0.075), (x + 0.13, b + 0.058), (x + 0.135, b + 0.05), (x + 0.055, b + 0.062)],
            [(x + 0.05, b + 0.08), (x + 0.09, b + 0.1), (x + 0.11, b + 0.12), (x + 0.1, b + 0.095), (x + 0.06, b + 0.078)],
            [(x - 0.03, b + 0.03), (x - 0.1, b + 0.06), (x - 0.1, b + 0.02), (x - 0.03, b + 0.015)]]
    rings = [rect(x - 0.012, b - 0.06 - 0.04 * k, x + 0.012, b - 0.05 - 0.04 * k) for k in range(2)]
    return [shaft] + bird + rings, 'solid', [W.circle(x + 0.044, b + 0.07, 0.005, 8)[0]]

def _it_alu(g, ang, fig):
    """Alu: the long rice pestle, upright in both hands."""
    lo, hi = fig.get('alu', (0.25, 1.3))
    x = g[0] + 0.004
    return [ribbon([(x, lo), (x, hi)], 0.016, 0.014), ellipse(x, lo + 0.02, 0.022, 0.035)], 'edge', []

def _it_tajau(g, ang, fig):
    """A tajau of tuak carried on the shoulder."""
    x, y = g[0] - 0.02, g[1] + 0.005
    left = _open([(-0.05, 0.22), (-0.045, 0.19), (-0.08, 0.16), (-0.12, 0.1), (-0.11, 0.03), (-0.06, -0.01), (-0.045, -0.015)], 4)
    jar = xf(mirror_pts(left), x, y)
    lugs = [ellipse(x + sx * 0.1, y + 0.135, 0.016, 0.012) for sx in (-1, 1)]
    return [jar] + lugs, 'lace', [xf(ribbon([(-0.1, 0.1), (0.1, 0.1)], 0.003), x, y)]

def _it_beater(g, ang, fig):
    """A padded gong beater."""
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.14 * d[0], g[1] + 0.14 * d[1])
    return [ribbon([(g[0] - 0.03 * d[0], g[1] - 0.03 * d[1]), end], 0.006), ellipse(end[0], end[1], 0.022, 0.022)], 'solid', []

def _it_saucer(g, ang, fig):
    """A saucer of sambal belacan with a lime half, offered with the laksa."""
    x, y = g[0] + 0.05, g[1] + 0.005
    return [[(x - 0.07, y + 0.012), (x + 0.07, y + 0.012), (x + 0.05, y - 0.01), (x - 0.05, y - 0.01)],
            ellipse(x - 0.02, y + 0.025, 0.028, 0.018), [(x + 0.01, y + 0.012)] + arc_pts(x + 0.035, y + 0.012, 0.025, 180, 0, 8)[1:-1] +
            [(x + 0.06, y + 0.012)]], 'solid', []

def _it_chopsticks(g, ang, fig):
    return [ribbon([(g[0] - 0.02, g[1] - 0.03), (g[0] + 0.12, g[1] + 0.1)], 0.0035),
            ribbon([(g[0] - 0.015, g[1] - 0.04), (g[0] + 0.13, g[1] + 0.08)], 0.0035)], 'solid', []

def _sanggul():
    """Hair drawn back into a bun."""
    hair = _open([(0.052, 0.912), (0.034, 0.944), (0.0, 0.956), (-0.036, 0.946), (-0.052, 0.912), (-0.05, 0.86)]) +            [(-0.03, 0.872), (0.0, 0.915), (0.03, 0.912)]
    return [hair, ellipse(-0.064, 0.9, 0.026, 0.024)], 'solid', [ribbon([(-0.08, 0.9), (-0.045, 0.905)], 0.0025)]

def _sugu():
    """Sugu tinggi: the tall silver comb-crown Iban women wear for Gawai."""
    polys = list(_sanggul()[0])
    polys.append(rect(-0.05, 0.94, 0.05, 0.958))
    for k in range(9):
        x = -0.045 + 0.0112 * k
        top = 1.06 + 0.02 * math.sin(math.pi * k / 8)
        polys.append(ribbon([(x, 0.955), (x, top)], 0.0028))
        polys.append(W.diamond(x, top, 0.012, 0.02)[0])
    polys.append(ribbon([(-0.05, 1.01), (0.05, 1.01)], 0.003))
    return polys, 'solid', []

W.register(W.HATS, 'sarawak_sanggul', _sanggul)
W.register(W.HATS, 'sarawak_sugu', _sugu)
W.register(W.HATS, 'sarawak_labong', _labong)
W.register(W.LOWERS, 'sarawak_sirat', _sirat)
W.register(W.COSTUMES, 'sarawak_tuai', dict(W.COSTUMES['farmer'], lower='sarawak_sirat', hem=0.5, extra=_chief,
                                            cls={'top': 'scales', 'lower': 'flower', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.COSTUMES, 'sarawak_iban', dict(W.COSTUMES['farmer'], lower='sarawak_sirat', hem=0.5,
                                            cls={'top': 'dots', 'lower': 'flower', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.COSTUMES, 'sarawak_bidang', dict(W.COSTUMES['kurung'], hem=0.52, flare=0.0,
                                              cls={'top': 'lace', 'lower': 'flower', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.POSES, 'sarawak_tuai', {'f': (26, 34), 'b': (-14, -12), 'lean': -2, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'sarawak_pound_up', {'f': (162, 12), 'b': (150, 24), 'lean': -4, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'sarawak_pound_down', {'f': (50, 64), 'b': (40, 78), 'lean': 12, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'sarawak_shoulder', {'f': (150, 120), 'b': (-14, -12), 'lean': 4, 'legs': 'walk', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'sarawak_strike', {'f': (78, 40), 'b': (20, 30), 'lean': 4, 'legs': 'walk', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'sarawak_eat', {'f': (60, 70), 'b': (30, 60), 'lean': 6, 'legs': 'sit', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'sarawak_wave', {'f': (140, 30), 'b': (-14, -12), 'lean': 0, 'legs': 'stand', 'hf': 'open', 'hb': 'open'})
W.register(W.POSES, 'sarawak_winnow', {'f': (62, 40), 'b': (52, 52), 'lean': 6, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'})
W.register(W.ITEMS2, 'sarawak_nyiru', lambda g, ang, fig: (
    [[(g[0] - 0.12, g[1] + 0.02), (g[0] + 0.22, g[1] + 0.07), (g[0] + 0.22, g[1] + 0.04), (g[0] - 0.12, g[1] - 0.01)]] +
    [W.circle(g[0] + 0.02 + 0.05 * k, g[1] + 0.1 + 0.03 * (k % 2) + 0.02 * k, 0.006, 6)[0] for k in range(4)], 'solid', []))
W.register(W.ITEMS2, 'sarawak_tongkat', _it_tongkat)
W.register(W.ITEMS2, 'sarawak_alu', _it_alu)
W.register(W.ITEMS2, 'sarawak_tajau', _it_tajau)
W.register(W.ITEMS2, 'sarawak_beater', _it_beater)
W.register(W.ITEMS2, 'sarawak_saucer', _it_saucer)
W.register(W.ITEMS2, 'sarawak_chopsticks', _it_chopsticks)

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def sarawak_land(cv):
    """The rumah panjang on its stilts at dusk, families gathered all along
    its gallery, the kenyalang pole standing guard at its end."""
    hills(cv, -0.5, 21, G + 2.0, 1.4, seed=33, n=4)
    for i, (x, h) in enumerate(((5.5, 3.6), (12.4, 3.2), (17.6, 4.0))):
        cv.add(canopy(x, G + h, 0.9, 40 + i, 8) + [ribbon([(x, G + 1.0), (x, G + h)], 0.12, 0.08)], 'edge', 'back')
    hornbill_fly(cv, 15.2, 6.4, 1.0, flip=True)
    hornbill_fly(cv, 16.7, 6.9, 0.8, flip=True)
    moon(cv, 3.4, 6.9, 0.55)
    cloud(cv, 17.8, 7.4, 0.55, 'back', flip=True, seed=6)
    fl = rumah_panjang(cv, 2.9, 16.4, G, 1.0, doors=9, wall_layer='back')
    tangga(cv, 2.2, G, 1.32, lean=0.45)
    folk = [(4.0, dict(head='old', costume='sarawak_iban', pose='stand')),
            (4.7, dict(body='female', hat='sarawak_sanggul', costume='sarawak_bidang', pose='carry', item_f='bowl')),
            (6.6, dict(head='young', costume='sarawak_iban', pose='sarawak_wave', scale=0.8)),
            (7.3, dict(body='female', hat='sarawak_sanggul', costume='sarawak_bidang', pose='stand')),
            (9.4, dict(head='refined', hat='sarawak_labong', costume='sarawak_iban', pose='teach')),
            (10.15, dict(body='female', hat='sarawak_sanggul', costume='sarawak_bidang', pose='gesture', flip=True)),
            (12.3, dict(head='young', costume='sarawak_iban', pose='stand', scale=0.75, flip=True)),
            (13.0, dict(body='female', hat='sarawak_sanggul', costume='sarawak_bidang', pose='carry', item_f='bowl', flip=True)),
            (14.9, dict(head='old', beard='tuft', costume='sarawak_iban', pose='stick', item_f='stick', flip=True))]
    for x, sp in folk:
        sp = dict(sp, rods=False)
        W.place_figure(cv, sp, x, fl, 1.35, flip=sp.pop('flip', False))
    kenyalang(cv, 1.1, G, 4.1)
    raintree(cv, 18.9, G + 0.02, 3.5, seed=12, flip=True)
    ground(cv, 'earth', seed=7)
    frame_edges(cv, seed=8, left='none', right='none')

def sarawak_people(cv):
    """Gawai is coming: two women pound the new rice turn and turn about, a
    man brings a tajau of tuak, another tries the gongs, and a pua kumbu is
    hung out on the gallery."""
    rumah_panjang(cv, -0.5, 21.0, G + 0.6, 1.2, layer='back', doors=7)
    pua(cv, 13.6, 6.9, 19.2, 2.4)
    cv.add([ribbon([(13.2, 6.92), (19.6, 6.92)], 0.035)], 'solid')
    padi_basket(cv, 1.4, G + 0.02, 1.2)
    W.place_figure(cv, dict(body='female', hat='sarawak_sugu', costume='sarawak_bidang', pose='sarawak_winnow', item_f='sarawak_nyiru',
                            rod_to=-0.25), 3.0, G, 3.2)
    W.place_figure(cv, dict(body='female', hat='sarawak_sugu', costume='sarawak_bidang', pose='sarawak_pound_up', item_f='sarawak_alu',
                            alu=(0.66, 1.62), rod_to=-0.25), 6.45, G, 3.2)
    W.place_figure(cv, dict(body='female', hat='sarawak_sanggul', costume='sarawak_bidang', pose='sarawak_pound_down', item_f='sarawak_alu',
                            alu=(0.24, 1.2), rod_to=-0.25), 8.0, G, 3.2, flip=True)
    lesung(cv, 6.98, G + 0.02, 1.1)
    W.place_figure(cv, dict(head='young', costume='sarawak_iban', pose='sarawak_shoulder', item_f='sarawak_tajau',
                            rod_to=-0.25), 12.0, G, 3.3, flip=True)
    gong_rack(cv, 16.6, G, 1.05)
    W.place_figure(cv, dict(head='refined', costume='sarawak_iban', pose='sarawak_strike', item_f='sarawak_beater',
                            rod_to=-0.25), 14.4, G, 3.3)
    ground(cv, 'earth', seed=17)
    frame_edges(cv, seed=18, left='none', right='none')

def sarawak_food(cv):
    """A steaming bowl of Sarawak laksa on the kopitiam table: prawns on the
    noodles, the server brings sambal and lime, a customer waits, chopsticks up."""
    kopitiam_back(cv)
    kopitiam_table(cv, 10.6, G + 0.02, 4.2, 1.45)
    laksa_bowl(cv, 10.6, G + 1.47, 2.7)
    for i, (dx, hh, cw) in enumerate(((-0.7, 2.0, False), (0.1, 2.4, True), (0.85, 1.9, True))):
        steam(cv, 10.6 + dx, G + 3.2, hh, cw=cw, seed=40 + i)
    W.place_figure(cv, dict(body='female', hat='sarawak_sanggul', costume='sarawak_bidang', pose='serve', item_f='sarawak_saucer', rod_to=-0.25),
                   6.7, G, 3.5)
    cv.add([rect(14.1, G, 14.25, G + 1.0), rect(15.05, G, 15.2, G + 1.0), rect(13.95, G + 0.96, 15.35, G + 1.08)], 'edge')
    W.place_figure(cv, dict(head='refined', costume='baju', pose='sarawak_eat', item_f='sarawak_chopsticks', rod_to=-0.25),
                   14.75, G, 3.3, flip=True)
    limes(cv, 3.6, G + 0.05, 0.9)
    jar(cv, 2.6, G, 0.75, cls='edge')                                   # sambal belacan
    plate(cv, 17.6, G + 0.02, 1.4)
    for k in range(4):                                                  # a stack of kopitiam bowls
        cv.add([xf(mirror_pts([(-0.45, 0.3), (-0.35, 0.08), (-0.2, 0.0)]), 17.6, G + 0.1 + 0.26 * k)], 'edge')
    ground(cv, 'earth', seed=27)
    frame_edges(cv, seed=28, left='none', right='none')

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

def icon_food_laksa_sarawak(seed=4):
    """Sarawak laksa: vermicelli in orange sambal-and-coconut broth, prawns,
    omelette strips, chicken shreds, coriander and a lime half."""
    rnd = random.Random(seed)
    w, h = 2.0, 2.0 * BOWL_DEPTH
    outer = [(-x * w, y * h) for x, y in reversed(BOWL_PROFILE)]
    rim = outer[-1]
    inner = [(r - 0.05, z) for r, z in reversed(outer) if z > 0.2 * h]
    prof = [(0.0, 0.0)] + outer + [(rim[0] - 0.025, rim[1] + 0.02)] + inner + [(0.0, inner[-1][1])]
    china = _mat('China', (0.92, 0.9, 0.84), 0.25)
    red = _mat('RimRed', (0.6, 0.08, 0.05), 0.35)
    _lathe('Bowl', prof, china, 72)
    _torus('RimLine', (0, 0, rim[1] - 0.05), rim[0] - 0.012, 0.016, red)
    soup_z = 0.84 * h
    _lathe('Kuah', [(0.0, soup_z), (0.9, soup_z)], _mat('Kuah', (0.72, 0.32, 0.07), 0.3), 64, sharp=0)
    noodle = _mat('Beehoon', (0.97, 0.95, 0.88), 0.45)
    for i in range(16):
        a0 = rnd.uniform(0, TAU)
        pts = []
        for k in range(30):
            t = k / 29
            a = a0 + t * rnd.uniform(1.5, 2.6)
            r = 0.12 + 0.62 * abs(math.sin(t * math.pi + i))
            pts.append((r * math.cos(a), r * math.sin(a), soup_z + 0.03 + 0.05 * math.sin(t * 6 + i)))
        _tube('Noodle%d' % i, pts, 0.022, noodle)
    egg = _mat('Omelette', (0.98, 0.78, 0.22), 0.45)
    for i in range(9):
        _box('Egg%d' % i, (-0.45 + 0.08 * i, 0.32 + rnd.uniform(-0.06, 0.06), soup_z + 0.1), (0.38, 0.05, 0.02),
             (0, 0, 1.2 + rnd.uniform(-0.3, 0.3)), egg)
    chicken = _mat('Chicken', (0.92, 0.84, 0.7), 0.6)
    for i in range(10):
        _box('Chk%d' % i, (0.35 + rnd.uniform(-0.15, 0.15), 0.3 + rnd.uniform(-0.15, 0.15), soup_z + 0.1), (0.24, 0.035, 0.03),
             (0.2, 0, rnd.uniform(0, 3)), chicken)
    shell = _mat('Prawn', (0.95, 0.42, 0.22), 0.35)
    stripe = _mat('PrawnWhite', (0.98, 0.82, 0.7), 0.4)
    for j, (px, py, rz) in enumerate(((-0.35, -0.25, 0.4), (0.05, -0.38, -0.2), (0.42, -0.15, -0.9))):
        for k in range(7):
            a = math.radians(-40 + 32 * k)
            r = 0.2
            _blob('P%d_%d' % (j, k), (px + r * math.cos(a + rz), py + r * math.sin(a + rz), soup_z + 0.13 + 0.01 * k),
                  (0.085 - 0.006 * k, 0.07 - 0.005 * k, 0.06), (0, 0, a + rz), shell if k % 2 == 0 else stripe, 12)
    herb = _mat('Coriander', (0.15, 0.5, 0.12), 0.5)
    for i in range(10):
        a = rnd.uniform(0, TAU)
        _blob('Cor%d' % i, (0.05 + 0.15 * math.cos(a), 0.05 + 0.12 * math.sin(a), soup_z + 0.2), (0.07, 0.05, 0.01),
              (0.3, 0.2, a), herb, 10)
    skin = _mat('LimeSkin', (0.3, 0.6, 0.12), 0.4)
    pulp = _mat('LimePulp', (0.75, 0.88, 0.38), 0.3)
    h1 = _lathe('Lime', [(0.0, 0.0), (0.12, 0.015), (0.18, 0.08), (0.2, 0.17)], skin, 32)
    c1 = _lathe('LimeCut', [(0.0, 0.17), (0.19, 0.17)], pulp, 32, sharp=0)
    for ob in (h1, c1):
        ob.location, ob.rotation_euler = (0.68, -0.48, soup_z + 0.05), (0.9, 0.2, 0.6)
    return (0, -4.7, 4.1), (0, 0, 0.55)

def _pua_image(n=256):
    """An ikat pua kumbu pattern as an image: hooked lozenges in cream and
    black on rust red, with a stepped border."""
    np = W.np
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    red = np.array([0.42, 0.08, 0.05]); cream = np.array([0.88, 0.72, 0.45]); black = np.array([0.08, 0.05, 0.04])
    img = np.ones((n, n, 3), np.float32) * red
    P = 0.25
    u, v = (x % P) / P - 0.5, (y % P) / P - 0.5
    d = np.abs(u) + np.abs(v)
    img[(d > 0.36) & (d < 0.44)] = cream
    img[(d > 0.18) & (d < 0.24)] = black
    img[d < 0.08] = cream
    hook = (np.abs(u - 0.32) < 0.05) & (np.abs(v + 0.18) < 0.12) | (np.abs(v - 0.32) < 0.05) & (np.abs(u + 0.18) < 0.12)
    img[hook] = black
    border = (x < 0.07) | (x > 0.93)
    img[border] = black
    teeth = border & (((y * 24) % 1.0) < np.abs(np.where(x < 0.5, x, 1 - x) / 0.07 - 0.5) * 2)
    img[teeth] = cream
    rgba = np.concatenate([img, np.ones((n, n, 1), np.float32)], 2)
    im = bpy.data.images.new('Pua', n, n)
    im.pixels.foreach_set(np.ascontiguousarray(rgba[::-1], np.float32).ravel())
    return im

def icon_item_pua():
    """Pua kumbu: the ceremonial ikat cloth, folded and draped over a carved
    rail, its pattern of hooked lozenges in rust, black and cream."""
    m = bpy.data.materials.new('PuaCloth')
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes['Principled BSDF']
    bs.inputs['Roughness'].default_value = 0.85
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = _pua_image()
    tex.interpolation = 'Closest'
    nt.links.new(tex.outputs['Color'], bs.inputs['Base Color'])
    # a cloth draped over a rail: flat on top, falling over the front edge in soft folds
    nu, nv = 40, 48
    verts, faces, uvs = [], [], []
    for j in range(nv + 1):
        t = j / nv
        for i in range(nu + 1):
            u = i / nu
            fold = 0.05 * math.sin(u * TAU * 3) * max(0.0, t - 0.45) * 2
            if t < 0.45:                                # lying on the rail
                yy, zz = -0.6 + 1.2 * (t / 0.45), 0.8
            else:                                       # hanging down in front of it
                a = min(1.0, (t - 0.45) / 0.12) * math.pi / 2
                k = max(0.0, t - 0.57) / 0.43
                yy = 0.6 + 0.12 * math.sin(a) + fold
                zz = 0.8 - 0.12 * (1 - math.cos(a)) - 1.3 * k
            verts.append(((u - 0.5) * 1.8, yy, zz))
            uvs.append((u * 1.5, t * 2.5))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    me = bpy.data.meshes.new('Pua')
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    me.shade_smooth()
    ob = bpy.data.objects.new('Pua', me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(m)
    wood = _mat('Rail', (0.3, 0.16, 0.07), 0.6, grain=(0.16, 0.08, 0.03))
    rail = _tube('Rail', [(-1.15, 0.6, 0.72), (1.15, 0.6, 0.72)], 0.07, wood)
    fringe = _mat('Fringe', (0.85, 0.7, 0.42), 0.8)
    for i in range(18):
        x = -0.85 + 1.7 * i / 17
        _tube('F%d' % i, [(x, 0.72 + 0.02 * math.sin(i), -0.5), (x + 0.01, 0.73, -0.68)], 0.012, fringe)
    _pivot((0, 0, math.radians(-28)), (0, 0, 0.2), 1.0)
    return (0.4, -5.3, 3.1), (0.0, 0.2, 0.15)

# =====================================================================
# registry: what the CLI renders for this state
# =====================================================================

PUPPET = dict(head='old', beard='tuft', hat='sarawak_labong', costume='sarawak_tuai', pose='sarawak_tuai',
              item_f='sarawak_tongkat', lean=-2)                                                   # Tuai Rumah Jarat
BEATS = {'land': sarawak_land, 'people': sarawak_people, 'food': sarawak_food}
ICONS = {'food': icon_food_laksa_sarawak, 'item': icon_item_pua}
