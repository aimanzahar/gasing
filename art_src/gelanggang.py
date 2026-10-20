"""Gelanggang ring dressing -- assets/gelanggang.glb, shown in every arena in place of main.tscn's Rim torus.
A twisted 3-strand rope on the Rim footprint (ring radius 4.15, tube ~0.2, centreline y 0.02), 16 short
carved stakes (<=0.25 m above the floor) and a low carved timber kerb hiding the dish/terrain seam.
Origin = ring centre at floor level (Godot y 0). Materials Mat* (arena_dress.gd styles them).
Nodes: GelRope (MatCloth_rope), GelStakes (MatWood_stake), GelKerb (MatWood_kerb) -- the kerb can be hidden alone.

  blender -b --factory-startup -P art_src/gelanggang.py -- [--export] [--render game,vista,close] [--out DIR]
"""
import sys, os, math, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import arenakit as K
importlib.reload(K)
import bpy
import numpy as np
from arenakit import P, xf, paint, nz, smooth01

R = 4.15            # rope ring radius (TorusMesh inner 3.95 / outer 4.35)
Z0 = 0.02           # rope centreline height (Rim node y)
TURNS = 21          # rope lay: full turns of each strand around the ring (lay length ~1.24 m)
SPT = 8             # samples per turn
STRAND_OFF = 0.11   # strand centre distance from the rope centreline
STRAND_R = 0.096    # strand radius -> outer extent ~0.206
SEG = 5             # strand cross-section sides
N_STAKES = 16
STAKE_R = 4.44
FIBRE = (0.55, 0.42, 0.26)
FIBRE_DK = (0.27, 0.19, 0.11)
STAKE = (0.36, 0.25, 0.16)
KERB = (0.33, 0.22, 0.14)
MOOD = {"sky_top": (0.30, 0.36, 0.58), "sky_horizon": (0.98, 0.66, 0.42), "fog": (0.84, 0.62, 0.44), "fog_density": 0.0,
        "sun_color": (1.0, 0.84, 0.62), "lantern": (1.0, 0.66, 0.34), "b_sun": 3.6, "b_world": 0.9, "b_fill": 0.4, "b_lantern": 12.0}


def ring_frame(u):
    """centreline point, outward radial and up at arc parameter u (radians around the ring)."""
    c = np.array((R * math.cos(u), R * math.sin(u), Z0))
    out = np.array((math.cos(u), math.sin(u), 0.0))
    return c, out, np.array((0.0, 0.0, 1.0))


def strand(k):
    """one helical strand as a closed tube (explicit periodic frames, no seam). Returns P + per-vertex
    'outwardness' (1 = rope surface, -1 = buried in the lay groove)."""
    n = TURNS * SPT
    V, W = [], []
    centres = []
    for i in range(n):
        u = 2 * math.pi * i / n
        c, out, up = ring_frame(u)
        ph = 2 * math.pi * k / 3 + 2 * math.pi * TURNS * i / n
        off = out * math.cos(ph) + up * math.sin(ph)
        centres.append((c + off * STRAND_OFF, c))
    for i in range(n):
        p0, c = centres[i]
        p1 = centres[(i + 1) % n][0]
        pm = centres[i - 1][0]
        t = p1 - pm
        t /= np.linalg.norm(t)
        a = np.cross(t, (0.0, 0.0, 1.0))
        a /= np.linalg.norm(a)
        b = np.cross(a, t)
        rel = p0 - c
        rel /= np.linalg.norm(rel)
        for s in range(SEG):
            th = 2 * math.pi * s / SEG
            d = a * math.cos(th) + b * math.sin(th)
            V.append(tuple(p0 + d * STRAND_R))
            W.append(float(np.dot(d, rel)))
    F = []
    for i in range(n):
        j = (i + 1) % n
        for s in range(SEG):
            s2 = (s + 1) % SEG
            F.append((i * SEG + s, i * SEG + s2, j * SEG + s2, j * SEG + s))
    return P(V, F), np.array(W)


