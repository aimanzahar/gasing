"""Journey and story extras: rides (one per departing state, 1536x640, fn.size = RIDE),
the travel strips (road / rail / water), the prologue, the endings and the sailor puppet.

  JOURNEY  {name: fn(cv) | puppet spec}  -> assets/wayang/wayang_<name>.png

Lane contract with main.gd (_show_beat, ride layer): the ride image's bottom edge sits on
stage.y * 0.88, which is the strips' ground line G. Wheels and keels are drawn at RIDE_Y
(0.3 of 6.4 ride units), so they meet the strip at G + 0.19 = 1.17 strip units: the rail top
on strip_rail, the near wheel ruts on strip_road, the water surface on strip_water.
"""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, RIDE_Y, ...
from wayang_scenes import _open                                # private kit helper

LANE = G + 0.19            # where ride wheels / keels meet a strip (see the module doc)
FEET = 0.03                # puppet sheet feet line: row 899 of 1024 = main.gd's ground (stage.y * 0.88)

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
# ponytail: patched here, not in the frozen lib; drop it once PUPPET_SHEET['feet'] is 0.03 there
if not getattr(W.render_puppet_v2, 'feet_aware', False):
    W.render_puppet_v2 = _feet_aware(W.render_puppet_v2)

# =====================================================================
# rig parts used by the journey (registered, never edited in the kit)
# =====================================================================

def _cap():
    """Flat cloth cap with a short peak (train driver, trishaw rider)."""
    p = [(-0.056, 0.893), (-0.054, 0.932), (-0.024, 0.962), (0.026, 0.968), (0.058, 0.952), (0.07, 0.928),
         (0.118, 0.912), (0.114, 0.902), (0.062, 0.904), (0.0, 0.896)]
    return [p], 'edge', [ribbon([(-0.05, 0.915), (0.064, 0.92)], 0.0025)]

W.register(W.HATS, 'journey_cap', _cap)
# cycling: feet on level pedals (the rig draws feet at y = 0), seated hip behind the crank
W.register(W.LEGS, 'journey_pedal', ((0.2, 0.30), (0.185, 0.058), (0.1, 0.25), (-0.015, 0.06), 0.44))
W.register(W.POSES, 'journey_cycle', {'f': (70, 20), 'b': (60, 30), 'lean': 18, 'legs': 'journey_pedal',
                                      'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'journey_throw', {'f': (52, 4), 'b': (-38, -28), 'lean': 16, 'legs': 'walk',
                                      'hf': 'open', 'hb': 'open'})
W.register(W.POSES, 'journey_paddle', {'f': (48, 30), 'b': (88, 40), 'lean': 16, 'legs': 'sit',
                                       'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'journey_show', {'f': (118, 18), 'b': (34, 40), 'lean': 6, 'legs': 'walk',
                                     'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'journey_tiller', {'f': (24, 40), 'b': (-62, 10), 'lean': 2, 'legs': 'sit',
                                       'hf': 'open', 'hb': 'grip'})
W.register(W.POSES, 'journey_haul', {'f': (100, 6), 'b': (86, 22), 'lean': -16, 'legs': 'walk',
                                     'hf': 'grip', 'hb': 'grip'})
W.register(W.POSES, 'journey_shoulder', {'f': (150, 40), 'b': (-14, -14), 'lean': 4, 'legs': 'walk',
                                         'hf': 'grip', 'hb': 'open'})
W.register(W.POSES, 'journey_hammer', {'f': (120, 60), 'b': (40, 50), 'lean': 10, 'legs': 'stand',
                                       'hf': 'grip', 'hb': 'grip'})

def _it_paddle(g, ang, fig):
    """Dayung: a shaft through the fist, angled down and back, leaf blade in the water."""
    a = math.radians(-118)
    d = (math.cos(a), math.sin(a))
    top = (g[0] - 0.14 * d[0], g[1] - 0.14 * d[1])
    end = (g[0] + 0.42 * d[0], g[1] + 0.42 * d[1])
    blade = leaf(end[0] - 0.02 * d[0], end[1] - 0.02 * d[1], math.degrees(a), 0.16, 0.034)
    return [ribbon([top, end], 0.0065), blade, ellipse(top[0], top[1], 0.012, 0.018)], 'solid', []

def _it_mallet(g, ang, fig):
    """Tukul kayu raised to strike."""
    a = math.radians(ang + 180)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])
    head = (g[0] + 0.12 * d[0], g[1] + 0.12 * d[1])
    blk = [(head[0] + n[0] * 0.05 + d[0] * 0.03, head[1] + n[1] * 0.05 + d[1] * 0.03),
           (head[0] - n[0] * 0.05 + d[0] * 0.03, head[1] - n[1] * 0.05 + d[1] * 0.03),
           (head[0] - n[0] * 0.05 - d[0] * 0.03, head[1] - n[1] * 0.05 - d[1] * 0.03),
           (head[0] + n[0] * 0.05 - d[0] * 0.03, head[1] + n[1] * 0.05 - d[1] * 0.03)]
    return [ribbon([(g[0] - 0.03 * d[0], g[1] - 0.03 * d[1]), head], 0.007), blk], 'solid', []

def _it_gasing(g, ang, fig):
    """A gasing held up on the palm, cord wound round its waist and the tail hanging free
    (the kit's 'gasing' is too small to read at beat scale)."""
    s = 0.2
    body = xf(gasing_top(0.0, 0.0, 1.0), g[0] + 0.012, g[1] - 0.004, s=s)
    tail = ribbon(_open([(g[0] - 0.02, g[1] + 0.05), (g[0] - 0.05, g[1] - 0.02), (g[0] - 0.03, g[1] - 0.09),
                         (g[0] - 0.06, g[1] - 0.15)]), 0.0035, 0.002)
    wind = [xf(ribbon([(-0.4, 0.3 + 0.08 * k), (0.4, 0.34 + 0.08 * k)], 0.02), g[0] + 0.012, g[1] - 0.004, s=s) for k in range(3)]
    return [body, tail], 'solid', wind

W.register(W.ITEMS2, 'journey_paddle', _it_paddle)
W.register(W.ITEMS2, 'journey_gasing', _it_gasing)
W.register(W.ITEMS2, 'journey_mallet', _it_mallet)

SAILOR = dict(head='foreign', beard='full', hat='sailor', costume='sailor')

def sailor(**kw):
    return dict(SAILOR, **kw)

def _sc(spec, s):
    return spec.get('scale', 1.0) * s * (0.93 if spec.get('body') == 'female' else 1.0)

def seated(cv, spec, x, seat, s, flip=False, layer='mid'):
    """A figure sitting with its hip on the seat line (rig 'sit' legs unless the spec says)."""
    sp = dict(spec)
    sp.setdefault('rods', False)
    pose = W.POSES[sp.get('pose', 'stand')]
    sp.setdefault('legs', 'sit' if pose['legs'] != 'journey_pedal' else pose['legs'])
    hip = W.LEGS[sp['legs']][4]
    W.place_figure(cv, sp, x, seat - hip * _sc(sp, s), s, flip, layer)
    return sp

def standing(cv, spec, x, y, s, flip=False, layer='mid', rods=False):
    sp = dict(spec)
    sp.setdefault('rods', rods)
    W.place_figure(cv, sp, x, y, s, flip, layer)
    return sp

def grip_of(spec, x, y, s, flip=False, which='f'):
    """Canvas position of a placed figure's hand grip (mirrors wayang_lib.figure's arm maths)."""
    pose = W.POSES[spec.get('pose', 'stand')]
    hip = W.LEGS[spec.get('legs', pose['legs'])][4]
    lean = pose['lean'] + spec.get('lean', 0)
    fem = spec.get('body') == 'female'
    if which == 'f':
        sh = (0.058, 0.758) if fem else (0.068, 0.762)
    else:
        sh = (-0.06, 0.76) if fem else (-0.072, 0.765)
    a1, a2 = pose[which]
    r1, r2 = math.radians(a1 - lean), math.radians(a1 - lean + a2)
    el = (sh[0] + 0.19 * math.sin(r1), sh[1] - 0.19 * math.cos(r1))
    wr = (el[0] + 0.175 * math.sin(r2), el[1] - 0.175 * math.cos(r2))
    g = (wr[0] + 0.026 * math.sin(r2), wr[1] - 0.026 * math.cos(r2))
    g = xf([g], 0.0, hip - 0.5, rot=-lean, ox=0.0, oy=0.5)[0]
    return xf([g], x, y, s=_sc(spec, s), flip=flip)[0]

def seated_grip(spec, x, seat, s, flip=False, which='f'):
    sp = dict(spec)
    pose = W.POSES[sp.get('pose', 'stand')]
    sp.setdefault('legs', 'sit' if pose['legs'] != 'journey_pedal' else pose['legs'])
    return grip_of(sp, x, seat - W.LEGS[sp['legs']][4] * _sc(sp, s), s, flip, which)

# =====================================================================
# journey prop kit
# =====================================================================

def hull(cv, x0, x1, yk, h, rise=0.6, cls='slits', layer='mid', steep=4, strakes=2):
    """Perahu hull, broadside: flat sheer rising to stem and stern posts. Returns gunwale y(x)."""
    L = x1 - x0
    gun = lambda x: yk + h + rise * abs(2 * (x - x0) / L - 1) ** steep
    top = [(x0 + L * i / 48, gun(x0 + L * i / 48)) for i in range(49)]
    bot = _open([(x1, gun(x1)), (x1 - 0.05 * L, yk + 0.5 * h), (x1 - 0.2 * L, yk + 0.05 * h), (x0 + L / 2, yk),
                 (x0 + 0.2 * L, yk + 0.05 * h), (x0 + 0.05 * L, yk + 0.5 * h), (x0, gun(x0))], 6)
    pid = cv.add([top + bot[1:-1]], cls, layer)
    cuts = []
    for k in range(1, strakes + 1):
        pts = [(x0 + L * (0.14 + 0.72 * i / 30), 0.0) for i in range(31)]
        pts = [(x, gun(x) - 0.26 * k * h - 0.04) for x, _ in pts]
        cuts.append(ribbon(pts, 0.011))
    cv.carve(cuts, layer)
    return gun

def wake(cv, x0, x1, y, h=0.34, seed=1, layer='mid', curl=1.0):
    """Water at a hull's waterline: a tapered band whose top curls back (ombak) as it moves right."""
    rnd = random.Random(seed)
    L = x1 - x0
    top = [(x0 + L * i / 40, y + 0.03 * math.sin(i * 1.7 + seed)) for i in range(41)]
    bot = _open([(x1 + 0.2, y - 0.02), (x1 - 0.2 * L, y - h * 0.75), (x0 + 0.5 * L, y - h * 0.85),
                 (x0 + 0.15 * L, y - h * 0.7), (x0 - 0.3, y - 0.02)], 6)
    pid = cv.add([top + bot], 'scales', layer)
    curls = []
    n = max(3, int(L / 0.8))
    for i in range(n):
        t = (i + 0.5) / n
        x = x0 + L * t
        r = h * curl * (0.32 + 0.3 * math.sin(math.pi * t)) * rnd.uniform(0.85, 1.12)
        curls.append(scroll(x - r * 0.4, y + r * 0.95, r, r * 0.32, 1.2, a0=0, cw=False,
                            tail=[(x + r * 1.7, y - 0.02), (x + r * 0.8, y + r * 0.35)]))
    cv.add(curls, 'edge', layer, pid=pid)
    return pid

def puffs(cv, pts, mid=2, seed=1):
    """Smoke or steam: rounded puffs, the first `mid` sharp, the rest drifting into the back layer."""
    for i, (x, y, r) in enumerate(pts):
        polys = canopy(x, y, r, seed + i, 6) + [ellipse(x, y - r * 0.15, r * 0.9, r * 0.5)]
        cv.add(polys, 'edge', 'mid' if i < mid else 'back')

def plume(cv, x, y, n=8, dx=-0.9, dy=0.22, r0=0.26, r1=0.62, mid=3, seed=1):
    """A rolling smoke plume from (x, y): puffs growing and drifting back (left) and up."""
    pts = []
    for i in range(n):
        t = i / max(n - 1, 1)
        pts.append((x + dx * i * (0.75 + 0.5 * t), y + dy * i * (1.2 - 0.6 * t) + 0.08 * math.sin(i * 2.1),
                    r0 + (r1 - r0) * t))
    puffs(cv, pts, mid, seed)

def sack(cv, x, y, w, h, layer='mid', cls='edge', tie=True):
    body = _open([(x - w * 0.5, y + 0.02), (x - w * 0.55, y + h * 0.5), (x - w * 0.4, y + h * 0.92), (x, y + h),
                  (x + w * 0.4, y + h * 0.92), (x + w * 0.55, y + h * 0.5), (x + w * 0.5, y + 0.02)], 4)
    polys = [body]
    if tie:
        polys.append([(x - w * 0.12, y + h * 0.95), (x - w * 0.22, y + h * 1.25), (x, y + h * 1.12),
                      (x + w * 0.22, y + h * 1.25), (x + w * 0.12, y + h * 0.95)])
    cv.add(polys, cls, layer)
    cv.carve([ribbon(_open([(x - w * 0.38, y + h * 0.42), (x, y + h * 0.36), (x + w * 0.38, y + h * 0.42)]), 0.012)], layer)

