extends Node
## One arena simulation for solo squads and host-authoritative FFA.

const TOP_SCENE: PackedScene = preload("res://gasing.tscn")
const HT = preload("res://scripts/heritage_theme.gd")
const ROUND_SECONDS: float = 90.0
const WIND_SECONDS: float = 15.0
const DEPLOY_AT: Array[float] = [0.0, 30.0, 45.0]
const COLORS: Array[Color] = [HT.PLAYER_COLOR, HT.FOE_COLOR, Color(0.95, 0.38, 0.5), Color(0.58, 0.55, 1)] # FFA seats
const FONT_TITLE: FontFile = preload("res://common/fonts/Kurland.ttf")
const SNAPSHOT_KEYS: Array[String] = ["position", "velocity", "control_velocity", "spin", "energy", "wobble", "dash_cd", "jump_cd", "nudge_cd", "dash_time", "jump_time", "rushing", "rush_direction", "launch_spin"]
enum Phase { IDLE, WIND, BATTLE, RESULT, OVER }

var game: Node
var phase: Phase = Phase.IDLE
var participants: Dictionary = {}
var roster: Dictionary = {}
var scores: Dictionary = {}
var ready_configs: Dictionary = {}
var winds: Dictionary = {}
var auto_winds: Dictionary = {} # id -> true: the WIND timer forced this opening launch
var rematches: Dictionary = {}
var disconnected: Array[int] = []
var round_id: int = 0
var elapsed: float = 0.0
var wind_elapsed: float = 0.0
var selected_slot: int = 0
var _steer_slot: int = 0 # the live top a selected reserve leaves steering (the host's last_live)
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
var cards: VBoxContainer # squad cards, bottom-right
var slot_cards: Array[SquadCard] = []
var reserve_prompt: PanelContainer # "reserve auto-launches in 3 s" above the cards
var reserve_label: Label
var start_button: Button
var lobby_roster: Label
var _hud_secs: int = -1 # update_hud caches: rebuild strings only when these change
var _hud_late: bool = false
var _hud_lead: int = -2
var _hud_wind_key: int = -1
var _hud_prompt_key: int = -1
var _hud_gauge_top: Gasing = null
var _hud_foe_top: Gasing = null
var _hud_lang: String = ""
var _row_codes: Array[int] = [0, 0, 0] # scratch for the FFA standings rows
var _card_words: Array = [] # squad card words (STRINGS card_words), rebuilt on a language change
var ai_charge_slot: int = -1
var ai_charge_power: float = 0.0
var ai_aggro: bool = false
var bot_clock: float = 0.0
var bot_rounds: int = 0
var round_stats: Dictionary = {} # {owner_id: {hits, kos (topples caused), ringouts (caused), perfect}}
var last_launch_grade: String = "" # local player's latest launch: "" | perfect | good | weak | snap
var reserve_warning_slot: int = -1 # local reserve that auto-launches within 3 s, else -1
var last_ko_point: Vector3 = Vector3.ZERO
var deny_ms: int = -1000


func _ready() -> void:
	_setup_actions()


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
				ev.keycode = key as Key
				InputMap.action_add_event(action, ev)


func build_ui() -> void:
	# squad cards stack bottom-right (plates at x 1030-1260, y 420-700; a 12 px gutter on
	# the left holds the selection marker), the reserve prompt just above (y 380-414)
	cards = VBoxContainer.new()
	cards.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	cards.offset_left = -262
	cards.offset_right = -20
	cards.offset_top = -300
	cards.offset_bottom = -20
	cards.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	cards.grow_vertical = Control.GROW_DIRECTION_BEGIN
	cards.add_theme_constant_override("separation", 14)
	cards.mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.hud.add_child(cards)
	for slot: int in 3:
		var card: SquadCard = SquadCard.new()
		card.slot = slot
		card.gui_input.connect(_on_card_input.bind(slot))
		cards.add_child(card)
		slot_cards.append(card)
	reserve_prompt = PanelContainer.new()
	var plate: StyleBoxFlat = game._hud_plate(Color(HT.DANGER, 0.85))
	plate.content_margin_top = 1.0
	plate.content_margin_bottom = 1.0
	reserve_prompt.add_theme_stylebox_override("panel", plate)
	reserve_prompt.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	reserve_prompt.offset_left = -250
	reserve_prompt.offset_right = -20
	reserve_prompt.offset_top = -340
	reserve_prompt.offset_bottom = -306
	reserve_prompt.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	reserve_prompt.grow_vertical = Control.GROW_DIRECTION_BEGIN
	reserve_prompt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	reserve_prompt.visible = false
	reserve_label = game._mk_label("", 13)
	reserve_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	reserve_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	reserve_label.add_theme_constant_override("line_spacing", -3)
	reserve_prompt.add_child(reserve_label)
	game.hud.add_child(reserve_prompt)
	var box: Node = game.wait_panel.get_child(0).get_child(0)
	lobby_roster = game._mk_label("", 17)
	start_button = game._mk_button("START FFA", HT.PLAYER_COLOR)
	start_button.pressed.connect(start_lobby)
	var start_wrap: CenterContainer = CenterContainer.new()
	start_wrap.add_child(start_button)
	# Roster, then START, both above CANCEL.
	var cancel_row: Node = game.wait_cancel_button.get_parent()
	box.add_child(lobby_roster)
	box.add_child(start_wrap)
	box.move_child(lobby_roster, cancel_row.get_index())
	box.move_child(start_wrap, cancel_row.get_index())
	refresh_lobby()


func refresh_lobby() -> void:
	if not is_instance_valid(start_button):
		return
	start_button.visible = Online.is_host
	start_button.disabled = Online.players.size() < 2 or Online.players.size() > 4
	start_button.text = game._t("ffa_start")
	var names: Array[String] = []
	for pd: PlayerData in Online.players.values():
		names.append(pd.display_name)
	lobby_roster.text = game._t("ffa_players_n") % names.size() + "\n" + "\n".join(names)
	if not Online.is_host:
		lobby_roster.text += "\n" + game._t("ffa_wait_host")


func start_lobby() -> void:
	if not Online.is_host or Online.players.size() < 2 or Online.players.size() > 4:
		return
	var names: Dictionary = {}
	for pd: PlayerData in Online.players.values():
		names[pd.multiplayer_id] = pd.display_name
	Online.set_match_locked(true)
	_start_match.rpc(unique_names(names), round_id + 1)


