extends RefCounted
# Runtime dressing for story arena GLBs built by art_src/arenakit.py:
#  - Mat<Kind>_* materials get a per-kind world-triplanar noise albedo breakup + noise normal and use the
#    COLOR_0 vertex colour (linear) as albedo; Water kinds get one shared water shader.
#  - EnvScatter<Grass|Paddy|Reed>_<density> hidden source meshes become swaying MultiMesh blades
#    (area-sampled, fixed seed, <= MAX_INSTANCES in total, no shadows).
#  - KHR point lights are normalised (Blender W -> energy W*0.02, range from an "_r<metres>" name suffix).
#  - EnvFar_* and flat ground/water meshes cast no shadows.
#  - MatSky_* (painted backdrop: cloud cards, far ridge layers) is unshaded, fog-free, two-sided vertex colour.
# Legacy GLBs (no Mat* materials, no EnvScatter*, no lights) pass through untouched.
# Textures/shaders/blade meshes are built once and cached in static vars (synchronous, no pop-in).

const MAX_INSTANCES: int = 15000
const NOISE_SIZE: int = 256
const LIGHT_W_PER_CANDELA: float = 4.0 * PI / 683.0 # glTF intensity (cd) -> Blender watts
const LIGHT_ENERGY_PER_W: float = 0.02
const NO_SHADOW_KINDS: Array[String] = ["Ground", "Grass", "Sand", "Mud", "Water", "Sky"]
# kind -> [noise, albedo floor (0..1 brightness of the darkest speck), normal strength, tiles per metre, stretch]
const KINDS: Dictionary = {
	"Ground": ["fbm", 0.64, 1.2, 0.7, Vector3.ONE],
	"Grass": ["fbm", 0.76, 0.7, 0.9, Vector3.ONE],
	"Sand": ["ridge", 0.84, 0.8, 0.6, Vector3(1.0, 1.0, 3.0)],
	"Mud": ["cell", 0.68, 1.1, 0.8, Vector3.ONE],
	"Rock": ["cell", 0.70, 1.1, 0.9, Vector3.ONE],
	"Wood": ["fbm", 0.72, 0.7, 1.4, Vector3(1.0, 5.0, 1.0)], # grain runs vertically on posts
	"Thatch": ["ridge", 0.62, 1.2, 1.8, Vector3(1.0, 4.0, 1.0)],
	"Leaf": ["fbm", 0.74, 0.8, 2.2, Vector3.ONE],
	"Plaster": ["fbm", 0.86, 0.4, 0.5, Vector3.ONE],
	"Tile": ["cell", 0.82, 0.5, 1.5, Vector3.ONE],
	"Metal": ["fbm", 0.78, 0.5, 1.2, Vector3.ONE],
	"Cloth": ["fbm", 0.86, 0.4, 3.0, Vector3.ONE],
}
# blade kinds: [blades per clump, height range, lean, base half-width, two-tri blades]
const BLADES: Dictionary = {
	"Grass": [6, Vector2(0.12, 0.26), 0.25, 0.022, false],
	"Paddy": [4, Vector2(0.32, 0.52), 0.16, 0.018, true],
	"Reed": [3, Vector2(0.75, 1.25), 0.14, 0.02, true],
}

const WATER_SHADER: String = """
shader_type spatial;
render_mode cull_back, specular_schlick_ggx;
uniform sampler2D ripple : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D breakup : filter_linear_mipmap, repeat_enable;
uniform vec3 foam_color : source_color = vec3(0.86, 0.84, 0.78);
varying vec3 wpos;
void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
void fragment() {
	vec2 uv = wpos.xz;
	vec3 a = texture(ripple, uv * 0.13 + TIME * vec2(0.011, 0.006)).rgb;
	vec3 b = texture(ripple, uv * 0.29 + vec2(0.37, 0.71) - TIME * vec2(0.006, 0.013)).rgb;
	NORMAL_MAP = (a + b) * 0.5;
	NORMAL_MAP_DEPTH = 0.6;
	float n = texture(breakup, uv * 0.35 + TIME * vec2(0.02, 0.004)).r;
	float foam = clamp((1.0 - COLOR.a) * 1.6 * smoothstep(0.25, 0.85, n + (1.0 - COLOR.a) * 0.35), 0.0, 1.0);
	ALBEDO = mix(COLOR.rgb * (0.85 + 0.3 * n), foam_color, foam);
	ROUGHNESS = mix(0.34, 0.9, foam);
	SPECULAR = 0.22;
}
"""