def basket(cv, x0, x1, y0, y1, layer='mid', handle=False):
    """Woven rattan basket (bakul): flared sides, lattice weave, rolled rim."""
    w = x1 - x0
    body = [(x0 + 0.1 * w, y0), (x1 - 0.1 * w, y0), (x1, y1), (x0, y1)]
    polys = [body, rect(x0 - 0.03, y1 - 0.02, x1 + 0.03, y1 + 0.07)]
    if handle:
        polys.append(ribbon(arc_pts((x0 + x1) / 2, y1, w * 0.42, 0, 180, 16), 0.025))
    cv.add(polys, 'grid', layer)

def jar(cv, x, y, s, layer='mid'):
    left = _open([(-0.18 * s, 0.82 * s), (-0.16 * s, 0.74 * s), (-0.32 * s, 0.6 * s), (-0.36 * s, 0.38 * s),
                  (-0.28 * s, 0.1 * s), (-0.17 * s, 0.0)], 5)
    cv.add([xf(mirror_pts(left), x, y)] + [ellipse(x + sx * 0.3 * s, y + 0.62 * s, 0.05 * s, 0.04 * s) for sx in (-1, 1)],
           'dots', layer)
    cv.carve([xf(ribbon(_open([(-0.3 * s, 0.5 * s), (0.0, 0.47 * s), (0.3 * s, 0.5 * s)]), 0.01 * s), x, y)], layer)

def gasing_top(x, y, s, tilt=0.0):
    """Gasing jantung outline, tip at (x, y)."""
    R = [(0.0, 0.0), (0.05, 0.04), (0.2, 0.16), (0.38, 0.31), (0.48, 0.43), (0.47, 0.52), (0.36, 0.6),
         (0.15, 0.64), (0.08, 0.68), (0.075, 0.75), (0.0, 0.77)]
    pts = R + [(-px, py) for px, py in reversed(R)][1:-1]
    return xf(pts, x, y, s=s, rot=tilt)

def spinning_top(cv, x, y, s, layer='mid', seed=1):
    """A gasing spinning on its tip with whirl lines round its waist and a dust curl."""
    cv.add([gasing_top(x, y, s)], 'edge', layer)
    cv.carve([ribbon([(x - 0.4 * s, y + 0.44 * s), (x + 0.4 * s, y + 0.44 * s)], 0.018 * s),
              ellipse(x, y + 0.71 * s, 0.03 * s)], layer)
    arcs = [ribbon(arc_pts(x, y + 0.42 * s, 0.78 * s, 200, 335, 18, ry=0.2 * s), 0.02 * s, 0.006 * s),
            ribbon(arc_pts(x, y + 0.5 * s, 0.68 * s, 25, 150, 16, ry=0.16 * s), 0.016 * s, 0.005 * s),
            scroll(x - 0.5 * s, y + 0.08 * s, 0.1 * s, 0.03 * s, 1.1, a0=0, cw=False,
                   tail=[(x - 0.05 * s, y + 0.01 * s), (x - 0.3 * s, y + 0.03 * s)]),
            scroll(x + 0.5 * s, y + 0.08 * s, 0.1 * s, 0.03 * s, 1.1, a0=180, cw=True,
                   tail=[(x + 0.05 * s, y + 0.01 * s), (x + 0.3 * s, y + 0.03 * s)])]
    cv.add(arcs, 'solid', layer)

def cord(cv, a, b, sag=0.25, w=0.016, layer='mid', waves=1.5):
    """A thrown gasing cord (tali) from a to b, a loose wave along its length."""
    pts = []
    for i in range(25):
        t = i / 24
        px = a[0] + (b[0] - a[0]) * t
        py = a[1] + (b[1] - a[1]) * t - sag * math.sin(math.pi * t) + 0.08 * math.sin(t * waves * TAU)
        pts.append((px, py))
    cv.add([ribbon(pts, w, w * 0.6)], 'solid', layer)

def flag(cv, x, y, L, layer='mid', wave=0.12, tails=True):
    """A pennant streaming back (left) from a masthead at (x, y)."""
    pts = [(x - L * i / 20, y - 0.06 * i / 20 + wave * math.sin(i / 20 * TAU * 1.2)) for i in range(21)]
    cv.add([ribbon(pts, 0.11, 0.02)], 'edge', layer)

def lug_sail(cv, tl, tr, br, bl, layer='mid', cls='slits', belly=0.25, battens=3):
    """Malay lug sail (layar): angled yard on top, bellied leech, carved battens."""
    top = [tl, ((tl[0] + tr[0]) / 2, (tl[1] + tr[1]) / 2 + 0.05), tr]
    lee = _open([tr, ((tr[0] + br[0]) / 2 + belly, (tr[1] + br[1]) / 2), br], 6)[1:]
    foot = _open([br, ((br[0] + bl[0]) / 2, (br[1] + bl[1]) / 2 - belly * 0.4), bl], 6)[1:]
    luff = _open([bl, ((bl[0] + tl[0]) / 2 + belly * 0.4, (bl[1] + tl[1]) / 2), tl], 6)[1:-1]
    pid = cv.add([top + lee + foot + luff], cls, layer)
    yard = ribbon([(tl[0] - 0.25 * (tr[0] - tl[0]) / 4, tl[1] - 0.06), (tr[0] + 0.15, tr[1] + 0.03)], 0.05)
    boom = ribbon([(bl[0] - 0.1, bl[1] - 0.02), (br[0] + 0.1, br[1] - 0.02)], 0.04)
    cv.add([yard, boom], 'solid', layer)
    cuts = []
    for k in range(1, battens + 1):
        t = k / (battens + 1)
        a = (tl[0] + (bl[0] - tl[0]) * t + 0.12, tl[1] + (bl[1] - tl[1]) * t)
        b = (tr[0] + (br[0] - tr[0]) * t - 0.12, tr[1] + (br[1] - tr[1]) * t)
        cuts.append(ribbon([a, ((a[0] + b[0]) / 2 + 0.05, (a[1] + b[1]) / 2 + 0.06), b], 0.014))
    cv.carve(cuts, layer)
    return pid

def horse(cv, x, y, s=1.0, layer='mid', plume=True):
    """Kuda walking right: arched neck and mane, blinkered head, collar and saddle pad, tail."""
    P = lambda pts: xf(pts, x, y, s=s)
    legs = []
    for hip, knee, fet, w in (((0.55, 1.42), (0.45, 0.74), (0.3, 0.2), 0.12),          # far fore
                              ((-0.62, 1.4), (-0.86, 0.78), (-0.68, 0.2), 0.13)):      # far hind
        legs += [ribbon([hip, knee], w, w * 0.55), ribbon([knee, fet], w * 0.45, w * 0.38),
                 [(fet[0] - 0.08, 0.0), (fet[0] + 0.12, 0.0), (fet[0] + 0.07, 0.15), (fet[0] - 0.05, 0.17)]]
    cv.add([P(l) for l in legs], 'solid', layer)
    torso = _open([(-1.28, 1.95), (-1.0, 2.12), (-0.5, 2.03), (0.0, 2.04), (0.45, 2.22), (0.72, 2.52), (0.95, 2.86),
                   (1.06, 3.06)], 5) + [(1.05, 3.3), (1.13, 3.12), (1.2, 3.08)] + \
        _open([(1.22, 3.05), (1.45, 2.74), (1.68, 2.42), (1.79, 2.26)], 4) + [(1.76, 2.17), (1.58, 2.15)] + \
        _open([(1.5, 2.24), (1.3, 2.38), (1.08, 2.38), (0.96, 2.08), (0.9, 1.7), (0.75, 1.36), (0.3, 1.2),
               (-0.4, 1.2), (-0.9, 1.3), (-1.25, 1.55), (-1.32, 1.8)], 5)
    near = []
    for hip, knee, fet, w in (((0.72, 1.45), (0.86, 0.76), (0.98, 0.2), 0.13),
                              ((-0.8, 1.45), (-1.1, 0.74), (-1.0, 0.2), 0.14)):
        near += [ribbon([hip, knee], w, w * 0.55), ribbon([knee, fet], w * 0.45, w * 0.38),
                 [(fet[0] - 0.08, 0.0), (fet[0] + 0.12, 0.0), (fet[0] + 0.07, 0.15), (fet[0] - 0.05, 0.17)]]
    tail = ribbon(_open([(-1.25, 1.95), (-1.5, 1.75), (-1.62, 1.3), (-1.55, 0.85)]), 0.07, 0.11)
    ears = [leaf(1.08, 3.1, 100, 0.22, 0.04), leaf(1.0, 3.08, 112, 0.2, 0.035)]
    pid = cv.add([P(torso), P(tail)] + [P(e) for e in ears] + [P(n) for n in near], 'lace', layer)
    mane = [leaf(0.98 - 0.11 * i, 3.02 - 0.17 * i, 160 - 4 * i, 0.32, 0.05, bend=-0.06) for i in range(6)]
    gear = [ribbon(_open([(0.6, 2.05), (0.86, 2.62), (1.0, 2.35), (0.98, 1.95), (0.78, 1.7)]), 0.05),     # collar
            _open([(-0.45, 2.08), (-0.1, 2.18), (0.25, 2.12)], 4) + [(0.22, 1.72), (-0.42, 1.72)],     # saddle pad
            ribbon([(1.42, 2.75), (1.6, 2.6)], 0.045)]                                                 # blinker
    if plume:
        gear += [leaf(1.08, 3.25, 95 + 18 * k, 0.35, 0.05, bend=-0.05) for k in range(3)]
    cv.add([P(m) for m in mane] + [P(g) for g in gear], 'edge', layer)
    cv.carve([P(leaf(1.5, 2.72, -30, 0.09, 0.022)), P(ribbon([(-0.1, 1.95), (0.15, 1.95)], 0.012))], layer)
    return pid, P([(1.72, 2.3)])[0]          # the bit, for the reins

# =====================================================================
# rides (1536x640 = 15.36 x 6.4 units, facing right, wheels / keel at RIDE_Y)
# =====================================================================

def kereta_lembu(cv):
    """Bullock cart: a saddle-roofed cart on one great spoked wheel, the driver
    on the shaft with his cane, the sailor riding under the roof."""
    y = RIDE_Y
    bullock(cv, 11.3, y, 1.15)
    cv.add([ribbon([(7.4, y + 2.2), (11.85, y + 2.95)], 0.07), ribbon([(11.7, y + 2.6), (12.2, y + 3.45)], 0.08)], 'solid')
    W.place_figure(cv, dict(head='foreign', beard='full', hat='sailor', costume='sailor', pose='stand', legs='sit',
                            rods=False), 3.9, y + 2.8 - 0.38 * 2.9, 2.9)
    cv.add([rect(1.5, y + 1.85, 7.6, y + 3.0)], 'slits')
    cv.add([ribbon([(1.6, y + 2.75), (1.6, y + 4.55)], 0.05), ribbon([(7.5, y + 2.75), (7.5, y + 4.55)], 0.05),
            ribbon([(1.4, y + 3.05), (7.7, y + 3.05)], 0.045)], 'solid')
    roof = _open([(0.75, y + 5.25), (1.2, y + 4.75), (1.7, y + 4.5), (3.0, y + 5.1), (4.55, y + 5.55), (6.1, y + 5.1),
                  (7.4, y + 4.5), (7.9, y + 4.75), (8.35, y + 5.25)], 6) + \
        [(8.3, y + 5.1), (7.7, y + 4.4), (4.55, y + 4.6), (1.4, y + 4.4), (0.8, y + 5.1)]
    cv.add([roof], 'scales')
    W.place_figure(cv, dict(head='old', hat='songkok', costume='farmer', pose='stand', legs='sit', item_f='switch',
                            rods=False, cls={'top': 'edge'}), 7.55, y + 2.9 - 0.38 * 2.9, 2.9)
    wheel(cv, 4.4, y + 1.3, 1.3, 12, knobs=False, rim=0.14)

def ride_perlis(cv):
    kereta_lembu(cv)