static func unique_names(names: Dictionary) -> Dictionary:
	# LAN names are the OS user, so two instances on one PC are both "User": number repeats
	var out: Dictionary = {}
	for id: int in names:
		var n: String = str(names[id])
		var k: int = 2
		while out.values().has(n):
			n = "%s %d" % [str(names[id]), k]
			k += 1
		out[id] = n
	return out


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
	game.craft_opp_status.text = game._t("ffa_ready") % [ids.size(), connected_ids().size()]


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
	round_stats.clear()
	last_ko_point = Vector3.ZERO
	# Roster order (not ready order) keeps colours and spawn seats stable across rounds.
	var ids: Array = configs.keys() if roster.is_empty() else roster.keys()
	var seated: Array = ids.filter(func(pid: int) -> bool: return configs.has(pid) and not disconnected.has(pid))
	for index: int in seated.size():
		var id: int = seated[index]
		var slots: Array = []
		for entry: Dictionary in configs[id].slots:
			slots.append({"style": entry.style, "stats": entry.stats.duplicate(), "state": "reserve", "top": null})
		participants[id] = {"name": roster.get(id, "Player"), "color": COLORS[ids.find(id) % 4], "slots": slots,
			"selected": 0, "last_live": 0, "grace": -1.0, "move": Vector3.ZERO, "aim": Vector3.FORWARD, "rush": false,
			"input_age": 0.0, "seq": -1, "angle": TAU * float(index) / float(seated.size())}
		round_stats[id] = {"hits": 0, "kos": 0, "ringouts": 0, "perfect": 0}


func begin_wind() -> void:
	if not game.net_active:
		round_id += 1
		disconnected.clear()
		var opp: Dictionary = game._current_opponent()
		ai_aggro = bool(opp.get("aggressive", false))
		roster = {1: game._t("you"), 2: opp.name}
		var mine: Array = []
		for style: String in game.loadout:
			mine.append({"style": style, "stats": game._style_battle_stats(style)})
		var enemy: Array = [{"style": str(opp.mesh), "stats": opp.duplicate()}]
		for style: String in ["jantung", "uri"]:
			enemy.append({"style": style, "stats": game.STYLE_DEFS[style].duplicate()})
		_build_participants({1: {"slots": mine}, 2: {"slots": enemy}})
	phase = Phase.WIND
	game._update_top_bar() # medallion duel line for this fight
	elapsed = 0.0
	wind_elapsed = 0.0
	selected_slot = 0
	_steer_slot = 0
	charge_active = false
	charge_power = 0.0
	aim_angle = 0.0
	initial_sent = false
	ai_charge_slot = -1
	reserve_warning_slot = -1
	last_launch_grade = ""
	winds.clear()
	auto_winds.clear()
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
	var side: Color = color
	if not game.net_active:
		# SP sides are fixed gold vs crimson; only the master's own top keeps its identity accent.
		side = HT.SIDE_YOU if id == my_id() else HT.SIDE_FOE
		if id == 1:
			color = game._style_accent(entry.style)
		else:
			color = game._current_opponent().color if slot == 0 else HT.SIDE_FOE
	top.setup(participants[id].name, str(entry.stats.get("shape", game.STYLE_DEFS[entry.style].shape)), entry.stats, color)
	top.set_team(side, id == my_id())
	top.position = spawn_position(id, slot)
	entry.top = top
	if authority():
		# Fresh instance (existing tops returned above), so each signal connects exactly once.
		top.landed.connect(_on_top_landed.bind(top))
		top.rim_touched.connect(_on_rim_touched.bind(top))
	return top


func _on_top_landed(point: Vector3, strength: float, top: Gasing) -> void:
	fx(point, strength, "land", top.team_color)


func _on_rim_touched(point: Vector3, speed: float, top: Gasing) -> void:
	if elapsed - float(top.get_meta("rim_at", -1.0)) < 0.5:
		return
	top.set_meta("rim_at", elapsed)
	fx(point, speed, "rim")


func top_at(id: int, slot: int) -> Gasing:
	if not participants.has(id) or slot < 0 or slot > 2:
		return null
	var top: Variant = participants[id].slots[slot].top
	return top if is_instance_valid(top) else null


func live_tops(id: int = 0) -> Array[Gasing]:
	var result: Array[Gasing] = []
	for pid: int in participants:
		if id != 0 and id != pid:
			continue
		for entry: Dictionary in participants[pid].slots:
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
			aim_angle = clampf(aim_angle - event.relative.x * 0.003 * _aim_flip(), -1.1, 1.1)
		return
	if event.is_action_pressed("arena_dash"):
		if _allow("dash"):
			var dir: Vector3 = _move_dir()
			_send_command("dash", {"dir": dir if dir.length() > 0.05 else _aim_dir()})
			game._play_action_sfx("dash")
	elif event.is_action_pressed("arena_jump"):
		if _allow("jump"):
			_send_command("jump", {})
			game._play_action_sfx("jump")
	elif event.is_action_pressed("arena_rush"):
		_allow("rush") # deny feedback only: rush and its loop sound are polled
	elif event.is_action_released("arena_rush"):
		_send_command("stop", {})
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var top: Gasing = top_at(my_id(), selected_slot)
		if is_instance_valid(top) and top.alive and top.nudge_cd <= 0.0 and top.dash_time <= 0.0:
			game._play_action_sfx("push")
		_send_command("nudge", {"dir": _aim_dir()})
		game._flash_click_marker(_flat_cursor())


func _aim_flip() -> float:
	# Far-side spawns launch toward the camera: flip aim input so it stays screen-relative.
	return -1.0 if cos(participants[my_id()].angle) < 0.0 else 1.0


func _block_reason(kind: String) -> String:
	# Local prediction for the selected top (puppets carry energy/cooldowns via snapshots).
	var top: Gasing = top_at(my_id(), selected_slot)
	if not is_instance_valid(top) or not top.alive or not top.battling:
		return "none"
	var cost: float = Gasing.DASH_COST if kind == "dash" else (Gasing.JUMP_COST if kind == "jump" else 0.01)
	if top.energy < cost: # energy only drains, so a stale puppet value errs toward allowing
		return "energy"
	# A puppet's cooldown is a snapshot old (50 ms + latency): near its end, let the host decide.
	# ponytail: fixed 0.15 s margin; scale by measured RTT if laggy Steam peers get refused.
	var slack: float = 0.0 if authority() else 0.15
	if (kind == "dash" and top.dash_cd > slack) or (kind == "jump" and top.jump_cd > slack):
		return "cooldown"
	return ""


