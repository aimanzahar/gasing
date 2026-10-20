"""Melaka: shophouses on the old harbour full of ships from far ports, Nyonyas
beading slippers, a bowl of Nyonya laksa, Uncle Tan with a kasut manik."""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# props: town and harbour
# =====================================================================

def _arch(x0, x1, y0, y1):
    """Opening with a round arch head, from y0 up to the crown y1."""
    r = (x1 - x0) / 2
    return [(x0, y0), (x1, y0)] + arc_pts(x0 + r, y1 - r, r, 0, 180, 14)

def shophouse(cv, cx, y, w=2.4, h1=1.7, h2=1.55, layer='mid', gable='curve'):
    """Peranakan shophouse front: arcaded five-foot way below, shuttered windows
    above, a tiled roof slope and fire walls with curled gable tops."""
    x0, x1 = cx - w / 2, cx + w / 2
    pw = 0.16
    span = (w - 2 * pw) / 3
    arches = [_arch(x0 + pw + i * span + 0.06, x0 + pw + (i + 1) * span - 0.06, y, y + h1 - 0.22) for i in range(3)]
    cv.add_eo([rect(x0, y, x1, y + h1)] + arches, 'edge', layer)
    cv.add([rect(cx - span / 2 + 0.2, y, cx + span / 2 - 0.2, y + h1 * 0.55)], 'slits', layer)   # pintu pagar
    top = y + h1 + 0.14 + h2
    cv.add([rect(x0 - 0.08, y + h1, x1 + 0.08, y + h1 + 0.14), rect(x0 - 0.1, top - 0.02, x1 + 0.1, top + 0.14)], 'solid', layer)
    wins = [_arch(cx + dx - 0.3, cx + dx + 0.3, y + h1 + 0.4, y + h1 + 1.42) for dx in (-w / 4, w / 4)]
    cv.add_eo([rect(x0, y + h1 + 0.14, x1, top)] + wins, 'flower', layer)
    for dx in (-w / 4, w / 4):                         # louvred shutters, one leaf each side
        cv.add([rect(cx + dx - 0.26, y + h1 + 0.44, cx + dx - 0.02, y + h1 + 1.1),
                rect(cx + dx + 0.02, y + h1 + 0.44, cx + dx + 0.26, y + h1 + 1.1)], 'slits', layer)
    cv.add([[(x0 - 0.15, top + 0.12), (x1 + 0.15, top + 0.12), (x1 - 0.1, top + 0.72), (x0 + 0.1, top + 0.72)]], 'scales', layer)
    for sx, xx in ((-1, x0), (1, x1)):                 # fire walls with a curled (water) or stepped gable
        wall = rect(xx - 0.08, y, xx + 0.08, top + 0.8)
        if gable == 'curve':
            cap = scroll(xx + sx * 0.12, top + 0.98, 0.14, 0.05, 1.1, a0=180 if sx < 0 else 0, cw=sx < 0,
                         tail=[(xx - sx * 0.06, top + 0.82), (xx, top + 0.95)])
        else:
            cap = [(xx - 0.16, top + 0.78), (xx + 0.16, top + 0.78), (xx + 0.1, top + 0.92), (xx, top + 1.05), (xx - 0.1, top + 0.92)]
        cv.add([wall, cap], 'solid', layer)
    cv.carve([ribbon([(x0 + 0.1, y + h1 + 0.07), (x1 - 0.1, y + h1 + 0.07)], 0.012),
              ribbon([(x0 + 0.1, top + 0.06), (x1 - 0.1, top + 0.06)], 0.012)] +
             [W.diamond(cx + dx, top - 0.18, 0.12, 0.12)[0] for dx in (-w * 0.38, 0.0, w * 0.38)], layer)

def quay(cv, x0, x1, y, h, layer='mid'):
    """Laterite quay wall, brick courses cut in, steps down to the water."""
    cv.add([rect(x0, y - 0.3, x1, y + h)] + [rect(x1 + 0.22 * i, y - 0.3, x1 + 0.22 * (i + 1), y + h - 0.12 * (i + 1))
                                              for i in range(3)], 'edge', layer)
    cuts = []
    for k in range(3):
        yy = y + (k + 0.5) * h / 3
        cuts.append(ribbon([(x0 + 0.1, yy), (x1 - 0.1, yy)], 0.01))
        cuts += [ribbon([(x0 + 0.35 + 0.55 * i + 0.27 * (k % 2), yy - h / 6 + 0.03), (x0 + 0.35 + 0.55 * i + 0.27 * (k % 2), yy + h / 6 - 0.03)],
                        0.008) for i in range(int((x1 - x0 - 0.5) / 0.55))]
    cv.carve(cuts, layer)

def church_hill(cv, x, y, w, h, layer='back'):
    """Bukit St Paul with the roofless church ruin on its crown."""
    hill = _open([(x - w / 2, y), (x - w * 0.3, y + h * 0.55), (x - w * 0.1, y + h * 0.95), (x + w * 0.12, y + h),
                  (x + w * 0.32, y + h * 0.6), (x + w / 2, y)], 5)
    cv.add([hill], 'edge', layer)
    cv.add_eo([[(x - 0.6, y + h - 0.05), (x + 0.7, y + h - 0.05), (x + 0.7, y + h + 0.7), (x + 0.45, y + h + 0.85),
                (x + 0.45, y + h + 0.7), (x - 0.6, y + h + 0.7)],
               _arch(x - 0.35, x - 0.05, y + h + 0.1, y + h + 0.55), _arch(x + 0.15, x + 0.45, y + h + 0.1, y + h + 0.55)], 'edge', layer)

