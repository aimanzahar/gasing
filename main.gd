extends Node3D

enum State { READY, CRAFT, WIND, LAUNCH, BATTLE, ROUND_OVER, OVER }

const GASING_SCENE: PackedScene = preload("res://gasing.tscn")
const PLAYER_COLOR: Color = Color(1.0, 0.78, 0.25)
const FOE_COLOR: Color = Color(0.2, 0.85, 0.8)
const TEXT_COLOR: Color = Color(0.96, 0.9, 0.78)
const PANEL_BG: Color = Color(0.11, 0.06, 0.035, 0.94)

const BASE_SHAPES: Dictionary = {
	"jantung": {"label": "Gasing Jantung", "mass": 2.4, "spin_reserve": 70.0, "balance": 60.0},
	"uri": {"label": "Gasing Uri", "mass": 1.4, "spin_reserve": 105.0, "balance": 78.0},
}
const MATERIAL_DEFS: Dictionary = {
	"merbau": {"label": "Kayu Merbau", "mass": 0.3, "balance": 0.0},
	"kemuning": {"label": "Kayu Kemuning", "mass": 0.0, "balance": 7.0},
	"besi": {"label": "Teras Besi", "mass": 0.5, "balance": 0.0},
}
const OPPONENTS: Array[Dictionary] = [
	{"name": "Pak Din", "shape": "uri", "mass": 1.5, "spin_reserve": 88.0, "balance": 66.0, "wind_mean": 72.0, "wind_dev": 14.0, "aggressive": false},
	{"name": "Cik Ros", "shape": "jantung", "mass": 2.2, "spin_reserve": 70.0, "balance": 62.0, "wind_mean": 82.0, "wind_dev": 9.0, "aggressive": true},
	{"name": "Tok Gayong", "shape": "jantung", "mass": 2.7, "spin_reserve": 76.0, "balance": 68.0, "wind_mean": 86.0, "wind_dev": 6.0, "aggressive": true},
	{"name": "Datuk Pangkah", "shape": "jantung", "mass": 2.9, "spin_reserve": 82.0, "balance": 74.0, "wind_mean": 90.0, "wind_dev": 3.5, "aggressive": true},
]

const STRINGS: Dictionary = {
	"en": {
		"heritage": "A Malay heritage game — wind your top, strike your rival, rule the ring.",
		"fact": "Did you know? Gasing is a heritage sport of Kelantan and Melaka.",
		"prompt": "Press SPACE to begin",
		"wind_hint": "Hold SPACE / left mouse to wind the cord — release in the GREEN zone!  (A/D to aim)",
		"bench": "CRAFTING BENCH",
		"duel_line": "Duel %d / %d  —  Opponent: %s",
		"craft_duel_line": "Duel %d / %d  —  Next opponent: %s",
		"mats_line": "Materials:  Merbau %d  ·  Kemuning %d  ·  Besi %d",
		"mats_hint": "Materials — click to forge onto the selected gasing:",
		"pick_info": "Pick your gasing for this duel.",
		"selected_info": "%s selected.",
		"no_mat": "No %s — win duels to earn materials!",
		"forged": "%s forged onto %s!",
		"fight": "FIGHT!",
		"round_win": "YOU WIN!",
		"round_lose": "%s wins this duel...",
		"awarded": "Materials earned: ",
		"round_out": "Your gasing is out.",
		"over_win": "CHAMPION OF THE GELANGGANG!",
		"over_lose": "DEFEATED...",
		"duels_won": "Duels won: %d / %d",
		"restart": "RESTART RUN",
		"or_space": "(or press SPACE)",
		"you": "You",
		"gauge_you": "YOU",
		"gauge_foe": "RIVAL",
		"toast_snap": "CORD SNAPPED!",
		"toast_topple": "%s TOPPLED!",
		"toast_ringout": "%s RING OUT!",
		"toast_double": "Both toppled at once!",
		"role_jantung": "Striker — knock rivals out",
		"role_uri": "Spinner — outlast rivals",
		"desc_merbau": "+0.3 mass",
		"desc_kemuning": "+7 balance",
		"desc_besi": "+0.5 mass, harder pangkah",
		"stat_mass": "Mass",
		"stat_spin": "Spin",
		"stat_balance": "Balance",
		"meter": "WIND",
		"tip_merbau": "Merbau — dense heartwood.\n+0.3 Mass: your strikes shove rivals harder\nand this top resists knockback.",
		"tip_kemuning": "Kemuning — fine golden wood.\n+7 Balance: wobbles later as spin fades\nand resists toppling when struck.",
		"tip_besi": "Besi — a heavy iron core.\n+0.5 Mass: much harder pangkah strikes.",
	},
	"ms": {
		"heritage": "Permainan warisan Melayu — pusing gasingmu, pangkah lawan, jadi juara gelanggang.",
		"fact": "Tahu tak? Gasing ialah sukan warisan di Kelantan dan Melaka.",
		"prompt": "Tekan SPACE untuk mula",
		"wind_hint": "Tahan SPACE / tetikus kiri untuk memusing tali — lepas dalam zon HIJAU!  (A/D untuk sasaran)",
		"bench": "BENGKEL GASING",
		"duel_line": "Duel %d / %d  —  Lawan: %s",
		"craft_duel_line": "Duel %d / %d  —  Lawan seterusnya: %s",
		"mats_line": "Bahan:  Merbau %d  ·  Kemuning %d  ·  Besi %d",
		"mats_hint": "Bahan kraf — klik untuk tempa pada gasing terpilih:",
		"pick_info": "Pilih gasing untuk duel ini.",
		"selected_info": "%s dipilih.",
		"no_mat": "Tiada %s — menang duel untuk dapat bahan!",
		"forged": "%s ditempa pada %s!",
		"fight": "MULA LAWAN!",
		"round_win": "KAMU MENANG!",
		"round_lose": "%s menang duel ini...",
		"awarded": "Bahan diperoleh: ",
		"round_out": "Gasing kamu tersingkir.",
		"over_win": "JUARA GELANGGANG!",
		"over_lose": "TEWAS...",
		"duels_won": "Duel dimenangi: %d / %d",
		"restart": "MULA SEMULA",
		"or_space": "(atau tekan SPACE)",
		"you": "Kamu",
		"gauge_you": "KAMU",
		"gauge_foe": "LAWAN",
		"toast_snap": "TALI PUTUS!",
		"toast_topple": "%s TUMBANG!",
		"toast_ringout": "%s KELUAR GELANGGANG!",
		"toast_double": "Kedua-dua tumbang serentak!",
		"role_jantung": "Pemangkah — tumbangkan lawan",
		"role_uri": "Pemusing — bertahan paling lama",
		"desc_merbau": "+0.3 jisim",
		"desc_kemuning": "+7 imbangan",
		"desc_besi": "+0.5 jisim, pangkah lebih kuat",
		"stat_mass": "Jisim",
		"stat_spin": "Pusingan",
		"stat_balance": "Imbangan",
		"meter": "PUSING",
		"tip_merbau": "Merbau — teras kayu padat.\n+0.3 Jisim: pangkah anda lebih kuat\ndan gasing lebih tahan tolakan.",
		"tip_kemuning": "Kemuning — kayu halus keemasan.\n+7 Imbangan: lambat goyang bila pusingan susut\ndan tahan tumbang bila dipangkah.",
		"tip_besi": "Besi — teras besi berat.\n+0.5 Jisim: pangkah jauh lebih kuat.",
	},
}