def ride_kedah(cv):
    """Old steam train to Penang: a tank engine with a balloon stack and cowcatcher pulling
    one open-windowed carriage; the sailor waves from a window, smoke rolls back overhead."""
    y = RIDE_Y
    plume(cv, 13.6, y + 4.15, n=10, dx=-0.62, dy=0.2, r0=0.3, r1=0.62, mid=4, seed=9)
    # carriage: passengers first, the wall with its window bays in front of them
    seated(cv, dict(body='female', hat='tudung', costume='kurung', pose='stand'), 1.35, y + 1.55, 2.35)
    seated(cv, dict(head='young', hat='songkok', costume='baju', pose='stand'), 2.95, y + 1.55, 2.35)
    seated(cv, sailor(pose='wonder'), 4.45, y + 1.55, 2.35)
    x0, x1 = 0.35, 6.75
    cv.add([rect(x0, y + 0.95, x1, y + 2.15)], 'slits')
    cv.add([rect(px - 0.07, y + 2.1, px + 0.07, y + 3.3) for px in (0.45, 2.2, 3.7, 5.55, 6.65)] +
           [rect(x0, y + 2.1, x1, y + 2.22)], 'solid')
    roof = _open([(x0 - 0.2, y + 3.25), (x0 + 0.3, y + 3.55), (3.55, y + 3.66), (x1 - 0.3, y + 3.55), (x1 + 0.2, y + 3.25)], 6) + \
        [(x1 + 0.2, y + 3.16), (x0 - 0.2, y + 3.16)]
    cv.add([roof, rect(1.0, y + 3.5, 6.1, y + 3.8)], 'edge')
    cv.carve([rect(1.3 + 0.75 * i, y + 3.58, 1.65 + 0.75 * i, y + 3.72) for i in range(7)] +
             [ribbon([(x0 + 0.15, y + 1.3), (x1 - 0.15, y + 1.3)], 0.014)], 'mid')
    cv.add([rect(x0 + 0.15, y + 0.68, x1 - 0.15, y + 0.97), rect(0.7, y + 0.45, 2.15, y + 0.72),
            rect(4.95, y + 0.45, 6.4, y + 0.72), ribbon([(x1, y + 0.85), (7.8, y + 0.85)], 0.05)], 'solid')
    for wx in (1.05, 1.82, 5.3, 6.07):
        wheel(cv, wx, y + 0.3, 0.3, 8, knobs=False, rim=0.2, cls='solid')
    # locomotive
    seated(cv, dict(head='old', hat='journey_cap', costume='baju', pose='crank'), 8.8, y + 2.25, 2.0)
    cv.add([rect(7.75, y + 1.5, 9.8, y + 2.45), rect(7.75, y + 2.4, 7.95, y + 3.7)], 'dots')
    cv.add_eo([rect(9.5, y + 1.5, 9.85, y + 3.7), ellipse(9.67, y + 3.05, 0.11, 0.17)], 'edge')
    cv.add([_open([(7.45, y + 3.68), (8.7, y + 3.95), (10.1, y + 3.68)], 6) + [(10.1, y + 3.58), (7.45, y + 3.58)]], 'edge')
    cv.add([rect(7.2, y + 1.5, 7.75, y + 2.35)] + [ellipse(7.3 + 0.13 * i, y + 2.38 + 0.05 * (i % 2), 0.09, 0.07) for i in range(4)],
           'edge')
    cv.add([rect(7.15, y + 1.35, 14.0, y + 1.52)], 'solid')
    boiler = rect(9.8, y + 1.52, 13.45, y + 2.78)
    cv.add([boiler, rect(13.35, y + 1.52, 13.95, y + 2.88)], 'dots')
    cv.carve([ribbon([(bx, y + 1.6), (bx, y + 2.7)], 0.016) for bx in (10.7, 11.95, 12.9)] +
             [ribbon([(9.95, y + 2.38), (13.3, y + 2.38)], 0.012), rect(8.4, y + 1.75, 9.15, y + 2.1)], 'mid')
    dome = [(11.62 - 0.38, y + 2.76)] + arc_pts(11.62, y + 2.76, 0.38, 180, 0, 16, ry=0.48)[1:-1] + [(11.62 + 0.38, y + 2.76)]
    sand = [(10.55 - 0.28, y + 2.76)] + arc_pts(10.55, y + 2.76, 0.28, 180, 0, 14, ry=0.33)[1:-1] + [(10.55 + 0.28, y + 2.76)]
    stack = [(13.42, y + 2.85), (13.86, y + 2.85), (13.78, y + 3.3), (14.0, y + 3.72), (13.28, y + 3.72), (13.5, y + 3.3)]
    cv.add([dome, sand, stack, rect(13.2, y + 3.7, 14.08, y + 3.84), ribbon([(10.0, y + 2.76), (10.0, y + 3.15)], 0.035),
            [(9.92, y + 3.12), (10.08, y + 3.12), (10.05, y + 3.3), (9.95, y + 3.3)]], 'edge')
    cv.add([rect(12.45, y + 0.72, 13.5, y + 1.32), rect(13.9, y + 1.22, 14.3, y + 1.56), rect(14.25, y + 1.3, 14.45, y + 1.48),
            rect(13.98, y + 2.62, 14.38, y + 2.98), [(13.95, y + 2.98), (14.42, y + 2.98), (14.3, y + 3.12), (14.05, y + 3.12)]],
           'edge')
    cv.add([[(13.95, y + 1.25), (15.0, y + 0.06), (13.95, y + 0.06)]], 'grid')
    wheel(cv, 13.15, y + 0.36, 0.36, 8, knobs=False, rim=0.2, cls='solid')
    wheel(cv, 8.55, y + 0.36, 0.36, 8, knobs=False, rim=0.2, cls='solid')
    for wx in (10.2, 11.65):
        wheel(cv, wx, y + 0.63, 0.63, 14, knobs=False, rim=0.15)
    pins = [(10.2 + 0.3, y + 0.63 - 0.17), (11.65 + 0.3, y + 0.63 - 0.17)]
    cv.add([ribbon(pins, 0.055), ribbon([(12.45, y + 0.98), pins[1]], 0.045), ribbon([(12.45, y + 0.98), (13.2, y + 0.98)], 0.03)]
           + [ellipse(px, py, 0.07) for px, py in pins], 'solid')

def ride_penang(cv):
    """Trishaw (beca), Penang style: the sailor rides in the hooded seat up front, the rider
    pedals behind and steers the whole carriage by the bar on its back."""
    y = RIDE_Y
    S = 3.0
    rw = 0.56
    wheel(cv, 5.3, y + rw, rw, 16, knobs=False, rim=0.12)
    rider = dict(head='old', hat='journey_cap', costume='farmer', pose='journey_cycle', rods=False,
                 cls={'top': 'edge', 'lower': 'edge'})
    hx, fy = 6.0, y + 0.5
    g = grip_of(rider, hx, fy, S)
    bb = (hx + 0.085 * S, fy + 0.08)
    seat = (hx - 0.05, fy + 0.44 * S - 0.04)
    frame = [ribbon([bb, (5.3, y + rw)], 0.035), ribbon([(5.3, y + rw), (seat[0] + 0.05, seat[1] - 0.25)], 0.03),
             ribbon([bb, (seat[0] + 0.05, seat[1] - 0.1)], 0.04), ribbon([(seat[0] + 0.05, seat[1] - 0.3), (7.95, y + 1.55)], 0.04),
             ribbon([bb, (7.95, y + 1.05)], 0.04), ribbon([(7.9, y + 2.15), (g[0] - 0.05, g[1] + 0.02)], 0.035),
             ribbon([(g[0] - 0.12, g[1] - 0.02), (g[0] + 0.12, g[1] + 0.03)], 0.04),
             [(seat[0] - 0.32, seat[1] + 0.02), (seat[0] + 0.2, seat[1] + 0.02), (seat[0] + 0.1, seat[1] - 0.08), (seat[0] - 0.28, seat[1] - 0.06)],
             ellipse(bb[0], bb[1], 0.2, n=24)]
    cv.add(frame, 'solid')
    cv.carve([ellipse(bb[0], bb[1], 0.12, n=20)], 'mid')
    W.place_figure(cv, rider, hx, fy, S)
    cv.add([ribbon([(bb[0] - 0.3, bb[1] - 0.02), (bb[0] + 0.3, bb[1] + 0.02)], 0.03)], 'solid')
    # the passenger seat, its hood and the sailor under it
    seated(cv, sailor(pose='gesture'), 8.85, y + 1.6, S * 0.92)
    box = [(7.95, y + 0.95), (9.85, y + 0.95), (9.85, y + 1.55), (8.15, y + 1.62), (8.05, y + 2.55), (7.85, y + 2.55)]
    cv.add([box, [(9.8, y + 1.0), (10.6, y + 0.6), (10.62, y + 0.5), (9.8, y + 0.85)]], 'flower')
    hood = _open([(7.7, y + 1.95), (7.82, y + 3.25), (8.3, y + 4.15), (9.2, y + 4.3), (9.85, y + 4.05)], 6) + \
        [(9.95, y + 3.72), (9.55, y + 3.62)] + _open([(9.5, y + 3.66), (9.05, y + 3.78), (8.62, y + 3.62), (8.4, y + 3.1), (8.3, y + 2.0)], 6)
    cv.add([hood], 'scales')
    piv = (8.05, y + 2.0)
    cv.carve([ribbon([(piv[0] + 0.25 * math.cos(a), piv[1] + 0.25 * math.sin(a)),
                      (piv[0] + 2.0 * math.cos(a), piv[1] + 2.0 * math.sin(a))], 0.012) for a in (1.1, 1.3)], 'mid')
    val = [scroll(8.0 + 0.36 * i, y + 3.68 + 0.08 * math.sin(i), 0.07, 0.02, 1.0, a0=180, cw=True) for i in range(5)]
    cv.add(val, 'solid')
    cv.add([ribbon([(9.75, y + 3.72), (9.75, y + 3.45)], 0.012), rect(9.66, y + 3.12, 9.84, y + 3.45),
            [(9.62, y + 3.45), (9.88, y + 3.45), (9.75, y + 3.55)]], 'solid')
    wheel(cv, 9.05, y + rw, rw, 16, knobs=False, rim=0.12)
    cv.add([ribbon(arc_pts(9.05, y + rw, rw + 0.12, 20, 160, 18), 0.04)], 'solid')

def ride_perak(cv):
    """Perahu tambang down the Perak river: an attap-roofed passenger boat, the boatman punting
    from the stern, the sailor and a trader under the roof, sacks of tin ore at the bow."""
    y = RIDE_Y
    yk = y + 0.12
    sk = dict(head='young', hat='tanjak', costume='farmer', pose='crank', lean=6, cls={'top': 'edge'})
    standing(cv, sk, 2.3, y + 0.92, 2.5)
    g = grip_of(sk, 2.3, y + 0.92, 2.5)
    d = (g[0] - 0.4, g[1] - (y + 0.05))
    ln = math.hypot(*d)
    top = (g[0] + 0.9 * d[0] / ln, g[1] + 0.9 * d[1] / ln)
    cv.add([ribbon([top, (0.4, y + 0.05)], 0.035, 0.03)], 'solid')
    seated(cv, dict(body='female', hat='tudung', costume='kurung', pose='carry', item_f='bowl'), 6.1, y + 1.2, 2.4)
    seated(cv, sailor(pose='gesture'), 8.5, y + 1.2, 2.4)
    for sx, sh in ((10.9, 0.62), (11.6, 0.72), (12.3, 0.58)):
        sack(cv, sx, y + 0.95, 0.72, sh)
    cv.add([ribbon([(px, y + 0.9), (px, y + 2.5)], 0.05) for px in (5.2, 7.8, 10.35)], 'solid')
    roof = _open([(4.65, y + 2.35), (5.3, y + 3.05), (7.8, y + 3.48), (10.3, y + 3.05), (10.95, y + 2.35)], 6) + \
        _open([(10.6, y + 2.42), (10.05, y + 2.8), (7.8, y + 3.05), (5.55, y + 2.8), (5.0, y + 2.42)], 6)
    cv.add([roof], 'scales')
    cv.add([leaf(4.85 + 0.3 * i, y + 2.45, -90 + (i % 3 - 1) * 8, 0.25, 0.05) for i in (0, 1, 2)] +
           [leaf(10.75 - 0.3 * i, y + 2.45, -90 + (i % 3 - 1) * 8, 0.25, 0.05) for i in (0, 1, 2)], 'solid')
    gun = hull(cv, 0.9, 14.5, yk, 0.78, rise=0.75, cls='slits')
    cv.add([ribbon(_open([(14.5, gun(14.5)), (14.75, gun(14.5) + 0.25), (14.6, gun(14.5) + 0.45)]), 0.05, 0.025),
            ribbon(_open([(0.9, gun(0.9)), (0.62, gun(0.9) + 0.22), (0.72, gun(0.9) + 0.4)]), 0.05, 0.025),
            rect(1.4, gun(2.3) - 0.06, 3.2, gun(2.3) + 0.04)], 'solid')
    wake(cv, 0.6, 14.9, y + 0.5, 0.36, seed=4)

