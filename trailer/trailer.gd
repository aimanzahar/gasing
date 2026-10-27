extends Node3D
# Gasing Pangkah — the 60-second motion-graphics trailer, built from the game's own assets.
# Render: tools/render_trailer.ps1 (score -> Movie Maker frames -> mp4). Preview: run this scene;
# `seek(sec)` or `-- --from=<sec>` starts mid-trailer.
#
# Picture and score share trailer/cues.json: 128 BPM, 32 bars = exactly 60 s. The edit clock `t` is
# frames / 60 (never delta), so Engine.time_scale can slow the world (tops, sparks, tweens, TIME) for
# bullet time while every cut stays on the beat. Cameras and motion graphics are pure functions of `t`.
# All 2D is laid out in 1920x1080 pixels (the window renders at that size whatever its own size).

const MAIN = preload("res://main.gd") # ARENA_DEFS, STYLE_DEFS and the real WindMeter
const HT = preload("res://scripts/heritage_theme.gd")
const SD = preload("res://scripts/story_data.gd")
const ARENA_DRESS = preload("res://scripts/arena_dress.gd")
const GASING_SCENE: PackedScene = preload("res://gasing.tscn")
const FONT_TITLE: FontFile = preload("res://common/fonts/Kurland.ttf")
const FONT_BODY: FontFile = preload("res://common/fonts/body.ttf")
const TEX_SONGKET: Texture2D = preload("res://assets/ui/songket_band.png")
const TEX_GUNUNGAN_GOLD: Texture2D = preload("res://assets/ui/gunungan_gold.png")
const SCORE_PATH: String = "res://trailer/trailer_score.wav"

const W: float = 1920.0
const H: float = 1080.0
const FPS: float = 60.0
const BAR_H: float = 138.3 # 2.39:1 letterbox inside 16:9
const STAGE_H: float = 768.7 # a 2048x820 kelir scene at full width
const GROUND_Y: float = 832.1 # its ground line (CUT_GROUND 0.12 up from the stage bottom)
const EMBLEM_Y: float = 320.0 # title lockup: gunungan centre, size, wordmark baseline
const EMBLEM_SIZE: float = 560.0
const TITLE_Y: float = 740.0
const INK: Color = HT.INK
const GOLD: Color = HT.SONGKET_GOLD
const CREAM: Color = HT.TEXT_COLOR
const DIM: Color = HT.TEXT_DIM
const OUTLINE: Color = Color(0.25, 0.12, 0.02)
const ORDER: Array[String] = ["perlis", "kedah", "penang", "perak", "selangor", "nsembilan", "melaka",
	"johor", "pahang", "terengganu", "kelantan", "sabah", "sarawak"]
const LINES: Dictionary = {
	"perlis": "Patient as the padi.", "kedah": "Times every move.", "penang": "Fast and loud.",
	"perak": "Knows every slope.", "selangor": "Restless and fierce.", "nsembilan": "Answers every move.",
	"melaka": "Many heritages, one style.", "johor": "Never lets up.", "pahang": "Calm on the slopes.",
	"terengganu": "Rises like the tide.", "kelantan": "Drifts like a kite.", "sabah": "Never tires.",
	"sarawak": "Your final challenge.",
}
# state capitals (lon, lat) in travel order, for the journey map
const CAPITALS: Array[Vector2] = [Vector2(100.20, 6.44), Vector2(100.37, 6.12), Vector2(100.33, 5.41),
	Vector2(101.08, 4.60), Vector2(101.52, 3.07), Vector2(101.94, 2.73), Vector2(102.25, 2.19),
	Vector2(103.74, 1.49), Vector2(103.33, 3.81), Vector2(103.14, 5.33), Vector2(102.24, 6.13),
	Vector2(116.07, 5.98), Vector2(110.34, 1.55)]
const PENINSULA: Array[Vector2] = [Vector2(100.13, 6.44), Vector2(100.20, 6.70), Vector2(100.40, 6.65),
	Vector2(100.80, 6.45), Vector2(101.10, 6.25), Vector2(101.60, 5.80), Vector2(101.80, 5.75),
	Vector2(102.10, 6.20), Vector2(102.30, 6.20), Vector2(102.60, 5.95), Vector2(103.00, 5.60),
	Vector2(103.25, 5.25), Vector2(103.45, 4.80), Vector2(103.45, 4.25), Vector2(103.40, 3.80),
	Vector2(103.45, 3.30), Vector2(103.65, 2.75), Vector2(103.85, 2.40), Vector2(104.10, 1.90),
	Vector2(104.25, 1.45), Vector2(103.95, 1.40), Vector2(103.50, 1.30), Vector2(103.40, 1.40),
	Vector2(103.00, 1.70), Vector2(102.60, 1.95), Vector2(102.25, 2.20), Vector2(101.85, 2.55),
	Vector2(101.40, 2.95), Vector2(101.20, 3.35), Vector2(100.90, 3.85), Vector2(100.70, 4.20),
	Vector2(100.60, 4.75), Vector2(100.40, 5.10), Vector2(100.35, 5.55), Vector2(100.30, 5.95),
	Vector2(100.20, 6.20)]
const BORNEO: Array[Vector2] = [Vector2(109.65, 2.05), Vector2(110.35, 1.72), Vector2(111.00, 1.60),
	Vector2(111.40, 2.30), Vector2(111.80, 2.85), Vector2(112.70, 3.10), Vector2(113.30, 3.35),
	Vector2(113.95, 4.40), Vector2(114.60, 4.90), Vector2(115.20, 5.10), Vector2(115.60, 5.60),
	Vector2(116.05, 6.00), Vector2(116.60, 6.70), Vector2(116.85, 7.00), Vector2(117.30, 6.60),
	Vector2(117.70, 6.00), Vector2(118.30, 5.80), Vector2(119.20, 5.20), Vector2(118.70, 4.50),
	Vector2(117.90, 4.20), Vector2(117.50, 4.20), Vector2(116.50, 4.30), Vector2(115.60, 4.00),
	Vector2(115.30, 3.40), Vector2(114.80, 2.30), Vector2(114.30, 1.50), Vector2(113.60, 1.25),
	Vector2(112.80, 1.55), Vector2(112.00, 1.40), Vector2(111.20, 1.00), Vector2(110.60, 0.90),
	Vector2(110.00, 1.30)]
const POST_SHADER: String = """
shader_type canvas_item;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform float flash = 0.0;
uniform vec3 flash_col = vec3(1.0, 0.92, 0.75);
uniform float ca = 0.0;
uniform float vignette = 0.32;
uniform float grain = 0.04;
uniform float frame = 0.0;
uniform vec2 shake = vec2(0.0);
uniform float zoom_blur = 0.0;
uniform vec2 zoom_center = vec2(0.5);
uniform float fade = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

void fragment() {
	vec2 uv = SCREEN_UV + shake;
	vec2 dir = uv - zoom_center;
	vec3 col = vec3(0.0);
	int n = zoom_blur > 0.001 ? 12 : 1;
	for (int i = 0; i < 12; i++) {
		if (i >= n) { break; }
		vec2 u = zoom_center + dir * (1.0 - zoom_blur * float(i) / 12.0);
		vec2 off = (u - 0.5) * ca;
		col += vec3(texture(screen_tex, u + off).r, texture(screen_tex, u).g, texture(screen_tex, u - off).b);
	}
	col /= float(n);
	float v = smoothstep(0.95, 0.25, length((SCREEN_UV - 0.5) * vec2(1.0, 0.75)));
	col *= mix(1.0, v, vignette);
	col += (hash(FRAGCOORD.xy + vec2(frame * 13.1, frame * 7.7)) - 0.5) * grain;
	col = mix(col, flash_col, clamp(flash, 0.0, 1.0));
	col = mix(col, vec3(0.0), clamp(fade, 0.0, 1.0));
	COLOR = vec4(col, 1.0);
}
"""
const SHINE_SHADER: String = """
shader_type canvas_item;
uniform float shine = -1.0;
void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	float band = 1.0 - smoothstep(0.0, 0.09, abs(UV.x * 0.8 + UV.y * 0.45 - shine));
	COLOR = vec4(c.rgb + band * 0.75 * c.a, c.a);
}
"""

# ---- clock
var t: float = 0.0
var spb: float = 60.0 / 128.0
var cues: Dictionary = {}
var _movie: bool = false
var _frame: int = 0
var _from: int = 0 # first frame of this run
var _t0_us: int = 0
var _shots: Array = [] # [name, start, end]
var _shot: int = -1
var _cards: Array = [] # {id, m, t0, t1, tier, idx}
var _card: int = -1
var _impacts: Array = [] # [time, amount] -> shake + aberration
var _flashes: Array = [] # [time, amount, decay, color]

# ---- world
var world: Node3D
var env: Environment
var sky_mat: ProceduralSkyMaterial
var sun: DirectionalLight3D
var ground: MeshInstance3D
var floor_mat: StandardMaterial3D
var lanterns: Array[OmniLight3D] = []
var arenas: Dictionary = {} # id -> Node3D
var cam: Camera3D
var cam_attr: CameraAttributesPractical
var bursts: Array[CPUParticles3D] = []
var _burst_i: int = 0
var shocks: Array = [] # [MeshInstance3D, start, pos, max radius]
var tops: Array[Gasing] = []
var hero: Gasing = null
var rival: Gasing = null
var ffa: Array[Gasing] = []
var title_top: Gasing = null
var hero_word: Label3D
var _hit_done: Dictionary = {} # one-shot events already fired (keyed by name)

# ---- 2D
var bg: Control
var mg: Control
var bars: Control
var post: ShaderMaterial
var meter: Control
var emblem: TextureRect
var shine: ShaderMaterial
var kelir_tex: GradientTexture2D
var lamp_mask: GradientTexture2D
var tex: Dictionary = {} # path -> Texture2D
var _fig_x: Dictionary = {} # puppet path -> horizontal centre of its figure (0..1)
var _map_dots: PackedVector2Array = PackedVector2Array()
var _map_pips: PackedVector2Array = PackedVector2Array()
var _emblem_dots: Array = [] # [target, start]
var _music: AudioStreamPlayer = null


func _ready() -> void:
	seed(1729)
	process_priority = -1 # tops read their choreographed positions in the same frame
	_movie = OS.has_feature("movie")
	var win: Window = get_window()
	win.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	win.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP
	win.content_scale_size = Vector2i(int(W), int(H))
	var from: float = 0.0
	for a: String in OS.get_cmdline_user_args():
		if a.begins_with("--from="):
			from = a.trim_prefix("--from=").to_float()
		elif a.begins_with("--from-frame="): # exact frame: re-rendered frames match the full run bit for bit
			from = a.trim_prefix("--from-frame=").to_float() / FPS
	_load_cues()
	_build_quality()
	_build_world()
	_build_2d()
	_build_timeline()
	if _movie: # tools/render_trailer.ps1 re-renders undrawn frames from the start of their shot
		print("TRAILER_SHOTS ", ",".join(_shots.map(func(s: Array) -> String: return str(int(floorf(float(s[1]) * FPS))))))
	if not _movie and FileAccess.file_exists(SCORE_PATH):
		_music = AudioStreamPlayer.new()
		_music.stream = AudioStreamWAV.load_from_file(ProjectSettings.globalize_path(SCORE_PATH))
		add_child(_music)
	seek(from)


func seek(sec: float) -> void:
	_from = roundi(sec * FPS)
	_frame = 0
	_t0_us = Time.get_ticks_usec()
	_shot = -1
	_card = -1
	_hit_done.clear()
	_clear_tops()
	if _music != null:
		_music.play(sec)


# ================================================================ clock, timeline

func _load_cues() -> void:
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://trailer/cues.json"))
	spb = 60.0 / float(d.bpm)
	for k: String in d.cues:
		var v: Array = d.cues[k]
		cues[k] = B(float(v[0]), float(v[1]))


func B(bar: float, beat: float = 1.0) -> float:
	return ((bar - 1.0) * 4.0 + beat - 1.0) * spb


func C(cue: String) -> float:
	return float(cues[cue])


func _build_timeline() -> void:
	_shots = [["lamp", 0.0, B(3)], ["storm", B(3), B(5)], ["shore", B(5), B(7)], ["sight", B(7), B(9)],
		["ring", B(9), B(15)], ["map", B(15), B(17)], ["cards", B(17), B(25)], ["food", B(25), B(26)],
		["carousel", B(26), B(27)], ["ffa", B(27), C("blackout")], ["black", C("blackout"), B(29)],
		["title", B(29), 999.0]]
	for i: int in ORDER.size():
		var id: String = ORDER[i]
		var t0: float = C("card_" + id)
		var t1: float = C("card_" + ORDER[i + 1]) if i + 1 < ORDER.size() else B(25)
		var beats: float = (t1 - t0) / spb
		var tier: int = 0 if beats > 3.5 else (1 if beats > 1.5 else 2)
		_cards.append({"id": id, "m": _master(id), "t0": t0, "t1": t1, "tier": tier, "idx": i})
	for c: Array in [["thunder_1", 0.35], ["thunder_2", 0.45], ["shipwreck", 0.5], ["gasing", 0.25],
			["drop", 0.6], ["launch_land", 0.75], ["rival_land", 0.5], ["pangkah", 1.0], ["snap_back", 0.55],
			["ringout", 0.45], ["map", 0.25], ["masters", 0.35], ["food", 0.3], ["tops", 0.3], ["tag_1", 0.4],
			["tag_2", 0.4], ["tag_3", 0.45], ["ffa_ringout", 0.65], ["title_gong", 0.6], ["topple", 0.35]]:
		_impacts.append([C(c[0]), c[1]])
	var warm: Color = Color(1.0, 0.9, 0.7)
	for f: Array in [["drop", 0.95, 7.0, warm], ["pangkah", 1.0, 11.0, Color(1.0, 0.85, 0.6)], ["snap_back", 0.3, 10.0, warm],
			["map", 0.25, 12.0, warm], ["food", 0.3, 12.0, warm], ["tops", 0.3, 12.0, warm], ["tag_1", 0.3, 14.0, warm],
			["ffa_ringout", 0.4, 10.0, warm], ["title_gong", 0.85, 4.5, Color(1.0, 0.82, 0.45)], ["topple", 0.2, 9.0, warm]]:
		_flashes.append([C(f[0]), f[1], f[2], f[3]])
	for c: Dictionary in _cards:
		var mc: Color = c.m.color
		_flashes.append([c.t0, 0.42 if c.tier == 0 else 0.3, 16.0, mc.lerp(Color.WHITE, 0.55)])
		if c.tier == 0:
			_impacts.append([c.t0, 0.3])