func _allow(kind: String) -> bool:
	var why: String = _block_reason(kind)
	if why == "":
		return true
	game._play_action_sfx("deny")
	var now: int = Time.get_ticks_msec()
	if why != "none" and now - deny_ms >= 400:
		deny_ms = now
		var text: String = game._t("deny_energy") if why == "energy" else game._t("deny_cooldown")
		game._toast(text, HT.DANGER, top_at(my_id(), selected_slot).position, false)
	return false


func select_slot(slot: int) -> void:
	if phase != Phase.BATTLE or slot < 0 or slot > 2 or not participants.has(my_id()):
		return
	if selected_slot == slot or participants[my_id()].slots[slot].state == "out":
		return
	_send_command("stop", {})
	charge_active = false
	charge_power = 0
	aim_angle = 0
	if participants[my_id()].slots[selected_slot].state == "alive":
		_steer_slot = selected_slot # mirrors accept_command's last_live
	selected_slot = slot
	_send_command("select", {})
	_refresh_selected()


func _auto_select() -> void:
	# The selected top just went out: hand control to a live top, else the next reserve.
	if phase != Phase.BATTLE or not participants.has(my_id()):
		return
	var slots: Array = participants[my_id()].slots
	if slots[selected_slot].state != "out":
		return
	for slot: int in 3:
		if slots[slot].state == "alive":
			select_slot(slot)
			return
	select_slot(reserve_slot(my_id()))


func _refresh_selected() -> void:
	game.player_top = top_at(my_id(), selected_slot)
	game.foe_top = null
	var nearest: float = INF
	var charging: bool = participants.has(my_id()) and participants[my_id()].slots[selected_slot].state == "reserve"
	for top: Gasing in live_tops():
		# the ring marks the top your keys move: the selected one, or the one a charging reserve leaves steering
		top.set_selected(top.owner_id == my_id() and (top.slot_id == selected_slot or (charging and top.slot_id == _steer_slot)))
		if top.owner_id == my_id():
			continue
		var d: float = top.position.distance_squared_to(game.player_top.position) if is_instance_valid(game.player_top) else 0.0
		if d < nearest:
			nearest = d
			game.foe_top = top


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
		var power: Variant = data.get("power")
		var angle: Variant = data.get("angle")
		if not (power is float or power is int) or not (angle is float or angle is int):
			return false
		if not is_finite(float(power)) or not is_finite(float(angle)) or power < 0 or power > 100 or absf(angle) > 1.1:
			return false
		if kind == "wind":
			if phase != Phase.WIND or slot != 0 or winds.has(id):
				return false
			winds[id] = Vector2(power, angle)
			_try_start_battle()
		else:
			if phase != Phase.BATTLE or p.slots[slot].state != "reserve":
				return false
			deploy(id, slot, power, angle)
		return true
	if phase != Phase.BATTLE:
		return false
	if kind == "select":
		if slot == p.selected:
			return true
		var old: Gasing = top_at(id, p.selected)
		if is_instance_valid(old):
			old.cancel_control()
		if p.slots[p.selected].state == "alive":
			p.last_live = p.selected # keeps steering while a reserve is selected for charging
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


func deploy(id: int, slot: int, power: float, angle: float = 0.0, auto: bool = false) -> void:
	if game.net_active:
		_deployed.rpc(round_id, id, slot, power, angle, auto)
	else:
		_deployed(round_id, id, slot, power, angle, auto)


@rpc("authority", "call_local", "reliable")
func _deployed(rid: int, id: int, slot: int, power: float, angle: float, auto: bool = false) -> void:
	if rid != round_id or not participants.has(id) or participants[id].slots[slot].state != "reserve":
		return
	var top: Gasing = _make_top(id, slot)
	participants[id].slots[slot].state = "alive"
	participants[id].grace = -1.0
	top.set_winding(false)
	top.launch((-spawn_position(id, slot)).normalized().rotated(Vector3.UP, angle), game._wind_effectiveness(power))
	var grade: String = "weak"
	if not auto:
		grade = "snap" if power > 95.0 else ("perfect" if power >= 80.0 else ("good" if power >= 40.0 else "weak"))
	if grade == "perfect":
		_count(id, "perfect")
	if id == my_id() and not auto:
		var colors: Dictionary = {"snap": HT.OVERWIND_RED, "perfect": HT.PLAYER_COLOR, "good": HT.ENERGY_BLUE, "weak": HT.TEXT_DIM}
		var grade_text: String = game._t("grade_" + grade)
		if slot == 0: # same frame as _battle_started: _banner replaces, so the grade rides under LAUNCH!
			game._banner(game._t("call_launch"), colors[grade], grade_text)
		else: # mid-fight reserve: a toast at that top, so no band covers the dish during play
			game._toast(grade_text, colors[grade], top.position, false)
		game._play_action_sfx("snap" if grade == "snap" else "launch")
	else:
		game._play_sfx(game.SND_LAUNCH, -7.0, 0.1)
	if id == my_id():
		last_launch_grade = grade
		if slot == selected_slot:
			charge_active = false
		if auto: # slot 0 only when the WIND timer ran out
			var text: String = game._t("auto_launched") if slot == 0 else game._t("reserve_auto_launched") % (slot + 1)
			game._toast(text, HT.DANGER, top.position, false)
	elif slot > 0 and _tutorial_duel():
		game._hint("reserve")
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
			deploy(id, 0, winds[id].x, winds[id].y, auto_winds.has(id))


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
	game._banner(game._t("call_launch"), HT.PLAYER_COLOR)
	game._play_action_sfx("gong")
	if _tutorial_duel():
		game._hint("steer")


func _tutorial_duel() -> bool:
	# Campaign duel 1 and Endless wave 1 teach: no early AI reserves, AI reserves charged to
	# at most 60, one-shot hints (the AI's opening launch is not softened).
	return not game.net_active and game.duel_index == 0


