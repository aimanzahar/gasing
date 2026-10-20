# Wayang kulit puppet builder — 2D filled curves with nested hole splines.
# Executed inside Blender 5.x via blender-mcp-pro execute_python.
import bpy, math, os

OUT = 'E:/GodotProject/gasing/assets/wayang'
SRC = 'E:/GodotProject/gasing/art_src'
ORTHO = 1.9
CAMY = 0.75
RES = 1024

# ---------------- shape helpers (return (points, center)) ----------------

def circle(cx, cy, r, n=10):
    pts = [(cx + r * math.cos(2 * math.pi * i / n),
            cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return (pts, (cx, cy))

def diamond(cx, cy, w, h):
    return ([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], (cx, cy))

def slit(cx, cy, L, W, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    hx, hy = ca * L / 2, sa * L / 2
    wx, wy = -sa * W / 2, ca * W / 2
    pts = [(cx - hx + wx, cy - hy + wy), (cx + hx + wx, cy + hy + wy),
           (cx + hx - wx, cy + hy - wy), (cx - hx - wx, cy - hy - wy)]
    return (pts, (cx, cy))

def teardrop(cx, cy, r, ang=0.0, elong=2.1):
    raw = []
    for deg in range(120, 421, 30):  # circle arc, leaves 60deg opening at top
        a = math.radians(deg)
        raw.append((r * math.cos(a), r * math.sin(a)))
    raw.append((0.0, elong * r))     # tip
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in raw]
    return (pts, (cx, cy))

def chaikin(pts, it=1):
    for _ in range(it):
        out = []
        n = len(pts)
        for i in range(n):
            p = pts[i]; q = pts[(i + 1) % n]
            out.append((0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]))
            out.append((0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]))
        pts = out
    return pts

# ---------------- base human figure ----------------

def human_outline(head, item):
    pts = []
    pts += [(-0.030, 0.00), (-0.032, 0.22)]                                    # handle left
    pts += [(-0.10, 0.235), (-0.20, 0.245), (-0.27, 0.26)]                     # hem back
    pts += [(-0.255, 0.33), (-0.225, 0.45), (-0.19, 0.58), (-0.155, 0.70),
            (-0.125, 0.80)]                                                    # skirt back
    pts += [(-0.135, 0.92), (-0.175, 0.82), (-0.21, 0.72), (-0.25, 0.63),
            (-0.30, 0.52), (-0.345, 0.53), (-0.36, 0.59),
            (-0.31, 0.70), (-0.275, 0.79), (-0.225, 0.93), (-0.19, 1.01),
            (-0.15, 1.045)]                                                    # back arm + hand
    pts += [(-0.06, 1.07), (-0.045, 1.13)]                                     # neck back
    pts += [(-0.075, 1.20), (-0.085, 1.28)]                                    # head back
    pts += head                                                                # headdress -> (0.115,1.31)
    pts += [(0.12, 1.27), (0.185, 1.235), (0.145, 1.21), (0.16, 1.19),
            (0.135, 1.18), (0.155, 1.16), (0.14, 1.13), (0.075, 1.10),
            (0.055, 1.06)]                                                     # face profile
    pts += [(0.10, 1.045), (0.14, 1.02)]                                       # front shoulder
    pts += [(0.19, 1.07), (0.30, 1.115), (0.42, 1.20)]                         # arm top edge
    pts += item                                                                # hand+item -> (0.44,1.15)
    pts += [(0.31, 1.05), (0.24, 1.015), (0.155, 0.96)]                        # arm underside
    pts += [(0.13, 0.88), (0.115, 0.80)]                                       # torso front
    pts += [(0.14, 0.70), (0.175, 0.58), (0.21, 0.45), (0.245, 0.33),
            (0.27, 0.27)]                                                      # skirt front
    pts += [(0.24, 0.245), (0.235, 0.225), (0.315, 0.185), (0.14, 0.175),
            (0.135, 0.21), (0.12, 0.24)]                                       # foot
    pts += [(0.032, 0.235), (0.030, 0.22), (0.030, 0.00)]                      # to handle right
    return pts

ROW_STYLES = [('tear', 'circ', 'tear'), ('circ', 'diam', 'circ'), ('diam', 'tear', 'circ')]

def std_holes(variant=0):
    H = []
    H.append(circle(0.05, 1.245, 0.02, 10))                                    # eye
    for x in (-0.05, -0.015, 0.02, 0.055):                                     # headdress band dots
        H.append(circle(x, 1.325, 0.010, 8))
    H.append(circle(-0.015, 1.065, 0.009, 8))                                  # collar
    H.append(circle(0.025, 1.065, 0.009, 8))
    for i in range(5):                                                          # chest sash rings
        t = i / 4.0
        cx = 0.095 + (-0.085 - 0.095) * t
        cy = 0.965 + (0.845 - 0.965) * t
        H.append(circle(cx, cy, 0.020 if i % 2 == 0 else 0.012, 10))
    for i in range(5):                                                          # belt diamonds
        H.append(diamond(-0.08 + i * 0.04, 0.79, 0.030, 0.024))
    rows = [(0.68, 0.10, 5, 0.015), (0.55, 0.14, 7, 0.016), (0.42, 0.17, 7, 0.018)]
    styles = ROW_STYLES[variant % 3]
    for (ry, hw, n, r), st in zip(rows, styles):                                # sarong rows
        for i in range(n):
            x = -hw + 2 * hw * i / (n - 1)
            if st == 'tear':
                H.append(teardrop(x, ry, r, math.pi))
            elif st == 'circ':
                H.append(circle(x, ry, r if i % 2 == 0 else r * 0.65, 10))
            else:
                H.append(diamond(x, ry, r * 1.7, r * 1.5))
    for i in range(9):                                                          # hem diamond chain
        H.append(diamond(-0.20 + i * 0.05, 0.31, 0.026, 0.022))
    H.append(slit(-0.06, 0.485, 0.055, 0.008, math.pi / 2))                     # skirt slits
    H.append(slit(0.06, 0.485, 0.055, 0.008, math.pi / 2))
    for (x, y, r) in [(0.215, 1.043, 0.010), (0.305, 1.082, 0.011), (0.43, 1.175, 0.009)]:
        H.append(circle(x, y, r, 8))                                            # front arm dots
    H.append(circle(-0.20, 0.88, 0.011, 8))                                     # back arm dots
    H.append(circle(-0.27, 0.68, 0.011, 8))
    H.append(circle(0.405, 1.155, 0.007, 8))                                    # wrist bead
    return H

# ---------------- headdresses (end at forehead (0.115,1.31)) ----------------

HEADS = {
 'kelantan': [(-0.09, 1.32), (-0.06, 1.36), (-0.045, 1.55), (0.005, 1.44),
              (0.045, 1.47), (0.08, 1.36), (0.115, 1.31)],
 'penang':   [(-0.085, 1.30), (-0.05, 1.36), (0.0, 1.385), (0.01, 1.39),
              (0.012, 1.425), (0.038, 1.425), (0.04, 1.385), (0.08, 1.355),
              (0.115, 1.31)],
 'melaka':   [(-0.09, 1.31), (-0.13, 1.37), (-0.16, 1.46), (-0.055, 1.415),
              (-0.06, 1.565), (0.01, 1.435), (0.025, 1.60), (0.07, 1.42),
              (0.125, 1.545), (0.115, 1.40), (0.185, 1.435), (0.13, 1.345),
              (0.115, 1.31)],
 'terengganu': [(-0.09, 1.31), (-0.07, 1.37), (0.0, 1.40), (0.055, 1.385),
              (0.075, 1.41), (0.095, 1.375), (0.115, 1.31)],
 'sarawak':  [(-0.09, 1.31), (-0.12, 1.38), (-0.16, 1.50), (-0.13, 1.56),
              (-0.10, 1.47), (-0.045, 1.38), (0.0, 1.40), (0.06, 1.385),
              (0.115, 1.31)],
 'sabah':    [(-0.09, 1.30), (-0.22, 1.33), (-0.05, 1.47), (0.02, 1.50),
              (0.09, 1.47), (0.24, 1.33), (0.115, 1.31)],
 'kl':       [(-0.09, 1.31), (-0.115, 1.36), (-0.095, 1.44), (-0.06, 1.40),
              (-0.05, 1.52), (-0.01, 1.42), (0.0, 1.62), (0.04, 1.42),
              (0.05, 1.50), (0.085, 1.39), (0.10, 1.44), (0.12, 1.35),
              (0.115, 1.31)],
 'dalang':   [(-0.085, 1.30), (-0.055, 1.35), (0.01, 1.375), (0.07, 1.35),
              (0.115, 1.31)],
}

# ---------------- hand items (start after (0.42,1.20), end (0.44,1.15)) ----------------

