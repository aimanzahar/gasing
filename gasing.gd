class_name Gasing
extends Node3D

signal eliminated(reason: String)

const RING_RADIUS: float = 4.0
const OUT_RADIUS: float = 4.2
const RIM_CLIMB_SPEED: float = 1.7

var display_name: String = "Gasing"
var shape_id: String = "jantung"
var mesh_id: String = "jantung"
var mass: float = 2.4
var spin_reserve: float = 70.0
var balance: float = 60.0
var radius: float = 0.44
var accent_color: Color = Color(1.0, 0.8, 0.25)

var puppet: bool = false # remote-controlled: net snapshots drive x/z/spin/wobble; die() is RPC-driven
var spin: float = 0.0
var launch_spin: float = 1.0
var velocity: Vector3 = Vector3.ZERO
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
	accent_color = p_accent
	mesh_id = String(stats.get("mesh", p_shape))
	radius = 0.56 if shape_id == "uri" else 0.44
	_rng.randomize()
	_build_visual()


func _build_visual() -> void:
	for child: Node in _visual.get_children():
		child.queue_free()
	var packed: PackedScene = load("res://assets/gasing_%s.glb" % mesh_id)
	var inst: Node3D = packed.instantiate() as Node3D
	_visual.add_child(inst)
	_spin_node = inst
	_mesh = _find_mesh(inst)
	_body_mat = StandardMaterial3D.new()
	_body_mat.albedo_color = Color(0.42, 0.24, 0.11)
	_body_mat.roughness = 0.62
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
	_highlight.visible = on


func launch(dir: Vector3, effectiveness: float) -> void:
	launch_spin = maxf(effectiveness * spin_reserve, 3.0)
	spin = launch_spin
	velocity = dir.normalized() * (2.2 + 2.8 * effectiveness)
	battling = true
	alive = true
	pending_elimination = ""
	scale = Vector3(0.55, 0.55, 0.55)
	position.y = 1.1
	var tw: Tween = create_tween()
	tw.set_parallel(true)
	tw.tween_property(self, "scale", Vector3.ONE, 0.28).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(self, "position:y", 0.0, 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)


func apply_hit(push_dir: Vector3, impulse: float, spin_penalty: float) -> void:
	velocity += push_dir.normalized() * impulse
	spin = maxf(spin - spin_penalty, 0.0)
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
	_highlight.visible = false
	if _dir_arrow != null:
		_dir_arrow.visible = false
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


func _physics_process(delta: float) -> void:
	if puppet:
		return
	if not battling or not alive:
		return
	var decay: float = 6.0 * (75.0 / spin_reserve)
	spin = maxf(spin - decay * delta, 0.0)
	var wobble_threshold: float = 0.25 * launch_spin
	var topple_threshold: float = 0.08 * launch_spin
	if spin < wobble_threshold:
		wobble = clampf((wobble_threshold - spin) / maxf(wobble_threshold - topple_threshold, 0.001), 0.0, 1.0)
	else:
		wobble = 0.0
	if wobble > 0.0:
		var drift_ang: float = _rng.randf_range(0.0, TAU)
		velocity += Vector3(cos(drift_ang), 0.0, sin(drift_ang)) * wobble * 2.0 * delta
	velocity = velocity.move_toward(Vector3.ZERO, 0.8 * delta)
	position.x += velocity.x * delta
	position.z += velocity.z * delta
	var flat: Vector2 = Vector2(position.x, position.z)
	var dist: float = flat.length()
	if dist > RING_RADIUS and dist < OUT_RADIUS:
		# ponytail: fake rim — soft radial bounce, a hard hit still climbs over
		var out_dir: Vector3 = Vector3(flat.x, 0.0, flat.y) / dist
		var radial_speed: float = velocity.dot(out_dir)
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
	var visual_rate: float = spin * 0.4 if battling else 1.2
	_spin_angle = wrapf(_spin_angle + visual_rate * delta, 0.0, TAU)
	if _spin_node != null:
		_spin_node.rotation.y = _spin_angle
	if battling:
		_lean_phase += (1.5 + spin * 0.05) * delta
		var lean_max: float = deg_to_rad(34.0) * (1.3 - balance / 100.0)
		var lean: float = wobble * lean_max
		_visual.rotation.x = lean * sin(_lean_phase)
		_visual.rotation.z = lean * cos(_lean_phase)