var lang: String = "en"
var state: State = State.READY
var player_shapes: Dictionary = {}
var materials_owned: Dictionary = {}
var selected_shape: String = "jantung"
var duel_index: int = 0
var run_won: bool = false
var player_top: Gasing = null
var foe_top: Gasing = null
var wind_power: float = 0.0
var winding: bool = false
var aim_angle: float = 0.0
var hit_cooldown: float = 0.0
var last_striker: String = ""
var last_wind_effectiveness: float = 0.0
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()

var ready_panel: Control = null
var craft_panel: Control = null
var round_panel: Control = null
var over_panel: Control = null
var hud: Control = null
var wind_meter: WindMeter = null
var wind_hint: Label = null
var player_gauge: SpinGauge = null
var foe_gauge: SpinGauge = null
var duel_label: Label = null
var mats_label: Label = null
var ready_heritage: Label = null
var ready_fact: Label = null
var ready_prompt: Label = null
var craft_title: Label = null
var craft_duel_label: Label = null
var craft_mats_hint: Label = null
var craft_info: Label = null
var round_label: Label = null
var award_label: Label = null
var over_title: Label = null
var over_stats: Label = null
var over_hint: Label = null
var fight_button: Button = null
var restart_button: Button = null
var shape_cards: Dictionary = {}
var material_buttons: Dictionary = {}
var lang_buttons: Dictionary = {}

@onready var camera: Camera3D = $Camera3D
@onready var aim_arrow: Node3D = $AimArrow
@onready var burst: CPUParticles3D = $HitBurst
@onready var ui: CanvasLayer = $UI


func _ready() -> void:
	_rng.randomize()
	aim_arrow.visible = false
	_configure_burst()
	_build_ui()
	_reset_run()
	_apply_language()
	_enter_state(State.READY)


func _t(key: String) -> String:
	return STRINGS[lang][key]


# ---------------------------------------------------------------- state flow

func _enter_state(next: State) -> void:
	state = next
	match next:
		State.READY:
			_clear_tops()
			_set_hud_visible(false)
			_show_panel(ready_panel)
		State.CRAFT:
			_clear_tops()
			_set_hud_visible(false)
			_refresh_craft()
			_show_panel(craft_panel)
		State.WIND:
			_show_panel(null)
			_set_hud_visible(true)
			player_gauge.visible = false
			foe_gauge.visible = false
			wind_meter.visible = true
			wind_hint.visible = true
			wind_power = 0.0
			wind_meter.power = 0.0
			wind_meter.shown = 0.0
			winding = false
			aim_angle = 0.0
			aim_arrow.rotation.y = 0.0
			aim_arrow.visible = true
			player_top = _spawn_top(true)
			player_top.set_winding(true)
			_update_top_bar()
		State.LAUNCH:
			wind_meter.visible = false
			wind_hint.visible = false
			aim_arrow.visible = false
			_do_launch()
		State.BATTLE:
			player_gauge.visible = true
			foe_gauge.visible = true
		State.ROUND_OVER:
			pass
		State.OVER:
			_clear_tops()
			_set_hud_visible(false)
			_show_panel(over_panel)


