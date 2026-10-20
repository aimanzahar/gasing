"""arenakit v2 -- data-driven arena builder for Gasing Pangkah (Blender 5.1; headless or blender-mcp).

Art bible: warm stylised carved-and-lacquered diorama. No bare primitives (everything is bevelled,
tapered, jittered or noise-displaced), smooth shading + sharp-by-angle 35 deg, all colour lives in a
POINT-domain vertex colour layer "Col" (exported as COLOR_0, no UVs). Godot's scripts/arena_dress.gd
adds per-kind triplanar noise, the water shader and MultiMesh grass at runtime.

Use from an arena script (see art_src/arena_perlis.py):
    import sys, os; sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import arenakit as K
    def build(G): ...add geometry...   ;   K.main("perlis", build, MOOD)
CLI:  blender -b --factory-startup -P art_src/arena_<id>.py -- [--export] [--render game,vista]
                                       [--out DIR] [--res 1600x900] [--samples 16]
MCP:  exec(open(path).read(), {"__name__": "__mcp__"}); then K.main(..., argv=[...]) yourself.

Coordinates: Blender (x,y,z) -> Godot (x, z, -y). Blender +y = far side (top of the battle screen),
-y = camera side. Ring centre at origin, ground at z=0, 1 unit = 1 m.

Node contract (merged per material): EnvBattle_<Mat>, EnvFar_<Mat>, EnvScatter<Grass|Paddy|Reed>_<density/m2>
(hidden sources, vertex colour = blade tint), EnvLight_<n>[_r<range m>] point lights (<=6).
Materials: Mat<Kind>_<variant>, Kind in KINDS.
"""
import bpy, bmesh, math, random, json, os, sys, struct, time
import numpy as np
from mathutils import Vector, Matrix, Euler, noise as mnoise

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO, "assets")

KINDS = ("Ground", "Grass", "Sand", "Mud", "Rock", "Wood", "Thatch", "Leaf", "Plaster", "Tile",
         "Metal", "Cloth", "Water", "Glow")
ROUGH = {"Ground": 0.95, "Grass": 0.9, "Sand": 0.9, "Mud": 0.75, "Rock": 0.85, "Wood": 0.8,
         "Thatch": 0.9, "Leaf": 0.7, "Plaster": 0.9, "Tile": 0.6, "Metal": 0.45, "Cloth": 0.9,
         "Water": 0.15, "Glow": 0.5}
TWO_SIDED = ("Leaf", "Cloth")
SCATTER_KINDS = ("Grass", "Paddy", "Reed")
BUDGET = {"battle_tris": 45000, "far_tris": 20000, "materials": 12, "far_materials": 6,
          "scatter_tris": 4000, "glb_bytes": 3_000_000, "lights": 6, "instances": 15000}
SHARP_DEG = 35.0
SHARP_KINDS = ("Wood", "Thatch", "Metal", "Tile", "Plaster", "Glow")  # organic kinds stay fully smooth


# ============================================================== pieces (numpy meshes)
class P:
    """A small mesh: v (n,3) float, f list of index tuples (tris/quads/ngons), c (n,4) sRGB or None."""
    __slots__ = ("v", "f", "c")

    def __init__(self, v, f, c=None):
        self.v = np.asarray(v, dtype=np.float64).reshape(-1, 3)
        self.f = [tuple(int(i) for i in x) for x in f]
        self.c = None if c is None else np.asarray(c, dtype=np.float64).reshape(-1, 4)

    def copy(self):
        return P(self.v.copy(), list(self.f), None if self.c is None else self.c.copy())


def join(*ps):
    ps = [p for p in _flat(ps) if p is not None and len(p.v)]
    if not ps:
        return P(np.zeros((0, 3)), [])
    v, f, c, off = [], [], [], 0
    for p in ps:
        v.append(p.v)
        f.extend(tuple(i + off for i in x) for x in p.f)
        c.append(p.c if p.c is not None else np.ones((len(p.v), 4)))
        off += len(p.v)
    return P(np.vstack(v), f, np.vstack(c))


def _flat(x):
    out = []
    for i in x:
        if isinstance(i, (list, tuple)):
            out.extend(_flat(i))
        else:
            out.append(i)
    return out


def dbl(p):
    """make an open surface visible from both sides with a single-sided material (adds flipped faces)."""
    q = p.copy()
    q.f = q.f + [tuple(reversed(x)) for x in q.f]
    return q


def from_bm(bm):
    bm.verts.index_update()
    v = [tuple(x.co) for x in bm.verts]
    f = [tuple(x.index for x in face.verts) for face in bm.faces]
    bm.free()
    return P(v, f)


def xf(p, loc=(0, 0, 0), rot=(0, 0, 0), s=1.0):
    """scale, then rotate (XYZ euler, radians), then translate. Returns a new piece."""
    q = p.copy()
    q.v = q.v * np.asarray(s if isinstance(s, (tuple, list)) else (s, s, s), dtype=np.float64)
    R = np.array(Euler(rot, 'XYZ').to_matrix())
    q.v = q.v @ R.T + np.asarray(loc, dtype=np.float64)
    return q


def aim(p, a, b):
    """map a piece built along +Z (0..1 length units already applied) so its +Z axis points a->b, base at a."""
    d = Vector(b) - Vector(a)
    R = np.array(d.normalized().to_track_quat('Z', 'Y').to_matrix())
    q = p.copy()
    q.v = q.v @ R.T + np.asarray(a, dtype=np.float64)
    return q


def vnormals(p):
    n = np.zeros_like(p.v)
    for f in p.f:
        if len(f) < 3:
            continue
        pts = p.v[list(f)]
        nn = np.cross(pts[1:-1] - pts[0], pts[2:] - pts[0]).sum(axis=0)  # fan sum = area-weighted normal
        n[list(f)] += nn
    l = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(l, 1e-9)


def smooth01(e0, e1, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def nz(x, y, z=0.0, s=1.0, seed=0):
    """coherent noise in [-1,1] at world point (scale s)."""
    return mnoise.noise(Vector((x * s + seed * 17.13, y * s - seed * 9.71, z * s + seed * 3.3)))


def nfield(v, s=1.0, seed=0, stretch=(1, 1, 1)):
    return np.array([mnoise.noise(Vector((a * s * stretch[0] + seed * 17.13, b * s * stretch[1] - seed * 9.71,
                                          c * s * stretch[2] + seed * 3.3))) for a, b, c in v])


def paint(p, rgb, var=0.05, ao=0.45, ao_h=0.5, ground=0.0, top=0.15, namp=0.0, ns=1.5, seed=None,
          alpha=1.0, stretch=(1, 1, 1)):
    """vertex-colour a placed piece: base rgb x per-piece jitter x height AO x top light x noise."""
    if len(p.v) == 0:  # e.g. fully culled by cull_back
        return p
    if seed is None:  # deterministic per placement
        seed = int(abs(p.v.mean(axis=0)).sum() * 1000)
    rng = random.Random(seed)
    n = vnormals(p)
    shade = np.full(len(p.v), 1.0 + rng.uniform(-var, var))
    shade *= 1.0 + top * n[:, 2]
    if ao:
        shade *= (1.0 - ao) + ao * smooth01(0.0, ao_h, p.v[:, 2] - ground)
    if namp:
        shade *= 1.0 + namp * nfield(p.v, ns, seed, stretch)
    c = np.ones((len(p.v), 4))
    c[:, :3] = np.clip(np.asarray(rgb[:3])[None, :] * shade[:, None], 0, 1)
    c[:, 3] = alpha
    p.c = c
    return p


def tint(p, fn):
    """per-vertex colour edit: fn(v (n,3), c (n,4)) -> c."""
    p.c = np.clip(fn(p.v, p.c if p.c is not None else np.ones((len(p.v), 4))), 0, 1)
    return p


# ============================================================== generators (local space)
def box(sx, sy, sz, bev=0.02, seg=1, jitter=0.0, seed=0):
    """bevelled box, base at z=0, centred in x/y."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz + sz * 0.5))
    if bev > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bev, 0.45 * min(sx, sy, sz)), segments=seg,
                        affect='EDGES', profile=0.5, clamp_overlap=True)
    p = from_bm(bm)
    if jitter:
        rng = np.random.default_rng(seed)
        p.v += rng.uniform(-jitter, jitter, p.v.shape)
    return p


def lathe(prof, seg=12, cap0=True, cap1=True, phase=0.0, rfn=None):
    """revolve profile [(r,z),...] bottom->top about Z. r==0 ends become poles.
    rfn(a, t) -> radius multiplier (fluting, wobble)."""
    v, f, rings = [], [], []
    n = len(prof)
    for k, (r, z) in enumerate(prof):
        if r < 1e-6:
            rings.append([len(v)])
            v.append((0, 0, z))
            continue
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg + phase
            rr = r * (rfn(a, k / max(1, n - 1)) if rfn else 1.0)
            ring.append(len(v))
            v.append((rr * math.cos(a), rr * math.sin(a), z))
        rings.append(ring)
    for k in range(n - 1):
        a, b = rings[k], rings[k + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(seg):
                f.append((a[0], b[(i + 1) % seg], b[i]))
        elif len(b) == 1:
            for i in range(seg):
                f.append((a[i], a[(i + 1) % seg], b[0]))
        else:
            for i in range(seg):
                j = (i + 1) % seg
                f.append((a[i], a[j], b[j], b[i]))
    if cap0 and len(rings[0]) > 1:
        f.append(tuple(reversed(rings[0])))
    if cap1 and len(rings[-1]) > 1:
        f.append(tuple(rings[-1]))
    return P(v, f)


def tube(path, r=0.05, seg=6, cap=True, twist=0.0):
    """sweep a circle along a 3D polyline; r = float or per-point list. Parallel-transport frames."""
    pts = [Vector(p) for p in path]
    n = len(pts)
    rs = r if isinstance(r, (list, tuple, np.ndarray)) else [r] * n
    tang = []
    for i in range(n):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])
        tang.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    up = Vector((0, 0, 1)) if abs(tang[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = tang[0].cross(up).normalized()
    v, f = [], []
    for i in range(n):
        if i:
            ax = tang[i - 1].cross(tang[i])
            if ax.length > 1e-9:
                ang = tang[i - 1].angle(tang[i])
                nrm = Matrix.Rotation(ang, 3, ax.normalized()) @ nrm
        bin_ = tang[i].cross(nrm).normalized()
        for k in range(seg):
            a = 2 * math.pi * k / seg + twist * i
            d = nrm * math.cos(a) + bin_ * math.sin(a)
            v.append(tuple(pts[i] + d * rs[i]))
    for i in range(n - 1):
        for k in range(seg):
            j = (k + 1) % seg
            f.append((i * seg + k, i * seg + j, (i + 1) * seg + j, (i + 1) * seg + k))
    if cap:
        f.append(tuple(reversed(range(seg))))
        f.append(tuple(range((n - 1) * seg, n * seg)))
    return P(v, f)


def arc(a, b, lift, n=8, side=(0, 0, 0)):
    """polyline from a to b bowing up by `lift` (and sideways by vector `side`) -- roots, ribs, ropes."""
    A, B, S = Vector(a), Vector(b), Vector(side)
    out = []
    for i in range(n + 1):
        t = i / n
        p = A.lerp(B, t) + Vector((0, 0, lift * 4 * t * (1 - t))) + S * (4 * t * (1 - t))
        out.append(tuple(p))
    return out


def rock(r=0.3, seed=0, sub=2, amp=0.28, freq=1.6, squash=(1, 1, 0.7), flat=0.3):
    """noise-displaced icosphere, flattened underside, base at z=0."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    o = Vector((seed * 3.7, seed * 1.3, seed * 2.1))
    for v in bm.verts:
        d = v.co.normalized()
        k = 1.0 + amp * mnoise.noise(d * freq + o) + amp * 0.4 * mnoise.noise(d * freq * 2.7 - o)
        v.co = Vector((v.co.x * k * squash[0], v.co.y * k * squash[1], v.co.z * k * squash[2]))
        v.co.z = max(v.co.z, -flat * r)
    p = from_bm(bm)
    p.v[:, 2] -= p.v[:, 2].min()
    return p


def canopy(r=1.0, seed=0, lumps=4, sub=2, squash=0.65, spread=0.55):
    """foliage mass: overlapping noise blobs. Base around z=0."""
    rng = random.Random(seed)
    ps = []
    for i in range(lumps):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.2, spread) * r if i else 0.0
        rr = r * rng.uniform(0.55, 0.8) if i else r * 0.75
        b = rock(rr, seed=seed * 31 + i, sub=sub, amp=0.32, freq=1.9, squash=(1, 1, squash), flat=0.9)
        ps.append(xf(b, (d * math.cos(a), d * math.sin(a), rng.uniform(-0.1, 0.25) * r)))
    return join(ps)