func _process(_delta: float) -> void:
	if _movie:
		t = float(_from + _frame) / FPS # integer frame first: a run started mid-trailer lands on the same floats
	else:
		t = float(_from) / FPS + float(Time.get_ticks_usec() - _t0_us) / 1000000.0
	_frame += 1
	var idx: int = _shots.size() - 1
	for i: int in _shots.size():
		if t < float(_shots[i][2]):
			idx = i
			break
	if idx != _shot:
		_shot = idx
		_enter(String(_shots[idx][0]))
	Engine.time_scale = _rate(t)
	var name_: String = _shots[_shot][0]
	if has_method("_upd_" + name_):
		call("_upd_" + name_, t - float(_shots[_shot][1]))
	_update_shocks()
	_update_post()
	bg.queue_redraw()
	mg.queue_redraw()
	bars.queue_redraw()


func _enter(name_: String) -> void:
	_clear_tops()
	meter.visible = false
	emblem.visible = false
	hero_word.visible = false
	cam.h_offset = 0.0
	world.visible = name_ in ["ring", "cards", "carousel", "ffa", "title"]
	if has_method("_enter_" + name_):
		call("_enter_" + name_)


func _rate(x: float) -> float:
	# world speed: bullet time after PANGKAH! (held, ramping back just before the snap) and a
	# shorter slow-mo on the FFA ring-out
	var r: float = 1.0
	var p: float = C("pangkah")
	var s: float = C("snap_back")
	if x >= p and x < s: # a breath of real speed first, so the sparks freeze already flying apart
		r = lerpf(lerpf(1.0, 0.05, eo_expo(seg(x, p, p + 0.1))), 1.0, ei_expo(seg(x, s - 0.14, s)))
	var f: float = C("ffa_ringout")
	if x >= f and x < f + 0.4:
		r = minf(r, lerpf(0.25, 1.0, ei_quad(seg(x, f + 0.12, f + 0.4))))
	return r


func _world_t(x: float) -> float:
	# integral of _rate: the world's own clock (the choreography under bullet time)
	var w: float = x
	var f: float = C("ffa_ringout")
	for win: Array in [[C("pangkah"), C("snap_back")], [f, f + 0.4]]:
		var a: float = win[0]
		var b: float = minf(win[1], x)
		var y: float = a
		while y < b:
			var h: float = minf(1.0 / 240.0, b - y)
			w -= (1.0 - _rate(y + h * 0.5)) * h
			y += h
	return w


# ================================================================ easing

func seg(x: float, a: float, b: float) -> float:
	return clampf((x - a) / (b - a), 0.0, 1.0)


func eo_expo(x: float) -> float:
	return 1.0 if x >= 1.0 else 1.0 - pow(2.0, -10.0 * x)


func ei_expo(x: float) -> float:
	return 0.0 if x <= 0.0 else pow(2.0, 10.0 * x - 10.0)


func eo_cubic(x: float) -> float:
	return 1.0 - pow(1.0 - x, 3.0)


func ei_cubic(x: float) -> float:
	return x * x * x


func ei_quad(x: float) -> float:
	return x * x


func eio_cubic(x: float) -> float:
	return 4.0 * x * x * x if x < 0.5 else 1.0 - pow(-2.0 * x + 2.0, 3.0) * 0.5


func eio_sine(x: float) -> float:
	return 0.5 - 0.5 * cos(PI * x)


func eo_back(x: float, s: float = 1.70158) -> float:
	return 1.0 + (s + 1.0) * pow(x - 1.0, 3.0) + s * pow(x - 1.0, 2.0)


func eo_elastic(x: float) -> float:
	if x <= 0.0 or x >= 1.0:
		return clampf(x, 0.0, 1.0)
	return pow(2.0, -10.0 * x) * sin((x * 10.0 - 0.75) * TAU / 3.0) + 1.0


func pulse(x: float, t0: float, decay: float) -> float:
	return 0.0 if x < t0 else exp(-(x - t0) * decay)


# ================================================================ world

func _build_quality() -> void:
	RenderingServer.environment_set_ssao_quality(RenderingServer.ENV_SSAO_QUALITY_ULTRA, false, 0.5, 2, 50.0, 300.0)
	RenderingServer.environment_set_ssil_quality(RenderingServer.ENV_SSIL_QUALITY_ULTRA, false, 0.5, 4, 50.0, 300.0)
	RenderingServer.directional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_ULTRA)
	RenderingServer.camera_attributes_set_dof_blur_quality(RenderingServer.DOF_BLUR_QUALITY_HIGH, false)
	var vp: Viewport = get_viewport()
	vp.msaa_3d = Viewport.MSAA_DISABLED
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = 2.0 if _movie and not "--draft" in OS.get_cmdline_user_args() else 1.0 # supersample: AA for grass and highlights


func _build_world() -> void:
	world = Node3D.new()
	world.name = "World"
	add_child(world)
	# atmosphere: main.tscn's Environment + main.gd:_polish_visuals
	env = Environment.new()
	sky_mat = ProceduralSkyMaterial.new()
	sky_mat.sky_curve = 0.15
	sky_mat.ground_bottom_color = Color(0.24, 0.15, 0.09)
	sky_mat.sun_angle_max = 25.0
	var sky: Sky = Sky.new()
	sky.sky_material = sky_mat
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.ssao_enabled = true
	env.ssao_radius = 0.7
	env.ssao_intensity = 3.5
	env.ssao_power = 1.6
	env.ssil_enabled = true
	env.ssil_intensity = 0.6
	env.fog_enabled = true
	env.fog_sky_affect = 0.2
	env.glow_enabled = true
	env.glow_intensity = 0.3
	env.glow_strength = 0.9
	env.glow_bloom = 0.1
	env.glow_hdr_threshold = 1.2
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	var we: WorldEnvironment = WorldEnvironment.new()
	we.environment = env
	add_child(we)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55.0, -35.0, 0.0)
	sun.shadow_enabled = true
	sun.light_angular_distance = 2.0
	sun.shadow_blur = 1.5
	sun.directional_shadow_max_distance = 40.0
	world.add_child(sun)
	var fill: DirectionalLight3D = DirectionalLight3D.new()
	fill.light_color = Color(0.55, 0.66, 0.90)
	fill.light_energy = 0.35
	fill.rotation_degrees = Vector3(-25.0, 150.0, 0.0)
	world.add_child(fill)
	ground = MeshInstance3D.new()
	var gp: PlaneMesh = PlaneMesh.new()
	gp.size = Vector2(44.0, 44.0)
	var gm: StandardMaterial3D = StandardMaterial3D.new()
	gm.albedo_color = Color(0.106, 0.059, 0.027)
	gp.material = gm
	ground.mesh = gp
	ground.position.y = -0.5
	world.add_child(ground)
	var dish: MeshInstance3D = MeshInstance3D.new()
	var cyl: CylinderMesh = CylinderMesh.new()
	cyl.top_radius = 4.2
	cyl.bottom_radius = 4.45
	cyl.height = 0.3
	cyl.radial_segments = 96
	dish.mesh = cyl
	dish.position.y = -0.15
	floor_mat = ARENA_DRESS.kind_material("Plaster", Color(0.6, 0.42, 0.23))
	dish.set_surface_override_material(0, floor_mat)
	world.add_child(dish)
	var mark_mat: ShaderMaterial = ShaderMaterial.new()
	mark_mat.shader = load("res://assets/floor_markings.gdshader") as Shader
	mark_mat.render_priority = -1
	mark_mat.set_shader_parameter("band_color", Color(HT.WOOD_EDGE, 0.6))
	mark_mat.set_shader_parameter("inlay_color", Color(GOLD, 0.5))
	var mark_plane: PlaneMesh = PlaneMesh.new()
	mark_plane.size = Vector2(8.4, 8.4)
	mark_plane.material = mark_mat
	var marks: MeshInstance3D = MeshInstance3D.new()
	marks.mesh = mark_plane
	marks.position.y = 0.006
	marks.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	world.add_child(marks)
	for i: int in 8:
		var ang: float = TAU * float(i) / 8.0
		var om: OmniLight3D = OmniLight3D.new()
		om.omni_range = 3.8
		om.omni_attenuation = 1.5
		om.position = Vector3(cos(ang) * 4.25, 1.6, sin(ang) * 4.25)
		world.add_child(om)
		lanterns.append(om)
	var gel: Node3D = (load("res://assets/gelanggang.glb") as PackedScene).instantiate() as Node3D
	world.add_child(gel)
	ARENA_DRESS.dress(gel, {})
	for id: String in ["kampung"] + ORDER:
		var def: Dictionary = MAIN.ARENA_DEFS[id]
		var inst: Node3D = (load(String(def.env)) as PackedScene).instantiate() as Node3D
		world.add_child(inst)
		ARENA_DRESS.dress(inst, def)
		# dress() shares one grass material whose wind is set per call: give each arena its own
		for b: Node in inst.find_children("*_Blades", "MultiMeshInstance3D", true, false):
			var mmi: MultiMeshInstance3D = b as MultiMeshInstance3D
			mmi.material_override = mmi.material_override.duplicate()
		inst.visible = false
		arenas[id] = inst
	cam = Camera3D.new()
	cam_attr = CameraAttributesPractical.new()
	cam.attributes = cam_attr
	cam.near = 0.05
	cam.far = 400.0
	world.add_child(cam)
	cam.make_current()
	_build_bursts()
	for i: int in 4:
		var ring: MeshInstance3D = MeshInstance3D.new()
		var tm: TorusMesh = TorusMesh.new()
		tm.inner_radius = 0.9
		tm.outer_radius = 1.0
		tm.rings = 96
		tm.ring_segments = 4
		var rm: StandardMaterial3D = StandardMaterial3D.new()
		rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		rm.albedo_color = Color(1.0, 0.92, 0.75, 0.0)
		tm.material = rm
		ring.mesh = tm
		ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		ring.visible = false
		world.add_child(ring)
		shocks.append([ring, -99.0, Vector3.ZERO, 2.4])
	hero_word = Label3D.new()
	hero_word.text = "GASING"
	hero_word.font = FONT_TITLE
	hero_word.font_size = 220
	hero_word.pixel_size = 0.0075
	hero_word.outline_size = 0
	hero_word.modulate = Color(GOLD, 0.95)
	hero_word.shaded = false
	hero_word.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	hero_word.position = Vector3(0.0, 1.05, -3.4)
	hero_word.visible = false
	world.add_child(hero_word)


func _build_bursts() -> void:
	# main.gd:_configure_burst's sparks: hot core -> orange -> clear, unshaded
	for i: int in 6:
		var b: CPUParticles3D = CPUParticles3D.new()
		b.emitting = false
		b.one_shot = true
		b.amount = 64
		b.lifetime = 0.6
		b.explosiveness = 1.0
		b.direction = Vector3.UP
		b.spread = 85.0
		b.initial_velocity_min = 3.0
		b.initial_velocity_max = 7.0
		b.gravity = Vector3(0.0, -9.0, 0.0)
		b.scale_amount_min = 0.5
		b.scale_amount_max = 1.0
		var shrink: Curve = Curve.new()
		shrink.add_point(Vector2(0.0, 1.0))
		shrink.add_point(Vector2(1.0, 0.0))
		b.scale_amount_curve = shrink
		var ramp: Gradient = Gradient.new() # hot yellow -> orange -> ember, never white
		ramp.set_color(0, Color(1.0, 0.9, 0.45))
		ramp.set_color(1, Color(0.9, 0.25, 0.05, 0.0))
		ramp.add_point(0.4, Color(1.0, 0.55, 0.15))
		b.color_ramp = ramp
		var mat: StandardMaterial3D = StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.vertex_color_use_as_albedo = true
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		var m: CapsuleMesh = CapsuleMesh.new() # a streak, stretched along its flight
		m.radius = 0.007
		m.height = 0.15
		m.radial_segments = 6
		m.rings = 2
		m.material = mat
		b.particle_flag_align_y = true
		b.mesh = m
		b.color = Color.WHITE
		world.add_child(b)
		bursts.append(b)


func _burst(pos: Vector3, tint: Color = Color.WHITE, power: float = 1.0) -> void:
	var b: CPUParticles3D = bursts[_burst_i % bursts.size()]
	_burst_i += 1
	b.global_position = pos
	b.color = tint
	b.initial_velocity_max = 7.0 * power
	b.scale_amount_max = 1.0 + 0.4 * power
	b.restart()


