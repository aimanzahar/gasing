extends Node
## One arena simulation for solo squads and host-authoritative FFA.

const TOP_SCENE: PackedScene = preload("res://gasing.tscn")
const ROUND_SECONDS: float = 90.0
const DEPLOY_AT: Array[float] = [0.0, 30.0, 45.0]
const COLORS: Array[Color] = [Color(1, 0.78, 0.25), Color(0.2, 0.85, 0.8), Color(0.95, 0.38, 0.5), Color(0.58, 0.55, 1)]
const SNAPSHOT_KEYS: Array[String] = ["position", "velocity", "control_velocity", "spin", "energy", "wobble", "dash_cd", "jump_cd", "nudge_cd", "dash_time", "jump_time", "rushing", "rush_direction", "launch_spin"]
enum Phase { IDLE, WIND, BATTLE, RESULT, OVER }

var game: Node
var phase: Phase = Phase.IDLE
var participants: Dictionary = {}
var roster: Dictionary = {}
var scores: Dictionary = {}
var ready_configs: Dictionary = {}
var winds: Dictionary = {}
var rematches: Dictionary = {}
var disconnected: Array[int] = []
var round_id: int = 0
var elapsed: float = 0.0
var wind_elapsed: float = 0.0
var selected_slot: int = 0
var charge_active: bool = false
var charge_power: float = 0.0
var aim_angle: float = 0.0
var initial_sent: bool = false
var pair_cooldowns: Dictionary = {}
var snapshot_cd: float = 0.0
var input_cd: float = 0.0
var input_seq: int = 0
var ai_cd: float = 0.0
var ai_deploy_cd: float = 0.0
var rush_fx_cd: float = 0.0
var applied_result: int = -1
var cards: HBoxContainer
var score_label: Label
var clock_label: Label
var start_button: Button
var lobby_roster: Label
var slot_buttons: Array[Button] = []
var spin_bars: Array[ProgressBar] = []
var energy_bars: Array[ProgressBar] = []
var ai_charge_slot: int = -1
var ai_charge_power: float = 0.0
var bot_clock: float = 0.0
var bot_rounds: int = 0


func _ready() -> void:
	_setup_actions()


func tr_text(en: String, ms: String) -> String:
	return ms if game.lang == "ms" else en


func my_id() -> int:
	return multiplayer.get_unique_id() if game.net_active else 1


func authority() -> bool:
	return not game.net_active or multiplayer.is_server()


func _setup_actions() -> void:
	var keys: Dictionary = {"arena_left": [KEY_A, KEY_LEFT], "arena_right": [KEY_D, KEY_RIGHT],
		"arena_up": [KEY_W, KEY_UP], "arena_down": [KEY_S, KEY_DOWN], "arena_dash": [KEY_SHIFT],
		"arena_rush": [KEY_E], "arena_jump": [KEY_SPACE]}
	for action: String in keys:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
			for key: int in keys[action]:
				var ev: InputEventKey = InputEventKey.new()
				ev.keycode = key
				InputMap.action_add_event(action, ev)


func build_ui() -> void:
	game.wind_hint.offset_left = -580
	game.wind_hint.offset_right = 580
	game.wind_hint.offset_top = -182
	game.wind_hint.offset_bottom = -150
	cards = HBoxContainer.new()
	cards.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	cards.offset_left = 210
	cards.offset_right = -210
	cards.offset_top = -136
	cards.offset_bottom = -64
	cards.add_theme_constant_override("separation", 10)
	game.hud.add_child(cards)
	for slot: int in 3:
		var column: VBoxContainer = VBoxContainer.new()
		column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		cards.add_child(column)
		var b: Button = game._mk_button("", game.WOOD_DARK, true)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.add_theme_font_size_override("font_size", 14)
		b.pressed.connect(select_slot.bind(slot))
		column.add_child(b)
		slot_buttons.append(b)
		for energy_bar: bool in [false, true]:
			var bar: ProgressBar = ProgressBar.new()
			bar.custom_minimum_size.y = 7
			bar.show_percentage = false
			bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
			var fill: StyleBoxFlat = StyleBoxFlat.new()
			fill.bg_color = Color(0.25, 0.8, 1.0) if energy_bar else COLORS[0]
			bar.add_theme_stylebox_override("fill", fill)
			column.add_child(bar)
			if energy_bar:
				energy_bars.append(bar)
			else:
				spin_bars.append(bar)
	score_label = game._mk_label("", 17)
	score_label.set_anchors_preset(Control.PRESET_TOP_WIDE)
	score_label.offset_top = 70
	score_label.offset_bottom = 96
	score_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.hud.add_child(score_label)
	clock_label = game._mk_label("", 20)
	clock_label.set_anchors_preset(Control.PRESET_TOP_WIDE)
	clock_label.offset_top = 98
	clock_label.offset_bottom = 126
	clock_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.hud.add_child(clock_label)
	var box: Node = game.wait_panel.get_child(0).get_child(0)
	lobby_roster = game._mk_label("", 17)
	box.add_child(lobby_roster)
	start_button = game._mk_button("START FFA", game.PLAYER_COLOR)
	start_button.pressed.connect(start_lobby)
	box.add_child(start_button)
	refresh_lobby()


func refresh_lobby() -> void:
	if not is_instance_valid(start_button):
		return
	start_button.visible = Online.is_host
	start_button.disabled = Online.players.size() < 2 or Online.players.size() > 4
	start_button.text = tr_text("START FFA", "MULA FFA")
	var names: Array[String] = []
	for pd: PlayerData in Online.players.values():
		names.append(pd.display_name)
	lobby_roster.text = "%d / 4\n%s" % [names.size(), "\n".join(names)]
	if not Online.is_host:
		lobby_roster.text += "\n" + tr_text("Waiting for host to start", "Menunggu host memulakan game")