def strip_mesh(path, widths, heights=None, fold=0.0, tears=0.0, seed=0, up=(0, 0, 1)):
    """leaf/cloth ribbon along a 3D path: widths per point, V-fold along the midrib (fold = depth ratio),
    jagged tears on the edges. Two-sided material expected."""
    rng = random.Random(seed)
    pts = [Vector(p) for p in path]
    n = len(pts)
    U = Vector(up)
    v, f = [], []
    for i in range(n):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        side = t.cross(U)
        if side.length < 1e-6:
            side = Vector((1, 0, 0))
        side.normalize()
        w = widths[i]
        cut = 1.0 - (tears * rng.random() if 0 < i < n - 1 else 0.0)
        drop = t.cross(side).normalized() * (fold * w)
        v.append(tuple(pts[i] - side * w * cut + drop))
        v.append(tuple(pts[i]))
        v.append(tuple(pts[i] + side * w * (1.0 - (tears * rng.random() if 0 < i < n - 1 else 0.0)) + drop))
    for i in range(n - 1):
        a, b = 3 * i, 3 * (i + 1)
        f.append((a, b, b + 1, a + 1))
        f.append((a + 1, b + 1, b + 2, a + 2))
    return P(v, f)


def grid(sx, sy, nx, ny, z=0.0):
    """flat subdivided rectangle centred at origin."""
    v, f = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            v.append(((i / nx - 0.5) * sx, (j / ny - 0.5) * sy, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            f.append((a, a + 1, a + nx + 2, a + nx + 1))
    return P(v, f)


def extrude(path2d, prof, zfn=None, step=0.4, jitter=0.0, seed=0, cap=True):
    """sweep a cross-section [(offset, z), ...] (left->right) along a 2D path, sampled every `step` m.
    zfn(x, y) adds ground height. jitter wobbles width/height (organic bunds, banks)."""
    pts = []
    for (x0, y0), (x1, y1) in zip(path2d[:-1], path2d[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(round(L / step)))
        for i in range(k):
            pts.append((x0 + (x1 - x0) * i / k, y0 + (y1 - y0) * i / k))
    pts.append(tuple(path2d[-1]))
    m = len(prof)
    v, f = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1.0
        nx_, ny_ = -ty / l, tx / l
        jw = 1.0 + jitter * nz(x, y, 0, 0.9, seed)
        jz = jitter * 0.5 * nz(x, y, 5, 1.7, seed + 1)
        g = zfn(x, y) if zfn else 0.0
        for (o, z) in prof:
            v.append((x + nx_ * o * jw, y + ny_ * o * jw, g + z * (1.0 + jz)))
    for i in range(len(pts) - 1):
        for k in range(m - 1):
            a = i * m + k
            f.append((a, a + m, a + m + 1, a + 1))
    if cap:
        f.append(tuple(range(m)))
        f.append(tuple(range(len(v) - 1, len(v) - m - 1, -1)))
    return P(v, f)


# ============================================================== reusable kit pieces
def post(h, r=0.07, seed=0, seg=7, lean=0.03):
    """rough round timber post, slightly leaning, tapered, base at z=0."""
    rng = random.Random(seed)
    la = rng.uniform(0, 2 * math.pi)
    path = [(lean * h * t * math.cos(la), lean * h * t * math.sin(la), h * t) for t in (0, 0.33, 0.66, 1.0)]
    return tube(path, [r * 1.08, r, r * 0.97, r * 0.92], seg=seg)


def plank(L, w=0.18, t=0.035, bev=0.008, seed=0, warp=0.0):
    """board along X, base at z=0, centred."""
    p = box(L, w, t, bev=bev)
    if warp:
        p.v[:, 2] += warp * (1 - (2 * p.v[:, 0] / L) ** 2)
    return p


def thatch_roof(w, d, rise, courses=5, over=0.35, thick=0.07, seed=0, tooth=0.05, cw=0.25):
    """gable atap/thatch roof: two slopes of overlapping courses with jagged eaves, ridge along X.
    Base (eave level) at z=0, centred. Returns piece (Thatch material)."""
    rng = random.Random(seed)
    W = w + 2 * over
    half = d / 2 + over
    L = math.hypot(half, rise)
    ps = []
    cols = max(4, int(W / cw))
    for side in (-1, 1):
        for c in range(courses):
            t0 = c / courses
            t1 = min(1.0, (c + 1.35) / courses)  # overlap the next course
            v, f = [], []
            for i in range(cols + 1):
                x = (i / cols - 0.5) * W
                drop = tooth * rng.random()
                for t, extra in ((t0, drop), (t1, 0.0)):
                    yy = side * half * (1 - t)
                    zz = rise * t - extra
                    v.append((x, yy, zz))
            for i in range(cols):
                a = 2 * i
                f.append((a, a + 1, a + 3, a + 2) if side > 0 else (a, a + 2, a + 3, a + 1))
            sheet = P(v, f)
            # thickness lip on the eave edge of each course
            lip_v, lip_f = [], []
            for i in range(cols + 1):
                x, yy, zz = v[2 * i]
                lip_v.append((x, yy, zz))
                lip_v.append((x, yy + side * 0.0, zz - thick))
            for i in range(cols):
                a = 2 * i
                lip_f.append((a, a + 2, a + 3, a + 1) if side > 0 else (a, a + 1, a + 3, a + 2))
            ps.append(join(sheet, P(lip_v, lip_f)))
    ridge = tube([(-W / 2, 0, rise + 0.02), (W / 2, 0, rise + 0.02)], 0.08, seg=6)
    return join(dbl(join(ps)), ridge)


def barrel(r=0.27, h=0.62, seg=16):
    """stave barrel (Wood) + hoops (Metal); upright, base at z=0. Returns (wood, metal)."""
    prof = [(0.0, 0.0), (r * 0.86, 0.0), (r * 0.98, h * 0.25), (r, h * 0.5), (r * 0.98, h * 0.75),
            (r * 0.86, h), (r * 0.80, h), (r * 0.80, h * 0.97), (0.0, h * 0.97)]
    wood = lathe(prof, seg=seg, cap0=False, cap1=False)
    hoops = [lathe([(r * k + 0.004, z - 0.02), (r * k + 0.012, z), (r * k + 0.004, z + 0.02)], seg=seg,
                   cap0=False, cap1=False) for k, z in ((0.9, h * 0.1), (0.99, h * 0.36), (0.99, h * 0.64),
                                                       (0.9, h * 0.9))]
    return wood, join(hoops)


def rope_coil(R=0.42, r=0.035, turns=3.2, layers=2, seed=0):
    """flat coiled rope (spiral, stacked layers) + a loose tail. base at z=0."""
    rng = random.Random(seed)
    path = []
    n = int(turns * 22)
    for L in range(layers):
        for i in range(n):
            t = i / n
            a = 2 * math.pi * turns * t + L * 0.7
            rr = R * (0.35 + 0.65 * (1 - t)) if L % 2 == 0 else R * (0.35 + 0.65 * t)
            rr *= 1 + 0.03 * math.sin(a * 3 + seed)
            path.append((rr * math.cos(a), rr * math.sin(a), r + L * r * 1.7 + 0.004 * rng.random()))
    end = Vector(path[-1])
    tail = [tuple(end + Vector((0.12 * k, -0.18 * k + 0.03 * math.sin(k * 2), -r * 0.3 * min(k, 1)))) for k in
            (0.5, 1, 1.6, 2.2, 2.8)]
    return tube(path + tail, r, seg=6, twist=0.0)


def caping(r=0.26, h=0.11, seg=18):
    """conical woven hat (Thatch); crown up, base at z=0 (brim edge)."""
    return lathe([(r, 0.0), (r * 0.97, 0.012), (r * 0.6, h * 0.55), (r * 0.15, h * 0.95), (0.0, h)], seg=seg,
                 cap0=True, cap1=False)


def basket(r=0.17, h=0.2, seg=14):
    prof = [(0.0, 0.0), (r * 0.72, 0.0), (r * 0.95, h * 0.6), (r, h), (r * 1.06, h), (r * 1.06, h * 1.06),
            (r * 0.93, h * 1.04), (r * 0.9, h * 0.6), (r * 0.68, h * 0.06), (0.0, h * 0.06)]
    return lathe(prof, seg=seg, cap0=False, cap1=False)


def jar(r=0.22, h=0.5, seg=16):
    """tempayan / clay jar, base at z=0."""
    prof = [(0.0, 0.0), (r * 0.55, 0.0), (r * 0.95, h * 0.35), (r, h * 0.55), (r * 0.7, h * 0.85),
            (r * 0.5, h * 0.92), (r * 0.58, h), (r * 0.45, h), (r * 0.4, h * 0.9), (0.0, h * 0.86)]
    return lathe(prof, seg=seg, cap0=False, cap1=False)


def seedling_bundle(h=0.32, n=11, seed=0):
    """tied bundle of rice seedlings (Leaf)."""
    rng = random.Random(seed)
    ps = []
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        spread = rng.uniform(0.04, 0.12)
        tip = (spread * math.cos(a), spread * math.sin(a), h * rng.uniform(0.75, 1.1))
        ps.append(tube([(0, 0, 0), (tip[0] * 0.3, tip[1] * 0.3, tip[2] * 0.45), tip], [0.012, 0.009, 0.002], seg=3,
                       cap=False))
    return join(ps)


def wheel(R=0.3, r=0.02, spokes=6):
    """iron hand-wheel in the XZ plane, centred at origin."""
    rim = [(R * math.cos(2 * math.pi * i / 24), 0, R * math.sin(2 * math.pi * i / 24)) for i in range(25)]
    ps = [tube(rim, r, seg=5, cap=False)]
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        ps.append(tube([(0, 0, 0), (R * math.cos(a), 0, R * math.sin(a))], r * 0.7, seg=4))
    ps.append(xf(lathe([(0, -0.04), (0.05, -0.04), (0.05, 0.04), (0, 0.04)], seg=8), rot=(math.pi / 2, 0, 0)))
    return join(ps)


def mangrove(h=4.0, seed=0, roots=11, lod=0):
    """mangrove: dense skirt of arching prop roots, short leaning trunk, broad clumped canopy that reads
    as one dark mass. Returns (wood, leaf); base at z=0. lod=1: far-set version (fewer roots/lumps)."""
    rng = random.Random(seed)
    if lod:
        roots = 4
    lean = (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2))
    hub = Vector((lean[0] * 0.2, lean[1] * 0.2, 0.55 + 0.15 * rng.random()))
    top = Vector((lean[0] * h * 0.2, lean[1] * h * 0.2, h * 0.5))
    wood = [tube([tuple(hub - Vector((0, 0, 0.2))), tuple(hub.lerp(top, 0.5) + Vector((0.06, -0.04, 0))), tuple(top)],
                 [0.12, 0.1, 0.08], seg=7)]
    for k in range(roots):
        a = 2 * math.pi * k / roots + rng.uniform(-0.25, 0.25)
        R = rng.uniform(0.55, 1.05) * (h / 4.0) ** 0.5
        start = hub + Vector((0.05 * math.cos(a), 0.05 * math.sin(a), rng.uniform(-0.15, 0.35)))
        end = (R * math.cos(a), R * math.sin(a), -0.05)
        wood.append(tube(arc(tuple(start), end, lift=0.28, n=4), [0.05, 0.045, 0.038, 0.032, 0.028], seg=4))
    for k in range(0 if lod else 3):  # branches into the canopy
        a = rng.uniform(0, 2 * math.pi)
        b0 = hub.lerp(top, rng.uniform(0.6, 0.95))
        b1 = b0 + Vector((math.cos(a) * h * 0.25, math.sin(a) * h * 0.25, h * 0.15))
        wood.append(tube([tuple(b0), tuple(b1)], [0.05, 0.025], seg=5))
    leaf = [xf(canopy(h * 0.34, seed=seed * 7, lumps=2 if lod else 3, squash=0.55, spread=0.7), tuple(top + Vector((0, 0, -0.25))))]
    for k in range(1 if lod else 2):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.35, 0.6) * h * 0.4
        c = top + Vector((d * math.cos(a), d * math.sin(a), rng.uniform(-0.45, 0.1)))
        leaf.append(xf(canopy(h * rng.uniform(0.2, 0.26), seed=seed * 7 + k + 1, lumps=2, squash=0.6), tuple(c)))
    return join(wood), join(leaf)


def banana(h=2.6, seed=0, leaves=6):
    """banana plant: pseudo-stem + arching tattered leaves. Returns (stem, leaf); base at z=0."""
    rng = random.Random(seed)
    stem = tube([(0, 0, 0), (0.02, 0.0, h * 0.5), (0.04, 0.02, h * 0.85)], [0.11, 0.09, 0.07], seg=8)
    lv = []
    for k in range(leaves):
        a = 2 * math.pi * k / leaves + rng.uniform(-0.3, 0.3)
        L = h * rng.uniform(0.55, 0.8)
        base = Vector((0.04, 0.02, h * 0.85))
        rise = rng.uniform(0.25, 0.6)
        path, widths = [], []
        for i in range(9):
            t = i / 8
            out = L * t
            z = rise * L * math.sin(t * math.pi * 0.8) - L * 0.5 * t * t * rng.uniform(0.6, 1.0)
            path.append(tuple(base + Vector((out * math.cos(a), out * math.sin(a), z))))
            widths.append(0.02 + 0.2 * math.sin(math.pi * min(t * 1.15, 1.0)) * (L / 1.8))
        lv.append(strip_mesh(path, widths, fold=0.25, tears=0.35, seed=seed * 13 + k))
    return stem, join(lv)


def coconut_palm(h=7.0, seed=0, fronds=9):
    """coconut palm, curved ringed trunk + drooping fronds. Returns (trunk, leaf). Cheap: for far sets."""
    rng = random.Random(seed)
    la = rng.uniform(0, 2 * math.pi)
    bend = rng.uniform(0.6, 1.4)
    path = [(bend * t * t * h * 0.18 * math.cos(la), bend * t * t * h * 0.18 * math.sin(la), h * t)
            for t in np.linspace(0, 1, 6)]
    trunk = tube(path, [0.2, 0.17, 0.15, 0.14, 0.13, 0.12], seg=5)
    top = Vector(path[-1])
    lv = []
    for k in range(fronds):
        a = 2 * math.pi * k / fronds + rng.uniform(-0.2, 0.2)
        L = rng.uniform(2.8, 3.8)
        up = rng.uniform(0.3, 1.1)
        p, w = [], []
        for i in range(5):
            t = i / 4
            p.append(tuple(top + Vector((L * t * math.cos(a), L * t * math.sin(a), up * t - (up + 1.4) * t * t))))
            w.append(0.05 + 0.36 * math.sin(math.pi * min(1, t * 1.2)))
        lv.append(strip_mesh(p, w, fold=-0.35, tears=0.25, seed=seed * 5 + k))
    return trunk, join(lv)


def perahu(L=5.0, W=1.1, H=0.6, seed=0):
    """fishing boat hull (Wood) with raised bow/stern posts, plank strakes; base at z=0, long axis X.
    Returns hull piece; paint it per-vertex (use z for strake bands)."""
    n, prof = 11, 7
    v, f = [], []
    for i in range(n):
        t = i / (n - 1)
        x = (t - 0.5) * L
        w = W * max(0.04, math.sin(math.pi * t) ** 0.6)
        lift = 0.5 * H * (2 * t - 1) ** 4
        for k in range(prof):
            s = k / (prof - 1)  # 0 port gunwale -> 1 starboard gunwale
            a = math.pi * s
            v.append((x, -w * math.cos(a), H + lift - H * math.sin(a) ** 0.8))
    for i in range(n - 1):
        for k in range(prof - 1):
            a = i * prof + k
            f.append((a, a + 1, a + prof + 1, a + prof))
    hull = P(v, f)
    # gunwale rail + bow/stern posts
    rail_l = [(v[i * prof][0], v[i * prof][1], v[i * prof][2]) for i in range(n)]
    rail_r = [(v[i * prof + prof - 1][0], v[i * prof + prof - 1][1], v[i * prof + prof - 1][2]) for i in range(n)]
    bow = tube([(L / 2 - 0.05, 0, H * 1.3), (L / 2 + 0.25, 0, H * 2.1)], [0.06, 0.04], seg=5)
    stern = tube([(-L / 2 + 0.05, 0, H * 1.3), (-L / 2 - 0.2, 0, H * 1.9)], [0.06, 0.04], seg=5)
    thwarts = [xf(box(0.12, W * 1.5, 0.04, bev=0.01), (x, 0, H * 0.75)) for x in (-L * 0.2, L * 0.1)]
    return join(dbl(hull), tube(rail_l, 0.03, seg=4), tube(rail_r, 0.03, seg=4), bow, stern, thwarts)


def karst(h=20.0, r=7.0, seed=0, seg=26, rings=11, cliff=0.25, taper=0.25):
    """limestone tower karst: steep fluted walls, overhang bulge, a sheer cliff side, domed top. base z=-1."""
    rng = random.Random(seed)
    o = Vector((seed * 1.7, seed * 0.3, 0))
    a0 = rng.uniform(0, 2 * math.pi)

    def prof(t):  # radius multiplier vs height: skirt at the foot, steep walls, rounded haystack crown
        return (1.0 + 0.25 * max(0.0, 0.12 - t) / 0.12) * (1 - taper * t) *             (math.sqrt(max(0.0, 1 - ((t - 0.62) / 0.38) ** 2)) if t > 0.62 else 1.0)

    v, f = [], []
    lean = Vector((rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), 0))
    for k in range(rings):
        t = k / (rings - 1)
        z = -1 + (h + 1) * t
        for i in range(seg):
            a = 2 * math.pi * i / seg
            d = Vector((math.cos(a), math.sin(a), 0))
            nn = mnoise.noise(d * 1.6 + o + Vector((0, 0, t * 2.2)))
            flute = 0.07 * math.sin(a * 9 + 2 * mnoise.noise(d * 3 + o))
            rr = r * max(0.08, prof(t)) * (1 + 0.28 * nn + flute) * (1 + cliff * math.cos(a - a0) * (0.4 + t))
            zz = z + (0.18 * r * mnoise.noise(d * 2.2 + o + Vector((0, 0, 9))) * (t - 0.6) / 0.4 if t > 0.6 else 0.0)  # ragged crown
            v.append((rr * d.x + lean.x * z, rr * d.y + lean.y * z, zz))
    cap = len(v)
    v.append((lean.x * h, lean.y * h, h + 0.04 * r))
    for k in range(rings - 1):
        for i in range(seg):
            j = (i + 1) % seg
            a = k * seg
            f.append((a + i, a + j, a + seg + j, a + seg + i))
    for i in range(seg):
        a = (rings - 1) * seg
        f.append((a + i, a + (i + 1) % seg, cap))
    return P(v, f)