def junk(cv, x, y, s=1.0, layer='mid', flip=False, seed=1):
    """Chinese junk: high carved stern, bluff bow with a painted eye, three masts
    of battened lug sails."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    hull = _open([(-2.3, 1.8), (-1.9, 1.62), (-1.2, 1.15), (0.0, 1.0), (1.2, 1.06), (2.0, 1.32), (2.25, 1.42)], 5) + \
        _open([(2.25, 1.42), (2.05, 0.9), (1.5, 0.42), (0.5, 0.16), (-0.8, 0.16), (-1.7, 0.42), (-2.15, 0.95), (-2.3, 1.8)], 5)[1:]
    cv.add([P(hull), P([(-2.1, 0.75), (-2.55, 0.25), (-2.2, 0.15), (-1.95, 0.5)])], 'slits', layer)
    cv.carve([P(W.circle(1.85, 1.15, 0.09, 16)[0]), P(W.circle(1.85, 1.15, 0.035, 10)[0])] +
             [P(rect(-2.15 + 0.22 * i, 1.35 + 0.1 * (2 - i), -2.02 + 0.22 * i, 1.5 + 0.1 * (2 - i))) for i in range(3)] +
             [P(ribbon(_open([(-1.8, 1.25), (-0.6, 0.85), (0.8, 0.86), (1.9, 1.1)]), 0.018))], layer)
    for m, top, bot, wide in ((0.2, 4.4, 1.15, 1.5), (1.45, 3.4, 1.2, 1.05), (-1.4, 3.3, 1.45, 0.95)):
        cv.add([P(ribbon([(m, 0.9), (m, top + 0.15)], 0.045, 0.03))], 'solid', layer)
        sail = _open([(m + 0.22, top), (m - wide * 0.45, top - 0.1), (m - wide, top - 0.3)], 4) + \
            _open([(m - wide - 0.12, top - 0.35), (m - wide * 1.1, (top + bot) / 2), (m - wide * 0.98, bot)], 4) + \
            [(m + 0.35, bot), (m + 0.3, (top + bot) / 2)]
        cv.add([P(sail)], 'edge', layer)
        n = int((top - bot) / 0.42)
        cv.carve([P(ribbon([(m + 0.25, bot + (k + 1) * (top - bot) / (n + 1)),
                            (m - wide * (1.02 + 0.06 * math.sin(math.pi * (k + 1) / (n + 1))),
                             bot + (k + 1) * (top - bot) / (n + 1) - 0.06)], 0.014)) for k in range(n)], layer)
    cv.add([P(ribbon([(0.2, 4.55), (-0.15, 4.95)], 0.02)), P([(-0.15, 4.95), (-0.65, 4.82), (-0.15, 4.72)])], 'solid', layer)

def dhow(cv, x, y, s=1.0, layer='mid', flip=False):
    """Arab dhow: long raked hull, one mast, a great lateen sail on a slanting yard."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    hull = _open([(-1.9, 1.15), (-1.6, 1.0), (0.0, 0.85), (1.5, 0.95), (2.4, 1.4)], 5) + \
        _open([(2.4, 1.4), (1.9, 0.7), (1.0, 0.22), (-0.6, 0.16), (-1.55, 0.42), (-1.95, 0.85), (-1.9, 1.15)], 5)[1:]
    cv.add([P(hull)], 'slits', layer)
    cv.carve([P(ribbon(_open([(-1.7, 0.95), (0.0, 0.66), (1.8, 0.82)]), 0.016))], layer)
    cv.add([P(ribbon([(0.35, 0.9), (0.55, 3.0)], 0.045, 0.03)), P(ribbon([(2.2, 1.35), (-1.25, 4.3)], 0.03, 0.018))], 'solid', layer)
    sail = _open([(2.05, 1.5), (0.5, 2.85), (-1.15, 4.18)], 5) + _open([(-1.15, 4.18), (-1.1, 2.6), (-1.5, 1.35)], 5)[1:] + \
        _open([(-1.5, 1.35), (0.2, 1.55), (2.05, 1.5)], 5)[1:-1]
    cv.add([P(sail)], 'dots', layer)

