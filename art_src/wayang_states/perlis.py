"""Perlis: the template state module (copy it for a new state; file name = story_data id).

A state module must define:
  PUPPET  figure spec of the master (wayang_lib.figure keys)  -> assets/wayang/wayang_<id>.png 1024x1024
  BEATS   {'land': fn, 'people': fn, 'food': fn}, fn(cv) draws on a 2048x820 Canvas
                                                              -> assets/wayang/wayang_<id>_<beat>.png
  ICONS   {'food': builder, 'item': builder}, builder() builds an EEVEE scene and
          returns (camera_location, look_at)                  -> assets/ui/icon_<kind>_<id>.png 256x256
New rig parts go in with W.register(...) at import time (see WAYANG_AUTHORING.md).
"""
from wayang_scenes import *                                    # prop kit, W (wayang_lib), G, WIDE, RIDE, ...
from wayang_scenes import _open, _mat, _lathe, _torus, _tube, _blob, _box   # private kit helpers

# =====================================================================
# beats (2048x820, scene units of 100 px, ground line G)
# =====================================================================

def perlis_land(cv):
    """Calm padi fields at dawn under the Perlis karsts."""
    # back: hazy karst range, a skein of egrets, two clouds
    for i, (x, w, h) in enumerate(((1.2, 2.0, 2.6), (3.6, 1.5, 1.9), (9.0, 2.2, 2.2), (11.6, 1.6, 2.9),
                                   (18.4, 2.4, 2.5), (20.3, 1.6, 1.8))):
        karst(cv, x, G + 0.8, w, h, seed=10 + i, layer='back', moss=False)
    hills(cv, -0.5, 21, G + 0.5, 0.8, seed=3)
    birds(cv, 9.2, 6.4, 4, 0.6, seed=4, layer='back', flip=True)
    cloud(cv, 3.2, 6.7, 0.9, 'back', seed=2)
    cloud(cv, 16.3, 6.9, 0.7, 'back', flip=True, seed=5)
    # mid: the sun lifting over a karst on the left third, hero towers on the right third
    sun(cv, 4.4, 4.5, 0.9)
    karst(cv, 5.6, G + 0.9, 2.1, 3.0, seed=23)
    karst(cv, 2.4, G + 0.9, 1.5, 2.1, seed=24, cave=True)
    karst(cv, 14.2, G + 0.9, 2.8, 5.0, seed=21, cave=True)
    karst(cv, 16.9, G + 0.9, 1.9, 3.5, seed=22)
    palm(cv, 8.4, G + 0.9, 3.1, lean=0.12, seed=31)
    palm(cv, 9.1, G + 0.9, 2.5, lean=-0.16, seed=32, fronds=8)
    pondok(cv, 10.6, G + 0.95, 0.75)
    field(cv, 0.0, 20.5, G + 0.12, h=0.62, rows=3, seed=40)
    egret(cv, 6.3, G + 0.02, 1.45)
    egret(cv, 7.6, G + 0.04, 1.2, flip=True, pose='peck')
    egret(cv, 12.6, G + 0.03, 1.15, flip=True)
    egret(cv, 11.7, 6.0, 0.95, pose='fly', flip=True)
    ground(cv, 'earth', seed=7)
    frame_edges(cv, seed=8, right=None)        # the kit's 7.2-unit edge palm runs into SKIP (top-right)
    palm(cv, 19.6, 0.0, 5.2, lean=-0.2, seed=10, layer='front', fronds=8)