def paint_karst(p, rock_rgb=(0.66, 0.64, 0.6), streak_rgb=(0.36, 0.36, 0.35), veg_rgb=(0.22, 0.31, 0.16), seed=0):
    n = vnormals(p)
    z = p.v[:, 2]
    zt = (z - z.min()) / max(1e-6, z.max() - z.min())
    streak = 0.5 + 0.5 * nfield(p.v, 0.35, seed, stretch=(1, 1, 0.08))
    c = np.asarray(rock_rgb)[None, :] * (1 - 0.45 * streak[:, None]) + np.asarray(streak_rgb)[None, :] * 0.45 * streak[:, None]
    veg = np.clip(smooth01(0.25, 0.6, n[:, 2]) + smooth01(0.82, 0.95, zt) + 0.35 * smooth01(0.3, 0.8, nfield(p.v, 0.25, seed + 5)), 0, 1)
    c = c * (1 - veg[:, None]) + np.asarray(veg_rgb)[None, :] * veg[:, None]
    c *= (0.75 + 0.25 * smooth01(0.0, 0.25, zt))[:, None]
    p.c = np.ones((len(p.v), 4))
    p.c[:, :3] = np.clip(c, 0, 1)
    return p


# ============================================================== the arena accumulator
class Arena:
    """Collects pieces per (set, material), terrain, scatter, lights, contacts. One per build."""

    def __init__(self, arena_id):
        self.id = arena_id
        self.buckets = {}      # (set, name) -> [P]
        self.contacts = []     # (x, y, radius, strength) -> terrain darkening
        self.lights = []       # (name, pos, watts, rgb)
        self.mats = {}

    def mat(self, name, rough=None, metal=None, emit=None, estr=0.0, two_sided=None):
        kind = kind_of(name)
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        if m.node_tree is None:
            m.use_nodes = True
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        vc = nt.nodes.get("VCol") or nt.nodes.new("ShaderNodeVertexColor")
        vc.name = "VCol"
        vc.layer_name = "Col"
        nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = ROUGH[kind] if rough is None else rough
        bsdf.inputs["Metallic"].default_value = (0.75 if kind == "Metal" else 0.0) if metal is None else metal
        if emit is not None:
            bsdf.inputs["Emission Color"].default_value = (emit[0], emit[1], emit[2], 1.0)
            bsdf.inputs["Emission Strength"].default_value = estr
        m.use_backface_culling = not (kind in TWO_SIDED if two_sided is None else two_sided)
        self.mats[name] = m
        return name

    def add(self, set_, name, *pieces):
        assert set_ in ("battle", "far", "scatter"), set_
        if set_ != "scatter":
            assert name in self.mats, "declare material first: " + name
        for p in _flat(pieces):
            if p is not None and len(p.v):
                if p.c is None:
                    p.c = np.ones((len(p.v), 4))
                self.buckets.setdefault((set_, name), []).append(p)

    def contact(self, x, y, r, k=0.35):
        """darken terrain vertex colour around a prop footprint (ambient-occlusion pool)."""
        self.contacts.append((x, y, r, k))

    def light(self, pos, watts, rgb=(1.0, 0.7, 0.4), range_m=None):
        """KHR point light; Godot energy = watts * 0.02, range = range_m (default 5 m) -- see arena_dress.gd."""
        n = len(self.lights)
        name = "EnvLight_%d" % n + ("_r%d" % int(round(range_m)) if range_m else "")
        self.lights.append((name, pos, watts, rgb))

    # ------------------------------------------------------------- terrain
    def terrain(self, height, color, kind=None, rin=4.5, rout=62.0, split=23.0, spacing=None, cull=None,
                jit=0.25, seed=0):
        """dense polar ground (rings stitched with a zipper so density can fall off with radius).
        height(x,y)->z ; color(x,y,z)->(r,g,b[,a]) sRGB ; kind(x,y,z)->material name (default first
        Ground material) ; cull(cx,cy,zmax)->True drops the face (e.g. hidden under opaque water).
        Faces with centroid r<split go to the battle set, the rest to far."""
        sp = spacing or (lambda r: 0.3 if r < 12 else (0.3 + 0.07 * (r - 12) if r < 22 else min(14.0, 1.5 + 0.25 * (r - 22))))
        rng = np.random.default_rng(seed)
        radii = [rin]
        while radii[-1] < rout:
            radii.append(radii[-1] + sp(radii[-1]))
        V, loops = [], []
        for k, r in enumerate(radii):
            n = max(24, int(round(2 * math.pi * r / sp(r))))
            loop = []
            for i in range(n):
                a = 2 * math.pi * i / n
                rr = r
                if 0 < k < len(radii) - 1:  # jitter interior verts to kill grid regularity
                    rr += rng.uniform(-jit, jit) * sp(r)
                    a += rng.uniform(-jit, jit) * sp(r) / r
                loop.append(len(V))
                V.append((rr * math.cos(a), rr * math.sin(a)))
            loops.append(loop)
        V = np.array(V)
        Z = np.array([height(x, y) for x, y in V])
        P3 = np.column_stack([V, Z])
        C = np.ones((len(V), 4))
        for i, (x, y, z) in enumerate(P3):
            c = color(x, y, z)
            C[i, :len(c)] = c
        if self.contacts:  # contact darkening pools
            for (cx, cy, cr, ck) in self.contacts:
                d = np.hypot(V[:, 0] - cx, V[:, 1] - cy)
                C[:, :3] *= (1.0 - ck * (1.0 - smooth01(cr * 0.35, cr, d)))[:, None]
        tris = []
        for a, b in zip(loops[:-1], loops[1:]):
            tris.extend(_zip(a, b))
        default = next((m for m in self.mats if kind_of(m) == "Ground"), None)
        groups = {}
        for t in tris:
            pts = P3[list(t)]
            cx, cy, cz = pts.mean(axis=0)
            if cull and cull(cx, cy, pts[:, 2].max()):
                continue
            m = kind(cx, cy, cz) if kind else default
            s = "battle" if math.hypot(cx, cy) < split else "far"
            groups.setdefault((s, m), []).append(t)
        for (s, m), fl in groups.items():
            idx = np.unique(np.array(fl).ravel())
            remap = {int(o): i for i, o in enumerate(idx)}
            self.add(s, m, P(P3[idx], [tuple(remap[i] for i in t) for t in fl], C[idx]))

    # ------------------------------------------------------------- scatter sources
    def scatter(self, kind, density, piece):
        """hidden MultiMesh source: triangles (any faces) whose area x density = instance count.
        Vertex colour = blade tint. Runtime builds the blades (scripts/arena_dress.gd)."""
        assert kind in SCATTER_KINDS
        self.add("scatter", "EnvScatter%s_%d" % (kind, int(round(density))), piece)

    def scatter_strip(self, kind, density, a, b, width, zfn, rgb, step=0.6):
        """a row (paddy row, bund verge) from a to b (2D), draped on zfn."""
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx_, ny_ = -ty * width / 2, tx * width / 2
        v, f = [], []
        for i in range(n + 1):
            x, y = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
            v += [(x - nx_, y - ny_, zfn(x - nx_, y - ny_) + 0.01), (x + nx_, y + ny_, zfn(x + nx_, y + ny_) + 0.01)]
        for i in range(n):
            f.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
        p = P(v, f)
        p.c = np.tile(list(rgb[:3]) + [1.0], (len(v), 1))
        self.scatter(kind, density, p)

    def scatter_patch(self, kind, density, cx, cy, r, zfn, rgb, n=10, seed=0, var=0.08):
        """irregular disc patch (grass clump around a prop, verge)."""
        rng = random.Random(seed)
        v = [(cx, cy, zfn(cx, cy) + 0.01)]
        for i in range(n):
            a = 2 * math.pi * i / n
            rr = r * rng.uniform(0.6, 1.15)
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            v.append((x, y, zfn(x, y) + 0.01))
        f = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
        p = P(v, f)
        p.c = np.array([[min(1, c * (1 + rng.uniform(-var, var))) for c in rgb[:3]] + [1.0] for _ in v])
        self.scatter(kind, density, p)

    # ------------------------------------------------------------- build Blender objects
    def finish(self):
        """create EnvBattle_/EnvFar_/EnvScatter objects + EnvLight lights in the current scene."""
        for (s, name), ps in sorted(self.buckets.items()):
            p = join(ps)
            oname = name if s == "scatter" else ("EnvBattle_" if s == "battle" else "EnvFar_") + name
            me = bpy.data.meshes.new(oname)
            me.from_pydata(p.v.tolist(), [], p.f)
            me.validate(clean_customdata=False)
            ca = me.color_attributes.new("Col", 'BYTE_COLOR', 'POINT')
            ca.data.foreach_set("color_srgb", np.clip(p.c, 0, 1).astype(np.float32).ravel())
            me.color_attributes.active_color = ca
            me.color_attributes.render_color_index = 0
            if s != "scatter":
                me.materials.append(self.mats[name])
                me.shade_smooth()
                if kind_of(name) in SHARP_KINDS:
                    me.set_sharp_from_angle(angle=math.radians(SHARP_DEG))
            ob = bpy.data.objects.new(oname, me)
            bpy.context.scene.collection.objects.link(ob)
            if s == "scatter":
                ob.hide_render = True
                ob.display_type = 'WIRE'
        for (name, pos, watts, rgb) in self.lights[:BUDGET["lights"]]:
            ld = bpy.data.lights.new(name, 'POINT')
            ld.energy = watts
            ld.color = rgb
            ld.shadow_soft_size = 0.05
            ld.use_shadow = False
            ob = bpy.data.objects.new(name, ld)
            ob.location = pos
            bpy.context.scene.collection.objects.link(ob)


