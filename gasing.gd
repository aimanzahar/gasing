class_name Gasing
extends Node3D

signal eliminated(reason: String)

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
	_accent_mat.emission_energy_multiplier = 0.5 # painted lacquer trim, not neon (flash spikes on hit)
	if _mesh != null:
		_mesh.set_surface_override_material(0, _body_mat)
		if _mesh.mesh != null and _mesh.mesh.get_surface_count() > 1:
			_mesh.set_surface_override_material(1, _accent_mat)
	_build_dir_arrow()
	var hl_mat: StandardMaterial3D = StandardMaterial3D.new()
	hl_mat.albedo_color = accent_color
	hl_mat.emission_enabled = true
	hl_mat.emission = accent_color
	hl_mat.emission_energy_multiplier = 2.2
	_highlight.set_surface_override_material(0, hl_mat)
	if arcana:
		_build_arcana()
	_build_level_bands()
	_build_action_visuals()


func _build_level_bands() -> void:
	# Each earned level adds a visible lacquer band; no extra asset variants needed.
	if _mesh == null or _mesh.mesh == null:
		return
	var vertices: PackedVector3Array = _mesh.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	for i: int in range(level - 1):
		var height: float = _mesh.get_aabb().end.y * (0.25 + float(i) * 0.1)
		var below: Vector2 = Vector2(-INF, 0.0)
		var above: Vector2 = Vector2(INF, 0.0)
		# The imported tops are lathed meshes; interpolate their actual side profile.
		for v: Vector3 in vertices:
			var width: float = Vector2(v.x, v.z).length()
			if v.y <= height and v.y >= below.x:
				below = Vector2(v.y, maxf(width, below.y) if is_equal_approx(v.y, below.x) else width)
			if v.y >= height and v.y <= above.x:
				above = Vector2(v.y, maxf(width, above.y) if is_equal_approx(v.y, above.x) else width)
		var band_radius: float = radius
		if is_finite(below.x) and is_finite(above.x):
			band_radius = lerpf(below.y, above.y, (height - below.x) / maxf(above.x - below.x, 0.001))
		var band: MeshInstance3D = MeshInstance3D.new()
		var ring: TorusMesh = TorusMesh.new()
		ring.inner_radius = maxf(band_radius - 0.005, 0.005)
		ring.outer_radius = band_radius + 0.025
		band.mesh = ring
		band.material_override = _accent_mat
		band.position.y = height
		_visual.add_child(band)


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
		_slot_label.position.y = 0.85
		_slot_label.font_size = 46
		_slot_label.pixel_size = 0.004
		_slot_label.outline_size = 10
		_slot_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_slot_label.no_depth_test = true
		add_child(_slot_label)
	_slot_label.modulate = accent_color
	_slot_label.visible = battling


func _build_arcana() -> void:
	_accent_mat.emission_energy_multiplier = 1.2
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


func _wood_grain_normal() -> NoiseTexture2D:
	var n: FastNoiseLite = FastNoiseLite.new()
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = 0.9
	var t: NoiseTexture2D = NoiseTexture2D.new()
	t.noise = n
	t.seamless = true
	t.as_normal_map = true
	t.bump_strength = 1.1
	return t


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
	if _highlight != null:
		_highlight.visible = on or _selected


func set_selected(on: bool) -> void:
	_selected = on
	if _highlight != null:
		_highlight.visible = alive and (on or _winding)


func set_inspect_rotation(yaw: float, pitch: float) -> void:
	if not is_finite(yaw) or not is_finite(pitch) or _visual == null:
		return
	inspection_mode = true
	_visual.rotation = Vector3(clampf(pitch, -1.1, 1.1), yaw, 0.0)


func _can_act() -> bool:
	return alive and battling and not puppet and pending_elimination.is_empty() \
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
	var tw: Tween = create_tween()
	tw.tween_property(_accent_mat, "emission_energy_multiplier", 5.5, 0.06)
	tw.tween_property(_accent_mat, "emission_energy_multiplier", 0.5, 0.4)


func die(reason: String) -> void:
	if not alive:
		return
	alive = false
	battling = false
	rushing = false
	dash_time = 0.0
	jump_time = 0.0
	_highlight.visible = false
	if _dir_arrow != null:
		_dir_arrow.visible = false
	if _trail != null:
		_trail.emitting = false
	if _action_trail != null:
		_action_trail.emitting = false
	if _slot_label != null:
		_slot_label.hide()
	var tw: Tween = create_tween()
	if reason == "topple":
		var fall: Vector3 = _visual.rotation
		fall.x = deg_to_rad(86.0)
		tw.set_parallel(true)
		tw.tween_property(_visual, "rotation", fall, 0.55).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
		tw.tween_property(self, "position:y", 0.04, 0.55)
		tw.set_parallel(false)
		tw.tween_interval(0.35)
	else:
		var out_dir: Vector3 = Vector3(position.x, 0.0, position.z)
		out_dir = out_dir.normalized() if out_dir.length() > 0.01 else Vector3.FORWARD
		tw.set_parallel(true)
		tw.tween_property(self, "position", position + out_dir * 1.7, 0.45).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(self, "position:y", -0.9, 0.5).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.set_parallel(false)
	tw.tween_property(self, "scale", Vector3(0.02, 0.02, 0.02), 0.3).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_callback(queue_free)
	eliminated.emit(reason)


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
	if _highlight != null:
		_highlight.visible = alive and (_selected or _winding)


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
	elif _launch_time > 0.0:
		_launch_time = maxf(_launch_time - delta, 0.0)
		var progress: float = 1.0 - _launch_time / 0.2
		position.y = 1.1 * (1.0 - progress * progress)
	else:
		position.y = 0.0


func _physics_process(delta: float) -> void:
	if puppet:
		return
	if not battling or not alive or not is_finite(delta) or delta <= 0.0:
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
	if pending_elimination == "":
		if Vector2(position.x, position.z).length() > OUT_RADIUS:
			pending_elimination = "ringout"
		elif spin <= topple_threshold:
			pending_elimination = "topple"


func _process(delta: float) -> void:
	if not alive:
		return
	if _shadow != null:
		_shadow.visible = battling
		_shadow.position.y = 0.01 - position.y
		_shadow.scale = Vector3.ONE * (1.0 + maxf(position.y, 0.0) * 0.2)
	if _slot_label != null:
		_slot_label.visible = battling
		_slot_label.text = "[%d]  Lv.%d" % [slot_id + 1, level]
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
	var visual_rate: float = spin * 0.4 if battling else (0.0 if inspection_mode else 1.2)
	_spin_angle = wrapf(_spin_angle + visual_rate * delta, 0.0, TAU)
	if _spin_node != null:
		_spin_node.rotation.y = _spin_angle
	if battling:
		_lean_phase += (1.5 + spin * 0.05) * delta
		var lean_max: float = deg_to_rad(34.0) * (1.3 - balance / 100.0)
		var lean: float = wobble * lean_max
		_visual.rotation.x = lean * sin(_lean_phase)
		_visual.rotation.z = lean * cos(_lean_phase)


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
	top.free()
	return true
