# Gasing build script: data-driven lathe tops -> assets/gasing_<id>.glb, plus the wayang top silhouette,
# a JSON report, previews and a contact sheet. Scripts are the source of truth: no .blend is saved.
#
#   blender -b --factory-startup -P art_src/gasing_build.py -- <id|all> [more ids]
#       [--out assets] [--preview DIR] [--compare DIR_WITH_OLD_GLBS] [--no-render] [--no-wayang]
#
# --out      GLBs go to <out>/gasing_<id>.glb, master silhouettes to <out>/wayang/wayang_top_<id>.png (default: repo
#            assets); the PNG is 512x512 black on transparent (8-bit indexed, wayang_lib format) with the tip at the
#            bottom centre (main.gd's pivot), perforated with wayang_lib's tatahan (same density as the beat scenes)
# --preview  previews, contact.png and report.json go here (no previews without it)
# --compare  folder holding the old gasing_<id>.glb files; ids without one compare against its jantung
#            (what the game fell back to). `git show HEAD:assets/gasing_<id>.glb` recovers an original.
# --no-render  build + export + report only (fast table validation)
# --sheet    with --preview: rebuild contact.png from the previews on disk (no ids needed); handy when each top
#            is built in its own Blender process
#
# Contract with gasing.gd (_build_visual / _build_level_bands / _band_profile):
#   one mesh object, tip at the origin, Y-up after export, no UVs, no torus nodes;
#   slots 0 Body (pure lathe only, so _band_profile reads the radius profile), 1 Accent, 2 Metal, 3 Deco,
#   materials named exactly so, every slot owning >= 1 face (glTF drops empty slots and shifts the rest).
#   gasing.gd keeps Body's albedo (the wood species; it multiplies a procedural grain) and overrides Accent with the
#   style/team colour (matte-satin lacquer); Metal and Deco ship as authored. Physics radius comes from the
#   archetype (uri 0.56, jantung 0.44).
#
# Colours in this file are sRGB (what Godot shows); material() converts to the linear values Blender/glTF store.
#
# Table units: "z" positions are fractions of H measured up the side, "c" positions are fractions of r_max
# measured on the crown (searched down from the axis). Lengths (w, d, h, raise, ...) are metres.
import bpy, bmesh, math, os, re, sys, json, struct, zlib, random
import numpy as np
from mathutils import Vector

sys.dont_write_bytecode = True   # no __pycache__ in art_src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wayang_lib as W            # read-only: tatahan perforation + indexed PNG writer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLOTS = ("Body", "Accent", "Metal", "Deco")
MI = {"body": 0, "accent": 1, "metal": 2, "deco": 3}
GOLD = (1.0, 0.78, 0.25)   # HT.PLAYER_COLOR: the accent a player's top wears in game
FOE = (0.88, 0.22, 0.26)   # HT.SIDE_FOE: the accent of the AI's reserve tops
ARCH = {"jantung": (0.44, 1.00), "uri": (0.56, 0.60)}   # physics footprint: r_max, H


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3])


# Body albedo (sRGB) carries the wood species; gasing.gd multiplies it by a grain texture (~0.85 average).
# Keep tops darker or more saturated than the dish floor (0.6, 0.42, 0.23): dark carved wood, bright lacquer.
WOOD = {
    "merbau": (0.46, 0.22, 0.12), "kemuning": (0.62, 0.45, 0.19), "nangka": (0.56, 0.33, 0.12),
    "cengal": (0.48, 0.30, 0.15), "keranji": (0.33, 0.15, 0.09), "sena": (0.52, 0.25, 0.16),
    "rengas": (0.50, 0.15, 0.10), "jati": (0.52, 0.35, 0.17), "belian": (0.26, 0.17, 0.11),
    "ebony": (0.12, 0.10, 0.09), "kempas": (0.54, 0.27, 0.13), "tembusu": (0.60, 0.48, 0.30),
    "meranti": (0.48, 0.23, 0.18),
}
# Metal / Deco finishes (sRGB, metallic, roughness): aged and satin, never mirror-bright
FINISH = {
    "iron": ((0.42, 0.41, 0.40), 0.85, 0.45), "forged": ((0.33, 0.32, 0.31), 0.8, 0.55),
    "steel": ((0.62, 0.63, 0.66), 0.95, 0.38), "brass": ((0.82, 0.62, 0.30), 0.95, 0.40),
    "gold": ((0.90, 0.70, 0.30), 0.9, 0.38), "tin": ((0.76, 0.77, 0.79), 0.95, 0.34),
    "silver": ((0.84, 0.84, 0.86), 0.95, 0.32), "copper": ((0.78, 0.45, 0.30), 0.95, 0.40),
    "rope": ((0.66, 0.53, 0.33), 0.0, 0.9), "bamboo": ((0.80, 0.68, 0.40), 0.0, 0.7),
    "bone": ((0.90, 0.85, 0.72), 0.0, 0.55), "pua": ((0.60, 0.14, 0.09), 0.0, 0.65),
    "nyonya": ((0.93, 0.58, 0.64), 0.0, 0.55), "indigo": ((0.20, 0.27, 0.55), 0.0, 0.6),
    "jade": ((0.36, 0.66, 0.50), 0.0, 0.5),
}

# Body curves: (z/H, r/r_max) control points from just inside the tip collar to the axis at the crown.
# Centripetal Catmull-Rom through them; build() rescales radii so the outermost point lands on r_max.
HEART = [(0.068, 0.07), (0.10, 0.16), (0.15, 0.36), (0.21, 0.58), (0.28, 0.79), (0.35, 0.925), (0.40, 0.966),
         (0.46, 0.962), (0.52, 0.925), (0.555, 0.875), (0.575, 0.82), (0.59, 0.775), (0.61, 0.765), (0.65, 0.78),
         (0.71, 0.79), (0.78, 0.775), (0.84, 0.735), (0.89, 0.66), (0.925, 0.55)]
PROFILES = {
    # jantung: round heart lobe (belly at 0.40 H), a crisp shoulder into a cove neck, a rounded head,
    # a domed crown and a short knob
    "heart": HEART + [(0.948, 0.42), (0.960, 0.28), (0.965, 0.19), (0.972, 0.155), (0.993, 0.145),
                      (1.0, 0.10), (1.0, 0.0)],
    # bell knob (penang)
    "bell": HEART[:-1] + [(0.905, 0.60), (0.915, 0.40), (0.925, 0.22), (0.945, 0.13), (0.97, 0.15),
                          (0.99, 0.20), (1.0, 0.12), (1.0, 0.0)],
    # domed head, lamp-like (perak)
    "dome": HEART[:-2] + [(0.88, 0.70), (0.93, 0.56), (0.97, 0.36), (0.99, 0.18), (1.0, 0.0)],
    # mushroom bollard crown (johor)
    "bollard": HEART[:-2] + [(0.88, 0.62), (0.895, 0.40), (0.905, 0.22), (0.94, 0.20), (0.965, 0.27),
                             (0.985, 0.25), (1.0, 0.14), (1.0, 0.0)],
    # tall knob (datuk)
    "tall": [(0.062, 0.07), (0.10, 0.15), (0.16, 0.36), (0.24, 0.62), (0.31, 0.84), (0.37, 0.95), (0.40, 0.966),
             (0.46, 0.95), (0.54, 0.88), (0.61, 0.78), (0.66, 0.70), (0.70, 0.62), (0.72, 0.45), (0.73, 0.26),
             (0.75, 0.20), (0.80, 0.19), (0.84, 0.21), (0.87, 0.19), (0.92, 0.18), (0.96, 0.17), (0.99, 0.12),
             (1.0, 0.0)],
    # slender heart (cikros)
    "slender": [(0.065, 0.07), (0.10, 0.12), (0.17, 0.30), (0.25, 0.55), (0.32, 0.80), (0.38, 0.93), (0.42, 0.966),
                (0.48, 0.95), (0.56, 0.88), (0.64, 0.77), (0.70, 0.66), (0.75, 0.62), (0.81, 0.64), (0.87, 0.62),
                (0.92, 0.55), (0.955, 0.42), (0.968, 0.26), (0.975, 0.14), (0.995, 0.12), (1.0, 0.0)],
    # heavy heart (tokgayong): full belly, low broad head
    "heavy": [(0.075, 0.07), (0.11, 0.15), (0.17, 0.36), (0.24, 0.62), (0.31, 0.84), (0.37, 0.95), (0.40, 0.966),
              (0.47, 0.96), (0.55, 0.92), (0.63, 0.86), (0.70, 0.82), (0.76, 0.82), (0.83, 0.78), (0.89, 0.68),
              (0.93, 0.52), (0.95, 0.30), (0.955, 0.20), (0.97, 0.17), (0.995, 0.16), (1.0, 0.0)],
    # uri: low wide lens with a domed top and a short knob
    "lens": [(0.11, 0.07), (0.14, 0.14), (0.19, 0.33), (0.24, 0.58), (0.28, 0.83), (0.30, 0.973), (0.36, 0.972),
             (0.43, 0.95), (0.50, 0.89), (0.57, 0.80), (0.64, 0.68), (0.71, 0.55), (0.78, 0.43), (0.85, 0.32),
             (0.90, 0.25), (0.93, 0.20), (0.95, 0.17), (0.99, 0.16), (1.0, 0.11), (1.0, 0.0)],
    # uri with a stepped crown (pakdin)
    "stepped": [(0.11, 0.07), (0.14, 0.14), (0.19, 0.34), (0.24, 0.60), (0.28, 0.85), (0.30, 0.973), (0.36, 0.972),
                (0.43, 0.95), (0.49, 0.89), (0.53, 0.80), (0.56, 0.76), (0.58, 0.66), (0.62, 0.64), (0.66, 0.60),
                (0.69, 0.50), (0.73, 0.47), (0.77, 0.44), (0.80, 0.33), (0.85, 0.30), (0.90, 0.27), (0.95, 0.20),
                (0.98, 0.13), (1.0, 0.0)],
    # uri disc with a carved boss on a rope-bound neck (perlis)
    "boss": [(0.11, 0.07), (0.14, 0.14), (0.19, 0.34), (0.24, 0.60), (0.28, 0.85), (0.30, 0.973), (0.36, 0.972),
             (0.42, 0.95), (0.48, 0.89), (0.53, 0.80), (0.58, 0.67), (0.62, 0.53), (0.65, 0.40), (0.67, 0.33),
             (0.70, 0.295), (0.76, 0.295), (0.80, 0.33), (0.86, 0.345), (0.92, 0.315), (0.96, 0.245),
             (0.985, 0.15), (0.995, 0.08), (1.0, 0.0)],
}