ITEMS = {
 'kris':   [(0.46, 1.24), (0.50, 1.23), (0.505, 1.30), (0.53, 1.36), (0.51, 1.43),
            (0.545, 1.50), (0.555, 1.42), (0.535, 1.35), (0.56, 1.28), (0.525, 1.22),
            (0.50, 1.17), (0.44, 1.15)],
 'dragon': [(0.46, 1.24), (0.50, 1.245), (0.495, 1.43), (0.47, 1.48), (0.53, 1.51),
            (0.615, 1.48), (0.575, 1.455), (0.615, 1.425), (0.555, 1.41), (0.56, 1.28),
            (0.585, 0.95), (0.585, 0.80), (0.555, 0.78), (0.545, 0.95), (0.53, 1.13),
            (0.50, 1.16), (0.44, 1.15)],
 'bud':    [(0.46, 1.24), (0.50, 1.26), (0.515, 1.33), (0.545, 1.42), (0.578, 1.33),
            (0.55, 1.25), (0.525, 1.20), (0.50, 1.17), (0.44, 1.15)],
 'oar':    [(0.46, 1.24), (0.505, 1.28), (0.525, 1.37), (0.505, 1.43), (0.545, 1.55),
            (0.60, 1.585), (0.65, 1.55), (0.655, 1.47), (0.61, 1.40), (0.585, 1.33),
            (0.615, 1.05), (0.64, 0.88), (0.61, 0.86), (0.578, 1.02), (0.545, 1.19),
            (0.50, 1.17), (0.44, 1.15)],
 'shield': [(0.47, 1.28), (0.55, 1.31), (0.63, 1.28), (0.68, 1.18), (0.63, 1.08),
            (0.55, 1.05), (0.47, 1.08), (0.445, 1.13), (0.44, 1.15)],
 'paddy':  [(0.46, 1.24), (0.50, 1.25), (0.505, 1.38), (0.53, 1.44), (0.585, 1.475),
            (0.64, 1.47), (0.675, 1.44), (0.655, 1.42), (0.60, 1.44), (0.55, 1.415),
            (0.535, 1.355), (0.545, 1.22), (0.558, 0.98), (0.572, 0.90), (0.542, 0.885),
            (0.525, 0.98), (0.515, 1.15), (0.50, 1.16), (0.44, 1.15)],
 'flag':   [(0.46, 1.24), (0.495, 1.25), (0.485, 1.53), (0.68, 1.50), (0.685, 1.41),
            (0.515, 1.435), (0.52, 1.26), (0.53, 1.06), (0.505, 1.05), (0.49, 1.16),
            (0.44, 1.15)],
 'fan':    [(0.46, 1.24), (0.435, 1.40), (0.505, 1.40), (0.57, 1.373), (0.623, 1.329),
            (0.658, 1.268), (0.52, 1.19), (0.50, 1.17), (0.44, 1.15)],
}

# ---------------- per-character extra holes ----------------

def _sarawak_ring():
    H = []
    for k in range(8):
        a = k * math.pi / 4
        H.append(circle(0.565 + 0.075 * math.cos(a), 1.18 + 0.075 * math.sin(a), 0.012, 8))
    H.append(circle(0.565, 1.18, 0.018, 10))
    H.append(slit(-0.112, 1.445, 0.05, 0.008, 1.25))   # plume slit
    return H

def _melaka_eyes():
    H = [circle(x, y, r, 8) for x, y, r in
         [(-0.1296, 1.4296, 0.011), (-0.043, 1.502, 0.011), (0.0318, 1.522, 0.011),
          (0.1104, 1.484, 0.011), (0.157, 1.407, 0.010)]]
    H.append(teardrop(0.5465, 1.325, 0.011, 0.0))       # bud hole
    return H

EXTRAS = {
 'kelantan': lambda: [slit(-0.03, 1.42, 0.07, 0.008, 1.35),
                      slit(0.028, 1.40, 0.05, 0.008, 1.2)],
 'penang':   lambda: [circle(0.545, 1.465, 0.009, 8), circle(0.565, 0.95, 0.007, 8),
                      circle(0.567, 0.87, 0.007, 8)],
 'melaka':   _melaka_eyes,
 'terengganu': lambda: [slit(0.578, 1.475, 0.10, 0.013, 1.15)],
 'sarawak':  _sarawak_ring,
 'sabah':    lambda: [slit(-0.16, 1.345, 0.05, 0.008, 0.69),
                      slit(-0.06, 1.39, 0.06, 0.008, 0.72),
                      slit(0.06, 1.39, 0.06, 0.008, -0.70),
                      slit(0.16, 1.36, 0.05, 0.008, -0.75)],
 'kl':       lambda: [circle(-0.086, 1.385, 0.007, 8), circle(-0.038, 1.44, 0.009, 8),
                      circle(0.010, 1.465, 0.0075, 8), circle(0.055, 1.43, 0.008, 8),
                      circle(0.095, 1.375, 0.007, 8),
                      slit(0.593, 1.487, 0.10, 0.008, -0.15),
                      slit(0.596, 1.452, 0.10, 0.008, -0.15)],
 'dalang':   lambda: [slit(0.494, 1.3295, 0.085, 0.007, 1.484),
                      slit(0.5455, 1.3132, 0.085, 0.007, 1.047),
                      slit(0.5854, 1.2767, 0.085, 0.007, 0.611)],
}

CHAR_ITEM = {'kelantan': 'kris', 'penang': 'dragon', 'melaka': 'bud',
             'terengganu': 'oar', 'sarawak': 'shield', 'sabah': 'paddy',
             'kl': 'flag', 'dalang': 'fan'}
CHAR_VARIANT = {'kelantan': 0, 'penang': 1, 'melaka': 2, 'terengganu': 0,
                'sarawak': 1, 'sabah': 2, 'kl': 0, 'dalang': 1}

def human(pid):
    outline = human_outline(HEADS[pid], ITEMS[CHAR_ITEM[pid]])
    holes = std_holes(CHAR_VARIANT[pid]) + EXTRAS[pid]()
    return outline, holes

# ---------------- gunungan ----------------

def gunungan():
    R = [(0.095, 1.52), (0.16, 1.40), (0.225, 1.26), (0.285, 1.10), (0.325, 0.93),
         (0.35, 0.75), (0.35, 0.58), (0.325, 0.46), (0.30, 0.40), (0.43, 0.335),
         (0.46, 0.26), (0.34, 0.215), (0.16, 0.195), (0.04, 0.19), (0.04, 0.0)]
    outline = [(0.0, 1.62)] + R + [(-x, y) for x, y in reversed(R)]
    H = []
    trunk = [(0.014, 0.42), (0.02, 0.55), (0.012, 0.70), (0.02, 0.85), (0.012, 1.0),
             (0.0, 1.08), (-0.012, 1.0), (-0.02, 0.85), (-0.012, 0.70), (-0.02, 0.55),
             (-0.014, 0.42)]
    H.append((trunk, (0.0, 0.70)))
    for x, y, a, l in [(0.09, 0.66, 0.6, 0.11), (0.10, 0.83, 0.5, 0.11),
                       (0.085, 0.99, 0.7, 0.10)]:
        H.append(slit(x, y, l, 0.012, a))
        H.append(slit(-x, y, l, 0.012, math.pi - a))
    for x, y in [(0.16, 0.72), (0.17, 0.89), (0.15, 1.05)]:
        H.append(circle(x, y, 0.016, 8))
        H.append(circle(-x, y, 0.016, 8))
    H.append(teardrop(0.0, 1.30, 0.02, 0.0))
    H.append(teardrop(0.055, 1.22, 0.017, -0.35))
    H.append(teardrop(-0.055, 1.22, 0.017, 0.35))
    H.append(circle(0.045, 1.40, 0.013, 8))
    H.append(circle(-0.045, 1.40, 0.013, 8))
    H.append(circle(0.0, 1.475, 0.012, 8))
    for x, y in [(0.295, 0.60), (0.295, 0.75), (0.27, 0.93), (0.23, 1.10),
                 (0.17, 1.26), (0.105, 1.40)]:
        H.append(teardrop(x, y, 0.014, -0.5))
        H.append(teardrop(-x, y, 0.014, 0.5))
    H.append(circle(0.38, 0.29, 0.016, 8))
    H.append(circle(-0.38, 0.29, 0.016, 8))
    for i in range(9):
        H.append(diamond(-0.24 + i * 0.06, 0.25, 0.03, 0.02))
    H.append(circle(0.06, 0.35, 0.017, 8))
    H.append(circle(-0.06, 0.35, 0.017, 8))
    H.append(circle(0.0, 0.30, 0.013, 8))
    return outline, H

PUPPETS = {pid: (lambda p=pid: human(p)) for pid in HEADS}
PUPPETS['gunungan'] = gunungan

# ---------------- blender scene plumbing ----------------

def wipe():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for _ in range(3):
        bpy.data.orphans_purge(do_recursive=True)

def add_spline(cu, pts):
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        sp.points[i].co = (x, y, 0.0, 1.0)
    sp.use_cyclic_u = True

def black_mat():
    mat = bpy.data.materials.get('WayangBlack')
    if mat is None:
        mat = bpy.data.materials.new('WayangBlack')
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (0, 0, 0, 1)
        em.inputs['Strength'].default_value = 1.0
        nt.links.new(em.outputs[0], out.inputs['Surface'])
    return mat

def make_cam():
    cd = bpy.data.cameras.new('WayangCam')
    cd.type = 'ORTHO'
    cd.ortho_scale = ORTHO
    cam = bpy.data.objects.new('WayangCam', cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0.0, CAMY, 5.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.scene.camera = cam
    return cam

def setup_render(sc, path):
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.film_transparent = True
    sc.render.resolution_x = RES
    sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.use_freestyle = False
    sc.use_nodes = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    try:
        sc.view_settings.view_transform = 'Standard'
    except Exception:
        pass
    wd = bpy.data.worlds.get('WayangWorld')
    if wd is None:
        wd = bpy.data.worlds.new('WayangWorld')
    wd.use_nodes = True
    bg = wd.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (0, 0, 0, 1)
        bg.inputs[1].default_value = 0.0
    sc.world = wd
    sc.render.filepath = path

def verify(path, holes):
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    a = arr[3::4]
    cov = float((a > 0.5).mean())
    grid = a.reshape(h, w)
    okc = tot = 0
    for _, (cx, cy) in holes:
        px = int((cx / ORTHO + 0.5) * w)
        py = int(((cy - CAMY) / ORTHO + 0.5) * h)
        if 0 <= px < w and 0 <= py < h:
            tot += 1
            if grid[py, px] < 0.5:
                okc += 1
    bpy.data.images.remove(img)
    return {'size': [w, h], 'coverage_pct': round(cov * 100, 1),
            'holes_transparent': '%d/%d' % (okc, tot)}

def build_and_render(pid):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SRC, exist_ok=True)
    wipe()
    outline, holes = PUPPETS[pid]()
    cu = bpy.data.curves.new('Wayang_' + pid, 'CURVE')
    cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'
    add_spline(cu, chaikin(outline, 1))
    for pts, _c in holes:
        add_spline(cu, pts)
    ob = bpy.data.objects.new('Wayang_' + pid, cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(black_mat())
    make_cam()
    sc = bpy.context.scene
    path = OUT + '/wayang_%s.png' % pid
    setup_render(sc, path)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=SRC + '/wayang_%s.blend' % pid,
                                check_existing=False)
    rep = verify(path, holes)
    rep['id'] = pid
    rep['splines'] = len(cu.splines)
    rep['holes'] = len(holes)
    return rep