func start_lobby() -> void:
	if not Online.is_host or Online.players.size() < 2 or Online.players.size() > 4:
		return
	var names: Dictionary = {}
	for pd: PlayerData in Online.players.values():
		names[pd.multiplayer_id] = pd.display_name
	Online.set_match_locked(true)
	_start_match.rpc(names, round_id + 1)


@rpc("authority", "call_local", "reliable")
func _start_match(names: Dictionary, baseline: int) -> void:
	round_id = baseline
	applied_result = -1
	roster = names.duplicate()
	disconnected.clear()
	scores.clear()
	ready_configs.clear()
	rematches.clear()
	for id: int in roster:
		scores[id] = 0
	game.net_active = true
	game.net_ended = false
	game.endless_mode = false
	game.net_rematch_sent = false
	game.net_match_mats = {}
	game.net_bonus_text = ""
	game._reset_run()
	game._enter_state(game.State.CRAFT)
	if game._netbot:
		print("netbot: start players=", roster.size())


func local_config() -> Dictionary:
	var entries: Array = []
	for style: String in game.loadout:
		entries.append({"style": style, "level": game._style_level(style)})
	return {"slots": entries}


func sanitize_config(cfg: Dictionary) -> Dictionary:
	var entries: Array = []
	var raw: Variant = cfg.get("slots", [])
	for i: int in 3:
		var item: Dictionary = {}
		if raw is Array and i < raw.size() and raw[i] is Dictionary:
			item = raw[i]
		var style: String = str(item.get("style", "jantung"))
		if not game.STYLE_DEFS.has(style):
			style = "jantung"
		var lev: Variant = item.get("level", 1)
		var level: int = clampi(int(lev), 1, 5) if (lev is int or lev is float) and is_finite(float(lev)) else 1
		var stats: Dictionary = game.STYLE_DEFS[style].duplicate()
		stats.level = level
		entries.append({"style": style, "stats": stats})
	return {"slots": entries}


func submit_loadout() -> void:
	if game.net_ready_sent:
		return
	game.net_ready_sent = true
	game.fight_button.disabled = true
	game.craft_info.text = game._t("waiting")
	if authority():
		_accept_ready(my_id(), local_config())
	else:
		_ready_config.rpc_id(1, round_id, local_config())


@rpc("any_peer", "reliable")
func _ready_config(previous_round: int, cfg: Dictionary) -> void:
	if not authority() or previous_round != round_id:
		return
	_accept_ready(multiplayer.get_remote_sender_id(), cfg)


func _accept_ready(id: int, cfg: Dictionary) -> void:
	if game.state != game.State.CRAFT or not roster.has(id) or disconnected.has(id) or ready_configs.has(id):
		return
	ready_configs[id] = sanitize_config(cfg)
	_ready_status.rpc(ready_configs.keys())
	_check_all_ready()


@rpc("authority", "call_local", "reliable")
func _ready_status(ids: Array) -> void:
	game.craft_opp_status.visible = true
	game.craft_opp_status.text = tr_text("Ready: %d / %d", "Sedia: %d / %d") % [ids.size(), connected_ids().size()]


func _check_all_ready() -> void:
	if not authority() or game.state != game.State.CRAFT:
		return
	for id: int in connected_ids():
		if not ready_configs.has(id):
			return
	_prepare_round.rpc(round_id + 1, ready_configs)


@rpc("authority", "call_local", "reliable")
func _prepare_round(next_id: int, configs: Dictionary) -> void:
	if next_id <= round_id:
		return
	round_id = next_id
	_build_participants(configs)
	ready_configs.clear()
	game._enter_state(game.State.WIND)


func _build_participants(configs: Dictionary) -> void:
	clear_tops()
	participants.clear()
	var index: int = 0
	for id: int in configs:
		if disconnected.has(id):
			continue
		var slots: Array = []
		for entry: Dictionary in configs[id].slots:
			slots.append({"style": entry.style, "stats": entry.stats.duplicate(), "state": "reserve", "top": null})
		participants[id] = {"name": roster.get(id, "Player"), "color": COLORS[index % 4], "slots": slots,
			"selected": 0, "grace": -1.0, "move": Vector3.ZERO, "aim": Vector3.FORWARD, "rush": false,
			"input_age": 0.0, "seq": -1, "angle": TAU * float(index) / float(configs.size())}
		index += 1


func begin_wind() -> void:
	if not game.net_active:
		round_id += 1
		disconnected.clear()
		var opp: Dictionary = game._current_opponent()
		roster = {1: game._t("you"), 2: opp.name}
		var mine: Array = []
		for style: String in game.loadout:
			mine.append({"style": style, "stats": game._style_battle_stats(style)})
		var enemy: Array = [{"style": str(opp.mesh), "stats": opp.duplicate()}]
		for style: String in ["jantung", "uri"]:
			enemy.append({"style": style, "stats": game.STYLE_DEFS[style].duplicate()})
		_build_participants({1: {"slots": mine}, 2: {"slots": enemy}})
	phase = Phase.WIND
	elapsed = 0.0
	wind_elapsed = 0.0
	selected_slot = 0
	charge_active = false
	charge_power = 0.0
	aim_angle = 0.0
	initial_sent = false
	ai_charge_slot = -1
	winds.clear()
	pair_cooldowns.clear()
	for id: int in participants:
		_make_top(id, 0).set_winding(id == my_id())
	_refresh_selected()
	game.wind_meter.visible = true
	game.wind_hint.visible = true
	game.aim_arrow.visible = true
	update_hud()


func spawn_position(id: int, slot: int) -> Vector3:
	var angle: float = participants[id].angle
	var radial: Vector3 = Vector3(sin(angle), 0.0, cos(angle))
	var tangent: Vector3 = Vector3(radial.z, 0.0, -radial.x)
	return radial * 3.0 + tangent * (float(slot) - 1.0) * 0.45