func _unhandled_input(event: InputEvent) -> void:
	match state:
		State.READY:
			if _is_advance_input(event):
				get_viewport().set_input_as_handled()
				_enter_state(State.CRAFT)
		State.WIND:
			if event.is_action_pressed("wind"):
				winding = true
			elif event.is_action_released("wind") and winding:
				winding = false
				_enter_state(State.LAUNCH)
			elif event is InputEventMouseMotion and winding:
				var motion: InputEventMouseMotion = event
				aim_angle = clampf(aim_angle - motion.relative.x * 0.003, -1.1, 1.1)
		State.OVER:
			if event.is_action_pressed("ui_accept"):
				_restart_run()


func _is_advance_input(event: InputEvent) -> bool:
	if event.is_action_pressed("ui_accept"):
		return true
	var mb: InputEventMouseButton = event as InputEventMouseButton
	return mb != null and mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT


func _physics_process(delta: float) -> void:
	if state == State.WIND:
		var turn: float = Input.get_axis("aim_left", "aim_right")
		aim_angle = clampf(aim_angle - turn * 1.5 * delta, -1.1, 1.1)
		aim_arrow.rotation.y = aim_angle
		if winding:
			wind_power = minf(wind_power + 55.0 * delta, 100.0)
		wind_meter.power = wind_power
		return
	if state != State.BATTLE:
		return
	hit_cooldown = maxf(hit_cooldown - delta, 0.0)
	var p_ok: bool = is_instance_valid(player_top) and player_top.alive
	var f_ok: bool = is_instance_valid(foe_top) and foe_top.alive
	if p_ok and f_ok:
		_ai_nudge(delta)
		_check_collision()
	_update_gauges()
	_resolve_eliminations()


# ---------------------------------------------------------------- launch

func _wind_effectiveness(power: float) -> float:
	if power > 95.0:
		return 0.15
	if power < 40.0:
		return 0.25 + 0.05 * (power / 40.0)
	if power < 80.0:
		return 0.3 + 0.65 * ((power - 40.0) / 40.0)
	return 0.95 + 0.05 * ((power - 80.0) / 15.0)


func _spawn_top(is_player: bool) -> Gasing:
	var g: Gasing = GASING_SCENE.instantiate() as Gasing
	g.name = "PlayerTop" if is_player else "FoeTop"
	add_child(g)
	if is_player:
		g.setup(_t("you"), selected_shape, player_shapes[selected_shape], PLAYER_COLOR)
		g.position = Vector3(0.0, 0.0, 3.0)
	else:
		var opp: Dictionary = OPPONENTS[duel_index]
		g.setup(opp.name, opp.shape, opp, FOE_COLOR)
		g.position = Vector3(0.0, 0.0, -3.0)
	return g


func _do_launch() -> void:
	last_wind_effectiveness = _wind_effectiveness(wind_power)
	var dir: Vector3 = Vector3.FORWARD.rotated(Vector3.UP, aim_angle)
	player_top.set_winding(false)
	player_top.launch(dir, last_wind_effectiveness)
	if wind_power > 95.0:
		_toast(_t("toast_snap"), Color(1.0, 0.35, 0.25), Vector3(0.0, 0.5, 3.0), true)
	foe_top = _spawn_top(false)
	var opp: Dictionary = OPPONENTS[duel_index]
	var foe_wind: float = clampf(_rng.randfn(opp.wind_mean, opp.wind_dev), 5.0, 100.0)
	var foe_eff: float = _wind_effectiveness(foe_wind)
	var foe_dir: Vector3 = Vector3.BACK.rotated(Vector3.UP, _rng.randf_range(-0.25, 0.25))
	foe_top.launch(foe_dir, foe_eff)
	last_striker = ""
	hit_cooldown = 0.0
	_enter_state(State.BATTLE)


# ---------------------------------------------------------------- battle

func _ai_nudge(delta: float) -> void:
	var opp: Dictionary = OPPONENTS[duel_index]
	var target: Vector3 = player_top.position if opp.aggressive else Vector3.ZERO
	var to_target: Vector3 = target - foe_top.position
	to_target.y = 0.0
	if to_target.length() > 0.2:
		# nudge must beat the 0.8 friction decel or the AI can never move once parked
		var strength: float = 1.6 if opp.aggressive else 0.95
		foe_top.velocity += to_target.normalized() * strength * delta