def rope():
    ps = []
    for k in range(3):
        p, w = strand(k)
        n = K.vnormals(p)
        groove = smooth01(-0.7, 0.55, w)                    # dark where strands press together
        rad = np.hypot(p.v[:, 0], p.v[:, 1])
        fib = np.array([nz(x * 3.0, y * 3.0, z * 3.0, 4.0, 40 + k) for x, y, z in p.v])
        wear = np.array([nz(x, y, 0, 0.35, 47) for x, y, _ in p.v])
        base = np.asarray(FIBRE) * (1 + 0.05 * (k - 1)) * (1 + 0.07 * fib)[:, None]
        base = base * (1 - 0.18 * smooth01(0.2, 0.8, wear))[:, None]                  # weathered stretches
        c = np.asarray(FIBRE_DK) + (base - np.asarray(FIBRE_DK)) * (0.25 + 0.75 * groove)[:, None]
        c = c * (0.72 + 0.28 * smooth01(-0.12, 0.12, p.v[:, 2]))[:, None]            # contact with the floor
        c = c * (1 + 0.08 * n[:, 2])[:, None]
        c = c * (1 - 0.12 * smooth01(4.2, 4.35, rad) * smooth01(0.05, -0.1, p.v[:, 2]))[:, None]
        p.c = np.ones((len(p.v), 4))
        p.c[:, :3] = np.clip(c, 0, 1)
        ps.append(p)
    return ps


def stake(seed):
    """hand-carved pasak: tapered peg, collar, domed head; 0.25 m above the floor, buried to -0.35."""
    rng = np.random.default_rng(seed)
    prof = [(0.0, -0.3), (0.05, -0.27), (0.05, 0.0), (0.046, 0.15), (0.058, 0.165), (0.058, 0.19), (0.04, 0.205),
            (0.027, 0.24), (0.0, 0.25)]
    p = K.lathe(prof, seg=6, cap0=False, cap1=False, phase=float(rng.uniform(0, 1)),
                rfn=lambda a, t: 1.0 + 0.06 * math.cos(3 * a + seed))      # hand-whittled, not lathe-perfect
    z = p.v[:, 2]
    paint(p, STAKE, var=0.08, ao=0.45, ao_h=0.12, ground=0.0, top=0.15, seed=seed)
    p.c[:, :3] *= np.where(((z > 0.163) & (z < 0.192))[:, None], 0.72, 1.0)       # dark carved collar band
    p.c[:, :3] *= np.where((z > 0.2)[:, None], 1.12, 1.0)                         # worn bright head
    return p


def kerb_segment(a0, a1, seed):
    """low carved timber kerb piece on the dish edge between two stakes (r 4.33..4.63, top y ~0.045)."""
    rng = np.random.default_rng(seed)
    hj = float(rng.uniform(-0.008, 0.008))
    prof = [(4.33, -0.3), (4.33, 0.02), (4.42, 0.045 + hj), (4.53, 0.03 + hj), (4.63, -0.05)]
    steps = 5
    V, F = [], []
    m = len(prof)
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        for (r, z) in prof:
            V.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(steps):
        for j in range(m - 1):
            q = i * m + j
            F.append((q, q + 1, q + m + 1, q + m))
    F.append(tuple(range(m - 1, -1, -1)))
    F.append(tuple(range(steps * m, steps * m + m)))
    p = P(V, F)
    paint(p, KERB, var=0.07, ao=0.5, ao_h=0.1, ground=-0.02, top=0.2, seed=seed)
    ang = np.arctan2(p.v[:, 1], p.v[:, 0])
    u = ((ang - a0) % (2 * math.pi)) / (a1 - a0)
    # carved pucuk-rebung teeth along the outer bevel: alternating light/dark per vertex column
    col = np.round(u * steps).astype(int)
    outer = (np.hypot(p.v[:, 0], p.v[:, 1]) > 4.48) & (p.v[:, 2] > -0.06)
    p.c[:, :3] *= np.where((outer & (col % 2 == 1))[:, None], 0.7, 1.0)
    p.c[:, :3] *= np.where(((u < 0.02) | (u > 0.98))[:, None], 0.65, 1.0)             # end grain
    return p