def ride_selangor(cv):
    """Bus to Negeri Sembilan: a round-nosed kampung bus with open windows, the sailor waving
    from one, luggage, a basket, a chicken coop and a bicycle on the roof rack."""
    y = RIDE_Y
    B = y + 0.98
    seated(cv, dict(head='refined', hat='songkok', costume='baju', pose='stand'), 2.0, y + 1.82, 2.05)
    seated(cv, dict(body='female', hat='tudung', costume='kurung', pose='stand'), 3.25, y + 1.82, 2.05)
    seated(cv, dict(head='young', costume='baju', pose='stand', scale=0.8), 4.5, y + 1.92, 2.05)
    seated(cv, sailor(pose='wonder'), 7.05, y + 1.82, 2.05)
    seated(cv, dict(head='old', beard='tuft', hat='journey_cap', costume='baju', pose='stand'), 9.5, y + 1.82, 2.05)
    seated(cv, dict(head='refined', hat='journey_cap', costume='baju', pose='crank'), 11.7, y + 1.82, 2.05)
    fw, rw = (12.45, 0.62), (3.6, 0.62)
    arch = lambda cx, a, b: [(cx + 0.74 * math.cos(math.radians(t)), y + 0.62 + 0.74 * math.sin(math.radians(t)))
                             for t in [a + (b - a) * i / 14 for i in range(15)]]
    k = math.degrees(math.asin((B - y - 0.62) / 0.74))
    outline = [(14.05, B)] + arch(fw[0], k, 180 - k) + arch(rw[0], k, 180 - k) + \
        [(0.85, B), (0.82, y + 3.3), (1.1, y + 3.55), (11.9, y + 3.6), (12.25, y + 3.45), (12.6, y + 2.45),
         (13.65, y + 2.32), (13.98, y + 2.05), (14.08, y + 1.4)]
    wins = [rect(1.35 + 1.28 * i, y + 2.2, 2.4 + 1.28 * i, y + 3.18) for i in range(8)]
    wins.append([(11.62, y + 2.2), (12.45, y + 2.2), (12.2, y + 3.2), (11.62, y + 3.2)])
    cv.add_eo([outline] + wins, 'dots')
    cv.carve([ribbon([(1.0, y + 1.92), (12.6, y + 1.92)], 0.03), ribbon([(1.0, y + 1.78), (12.6, y + 1.78)], 0.012)] +
             [ribbon([(13.45 + 0.12 * i, y + 1.55), (13.5 + 0.12 * i, y + 2.05)], 0.018) for i in range(4)], 'mid')
    cv.add([ellipse(12.0, y + 2.35, 0.08, 0.26, rot=-25)], 'solid')
    cv.add([ellipse(13.95, y + 1.95, 0.17), rect(13.7, y + 0.88, 14.32, y + 1.08), rect(0.6, y + 0.9, 1.0, y + 1.06)], 'edge')
    cv.carve([ellipse(13.95, y + 1.95, 0.07)], 'mid')
    for cx, r in (fw, rw):
        wheel(cv, cx, y + r, r, 10, knobs=False, rim=0.2)
        cv.add([ellipse(cx, y + r, r * 0.42)], 'edge')
    cv.add([ribbon([(0.92, y + 1.1), (0.92, y + 3.5)], 0.03)] +
           [ribbon([(0.82, y + 1.3 + 0.35 * i), (1.02, y + 1.3 + 0.35 * i)], 0.02) for i in range(7)], 'solid')
    # roof rack and its load
    cv.add([ribbon([(1.4, y + 3.95), (11.2, y + 3.95)], 0.035)] +
           [ribbon([(px, y + 3.55), (px, y + 3.95)], 0.025) for px in (1.5, 3.3, 5.1, 6.9, 8.7, 10.5, 11.1)], 'solid')
    cv.add([rect(1.7, y + 3.6, 2.95, y + 4.25), rect(2.15, y + 4.25, 2.5, y + 4.35)], 'edge')
    cv.carve([ribbon([(2.32, y + 3.62), (2.32, y + 4.23)], 0.02)], 'mid')
    basket(cv, 3.2, 4.25, y + 3.6, y + 4.45, handle=True)
    cv.add([rect(4.6, y + 3.6, 6.2, y + 4.55), _open([(4.5, y + 4.55), (5.4, y + 4.85), (6.3, y + 4.55)], 4)], 'grid')
    hen = [ellipse(5.75, y + 5.0, 0.22, 0.16), ellipse(5.95, y + 5.2, 0.08, 0.08), [(6.0, y + 5.22), (6.12, y + 5.18), (6.0, y + 5.15)],
           leaf(5.55, y + 5.05, 140, 0.28, 0.08), leaf(5.95, y + 5.27, 90, 0.08, 0.03), ribbon([(5.75, y + 4.85), (5.75, y + 4.6)], 0.012)]
    cv.add(hen, 'solid')
    cv.add([_open([(6.6, y + 3.62), (6.5, y + 4.0), (6.75, y + 4.25), (8.4, y + 4.25), (8.6, y + 3.95), (8.45, y + 3.62)], 4)], 'slits')
    for cx in (9.2, 10.55):
        wheel(cv, cx, y + 4.05, 0.42, 10, knobs=False, rim=0.15, cls='solid')
    cv.add([ribbon([(9.2, y + 4.05), (9.85, y + 4.08), (10.55, y + 4.05)], 0.025), ribbon([(9.85, y + 4.08), (9.7, y + 4.5)], 0.025),
            ribbon([(9.45, y + 4.42), (10.35, y + 4.42)], 0.025), ribbon([(10.35, y + 4.42), (10.55, y + 4.05)], 0.025),
            rect(9.55, y + 4.5, 9.85, y + 4.56), ribbon([(10.3, y + 4.42), (10.42, y + 4.62), (10.58, y + 4.62)], 0.02)], 'solid')
    puffs(cv, [(0.45, y + 0.75, 0.22), (0.2, y + 1.05, 0.28)], mid=0, seed=3)

def ride_nsembilan(cv):
    """Horse-drawn cart to Melaka: a two-wheeled kereta kuda under a gonjong roof whose horn
    tips sweep up like a Negeri Sembilan house, the driver in his tengkolok, the sailor behind."""
    y = RIDE_Y
    _, bit = horse(cv, 11.65, y, 1.1)
    drv = dict(head='refined', hat='tengkolok', costume='baju', pose='stand', item_f='switch')
    seated(cv, sailor(pose='gesture'), 4.6, y + 2.5, 2.6)
    seated(cv, drv, 7.6, y + 2.5, 2.6)
    g = seated_grip(drv, 7.6, y + 2.5, 2.6)
    cv.add([ribbon(_open([g, ((g[0] + bit[0]) / 2, (g[1] + bit[1]) / 2 - 0.25), bit]), 0.015)], 'solid')
    cv.add([ribbon([(8.0, y + 2.0), (11.35, y + 2.35)], 0.055), ribbon([(8.0, y + 1.75), (11.2, y + 1.95)], 0.045)], 'solid')
    cv.add([rect(2.6, y + 1.7, 8.25, y + 2.5), [(6.9, y + 1.75), (8.45, y + 1.75), (8.6, y + 1.38), (6.9, y + 1.38)],
            [(8.2, y + 2.5), (8.45, y + 2.5), (8.3, y + 1.7), (8.2, y + 1.7)]], 'slits')
    cv.add([rect(2.5, y + 2.45, 8.35, y + 2.56)] +
           [ribbon([(px, y + 2.5), (px, y + 4.5)], 0.05) for px in (2.75, 5.45, 8.15)], 'solid')
    roof = _open([(1.55, y + 5.98), (1.95, y + 5.55), (2.6, y + 5.25), (5.45, y + 5.12), (8.3, y + 5.25), (8.95, y + 5.55),
                  (9.35, y + 5.98)], 6) + \
        _open([(9.15, y + 5.78), (8.7, y + 5.2), (8.3, y + 4.6), (5.45, y + 4.48), (2.6, y + 4.6), (2.2, y + 5.2),
               (1.75, y + 5.78)], 6)
    cv.add([roof], 'scales')
    cv.add([leaf(1.62, y + 5.88, 122, 0.42, 0.075, bend=0.08), leaf(9.28, y + 5.88, 58, 0.42, 0.075, bend=-0.08)], 'solid')
    cv.carve([ribbon(_open([(2.3, y + 4.95), (5.45, y + 4.78), (8.6, y + 4.95)]), 0.016)], 'mid')
    val = rect(2.8, y + 4.3, 8.1, y + 4.55)
    cv.add([val] + [[(2.8 + 0.33 * i, y + 4.3), (3.13 + 0.33 * i, y + 4.3), (2.965 + 0.33 * i, y + 4.12)] for i in range(16)], 'edge')
    cv.carve([W.diamond(2.98 + 0.33 * i, y + 4.43, 0.07, 0.07)[0] for i in range(16)], 'mid')
    cv.add([ribbon([(8.15, y + 4.3), (8.15, y + 3.95)], 0.012), rect(8.05, y + 3.6, 8.25, y + 3.95)], 'solid')
    wheel(cv, 5.45, y + 1.05, 1.05, 14, knobs=False, rim=0.13)

def ride_melaka(cv):
    """Fishing boat down the coast to Johor: a perahu under a tall lug sail, the fisherman at
    the steering oar, nets heaped amidships, the sailor on the foredeck with the sheet."""
    y = RIDE_Y
    yk = y + 0.1
    fisher = dict(head='old', beard='tuft', hat='caping', costume='farmer', pose='crank', lean=-4, cls={'top': 'edge'})
    standing(cv, fisher, 2.65, y + 1.0, 2.45)
    g = grip_of(fisher, 2.65, y + 1.0, 2.45)
    cv.add([ribbon([(g[0] + 0.35, g[1] + 0.35), (1.2, y + 0.05)], 0.04, 0.03), leaf(1.45, y + 0.35, -122, 0.7, 0.13)], 'solid')
    cv.add([ribbon([(7.55, y + 0.95), (7.25, y + 5.2)], 0.06, 0.045)], 'solid')
    lug_sail(cv, (4.4, y + 4.8), (9.9, y + 5.75), (9.5, y + 1.75), (4.7, y + 1.55), cls='slits')
    flag(cv, 7.25, y + 5.25, 1.1)
    cv.add([_open([(5.2, y + 0.95), (5.5, y + 1.45), (6.4, y + 1.6), (7.2, y + 1.35), (7.4, y + 0.95)], 5)], 'scales')
    seated(cv, sailor(pose='pull'), 11.3, y + 1.2, 2.35)
    sg = seated_grip(sailor(pose='pull'), 11.3, y + 1.2, 2.35)
    cv.add([ribbon([sg, (9.6, y + 1.85)], 0.012)], 'solid')
    gun = hull(cv, 1.6, 13.6, yk, 0.85, rise=1.05, cls='slits', steep=5)
    for x, sgn in ((13.6, 1), (1.6, -1)):
        t = gun(x)
        cv.add([ribbon(_open([(x, t - 0.1), (x + sgn * 0.3, t + 0.25), (x + sgn * 0.12, t + 0.55)]), 0.06, 0.02),
                scroll(x + sgn * 0.02, t + 0.58, 0.14, 0.04, 1.1, a0=0 if sgn > 0 else 180, cw=sgn < 0)], 'solid')
    cv.carve([leaf(12.4 - 0.32 * i, y + 0.75, 0, 0.22, 0.045) for i in range(4)], 'mid')
    egret(cv, 12.3, y + 4.6, 0.75, pose='fly')
    wake(cv, 1.3, 13.9, y + 0.48, 0.42, seed=6, curl=1.25)