def kind_of(name):
    assert name.startswith("Mat") and "_" in name, "material must be Mat<Kind>_<variant>: " + name
    k = name[3:name.index("_")]
    assert k in KINDS, "unknown kind %s (KINDS=%s)" % (k, KINDS)
    return k


def _zip(a, b):
    """stitch two closed angle-ordered loops (inner a, outer b) with CCW triangles."""
    n, m = len(a), len(b)
    i = j = 0
    out = []
    while i < n or j < m:
        if j >= m or (i < n and (i + 1) / n < (j + 1) / m):
            out.append((a[i % n], b[j % m], a[(i + 1) % n]))
            i += 1
        else:
            out.append((a[i % n], b[j % m], b[(j + 1) % m]))
            j += 1
    return out


# ============================================================== checks / reports
def zone_of(x, y, r=None):
    """Godot design zones (design_art.md section c) in Blender coords (+y far)."""
    r = math.hypot(x, y) if r is None else r
    if r < 4.5:
        return "Z0"
    if r < 6.0:
        return "Z1"
    if y > 13 or r > 23:
        return "Z6"
    if y < -4.5:
        return "Z5"
    if x < -6.5 and -4 <= y <= 6:
        return "Z3"
    if x > 6.5 and -1 <= y <= 8:
        return "Z4"
    if 4.5 <= y <= 9:
        return "Z2"
    return "other"