func _make_top(id: int, slot: int) -> Gasing:
	var entry: Dictionary = participants[id].slots[slot]
	if is_instance_valid(entry.top):
		return entry.top
	var top: Gasing = TOP_SCENE.instantiate() as Gasing
	top.name = "Top_%d_%d" % [id, slot]
	add_child(top)
	top.set_physics_process(false) # Arena advances all tops before resolving contact/results.
	top.owner_id = id
	top.slot_id = slot
	top.puppet = not authority()
	var color: Color = participants[id].color
	if not game.net_active and id == 1:
		color = game._style_accent(entry.style)
	top.setup(participants[id].name, str(entry.stats.get("shape", game.STYLE_DEFS[entry.style].shape)), entry.stats, color)
	top.position = spawn_position(id, slot)
	entry.top = top
	return top


func top_at(id: int, slot: int) -> Gasing:
	if not participants.has(id) or slot < 0 or slot > 2:
		return null
	var top: Variant = participants[id].slots[slot].top
	return top if is_instance_valid(top) else null


func live_tops(id: int = 0) -> Array[Gasing]:
	var result: Array[Gasing] = []
	for owner: int in participants:
		if id != 0 and id != owner:
			continue
		for entry: Dictionary in participants[owner].slots:
			if entry.state == "alive" and is_instance_valid(entry.top) and entry.top.alive:
				result.append(entry.top)
	return result


func reserve_slot(id: int) -> int:
	for slot: int in 3:
		if participants[id].slots[slot].state == "reserve":
			return slot
	return -1


func clear_tops() -> void:
	for child: Node in get_children():
		if child is Gasing:
			child.queue_free()
	for id: int in participants:
		for slot: Dictionary in participants[id].slots:
			slot.top = null
	game.player_top = null
	game.foe_top = null
	charge_active = false
	phase = Phase.IDLE


func reset() -> void:
	clear_tops()
	participants.clear()
	roster.clear()
	scores.clear()
	ready_configs.clear()
	disconnected.clear()
	rematches.clear()
	# Round IDs stay monotonic across rematches to reject delayed packets.


func _flat_cursor() -> Vector3:
	var screen: Vector2 = get_viewport().get_mouse_position()
	var hit: Variant = Plane(Vector3.UP, 0.0).intersects_ray(game.camera.project_ray_origin(screen), game.camera.project_ray_normal(screen))
	return hit if hit != null else Vector3.ZERO


func _aim_dir() -> Vector3:
	var top: Gasing = top_at(my_id(), selected_slot)
	var origin: Vector3 = top.position if is_instance_valid(top) else spawn_position(my_id(), selected_slot)
	var dir: Vector3 = _flat_cursor() - origin
	dir.y = 0
	return dir.normalized() if dir.length() > 0.05 else -spawn_position(my_id(), selected_slot).normalized()


func _move_dir() -> Vector3:
	var move: Vector2 = Input.get_vector("arena_left", "arena_right", "arena_up", "arena_down")
	return Vector3(move.x, 0, move.y)


func handle_input(event: InputEvent) -> void:
	if phase != Phase.WIND and phase != Phase.BATTLE:
		return
	if not participants.has(my_id()):
		return
	if event is InputEventKey and event.pressed and not event.echo:
		var key: int = event.physical_keycode if event.physical_keycode != 0 else event.keycode
		if key >= KEY_1 and key <= KEY_3 and phase == Phase.BATTLE:
			select_slot(key - KEY_1)
			return
		if key == KEY_ESCAPE and charge_active:
			charge_active = false
			charge_power = 0
			return
	var reserve: bool = participants[my_id()].slots[selected_slot].state == "reserve"
	if phase == Phase.WIND or reserve:
		if initial_sent and phase == Phase.WIND:
			return
		if event.is_action_pressed("arena_jump") or (phase == Phase.WIND and event.is_action_pressed("wind")):
			charge_active = true
			charge_power = 0
		elif (event.is_action_released("arena_jump") or (phase == Phase.WIND and event.is_action_released("wind"))) and charge_active:
			charge_active = false
			if phase == Phase.WIND:
				initial_sent = true
				_send_command("wind", {"power": charge_power, "angle": aim_angle})
			else:
				_send_command("deploy", {"power": charge_power, "angle": aim_angle})
		elif event is InputEventMouseMotion and charge_active:
			aim_angle = clampf(aim_angle - event.relative.x * 0.003, -1.1, 1.1)
		return
	if event.is_action_pressed("arena_dash"):
		var dir: Vector3 = _move_dir()
		_send_command("dash", {"dir": dir if dir.length() > 0.05 else _aim_dir()})
	elif event.is_action_pressed("arena_jump"):
		_send_command("jump", {})
	elif event.is_action_released("arena_rush"):
		_send_command("stop", {})
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_send_command("nudge", {"dir": _aim_dir()})
		game._flash_click_marker(_flat_cursor())


func select_slot(slot: int) -> void:
	if phase != Phase.BATTLE or slot < 0 or slot > 2 or not participants.has(my_id()):
		return
	if selected_slot == slot:
		return
	_send_command("stop", {})
	charge_active = false
	charge_power = 0
	aim_angle = 0
	selected_slot = slot
	_send_command("select", {})
	_refresh_selected()


func _refresh_selected() -> void:
	for top: Gasing in live_tops():
		top.set_selected(top.owner_id == my_id() and top.slot_id == selected_slot)
	game.player_top = top_at(my_id(), selected_slot)
	game.foe_top = null
	for top: Gasing in live_tops():
		if top.owner_id != my_id():
			game.foe_top = top
			break


