extends SceneTree
## Run: Godot --headless --path . --script scripts/feature_checks.gd -- --test-mode

var game: Node
var arena: Node
var failures: int = 0
var checks: int = 0


class ResultSink extends Node:
	var real_game: Node
	var net_active: bool = false
	var _netbot: bool = false
	var wind_meter: Control
	var wind_hint: Control
	var aim_arrow: Node3D
	var results: int = 0

	func _award_style_xp(styles: Array, won: bool) -> void:
		real_game._award_style_xp(styles, won)

	func _save_workshop() -> void:
		pass # The actual game's test mode suppresses persistence.

	func _arena_round_finished(_winner: int) -> void:
		results += 1 # Capture completion without starting campaign or rematch timers.


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
	_check_keybinds_and_designs()
	_check_progression()
	_check_migration()
	_check_commands()
	_check_collisions()
	_check_reserves_and_timeout()
	_check_results()
	print("feature_checks: %d checks, %d failures" % [checks, failures])
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
	expect(game.loadout == ["kelantan", "uri", "jantung"] and game._style_level("kelantan") == 1 and game.difficulty == 1, "v2 gains safe squad, level and difficulty defaults")
	legacy.set_value("workshop", "style_xp", {"jantung": -20, "uri": 1e30, "kelantan": NAN, "unknown": 100})
	legacy.set_value("workshop", "loadout", ["unknown", "pakdin", "uri", "jantung"])
	legacy.set_value("workshop", "difficulty", NAN)
	game._load_workshop(legacy)
	expect(game._style_level("jantung") == 1 and game._style_level("uri") == 5 and game._style_level("kelantan") == 1 and not game.style_xp.has("unknown"), "Corrupt XP is bounded and unknown styles ignored")
	expect(game.loadout == ["kelantan", "uri", "uri"] and game.difficulty == 1, "Invalid, locked and excess loadout entries are ignored")
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
	arena.top_at(2, 0).spin *= 0.6
	expect(arena.timeout_winner() == 1, "Normalized spin breaks equal-count timeout ties")
	arena._deployed(arena.round_id, 2, 1, 55.0, 0.0)
	expect(arena.timeout_winner() == 2, "Surviving top count ranks before spin at timeout")
	arena.disconnected.append(2)
	expect(arena.timeout_winner() == 1, "Disconnected players cannot win the timeout")


func _check_results() -> void:
	fixture()
	game.style_xp.clear()
	var sink: ResultSink = ResultSink.new()
	sink.real_game = game
	sink.wind_meter = game.wind_meter
	sink.wind_hint = game.wind_hint
	sink.aim_arrow = game.aim_arrow
	root.add_child(sink)
	arena.game = sink
	arena._result(arena.round_id, 1, {1: 1, 2: 0})
	var earned: Dictionary = game.style_xp.duplicate()
	arena._result(arena.round_id, 1, {1: 2, 2: 0})
	arena._result(arena.round_id - 1, 2, {1: 0, 2: 9})
	expect(sink.results == 1 and arena.scores == {1: 1, 2: 0} and game.style_xp == earned and earned.get("jantung") == 30, "Duplicate and stale results cannot award XP or scores twice")
	expect(not arena.top_at(1, 0).battling, "Applying a result freezes the remaining tops")
	arena.game = game
	sink.queue_free()
	arena.reset()