func _check_collision() -> void:
	# ponytail: exactly two tops -> plain distance check is the overlap query
	var diff: Vector3 = foe_top.position - player_top.position
	diff.y = 0.0
	var min_d: float = player_top.radius + foe_top.radius
	if diff.length() >= min_d or hit_cooldown > 0.0:
		return
	hit_cooldown = 0.3
	var dir: Vector3 = diff.normalized() if diff.length() > 0.001 else Vector3.FORWARD
	var imp_on_foe: float = 0.02 * player_top.spin * (player_top.mass / foe_top.mass)
	var imp_on_player: float = 0.02 * foe_top.spin * (foe_top.mass / player_top.mass)
	foe_top.apply_hit(dir, imp_on_foe, imp_on_foe * 2.5)
	player_top.apply_hit(-dir, imp_on_player, imp_on_player * 2.5)
	var overlap: float = min_d - diff.length()
	foe_top.position += dir * overlap * 0.5
	player_top.position -= dir * overlap * 0.5
	last_striker = "player" if imp_on_foe >= imp_on_player else "foe"
	var contact: Vector3 = player_top.position + dir * player_top.radius
	_hit_effects(contact, maxf(imp_on_foe, imp_on_player))


func _hit_effects(contact: Vector3, strength: float) -> void:
	burst.global_position = contact + Vector3(0.0, 0.35, 0.0)
	burst.restart()
	_camera_nudge()
	if strength > 1.6:
		_toast("PANGKAH!", Color(1.0, 0.55, 0.15), contact, true)


func _update_gauges() -> void:
	if is_instance_valid(player_top):
		player_gauge.frac = player_top.spin / maxf(player_top.spin_reserve, 1.0)
		player_gauge.wobbling = player_top.alive and player_top.wobble > 0.0
	if is_instance_valid(foe_top):
		foe_gauge.frac = foe_top.spin / maxf(foe_top.spin_reserve, 1.0)
		foe_gauge.wobbling = foe_top.alive and foe_top.wobble > 0.0


func _resolve_eliminations() -> void:
	var p_reason: String = ""
	var f_reason: String = ""
	if is_instance_valid(player_top) and player_top.alive:
		p_reason = player_top.pending_elimination
	if is_instance_valid(foe_top) and foe_top.alive:
		f_reason = foe_top.pending_elimination
	if p_reason == "" and f_reason == "":
		return
	var player_wins: bool = false
	if p_reason != "" and f_reason != "":
		if absf(player_top.spin - foe_top.spin) < 0.0001:
			player_wins = last_striker != "player"
		else:
			player_wins = player_top.spin > foe_top.spin
		_toast(_t("toast_double"), TEXT_COLOR, Vector3.ZERO, false)
		player_top.die(p_reason)
		foe_top.die(f_reason)
	elif f_reason != "":
		player_wins = true
		_toast_elimination(foe_top, f_reason)
		foe_top.die(f_reason)
	else:
		player_wins = false
		_toast_elimination(player_top, p_reason)
		player_top.die(p_reason)
	_finish_duel(player_wins)


func _toast_elimination(top: Gasing, reason: String) -> void:
	var template: String = _t("toast_ringout") if reason == "ringout" else _t("toast_topple")
	_toast(template % top.display_name, Color(1.0, 0.45, 0.3), top.position, false)


func _finish_duel(player_wins: bool) -> void:
	state = State.ROUND_OVER
	player_gauge.wobbling = false
	foe_gauge.wobbling = false
	var opp: Dictionary = OPPONENTS[duel_index]
	if player_wins:
		round_label.text = _t("round_win")
		round_label.add_theme_color_override("font_color", PLAYER_COLOR)
		var award_count: int = _rng.randi_range(1, 2)
		var awarded: Array[String] = []
		var keys: Array = MATERIAL_DEFS.keys()
		for i: int in award_count:
			var pick: String = keys[_rng.randi_range(0, keys.size() - 1)]
			materials_owned[pick] += 1
			awarded.append(String(MATERIAL_DEFS[pick].label))
		award_label.text = _t("awarded") + ", ".join(awarded)
		duel_index += 1
		_update_top_bar()
	else:
		round_label.text = _t("round_lose") % opp.name
		round_label.add_theme_color_override("font_color", FOE_COLOR)
		award_label.text = _t("round_out")
	_show_panel(round_panel)
	get_tree().create_timer(2.4).timeout.connect(_after_round.bind(player_wins))


func _after_round(player_wins: bool) -> void:
	if state != State.ROUND_OVER:
		return
	if not player_wins:
		_finish_run(false)
	elif duel_index >= OPPONENTS.size():
		_finish_run(true)
	else:
		_enter_state(State.CRAFT)


func _finish_run(won: bool) -> void:
	run_won = won
	over_title.text = _t("over_win") if won else _t("over_lose")
	over_title.add_theme_color_override("font_color", PLAYER_COLOR if won else Color(1.0, 0.45, 0.3))
	over_stats.text = _t("duels_won") % [duel_index, OPPONENTS.size()]
	_enter_state(State.OVER)


# ---------------------------------------------------------------- run / craft

func _reset_run() -> void:
	player_shapes = {}
	for id: String in BASE_SHAPES:
		var src: Dictionary = BASE_SHAPES[id]
		player_shapes[id] = {"mass": src.mass, "spin_reserve": src.spin_reserve, "balance": src.balance}
	materials_owned = {"merbau": 0, "kemuning": 0, "besi": 0}
	duel_index = 0
	selected_shape = "jantung"
	run_won = false
	last_striker = ""


func _restart_run() -> void:
	_reset_run()
	_enter_state(State.CRAFT)


func _on_restart_pressed() -> void:
	_restart_run()