# =====================================================================
# v2 (story rebuild): vector kit, layered canvas, numpy perforation and an
# articulated puppet rig. Everything is drawn as flat 2D curves in canvas
# units, rendered by Workbench as ID colours (R = lace class, G/B = part id),
# and the tatahan (carved lace) is cut afterwards in numpy, so every part gets
# a perforated rim that follows its own outline. Driven headless by
# art_src/wayang_scenes.py:  blender -b --factory-startup -P art_src/wayang_scenes.py -- <cmd> [ids]
# =====================================================================
import random
import tempfile
import numpy as np

TAU = 2 * math.pi
TMP = os.path.join(tempfile.gettempdir(), 'wayang_v2')

# ---------------- vector kit (everything is a list of (x, y)) ----------------

def catmull(ctrl, closed=True, seg=8):
    """Catmull-Rom curve through the control points."""
    n = len(ctrl)
    out = []
    for i in range(n if closed else n - 1):
        p0 = ctrl[(i - 1) % n] if (closed or i > 0) else ctrl[0]
        p1, p2 = ctrl[i], ctrl[(i + 1) % n]
        p3 = ctrl[(i + 2) % n] if (closed or i + 2 < n) else ctrl[-1]
        for k in range(seg):
            t = k / seg
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (p2[j] - p0[j]) * t
                                    + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (3 * p1[j] - p0[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(tuple(ctrl[-1]))
    return out

def xf(pts, dx=0.0, dy=0.0, s=1.0, rot=0.0, sy=None, flip=False, ox=0.0, oy=0.0):
    """Scale and rotate (deg, ccw) about (ox, oy), mirror x if flip, then move by (dx, dy)."""
    sy = s if sy is None else sy
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for x, y in pts:
        x, y = (x - ox) * s, (y - oy) * sy
        x, y = x * c - y * sn, x * sn + y * c
        out.append(((-x if flip else x) + ox + dx, y + oy + dy))
    return out

def ellipse(cx, cy, rx, ry=None, n=40, rot=0.0):
    ry = rx if ry is None else ry
    return xf([(rx * math.cos(TAU * i / n), ry * math.sin(TAU * i / n)) for i in range(n)],
              cx, cy, rot=rot)

def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def ribbon(path, w0, w1=None, wf=None):
    """Closed outline of a stroke along path; half-width w0 -> w1 (or wf(t), t in 0..1)."""
    n = len(path)
    if n < 2:
        return []
    acc = [0.0]
    for i in range(1, n):
        acc.append(acc[-1] + math.dist(path[i - 1], path[i]))
    tot = acc[-1] or 1.0
    L, R = [], []
    for i, p in enumerate(path):
        a, b = path[max(i - 1, 0)], path[min(i + 1, n - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1e-9
        nx, ny = -ty / ln, tx / ln
        t = acc[i] / tot
        w = wf(t) if wf else (w0 if w1 is None else w0 + (w1 - w0) * t)
        L.append((p[0] + nx * w, p[1] + ny * w))
        R.append((p[0] - nx * w, p[1] - ny * w))
    if math.dist(L[-1], R[-1]) < 1e-6:
        R.pop()
    if R and math.dist(L[0], R[0]) < 1e-6:
        R = R[1:]
    return L + R[::-1]

def spiral(cx, cy, r, turns=1.25, a0=90.0, cw=True, end=0.15, n=None):
    """Spiral centreline from radius r at angle a0 (deg) winding inward to r*end."""
    n = n or max(24, int(56 * turns))
    sgn = -1 if cw else 1
    out = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0) + sgn * TAU * turns * t
        rr = r * (1 - (1 - end) * t)
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return out

def scroll(cx, cy, r, w, turns=1.25, a0=90.0, cw=True, tail=None, wt=None):
    """Awan-larat curl: optional tail path leading into a tapering spiral band."""
    sp = spiral(cx, cy, r, turns, a0, cw)
    path = (list(tail) + sp[1:]) if tail else sp
    nt = len(tail) if tail else 0
    tot = len(path) - 1
    wt = w * 0.5 if wt is None else wt
    def wf(t):
        i = t * tot
        if i < nt:
            return wt + (w - wt) * (i / max(nt, 1))
        u = (i - nt) / max(tot - nt, 1)
        return w * (1 - u) ** 0.9 + 0.12 * w
    return ribbon(path, 0, wf=wf)

def leaf(x, y, ang, length, width, bend=0.0, n=12, wide_at=0.4):
    """Pointed leaf from its base (x, y) along ang (deg); bend curls the midrib."""
    L, R = [], []
    p = math.log(0.5) / math.log(wide_at)
    for i in range(n + 1):
        t = i / n
        w = width * math.sin(math.pi * t ** p) * (1 - 0.15 * t)
        c = bend * t * t
        L.append((t * length, c + w))
        R.append((t * length, c - w))
    return xf(L + R[::-1][1:-1], x, y, rot=ang)

def noise1(seed, freq=6):
    """Smooth deterministic 1D value noise f(t) in -1..1 for t in 0..1."""
    rnd = random.Random(seed)
    v = [rnd.uniform(-1, 1) for _ in range(freq + 3)]
    def f(t):
        u = max(0.0, min(t, 1.0)) * freq
        i = min(int(u), freq)
        fr = u - i
        s = fr * fr * (3 - 2 * fr)
        return v[i] * (1 - s) + v[i + 1] * s
    return f

def arc_pts(cx, cy, r, a0, a1, n=24, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

# ---------------- perforation (tatahan) ----------------
# Classes cut different patterns. Sizes are pixels at the 2x supersampled
# render for k=1 (scene scale); Canvas.k scales them (puppet sheets use more).
# rows: contour-following rows (shape, depth from the part's edge, size, spacing)
# fill: interior lattice (shape, start depth, cell w, cell h, size) or None
CLS = ['none', 'solid', 'edge', 'dots', 'lace', 'scales', 'slits', 'grid', 'flower', 'rays']
_ROW = ('dot', 7.5, 3.2, 14)
PERF = {
    'solid':  ((), None),
    'edge':   ((_ROW,), None),
    'dots':   ((_ROW,), ('dot', 21, 21, 18, 3.6)),
    'lace':   ((_ROW, ('tear', 24, 4.4, 16)), ('dot', 38, 17, 15, 3.4)),
    'scales': ((_ROW,), ('scale', 19, 26, 17, 9.5)),
    'slits':  ((_ROW,), ('slit', 18, 30, 14, 8.5)),
    'grid':   ((_ROW,), ('diamond', 18, 20, 20, 5.6)),
    'flower': ((_ROW, ('tear', 24, 4.4, 16)), ('rosette', 38, 30, 26, 3.4)),
    'rays':   ((_ROW, ('slit', 22, 8, 13)), None),
}
N4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
N8 = N4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))

def part_distance(pid, dmax):
    """Octagonal distance (px) of each pixel to its own part's visible outline.
    A neighbour counts as outline if it is empty or belongs to a part BEHIND
    (lower id), so the part in front carries the lace along a shared seam."""
    H, W = pid.shape
    P = np.pad(pid, 1)
    c = P[1:-1, 1:-1]
    mask = c > 0
    edge = np.zeros((H, W), bool)
    same = {}
    for dy, dx in N8:
        n = P[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx]
        if (dy, dx) in N4:
            edge |= n < c
        same[(dy, dx)] = n == c
    edge &= mask
    d = np.full((H, W), 255, np.uint8)
    d[edge] = 0
    reached = edge | ~mask
    F = edge
    for k in range(1, dmax + 1):
        Fp = np.pad(F, 1)
        new = np.zeros((H, W), bool)
        for dy, dx in (N4 if k % 2 else N8):
            new |= Fp[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx] & same[(dy, dx)]
        new &= ~reached
        if not new.any():
            break
        d[new] = k
        reached |= new
        F = new
    return d

def _greedy(ys, xs, sp):
    """Raster-order Poisson thinning: keep points at least sp apart."""
    s2 = sp * sp
    grid = {}
    keep = []
    for y, x in zip(ys.tolist(), xs.tolist()):
        gx, gy = int(x // sp), int(y // sp)
        ok = True
        for ix in (gx - 1, gx, gx + 1):
            for iy in (gy - 1, gy, gy + 1):
                for px, py in grid.get((ix, iy), ()):
                    if (px - x) ** 2 + (py - y) ** 2 < s2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            keep.append((y, x))
            grid.setdefault((gx, gy), []).append((x, y))
    return keep

def _sd_uneven(px, py, r1, r2, h):
    """Signed distance to a capsule along +py: radius r1 at 0, r2 at h."""
    px = np.abs(px)
    b = (r1 - r2) / h
    a = math.sqrt(max(1 - b * b, 1e-6))
    k = -b * px + a * py
    d1 = np.sqrt(px * px + py * py) - r1
    d2 = np.sqrt(px * px + (py - h) ** 2) - r2
    d3 = a * px + b * py - r1
    return np.where(k < 0, d1, np.where(k > a * h, d2, d3))

def _row_holes(hole, d, cls, pid, code, row, k, avoid):
    shape, depth, size, sp = row
    depth, size, sp = depth * k, size * k, sp * k
    cand = (cls == code) & (d == int(round(depth)))
    if avoid is not None:
        cand &= ~avoid
    ys, xs = np.nonzero(cand)
    H, W = d.shape
    df = np.minimum(d, 60).astype(np.float32)
    R = int(size * 3.0) + 3
    for y, x in _greedy(ys, xs, sp):
        gy = df[min(y + 2, H - 1), x] - df[max(y - 2, 0), x]
        gx = df[y, min(x + 2, W - 1)] - df[y, max(x - 2, 0)]
        ln = math.hypot(gx, gy) or 1.0
        nx, ny = gx / ln, gy / ln                      # inward normal (towards deeper pixels)
        y0, y1, x0, x1 = max(y - R, 0), min(y + R + 1, H), max(x - R, 0), min(x + R + 1, W)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        yy -= y
        xx -= x
        if shape == 'dot':
            sd = np.sqrt(xx * xx + yy * yy) - size
        elif shape == 'tear':                          # round end here, tip pointing at the edge
            sd = _sd_uneven(xx * ny - yy * nx, -(xx * nx + yy * ny), size, size * 0.18, size * 2.1)
        else:                                          # 'slit' across the rim
            sd = _sd_uneven(xx * ny - yy * nx, -(xx * nx + yy * ny) + size, size * 0.3, size * 0.3, size * 2)
        cov = np.clip(0.5 - sd, 0, 1) * (pid[y0:y1, x0:x1] == pid[y, x])
        np.maximum(hole[y0:y1, x0:x1], cov, out=hole[y0:y1, x0:x1])

def _fill_holes(hole, d, cls, pid, code, fill, k, avoid):
    shape, start, sx, sy, size = fill
    start, sx, sy, size = start * k, sx * k, sy * k, size * k
    H, W = d.shape
    sel = cls == code
    if not sel.any():
        return
    yy, xx = np.nonzero(sel)
    y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
    Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    j = np.floor(Y / sy)
    off = (j % 2) * sx * 0.5
    i = np.floor((X - off) / sx)
    cx, cy = (i + 0.5) * sx + off, (j + 0.5) * sy
    u, v = X - cx, Y - cy
    if shape == 'dot':
        sd = np.sqrt(u * u + v * v) - size
    elif shape == 'diamond':
        sd = (np.abs(u) + np.abs(v)) * 0.7071 - size * 0.75
    elif shape == 'slit':
        sd = np.sqrt(np.maximum(np.abs(u) - size, 0) ** 2 + v * v) - size * 0.3
    elif shape == 'scale':                             # arch: disc minus the disc below it
        c1 = np.sqrt(u * u + v * v) - size
        c2 = np.sqrt(u * u + (v - size * 0.55) ** 2) - size * 0.95
        sd = np.maximum(c1, -c2)
    else:                                              # 'rosette': centre dot ringed by 4 petals
        sd = np.sqrt(u * u + v * v) - size
        for ang in (45, 135, 225, 315):
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            sd = np.minimum(sd, np.sqrt((u - ca * size * 2.4) ** 2 + (v - sa * size * 2.4) ** 2) - size * 0.62)
    ci = np.clip(cy.astype(np.int32), 0, H - 1)
    cj = np.clip(cx.astype(np.int32), 0, W - 1)
    gate = (cls[ci, cj] == code) & (pid[ci, cj] == pid[y0:y1, x0:x1]) & (d[ci, cj] >= start + size)
    if avoid is not None:
        gate &= ~avoid[ci, cj]
    cov = np.clip(0.5 - sd, 0, 1) * gate
    np.maximum(hole[y0:y1, x0:x1], cov, out=hole[y0:y1, x0:x1])

def perforate(cls, pid, k=1.0, avoid=None):
    """Hole coverage (0..1) for an ID render: contour lace rows plus class lattices."""
    hole = np.zeros(pid.shape, np.float32)
    rows = np.nonzero(pid.any(1))[0]
    cols = np.nonzero(pid.any(0))[0]
    if not len(rows):
        return hole
    y0, y1 = max(rows[0] - 2, 0), rows[-1] + 3
    x0, x1 = max(cols[0] - 2, 0), cols[-1] + 3
    P, C = pid[y0:y1, x0:x1], cls[y0:y1, x0:x1]
    A = None if avoid is None else avoid[y0:y1, x0:x1]
    need = 0.0
    for rws, fill in PERF.values():
        for r in rws:
            need = max(need, r[1] + r[2] * 2.5)
        if fill:
            need = max(need, fill[1] + fill[4])
    d = part_distance(P, min(int(need * k) + 4, 250))
    h = hole[y0:y1, x0:x1]
    for code in np.unique(C):
        if code == 0 or code >= len(CLS):
            continue
        rws, fill = PERF[CLS[code]]
        for row in rws:
            _row_holes(h, d, C, P, code, row, k, A)
        if fill:
            _fill_holes(h, d, C, P, code, fill, k, A)
    return hole

def box_blur(a, r, passes=2):
    for _ in range(passes):
        for ax in (0, 1):
            pad = [(0, 0), (0, 0)]
            pad[ax] = (r + 1, r)
            c = np.cumsum(np.pad(a, pad, mode='edge'), axis=ax, dtype=np.float64)
            n = 2 * r + 1
            a = (c[n:] - c[:-n]) / n if ax == 0 else (c[:, n:] - c[:, :-n]) / n
    return a.astype(np.float32)

# ---------------- layered canvas ----------------

class Canvas:
    """Parts in canvas units; later parts sit in front. Layers: 'back' (blurred,
    BACK_ALPHA), 'mid' (perforated), 'front' (perforated framing)."""
    LAYERS = ('back', 'mid', 'front')
    BACK_ALPHA = 0.45
    BACK_BLUR = 7          # px at 2x

    def __init__(self, w, h, view_w, cx=None, cy=None, k=1.0, ss=2):
        self.w, self.h, self.view_w, self.k, self.ss = w, h, view_w, k, ss
        self.view_h = view_w * h / w
        self.cx = view_w / 2 if cx is None else cx
        self.cy = self.view_h / 2 if cy is None else cy
        self.parts = []      # (layer, pid, cls, rings)
        self.carves = []     # (layer, ring)
        self.pid = 0

    def add(self, polys, cls='lace', layer='mid', pid=None):
        """Union of simple polygons as one part (one lace outline). Returns its id."""
        if pid is None:
            self.pid += 1
            pid = self.pid
        for p in polys:
            if p and len(p) >= 3:
                self.parts.append((layer, pid, cls, [p]))
        return pid

    def add_eo(self, rings, cls='lace', layer='mid', pid=None):
        """One even-odd part: an outer ring plus openings the lace will follow."""
        if pid is None:
            self.pid += 1
            pid = self.pid
        self.parts.append((layer, pid, cls, [r for r in rings if len(r) >= 3]))
        return pid

    def carve(self, polys, layer='mid'):
        """Decorative cuts applied after the lace (no rim of their own)."""
        for p in polys:
            if p and len(p) >= 3:
                self.carves.append((layer, p))

    def render(self):
        """Returns the composited alpha (h, w) float32, 0..1."""
        sc = _v2_scene(self)
        ss = self.ss
        cols = {}
        for L in self.LAYERS:
            for kind in ('p', 'c'):
                co = bpy.data.collections.new('wy_%s_%s' % (L, kind))
                sc.collection.children.link(co)
                cols[(L, kind)] = co
        for i, (L, pid, cls, rings) in enumerate(self.parts):
            col = (CLS.index(cls) / 255.0, (pid % 256) / 255.0, (pid // 256) / 255.0, 1.0)
            _v2_curve('p%d' % i, rings, col, cols[(L, 'p')], pid * 1e-3)
        for i, (L, ring) in enumerate(self.carves):
            _v2_curve('c%d' % i, [ring], (1, 1, 1, 1), cols[(L, 'c')], 0.0)
        out = np.zeros((self.h * ss, self.w * ss), np.float32)
        for L in self.LAYERS:
            if not any(p[0] == L for p in self.parts):
                continue
            for key, co in cols.items():
                co.hide_render = key != (L, 'p')
            a = _v2_grab(sc, 'OFF') if L != 'back' else None
            alpha = _v2_grab(sc, '16')[..., 3]
            carve = None
            if any(c[0] == L for c in self.carves):
                for key, co in cols.items():
                    co.hide_render = key != (L, 'c')
                carve = _v2_grab(sc, '16')[..., 3]
                alpha = alpha * (1 - carve)
            if L == 'back':
                alpha = box_blur(alpha, self.BACK_BLUR) * self.BACK_ALPHA
            else:
                cls = np.rint(a[..., 0] * 255).astype(np.uint8)
                pid = (np.rint(a[..., 1] * 255) + 256 * np.rint(a[..., 2] * 255)).astype(np.uint16)
                avoid = None
                if carve is not None:
                    avoid = box_blur(carve, int(5 * self.k), 1) > 0.02
                alpha = alpha * (1 - perforate(cls, pid, self.k, avoid))
            out = 1 - (1 - out) * (1 - alpha)
        return out.reshape(self.h, ss, self.w, ss).mean((1, 3))

def _v2_scene(cv):
    wipe()
    for co in list(bpy.data.collections):
        bpy.data.collections.remove(co)
    sc = bpy.context.scene
    cd = bpy.data.cameras.new('WyCam')
    cd.type = 'ORTHO'
    cd.sensor_fit = 'HORIZONTAL'
    cd.ortho_scale = cv.view_w
    cd.clip_start, cd.clip_end = 0.1, 500
    cam = bpy.data.objects.new('WyCam', cd)
    sc.collection.objects.link(cam)
    cam.location = (cv.cx, -100.0, cv.cy)
    cam.rotation_euler = (math.pi / 2, 0.0, 0.0)
    sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'FLAT'
    sh.color_type = 'OBJECT'
    for a in ('show_object_outline', 'show_cavity', 'show_shadows', 'show_specular_highlight', 'show_xray'):
        setattr(sh, a, False)
    sc.render.film_transparent = True
    sc.render.dither_intensity = 0.0
    sc.view_settings.view_transform = 'Raw'
    sc.render.resolution_x = cv.w * cv.ss
    sc.render.resolution_y = cv.h * cv.ss
    sc.render.resolution_percentage = 100
    st = sc.render.image_settings
    st.file_format, st.color_mode, st.color_depth, st.compression = 'PNG', 'RGBA', '8', 0
    return sc

def _v2_curve(name, rings, color, coll, depth):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'
    for r in rings:
        add_spline(cu, r)
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    ob.rotation_euler = (math.pi / 2, 0.0, 0.0)
    ob.location = (0.0, -depth, 0.0)
    ob.color = color

def _v2_grab(sc, aa):
    os.makedirs(TMP, exist_ok=True)
    path = os.path.join(TMP, 'pass_%d.png' % os.getpid())
    sc.display.render_aa = aa
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    os.remove(path)
    return px.reshape(h, w, 4)[::-1]

def save_alpha_png(alpha, path, levels=32):
    """Black silhouette PNG: 8-bit indexed, an all-black palette whose tRNS holds
    `levels`+1 alpha steps. Godot decodes it as RGBA8 (RGB = 0); it is ~55%
    smaller than RGBA at max zlib. Filter 'none' beats adaptive filters here."""
    import struct, zlib
    h, w = alpha.shape
    raw = np.zeros((h, w + 1), np.uint8)
    raw[:, 1:] = np.rint(np.clip(alpha, 0, 1) * levels)
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 3, 0, 0, 0))
           + chunk(b'PLTE', bytes(3 * (levels + 1)))
           + chunk(b'tRNS', bytes(round(i * 255 / levels) for i in range(levels + 1)))
           + chunk(b'IDAT', zlib.compress(raw.tobytes(), 9)) + chunk(b'IEND', b''))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)

def save_rgba_png(rgba, path):
    """Colour RGBA8 PNG (icons): tries filters none/sub/up/paeth for the whole
    image at zlib 9 and keeps the smallest."""
    import struct, zlib
    h, w, _ = rgba.shape
    px = rgba.astype(np.int16)
    left = np.zeros_like(px)
    left[:, 1:] = px[:, :-1]
    up = np.zeros_like(px)
    up[1:] = px[:-1]
    ul = np.zeros_like(px)
    ul[1:, 1:] = px[:-1, :-1]
    pa, pb, pc = np.abs(up - ul), np.abs(left - ul), np.abs(left + up - 2 * ul)
    paeth = np.where((pa <= pb) & (pa <= pc), left, np.where(pb <= pc, up, ul))
    best = None
    for ftype, pred in ((0, 0), (1, left), (2, up), (4, paeth)):
        rows = ((px - pred) % 256).astype(np.uint8).reshape(h, w * 4)
        raw = np.concatenate([np.full((h, 1), ftype, np.uint8), rows], 1)
        data = zlib.compress(raw.tobytes(), 9)
        if best is None or len(data) < len(best):
            best = data
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = (bytes([0x89]) + b'PNG' + bytes([13, 10, 26, 10]) + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
           + chunk(b'IDAT', best) + chunk(b'IEND', b''))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)