def _env_meshes():
    return [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("Env")]


def check_exclusion():
    """Z0: no verts r<4.49. Z1: nothing taller than 0.6 within r<6. Z5: <=1.2 m within |x|<5, y<-4.5."""
    bad = {"Z0_inside_r4.5": [], "Z1_tall_within_r6": [], "Z5_tall_near_strip": []}
    for o in _env_meshes():
        if o.name.startswith("EnvScatter"):
            continue
        v = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", v)
        v = v.reshape(-1, 3)
        r = np.hypot(v[:, 0], v[:, 1])
        if (r < 4.49).any():
            bad["Z0_inside_r4.5"].append((o.name, round(float(r.min()), 2)))
        m = (r < 6.0) & (v[:, 2] > 0.6)
        if m.any():
            bad["Z1_tall_within_r6"].append((o.name, round(float(v[m, 2].max()), 2)))
        m = (v[:, 1] < -4.5) & (np.abs(v[:, 0]) < 5) & (v[:, 2] > 1.2)
        if m.any():
            bad["Z5_tall_near_strip"].append((o.name, round(float(v[m, 2].max()), 2)))
    bad["ok"] = not any(bad[k] for k in list(bad))
    return bad


def tri_report():
    rep = {"battle": 0, "far": 0, "scatter": 0, "objects": {}, "zones": {}}
    for o in _env_meshes():
        me = o.data
        me.calc_loop_triangles()
        n = len(me.loop_triangles)
        s = "scatter" if o.name.startswith("EnvScatter") else ("battle" if o.name.startswith("EnvBattle") else "far")
        rep[s] += n
        rep["objects"][o.name] = n
        if s == "scatter":
            continue
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        idx = np.empty(n * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("vertices", idx)
        cen = co[idx.reshape(-1, 3)].mean(axis=1)
        for cx, cy, _ in cen:
            z = zone_of(cx, cy)
            rep["zones"][z] = rep["zones"].get(z, 0) + 1
    return rep


def scatter_report():
    out, total = {}, 0
    for o in _env_meshes():
        if not o.name.startswith("EnvScatter"):
            continue
        me = o.data
        me.calc_loop_triangles()
        area = sum(t.area for t in me.loop_triangles)
        dens = float(o.name.rsplit("_", 1)[1])
        out[o.name] = {"area_m2": round(area, 1), "instances": int(area * dens)}
        total += int(area * dens)
    return {"sources": out, "instances_before_cap": total, "cap": BUDGET["instances"]}


def glb_report(path):
    b = open(path, 'rb').read()
    n = struct.unpack_from('<I', b, 12)[0]
    j = json.loads(b[20:20 + n])
    attrs = [set(p["attributes"]) for m in j.get("meshes", []) for p in m["primitives"]]
    return {"bytes": len(b), "nodes": len(j.get("nodes", [])), "materials": [m["name"] for m in j.get("materials", [])],
            "all_have_COLOR_0": all("COLOR_0" in a for a in attrs),
            "any_TEXCOORD": any(any(k.startswith("TEXCOORD") for k in a) for a in attrs),
            "lights": len(j.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])),
            "extensions": j.get("extensionsUsed", [])}


def report(arena_id, glb=None, out=None):
    tr = tri_report()
    mats = sorted({o.data.materials[0].name for o in _env_meshes() if o.data.materials})
    far_mats = sorted({o.data.materials[0].name for o in _env_meshes() if o.name.startswith("EnvFar") and o.data.materials})
    rep = {"arena": arena_id, "tris": {"battle": tr["battle"], "far": tr["far"], "scatter_src": tr["scatter"]},
           "zones_battle_far": tr["zones"], "objects": tr["objects"], "materials": mats,
           "far_materials": far_mats, "exclusion": check_exclusion(), "scatter": scatter_report(),
           "lights": len([o for o in bpy.data.objects if o.type == 'LIGHT' and o.name.startswith("EnvLight")])}
    if glb and os.path.exists(glb):
        rep["glb"] = glb_report(glb)
    over = []
    if tr["battle"] > BUDGET["battle_tris"]: over.append("battle_tris")
    if tr["far"] > BUDGET["far_tris"]: over.append("far_tris")
    if tr["scatter"] > BUDGET["scatter_tris"]: over.append("scatter_tris")
    if len(mats) > BUDGET["materials"]: over.append("materials")
    if len(far_mats) > BUDGET["far_materials"]: over.append("far_materials")
    if rep["lights"] > BUDGET["lights"]: over.append("lights")
    if "glb" in rep and rep["glb"]["bytes"] > BUDGET["glb_bytes"]: over.append("glb_bytes")
    rep["over_budget"] = over
    rep["budget"] = BUDGET
    if out:
        with open(out, "w") as fh:
            json.dump(rep, fh, indent=1)
    return rep


# ============================================================== cameras / preview render
def _cam(name, loc, target, fov_deg):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle_y = math.radians(fov_deg)
    cam.data.clip_end = 600
    bpy.context.scene.camera = cam
    return cam


def cam_game():
    """battle camera: Godot (0,9,7) looking at the origin, vertical FOV 55."""
    return _cam("GameCam", (0, -7, 9), (0, 0, 0), 55)


def cam_vista():
    """hub/title VISTA: Godot pos (-1.5,3.2,12.5) looking at (-3,1.2,-2), vertical FOV 50."""
    return _cam("VistaCam", (-1.5, -12.5, 3.2), (-3.0, 2.0, 1.2), 50)


def wipe():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for x in list(coll):
            if x.users == 0:
                coll.remove(x)


def _srgb2lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c[:3])


def preview_rig(mood):
    """approximate the game's lighting: fixed sun (main.tscn Sun basis), sky gradient, fog, dish stand-in,
    two dark tops, 8 lanterns. Everything is named Preview* and never exported."""
    sc = bpy.context.scene
    # sun: Godot light dir (0.329,-0.819,-0.470) -> Blender (0.329, 0.470, -0.819)
    ld = bpy.data.lights.new("PreviewSun", 'SUN')
    ld.energy = mood.get("b_sun", 3.2)
    ld.color = _srgb2lin(mood["sun_color"])
    ld.angle = math.radians(2.0)
    sun = bpy.data.objects.new("PreviewSun", ld)
    sun.rotation_euler = Vector((0.329, 0.470, -0.819)).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(sun)
    fill = bpy.data.lights.new("PreviewFill", 'SUN')
    fill.energy = mood.get("b_fill", 0.5)
    fill.color = (0.55, 0.66, 0.90)
    fob = bpy.data.objects.new("PreviewFill", fill)
    fob.rotation_euler = Vector((-0.4, -0.5, -0.42)).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(fob)
    # world: horizon -> top gradient + optional volume fog
    w = bpy.data.worlds.new("PreviewWorld")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*_srgb2lin(mood["sky_horizon"]), 1)
    els[1].position, els[1].color = 0.55, (*_srgb2lin(mood["sky_top"]), 1)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = mood.get("b_world", 1.0)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    # dish stand-in (matches main.tscn Floor/Rim/Ground)
    def solid(name, p, rgb, rough=0.85, metal=0.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs["Base Color"].default_value = (*_srgb2lin(rgb), 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        me = bpy.data.meshes.new(name)
        me.from_pydata(p.v.tolist(), [], p.f)
        me.materials.append(m)
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(40))
        ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
        return ob
    solid("PreviewGround", grid(44, 44, 1, 1, -0.5), (0.25, 0.16, 0.09))
    solid("PreviewFloor", lathe([(0, -0.3), (4.45, -0.3), (4.2, 0.0), (0, 0.0)], seg=96), (0.6, 0.42, 0.23), 0.92)
    rim = [(4.15 * math.cos(2 * math.pi * i / 96), 4.15 * math.sin(2 * math.pi * i / 96), 0.02) for i in range(97)]
    solid("PreviewRim", tube(rim, 0.2, seg=10, cap=False), (0.34, 0.22, 0.12), 0.8)
    for i, (x, y) in enumerate(((0.9, -1.4), (-0.8, 1.1))):
        top = lathe([(0, 0), (0.05, 0.03), (0.38, 0.38), (0.44, 0.5), (0.36, 0.75), (0.18, 0.95), (0, 1.0)], seg=32)
        solid("PreviewTop%d" % i, xf(top, (x, y, 0)), (0.42, 0.24, 0.11), 0.4)
    for i in range(8):
        a = 2 * math.pi * i / 8
        l = bpy.data.lights.new("PreviewLantern%d" % i, 'POINT')
        l.energy = mood.get("b_lantern", 18.0)
        l.color = _srgb2lin(mood["lantern"])
        l.use_soft_falloff = True
        l.shadow_soft_size = 0.1
        lo = bpy.data.objects.new("PreviewLantern%d" % i, l)
        lo.location = (math.cos(a) * 4.25, math.sin(a) * 4.25, 0.85)
        sc.collection.objects.link(lo)


def _preview_fog(density, rgb):
    """Godot-like depth fog for previews: mix every material toward an unlit fog colour by 1-exp(-d*density).
    Runs after export (materials are only touched in the preview scene)."""
    for m in bpy.data.materials:
        if m.node_tree is None or m.node_tree.nodes.get("FogMix") or m.name.startswith("MatSky"):
            continue  # Sky kind is fog-free in Godot too
        nt = m.node_tree
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out is None or not out.inputs["Surface"].links:
            continue
        src = out.inputs["Surface"].links[0].from_socket
        cam = nt.nodes.new("ShaderNodeCameraData")
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = -density
        ex = nt.nodes.new("ShaderNodeMath"); ex.operation = 'EXPONENT'
        inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1); em.inputs["Strength"].default_value = 1.0
        mix = nt.nodes.new("ShaderNodeMixShader"); mix.name = "FogMix"
        nt.links.new(cam.outputs["View Distance"], mul.inputs[0])
        nt.links.new(mul.outputs[0], ex.inputs[0])
        nt.links.new(ex.outputs[0], inv.inputs[1])
        nt.links.new(inv.outputs[0], mix.inputs[0])
        nt.links.new(src, mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])