func _on_fight_pressed() -> void:
	_enter_state(State.WIND)


func _on_lang_pressed(code: String) -> void:
	lang = code
	_apply_language()


func _on_shape_selected(id: String) -> void:
	selected_shape = id
	craft_info.text = _t("selected_info") % BASE_SHAPES[id].label
	_refresh_craft()


func _on_material_pressed(mat_id: String) -> void:
	var def: Dictionary = MATERIAL_DEFS[mat_id]
	if materials_owned.get(mat_id, 0) <= 0:
		craft_info.text = _t("no_mat") % def.label
		return
	materials_owned[mat_id] -= 1
	var stats: Dictionary = player_shapes[selected_shape]
	stats.mass = clampf(stats.mass + def.mass, 1.4, 3.0)
	stats.balance = clampf(stats.balance + def.balance, 55.0, 85.0)
	craft_info.text = _t("forged") % [def.label, BASE_SHAPES[selected_shape].label]
	_refresh_craft()


func _clear_tops() -> void:
	if is_instance_valid(player_top):
		player_top.queue_free()
	if is_instance_valid(foe_top):
		foe_top.queue_free()
	player_top = null
	foe_top = null


# ---------------------------------------------------------------- effects

func _configure_burst() -> void:
	burst.emitting = false
	burst.one_shot = true
	burst.amount = 26
	burst.lifetime = 0.45
	burst.explosiveness = 1.0
	burst.direction = Vector3.UP
	burst.spread = 180.0
	burst.initial_velocity_min = 2.0
	burst.initial_velocity_max = 4.5
	burst.gravity = Vector3(0.0, -9.0, 0.0)
	burst.scale_amount_min = 0.6
	burst.scale_amount_max = 1.0
	var m: SphereMesh = SphereMesh.new()
	m.radius = 0.05
	m.height = 0.1
	burst.mesh = m
	burst.color = Color(1.0, 0.85, 0.4)


func _camera_nudge() -> void:
	var tw: Tween = create_tween()
	tw.tween_property(camera, "v_offset", 0.18, 0.05)
	tw.tween_property(camera, "v_offset", 0.0, 0.2)