# ---------------- articulated puppet rig (v2) ----------------
# Figure units: feet on y=0, crown ~0.95 (hats go higher), facing +x, hip at
# (0, 0.5). figure(spec) returns parts back-to-front as (polys, cls, carves);
# place_figure() drops them on a Canvas. Shoulders are frontal, head and feet
# in profile, arms on control rods -- the Kelantan wayang convention.
#
# spec keys (all optional):
#   body 'male'|'female'   head: key of FACES ('refined'|'old'|'foreign'|'female'|'young')
#   hat  None|'caping'|'songkok'|'tengkolok'|'tudung'|'sailor'|'tanjak' or a key of HATS
#   beard None or key of BEARDS   costume: key of COSTUMES   pose: key of POSES
#   legs: key of LEGS (default: the pose's)   hf / hb: key of HANDS (default: the pose's)
#   item_f / item_b: key of ITEMS2 for the front / back hand (or None)
#   lean: extra forward lean (deg)   rods: True   rod_to: rod end y (figure units)
#   cls: {part: lace class} overrides  (parts: top, lower, legs, arm, hat, head)
#   scale: size multiplier
# State modules add parts with register(TABLE, key, value) instead of editing
# this file. Tables: FACES, BEARDS, HATS, COSTUMES, LOWERS, POSES, LEGS, HANDS,
# ITEMS2. Signatures: FACES/BEARDS point lists in figure units; HATS fn() ->
# (polys, cls, carves) in head units; LOWERS fn(body) -> poly; ITEMS2
# fn(grip, forearm_deg, spec) -> (polys, cls, carves). A COSTUMES entry may add
# 'long': True (ankle cloth, squashed like kain) and 'extra': fn(spec) ->
# [(polys, cls, carves)] drawn over the torso, upright figure units.