# The 19 tops. Keys: arch, r/h (footprint, default ARCH; h is the total height incl. horns), segs (96 base /
# 128 master), profile, wood, lacquer (Accent default; in game the style/team colour replaces it), metal, deco
# (FINISH keys), density (ang deg, step m: smooth-row spacing; default 16/0.14 base, 12/0.10 master),
# lace (wayang classes cycled over the body zones, bottom-up), lathe (profile features), parts (non-lathe pieces).
# lathe kinds (all carved with real depth and bevelled lips):
#   groove (v|u, w 16 mm, d 8 mm, lip 3.5 mm chamfers), bead (half-round 18x8 mm), band (raised 6 mm lacquer
#   fillet, 4.5 mm chamfers), inlay (5 mm recessed channel whose floor is the inlay material), ring (iron belly
#   ring 28x16 mm, 4 mm bevel), paint (material only), facets (gouge|flat flutes, n divides segs).
# part kinds: petals (leaf|drop|ray|grain carved relief with a midrib, bend = swirl), rope (3-lay twisted cord),
#   beads, horns.
TOPS = {
    # ---------------------------------------------------------------- base tops
    "jantung": dict(arch="jantung", segs=96, profile="heart", wood="merbau", metal="iron", deco="brass",
        density=(26.0, 0.22), lace=("scales", "lace", "flower"),
        lathe=[dict(k="facets", z=(0.10, 0.37), n=12, depth=0.026),
               dict(k="ring", z=0.40), dict(k="band", z=(0.50, 0.555)), dict(k="bead", z=0.60, mat="deco"),
               dict(k="band", z=(0.685, 0.72)), dict(k="facets", z=(0.735, 0.885), n=12, depth=0.018, phase=0.5),
               dict(k="groove", z=0.81, mat="deco"),
               dict(k="inlay", c=(0.58, 0.64), mat="deco"), dict(k="paint", c=(0.0, 0.165), mat="deco")],
        parts=[dict(k="petals", n=8, c=(0.22, 0.54), w=0.034, h=0.012, shape="leaf", mat="accent")]),
    "uri": dict(arch="uri", segs=96, profile="lens", wood="kemuning", metal="steel", deco="brass",
        density=(18.0, 0.16), lace=("lace", "flower"),
        lathe=[dict(k="facets", z=(0.13, 0.275), n=24, depth=0.010), dict(k="ring", z=0.30),
               dict(k="band", z=(0.40, 0.47)), dict(k="groove", z=0.56, mat="deco"), dict(k="groove", z=0.665),
               dict(k="inlay", c=(0.40, 0.46)), dict(k="paint", c=(0.0, 0.175), mat="deco")],
        parts=[dict(k="petals", n=6, c=(0.20, 0.37), w=0.034, h=0.011, shape="drop", mat="accent")]),
    "pakdin": dict(arch="uri", r=0.56, h=0.61, segs=96, profile="stepped", wood="cengal", metal="steel",
        deco="brass", density=(22.0, 0.20), lace=("scales", "grid"),
        lathe=[dict(k="ring", z=0.30), dict(k="band", z=(0.40, 0.47)),
               dict(k="groove", z=0.75, shape="u", w=0.020, d=0.009),
               dict(k="inlay", c=(0.62, 0.67)), dict(k="paint", c=(0.0, 0.14), mat="deco")],
        parts=[dict(k="petals", n=12, c=(0.15, 0.27), w=0.013, h=0.009, shape="ray", mat="accent")]),
    "cikros": dict(arch="jantung", r=0.40, h=1.05, segs=96, profile="slender", wood="sena", metal="iron",
        deco="brass", density=(24.0, 0.20), lace=("lace", "scales", "flower"),
        lathe=[dict(k="groove", z=0.22), dict(k="ring", z=0.42), dict(k="groove", z=0.72, mat="deco"),
               dict(k="band", z=(0.78, 0.86)), dict(k="paint", c=(0.0, 0.15), mat="deco")],
        parts=[dict(k="petals", n=10, c=(0.18, 0.50), w=0.028, h=0.011, shape="leaf", mat="accent"),
               dict(k="petals", n=10, c=(0.40, 0.56), w=0.015, h=0.008, shape="drop", mat="deco", phase=0.5)]),
    "tokgayong": dict(arch="jantung", r=0.50, h=0.85, segs=96, profile="heavy", wood="keranji", metal="iron",
        deco="brass", density=(20.0, 0.18), lace=("scales", "grid", "flower"),
        lathe=[dict(k="groove", z=0.24), dict(k="ring", z=0.40, h=0.042, p=0.020),
               dict(k="facets", z=(0.46, 0.67), n=16, depth=0.016), dict(k="band", z=(0.70, 0.80)),
               dict(k="groove", z=0.845, mat="deco"), dict(k="paint", c=(0.0, 0.18), mat="deco")],
        parts=[dict(k="petals", n=4, c=(0.20, 0.62), w=0.07, h=0.013, shape="leaf", mat="accent")]),
    "datuk": dict(arch="jantung", r=0.52, h=1.10, segs=96, profile="tall", wood="rengas", metal="iron",
        deco="brass", density=(26.0, 0.22), lace=("lace", "scales", "edge"),
        lathe=[dict(k="groove", z=0.22), dict(k="ring", z=0.40), dict(k="band", z=(0.55, 0.64)),
               dict(k="bead", z=0.80, mat="deco"), dict(k="bead", z=0.86, mat="deco"),
               dict(k="bead", z=0.92, mat="deco"), dict(k="paint", c=(0.0, 0.10), mat="deco")],
        parts=[dict(k="petals", n=8, c=(0.30, 0.56), w=0.032, h=0.011, shape="drop", mat="accent")]),
    # ---------------------------------------------------------------- masters (story order)
    # Perlis, Pak Latif: deliberately faceted, hand-carved, rope neck, iron nail knob, padi-grain crown
    "perlis": dict(arch="uri", segs=128, density=(14.0, 0.12), profile="boss", wood="nangka", metal="forged",
        deco="rope", lace=("scales", "lace", "flower"),
        lathe=[dict(k="facets", z=(0.12, 0.275), n=16, depth=0.022, style="gouge", jitter=0.35, seed=3),
               dict(k="ring", z=0.30), dict(k="band", z=(0.36, 0.43)), dict(k="groove", z=0.47),
               dict(k="facets", z=(0.49, 0.665), n=16, depth=0.046, style="gouge", phase=0.5, jitter=0.3, seed=5),
               dict(k="facets", z=(0.775, 0.912), n=8, style="flat"),
               dict(k="inlay", c=(0.25, 0.31), mat="metal"), dict(k="paint", c=(0.0, 0.06), mat="metal")],
        parts=[dict(k="rope", z=0.73, a=0.021), dict(k="beads", n=16, c=0.62, a=0.011, squash=0.45, phase=0.5,
                                                    mat="metal"),
               dict(k="petals", n=8, c=(0.075, 0.24), w=0.018, h=0.010, shape="grain", mat="accent")]),
    # Kedah, Mak Semah: paddy-sheaf rays and a gate-wheel inlay
    "kedah": dict(arch="uri", segs=128, profile="lens", wood="kempas", metal="iron", deco="gold",
        density=(14.0, 0.12), lace=("lace", "grid", "rays"),
        lathe=[dict(k="facets", z=(0.13, 0.275), n=32, depth=0.010), dict(k="ring", z=0.30),
               dict(k="band", z=(0.40, 0.47)), dict(k="groove", z=0.54, mat="deco"),
               dict(k="inlay", c=(0.56, 0.62)), dict(k="paint", c=(0.0, 0.175), mat="deco")],
        parts=[dict(k="petals", n=16, c=(0.22, 0.52), w=0.016, h=0.010, shape="ray", mat="accent"),
               dict(k="petals", n=8, c=(0.08, 0.17), w=0.009, h=0.008, shape="ray", mat="deco")]),
    # Penang, Ah Kow: red-gold lacquer and a bell knob
    "penang": dict(arch="jantung", segs=128, profile="bell", wood="keranji", metal="iron", deco="gold",
        density=(18.0, 0.16), lace=("scales", "lace", "flower"),
        lathe=[dict(k="groove", z=0.22), dict(k="ring", z=0.40), dict(k="band", z=(0.555, 0.62)),
               dict(k="bead", z=0.66, mat="deco"), dict(k="band", z=(0.77, 0.86)), dict(k="bead", z=0.885, mat="deco"),
               dict(k="paint", c=(0.0, 0.21), mat="deco")],
        parts=[dict(k="petals", n=8, c=(0.25, 0.55), w=0.030, h=0.012, shape="drop", mat="deco")]),
    # Perak, Uncle Chandran: tin bands and a lamp dome
    "perak": dict(arch="jantung", segs=128, profile="dome", wood="jati", metal="tin", deco="copper",
        density=(16.0, 0.14), lace=("grid", "lace", "dots"),
        lathe=[dict(k="facets", z=(0.10, 0.36), n=16, depth=0.016),
               dict(k="band", z=(0.18, 0.22), mat="metal"), dict(k="ring", z=0.40),
               dict(k="band", z=(0.52, 0.56), mat="metal"), dict(k="groove", z=0.59), dict(k="band", z=(0.62, 0.70)),
               dict(k="groove", z=0.74), dict(k="band", z=(0.78, 0.82), mat="metal"),
               dict(k="facets", z=(0.85, 0.985), n=16, depth=0.012), dict(k="paint", c=(0.0, 0.40), mat="deco")],
        parts=[dict(k="petals", n=6, c=(0.42, 0.66), w=0.032, h=0.011, shape="drop", mat="accent")]),
    # Selangor, Danial: batik bands
    "selangor": dict(arch="jantung", segs=128, profile="heart", wood="tembusu", metal="iron", deco="indigo",
        density=(16.0, 0.14), lace=("lace", "slits", "flower"),
        lathe=[dict(k="groove", z=0.22), dict(k="ring", z=0.40), dict(k="band", z=(0.495, 0.545)),
               dict(k="band", z=(0.555, 0.60), mat="deco"), dict(k="band", z=(0.61, 0.66)),
               dict(k="band", z=(0.775, 0.855), mat="deco"),
               dict(k="inlay", c=(0.60, 0.66), mat="accent"), dict(k="paint", c=(0.0, 0.165), mat="deco")],
        parts=[dict(k="petals", n=6, c=(0.20, 0.56), w=0.036, h=0.012, shape="drop", mat="accent")]),
    # Negeri Sembilan, Mak Cik Ramlah: 4-fold gonjong horns
    "nsembilan": dict(arch="jantung", segs=128, profile="heart", wood="cengal", metal="iron", deco="gold",
        density=(16.0, 0.14), lace=("scales", "lace", "grid"),
        lathe=[dict(k="facets", z=(0.10, 0.36), n=16, depth=0.016), dict(k="ring", z=0.40),
               dict(k="band", z=(0.50, 0.555)), dict(k="groove", z=0.60, mat="deco"),
               dict(k="band", z=(0.775, 0.855)), dict(k="inlay", c=(0.60, 0.66)),
               dict(k="paint", c=(0.0, 0.165), mat="deco")],
        parts=[dict(k="horns", n=4, c=0.40, len=0.07, r0=0.016, lean=0.8, curl=1.0, mat="deco")]),
    # Melaka, Uncle Tan: 24 beads and nyonya pink-green
    "melaka": dict(arch="jantung", h=0.97, segs=128, profile="heart", wood="rengas", metal="iron", deco="nyonya",
        density=(16.0, 0.14), lace=("lace", "flower", "dots"),
        lathe=[dict(k="groove", z=0.22, mat="deco"), dict(k="ring", z=0.40), dict(k="band", z=(0.52, 0.58)),
               dict(k="band", z=(0.775, 0.855)), dict(k="inlay", c=(0.60, 0.66)),
               dict(k="paint", c=(0.0, 0.165), mat="deco")],
        parts=[dict(k="beads", n=24, z=0.70, a=0.012, mat="deco"),
               dict(k="petals", n=8, c=(0.21, 0.56), w=0.028, h=0.011, shape="leaf", mat="accent")]),
    # Johor, Pak Zaid: rope coil neck and a bollard crown
    "johor": dict(arch="jantung", segs=128, profile="bollard", wood="belian", metal="iron", deco="rope",
        density=(16.0, 0.14), lace=("grid", "lace", "flower"),
        lathe=[dict(k="groove", z=0.22), dict(k="ring", z=0.40), dict(k="band", z=(0.58, 0.66)),
               dict(k="band", z=(0.80, 0.86)), dict(k="paint", c=(0.0, 0.29), mat="metal")],
        parts=[dict(k="rope", z=0.735, a=0.018)]),
    # Pahang, Along: woven bamboo band
    "pahang": dict(arch="uri", segs=128, profile="lens", wood="meranti", metal="iron", deco="bamboo",
        density=(16.0, 0.14), lace=("scales", "grid", "lace"),
        lathe=[dict(k="facets", z=(0.13, 0.275), n=32, depth=0.010),
               dict(k="facets", z=(0.40, 0.50), n=32, depth=0.008, style="gouge", pitch=0.018, fade=0.0),
               dict(k="paint", z=(0.40, 0.50), mat="deco"),
               dict(k="ring", z=0.30), dict(k="groove", z=0.385), dict(k="groove", z=0.512),
               dict(k="band", z=(0.53, 0.59)), dict(k="bead", z=0.625, mat="deco"),
               dict(k="inlay", c=(0.40, 0.46), mat="deco"),
               dict(k="paint", c=(0.0, 0.175), mat="deco")],
        parts=[dict(k="petals", n=8, c=(0.20, 0.38), w=0.026, h=0.010, shape="leaf", mat="accent")]),
    # Terengganu, Pak Ngah: songket gold and an 8-fold wave crest
    "terengganu": dict(arch="uri", h=0.56, segs=128, profile="lens", wood="cengal", metal="iron", deco="gold",
        density=(16.0, 0.14), lace=("lace", "scales", "flower"),
        lathe=[dict(k="facets", z=(0.13, 0.275), n=16, depth=0.012), dict(k="ring", z=0.30), dict(k="groove", z=0.20),
               dict(k="band", z=(0.37, 0.445)),
               dict(k="facets", z=(0.37, 0.445), n=32, depth=0.004, style="gouge", pitch=0.0125, fade=0.0),
               dict(k="bead", z=0.475, mat="deco"), dict(k="bead", z=0.52, mat="deco"), dict(k="groove", z=0.58),
               dict(k="paint", c=(0.0, 0.175), mat="deco")],
        parts=[dict(k="petals", n=8, c=(0.20, 0.62), w=0.034, h=0.012, shape="drop", bend=0.6, mat="deco")]),
    # Kelantan, Cik Zainab: 4-fold wau crescents
    "kelantan": dict(arch="uri", h=0.64, segs=128, profile="lens", wood="sena", metal="iron", deco="gold",
        density=(16.0, 0.14), lace=("flower", "lace"),
        lathe=[dict(k="facets", z=(0.13, 0.275), n=16, depth=0.012), dict(k="groove", z=0.20), dict(k="ring", z=0.30),
               dict(k="band", z=(0.40, 0.47)), dict(k="bead", z=0.505, mat="deco"), dict(k="groove", z=0.57, mat="deco"),
               dict(k="inlay", c=(0.62, 0.67)),
               dict(k="paint", c=(0.0, 0.175), mat="deco")],
        parts=[dict(k="petals", n=4, c=(0.20, 0.58), w=0.07, h=0.012, shape="leaf", bend=1.1, mat="accent")]),
    # Sabah, Guntor: 5-fold Kinabalu peaks
    "sabah": dict(arch="jantung", h=0.98, segs=128, profile="heart", wood="merbau", metal="iron", deco="silver",
        density=(16.0, 0.14), lace=("scales", "lace", "grid"),
        lathe=[dict(k="groove", z=0.22), dict(k="ring", z=0.40), dict(k="groove", z=0.52, mat="deco"),
               dict(k="facets", z=(0.555, 0.74), n=20, depth=0.014), dict(k="band", z=(0.775, 0.855)),
               dict(k="inlay", c=(0.64, 0.69)), dict(k="paint", c=(0.0, 0.165), mat="deco")],
        parts=[dict(k="horns", n=5, c=0.34, len=0.075, r0=0.027, lean=0.12, curl=0.0, mat="deco"),
               dict(k="petals", n=5, c=(0.40, 0.60), w=0.032, h=0.011, shape="drop", phase=0.5, mat="accent")]),
    # Sarawak, Tuai Rumah Jarat: ebony, kenyalang crest, pua bands (the most ornate)
    "sarawak": dict(arch="jantung", h=1.0, segs=128, profile="heart", wood="ebony", metal="iron", deco="gold",
        density=(18.0, 0.16), lace=("scales", "lace", "flower"),
        lathe=[dict(k="groove", z=0.20, mat="deco"), dict(k="ring", z=0.40), dict(k="band", z=(0.50, 0.54)),
               dict(k="bead", z=0.57, mat="deco"), dict(k="band", z=(0.60, 0.65)), dict(k="band", z=(0.775, 0.855)),
               dict(k="inlay", c=(0.60, 0.66)), dict(k="paint", c=(0.0, 0.165), mat="deco")],
        parts=[dict(k="beads", n=16, z=0.705, a=0.011, mat="deco"),
               dict(k="horns", n=4, c=0.36, len=0.06, r0=0.014, lean=0.9, curl=1.4, mat="deco"),
               dict(k="petals", n=8, c=(0.40, 0.57), w=0.022, h=0.009, shape="drop", mat="accent")]),
}
BASE = ("jantung", "uri", "pakdin", "cikros", "tokgayong", "datuk")
GAME_LIGHT = {"ambient": ((0.26, 0.12, 0.03), 0.3), "sun": ((1.0, 0.58, 0.26), 0.85), "lantern": ((1.0, 0.42, 0.12), 60.0)}