def ride_johor(cv):
    """Coastal ferry up the east coast: a motor launch with a cabin deck, an awning aft, the
    wheelhouse forward and a raked funnel; the sailor at the upper rail looks out to sea."""
    y = RIDE_Y
    D, U = y + 1.65, y + 3.05
    plume(cv, 7.05, y + 5.25, n=7, dx=-0.62, dy=0.1, r0=0.24, r1=0.45, mid=3, seed=21)
    standing(cv, dict(body='female', hat='tudung', costume='kurung', pose='stand'), 3.4, U + 0.1, 1.95)
    standing(cv, dict(head='young', costume='baju', pose='gesture', scale=0.72), 4.15, U + 0.1, 1.95)
    standing(cv, sailor(pose='wonder', item_b='rope'), 8.05, U + 0.1, 2.0)
    seated(cv, dict(head='refined', hat='journey_cap', costume='baju', pose='crank'), 10.5, y + 3.25, 1.4)
    cv.add([ribbon([(px, U + 0.1), (px, y + 5.05)], 0.035) for px in (2.45, 6.35)] +
           [_open([(2.15, y + 5.0), (4.4, y + 5.22), (6.65, y + 5.0)], 5) + [(6.65, y + 4.9), (2.15, y + 4.9)]], 'edge')
    cv.add([[(2.3 + 0.35 * i, y + 4.9), (2.65 + 0.35 * i, y + 4.9), (2.475 + 0.35 * i, y + 4.72)] for i in range(12)], 'solid')
    cv.add([[(6.9, U + 0.1), (7.6, U + 0.1), (7.42, y + 5.0), (6.82, y + 5.0)], rect(6.75, y + 4.85, 7.5, y + 5.05)], 'edge')
    cv.carve([ribbon([(6.88, y + 4.4), (7.52, y + 4.4)], 0.03)], 'mid')
    wh = [(9.4, U + 0.1), (11.6, U + 0.1), (11.75, y + 4.15), (9.3, y + 4.15)]
    cv.add_eo([wh, rect(9.65, y + 3.55, 10.45, y + 4.0), rect(10.65, y + 3.55, 11.5, y + 4.0)], 'dots')
    cv.add([rect(9.1, y + 4.12, 11.95, y + 4.28)], 'solid')
    cv.add([ribbon([(px, U + 0.1), (px, U + 0.75)], 0.022) for px in [2.4 + 0.42 * i for i in range(17)]] +
           [ribbon([(2.3, U + 0.42), (9.4, U + 0.42)], 0.02), ribbon([(2.3, U + 0.75), (9.4, U + 0.75)], 0.028),
            rect(2.25, U, 11.7, U + 0.14)], 'solid')
    cabin = [(2.6, D), (11.2, D), (11.2, U), (2.6, U)]
    cv.add_eo([cabin] + [rect(3.0 + 1.05 * i, D + 0.4, 3.7 + 1.05 * i, D + 1.05) for i in range(8)], 'dots')
    cv.add([ribbon([(12.9, y + 1.95), (12.85, y + 5.3)], 0.045), ribbon([(12.85, y + 5.2), (14.6, y + 2.0)], 0.012),
            ribbon([(12.85, y + 5.2), (11.7, y + 4.2)], 0.012), ribbon([(12.6, y + 4.4), (13.1, y + 4.4)], 0.025)], 'solid')
    flag(cv, 12.85, y + 5.3, 0.9, wave=0.1)
    for lx in (4.6, 8.8):
        cv.add_eo([ellipse(lx, D + 0.72, 0.28), ellipse(lx, D + 0.72, 0.15)], 'edge')
    top = _open([(1.0, D + 0.02), (5.0, D - 0.04), (10.0, D + 0.02), (13.0, D + 0.18), (14.7, D + 0.42)], 6)
    body = top + [(14.55, D), (14.0, y + 0.9), (13.0, y + 0.3), (11.0, y + 0.12), (2.0, y + 0.12), (1.2, y + 0.4), (1.05, y + 1.1)]
    cv.add([body], 'slits')
    cv.carve([ribbon([(1.3, D - 0.25), (14.3, D - 0.05)], 0.02)] +
             [ellipse(2.4 + 0.75 * i, y + 1.2, 0.08) for i in range(15)], 'mid')
    cv.add([ribbon([(14.1, D + 0.2), (14.3, D - 0.4)], 0.04), [(14.15, D - 0.42), (14.45, D - 0.55), (14.2, D - 0.6)]], 'solid')
    wake(cv, 0.8, 15.1, y + 0.55, 0.45, seed=8, curl=1.2)

def ride_pahang(cv):
    """River longboat through the forest: a long dugout, a paddler kneeling at the bow, the
    sailor amidships on the cargo, the steersman standing at the stern with his long paddle."""
    y = RIDE_Y
    yk = y + 0.16
    st = dict(head='young', hat='tanjak', costume='farmer', pose='stick', cls={'top': 'edge'})
    standing(cv, st, 1.85, y + 0.86, 2.45)
    g = grip_of(st, 1.85, y + 0.86, 2.45)
    cv.add([ribbon([(g[0] + 0.35, g[1] + 0.6), (0.55, y + 0.15)], 0.035, 0.028), leaf(0.85, y + 0.5, -125, 0.75, 0.12)], 'solid')
    for i, (rx, h) in enumerate(((9.0, 0.55), (9.75, 0.62), (10.5, 0.5))):
        cv.add([_open([(rx - 0.38, y + 0.8), (rx - 0.42, y + 0.8 + h * 0.5), (rx - 0.3, y + 0.8 + h), (rx + 0.3, y + 0.8 + h),
                       (rx + 0.42, y + 0.8 + h * 0.5), (rx + 0.38, y + 0.8)], 4)], 'slits')
        cv.carve([ribbon([(rx - 0.4, y + 0.8 + h * 0.5), (rx + 0.4, y + 0.8 + h * 0.5)], 0.02)], 'mid')
    jar(cv, 4.6, y + 0.82, 0.9)
    seated(cv, sailor(pose='gesture'), 7.0, y + 1.25, 2.4)
    pd = dict(head='refined', costume='farmer', pose='journey_paddle', item_f='journey_paddle', cls={'top': 'edge'}, hat='tanjak')
    seated(cv, pd, 12.4, y + 1.05, 2.4)
    gun = hull(cv, 0.7, 14.7, yk, 0.6, rise=0.5, cls='slits', steep=6, strakes=1)
    cv.add([ribbon(_open([(14.7, gun(14.7)), (14.95, gun(14.7) + 0.2), (14.85, gun(14.7) + 0.42)]), 0.05, 0.02),
            scroll(14.78, gun(14.7) + 0.46, 0.12, 0.035, 1.1, a0=0, cw=False)], 'solid')
    wake(cv, 0.5, 15.0, y + 0.46, 0.3, seed=12, curl=0.9)

def ride_terengganu(cv):
    """Bicycle up the coast road to Kelantan: the sailor pedals an old roadster, his
    neckerchief flying, a rattan basket of fish on the carrier and coconuts up front."""
    y = RIDE_Y
    S = 3.7
    r = 0.8
    rear, front = (4.85, y + r), (9.25, y + r)
    rider = sailor(pose='journey_cycle', rods=False)
    hx, fy = 6.25, y + 0.5
    bb = (hx + 0.085 * S, fy + 0.08)
    g = grip_of(rider, hx, fy, S)
    seat = (hx - 0.05, fy + 0.44 * S - 0.05)
    head = (8.45, y + 1.95)
    for c in (rear, front):
        wheel(cv, c[0], c[1], r, 18, knobs=False, rim=0.09)
        cv.add([ribbon(arc_pts(c[0], c[1], r + 0.1, 25, 165, 18), 0.03)], 'solid')
    basket(cv, 3.95, 5.65, y + 1.62, y + 2.42)
    cv.add([leaf(4.3 + 0.32 * i, y + 2.38, 95 - 10 * i, 0.38, 0.09, bend=0.03) for i in range(4)] +
           [[(4.3 + 0.32 * i, y + 2.74 + 0.02 * i), (4.2 + 0.32 * i, y + 2.88), (4.42 + 0.32 * i, y + 2.86)] for i in range(4)],
           'solid')
    frame = [ribbon([bb, rear], 0.035), ribbon([rear, (seat[0] + 0.05, seat[1] - 0.25)], 0.03),
             ribbon([bb, (seat[0] + 0.03, seat[1] - 0.08)], 0.04), ribbon([(seat[0] + 0.05, seat[1] - 0.28), (head[0] + 0.02, head[1] - 0.02)], 0.04),
             ribbon([bb, (head[0] + 0.1, head[1] - 0.35)], 0.045), ribbon([head, (head[0] + 0.12, head[1] - 0.4)], 0.05),
             ribbon([(head[0] + 0.12, head[1] - 0.4), front], 0.035),
             ribbon([(head[0], head[1]), (head[0] - 0.05, g[1] + 0.12)], 0.035),
             ribbon(_open([(head[0] - 0.05, g[1] + 0.12), (g[0] + 0.25, g[1] + 0.15), (g[0], g[1] + 0.03)]), 0.03),
             rect(3.9, y + 1.55, 6.05, y + 1.62), ribbon([(4.0, y + 1.58), (rear[0], rear[1])], 0.025),
             [(seat[0] - 0.34, seat[1] + 0.04), (seat[0] + 0.22, seat[1] + 0.04), (seat[0] + 0.12, seat[1] - 0.08), (seat[0] - 0.3, seat[1] - 0.06)],
             ellipse(bb[0], bb[1], 0.22, n=24), ellipse(head[0] - 0.05, g[1] + 0.2, 0.06)]
    cv.add(frame, 'solid')
    cv.carve([ellipse(bb[0], bb[1], 0.13, n=20)], 'mid')
    W.place_figure(cv, rider, hx, fy, S)
    nk = [ribbon(_open([(hx + 0.15, fy + 2.35), (hx - 0.4, fy + 2.45), (hx - 0.9, fy + 2.3), (hx - 1.3, fy + 2.42)]), 0.06, 0.02)]
    cv.add(nk, 'edge')
    cv.add([ribbon([(bb[0] - 0.32, bb[1] - 0.03), (bb[0] + 0.32, bb[1] + 0.03)], 0.03)], 'solid')
    basket(cv, 9.0, 9.85, y + 1.55, y + 2.1)
    cv.add([ellipse(9.25, y + 2.2, 0.17, 0.15), ellipse(9.6, y + 2.18, 0.16, 0.14)], 'dots')
    cv.add([ribbon([(head[0] + 0.06, head[1] - 0.15), (9.0, y + 1.85)], 0.025)], 'solid')

def ride_kelantan(cv):
    """Chartered boat across the South China Sea: a two-masted perahu besar under lug sails,
    pennants flying, the carved bangau rising from its bow; the sailor watches for Sabah
    through his spyglass, the skipper holds the tiller, the sea breaks round the hull."""
    y = RIDE_Y
    yk = y + 0.1
    wave(cv, 1.6, y - 0.25, 3.0, 1.05, layer='back', seed=31, claws=3)
    wave(cv, 14.2, y - 0.25, 2.6, 0.95, flip=True, layer='back', seed=32, claws=3)
    sk = dict(head='old', beard='tuft', hat='tanjak', costume='farmer', pose='stand', cls={'top': 'edge'})
    standing(cv, sk, 1.95, y + 1.55, 2.25)
    g = grip_of(sk, 1.95, y + 1.55, 2.25)
    cv.add([ribbon([g, (1.15, y + 1.62)], 0.035), ribbon([(1.15, y + 1.62), (0.95, y + 0.2)], 0.05),
            leaf(1.05, y + 0.75, -100, 0.6, 0.15)], 'solid')
    for mx, top in ((4.75, y + 4.75), (9.0, y + 5.55)):
        cv.add([ribbon([(mx, y + 1.2), (mx - 0.2, top)], 0.06, 0.045)], 'solid')
        flag(cv, mx - 0.2, top + 0.05, 1.0, wave=0.1)
    lug_sail(cv, (2.85, y + 4.35), (6.2, y + 4.85), (5.95, y + 2.35), (3.1, y + 2.2), cls='slits', battens=2)
    lug_sail(cv, (6.55, y + 5.05), (11.4, y + 5.85), (11.05, y + 2.0), (6.85, y + 1.85), cls='slits', battens=3)
    for jx in (7.4, 8.1):
        jar(cv, jx, y + 1.25, 0.75)
    standing(cv, sailor(pose='wonder', item_f='spyglass'), 12.15, y + 1.3, 2.2)
    cv.add([rect(1.3, y + 1.45, 3.6, y + 1.58)], 'solid')
    gun = hull(cv, 0.8, 14.0, yk, 1.05, rise=0.75, cls='slits', steep=5, strakes=3)
    t = gun(14.0)
    stem = ribbon(_open([(13.85, t - 0.2), (14.3, t + 0.3), (14.2, t + 0.95), (14.45, t + 1.35)]), 0.09, 0.05)
    head = [ellipse(14.5, t + 1.4, 0.11, 0.09), [(14.58, t + 1.44), (15.05, t + 1.36), (14.6, t + 1.33)],
            leaf(14.4, t + 1.46, 160, 0.35, 0.05, bend=-0.08)]
    cv.add([stem] + head, 'edge')
    cv.carve([ribbon(_open([(13.95, t), (14.25, t + 0.45), (14.2, t + 0.9)]), 0.012), ellipse(14.52, t + 1.42, 0.025)], 'mid')
    cv.add([ribbon(_open([(0.8, gun(0.8)), (0.55, gun(0.8) + 0.3), (0.7, gun(0.8) + 0.55)]), 0.06, 0.03)], 'solid')
    spray(cv, 14.3, y + 0.55, 0.8, seed=5)
    wake(cv, 0.5, 14.6, y + 0.55, 0.42, seed=33, curl=0.95)