def sampan(cv, x, y, s=1.0, layer='mid', flip=False, rower=True):
    """A small sampan with a standing boatman sculling at the stern."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    cv.add([P(_open([(-1.2, 0.55), (-0.9, 0.42), (0.0, 0.38), (0.9, 0.42), (1.25, 0.6)], 5) +
              _open([(1.25, 0.6), (0.9, 0.18), (0.0, 0.08), (-0.9, 0.18), (-1.2, 0.55)], 5)[1:])], 'edge', layer)
    cv.add([P([(-0.3, 0.42), (0.6, 0.42), (0.5, 0.95), (-0.2, 0.95)])], 'grid', layer)                 # woven hood
    if rower:
        W.place_figure(cv, dict(head='refined', hat='caping', costume='farmer', pose='pull', rods=False),
                       x + (-0.85 if not flip else 0.85) * s, y + 0.42 * s, 1.6 * s, flip=flip, layer=layer)
        cv.add([P(ribbon([(-0.5, 1.25), (-1.6, -0.1)], 0.025))], 'solid', layer)

# =====================================================================
# props: Peranakan house, table and dishes
# =====================================================================

def kamcheng(cv, x, y, s, layer='mid', cls='flower'):
    """Kamcheng: squat lidded Peranakan jar with a knob and shoulder lugs."""
    left = _open([(-0.28 * s, 0.62 * s), (-0.42 * s, 0.52 * s), (-0.48 * s, 0.32 * s), (-0.4 * s, 0.08 * s), (-0.24 * s, 0.0)], 5)
    lid = _open([(-0.3 * s, 0.62 * s), (-0.2 * s, 0.76 * s), (0.0, 0.8 * s), (0.2 * s, 0.76 * s), (0.3 * s, 0.62 * s)], 5)
    cv.add([xf(mirror_pts(left), x, y), xf(lid, x, y), ellipse(x, y + 0.86 * s, 0.07 * s, 0.07 * s, n=16)] +
           [ellipse(x + sx * 0.44 * s, y + 0.5 * s, 0.05 * s, 0.04 * s, n=12) for sx in (-1, 1)], cls, layer)

def tingkat(cv, x, y, s, layer='mid', n=3):
    """Tiffin carrier: stacked tiers, side bars and a carrying handle."""
    polys = []
    for k in range(n):
        y0 = y + k * 0.32 * s
        polys.append(_open([(-0.32 * s, y0 + 0.02 * s), (-0.35 * s, y0 + 0.15 * s), (-0.32 * s, y0 + 0.28 * s)], 4) +
                     _open([(0.32 * s, y0 + 0.28 * s), (0.35 * s, y0 + 0.15 * s), (0.32 * s, y0 + 0.02 * s)], 4))
    polys = [xf(p, x, 0) for p in polys]
    top = y + n * 0.32 * s
    polys.append(ellipse(x, top + 0.04 * s, 0.3 * s, 0.07 * s))
    polys += [ribbon([(x + sx * 0.4 * s, y + 0.1 * s), (x + sx * 0.4 * s, top + 0.3 * s)], 0.025 * s) for sx in (-1, 1)]
    polys.append(ribbon(arc_pts(x, top + 0.3 * s, 0.4 * s, 0, 180, 16), 0.03 * s))
    cv.add(polys, 'flower', layer)
    cv.carve([ribbon([(x - 0.28 * s, y + (k + 0.5) * 0.32 * s), (x + 0.28 * s, y + (k + 0.5) * 0.32 * s)], 0.008 * s)
              for k in range(n)], layer)

def marble_table(cv, cx, y, w, h, layer='mid'):
    """Peranakan marble-top table: thick slab, turned pedestal, splayed feet."""
    left = _open([(-0.08 * w, h - 0.12), (-0.12 * w, h * 0.78), (-0.07 * w, h * 0.55), (-0.1 * w, h * 0.3), (-0.06 * w, h * 0.18)], 4)
    cv.add([xf(mirror_pts(left), cx, y), rect(cx - w / 2, y + h - 0.14, cx + w / 2, y + h)] +
           [ribbon(_open([(cx, y + h * 0.2), (cx + sx * 0.18 * w, y + h * 0.08), (cx + sx * 0.3 * w, y + 0.02)]), 0.05, 0.03)
            for sx in (-1, 1)], 'edge', layer)
    cv.carve([ribbon([(cx - w / 2 + 0.12, y + h - 0.07), (cx + w / 2 - 0.12, y + h - 0.07)], 0.014)], layer)

def prawn(cv, x, y, s, flip=False, layer='mid'):
    """Udang lying on its side: a tapering arched body with carved segment
    joints, a spiked head with long whiskers swept back, a fan tail, legs."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    R = 0.4
    at = lambda a, r=R: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
    path = [at(170 - 160 * t) for t in (k / 20 for k in range(21))]
    polys = [ribbon(path, 0.15, 0.045)]
    hx, hy = at(172)
    polys.append(ellipse(hx + 0.02, hy + 0.02, 0.2, 0.13, rot=-25, n=20))                    # carapace
    polys.append([(hx - 0.12, hy + 0.06), (hx - 0.46, hy + 0.0), (hx - 0.12, hy - 0.02)])  # rostrum
    polys += [ribbon(_open([(hx - 0.12, hy + 0.04), (hx - 0.05, hy + 0.4), (0.1, 0.66), (0.78, 0.6)]), 0.01, 0.003),
              ribbon(_open([(hx - 0.12, hy + 0.0), (hx + 0.05, hy + 0.3), (0.3, 0.52), (0.82, 0.42)]), 0.009, 0.003)]
    tx, ty = path[-1]
    polys += [leaf(tx, ty + 0.02, -60 - k * 32, 0.24, 0.07) for k in range(3)]                # fan tail
    for k in range(6):                                  # swimmerets under the body
        a = 160 - 18 * k
        polys.append(ribbon([at(a, R - 0.08), at(a - 6, R - 0.28)], 0.012, 0.004))
    cv.add([P(p) for p in polys], 'edge', layer)
    cuts = [W.circle(hx - 0.05, hy + 0.05, 0.03, 10)[0]]
    for k in range(1, 7):                               # segment joints across the body
        a = 170 - 160 * k / 7
        cuts.append(ribbon([at(a, R + 0.11 * (1 - 0.6 * k / 7)), at(a, R - 0.11 * (1 - 0.6 * k / 7))], 0.008))
    cv.carve([P(c) for c in cuts], layer)

