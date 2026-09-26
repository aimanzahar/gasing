extends SceneTree
## Run: Godot --headless --path . --script scripts/feature_checks.gd -- --test-mode

var game: Node
var arena: Node
var failures: int = 0
var checks: int = 0


class ResultSink extends Node:
	# Stands in for main.gd under arena _result/_eliminated/_deployed/collisions/fx:
	# records effects instead of starting panels, timers or campaign flow.
	var real_game: Node
	var net_active: bool = false
	var _netbot: bool = false
	var lang: String = "en"
	var endless_mode: bool = false
	var duel_index: int = 0
	var menus: Node = null
	var player_top: Gasing
	var foe_top: Gasing
	var wind_meter: Control
	var wind_hint: Control
	var aim_arrow: Node3D
	var STYLE_DEFS: Dictionary
	var PLAYER_COLOR: Color
	var DANGER: Color
	var SND_LAUNCH: AudioStream
	var results: int = 0
	var last_reason: Dictionary = {}
	var last_hit_strength: float = -1.0
	var calls: Array[String] = []

	func _init(game_node: Node) -> void:
		real_game = game_node
		wind_meter = game_node.wind_meter
		wind_hint = game_node.wind_hint
		aim_arrow = game_node.aim_arrow
		STYLE_DEFS = game_node.STYLE_DEFS
		PLAYER_COLOR = game_node.PLAYER_COLOR
		DANGER = game_node.DANGER
		SND_LAUNCH = game_node.SND_LAUNCH

	func _award_style_xp(styles: Array, won: bool) -> void:
		real_game._award_style_xp(styles, won)

	func _save_workshop() -> void:
		pass # The actual game's test mode suppresses persistence.

	func _arena_round_finished(_winner: int, reason: Dictionary = {}) -> void:
		results += 1 # Capture completion without starting campaign or rematch timers.
		last_reason = reason

	func _wind_effectiveness(power: float) -> float:
		return real_game._wind_effectiveness(power)

	func _style_accent(id: String) -> Color:
		return real_game._style_accent(id)

	func _current_opponent() -> Dictionary:
		return real_game._current_opponent()

	func _hit_effects(_contact: Vector3, strength: float, kind: String = "hit", _tint: Color = Color()) -> void:
		calls.append("fx:" + kind)
		if kind == "hit":
			last_hit_strength = strength

	func _play_action_sfx(kind: String, _pitch: float = 1.0) -> void:
		calls.append("sfx:" + kind)

	func _play_sfx(_stream: AudioStream, _volume_db: float = 0.0, _pitch_jitter: float = 0.1, _pitch: float = 1.0) -> void:
		pass

	func _banner(text: String, _color: Color, sub: String = "") -> void:
		calls.append("banner:%s|%s" % [text, sub])

	func _hint(key: String) -> void:
		calls.append("hint:" + key)

	func _toast(text: String, _color: Color, _world_pos: Vector3, _big: bool) -> void:
		calls.append("toast:" + text)

	func _toast_elimination(_top: Gasing, reason: String) -> void:
		calls.append("out:" + reason)

	func _t(key: String) -> String:
		return real_game._t(key)


func _initialize() -> void:
	if not "--test-mode" in OS.get_cmdline_user_args():
		push_error("Feature checks require -- --test-mode; real workshop data must remain untouched.")
		quit(2)
		return
	_run.call_deferred()