const BLADE_SHADER: String = """
shader_type spatial;
render_mode cull_disabled, diffuse_burley;
uniform float sway = 0.05;
uniform vec2 wind_dir = vec2(1.0, 0.3);
uniform float gust_period = 0.0;
uniform float gust = 0.0;
void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float g = 0.0;
	if (gust_period > 0.0) {
		float ph = fract(TIME / gust_period);
		g = gust * smoothstep(0.0, 0.06, ph) * (1.0 - smoothstep(0.06, 0.45, ph));
	}
	float s = sin(TIME * 1.7 + dot(w.xz, vec2(0.55, 0.35))) * 0.6 + sin(TIME * 2.9 + w.x * 1.3 - w.z * 0.7) * 0.4;
	vec2 off = normalize(wind_dir) * sway * (0.5 + s + 2.5 * g) * VERTEX.y * VERTEX.y;
	VERTEX += inverse(mat3(MODEL_MATRIX)) * vec3(off.x, 0.0, off.y);
}
void fragment() {
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz); // both faces lit like the ground
	ALBEDO = COLOR.rgb;
	ROUGHNESS = 0.85;
	SPECULAR = 0.2;
	BACKLIGHT = COLOR.rgb * 0.35;
}
"""

static var _tex: Dictionary = {}
static var _water: ShaderMaterial
static var _blade_mat: ShaderMaterial
static var _blades: Dictionary = {}


static func dress(root: Node3D, def: Dictionary) -> void:
	if root == null:
		return
	var scatter: Array[MeshInstance3D] = []
	for n: Node in root.find_children("*", "", true, false):
		if n is MeshInstance3D:
			var mi: MeshInstance3D = n as MeshInstance3D
			if String(mi.name).begins_with("EnvScatter"):
				scatter.append(mi)
			else:
				_dress_mesh(mi)
		elif n is OmniLight3D:
			_dress_light(n as OmniLight3D)
	if not scatter.is_empty():
		_build_scatter(root, scatter, def.get("hazard", {}))


static func _dress_mesh(mi: MeshInstance3D) -> void:
	var mesh: Mesh = mi.mesh
	if mesh == null:
		return
	var flat: bool = String(mi.name).begins_with("EnvFar_")
	for s: int in mesh.get_surface_count():
		var m: StandardMaterial3D = mesh.surface_get_material(s) as StandardMaterial3D
		if m == null or not m.resource_name.begins_with("Mat"):
			continue
		var kind: String = m.resource_name.substr(3).get_slice("_", 0)
		flat = flat or kind in NO_SHADOW_KINDS
		if kind == "Water":
			mi.set_surface_override_material(s, _water_material())
		elif kind == "Glow":
			m.vertex_color_use_as_albedo = true
		elif kind == "Sky":
			_apply_sky(m)
		elif KINDS.has(kind):
			_apply_kind(m, KINDS[kind])
	if flat:
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


# Edits the cached imported material in place; every assignment is absolute, so re-dressing is a no-op.
static func _apply_kind(m: StandardMaterial3D, p: Array) -> void:
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = false # glTF COLOR_0 is linear
	m.albedo_color = Color.WHITE
	m.albedo_texture = _noise(p[0], p[1], false)
	m.normal_enabled = true
	m.normal_texture = _noise(p[0], 0.0, true)
	m.normal_scale = p[2]
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_triplanar_sharpness = 2.0
	m.uv1_scale = (p[4] as Vector3) * float(p[3])
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC


# Painted backdrop: the vertex colour is the final (linear) colour; the author bakes the haze in.
static func _apply_sky(m: StandardMaterial3D) -> void:
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = false
	m.albedo_color = Color.WHITE
	m.albedo_texture = null
	m.emission_enabled = false
	m.disable_fog = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED


# A dressed material for meshes outside the GLBs (e.g. main.gd's Floor dish): same triplanar noise breakup
# and normal as the arena kinds, flat `color` instead of vertex colour. Unknown kinds fall back to Ground.
static func kind_material(kind: String, color: Color, roughness: float = 0.92) -> StandardMaterial3D:
	var m: StandardMaterial3D = StandardMaterial3D.new()
	_apply_kind(m, KINDS.get(kind, KINDS["Ground"]))
	m.vertex_color_use_as_albedo = false
	m.albedo_color = color
	m.roughness = roughness
	return m


static func _dress_light(l: OmniLight3D) -> void:
	if l.light_energy < 30.0: # already normalised (or not a raw glTF candela value)
		return
	l.light_energy = l.light_energy * LIGHT_W_PER_CANDELA * LIGHT_ENERGY_PER_W
	var r: float = 5.0
	var nm: String = String(l.name)
	var i: int = nm.rfind("_r")
	if i >= 0 and nm.substr(i + 2).is_valid_float():
		r = nm.substr(i + 2).to_float()
	l.omni_range = r
	l.omni_attenuation = 1.0
	l.shadow_enabled = false