def ride_sabah(cv):
    """Riverboat into Borneo's interior: a long motorboat with an outboard, the boatman at its
    tiller, the sailor under a canopy beside a woman with her wakid basket, the guide at the bow
    sounding the river with his pole."""
    y = RIDE_Y
    yk = y + 0.14
    bm = dict(head='young', hat='journey_cap', costume='farmer', pose='journey_tiller', cls={'top': 'edge'})
    seated(cv, bm, 2.3, y + 1.0, 2.4)
    g = seated_grip(bm, 2.3, y + 1.0, 2.4, which='b')
    motor = [_open([(0.42, y + 1.12), (0.36, y + 1.5), (0.55, y + 1.8), (1.05, y + 1.86), (1.4, y + 1.62), (1.42, y + 1.12)], 4),
             [(0.62, y + 1.15), (1.15, y + 1.15), (1.0, y + 0.3), (0.8, y + 0.3)],                         # leg
             [(0.55, y + 0.42), (1.25, y + 0.42), (1.2, y + 0.34), (0.6, y + 0.34)],                       # cavitation plate
             ellipse(0.62, y + 0.2, 0.06, 0.16), ellipse(0.9, y + 0.2, 0.12, 0.09),                       # propeller, hub
             ribbon([g, (1.25, y + 1.62)], 0.035), rect(1.3, y + 1.25, 1.55, y + 1.45)]                  # tiller, clamp
    cv.add(motor, 'edge')
    cv.carve([ribbon([(0.55, y + 1.45), (1.3, y + 1.48)], 0.012)], 'mid')
    spray(cv, 0.55, y + 0.3, 0.85, flip=True, seed=8)
    for px in (5.0, 10.2):
        cv.add([ribbon([(px, y + 0.85), (px, y + 3.12)], 0.04)], 'solid')
    cv.add([_open([(4.6, y + 3.3), (7.6, y + 3.18), (10.6, y + 3.3)], 5) + [(10.55, y + 2.98), (7.6, y + 2.9), (4.65, y + 2.98)]] +
           [[(4.8 + 0.4 * i, y + 2.98), (5.2 + 0.4 * i, y + 2.98), (5.0 + 0.4 * i, y + 2.8)] for i in range(14)], 'edge')
    seated(cv, sailor(pose='gesture'), 6.6, y + 1.15, 2.4)
    sack(cv, 5.5, y + 0.85, 0.6, 0.6, cls='slits')
    seated(cv, dict(body='female', hat='tudung', costume='kurung', pose='stand'), 8.6, y + 1.15, 2.4)
    wk = [(9.4, y + 0.9), (9.62, y + 0.9), (10.05, y + 2.45), (8.97, y + 2.45)]
    cv.add([wk, rect(8.92, y + 2.43, 10.1, y + 2.55)], 'grid')
    cv.carve([ribbon([(9.1 + 0.02 * k, y + 1.3 + 0.35 * k), (9.92 - 0.02 * k, y + 1.3 + 0.35 * k)], 0.015) for k in range(3)], 'mid')
    jar(cv, 11.3, y + 0.85, 0.75)
    gd = dict(head='refined', hat='tanjak', costume='farmer', pose='stick', cls={'top': 'edge'})
    standing(cv, gd, 12.75, y + 0.92, 2.35)
    gg = grip_of(gd, 12.75, y + 0.92, 2.35)
    cv.add([ribbon([(gg[0] - 0.25, gg[1] + 1.1), (gg[0] + 0.55, y - 0.05)], 0.03)], 'solid')
    L0, L1 = 1.35, 14.6
    gun = lambda x: yk + 0.7 + 0.45 * max(0.0, (x - 11.0) / (L1 - 11.0)) ** 2
    top = [(L0 + (L1 - L0) * i / 40, gun(L0 + (L1 - L0) * i / 40)) for i in range(41)]
    bot = _open([(L1, gun(L1)), (L1 - 0.6, yk + 0.25), (L1 - 2.2, yk), (L0 + 0.3, yk + 0.05), (L0, yk + 0.25)], 6)
    cv.add([top + bot[1:]], 'slits')
    cv.carve([ribbon([(x, gun(x) - 0.28) for x in [L0 + 0.4 + (L1 - L0 - 1.5) * i / 20 for i in range(21)]], 0.011)], 'mid')
    wake(cv, 0.9, 14.9, y + 0.48, 0.36, seed=14, curl=1.1)
    puffs(cv, [(0.0, y + 0.6, 0.3)], mid=0, seed=15)

for _fn in (ride_perlis, ride_kedah, ride_penang, ride_perak, ride_selangor, ride_nsembilan, ride_melaka,
            ride_johor, ride_pahang, ride_terengganu, ride_kelantan, ride_sabah):
    _fn.size = RIDE

# =====================================================================
# prologue, strips, endings (2048x820)
# =====================================================================

def prologue(cv):
    """The shipwreck: a foreign ship breaking in two on wayang waves in a storm."""
    rain(cv, 0.0, 20.5, 2.0, 8.6, 90, seed=3)
    for i, (x, y) in enumerate(((1.5, 7.0), (4.8, 6.7), (15.6, 7.0))):
        cloud(cv, x, y, 1.3, 'back', flip=i > 1, seed=30 + i)
    for i in range(7):
        wave(cv, 1.0 + i * 3.2, G + 0.4, 3.4, 1.4, flip=i % 2 == 1, layer='back', seed=40 + i, claws=3)
    cloud(cv, 1.6, 6.6, 1.25, 'mid', seed=33)
    cloud(cv, 16.2, 6.2, 0.95, 'mid', flip=True, seed=34)
    lightning(cv, 3.2, 6.4, 2.8, seed=5)
    ship(cv, 9.4, G + 0.15, 0.78, breaks=(0.7, -13.0, 17.0), seed=7)
    for i, (bx, by, rot) in enumerate(((8.9, 3.7, 25), (10.9, 4.3, -40), (13.9, 2.6, 70), (6.0, 2.2, -15))):
        body, bands = barrel(bx, by, 0.55 + 0.1 * (i % 2), rot)
        cv.add([body], 'edge')
        cv.carve(bands)
    cv.add([xf(rect(-0.5, -0.06, 0.5, 0.06), px, py, rot=r) for px, py, r in
            ((9.6, 5.1, 30), (10.3, 5.7, -50), (12.6, 4.9, 15), (7.6, 4.6, 70), (14.6, 3.6, -25))], 'solid')
    wave(cv, 3.8, G, 5.4, 3.3, seed=11)
    wave(cv, 17.2, G, 5.0, 2.7, flip=True, seed=12)
    wave(cv, 10.6, G - 0.1, 7.6, 2.3, seed=13, claws=4)
    spray(cv, 9.9, 3.1, 1.2, seed=3)
    spray(cv, 6.4, 3.4, 1.0, flip=True, seed=4)
    ground(cv, 'water', seed=37)
    wave(cv, -0.3, -0.2, 3.6, 2.2, layer='front', seed=14, claws=4)
    wave(cv, 20.8, -0.2, 3.4, 2.0, flip=True, layer='front', seed=15, claws=4)

def strip_road(cv):
    """Travel strip, road: a kampung road between rain trees and palms; the
    middle band is left open for the vehicle sliding across."""
    hills(cv, -0.5, 21, G + 1.6, 1.6, seed=21, n=4)
    for i, (x, sc) in enumerate(((3.2, 0.7), (8.4, 0.6), (13.6, 0.65), (17.4, 0.55))):
        rumah(cv, x, G + 1.1, sc, 'back', flip=i % 2 == 1)
    for i, x in enumerate((1.0, 5.6, 6.3, 10.8, 11.5, 15.9, 19.6)):
        palm(cv, x, G + 1.0, 2.6 + 0.4 * (i % 3), lean=0.12 * (-1) ** i, seed=70 + i, layer='back', fronds=7)
    cloud(cv, 4.6, 7.2, 0.8, 'back', seed=71)
    cloud(cv, 15.0, 7.4, 0.7, 'back', flip=True, seed=72)
    birds(cv, 11.5, 6.8, 3, 0.5, seed=73, layer='back', flip=True)
    raintree(cv, 2.2, G + 0.2, 5.4, seed=74)
    palm(cv, 18.3, G + 0.2, 4.6, lean=-0.1, seed=75)
    palm(cv, 19.3, G + 0.2, 4.0, lean=0.12, seed=76, fronds=8)
    cv.add([ribbon(_open([(-0.2, G + 0.92), (7.0, G + 0.97), (14.0, G + 0.9), (20.7, G + 0.96)]), 0.05)], 'solid')
    fence(cv, 4.6, 16.6, G + 0.95, 0.55)
    banana(cv, 13.8, G + 0.95, 2.4, seed=81, layer='mid', flip=True)
    banana(cv, 6.0, G + 0.95, 2.0, seed=82, layer='mid')
    milestone(cv, 15.6, G + 0.1, 0.9)
    grass(cv, 4.0, 17.0, G + 0.95, 0.45, seed=77, layer='mid', n=40)
    ground(cv, 'road', seed=78)
    grass(cv, -0.2, 2.6, 0.0, 1.2, seed=79)
    grass(cv, 17.8, 20.7, 0.0, 1.1, seed=80)

def nipah(cv, x, y, h, seed=1, layer='mid', n=7):
    """Nipah palm: stemless fronds rising in a fountain from the water's edge."""
    rnd = random.Random(seed)
    polys = []
    for i in range(n):
        a = math.radians(90 + (i - (n - 1) / 2) * 17 + rnd.uniform(-5, 5))
        L = h * rnd.uniform(0.8, 1.05)
        d = (math.cos(a), math.sin(a))
        droop = L * (0.12 + 0.3 * abs(d[0]))
        path = _open([(x, y), (x + d[0] * L * 0.4, y + d[1] * L * 0.5), (x + d[0] * L * 0.8, y + d[1] * L * 0.78 - droop * 0.3),
                      (x + d[0] * L, y + d[1] * L * 0.72 - droop)])
        polys.append(ribbon(path, 0.03 * h ** 0.5, 0.006))
        for k in range(4, len(path) - 1, 2):
            p, q = path[k], path[k + 1]
            ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
            ll = h * 0.13 * (1 - 0.5 * k / len(path))
            polys += [leaf(p[0], p[1], ang + 50, ll, 0.011 * h ** 0.5), leaf(p[0], p[1], ang - 50, ll, 0.011 * h ** 0.5)]
    cv.add(polys, 'solid', layer)

def mangrove(cv, x, y, h, seed=1, layer='mid'):
    """Bakau: a trunk standing on arching prop roots under a rounded crown."""
    base = y + 0.26 * h
    roots = []
    for i in range(7):
        t = (i - 3) / 3
        roots.append(ribbon(_open([(x + t * 0.04 * h, base + 0.12 * h), (x + t * 0.3 * h, base + 0.03 * h),
                                   (x + t * 0.46 * h, y - 0.05)]), 0.018 * h, 0.011 * h))
    cv.add(roots + [ribbon([(x, base), (x + 0.03 * h, y + 0.64 * h)], 0.05 * h, 0.035 * h)], 'solid', layer)
    crown = canopy(x, y + 0.76 * h, 0.36 * h, seed, 7) + canopy(x - 0.3 * h, y + 0.64 * h, 0.2 * h, seed + 1, 5) + \
        canopy(x + 0.3 * h, y + 0.66 * h, 0.21 * h, seed + 2, 5)
    cv.add(crown, 'scales', layer)

def hornbill(cv, x, y, s, flip=False, layer='mid'):
    """Kenyalang in flight: fingered wings raised, long tail, great casqued bill."""
    P = lambda pts: xf(pts, x, y, s=s, flip=flip)
    parts = [ellipse(0, 0, 0.45, 0.13, rot=6), ellipse(0.48, 0.08, 0.11, 0.1),
             [(0.55, 0.13), (0.96, -0.05), (0.99, -0.1), (0.56, 0.02)], [(0.5, 0.16), (0.62, 0.23), (0.84, 0.07), (0.58, 0.1)],
             [(-0.38, 0.03), (-1.08, 0.13), (-1.1, -0.04), (-0.38, -0.08)]]
    parts += [leaf(-0.08 + 0.05 * k, 0.06, 104 - 13 * k, 0.95 - 0.1 * k, 0.11, bend=-0.05) for k in range(5)]
    cv.add([P(p) for p in parts], 'edge', layer)
    cv.carve([P(ellipse(0.5, 0.1, 0.022)), P(ribbon([(-0.5, 0.0), (-1.02, 0.06)], 0.01)),
              P(ribbon([(0.58, 0.15), (0.78, 0.08)], 0.008))], layer)

def longhouse(cv, x0, x1, y, s=1.0, layer='back'):
    """Rumah panjang: one long attap roof over a row of bilik doors, the ruai, stilts, notched ladders."""
    n = int((x1 - x0) / (0.55 * s))
    posts = [ribbon([(x0 + 0.15 + i * 0.55 * s, y), (x0 + 0.15 + i * 0.55 * s, y + 0.98 * s)], 0.035 * s) for i in range(n + 1)]
    cv.add(posts + [rect(x0, y + 0.95 * s, x1, y + 1.07 * s)], 'solid', layer)
    doors = [rect(x0 + 0.5 * s + i * 1.1 * s, y + 1.12 * s, x0 + 0.8 * s + i * 1.1 * s, y + 1.55 * s)
             for i in range(int((x1 - x0) / (1.1 * s)))]
    cv.add_eo([rect(x0 + 0.1, y + 1.07 * s, x1 - 0.1, y + 1.7 * s)] + doors, 'grid', layer)
    cv.add([[(x0 - 0.4 * s, y + 1.6 * s), (x1 + 0.4 * s, y + 1.6 * s), (x1 - 0.15 * s, y + 2.5 * s), (x0 + 0.15 * s, y + 2.5 * s)]],
           'scales', layer)
    cv.add([ribbon([(lx, y), (lx + 0.35 * s, y + 1.0 * s)], 0.05 * s) for lx in (x0 + 1.2 * s, (x0 + x1) / 2, x1 - 1.6 * s)], 'solid', layer)