def lantern(cv, x, y, s, layer='mid'):
    """Hanging Chinese lantern: round paper body with ribs, cap, tassel."""
    cv.add([ribbon([(x, y + 1.2 * s), (x, y + 0.42 * s)], 0.012 * s), rect(x - 0.12 * s, y + 0.36 * s, x + 0.12 * s, y + 0.44 * s),
            ellipse(x, y, 0.36 * s, 0.38 * s), rect(x - 0.12 * s, y - 0.44 * s, x + 0.12 * s, y - 0.36 * s)] +
           [ribbon([(x + 0.03 * s * (k - 1), y - 0.44 * s), (x + 0.04 * s * (k - 1), y - 0.75 * s)], 0.01 * s) for k in range(3)],
           'edge', layer)
    cv.carve([ribbon(arc_pts(x, y, 0.36 * s * f, 100, 260, 16, ry=0.36 * s), 0.008 * s) for f in (0.35, 0.7)] +
             [ribbon(arc_pts(x, y, 0.36 * s * f, -80, 80, 16, ry=0.36 * s), 0.008 * s) for f in (0.35, 0.7)], layer)

def pemidang(cv, cx, y, w=3.2, layer='mid'):
    """Beading frame on low trestles at lap height: taut cloth, a slipper vamp
    half beaded in a peony, rows of beads waiting along the border."""
    y0, y1 = y + 1.2, y + 2.55
    cv.add([ribbon([(cx + sx * w * 0.36, y), (cx + sx * w * 0.3, y0 + 0.05)], 0.05) for sx in (-1, 1)] +
           [ribbon([(cx + sx * w * 0.22, y), (cx + sx * w * 0.3, y0 + 0.05)], 0.05) for sx in (-1, 1)], 'solid', layer)
    cv.add_eo([rect(cx - w / 2, y0, cx + w / 2, y1), rect(cx - w / 2 + 0.14, y0 + 0.12, cx + w / 2 - 0.14, y1 - 0.12)],
              'edge', layer)
    cv.add([rect(cx - w / 2 + 0.17, y0 + 0.15, cx + w / 2 - 0.17, y1 - 0.15)], 'dots', layer)
    for sx in (-1, 1):                                  # the frame's turned end rails
        cv.add([ribbon([(cx + sx * (w / 2 + 0.05), y0 - 0.12), (cx + sx * (w / 2 + 0.05), y1 + 0.12)], 0.06)], 'solid', layer)
    vy = (y0 + y1) / 2 - 0.35
    vamp = ribbon(_open([(cx - 0.75, vy), (cx - 0.68, vy + 0.5), (cx - 0.3, vy + 0.82), (cx + 0.3, vy + 0.82),
                         (cx + 0.68, vy + 0.5), (cx + 0.75, vy)]), 0.025)
    flower = [leaf(cx, vy + 0.38, a, 0.3, 0.07) for a in range(0, 360, 60)] + [W.circle(cx, vy + 0.38, 0.06, 12)[0]]
    cv.carve([vamp] + flower, layer)

def slippers(cv, x, y, s, layer='mid', n=2, flip=False):
    """Kasut manik side-on: low heel, beaded vamp rounded over the toe."""
    polys = []
    for i in range(n):
        dx = i * 0.95 * s
        polys.append(xf([(-0.42, 0.0), (0.4, 0.0), (0.46, 0.06), (0.42, 0.2), (0.25, 0.3), (0.0, 0.3), (-0.08, 0.12),
                         (-0.42, 0.1)], x + dx, y, s=s, flip=flip))
    cv.add(polys, 'edge', layer)
    cv.carve([xf(W.circle(0.08 + 0.12 * k, 0.17, 0.03, 8)[0], x + i * 0.95 * s, y, s=s, flip=flip)
              for i in range(n) for k in range(3)], layer)

# =====================================================================
# rig parts: Uncle Tan and the Nyonyas
# =====================================================================

def _hat_skullcap():
    """Baba skullcap: a six-panel dome with a corded knot on top."""
    dome = _open([(-0.056, 0.905), (-0.054, 0.94), (-0.036, 0.968), (0.0, 0.978), (0.036, 0.97), (0.054, 0.945),
                  (0.059, 0.905)], 5) + [(0.0, 0.9)]
    knob = ellipse(0.0, 0.99, 0.014, 0.012, n=12)
    carves = [ribbon([(-0.05, 0.918), (0.054, 0.918)], 0.0028)] + \
        [ribbon([(0.0, 0.972), (0.04 * k, 0.925)], 0.0018) for k in (-1, 0, 1)]
    return [dome, knob], 'edge', carves

def _hat_sanggul():
    """Nyonya sanggul: hair swept back into a high bun held by three pins."""
    hair = _open([(0.054, 0.905), (0.04, 0.935), (0.0, 0.952), (-0.04, 0.94), (-0.062, 0.9), (-0.06, 0.86),
                  (-0.04, 0.83)], 5) + [(-0.02, 0.86), (0.02, 0.89)]
    bun = ellipse(-0.06, 0.935, 0.038, 0.03, rot=20, n=20)
    pins = [ribbon([(-0.06, 0.935), (-0.06 + 0.07 * math.cos(math.radians(a)), 0.935 + 0.07 * math.sin(math.radians(a)))],
                   0.0035, 0.002) for a in (60, 100, 140)]
    pins += [ellipse(-0.06 + 0.072 * math.cos(math.radians(a)), 0.935 + 0.072 * math.sin(math.radians(a)), 0.007, n=8)
             for a in (60, 100, 140)]
    return [hair, bun] + pins, 'edge', [ribbon(arc_pts(-0.06, 0.935, 0.02, 0, 300, 12), 0.002)]

