class_name Gasing
extends Node3D

# Authority only (puppets never tick): arena turns these into dust/sound/shake.
signal landed(point: Vector3, strength: float)
signal rim_touched(point: Vector3, speed: float)

const HT = preload("res://scripts/heritage_theme.gd")
const DIE_SECONDS: float = 1.0 # die() -> queue_free; the arena delays result panels by this
const DANGER_COLOR: Color = Color(1.0, 0.3, 0.2)
const RING_RADIUS: float = 4.0
const OUT_RADIUS: float = 4.2
const RIM_CLIMB_SPEED: float = 3.6
const SPIN_DECAY: float = 1.15
const MOMENTUM_DRAG: float = 4.0
const MOVE_SPEED: float = 2.2
const MOVE_ACCELERATION: float = 12.0
const DASH_COST: float = 20.0
const DASH_DURATION: float = 0.18
const RUSH_COST_PER_SECOND: float = 20.0
const RUSH_SPEED: float = 3.6
const JUMP_COST: float = 25.0
const JUMP_DURATION: float = 0.6
const JUMP_HEIGHT: float = 0.85

var display_name: String = "Gasing"
var shape_id: String = "jantung"
var mesh_id: String = "jantung"
var mass: float = 2.4
var spin_reserve: float = 70.0
var balance: float = 60.0
var radius: float = 0.44
var accent_color: Color = Color(1.0, 0.8, 0.25)
var owner_id: int = 0
var slot_id: int = 0
var level: int = 1
var inspection_mode: bool = false

var puppet: bool = false # remote-controlled: net snapshots drive x/z/spin/wobble; die() is RPC-driven
var arcana: bool = false # the KL rainbow gasing: hue-cycling aura + particle trail
var spin: float = 0.0
var launch_spin: float = 1.0
var velocity: Vector3 = Vector3.ZERO
var control_velocity: Vector3 = Vector3.ZERO
var energy: float = 0.0
var dash_cd: float = 0.0
var jump_cd: float = 0.0
var nudge_cd: float = 0.0
var dash_time: float = 0.0
var jump_time: float = 0.0
var rushing: bool = false
var rush_paid_seconds: float = 0.0
var rush_direction: Vector3 = Vector3.FORWARD
var battling: bool = false
var alive: bool = true
var wobble: float = 0.0
var pending_elimination: String = ""
var round_over: bool = false # result applied: still spinning on screen, but refuses every action
var team_color: Color = Color(1.0, 0.8, 0.25)
var is_local: bool = false

var _spin_node: Node3D = null
var _dir_arrow: Node3D = null
var _arrow_tween: Tween = null
var _mesh: MeshInstance3D = null
var _body_mat: StandardMaterial3D = null
var _accent_mat: StandardMaterial3D = null
var _spin_angle: float = 0.0
var _lean_phase: float = 0.0
var _trail: CPUParticles3D = null
var _action_trail: CPUParticles3D = null
var _shadow: MeshInstance3D = null
var _slot_label: Label3D = null
var _selected: bool = false
var _winding: bool = false
var _steering: bool = false
var _showed_rush_arrow: bool = false
var _launch_time: float = 0.0
var _dash_direction: Vector3 = Vector3.FORWARD
var _hue: float = 0.0
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()
var _accent_base: float = 0.5 # resting lacquer glow; flashes tween back to this
var _flash_tween: Tween = null
var _ring_mat: StandardMaterial3D = null
var _has_team: bool = false
var _label_pct: int = -1
var _showcase: bool = false
var _net_target: Vector3 = Vector3.ZERO
var _has_net_target: bool = false

# Shared across every top: one grain texture, one lathe-profile scan per mesh/band.
static var _grain_normal: NoiseTexture2D = null
static var _band_cache: Dictionary = {}

@onready var _visual: Node3D = $Visual
@onready var _highlight: MeshInstance3D = $HighlightRing


func _ready() -> void:
	_highlight.visible = false


func setup(p_name: String, p_shape: String, stats: Dictionary, p_accent: Color) -> void:
	display_name = p_name
	shape_id = p_shape
	mass = stats.get("mass", 2.0)
	spin_reserve = stats.get("spin_reserve", 80.0)
	balance = stats.get("balance", 70.0)
	level = clampi(int(stats.get("level", 1)), 1, 5)
	accent_color = p_accent
	mesh_id = String(stats.get("mesh", p_shape))
	arcana = mesh_id == "kl"
	radius = 0.56 if shape_id == "uri" else 0.44
	_rng.randomize()
	_build_visual()