func _send_command(kind: String, data: Dictionary) -> void:
	if authority():
		accept_command(my_id(), round_id, selected_slot, kind, data)
	else:
		_command.rpc_id(1, round_id, selected_slot, kind, data)


@rpc("any_peer", "reliable")
func _command(rid: int, slot: int, kind: String, data: Dictionary) -> void:
	if authority():
		accept_command(multiplayer.get_remote_sender_id(), rid, slot, kind, data)


func finite_dir(value: Variant) -> bool:
	return value is Vector3 and value.is_finite() and value.length_squared() <= 4.0


func accept_command(id: int, rid: int, slot: int, kind: String, data: Dictionary) -> bool:
	if rid != round_id or not participants.has(id) or disconnected.has(id) or slot < 0 or slot > 2:
		return false
	var p: Dictionary = participants[id]
	if kind == "wind" or kind == "deploy":
		var pow: Variant = data.get("power")
		var angle: Variant = data.get("angle")
		if not (pow is float or pow is int) or not (angle is float or angle is int):
			return false
		if not is_finite(float(pow)) or not is_finite(float(angle)) or pow < 0 or pow > 100 or absf(angle) > 1.1:
			return false
		if kind == "wind":
			if phase != Phase.WIND or slot != 0 or winds.has(id):
				return false
			winds[id] = Vector2(pow, angle)
			_try_start_battle()
		else:
			if phase != Phase.BATTLE or p.slots[slot].state != "reserve":
				return false
			deploy(id, slot, pow, angle)
		return true
	if phase != Phase.BATTLE:
		return false
	if kind == "select":
		if slot == p.selected:
			return true
		var old: Gasing = top_at(id, p.selected)
		if is_instance_valid(old):
			old.cancel_control()
		p.selected = slot
		p.move = Vector3.ZERO
		p.rush = false
		return true
	if slot != p.selected:
		return false
	var top: Gasing = top_at(id, slot)
	if not is_instance_valid(top) or not top.battling or not top.alive:
		return false
	match kind:
		"stop":
			p.rush = false
			top.set_rush(false, Vector3.ZERO)
			return true
		"jump":
			return top.jump()
		"dash", "nudge":
			var dir: Variant = data.get("dir")
			if not finite_dir(dir) or dir.length() < 0.05:
				return false
			return top.dash(dir) if kind == "dash" else top.nudge(dir)
	return false


func deploy(id: int, slot: int, power: float, angle: float = 0.0) -> void:
	if game.net_active:
		_deployed.rpc(round_id, id, slot, power, angle)
	else:
		_deployed(round_id, id, slot, power, angle)


@rpc("authority", "call_local", "reliable")
func _deployed(rid: int, id: int, slot: int, power: float, angle: float) -> void:
	if rid != round_id or not participants.has(id) or participants[id].slots[slot].state != "reserve":
		return
	var top: Gasing = _make_top(id, slot)
	participants[id].slots[slot].state = "alive"
	participants[id].grace = -1.0
	top.set_winding(false)
	top.launch((-spawn_position(id, slot)).normalized().rotated(Vector3.UP, angle), game._wind_effectiveness(power))
	game._play_sfx(game.SND_LAUNCH, -7.0, 0.1)
	if id == my_id() and slot == selected_slot:
		charge_active = false
		if power > 95.0:
			game._toast(game._t("toast_snap"), game.DANGER, top.position, true)
	_refresh_selected()
	if game._netbot:
		print("netbot: deployed round=", rid, " owner=", id, " slot=", slot)


func _try_start_battle() -> void:
	if phase != Phase.WIND or not authority():
		return
	if not game.net_active and not winds.has(2):
		var opp: Dictionary = game._current_opponent()
		var floor_power: float = [55.0, 75.0, 85.0][game.difficulty]
		winds[2] = Vector2(clampf(game._rng.randfn(opp.wind_mean, opp.wind_dev), floor_power, 95), game._rng.randf_range(-0.15, 0.15))
	for id: int in participants:
		if not disconnected.has(id) and not winds.has(id):
			return
	if game.net_active:
		_battle_started.rpc(round_id)
	else:
		_battle_started(round_id)
	for id: int in participants:
		if not disconnected.has(id):
			deploy(id, 0, winds[id].x, winds[id].y)


@rpc("authority", "call_local", "reliable")
func _battle_started(rid: int) -> void:
	if rid != round_id:
		return
	phase = Phase.BATTLE
	elapsed = 0
	ai_cd = 0.5
	ai_deploy_cd = 8
	charge_active = false
	game.wind_meter.visible = false
	game.wind_hint.visible = false
	game.aim_arrow.visible = false
	game._enter_state(game.State.BATTLE)


@rpc("any_peer", "call_remote", "unreliable_ordered", 1)
func _input_frame(rid: int, seq: int, slot: int, move: Vector3, aim: Vector3, rush: bool) -> void:
	if authority():
		accept_input(multiplayer.get_remote_sender_id(), rid, seq, slot, move, aim, rush)


func accept_input(id: int, rid: int, seq: int, slot: int, move: Vector3, aim: Vector3, rush: bool) -> bool:
	if phase != Phase.BATTLE or rid != round_id or not participants.has(id) or disconnected.has(id):
		return false
	var p: Dictionary = participants[id]
	if slot != p.selected or seq <= p.seq or not finite_dir(move) or not finite_dir(aim):
		return false
	p.seq = seq
	p.move = Vector3(move.x, 0, move.z).limit_length(1)
	p.aim = Vector3(aim.x, 0, aim.z).normalized()
	p.rush = rush
	p.input_age = 0
	return true