def _baba_extra(spec):
    """Mandarin collar and a run of frog-knot buttons down the side placket."""
    collar = ribbon([(-0.03, 0.802), (0.034, 0.806)], 0.012)
    placket = _open([(0.03, 0.795), (0.06, 0.77), (0.07, 0.72), (0.07, 0.6), (0.075, 0.45)], 4)
    knots = [ellipse(px - 0.008, py, 0.008, 0.005, n=10) for px, py in placket[::3]]
    return [([collar], 'solid', [ribbon(placket, 0.0022)] + knots)]

def _kebaya_extra(spec):
    """Kebaya: lace-edged pointed front tails over the sarong, three kerongsang."""
    tails = [[(0.06, 0.6), (0.085, 0.44), (0.03, 0.5)], [(-0.05, 0.6), (-0.075, 0.44), (-0.02, 0.5)]]
    brooch = [W.circle(0.042, 0.77 - 0.05 * k, 0.009, 10)[0] for k in range(3)]
    return [(tails, 'edge', brooch)]

def _it_slipper(g, ang, fig):
    """A beaded slipper held up on the palm, toe forward, beads cut through."""
    x, y = g[0] - 0.02, g[1] + 0.012
    shoe = [(x - 0.05, y), (x + 0.07, y), (x + 0.08, y + 0.008), (x + 0.074, y + 0.03), (x + 0.045, y + 0.044),
            (x + 0.005, y + 0.044), (x - 0.01, y + 0.018), (x - 0.05, y + 0.014)]
    beads = [W.circle(x + 0.018 + 0.016 * k, y + 0.024 + 0.006 * (k % 2), 0.0045, 8)[0] for k in range(4)]
    return [shoe], 'solid', beads

def _it_tray(g, ang, fig):
    """A brass tray carried flat at the hand with a steaming bowl of laksa."""
    x, y = g[0] + 0.03, g[1] + 0.01
    tray = [(x - 0.11, y), (x + 0.11, y), (x + 0.1, y + 0.012), (x - 0.1, y + 0.012)]
    bowl = [(x - 0.06, y + 0.07), (x + 0.06, y + 0.07)] + \
        [(x + 0.06 * math.cos(math.radians(a)), y + 0.07 + 0.055 * math.sin(math.radians(a))) for a in range(-10, -171, -16)]
    steam_ = [scroll(x - 0.025 + 0.035 * i, y + 0.15 + 0.02 * (i % 2), 0.015, 0.004, 1.1, a0=0, cw=i % 2 == 0,
                     tail=[(x - 0.025 + 0.035 * i, y + 0.08), (x - 0.017 + 0.035 * i, y + 0.11)]) for i in range(2)]
    return [tray, bowl] + steam_, 'solid', [ribbon([(x - 0.045, y + 0.05), (x + 0.045, y + 0.05)], 0.002)]

def _it_needle(g, ang, fig):
    """Needle and a long beaded thread drawn up from the frame."""
    return [ribbon([(g[0], g[1] - 0.01), (g[0] + 0.01, g[1] + 0.05)], 0.0022),
            ribbon(_open([(g[0], g[1]), (g[0] + 0.06, g[1] - 0.06), (g[0] + 0.12, g[1] - 0.16)]), 0.0015)], 'solid', []

W.register(W.HATS, 'melaka_skullcap', _hat_skullcap)
W.register(W.HATS, 'melaka_sanggul', _hat_sanggul)
W.register(W.COSTUMES, 'melaka_baba', {'hem': 0.27, 'flare': 0.03, 'lower': None, 'legs': 'trousers', 'sleeve': 0.034,
                                       'extra': _baba_extra,
                                       'cls': {'top': 'flower', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}})
W.register(W.COSTUMES, 'melaka_kebaya', dict(W.COSTUMES['kurung'], hem=0.46, flare=0.02, extra=_kebaya_extra,
                                             cls={'top': 'lace', 'lower': 'flower', 'legs': 'edge', 'arm': 'edge'}))