func _shock(pos: Vector3, at: float, radius: float = 2.4) -> void:
	var best: Array = shocks[0]
	for s: Array in shocks:
		if float(s[1]) < float(best[1]):
			best = s
	best[1] = at
	best[2] = pos
	best[3] = radius


func _update_shocks() -> void:
	for s: Array in shocks:
		var ring: MeshInstance3D = s[0]
		var age: float = t - float(s[1])
		ring.visible = age >= 0.0 and age < 0.6 and world.visible
		if not ring.visible:
			continue
		var k: float = eo_cubic(age / 0.6)
		ring.position = (s[2] as Vector3) + Vector3(0.0, 0.03, 0.0)
		ring.scale = Vector3(1.0, 0.25, 1.0) * lerpf(0.3, float(s[3]), k)
		((ring.mesh as TorusMesh).material as StandardMaterial3D).albedo_color.a = 0.85 * (1.0 - k)


func _set_arena(id: String, over: Dictionary = {}) -> void:
	var def: Dictionary = (MAIN.ARENA_DEFS[id] as Dictionary).merged(over, true)
	for k: String in arenas:
		(arenas[k] as Node3D).visible = k == id
	sky_mat.sky_top_color = def.sky_top
	sky_mat.sky_horizon_color = def.sky_horizon
	sky_mat.ground_horizon_color = (def.sky_horizon as Color).darkened(0.35)
	env.fog_light_color = def.fog
	env.fog_density = def.fog_density
	env.tonemap_exposure = float(def.get("exposure", 1.05))
	env.ambient_light_energy = float(def.get("ambient", 0.9))
	sun.light_color = def.sun_color
	sun.light_energy = def.sun_energy
	for l: OmniLight3D in lanterns:
		l.light_color = def.lantern
		l.light_energy = float(def.get("lantern_energy", 2.2))
	floor_mat.albedo_color = def.get("floor", Color(0.6, 0.42, 0.23))
	ground.visible = not bool(def.get("hide_ground", false))


func _spawn_top(style: String, accent: Color, pos: Vector3, level: int = 1) -> Gasing:
	var def: Dictionary = MAIN.STYLE_DEFS[style]
	var g: Gasing = GASING_SCENE.instantiate() as Gasing
	world.add_child(g)
	g.setup(String(def.label), String(def.shape), {"mass": def.mass, "spin_reserve": def.spin_reserve,
		"balance": def.balance, "level": level, "mesh": def.mesh}, accent)
	g.set_physics_process(false)
	g.position = pos
	g.battling = true
	g.spin = 40.0 # ~16 rad/s: fast, and slow enough per frame that the carving never wagon-wheels
	g.wobble = 0.05
	if g._slot_label != null:
		g._slot_label.layers = 0 # its visibility is re-set every frame; a cleared layer mask hides it for good
	tops.append(g)
	return g


func _clear_tops() -> void:
	for g: Gasing in tops:
		if is_instance_valid(g):
			g.queue_free()
	tops.clear()
	ffa.clear()
	hero = null
	rival = null
	title_top = null


func _orbit(target: Vector3, r: float, az_deg: float, el_deg: float, fov: float) -> void:
	var az: float = deg_to_rad(az_deg)
	var el: float = deg_to_rad(minf(el_deg, 89.0))
	cam.position = target + Vector3(r * cos(el) * sin(az), r * sin(el), r * cos(el) * cos(az))
	cam.fov = fov
	cam.look_at(target, Vector3.UP)


func _dof(far_dist: float, amount: float = 0.1, transition: float = 2.0) -> void:
	cam_attr.dof_blur_far_enabled = far_dist > 0.0
	cam_attr.dof_blur_far_distance = maxf(far_dist, 0.01)
	cam_attr.dof_blur_far_transition = transition
	cam_attr.dof_blur_amount = amount
	cam_attr.dof_blur_near_enabled = false


func _scr(p: Vector3) -> Vector2:
	return cam.unproject_position(p)


func _once(key: String, at: float) -> bool:
	# fire a world event exactly once when the clock passes `at`
	if t >= at and not _hit_done.has(key):
		_hit_done[key] = true
		return true
	return false


func _master(id: String) -> Dictionary:
	for m: Dictionary in SD.MASTERS:
		if m.id == id:
			return m
	return {}


# ================================================================ 2D layers, post

func _build_2d() -> void:
	bg = _layer(1)
	bg.draw.connect(_draw_bg)
	mg = _layer(2)
	mg.draw.connect(_draw_mg)
	var post_layer: CanvasLayer = CanvasLayer.new()
	post_layer.layer = 3
	add_child(post_layer)
	var rect: ColorRect = ColorRect.new()
	rect.size = Vector2(W, H)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	post = ShaderMaterial.new()
	post.shader = Shader.new()
	post.shader.code = POST_SHADER
	rect.material = post
	post_layer.add_child(rect)
	bars = _layer(4)
	bars.draw.connect(_draw_bars)
	# the real in-game wind gauge, scaled up
	meter = MAIN.WindMeter.new()
	var th: Theme = Theme.new()
	th.default_font = FONT_BODY
	meter.theme = th
	mg.add_child(meter)
	meter.size = Vector2(64.0, 270.0)
	meter.scale = Vector2(2.3, 2.3)
	meter.visible = false
	emblem = TextureRect.new()
	emblem.texture = TEX_GUNUNGAN_GOLD
	emblem.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	emblem.size = Vector2(520.0, 520.0)
	emblem.pivot_offset = emblem.size * 0.5
	emblem.self_modulate = GOLD
	shine = ShaderMaterial.new()
	shine.shader = Shader.new()
	shine.shader.code = SHINE_SHADER
	emblem.material = shine
	emblem.visible = false
	mg.add_child(emblem)
	# the kelir: main.gd:_kelir_texture, pale gold at the flame -> amber -> carved-wood dark
	var grad: Gradient = Gradient.new()
	grad.set_color(0, GOLD.lerp(CREAM, 0.5))
	grad.set_color(1, HT.WOOD_EDGE)
	grad.add_point(0.45, HT.WOOD_AMBER)
	kelir_tex = GradientTexture2D.new()
	kelir_tex.gradient = grad
	kelir_tex.fill = GradientTexture2D.FILL_RADIAL
	kelir_tex.fill_from = Vector2(0.5, 0.42)
	kelir_tex.fill_to = Vector2(0.5, 1.1)
	kelir_tex.width = 512
	kelir_tex.height = 512
	var mask: Gradient = Gradient.new() # clear centre, soft edge, black beyond
	mask.set_color(0, Color(0.0, 0.0, 0.0, 0.0))
	mask.set_color(1, Color(0.0, 0.0, 0.0, 1.0))
	mask.set_offset(1, 0.5)
	mask.add_point(0.3, Color(0.0, 0.0, 0.0, 0.0))
	lamp_mask = GradientTexture2D.new()
	lamp_mask.gradient = mask
	lamp_mask.fill = GradientTexture2D.FILL_RADIAL
	lamp_mask.fill_from = Vector2(0.5, 0.5)
	lamp_mask.fill_to = Vector2(1.0, 0.5)
	lamp_mask.width = 512
	lamp_mask.height = 512
	_build_map()
	_build_emblem_dots()


func _layer(n: int) -> Control:
	var cl: CanvasLayer = CanvasLayer.new()
	cl.layer = n
	add_child(cl)
	var c: Control = Control.new()
	c.size = Vector2(W, H)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cl.add_child(c)
	return c


func T(path: String) -> Texture2D:
	if not tex.has(path):
		tex[path] = load(path) as Texture2D
	return tex[path]


func _figure_x(path: String) -> float:
	# puppet sheets sit their figure anywhere across the 1024 canvas (a kite, a staff, a lamp held
	# out): centre on the opaque bounds instead
	if not _fig_x.has(path):
		var img: Image = T(path).get_image()
		if img.is_compressed():
			img.decompress()
		var r: Rect2i = img.get_used_rect()
		_fig_x[path] = (float(r.position.x) + float(r.size.x) * 0.5) / float(img.get_width())
	return _fig_x[path]


func _shake_amount(x: float) -> float:
	var s: float = 0.0
	for im: Array in _impacts:
		s += float(im[1]) * pulse(x, float(im[0]), 7.0)
	if x > B(8, 3) and x < B(9): # the riser shudders into the drop
		s += 0.35 * ei_cubic(seg(x, B(8, 3), B(9)))
	return clampf(s, 0.0, 1.2)


func _update_post() -> void:
	var s: float = _shake_amount(t)
	var n: Vector2 = Vector2(sin(t * 71.0) + sin(t * 43.0 + 1.3), cos(t * 67.0) + sin(t * 37.0 + 2.1)) * 0.5
	post.set_shader_parameter("shake", n * s * s * 0.012)
	var f: float = 0.0
	var fc: Color = Color(1.0, 0.92, 0.75)
	for fl: Array in _flashes:
		var v: float = float(fl[1]) * pulse(t, float(fl[0]), float(fl[2]))
		if v > f:
			f = v
			fc = fl[3]
	f = maxf(f, _lightning(t))
	post.set_shader_parameter("flash", f)
	post.set_shader_parameter("flash_col", Vector3(fc.r, fc.g, fc.b))
	var bullet: float = 1.0 if t >= C("pangkah") and t < C("snap_back") else 0.0
	post.set_shader_parameter("ca", 0.006 * s + 0.003 * bullet)
	var zb: float = 0.16 * ei_cubic(seg(t, B(8, 2), B(9))) * (1.0 if t < B(9) else 0.0)
	zb = maxf(zb, 0.07 * pulse(t, C("pangkah"), 7.0))
	zb = maxf(zb, 0.07 * pulse(t, C("drop"), 9.0))
	post.set_shader_parameter("zoom_blur", zb)
	post.set_shader_parameter("zoom_center", Vector2(0.5, 0.5))
	post.set_shader_parameter("frame", float(_frame % 997))
	post.set_shader_parameter("fade", seg(t, 59.8, 60.0))


func _lightning(x: float) -> float:
	var v: float = 0.0
	for c: String in ["thunder_1", "thunder_2"]:
		var t0: float = C(c) + (0.12 if c == "thunder_1" else 0.0) # the first strike lands as the wipe clears
		for k: Array in [[0.0, 0.7], [0.09, 0.45], [0.2, 0.6]]:
			v = maxf(v, float(k[1]) * pulse(x, t0 + float(k[0]), 22.0))
	return v


func _draw_bg() -> void:
	var name_: String = _shots[_shot][0]
	if has_method("_bg_" + name_):
		call("_bg_" + name_, bg, t - float(_shots[_shot][1]))


func _draw_mg() -> void:
	var name_: String = _shots[_shot][0]
	if has_method("_mg_" + name_):
		call("_mg_" + name_, mg, t - float(_shots[_shot][1]))
	_wipe_gunungan(mg, C("storm_wipe"), 1.0)
	_wipe_gunungan(mg, C("shore_wipe"), -1.0)
	_wipe_songket(mg, B(15), 1.0)
	_wipe_songket(mg, B(17), -1.0)


func _draw_bars() -> void:
	# 2.39:1 letterbox for the shadow play; it slams open on the drop
	var k: float = 1.0 - eio_cubic(seg(t, B(9), B(9) + 0.32))
	if k > 0.0:
		bars.draw_rect(Rect2(0.0, 0.0, W, BAR_H * k), Color.BLACK)
		bars.draw_rect(Rect2(0.0, H - BAR_H * k, W, BAR_H * k), Color.BLACK)
	var cap: float = seg(t, 1.1, 1.7) * (1.0 - seg(t, 3.2, 3.6))
	if cap > 0.0:
		_tracked(bars, FONT_BODY, "A  WAYANG  KULIT  TALE", Vector2(W * 0.5, H - 58.0), 24, Color(DIM, 0.85 * cap), 6.0, 0, true)


# ================================================================ text + drawing helpers

func _tw(font: Font, text: String, size: int, tracking: float = 0.0) -> float:
	var w: float = 0.0
	for i: int in text.length():
		w += font.get_char_size(text.unicode_at(i), size).x + tracking
	return w - tracking


func _tracked(ci: CanvasItem, font: Font, text: String, pos: Vector2, size: int, col: Color, tracking: float,
		outline: int = 0, centered: bool = false) -> void:
	var x: float = pos.x - (_tw(font, text, size, tracking) * 0.5 if centered else 0.0)
	for i: int in text.length():
		var ch: String = text[i]
		if outline > 0:
			ci.draw_char_outline(font, Vector2(x, pos.y), ch, size, outline, Color(OUTLINE, col.a))
		ci.draw_char(font, Vector2(x, pos.y), ch, size, col)
		x += font.get_char_size(text.unicode_at(i), size).x + tracking