def preview_scatter(seed=7, cap=BUDGET["instances"]):
    """realise the EnvScatter sources as blade clumps so Blender previews show grass/paddy.
    Mirrors arena_dress.gd sampling (area x density, capped). Preview only."""
    srcs = [o for o in _env_meshes() if o.name.startswith("EnvScatter")]
    if not srcs:
        return
    rng = random.Random(seed)
    info = []
    total = 0.0
    for o in srcs:
        me = o.data
        me.calc_loop_triangles()
        dens = float(o.name.rsplit("_", 1)[1])
        kind = o.name[len("EnvScatter"):].split("_")[0]
        col = me.color_attributes["Col"].data
        tris = [(t.vertices[:], t.area) for t in me.loop_triangles]
        total += sum(a for _, a in tris) * dens
        info.append((me, kind, dens, col, tris))
    k = min(1.0, cap / max(total, 1.0))
    shapes = {"Grass": (5, 0.16, 0.28, 0.18, 0.006), "Paddy": (4, 0.32, 0.5, 0.06, 0.008), "Reed": (3, 0.8, 1.3, 0.12, 0.012)}
    v, f, c = [], [], []
    for me, kind, dens, col, tris in info:
        nb, h0, h1, spread, wid = shapes[kind]
        acc = 0.0
        for (ids, area) in tris:
            acc += area * dens * k
            while acc >= 1.0:
                acc -= 1.0
                r1, r2 = rng.random(), rng.random()
                if r1 + r2 > 1:
                    r1, r2 = 1 - r1, 1 - r2
                a, b, cc = (me.vertices[i].co for i in ids)
                pt = a + (b - a) * r1 + (cc - a) * r2
                tint = col[ids[0]].color_srgb
                hh = rng.uniform(h0, h1)
                yaw = rng.uniform(0, 2 * math.pi)
                for bl in range(nb):
                    ang = yaw + 2 * math.pi * bl / nb
                    lean = spread * rng.uniform(0.4, 1.0)
                    tip = pt + Vector((math.cos(ang) * lean, math.sin(ang) * lean, hh * rng.uniform(0.8, 1.1)))
                    side = Vector((-math.sin(ang), math.cos(ang), 0)) * wid
                    base = len(v)
                    v += [tuple(pt - side), tuple(pt + side), tuple(tip)]
                    f.append((base, base + 1, base + 2))
                    j = rng.uniform(0.85, 1.12)
                    c += [(tint[0] * 0.55 * j, tint[1] * 0.55 * j, tint[2] * 0.55 * j, 1)] * 2
                    c += [(min(1, tint[0] * 1.15 * j), min(1, tint[1] * 1.15 * j), min(1, tint[2] * 1.15 * j), 1)]
    me = bpy.data.meshes.new("PreviewScatter")
    me.from_pydata(v, [], f)
    ca = me.color_attributes.new("Col", 'BYTE_COLOR', 'POINT')
    ca.data.foreach_set("color_srgb", np.array(c, dtype=np.float32).ravel())
    m = bpy.data.materials.new("PreviewBlade")
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    nt.links.new(vc.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    me.materials.append(m)
    ob = bpy.data.objects.new("PreviewScatter", me)
    bpy.context.scene.collection.objects.link(ob)


def render(cam, path, res=(1600, 900), samples=16):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.eevee.taa_render_samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'None'
    sc.render.image_settings.file_format = 'PNG'
    (cam_game if cam == "game" else cam_vista)()
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return round(time.time() - t, 1)


# ============================================================== export / driver
def export_arena(arena_id, path=None):
    """GLB with COLOR_0, normals, no UVs, KHR point lights; Env* meshes + EnvLight* only."""
    path = path or os.path.join(ASSETS, "arena_%s.glb" % arena_id)
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if (o.type == 'MESH' and o.name.startswith("Env")) or (o.type == 'LIGHT' and o.name.startswith("EnvLight")):
            o.hide_set(False)
            o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                              export_texcoords=False, export_normals=True, export_tangents=False,
                              export_vertex_color='ACTIVE', export_all_vertex_colors=False,
                              export_lights=True, export_cameras=False, export_animations=False,
                              export_yup=True, export_extras=False)
    return path


def _argv(argv):
    if argv is None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"export": "--export" in argv, "render": [], "out": None, "res": (1600, 900), "samples": 16,
         "report": True}
    for i, a in enumerate(argv):
        if a == "--render":
            o["render"] = argv[i + 1].split(",")
        elif a == "--out":
            o["out"] = argv[i + 1]
        elif a == "--res":
            o["res"] = tuple(int(x) for x in argv[i + 1].split("x"))
        elif a == "--samples":
            o["samples"] = int(argv[i + 1])
    return o


def main(arena_id, build, mood, argv=None):
    """wipe -> build(Arena) -> finish -> [export] -> report JSON -> [preview renders]."""
    o = _argv(argv)
    out = o["out"] or os.path.join(__import__("tempfile").gettempdir(), "arena_preview")
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    wipe()
    A = Arena(arena_id)
    build(A)
    A.finish()
    glb = export_arena(arena_id) if o["export"] else None
    rep = report(arena_id, glb, os.path.join(out, "%s_report.json" % arena_id))
    rep["build_s"] = round(time.time() - t0, 1)
    print("ARENA_REPORT " + json.dumps({k: rep[k] for k in ("tris", "materials", "exclusion", "over_budget", "build_s")}
                                        | ({"glb": rep["glb"]} if "glb" in rep else {})
                                        | {"instances": rep["scatter"]["instances_before_cap"]}))
    if o["render"]:
        preview_rig(mood)
        preview_scatter()
        _preview_sky()
        if mood.get("fog_density", 0) > 0:
            _preview_fog(mood["fog_density"], _srgb2lin(mood["fog"]))
        for cam in o["render"]:
            p = os.path.join(out, "%s_%s.png" % (arena_id, cam))
            print("RENDER", cam, render(cam, p, o["res"], o["samples"]), "s ->", p)
    return rep


# ============================================================== v2.1 additions (arena-E, backward compatible; see KIT_CHANGES.md)
# Sky kind: unshaded, vertex-colour, fog-free painted backdrop (cloud cards, far ridge layers). arena_dress.gd
# renders MatSky_* with SHADING_MODE_UNSHADED + disable_fog + no culling + no shadows, so paint the haze in yourself
# (ridge_layer/cloud_card take the colours). Previews show Sky as emission (see _preview_sky).
KINDS = KINDS + ("Sky",)
ROUGH["Sky"] = 1.0
TWO_SIDED = TWO_SIDED + ("Sky",)

VISTA_EYE = (-1.5, -12.5, 3.2)   # hub/title camera, Blender coords (cam_vista)
VISTA_AZ = (-46.0, 34.0)         # visible azimuth range about VISTA_EYE: degrees from +y, positive toward +x


def compact(p):
    """drop unused vertices (after removing faces)."""
    if not p.f:
        return P(np.zeros((0, 3)), [])
    used = np.unique(np.fromiter((i for f in p.f for i in f), dtype=np.int64))
    remap = -np.ones(len(p.v), dtype=np.int64)
    remap[used] = np.arange(len(used))
    return P(p.v[used], [tuple(int(remap[i]) for i in f) for f in p.f], None if p.c is None else p.c[used])


def cull_back(p, eye=VISTA_EYE, margin=0.3):
    """drop faces turned away from a fixed camera (vista-only far props: karsts, hills, houses). A face goes only
    when every triangle of its fan points more than `margin` away from the eye, so silhouettes stay intact.
    Far set only (far meshes cast no shadows)."""
    E = np.asarray(eye, dtype=np.float64)
    keep = []
    for f in p.f:
        pts = p.v[list(f)]
        e = E - pts.mean(axis=0)
        e /= max(np.linalg.norm(e), 1e-9)
        tn = np.cross(pts[1:-1] - pts[0], pts[2:] - pts[0])
        ln = np.linalg.norm(tn, axis=1)
        ok = ln > 1e-12
        if ok.any() and ((tn[ok] / ln[ok, None]) @ e > -margin).any():
            keep.append(f)
    return compact(P(p.v, keep, p.c))


def at_vista(dist, az_deg, z=0.0, eye=VISTA_EYE):
    """world point at horizontal distance `dist` from the vista eye along azimuth az (deg from +y, + toward +x)."""
    a = math.radians(az_deg)
    return (eye[0] + dist * math.sin(a), eye[1] + dist * math.cos(a), z)


def face_eye(p, loc, eye=VISTA_EYE):
    """rotate a card built facing -y about Z so its front faces the eye, then move it to loc."""
    dx, dy = eye[0] - loc[0], eye[1] - loc[1]
    return xf(p, loc, (0, 0, math.atan2(dx, -dy)))


def elev_z(dist, el_deg, eye=VISTA_EYE):
    """height that appears at elevation el (deg above the eye's horizontal) at horizontal distance dist."""
    return eye[2] + dist * math.tan(math.radians(el_deg))


