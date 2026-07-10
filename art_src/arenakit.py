# Arena kit for gasing arenas — loaded fresh in each blender-mcp execute_python call.
import bpy, bmesh, math, random
from mathutils import Vector, Euler

# ---------------------------------------------------------------- scene utils
def wipe():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for _ in range(3):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

def M(name, col, rough=0.8, metal=0.0, emit=None, estr=0.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit is not None:
        b.inputs["Emission Color"].default_value = (emit[0], emit[1], emit[2], 1.0)
        b.inputs["Emission Strength"].default_value = estr
    else:
        b.inputs["Emission Strength"].default_value = 0.0
    return m

def _link(ob):
    bpy.context.collection.objects.link(ob)
    return ob

def _setmat(ob, mat):
    if mat is not None:
        ob.data.materials.append(mat)
    return ob

# ---------------------------------------------------------------- primitives
def box(pos, size, mat, rz=0.0, rx=0.0, ry=0.0):
    """size = full dims (x,y,z); pos = center."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=pos)
    ob = bpy.context.active_object
    ob.scale = (size[0], size[1], size[2])
    ob.rotation_euler = (rx, ry, rz)
    return _setmat(ob, mat)

def cyl(pos, r1, r2, depth, mat, verts=8, rot=(0,0,0)):
    """pos = center of cylinder."""
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2,
                                    depth=depth, location=pos, rotation=rot)
    return _setmat(bpy.context.active_object, mat)

def cylz(base, r1, r2, h, mat, verts=8, rot_z=0.0):
    """cylinder standing on base point (z = bottom)."""
    ob = cyl((base[0], base[1], base[2] + h*0.5), r1, r2, h, mat, verts)
    ob.rotation_euler = (0, 0, rot_z)
    return ob

def cone(pos_base, r, h, mat, verts=8):
    return cylz(pos_base, r, 0.0, h, mat, verts)

def sphere(pos, r, mat, seg=10, rings=8, scale=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=pos)
    ob = bpy.context.active_object
    if scale: ob.scale = scale
    return _setmat(ob, mat)

def plane(pos, sx, sy, mat, rot=(0,0,0)):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=pos, rotation=rot)
    ob = bpy.context.active_object
    ob.scale = (sx, sy, 1.0)
    return _setmat(ob, mat)

def blob(pos, r, mat, jitter=0.22, scale=(1,1,1), seed=0):
    """jittered icosphere: rock / canopy."""
    rng = random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=pos)
    ob = bpy.context.active_object
    for v in ob.data.vertices:
        v.co *= 1.0 + rng.uniform(-jitter, jitter)
    ob.scale = scale
    return _setmat(ob, mat)

def ring(name, rin, rout, mat, seg=32, z=0.0, rdiv=1, zfun=None):
    """flat donut ring with planar UVs (used for EnvEarth / water / tile rings).
    rdiv = radial subdivisions; zfun(x, y, r, a) -> z offset for gentle relief."""
    bm = bmesh.new()
    rows = []
    for k in range(rdiv+1):
        r = rin + (rout-rin)*k/rdiv
        row = []
        for i in range(seg):
            a = 2*math.pi*i/seg
            x, y = r*math.cos(a), r*math.sin(a)
            zz = z if zfun is None else z + zfun(x, y, r, a)
            row.append(bm.verts.new((x, y, zz)))
        rows.append(row)
    for k in range(rdiv):
        for i in range(seg):
            j = (i+1) % seg
            bm.faces.new((rows[k][i], rows[k+1][i], rows[k+1][j], rows[k][j]))
    uv = bm.loops.layers.uv.new("UVMap")
    s = 1.0/(2*rout)
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = (l.vert.co.x*s + 0.5, l.vert.co.y*s + 0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = _link(bpy.data.objects.new(name, me))
    return _setmat(ob, mat)

def prism(pos, w, d, h, mat, rz=0.0):
    """gable roof: base w(x) × d(y) at pos.z, ridge along X at +h."""
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),
                                   (-w/2,0,h),(w/2,0,h)]]
    for idx in [(0,1,5,4),(2,3,4,5),(1,2,5),(3,0,4),(3,2,1,0)]:
        bm.faces.new([v[i] for i in idx])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("prism")
    bm.to_mesh(me); bm.free()
    ob = _link(bpy.data.objects.new("prism", me))
    ob.location = pos
    ob.rotation_euler = (0,0,rz)
    return _setmat(ob, mat)

# ---------------------------------------------------------------- kit pieces
def palm(pos, h=3.4, mat_wood=None, mat_leaf=None, seed=0, lean=0.10):
    rng = random.Random(seed)
    la = rng.uniform(0, 2*math.pi)
    objs = []
    tr = cylz(pos, 0.14, 0.07, h, mat_wood, verts=6)
    tr.rotation_euler = (lean*math.cos(la), lean*math.sin(la), 0)
    objs.append(tr)
    bpy.context.view_layer.update()
    tip = tr.matrix_world @ Vector((0, 0, h*0.5))
    top = (tip.x, tip.y, tip.z)
    n = 7
    for i in range(n):
        a = 2*math.pi*i/n + rng.uniform(-0.2, 0.2)
        leaf = box((0,0,0), (1.5, 0.34, 0.05), mat_leaf)
        leaf.rotation_euler = Euler((0, math.radians(rng.uniform(22, 40)), a), 'XYZ')
        off = Vector((math.cos(a), math.sin(a), 0)) * 0.55
        leaf.location = (top[0] + off.x, top[1] + off.y, top[2] - 0.12)
        objs.append(leaf)
    return objs

def casuarina(pos, h=4.2, mat_wood=None, mat_leaf=None, seed=0):
    rng = random.Random(seed)
    objs = [cylz(pos, 0.10, 0.05, h*0.5, mat_wood, verts=5)]
    z = pos[2] + h*0.30
    r = 0.85 * h/4.2
    for i in range(3):
        objs.append(cone((pos[0]+rng.uniform(-0.05,0.05), pos[1]+rng.uniform(-0.05,0.05), z),
                         r, h*0.30, mat_leaf, verts=7))
        z += h*0.22
        r *= 0.72
    return objs

def stilt_hut(pos, rz=0.0, w=2.6, d=2.0, mat_wood=None, mat_wall=None, mat_roof=None):
    """kampung stilt hut; returns objs. pos = ground center."""
    x, y, z = pos
    objs = []
    fl = 1.0  # floor height
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(cylz((sx*w*0.38, sy*d*0.38, 0), 0.07, 0.06, fl, mat_wood, verts=6))
    objs.append(box((0, 0, fl+0.08), (w, d, 0.16), mat_wood))            # floor
    objs.append(box((0, 0, fl+0.16+0.65), (w*0.9, d*0.9, 1.3), mat_wall))  # walls
    objs.append(box((0, -d*0.45-0.02, fl+0.16+0.45), (0.55, 0.06, 0.9), mat_wood))  # door
    objs.append(prism((0, 0, fl+0.16+1.3), w*1.15, d*1.25, 0.85, mat_roof))
    # ladder
    objs.append(box((0, -d*0.55, fl*0.5), (0.4, 0.06, fl*1.15), mat_wood, rx=math.radians(28)))
    grp = merge("tmp_hut", objs)
    grp.location = (x, y, z)
    grp.rotation_euler = (0, 0, rz)
    return [grp]

def fence_arc(r, a0, a1, n, mat_wood, h=0.5):
    """low fence following an arc (angles in radians)."""
    objs = []
    for i in range(n+1):
        a = a0 + (a1-a0)*i/n
        objs.append(box((r*math.cos(a), r*math.sin(a), h*0.5), (0.08, 0.08, h), mat_wood, rz=a))
    for i in range(n):
        a = a0 + (a1-a0)*(i+0.5)/n
        seg = 2*r*math.sin((a1-a0)/(2*n)) + 0.1
        objs.append(box((r*math.cos(a), r*math.sin(a), h*0.8), (seg, 0.05, 0.05), mat_wood, rz=a+math.pi/2))
    return objs

def boat(pos, rz, L=3.0, W=0.85, H=0.55, mat=None, mat_in=None):
    n = 7
    bm = bmesh.new()
    rows = []
    for i in range(n):
        t = i/(n-1)
        x = (t-0.5)*L
        w = W * max(0.10, math.sin(math.pi*min(max(t, 0.02), 0.98))**0.65)
        lift = 0.55*H*((2*t-1)**4)
        pts = [(-w, H), (-0.8*w, 0.30*H), (0.0, 0.05*H), (0.8*w, 0.30*H), (w, H), (0.0, 0.86*H)]
        rows.append([bm.verts.new((x, p[0], p[1]+lift)) for p in pts])
    for i in range(n-1):
        a, b = rows[i], rows[i+1]
        for k in range(6):
            j = (k+1) % 6
            bm.faces.new((a[k], b[k], b[j], a[j]))
    bm.faces.new(rows[0])
    bm.faces.new(list(reversed(rows[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("boat")
    bm.to_mesh(me); bm.free()
    ob = _link(bpy.data.objects.new("boat", me))
    ob.location = pos
    ob.rotation_euler = (0, 0, rz)
    _setmat(ob, mat)
    return [ob]

def market_stall(pos, rz=0.0, mat_wood=None, mat_canvas=None, mat_goods=None,
                 lamp_mat=None):
    objs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(cylz((sx*0.9, sy*0.65, 0), 0.05, 0.05, 2.0 if sy > 0 else 2.3, mat_wood, verts=6))
    objs.append(box((0, 0, 2.25), (2.3, 1.8, 0.07), mat_canvas, rx=math.radians(-10)))  # slanted roof
    objs.append(box((0, 0, 0.55), (2.0, 1.1, 1.1), mat_wood))  # counter
    rng = random.Random(int(pos[0]*7+pos[1]*13))
    for i in range(4):
        objs.append(sphere((rng.uniform(-0.7, 0.7), rng.uniform(-0.3, 0.3), 1.22), 0.14, mat_goods, seg=8, rings=6))
    if lamp_mat is not None:
        objs.append(sphere((0, 0.4, 1.95), 0.13, lamp_mat, seg=8, rings=6))
    grp = merge("tmp_stall", objs)
    grp.location = pos
    grp.rotation_euler = (0, 0, rz)
    return [grp]

def catenary(p0, p1, n, sag, r, mat):
    objs = []
    for i in range(n):
        t = (i+0.5)/n
        x = p0[0] + (p1[0]-p0[0])*t
        y = p0[1] + (p1[1]-p0[1])*t
        z = p0[2] + (p1[2]-p0[2])*t - sag*4*t*(1-t)
        objs.append(sphere((x, y, z), r, mat, seg=6, rings=5))
    return objs

def skyline_boxes(arc_r, a0, a1, n, hmin, hmax, mat, seed=0, wmin=1.6, wmax=3.2):
    rng = random.Random(seed)
    objs = []
    for i in range(n):
        a = a0 + (a1-a0)*(i+0.5)/n + rng.uniform(-0.02, 0.02)
        r = arc_r + rng.uniform(-1.0, 1.0)
        h = rng.uniform(hmin, hmax)
        w = rng.uniform(wmin, wmax)
        d = rng.uniform(1.4, 2.4)
        ob = box((r*math.cos(a), r*math.sin(a), h*0.5), (w, d, h), mat, rz=a+math.pi/2)
        objs.append(ob)
        if rng.random() < 0.5:  # rooftop block
            objs.append(box((r*math.cos(a), r*math.sin(a), h+0.25), (w*0.4, d*0.4, 0.5), mat, rz=a+math.pi/2))
    return objs

# ---------------------------------------------------------------- small-detail helpers
def noise_ground(name, mat, rin=4.5, rout=19.0, seg=48, rdiv=6, amp=0.10, seed=0):
    """dense EnvEarth ring with gentle vertex relief — the Terengganu look."""
    rng = random.Random(seed)
    grid = {}
    def zf(x, y, r, a):
        key = (round(x*2), round(y*2))
        if key not in grid:
            grid[key] = rng.uniform(-amp, amp)
        edge = min(1.0, (r - rin) / 1.5)  # flatten toward the ring lip
        return grid[key] * edge
    return ring(name, rin, rout, mat, seg=seg, z=0.0, rdiv=rdiv, zfun=zf)

def water_sheet(name, mat, rin, rout, seg=48, rdiv=5, amp=0.03, z=0.05, seed=1):
    """subdivided glossy sheet with ripple relief."""
    rng = random.Random(seed)
    grid = {}
    def zf(x, y, r, a):
        key = (round(x*1.5), round(y*1.5))
        if key not in grid:
            grid[key] = rng.uniform(-amp, amp)
        return grid[key]
    return ring(name, rin, rout, mat, seg=seg, z=z, rdiv=rdiv, zfun=zf)

def rock_scatter(n, r0, r1, mat, seed=0, rmax_size=0.45, avoid=None):
    """jittered rocks in the visible band; avoid = list of (x,y,rad) exclusion discs."""
    rng = random.Random(seed)
    objs = []
    for i in range(n):
        a = rng.uniform(0, 2*math.pi)
        rr = rng.uniform(r0, r1)
        x, y = rr*math.cos(a), rr*math.sin(a)
        if avoid and any(math.hypot(x-ax, y-ay) < ar for (ax, ay, ar) in avoid):
            continue
        s = rng.uniform(0.12, rmax_size)
        objs.append(blob((x, y, s*0.35), s, mat, jitter=0.35,
                         scale=(1.0, rng.uniform(0.7, 1.3), rng.uniform(0.5, 0.8)), seed=seed*100+i))
    return objs

def tuft_scatter(n, r0, r1, mat, seed=0, h=0.28, avoid=None):
    """grass tufts: tiny 3-cone clusters."""
    rng = random.Random(seed)
    objs = []
    for i in range(n):
        a = rng.uniform(0, 2*math.pi)
        rr = rng.uniform(r0, r1)
        x, y = rr*math.cos(a), rr*math.sin(a)
        if avoid and any(math.hypot(x-ax, y-ay) < ar for (ax, ay, ar) in avoid):
            continue
        for k in range(3):
            objs.append(cone((x+rng.uniform(-0.08,0.08), y+rng.uniform(-0.08,0.08), 0),
                             0.045, h*rng.uniform(0.7, 1.2), mat, verts=4))
    return objs

def bunting(p0, p1, n, mats, sag=0.35):
    """string of alternating triangle flags between two points."""
    objs = []
    for i in range(n):
        t = (i+0.5)/n
        x = p0[0] + (p1[0]-p0[0])*t
        y = p0[1] + (p1[1]-p0[1])*t
        z = p0[2] + (p1[2]-p0[2])*t - sag*4*t*(1-t)
        m = mats[i % len(mats)]
        f = cone((x, y, z-0.22), 0.11, 0.22, m, verts=3)
        f.rotation_euler = (math.pi, 0, math.atan2(p1[1]-p0[1], p1[0]-p0[0]))
        objs.append(f)
    return objs

def lamp_post(pos, mat_pole, mat_lamp, h=1.9):
    return [cylz(pos, 0.05, 0.04, h, mat_pole, verts=6),
            sphere((pos[0], pos[1], pos[2]+h+0.12), 0.13, mat_lamp, seg=8, rings=6)]

def crate_stack(pos, rz, mat, n=3, s=0.38, seed=0):
    rng = random.Random(seed)
    objs = []
    zacc = 0.0
    for i in range(n):
        objs.append(box((pos[0]+rng.uniform(-0.06,0.06), pos[1]+rng.uniform(-0.06,0.06), zacc+s*0.5),
                        (s, s, s), mat, rz=rz+rng.uniform(-0.3, 0.3)))
        zacc += s
    return objs

def basket(pos, mat, r=0.16):
    return [cylz(pos, r*0.75, r, r*1.4, mat, verts=8)]

# ---------------------------------------------------------------- assembly
def merge(name, objs):
    """join objs into one mesh object `name` at world origin, identity transform."""
    objs = [o for o in objs if o is not None]
    me = bpy.data.meshes.new(name)
    anchor = _link(bpy.data.objects.new(name, me))
    with bpy.context.temp_override(active_object=anchor,
                                   selected_editable_objects=[anchor]+objs,
                                   selected_objects=[anchor]+objs):
        bpy.ops.object.join()
    return anchor

def flatten(lists):
    out = []
    for l in lists:
        if isinstance(l, (list, tuple)): out.extend(l)
        else: out.append(l)
    return out

def tri_report():
    dg = bpy.context.evaluated_depsgraph_get()
    rep, total = [], 0
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        n = len(me.loop_triangles)
        total += n
        mn = o.matrix_world @ Vector(o.bound_box[0])
        mx = o.matrix_world @ Vector(o.bound_box[6])
        rep.append((o.name, n, tuple(round(v,2) for v in mn), tuple(round(v,2) for v in mx)))
        o.evaluated_get(dg).to_mesh_clear()
    return {"total": total, "objects": rep}

def check_exclusion():
    """verify: no verts inside r4.5; nothing taller than 0.6 within r6."""
    bad_inner, bad_low = [], []
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        mw = o.matrix_world
        for v in o.data.vertices:
            co = mw @ v.co
            rr = math.hypot(co.x, co.y)
            if rr < 4.49:
                bad_inner.append((o.name, round(rr,2)))
                break
        for v in o.data.vertices:
            co = mw @ v.co
            rr = math.hypot(co.x, co.y)
            if rr < 6.0 and co.z > 0.6:
                bad_low.append((o.name, round(rr,2), round(co.z,2)))
                break
    return {"verts_inside_r4.5": bad_inner, "tall_within_r6": bad_low}

# ---------------------------------------------------------------- view / export
def cam_game():
    cam = bpy.data.objects.get("GameCam")
    if cam is None:
        cd = bpy.data.cameras.new("GameCam")
        cam = _link(bpy.data.objects.new("GameCam", cd))
    cam.location = (0, -7, 9)
    d = Vector((0, 7, -9)).normalized()
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle_y = math.radians(55)
    cam.data.clip_end = 200
    bpy.context.scene.camera = cam
    return cam

def _areas3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                yield area

def look_game():
    cam_game()
    for area in _areas3d():
        sp = area.spaces.active
        sp.shading.type = 'MATERIAL'
        sp.region_3d.view_perspective = 'CAMERA'
        sp.overlay.show_overlays = False

def look_top(dist=42):
    for area in _areas3d():
        sp = area.spaces.active
        sp.shading.type = 'MATERIAL'
        r3d = sp.region_3d
        r3d.view_perspective = 'ORTHO'
        r3d.view_rotation = (1, 0, 0, 0)
        r3d.view_location = (0, 0, 0)
        r3d.view_distance = dist
        sp.overlay.show_overlays = False

def export_arena(arena_id):
    bpy.ops.object.select_all(action='DESELECT')
    names = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith("Env"):
            o.select_set(True)
            names.append(o.name)
    bpy.ops.export_scene.gltf(
        filepath="E:/GodotProject/gasing/assets/arena_%s.glb" % arena_id,
        export_format='GLB', use_selection=True, export_apply=True)
    bpy.ops.wm.save_as_mainfile(filepath="E:/GodotProject/gasing/art_src/arena_%s.blend" % arena_id)
    return names