func _stagger(ci: CanvasItem, font: Font, text: String, pos: Vector2, size: int, col: Color, t0: float,
		step: float, dur: float, dy: float, tracking: float = 0.0, outline: int = 0, hi: Vector2i = Vector2i(-1, -1),
		hi_col: Color = GOLD, centered: bool = false, fade_out: float = 999.0) -> void:
	# letters rise into place one after another (expo out); hi = [from, to) index range in hi_col
	var x: float = pos.x - (_tw(font, text, size, tracking) * 0.5 if centered else 0.0)
	var out: float = 1.0 - seg(t, fade_out - 0.18, fade_out)
	for i: int in text.length():
		var ch: String = text[i]
		var p: float = seg(t, t0 + i * step, t0 + i * step + dur)
		var a: float = clampf(p * 3.0, 0.0, 1.0) * out
		if a <= 0.0:
			x += font.get_char_size(text.unicode_at(i), size).x + tracking
			continue
		var c: Color = hi_col if i >= hi.x and i < hi.y else col
		var at: Vector2 = Vector2(x, pos.y + dy * (1.0 - eo_expo(p)) - 30.0 * (1.0 - out))
		if outline > 0:
			ci.draw_char_outline(font, at, ch, size, outline, Color(OUTLINE, a * col.a))
		ci.draw_char(font, at, ch, size, Color(c, c.a * a))
		x += font.get_char_size(text.unicode_at(i), size).x + tracking


func _stamp(ci: CanvasItem, text: String, center: Vector2, size: int, col: Color, t_in: float, t_out: float,
		outline: int = 10, font: Font = FONT_TITLE) -> void:
	# a word slammed onto the frame: scale 1.45 -> 1 (expo) with fading motion ghosts, then a quick exit
	if t < t_in or t > t_out:
		return
	var p: float = seg(t, t_in, t_in + 0.24)
	var q: float = seg(t, t_out - 0.14, t_out)
	var s: float = lerpf(1.45, 1.0, eo_expo(p)) * lerpf(1.0, 0.9, q)
	var a: float = eo_cubic(seg(t, t_in, t_in + 0.07)) * (1.0 - q)
	var w: float = font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var base: Vector2 = Vector2(-w * 0.5, (font.get_ascent(size) - font.get_descent(size)) * 0.5)
	for g: int in [2, 1]:
		var gs: float = s * (1.0 + 0.09 * g * (1.0 - p))
		var ga: float = a * 0.22 * (1.0 - p)
		if ga > 0.0:
			ci.draw_set_transform(center, 0.0, Vector2(gs, gs))
			ci.draw_string(font, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(col, ga))
	ci.draw_set_transform(center, 0.0, Vector2(s, s))
	ci.draw_string(font, base + Vector2(4.0, 6.0), text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(0.0, 0.0, 0.0, 0.5 * a))
	if outline > 0:
		ci.draw_string_outline(font, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, outline, Color(OUTLINE, a))
	ci.draw_string(font, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(col, col.a * a))
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


func _toast(ci: CanvasItem, text: String, at: Vector2, col: Color, t0: float, size: int = 72) -> void:
	# the game's combat toast (main.gd:_toast): pop 0.6 -> 1 with a back ease, rise 70 px, fade
	var age: float = t - t0
	if age < 0.0 or age > 1.0:
		return
	var s: float = lerpf(0.6, 1.0, eo_back(seg(age, 0.0, 0.18)))
	var a: float = 1.0 - seg(age, 0.45, 1.0)
	var w: float = FONT_TITLE.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	ci.draw_set_transform(at - Vector2(0.0, 70.0 * eo_cubic(age)), 0.0, Vector2(s, s))
	var base: Vector2 = Vector2(-w * 0.5, size * 0.35)
	ci.draw_string(FONT_TITLE, base + Vector2(3.0, 4.0), text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(0.0, 0.0, 0.0, 0.6 * a))
	ci.draw_string_outline(FONT_TITLE, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, 9, Color(OUTLINE, a))
	ci.draw_string(FONT_TITLE, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(col, a))
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


func _diamond(ci: CanvasItem, c: Vector2, r: float, col: Color, filled: bool = true) -> void:
	var pts: PackedVector2Array = PackedVector2Array([c + Vector2(0.0, -r), c + Vector2(r * 0.8, 0.0),
		c + Vector2(0.0, r), c + Vector2(-r * 0.8, 0.0)])
	if filled:
		ci.draw_colored_polygon(pts, col)
	else:
		pts.append(pts[0])
		ci.draw_polyline(pts, col, 2.0, true)


func _songket_bar(ci: CanvasItem, rect: Rect2, col: Color = GOLD) -> void:
	# the game's songket band, tiled along a strip
	if rect.size.x <= 0.0:
		return
	ci.draw_texture_rect(TEX_SONGKET, rect, true, col)


func _kelir(ci: CanvasItem, rect: Rect2, bright: float = 1.0) -> void:
	ci.draw_texture_rect(kelir_tex, rect, false, Color(bright, bright, bright))
	# the cloth's weave, barely there
	var step: float = 7.0
	var y: float = rect.position.y
	while y < rect.end.y:
		ci.draw_line(Vector2(rect.position.x, y), Vector2(rect.end.x, y), Color(0.0, 0.0, 0.0, 0.025), 1.0)
		y += step


func _cut(ci: CanvasItem, path: String, pivot: Vector2, pivot_uv: Vector2, height: float, rot: float = 0.0,
		col: Color = INK, flip: float = 1.0, xf: Transform2D = Transform2D.IDENTITY, soft: float = 0.3) -> void:
	# a wayang cut-out: black silhouette PNG drawn as ink against the lamp, with a soft penumbra
	var tx: Texture2D = T(path)
	var sz: Vector2 = tx.get_size() * (height / tx.get_size().y)
	ci.draw_set_transform_matrix(xf * Transform2D(rot, Vector2(flip, 1.0), 0.0, pivot))
	var r: Rect2 = Rect2(-pivot_uv * sz, sz)
	if soft > 0.0:
		ci.draw_texture_rect(tx, r.grow(sz.y * 0.01), false, Color(col, col.a * soft))
	ci.draw_texture_rect(tx, r, false, col)
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


func _stage(ci: CanvasItem, path: String, scale_: float = 1.0, rot: float = 0.0, offset: Vector2 = Vector2.ZERO,
		col: Color = INK, xf: Transform2D = Transform2D.IDENTITY) -> void:
	# a full-width 2048x820 kelir scene, pivoting on its bottom centre
	_cut(ci, path, Vector2(W * 0.5, H * 0.5 + STAGE_H * 0.5) + offset, Vector2(0.5, 1.0), STAGE_H * scale_, rot, col, 1.0, xf, 0.0)


func _ring_mask(ci: CanvasItem, center: Vector2, radius: float, col: Color = INK) -> void:
	# everything outside a circle (iris)
	var thick: float = 2600.0
	ci.draw_arc(center, radius + thick * 0.5, 0.0, TAU, 128, col, thick)


func _speed_lines(ci: CanvasItem, center: Vector2, amount: float, col: Color, seed_: int = 0, inner: float = 160.0) -> void:
	if amount <= 0.0:
		return
	for i: int in 64:
		var h: float = fposmod(sin(float(i * 7 + seed_) * 12.9898) * 43758.5453, 1.0)
		var ang: float = TAU * float(i) / 64.0 + h * 0.08
		var r0: float = inner + h * 260.0 + fposmod(t * 1900.0 + h * 900.0, 700.0) * (1.0 - amount * 0.3)
		var r1: float = r0 + 160.0 + h * 420.0 * amount
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		ci.draw_line(center + d * r0, center + d * r1, Color(col, col.a * amount * (0.35 + h * 0.65)), 2.0 + h * 5.0 * amount)


func _wipe_gunungan(ci: CanvasItem, tc: float, dir: float) -> void:
	# the wayang scene change: the gunungan swings past close to the lamp, its shadow swelling
	# over the whole kelir at the cut, then sweeping on
	var p: float = seg(t, tc - 0.42, tc + 0.42)
	if p <= 0.0 or p >= 1.0:
		return
	var bell: float = pow(sin(PI * p), 1.3)
	var s: float = lerpf(0.9, 7.6, bell)
	var x: float = W * 0.5 + dir * W * 0.85 * (1.0 - 2.0 * eio_cubic(p))
	_cut(ci, "res://assets/wayang/wayang_gunungan.png", Vector2(x, H * 0.5), Vector2(0.5, 0.46), 857.0 * s,
		dir * deg_to_rad(10.0) * (1.0 - 2.0 * p), INK, 1.0, Transform2D.IDENTITY, 0.45)


func _wipe_songket(ci: CanvasItem, tc: float, dir: float) -> void:
	# a carved-wood slab with songket edges slides across, covering the frame at the cut
	var p: float = seg(t, tc - 0.3, tc + 0.3)
	if p <= 0.0 or p >= 1.0:
		return
	var skew: float = 360.0
	var slab: float = W + skew + 100.0 # wide enough to cover the whole frame at the cut
	var lead: float = lerpf(0.0, 2.0 * W + 2.0 * skew + 100.0, eio_cubic(p)) # leading edge (top), travelling in +x
	var xs: Array[float] = [lead, lead - skew, lead - slab - skew, lead - slab] # top-lead, bottom-lead, bottom-trail, top-trail
	var ys: Array[float] = [0.0, H, H, 0.0]
	var pts: PackedVector2Array = PackedVector2Array()
	for i: int in 4:
		pts.append(Vector2(W - xs[i] if dir > 0.0 else xs[i], ys[i]))
	ci.draw_colored_polygon(pts, HT.WOOD_EDGE)
	for e: Array in [[pts[0], pts[1]], [pts[3], pts[2]]]:
		var a: Vector2 = e[0]
		var b: Vector2 = e[1]
		ci.draw_set_transform(a, (b - a).angle(), Vector2.ONE)
		_songket_bar(ci, Rect2(0.0, -22.0, (b - a).length(), 44.0))
		ci.draw_set_transform_matrix(Transform2D.IDENTITY)


# ================================================================ ACT I — the shadow screen

func _lamp(x: float) -> float:
	# the dalang's oil lamp breathing
	return 0.93 + 0.05 * sin(x * 23.0) * sin(x * 7.3 + 1.0) + 0.03 * sin(x * 3.1)


func _bg_lamp(ci: CanvasItem, lt: float) -> void:
	# the lamp is lit behind the cloth: its light blooms out from the hot spot in a soft circle
	var b: float = _lamp(lt) * clampf(seg(lt, 0.05, 0.6) * 1.2, 0.0, 1.0)
	_kelir(ci, Rect2(0.0, 0.0, W, H), b)
	var hot: Vector2 = Vector2(W * 0.5, H * 0.56)
	var s: float = lerpf(60.0, 3400.0, eo_expo(seg(lt, 0.2, 2.6)))
	var r: Rect2 = Rect2(hot - Vector2(s, s) * 0.5, Vector2(s, s))
	ci.draw_texture_rect(lamp_mask, r, false)
	for edge: Rect2 in [Rect2(0.0, 0.0, W, maxf(r.position.y, 0.0)), Rect2(0.0, r.end.y, W, maxf(H - r.end.y, 0.0)),
			Rect2(0.0, 0.0, maxf(r.position.x, 0.0), H), Rect2(r.end.x, 0.0, maxf(W - r.end.x, 0.0), H)]:
		ci.draw_rect(edge, Color.BLACK)
	# the gunungan rises on its rod, sways, and turns
	var rise: float = eo_cubic(seg(lt, 0.7, 2.2))
	var turn: float = cos(TAU * eio_cubic(seg(t, C("gunungan_turn") - 0.1, C("gunungan_turn") + 0.5)))
	var sway: float = deg_to_rad(3.0) * sin(lt * 2.1) + deg_to_rad(6.0) * (1.0 - rise)
	_cut(ci, "res://assets/wayang/wayang_gunungan.png", Vector2(W * 0.5, 945.0 + 700.0 * (1.0 - rise)),
		Vector2(0.5, 0.894), 857.0, sway, Color(INK, rise), turn)


func _bg_storm(ci: CanvasItem, lt: float) -> void:
	var flash: float = _lightning(t)
	_kelir(ci, Rect2(0.0, 0.0, W, H), 0.62 + 0.4 * flash)
	var rock: float = deg_to_rad(2.4) * sin(lt * 1.9) + deg_to_rad(1.0) * sin(lt * 3.7)
	var bob: Vector2 = Vector2(0.0, 8.0 * sin(lt * 1.9 + 0.6))
	_stage(ci, "res://assets/wayang/wayang_prologue.png", 1.05 + 0.04 * lt / 3.75, rock, bob)
	# rain
	for i: int in 150:
		var h1: float = fposmod(float(i) * 0.6180339, 1.0)
		var h2: float = fposmod(float(i) * 0.4142135, 1.0)
		var y: float = fposmod(h2 + lt * (1.1 + h1 * 0.5), 1.0) * (H + 300.0) - 150.0
		var x: float = h1 * (W + 600.0) - 300.0 - y * 0.32
		ci.draw_line(Vector2(x, y), Vector2(x - 26.0, y + 80.0), Color(INK, 0.3 + 0.25 * h2), 2.0 + h1 * 2.0)
	# the bolt, while the sky flashes
	if flash > 0.15:
		var pts: PackedVector2Array = PackedVector2Array()
		var p: Vector2 = Vector2(1380.0, 120.0)
		var r: int = int(t * 3.0)
		for s: int in 7:
			pts.append(p)
			p += Vector2(fposmod(sin(float(s * 13 + r) * 91.7) * 4375.0, 1.0) * 120.0 - 70.0, 70.0)
		ci.draw_polyline(pts, Color(1.0, 0.97, 0.85, flash * 0.35), 16.0, true)
		ci.draw_polyline(pts, Color(1.0, 1.0, 0.95, flash), 4.0, true)


func _mg_storm(ci: CanvasItem, _lt: float) -> void:
	_stamp(ci, "A STORM.", Vector2(W * 0.5, 330.0), 120, GOLD, C("thunder_1") + 0.3, C("shipwreck") - 0.02)
	_stamp(ci, "A SHIPWRECK.", Vector2(W * 0.5, 330.0), 120, GOLD, C("shipwreck"), C("shore_wipe") - 0.25)