func _physics_process(delta: float) -> void:
	if not is_instance_valid(game):
		return
	if phase == Phase.WIND:
		wind_elapsed += delta
		_update_charge(delta)
		if authority() and wind_elapsed >= 15:
			for id: int in participants:
				if not winds.has(id) and not disconnected.has(id):
					winds[id] = Vector2(55, 0)
			_try_start_battle()
		update_hud()
		return
	if phase != Phase.BATTLE:
		return
	elapsed += delta
	_update_charge(delta)
	input_cd -= delta
	if input_cd <= 0 and participants.has(my_id()):
		input_cd = 0.05
		input_seq += 1
		var move: Vector3 = _move_dir()
		var aim: Vector3 = _aim_dir()
		var rush: bool = Input.is_action_pressed("arena_rush") and not charge_active
		if game._netbot:
			move = Vector3.ZERO
			rush = false
		if authority():
			accept_input(my_id(), round_id, input_seq, selected_slot, move, aim, rush)
		else:
			_input_frame.rpc_id(1, round_id, input_seq, selected_slot, move, aim, rush)
	if authority():
		for id: int in participants:
			var p: Dictionary = participants[id]
			p.input_age += delta
			var top: Gasing = top_at(id, p.selected)
			if not is_instance_valid(top) or not top.battling or not top.alive:
				continue
			if p.input_age > 0.3:
				if p.move != Vector3.ZERO or p.rush:
					top.cancel_control()
				p.move = Vector3.ZERO
				p.rush = false
			elif game.net_active or id == my_id():
				top.steer(p.move, delta)
				top.set_rush(p.rush, p.aim)
		if not game.net_active:
			_ai_tick(delta)
		_reserves_tick(delta)
		for top: Gasing in live_tops():
			top._physics_process(delta)
		collisions(delta)
		resolve_eliminations()
		snapshot_cd -= delta
		if game.net_active and phase == Phase.BATTLE and snapshot_cd <= 0:
			snapshot_cd = 0.05
			var data: Array = []
			var graces: Dictionary = {}
			for id: int in participants:
				graces[id] = participants[id].grace
			for top: Gasing in live_tops():
				var row: Array = [top.owner_id, top.slot_id]
				for key: String in SNAPSHOT_KEYS:
					row.append(top.get(key))
				data.append(row)
			# Three compact states fit below ENet's MTU, even at the 12-top limit.
			for offset: int in range(0, maxi(data.size(), 1), 3):
				_snapshot.rpc(round_id, elapsed, data.slice(offset, offset + 3), graces)
	update_hud()


func _update_charge(delta: float) -> void:
	if not participants.has(my_id()):
		return
	if phase == Phase.WIND or participants[my_id()].slots[selected_slot].state == "reserve":
		aim_angle = clampf(aim_angle - Input.get_axis("aim_left", "aim_right") * 1.5 * delta, -1.1, 1.1)
		if charge_active:
			charge_power = minf(charge_power + 55 * delta, 100)
		game.wind_meter.power = charge_power
		game.aim_arrow.position = spawn_position(my_id(), selected_slot)
		game.aim_arrow.rotation.y = participants[my_id()].angle + aim_angle


@rpc("authority", "call_remote", "unreliable_ordered", 2)
func _snapshot(rid: int, seconds: float, data: Array, graces: Dictionary) -> void:
	if rid != round_id or phase != Phase.BATTLE:
		return
	elapsed = seconds
	for id: int in graces:
		if participants.has(id):
			participants[id].grace = graces[id]
	for item: Array in data:
		var top: Gasing = top_at(item[0], item[1])
		if is_instance_valid(top) and top.alive and top.battling:
			var state: Dictionary = {}
			for index: int in SNAPSHOT_KEYS.size():
				state[SNAPSHOT_KEYS[index]] = item[index + 2]
			top.apply_snapshot(state)


func _reserves_tick(delta: float) -> void:
	for id: int in participants:
		if disconnected.has(id):
			continue
		var p: Dictionary = participants[id]
		for slot: int in range(1, 3):
			if p.slots[slot].state == "reserve" and elapsed >= DEPLOY_AT[slot]:
				deploy(id, slot, 55)
		if live_tops(id).is_empty() and reserve_slot(id) >= 0:
			if p.grace < 0:
				p.grace = 5.0
			else:
				p.grace -= delta
				if p.grace <= 0:
					deploy(id, reserve_slot(id), 55)
		else:
			p.grace = -1.0


func collisions(delta: float) -> void:
	for key: String in pair_cooldowns.keys():
		pair_cooldowns[key] -= delta
		if pair_cooldowns[key] <= 0:
			pair_cooldowns.erase(key)
	rush_fx_cd = maxf(rush_fx_cd - delta, 0)
	var tops: Array[Gasing] = live_tops()
	# ponytail: at most 12 tops / 66 pairs; use a spatial index only for larger arenas.
	for i: int in tops.size():
		for j: int in range(i + 1, tops.size()):
			var a: Gasing = tops[i]
			var b: Gasing = tops[j]
			if absf(a.position.y - b.position.y) > 0.45:
				continue
			var diff: Vector3 = b.position - a.position
			diff.y = 0
			var dist: float = diff.length()
			var contact_dist: float = a.radius + b.radius
			if dist > contact_dist + 0.035:
				continue
			var dir: Vector3 = diff / dist if dist > 0.001 else Vector3.RIGHT
			var overlap: float = maxf(contact_dist - dist, 0)
			a.position -= dir * overlap * 0.5
			b.position += dir * overlap * 0.5
			if a.owner_id == b.owner_id:
				continue
			var a_rush_contact: bool = a.rush_paid_seconds > 0 and a.rush_direction.dot(dir) > 0.5
			var b_rush_contact: bool = b.rush_paid_seconds > 0 and b.rush_direction.dot(-dir) > 0.5
			if a_rush_contact:
				b.spin = maxf(b.spin - 12 * a.rush_paid_seconds, 0)
			if b_rush_contact:
				a.spin = maxf(a.spin - 12 * b.rush_paid_seconds, 0)
			if (a_rush_contact or b_rush_contact) and rush_fx_cd <= 0:
				fx((a.position + b.position) * 0.5, 1.2)
				rush_fx_cd = 0.12
			var key: String = "%s:%s" % [a.name, b.name]
			if pair_cooldowns.has(key):
				continue
			pair_cooldowns[key] = 0.3
			var hit_b: float = minf(0.02 * a.spin * a.mass / b.mass + maxf(a.motion_velocity().dot(dir), 0) * 1.3 * a.mass / b.mass, 2.4)
			var hit_a: float = minf(0.02 * b.spin * b.mass / a.mass + maxf(-b.motion_velocity().dot(dir), 0) * 1.3 * b.mass / a.mass, 2.4)
			a.apply_hit(-dir, hit_a, hit_a * 0.4)
			b.apply_hit(dir, hit_b, hit_b * 0.4)
			fx((a.position + b.position) * 0.5, maxf(hit_a, hit_b))