# Seamless greyscale noise: albedo = remapped to [lo, 1] (mean ~1, so vertex colour keeps its value),
# normal = bump-mapped. Synchronous Image work (no NoiseTexture2D thread -> no first-frame pop).
static func _noise(kind: String, lo: float, normal: bool) -> Texture2D:
	var key: String = "%s:%s:%s" % [kind, lo, normal]
	if _tex.has(key):
		return _tex[key]
	var fn: FastNoiseLite = FastNoiseLite.new()
	fn.seed = 7
	fn.fractal_octaves = 4
	match kind:
		"cell":
			fn.noise_type = FastNoiseLite.TYPE_CELLULAR
			fn.cellular_return_type = FastNoiseLite.RETURN_DISTANCE2_SUB
			fn.fractal_type = FastNoiseLite.FRACTAL_FBM
			fn.fractal_octaves = 2
			fn.frequency = 0.035
		"ridge":
			fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
			fn.fractal_type = FastNoiseLite.FRACTAL_RIDGED
			fn.frequency = 0.03
		_:
			fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
			fn.fractal_type = FastNoiseLite.FRACTAL_FBM
			fn.frequency = 0.03
	var img: Image = fn.get_seamless_image(NOISE_SIZE, NOISE_SIZE)
	img.convert(Image.FORMAT_RGB8)
	if normal:
		img.bump_map_to_normal_map(6.0)
	else:
		var k: float = (1.0 - lo) / (1.0 + lo)
		img.adjust_bcs(1.0, k, 1.0) # squeeze around 0.5 ...
		img.adjust_bcs(1.0 / (0.5 + 0.5 * k), 1.0, 1.0) # ... then lift so the brightest speck is 1.0
	img.generate_mipmaps()
	var tex: ImageTexture = ImageTexture.create_from_image(img)
	_tex[key] = tex
	return tex


static func _water_material() -> ShaderMaterial:
	if _water == null:
		var sh: Shader = Shader.new()
		sh.code = WATER_SHADER
		_water = ShaderMaterial.new()
		_water.shader = sh
		_water.set_shader_parameter("ripple", _noise("fbm", 0.0, true))
		_water.set_shader_parameter("breakup", _noise("fbm", 0.4, false))
	return _water


static func _blade_material(hazard: Dictionary) -> ShaderMaterial:
	if _blade_mat == null:
		var sh: Shader = Shader.new()
		sh.code = BLADE_SHADER
		_blade_mat = ShaderMaterial.new()
		_blade_mat.shader = sh
	var windy: bool = String(hazard.get("kind", "")) == "wind"
	var dir: Vector2 = hazard.get("dir", Vector2(1.0, 0.3)) if windy else Vector2(1.0, 0.3)
	_blade_mat.set_shader_parameter("wind_dir", dir if dir.length() > 0.01 else Vector2(1.0, 0.3))
	_blade_mat.set_shader_parameter("sway", 0.05 + (0.05 * float(hazard.get("strength", 1.0)) if windy else 0.0))
	_blade_mat.set_shader_parameter("gust_period", float(hazard.get("period", 0.0)) if windy else 0.0)
	_blade_mat.set_shader_parameter("gust", float(hazard.get("gust", 0.0)) * 0.5 if windy else 0.0)
	return _blade_mat


# One clump mesh per kind, height normalised to 1 (instances scale it), normals up so blades shade like
# the ground, vertex colour = base-to-tip gradient (multiplied by the instance tint).
static func _blade_mesh(kind: String) -> ArrayMesh:
	if _blades.has(kind):
		return _blades[kind]
	var b: Array = BLADES[kind]
	var n: int = b[0]
	var lean: float = b[2]
	var w: float = b[3]
	var bent: bool = b[4]
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 11
	var st: SurfaceTool = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_normal(Vector3.UP)
	for i: int in n:
		var a: float = TAU * float(i) / float(n) + rng.randf_range(-0.4, 0.4)
		var d: Vector3 = Vector3(cos(a), 0.0, sin(a))
		var side: Vector3 = Vector3(-d.z, 0.0, d.x) * w
		var tip: Vector3 = d * lean * rng.randf_range(0.6, 1.2) + Vector3.UP * rng.randf_range(0.8, 1.0)
		var c0: Color = Color(0.62, 0.62, 0.6)
		var c1: Color = Color(1.0, 1.0, 0.92)
		if bent:
			var mid: Vector3 = tip * 0.55 - d * lean * 0.15
			var cm: Color = c0.lerp(c1, 0.6)
			for v: Array in [[-side, c0], [side, c0], [mid + side * 0.6, cm], [-side, c0], [mid + side * 0.6, cm], [mid - side * 0.6, cm],
					[mid - side * 0.6, cm], [mid + side * 0.6, cm], [tip, c1]]:
				st.set_color(v[1])
				st.add_vertex(v[0])
		else:
			for v: Array in [[-side, c0], [side, c0], [tip, c1]]:
				st.set_color(v[1])
				st.add_vertex(v[0])
	var mesh: ArrayMesh = st.commit()
	_blades[kind] = mesh
	return mesh