func _bg_shore(ci: CanvasItem, lt: float) -> void:
	_kelir(ci, Rect2(0.0, 0.0, W, H), _lamp(t))
	_stage(ci, "res://assets/wayang/wayang_prologue_shore.png", 1.03, 0.0, Vector2(30.0 - 40.0 * lt / 3.75, 0.0))
	# the sailor walks in from the right, a step on every beat, and stops to look
	var walk: float = seg(lt, 0.3, 2.6)
	var x: float = lerpf(2000.0, 1580.0, eio_cubic(walk))
	var stepping: float = 1.0 - seg(lt, 2.3, 2.7)
	var ph: float = PI * (t / spb)
	var bob: float = -absf(sin(ph)) * 12.0 * stepping
	var rot: float = deg_to_rad(2.5) * sin(ph) * stepping + deg_to_rad(1.2) * sin(lt * 2.0) * (1.0 - stepping)
	_cut(ci, "res://assets/wayang/wayang_sailor.png", Vector2(x, GROUND_Y + bob), Vector2(0.5, 0.878), 640.0, rot, INK, -1.0)


func _mg_shore(ci: CanvasItem, _lt: float) -> void:
	# in the open sky between the moon and the sailor's raised arm
	_stagger(ci, FONT_TITLE, "A STRANGER", Vector2(1050.0, 262.0), 118, CREAM, C("stranger"), 0.035, 0.45, 50.0, 4.0, 10,
		Vector2i(-1, -1), GOLD, true, B(7) - 0.05)
	_stagger(ci, FONT_BODY, "ON THE PERLIS SHORE.", Vector2(1050.0, 334.0), 40, CREAM, B(6), 0.025, 0.4, 24.0, 7.0, 6,
		Vector2i(7, 13), GOLD, true, B(7) - 0.05)


func _bg_sight(ci: CanvasItem, lt: float) -> void:
	# the whole kelir pushes into the top from "A GASING." until its ink fills the frame
	var z: float = exp(log(16.0) * ei_cubic(seg(t, C("gasing") + 0.25, B(9))))
	var focus: Vector2 = Vector2(W * 0.5, GROUND_Y - 150.0)
	var xf: Transform2D = Transform2D(0.0, Vector2(z, z), 0.0, focus) * Transform2D(0.0, -focus)
	_kelir(ci, Rect2(0.0, 0.0, W, H), _lamp(t) + 0.15 * seg(t, B(8), B(9)))
	var people_a: float = 1.0 - 0.6 * seg(t, C("game"), C("game") + 0.3)
	_stage(ci, "res://assets/wayang/wayang_perlis_people.png", 1.0, 0.0, Vector2.ZERO, Color(INK, people_a), xf)
	var pop: float = eo_back(seg(t, C("game"), C("game") + 0.3))
	if pop > 0.0:
		var wob: float = deg_to_rad(4.0) * sin(lt * 9.0)
		_cut(ci, "res://assets/wayang/wayang_top_perlis.png", Vector2(W * 0.5, GROUND_Y), Vector2(0.5, 0.988),
			470.0 * pop, wob, INK, 1.0, xf, 0.3)
		# spin arcs whirling round the body
		var c: Vector2 = xf * Vector2(W * 0.5, GROUND_Y - 120.0)
		for i: int in 3:
			var a0: float = lt * 13.0 + float(i) * TAU / 3.0
			ci.draw_set_transform(c, 0.0, Vector2(z, z * 0.2))
			ci.draw_arc(Vector2.ZERO, 290.0 * pop, a0, a0 + 1.2, 24, Color(INK, 0.55 * pop), 7.0, true)
			ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	if t > B(9) - 0.08: # fully inside the ink
		ci.draw_rect(Rect2(0.0, 0.0, W, H), INK)


func _mg_sight(ci: CanvasItem, _lt: float) -> void:
	_stamp(ci, "A VILLAGE.", Vector2(W * 0.5, 300.0), 116, GOLD, C("village"), C("game") - 0.02)
	_stamp(ci, "A GAME.", Vector2(W * 0.5, 300.0), 116, GOLD, C("game"), C("gasing") - 0.02)
	_stamp(ci, "A GASING.", Vector2(W * 0.5, 300.0), 130, GOLD, C("gasing"), B(8, 4))
	_speed_lines(ci, Vector2(W * 0.5, H * 0.5), ei_cubic(seg(t, B(8, 2), B(9))), Color(CREAM, 0.8), 3, 220.0)


# ================================================================ ACT II — the ring

const P0: Vector3 = Vector3(-1.2, 0.0, 0.9) # the hero's launch spot
const R0: Vector3 = Vector3(1.2, 0.0, -0.9) # the rival's


func _enter_ring() -> void:
	_set_arena("kampung")
	hero = _spawn_top("jantung", GOLD, Vector3.ZERO, 5)
	hero.battling = false
	hero.set_showcase(true)
	hero_word.visible = true


func _upd_ring(lt: float) -> void:
	var w: float = _world_t(t)
	var t_wind: float = C("wind")
	var t_rel: float = B(11, 4.5) # cord released
	var t_land: float = C("launch_land")
	if t < t_wind: # ---- hero reveal: top-down iris, swoop to a low hero angle, slow orbit
		hero.position = Vector3.ZERO
		var sw: float = eio_cubic(seg(lt, 0.12, 1.6))
		var el: float = lerpf(89.0, 10.0, sw) + 3.0 * seg(lt, 1.6, 3.75)
		var az: float = lerpf(0.0, 35.0, sw) + 25.0 * seg(lt, 1.6, 3.75)
		var r: float = lerpf(1.75, 2.3, sw)
		_orbit(Vector3(0.0, lerpf(0.45, 0.5, sw), 0.0), r, az, el, lerpf(42.0, 34.0, seg(lt, 0.0, 3.75)))
		_dof(r + 0.5, 0.16 * sw, 2.0)
		# the word stands right behind the top, whichever way the camera has swung
		hero_word.position = Vector3(-sin(deg_to_rad(az)), 0.0, -cos(deg_to_rad(az))) * 3.4 + Vector3(0.0, 1.05, 0.0)
		hero_word.modulate.a = 0.95 * sw
		return
	hero_word.visible = false
	if rival == null:
		rival = _spawn_top("perlis", (_master("perlis").color as Color), R0 + Vector3(0.0, 1.15, 0.0))
		rival.visible = false
		hero.set_showcase(true)
	if t < t_land: # ---- wind: the top hangs above its spot, spinning up; then the cord lets go
		var drop: float = ei_quad(seg(t, t_rel, t_land))
		hero.position = P0 + Vector3(0.0, lerpf(1.15, 0.0, drop), 0.0)
		var target: Vector3 = hero.position + Vector3(0.0, 0.45, 0.0)
		var az2: float = lerpf(58.0, 70.0, seg(t, t_wind, t_land))
		var r2: float = lerpf(3.1, 2.5, eio_cubic(seg(t, t_wind, t_rel)))
		_orbit(Vector3(target.x, P0.y + 1.55, target.z), r2, az2, 6.0, 36.0)
		cam.h_offset = -0.62 # the gauge panel owns the left of frame
		_dof(r2 + 0.6, 0.1, 2.0)
		meter.visible = true
		var m: Control = meter
		m.set("power", 88.0 * eio_cubic(seg(t, t_wind + 0.1, C("perfect"))))
		m.position = Vector2(lerpf(-300.0, 250.0, eo_expo(seg(t, t_wind, t_wind + 0.35))) - 900.0 * ei_expo(seg(t, t_rel, t_land)), 175.0)
		return
	meter.visible = false
	cam.h_offset = 0.0
	if _once("land", t_land):
		hero.battling = true
		hero.set_showcase(false)
		hero._spawn_dust()
		_shock(P0, t_land, 2.6)
		_burst(P0 + Vector3(0.0, 0.05, 0.0), Color(1.0, 0.9, 0.6), 0.7)
	var t_rl: float = C("rival_land")
	if is_instance_valid(rival):
		rival.visible = t > t_rl - 0.25
	if t < C("strike"): # ---- launch: wide 3/4 view, the rival drops in, the camera whips round
		hero.position = P0
		rival.position = R0 + Vector3(0.0, lerpf(1.6, 0.0, ei_quad(seg(t, t_rl - 0.25, t_rl))), 0.0)
		if _once("rland", t_rl):
			rival.battling = true
			rival._spawn_dust()
			_shock(R0, t_rl, 2.2)
		var whip: float = eio_cubic(seg(t, B(12, 3.5), B(13)))
		var r3: float = lerpf(5.0, 4.4, seg(t, t_land, C("strike")))
		_orbit(Vector3(0.0, 0.2, 0.0), r3, lerpf(28.0, 40.0, seg(t, t_land, B(12, 3.5))) + 110.0 * whip, lerpf(40.0, 26.0, whip),
			46.0 - 6.0 * pulse(t, t_land, 7.0))
		_dof(0.0)
		return
	# ---- strike: spiral in, PANGKAH! in bullet time, snap back, the rival rings out
	var p: float = C("pangkah")
	var wp: float = _world_t(p)
	var a0: float = atan2(P0.z, P0.x)
	if w < wp:
		var k: float = seg(w, C("strike") - 0.05, wp)
		var r: float = lerpf(P0.length(), 0.5, ei_cubic(k))
		var a: float = a0 + 2.6 * k + 1.6 * k * k
		hero.position = Vector3(cos(a), 0.0, sin(a)) * r
		rival.position = -hero.position
		hero.wobble = 0.05
	else:
		var contact_dir: Vector3 = Vector3(cos(a0 + 4.2), 0.0, sin(a0 + 4.2))
		var after: float = w - wp
		hero.position = contact_dir * (0.5 + 0.55 * eo_cubic(seg(after, 0.0, 0.7)))
		if is_instance_valid(rival) and rival.alive:
			rival.position = -contact_dir * (0.5 + 3.4 * eo_cubic(seg(after, 0.0, 1.0)))
		hero.wobble = 0.05 + 0.25 * pulse(after, 0.0, 3.0)
	if _once("pangkah", p):
		var c: Vector3 = Vector3.ZERO + Vector3(0.0, 0.45, 0.0)
		_burst(c, Color.WHITE, 1.6)
		_burst(c, Color(1.0, 0.6, 0.25), 1.2)
		_burst(c + Vector3(0.0, 0.2, 0.0), Color(1.0, 1.0, 0.8), 1.0)
		_shock(Vector3.ZERO, p, 3.0)
	if _once("snap", C("snap_back")): # the accents flare as real time snaps back (a flare held through
		hero.flash_accent() # bullet time would bleach the frozen frame)
		if is_instance_valid(rival):
			rival.flash_accent()
	if _once("ringout", C("ringout")) and is_instance_valid(rival):
		rival.velocity = -Vector3(cos(a0 + 4.2), 0.0, sin(a0 + 4.2)) * 3.0
		rival.die("ringout")
	if t < p: # tracking low as they close
		var k2: float = seg(t, C("strike"), p)
		_orbit(Vector3(0.0, 0.35, 0.0), lerpf(4.0, 2.9, k2), lerpf(150.0, 185.0, k2), lerpf(22.0, 13.0, k2), 42.0)
		_dof(0.0)
	elif t < C("snap_back"): # bullet time: the camera keeps its real-time speed round the frozen clash
		var k3: float = eio_cubic(seg(t, p, C("snap_back")))
		_orbit(Vector3(0.0, 0.45, 0.0), lerpf(2.2, 1.8, k3), lerpf(185.0, 300.0, k3), lerpf(10.0, 7.0, k3), 36.0)
		_dof(2.6, 0.14, 1.5)
	else: # wide: watch the rival fly
		var k4: float = seg(t, C("snap_back"), B(15))
		_orbit(Vector3(0.0, 0.0, 0.0), lerpf(8.6, 9.2, k4), lerpf(205.0, 222.0, k4), 48.0, 46.0 - 5.0 * pulse(t, C("snap_back"), 8.0))
		_dof(0.0)