def master_colors():
    """Each master's own lacquer (story_data.gd MASTERS[i].color), for previews of the master's top."""
    try:
        src = open(os.path.join(REPO, "scripts", "story_data.gd"), encoding="utf-8").read()
    except OSError:
        return {}
    out, cur = {}, None
    for line in src.splitlines():
        m = re.search(r'"id": "(\w+)", "mesh"', line)
        if m:
            cur = m.group(1)
        m = re.search(r'"color": Color\(([\d.]+), ([\d.]+), ([\d.]+)\)', line)
        if m and cur:
            out[cur] = tuple(float(x) for x in m.groups())
            cur = None
    return out


# ---------------------------------------------------------------- profile curve
def _lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def catmull(pts, n=32):
    """Centripetal Catmull-Rom through (r, z) points -> dense polyline (no overshoot at tight turns)."""
    P = [_lerp(pts[1], pts[0], 2.0)] + list(pts) + [_lerp(pts[-2], pts[-1], 2.0)]
    out = [pts[0]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t1 = max(math.dist(p0, p1), 1e-9) ** 0.5
        t2 = t1 + max(math.dist(p1, p2), 1e-9) ** 0.5
        t3 = t2 + max(math.dist(p2, p3), 1e-9) ** 0.5
        for k in range(1, n + 1):
            t = t1 + (t2 - t1) * k / n
            a1, a2, a3 = _lerp(p0, p1, t / t1), _lerp(p1, p2, (t - t1) / (t2 - t1)), _lerp(p2, p3, (t - t2) / (t3 - t2))
            b1, b2 = _lerp(a1, a2, t / t2), _lerp(a2, a3, (t - t1) / (t3 - t1))
            out.append(_lerp(b1, b2, (t - t1) / (t2 - t1)))
    return out


class Curve:
    """Dense (r, z) profile with arc length s and outward normals (tangent rotated -90 deg)."""
    def __init__(self, pts):
        self.p = catmull(pts)
        self.s = [0.0]
        for a, b in zip(self.p, self.p[1:]):
            self.s.append(self.s[-1] + math.dist(a, b))
        self.n = []
        for i in range(len(self.p)):
            a, b = self.p[max(i - 1, 0)], self.p[min(i + 1, len(self.p) - 1)]
            tr, tz = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(tr, tz) or 1.0
            self.n.append((tz / ln, -tr / ln))
        self.length = self.s[-1]

    def _idx(self, s):
        lo, hi = 0, len(self.s) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.s[mid] <= s:
                lo = mid
            else:
                hi = mid
        return lo

    def at(self, s):
        """-> r, z, nr, nz at arc length s."""
        s = min(max(s, 0.0), self.length)
        i = self._idx(s)
        u = (s - self.s[i]) / max(self.s[i + 1] - self.s[i], 1e-12)
        r, z = _lerp(self.p[i], self.p[i + 1], u)
        nr, nz = _lerp(self.n[i], self.n[i + 1], u)
        ln = math.hypot(nr, nz) or 1.0
        return r, z, nr / ln, nz / ln

    def s_at_z(self, z):
        """First crossing of height z going up the side."""
        for i in range(len(self.p) - 1):
            za, zb = self.p[i][1], self.p[i + 1][1]
            if za <= z <= zb and zb > za:
                return self.s[i] + (self.s[i + 1] - self.s[i]) * (z - za) / (zb - za)
        return 0.0 if z <= self.p[0][1] else self.length

    def s_at_c(self, r):
        """Crown position: first crossing of radius r searching down from the axis."""
        for i in range(len(self.p) - 1, 0, -1):
            ra, rb = self.p[i][0], self.p[i - 1][0]
            if ra <= r <= rb and rb > ra:
                return self.s[i] - (self.s[i] - self.s[i - 1]) * (r - ra) / (rb - ra)
        return self.length if r <= self.p[-1][0] else 0.0

    def samples(self, ang=9.0, step=0.04):
        """Adaptive base rows: a new row every `ang` degrees of turning or `step` metres of arc."""
        keep, acc = [0.0], 0.0
        for i in range(1, len(self.p) - 1):
            a = math.atan2(self.p[i][1] - self.p[i - 1][1], self.p[i][0] - self.p[i - 1][0])
            b = math.atan2(self.p[i + 1][1] - self.p[i][1], self.p[i + 1][0] - self.p[i][0])
            acc += abs(math.degrees((b - a + math.pi) % (2 * math.pi) - math.pi))
            if acc >= ang or self.s[i] - keep[-1] >= step:
                keep.append(self.s[i])
                acc = 0.0
        keep.append(self.length)
        return keep


def smoothstep(e0, e1, x):
    t = min(max((x - e0) / max(e1 - e0, 1e-9), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------- profile features -> lathe rows
def resolve(curve, f, H, R):
    """Feature position -> arc length (or sorted pair)."""
    v, fn = (f["z"], lambda x: curve.s_at_z(x * H)) if "z" in f else (f["c"], lambda x: curve.s_at_c(x * R))
    if isinstance(v, (tuple, list)):
        return tuple(sorted((fn(v[0]), fn(v[1]))))
    return fn(v)


def profile_rows(curve, spec, H, R):
    """-> rows [(s, off, sharp, order)], spans [(a, b, mat)], facets, zones [(z0, z1, kind)] for the wayang.
    Every cut has depth: bevelled lips into the groove, chamfered fillets under the lacquer, recessed inlays."""
    bps, solid, plateau, spans, facets, zones = [], [], [], [], [], []

    def zone(a, b, kind, f):
        if "z" in f:   # side features only: the crown is a thin dome seen side-on
            zones.append((curve.at(a)[1], curve.at(b)[1], kind))

    for f in spec.get("lathe", []):
        k, mat = f["k"], f.get("mat")
        if k == "groove":
            c = resolve(curve, f, H, R)
            w, d, e = f.get("w", 0.016), f.get("d", 0.008), f.get("lip", 0.0035)
            a, b = c - w / 2, c + w / 2
            if f.get("shape", "v") == "v":
                mid = [(a + e, -e * 0.55), (c, -d), (b - e, -e * 0.55)]
            else:
                mid = [(a + e, -e * 0.55), (a + w * 0.34, -d), (b - w * 0.34, -d), (b - e, -e * 0.55)]
            bps += [(a, 0.0, True, 0)] + [(s, o, True, 1 + i) for i, (s, o) in enumerate(mid)] + [(b, 0.0, True, 9)]
            solid.append((a, b))
            spans.append((a, b, mat or "body"))
            zone(c, c, "cut", f)
        elif k == "bead":
            c = resolve(curve, f, H, R)
            w, h = f.get("w", 0.018), f.get("h", 0.008)
            a, b = c - w / 2, c + w / 2
            bps += [(a, 0.0, True, 0), (a + w * 0.28, h * 0.86, False, 1), (b - w * 0.28, h * 0.86, False, 2),
                    (b, 0.0, True, 3)]
            solid.append((a, b))
            spans.append((a, b, mat or "deco"))
            zone(a, b, "bead", f)
        elif k == "band":
            a, b = resolve(curve, f, H, R)
            dz, e = f.get("raise", 0.006), f.get("chamfer", 0.0045)
            bps += [(a, 0.0, True, 0), (a + e, dz, True, 1), (b - e, dz, True, 0), (b, 0.0, True, 1)]
            solid += [(a, a + e), (b - e, b)]
            plateau.append((a + e, b - e, dz))
            spans.append((a, b, mat or "accent"))
            zone(a, b, "band", f)
        elif k == "inlay":
            a, b = resolve(curve, f, H, R)
            d, e = f.get("depth", 0.005), f.get("wall", 0.0015)
            bps += [(a, 0.0, True, 0), (a + e, -d, True, 1), (b - e, -d, True, 0), (b, 0.0, True, 1)]
            solid += [(a, a + e), (b - e, b)]
            plateau.append((a + e, b - e, -d))
            spans.append((a + e, b - e, mat or "deco"))   # walls stay wood: a channel cut into the crown
            zone(a, b, "band", f)
        elif k == "ring":
            c = resolve(curve, f, H, R)
            h, p, bv = f.get("h", 0.028), f.get("p", 0.016), f.get("bevel", 0.004)
            a, b = c - h / 2, c + h / 2
            bps += [(a, 0.0, True, 0), (a, p - bv, True, 1), (a + bv, p, True, 2), (b - bv, p, True, 3),
                    (b, p - bv, True, 4), (b, 0.0, True, 5)]
            solid.append((a, b))
            spans.append((a, b, mat or "metal"))
            zone(a, b, "ring", f)
        elif k == "paint":
            a, b = resolve(curve, f, H, R)
            bps += [(a, 0.0, False, 0), (b, 0.0, False, 0)]
            spans.append((a, b, mat))
        elif k == "facets":
            a, b = resolve(curve, f, H, R)
            rnd = random.Random(f.get("seed", 0))
            jit = [1.0 + f.get("jitter", 0.0) * (rnd.random() * 2 - 1) for _ in range(f["n"])]
            facets.append(dict(f, span=(a, b), jit=jit))
            if f.get("pitch"):   # woven cells: a near-vertical step at every pitch boundary
                q = a + f["pitch"]
                while q < b - 0.004:
                    bps += [(q - 0.0012, 0.0, True, 0), (q + 0.0012, 0.0, True, 0)]
                    q += f["pitch"]
        else:
            print("gasing_build: unknown lathe feature", k)
    rows = list(bps)
    for s in curve.samples(*spec.get("density", (16.0, 0.14) if spec.get("segs", 128) <= 96 else (12.0, 0.10))):
        if any(abs(s - b[0]) < 0.0025 for b in bps) or any(a <= s <= b for a, b in solid):
            continue
        off = 0.0
        for a, b, dz in plateau:
            if a <= s <= b:
                off = dz
        rows.append((s, off, False, 0))
    rows.sort(key=lambda r: (r[0], r[3]))
    return rows, spans, facets, zones


def mat_at(spans, s):
    for a, b, mat in reversed(spans):
        if a - 1e-7 <= s <= b + 1e-7:
            return MI[mat]
    return 0


def facet_phase(f, s, per):
    off = int(round(f.get("phase", 0.0) * per))
    if f.get("pitch"):
        off += (per // 2) * (int((s - f["span"][0]) / f["pitch"]) % 2)
    return off


def facet_disp(facets, s, j, segs, r):
    d = 0.0
    for f in facets:
        a, b = f["span"]
        if not (a <= s <= b):
            continue
        t = (s - a) / max(b - a, 1e-9)
        fade = f.get("fade", 0.0 if f.get("style") == "flat" else 0.2)   # flat cuts stay crisp to the zone edge
        taper = smoothstep(0.0, fade, t) * smoothstep(0.0, fade, 1.0 - t)
        n = f["n"]
        per = segs // n
        jj = j + facet_phase(f, s, per)
        phi = (jj % per) / per
        if f.get("style") == "flat":
            dd = r * (1.0 - math.cos(math.pi / n) / math.cos(math.pi * (2.0 * phi - 1.0) / n))
        else:
            dd = f.get("depth", 0.012) * math.sin(math.pi * phi) ** 0.6   # flat-bottomed gouge, crisp ridges
        d -= dd * f["jit"][(jj // per) % n] * taper
    return d


# ---------------------------------------------------------------- mesh builders (all into one bmesh)
def lathe(bm, rows, segs, facets=()):
    """rows: [(r, z, nr, nz, mat, sharp, s)] tip -> axis; faces between rows i, i+1 take rows[i] mat."""
    rings = []
    for r, z, nr, nz, _m, _sh, s in rows:
        if r < 1e-6:
            rings.append([bm.verts.new((0.0, 0.0, z))])
            continue
        ring = []
        for j in range(segs):
            a = 2.0 * math.pi * j / segs
            d = facet_disp(facets, s, j, segs, r) if facets else 0.0
            rr, zz = r + d * nr, z + d * nz
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), zz)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        lo, hi = rings[i], rings[i + 1]
        for j in range(segs):
            k = (j + 1) % segs
            if len(lo) == 1:
                f = bm.faces.new((lo[0], hi[k], hi[j]))
            elif len(hi) == 1:
                f = bm.faces.new((lo[j], lo[k], hi[0]))
            else:
                f = bm.faces.new((lo[j], lo[k], hi[k], hi[j]))
            f.material_index = rows[i][4]
            f.smooth = True
    for i, row in enumerate(rows):
        if row[5] and len(rings[i]) > 1:
            for j in range(segs):
                bm.edges.get((rings[i][j], rings[i][(j + 1) % segs])).smooth = False
    for f in facets:   # carved ridges stay crisp
        per = segs // f["n"]
        for i in range(len(rows) - 1):
            s0, s1 = rows[i][6], rows[i + 1][6]
            a, b = f["span"]
            if len(rings[i]) == 1 or len(rings[i + 1]) == 1 or not (a < s0 and s1 < b):
                continue
            o0, o1 = facet_phase(f, s0, per), facet_phase(f, s1, per)
            if o0 != o1:
                continue
            for j in range(segs):
                if (j + o0) % per == 0:
                    bm.edges.get((rings[i][j], rings[i + 1][j])).smooth = False
    return rings


def add_grid(bm, grid, mi, closed_u=False):
    """Quad strip between consecutive rows of vertex lists."""
    for g0, g1 in zip(grid, grid[1:]):
        n = len(g0)
        for j in range(n if closed_u else n - 1):
            k = (j + 1) % n
            f = bm.faces.new((g0[j], g1[j], g1[k], g0[k]))
            f.material_index = mi
            f.smooth = True


def petal_width(shape, u):
    if shape == "drop":   # teardrop, round outer end
        return math.sin(math.pi * 0.5 * u / 0.7) ** 0.8 if u < 0.7 else math.sqrt(max(0.0, 1 - ((u - 0.7) / 0.3) ** 2))
    if shape == "ray":
        return 0.5 + 0.5 * math.sin(math.pi * u) ** 0.3
    if shape == "grain":  # plump padi grain
        return math.sin(math.pi * u) ** 0.55
    return math.sin(math.pi * u) ** 0.75   # leaf


# carved relief cross-section: steep walls rising from below the crown, a bevelled top edge, an incised midrib
PETAL_X = (-1.0, -1.0, -0.78, -0.3, 0.0, 0.3, 0.78, 1.0, 1.0)
PETAL_H = (-0.45, 0.55, 0.96, 1.0, 0.70, 1.0, 0.96, 0.55, -0.45)


def petals(bm, curve, f, R):
    """n carved relief petals lying on the crown between crown radii c0..c1."""
    n, rows_n, mi = f["n"], f.get("rows", 7), MI[f.get("mat", "accent")]
    c0, c1 = f["c"]
    W_, h, bend, shape = f["w"], f.get("h", 0.010), f.get("bend", 0.0), f.get("shape", "leaf")
    xs, hs = (PETAL_X, PETAL_H) if shape != "ray" else ((-1, -1, -0.7, 0, 0.7, 1, 1), (-0.45, 0.6, 0.95, 1.0, 0.95, 0.6, -0.45))

    def surf(u, ang, height):
        r, z, nr, nz = curve.at(curve.s_at_c((c0 + (c1 - c0) * u) * R))
        ang += bend * u
        return bm.verts.new(((r + nr * height) * math.cos(ang), (r + nr * height) * math.sin(ang), z + nz * height))

    for k in range(n):
        a0 = 2.0 * math.pi * (k + f.get("phase", 0.0)) / n
        grid = []
        for i in range(rows_n):
            u = (i + 1) / (rows_n + 1)
            rho = (c0 + (c1 - c0) * u) * R
            hw = W_ * max(petal_width(shape, u), 0.08)
            grid.append([surf(u, a0 + x * hw / rho, hh * h) for x, hh in zip(xs, hs)])
        add_grid(bm, grid, mi)
        for u, row, inner in ((0.0, grid[0], True), (1.0, grid[-1], False)):
            tip = surf(u, a0, 0.15 * h)
            for j in range(len(row) - 1):
                fc = bm.faces.new((tip, row[j], row[j + 1]) if inner else (tip, row[j + 1], row[j]))
                fc.material_index = mi
                fc.smooth = True


def rope(bm, curve, f, H):
    """3-lay twisted cord ringing the body at height z, half sunk into it."""
    a, mi = f["a"], MI[f.get("mat", "deco")]
    r, z, nr, _nz = curve.at(curve.s_at_z(f["z"] * H))
    ring_r = r + a * 0.55
    lay = max(3, round(2 * math.pi * ring_r / (7.0 * a)))   # lay length ~3.5 diameters
    m, kk = f.get("samples", lay * 9), 9
    grid = []
    for i in range(m):
        al = 2.0 * math.pi * i / m
        psi = 2.0 * math.pi * lay * i / m
        ux, uy = math.cos(al), math.sin(al)
        row = []
        for j in range(kk):
            ph = 2.0 * math.pi * j / kk
            rho = a * (1.0 + 0.24 * math.cos(3.0 * (ph - psi)))
            rr = ring_r + rho * math.cos(ph)
            row.append(bm.verts.new((rr * ux, rr * uy, z + rho * math.sin(ph))))
        grid.append(row)
    for g0, g1 in zip(grid, grid[1:] + grid[:1]):
        for j in range(kk):
            k = (j + 1) % kk
            fc = bm.faces.new((g0[j], g0[k], g1[k], g1[j]))
            fc.material_index = mi
            fc.smooth = True
    return z - a, z + a


def beads(bm, curve, f, H, R):
    s = resolve(curve, f, H, R)
    r, z, nr, nz = curve.at(s)
    a, mi, sq = f["a"], MI[f.get("mat", "deco")], f.get("squash", 1.0)   # squash < 1: domed nail heads
    for k in range(f["n"]):
        al = 2.0 * math.pi * (k + f.get("phase", 0.0)) / f["n"]
        nrm = Vector((nr * math.cos(al), nr * math.sin(al), nz))
        c = Vector((r * math.cos(al), r * math.sin(al), z)) + nrm * (a * sq * 0.5)
        res = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=a)
        for v in res["verts"]:
            v.co = c + v.co - nrm * (v.co.dot(nrm) * (1.0 - sq))
        for fc in {fc for v in res["verts"] for fc in v.link_faces}:
            fc.material_index = mi
            fc.smooth = True
    return z - a, z + a


def horns(bm, curve, f, R):
    """n tapered horns rising from the crown: lean pushes them outward, curl sweeps the tips up."""
    r, z, nr, nz = curve.at(curve.s_at_c(f["c"] * R))
    L, r0, mi = f["len"], f["r0"], MI[f.get("mat", "deco")]
    lean, curl, sides, steps = f.get("lean", 0.5), f.get("curl", 0.0), 8, 9
    for k in range(f["n"]):
        al = 2.0 * math.pi * (k + f.get("phase", 0.0)) / f["n"]
        out, up = Vector((math.cos(al), math.sin(al), 0.0)), Vector((0.0, 0.0, 1.0))
        p0 = Vector((r * math.cos(al), r * math.sin(al), z - r0 * 0.4))
        p1 = p0 + out * (lean * L) + up * (0.35 * L)
        p2 = p0 + out * (lean * L * (1.3 - 0.5 * curl)) + up * (L * (1.0 + 0.4 * curl))
        side = Vector((-math.sin(al), math.cos(al), 0.0))
        grid = []
        for i in range(steps):
            u = i / (steps - 1)
            c = p0.lerp(p1, u).lerp(p1.lerp(p2, u), u)
            tan = ((p1 - p0) * (1 - u) + (p2 - p1) * u).normalized()
            nrm = side.cross(tan).normalized()
            rad = r0 * (1.0 - u) ** 0.8 + 0.0015
            grid.append([bm.verts.new(c + (side * math.cos(2 * math.pi * j / sides) +
                                           nrm * math.sin(2 * math.pi * j / sides)) * rad) for j in range(sides)])
        add_grid(bm, grid, mi, closed_u=True)
        tip = bm.verts.new(p2 + (p2 - p1).normalized() * 0.004)
        last = grid[-1]
        for j in range(sides):
            fc = bm.faces.new((last[j], tip, last[(j + 1) % sides]))
            fc.material_index = mi
            fc.smooth = True


def mark_sharp_by_angle(bm, deg=35.0):
    lim = math.radians(deg)
    bm.normal_update()
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > lim:
            e.smooth = False


def material(name, srgb, metal=0.0, rough=0.5):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = lin(srgb) + (1.0,)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    return m


# ---------------------------------------------------------------- build one top
def build_mesh(spec, R, H, segs):
    ctrl = spec["profile"] if isinstance(spec["profile"], list) else PROFILES[spec["profile"]]
    k = 1.0
    for _ in range(3):   # radial fit: the outermost row (the iron ring) lands exactly on r_max
        curve = Curve([(rn * R * k, t * H) for t, rn in ctrl])
        rows, spans, facets, zones = profile_rows(curve, spec, H, R)
        best = max(rows, key=lambda q: curve.at(q[0])[0] + q[1] * curve.at(q[0])[2])
        r0, _z, nr, _nz = curve.at(best[0])
        k *= (R - best[1] * nr) / r0
        if abs(r0 + best[1] * nr - R) < 2e-5:
            break
    lrows = []
    for i, (s, off, sharp, _o) in enumerate(rows):
        r, z, nr, nz = curve.at(s)
        nxt = rows[i + 1][0] if i + 1 < len(rows) else s
        lrows.append((max(r + off * nr, 0.0) if s < curve.length - 1e-6 else 0.0, z + off * nz, nr, nz,
                      mat_at(spans, (s + nxt) / 2), sharp, s))
    bm = bmesh.new()
    lathe(bm, lrows, segs, facets)
    # paku tip + collar: its own 16-segment lathe (iron), hiding the body's open start ring
    rs0, zs0 = curve.p[0]
    rtop = curve.at(curve.s_at_z(zs0 + 0.008))[0]
    rc, zc0, zc1 = rtop + 0.005, zs0 - 0.010, zs0 + 0.008
    rsp = 0.42 * rc
    tip = [(0.0, 0.0), (0.0025, 0.0015), (0.0045, 0.0045), (rsp, zc0), (rc - 0.003, zc0), (rc, zc0 + 0.003),
           (rc, zc1 - 0.003), (rc - 0.003, zc1), (rs0 * 0.6, zc1)]
    lathe(bm, [(r, z, 1.0, 0.0, MI["metal"], False, 0.0) for r, z in tip], 16)
    for f in spec.get("parts", []):
        if f["k"] == "petals":
            petals(bm, curve, f, R)
        elif f["k"] == "rope":
            zones.append(rope(bm, curve, f, H) + ("rope",))
        elif f["k"] == "beads":
            zr = beads(bm, curve, f, H, R)
            if "z" in f:
                zones.append(zr + ("beads",))
        elif f["k"] == "horns":
            horns(bm, curve, f, R)
        else:
            print("gasing_build: unknown part", f["k"])
    mark_sharp_by_angle(bm)
    return bm, dict(rows=len(lrows), zones=zones, tip_top=zc1)


def build(tid):
    spec = TOPS[tid]
    R, H = spec.get("r", ARCH[spec["arch"]][0]), spec.get("h", ARCH[spec["arch"]][1])
    segs = spec.get("segs", 96 if tid in BASE else 128)
    hb = H
    for _ in range(5):   # height fit: horns and crests count toward H, so the lathe shrinks to make room
        bm, info = build_mesh(spec, R, hb, segs)
        zmax = max(v.co.z for v in bm.verts)
        if abs(zmax - H) < 0.003:
            break
        bm.free()
        hb *= H / zmax
    me = bpy.data.meshes.new("Gasing_" + tid)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material("Body", WOOD[spec["wood"]], 0.0, 0.7))
    me.materials.append(material("Accent", spec.get("lacquer", GOLD), 0.0, 0.55))
    me.materials.append(material("Metal", *FINISH[spec["metal"]]))
    me.materials.append(material("Deco", *FINISH[spec["deco"]]))
    used = {p.material_index for p in me.polygons}
    missing = [SLOTS[i] for i in range(4) if i not in used]
    if missing:
        raise RuntimeError("%s: slots own no faces: %s (glTF would drop them)" % (tid, missing))
    ob = bpy.data.objects.new("Gasing_" + tid, me)
    bpy.context.collection.objects.link(ob)
    info.update(R=R, H=H, H_lathe=round(hb, 4), spec=spec)
    return ob, info


def export_glb(ob, path):
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_texcoords=False, export_normals=True, export_tangents=False,
                              export_vertex_color="NONE", export_attributes=False, export_materials="EXPORT",
                              export_cameras=False, export_lights=False, export_extras=False)


def check_glb(path):
    """Parse the GLB itself: node/mesh count, primitive -> material order, attributes, footprint, Godot band radii."""
    data = open(path, "rb").read()
    jlen = struct.unpack_from("<I", data, 12)[0]
    js = json.loads(data[20:20 + jlen])
    binoff = 20 + jlen + 8
    prims = js["meshes"][0]["primitives"]
    names = [js["materials"][p["material"]]["name"] for p in prims]
    attrs = sorted({a for p in prims for a in p["attributes"]})

    def floats(acc_i):
        acc = js["accessors"][acc_i]
        bv = js["bufferViews"][acc["bufferView"]]
        off = binoff + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        return np.frombuffer(data, dtype="<f4", count=acc["count"] * 3, offset=off).reshape(-1, 3)

    pos = [floats(p["attributes"]["POSITION"]) for p in prims]
    allp = np.concatenate(pos)
    rad = np.hypot(allp[:, 0], allp[:, 2])
    tris = sum(js["accessors"][p["indices"]]["count"] // 3 for p in prims)
    body = pos[0]
    bands = []
    for i in range(4):   # gasing.gd _band_profile on surface 0 at aabb.end.y * (0.25 + 0.1 i)
        h = float(allp[:, 1].max()) * (0.25 + 0.1 * i)
        below, above = body[body[:, 1] <= h], body[body[:, 1] >= h]
        if len(below) == 0 or len(above) == 0:
            bands.append(-1.0)
            continue
        yb, ya = below[:, 1].max(), above[:, 1].min()
        wb = np.hypot(below[below[:, 1] == yb][:, 0], below[below[:, 1] == yb][:, 2]).max()
        wa = np.hypot(above[above[:, 1] == ya][:, 0], above[above[:, 1] == ya][:, 2]).max()
        bands.append(round(float(wb + (wa - wb) * (h - yb) / max(ya - yb, 1e-3)), 4))
    # belly: height of the widest Body ring (the footprint rule wants it at 0.38-0.48 H jantung, 0.30-0.40 H uri)
    belly = float(body[np.argmax(np.hypot(body[:, 0], body[:, 2])), 1])
    return dict(nodes=len(js["nodes"]), meshes=len(js["meshes"]), slots=names, attributes=attrs,
                tris=int(tris), verts=int(len(allp)), r_max=round(float(rad.max()), 4),
                H=round(float(allp[:, 1].max()), 4), y_min=round(float(allp[:, 1].min()), 5),
                belly_frac=round(belly / float(allp[:, 1].max()), 3),
                tip_r=round(float(rad[allp[:, 1] < 0.002].max()), 4) if (allp[:, 1] < 0.002).any() else None,
                band_radii=bands, faces_per_slot=[js["accessors"][p["indices"]]["count"] // 3 for p in prims],
                bytes=len(data))


# ---------------------------------------------------------------- images (stdlib PNG writer, numpy post)
def write_png(path, a):
    """a: HxWx4 uint8, top row first."""
    h, w = a.shape[:2]
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) +
                 chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def load_px(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    return buf.reshape(h, w, 4)[::-1]


def to8(a):
    return (np.clip(a, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def erode(m, n):
    for i in range(n):
        p = np.pad(m, 1)
        c = p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
        if i % 2:
            c &= p[:-2, :-2] & p[:-2, 2:] & p[2:, :-2] & p[2:, 2:]
        m = c
    return m


def stamp(m, y, x, r, diamond=False):
    r = max(int(r), 1)
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    k = (np.abs(yy) + np.abs(xx) <= r) if diamond else (yy * yy + xx * xx <= r * r)
    y0, x0 = y - r, x - r
    sy, sx = slice(max(y0, 0), min(y0 + 2 * r + 1, m.shape[0])), slice(max(x0, 0), min(x0 + 2 * r + 1, m.shape[1]))
    m[sy, sx] |= k[sy.start - y0:sy.stop - y0, sx.start - x0:sx.stop - x0]


# ---------------------------------------------------------------- wayang top silhouette
def wayang_parts(info, z_of_row, rows, ppm):
    """Horizontal part map for the side silhouette: tip, then body zones between the carved features, each feature
    (ring, lacquer band, bead row, rope) its own part. Parts are numbered bottom-up so, as in wayang_lib's Canvas,
    the upper part carries the lace along each seam. -> (pid per row, cls name per pid, body pids)."""
    feats = sorted((min(a, b), max(a, b), k) for a, b, k in info["zones"] if k != "cut")
    cuts = sorted(a for a, b, k in info["zones"] if k == "cut")
    segs, z = [(-1.0, info["tip_top"], "tip")], info["tip_top"]

    def body(z0, z1):
        edges = [z0] + [c for c in cuts if z0 + 0.02 < c < z1 - 0.02] + [z1]
        for a, b in zip(edges, edges[1:]):
            segs.append((a, b, "body"))

    for z0, z1, k in feats:
        if z1 <= z:
            continue
        if z0 > z:
            body(z, z0)
        segs.append((max(z0, z), z1, k))
        z = z1
    body(z, 9.0)
    cycle = info["spec"].get("lace", ("scales", "lace", "flower"))
    cls, bodies, bi = [], [], 0
    for i, (z0, z1, k) in enumerate(segs):
        hpx = (min(z1, info["H"]) - max(z0, 0.0)) * ppm
        if k == "tip" or hpx < 22:
            c = "solid"
        elif k == "band" and hpx >= 56:
            c = "grid"   # a broad lacquer band gets its own diamond lattice
        elif k != "body" or hpx < 40:
            c = "edge" if hpx >= 30 else "solid"
        elif i == len(segs) - 1 and hpx < 80:
            c = "rays" if hpx >= 60 else "edge"   # a small knob/crown cap
        else:
            c = cycle[bi % len(cycle)]
            bi += 1
            bodies.append(i + 1)
        cls.append(c)
    zr = z_of_row(np.arange(rows))
    pid_row = np.zeros(rows, np.uint16)
    for i, (z0, z1, k) in enumerate(segs):
        pid_row[(zr >= z0) & (zr < z1)] = i + 1
    pid_row[zr >= segs[-1][0]] = len(segs)
    return pid_row, cls, bodies


def render_wayang(ob, info, path, preview_path):
    """Side silhouette, black on transparent, 512x512, tip at the bottom centre (main.gd pivots there), cut with
    wayang_lib's tatahan (contour lace rows + class lattices, k = 1 like the beat scenes) and one carved bunga."""
    R, H, res = info["R"], info["H"], 1024
    ppm = min(880.0 / (2.0 * R), 900.0 / H)
    engine_setup(res, res, 16, transparent=True)
    world((0, 0, 0), 0.0)
    only([ob])
    zc = (res / 2 - 12) / ppm   # tip 12 px above the bottom edge at 2x
    cam = add_cam((0.0, -20.0, zc), (90.0, 0.0, 0.0), ortho=res / ppm)
    tmp = path + ".tmp.png"
    render(tmp)
    alpha = load_px(tmp)[:, :, 3]
    os.remove(tmp)
    bpy.data.objects.remove(cam, do_unlink=True)
    solid = alpha > 0.5
    pid_row, cls_names, bodies = wayang_parts(info, lambda y: (res / 2 + zc * ppm - y) / ppm, res, ppm)
    pid = np.where(solid, pid_row[:, None], 0).astype(np.uint16)
    code = np.array([0] + [W.CLS.index(c) for c in cls_names], np.uint8)
    cls = code[pid]
    # bunga: one carved rosette (no rim, like Canvas.carve) at the deepest point of the biggest lattice zone
    carve = np.zeros_like(solid)
    if bodies:
        big = max(bodies, key=lambda p: int((pid == p).sum()))
        m, d = pid == big, 0
        while True:
            nxt = erode(m, 6)
            if not nxt.any():
                break
            m, d = nxt, d + 6
        if d >= 36:
            ys, xs = np.nonzero(m)
            cy, cx, rr = int(ys.mean()), int(xs.mean()), d * 0.8
            n = next((p["n"] for p in info["spec"].get("parts", []) if p["k"] == "petals" and p["n"] >= 6), 8)
            stamp(carve, cy, cx, rr * 0.16)
            for i in range(n):
                a = 2.0 * math.pi * (i + 0.5) / n
                for t, rad in ((0.40, 0.12), (0.60, 0.095), (0.77, 0.065)):   # teardrop petals
                    stamp(carve, int(cy + math.sin(a) * rr * t), int(cx + math.cos(a) * rr * t), rr * rad)
    avoid = W.box_blur(carve.astype(np.float32), 5, 1) > 0.02
    hole = W.perforate(cls, pid, 1.0, avoid)
    a = alpha * (1.0 - hole) * (1.0 - carve)
    a = a.reshape(512, 2, 512, 2).mean(axis=(1, 3))
    size = W.save_alpha_png(a, path)
    if preview_path:   # kelir: lamp-lit cloth with the silhouette tinted ink
        g = np.linspace(0.0, 1.0, 512)[:, None, None]
        bg = np.array([0.98, 0.82, 0.50]) * (1 - g) + np.array([0.70, 0.40, 0.16]) * g
        col = bg * (1 - a[:, :, None]) + np.array([0.12, 0.07, 0.03]) * a[:, :, None]
        pv = np.ones((512, 512, 4), dtype=np.float32)
        pv[:, :, :3] = col
        write_png(preview_path, to8(pv))
    return size, dict(zip(range(1, len(cls_names) + 1), cls_names))


# ---------------------------------------------------------------- render helpers
def engine_setup(w, h, samples=32, transparent=False):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.eevee.taa_render_samples = samples
    sc.view_settings.view_transform = "Standard"   # keeps lacquer saturation; Blender's Filmic/AgX wash it out
    sc.view_settings.look = "Medium High Contrast"


def world(rgb, strength):
    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    if w.node_tree is None:
        w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bg.inputs[1].default_value = strength


def add_light(name, direction, strength, rgb=(1, 1, 1), angle=2.0, at=None):
    """Sun shining along `direction`, or a point light of `strength` watts placed `at`."""
    ld = bpy.data.lights.new(name, "SUN" if at is None else "POINT")
    ld.energy, ld.color = strength, rgb
    if at is None:
        ld.angle = math.radians(angle)
    else:
        ld.shadow_soft_size = 0.05
    ob = bpy.data.objects.new(name, ld)
    if at is not None:
        ob.location = at
    ob.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(ob)
    return ob


def add_cam(loc, rot_deg=None, target=None, ortho=None, fov=None, vertical=False):
    cd = bpy.data.cameras.new("Cam")
    if ortho:
        cd.type, cd.ortho_scale = "ORTHO", ortho
    if fov:
        cd.sensor_fit = "VERTICAL" if vertical else "AUTO"
        cd.angle = math.radians(fov)
    cd.clip_end = 200.0
    ob = bpy.data.objects.new("Cam", cd)
    ob.location = loc
    if target is not None:
        ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    else:
        ob.rotation_euler = [math.radians(a) for a in rot_deg]
    bpy.context.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def plain(name, rgb, rough=0.8):
    return material(name, rgb, 0.0, rough)


def disc(name, r, z, mat, depth=0.3):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=r, radius2=r, depth=depth)
    for v in bm.verts:
        v.co.z += z - depth / 2
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def wood_preview(name, base_lin, old=False):
    """Approximates gasing.gd in game: species albedo x gently swept straight grain (dark latewood lines), the same
    height as a bump, roughness 0.70, no clearcoat at level 1. Old tops: stock brown, old noise normal + gloss."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Roughness"].default_value = 0.5 if old else 0.7
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 2.0, 0.9)
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_profile = "SIN"
    wv.inputs["Scale"].default_value = 4.4    # ~14 rings per grain tile, like gasing.gd
    wv.inputs["Distortion"].default_value = 1.5
    wv.inputs["Detail"].default_value = 1.5
    wv.inputs["Detail Scale"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (1.0, 1.0, 1.0, 1.0)
    els[1].position, els[1].color = 1.0, (0.62, 0.62, 0.62, 1.0)
    e = els.new(0.7)
    e.color = (0.97, 0.97, 0.97, 1.0)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs["A"].default_value = base_lin + (1.0,)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    nt.links.new(wv.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    if old:
        b.inputs["Coat Weight"].default_value = 0.6
        b.inputs["Coat Roughness"].default_value = 0.2
    return m


def accent_preview(name, srgb):
    """gasing.gd in game: Accent = style/team colour, satin (roughness 0.55), emission 0.15."""
    m = material(name, srgb, 0.0, 0.55)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Emission Color"].default_value = lin(srgb) + (1.0,)
    b.inputs["Emission Strength"].default_value = 0.15
    return m


def game_copy(src, x, accent, new=True, name=None):
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = name or src.name + "_pv"
    ob.location = (x, 0.0, 0.0)
    bpy.context.collection.objects.link(ob)
    body = ob.data.materials[0]
    wood = tuple(body.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value)[:3] if new else \
        lin((0.42, 0.24, 0.11))   # old tops: gasing.gd's hard-coded brown
    ob.data.materials[0] = wood_preview("PvWood", wood, old=not new)
    ob.data.materials[1] = accent_preview("PvAccent", accent)
    ob.hide_render = False
    return ob


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    obs = [o for o in bpy.data.objects if o not in before]
    mesh = [o for o in obs if o.type == "MESH"][0]
    mw = mesh.matrix_world.copy()
    mesh.parent = None
    mesh.matrix_world = mw
    for o in obs:
        if o is not mesh:
            bpy.data.objects.remove(o, do_unlink=True)
    mesh.hide_render = True
    return mesh


def only(obs):
    keep = set(obs)
    for o in bpy.context.scene.objects:
        if o.type in ("MESH",):
            o.hide_render = o not in keep


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def projected_box(cam, obs, w, h):
    from bpy_extras.object_utils import world_to_camera_view
    xs, ys = [], []
    for o in obs:
        for c in o.bound_box:
            p = world_to_camera_view(bpy.context.scene, cam, o.matrix_world @ Vector(c))
            xs.append(p.x * w)
            ys.append((1.0 - p.y) * h)
    return min(xs), min(ys), max(xs), max(ys)


def render_previews(tid, ob, info, pdir, old_path, master):
    R, H = info["R"], info["H"]
    alt = master if master else FOE
    old = import_glb(old_path) if old_path and os.path.exists(old_path) else None
    old_r = max(Vector(c).xy.length for c in old.bound_box) if old else 0.0
    old_h = max(c[2] for c in old.bound_box) if old else 0.0
    studio = [add_light("Key", (0.7, 1.0, -1.1), 3.4, (1.0, 0.95, 0.88), 3.0),
              add_light("Rim", (-0.5, -1.4, -0.5), 2.4, (0.85, 0.9, 1.0), 3.0)]
    # side ortho, old | new
    engine_setup(768, 384, 32)
    world((0.30, 0.28, 0.26), 0.8)
    gap = 0.3
    xo, xn = -(old_r + gap / 2) if old else 0.0, (R + gap / 2) if old else 0.0
    shown = [game_copy(ob, xn, GOLD)]
    if old:
        shown.append(game_copy(old, xo, GOLD, new=False))
    width = (2 * (old_r + R) + gap + 0.5) if old else 2 * R + 0.5
    span = max(width, 2.0 * 1.15 * max(H, old_h))
    only(shown)
    cam = add_cam(((xo + xn) / 2 if old else 0.0, -20.0, span / 4 - 0.04), (90.0, 0.0, 0.0), ortho=span)
    render(os.path.join(pdir, tid + "_side.png"))
    for o in shown + [cam]:
        bpy.data.objects.remove(o, do_unlink=True)
    # 3/4 close-up (workshop-like): player's gold lacquer, warm floor for contact shadow
    engine_setup(768, 768, 48)
    world((0.20, 0.17, 0.14), 0.7)
    floor = disc("PvFloor", 3.0, 0.0, plain("PvFloorMat", (0.45, 0.33, 0.24), 0.8), 0.05)
    shown = [game_copy(ob, 0.0, GOLD)]
    only(shown + [floor])
    size = max(H, 2.0 * R)
    d = size * 0.5 / math.tan(math.radians(14.0)) / 0.82
    el, az = math.radians(26.0), math.radians(-38.0)
    tgt = (0.0, 0.0, H * 0.48)
    cam = add_cam((d * math.cos(el) * math.sin(az), -d * math.cos(el) * math.cos(az), tgt[2] + d * math.sin(el)),
                  target=tgt, fov=28.0)
    render(os.path.join(pdir, tid + "_34.png"))
    for o in shown + [cam, floor] + studio:
        bpy.data.objects.remove(o, do_unlink=True)
    # game camera at battle scale: Godot (0,9,7) pitch -52 FOV 55 (vertical) 1280x720; sun direction and the 8 rim
    # lanterns from main.tscn/_polish_visuals
    engine_setup(1280, 720, 16)
    world(*GAME_LIGHT["ambient"])
    sun = add_light("Sun", (0.329, 0.470, -0.819), GAME_LIGHT["sun"][1] * 1.6, GAME_LIGHT["sun"][0], 1.0)
    lamps = [add_light("Lantern", (0, 0, -1), GAME_LIGHT["lantern"][1], GAME_LIGHT["lantern"][0],
                       at=(4.25 * math.cos(i * math.pi / 4), 4.25 * math.sin(i * math.pi / 4), 0.85)) for i in range(8)]
    dish = disc("PvDish", 4.2, 0.0, plain("PvDishMat", (0.6, 0.42, 0.23), 0.85))
    ground = disc("PvGround", 30.0, -0.02, plain("PvGroundMat", (0.38, 0.26, 0.13), 0.9), 0.1)
    shown = [game_copy(ob, 0.0, GOLD), game_copy(ob, 1.35, alt)]
    if old:
        shown.append(game_copy(old, -1.35, GOLD, new=False))
    only(shown + [dish, ground])
    cam = add_cam((0.0, -7.0, 9.0), (38.0, 0.0, 0.0), fov=55.0, vertical=True)
    full = os.path.join(pdir, tid + "_game.png")
    render(full)
    x0, y0, x1, y1 = projected_box(cam, shown, 1280, 720)
    cx, cy = int((x0 + x1) / 2), int((y0 + y1) / 2)
    px = load_px(full)
    crop = px[max(cy - 64, 0):max(cy - 64, 0) + 128, max(cx - 128, 0):max(cx - 128, 0) + 256]
    crop = np.repeat(np.repeat(crop, 3, axis=0), 3, axis=1)
    crop[:, :, 3] = 1.0
    write_png(os.path.join(pdir, tid + "_game_crop.png"), to8(crop))
    info["game_px_height"] = round(y1 - y0, 1)
    for o in shown + [cam, sun, dish, ground] + lamps:
        bpy.data.objects.remove(o, do_unlink=True)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)


def contact_sheet(ids, pdir):
    """Per top: [side old|new 768x384] [3/4 384x384] [battle-scale crop x3 768x384] [wayang 384x384 (masters)]."""
    rows = []
    for tid in ids:
        paths = [os.path.join(pdir, tid + s) for s in ("_side.png", "_34.png", "_game_crop.png")]
        if not all(os.path.exists(p) for p in paths):
            continue
        side, q, crop = (load_px(p) for p in paths)
        q = q.reshape(384, 2, 384, 2, 4).mean(axis=(1, 3))
        wp = os.path.join(pdir, tid + "_wayang_preview.png")
        ix = (np.arange(384) * 4) // 3   # the whole 512 silhouette, nearest-sampled to 384
        wy = load_px(wp)[ix][:, ix] if os.path.exists(wp) else np.zeros((384, 384, 4), np.float32)
        row = np.concatenate([side, q, crop, wy], axis=1)
        row[:, :, 3] = 1.0
        row[-3:] = (0.08, 0.05, 0.03, 1.0)
        rows.append(row)
    if rows:
        write_png(os.path.join(pdir, "contact.png"), to8(np.concatenate(rows, axis=0)))


# ---------------------------------------------------------------- main
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts, ids, i = {}, [], 0
    while i < len(argv):
        a = argv[i]
        if a in ("--out", "--preview", "--compare"):
            opts[a[2:]] = argv[i + 1]
            i += 2
            continue
        if a.startswith("--"):
            opts[a[2:]] = True
        else:
            ids += list(TOPS) if a == "all" else [a]
        i += 1
    if opts.get("sheet") and opts.get("preview"):   # contact sheet only, from previews already on disk
        return contact_sheet(list(TOPS), opts["preview"])
    unknown = [t for t in ids if t not in TOPS]
    if unknown or not ids:
        raise SystemExit("gasing_build: give ids from %s or 'all' (unknown: %s)" % (list(TOPS), unknown))
    out = os.path.abspath(opts.get("out", os.path.join(REPO, "assets")))
    pdir = opts.get("preview")
    masters = master_colors()
    os.makedirs(os.path.join(out, "wayang"), exist_ok=True)
    report = {}
    if pdir:
        os.makedirs(pdir, exist_ok=True)
        rp = os.path.join(pdir, "report.json")
        if os.path.exists(rp):
            report = json.load(open(rp))
    for tid in ids:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        ob, info = build(tid)
        glb = os.path.join(out, "gasing_%s.glb" % tid)
        export_glb(ob, glb)
        rep = check_glb(glb)
        base = tid in BASE
        R, H = info["R"], info["H"]
        lo, hi = (6000, 10000) if base else (12000, 18000)
        bl = (0.30, 0.40) if TOPS[tid]["arch"] == "uri" else (0.38, 0.48)
        rep["checks"] = {
            "single_mesh": rep["nodes"] == 1 and rep["meshes"] == 1,
            "slots": rep["slots"] == list(SLOTS),
            "no_uv_no_color": not any(a.startswith(("TEXCOORD", "COLOR")) for a in rep["attributes"]),
            "tip_at_origin": abs(rep["y_min"]) < 1e-4,
            "r_max": abs(rep["r_max"] - R) <= 0.01,
            "H": abs(rep["H"] - H) <= 0.01,
            "belly": bl[0] - 0.005 <= rep["belly_frac"] <= bl[1] + 0.005,
            "tris_budget": lo <= rep["tris"] <= hi,
            "size_budget": rep["bytes"] <= 450 * 1024,
            "bands_found": all(b > 0 for b in rep["band_radii"]),
        }
        rep.update(target_r=R, target_H=H, H_lathe=info["H_lathe"], lathe_rows=info["rows"], glb=glb,
                   wood=TOPS[tid]["wood"])
        if pdir and not opts.get("no-render"):
            cmp_dir = opts.get("compare")
            old = None
            if cmp_dir:
                old = os.path.join(cmp_dir, "gasing_%s.glb" % tid)
                if not os.path.exists(old):
                    old = os.path.join(cmp_dir, "gasing_jantung.glb")   # what the game fell back to
            render_previews(tid, ob, info, pdir, old, masters.get(tid))
            rep["compare"] = old
            rep["game_px_height"] = info.get("game_px_height")
        if tid not in BASE and not opts.get("no-wayang") and not opts.get("no-render"):   # cutscenes use masters only
            wp = os.path.join(out, "wayang", "wayang_top_%s.png" % tid)
            size, parts = render_wayang(ob, info, wp, os.path.join(pdir, tid + "_wayang_preview.png") if pdir else None)
            rep.update(wayang=wp, wayang_bytes=size, wayang_parts=parts)
        report[tid] = rep
        print("GASING %s %s" % (tid, json.dumps({k: rep[k] for k in ("tris", "lathe_rows", "verts", "r_max", "H",
                                                                     "belly_frac", "bytes", "slots", "band_radii",
                                                                     "checks")})))
    if pdir:
        json.dump(report, open(os.path.join(pdir, "report.json"), "w"), indent=1)
        if not opts.get("no-render"):
            contact_sheet([t for t in TOPS if t in report], pdir)


main()