W.register(W.ITEMS2, 'melaka_slipper', _it_slipper)
W.register(W.ITEMS2, 'melaka_tray', _it_tray)
W.register(W.ITEMS2, 'melaka_needle', _it_needle)
W.register(W.POSES, 'melaka_present', {'f': (96, 26), 'b': (-26, -14), 'lean': -3, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'melaka_bead', {'f': (70, 64), 'b': (38, 70), 'lean': 10, 'legs': 'sit', 'hf': 'grip', 'hb': 'open'})

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def melaka_land(cv):
    """Old shophouses line a harbour full of ships from distant lands."""
    hills(cv, -0.5, 21, G + 0.5, 0.6, seed=41, n=4)
    for i, x in enumerate((9.0, 13.2, 17.6)):           # far masts on the roads
        cv.add([ribbon([(x, G + 0.7), (x, G + 2.0 + 0.3 * (i % 2))], 0.03), rect(x - 0.45, G + 0.55, x + 0.45, G + 0.8),
                [(x, G + 1.95), (x - 0.55, G + 1.1), (x + 0.05, G + 1.15)]], 'solid', 'back')
    cloud(cv, 9.8, 7.3, 0.75, 'back', seed=42)
    cloud(cv, 16.6, 6.9, 0.65, 'back', flip=True, seed=43)
    birds(cv, 12.5, 6.4, 3, 0.5, seed=44, layer='back', flip=True)
    # mid: the quay with its shophouse row on the left third
    quay(cv, -0.2, 7.6, G, 0.55)
    for cx, w, h1, h2, gb in ((1.2, 2.4, 1.7, 1.55, 'curve'), (3.7, 2.5, 1.75, 1.7, 'step'), (6.2, 2.3, 1.65, 1.5, 'curve')):
        shophouse(cv, cx, G + 0.55, w, h1, h2, gable=gb)
    lantern(cv, 8.0, G + 2.6, 0.6)
    cv.add([ribbon([(8.0, G + 0.55), (8.0, G + 3.85)], 0.04), ribbon([(7.6, G + 3.85), (8.25, G + 3.85)], 0.03)], 'solid')
    # the harbour: a junk, a Portuguese carrack, an Arab dhow, a sampan
    junk(cv, 11.2, G - 0.15, 0.82)
    ship(cv, 15.7, G - 0.05, 0.56, seed=45)
    dhow(cv, 18.9, G - 0.1, 0.62, flip=True)
    sampan(cv, 9.2, G - 0.12, 0.85)
    ground(cv, 'water', seed=46)
    frame_edges(cv, seed=47, left='none', right='none')

def melaka_people(cv):
    """Beaded slippers are stitched, one tiny bead at a time."""
    # back: a Peranakan front room, carved screen, kamcheng on the sideboard
    cv.add_eo([rect(1.2, 2.3, 4.4, 6.8), _arch(1.5, 4.1, 2.6, 6.5)], 'edge', 'back')
    cv.add([ribbon([(1.5 + 0.52 * i, 2.6), (1.5 + 0.52 * i, 6.5)], 0.03) for i in range(1, 5)], 'solid', 'back')
    cv.add([rect(14.6, 3.0, 19.4, 3.15), rect(14.8, G, 15.0, 3.0), rect(19.0, G, 19.2, 3.0)], 'solid', 'back')
    for i, x in enumerate((15.4, 16.6, 17.8, 18.9)):
        kamcheng(cv, x, 3.15, 0.75 + 0.15 * (i % 2), 'back')
    for x in (6.2, 14.0):
        lantern(cv, x, 6.6, 0.75, 'back')
    # mid: the frame between two seated Nyonyas, a girl holding up a finished pair
    pemidang(cv, 10.2, G, 3.4)
    for x, fl in ((7.7, False), (12.7, True)):
        cv.add([[(x - 0.35, G), (x + 0.35, G), (x + 0.3, G + 1.14), (x - 0.3, G + 1.14)]], 'grid')
    W.place_figure(cv, dict(body='female', hat='melaka_sanggul', costume='melaka_kebaya', pose='melaka_bead',
                            item_f='melaka_needle', rod_to=-0.25), 7.5, G, 3.25)
    W.place_figure(cv, dict(body='female', hat='melaka_sanggul', costume='melaka_kebaya', pose='melaka_bead',
                            item_f='melaka_needle', rod_to=-0.25), 12.9, G, 3.25, flip=True)
    W.place_figure(cv, dict(body='female', hat='melaka_sanggul', costume='melaka_kebaya', pose='melaka_present',
                            item_f='melaka_slipper', rod_to=-0.25, scale=0.9), 16.2, G, 3.25, flip=True)
    cv.add([rect(2.4, G + 0.9, 5.2, G + 1.02), ribbon([(2.6, G), (2.6, G + 0.9)], 0.05), ribbon([(5.0, G), (5.0, G + 0.9)], 0.05)],
           'edge')
    slippers(cv, 2.9, G + 1.02, 0.8, n=3)
    ground(cv, 'earth', seed=48)
    frame_edges(cv, seed=49, left='none', right='none')

def melaka_food(cv):
    """A bowl of Nyonya laksa is served at the marble table."""
    # back: kitchen shelf with plates and kamcheng, a hanging lantern
    cv.add([rect(1.0, 5.0, 6.0, 5.15)], 'solid', 'back')
    for i, x in enumerate((1.6, 2.8, 4.0, 5.2)):
        kamcheng(cv, x, 5.15, 0.6 + 0.15 * (i % 2), 'back')
    cv.add_eo([rect(14.8, 2.6, 18.8, 6.6), _arch(15.1, 18.5, 2.9, 6.3)], 'edge', 'back')
    lantern(cv, 13.6, 6.7, 0.7, 'back')
    # hero: the bowl on the marble table at ~40% height
    marble_table(cv, 10.6, G, 4.4, 1.45)
    bx, by, bw = 10.6, G + 1.45, 2.4
    h = bw * BOWL_DEPTH
    mound = _open([(-0.45 * bw, h * 0.85), (-0.38 * bw, h * 1.04), (-0.2 * bw, h * 1.14), (0.0, h * 1.18),
                   (0.22 * bw, h * 1.12), (0.38 * bw, h * 1.02), (0.45 * bw, h * 0.85)], 5)
    cv.add([xf(mound, bx, by)], 'edge')
    for k, (dx, fl) in enumerate(((-0.12, False), (0.16, True))):     # two prawns crowning the bowl
        prawn(cv, bx + dx * bw, by + h * 1.06, 0.95, flip=fl)
    cv.add([ellipse(bx + 0.33 * bw, by + h * 1.12, 0.1 * bw, 0.07 * bw)] +                       # egg half
           [ellipse(bx - 0.33 * bw + 0.09 * bw * k, by + h * 1.08 + 0.02 * k, 0.06 * bw, 0.025 * bw, rot=20 - 15 * k) for k in range(3)] +
           [leaf(bx - 0.02 * bw + 0.04 * bw * k, by + h * 1.15, 60 + 25 * k, 0.16 * bw, 0.025 * bw) for k in range(3)], 'edge')
    cv.carve([ellipse(bx + 0.33 * bw, by + h * 1.12, 0.045 * bw, 0.032 * bw)], 'mid')
    rim = bowl(cv, bx, by, bw, heap=None)
    for i, (dx, hh, cw) in enumerate(((-0.7, 1.8, False), (0.0, 2.1, True), (0.65, 1.8, False))):
        steam(cv, bx + dx, rim + 0.5, hh, cw=cw, seed=50 + i)
    W.place_figure(cv, dict(body='female', hat='melaka_sanggul', costume='melaka_kebaya', pose='serve', item_f='melaka_tray',
                            rod_to=-0.25), 5.4, G, 3.5)
    tingkat(cv, 14.0, G, 1.0)
    kamcheng(cv, 15.7, G, 1.25)
    for sx in (-1, 1):                                  # prawns and limes laid out, mirrored about the bowl
        prawn(cv, bx + sx * 7.0, G + 0.12, 1.7, flip=sx > 0)
    limes(cv, 1.6, G + 0.05, 1.0)
    limes(cv, 18.9, G + 0.05, 1.0)
    ground(cv, 'earth', seed=57)
    frame_edges(cv, seed=58, left='banana', right='none')

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def icon_food_nyonya_laksa(seed=2):
    """Nyonya laksa: orange coconut-curry broth, rice vermicelli, prawns, fish
    cake slices, half an egg, bean sprouts and laksa leaf, in a Peranakan
    bowl painted pink and green."""
    rnd = random.Random(seed)
    w, h = 2.0, 2.0 * BOWL_DEPTH
    outer = [(-x * w, y * h) for x, y in reversed(BOWL_PROFILE)]
    rim = outer[-1]
    inner = [(r - 0.05, z) for r, z in reversed(outer) if z > 0.2 * h]
    prof = [(0.0, 0.0)] + outer + [(rim[0] - 0.025, rim[1] + 0.02)] + inner + [(0.0, inner[-1][1])]
    _lathe('Bowl', prof, _mat('Porcelain', (0.95, 0.93, 0.86), 0.2, coat=0.3), 72)
    pink, green = _mat('Pink', (0.88, 0.36, 0.5), 0.3), _mat('Jade', (0.18, 0.55, 0.38), 0.3)
    _torus('RimLine', (0, 0, rim[1] - 0.06), rim[0] - 0.012, 0.022, green)
    _torus('Band', (0, 0, 0.55 * h), 0.86, 0.03, pink)
    for k in range(10):                                 # little peony dabs round the band
        a = TAU * k / 10
        _blob('Peony%d' % k, (0.9 * math.cos(a), 0.9 * math.sin(a), 0.62 * h), (0.07, 0.07, 0.04), (0, 0, a),
              pink if k % 2 else green, seg=10)
    soup_z = 0.84 * h
    _lathe('Soup', [(0.0, soup_z), (0.9, soup_z)], _mat('Kuah', (0.85, 0.36, 0.06), 0.3, coat=0.3), 64, sharp=0)
    noodle = _mat('Beehoon', (0.96, 0.94, 0.86), 0.5)
    for i in range(12):
        a0 = rnd.uniform(0, TAU)
        pts = [((0.15 + 0.6 * abs(math.sin(t * math.pi + i))) * math.cos(a0 + t * 1.8),
                (0.15 + 0.6 * abs(math.sin(t * math.pi + i))) * math.sin(a0 + t * 1.8), soup_z + 0.03 + 0.04 * math.sin(t * 5 + i))
               for t in (k / 23 for k in range(24))]
        _tube('Noodle%d' % i, pts, 0.025, noodle)
    shell = _mat('Prawn', (0.95, 0.42, 0.22), 0.35)
    for p, (px, py, rot) in enumerate(((-0.3, 0.25, 0.4), (0.25, 0.35, 2.4))):    # two curled prawns
        pts = [(px + 0.28 * math.cos(rot + t * 3.6) * (1 - 0.3 * t), py + 0.28 * math.sin(rot + t * 3.6) * (1 - 0.3 * t),
                soup_z + 0.15 + 0.06 * math.sin(t * math.pi)) for t in (k / 11 for k in range(12))]
        _tube('Prawn%d' % p, pts, 0.07, shell)
        _blob('Tail%d' % p, pts[-1], (0.09, 0.05, 0.02), (0, 0, rot + 3.6), shell, seg=8)
    cake = _mat('FishCake', (0.93, 0.86, 0.72), 0.5)
    for k in range(4):
        _lathe('Cake%d' % k, [(0.0, 0.0), (0.16, 0.0), (0.16, 0.04), (0.0, 0.04)], cake, 24).location = \
            (-0.45 + 0.12 * k, -0.25 - 0.07 * k, soup_z + 0.06 + 0.02 * k)
    sprout = _mat('Sprout', (0.97, 0.95, 0.8), 0.4)
    for k in range(10):
        a = rnd.uniform(-0.6, 0.6)
        _tube('Sprout%d' % k, [(0.15 + 0.05 * k * math.cos(a), -0.45 + 0.03 * k, soup_z + 0.1),
                               (0.35 + 0.05 * k * math.cos(a), -0.4 + 0.035 * k, soup_z + 0.16)], 0.015, sprout)
    white, yolk = _mat('EggWhite', (0.97, 0.96, 0.92), 0.35), _mat('Yolk', (0.98, 0.62, 0.08), 0.35)
    _blob('Egg', (0.5, -0.05, soup_z + 0.12), (0.24, 0.17, 0.13), (0, 0, 0.5), white)
    _blob('YolkB', (0.5, -0.05, soup_z + 0.24), (0.12, 0.09, 0.03), (0, 0, 0.5), yolk)
    leafm = _mat('Laksa leaf', (0.1, 0.4, 0.12), 0.45)
    for k in range(7):
        a = TAU * k / 7
        _blob('Leaf%d' % k, (-0.02 + 0.12 * math.cos(a), 0.0 + 0.1 * math.sin(a), soup_z + 0.22), (0.12, 0.035, 0.012),
              (0.3 * math.cos(a), 0.3 * math.sin(a), a), leafm, seg=8)
    _blob('Sambal', (-0.05, -0.55, soup_z + 0.1), (0.14, 0.12, 0.06), (0, 0, 0), _mat('Sambal', (0.6, 0.06, 0.03), 0.4), seg=12)
    return (0, -4.7, 4.1), (0, 0, 0.55)

def icon_item_slipper():
    """Kasut manik: a Peranakan beaded mule, a low-heeled sole under an open
    vamp covered in tiny glass beads: a pink peony with green leaves on cream,
    edged in gold."""
    import bmesh
    from wayang_scenes import _obj
    rnd = random.Random(5)
    leather = _mat('Sole', (0.3, 0.17, 0.09), 0.6)
    me = bpy.data.meshes.new('Sole')
    bm = bmesh.new()
    ring = []
    for k in range(48):                                 # footprint: round toe, narrow waist, round heel
        a = TAU * k / 48
        x = 1.1 * math.cos(a)
        y = (0.42 if x > 0 else 0.34) * math.sin(a) * (1 - 0.18 * math.exp(-((x + 0.15) / 0.35) ** 2))
        ring.append((x, y))
    lo = [bm.verts.new((x, y, 0.0)) for x, y in ring]
    hi = [bm.verts.new((x, y, 0.07)) for x, y in ring]
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    for i in range(48):
        bm.faces.new((lo[i], lo[(i + 1) % 48], hi[(i + 1) % 48], hi[i]))
    bm.to_mesh(me)
    bm.free()
    _obj('Sole', me, leather)
    _box('Heel', (-0.8, 0.0, -0.06), (0.42, 0.5, 0.12), (0, 0, 0), leather)
    # vamp: the front of an ellipsoid shell, open at the back
    c, ax = (0.42, 0.0, 0.07), (0.68, 0.42, 0.34)
    lining = _mat('Lining', (0.12, 0.1, 0.25), 0.7)
    me = bpy.data.meshes.new('Vamp')
    bm = bmesh.new()
    rows = []
    for j in range(13):
        v = math.pi / 2 * j / 12                        # 0 = sole edge, pi/2 = top
        row = []
        for i in range(33):
            u = -2.3 + 4.6 * i / 32                     # around the front, back open
            row.append(bm.verts.new((c[0] + ax[0] * math.cos(v) * math.cos(u), c[1] + ax[1] * math.cos(v) * math.sin(u),
                                     c[2] + ax[2] * math.sin(v))))
        rows.append(row)
    for j in range(12):
        for i in range(32):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    _obj('Vamp', me, lining)
    cols = {k: _mat('Bead_' + k, v, 0.22, coat=0.7) for k, v in
            (('pink', (0.95, 0.42, 0.58)), ('red', (0.8, 0.08, 0.18)), ('green', (0.15, 0.6, 0.32)),
             ('cream', (0.96, 0.92, 0.8)), ('gold', (0.95, 0.72, 0.2)))}
    n = 0
    for j in range(1, 16):                              # beads in rings over the shell
        v = math.pi / 2 * (j - 0.5) / 15
        circ = TAU * ax[0] * math.cos(v)
        m = max(6, int(circ * 0.73 / 0.055))
        for i in range(m):
            u = -2.25 + 4.5 * (i + 0.5 * (j % 2)) / m
            p = (c[0] + 1.03 * ax[0] * math.cos(v) * math.cos(u), c[1] + 1.03 * ax[1] * math.cos(v) * math.sin(u),
                 c[2] + 1.03 * ax[2] * math.sin(v))
            fx, fy = math.cos(v) * math.cos(u), math.cos(v) * math.sin(u)
            d = math.hypot(fx - 0.35, fy * 1.1)         # the peony sits on the instep
            if abs(abs(u) - 2.25) < 0.12 or j == 1:
                col = 'gold'
            elif d < 0.13:
                col = 'red'
            elif d < 0.33:
                col = 'pink' if (i + j) % 5 else 'red'
            elif d < 0.5 and rnd.random() < 0.6:
                col = 'green'
            else:
                col = 'cream'
            _blob('Bead%d' % n, p, (0.03, 0.03, 0.03), (0, 0, 0), cols[col], seg=6)
            n += 1
    return (2.7, -3.7, 2.6), (0.15, 0.0, 0.15)

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

PUPPET = dict(head='refined', hat='melaka_skullcap', costume='melaka_baba', pose='melaka_present',
              item_f='melaka_slipper', feet=0.03)                                      # Uncle Tan
BEATS = {'land': melaka_land, 'people': melaka_people, 'food': melaka_food}
ICONS = {'food': icon_food_nyonya_laksa, 'item': icon_item_slipper}