func _mg_ring(ci: CanvasItem, lt: float) -> void:
	# iris out of the ink: the circle of the top seen from above
	var iris: float = eo_expo(seg(lt, 0.0, 0.5))
	if iris < 1.0:
		_ring_mask(ci, Vector2(W * 0.5, H * 0.5), lerpf(0.0, 1300.0, iris))
	if t < C("wind"):
		_callout(ci, C("callout_1"), Vector3(0.0, 0.62, 0.0), 0.36, -1.0, Vector2(150.0, 330.0), "KAYU MERBAU", "MASS", 0.8, "2.4")
		_callout(ci, C("callout_2"), Vector3(0.0, 0.3, 0.0), 0.3, 1.0, Vector2(1400.0, 520.0), "TERAS BESI", "SPIN", 0.74, "74")
		_callout(ci, C("callout_3"), Vector3(0.0, 0.06, 0.0), 0.05, -1.0, Vector2(150.0, 760.0), "KAYU KEMUNING", "BALANCE", 0.61, "61")
	# the gauge's dark-wood panel, the split edge in songket
	var pin: float = eo_expo(seg(t, C("wind"), C("wind") + 0.35)) * (1.0 - ei_expo(seg(t, B(11, 4.5), C("launch_land"))))
	if pin > 0.0 and t < C("launch_land"):
		var ox: float = -820.0 * (1.0 - pin)
		var pts: PackedVector2Array = PackedVector2Array([Vector2(ox, 0.0), Vector2(ox + 760.0, 0.0), Vector2(ox + 600.0, H), Vector2(ox, H)])
		ci.draw_colored_polygon(pts, Color(HT.WOOD_EDGE, 0.94))
		ci.draw_set_transform(Vector2(ox + 760.0, 0.0), (Vector2(-160.0, H)).angle(), Vector2.ONE)
		_songket_bar(ci, Rect2(0.0, -16.0, Vector2(-160.0, H).length(), 32.0))
		ci.draw_set_transform_matrix(Transform2D.IDENTITY)
		_stamp(ci, "WIND.", Vector2(ox + 330.0, 980.0), 120, GOLD, C("wind"), C("launch_land"))
		# charge rings pulsing round the hanging top on the 16ths
		var c: Vector2 = _scr(hero.position + Vector3(0.0, 0.5, 0.0))
		var pw: float = seg(t, C("wind") + 0.1, C("perfect"))
		for i: int in 3:
			var ph: float = fposmod((t - C("wind")) / (spb * 0.25) + float(i) / 3.0, 1.0)
			var col: Color = GOLD if pw > 0.9 else CREAM
			ci.draw_set_transform(c, 0.0, Vector2(1.0, 0.32))
			ci.draw_arc(Vector2.ZERO, 120.0 + 260.0 * ph, 0.0, TAU, 64, Color(col, (1.0 - ph) * 0.55 * pin * (0.4 + pw)), 4.0, true)
			ci.draw_set_transform_matrix(Transform2D.IDENTITY)
		_toast(ci, "PERFECT!", Vector2(ox + 560.0, 330.0), GOLD, C("perfect"), 76)
	_stamp(ci, "LAUNCH.", Vector2(330.0, 980.0), 120, GOLD, C("launch_land"), C("strike") - 0.02)
	if t > B(12, 3.5) and t < B(13) + 0.05: # whip-pan streaks
		var k: float = sin(PI * seg(t, B(12, 3.5), B(13) + 0.05))
		for i: int in 40:
			var h: float = fposmod(float(i) * 0.618034, 1.0)
			var y: float = h * H
			var x: float = fposmod(h * 7000.0 + t * 9000.0, W + 800.0) - 400.0
			ci.draw_line(Vector2(x, y), Vector2(x + 300.0 + 500.0 * h, y), Color(CREAM, 0.25 * k), 2.0 + 3.0 * h)
	_stamp(ci, "STRIKE.", Vector2(330.0, 980.0), 120, GOLD, C("strike"), C("pangkah") - 0.02)
	var p: float = C("pangkah")
	var s: float = C("snap_back")
	if t >= p and t < s + 0.3:
		var c2: Vector2 = Vector2(W * 0.5, H * 0.5)
		_speed_lines(ci, c2, 1.0 - seg(t, s - 0.1, s + 0.25), Color(1.0, 0.95, 0.85, 0.9), 11, 240.0)
		# PANGKAH! slammed with drifting RGB-split echoes; blown away on the snap
		var blow: float = seg(t, s, s + 0.3)
		var sl: float = lerpf(2.4, 1.0, eo_back(seg(t, p, p + 0.22), 1.2)) * (1.0 + 1.6 * ei_quad(blow))
		var a: float = 1.0 - blow
		var w: float = FONT_TITLE.get_string_size("PANGKAH!", HORIZONTAL_ALIGNMENT_LEFT, -1, 170).x
		var base: Vector2 = Vector2(-w * 0.5, 60.0)
		var drift: float = 6.0 + 22.0 * seg(t, p, s)
		var at: Vector2 = Vector2(W * 0.5, 300.0)
		for e: Array in [[Vector2(-drift, 0.0), Color(1.0, 0.2, 0.25, 0.45 * a)], [Vector2(drift, drift * 0.3), Color(0.2, 0.85, 1.0, 0.45 * a)]]:
			ci.draw_set_transform(at + (e[0] as Vector2), 0.0, Vector2(sl, sl))
			ci.draw_string(FONT_TITLE, base, "PANGKAH!", HORIZONTAL_ALIGNMENT_LEFT, -1, 170, e[1])
		ci.draw_set_transform(at, 0.0, Vector2(sl, sl))
		ci.draw_string_outline(FONT_TITLE, base, "PANGKAH!", HORIZONTAL_ALIGNMENT_LEFT, -1, 170, 14, Color(OUTLINE, a))
		ci.draw_string(FONT_TITLE, base, "PANGKAH!", HORIZONTAL_ALIGNMENT_LEFT, -1, 170, Color(HT.HIT_ORANGE, a))
		ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	_toast(ci, "RING OUT!", Vector2(W * 0.5, 380.0), HT.SIDE_FOE, C("ringout"), 96)


func _callout(ci: CanvasItem, t0: float, local: Vector3, radius: float, side: float, label_at: Vector2,
		title: String, stat: String, frac: float, value: String) -> void:
	# technical-drawing callout: a dot on the top, a drawn leader, the label, a songket stat bar
	if t < t0 or hero == null:
		return
	var right: Vector3 = cam.global_transform.basis.x
	var anchor: Vector2 = _scr(hero.global_position + local + right * radius * side)
	var k: float = eo_expo(seg(t, t0, t0 + 0.3))
	var elbow: Vector2 = Vector2(label_at.x + (330.0 if side < 0.0 else -40.0), label_at.y + 26.0)
	var leg1: Vector2 = anchor.lerp(elbow, k)
	ci.draw_circle(anchor, 7.0, GOLD)
	ci.draw_arc(anchor, 7.0 + 18.0 * fposmod((t - t0) * 1.5, 1.0), 0.0, TAU, 32, Color(GOLD, 1.0 - fposmod((t - t0) * 1.5, 1.0)), 2.0, true)
	ci.draw_line(anchor, leg1, Color(CREAM, 0.9), 2.5, true)
	var k2: float = eo_expo(seg(t, t0 + 0.15, t0 + 0.45))
	if k2 > 0.0:
		var end: Vector2 = Vector2(label_at.x - 10.0 if side < 0.0 else label_at.x + 380.0, elbow.y)
		ci.draw_line(elbow, elbow.lerp(end, k2), Color(CREAM, 0.9), 2.5, true)
	_stagger(ci, FONT_TITLE, title, label_at, 50, GOLD, t0 + 0.12, 0.025, 0.35, 18.0, 2.0, 7)
	_stagger(ci, FONT_BODY, stat, label_at + Vector2(0.0, 58.0), 26, CREAM, t0 + 0.22, 0.03, 0.3, 10.0, 6.0, 4)
	var bar: Rect2 = Rect2(label_at + Vector2(0.0, 76.0), Vector2(300.0, 16.0))
	ci.draw_rect(bar, HT.GROOVE)
	var fill: float = frac * eo_expo(seg(t, t0 + 0.25, t0 + 0.8))
	_songket_bar(ci, Rect2(bar.position, Vector2(bar.size.x * fill, bar.size.y)))
	var shown: String = value
	if value.is_valid_int():
		shown = str(int(round(float(value) * eo_expo(seg(t, t0 + 0.25, t0 + 0.8)))))
	_tracked(ci, FONT_TITLE, shown, bar.position + Vector2(bar.size.x + 18.0, 18.0), 34, CREAM, 1.0, 5)


# ================================================================ the journey map

func _geo(ll: Vector2) -> Vector2:
	return Vector2(160.0 + (ll.x - 99.5) * 80.0, 120.0 + (7.3 - ll.y) * 80.0)


func _build_map() -> void:
	for poly: Array[Vector2] in [PENINSULA, BORNEO]:
		var n: int = poly.size()
		for i: int in n:
			var a: Vector2 = _geo(poly[i])
			var b: Vector2 = _geo(poly[(i + 1) % n])
			var steps: int = maxi(1, int(a.distance_to(b) / 12.0))
			for s: int in steps:
				_map_dots.append(a.lerp(b, float(s) / float(steps)))
	for ll: Vector2 in CAPITALS:
		_map_pips.append(_geo(ll))


func _bg_map(ci: CanvasItem, _lt: float) -> void:
	ci.draw_rect(Rect2(0.0, 0.0, W, H), HT.WOOD_EDGE.darkened(0.35))
	ci.draw_texture_rect(kelir_tex, Rect2(-200.0, -300.0, W + 400.0, H + 700.0), false, Color(0.32, 0.26, 0.2, 0.55))


func _mg_map(ci: CanvasItem, lt: float) -> void:
	var t0: float = C("map")
	var z: float = 1.0 + 0.04 * seg(lt, 0.0, 3.75)
	var piv: Vector2 = Vector2(W * 0.5, 380.0)
	var xf: Transform2D = Transform2D(0.0, Vector2(z, z), 0.0, piv) * Transform2D(0.0, -piv)
	ci.draw_set_transform_matrix(xf)
	var shown: int = int(_map_dots.size() * eo_cubic(seg(t, t0, t0 + 0.9)))
	for i: int in shown:
		ci.draw_circle(_map_dots[i], 3.2, Color(CREAM, 0.6))
	var dim: float = 1.0 - 0.45 * seg(t, C("masters"), C("masters") + 0.3)
	var count: int = 0
	for i: int in _map_pips.size():
		var ti: float = t0 + 0.15 + float(i) * spb * 0.25
		if t < ti:
			break
		count = i + 1
		var pp: Vector2 = _map_pips[i]
		if i > 0: # the route, dashed gold; the Kelantan -> Sabah leg arcs over the sea
			var prev: Vector2 = _map_pips[i - 1]
			var k: float = eo_cubic(seg(t, ti - spb * 0.25, ti))
			var pts: PackedVector2Array = PackedVector2Array()
			var ctrl: Vector2 = (prev + pp) * 0.5 + Vector2(0.0, -260.0 if i == 11 else 0.0)
			for s: int in 25:
				var u: float = float(s) / 24.0 * k
				pts.append(prev.lerp(ctrl, u).lerp(ctrl.lerp(pp, u), u))
			for s: int in range(0, 24, 2):
				ci.draw_line(pts[s], pts[s + 1], Color(GOLD, 0.85 * dim), 3.0, true)
		var pop: float = eo_back(seg(t, ti, ti + 0.18))
		var ring_k: float = seg(t, ti, ti + 0.5)
		ci.draw_arc(pp, 10.0 + 40.0 * ring_k, 0.0, TAU, 32, Color(GOLD, 0.8 * (1.0 - ring_k)), 2.0, true)
		_diamond(ci, pp, 13.0 * pop, Color(GOLD, dim))
		var lbl_a: float = seg(t, ti, ti + 0.05) * (1.0 - seg(t, ti + 0.3, ti + 0.45))
		if lbl_a > 0.0:
			var name_: String = String(_master(ORDER[i]).region_en).to_upper()
			_tracked(ci, FONT_BODY, name_, pp + Vector2(22.0, -14.0), 24, Color(CREAM, lbl_a), 4.0, 4)
		# a master stands in every state
		var mp: float = eo_back(seg(t, C("masters") + float(i) * spb * 0.125, C("masters") + float(i) * spb * 0.125 + 0.25))
		if mp > 0.0:
			_cut(ci, "res://assets/wayang/wayang_%s.png" % ORDER[i], pp + Vector2(0.0, -6.0), Vector2(0.5, 0.878),
				118.0 * mp, 0.0, (_master(ORDER[i]).color as Color), 1.0, xf, 0.0)
			ci.draw_set_transform_matrix(xf) # _cut resets the transform
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	# the count: 13 STATES · 13 MASTERS.
	var num: String = "%02d" % count
	_tracked(ci, FONT_TITLE, num, Vector2(160.0, 960.0), 210, GOLD, 4.0, 12)
	_stagger(ci, FONT_BODY, "STATES", Vector2(480.0, 880.0), 50, CREAM, t0 + 0.05, 0.03, 0.35, 20.0, 14.0, 6)
	_stagger(ci, FONT_TITLE, "MASTERS.", Vector2(474.0, 965.0), 92, GOLD, C("masters"), 0.03, 0.3, 40.0, 4.0, 9)


# ================================================================ ACT III — the masters

func _upd_cards(_lt: float) -> void:
	var idx: int = 0
	for i: int in _cards.size():
		if t >= float(_cards[i].t0):
			idx = i
	var c: Dictionary = _cards[idx]
	if idx != _card:
		_card = idx
		_clear_tops()
		_set_arena(c.id)
		var m: Dictionary = c.m
		hero = _spawn_top("jantung", GOLD, Vector3(0.9, 0.0, 0.0))
		rival = _spawn_top(String(m.mesh), (m.color as Color), Vector3(-0.9, 0.0, 0.0))
	var lt: float = t - float(c.t0)
	var dur: float = float(c.t1) - float(c.t0)
	# the pair circle each other; the long cards trade one blow on beat 3
	var th: float = spb * 2.0
	var dip: float = 0.4 * exp(-pow((lt - th) / 0.09, 2.0)) if c.tier == 0 else 0.0
	var a: float = float(c.idx) * 1.7 + lt * 2.4
	var r: float = 0.92 - dip
	hero.position = Vector3(cos(a), 0.0, sin(a)) * r
	rival.position = -hero.position
	if c.tier == 0 and _once("hit_" + String(c.id), float(c.t0) + th):
		_burst(Vector3(0.0, 0.45, 0.0), Color.WHITE, 1.0)
		hero.flash_accent()
		rival.flash_accent()
	# inside the gelanggang looking across at the state behind
	var k: float = seg(lt, 0.0, dur)
	var base_az: float = float(_card_cam(String(c.id)).x)
	var sweep: float = [26.0, 16.0, 9.0][c.tier]
	# every cut lands as a punch-in that settles out of a slight Dutch angle
	var punch: float = 1.0 - eo_expo(seg(lt, 0.0, 0.4))
	_orbit(Vector3(0.0, 0.55, 0.0), lerpf(3.7, 3.2, k), base_az - sweep * 0.5 + sweep * k, lerpf(15.0, 11.0, k), 56.0 + 16.0 * punch)
	cam.rotate_object_local(Vector3.BACK, deg_to_rad(5.0) * punch * (1.0 if int(c.idx) % 2 == 0 else -1.0))
	_dof(0.0)