def smooth_rock(r=0.3, seed=0, sub=2, amp=0.22, freq=1.3, squash=(1, 1, 0.7), flat=0.3, relax=2):
    """rounded boulder/pebble: low-frequency noise on an icosphere + Laplacian relax passes (no faceted lumps).
    sub=1 (80 tris) for pebbles, 2 (320) for rocks, 3 (1280) for hero boulders. Base at z=0."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    o = Vector((seed * 3.7, seed * 1.3, seed * 2.1))
    for v in bm.verts:
        d = v.co.normalized()
        k = 1.0 + amp * mnoise.noise(d * freq + o) + amp * 0.35 * mnoise.noise(d * freq * 2.3 - o)
        v.co = Vector((d.x * r * k * squash[0], d.y * r * k * squash[1], d.z * r * k * squash[2]))
    for _ in range(relax):
        bmesh.ops.smooth_vert(bm, verts=list(bm.verts), factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    for v in bm.verts:
        v.co.z = max(v.co.z, -flat * r)
    p = from_bm(bm)
    p.v[:, 2] -= p.v[:, 2].min()
    return p


def smooth_karst(h=20.0, r=7.0, seed=0, seg=36, rings=20, cliff=0.2, taper=None, flutes=13, flute_depth=0.06,
                 notch=0.5, ledges=1, crown=None, lean=0.08, rock=(0.68, 0.66, 0.61), streak=(0.30, 0.30, 0.29),
                 stain=(0.60, 0.48, 0.35), veg=(0.19, 0.26, 0.13), veg2=(0.31, 0.37, 0.18), eye=None):
    """eroded limestone tower karst (smooth, painted; crown/taper None = random per seed): talus skirt + tidal/solution notch at the foot, steep walls
    with vertical fluting (grooves darker), ledges with vegetation, domed vegetated crown with canopy bumps and
    hanging green fringe, dark water streaks + orange iron stains. Base z=-1 (sink into terrain).
    eye: cull faces turned away from that camera (far set only). Returns a painted piece (Rock material)."""
    rng = random.Random(seed)
    o = Vector((seed * 1.7, seed * 0.3, seed * 0.9))
    o2 = Vector((seed * 0.6, seed * 2.2, 5.0))
    a0 = rng.uniform(0, 2 * math.pi)
    crown = rng.uniform(0.5, 0.66) if crown is None else crown
    taper = rng.uniform(0.2, 0.4) if taper is None else taper
    lt = sorted(rng.uniform(0.28, 0.62) for _ in range(ledges))
    ld = Vector((rng.uniform(-lean, lean), rng.uniform(-lean, lean), 0))
    # ring parameters (denser at the foot notch and on the crown)
    ts = sorted(set([round(x, 4) for x in list(np.linspace(0, 1, rings)) + [0.05, 0.085, 0.12] + [c + 0.02 for c in lt]]))

    def prof(t):
        s = 1.0 + 0.3 * (max(0.0, 0.1 - t) / 0.1) ** 2                                # talus skirt
        s *= 1.0 - notch * 0.13 * math.exp(-((t - 0.11) / 0.03) ** 2)                 # undercut notch
        s *= 1.0 - taper * t
        for l in lt:
            s *= 1.0 - 0.05 * smooth01(l - 0.01, l + 0.05, t)                        # ledge steps
        if t > crown:
            s *= math.sqrt(max(0.0, 1.0 - ((t - crown) / (1.0 - crown)) ** 2)) * 0.92 + 0.08
        return s

    V, C, meta = [], [], []
    for k, t in enumerate(ts):
        z = -1 + (h + 1) * t
        wall = float(smooth01(0.1, 0.2, t) * (1 - smooth01(crown - 0.08, crown + 0.02, t)))
        for i in range(seg):
            a = 2 * math.pi * i / seg
            d = Vector((math.cos(a), math.sin(a), 0))
            lump = 0.28 * mnoise.noise(d * 1.0 + o + Vector((0, 0, t * 1.1))) + 0.1 * mnoise.noise(d * 1.8 + o2 + Vector((0, 0, t * 3.2)))                 + 0.04 * mnoise.noise(d * 4.0 + o + Vector((0, 0, t * 6.0)))
            g = max(0.0, math.cos(flutes * a + 1.6 * mnoise.noise(d * 1.3 + o2) + 2.0 * t)) ** 4 * wall
            sheer = 1 + cliff * math.cos(a - a0) * (0.35 + t)
            cap = 0.0
            if t > crown - 0.04:
                cap = 0.06 * (0.5 + 0.5 * mnoise.noise(d * 4.0 + o + Vector((0, 0, t * 6.0))))
            rr = r * max(0.06, prof(t)) * (1 + lump - flute_depth * g + cap) * sheer
            zz = z + ((0.12 * r * mnoise.noise(d * 1.1 + o + Vector((0, 0, 9))) + 0.025 * r * mnoise.noise(d * 3.0 + o2))
                      * (t - crown) / (1 - crown) if t > crown else 0.0)   # 1-3 rounded summits
            V.append((rr * d.x + ld.x * z, rr * d.y + ld.y * z, zz))
            meta.append((t, g, a))
    nr = len(ts)
    F = []
    for k in range(nr - 1):
        for i in range(seg):
            j = (i + 1) % seg
            F.append((k * seg + i, k * seg + j, (k + 1) * seg + j, (k + 1) * seg + i))
    cap_i = len(V)
    V.append((ld.x * h, ld.y * h, h + 0.05 * r))
    meta.append((1.0, 0.0, 0.0))
    for i in range(seg):
        F.append(((nr - 1) * seg + i, (nr - 1) * seg + (i + 1) % seg, cap_i))
    p = P(V, F)
    n = vnormals(p)
    T = np.array([m[0] for m in meta])
    G = np.array([m[1] for m in meta])
    vs = nfield(p.v, 0.32, seed, stretch=(1, 1, 0.07))             # vertical water streaks
    st = nfield(p.v, 0.18, seed + 3, stretch=(1, 1, 0.3))          # iron stain patches
    vn = nfield(p.v, 0.6, seed + 7)
    c = np.tile(np.asarray(rock, dtype=np.float64), (len(V), 1)) * (1 + 0.06 * vn)[:, None]
    c = c + (np.asarray(stain) - c) * (0.55 * smooth01(0.25, 0.7, st) * smooth01(0.15, 0.3, T))[:, None]
    sk = 0.75 * smooth01(-0.1, 0.55, vs) * smooth01(0.12, 0.25, T)
    c = c + (np.asarray(streak) - c) * np.clip(sk + 0.45 * G, 0, 0.9)[:, None]
    fringe = crown - 0.04 - 0.16 * (0.5 + 0.5 * nfield(p.v, 0.9, seed + 11, stretch=(1, 1, 0.25)))
    patches = smooth01(0.25, 0.55, nfield(p.v, 0.45, seed + 13)) * smooth01(0.0, 0.5, n[:, 2] + 0.35)
    vg = np.clip(smooth01(0.25, 0.55, n[:, 2]) + smooth01(fringe - 0.02, fringe + 0.03, T) + 0.8 * patches
                 + 0.8 * (1 - smooth01(0.05, 0.1, T)), 0, 1)
    vcol = np.asarray(veg) + (np.asarray(veg2) - np.asarray(veg)) * (0.5 + 0.5 * nfield(p.v, 0.7, seed + 17))[:, None]
    c = c + (vcol - c) * vg[:, None]
    c *= (0.62 + 0.38 * smooth01(0.0, 0.14, T))[:, None]           # dark foot / talus in shade
    c *= (1.0 - 0.18 * np.clip(-n[:, 2], 0, 1))[:, None]            # undercuts darker
    p.c = np.ones((len(V), 4))
    p.c[:, :3] = np.clip(c, 0, 1)
    return cull_back(p, eye) if eye is not None else p


def cloud_card(w=60.0, h=16.0, seed=0, lobes=6, cols=30, top=(1.0, 0.88, 0.76), mid=(0.96, 0.76, 0.66),
               base=(0.80, 0.62, 0.60), sun_side=1.0):
    """flat cumulus silhouette card in the XZ plane facing -y (use face_eye): lobed top, flat-ish base, 3-tone
    vertical shading (base/mid/top) brighter on the sun side (sun_side +1 = +x). Base at z=0. ~6 tris/column."""
    rng = random.Random(seed)
    L = []
    for i in range(lobes):
        u = (i + 0.5) / lobes * 2 - 1
        env = 1 - 0.65 * u * u
        rl = h * env * rng.uniform(0.45, 0.7)
        L.append((u * w * 0.4 + rng.uniform(-0.05, 0.05) * w, rl, h * env * rng.uniform(0.15, 0.4)))
    xs = np.linspace(-w / 2, w / 2, cols)
    V, Cc, F = [], [], []
    for x in xs:
        tp = 0.0
        for cx, rl, cy in L:
            if abs(x - cx) < rl:
                tp = max(tp, cy + math.sqrt(rl * rl - (x - cx) ** 2))
        tp = max(tp, 0.04 * h)
        b = -0.04 * h * (0.5 + 0.5 * mnoise.noise(Vector((x * 0.08, seed, 0))))
        side = 0.5 + 0.5 * sun_side * x / (w / 2)
        for zf, col in ((0.0, base), (0.38, mid), (0.78, None), (1.0, top)):
            z = b + (tp - b) * zf
            if col is None:
                col = tuple(np.asarray(mid) * 0.5 + np.asarray(top) * 0.5)
            k = 0.94 + 0.08 * side if zf > 0.5 else 1.0
            V.append((x, 0.0, z))
            Cc.append([min(1, col[0] * k), min(1, col[1] * k), min(1, col[2] * k), 1.0])
    for i in range(cols - 1):
        for rI in range(3):
            a = i * 4 + rI
            F.append((a, a + 4, a + 5, a + 1))
    return P(V, F, Cc)


def cloud_bank(A, n=7, dist=(260, 420), az=(-44, 32), el=(3.0, 9.0), size=(45, 110), seed=0, set_="far",
               mat="MatSky_cloud", top=(1.0, 0.88, 0.76), mid=(0.96, 0.76, 0.66), base=(0.80, 0.62, 0.60), eye=VISTA_EYE):
    """n cloud cards spread across the vista sky (el = elevation of the card base, degrees). Two stacked puffs per
    cloud (back one larger and slightly darker) for depth. Declare `mat` (a MatSky_*) first."""
    rng = random.Random(seed)
    for k in range(n):
        d = rng.uniform(*dist)
        a = az[0] + (az[1] - az[0]) * (k + rng.uniform(0.15, 0.85)) / n
        w = rng.uniform(*size) * d / 340.0
        z = elev_z(d, rng.uniform(*el), eye)
        loc = at_vista(d, a, z, eye)
        dim = 0.93 + 0.05 * rng.random()
        back = cloud_card(w, w * rng.uniform(0.22, 0.32), seed=seed * 31 + k, lobes=rng.randint(4, 7), cols=26,
                          top=tuple(np.asarray(top) * dim), mid=tuple(np.asarray(mid) * dim), base=tuple(np.asarray(base) * dim))
        A.add(set_, mat, face_eye(back, loc, eye))
        fl = at_vista(d - 6, a + rng.uniform(-1.5, 1.5), z - 0.06 * w * 0.25, eye)
        front = cloud_card(w * 0.55, w * 0.2, seed=seed * 31 + k + 500, lobes=rng.randint(3, 5), cols=18, top=top, mid=mid, base=base)
        A.add(set_, mat, face_eye(front, fl, eye))


def ridge_layer(dist, az=(-50, 38), base=8.0, amp=10.0, seed=0, hills=7, cols=90, z0=-6.0, ridge=0.0, canopy=0.0,
                top=(0.45, 0.42, 0.52), bottom=(0.80, 0.66, 0.60), eye=VISTA_EYE):
    """painted far ridge silhouette: a curtain on an arc of radius `dist` around the eye spanning az (deg). The
    ridgeline is the max of `hills` rounded bumps (ridge>0 sharpens them toward peaks/karst towers) on a base
    height, plus `canopy` (0..1) small forest bumps. Colour fades from `top` at the ridgeline to `bottom` (valley
    haze) at z0. Use with a MatSky_* material (unshaded, fog-free): paint each layer closer to the sky-horizon
    colour the farther it is. ~6 tris/column."""
    rng = random.Random(seed)
    B = [(rng.uniform(-0.1, 1.1), rng.uniform(0.04, 0.16), rng.uniform(0.35, 1.0)) for _ in range(hills)]
    V, Cc, F = [], [], []
    for i in range(cols):
        t = i / (cols - 1)
        a = az[0] + (az[1] - az[0]) * t
        hb = 0.0
        for c, w, hh in B:
            u = abs(t - c) / w
            hb = max(hb, hh * (math.exp(-u * u) if not ridge else (1 - ridge) * math.exp(-u * u) + ridge * max(0.0, 1 - u) ** 1.5))
        hb += 0.08 * mnoise.noise(Vector((t * 9.0, seed * 1.7, 0))) + canopy * 0.05 * mnoise.noise(Vector((t * 70.0, seed, 3)))
        zt = base + amp * hb
        x, y, _ = at_vista(dist, a, 0, eye)
        for f, mixk in ((0.0, 1.0), (0.5, 0.6), (0.85, 0.2), (1.0, 0.0)):
            V.append((x, y, z0 + (zt - z0) * f))
            Cc.append(list(np.asarray(top) * (1 - mixk) + np.asarray(bottom) * mixk) + [1.0])
    for i in range(cols - 1):
        for rI in range(3):
            a_ = i * 4 + rI
            F.append((a_, a_ + 1, a_ + 5, a_ + 4))
    return P(V, F, Cc)


def hero_palm(h=8.0, seed=0, fronds=13, bend=1.0, lean_dir=None, leaflets=17, nuts=6, dead=2,
              trunk_rgb=(0.46, 0.39, 0.31), leaf_rgb=(0.30, 0.44, 0.16), old_rgb=(0.52, 0.50, 0.22), dead_rgb=(0.45, 0.33, 0.20),
              nut_rgb=(0.40, 0.46, 0.16)):
    """detailed coconut palm (battle/vista hero): curved ringed trunk with root flare, pinnate fronds (rachis +
    drooping leaflet pairs, older fronds lower and yellower), dead fronds hanging, coconut cluster.
    Returns painted (trunk, leaf, nuts) pieces; base at z=0. ~1.4k tris at fronds=13. lean_dir: radians."""
    rng = random.Random(seed)
    la = rng.uniform(0, 2 * math.pi) if lean_dir is None else lean_dir
    bd = bend * rng.uniform(0.7, 1.2)
    path = []
    N = 14
    for i in range(N + 1):
        t = i / N
        off = bd * h * 0.16 * t * t
        path.append((off * math.cos(la), off * math.sin(la), h * t))
    rs = []
    for i in range(N + 1):
        t = i / N
        rs.append(0.21 * (1 - 0.35 * t) + 0.16 * max(0.0, 0.12 - t) / 0.12)
    trunk = tube(path, rs, seg=8)
    tz = trunk.v[:, 2]
    ring = 0.5 + 0.5 * np.cos(tz * 2 * math.pi / 0.16)
    paint(trunk, trunk_rgb, var=0.04, ao=0.35, ao_h=1.2, top=0.0)
    trunk.c[:, :3] *= (0.86 + 0.14 * ring)[:, None] * (0.95 + 0.1 * smooth01(0, h, tz))[:, None]
    top = Vector(path[-1])
    tdir = (Vector(path[-1]) - Vector(path[-3])).normalized()
    leaves = []
    for k in range(fronds):
        a = 2 * math.pi * k / fronds * 2.618 + rng.uniform(-0.15, 0.15)   # golden-angle spiral
        age = k / max(1, fronds - 1)                                       # 0 young (up) .. 1 old (drooping)
        Lf = h * rng.uniform(0.42, 0.52) * (0.8 + 0.3 * (1 - abs(age - 0.5)))
        up = 0.9 - 1.3 * age
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = []
        for i in range(7):
            t = i / 6
            pts.append(top + tdir * 0.15 + d * Lf * t * 0.95 + Vector((0, 0, Lf * (up * t - (0.55 + 0.4 * age) * t * t))))
        rach = tube([tuple(q) for q in pts], [0.035, 0.03, 0.025, 0.02, 0.015, 0.01, 0.005], seg=3, cap=False)
        lv, lf = [], []
        for j in range(leaflets):
            t = 0.12 + 0.86 * j / (leaflets - 1)
            fi = t * 6
            i0 = min(5, int(fi))
            q = pts[i0].lerp(pts[i0 + 1], fi - i0)
            tang = (pts[i0 + 1] - pts[i0]).normalized()
            side = tang.cross(Vector((0, 0, 1)))
            if side.length < 1e-6:
                side = Vector((1, 0, 0))
            side.normalize()
            ll = 0.95 * math.sin(math.pi * min(1.0, 0.25 + 0.85 * t)) * (h / 8.0) + 0.12
            for s in (-1, 1):
                dirl = (side * s * 0.75 + tang * 0.45 + Vector((0, 0, -0.55 - 0.4 * t))).normalized()
                tip = q + dirl * ll
                midp = q + dirl * ll * 0.5 + Vector((0, 0, 0.06))
                wv = tang * 0.08 * (h / 8.0) ** 0.5
                b = len(lv)
                lv += [tuple(q), tuple(midp - wv), tuple(midp + wv), tuple(tip)]
                lf += [(b, b + 1, b + 3), (b, b + 3, b + 2)]
        fl = P(lv, lf)
        col = np.asarray(leaf_rgb) * (1 - 0.6 * age) + np.asarray(old_rgb) * 0.6 * age
        paint(fl, col, var=0.08, ao=0.0, top=0.25, namp=0.12, ns=1.5, seed=seed * 100 + k)
        paint(rach, np.asarray(old_rgb) * 1.05, var=0.04, ao=0.0, top=0.1, seed=seed * 100 + k)
        leaves += [fl, rach]
    for k in range(dead):  # dead fronds hanging against the trunk
        a = rng.uniform(0, 2 * math.pi)
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [top - Vector((0, 0, 0.1)) + d * 0.2, top + d * 0.6 - Vector((0, 0, 0.6)), top + d * 0.7 - Vector((0, 0, 1.8 + 0.4 * k))]
        st = strip_mesh([tuple(q) for q in pts], [0.05, 0.22, 0.12], fold=0.3, tears=0.5, seed=seed + k, up=tuple(d))
        leaves.append(paint(st, dead_rgb, var=0.1, ao=0.0, top=0.0))
    ns = []
    for k in range(nuts):
        a = 2 * math.pi * k / max(1, nuts) + rng.uniform(-0.3, 0.3)
        c = top - tdir * rng.uniform(0.15, 0.4) + Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.2, 0.3)
        nut = xf(smooth_rock(0.12, seed=seed * 9 + k, sub=1, amp=0.08, squash=(1, 1, 1.1), flat=1.0, relax=1), tuple(c - Vector((0, 0, 0.12))))
        ns.append(paint(nut, np.asarray(nut_rgb) * rng.uniform(0.85, 1.15), var=0.05, ao=0.2, ao_h=0.25, ground=c.z - 0.12, top=0.2))
    return trunk, join(leaves), join(ns)


def broadleaf_tree(h=5.0, r=2.2, seed=0, lumps=9, trunk_r=0.16, branches=4, squash=0.7, sub=2):
    """fruit/shade tree (rambutan, mango, rain tree...): flared trunk, forked branches, clumped canopy of smooth
    lumps. Returns UNPAINTED (wood, leaf); base at z=0. Paint the leaf with fruit dots via tint() if wanted."""
    rng = random.Random(seed)
    fork = h * rng.uniform(0.35, 0.45)
    wood = [tube([(0, 0, -0.1), (0.05, 0.02, fork * 0.5), (0.02, -0.03, fork)], [trunk_r * 1.5, trunk_r * 1.05, trunk_r * 0.9], seg=8)]
    for k in range(4):  # root flare
        a = 2 * math.pi * k / 4 + rng.uniform(-0.3, 0.3)
        wood.append(tube([(0, 0, 0.35), (math.cos(a) * trunk_r * 2.6, math.sin(a) * trunk_r * 2.6, -0.05)], [trunk_r * 0.5, trunk_r * 0.25], seg=5))
    leaf = []
    for k in range(branches):
        a = 2 * math.pi * k / branches + rng.uniform(-0.4, 0.4)
        d = Vector((math.cos(a), math.sin(a), 0))
        b0 = Vector((0.02, -0.03, fork))
        b1 = b0 + d * r * 0.45 + Vector((0, 0, (h - fork) * 0.45))
        b2 = b1 + d * r * 0.3 + Vector((0, 0, (h - fork) * 0.25))
        wood.append(tube([tuple(b0), tuple(b1), tuple(b2)], [trunk_r * 0.75, trunk_r * 0.5, trunk_r * 0.25], seg=6))
    for k in range(lumps):
        if k == 0:
            c, rr = (0, 0, h - r * 0.8), r * 0.7
        else:
            a = 2 * math.pi * k / (lumps - 1) * 1.618 + rng.uniform(-0.3, 0.3)
            el = rng.uniform(-0.25, 0.75)
            c = (r * 0.62 * math.cos(a) * math.cos(el), r * 0.62 * math.sin(a) * math.cos(el), h - r * 0.8 + r * 0.55 * squash * math.sin(el))
            rr = r * rng.uniform(0.38, 0.5)
        leaf.append(xf(smooth_rock(rr, seed=seed * 13 + k, sub=sub, amp=0.25, freq=2.2, squash=(1, 1, 0.85), flat=0.6, relax=1), c))
    return join(wood), join(leaf)


def _preview_sky():
    """previews only: render MatSky_* as their vertex colour (emission), like Godot's unshaded Sky kind."""
    for m in bpy.data.materials:
        if not m.name.startswith("MatSky") or m.node_tree is None or m.node_tree.nodes.get("SkyEmit"):
            continue
        nt = m.node_tree
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        vc = nt.nodes.get("VCol")
        if out is None or vc is None:
            continue
        em = nt.nodes.new("ShaderNodeEmission")
        em.name = "SkyEmit"
        nt.links.new(vc.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs[0], out.inputs["Surface"])