def register(table, key, value):
    """Add a rig part from a state module. Refuses to replace an existing key,
    so parallel states can't silently change each other's (or Perlis's) art."""
    if key in table and table[key] is not value:
        raise KeyError('wayang part %r is already registered' % (key,))
    table[key] = value
    return value

HATS = {}      # new kind -> fn() -> (polys, cls, carves), head units (see _hat)
LOWERS = {}    # new kind -> fn(body) -> poly (see _lower)

HANDS = {
    'open': [(0, -0.012), (0.03, -0.016), (0.055, -0.013), (0.073, -0.005), (0.076, 0.003),
             (0.064, 0.007), (0.042, 0.008), (0.036, 0.015), (0.031, 0.027), (0.022, 0.027),
             (0.014, 0.015), (0, 0.012)],
    'grip': [(0, -0.012), (0.02, -0.017), (0.04, -0.015), (0.048, -0.002), (0.043, 0.012),
             (0.024, 0.017), (0, 0.012)],
}

# arm angles in degrees from hanging straight down, + = forward: (shoulder, elbow bend)
POSES = {
    'stand':   {'f': (22, 28), 'b': (-12, -12), 'lean': 0, 'legs': 'stand', 'hf': 'open', 'hb': 'open'},
    'gesture': {'f': (72, 48), 'b': (-14, -18), 'lean': 0, 'legs': 'stand', 'hf': 'open', 'hb': 'open'},
    'wonder':  {'f': (95, 40), 'b': (20, 50), 'lean': -4, 'legs': 'walk', 'hf': 'open', 'hb': 'open'},
    'stick':   {'f': (30, 42), 'b': (-22, -20), 'lean': 7, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'},
    'crank':   {'f': (84, 40), 'b': (74, 58), 'lean': 10, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'},
    'carry':   {'f': (38, 118), 'b': (-14, -12), 'lean': 3, 'legs': 'walk', 'hf': 'grip', 'hb': 'open'},
    'plant':   {'f': (28, 12), 'b': (8, 22), 'lean': 38, 'legs': 'bend', 'hf': 'grip', 'hb': 'open'},
    'hoe':     {'f': (40, 20), 'b': (25, 40), 'lean': 25, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'},
    'serve':   {'f': (58, 38), 'b': (44, 70), 'lean': 5, 'legs': 'stand', 'hf': 'grip', 'hb': 'grip'},
    'pour':    {'f': (84, 26), 'b': (28, 60), 'lean': 6, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'},
    'stir':    {'f': (48, 62), 'b': (-14, -16), 'lean': 8, 'legs': 'stand', 'hf': 'grip', 'hb': 'open'},
    'pull':    {'f': (82, 8), 'b': (70, 28), 'lean': -12, 'legs': 'walk', 'hf': 'grip', 'hb': 'grip'},
    'teach':   {'f': (50, 70), 'b': (-18, -15), 'lean': 3, 'legs': 'stand', 'hf': 'open', 'hb': 'grip'},
}

# leg stances: front knee, front ankle, back knee, back ankle, hip height
LEGS = {
    'stand': ((0.045, 0.27), (0.062, 0.055), (-0.035, 0.27), (-0.058, 0.055), 0.50),
    'walk':  ((0.095, 0.28), (0.13, 0.058), (-0.055, 0.26), (-0.12, 0.062), 0.49),
    'bend':  ((0.13, 0.27), (0.085, 0.058), (0.0, 0.25), (-0.085, 0.058), 0.43),
    'sit':   ((0.21, 0.37), (0.23, 0.07), (0.17, 0.355), (0.16, 0.075), 0.38),   # on a seat edge
}

COSTUMES = {
    # top: tunic hem height, flare; lower: garment; legs: trouser style; sleeve half-width
    'baju':   {'hem': 0.44, 'flare': 0.0, 'lower': 'sampin', 'legs': 'trousers', 'sleeve': 0.031,
               'cls': {'top': 'dots', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}},
    'farmer': {'hem': 0.45, 'flare': 0.006, 'lower': 'sampin', 'legs': 'rolled', 'sleeve': 0.031,
               'cls': {'top': 'dots', 'lower': 'grid', 'legs': 'edge', 'arm': 'edge'}},
    'sarong': {'hem': 0.44, 'flare': 0.0, 'lower': 'sarong', 'legs': None, 'sleeve': 0.031,
               'cls': {'top': 'lace', 'lower': 'scales', 'legs': 'edge', 'arm': 'edge'}},
    'kurung': {'hem': 0.36, 'flare': 0.05, 'lower': 'kain', 'legs': None, 'sleeve': 0.029,
               'cls': {'top': 'flower', 'lower': 'scales', 'legs': 'edge', 'arm': 'edge'}},
    'sailor': {'hem': 0.47, 'flare': 0.004, 'lower': None, 'legs': 'bell', 'sleeve': 0.03,
               'cls': {'top': 'dots', 'lower': 'grid', 'legs': 'slits', 'arm': 'edge'}},
}

def _arc_open(ctrl, seg=6):
    return catmull(ctrl, closed=False, seg=seg)

_SKULL = [(-0.018, 0.80), (-0.034, 0.835), (-0.039, 0.875), (-0.031, 0.91), (-0.008, 0.936),
          (0.02, 0.942), (0.042, 0.93), (0.052, 0.91)]
FACES = {   # forehead -> nose -> lips -> chin -> throat, kept sharp (no smoothing)
    'refined': [(0.056, 0.899), (0.07, 0.886), (0.086, 0.872), (0.108, 0.856), (0.099, 0.852),
                (0.077, 0.852), (0.078, 0.845), (0.071, 0.841), (0.073, 0.834), (0.065, 0.827),
                (0.058, 0.817), (0.042, 0.811), (0.03, 0.80)],
    'young':   [(0.056, 0.9), (0.068, 0.887), (0.082, 0.873), (0.098, 0.858), (0.092, 0.854),
                (0.074, 0.854), (0.075, 0.847), (0.068, 0.843), (0.07, 0.836), (0.063, 0.828),
                (0.057, 0.818), (0.042, 0.811), (0.03, 0.80)],
    'old':     [(0.056, 0.9), (0.068, 0.889), (0.086, 0.874), (0.1, 0.861), (0.103, 0.85),
                (0.094, 0.845), (0.08, 0.85), (0.072, 0.851), (0.068, 0.844), (0.063, 0.841),
                (0.066, 0.832), (0.058, 0.822), (0.044, 0.812), (0.03, 0.80)],
    'foreign': [(0.062, 0.906), (0.058, 0.894), (0.068, 0.886), (0.088, 0.868), (0.1, 0.856),
                (0.097, 0.846), (0.084, 0.848), (0.074, 0.85), (0.069, 0.843), (0.064, 0.84),
                (0.067, 0.832), (0.06, 0.822), (0.046, 0.812), (0.032, 0.80)],
    'female':  [(0.054, 0.9), (0.066, 0.887), (0.08, 0.873), (0.096, 0.859), (0.09, 0.855),
                (0.072, 0.855), (0.072, 0.848), (0.066, 0.844), (0.068, 0.838), (0.06, 0.83),
                (0.054, 0.821), (0.04, 0.814), (0.028, 0.802)],
}
BEARDS = {
    'tuft': [(0.062, 0.835), (0.062, 0.815), (0.058, 0.79), (0.046, 0.758), (0.040, 0.785),
             (0.032, 0.806), (0.036, 0.83)],
    'full': [(-0.022, 0.868), (0.008, 0.862), (0.04, 0.85), (0.068, 0.846), (0.072, 0.83),
             (0.068, 0.806), (0.06, 0.78), (0.046, 0.752), (0.03, 0.772), (0.004, 0.80),
             (-0.02, 0.83)],
}

def _head(kind, beard):
    face = FACES[kind]
    poly = _arc_open(_SKULL) + face
    parts = [poly, ribbon([(0.004, 0.77), (0.016, 0.83)], 0.02)]
    carves = [leaf(0.03, 0.892, -16, 0.026 if kind != 'female' else 0.023, 0.0058),
              ribbon(_arc_open([(0.026, 0.905), (0.042, 0.911), (0.06, 0.903)]), 0.0022),
              ribbon([(0.062, 0.8455), (0.074, 0.8475)], 0.0013)]
    if kind == 'old':
        carves.append(ribbon(_arc_open([(0.052, 0.873), (0.06, 0.864), (0.057, 0.852)]), 0.0016))
    if beard:
        parts.append(BEARDS[beard])
        for i in range(4 if beard == 'full' else 2):
            x = 0.012 + i * 0.014 if beard == 'full' else 0.046 + i * 0.006
            carves.append(ribbon([(x, 0.84 - i * 0.004), (x + 0.012, 0.79 - i * 0.006)], 0.0018, 0.0008))
    return parts, carves

def _hat(kind):
    """(polys, cls, carves) in head coordinates."""
    if kind == 'caping':
        A, F, B = (0.008, 1.045), (0.185, 0.906), (-0.168, 0.91)
        top = _arc_open([B, (-0.09, 0.958), (-0.03, 1.012), A], 6)[:-1]
        top += [A, (0.012, 1.052), (0.016, 1.045)]
        top += _arc_open([(0.016, 1.045), (0.08, 0.995), (0.14, 0.946), F], 6)[1:]
        top += [(F[0] + 0.004, F[1] - 0.008), (0.06, 0.895), (-0.06, 0.896), (B[0] - 0.004, B[1] - 0.007)]
        carves = []
        for t in (0.1, 0.24, 0.38, 0.52, 0.66, 0.8):
            px, py = B[0] + (F[0] - B[0]) * t, B[1] + (F[1] - B[1]) * t + 0.014
            qx, qy = A[0] + (px - A[0]) * 0.22, A[1] + (py - A[1]) * 0.22
            carves.append(ribbon([(qx, qy), (px, py)], 0.0012, 0.0034))
        carves.append(ribbon([(B[0] + 0.03, B[1] + 0.007), (F[0] - 0.03, F[1] + 0.004)], 0.0022))
        return [top], 'edge', carves
    if kind == 'songkok':
        return [_arc_open([(-0.052, 0.893), (-0.05, 0.94), (-0.047, 0.978), (0.0, 0.987),
                           (0.046, 0.983), (0.053, 0.94), (0.057, 0.902)]) + [(0.0, 0.896)]], 'dots', []
    if kind == 'tengkolok':
        p = [(0.058, 0.902), (0.052, 0.94), (0.025, 0.968), (0.004, 1.045), (-0.02, 1.0),
             (-0.05, 0.985), (-0.062, 0.94), (-0.058, 0.892), (0.0, 0.905)]
        return [p], 'lace', [ribbon([(-0.03, 0.93), (0.0, 1.01)], 0.002)]
    if kind == 'tanjak':
        p = [(0.058, 0.902), (0.056, 0.95), (0.03, 0.985), (-0.012, 1.075), (-0.03, 1.0),
             (-0.075, 1.03), (-0.064, 0.95), (-0.058, 0.892), (0.0, 0.905)]
        return [p], 'lace', []
    if kind == 'tudung':                         # selendang draped over the head and shoulder
        p = _arc_open([(0.056, 0.912), (0.036, 0.954), (0.0, 0.97), (-0.042, 0.958), (-0.064, 0.918),
                       (-0.07, 0.868), (-0.062, 0.83), (-0.04, 0.80)]) + \
            _arc_open([(-0.03, 0.792), (0.0, 0.79), (0.03, 0.795), (0.048, 0.806)]) + \
            [(0.036, 0.822), (0.025, 0.842), (0.022, 0.866), (0.03, 0.89), (0.046, 0.905)]
        tail = ribbon(_arc_open([(-0.05, 0.82), (-0.085, 0.76), (-0.1, 0.68), (-0.095, 0.6)]), 0.022, 0.03)
        return [p, tail], 'flower', []
    if kind == 'sailor':
        brim = ribbon(_arc_open([(-0.09, 0.925), (-0.06, 0.914), (0.0, 0.915), (0.06, 0.92), (0.095, 0.932)]), 0.0065)
        crown = _arc_open([(-0.05, 0.914), (-0.052, 0.96), (-0.042, 0.992), (0.0, 1.0), (0.044, 0.994),
                           (0.054, 0.962), (0.056, 0.918)])
        tails = [ribbon(_arc_open([(-0.046, 0.93), (-0.07, 0.89), (-0.078, 0.85)]), 0.007, 0.003),
                 ribbon(_arc_open([(-0.04, 0.93), (-0.056, 0.885), (-0.058, 0.845)]), 0.006, 0.003)]
        return [brim, crown] + tails, 'edge', [ribbon([(-0.044, 0.935), (0.046, 0.94)], 0.003)]
    return HATS[kind]() if kind in HATS else ([], 'edge', [])   # registered hats (built-in names win)

def _torso(body, hem, flare):
    if body == 'female':
        fr = [(0.025, 0.80), (0.06, 0.783), (0.082, 0.756), (0.078, 0.712), (0.075, 0.68), (0.058, 0.622),
              (0.05, 0.58), (0.058, 0.52), (0.074 + flare, hem)]
        bk = [(-0.068 - flare, hem), (-0.052, 0.52), (-0.046, 0.58), (-0.056, 0.66), (-0.07, 0.72),
              (-0.082, 0.756), (-0.06, 0.785), (-0.02, 0.80)]
    else:
        fr = [(0.03, 0.805), (0.072, 0.787), (0.098, 0.758), (0.086, 0.70), (0.072, 0.64), (0.06, 0.578),
              (0.068, 0.52), (0.084 + flare, hem)]
        bk = [(-0.079 - flare, hem), (-0.061, 0.52), (-0.055, 0.578), (-0.064, 0.65), (-0.08, 0.71),
              (-0.098, 0.758), (-0.074, 0.788), (-0.025, 0.805)]
    return _arc_open(fr) + _arc_open(bk)

def _lower(kind, body):
    if kind == 'sampin':
        return [(0.064, 0.565), (0.074, 0.48), (0.088, 0.38), (0.104, 0.292), (0.06, 0.305),
                (0.0, 0.302), (-0.06, 0.298), (-0.098, 0.292), (-0.084, 0.38), (-0.07, 0.48), (-0.06, 0.565)]
    if kind == 'sarong':
        return _arc_open([(0.062, 0.565), (0.07, 0.4), (0.088, 0.2), (0.112, 0.07)]) + \
            [(0.13, 0.058), (0.0, 0.066), (-0.1, 0.066)] + _arc_open([(-0.1, 0.066), (-0.084, 0.2), (-0.068, 0.4), (-0.06, 0.565)])[1:]
    if kind == 'kain':
        return _arc_open([(0.05, 0.575), (0.062, 0.4), (0.07, 0.2), (0.09, 0.045)]) + \
            [(0.0, 0.05), (-0.084, 0.045)] + _arc_open([(-0.084, 0.045), (-0.07, 0.2), (-0.06, 0.4), (-0.048, 0.575)])[1:]
    return LOWERS[kind](body) if kind in LOWERS else []       # registered lowers (built-in names win)

def _foot(ax, ay, big=False):
    s = 1.18 if big else 1.0
    return xf([(-0.03, 0.0), (0.072, 0.0), (0.078, 0.011), (0.035, 0.026), (0.012, 0.05),
               (-0.022, 0.05), (-0.032, 0.022)], ax, 0.0, s=s, ox=0.0)

def _leg(hip, knee, ankle, style):
    if style == 'rolled':
        calf = (knee[0] + (ankle[0] - knee[0]) * 0.55, knee[1] + (ankle[1] - knee[1]) * 0.55)
        return [ribbon([hip, knee], 0.035, 0.031), ribbon([knee, calf], 0.031, 0.029),
                ellipse(knee[0], knee[1], 0.031, n=14), ribbon([calf, ankle], 0.017, 0.014)]
    if style == 'bell':
        return [ribbon([hip, knee], 0.034, 0.029), ribbon([knee, ankle], 0.029, 0.038),
                ellipse(knee[0], knee[1], 0.029, n=14)]
    return [ribbon([hip, knee], 0.034, 0.029), ribbon([knee, ankle], 0.029, 0.022),
            ellipse(knee[0], knee[1], 0.029, n=14)]

def _arm(sh, a1, a2, sleeve, hand):
    r1, r2 = math.radians(a1), math.radians(a1 + a2)
    el = (sh[0] + 0.19 * math.sin(r1), sh[1] - 0.19 * math.cos(r1))
    wr = (el[0] + 0.175 * math.sin(r2), el[1] - 0.175 * math.cos(r2))
    polys = [ellipse(sh[0], sh[1], sleeve * 1.25, n=16), ribbon([sh, el], sleeve * 1.12, sleeve),
             ellipse(el[0], el[1], sleeve, n=16), ribbon([el, wr], sleeve, sleeve * 0.82)]
    ang = math.degrees(math.atan2(-math.cos(r2), math.sin(r2)))
    polys.append(xf(HANDS[hand], wr[0], wr[1], rot=ang))
    grip = (wr[0] + 0.026 * math.sin(r2), wr[1] - 0.026 * math.cos(r2))
    return polys, grip, ang

def _arm_bands(sh, a1, a2, sleeve):
    """Carved gelang bands: two thin cuts across the upper arm and the cuff."""
    r1, r2 = math.radians(a1), math.radians(a1 + a2)
    el = (sh[0] + 0.19 * math.sin(r1), sh[1] - 0.19 * math.cos(r1))
    out = []
    for base, r, t, w in ((sh, r1, 0.075, sleeve * 0.75), (el, r2, 0.15, sleeve * 0.62)):
        d = (math.sin(r), -math.cos(r))
        n = (-d[1], d[0])
        for o in (0.0, 0.012):
            c = (base[0] + d[0] * (t + o), base[1] + d[1] * (t + o))
            out.append(ribbon([(c[0] - n[0] * w, c[1] - n[1] * w), (c[0] + n[0] * w, c[1] + n[1] * w)], 0.0022))
    return out

# items held in a hand: f(grip, forearm_angle_deg, figure) -> (polys, cls, carves)
def _it_stick(g, ang, fig):
    top = (g[0] - 0.004, g[1] + 0.05)
    crook = arc_pts(top[0] - 0.024, top[1], 0.024, 0, 160, 12)
    path = crook[::-1] + [(g[0] + 0.004, g[1] - 0.06), (g[0] + 0.03, 0.0)]
    return [ribbon(path, 0.0072, 0.0058)], 'solid', []

def _it_sickle(g, ang, fig):
    a = math.radians(ang)
    tip = (g[0] + 0.07 * math.cos(a), g[1] + 0.07 * math.sin(a))
    blade = arc_pts(tip[0] + 0.045, tip[1], 0.05, 180, 330, 16)
    poly = ribbon(blade, 0.011, 0.002)
    return [ribbon([(g[0] - 0.02 * math.cos(a), g[1] - 0.02 * math.sin(a)), tip], 0.008), poly], 'solid', []

def _it_padi(g, ang, fig):
    polys = []
    rnd = random.Random(3)
    for i in range(9):
        a = math.radians(-90 + (i - 4) * 5 + rnd.uniform(-2, 2))
        L = 0.2 + rnd.uniform(-0.02, 0.02)
        end = (g[0] + L * math.cos(a), g[1] + L * math.sin(a))
        polys.append(ribbon([(g[0], g[1] + 0.03), end], 0.003, 0.0018))
    for i in range(7):
        a = -90 + (i - 3) * 9
        bx = g[0] + 0.045 * math.cos(math.radians(a + 180))
        polys.append(leaf(g[0] + (i - 3) * 0.006, g[1] + 0.035, 90 + (i - 3) * 14, 0.09, 0.008, bend=-0.02 * (1 if i > 3 else -1)))
    polys.append(ellipse(g[0], g[1] - 0.012, 0.012, 0.02))
    return polys, 'solid', []

def _it_hoe(g, ang, fig):
    """Cangkul struck into the ground ahead: handle down-forward, broad blade."""
    a = math.radians(-38)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])
    end = (g[0] + 0.4 * d[0], g[1] + 0.4 * d[1])
    back = (g[0] - 0.14 * d[0], g[1] - 0.14 * d[1])
    blade = [(end[0] + n[0] * 0.012 - d[0] * 0.01, end[1] + n[1] * 0.012 - d[1] * 0.01),
             (end[0] + n[0] * 0.012 + d[0] * 0.025, end[1] + n[1] * 0.012 + d[1] * 0.025),
             (end[0] - n[0] * 0.11 + d[0] * 0.035, end[1] - n[1] * 0.11 + d[1] * 0.035),
             (end[0] - n[0] * 0.115 - d[0] * 0.045, end[1] - n[1] * 0.115 - d[1] * 0.045),
             (end[0] - n[0] * 0.02 - d[0] * 0.03, end[1] - n[1] * 0.02 - d[1] * 0.03)]
    return [ribbon([back, end], 0.0075), blade], 'solid', []

def _it_ladle(g, ang, fig):
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    end = (g[0] + 0.2 * d[0], g[1] + 0.2 * d[1])
    return [ribbon([(g[0] - 0.05 * d[0], g[1] - 0.05 * d[1]), end], 0.006),
            ellipse(end[0] + 0.018, end[1] - 0.012, 0.03, 0.022)], 'solid', []

def _it_seedlings(g, ang, fig):
    polys = [ellipse(g[0], g[1], 0.016, 0.026)]
    for i in range(9):
        polys.append(leaf(g[0], g[1] + 0.01, 90 + (i - 4) * 11, 0.12 + 0.02 * (i % 3), 0.006, bend=0.01 * (i - 4)))
    for i in range(5):
        polys.append(ribbon([(g[0] + (i - 2) * 0.006, g[1] - 0.01), (g[0] + (i - 2) * 0.014, g[1] - 0.06)], 0.002, 0.0008))
    return polys, 'solid', []

def _it_rope(g, ang, fig):
    polys = []
    for i in range(4):
        polys.append(ribbon(_arc_open([(g[0] - 0.01, g[1] + 0.02), (g[0] - 0.05 - i * 0.008, g[1] - 0.05),
                                       (g[0] - 0.01, g[1] - 0.11 - i * 0.01), (g[0] + 0.035 + i * 0.006, g[1] - 0.05),
                                       (g[0] + 0.006, g[1] + 0.02)]), 0.0045))
    return polys, 'solid', []

def _it_bowl(g, ang, fig):
    cx, cy = g[0] + 0.035, g[1] + 0.012
    bowl = [(cx - 0.065, cy + 0.045), (cx + 0.065, cy + 0.045)] + \
        [(cx + 0.065 * math.cos(math.radians(a)), cy + 0.045 + 0.05 * math.sin(math.radians(a))) for a in range(-10, -171, -16)]
    foot = rect(cx - 0.025, cy - 0.012, cx + 0.025, cy)
    steam = [scroll(cx - 0.02 + 0.03 * i, cy + 0.11 + 0.025 * (i % 2), 0.016, 0.004, 1.1, a0=0, cw=i % 2 == 0,
                    tail=[(cx - 0.02 + 0.03 * i, cy + 0.055), (cx - 0.012 + 0.03 * i, cy + 0.08)]) for i in range(2)]
    return [bowl, foot] + steam, 'edge', []

def _it_gasing(g, ang, fig):
    cx, cy = g[0] + 0.01, g[1] - 0.075
    body = [(cx, cy - 0.05), (cx + 0.035, cy - 0.01), (cx + 0.045, cy + 0.012), (cx + 0.02, cy + 0.03),
            (cx + 0.004, cy + 0.045), (cx - 0.004, cy + 0.045), (cx - 0.02, cy + 0.03), (cx - 0.045, cy + 0.012),
            (cx - 0.035, cy - 0.01)]
    cord = ribbon([g, (cx + 0.003, cy + 0.045)], 0.0018)
    return [body, cord], 'solid', [ribbon([(cx - 0.03, cy + 0.006), (cx + 0.03, cy + 0.006)], 0.002)]

def _it_spyglass(g, ang, fig):
    a = math.radians(ang + 70)
    d = (math.cos(a), math.sin(a))
    return [ribbon([(g[0] - 0.04 * d[0], g[1] - 0.04 * d[1]), (g[0] + 0.1 * d[0], g[1] + 0.1 * d[1])], 0.011, 0.015)], 'solid', []

def _it_lantern(g, ang, fig):
    cx, top = g[0] + 0.004, g[1] - 0.035
    ring = ribbon(arc_pts(cx, g[1] - 0.008, 0.018, 200, 340, 10), 0.0035)
    cap = [(cx - 0.034, top), (cx + 0.034, top), (cx + 0.016, top + 0.022), (cx - 0.016, top + 0.022)]
    body = rect(cx - 0.028, top - 0.105, cx + 0.028, top)
    base = rect(cx - 0.036, top - 0.122, cx + 0.036, top - 0.103)
    hang = ribbon([(cx, top + 0.02), (cx, g[1] - 0.02)], 0.0032)
    panes = [rect(cx - 0.02 + 0.021 * i, top - 0.094, cx - 0.004 + 0.021 * i, top - 0.012) for i in range(2)]
    return [ring, cap, body, base, hang], 'solid', panes

def _it_switch(g, ang, fig):
    """A drover's cane held up and forward."""
    return [ribbon(_arc_open([(g[0] - 0.03, g[1] - 0.03), (g[0] + 0.15, g[1] + 0.14), (g[0] + 0.34, g[1] + 0.22),
                              (g[0] + 0.48, g[1] + 0.2)]), 0.006, 0.0025)], 'solid', []

ITEMS2 = {'stick': _it_stick, 'sickle': _it_sickle, 'padi': _it_padi, 'hoe': _it_hoe,
          'ladle': _it_ladle, 'seedlings': _it_seedlings, 'rope': _it_rope, 'bowl': _it_bowl,
          'gasing': _it_gasing, 'spyglass': _it_spyglass, 'lantern': _it_lantern, 'switch': _it_switch}

def figure(spec):
    """Parts back-to-front: list of (polys, cls, carves) in figure units."""
    body = spec.get('body', 'male')
    cos = dict(COSTUMES[spec.get('costume', 'baju')])
    cls = dict(cos['cls'])
    cls.update(spec.get('cls', {}))
    pose = POSES[spec.get('pose', 'stand')]
    fk, fa, bk, ba, hip = LEGS[spec.get('legs', pose['legs'])]
    lean = pose['lean'] + spec.get('lean', 0)
    dy = hip - 0.5
    up = lambda pts: xf(pts, 0.0, dy, rot=-lean, ox=0.0, oy=0.5)       # upper-body transform
    upp = lambda p: up([p])[0]
    sleeve = cos['sleeve'] * (0.92 if body == 'female' else 1.0)
    sh_f, sh_b = (0.068, 0.762), (-0.072, 0.765)
    if body == 'female':
        sh_f, sh_b = (0.058, 0.758), (-0.06, 0.76)
    parts = []
    # back arm (+ item behind it)
    a1, a2 = pose['b']
    arm, grip_b, ang_b = _arm(sh_b, a1 - lean, a2, sleeve, spec.get('hb', pose['hb']))
    arm = [up(p) for p in arm]
    bands_b = [up(c) for c in _arm_bands(sh_b, a1 - lean, a2, sleeve)]
    grip_b, ang_b = upp(grip_b), ang_b - lean
    if spec.get('item_b'):
        parts.append(ITEMS2[spec['item_b']](grip_b, ang_b, spec))
    parts.append((arm, cls['arm'], bands_b))
    # legs and feet
    lower = cos['lower']
    legs = cos['legs']
    big = legs == 'bell'
    hips = ((0.028, hip), (-0.026, hip))
    if legs:
        parts.append((_leg(hips[1], bk, ba, legs) + [_foot(ba[0], ba[1], big)], cls['legs'], []))
        if lower:                                # thighs go under the cloth
            parts.append((_leg(hips[0], fk, fa, legs) + [_foot(fa[0], fa[1], big)], cls['legs'], []))
    else:
        parts.append(([_foot(ba[0], ba[1])], 'solid', []))
    if lower and spec.get('legs', pose['legs']) == 'sit':   # cloth over the lap
        parts.append(([[(-0.075, hip + 0.07), (0.06, hip + 0.075), (fk[0] + 0.035, fk[1] + 0.045),
                        (fk[0] + 0.03, fk[1] - 0.06), (-0.085, hip - 0.07)]], cls['lower'], []))
    elif lower:
        if lower in ('sarong', 'kain') or cos.get('long'):   # long cloth: squash between hem and waist
            lw = xf(_lower(lower, body), 0.0, 0.0, sy=(0.52 + dy) / 0.52, oy=0.05)
        else:
            lw = xf(_lower(lower, body), 0.0, dy)
        parts.append(([lw], cls['lower'], []))
    if legs and not lower:
        parts.append((_leg(hips[0], fk, fa, legs) + [_foot(fa[0], fa[1], big)], cls['legs'], []))
    elif not legs:
        parts.append(([_foot(fa[0] + 0.02, fa[1])], 'solid', []))
    # torso
    tor = up(_torso(body, cos['hem'], cos['flare']))
    tcarve = []
    if spec.get('costume') == 'sailor':
        tcarve = [up(ellipse(0.05, 0.72 - 0.05 * i, 0.007, n=10)) for i in range(5)]
    parts.append(([tor], cls['top'], tcarve))
    if cos.get('extra'):                         # registered costume pieces (sash, keris, collar...)
        parts += [([up(p) for p in ps], pc, [up(c) for c in cs]) for ps, pc, cs in cos['extra'](spec)]
    if spec.get('costume') == 'sailor':          # square sailor collar flap + neckerchief
        parts.append(([up([(-0.02, 0.805), (-0.088, 0.792), (-0.09, 0.725), (-0.03, 0.735)]),
                       up([(0.02, 0.80), (0.055, 0.79), (0.05, 0.74), (0.065, 0.66), (0.045, 0.66), (0.035, 0.73)])],
                      'edge', []))
    if lower == 'sampin':                        # waist sash knot
        parts.append(([up(ribbon([(-0.07, 0.535), (0.07, 0.54)], 0.016)),
                       up([(0.05, 0.53), (0.085, 0.47), (0.07, 0.465), (0.045, 0.515)])], 'edge', []))
    # head, beard, hat
    hs = lambda pts: up(xf(pts, s=HEAD_SCALE, ox=0.0, oy=0.79))
    hp, hc = _head(spec.get('head', 'refined' if body == 'male' else 'female'), spec.get('beard'))
    if spec.get('scarf'):                        # farmer's towel over the shoulders
        parts.append(([up(ribbon(_arc_open([(-0.085, 0.70), (-0.06, 0.775), (0.0, 0.80), (0.06, 0.785),
                                             (0.085, 0.72), (0.09, 0.64)]), 0.017, 0.012)),
                       up(ribbon([(0.082, 0.70), (0.072, 0.60)], 0.012, 0.016))], 'edge', []))
    parts.append(([hs(p) for p in hp], cls.get('head', 'solid'), [hs(c) for c in hc]))
    if spec.get('hat'):
        hpol, hcls, hcar = _hat(spec['hat'])
        parts.append(([hs(p) for p in hpol], cls.get('hat', hcls), [hs(c) for c in hcar]))
    # front item, then the front arm over it
    a1, a2 = pose['f']
    arm, grip_f, ang_f = _arm(sh_f, a1 - lean, a2, sleeve, spec.get('hf', pose['hf']))
    arm = [up(p) for p in arm]
    bands_f = [up(c) for c in _arm_bands(sh_f, a1 - lean, a2, sleeve)]
    grip_f, ang_f = upp(grip_f), ang_f - lean
    if spec.get('item_f'):
        parts.append(ITEMS2[spec['item_f']](grip_f, ang_f, spec))
    parts.append((arm, cls['arm'], bands_f))
    # control rods: one per hand plus the central gapit
    if spec.get('rods', True):
        y_end = spec.get('rod_to', -0.42)
        rods = [ribbon([grip_f, (grip_f[0] + 0.06, y_end)], 0.0026, 0.0034),
                ribbon([grip_b, (grip_b[0] - 0.05, y_end)], 0.0026, 0.0034),
                ribbon([(0.0, hip - 0.06), (0.0, y_end)], 0.0052, 0.0068)]
        parts.append((rods, 'solid', []))
    return parts

def place_figure(cv, spec, x, y, s, flip=False, layer='mid'):
    """Put a figure on the canvas with its feet at (x, y), scale s (figure unit -> canvas units)."""
    sc = spec.get('scale', 1.0) * s * (0.93 if spec.get('body') == 'female' else 1.0)
    for polys, cls, carves in figure(spec):
        cv.add([xf(p, x, y, s=sc, flip=flip) for p in polys], cls, layer)
        cv.carve([xf(c, x, y, s=sc, flip=flip) for c in carves], layer)

HEAD_SCALE = 1.2

PUPPET_SHEET = {'w': 1024, 'view_w': 1.9, 'cy': 0.75, 'k': 1.25, 'feet': 0.03, 'scale': 1.32}  # feet on row 899 = main.gd CUT_PUPPET_FEET

def render_puppet_v2(spec, path):
    """1024x1024 master/sailor puppet sheet, framed like the legacy puppets."""
    P = PUPPET_SHEET
    cv = Canvas(P['w'], P['w'], P['view_w'], 0.0, P['cy'], k=P['k'])
    sp = dict(spec)
    sp.setdefault('rod_to', (P['cy'] - P['view_w'] * 0.47 - P['feet']) / P['scale'])
    place_figure(cv, sp, spec.get('x', -0.04), P['feet'], P['scale'])
    a = cv.render()
    return save_alpha_png(a, path)