func _card_cam(id: String) -> Vector2:
	# per-arena camera azimuth (deg) so each state's landmark sits behind the ring
	var az: Dictionary = {"perlis": 0.0, "kedah": 10.0, "penang": -10.0, "perak": 0.0, "selangor": 8.0,
		"nsembilan": -8.0, "melaka": 0.0, "johor": 12.0, "pahang": -6.0, "terengganu": 0.0, "kelantan": 6.0,
		"sabah": -10.0, "sarawak": 0.0}
	return Vector2(float(az.get(id, 0.0)), 0.0)


func _mg_cards(ci: CanvasItem, _lt: float) -> void:
	var c: Dictionary = _cards[maxi(_card, 0)]
	var m: Dictionary = c.m
	var mc: Color = m.color
	var t0: float = c.t0
	var t1: float = c.t1
	# whip streaks in the master's colour across the cut
	var wk: float = 1.0 - seg(t, t0, t0 + 0.14)
	if wk > 0.0:
		for i: int in 36:
			var h: float = fposmod(float(i) * 0.618034 + float(c.idx) * 0.13, 1.0)
			var x: float = lerpf(-600.0, W + 200.0, fposmod(h * 3.0 + (t - t0) * 7.0, 1.0))
			ci.draw_line(Vector2(x, h * H), Vector2(x + 400.0 + 600.0 * h, h * H), Color(mc, 0.5 * wk), 3.0 + 6.0 * h)
	# lower third: colour bar, name, state + one-liner
	var bar_k: float = eo_expo(seg(t, t0, t0 + 0.25))
	ci.draw_rect(Rect2(96.0, 1000.0 - 150.0 * bar_k, 12.0, 150.0 * bar_k), mc)
	var name_: String = String(m.name).to_upper()
	var nsize: int = 96 if c.tier < 2 else 110
	_stagger(ci, FONT_TITLE, name_, Vector2(134.0, 940.0), nsize, CREAM, t0 + 0.02, 0.018, 0.3, 0.0, 3.0, 10,
		Vector2i(-1, -1), GOLD, false, t1 + 0.2)
	if c.tier < 2:
		var region: String = String(m.region_en).to_upper()
		var line: String = region + "   " + String(LINES[c.id])
		_stagger(ci, FONT_BODY, line, Vector2(138.0, 992.0), 34, CREAM, t0 + 0.08, 0.012, 0.3, 14.0, 2.0, 5,
			Vector2i(0, region.length()), mc.lerp(Color.WHITE, 0.2))
	# the kelir card: the master's puppet steps up to the lamp
	if c.tier == 0:
		var pin: float = eo_expo(seg(t, t0 + 0.05, t0 + 0.4)) * (1.0 - ei_expo(seg(t, t1 - 0.15, t1)))
		var rect: Rect2 = Rect2(1490.0 + 420.0 * (1.0 - pin), 220.0, 330.0, 620.0)
		ci.draw_rect(rect.grow(10.0), INK)
		_kelir(ci, rect, _lamp(t))
		ci.draw_rect(rect.grow(4.0), mc, false, 3.0)
		var sway: float = deg_to_rad(2.5) * sin((t - t0) * 2.6)
		var path: String = "res://assets/wayang/wayang_%s.png" % c.id
		_cut(ci, path, Vector2(rect.get_center().x, rect.end.y - 40.0), Vector2(_figure_x(path), 0.878), 520.0, sway, INK)
		_songket_bar(ci, Rect2(rect.position.x, rect.end.y + 14.0, rect.size.x, 22.0), mc.lerp(GOLD, 0.4))
	# 01 / 13 with the pips
	var n: String = "%02d" % (int(c.idx) + 1)
	_tracked(ci, FONT_TITLE, n, Vector2(1590.0, 140.0), 92, GOLD, 2.0, 8)
	_tracked(ci, FONT_BODY, "/ 13", Vector2(1720.0, 140.0), 36, DIM, 4.0, 4)
	for i: int in 13:
		var pp: Vector2 = Vector2(1596.0 + float(i) * 19.0, 178.0)
		var cur: bool = i == int(c.idx)
		var r: float = 7.0 + (2.5 * sin(t * 18.0) if cur else 0.0)
		_diamond(ci, pp, r, GOLD if i <= int(c.idx) else Color(DIM, 0.5), i <= int(c.idx))


# ================================================================ ACT IV — the world

func _bg_food(ci: CanvasItem, lt: float) -> void:
	ci.draw_rect(Rect2(0.0, 0.0, W, H), HT.WOOD_EDGE.darkened(0.3))
	ci.draw_texture_rect(kelir_tex, Rect2(-300.0, -400.0, W + 600.0, H + 800.0), false, Color(0.45, 0.32, 0.2, 0.6))
	var c: Vector2 = Vector2(W * 0.5, H * 0.5 + 10.0)
	for ring: int in 3:
		var rr: float = 250.0 + 120.0 * float(ring)
		var n: int = 24 + ring * 8
		for i: int in n:
			var a: float = TAU * float(i) / float(n) + lt * (0.25 if ring % 2 == 0 else -0.2)
			_diamond(ci, c + Vector2(cos(a), sin(a)) * rr, 5.0, Color(GOLD, 0.18))


func _mg_food(ci: CanvasItem, lt: float) -> void:
	var c: Vector2 = Vector2(W * 0.5, H * 0.5 + 10.0)
	var t0: float = C("food")
	for i: int in ORDER.size():
		var ti: float = t0 + float(i) * spb / 8.0
		var p: float = seg(t, ti, ti + 0.5)
		if p <= 0.0:
			continue
		var a: float = -PI * 0.5 + TAU * float(i) / 13.0 + lt * 0.18
		var at: Vector2 = c.lerp(c + Vector2(cos(a), sin(a)) * 395.0, eo_back(p, 1.4))
		var s: float = lerpf(0.2, 1.0, eo_elastic(seg(t, ti, ti + 0.7)))
		var tx: Texture2D = T("res://assets/ui/icon_food_%s.png" % ORDER[i])
		var sz: Vector2 = Vector2(175.0, 175.0) * s
		ci.draw_circle(at + Vector2(0.0, 8.0), 80.0 * s, Color(0.0, 0.0, 0.0, 0.3))
		ci.draw_texture_rect(tx, Rect2(at - sz * 0.5, sz), false)
	_stamp(ci, "EAT LIKE", Vector2(W * 0.5, c.y - 40.0), 92, GOLD, t0, B(26) - 0.02)
	_stamp(ci, "A LOCAL.", Vector2(W * 0.5, c.y + 60.0), 92, GOLD, t0 + spb * 0.5, B(26) - 0.02)
	_tracked(ci, FONT_BODY, "13 DISHES  ·  TEMPORARY BUFFS", Vector2(W * 0.5, c.y + 140.0), 26,
		Color(CREAM, seg(t, t0 + 0.3, t0 + 0.5) * (1.0 - seg(t, B(26) - 0.15, B(26)))), 5.0, 4, true)


func _enter_carousel() -> void:
	_set_arena("kampung")
	var styles: Array[String] = ["jantung", "uri", "pakdin", "cikros", "tokgayong", "datuk"]
	var lacquer: Array[Color] = [GOLD, HT.SEPANG.lightened(0.3), HT.PANDAN, HT.NILA.lightened(0.2), HT.COPPER, CREAM]
	var all: Array = []
	for i: int in styles.size():
		all.append([styles[i], lacquer[i]])
	for id: String in ORDER:
		all.append([id, _master(id).color])
	all.append(["kl", Color(0.85, 0.7, 1.0)])
	for i: int in all.size():
		var a: float = TAU * float(i) / float(all.size())
		var g: Gasing = _spawn_top(String(all[i][0]), all[i][1], Vector3(cos(a), 0.0, sin(a)) * 3.05, 3)
		g.battling = false
		g.set_showcase(true)
		g.scale = Vector3.ONE * 0.9


func _upd_carousel(lt: float) -> void:
	# a crane reveal: from rope height the camera rises and swings until all twenty stand in one circle.
	# Kept to ~2 deg of turn per frame: a whip pan with no motion blur judders at 60 fps.
	var k: float = eio_sine(seg(lt, 0.0, spb * 4.0))
	_orbit(Vector3(0.0, 0.25, 0.0), lerpf(5.6, 6.8, k), lerpf(-10.0, 36.0, k), lerpf(12.0, 54.0, k), lerpf(44.0, 48.0, k))
	_dof(0.0)
	# a light chase runs round the ring on the 32nds
	for i: int in tops.size():
		if _once("chase_%d" % i, C("tops") + 0.15 + float(i) * spb / 8.0):
			tops[i].flash_accent()


func _mg_carousel(ci: CanvasItem, _lt: float) -> void:
	_stamp(ci, "COLLECT 20 TOPS.", Vector2(W * 0.5, 180.0), 104, GOLD, C("tops"), B(27) - 0.02)
	_tracked(ci, FONT_BODY, "FORGE  ·  LACQUER  ·  LEVEL UP", Vector2(W * 0.5, 262.0), 28,
		Color(CREAM, seg(t, C("tops") + 0.2, C("tops") + 0.4) * (1.0 - seg(t, B(27) - 0.12, B(27)))), 6.0, 5, true)


# ---- 2-4 player FFA in the kampung yard at dusk

# per top: [time, pos, velocity in, velocity out] keys; contacts sit 1.0 m apart (radii ~0.44-0.56)
var _ffa_keys: Array = []


func _enter_ffa() -> void:
	# the same yard at blue hour: cool sky and fill, warm lantern pools on the dish
	_set_arena("kampung", {"sky_top": Color(0.10, 0.13, 0.32), "sky_horizon": Color(0.62, 0.48, 0.62),
		"fog": Color(0.32, 0.32, 0.45), "fog_density": 0.004, "sun_color": Color(0.75, 0.78, 1.0), "sun_energy": 0.55,
		"lantern": Color(1.0, 0.66, 0.36), "lantern_energy": 3.2, "exposure": 1.1, "ambient": 0.45})
	var t1: float = C("tag_1")
	var t2: float = C("tag_2")
	var t3: float = C("tag_3")
	var t4: float = C("ffa_ringout")
	var end: float = C("blackout") + 0.1
	_ffa_keys = [
		[[t1, Vector3(-0.5, 0, 0.6), Vector3(2.0, 0, 0), Vector3(-2.4, 0, 0.6)], [t3, Vector3(-1.0, 0, -0.4), Vector3(0, 0, -2.2), Vector3(1.6, 0, 2.0)],
			[t4 + 0.3, Vector3(0.4, 0, 1.4), Vector3(1.2, 0, 1.0), Vector3(1.0, 0, 0.6)], [end, Vector3(1.4, 0, 1.9), Vector3(0.6, 0, 0.2), Vector3.ZERO]],
		[[t1, Vector3(0.5, 0, 0.6), Vector3(-2.0, 0, 0), Vector3(2.2, 0, 0.8)], [t4 - 0.45, Vector3(0.6, 0, 1.0), Vector3(-1.0, 0, -1.6), Vector3(0.0, 0, -2.0)],
			[t4, Vector3(1.2, 0, -0.1), Vector3(1.6, 0, -0.8), Vector3(-1.4, 0, 0.9)], [end, Vector3(-0.2, 0, 0.6), Vector3(-0.8, 0, 0.2), Vector3.ZERO]],
		[[t1, Vector3(-2.0, 0, -2.2), Vector3(0.6, 0, 1.4), Vector3(0.6, 0, 1.4)], [t2, Vector3(-0.3, 0, -1.4), Vector3(2.0, 0, 0.4), Vector3(-1.8, 0, 0.6)],
			[t3, Vector3(-1.0, 0, -1.4), Vector3(0, 0, 1.6), Vector3(-0.8, 0, -2.0)], [end, Vector3(-2.3, 0, -1.6), Vector3(-0.4, 0, 0.6), Vector3.ZERO]],
		[[t1, Vector3(2.2, 0, -2.2), Vector3(-1.2, 0, 1.0), Vector3(-1.2, 0, 1.0)], [t2, Vector3(0.7, 0, -1.4), Vector3(-2.0, 0, 0.2), Vector3(2.0, 0, 0.4)],
			[t4, Vector3(2.0, 0, -0.75), Vector3(-0.4, 0, 1.2), Vector3(3.2, 0, -2.6)], [t4 + 0.4, Vector3(3.3, 0, -1.65), Vector3(2.0, 0, -1.6), Vector3.ZERO]],
	]
	var kit: Array = [["jantung", GOLD], ["uri", HT.FOE_COLOR], ["cikros", HT.SIDE_FOE], ["datuk", Color(0.65, 0.52, 1.0)]]
	for i: int in 4:
		var g: Gasing = _spawn_top(String(kit[i][0]), kit[i][1], (_ffa_keys[i][0][1] as Vector3), 2)
		g.set_team(kit[i][1], i == 0)
		ffa.append(g)