static func _build_scatter(root: Node3D, sources: Array[MeshInstance3D], hazard: Dictionary) -> void:
	# pass 1: total requested instances -> global density scale k (cap MAX_INSTANCES)
	var plans: Array = []
	var total: float = 0.0
	for mi: MeshInstance3D in sources:
		mi.visible = false
		var parts: PackedStringArray = String(mi.name).trim_prefix("EnvScatter").split("_")
		if mi.mesh == null or not BLADES.has(parts[0]):
			continue
		var dens: float = parts[1].to_float() if parts.size() > 1 else 10.0
		var arr: Array = mi.mesh.surface_get_arrays(0)
		var xf: Transform3D = Transform3D.IDENTITY
		var p: Node = mi
		while p != null and p != root:
			xf = (p as Node3D).transform * xf
			p = p.get_parent()
		var verts: PackedVector3Array = xf * (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array)
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array(range(verts.size()))
		var area: float = 0.0
		for t: int in range(0, idx.size(), 3):
			area += (verts[idx[t + 1]] - verts[idx[t]]).cross(verts[idx[t + 2]] - verts[idx[t]]).length() * 0.5
		total += area * dens
		plans.append([mi, parts[0], dens, verts, idx, arr[Mesh.ARRAY_COLOR]])
	var k: float = minf(1.0, float(MAX_INSTANCES) / maxf(total, 1.0))
	var mat: ShaderMaterial = _blade_material(hazard)
	# pass 2: one MultiMesh per source, cached on the source mesh (re-dress = reuse)
	for pl: Array in plans:
		var src: MeshInstance3D = pl[0]
		var mm: MultiMesh = src.mesh.get_meta("dress_mm") if src.mesh.has_meta("dress_mm") else null
		if mm == null:
			mm = _sample(pl[1], pl[2] * k, pl[3], pl[4], pl[5], hash(String(src.name)))
			src.mesh.set_meta("dress_mm", mm)
		var mmi: MultiMeshInstance3D = MultiMeshInstance3D.new()
		mmi.name = String(src.name) + "_Blades"
		mmi.multimesh = mm
		mmi.material_override = mat
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(mmi)


static func _sample(kind: String, dens: float, verts: PackedVector3Array, idx: PackedInt32Array, cols: Variant, rng_seed: int) -> MultiMesh:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = rng_seed
	var hr: Vector2 = (BLADES[kind] as Array)[1]
	var xfs: Array[Transform3D] = []
	var tints: Array[Color] = []
	var has_col: bool = cols != null and (cols as PackedColorArray).size() == verts.size()
	var carry: float = 0.0
	for t: int in range(0, idx.size(), 3):
		var a: Vector3 = verts[idx[t]]
		var e1: Vector3 = verts[idx[t + 1]] - a
		var e2: Vector3 = verts[idx[t + 2]] - a
		carry += e1.cross(e2).length() * 0.5 * dens
		while carry >= 1.0:
			carry -= 1.0
			var r1: float = rng.randf()
			var r2: float = rng.randf()
			if r1 + r2 > 1.0:
				r1 = 1.0 - r1
				r2 = 1.0 - r2
			var h: float = rng.randf_range(hr.x, hr.y)
			var wsc: float = rng.randf_range(0.8, 1.25)
			var basis: Basis = Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(wsc, h, wsc))
			xfs.append(Transform3D(basis, a + e1 * r1 + e2 * r2))
			var c: Color = (cols as PackedColorArray)[idx[t]] if has_col else Color(0.3, 0.42, 0.18)
			var j: float = rng.randf_range(0.85, 1.12)
			tints.append(Color(c.r * j, c.g * j, c.b * rng.randf_range(0.85, 1.1)))
	var mm: MultiMesh = MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = _blade_mesh(kind)
	mm.instance_count = xfs.size()
	for i: int in xfs.size():
		mm.set_instance_transform(i, xfs[i])
		mm.set_instance_color(i, tints[i])
	return mm