func fx(point: Vector3, strength: float) -> void:
	game._hit_effects(point, strength)
	if game.net_active:
		_hit_fx.rpc(round_id, point, strength)


@rpc("authority", "unreliable")
func _hit_fx(rid: int, point: Vector3, strength: float) -> void:
	if rid == round_id and phase == Phase.BATTLE:
		game._hit_effects(point, strength)


func resolve_eliminations() -> void:
	for top: Gasing in live_tops():
		var reason: String = top.pending_elimination
		if top.spin <= 0.08 * top.launch_spin:
			reason = "topple"
		if Vector2(top.position.x, top.position.z).length() > top.OUT_RADIUS:
			reason = "ringout"
		if reason != "":
			if game.net_active:
				_eliminated.rpc(round_id, top.owner_id, top.slot_id, reason)
			else:
				_eliminated(round_id, top.owner_id, top.slot_id, reason)
	var remaining: Array[int] = []
	for id: int in participants:
		if not disconnected.has(id) and (not live_tops(id).is_empty() or reserve_slot(id) >= 0):
			remaining.append(id)
	if remaining.size() <= 1:
		finish_round(remaining[0] if remaining.size() == 1 else 0)
	elif elapsed >= ROUND_SECONDS:
		finish_round(timeout_winner())


@rpc("authority", "call_local", "reliable")
func _eliminated(rid: int, id: int, slot: int, reason: String) -> void:
	if rid != round_id or not participants.has(id) or participants[id].slots[slot].state == "out":
		return
	participants[id].slots[slot].state = "out"
	var top: Gasing = top_at(id, slot)
	if is_instance_valid(top):
		game._toast_elimination(top, reason)
		top.die(reason)
	_refresh_selected()


func timeout_winner() -> int:
	var winner: int = 0
	var best_count: int = -1
	var best_spin: float = -1
	for id: int in participants:
		if disconnected.has(id):
			continue
		var living: Array[Gasing] = live_tops(id)
		var total: float = 0
		for top: Gasing in living:
			total += top.spin / top.spin_reserve
		if living.size() > best_count or (living.size() == best_count and total > best_spin + 0.0001):
			winner = id
			best_count = living.size()
			best_spin = total
		elif living.size() == best_count and absf(total - best_spin) <= 0.0001:
			winner = 0
	return winner


func deployed_styles(id: int) -> Array:
	var styles: Array = []
	if participants.has(id):
		for entry: Dictionary in participants[id].slots:
			if entry.state != "reserve" and not styles.has(entry.style):
				styles.append(entry.style)
	return styles


func finish_round(winner: int) -> void:
	if phase != Phase.BATTLE:
		return
	var next_scores: Dictionary = scores.duplicate()
	if winner != 0:
		next_scores[winner] = int(next_scores.get(winner, 0)) + 1
	if game.net_active:
		_result.rpc(round_id, winner, next_scores)
	else:
		_result(round_id, winner, next_scores)


@rpc("authority", "call_local", "reliable")
func _result(rid: int, winner: int, next_scores: Dictionary) -> void:
	if rid != round_id or applied_result == rid:
		return
	applied_result = rid
	phase = Phase.RESULT
	scores = next_scores.duplicate()
	charge_active = false
	for top: Gasing in live_tops():
		top.cancel_control()
		top.battling = false
	game.wind_meter.visible = false
	game.wind_hint.visible = false
	game.aim_arrow.visible = false
	game._award_style_xp(deployed_styles(my_id()), winner == my_id())
	game._save_workshop()
	if game._netbot:
		bot_rounds += 1
		print("netbot: round result rid=", rid, " winner=", winner, " seconds=", elapsed, " scores=", scores)
	game._arena_round_finished(winner)


func connected_ids() -> Array[int]:
	var result: Array[int] = []
	for id: int in roster:
		if not disconnected.has(id):
			result.append(id)
	return result


func after_round() -> void:
	if not authority() or not game.net_active or game.net_ended or phase != Phase.RESULT:
		return
	var winner: int = 0
	for id: int in connected_ids():
		if scores.get(id, 0) >= 3:
			winner = id
	if connected_ids().size() == 1:
		winner = connected_ids()[0]
	if winner != 0:
		_match_over.rpc(winner)
	else:
		_next_round.rpc()


@rpc("authority", "call_local", "reliable")
func _next_round() -> void:
	ready_configs.clear()
	game._enter_state(game.State.CRAFT)


@rpc("authority", "call_local", "reliable")
func _match_over(winner: int) -> void:
	phase = Phase.OVER
	game._arena_match_finished(winner)
	if game._netbot:
		print("netbot: match over winner=", winner)


func request_rematch() -> void:
	if authority():
		_accept_rematch(my_id())
	else:
		_rematch.rpc_id(1, round_id)


@rpc("any_peer", "reliable")
func _rematch(rid: int) -> void:
	if authority() and rid == round_id:
		_accept_rematch(multiplayer.get_remote_sender_id())