func _hermite(keys: Array, w: float) -> Vector3:
	if w <= float(keys[0][0]):
		return keys[0][1]
	for i: int in keys.size() - 1:
		var a: Array = keys[i]
		var b: Array = keys[i + 1]
		if w <= float(b[0]):
			var d: float = float(b[0]) - float(a[0])
			var u: float = (w - float(a[0])) / d
			var u2: float = u * u
			var u3: float = u2 * u
			return (a[1] as Vector3) * (2.0 * u3 - 3.0 * u2 + 1.0) + (a[3] as Vector3) * d * (u3 - 2.0 * u2 + u) \
				+ (b[1] as Vector3) * (-2.0 * u3 + 3.0 * u2) + (b[2] as Vector3) * d * (u3 - u2)
	return keys[keys.size() - 1][1]


func _upd_ffa(lt: float) -> void:
	var w: float = _world_t(t)
	for i: int in ffa.size():
		if is_instance_valid(ffa[i]) and ffa[i].alive:
			ffa[i].position = _hermite(_ffa_keys[i], w)
	for hit: Array in [["tag_1", 0, 1], ["tag_2", 2, 3], ["tag_3", 0, 2], ["ffa_ringout", 1, 3]]:
		if _once("ffa_" + String(hit[0]), C(hit[0])):
			var a: Gasing = ffa[hit[1]]
			var b: Gasing = ffa[hit[2]]
			var mid: Vector3 = (a.position + b.position) * 0.5 + Vector3(0.0, 0.45, 0.0)
			_burst(mid, Color.WHITE, 1.3 if hit[0] == "ffa_ringout" else 1.0)
			a.flash_accent()
			b.flash_accent()
			_shock(mid - Vector3(0.0, 0.45, 0.0), C(hit[0]), 1.8)
	if _once("ffa_out", C("ffa_ringout") + 0.4) and is_instance_valid(ffa[3]):
		ffa[3].velocity = Vector3(2.0, 0.0, -1.6)
		ffa[3].die("ringout")
	var k: float = seg(lt, 0.0, C("blackout") - B(27))
	_orbit(Vector3(0.0, 0.0, 0.2), lerpf(8.0, 6.6, k), lerpf(-10.0, 55.0, eio_cubic(k)), lerpf(54.0, 38.0, k),
		48.0 - 5.0 * pulse(t, C("ffa_ringout"), 8.0))
	cam.h_offset = -1.9 # the ring sits right of frame, the feature tags own the left
	_dof(0.0)


func _mg_ffa(ci: CanvasItem, _lt: float) -> void:
	var out: float = C("blackout") - 0.25
	var shade: float = eo_expo(seg(t, C("tag_1"), C("tag_1") + 0.3)) * (1.0 - ei_expo(seg(t, out, out + 0.25)))
	for i: int in 30: # a soft dark wash behind the tags
		ci.draw_rect(Rect2(float(i) * 40.0, 0.0, 40.0, H), Color(0.0, 0.0, 0.0, 0.55 * shade * (1.0 - float(i) / 30.0)))
	for i: int in 3:
		var t0: float = C("tag_%d" % (i + 1))
		var txt: String = ["STORY JOURNEY", "ENDLESS GELANGGANG", "2-4 PLAYERS  ·  LAN / STEAM"][i]
		var k: float = eo_expo(seg(t, t0, t0 + 0.3))
		if k <= 0.0:
			continue
		var y: float = 190.0 + 110.0 * float(i)
		var x: float = lerpf(-700.0, 110.0, k) - 900.0 * ei_expo(seg(t, out, out + 0.25))
		var size: int = 80 if i < 2 else 64
		ci.draw_string(FONT_TITLE, Vector2(x + 4.0, y + 6.0), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(0.0, 0.0, 0.0, 0.45))
		ci.draw_string_outline(FONT_TITLE, Vector2(x, y), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, size, 10, OUTLINE)
		ci.draw_string(FONT_TITLE, Vector2(x, y), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, size, GOLD if i == 2 else CREAM)
		_songket_bar(ci, Rect2(x, y + 18.0, 520.0 * eo_expo(seg(t, t0 + 0.1, t0 + 0.45)), 14.0))
	# player tags tracked above each top
	for i: int in ffa.size():
		if not is_instance_valid(ffa[i]) or not ffa[i].alive:
			continue
		var p: Vector2 = _scr(ffa[i].position + Vector3(0.0, 1.35, 0.0))
		var col: Color = [GOLD, HT.FOE_COLOR, HT.SIDE_FOE, Color(0.65, 0.52, 1.0)][i]
		var r: Rect2 = Rect2(p - Vector2(38.0, 26.0), Vector2(76.0, 44.0))
		ci.draw_rect(r, col)
		ci.draw_rect(r, INK, false, 3.0)
		ci.draw_colored_polygon(PackedVector2Array([p + Vector2(-10.0, 18.0), p + Vector2(10.0, 18.0), p + Vector2(0.0, 32.0)]), col)
		_tracked(ci, FONT_TITLE, "P%d" % (i + 1), p + Vector2(0.0, 12.0), 34, INK, 1.0, 0, true)
	_toast(ci, "RING OUT!", Vector2(W * 0.62, 420.0), Color(0.65, 0.52, 1.0), C("ffa_ringout") + 0.4, 96)


func _bg_black(ci: CanvasItem, _lt: float) -> void:
	ci.draw_rect(Rect2(0.0, 0.0, W, H), Color.BLACK)


# ================================================================ ACT V — the title

func _build_emblem_dots() -> void:
	var img: Image = TEX_GUNUNGAN_GOLD.get_image()
	if img.is_compressed():
		img.decompress()
	var step: int = 20
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 99
	for y: int in range(step / 2, img.get_height(), step):
		for x: int in range(step / 2, img.get_width(), step):
			if img.get_pixel(x, y).a > 0.5:
				var a: float = rng.randf() * TAU
				var start: Vector2 = Vector2(W * 0.5, 330.0) + Vector2(cos(a), sin(a)) * rng.randf_range(700.0, 1400.0)
				_emblem_dots.append([Vector2(x, y) / float(img.get_width()), start, rng.randf() * 0.3])


func _enter_title() -> void:
	_set_arena("kampung")
	title_top = _spawn_top("jantung", GOLD, Vector3.ZERO, 5)


func _title_group() -> Transform2D:
	# the lockup settles up and smaller as the yard fades in behind it
	var k: float = eio_cubic(seg(t, C("tagline_1") - 0.1, C("tagline_1") + 0.55))
	var s: float = lerpf(1.0, 0.6, k)
	return Transform2D(0.0, Vector2(s, s), 0.0, Vector2(W * 0.5, lerpf(400.0, 230.0, k))) * Transform2D(0.0, -Vector2(W * 0.5, 400.0))


func _upd_title(_lt: float) -> void:
	var tl: float = C("tagline_1")
	var top_t: float = C("topple")
	if is_instance_valid(title_top) and title_top.alive:
		title_top.wobble = lerpf(0.05, 0.95, ei_quad(seg(t, top_t - 1.2, top_t)))
		title_top.spin = lerpf(40.0, 14.0, seg(t, top_t - 1.5, top_t))
		if _once("topple", top_t):
			title_top.velocity = Vector3(0.6, 0.0, 0.4)
			title_top.die("topple")
	var k: float = seg(t, tl - 0.3, 60.0)
	# the top stands low in frame, between the lockup and the tagline
	_orbit(Vector3(0.0, 0.95, 0.0), lerpf(3.7, 3.4, k), lerpf(20.0, 34.0, k), 10.0, 44.0)
	_dof(4.4, 0.08, 3.0)
	emblem.visible = true
	var g: Transform2D = _title_group()
	var gs: float = g.get_scale().x
	var center: Vector2 = g * Vector2(W * 0.5, EMBLEM_Y)
	emblem.size = Vector2(EMBLEM_SIZE, EMBLEM_SIZE)
	emblem.pivot_offset = emblem.size * 0.5
	emblem.scale = Vector2(gs, gs)
	emblem.position = center - emblem.size * 0.5
	emblem.modulate.a = seg(t, B(29, 3.0), B(29, 3.6))
	shine.set_shader_parameter("shine", lerpf(-0.4, 1.7, seg(t, B(29, 4), B(30, 2))))


func _bg_title(ci: CanvasItem, _lt: float) -> void:
	# black until the yard fades up under the tagline, then a dark gradient keeps the lockup legible
	var yard: float = seg(t, C("tagline_1") - 0.1, C("tagline_1") + 0.6)
	ci.draw_rect(Rect2(0.0, 0.0, W, H), Color(0.0, 0.0, 0.0, 1.0 - 0.9 * yard))
	if yard > 0.0:
		for i: int in 24:
			var y: float = float(i) * 24.0
			ci.draw_rect(Rect2(0.0, y, W, 24.0), Color(0.0, 0.0, 0.0, 0.55 * yard * (1.0 - float(i) / 24.0)))
		ci.draw_rect(Rect2(0.0, H - 220.0, W, 220.0), Color(0.0, 0.0, 0.0, 0.35 * yard))


func _mg_title(ci: CanvasItem, _lt: float) -> void:
	var t0: float = C("title_gong")
	var g: Transform2D = _title_group()
	# the gong's shockwave ring
	var rk: float = seg(t, t0, t0 + 1.0)
	if rk > 0.0 and rk < 1.0:
		ci.draw_arc(g * Vector2(W * 0.5, EMBLEM_Y), 40.0 + 1300.0 * eo_cubic(rk), 0.0, TAU, 128, Color(GOLD, 0.7 * (1.0 - rk)), 6.0 * (1.0 - rk) + 1.0, true)
	# perforation dots implode into the gunungan, then the gold fills in
	var fade_dots: float = 1.0 - seg(t, B(29, 3.4), B(29, 4.2))
	if fade_dots > 0.0:
		ci.draw_set_transform_matrix(g)
		for d: Array in _emblem_dots:
			var target: Vector2 = Vector2(W * 0.5, EMBLEM_Y) + ((d[0] as Vector2) - Vector2(0.5, 0.5)) * EMBLEM_SIZE
			var p: float = eo_expo(seg(t, t0 + float(d[2]), t0 + float(d[2]) + 0.65))
			var p2: float = eo_expo(seg(t - 0.035, t0 + float(d[2]), t0 + float(d[2]) + 0.65))
			if p <= 0.0:
				continue
			var at: Vector2 = (d[1] as Vector2).lerp(target, p)
			var prev: Vector2 = (d[1] as Vector2).lerp(target, p2)
			ci.draw_line(prev, at, Color(GOLD, 0.35 * fade_dots), 3.0, true)
			ci.draw_circle(at, 4.0, Color(GOLD, fade_dots))
		ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	# GASING PANGKAH: letters drop in with overshoot; the songket band draws out from the centre
	var title: String = "GASING PANGKAH"
	var size: int = 140
	var tl: float = C("title_letters")
	var x: float = W * 0.5 - _tw(FONT_TITLE, title, size, 6.0) * 0.5
	ci.draw_set_transform_matrix(g)
	for i: int in title.length():
		var p: float = seg(t, tl + float(i) * 0.04, tl + float(i) * 0.04 + 0.45)
		var cw: float = FONT_TITLE.get_char_size(title.unicode_at(i), size).x + 6.0
		if p > 0.0:
			var a: float = clampf(p * 4.0, 0.0, 1.0)
			var at: Vector2 = Vector2(x, TITLE_Y - 90.0 * (1.0 - eo_back(p, 2.2)))
			ci.draw_char(FONT_TITLE, at + Vector2(4.0, 6.0), title[i], size, Color(0.0, 0.0, 0.0, 0.5 * a))
			ci.draw_char_outline(FONT_TITLE, at, title[i], size, 14, Color(0.25, 0.12, 0.02, a))
			ci.draw_char(FONT_TITLE, at, title[i], size, Color(GOLD, a))
		x += cw
	var bk: float = eo_expo(seg(t, tl + 0.5, tl + 1.1))
	_songket_bar(ci, Rect2(W * 0.5 - 500.0 * bk, TITLE_Y + 45.0, 1000.0 * bk, 30.0))
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	# the tagline, phrase by phrase on the beat
	var phrases: Array[String] = ["WIND YOUR TOP.", "STRIKE YOUR RIVAL.", "RULE THE RING."]
	var gap: float = 54.0
	var tsize: int = 58
	var total: float = gap * 2.0
	for ph: String in phrases:
		total += _tw(FONT_TITLE, ph, tsize, 3.0)
	var px: float = W * 0.5 - total * 0.5
	for i: int in 3:
		var t0p: float = C("tagline_%d" % (i + 1))
		_stagger(ci, FONT_TITLE, phrases[i], Vector2(px, 960.0), tsize, GOLD if i == 2 else CREAM, t0p, 0.025, 0.4, 30.0, 3.0, 8)
		px += _tw(FONT_TITLE, phrases[i], tsize, 3.0) + gap
	_tracked(ci, FONT_BODY, "A MALAY HERITAGE GAME   ·   PC   ·   2-4 PLAYERS  LAN / STEAM", Vector2(W * 0.5, 1030.0), 24,
		Color(DIM, seg(t, B(32, 2), B(32, 3))), 4.0, 4, true)