func expect(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(message)


func _run() -> void:
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	await process_frame
	game.process_mode = Node.PROCESS_MODE_DISABLED
	for _frame: int in 30:
		arena = game.get("arena")
		if is_instance_valid(arena):
			break
		await process_frame
	if not is_instance_valid(arena):
		push_error("main.tscn must attach its arena controller before checks run.")
		quit(1)
		return
	expect(game._test_mode, "Test mode must be set before workshop loading")
	expect(Gasing.run_action_checks(), "Gasing action, lifetime and puppet self-checks")
	var saved_lang: String = game.lang
	game.lang = "xx"
	expect(game._t("prompt") == game.STRINGS["en"]["prompt"] and game._t("no_such_key") == "no_such_key", "_t falls back to English, then to the key")
	game.lang = saved_lang
	game._on_lang_pressed("fr") # a hand-edited settings.cfg
	expect(game.lang == saved_lang, "An unknown language code is ignored, never applied")
	expect(load("res://scripts/heritage_theme.gd").run_checks(), "Heritage theme self-checks")
	_check_keybinds_and_designs()
	_check_progression()
	_check_migration()
	_check_commands()
	await _check_selection()
	_check_roster_order()
	_check_collisions()
	_check_impact_tiers()
	_check_reserves_and_timeout()
	_check_wind_timeout()
	_check_squad_hud()
	_check_results()
	_check_duel_flow()
	_check_music()
	_check_curtain()
	_check_mp_round_break()
	_check_forfeit()
	_check_reserve_steer()
	_check_left_before_battle()
	_check_banner_clears_toasts()
	_check_locked_fight()
	_check_strings()
	await _check_round_advance()
	_check_volume_slider()
	_check_atomic_save()
	print("feature_checks: %d checks, %d failures" % [checks, failures])
	for p: Node in game.find_children("*", "AudioStreamPlayer", true, false):
		(p as AudioStreamPlayer).stop() # a bed or SFX still streaming at quit can leak its Ogg playback (an exit-time race)
	await create_timer(0.1).timeout # let the mixer release the stopped playbacks
	game.queue_free()
	await process_frame
	quit(1 if failures else 0)


func _check_keybinds_and_designs() -> void:
	for binding: Array in [[KEY_SPACE, "arena_jump"], [KEY_E, "arena_rush"], [KEY_SHIFT, "arena_dash"], [KEY_W, "arena_up"]]:
		var event: InputEventKey = InputEventKey.new()
		event.keycode = binding[0]
		event.pressed = true
		expect(event.is_action_pressed(binding[1]), "Logical keycode %s activates its arena action" % binding[1])
		event.pressed = false
		expect(event.is_action_released(binding[1]), "Logical keycode %s releases its arena action" % binding[1])
	for style: String in game.STYLE_DEFS:
		for level: int in range(1, 6):
			var top: Gasing = load("res://gasing.tscn").instantiate()
			game.add_child(top)
			var stats: Dictionary = game.STYLE_DEFS[style].duplicate()
			stats.level = level
			top.setup("Inspect", str(stats.shape), stats, Color.GOLD)
			var bands: int = 0
			for child: Node in top.get_node("Visual").get_children():
				if child is MeshInstance3D and child.mesh is TorusMesh:
					bands += 1
			expect(top.level == level and bands == level - 1, "%s level %d has its earned visual bands" % [style, level])
			top.free()


func _check_progression() -> void:
	game.style_xp.clear()
	for pair: Array in [[0, 1], [99, 1], [100, 2], [249, 2], [250, 3], [449, 3], [450, 4], [699, 4], [700, 5]]:
		game.style_xp.jantung = pair[0]
		expect(game._style_level("jantung") == pair[1], "XP boundary %d" % pair[0])
	var forged: Dictionary = game.player_shapes.jantung.duplicate()
	var stats: Dictionary = game._style_battle_stats("jantung")
	expect(is_equal_approx(stats.mass, forged.mass + 0.16) and is_equal_approx(stats.spin_reserve, forged.spin_reserve + 16.0) and is_equal_approx(stats.balance, forged.balance + 4.0), "Level five applies four stat bonuses")
	expect(stats == game._style_battle_stats("jantung") and game.player_shapes.jantung == forged, "Derived bonuses never compound or alter forging")
	game.net_active = true
	var normalized: Dictionary = game._style_battle_stats("jantung")
	expect(normalized.mass == game.STYLE_DEFS.jantung.mass and normalized.spin_reserve == game.STYLE_DEFS.jantung.spin_reserve and normalized.balance == game.STYLE_DEFS.jantung.balance and normalized.level == 5, "MP retains cosmetic level but normalizes every combat stat")
	game.net_active = false
	game.style_xp.clear()
	game._award_style_xp(["jantung", "jantung", "unknown", "kelantan"], true)
	expect(game.style_xp.get("jantung") == 30 and not game.style_xp.has("uri") and not game.style_xp.has("kelantan"), "Only unique, owned, deployed styles earn XP")
	game._award_style_xp(["uri"], false)
	expect(game.style_xp.uri == 15, "Defeat still awards participation XP")
	game.style_xp.jantung = 695
	game._award_style_xp(["jantung"], true)
	expect(game.style_xp.jantung == 700, "XP caps at max level")


func _check_migration() -> void:
	var legacy: ConfigFile = ConfigFile.new()
	legacy.set_value("workshop", "version", 2)
	legacy.set_value("workshop", "coins", 123)
	legacy.set_value("workshop", "unlocked", ["jantung", "uri", "kelantan"])
	legacy.set_value("workshop", "selected", "kelantan")
	legacy.set_value("workshop", "materials", {"merbau": 4})
	legacy.set_value("workshop", "shapes", {"kelantan": {"mass": 2.6, "balance": 81.0}})
	legacy.set_value("workshop", "accents", {"kelantan": Color.CORAL})
	legacy.set_value("workshop", "defeated", ["kelantan"])
	legacy.set_value("workshop", "endless_best", 8)
	game._load_workshop(legacy)
	expect(game.coins == 123 and game.materials_owned.merbau == 4 and game.endless_best == 8 and game.defeated_masters.has("kelantan"), "v2 migration preserves economy and accomplishments")
	expect(game.player_shapes.kelantan.mass == 2.6 and game.player_shapes.kelantan.balance == 81.0 and game.style_accents.kelantan == Color.CORAL, "v2 migration preserves forging and lacquer")
	expect(game.loadout == ["kelantan", "uri", "jantung"] and game._style_level("kelantan") == 1 and game.difficulty == 0, "v2 gains safe squad, level and Normal difficulty defaults")
	legacy.set_value("workshop", "style_xp", {"jantung": -20, "uri": 1e30, "kelantan": NAN, "unknown": 100})
	legacy.set_value("workshop", "loadout", ["unknown", "pakdin", "uri", "jantung"])
	legacy.set_value("workshop", "difficulty", NAN)
	game._load_workshop(legacy)
	expect(game._style_level("jantung") == 1 and game._style_level("uri") == 5 and game._style_level("kelantan") == 1 and not game.style_xp.has("unknown"), "Corrupt XP is bounded and unknown styles ignored")
	expect(game.loadout == ["kelantan", "uri", "uri"] and game.difficulty == 0, "Invalid, locked and excess loadout entries are ignored")
	legacy.set_value("workshop", "difficulty", 2)
	legacy.set_value("workshop", "campaign_index", 99)
	game._load_workshop(legacy)
	expect(game.difficulty == 2 and game.campaign_index == game.MASTERS.size() - 1, "Saved difficulty is kept and campaign progress is clamped")
	game._load_workshop() # Test mode resets defaults without reading user://.


func fixture(owners: Array = [1, 2], slots: Array = [0]) -> void:
	game.net_active = false
	arena.round_id += 1
	arena.roster.clear()
	arena.disconnected.clear()
	arena.scores.clear()
	arena.pair_cooldowns.clear()
	arena.winds.clear()
	arena.elapsed = 0.0
	arena.selected_slot = 0
	var configs: Dictionary = {}
	for id: int in owners:
		arena.roster[id] = "Test %d" % id
		configs[id] = arena.sanitize_config({})
	arena._build_participants(configs)
	arena.phase = arena.Phase.BATTLE
	for id: int in owners:
		for slot: int in slots:
			var top: Gasing = arena._make_top(id, slot)
			arena.participants[id].slots[slot].state = "alive"
			top.launch(Vector3.FORWARD, 1.0)
			top._tick_actions(0.2)
			top.position = arena.spawn_position(id, slot)
			top.velocity = Vector3.ZERO


func _check_commands() -> void:
	var clean: Dictionary = arena.sanitize_config({"slots": [{"style": "unknown", "level": NAN}, {"style": "uri", "level": 999, "stats": {"mass": 999}}, "bad", {}]})
	expect(clean.slots.size() == 3 and clean.slots[0].style == "jantung" and clean.slots[0].stats.level == 1 and clean.slots[1].stats.level == 5 and clean.slots[1].stats.mass == game.STYLE_DEFS.uri.mass, "Untrusted loadouts cannot inject stats or invalid styles")
	fixture()
	var rid: int = arena.round_id
	var top: Gasing = arena.top_at(1, 0)
	var enemy: Gasing = arena.top_at(2, 0)
	for request: Array in [[999, rid, 0], [1, rid - 1, 0], [1, rid, -1], [1, rid, 3]]:
		expect(not arena.accept_command(request[0], request[1], request[2], "dash", {"dir": Vector3.RIGHT}), "Reject wrong owner, round or slot")
	for direction: Variant in [Vector3(NAN, 0, 0), Vector3(INF, 0, 0), Vector3(3, 0, 0), Vector3.ZERO, "right"]:
		expect(not arena.accept_command(1, rid, 0, "dash", {"dir": direction}), "Reject invalid action directions")
	expect(top.energy == 100 and enemy.energy == 100, "Rejected commands cannot spend energy")
	expect(arena.accept_command(1, rid, 0, "dash", {"dir": Vector3.RIGHT, "owner": 2}) and top.energy == 80 and enemy.energy == 100, "Sender identity owns the action; payload cannot select another player")
	expect(arena.accept_command(1, rid, 1, "select", {}) and not arena.accept_command(1, rid, 0, "jump", {}), "Actions address only the selected slot")
	expect(not arena.accept_command(1, rid, 1, "deploy", {"power": NAN, "angle": 0.0}) and not arena.accept_command(1, rid, 1, "deploy", {"power": 101, "angle": 0.0}), "Reserve launch validates charge")
	expect(arena.accept_input(1, rid, 1, 1, Vector3.RIGHT, Vector3.FORWARD, true), "Valid selected-slot input is accepted")
	expect(not arena.accept_input(1, rid, 1, 1, Vector3.LEFT, Vector3.FORWARD, false) and not arena.accept_input(1, rid, 2, 1, Vector3(NAN, 0, 0), Vector3.FORWARD, true), "Stale or NaN input frames cannot replace good input")
	arena.disconnected.append(1)
	expect(not arena.accept_command(1, rid, 1, "select", {}) and not arena.accept_input(1, rid, 3, 1, Vector3.ZERO, Vector3.FORWARD, false), "Disconnected players cannot control reserves or live tops")


func _check_selection() -> void:
	fixture([1, 2], [0, 1])
	arena._eliminated(arena.round_id, 1, 0, "topple")
	await process_frame # auto-select is deferred
	expect(arena.selected_slot == 1 and arena.participants[1].selected == 1, "Losing the selected top hands control to a live top")
	arena._eliminated(arena.round_id, 1, 1, "ringout")
	await process_frame
	expect(arena.selected_slot == 2 and arena.participants[1].slots[2].state == "reserve", "With no live top left, control moves to the next reserve")
	arena.select_slot(0)
	expect(arena.selected_slot == 2, "select_slot refuses a knocked-out slot")


func _check_roster_order() -> void:
	fixture()
	arena.roster.clear()
	var configs: Dictionary = {}
	for id: int in [1, 2, 3]:
		arena.roster[id] = "Test %d" % id
	for id: int in [3, 2, 1]: # ready order is the reverse of roster order
		configs[id] = arena.sanitize_config({})
	arena._build_participants(configs)
	var first_order: Array = arena.participants.keys()
	var third_color: Color = arena.participants[3].color
	arena.disconnected.append(2)
	arena._build_participants(configs)
	expect(first_order == [1, 2, 3] and arena.participants.keys() == [1, 3] and third_color == arena.COLORS[2] and arena.participants[3].color == third_color, "Participants follow roster order and keep their colour after a disconnect")
	arena.disconnected.clear()
	expect(arena.unique_names({5: "User", 9: "User", 12: "Ali", 14: "User"}) == {5: "User", 9: "User 2", 12: "Ali", 14: "User 3"}, "LAN players sharing an OS user name get numbered seats")


func _check_collisions() -> void:
	fixture([1, 2], [0, 1])
	var a: Gasing = arena.top_at(1, 0)
	var b: Gasing = arena.top_at(2, 0)
	var c: Gasing = arena.top_at(1, 1)
	var d: Gasing = arena.top_at(2, 1)
	a.position = Vector3(-2, 0, 0)
	b.position = Vector3(-1.2, 0, 0)
	c.position = Vector3(1.2, 0, 0)
	d.position = Vector3(2, 0, 0)
	arena.collisions(0.1)
	expect(a.spin < a.launch_spin and b.spin < b.launch_spin and c.spin < c.launch_spin and d.spin < d.launch_spin and arena.pair_cooldowns.size() == 2, "Independent pairs collide during the same frame")
	var spin_before: float = b.spin
	a.set_rush(true, Vector3.RIGHT)
	a._tick_actions(0.1)
	arena.collisions(0.1)
	expect(is_equal_approx(b.spin, spin_before - 1.2), "Rush drains opponent spin during the pair impulse cooldown")
	spin_before = b.spin
	a.energy = 1.0
	a._tick_actions(0.1)
	arena.collisions(0.1)
	expect(is_equal_approx(b.spin, spin_before - 0.6) and is_zero_approx(a.energy), "Partial energy pays only for proportional rush contact damage")
	spin_before = b.spin
	a._tick_actions(0.01)
	arena.collisions(0.01)
	expect(is_equal_approx(b.spin, spin_before), "Exhausted rush cannot keep damaging an opponent")
	for direction: Vector3 in [Vector3.LEFT, Vector3.FORWARD]:
		a.energy = 100.0
		a.set_rush(true, direction)
		a._tick_actions(0.01)
		spin_before = b.spin
		arena.collisions(0.01)
		expect(a.rush_paid_seconds > 0.0 and is_equal_approx(b.spin, spin_before), "Paid rush cannot damage opponents behind or beside its forward cone")
	fixture([1], [0, 1])
	a = arena.top_at(1, 0)
	b = arena.top_at(1, 1)
	a.position = Vector3.ZERO
	b.position = Vector3(0.2, 0, 0)
	a.set_rush(true, Vector3.RIGHT)
	a._tick_actions(0.1)
	arena.collisions(0.1)
	expect(a.spin == a.launch_spin and b.spin == b.launch_spin and a.position.distance_to(b.position) >= a.radius + b.radius - 0.001, "Friendly tops separate without hit or rush damage")
	fixture()
	a = arena.top_at(1, 0)
	b = arena.top_at(2, 0)
	a.position = Vector3(0, 0.8, 0)
	b.position = Vector3(0.2, 0, 0)
	arena.collisions(0.1)
	expect(a.spin == a.launch_spin and b.spin == b.launch_spin and arena.pair_cooldowns.is_empty(), "Airborne tops clear grounded collisions")
	a.position.y = 0.0
	arena.collisions(0.1)
	expect(a.spin < a.launch_spin and b.spin < b.launch_spin, "Collision resumes after landing")


func _check_impact_tiers() -> void:
	# Tier and spin bite key on the faster top's own speed, not the closing speed.
	fixture()
	var sink: ResultSink = ResultSink.new(game)
	root.add_child(sink)
	arena.game = sink
	var a: Gasing = arena.top_at(1, 0)
	var b: Gasing = arena.top_at(2, 0)
	var strengths: Array[float] = []
	for speeds: Vector2 in [Vector2(Gasing.MOVE_SPEED, Gasing.MOVE_SPEED), Vector2(5.0, 0.0)]:
		arena.pair_cooldowns.clear()
		a.position = Vector3.ZERO
		b.position = Vector3.RIGHT * (a.radius + b.radius)
		a.velocity = Vector3.ZERO
		b.velocity = Vector3.ZERO
		a.control_velocity = Vector3.RIGHT * speeds.x
		b.control_velocity = Vector3.LEFT * speeds.y
		arena.collisions(0.01)
		strengths.append(sink.last_hit_strength)
	expect(strengths[0] < 3.5 and strengths[1] >= 3.5, "Two tops steering into each other clash; only a dash-speed ram is a big hit")
	arena.game = game
	sink.queue_free()


func _check_reserves_and_timeout() -> void:
	fixture()
	var first: Gasing = arena.top_at(1, 0)
	arena.elapsed = 29.9
	arena._reserves_tick(0.0)
	expect(arena.live_tops(1).size() == 1, "Reserve two waits until its deadline")
	arena.elapsed = 30.0
	arena._reserves_tick(0.0)
	expect(arena.live_tops(1).size() == 2 and arena.top_at(1, 0) == first, "Reserve two launches without replacing the spinning first top")
	arena.elapsed = 45.0
	arena._reserves_tick(0.0)
	expect(arena.live_tops(1).size() == 3, "Reserve three cannot stall beyond its deadline")
	fixture()
	arena.participants[1].slots[0].state = "out"
	arena.top_at(1, 0).alive = false
	arena.resolve_eliminations()
	expect(arena.phase == arena.Phase.BATTLE, "A player with reserves has not lost")
	arena._reserves_tick(0.1)
	arena._reserves_tick(4.9)
	expect(arena.live_tops(1).is_empty() and arena.participants[1].grace > 0, "Last-top loss provides a five-second deployment grace")
	arena._reserves_tick(0.2)
	expect(arena.live_tops(1).size() == 1 and arena.participants[1].slots[1].state == "alive", "Grace expiry automatically deploys the next reserve")
	fixture()
	expect(arena.timeout_winner() == 0, "Equal surviving tops and normalized spin is a draw")
	expect(arena._timeout_reason(0).kind == "draw", "An even timeout reads as a draw")
	arena.top_at(2, 0).spin *= 0.6
	expect(arena.timeout_winner() == 1, "Normalized spin breaks equal-count timeout ties")
	var reason: Dictionary = arena._timeout_reason(1)
	expect(reason.kind == "time_spin" and reason.spins == {1: 100, 2: 60} and arena.leading_id() == 1, "An equal-count timeout reads each side's spin %, as the top labels show it")
	arena._deployed(arena.round_id, 2, 1, 55.0, 0.0)
	expect(arena.timeout_winner() == 2, "Surviving top count ranks before spin at timeout")
	reason = arena._timeout_reason(2)
	expect(reason.kind == "time_count" and reason.counts == {1: 1, 2: 2}, "A top-count timeout is explained by live top counts")
	arena.disconnected.append(2)
	expect(arena.timeout_winner() == 1, "Disconnected players cannot win the timeout")
	fixture([1, 2, 3]) # FFA: 1 and 2 tie on two tops, 3 has one top at full spin
	arena._deployed(arena.round_id, 1, 1, 90.0, 0.0)
	arena._deployed(arena.round_id, 2, 1, 90.0, 0.0)
	arena.top_at(2, 0).spin *= 0.6
	reason = arena._timeout_reason(arena.timeout_winner())
	expect(arena.timeout_winner() == 1 and reason.kind == "time_spin" and reason.spins.has(2) and not reason.spins.has(3), "A spin tiebreak compares only the seats tied on tops")


func _check_wind_timeout() -> void:
	# Nobody wound: the WIND timer's forced opening launch is an auto-launch, never graded.
	fixture()
	for id: int in [1, 2]:
		arena.participants[id].slots[0].state = "reserve"
	arena.phase = arena.Phase.WIND
	arena.wind_elapsed = arena.WIND_SECONDS
	arena._physics_process(0.0)
	expect(arena.phase == arena.Phase.BATTLE and arena.last_launch_grade == "weak" and arena.auto_winds.has(1), "A WIND timeout launches the idle player as an ungraded auto-launch")
	expect(game._hints_shown.is_empty(), "One-shot tutorial hints are skipped in test mode")
	game.endless_mode = true
	game.duel_index = 0
	var endless_first: bool = arena._tutorial_duel()
	game.net_active = true
	var online: bool = arena._tutorial_duel()
	game.net_active = false
	game.endless_mode = false
	expect(endless_first and not online, "Endless wave 1 teaches like campaign duel 1; an MP match never does")


func _check_results() -> void:
	fixture()
	game.style_xp.clear()
	var sink: ResultSink = ResultSink.new(game)
	root.add_child(sink)
	arena.game = sink
	var rid: int = arena.round_id
	arena._deployed(rid, 1, 1, 90.0, 0.0)
	expect(arena.last_launch_grade == "perfect" and arena.round_stats[1].perfect == 1 and sink.calls.has("toast:PERFECT!") and not sink.calls.has("banner:PERFECT!|"), "A manual 80-95 reserve launch is graded PERFECT and counted, as a toast (no band over the dish mid-fight)")
	arena._deployed(rid, 1, 2, 90.0, 0.0, true)
	expect(arena.last_launch_grade == "weak" and arena.round_stats[1].perfect == 1 and sink.calls.has("toast:Reserve 3 auto-launched"), "Auto-launches are announced and never graded PERFECT")
	arena.top_at(2, 0).set_meta("last_hit_by", 1)
	arena._eliminated(rid, 2, 0, "ringout")
	expect(arena.round_stats[1].ringouts == 1 and arena.round_stats[1].kos == 0 and sink.calls.has("fx:ko") and sink.calls.has("out:ringout"), "A ring-out is credited to the last opponent contact")
	arena.elapsed = arena.ROUND_SECONDS
	arena.resolve_eliminations() # player 2 still holds reserves, so the clock decides
	var earned: Dictionary = game.style_xp.duplicate()
	arena._result(rid, 1, {1: 2, 2: 0})
	arena._result(rid - 1, 2, {1: 0, 2: 9})
	expect(sink.results == 1 and arena.scores == {1: 1} and game.style_xp == earned and earned.get("jantung") == 30, "Duplicate and stale results cannot award XP or scores twice")
	expect(sink.last_reason.get("kind") == "time_count" and sink.last_reason.counts == {1: 3, 2: 0} and arena.round_stats[1].ringouts == 1, "The round result carries its reason and the authority's stats")
	var survivor: Gasing = arena.top_at(1, 0)
	expect(arena.phase == arena.Phase.RESULT and survivor.battling and survivor.round_over and not survivor.dash(Vector3.RIGHT), "Applying a result keeps tops spinning but refuses their actions")
	arena.game = game
	sink.queue_free()
	arena.reset()


func _check_duel_flow() -> void:
	expect(game._duel_outcome({1: 2}) == 1 and game._duel_outcome({2: 2}) == -1 and game._duel_outcome({1: 1, 2: 1}) == 0 and game._duel_outcome({}) == 0, "A best-of-3 duel is decided at two wins")
	var previous: float = game._wind_effectiveness(95.0)
	var falling: bool = true
	for power: float in [96.0, 97.0, 98.0, 99.0, 100.0]:
		var effect: float = game._wind_effectiveness(power)
		falling = falling and effect < previous
		previous = effect
	expect(is_equal_approx(game._wind_effectiveness(95.0), 1.0) and is_equal_approx(previous, 0.55) and falling, "Overwinding past 95 fades to 0.55 instead of a cliff")
	game.selected_shape = "jantung"
	game.materials_owned.merbau = 1
	game.player_shapes.jantung.mass = 3.0
	game._on_material_pressed("merbau")
	var capped_kept: bool = game.materials_owned.merbau == 1 and game.player_shapes.jantung.mass == 3.0
	game.player_shapes.jantung.mass = 2.0
	game._on_material_pressed("merbau")
	expect(capped_kept and game.materials_owned.merbau == 0 and is_equal_approx(game.player_shapes.jantung.mass, 2.3), "Forging spends a material only when it changes the top")
	game.endless_mode = false
	game.duel_index = game.MASTERS.size() - 1
	game._finish_duel(true)
	var after_final: int = game.campaign_index
	game.duel_index = 2
	game.campaign_index = 2
	game._finish_duel(false)
	expect(after_final == 0 and game.campaign_index == 0, "Beating the last master or losing a duel resets campaign progress before the panel times out")
	game._enter_state(game.State.READY) # disarms the pending _after_round timers
	game._load_workshop() # Test mode resets defaults without reading user://.
	for kind: String in ["hit", "grind", "rim", "land", "ko"]:
		for strength: float in [0.5, 2.5, 4.0]:
			game._hit_effects(Vector3.ZERO, strength, kind)
	expect(Engine.time_scale == 1.0 and game._trauma > 0.0, "Every hit-effect tier runs, and test mode never warps time")
	# a rush re-scores 'big' every 0.3 s: the hit-stop + PANGKAH! share one 1 s cooldown
	# (test mode never warps time, so the shared cooldown stands in for the hit-stop)
	game._pangkah_next = 0
	var t0: int = Time.get_ticks_msec()
	game._hit_effects(Vector3.ZERO, 4.0, "hit")
	var armed: int = game._pangkah_next
	game._pangkah_next -= 700 # as if 0.7 s had passed
	game._hit_effects(Vector3.ZERO, 4.0, "hit")
	expect(armed >= t0 + 1000 and game._pangkah_next == armed - 700, "A big hit 0.7 s after another does not re-arm the shared PANGKAH!/hit-stop cooldown (1 s)")
	game.endless_mode = true
	game.campaign_index = 2
	game._enter_state(game.State.READY)
	var space: InputEventKey = InputEventKey.new()
	space.keycode = KEY_SPACE
	space.pressed = true
	game._unhandled_input(space)
	expect(game.state == game.State.CRAFT and not game.endless_mode and game.duel_index == 2, "Title SPACE continues the campaign, never Endless")
	game.campaign_index = 0


func _check_squad_hud() -> void:
	fixture([1, 2], [0])
	arena.participants[1].slots[2].state = "out"
	var codes: Array[int] = [9, 9, 9]
	arena._squad_codes(1, codes)
	expect(codes == [0, 1, 2], "Squad glyphs read alive / reserve / out per slot")
	arena.update_hud()
	var cards: Array = arena.slot_cards.map(func(c: Object) -> Variant: return c.get("state"))
	expect(game.player_gauge.squad == [0, 1, 2] and cards == ["alive", "reserve", "out"], "The fight bar glyphs and the squad cards agree on every slot's state")


func _playing_music() -> Array:
	return game._music.filter(func(p: AudioStreamPlayer) -> bool: return p.playing)


func _check_music() -> void:
	if game._music_key == "victory" or game._music_key == "defeat":
		game._on_music_finished(game._music[game._music_idx]) # the duel checks above left a stinger playing
	var map: Dictionary = game.STATE_MUSIC
	expect(map[game.State.READY] == "menu" and map[game.State.CRAFT] == "menu" and map[game.State.OVER] == "menu" and map[game.State.CUTSCENE] == "cutscene" 		and map[game.State.WIND] == "battle" and map[game.State.BATTLE] == "battle" and not map.has(game.State.ROUND_OVER), "Each screen maps to its music bed; the battle bed carries on between rounds")
	game._enter_state(game.State.READY)
	var bed: AudioStreamPlayer = game._music[game._music_idx]
	game._enter_state(game.State.CRAFT)
	expect(game._music_key == "menu" and game._music[game._music_idx] == bed and bed.playing and bed.stream.get("loop") == true, "The looping menu bed plays on from the title into the workshop without restarting")
	for key: String in ["battle", "cutscene", "battle"]: # rapid screen changes mid-crossfade
		game._play_music(key)
	game._music_tween.custom_step(2.0)
	var playing: Array = _playing_music()
	expect(game._music.size() == 2 and playing.size() == 1 and playing[0] == game._music[game._music_idx] and game._music_key == "battle", "Crossfades reuse two players and settle on exactly one bed")
	game._play_music("victory")
	game._play_music("menu") # a state change during the stinger only queues the bed
	var stinger: AudioStreamPlayer = game._music[game._music_idx]
	expect(game._music_key == "victory" and stinger.stream.get("loop") == false and game._music_bed == "menu", "A stinger plays once and is never cut off by the next screen's bed")
	game._on_music_finished(stinger)
	game._music_tween.custom_step(2.0)
	playing = _playing_music()
	expect(game._music_key == "menu" and playing.size() == 1 and playing[0].stream == game._music_streams["menu"], "When the stinger ends, the latest screen's bed fades back in")


func _check_curtain() -> void:
	game._enter_state(game.State.READY)
	game._test_mode = false # the curtain only runs outside test mode; nothing below saves
	game._enter_state(game.State.CRAFT)
	var root_ctl: Control = game._curtain_root
	expect(game.state == game.State.CRAFT and game.craft_panel.visible and root_ctl != null and root_ctl.visible and root_ctl.mouse_filter == Control.MOUSE_FILTER_IGNORE, "The curtain wipe overlays a state change that has already happened and never blocks input")
	game._test_mode = true
	game._curtain_tween.kill()
	root_ctl.hide()


func _check_mp_round_break() -> void:
	# MP rounds go ROUND_OVER -> CRAFT (loadout) -> WIND: that loadout keeps the battle bed and never wipes
	game._play_music("battle")
	game.net_active = true
	game.state = game.State.ROUND_OVER
	game._test_mode = false # the curtain only runs outside test mode; nothing below saves
	game._enter_state(game.State.CRAFT)
	var wiped: bool = game._curtain_root.visible
	var kept: bool = game._music_key == "battle"
	game._enter_state(game.State.READY) # leaving the match still wipes and brings the menu bed back
	var left_wiped: bool = game._curtain_root.visible
	game._test_mode = true
	game.net_active = false
	game._curtain_tween.kill()
	game._curtain_root.hide()
	game._music_tween.custom_step(2.0) # settle the crossfade on one bed, as _check_music does
	expect(kept and not wiped and left_wiped and game._music_key == "menu", "An MP between-round loadout keeps the battle bed and skips the curtain; leaving still wipes")
	fixture()
	game.net_active = true
	game._arena_round_finished(2, {"kind": "ko"})
	var verdict: String = game.round_label.text
	game.net_active = false
	game._enter_state(game.State.READY)
	expect(verdict == game._t("round_lost") % "Test 2", "An MP round verdict names the round, not the duel: the match goes on")


func _check_forfeit() -> void:
	# pause FORFEIT DUEL loses a live campaign duel (no free replay from 0-0); workshop BACK keeps the campaign
	game.endless_mode = false
	game.campaign_index = 3
	game.state = game.State.BATTLE
	game._forfeit_duel()
	var forfeited: bool = game.campaign_index == 0 and game.state == game.State.READY
	game.campaign_index = 3
	game._enter_state(game.State.CRAFT)
	game._leave_to_title()
	expect(forfeited and game.campaign_index == 3 and game.state == game.State.READY, "Forfeiting a live duel ends the run; leaving the workshop keeps the campaign")
	game.campaign_index = 0
	# alt-tab on a round panel: the flag makes the next WIND open the pause (that pause itself
	# is gated off in test mode, so only the focus bookkeeping is checked here)
	game.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	var away: bool = game.get("_app_unfocused") == true
	game.notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	expect(away and game.get("_app_unfocused") == false, "Losing app focus is remembered until focus returns")


func _check_reserve_steer() -> void:
	# a reserve selected mid-fight leaves its last live top steering (the host's last_live)
	fixture([1, 2], [0, 1])
	arena.update_hud() # the bars start on slot 0 and its nearest foe top
	var steer: Gasing = arena.top_at(1, 1)
	steer.spin = 0.4 * steer.spin_reserve
	game.player_gauge.shown = 1.0
	arena.select_slot(1)
	arena.update_hud()
	var player_reset: bool = is_equal_approx(game.player_gauge.shown, 0.4)
	var other: Gasing = arena.top_at(2, 1 - game.foe_top.slot_id)
	other.spin = 0.5 * other.spin_reserve
	other.position = steer.position + Vector3(0.6, 0.0, 0.0) # now the nearest foe
	game.foe_gauge.shown = 1.0
	arena.update_hud()
	expect(player_reset and game.foe_top == other and is_equal_approx(game.foe_gauge.shown, 0.5), "A fight bar switching tops starts at the new top's spin, with no orange damage trail")
	arena.select_slot(2) # charge the reserve in slot 2: slot 1 keeps steering
	arena.update_hud()
	expect(arena._hud_gauge_top == steer and steer._selected and not arena.top_at(1, 0)._selected, "While a reserve charges, the YOU bar and the ring follow the live top it leaves steering")
	arena._eliminated(arena.round_id, 1, 1, "topple") # the steered top goes out: steering moves to slot 0
	expect(arena.participants[1].last_live == 0 and arena._steer_slot == 0 and arena.top_at(1, 0)._selected, "When the top a charging reserve steers goes out, steering and the ring move to a surviving top")
	arena.aim_angle = 0.0
	Input.action_press("aim_left")
	arena._update_charge(0.1)
	var held: bool = arena.aim_angle == 0.0
	arena.phase = arena.Phase.WIND
	arena._update_charge(0.1)
	var wind_aims: bool = arena.aim_angle != 0.0
	arena.phase = arena.Phase.BATTLE
	arena.aim_angle = 0.0
	for slot: int in 2:
		arena.participants[1].slots[slot].state = "out" # the grace window: nothing left to steer
	arena._update_charge(0.1)
	var grace_aims: bool = arena.aim_angle != 0.0
	Input.action_release("aim_left")
	expect(held and wind_aims and grace_aims, "A/D steer the live top instead of swinging a charging reserve's aim; with nothing to steer, and in WIND, they aim")


func _check_left_before_battle() -> void:
	# a rival who left during WIND or the loadout is only noticed on BATTLE's first tick
	var sink: ResultSink = ResultSink.new(game)
	root.add_child(sink)
	arena.game = sink
	var kinds: Array[String] = []
	for gone: bool in [true, false]:
		fixture()
		if gone:
			arena._forfeit(arena.round_id, 2)
		else:
			for slot: int in 3:
				arena._eliminated(arena.round_id, 2, slot, "topple")
		arena.resolve_eliminations()
		kinds.append(String(sink.last_reason.get("kind", "")))
	expect(kinds == ["forfeit", "ko"], "A rival who left before BATTLE ends the round as a forfeit; a knocked-out one as a K.O.")
	arena.game = game
	sink.queue_free()
	arena.reset()


func _check_banner_clears_toasts() -> void:
	# the K.O.! banner lands the frame after the elimination toasts: it supersedes one in, or
	# rising into, its band, and a toast raised under a banner never rises into it
	if is_instance_valid(game._banner_box):
		game._banner_box.free()
	game._banner_queue.clear()
	game._toast("band check", Color.WHITE, Vector3.ZERO, false)
	var in_band: Control = game.hud.get_child(game.hud.get_child_count() - 1)
	in_band.position.y = 125.0 # centre y 150: the old floor, inside the band (y 122-192)
	game._banner("K.O.!", game.DANGER)
	var far: Vector3 = Vector3(0.0, 0.0, -6.0) # a ring-out flying past the far rim: above the band on screen
	var raw: float = game.camera.unproject_position(far + Vector3(0.0, 1.6, 0.0)).y
	game._toast("under banner", Color.WHITE, far, false)
	var under: Control = game.hud.get_child(game.hud.get_child_count() - 1)
	var band_bottom: float = game._banner_box.offset_bottom
	expect(in_band.is_queued_for_deletion(), "A banner clears a world toast inside its band")
	expect(raw - 70.0 < band_bottom and under.position.y + 25.0 - 70.0 >= band_bottom, "A toast raised under a banner ends its 70 px rise below the band")
	game._toast("second under banner", Color.WHITE, far, false) # e.g. PANGKAH! then a deny at the same top
	var second: Control = game.hud.get_child(game.hud.get_child_count() - 1)
	var beside: Vector3 = far + Vector3(1.0, 0.0, 0.0) # a neighbouring top: its long text still meets theirs
	var dx: float = game.camera.unproject_position(beside).x - game.camera.unproject_position(far).x
	game._toast("Tok Wan Nik 2 toppled beside", Color.WHITE, beside, false)
	var third: Control = game.hud.get_child(game.hud.get_child_count() - 1)
	expect(second.position.y - under.position.y >= 44.0 and dx >= 44.0 and third.position.y - second.position.y >= 44.0, "Toasts floored under a banner stack downward instead of drawing over each other, a neighbour's wide text included")
	game._banner_box.free()
	game._banner_queue.clear()
	for t: Node in game.hud.get_children():
		if t.has_meta("toast"):
			t.queue_free()


func _check_locked_fight() -> void:
	# browsing to a locked top never blocks the duel: FIGHT snaps back to the loadout and
	# fights; only an affordable top on sale turns it into BUY
	game._load_workshop() # a fresh workshop: jantung + uri, no coins
	game.endless_mode = false
	game.duel_index = 0
	game._seen_cutscenes[String(game._current_opponent().id)] = true # straight to the wind-up
	var keys: Array = game.STYLE_DEFS.keys()
	var usable: bool = true
	for id: String in ["kelantan", "datuk"]: # behind an unbeaten master; more coins than owned
		game._enter_state(game.State.CRAFT)
		game.craft_index = keys.find(id)
		game._refresh_craft()
		usable = usable and not game.fight_button.disabled and game.fight_button.text == game._t("fight")
		game._on_fight_pressed()
		usable = usable and game.craft_index == keys.find(game.loadout[game.loadout_slot]) and game.state == game.State.WIND
		game._enter_state(game.State.READY)
	expect(usable, "FIGHT on a locked or unaffordable top snaps back to the loadout and starts the duel")
	game.coins = 100
	game._enter_state(game.State.CRAFT)
	game.craft_index = keys.find("pakdin")
	game._refresh_craft()
	var buy_text: bool = game.fight_button.text == game._t("buy_prefix") + String(game.STYLE_DEFS.pakdin.label)
	game._on_fight_pressed()
	expect(buy_text and game._pending_buy == "pakdin" and game.state == game.State.CRAFT and not game.unlocked_styles.has("pakdin"), "On an affordable top for sale, FIGHT reads BUY and asks to confirm the purchase")
	game.craft_index = keys.find("kelantan") - 1 # browse on to a locked top
	game._craft_cycle(1)
	expect(game._pending_buy == "" and game.craft_info.text == game._t("pick_info"), "Browsing away from a BUY prompt clears it from the info line")
	game._enter_state(game.State.READY)
	game._load_workshop()


func _check_strings() -> void:
	var en: Array = game.STRINGS.en.keys()
	var ms: Array = game.STRINGS.ms.keys()
	en.sort()
	ms.sort()
	expect(en == ms and game.STRINGS.en.card_words.split("|").size() == 8 and game.STRINGS.ms.card_words.split("|").size() == 8, "Every UI string exists in English and Malay")


func _check_round_advance() -> void:
	var fired: Array[int] = [0]
	var bump: Callable = func() -> void: fired[0] += 1
	game._arm_round_advance(0.05, bump)
	expect(game.round_continue_button.visible and game.round_continue_button.focus_mode == Control.FOCUS_NONE, "The round panel offers CONTINUE (never keyboard-focused)")
	game.round_continue_button.pressed.emit()
	game.round_continue_button.pressed.emit() # a double click
	await create_timer(0.2).timeout
	expect(fired[0] == 1, "CONTINUE and the auto-advance timer advance the round panel exactly once")
	game._arm_round_advance(0.05, bump)
	game._arm_round_advance(30.0, bump) # the next panel, armed before the old timer fires
	await create_timer(0.2).timeout
	expect(fired[0] == 1, "A timer left over from an earlier round panel never advances the next one")
	game._reset_round_panel()
	game._on_round_timeout(game._round_token)
	expect(fired[0] == 1 and not game.round_continue_button.visible, "Resetting the panel disarms its pending advance")


func _check_volume_slider() -> void:
	game.menus.show_info("settings")
	var sliders: Array[Node] = game.menus._page.find_children("*", "HSlider", true, false)
	var bus: int = AudioServer.get_bus_index("Music")
	var slider: HSlider = (sliders[1] as HSlider) if sliders.size() == 3 else null # Master, Music, SFX
	var before: float = slider.value if slider != null else 0.0
	if slider != null:
		slider.value = 0.25
	expect(bus >= 0 and slider != null and is_equal_approx(AudioServer.get_bus_volume_db(bus), linear_to_db(0.25)), "The Music volume slider sets the Music bus level")
	if slider != null:
		slider.value = before
	game.menus.close_pause()


func _check_atomic_save() -> void:
	var dir: String = "user://feature_checks_tmp/" # never the real save path
	DirAccess.make_dir_recursive_absolute(dir)
	var path: String = dir + "save.cfg"
	var cfg: ConfigFile = ConfigFile.new()
	cfg.set_value("t", "v", 1)
	var first: Error = game._write_cfg(cfg, path)
	cfg.set_value("t", "v", 2)
	var second: Error = game._write_cfg(cfg, path)
	var loaded: ConfigFile = game._read_cfg(path)
	expect(first == OK and second == OK and loaded != null and loaded.get_value("t", "v") == 2 and not FileAccess.file_exists(path + ".tmp"), "Atomic save round-trips without leaving a temp file")
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	file.store_string("[t\nv = \"unterminated")
	file.close()
	print("feature_checks: the ConfigFile parse error below is expected (corrupt-save fallback)")
	loaded = game._read_cfg(path)
	expect(loaded != null and loaded.get_value("t", "v") == 1, "A corrupt save falls back to the previous .bak")
	for leftover: String in [path, path + ".bak", path + ".tmp"]:
		if FileAccess.file_exists(leftover):
			DirAccess.remove_absolute(leftover)
	DirAccess.remove_absolute(dir)