def perlis_people(cv):
    """Farmers working the fields: one winds open the sluice gate, water runs
    out to the plots where a man works the bund and a woman plants seedlings."""
    for i, (x, w, h) in enumerate(((2.5, 2.0, 2.4), (6.5, 1.6, 2.0), (12.2, 2.4, 2.8), (16.0, 1.7, 2.1),
                                   (19.4, 2.2, 2.6))):
        karst(cv, x, G + 0.9, w, h, seed=60 + i, layer='back', moss=False)
    hills(cv, -0.5, 21, G + 0.5, 0.7, seed=6)
    pondok(cv, 9.6, G + 1.0, 0.55, layer='back')
    palm(cv, 8.8, G + 0.9, 2.4, lean=0.1, seed=61, layer='back')
    cloud(cv, 12.6, 6.9, 0.8, 'back', flip=True, seed=7)
    birds(cv, 3.0, 6.6, 3, 0.55, seed=9, layer='back')
    # mid: the gate on its channel, water running right into the plots
    sluice(cv, 7.3, G + 0.05, 1.08)
    water_run(cv, 8.2, 14.8, G + 0.02, 0.5, flow=1, seed=3)
    W.place_figure(cv, dict(head='refined', hat='caping', costume='farmer', pose='crank', scarf=True,
                            rod_to=-0.25), 5.2, G, 3.3)
    field(cv, 12.4, 20.5, G + 0.15, h=0.55, rows=2, seed=44)
    W.place_figure(cv, dict(head='young', hat='songkok', costume='farmer', pose='hoe', item_f='hoe',
                            rod_to=-0.25), 12.6, G + 0.05, 3.2, flip=True)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kurung', pose='plant', item_f='seedlings',
                            rod_to=-0.25), 16.6, G + 0.05, 3.3, flip=True)
    egret(cv, 9.7, G + 0.42, 0.95, flip=True)
    ground(cv, 'earth', seed=17)
    frame_edges(cv, seed=18, left='palm', right='banana')

def perlis_food(cv):
    """A bowl of Laksa Perlis being served: the cook ladles fish broth over the
    noodles, the hearth simmers behind, the ingredients laid out in front."""
    kitchen_back(cv)
    dapur(cv, 15.2, G + 0.05, 1.25)
    steam(cv, 15.0, 4.0, 2.2, cw=False, seed=3)
    stand(cv, 10.6, G + 0.02, 2.0, 1.1)
    rim = bowl(cv, 10.6, G + 1.1, 2.4)
    for i, (dx, hh, cw) in enumerate(((-0.6, 1.9, False), (0.05, 2.2, True), (0.65, 1.8, True))):
        steam(cv, 10.6 + dx, rim + 0.65, hh, cw=cw, seed=10 + i)
    W.place_figure(cv, dict(body='female', hat='tudung', costume='kurung', pose='pour', item_f='ladle',
                            rod_to=-0.25), 6.4, G, 3.55)
    cv.add([ribbon(_open([(8.48, 3.86), (8.75, 3.72), (9.2, 3.55), (9.6, 3.35)]), 0.035, 0.02)], 'solid')
    for sx in (-1, 1):                                  # ingredients, mirrored about the dish
        fish(cv, 10.6 + sx * 6.7, G + 0.35, 1.25, flip=sx > 0, ang=8)
        plate(cv, 10.6 + sx * 2.55, G, 1.3)
    chillies(cv, 7.7, G + 0.05, 1.0)
    limes(cv, 12.85, G + 0.05, 1.0)
    jar(cv, 18.7, G, 0.75, cls='edge')
    for k, lean in enumerate((-0.12, 0.0, 0.14)):
        kantan(cv, 18.62 + 0.08 * k, G + 0.55, 1.8 + 0.25 * (k == 1), lean=lean)
    serai(cv, 2.4, G, 1.9)
    ground(cv, 'earth', seed=27)
    frame_edges(cv, seed=28, left='banana', right='banana')

# =====================================================================
# colour icons (EEVEE, 256x256)
# =====================================================================