func _build_visual() -> void:
	for child: Node in _visual.get_children():
		child.queue_free()
	var packed: PackedScene = load("res://assets/gasing_%s.glb" % mesh_id)
	if packed == null:
		packed = load("res://assets/gasing_jantung.glb") # master GLB not produced yet
	var inst: Node3D = packed.instantiate() as Node3D
	_visual.add_child(inst)
	_spin_node = inst
	_mesh = _find_mesh(inst)
	_body_mat = StandardMaterial3D.new()
	_body_mat.albedo_color = Color(0.42, 0.24, 0.11)
	_body_mat.roughness = 0.62 - float(level - 1) * 0.075
	_body_mat.normal_enabled = true
	_body_mat.normal_texture = _wood_grain_normal()
	_body_mat.uv1_triplanar = true # lathe mesh has no UVs; project grain from local axes
	_body_mat.uv1_scale = Vector3(2.4, 2.4, 2.4)
	_accent_mat = StandardMaterial3D.new()
	_accent_mat.albedo_color = accent_color
	_accent_mat.emission_enabled = true
	_accent_mat.emission = accent_color
	_accent_base = 0.5 # painted lacquer trim, not neon (flash spikes on hit)
	_accent_mat.emission_energy_multiplier = _accent_base
	if _mesh != null:
		_mesh.set_surface_override_material(0, _body_mat)
		if _mesh.mesh != null and _mesh.mesh.get_surface_count() > 1:
			_mesh.set_surface_override_material(1, _accent_mat)
	_build_dir_arrow()
	var ring_color: Color = team_color if _has_team else accent_color
	_ring_mat = StandardMaterial3D.new()
	_ring_mat.albedo_color = ring_color
	_ring_mat.emission_enabled = true
	_ring_mat.emission = ring_color
	_ring_mat.emission_energy_multiplier = 2.2
	_highlight.set_surface_override_material(0, _ring_mat)
	if arcana:
		_build_arcana()
	_build_level_bands()
	_build_action_visuals()


func _build_level_bands() -> void:
	# Each earned level adds a visible lacquer band; no extra asset variants needed.
	if _mesh == null or _mesh.mesh == null:
		return
	var vertices: PackedVector3Array = PackedVector3Array()
	for i: int in range(level - 1):
		var key: String = "%s:%d" % [mesh_id, i]
		if not _band_cache.has(key):
			if vertices.is_empty(): # surface_get_arrays copies the whole mesh; only pay it on a miss
				vertices = _mesh.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
			_band_cache[key] = _band_profile(vertices, _mesh.get_aabb().end.y * (0.25 + float(i) * 0.1))
		var profile: Vector2 = _band_cache[key] # x = height, y = radius (< 0: profile not found)
		var band_radius: float = profile.y if profile.y >= 0.0 else radius
		var band: MeshInstance3D = MeshInstance3D.new()
		var ring: TorusMesh = TorusMesh.new()
		ring.inner_radius = maxf(band_radius - 0.005, 0.005)
		ring.outer_radius = band_radius + 0.025
		band.mesh = ring
		band.material_override = _accent_mat
		band.position.y = profile.x
		_visual.add_child(band)


static func _band_profile(vertices: PackedVector3Array, height: float) -> Vector2:
	var below: Vector2 = Vector2(-INF, 0.0)
	var above: Vector2 = Vector2(INF, 0.0)
	# The imported tops are lathed meshes; interpolate their actual side profile.
	for v: Vector3 in vertices:
		var width: float = Vector2(v.x, v.z).length()
		if v.y <= height and v.y >= below.x:
			below = Vector2(v.y, maxf(width, below.y) if is_equal_approx(v.y, below.x) else width)
		if v.y >= height and v.y <= above.x:
			above = Vector2(v.y, maxf(width, above.y) if is_equal_approx(v.y, above.x) else width)
	if not is_finite(below.x) or not is_finite(above.x):
		return Vector2(height, -1.0)
	return Vector2(height, lerpf(below.y, above.y, (height - below.x) / maxf(above.x - below.x, 0.001)))


func _build_action_visuals() -> void:
	if _action_trail != null:
		_action_trail.queue_free()
	_action_trail = CPUParticles3D.new()
	_action_trail.local_coords = false
	_action_trail.amount = 36
	_action_trail.lifetime = 0.28
	_action_trail.emitting = false
	_action_trail.gravity = Vector3.ZERO
	_action_trail.initial_velocity_max = 0.15
	_action_trail.scale_amount_min = 0.04
	_action_trail.scale_amount_max = 0.09
	_action_trail.position.y = 0.18
	var spark: SphereMesh = SphereMesh.new()
	spark.radius = 1.0
	spark.height = 2.0
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = accent_color
	mat.emission_enabled = true
	mat.emission = accent_color
	mat.emission_energy_multiplier = 2.0
	spark.material = mat
	_action_trail.mesh = spark
	add_child(_action_trail)
	if _shadow == null:
		_shadow = MeshInstance3D.new()
		var disk: CylinderMesh = CylinderMesh.new()
		disk.top_radius = radius * 0.8
		disk.bottom_radius = radius * 0.8
		disk.height = 0.005
		_shadow.mesh = disk
		var shadow_mat: StandardMaterial3D = StandardMaterial3D.new()
		shadow_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		shadow_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		shadow_mat.albedo_color = Color(0.02, 0.015, 0.01, 0.42)
		_shadow.material_override = shadow_mat
		_shadow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(_shadow)
	if _slot_label == null:
		_slot_label = Label3D.new()
		_slot_label.font_size = 56
		_slot_label.pixel_size = 0.0042
		_slot_label.outline_size = 14
		_slot_label.outline_modulate = HT.WOOD_EDGE # the HUD's carved outline
		_slot_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_slot_label.no_depth_test = true
		add_child(_slot_label)
	# raised by the footprint too: under the steep camera a wide, flat top's crown would
	# otherwise project over its own label
	var box: AABB = _mesh.get_aabb() if _mesh != null else AABB(Vector3.ZERO, Vector3(0.5, 0.55, 0.5))
	_slot_label.position.y = box.end.y + 0.3 + box.size.x * 0.4
	_slot_label.modulate = team_color if _has_team else accent_color
	_slot_label.visible = battling
	_label_pct = -1