func wind_time_left() -> float:
	return maxf(WIND_SECONDS - wind_elapsed, 0.0) if phase == Phase.WIND else 0.0


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
		if authority() and wind_elapsed >= WIND_SECONDS:
			for id: int in participants:
				if not winds.has(id) and not disconnected.has(id):
					winds[id] = Vector2(55, 0)
					auto_winds[id] = true
			_try_start_battle()
		update_hud()
		return
	if phase != Phase.BATTLE:
		if phase == Phase.RESULT:
			update_hud() # the result moved the score pips and squad glyphs; keep the HUD honest
		return
	elapsed += delta
	if _tutorial_duel():
		for hint: Array in [[8.0, "dash"], [25.0, "reserve"]]:
			if elapsed >= hint[0] and elapsed - delta < hint[0]:
				game._hint(hint[1])
	_update_charge(delta)
	input_cd -= delta
	if input_cd <= 0 and participants.has(my_id()):
		input_cd = 0.05
		input_seq += 1
		var move: Vector3 = _move_dir()
		var aim: Vector3 = _aim_dir()
		var rush: bool = Input.is_action_pressed("arena_rush") and not charge_active
		var menus: Variant = game.get("menus")
		if game._netbot or (is_instance_valid(menus) and menus.is_open()):
			move = Vector3.ZERO # polled keys must not steer under the (MP, unpaused) pause overlay
			rush = false
		if authority():
			accept_input(my_id(), round_id, input_seq, selected_slot, move, aim, rush)
		else:
			_input_frame.rpc_id(1, round_id, input_seq, selected_slot, move, aim, rush)
	if authority():
		for id: int in participants:
			var p: Dictionary = participants[id]
			p.input_age += delta
			# A reserve selected for charging still steers the last live top (no rush).
			var charging: bool = p.slots[p.selected].state == "reserve"
			var top: Gasing = top_at(id, p.last_live if charging else p.selected)
			if not is_instance_valid(top) or not top.battling or not top.alive:
				continue
			if p.input_age > 0.3:
				if p.move != Vector3.ZERO or p.rush:
					top.cancel_control()
				p.move = Vector3.ZERO
				p.rush = false
			elif game.net_active or id == my_id():
				top.steer(p.move, delta)
				top.set_rush(p.rush and not charging, p.aim)
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
	_update_reserve_warning()
	update_hud()


func _update_reserve_warning() -> void:
	reserve_warning_slot = -1
	if phase != Phase.BATTLE or not participants.has(my_id()):
		return
	var p: Dictionary = participants[my_id()]
	if p.grace >= 0.0 and reserve_slot(my_id()) >= 0:
		reserve_warning_slot = reserve_slot(my_id())
		return
	for slot: int in range(1, 3):
		var left: float = DEPLOY_AT[slot] - elapsed
		if p.slots[slot].state == "reserve" and left > 0.0 and left <= 3.0:
			reserve_warning_slot = slot
			return


func _update_charge(delta: float) -> void:
	if not participants.has(my_id()):
		return
	if phase == Phase.WIND or participants[my_id()].slots[selected_slot].state == "reserve":
		# A/D also steer the last live top while a reserve charges: keys aim only when
		# nothing else is steered (the mouse still aims a mid-fight reserve)
		if phase == Phase.WIND or live_tops(my_id()).is_empty():
			aim_angle = clampf(aim_angle - Input.get_axis("aim_left", "aim_right") * 1.5 * delta * _aim_flip(), -1.1, 1.1)
		if charge_active:
			var before: float = charge_power
			charge_power = minf(charge_power + 55 * delta, 100)
			for tick: Vector2 in [Vector2(40, 1.0), Vector2(80, 1.2), Vector2(95, 1.45)]:
				if before < tick.x and charge_power >= tick.x:
					game._play_action_sfx("charge_tick", tick.y)
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
				deploy(id, slot, 55, 0.0, true)
		if live_tops(id).is_empty() and reserve_slot(id) >= 0:
			if p.grace < 0:
				p.grace = 5.0
			else:
				p.grace -= delta
				if p.grace <= 0:
					deploy(id, reserve_slot(id), 55, 0.0, true)
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
				b.set_meta("last_hit_by", a.owner_id)
			if b_rush_contact:
				a.spin = maxf(a.spin - 12 * b.rush_paid_seconds, 0)
				a.set_meta("last_hit_by", b.owner_id)
			if (a_rush_contact or b_rush_contact) and rush_fx_cd <= 0:
				fx((a.position + b.position) * 0.5, 1.2, "grind", (a if a_rush_contact else b).team_color)
				rush_fx_cd = 0.12
			var key: String = "%s:%s" % [a.name, b.name]
			if pair_cooldowns.has(key):
				continue
			pair_cooldowns[key] = 0.3
			var a_in: float = a.motion_velocity().dot(dir) # a's speed into b
			var b_in: float = -b.motion_velocity().dot(dir) # b's speed into a
			# Impact is the faster top's own speed into the other, not the closing speed: two tops
			# just steering together (2 x MOVE_SPEED) stay a clash; dash (5.0), rush (3.6) or
			# launch momentum reach the big tier (>= 3.5).
			var impact: float = maxf(maxf(a_in, b_in), 0)
			# Tuning knob: steering-speed contact bites like before (0.4), a full dash takes 4x.
			var bite: float = lerpf(0.4, 1.6, clampf((impact - Gasing.MOVE_SPEED) / (5.0 - Gasing.MOVE_SPEED), 0, 1))
			var hit_b: float = minf(0.02 * a.spin * a.mass / b.mass + maxf(a_in, 0) * 1.3 * a.mass / b.mass, 2.4)
			var hit_a: float = minf(0.02 * b.spin * b.mass / a.mass + maxf(b_in, 0) * 1.3 * b.mass / a.mass, 2.4)
			a.apply_hit(-dir, hit_a, hit_a * bite)
			b.apply_hit(dir, hit_b, hit_b * bite)
			a.set_meta("last_hit_by", b.owner_id)
			b.set_meta("last_hit_by", a.owner_id)
			var attacker: Gasing = a if a_in >= b_in else b
			if impact >= 1.5:
				_count(attacker.owner_id, "hits")
			fx((a.position + b.position) * 0.5, impact, "hit", attacker.team_color)


func _count(id: int, stat: String) -> void:
	if round_stats.has(id):
		round_stats[id][stat] += 1


func fx(point: Vector3, strength: float, kind: String = "hit", tint: Color = Color(1.0, 0.85, 0.4)) -> void:
	game._hit_effects(point, strength, kind, tint)
	if game.net_active:
		_hit_fx.rpc(round_id, point, strength, kind, tint)


@rpc("authority", "unreliable")
func _hit_fx(rid: int, point: Vector3, strength: float, kind: String, tint: Color) -> void:
	if rid == round_id and phase == Phase.BATTLE:
		game._hit_effects(point, strength, kind, tint)