def icon_food_laksa(seed=1):
    """Laksa Perlis: thick rice noodles in brown fish gravy, cucumber, onion,
    chilli, mint, torch ginger and half an egg, in the beat's mangkuk."""
    rnd = random.Random(seed)
    w, h = 2.0, 2.0 * BOWL_DEPTH
    outer = [(-x * w, y * h) for x, y in reversed(BOWL_PROFILE)]
    rim = outer[-1]
    inner = [(r - 0.05, z) for r, z in reversed(outer) if z > 0.2 * h]
    prof = [(0.0, 0.0)] + outer + [(rim[0] - 0.025, rim[1] + 0.02)] + inner + [(0.0, inner[-1][1])]
    porcelain = _mat('Porcelain', (0.93, 0.91, 0.86), 0.18, coat=0.4)
    blue = _mat('Blue', (0.08, 0.2, 0.55), 0.3)
    _lathe('Bowl', prof, porcelain, 72)
    _torus('RimLine', (0, 0, rim[1] - 0.06), rim[0] - 0.012, 0.018, blue)
    _torus('Band', (0, 0, 0.55 * h), 0.86, 0.016, blue)
    soup_z = 0.84 * h
    _lathe('Soup', [(0.0, soup_z), (0.9, soup_z)], _mat('Kuah', (0.36, 0.13, 0.03), 0.25, coat=0.3), 64, sharp=0)
    noodle = _mat('Noodle', (0.95, 0.92, 0.82), 0.5)
    for i in range(11):
        a0 = rnd.uniform(0, TAU)
        pts = []
        for k in range(28):
            t = k / 27
            a = a0 + t * rnd.uniform(1.2, 2.2)
            r = 0.15 + 0.6 * abs(math.sin(t * math.pi + i))
            pts.append((r * math.cos(a), r * math.sin(a), soup_z + 0.03 + 0.06 * math.sin(t * 5 + i)))
        _tube('Noodle%d' % i, pts, 0.042, noodle)
    cuc = _mat('Cucumber', (0.62, 0.82, 0.38), 0.45)
    cucs = _mat('CucSkin', (0.12, 0.38, 0.1), 0.45)
    for i in range(10):
        a = rnd.uniform(-1.2, 1.4)
        _box('Cuc%d' % i, (-0.35 + 0.03 * i, -0.15 + 0.05 * (i % 4), soup_z + 0.14 + 0.025 * (i % 3)), (0.55, 0.055, 0.055),
             (0.15 * (i % 2), 0.1, a), cuc if i % 3 else cucs)
    onion = _mat('Onion', (0.62, 0.25, 0.48), 0.35)
    for i in range(4):
        _torus('Onion%d' % i, (0.35 + 0.12 * (i % 2), 0.35 - 0.16 * i, soup_z + 0.1 + 0.02 * i), 0.1, 0.018, onion,
               rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0))
    chili = _mat('Chilli', (0.82, 0.06, 0.04), 0.3)
    for i in range(5):
        _torus('Chilli%d' % i, (-0.5 + 0.15 * i, 0.4 - 0.08 * i, soup_z + 0.1), 0.045, 0.02, chili,
               rot=(rnd.uniform(-0.3, 0.3), 0.2, 0))
    mint = _mat('Mint', (0.12, 0.45, 0.12), 0.5)
    for i in range(6):
        a = TAU * i / 6
        _blob('Mint%d' % i, (0.05 + 0.13 * math.cos(a), -0.05 + 0.1 * math.sin(a), soup_z + 0.2 + 0.03 * (i % 2)),
              (0.13, 0.065, 0.015), (0.4 * math.cos(a), 0.4 * math.sin(a), a), mint)
    kantan = _mat('Kantan', (0.95, 0.38, 0.55), 0.4)
    for i in range(7):
        _box('Kantan%d' % i, (-0.15 + 0.06 * i, 0.5 - 0.03 * i, soup_z + 0.12), (0.32, 0.03, 0.02), (0.1, 0, 0.5 + 0.3 * i), kantan)
    white = _mat('EggWhite', (0.97, 0.96, 0.92), 0.35)
    yolk = _mat('Yolk', (0.98, 0.62, 0.08), 0.35)
    egg = _blob('Egg', (0.48, -0.3, soup_z + 0.12), (0.26, 0.18, 0.14), (0, 0, 0.6), white)
    _blob('Yolk', (0.48, -0.3, soup_z + 0.25), (0.13, 0.1, 0.03), (0, 0, 0.6), yolk)
    return (0, -4.7, 4.1), (0, 0, 0.55)