func _build_arcana() -> void:
	_accent_base = 1.2
	_accent_mat.emission_energy_multiplier = _accent_base
	if _trail != null:
		_trail.queue_free()
	_trail = CPUParticles3D.new()
	_trail.local_coords = false # particles stay behind in world space = ribbon trail
	_trail.amount = 42
	_trail.lifetime = 0.7
	_trail.emitting = false
	_trail.gravity = Vector3.ZERO
	_trail.initial_velocity_max = 0.25
	_trail.scale_amount_min = 0.05
	_trail.scale_amount_max = 0.12
	var pm: SphereMesh = SphereMesh.new()
	pm.radius = 0.05
	pm.height = 0.1
	_trail.mesh = pm
	var pmat: StandardMaterial3D = StandardMaterial3D.new()
	pmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	pmat.vertex_color_use_as_albedo = true
	pmat.emission_enabled = true
	pmat.emission = Color.WHITE
	pmat.emission_energy_multiplier = 1.5
	pm.material = pmat
	var grad: Gradient = Gradient.new()
	for i: int in 7:
		grad.add_point(float(i) / 6.0, Color.from_hsv(float(i) / 6.0, 0.85, 1.0))
	_trail.color_ramp = grad
	_trail.position.y = 0.15
	add_child(_trail)


func _build_dir_arrow() -> void:
	if _dir_arrow != null:
		_dir_arrow.queue_free()
	_dir_arrow = Node3D.new()
	add_child(_dir_arrow)
	var arrow_mat: StandardMaterial3D = StandardMaterial3D.new()
	arrow_mat.albedo_color = accent_color
	arrow_mat.emission_enabled = true
	arrow_mat.emission = accent_color
	arrow_mat.emission_energy_multiplier = 2.5
	var shaft: MeshInstance3D = MeshInstance3D.new()
	var shaft_mesh: BoxMesh = BoxMesh.new()
	shaft_mesh.size = Vector3(0.07, 0.02, 0.7)
	shaft.mesh = shaft_mesh
	shaft.position = Vector3(0.0, 0.06, -0.8)
	shaft.material_override = arrow_mat
	_dir_arrow.add_child(shaft)
	var head: MeshInstance3D = MeshInstance3D.new()
	var head_mesh: CylinderMesh = CylinderMesh.new()
	head_mesh.top_radius = 0.0
	head_mesh.bottom_radius = 0.12
	head_mesh.height = 0.28
	head.mesh = head_mesh
	head.position = Vector3(0.0, 0.06, -1.25)
	head.rotation_degrees = Vector3(-90.0, 0.0, 0.0)
	head.material_override = arrow_mat
	_dir_arrow.add_child(head)
	_dir_arrow.visible = false