func resolve_eliminations(forfeit: bool = false) -> void:
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
		var winner: int = remaining[0] if remaining.size() == 1 else 0
		# rivals who left before BATTLE are only noticed here, on its first tick
		var left: bool = forfeit or participants.keys().all(func(pid: int) -> bool: return pid == winner or disconnected.has(pid))
		var kind: String = "draw" if winner == 0 else ("forfeit" if left else "ko")
		finish_round(winner, {"kind": kind, "point": last_ko_point})
	elif elapsed >= ROUND_SECONDS:
		var winner: int = timeout_winner()
		finish_round(winner, _timeout_reason(winner))


@rpc("authority", "call_local", "reliable")
func _eliminated(rid: int, id: int, slot: int, reason: String) -> void:
	if rid != round_id or not participants.has(id) or participants[id].slots[slot].state == "out":
		return
	participants[id].slots[slot].state = "out"
	var top: Gasing = top_at(id, slot)
	if is_instance_valid(top):
		game._toast_elimination(top, reason)
		top.die(reason)
		game._hit_effects(top.position, 3.0, "ko", top.team_color) # local: this RPC already runs on every peer
		last_ko_point = top.position
		# Credit the last opponent contact (authority-side meta; clients get round_stats via _result).
		var by: int = int(top.get_meta("last_hit_by", 0))
		if by != 0 and not disconnected.has(id):
			_count(by, "ringouts" if reason == "ringout" else "kos")
	if id == my_id() and slot == selected_slot:
		_auto_select.call_deferred()
	_refresh_selected()


func _standings() -> Dictionary:
	# Timeout ranking per connected owner: Vector2(live top count, summed normalized spin).
	var rows: Dictionary = {}
	for id: int in participants:
		if disconnected.has(id):
			continue
		var living: Array[Gasing] = live_tops(id)
		var total: float = 0
		for top: Gasing in living:
			total += top.spin / top.spin_reserve
		rows[id] = Vector2(living.size(), total)
	return rows


func timeout_winner() -> int:
	var winner: int = 0
	var best: Vector2 = Vector2(-1, -1)
	var rows: Dictionary = _standings()
	for id: int in rows:
		var row: Vector2 = rows[id]
		if row.x > best.x or (row.x == best.x and row.y > best.y + 0.0001):
			winner = id
			best = row
		elif row.x == best.x and absf(row.y - best.y) <= 0.0001:
			winner = 0
	return winner


func leading_id() -> int:
	return timeout_winner()


func _timeout_reason(winner: int) -> Dictionary:
	var rows: Dictionary = _standings()
	var counts: Dictionary = {}
	var spins: Dictionary = {} # average spin % of live tops: the same number the top labels show
	for id: int in rows:
		counts[id] = int(rows[id].x)
		spins[id] = roundi(100.0 * rows[id].y / maxf(rows[id].x, 1.0))
	var kind: String = "draw"
	if winner != 0:
		kind = "time_count" if counts.values().count(counts[winner]) == 1 else "time_spin"
	if kind == "time_spin": # spin only split the seats tied on tops; the rest could not have won
		for id: int in spins.keys():
			if counts[id] != counts[winner]:
				spins.erase(id)
	return {"kind": kind, "counts": counts, "spins": spins}


func deployed_styles(id: int) -> Array:
	var styles: Array = []
	if participants.has(id):
		for entry: Dictionary in participants[id].slots:
			if entry.state != "reserve" and not styles.has(entry.style):
				styles.append(entry.style)
	return styles


func finish_round(winner: int, reason: Dictionary = {}) -> void:
	if phase != Phase.BATTLE:
		return
	var next_scores: Dictionary = scores.duplicate()
	if winner != 0:
		next_scores[winner] = int(next_scores.get(winner, 0)) + 1
	if game.net_active:
		_result.rpc(round_id, winner, next_scores, reason, round_stats.duplicate(true))
	else:
		_result(round_id, winner, next_scores, reason, round_stats.duplicate(true))


@rpc("authority", "call_local", "reliable")
func _result(rid: int, winner: int, next_scores: Dictionary, reason: Dictionary = {}, stats: Dictionary = {}) -> void:
	if rid != round_id or applied_result == rid:
		return
	applied_result = rid
	phase = Phase.RESULT
	scores = next_scores.duplicate()
	if not stats.is_empty():
		round_stats = stats.duplicate(true) # the authority's tally, so every peer shows the same numbers
	charge_active = false
	reserve_warning_slot = -1
	for top: Gasing in live_tops():
		top.end_round() # keeps spinning on screen but refuses every action
	game.wind_meter.visible = false
	game.wind_hint.visible = false
	game.aim_arrow.visible = false
	game._award_style_xp(deployed_styles(my_id()), winner == my_id()) # also saves the workshop
	if game._netbot:
		bot_rounds += 1
		print("netbot: round result rid=", rid, " winner=", winner, " seconds=", elapsed, " scores=", scores)
	game._arena_round_finished(winner, reason)


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
			resolve_eliminations(true)
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
	var tutorial: bool = _tutorial_duel()
	ai_deploy_cd -= delta
	# Charging a reserve is its own block: p.selected stays on the live top, which keeps fighting.
	if ai_charge_slot >= 0:
		if p.slots[ai_charge_slot].state != "reserve":
			ai_charge_slot = -1
		else:
			var goal: float = minf([72.0, 85.0, 93.0][game.difficulty], 60.0 if tutorial else 100.0)
			ai_charge_power += 55 * delta
			if ai_charge_power >= goal:
				deploy(2, ai_charge_slot, goal)
				ai_charge_slot = -1
	elif reserve_slot(2) >= 0 and (own.is_empty() or (ai_deploy_cd <= 0 and (own.size() < enemies.size() or elapsed > 18))) \
			and (not tutorial or elapsed >= DEPLOY_AT[reserve_slot(2)]):
		ai_charge_slot = reserve_slot(2)
		ai_charge_power = 0
		ai_deploy_cd = [13.0, 9.0, 6.0][game.difficulty] * (0.7 if ai_aggro else 1.0)
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
		var best: float = INF
		for enemy: Gasing in enemies:
			var d: float = chosen.position.distance_to(enemy.position)
			# Aggressive masters hunt tops already near the rim (one shove from a ring-out).
			var score: float = d * (0.5 if ai_aggro and Vector2(enemy.position.x, enemy.position.z).length() > 3.0 else 1.0)
			if score < best:
				best = score
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
			p.rush = distance < (2.4 if ai_aggro else 1.8) and chosen.energy >= 8 and chosen.spin > 0.2 * chosen.launch_spin
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


func short_name(value: String, cap: int = 15) -> String:
	return value if value.length() <= cap else value.substr(0, cap - 1) + "…"