def telegraph(cv, xs, y, h, layer='mid'):
    """Tiang telegraf: poles with a crossarm and insulators, wires sagging between."""
    polys = []
    for x in xs:
        polys += [ribbon([(x, y), (x, y + h)], 0.045, 0.03), rect(x - 0.32, y + h - 0.22, x + 0.32, y + h - 0.15)]
        polys += [ellipse(x + dx, y + h - 0.1, 0.04) for dx in (-0.26, 0.26)]
    for a, b in zip(xs, xs[1:]):
        for dx in (-0.26, 0.26):
            polys.append(ribbon([(a + dx + (b - a) * t, y + h - 0.1 - 0.3 * math.sin(math.pi * t)) for t in [i / 24 for i in range(25)]],
                                0.008))
    cv.add(polys, 'solid', layer)

def semaphore(cv, x, y, h, layer='mid'):
    """Signal post: lattice mast, raised arm with its lamp spectacle, ladder and finial."""
    cv.add([[(x - 0.12, y), (x + 0.12, y), (x + 0.05, y + h), (x - 0.05, y + h)], [(x - 0.09, y + h), (x + 0.09, y + h), (x, y + h + 0.25)]],
           'grid', layer)
    cv.add([[(x + 0.05, y + h - 0.42), (x + 1.0, y + h - 0.12), (x + 1.0, y + h + 0.02), (x + 0.05, y + h - 0.26)],
            ellipse(x - 0.17, y + h - 0.42, 0.13), rect(x - 0.4, y + h * 0.35, x + 0.4, y + h * 0.35 + 0.08)] +
           [ribbon([(x - 0.3, y + 0.05), (x - 0.15, y + h * 0.35)], 0.02)] +
           [ribbon([(x - 0.3 + 0.15 * t, y + 0.05 + (h * 0.35 - 0.05) * t), (x - 0.12 + 0.12 * t, y + 0.05 + (h * 0.35 - 0.05) * t)], 0.015)
            for t in (0.25, 0.5, 0.75)], 'edge', layer)
    cv.carve([ribbon([(x + 0.85, y + h - 0.16), (x + 0.85, y + h - 0.02)], 0.03), ellipse(x - 0.17, y + h - 0.42, 0.06)], layer)

def gunung(cv, x0, x1, base, peak_x, h, seed=1, layer='back'):
    """A lone forested mountain (Gunung Jerai / Kinabalu shapes): long shoulders, a craggy crown."""
    f = noise1(seed, 11)
    pts = [(x0, base - 0.2)]
    for i in range(61):
        t = i / 60
        x = x0 + (x1 - x0) * t
        u = (x - peak_x) / ((peak_x - x0) if x < peak_x else (x1 - peak_x))
        pts.append((x, base + h * (1 - abs(u)) ** 1.6 + 0.12 * h * f(t) * (1 - abs(u))))
    pts.append((x1, base - 0.2))
    return cv.add([pts], 'edge', layer)

def net_rack(cv, x, y, w, h, layer='mid'):
    """Nets hung to dry between two forked poles."""
    cv.add([ribbon([(x, y), (x, y + h)], 0.04), ribbon([(x + w, y), (x + w, y + h)], 0.04),
            ribbon([(x - 0.1, y + h - 0.05), (x + w + 0.1, y + h)], 0.03)], 'solid', layer)
    net = _open([(x + 0.05, y + h - 0.05), (x + w * 0.5, y + h - 0.02), (x + w - 0.05, y + h - 0.02)], 4) + \
        _open([(x + w - 0.08, y + h * 0.35), (x + w * 0.6, y + h * 0.15), (x + w * 0.3, y + h * 0.3), (x + 0.1, y + h * 0.45)], 4)
    cv.add([net], 'grid', layer)
    cv.add([ellipse(x + w * (0.15 + 0.14 * i), y + h * (0.33 - 0.06 * math.sin(i)), 0.05) for i in range(6)], 'solid', layer)

def kid(spec=None, **kw):
    return dict(dict(head='young', costume='baju', scale=0.72), **(spec or {}), **kw)

def ship_repaired(cv, x, y, s, layer='mid', seed=1):
    """The kit ship with its sails whole again (the kit's always tears fore and mizzen)."""
    import wayang_scenes as WS
    keep = WS._sail
    WS._sail = lambda *a, **k: keep(*a, **dict(k, torn=0))
    try:
        ship(cv, x, y, s, layer, seed=seed)
    finally:
        WS._sail = keep

def strip_rail(cv):
    """Travel strip, rail (Kedah to Penang): the line runs on a low ballast bank across the
    rice plain under Gunung Jerai, telegraph wires alongside, a signal arm raised for the train.
    Rail top = LANE, where the ride's wheels land."""
    gunung(cv, -0.8, 10.5, G + 1.2, 4.2, 3.9, seed=5)
    hills(cv, 8.0, 21, G + 1.2, 0.9, seed=6, n=5)
    for i, x in enumerate((9.5, 10.2, 13.9, 16.4, 17.0)):
        palm(cv, x, G + 1.0, 2.3 + 0.4 * (i % 2), lean=0.1 * (-1) ** i, seed=90 + i, layer='back', fronds=7)
    rumah(cv, 12.0, G + 1.05, 0.55, 'back')
    pondok(cv, 15.2, G + 1.05, 0.5, 'back', flip=True)
    padi_row(cv, 0.0, 20.5, G + 1.05, 0.55, seed=91, layer='back', young=False, gap=0.26)
    cloud(cv, 6.6, 7.0, 0.8, 'back', seed=92)
    cloud(cv, 14.2, 7.2, 0.7, 'back', flip=True, seed=93)
    birds(cv, 10.5, 6.5, 4, 0.5, seed=94, layer='back', flip=True)
    telegraph(cv, [-0.6, 4.4, 9.4, 14.4, 19.4], G + 0.25, 4.1)
    raintree(cv, 1.6, G + 0.1, 5.2, seed=95)
    semaphore(cv, 16.6, G + 0.2, 4.2)
    for i, x in enumerate((5.6, 6.1, 12.4)):
        cv.add([leaf(x + 0.04 * k, G + 0.25, 90 + (k - 2) * 12, 0.75, 0.05, bend=0.02 * (k - 2)) for k in range(5)] +
               [ribbon([(x - 0.12, G + 0.45), (x + 0.24, G + 0.45)], 0.03)], 'solid')
    palm(cv, 18.7, G + 0.15, 4.6, lean=-0.12, seed=96)
    palm(cv, 19.6, G + 0.15, 3.6, lean=0.1, seed=97, fronds=8)
    bank = _open([(-0.2, G + 0.02), (3.0, LANE - 0.11), (10.0, LANE - 0.12), (17.0, LANE - 0.11), (20.7, G + 0.02)], 4)
    pid = cv.add([bank + [(20.7, G - 0.1), (-0.2, G - 0.1)]], 'dots')
    cv.add([rect(x - 0.17, LANE - 0.16, x + 0.17, LANE - 0.06) for x in [0.2 + 0.62 * i for i in range(33)]] +
           [rect(-0.2, LANE - 0.07, 20.7, LANE)], 'solid', pid=pid)
    grass(cv, 2.0, 18.5, G + 0.02, 0.3, seed=98, layer='mid', n=30)
    ground(cv, 'earth', seed=99)
    grass(cv, -0.2, 2.6, 0.0, 1.2, seed=100)
    grass(cv, 17.8, 20.7, 0.0, 1.1, seed=101)

def strip_water(cv):
    """Travel strip, water (rivers and coasts): open water to a far shore of nipah and
    mangrove under the hills, a stilt village and a distant sail; boats ride at LANE."""
    hills(cv, -0.5, 21, G + 1.45, 1.5, seed=31, n=4)
    for x in (2.2, 3.4, 4.1, 9.0, 10.6, 11.3, 19.2):
        nipah(cv, x, G + 1.15, 1.2, seed=int(x * 10), layer='back')
    for i, x in enumerate((5.4, 6.6, 7.8)):
        mangrove(cv, x, G + 1.15, 1.6 + 0.3 * (i % 2), seed=40 + i, layer='back')
    rumah(cv, 14.2, G + 1.25, 0.55, 'back')
    rumah(cv, 16.6, G + 1.3, 0.5, 'back', flip=True)
    cv.add([ribbon([(13.0, G + 1.85), (18.3, G + 1.85)], 0.04)] +
           [ribbon([(13.2 + 0.5 * i, G + 1.15), (13.2 + 0.5 * i, G + 1.85)], 0.03) for i in range(11)], 'solid', 'back')
    cv.add([[(12.0, G + 1.3), (12.9, G + 1.3), (12.7, G + 1.12), (12.15, G + 1.12)], ribbon([(12.45, G + 1.3), (12.45, G + 2.3)], 0.02),
            [(12.47, G + 2.25), (12.95, G + 1.45), (12.47, G + 1.42)]], 'solid', 'back')
    cloud(cv, 5.0, 7.1, 0.85, 'back', seed=33)
    cloud(cv, 15.8, 7.0, 0.7, 'back', flip=True, seed=34)
    birds(cv, 9.6, 6.6, 3, 0.55, seed=35, layer='back')
    shore = [(x / 40 * 20.8 - 0.15, G + 1.12 + 0.04 * math.sin(x * 0.9)) for x in range(41)]
    cv.add([shore + [(20.65, G + 1.0), (-0.15, G + 1.0)]], 'solid', 'back')
    rnd = random.Random(36)
    rip = []
    for row, (yy, n, r) in enumerate(((G + 0.95, 8, 0.06), (G + 0.6, 9, 0.075))):
        for i in range(n):
            x = (i + 0.5 + rnd.uniform(-0.25, 0.25) + 0.5 * (row % 2)) * 20.48 / n
            if 2.6 < x < 17.6 or row == 0:
                rip.append(scroll(x - r * 0.4, yy + r, r, r * 0.3, 1.15, a0=0, cw=False,
                                  tail=[(x + r * 2.2, yy - 0.01), (x + r * 1.0, yy + r * 0.3)]))
    cv.add(rip, 'solid')
    mangrove(cv, 0.9, G + 0.3, 3.8, seed=37)
    nipah(cv, 2.6, G + 0.25, 2.2, seed=38, n=8)
    nipah(cv, 18.0, G + 0.25, 2.4, seed=39, n=8)
    nipah(cv, 19.6, G + 0.2, 3.0, seed=41, n=9)
    cv.add([ribbon([(17.0, G + 0.1), (17.0, G + 1.0)], 0.06), ribbon([(17.35, G + 0.1), (17.35, G + 0.85)], 0.05),
            rect(16.75, G + 0.82, 17.6, G + 0.92)], 'solid')
    ground(cv, 'water', seed=42)
    nipah(cv, -0.1, -0.1, 2.0, seed=43, layer='front', n=6)
    nipah(cv, 20.6, -0.1, 1.9, seed=44, layer='front', n=6)