func _toast(text: String, color: Color, world_pos: Vector3, big: bool) -> void:
	var l: Label = _mk_label(text, 40 if big else 24, color)
	l.size = Vector2(500.0, 50.0)
	l.pivot_offset = Vector2(250.0, 25.0)
	var screen: Vector2 = camera.unproject_position(world_pos + Vector3(0.0, 0.8, 0.0))
	l.position = screen - Vector2(250.0, 25.0)
	l.z_index = 10
	l.scale = Vector2(0.6, 0.6)
	hud.add_child(l)
	var tw: Tween = create_tween()
	tw.set_parallel(true)
	tw.tween_property(l, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(l, "position:y", l.position.y - 70.0, 1.0)
	tw.tween_property(l, "modulate:a", 0.0, 0.55).set_delay(0.45)
	tw.chain().tween_callback(l.queue_free)


# ---------------------------------------------------------------- UI build

func _set_hud_visible(v: bool) -> void:
	hud.visible = v


func _show_panel(target: Control) -> void:
	for panel: Control in [ready_panel, craft_panel, round_panel, over_panel]:
		if panel == null:
			continue
		if panel == target:
			panel.visible = true
			panel.modulate.a = 0.0
			var tw: Tween = create_tween()
			tw.tween_property(panel, "modulate:a", 1.0, 0.25)
		elif panel.visible:
			var tw2: Tween = create_tween()
			tw2.tween_property(panel, "modulate:a", 0.0, 0.15)
			tw2.tween_callback(panel.hide)


func _update_top_bar() -> void:
	var opp: Dictionary = OPPONENTS[mini(duel_index, OPPONENTS.size() - 1)]
	duel_label.text = _t("duel_line") % [mini(duel_index + 1, OPPONENTS.size()), OPPONENTS.size(), opp.name]
	mats_label.text = _t("mats_line") % [materials_owned.merbau, materials_owned.kemuning, materials_owned.besi]


func _apply_language() -> void:
	ready_heritage.text = _t("heritage")
	ready_fact.text = _t("fact")
	ready_prompt.text = _t("prompt")
	wind_hint.text = _t("wind_hint")
	wind_meter.label_text = _t("meter")
	player_gauge.title = _t("gauge_you")
	foe_gauge.title = _t("gauge_foe")
	craft_title.text = _t("bench")
	craft_mats_hint.text = _t("mats_hint")
	craft_info.text = _t("pick_info")
	fight_button.text = _t("fight")
	restart_button.text = _t("restart")
	over_hint.text = _t("or_space")
	for id: String in shape_cards:
		var card: Dictionary = shape_cards[id]
		var role: Label = card.role
		role.text = _t("role_" + id)
		var stat_labels: Array = card.stat_labels
		var names: Array = ["stat_mass", "stat_spin", "stat_balance"]
		for i: int in stat_labels.size():
			var lbl: Label = stat_labels[i]
			lbl.text = _t(names[i])
	for mat_id: String in material_buttons:
		var mb: Button = material_buttons[mat_id]
		mb.tooltip_text = _t("tip_" + mat_id)
	for code: String in lang_buttons:
		var b: Button = lang_buttons[code]
		b.modulate = Color(1.0, 1.0, 1.0, 1.0) if code == lang else Color(0.55, 0.55, 0.55, 1.0)
	_update_top_bar()
	_refresh_craft()


func _mk_label(text: String, font_size: int, color: Color = TEXT_COLOR) -> Label:
	var l: Label = Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _mk_button(text: String, base: Color, light_text: bool = false) -> Button:
	var b: Button = Button.new()
	b.text = text
	b.add_theme_font_size_override("font_size", 17)
	var txt_col: Color = TEXT_COLOR if light_text else Color(0.12, 0.07, 0.03)
	b.add_theme_color_override("font_color", txt_col)
	b.add_theme_color_override("font_hover_color", txt_col)
	b.add_theme_color_override("font_pressed_color", txt_col.darkened(0.2) if not light_text else txt_col)
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = base
	sb.set_corner_radius_all(8)
	sb.content_margin_left = 14.0
	sb.content_margin_right = 14.0
	sb.content_margin_top = 8.0
	sb.content_margin_bottom = 8.0
	b.add_theme_stylebox_override("normal", sb)
	var sb_h: StyleBoxFlat = sb.duplicate()
	sb_h.bg_color = base.lightened(0.18)
	b.add_theme_stylebox_override("hover", sb_h)
	var sb_p: StyleBoxFlat = sb.duplicate()
	sb_p.bg_color = base.darkened(0.28)
	b.add_theme_stylebox_override("pressed", sb_p)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	return b


func _mk_panel_box() -> PanelContainer:
	var p: PanelContainer = PanelContainer.new()
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = PANEL_BG
	sb.set_corner_radius_all(14)
	sb.content_margin_left = 26.0
	sb.content_margin_right = 26.0
	sb.content_margin_top = 20.0
	sb.content_margin_bottom = 20.0
	sb.border_width_bottom = 2
	sb.border_width_top = 2
	sb.border_width_left = 2
	sb.border_width_right = 2
	sb.border_color = Color(0.55, 0.38, 0.16, 0.8)
	p.add_theme_stylebox_override("panel", sb)
	return p


func _mk_fullrect_center() -> CenterContainer:
	var c: CenterContainer = CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.visible = false
	ui.add_child(c)
	return c


func _mk_stat_row(parent: Container, fill_color: Color) -> Dictionary:
	var row: HBoxContainer = HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var lbl: Label = _mk_label("", 13)
	lbl.custom_minimum_size = Vector2(84.0, 0.0)
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	row.add_child(lbl)
	var bar: ProgressBar = ProgressBar.new()
	bar.max_value = 1.0
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(150.0, 14.0)
	bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var bg: StyleBoxFlat = StyleBoxFlat.new()
	bg.bg_color = Color(0.0, 0.0, 0.0, 0.5)
	bg.set_corner_radius_all(4)
	bar.add_theme_stylebox_override("background", bg)
	var fill: StyleBoxFlat = StyleBoxFlat.new()
	fill.bg_color = fill_color
	fill.set_corner_radius_all(4)
	bar.add_theme_stylebox_override("fill", fill)
	row.add_child(bar)
	parent.add_child(row)
	return {"label": lbl, "bar": bar}


func _build_ui() -> void:
	hud = Control.new()
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.visible = false
	ui.add_child(hud)

	var top_bar: HBoxContainer = HBoxContainer.new()
	top_bar.set_anchors_preset(Control.PRESET_TOP_WIDE)
	top_bar.offset_left = 20.0
	top_bar.offset_right = -20.0
	top_bar.offset_top = 12.0
	top_bar.offset_bottom = 170.0
	top_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(top_bar)
	player_gauge = SpinGauge.new()
	player_gauge.ring_color = PLAYER_COLOR
	top_bar.add_child(player_gauge)
	var spacer1: Control = Control.new()
	spacer1.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer1.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top_bar.add_child(spacer1)
	var center_box: VBoxContainer = VBoxContainer.new()
	center_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	duel_label = _mk_label("", 22, PLAYER_COLOR)
	mats_label = _mk_label("", 14)
	center_box.add_child(duel_label)
	center_box.add_child(mats_label)
	top_bar.add_child(center_box)
	var spacer2: Control = Control.new()
	spacer2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top_bar.add_child(spacer2)
	foe_gauge = SpinGauge.new()
	foe_gauge.ring_color = FOE_COLOR
	top_bar.add_child(foe_gauge)

	wind_meter = WindMeter.new()
	wind_meter.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	wind_meter.offset_left = 46.0
	wind_meter.offset_right = 102.0
	wind_meter.offset_top = -320.0
	wind_meter.offset_bottom = -50.0
	wind_meter.visible = false
	hud.add_child(wind_meter)

	wind_hint = _mk_label("", 16)
	wind_hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	wind_hint.offset_left = -420.0
	wind_hint.offset_right = 420.0
	wind_hint.offset_top = -44.0
	wind_hint.offset_bottom = -16.0
	wind_hint.visible = false
	hud.add_child(wind_hint)

	_build_ready_panel()
	_build_craft_panel()
	_build_round_panel()
	_build_over_panel()


func _build_ready_panel() -> void:
	ready_panel = _mk_fullrect_center()
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	ready_panel.add_child(v)
	v.add_child(_mk_label("GASING PANGKAH", 56, PLAYER_COLOR))
	ready_heritage = _mk_label("", 19)
	v.add_child(ready_heritage)
	ready_fact = _mk_label("", 14, Color(0.75, 0.66, 0.52))
	v.add_child(ready_fact)
	ready_prompt = _mk_label("", 20, Color(0.95, 0.95, 0.9))
	v.add_child(ready_prompt)
	var lang_row: HBoxContainer = HBoxContainer.new()
	lang_row.add_theme_constant_override("separation", 12)
	lang_row.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(lang_row)
	for entry: Array in [["en", "ENGLISH"], ["ms", "BAHASA MELAYU"]]:
		var code: String = entry[0]
		var b: Button = _mk_button(entry[1], Color(0.3, 0.2, 0.1), true)
		b.pressed.connect(_on_lang_pressed.bind(code))
		lang_row.add_child(b)
		lang_buttons[code] = b
	var pulse: Tween = create_tween().set_loops()
	pulse.tween_property(ready_prompt, "modulate:a", 0.35, 0.7)
	pulse.tween_property(ready_prompt, "modulate:a", 1.0, 0.7)


func _build_craft_panel() -> void:
	craft_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box()
	craft_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	box.add_child(v)
	craft_title = _mk_label("", 30, PLAYER_COLOR)
	v.add_child(craft_title)
	craft_duel_label = _mk_label("", 16)
	v.add_child(craft_duel_label)

	var cards: HBoxContainer = HBoxContainer.new()
	cards.add_theme_constant_override("separation", 16)
	cards.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(cards)
	for id: String in BASE_SHAPES:
		var def: Dictionary = BASE_SHAPES[id]
		var card: PanelContainer = _mk_panel_box()
		cards.add_child(card)
		var cv: VBoxContainer = VBoxContainer.new()
		cv.add_theme_constant_override("separation", 6)
		card.add_child(cv)
		var pick: Button = _mk_button(def.label, Color(0.82, 0.6, 0.24))
		pick.pressed.connect(_on_shape_selected.bind(id))
		cv.add_child(pick)
		var role: Label = _mk_label("", 12, Color(0.78, 0.7, 0.56))
		cv.add_child(role)
		var mass_row: Dictionary = _mk_stat_row(cv, Color(0.85, 0.45, 0.25))
		var spin_row: Dictionary = _mk_stat_row(cv, Color(0.35, 0.75, 0.9))
		var bal_row: Dictionary = _mk_stat_row(cv, Color(0.5, 0.85, 0.4))
		shape_cards[id] = {
			"card": card,
			"pick": pick,
			"role": role,
			"mass": mass_row.bar,
			"spin_reserve": spin_row.bar,
			"balance": bal_row.bar,
			"stat_labels": [mass_row.label, spin_row.label, bal_row.label],
		}

	craft_mats_hint = _mk_label("", 14)
	v.add_child(craft_mats_hint)
	var mats_row: HBoxContainer = HBoxContainer.new()
	mats_row.add_theme_constant_override("separation", 12)
	mats_row.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(mats_row)
	for mat_id: String in MATERIAL_DEFS:
		var mb: Button = _mk_button("", Color(0.3, 0.2, 0.1), true)
		mb.icon = load("res://assets/icon_%s.png" % mat_id)
		mb.add_theme_constant_override("icon_max_width", 44)
		mb.add_theme_constant_override("h_separation", 8)
		mb.pressed.connect(_on_material_pressed.bind(mat_id))
		mats_row.add_child(mb)
		material_buttons[mat_id] = mb

	craft_info = _mk_label("", 14, Color(0.85, 0.8, 0.65))
	v.add_child(craft_info)
	fight_button = _mk_button("", PLAYER_COLOR)
	fight_button.add_theme_font_size_override("font_size", 22)
	fight_button.pressed.connect(_on_fight_pressed)
	var fb_wrap: CenterContainer = CenterContainer.new()
	fb_wrap.add_child(fight_button)
	v.add_child(fb_wrap)


func _build_round_panel() -> void:
	round_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box()
	round_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	box.add_child(v)
	round_label = _mk_label("", 34, PLAYER_COLOR)
	award_label = _mk_label("", 18)
	v.add_child(round_label)
	v.add_child(award_label)


func _build_over_panel() -> void:
	over_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box()
	over_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	box.add_child(v)
	over_title = _mk_label("", 40, PLAYER_COLOR)
	over_stats = _mk_label("", 18)
	v.add_child(over_title)
	v.add_child(over_stats)
	restart_button = _mk_button("", PLAYER_COLOR)
	restart_button.name = "RestartButton"
	restart_button.add_theme_font_size_override("font_size", 20)
	restart_button.pressed.connect(_on_restart_pressed)
	var rb_wrap: CenterContainer = CenterContainer.new()
	rb_wrap.add_child(restart_button)
	v.add_child(rb_wrap)
	over_hint = _mk_label("", 13, Color(0.75, 0.66, 0.52))
	v.add_child(over_hint)


func _refresh_craft() -> void:
	var opp: Dictionary = OPPONENTS[mini(duel_index, OPPONENTS.size() - 1)]
	craft_duel_label.text = _t("craft_duel_line") % [mini(duel_index + 1, OPPONENTS.size()), OPPONENTS.size(), opp.name]
	for mat_id: String in MATERIAL_DEFS:
		var mb: Button = material_buttons[mat_id]
		var def: Dictionary = MATERIAL_DEFS[mat_id]
		mb.text = "%s ×%d\n%s" % [def.label, materials_owned.get(mat_id, 0), _t("desc_" + mat_id)]
	for id: String in shape_cards:
		var card: Dictionary = shape_cards[id]
		var stats: Dictionary = player_shapes[id]
		_tween_bar(card.mass, (stats.mass - 1.4) / 1.6)
		_tween_bar(card.spin_reserve, (stats.spin_reserve - 60.0) / 50.0)
		_tween_bar(card.balance, (stats.balance - 55.0) / 30.0)
		var panel: PanelContainer = card.card
		panel.modulate = Color(1.0, 1.0, 1.0, 1.0) if id == selected_shape else Color(0.68, 0.68, 0.68, 1.0)
		var pick: Button = card.pick
		var prefix: String = "> " if id == selected_shape else ""
		pick.text = prefix + String(BASE_SHAPES[id].label)


func _tween_bar(bar: ProgressBar, value: float) -> void:
	var tw: Tween = create_tween()
	tw.tween_property(bar, "value", clampf(value, 0.0, 1.0), 0.35).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


# ---------------------------------------------------------------- widgets

class SpinGauge:
	extends Control

	var frac: float = 1.0
	var shown: float = 1.0
	var ring_color: Color = Color.WHITE
	var title: String = ""
	var wobbling: bool = false
	var _flash: float = 0.0

	func _ready() -> void:
		custom_minimum_size = Vector2(110.0, 134.0)
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _process(delta: float) -> void:
		shown = lerpf(shown, frac, minf(8.0 * delta, 1.0))
		if wobbling:
			_flash = wrapf(_flash + delta * 7.0, 0.0, TAU)
		queue_redraw()

	func _draw() -> void:
		var c: Vector2 = Vector2(size.x / 2.0, size.x / 2.0)
		var r: float = size.x / 2.0 - 10.0
		draw_arc(c, r, 0.0, TAU, 40, Color(1.0, 1.0, 1.0, 0.12), 8.0, true)
		var col: Color = ring_color
		if wobbling:
			col = ring_color.lerp(Color(1.0, 0.3, 0.2), 0.5 + 0.5 * sin(_flash))
		if shown > 0.004:
			draw_arc(c, r, -PI / 2.0, -PI / 2.0 + TAU * clampf(shown, 0.0, 1.0), 40, col, 8.0, true)
		var f: Font = get_theme_default_font()
		draw_string(f, Vector2(0.0, c.y + 7.0), str(int(round(shown * 100.0))), HORIZONTAL_ALIGNMENT_CENTER, size.x, 20, col)
		draw_string(f, Vector2(0.0, size.x + 18.0), title, HORIZONTAL_ALIGNMENT_CENTER, size.x, 14, Color(0.96, 0.9, 0.78))


class WindMeter:
	extends Control

	var power: float = 0.0
	var shown: float = 0.0
	var label_text: String = "WIND"

	func _ready() -> void:
		custom_minimum_size = Vector2(56.0, 270.0)
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _process(delta: float) -> void:
		shown = lerpf(shown, power, minf(10.0 * delta, 1.0))
		queue_redraw()

	func _y(v: float) -> float:
		return size.y * (1.0 - v / 100.0)

	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.0, 0.0, 0.0, 0.55), true)
		draw_rect(Rect2(Vector2(0.0, _y(80.0)), Vector2(size.x, _y(40.0) - _y(80.0))), Color(0.9, 0.7, 0.2, 0.25), true)
		draw_rect(Rect2(Vector2(0.0, _y(95.0)), Vector2(size.x, _y(80.0) - _y(95.0))), Color(0.2, 0.9, 0.3, 0.45), true)
		draw_rect(Rect2(Vector2.ZERO, Vector2(size.x, _y(95.0))), Color(0.95, 0.2, 0.15, 0.45), true)
		var col: Color = Color(0.55, 0.6, 0.75)
		if shown > 95.0:
			col = Color(1.0, 0.25, 0.2)
		elif shown >= 80.0:
			col = Color(0.25, 0.95, 0.35)
		elif shown >= 40.0:
			col = Color(0.95, 0.75, 0.25)
		var fill_top: float = _y(shown)
		draw_rect(Rect2(Vector2(4.0, fill_top), Vector2(size.x - 8.0, size.y - fill_top)), col, true)
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.96, 0.9, 0.78, 0.8), false, 2.0)
		var f: Font = get_theme_default_font()
		draw_string(f, Vector2(0.0, -10.0), label_text, HORIZONTAL_ALIGNMENT_CENTER, size.x, 13, Color(0.96, 0.9, 0.78))
