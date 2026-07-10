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