def prologue_shore(cv):
    """The Perlis fishing village at evening: perahu pulled up on the sand, stilt houses and
    nets, villagers spinning gasing; the right of the shore is left open for the sailor."""
    for i, (x, w, h) in enumerate(((1.6, 1.8, 2.3), (4.2, 1.4, 1.7), (7.6, 2.0, 2.1))):
        karst(cv, x, G + 1.0, w, h, seed=110 + i, layer='back', moss=False)
    hills(cv, -0.5, 9.5, G + 0.7, 0.6, seed=111, n=3)
    sea = [(x / 30 * 11.5 + 9.2, G + 1.05 + 0.03 * math.sin(x)) for x in range(31)]
    cv.add([sea + [(20.7, G + 0.6), (9.2, G + 0.6)]], 'edge', 'back')
    for i in range(6):
        wave(cv, 10.5 + i * 1.8, G + 0.75, 1.6, 0.5, flip=i % 2 == 1, layer='back', seed=112 + i, claws=2)
    sun(cv, 16.8, G + 1.35, 0.7, layer='back', rays=16)
    cv.add([[(x - 0.12, G + 1.2), (x + 0.12, G + 1.2), (x, G + 1.75)] for x in (12.6,)] +
           [ribbon([(12.6, G + 1.18), (12.6, G + 1.9)], 0.02)], 'solid', 'back')
    birds(cv, 5.4, 6.7, 4, 0.55, seed=113, layer='back', flip=True)
    cloud(cv, 4.2, 7.2, 0.8, 'back', seed=114)
    cloud(cv, 13.6, 7.0, 0.7, 'back', flip=True, seed=115)
    cv.add([ribbon(arc_pts(6.0, 6.85, 0.36, 70, 290, 24), 0, wf=lambda t: 0.012 + 0.07 * math.sin(math.pi * t)),
            ellipse(6.7, 7.35, 0.05)], 'solid')
    rumah(cv, 2.1, G + 0.45, 0.82)
    net_rack(cv, 4.9, G + 0.05, 1.7, 2.0)
    palm(cv, 4.3, G + 0.1, 4.6, lean=0.14, seed=116)
    gun = hull(cv, 6.4, 10.2, G + 0.06, 0.55, rise=0.8, cls='slits', steep=5, strakes=1)
    for x, sgn in ((10.2, 1), (6.4, -1)):
        t = gun(x)
        cv.add([scroll(x + sgn * 0.02, t + 0.15, 0.13, 0.04, 1.1, a0=0 if sgn > 0 else 180, cw=sgn < 0,
                       tail=[(x, t - 0.15), (x + sgn * 0.05, t)])], 'solid')
    cv.add([ribbon([(6.05, G + 0.05), (6.75, G + 2.2)], 0.03), leaf(6.73, G + 2.15, 72, 0.6, 0.1)], 'solid')
    seated(cv, dict(head='old', beard='tuft', hat='songkok', costume='sarong', pose='stick', item_f='stick'), 7.3,
           gun(7.3) + 0.02, 3.1, layer='mid')
    thrower = dict(head='young', hat='tengkolok', costume='farmer', pose='journey_throw', rod_to=-0.25)
    W.place_figure(cv, thrower, 10.9, G, 3.3)
    g = grip_of(thrower, 10.9, G, 3.3)
    spinning_top(cv, 12.3, G + 0.05, 0.95, seed=117)
    cord(cv, g, (12.15, G + 0.68), sag=0.3, w=0.016)
    W.place_figure(cv, kid(pose='wonder', rod_to=-0.25), 12.95, G, 3.3, flip=True)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kurung', pose='carry', item_f='journey_gasing', rod_to=-0.25),
                   9.35, G, 3.3)
    ground(cv, 'earth', seed=118)
    palm(cv, 0.4, 0.0, 6.6, lean=0.16, seed=119, layer='front', fronds=8)
    grass(cv, -0.2, 3.0, 0.0, 1.2, seed=120)
    grass(cv, 18.4, 20.7, 0.0, 0.9, seed=121)

def end_repair(cv):
    """Word has run ahead: at a Sarawak longhouse jetty the villagers mend the sailor's ship.
    Men on the scaffold hammer new planks, others haul a line to the mast, timber and rope
    are carried down to the water; the right of the bank is left calm for the sailor."""
    hills(cv, -0.5, 21, G + 2.2, 1.6, seed=131, n=4)
    longhouse(cv, 6.0, 20.4, G + 0.95, 1.05)
    for x in (5.0, 5.8):
        palm(cv, x, G + 1.2, 2.6, lean=0.1, seed=int(x * 7), layer='back', fronds=7)
    cloud(cv, 11.0, 7.3, 0.7, 'back', seed=132)
    hornbill(cv, 2.6, 6.7, 1.1)
    ship(cv, 5.3, G + 0.3, 0.62, seed=7)
    water = [(x / 30 * 10.0 - 0.2, G + 0.62 + 0.03 * math.sin(x * 1.3)) for x in range(31)]
    pid = cv.add([water + [(9.8, G - 0.05), (-0.2, G - 0.05)]], 'scales')
    cv.add([scroll(0.6 + 1.0 * i - 0.04, G + 0.72, 0.1, 0.03, 1.15, a0=0, cw=False,
                   tail=[(0.6 + 1.0 * i + 0.22, G + 0.61), (0.6 + 1.0 * i + 0.1, G + 0.65)]) for i in range(9)], 'edge', pid=pid)
    plank = G + 1.5                                     # staging lashed round the stern
    cv.add([ribbon([(px, G + 0.2), (px, G + 3.1)], 0.05) for px in (0.9, 2.1, 3.3)] +
           [ribbon([(0.7, plank), (3.6, plank)], 0.06), ribbon([(0.7, G + 2.85), (3.5, G + 2.85)], 0.035)] +
           [ribbon([(a, G + 0.6), (b, plank - 0.05)], 0.028) for a, b in ((0.9, 2.1), (3.3, 2.1))], 'solid')
    W.place_figure(cv, dict(head='young', hat='journey_cap', costume='farmer', pose='journey_hammer', item_f='journey_mallet',
                            rods=False, cls={'top': 'edge'}), 2.55, plank + 0.06, 2.45)
    W.place_figure(cv, dict(head='old', hat='tanjak', costume='farmer', pose='carry', item_f='rope', rods=False,
                            cls={'top': 'edge'}), 1.3, plank + 0.06, 2.45)
    cv.add([rect(8.4, G + 0.82, 13.2, G + 0.95)] + [ribbon([(px, G - 0.2), (px, G + 0.85)], 0.05) for px in (8.7, 10.2, 11.7, 13.0)],
           'solid')
    mast = (5.3 + 0.25 * 0.62, G + 0.3 + (1.78 + 5.8 * 0.95) * 0.62)
    haul = []
    for i, hx in enumerate((9.1, 10.15, 11.2)):
        sp = dict(head=('refined', 'young', 'old')[i], hat=('songkok', 'caping', 'tengkolok')[i], costume='farmer',
                  pose='journey_haul', rods=False, cls={'top': 'edge'})
        W.place_figure(cv, sp, hx, G + 0.95, 2.7, flip=True)
        haul.append(grip_of(sp, hx, G + 0.95, 2.7, flip=True))
    cv.add([ribbon([mast, haul[0], haul[-1], (12.1, G + 1.05)], 0.016)], 'solid')
    grips = []
    for i, cx in enumerate((11.95, 13.3)):
        sp = dict(head=('young', 'refined')[i], hat=(None, 'songkok')[i], costume='farmer', pose='journey_shoulder',
                  rods=False, cls={'top': 'edge'})
        W.place_figure(cv, sp, cx, G, 2.9, flip=True)
        grips.append(grip_of(sp, cx, G, 2.9, flip=True))
    (ax, ay), (bx, by) = grips
    cv.add([ribbon([(ax - 0.9, ay + 0.06 + (ay - by) * 0.9 / (bx - ax)), (bx + 0.9, by + 0.06 - (ay - by) * 0.9 / (bx - ax))], 0.07)],
           'edge')
    logs = [(16.9 + 0.46 * i, G + 0.2) for i in range(5)] + [(17.13 + 0.46 * i, G + 0.58) for i in range(4)] + \
        [(17.36 + 0.46 * i, G + 0.96) for i in range(2)]
    cv.add([ellipse(lx, ly, 0.22, 0.2) for lx, ly in logs], 'edge')
    cv.carve([ellipse(lx, ly, 0.07, 0.06) for lx, ly in logs], 'mid')
    cv.add_eo([ellipse(15.3, G + 0.16, 0.45, 0.16), ellipse(15.3, G + 0.16, 0.24, 0.07)], 'edge')
    ground(cv, 'earth', seed=133)
    banana(cv, 20.0, 0.2, 4.0, seed=134, layer='front', flip=True)
    grass(cv, -0.2, 2.4, 0.0, 1.0, seed=135)
    grass(cv, 17.6, 20.7, 0.0, 1.0, seed=136)

def end_home(cv):
    """Sailing home at sunrise: the mended ship runs out to sea, the coast falling away
    behind; at the stern rail the sailor lifts a gasing in farewell."""
    for i, (x, w, h) in enumerate(((0.8, 1.4, 1.9), (2.6, 1.1, 1.3))):
        karst(cv, x, G + 0.9, w, h, seed=140 + i, layer='back', moss=False)
    for i, x in enumerate((3.6, 4.2, 4.9)):
        palm(cv, x, G + 0.9, 1.8 + 0.3 * i, lean=0.1, seed=141 + i, layer='back', fronds=7)
    cloud(cv, 6.0, 6.9, 0.8, 'back', seed=144)
    cloud(cv, 16.6, 6.4, 0.75, 'back', flip=True, seed=145)
    sun(cv, 14.8, G + 1.0, 1.05, layer='mid', rays=20)
    horizon = [(x / 40 * 20.8 - 0.15, G + 0.78 + 0.03 * math.sin(x * 1.1)) for x in range(41)]
    cv.add([horizon + [(20.65, G - 0.1), (-0.15, G - 0.1)]], 'scales')
    for i in range(7):
        wave(cv, 0.8 + i * 3.1, G + 0.55, 2.0, 0.45, flip=i % 2 == 1, seed=146 + i, claws=2)
    ship_repaired(cv, 6.6, G + 0.25, 0.72, seed=9)
    deck = G + 0.25 + 2.42 * 0.72                       # forecastle, by the bowsprit
    standing(cv, sailor(pose='journey_show', item_f='journey_gasing'), 9.45, deck, 2.2)
    for x, y, s in ((11.0, 5.4, 0.55), (12.2, 4.9, 0.45), (9.6, 6.1, 0.4)):
        egret(cv, x, y, s, pose='fly')
    wave(cv, 3.0, G - 0.2, 3.4, 1.0, seed=153, claws=3)
    wave(cv, 11.8, G - 0.2, 3.0, 0.9, flip=True, seed=154, claws=3)
    ground(cv, 'water', seed=155)

def end_stay(cv):
    """Staying on: under the village rain tree the sailor shows the children how to wind and
    throw a gasing; one top already hums on the packed earth."""
    hills(cv, -0.5, 21, G + 1.3, 1.0, seed=161, n=4)
    for i, (x, sc) in enumerate(((9.6, 0.55), (12.8, 0.5))):
        rumah(cv, x, G + 1.05, sc, 'back', flip=i % 2 == 1)
    for i, x in enumerate((8.4, 11.6, 14.6)):
        palm(cv, x, G + 1.0, 2.4 + 0.4 * (i % 2), lean=0.1 * (-1) ** i, seed=162 + i, layer='back', fronds=7)
    cloud(cv, 12.4, 7.1, 0.75, 'back', flip=True, seed=165)
    birds(cv, 9.0, 6.6, 3, 0.5, seed=166, layer='back')
    raintree(cv, 1.6, G + 0.05, 6.2, seed=167)
    rumah(cv, 17.0, G + 0.3, 0.82, flip=True)
    palm(cv, 19.6, G + 0.1, 4.2, lean=-0.1, seed=168)
    t = sailor(pose='journey_show', item_f='journey_gasing', rod_to=-0.25)
    W.place_figure(cv, t, 6.4, G, 3.4)
    W.place_figure(cv, kid(pose='carry', item_f='journey_gasing', rod_to=-0.25), 8.4, G, 3.4, flip=True)
    thrower = kid(pose='journey_throw', hat='songkok', rod_to=-0.25)
    W.place_figure(cv, thrower, 10.0, G, 3.4)
    g = grip_of(thrower, 10.0, G, 3.4)
    spinning_top(cv, 11.75, G + 0.05, 0.95, seed=169)
    cord(cv, g, (11.6, G + 0.68), sag=0.28, w=0.016)
    W.place_figure(cv, kid(body='female', head='female', costume='kurung', pose='gesture', rod_to=-0.25), 13.0, G, 3.4, flip=True)
    W.place_figure(cv, kid(pose='wonder', rod_to=-0.25, scale=0.62), 14.3, G, 3.4, flip=True)
    spinning_top(cv, 7.55, G + 0.05, 0.72, seed=170)
    ground(cv, 'earth', seed=171)
    banana(cv, 0.4, 0.2, 4.2, seed=172, layer='front')
    grass(cv, -0.2, 3.0, 0.0, 1.2, seed=173)
    grass(cv, 17.6, 20.7, 0.0, 1.0, seed=174)

# =====================================================================
# registry: what the CLI renders (`journey [names]`, `puppet sailor`)
# =====================================================================

JOURNEY = {
    'prologue': prologue,
    'sailor': dict(SAILOR, pose='wonder', item_b='lantern', feet=FEET),
    'prologue_shore': prologue_shore,
    'strip_road': strip_road,
    'strip_rail': strip_rail,
    'strip_water': strip_water,
    'end_repair': end_repair,
    'end_home': end_home,
    'end_stay': end_stay,
    'ride_perlis': ride_perlis,
    'ride_kedah': ride_kedah,
    'ride_penang': ride_penang,
    'ride_perak': ride_perak,
    'ride_selangor': ride_selangor,
    'ride_nsembilan': ride_nsembilan,
    'ride_melaka': ride_melaka,
    'ride_johor': ride_johor,
    'ride_pahang': ride_pahang,
    'ride_terengganu': ride_terengganu,
    'ride_kelantan': ride_kelantan,
    'ride_sabah': ride_sabah,
}