func _accept_rematch(id: int) -> void:
	if game.state != game.State.OVER or not roster.has(id) or disconnected.has(id):
		return
	rematches[id] = true
	if connected_ids().size() < 2:
		return
	for peer: int in connected_ids():
		if not rematches.has(peer):
			return
	var names: Dictionary = {}
	for peer: int in connected_ids():
		names[peer] = roster[peer]
	_start_match.rpc(names, round_id + 1)


func peer_left(id: int) -> void:
	refresh_lobby()
	if game.net_active and authority() and roster.has(id) and not disconnected.has(id):
		_forfeit.rpc(round_id, id)
		if phase == Phase.BATTLE:
			resolve_eliminations()
		elif phase == Phase.WIND:
			_try_start_battle()
		elif game.state == game.State.CRAFT:
			_check_all_ready()
		elif game.state == game.State.OVER:
			for peer: int in rematches.keys():
				if not disconnected.has(peer):
					_accept_rematch(peer)
					break


@rpc("authority", "call_local", "reliable")
func _forfeit(rid: int, id: int) -> void:
	if rid != round_id or disconnected.has(id):
		return
	disconnected.append(id)
	ready_configs.erase(id)
	if participants.has(id):
		for slot: int in 3:
			_eliminated(rid, id, slot, "ringout")
	if game._netbot:
		print("netbot: forfeit owner=", id)


func _ai_tick(delta: float) -> void:
	if not participants.has(2):
		return
	var p: Dictionary = participants[2]
	var own: Array[Gasing] = live_tops(2)
	var enemies: Array[Gasing] = live_tops(1)
	ai_deploy_cd -= delta
	if ai_charge_slot >= 0:
		if p.slots[ai_charge_slot].state != "reserve":
			ai_charge_slot = -1
		else:
			ai_charge_power += 55 * delta
			if ai_charge_power >= [72.0, 85.0, 93.0][game.difficulty]:
				deploy(2, ai_charge_slot, [72.0, 85.0, 93.0][game.difficulty])
				ai_charge_slot = -1
			return
	if reserve_slot(2) >= 0 and (own.is_empty() or (ai_deploy_cd <= 0 and (own.size() < enemies.size() or elapsed > 18))):
		var previous: Gasing = top_at(2, p.selected)
		if is_instance_valid(previous):
			previous.cancel_control()
		ai_charge_slot = reserve_slot(2)
		ai_charge_power = 0
		p.selected = ai_charge_slot
		p.move = Vector3.ZERO
		p.rush = false
		ai_deploy_cd = [13.0, 9.0, 6.0][game.difficulty]
		return
	if own.is_empty():
		return
	ai_cd -= delta
	if ai_cd <= 0:
		ai_cd = maxf([0.65, 0.4, 0.22][game.difficulty] - 0.015 * game.duel_index, 0.15)
		var chosen: Gasing = own[0]
		var danger: float = -1
		for candidate: Gasing in own:
			var dist: float = Vector2(candidate.position.x, candidate.position.z).length()
			var urgency: float = dist if dist > 2.7 else candidate.energy * 0.02
			if urgency > danger:
				chosen = candidate
				danger = urgency
		if p.selected != chosen.slot_id:
			var old: Gasing = top_at(2, p.selected)
			if is_instance_valid(old):
				old.cancel_control()
			p.selected = chosen.slot_id
		var target: Gasing = null
		var distance: float = INF
		for enemy: Gasing in enemies:
			var d: float = chosen.position.distance_to(enemy.position)
			if d < distance:
				target = enemy
				distance = d
		var outward: Vector3 = Vector3(chosen.position.x, 0, chosen.position.z)
		var dir: Vector3 = -outward.normalized()
		p.rush = false
		if is_instance_valid(target) and outward.length() < 2.9:
			var lead: float = [0.15, 0.3, 0.45][game.difficulty]
			dir = target.position + target.motion_velocity() * lead - chosen.position
			dir.y = 0
			dir = dir.normalized().rotated(Vector3.UP, game._rng.randfn(0, [0.25, 0.12, 0.04][game.difficulty]))
			p.rush = distance < 1.8 and chosen.energy >= 8 and chosen.spin > 0.2 * chosen.launch_spin
			if target.rushing and distance < 2.1 and game.difficulty > 0:
				if chosen.energy >= 25 and game.difficulty == 2:
					if not chosen.jump():
						chosen.dash(dir.rotated(Vector3.UP, PI * 0.5))
				else:
					chosen.dash(dir.rotated(Vector3.UP, PI * 0.5))
			elif distance < 2.4 and target.wobble > 0.1:
				chosen.dash(dir)
		p.move = dir
		p.aim = dir
	var top: Gasing = top_at(2, p.selected)
	if is_instance_valid(top) and top.alive:
		top.steer(p.move, delta)
		top.set_rush(p.rush, p.aim)
		p.input_age = 0


func scoreboard() -> String:
	var lines: Array[String] = []
	for id: int in roster:
		var mark: String = " ×" if disconnected.has(id) else ""
		lines.append("%s: %d%s" % [short_name(str(roster[id])), scores.get(id, 0), mark])
	return "   |   ".join(lines)


func short_name(value: String) -> String:
	return value if value.length() <= 15 else value.substr(0, 14) + "…"