func update_hud() -> void:
	if not is_instance_valid(cards):
		return
	var fighting: bool = phase == Phase.WIND or phase == Phase.BATTLE or phase == Phase.RESULT
	var mine: bool = fighting and participants.has(my_id())
	var clash: bool = phase == Phase.BATTLE or phase == Phase.RESULT
	cards.visible = mine
	game.hud_medallion.visible = fighting
	game.battle_hint.visible = fighting # key strip: its own fade decides when it shows
	game.player_gauge.visible = clash and mine
	game.foe_gauge.visible = clash
	if not mine:
		reserve_prompt.visible = false
		game.wind_hint.visible = false
		for row: Control in game.hud_rows:
			row.visible = false
		return
	_refresh_selected()
	_hud_centre()
	_hud_bars()
	_hud_wind()
	_hud_cards()
	_hud_lang = game.lang


func _side(id: int) -> Color:
	# side colour: SP is always gold (you) vs crimson; FFA uses each seat's colour
	if not game.net_active:
		return HT.SIDE_YOU if id == my_id() else HT.SIDE_FOE
	return participants[id].color if participants.has(id) else HT.TEXT_DIM


func _squad_codes(id: int, out: Array[int]) -> void:
	# glyph row per slot: 0 alive, 1 reserve, 2 out
	var slots: Array = participants[id].slots
	for s: int in 3:
		out[s] = 0 if slots[s].state == "alive" else (1 if slots[s].state == "reserve" else 2)


func _style_name(id: int, slot: int) -> String:
	return str(game.STYLE_DEFS[participants[id].slots[slot].style].label).trim_prefix("Gasing ")


func _hud_centre() -> void:
	# medallion: round clock (red + pulsing for the last 15 s, with the leader named),
	# you vs the best rival as score pips; the duel line comes from game._update_top_bar
	var secs: int = int(ROUND_SECONDS) if phase == Phase.WIND else ceili(maxf(ROUND_SECONDS - elapsed, 0.0))
	if secs != _hud_secs:
		_hud_secs = secs
		game.hud_clock.text = str(secs)
	var late: bool = phase == Phase.BATTLE and elapsed >= ROUND_SECONDS - 15.0
	if late != _hud_late:
		_hud_late = late
		_hud_lead = -2
		game.hud_clock.add_theme_color_override("font_color", HT.DANGER if late else HT.TEXT_COLOR)
		game.duel_label.visible = not late
		game.hud_lead.visible = late
	game.hud_clock.scale = Vector2.ONE * (1.0 + 0.1 * maxf(sin(elapsed * TAU * 2.0), 0.0)) if late else Vector2.ONE
	if late:
		var lead: int = leading_id()
		if lead != _hud_lead or game.lang != _hud_lang:
			_hud_lead = lead
			game.hud_lead.text = game._t("hud_even") if lead == 0 else game._t("hud_leading") % short_name(str(participants[lead].name))
			game.hud_lead.add_theme_color_override("font_color", HT.TEXT_COLOR if lead == 0 else _side(lead))
	var best: int = 0
	var rival: int = 0
	for id: int in participants:
		if id != my_id() and (rival == 0 or int(scores.get(id, 0)) > best):
			best = int(scores.get(id, 0))
			rival = id
	var pips: bool = game.net_active or not game.endless_mode # endless waves are single rounds
	if game.score_row.visible != pips:
		game.score_row.visible = pips
		for l: Label in [game.duel_label, game.hud_lead]: # no pips: the caption moves up into the gap
			l.offset_top = 76.0 if pips else 62.0
			l.offset_bottom = l.offset_top + 22.0
	var target: int = game.NET_MATCH_TARGET if game.net_active else 2 # SP duels are best of 3
	game.my_pips.show_score(int(scores.get(my_id(), 0)), target, _side(my_id()))
	game.opp_pips.show_score(best, target, _side(rival))


func _hud_bars() -> void:
	# you: the selected top (while a reserve is selected, the live top it leaves steering, else
	# your first live one); rival: the nearest foe top; each bar fills in its side colour
	var top: Gasing = game.player_top
	if not is_instance_valid(top) or not top.alive:
		top = null
		for slot: int in [_steer_slot, 0, 1, 2]:
			var t: Gasing = top_at(my_id(), slot)
			if is_instance_valid(t) and t.alive and participants[my_id()].slots[slot].state == "alive":
				top = t
				break
	if top != _hud_gauge_top and top != null:
		game.player_gauge.shown = top.spin / top.spin_reserve # a switch is not damage: no orange trail
	if top != _hud_gauge_top or game.lang != _hud_lang:
		_hud_gauge_top = top
		game.player_gauge.title = game._t("gauge_you") if top == null \
			else "%s · %d %s" % [game._t("gauge_you"), top.slot_id + 1, _style_name(my_id(), top.slot_id)]
	# always the side colour: a red or blue lacquer must never pass for the rival's bar or
	# the energy bars (the lacquer shows on the top itself)
	game.player_gauge.ring_color = _side(my_id())
	game.player_gauge.side_color = _side(my_id())
	game.player_gauge.frac = top.spin / top.spin_reserve if top != null else 0.0
	game.player_gauge.wobbling = top != null and top.wobble > 0.0
	_squad_codes(my_id(), game.player_gauge.squad)
	var foe: Gasing = game.foe_top
	if is_instance_valid(foe) and participants.has(foe.owner_id):
		if foe != _hud_foe_top:
			_hud_foe_top = foe
			game.foe_gauge.title = "%s · %d" % [short_name(foe.display_name, 18), foe.slot_id + 1] # 18 fits every master
			game.foe_gauge.ring_color = foe.team_color
			game.foe_gauge.side_color = foe.team_color
			game.foe_gauge.shown = foe.spin / foe.spin_reserve # a switch is not damage: no orange trail
		game.foe_gauge.frac = foe.spin / foe.spin_reserve
		game.foe_gauge.wobbling = foe.wobble > 0.0
		_squad_codes(foe.owner_id, game.foe_gauge.squad)
	else:
		game.foe_gauge.frac = 0.0
		game.foe_gauge.wobbling = false
	# FFA with 3-4 seats: a standings row per rival under the foe bar
	var row_i: int = 0
	if participants.size() > 2:
		for id: int in participants:
			if id == my_id() or row_i >= game.hud_rows.size():
				continue
			_squad_codes(id, _row_codes)
			var gone: String = " ×" if disconnected.has(id) else ""
			game.hud_rows[row_i].show_row(short_name(str(participants[id].name)) + gone, _side(id), _row_codes, int(scores.get(id, 0)))
			game.hud_rows[row_i].visible = true
			row_i += 1
	for j: int in range(row_i, game.hud_rows.size()):
		game.hud_rows[j].visible = false