def icon_item_carved_gasing():
    """Pak Latif's hand-carved top: a faceted merbau gasing (carved, not turned),
    a rope groove at the neck, brass crown inlay, iron paku, and its cord."""
    from mathutils import Euler
    wood = _mat('Wood', (0.34, 0.14, 0.05), 0.4, coat=0.35, grain=(0.16, 0.06, 0.02))
    dark = _mat('Groove', (0.12, 0.06, 0.03), 0.6)
    iron = _mat('Iron', (0.42, 0.42, 0.44), 0.3, metal=1.0)
    brass = _mat('Brass', (0.85, 0.62, 0.22), 0.28, metal=1.0)
    rope = _mat('Rope', (0.62, 0.48, 0.28), 0.75)
    prof = [(0.0, 0.0), (0.06, 0.03), (0.16, 0.1), (0.28, 0.22), (0.38, 0.36), (0.44, 0.5), (0.45, 0.58),
            (0.42, 0.68), (0.34, 0.77), (0.22, 0.84), (0.15, 0.87), (0.15, 0.9), (0.12, 0.94), (0.0, 0.96)]
    parts = [_lathe('Gasing', prof, wood, 12, smooth=False)]
    parts.append(_lathe('Paku', [(0.0, -0.13), (0.04, -0.02), (0.07, 0.02), (0.0, 0.04)], iron, 24, sharp=40))
    parts.append(_lathe('Knob', [(0.0, 0.94), (0.07, 0.95), (0.08, 1.0), (0.05, 1.05), (0.0, 1.06)], wood, 12, smooth=False))
    parts.append(_torus('Inlay', (0, 0, 0.865), 0.17, 0.016, brass))
    for z, r in ((0.28, 0.32), (0.44, 0.432)):
        parts.append(_torus('Groove%.2f' % z, (0, 0, z), r, 0.012, dark, seg=12))
    for k in range(3):                                  # rope coils wound at the neck
        z = 0.62 + 0.045 * k
        parts.append(_torus('Coil%d' % k, (0, 0, z), 0.44 - 0.035 * k + 0.012, 0.022, rope, seg=48))
    pivot = bpy.data.objects.new('Pivot', None)
    bpy.context.scene.collection.objects.link(pivot)
    for ob in parts:
        ob.parent = pivot
    pivot.rotation_euler = Euler((math.radians(-14), math.radians(10), 0.3))
    pivot.location = (0.1, 0, 0.0)
    pivot.scale = (1.7, 1.7, 1.7)
    tail = []
    for k in range(18):                                 # the loose end of the cord trailing away
        t = k / 17
        tail.append((0.62 + 0.9 * t, -0.2 - 0.25 * math.sin(t * 3.0), 0.95 - 1.15 * t + 0.12 * math.sin(t * 7)))
    _tube('Cord', tail, 0.03, rope)
    return (0.4, -4.6, 3.4), (0.3, 0, 0.75)

# =====================================================================
# registry: what the CLI renders for this state
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
# ponytail: same patch as journey.py; drop both once the lib's PUPPET_SHEET['feet'] is 0.03
if not getattr(W.render_puppet_v2, 'feet_aware', False):
    W.render_puppet_v2 = _feet_aware(W.render_puppet_v2)

PUPPET = dict(head='old', beard='tuft', hat='caping', costume='farmer', pose='stick',
              item_f='stick', item_b='sickle', scarf=True, lean=5,
              feet=0.03)          # Pak Latif; feet on row 899 = main.gd's ground line (stage.y * 0.88)
BEATS = {'land': perlis_land, 'people': perlis_people, 'food': perlis_food}
ICONS = {'food': icon_food_laksa, 'item': icon_item_carved_gasing}