func flash_direction(dir: Vector3) -> void:
	if _dir_arrow == null:
		return
	var flat: Vector3 = Vector3(dir.x, 0.0, dir.z)
	if flat.length() < 0.01:
		return
	flat = flat.normalized()
	_dir_arrow.rotation.y = atan2(-flat.x, -flat.z)
	if _arrow_tween != null and _arrow_tween.is_valid():
		_arrow_tween.kill()
	_dir_arrow.visible = true
	_dir_arrow.scale = Vector3(0.5, 0.5, 0.5)
	_arrow_tween = create_tween()
	_arrow_tween.tween_property(_dir_arrow, "scale", Vector3.ONE, 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_arrow_tween.tween_interval(0.3)
	_arrow_tween.tween_property(_dir_arrow, "scale", Vector3(0.05, 0.05, 0.05), 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	_arrow_tween.tween_callback(_dir_arrow.hide)


static func _wood_grain_normal() -> NoiseTexture2D:
	if _grain_normal != null:
		return _grain_normal
	var n: FastNoiseLite = FastNoiseLite.new()
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = 0.9
	_grain_normal = NoiseTexture2D.new()
	_grain_normal.noise = n
	_grain_normal.seamless = true
	_grain_normal.as_normal_map = true
	_grain_normal.bump_strength = 1.1
	return _grain_normal


func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node
	for child: Node in node.get_children():
		var found: MeshInstance3D = _find_mesh(child)
		if found != null:
			return found
	return null


func set_winding(on: bool) -> void:
	_winding = on
	_update_ring()


func set_selected(on: bool) -> void:
	_selected = on
	_update_ring()


func set_team(color: Color, p_is_local: bool) -> void:
	# Side identity: the highlight becomes a floor ring in the team colour for every live top.
	team_color = color
	is_local = p_is_local
	_has_team = true
	_label_pct = -1
	if _ring_mat != null:
		_ring_mat.albedo_color = color
		_ring_mat.emission = color
	_update_ring()


func _update_ring() -> void:
	if _highlight == null:
		return
	if not _has_team:
		_highlight.visible = alive and (_selected or _winding) # menu/workshop tops: legacy highlight
		return
	_highlight.visible = alive
	_highlight.position.y = (0.03 - position.y) / maxf(scale.y, 0.01) # stays on the floor while airborne
	var size: float = radius / 0.5
	var glow: float = 0.6 # unselected: dim, flattened
	if _selected:
		glow = 2.85 + 0.65 * sin(Time.get_ticks_msec() * 0.005)
	elif _winding:
		glow = 3.0
	_highlight.scale = Vector3(size, size if glow > 1.0 else size * 0.45, size)
	if _ring_mat != null:
		_ring_mat.emission_energy_multiplier = glow


func set_showcase(on: bool) -> void:
	# Title-screen hero: fast spin with a steady precessing lean so it reads as a live top.
	_showcase = on
	if not on and _visual != null and not battling and not inspection_mode:
		_visual.rotation = Vector3.ZERO


func set_inspect_rotation(yaw: float, pitch: float) -> void:
	if not is_finite(yaw) or not is_finite(pitch) or _visual == null:
		return
	inspection_mode = true
	_visual.rotation = Vector3(clampf(pitch, -1.1, 1.1), yaw, 0.0)


func _can_act() -> bool:
	return alive and battling and not puppet and not round_over and pending_elimination.is_empty() \
		and is_finite(energy) and is_finite(spin) and velocity.is_finite() and control_velocity.is_finite()


func _flat_direction(dir: Vector3) -> Vector3:
	if not dir.is_finite():
		return Vector3.ZERO
	var flat: Vector3 = Vector3(dir.x, 0.0, dir.z)
	return flat.normalized() if flat.length_squared() > 0.0001 else Vector3.ZERO


func steer(direction: Vector3, delta: float) -> void:
	if not _can_act() or not is_finite(delta) or delta <= 0.0:
		return
	var dir: Vector3 = _flat_direction(direction)
	if dir == Vector3.ZERO or dash_time > 0.0 or rushing:
		return
	_steering = true
	control_velocity = control_velocity.move_toward(dir * MOVE_SPEED, MOVE_ACCELERATION * delta)


func nudge(dir: Vector3) -> bool:
	var flat: Vector3 = _flat_direction(dir)
	if not _can_act() or nudge_cd > 0.0 or flat == Vector3.ZERO or dash_time > 0.0:
		return false
	nudge_cd = 0.35
	control_velocity = flat * MOVE_SPEED
	flash_direction(flat)
	return true


func dash(dir: Vector3) -> bool:
	var flat: Vector3 = _flat_direction(dir)
	if not _can_act() or dash_cd > 0.0 or energy < DASH_COST or flat == Vector3.ZERO:
		return false
	energy -= DASH_COST
	dash_cd = 1.0
	dash_time = DASH_DURATION
	_dash_direction = flat
	rushing = false
	control_velocity = flat * 5.0
	flash_direction(flat)
	return true


func set_rush(on: bool, dir: Vector3) -> void:
	var flat: Vector3 = _flat_direction(dir)
	rushing = on and _can_act() and energy > 0.0 and dash_time <= 0.0 and jump_time <= 0.0 and flat != Vector3.ZERO
	if rushing:
		rush_direction = flat


func jump() -> bool:
	if not _can_act() or jump_cd > 0.0 or energy < JUMP_COST or _launch_time > 0.0:
		return false
	energy -= JUMP_COST
	jump_cd = 2.5
	jump_time = JUMP_DURATION
	rushing = false
	flash_accent()
	return true


func cancel_control() -> void:
	_steering = false
	rushing = false


func end_round() -> void:
	# Result applied: freeze in place and refuse actions, but stay alive+battling so the top
	# keeps spinning with its shadow, lean, label and ring. The arena stops ticking physics.
	cancel_control()
	round_over = true
	dash_time = 0.0
	jump_time = 0.0
	_launch_time = 0.0
	rush_paid_seconds = 0.0
	control_velocity = Vector3.ZERO
	velocity = Vector3.ZERO
	position.y = 0.0 # a mid-jump top lands instead of hovering
	_has_net_target = false
	if _arrow_tween != null and _arrow_tween.is_valid():
		_arrow_tween.kill()
	_showed_rush_arrow = false
	if _dir_arrow != null:
		_dir_arrow.visible = false
	if _action_trail != null:
		_action_trail.emitting = false


func motion_velocity() -> Vector3:
	return velocity + control_velocity


func launch(dir: Vector3, effectiveness: float) -> void:
	if not dir.is_finite() or not is_finite(effectiveness):
		return
	effectiveness = clampf(effectiveness, 0.0, 1.0)
	launch_spin = maxf(effectiveness * spin_reserve, 3.0)
	spin = launch_spin
	energy = 100.0 * effectiveness
	velocity = _flat_direction(dir) * (2.2 + 2.8 * effectiveness)
	control_velocity = Vector3.ZERO
	dash_cd = 0.0
	jump_cd = 0.0
	nudge_cd = 0.0
	dash_time = 0.0
	jump_time = 0.0
	rushing = false
	_steering = false
	battling = true
	alive = true
	round_over = false
	pending_elimination = ""
	_launch_time = 0.2
	scale = Vector3(0.55, 0.55, 0.55)
	position.y = 1.1
	if is_inside_tree():
		var tw: Tween = create_tween()
		tw.tween_property(self, "scale", Vector3.ONE, 0.28).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func apply_hit(push_dir: Vector3, impulse: float, spin_penalty: float) -> void:
	if not _can_act() or not push_dir.is_finite() or not is_finite(impulse) or not is_finite(spin_penalty):
		return
	velocity += _flat_direction(push_dir) * maxf(impulse, 0.0)
	spin = maxf(spin - maxf(spin_penalty, 0.0), 0.0)
	flash_accent()


func flash_accent() -> void:
	if _accent_mat == null:
		return
	if _flash_tween != null and _flash_tween.is_valid():
		_flash_tween.kill()
	if not is_inside_tree():
		_accent_mat.emission_energy_multiplier = _accent_base # tweens never step outside the tree
		return
	_flash_tween = create_tween()
	_flash_tween.tween_property(_accent_mat, "emission_energy_multiplier", 5.5, 0.06)
	_flash_tween.tween_property(_accent_mat, "emission_energy_multiplier", _accent_base, 0.4)


func die(reason: String) -> void:
	if not alive:
		return
	alive = false
	battling = false
	rushing = false
	dash_time = 0.0
	jump_time = 0.0
	if _highlight != null:
		_highlight.visible = false
	if _dir_arrow != null:
		_dir_arrow.visible = false
	if _trail != null:
		_trail.emitting = false
	if _action_trail != null:
		_action_trail.emitting = false
	if _slot_label != null:
		_slot_label.hide()
	if _visual == null or not is_inside_tree():
		queue_free()
		return
	_visual.position.y = 0.0
	_spawn_dust()
	# Both branches add up to DIE_SECONDS.
	var tw: Tween = create_tween()
	var shrink: float = 0.25
	if reason == "topple":
		# Tip over toward where it was heading, bounce on the floor, rest, then vanish.
		var dir: Vector3 = _flat_direction(motion_velocity())
		if dir == Vector3.ZERO:
			var ang: float = randf() * TAU
			dir = Vector3(cos(ang), 0.0, sin(ang))
		var axis: Vector3 = Vector3.UP.cross(dir).normalized()
		var lean: Basis = _visual.basis
		tw.set_parallel(true)
		tw.tween_method(func(a: float) -> void: _visual.basis = Basis(axis, a) * lean, 0.0, deg_to_rad(86.0), 0.5) \
			.set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
		tw.tween_property(self, "position:y", 0.04, 0.5)
		tw.set_parallel(false)
		tw.tween_interval(0.25)
	else:
		# Ring-out: arc up over the rim, tumbling, then drop out of the arena.
		if _shadow != null:
			_shadow.hide()
		var out_dir: Vector3 = Vector3(position.x, 0.0, position.z)
		out_dir = out_dir.normalized() if out_dir.length() > 0.01 else Vector3.FORWARD
		var goal: Vector3 = position + out_dir * 1.9
		shrink = 0.3
		tw.set_parallel(true)
		tw.tween_property(self, "position:x", goal.x, 0.55).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(self, "position:z", goal.z, 0.55).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(self, "position:y", 0.7, 0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(self, "position:y", -1.2, 0.45).from(0.7).set_delay(0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.tween_property(_visual, "rotation", _visual.rotation + Vector3(1.5 * PI, 0.0, 0.5 * PI), 0.7).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.set_parallel(false)
	tw.tween_property(self, "scale", Vector3(0.02, 0.02, 0.02), shrink).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_callback(queue_free)


func _spawn_dust() -> void:
	# One-shot puff parented beside the top so it outlives the queue_free.
	var parent: Node = get_parent()
	if parent == null or not is_inside_tree():
		return
	var puff: CPUParticles3D = CPUParticles3D.new()
	puff.one_shot = true
	puff.explosiveness = 0.9
	puff.amount = 18
	puff.lifetime = 0.7
	puff.direction = Vector3.UP
	puff.spread = 75.0
	puff.initial_velocity_min = 0.5
	puff.initial_velocity_max = 1.4
	puff.gravity = Vector3(0.0, -1.2, 0.0)
	puff.damping_min = 1.5
	puff.damping_max = 2.5
	puff.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	puff.emission_sphere_radius = radius * 0.6
	puff.scale_amount_min = 0.8
	puff.scale_amount_max = 1.6
	var fade: Curve = Curve.new()
	fade.add_point(Vector2(0.0, 1.0))
	fade.add_point(Vector2(1.0, 0.0))
	puff.scale_amount_curve = fade
	var ramp: Gradient = Gradient.new()
	ramp.set_color(0, Color(0.78, 0.64, 0.45, 0.85))
	ramp.set_color(1, Color(0.55, 0.42, 0.28, 0.0))
	puff.color_ramp = ramp
	var ball: SphereMesh = SphereMesh.new()
	ball.radius = 0.07
	ball.height = 0.14
	ball.radial_segments = 8
	ball.rings = 4
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ball.material = mat
	puff.mesh = ball
	puff.position = position + Vector3(0.0, 0.1, 0.0)
	parent.add_child(puff)
	puff.emitting = true
	get_tree().create_timer(puff.lifetime + 0.3).timeout.connect(puff.queue_free)


func snapshot() -> Dictionary:
	return {
		"owner_id": owner_id, "slot_id": slot_id, "level": level,
		"position": position, "velocity": velocity, "control_velocity": control_velocity,
		"spin": spin, "launch_spin": launch_spin, "energy": energy, "wobble": wobble,
		"dash_cd": dash_cd, "jump_cd": jump_cd, "nudge_cd": nudge_cd,
		"dash_time": dash_time, "jump_time": jump_time, "rushing": rushing,
		"rush_direction": rush_direction, "alive": alive, "battling": battling,
		"pending_elimination": pending_elimination,
	}


func apply_snapshot(data: Dictionary) -> void:
	# Only the match authority sends snapshots; reject malformed vectors before rendering.
	for key: String in ["position", "velocity", "control_velocity", "rush_direction"]:
		var value: Variant = data.get(key)
		if value is Vector3 and value.is_finite():
			if key == "position" and puppet:
				_set_net_target(value)
			else:
				set(key, value)
	for key: String in ["spin", "launch_spin", "energy", "wobble", "dash_cd", "jump_cd", "nudge_cd", "dash_time", "jump_time"]:
		var value: Variant = data.get(key)
		if (value is float or value is int) and is_finite(float(value)):
			set(key, maxf(float(value), 0.0))
	energy = minf(energy, 100.0)
	wobble = minf(wobble, 1.0)
	rushing = bool(data.get("rushing", false)) and energy > 0.0
	alive = bool(data.get("alive", alive))
	battling = bool(data.get("battling", battling)) and alive
	pending_elimination = String(data.get("pending_elimination", ""))
	_update_ring()


func _set_net_target(target: Vector3) -> void:
	# Puppets glide toward snapshots in _process. Snap on the first one, on big corrections,
	# and outside the tree (no _process there; checks read the position back immediately).
	if not _has_net_target or not is_inside_tree() or position.distance_to(target) > 1.0:
		position = target
	_net_target = target
	_has_net_target = true


func _tick_actions(delta: float) -> void:
	rush_paid_seconds = 0.0
	dash_cd = maxf(dash_cd - delta, 0.0)
	jump_cd = maxf(jump_cd - delta, 0.0)
	nudge_cd = maxf(nudge_cd - delta, 0.0)
	if dash_time > 0.0:
		dash_time = maxf(dash_time - delta, 0.0)
		control_velocity = _dash_direction * (5.0 if dash_time > 0.0 else MOVE_SPEED)
	elif rushing:
		var paid_time: float = minf(delta, energy / RUSH_COST_PER_SECOND)
		rush_paid_seconds = paid_time
		energy = maxf(energy - RUSH_COST_PER_SECOND * paid_time, 0.0)
		control_velocity = control_velocity.move_toward(rush_direction * RUSH_SPEED, MOVE_ACCELERATION * paid_time)
		if energy <= 0.0:
			rushing = false
	elif not _steering:
		control_velocity = control_velocity.move_toward(Vector3.ZERO, 0.8 * delta)
	_steering = false
	if jump_time > 0.0:
		jump_time = maxf(jump_time - delta, 0.0)
		var progress: float = 1.0 - jump_time / JUMP_DURATION
		position.y = 4.0 * JUMP_HEIGHT * progress * (1.0 - progress)
		if jump_time <= 0.0:
			_land(0.5)
	elif _launch_time > 0.0:
		_launch_time = maxf(_launch_time - delta, 0.0)
		var progress: float = 1.0 - _launch_time / 0.2
		position.y = 1.1 * (1.0 - progress * progress)
		if _launch_time <= 0.0:
			_land(launch_spin / maxf(spin_reserve, 0.001))
	else:
		position.y = 0.0


func _land(strength: float) -> void:
	flash_accent()
	landed.emit(Vector3(position.x, 0.0, position.z), strength)


func _physics_process(delta: float) -> void:
	if puppet:
		return
	if not battling or not alive or round_over or not is_finite(delta) or delta <= 0.0:
		return
	var dash_seconds: float = minf(delta, dash_time)
	_tick_actions(delta)
	spin = maxf(spin - SPIN_DECAY * delta, 0.0)
	var wobble_threshold: float = 0.25 * launch_spin
	var topple_threshold: float = 0.08 * launch_spin
	if spin < wobble_threshold:
		wobble = clampf((wobble_threshold - spin) / maxf(wobble_threshold - topple_threshold, 0.001), 0.0, 1.0)
	else:
		wobble = 0.0
	if wobble > 0.0:
		var drift_ang: float = _rng.randf_range(0.0, TAU)
		velocity += Vector3(cos(drift_ang), 0.0, sin(drift_ang)) * wobble * 2.0 * delta
	velocity = velocity.move_toward(Vector3.ZERO, MOMENTUM_DRAG * delta)
	var motion: Vector3 = motion_velocity()
	var travel: Vector3 = motion * delta
	if dash_seconds > 0.0 and dash_time <= 0.0:
		# The final tick contains both dash speed and normal speed.
		travel += _dash_direction * (5.0 - MOVE_SPEED) * dash_seconds
	position.x += travel.x
	position.z += travel.z
	var flat: Vector2 = Vector2(position.x, position.z)
	var dist: float = flat.length()
	if dist > RING_RADIUS and dist < OUT_RADIUS:
		# ponytail: fake rim — soft radial bounce, a hard hit still climbs over
		var out_dir: Vector3 = Vector3(flat.x, 0.0, flat.y) / dist
		var radial_speed: float = motion.dot(out_dir)
		if radial_speed > 0.0 and radial_speed < RIM_CLIMB_SPEED:
			position.x -= out_dir.x * (dist - RING_RADIUS)
			position.z -= out_dir.z * (dist - RING_RADIUS)
			velocity -= out_dir * radial_speed * 1.5
			if radial_speed > 0.8:
				rim_touched.emit(out_dir * RING_RADIUS, radial_speed)
	if pending_elimination == "":
		if Vector2(position.x, position.z).length() > OUT_RADIUS:
			pending_elimination = "ringout"
		elif spin <= topple_threshold:
			pending_elimination = "topple"


func _process(delta: float) -> void:
	if not alive:
		return
	if puppet and _has_net_target:
		position = position.lerp(_net_target, 1.0 - exp(-18.0 * delta))
	if _shadow != null:
		_shadow.visible = battling
		_shadow.position.y = 0.01 - position.y
		_shadow.scale = Vector3.ONE * (1.0 + maxf(position.y, 0.0) * 0.2)
	if _has_team:
		_update_ring() # selected ring pulses; stays pinned to the floor
	if _slot_label != null:
		_slot_label.visible = battling
		if battling:
			_update_label()
	if _action_trail != null:
		_action_trail.emitting = battling and (rushing or dash_time > 0.0)
	if rushing and _dir_arrow != null:
		_showed_rush_arrow = true
		_dir_arrow.visible = true
		_dir_arrow.scale = Vector3.ONE
		_dir_arrow.rotation.y = atan2(-rush_direction.x, -rush_direction.z)
	elif _showed_rush_arrow and _dir_arrow != null:
		_showed_rush_arrow = false
		_dir_arrow.hide()
	if arcana and _accent_mat != null:
		# rainbow arcana: cycle the accent hue; runs on puppets too (cosmetic only)
		_hue = wrapf(_hue + delta * 0.35, 0.0, 1.0)
		var c: Color = Color.from_hsv(_hue, 0.85, 1.0)
		_accent_mat.albedo_color = c
		_accent_mat.emission = c
		if _trail != null:
			_trail.emitting = battling and spin > 1.0
	var idle_rate: float = 0.0 if inspection_mode else (14.0 if _showcase else 1.2)
	var visual_rate: float = spin * 0.4 if battling else idle_rate
	_spin_angle = wrapf(_spin_angle + visual_rate * delta, 0.0, TAU)
	if _spin_node != null:
		_spin_node.rotation.y = _spin_angle
	if battling:
		# Precession speeds up toward topple; a near-dead top also shudders.
		_lean_phase += (3.0 + wobble * 14.0) * delta
		var lean_max: float = deg_to_rad(34.0) * (1.3 - balance / 100.0)
		var lean: float = wobble * lean_max
		_visual.rotation.x = lean * sin(_lean_phase)
		_visual.rotation.z = lean * cos(_lean_phase)
		_visual.position.y = randf_range(-0.01, 0.01) if wobble > 0.7 else 0.0
	elif _showcase and not inspection_mode:
		_lean_phase += 2.2 * delta
		var tilt: float = deg_to_rad(7.0)
		_visual.rotation.x = tilt * sin(_lean_phase)
		_visual.rotation.z = tilt * cos(_lean_phase)


func _update_label() -> void:
	var pct: int = clampi(roundi(100.0 * spin / maxf(spin_reserve, 0.001)), 0, 100)
	if pct != _label_pct:
		_label_pct = pct
		_slot_label.text = ("%d · %d%%" % [slot_id + 1, pct]) if is_local else ("%d%%" % pct)
	var tint: Color = team_color if _has_team else accent_color
	# the alarm must contrast with the label: red on gold/teal/violet, cream on a crimson or pink one
	var red_label: bool = Vector3(tint.r, tint.g, tint.b).distance_to(Vector3(DANGER_COLOR.r, DANGER_COLOR.g, DANGER_COLOR.b)) < 0.35
	var alarm: Color = HT.TEXT_COLOR if red_label else DANGER_COLOR
	var flat: Vector3 = Vector3(position.x, 0.0, position.z)
	if flat.length() > 3.5 and motion_velocity().dot(flat.normalized()) > 0.3:
		tint = alarm # heading out over the rim
	elif wobble > 0.0:
		tint = tint.lerp(alarm, 0.5 + 0.5 * sin(_lean_phase))
	_slot_label.modulate = tint


static func run_action_checks() -> bool:
	# Runnable without a scene: load("res://gasing.gd").run_action_checks().
	var top: Gasing = Gasing.new()
	top.launch(Vector3.FORWARD, 0.75)
	assert(is_equal_approx(top.energy, 75.0))
	assert(top.nudge(Vector3.RIGHT) and not top.nudge(Vector3.RIGHT))
	assert(is_equal_approx(top.energy, 75.0))
	top.velocity = Vector3(7.0, 0.0, 0.0)
	top.steer(Vector3.FORWARD, 0.1)
	assert(is_equal_approx(top.velocity.x, 7.0), "Steering must preserve collision momentum")
	var moving: Vector3 = top.motion_velocity()
	top.cancel_control()
	top.cancel_control()
	assert(top.motion_velocity().is_equal_approx(moving), "Selection changes preserve coasting momentum")
	var coasting: Gasing = Gasing.new()
	coasting.launch(Vector3.FORWARD, 1.0)
	coasting.velocity = Vector3.ZERO
	assert(coasting.nudge(Vector3.FORWARD))
	for i: int in 30:
		coasting.cancel_control()
		coasting.steer(Vector3.FORWARD, 1.0 / 60.0)
		assert(coasting.motion_velocity().is_equal_approx(Vector3.FORWARD * MOVE_SPEED), "Reselecting cannot invent momentum")
	coasting.free()
	assert(top.dash(Vector3.FORWARD) and not top.dash(Vector3.FORWARD))
	assert(is_equal_approx(top.energy, 55.0))
	top.cancel_control()
	top._tick_actions(DASH_DURATION)
	assert(top.motion_velocity().is_equal_approx(Vector3(7.0, 0.0, -MOVE_SPEED)) and top.dash_time <= 0.0)
	top._tick_actions(0.1)
	assert(top.jump() and not top.jump())
	assert(is_equal_approx(top.energy, 30.0))
	top._tick_actions(JUMP_DURATION * 0.5)
	assert(is_equal_approx(top.position.y, JUMP_HEIGHT))
	top._tick_actions(JUMP_DURATION * 0.5)
	assert(is_zero_approx(top.position.y))
	top.energy = 1.0
	top.set_rush(true, Vector3.FORWARD)
	top._tick_actions(0.1)
	assert(is_zero_approx(top.energy) and not top.rushing)
	assert(is_equal_approx(top.rush_paid_seconds, 0.05))
	top._tick_actions(0.1)
	assert(is_zero_approx(top.rush_paid_seconds))
	assert(not top.dash(Vector3(INF, 0.0, 0.0)))
	for step: float in [0.1, 0.25]:
		top.launch(Vector3.FORWARD, 1.0)
		top.set_rush(true, Vector3.FORWARD)
		for i: int in int(round(1.0 / step)):
			top._tick_actions(step)
		assert(is_equal_approx(top.energy, 80.0), "Rush cost must use elapsed seconds")
	var dash_distances: Array[float] = []
	for step: float in [0.01, 0.05]:
		top.position = Vector3.ZERO
		top.launch(Vector3.FORWARD, 1.0)
		top.velocity = Vector3.ZERO
		assert(top.dash(Vector3.FORWARD))
		for i: int in int(round(0.2 / step)):
			top._physics_process(step)
		dash_distances.append(absf(top.position.z))
		assert(absf(absf(top.position.z) - 0.944) < 0.001, "Dash must keep its final partial tick")
		assert(is_equal_approx(top.energy, 80.0) and is_equal_approx(top.dash_cd, 0.8))
	assert(absf(dash_distances[0] - dash_distances[1]) < 0.001)
	top.launch(Vector3.FORWARD, 1.0)
	top.velocity = Vector3.ZERO
	for i: int in 55:
		top.position = Vector3.ZERO
		top.velocity = Vector3.ZERO
		top._physics_process(1.0)
	assert(top.pending_elimination.is_empty())
	for i: int in 2:
		top.position = Vector3.ZERO
		top.velocity = Vector3.ZERO
		top._physics_process(1.0)
	assert(top.pending_elimination == "topple", "Perfect Jantung should last about 56 seconds")
	top.puppet = true
	var saved: Dictionary = top.snapshot()
	top._physics_process(2.0)
	assert(top.snapshot() == saved and not top.jump(), "Puppets never run local combat")
	top.apply_snapshot({"position": Vector3(1.0, 0.0, 2.0)})
	assert(top.position == Vector3(1.0, 0.0, 2.0), "Out-of-tree puppets snap straight to snapshots")
	top.free()
	var ender: Gasing = Gasing.new()
	var landings: Array[float] = []
	ender.landed.connect(func(_point: Vector3, strength: float) -> void: landings.append(strength))
	ender.launch(Vector3.FORWARD, 0.8)
	ender._tick_actions(0.2)
	assert(landings.size() == 1 and is_equal_approx(landings[0], 0.8), "Launch landing reports its strength")
	assert(ender.dash(Vector3.RIGHT) and ender.dash_time > 0.0)
	ender.rushing = true
	ender.end_round()
	assert(ender.dash_time == 0.0 and not ender.rushing and ender.control_velocity == Vector3.ZERO)
	ender.energy = 100.0
	ender.dash_cd = 0.0
	ender.nudge_cd = 0.0
	assert(not ender.dash(Vector3.RIGHT) and not ender.jump() and not ender.nudge(Vector3.RIGHT), "A decided round refuses every action")
	assert(ender.alive and ender.battling, "A decided round keeps the top spinning on screen")
	ender.set_team(Color.CRIMSON, true)
	ender.set_selected(true)
	ender.set_showcase(true)
	assert(ender.team_color == Color.CRIMSON and ender.is_local, "Team and showcase setters are scene-free safe")
	ender._accent_mat = StandardMaterial3D.new()
	ender._accent_base = 1.2
	ender.flash_accent()
	assert(is_equal_approx(ender._accent_mat.emission_energy_multiplier, 1.2), "Flash settles on the stored base glow (arcana keeps 1.2)")
	ender.free()
	return true