def build(A):
    A.mat("MatCloth_rope", two_sided=False)
    A.mat("MatWood_stake")
    A.mat("MatWood_kerb")
    A.add("battle", "MatCloth_rope", rope())
    step = 2 * math.pi / N_STAKES
    for k in range(N_STAKES):
        a = step * (k + 0.5)
        lean = 0.12
        s = xf(stake(k), (0, 0, 0), (0, lean, 0))                         # lean outward (+x before rotation)
        A.add("battle", "MatWood_stake", xf(s, (STAKE_R * math.cos(a), STAKE_R * math.sin(a), 0.0), (0, 0, a)))
        A.add("battle", "MatWood_kerb", kerb_segment(a + 0.03, a + step - 0.03, 100 + k))


NAMES = {"EnvBattle_MatCloth_rope": "GelRope", "EnvBattle_MatWood_stake": "GelStakes", "EnvBattle_MatWood_kerb": "GelKerb"}


def export(path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.name in NAMES.values():
            o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                              export_texcoords=False, export_normals=True, export_tangents=False,
                              export_vertex_color='ACTIVE', export_all_vertex_colors=False,
                              export_lights=False, export_cameras=False, export_animations=False,
                              export_yup=True, export_extras=False)


def main():
    o = K._argv(None)
    out = o["out"] or os.path.join(__import__("tempfile").gettempdir(), "arena_preview")
    os.makedirs(out, exist_ok=True)
    K.wipe()
    A = K.Arena("gelanggang")
    build(A)
    A.finish()
    for ob in list(bpy.data.objects):
        if ob.name in NAMES:
            ob.name = NAMES[ob.name]
            ob.data.name = ob.name
    rep = {"tris": {}, "materials": sorted(A.mats)}
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and ob.name.startswith("Gel"):
            ob.data.calc_loop_triangles()
            rep["tris"][ob.name] = len(ob.data.loop_triangles)
            co = np.empty(len(ob.data.vertices) * 3)
            ob.data.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            rr = np.hypot(co[:, 0], co[:, 1])
            rep.setdefault("extent", {})[ob.name] = {"r": [round(float(rr.min()), 3), round(float(rr.max()), 3)],
                                                     "z": [round(float(co[:, 2].min()), 3), round(float(co[:, 2].max()), 3)]}
    rep["tris"]["total"] = sum(rep["tris"].values())
    if o["export"]:
        path = os.path.join(K.ASSETS, "gelanggang.glb")
        export(path)
        rep["glb"] = K.glb_report(path)
    with open(os.path.join(out, "gelanggang_report.json"), "w") as fh:
        json.dump(rep, fh, indent=1)
    print("GEL_REPORT " + json.dumps(rep))
    if o["render"]:
        K.preview_rig(MOOD)
        for nm in ("PreviewRim",):
            if bpy.data.objects.get(nm):
                bpy.data.objects.remove(bpy.data.objects[nm])
        for cam in o["render"]:
            p = os.path.join(out, "gelanggang_%s.png" % cam)
            if cam == "close":
                K._cam("CloseCam", (2.2, -7.2, 1.6), (3.4, -2.0, 0.0), 40)
                sc = bpy.context.scene
                sc.render.engine = 'BLENDER_EEVEE'
                sc.eevee.taa_render_samples = o["samples"]
                sc.render.resolution_x, sc.render.resolution_y = o["res"]
                sc.view_settings.view_transform = 'AgX'
                sc.render.filepath = p
                bpy.ops.render.render(write_still=True)
            else:
                K.render(cam, p, o["res"], o["samples"])
            print("RENDER", cam, "->", p)


if __name__ == "__main__":
    main()