func update_hud() -> void:
	if not is_instance_valid(cards):
		return
	var fighting: bool = phase == Phase.WIND or phase == Phase.BATTLE
	cards.visible = fighting
	score_label.visible = fighting
	clock_label.visible = fighting
	# Retain the existing slanted FightBar design; the squad strip supplies the extra slots.
	game.player_gauge.visible = phase == Phase.BATTLE
	game.foe_gauge.visible = phase == Phase.BATTLE
	game.duel_label.get_parent().visible = false
	if not fighting or not participants.has(my_id()):
		return
	var owners: Array[String] = []
	for id: int in participants:
		owners.append("%s [%d/3] %s" % [short_name(participants[id].name), live_tops(id).size(), "◆".repeat(int(scores.get(id, 0)))])
	score_label.text = "   |   ".join(owners)
	clock_label.text = "%02d" % ceili(maxf(ROUND_SECONDS - elapsed, 0)) if phase == Phase.BATTLE else tr_text("Opening launch", "Lontaran pertama")
	if not game.net_active and phase == Phase.BATTLE:
		clock_label.text += (" · " + game._t("wave_line") % [game.duel_index + 1, ""]).strip_edges() if game.endless_mode else " · %d / %d" % [game.duel_index + 1, game.MASTERS.size()]
	var reserve: bool = participants[my_id()].slots[selected_slot].state == "reserve"
	_refresh_selected()
	game.player_gauge.title = "%s · %d" % [game._t("you"), selected_slot + 1]
	if is_instance_valid(game.player_top):
		game.player_gauge.frac = game.player_top.spin / game.player_top.spin_reserve
		game.player_gauge.wobbling = game.player_top.wobble > 0
	else:
		game.player_gauge.frac = 0
	if is_instance_valid(game.foe_top):
		game.foe_gauge.frac = game.foe_top.spin / game.foe_top.spin_reserve
		game.foe_gauge.title = "%s · %d" % [game.foe_top.display_name, game.foe_top.slot_id + 1]
		game.foe_gauge.ring_color = game.foe_top.accent_color
		game.foe_gauge.wobbling = game.foe_top.wobble > 0
	else:
		game.foe_gauge.frac = 0
	game.wind_meter.visible = (phase == Phase.WIND and not initial_sent) or (phase == Phase.BATTLE and reserve)
	game.wind_hint.visible = game.wind_meter.visible
	game.aim_arrow.visible = game.wind_meter.visible
	game.wind_hint.text = tr_text("Hold SPACE, release in gold · Energy %.0f/100 · A/D aim", "Tahan SPACE, lepas dalam zon emas · Energy %.0f/100 · A/D halakan") % (100 * game._wind_effectiveness(charge_power))
	for slot: int in 3:
		var entry: Dictionary = participants[my_id()].slots[slot]
		var top: Gasing = top_at(my_id(), slot)
		var line: String = tr_text("OUT", "TUMBANG")
		if entry.state == "reserve":
			var seconds: float = maxf(DEPLOY_AT[slot] - elapsed, 0)
			if phase == Phase.WIND:
				seconds = maxf(15 - wind_elapsed, 0) if slot == 0 else DEPLOY_AT[slot]
			if participants[my_id()].grace >= 0:
				seconds = minf(seconds, participants[my_id()].grace)
			line = tr_text("RESERVE · launch by %ds", "SIMPANAN · lontar dalam %ds") % ceili(seconds)
		elif is_instance_valid(top) and top.alive:
			line = "SPIN %d%%   ENERGY %d" % [roundi(100 * top.spin / top.spin_reserve), roundi(top.energy)]
		spin_bars[slot].value = 100 * top.spin / top.spin_reserve if is_instance_valid(top) and top.alive else 0
		energy_bars[slot].value = top.energy if is_instance_valid(top) and top.alive else 0
		slot_buttons[slot].text = "%s%d · %s\n%s" % ["▶ " if slot == selected_slot else "", slot + 1, str(game.STYLE_DEFS[entry.style].label).trim_prefix("Gasing "), line]
		slot_buttons[slot].modulate = Color.WHITE if slot == selected_slot else Color(0.75, 0.75, 0.75)
	game.battle_hint.visible = phase == Phase.BATTLE
	game.battle_hint.text = tr_text("WASD move · Click push · SHIFT dash 20 · Hold E rush 20/s · SPACE jump 25 · 1/2/3 select", "WASD gerak · Klik tolak · SHIFT dash 20 · Tahan E rush 20/s · SPACE lompat 25 · 1/2/3 pilih")
	if reserve and phase == Phase.BATTLE:
		game.battle_hint.text = tr_text("Hold SPACE to charge reserve · Release to launch · ESC cancels · Battle continues!", "Tahan SPACE untuk cas simpanan · Lepas untuk lontar · ESC batal · Battle terus berjalan!")


func bot_tick(delta: float) -> void:
	bot_clock += delta
	var args: PackedStringArray = OS.get_cmdline_user_args()
	var target: int = 2
	for arg: String in args:
		if arg.begins_with("netbot-count="):
			target = clampi(arg.get_slice("=", 1).to_int(), 2, 4)
	if not game.net_active:
		if Online.is_host and Online.players.size() >= target:
			start_lobby()
		return
	if game.state == game.State.CRAFT:
		if not game.net_ready_sent:
			game._on_fight_pressed()
	elif phase == Phase.WIND:
		if not initial_sent:
			if not charge_active:
				charge_active = true
			elif charge_power >= 84:
				charge_active = false
				initial_sent = true
				_send_command("wind", {"power": charge_power, "angle": 0.0})
	elif phase == Phase.BATTLE:
		var slot: int = 2 if elapsed > 6 else (1 if elapsed > 3 else 0)
		select_slot(slot)
		if participants[my_id()].slots[slot].state == "reserve":
			_send_command("deploy", {"power": 88.0, "angle": 0.0})
		if int(elapsed * 10) % 30 == 0:
			_send_command("jump", {})
		if "netbot-forfeit" in args and elapsed > 8:
			game._net_teardown()
			get_tree().create_timer(0.1).timeout.connect(get_tree().quit)
	elif game.state == game.State.OVER and not game.net_ended and not game.net_rematch_sent:
		game._on_restart_pressed()