func _hud_wind() -> void:
	# wind card beside the meter: WIND countdown (or the reserve being charged) + how to launch
	var reserve: bool = participants[my_id()].slots[selected_slot].state == "reserve"
	var can_charge: bool = (phase == Phase.WIND and not initial_sent) or (phase == Phase.BATTLE and reserve)
	game.wind_meter.visible = can_charge
	game.aim_arrow.visible = can_charge
	game.wind_hint.visible = can_charge or phase == Phase.WIND
	if not game.wind_hint.visible:
		return
	var mode: int = 2 if phase == Phase.BATTLE else (1 if initial_sent else 0)
	var secs: int = ceili(wind_time_left())
	var spin_pct: int = roundi(100.0 * game._wind_effectiveness(charge_power))
	var key: int = ((mode * 4 + selected_slot) * 100 + secs) * 1000 + spin_pct
	if key == _hud_wind_key and game.lang == _hud_lang:
		return
	_hud_wind_key = key
	var how: String = game._t("hud_how")
	match mode:
		0:
			game.wind_count.text = game._t("hud_launch_in") % secs
			game.wind_text.text = how + "\n" + game._t("hud_aim_spin") % spin_pct
		1:
			game.wind_count.text = game._t("hud_launched")
			game.wind_text.text = game._t("hud_waiting") % secs
		_:
			game.wind_count.text = game._t("hud_reserve_n") % (selected_slot + 1)
			game.wind_text.text = how + "\n" + game._t("hud_cancel_spin") % spin_pct
	game.wind_count.add_theme_color_override("font_color", HT.DANGER if mode == 0 and secs <= 5 else HT.SONGKET_GOLD)


func _hud_cards() -> void:
	# squad cards + the reserve prompt above them
	var p: Dictionary = participants[my_id()]
	if _card_words.is_empty() or game.lang != _hud_lang:
		_card_words = Array(game._t("card_words").split("|"))
	for slot: int in 3:
		var entry: Dictionary = p.slots[slot]
		var top: Gasing = top_at(my_id(), slot)
		var state: String = entry.state
		if state == "alive" and not (is_instance_valid(top) and top.alive):
			state = "out" # dying this frame
		var left: float = 0.0
		var total: float = 1.0
		if state == "reserve":
			total = WIND_SECONDS if slot == 0 else DEPLOY_AT[slot]
			left = wind_time_left() if slot == 0 else (DEPLOY_AT[slot] - (0.0 if phase == Phase.WIND else elapsed))
			if p.grace >= 0.0 and p.grace < left and slot == reserve_slot(my_id()): # grace launches the next reserve only
				left = p.grace
				total = 5.0
		var alive: bool = state == "alive"
		var card: SquadCard = slot_cards[slot]
		if card.style_id != entry.style: # the name string is built only when the style changes
			card.style_id = entry.style
			card.title = _style_name(my_id(), slot)
			card.queue_redraw()
		card.show_slot(state, slot == selected_slot, _side(my_id()),
			top.spin / top.spin_reserve if alive else 0.0, top.energy if alive else 0.0,
			alive and top.energy >= Gasing.DASH_COST and top.dash_cd <= 0.0,
			alive and top.energy >= Gasing.JUMP_COST and top.jump_cd <= 0.0, maxf(left, 0.0), total, _card_words)
	var warn: int = reserve_warning_slot if phase == Phase.BATTLE else -1
	reserve_prompt.visible = warn >= 0
	if warn < 0:
		return
	var grace: bool = p.grace >= 0.0
	var secs: int = ceili(p.grace if grace else DEPLOY_AT[warn] - elapsed)
	var key: int = (warn * 100 + secs) * 2 + int(grace)
	if key != _hud_prompt_key or game.lang != _hud_lang:
		_hud_prompt_key = key
		reserve_label.text = game._t("prompt_grace") % [warn + 1, secs] if grace \
			else game._t("prompt_reserve") % [warn + 1, secs, warn + 1]
	reserve_prompt.modulate.a = 0.8 + 0.2 * sin(elapsed * TAU * 1.5)


func _on_card_input(event: InputEvent, slot: int) -> void:
	# clicking a squad card selects that slot, like its number key
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		select_slot(slot)
		cards.accept_event()


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
				_send_command("wind", {"power": charge_power, "angle": game._rng.randf_range(-0.4, 0.4)}) # jitter: mirrored bots always draw
	elif phase == Phase.BATTLE:
		var slot: int = 2 if elapsed > 6 else (1 if elapsed > 3 else 0)
		select_slot(slot)
		if participants[my_id()].slots[slot].state == "reserve":
			_send_command("deploy", {"power": game._rng.randf_range(80.0, 92.0), "angle": game._rng.randf_range(-0.4, 0.4)})
		if int(elapsed * 10) % 30 == 0:
			_send_command("jump", {})
		if "netbot-forfeit" in args and elapsed > 8:
			game._net_teardown()
			get_tree().create_timer(0.1).timeout.connect(get_tree().quit)
	elif game.state == game.State.OVER and not game.net_ended and not game.net_rematch_sent:
		game._on_restart_pressed()


class SquadCard:
	extends Control
	# one squad slot in the bottom-right stack, drawn in one pass: key chip, style name,
	# spin + energy grooves, dash/jump readiness; a RESERVE countdown; OUT with a cross.
	# The plate starts 12 px in: the gutter holds the selected-slot marker.

	const GUTTER: float = 12.0
	const STATES: Array[String] = ["alive", "reserve", "out"]

	var slot: int = 0
	var style_id: String = ""
	var title: String = ""
	var state: String = "reserve" # alive | reserve | out
	var selected: bool = false
	var side: Color = HT.SIDE_YOU
	var spin: float = 0.0 # fraction of the top's spin reserve
	var energy: float = 0.0
	var dash_ok: bool = false
	var jump_ok: bool = false
	var left: float = 0.0 # reserve: seconds until it auto-launches
	var total: float = 1.0
	var words: Array = [] # SPIN ENERGY DASH JUMP RESERVE OUT "Launches in %ds" "Knocked out", in the UI language
	var _sig: int = -1
	var _plate: StyleBoxFlat = StyleBoxFlat.new()
	var _groove: StyleBoxFlat = HT.groove_box()
	var _weave: StyleBoxTexture = HT.songket_box(HT.SIDE_YOU)
	var _bar: StyleBoxFlat = StyleBoxFlat.new()

	func _ready() -> void:
		custom_minimum_size = Vector2(242.0, 84.0)
		mouse_filter = Control.MOUSE_FILTER_STOP # click = select, like the number key
		_plate.set_corner_radius_all(6)
		_plate.shadow_color = Color(0.0, 0.0, 0.0, 0.3)
		_plate.shadow_size = 4
		_bar.set_corner_radius_all(3)

	func show_slot(p_state: String, p_selected: bool, p_side: Color, p_spin: float, p_energy: float,
			p_dash: bool, p_jump: bool, p_left: float, p_total: float, p_words: Array) -> void:
		# called every HUD tick: redraws only when something visible changed
		var sig: int = STATES.find(p_state) + 4 * int(p_selected) + 8 * int(p_dash) + 16 * int(p_jump) \
			+ 64 * roundi(p_spin * 100.0) + 8192 * roundi(p_energy) + 1048576 * roundi(p_left * 10.0)
		if sig == _sig and p_side == side and p_words == words:
			return
		_sig = sig
		state = p_state
		selected = p_selected
		side = p_side
		spin = p_spin
		energy = p_energy
		dash_ok = p_dash
		jump_ok = p_jump
		left = p_left
		total = p_total
		words = p_words
		queue_redraw()

	func _text(pos: Vector2, text: String, font_size: int, col: Color, align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT, width: float = -1.0) -> void:
		var f: Font = get_theme_default_font()
		draw_string_outline(f, pos, text, align, width, font_size, 3, HT.WOOD_EDGE)
		draw_string(f, pos, text, align, width, font_size, col)

	func _fill(rect: Rect2, frac: float, box: StyleBox) -> void:
		draw_style_box(_groove, rect)
		if frac > 0.005:
			draw_style_box(box, Rect2(rect.position, Vector2(maxf(rect.size.x * clampf(frac, 0.0, 1.0), 4.0), rect.size.y)))

	func _draw() -> void:
		if words.is_empty():
			return # not shown yet: the first show_slot brings the words
		var out: bool = state == "out"
		_plate.bg_color = Color(HT.WOOD_EDGE, 0.6 if out else 0.88)
		_plate.border_color = side if selected else Color(HT.SONGKET_GOLD, 0.35)
		_plate.set_border_width_all(2 if selected else 1)
		draw_style_box(_plate, Rect2(GUTTER, 0.0, size.x - GUTTER, size.y))
		if selected: # marker in the gutter, pointing at the card
			draw_colored_polygon(PackedVector2Array([Vector2(1.0, 32.0), Vector2(9.0, 42.0), Vector2(1.0, 52.0)]), side)
		var x0: float = GUTTER + 10.0
		var right: float = size.x - 10.0
		# key chip: the number key that selects this slot
		var chip: Rect2 = Rect2(x0, 10.0, 24.0, 24.0)
		draw_rect(chip, side if selected else HT.WOOD_DARK)
		draw_rect(chip, Color(HT.SONGKET_GOLD, 0.6), false, 1.0)
		draw_string(FONT_TITLE, Vector2(x0, 30.0), str(slot + 1), HORIZONTAL_ALIGNMENT_CENTER, 24.0, 18, HT.INK if selected else HT.TEXT_COLOR)
		if out:
			draw_line(chip.position + Vector2(3.0, 3.0), chip.end - Vector2(3.0, 3.0), HT.DANGER, 3.0, true)
			draw_line(Vector2(chip.end.x - 3.0, chip.position.y + 3.0), Vector2(chip.position.x + 3.0, chip.end.y - 3.0), HT.DANGER, 3.0, true)
		var tx: float = x0 + 34.0
		_text(Vector2(tx, 28.0), title, 14, HT.TEXT_DIM if out else (side if selected else HT.TEXT_COLOR))
		match state:
			"alive":
				# readiness: a lit dot + word when dash / jump can fire now
				var f: Font = get_theme_default_font()
				var x: float = right
				for i: int in [3, 2]:
					var ok: bool = jump_ok if i == 3 else dash_ok
					var w: float = f.get_string_size(words[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
					x -= w
					_text(Vector2(x, 27.0), words[i], 11, HT.TEXT_COLOR if ok else Color(HT.TEXT_DIM, 0.6))
					x -= 8.0
					draw_circle(Vector2(x, 23.0), 3.5, HT.SONGKET_GOLD if ok else Color(HT.TEXT_DIM, 0.35))
					x -= 10.0
				var bx: float = tx + 48.0
				var bw: float = right - 40.0 - bx
				_text(Vector2(tx, 53.0), words[0], 11, HT.TEXT_DIM)
				_weave.modulate_color = side
				_fill(Rect2(bx, 44.0, bw, 9.0), spin, _weave)
				_text(Vector2(right - 38.0, 54.0), "%d%%" % roundi(spin * 100.0), 13, HT.TEXT_COLOR, HORIZONTAL_ALIGNMENT_RIGHT, 38.0)
				_text(Vector2(tx, 72.0), words[1], 11, HT.TEXT_DIM)
				_bar.bg_color = HT.DANGER if energy < 20.0 else HT.ENERGY_BLUE
				_fill(Rect2(bx, 64.0, bw, 7.0), energy / 100.0, _bar)
				_text(Vector2(right - 38.0, 73.0), str(roundi(energy)), 13, HT.DANGER if energy < 20.0 else HT.TEXT_COLOR, HORIZONTAL_ALIGNMENT_RIGHT, 38.0)
			"reserve":
				_text(Vector2(right - 120.0, 27.0), words[4], 11, side, HORIZONTAL_ALIGNMENT_RIGHT, 120.0)
				var soon: bool = left <= 3.0
				_text(Vector2(tx, 55.0), words[6] % ceili(left), 13, HT.DANGER if soon else HT.TEXT_COLOR)
				_bar.bg_color = Color(HT.DANGER if soon else side, 0.8)
				_fill(Rect2(tx, 63.0, right - tx, 6.0), left / maxf(total, 0.01), _bar)
			_:
				_text(Vector2(right - 120.0, 27.0), words[5], 12, HT.DANGER, HORIZONTAL_ALIGNMENT_RIGHT, 120.0)
				_text(Vector2(tx, 58.0), words[7], 13, HT.TEXT_DIM)
