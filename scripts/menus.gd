extends Node
# Pause / settings / how-to-play / credits overlay. One full-rect overlay under
# game.ui with a page stack (pause -> settings/howto/credits -> BACK). Pages are
# rebuilt on every open so the language is always current. Runs while the tree
# is paused (PROCESS_MODE_ALWAYS + TWEEN_PAUSE_PROCESS tweens).

signal closed # the overlay was dismissed (the how-to offer before the first fight waits on it)

const HT = preload("res://scripts/heritage_theme.gd")
const SETTINGS_PATH: String = "user://settings.cfg"
const BUSES: Array[String] = ["Master", "Music", "SFX"]

var game: Node
var seen_howto: bool = false # persisted
var volumes: Dictionary = {"Master": 1.0, "Music": 0.7, "SFX": 0.9}
var fullscreen: bool = false
var low_gfx: bool = false

var _overlay: Control = null
var _dim: ColorRect = null
var _center: CenterContainer = null
var _page: Control = null
var _stack: Array[String] = []
var _paused_by_me: bool = false
var _gfx_orig: Dictionary = {} # env/sun values captured before low graphics, restored on off
var _fs_check: CheckButton = null
var _close_text: String = "" # label for the lone page's close button (e.g. "GOT IT — FIGHT!")


func _tr(en: String, ms: String) -> String:
	return ms if game.lang == "ms" else en


func build() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_overlay = Control.new()
	_overlay.name = "MenuOverlay"
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.process_mode = Node.PROCESS_MODE_ALWAYS
	_overlay.z_index = 100
	_overlay.visible = false
	_dim = ColorRect.new()
	_dim.color = Color(0.03, 0.015, 0.005, 0.74)
	_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_dim.mouse_filter = Control.MOUSE_FILTER_STOP # nothing underneath is clickable
	_overlay.add_child(_dim)
	_center = CenterContainer.new()
	_center.set_anchors_preset(Control.PRESET_FULL_RECT)
	_center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.add_child(_center)
	game.ui.add_child(_overlay)


# ---------------------------------------------------------------- settings file

func load_settings() -> void:
	var cfg: ConfigFile = ConfigFile.new()
	if not game._test_mode and cfg.load(SETTINGS_PATH) == OK:
		for bus: String in BUSES:
			volumes[bus] = clampf(float(cfg.get_value("settings", bus.to_lower(), volumes[bus])), 0.0, 1.0)
		fullscreen = bool(cfg.get_value("settings", "fullscreen", fullscreen))
		low_gfx = bool(cfg.get_value("settings", "low_gfx", low_gfx))
		seen_howto = bool(cfg.get_value("settings", "seen_howto", seen_howto))
		var code: String = String(cfg.get_value("settings", "lang", ""))
		if code != "" and code != game.lang:
			game._on_lang_pressed(code)
	for bus: String in BUSES:
		_apply_volume(bus)
	if not OS.has_feature("mobile") and fullscreen != _is_fullscreen():
		_apply_fullscreen() # mobile: leave the export's immersive mode alone
	_apply_low_gfx()


func save_settings() -> void:
	if game._test_mode:
		return
	var cfg: ConfigFile = ConfigFile.new()
	for bus: String in BUSES:
		cfg.set_value("settings", bus.to_lower(), volumes[bus])
	cfg.set_value("settings", "fullscreen", fullscreen)
	cfg.set_value("settings", "low_gfx", low_gfx)
	cfg.set_value("settings", "lang", game.lang)
	cfg.set_value("settings", "seen_howto", seen_howto)
	cfg.save(SETTINGS_PATH)


func _apply_volume(bus: String) -> void:
	var idx: int = AudioServer.get_bus_index(bus)
	if idx < 0:
		return
	var v: float = float(volumes[bus])
	AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(v, 0.001)))
	AudioServer.set_bus_mute(idx, v <= 0.0)


func _is_fullscreen() -> bool:
	var m: int = DisplayServer.window_get_mode()
	return m == DisplayServer.WINDOW_MODE_FULLSCREEN or m == DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN


func _apply_fullscreen() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)


func toggle_fullscreen() -> void:
	_set_fullscreen(not _is_fullscreen())


func _set_fullscreen(on: bool) -> void:
	if OS.has_feature("mobile"):
		return
	fullscreen = on
	_apply_fullscreen()
	save_settings()
	if is_instance_valid(_fs_check):
		_fs_check.set_pressed_no_signal(on)


func _apply_low_gfx() -> void:
	var env: Environment = game._env
	var sun: DirectionalLight3D = game._sun
	if low_gfx:
		if _gfx_orig.is_empty():
			if env != null:
				_gfx_orig = {"ssao": env.ssao_enabled, "ssil": env.ssil_enabled, "glow": env.glow_enabled}
			if sun != null:
				_gfx_orig["shadow"] = sun.shadow_enabled
		if env != null:
			env.ssao_enabled = false
			env.ssil_enabled = false
			env.glow_enabled = false
		if sun != null:
			sun.shadow_enabled = false
	elif not _gfx_orig.is_empty():
		if env != null:
			env.ssao_enabled = bool(_gfx_orig.get("ssao", true))
			env.ssil_enabled = bool(_gfx_orig.get("ssil", true))
			env.glow_enabled = bool(_gfx_orig.get("glow", true))
		if sun != null:
			sun.shadow_enabled = bool(_gfx_orig.get("shadow", true))
		_gfx_orig.clear()


# ---------------------------------------------------------------- page stack

func is_open() -> bool:
	return not _stack.is_empty()


func open_pause() -> void:
	if is_open():
		return
	var a: Node = game.arena
	if a != null and a.get("charge_active") == true:
		a.set("charge_active", false)
		a.set("charge_power", 0.0)
	if not game.net_active: # never pause the MP host sim
		get_tree().paused = true
		_paused_by_me = true
	_push("pause")


func close_pause() -> void:
	var was_open: bool = is_open()
	_stack.clear()
	_close_text = ""
	if _overlay != null:
		_overlay.visible = false
	_clear_page()
	if _paused_by_me:
		get_tree().paused = false
		_paused_by_me = false
	if was_open:
		closed.emit()


func show_info(kind: String, close_text: String = "") -> void:
	if not kind in ["settings", "howto", "credits"]:
		return
	if _stack.is_empty():
		_close_text = close_text
		if kind == "howto":
			seen_howto = true
			save_settings()
	_push(kind)


func back() -> void:
	if _stack.size() <= 1:
		close_pause()
		return
	_stack.pop_back()
	_render()


func _push(kind: String) -> void:
	_stack.append(kind)
	_render()
	if not _overlay.visible:
		_overlay.visible = true
		_overlay.move_to_front() # GUI picking follows tree order, not z_index
		_dim.modulate.a = 0.0
		_tween().tween_property(_dim, "modulate:a", 1.0, 0.15)


func _tween() -> Tween:
	return create_tween().set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)


func _clear_page() -> void:
	if _page != null:
		_center.remove_child(_page) # detach now so old + new never overlap for a frame
		_page.queue_free()
		_page = null
	_fs_check = null


func _render() -> void:
	_clear_page()
	match _stack.back():
		"pause":
			_page = _build_pause()
		"settings":
			_page = _build_settings()
		"howto":
			_page = _build_howto()
		_:
			_page = _build_credits()
	_center.add_child(_page)
	# the pause card sits lower, so its frame clears the HUD clock medallion (to y 120)
	_center.offset_top = 84.0 if _stack.back() == "pause" else 0.0
	_page.pivot_offset = _page.get_combined_minimum_size() * 0.5
	_page.modulate.a = 0.0
	var tw: Tween = _tween().set_parallel(true)
	tw.tween_property(_page, "modulate:a", 1.0, 0.18)
	# .from(): the CenterContainer sort resets scale before the first step, so seed it there
	tw.tween_property(_page, "scale", Vector2.ONE, 0.18).from(Vector2(0.94, 0.94)).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _unhandled_input(event: InputEvent) -> void:
	if not is_open():
		return # closed: Esc is main's to open the pause
	var key: InputEventKey = event as InputEventKey
	if event.is_action_pressed("ui_cancel") or (key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE):
		back()
	elif key == null:
		return # mouse falls to the dimmer
	elif key.keycode == KEY_F11 and key.pressed and not key.echo:
		toggle_fullscreen() # main may be paused under us
	# modal: swallow keys so ENTER/SPACE don't start or steer anything underneath (MP isn't paused)
	get_viewport().set_input_as_handled()


# ---------------------------------------------------------------- shared bits

func _page_box(compact: bool = false, pad: float = 0.0) -> VBoxContainer:
	var box: PanelContainer = game._mk_panel_box(compact, pad)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	box.add_child(v)
	return v


func _header(v: VBoxContainer, title: String, gunungan: float = 44.0) -> void:
	if gunungan > 0.0:
		v.add_child(game._mk_gunungan(gunungan))
	v.add_child(game._mk_title(title, 38))
	v.add_child(game._mk_divider())


func _add_back_button(v: VBoxContainer) -> void:
	var text: String = _tr("BACK", "KEMBALI") if _stack.size() > 1 else _tr("CLOSE", "TUTUP")
	var go: bool = _stack.size() == 1 and _close_text != ""
	# a close that continues into play (the first-fight how-to) is the gold primary plaque
	var b: Button = game._mk_button(_close_text if go else text, HT.PLAYER_COLOR if go else HT.WOOD_DARK, not go)
	b.custom_minimum_size = Vector2(200.0, 0.0)
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	b.pressed.connect(back)
	v.add_child(b)


func _chip(text: String, color: Color) -> PanelContainer:
	# key-cap: dark wood with a 1px songket-gold rim
	var p: PanelContainer = PanelContainer.new()
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = Color(HT.WOOD_EDGE, 0.96)
	sb.border_color = Color(HT.SONGKET_GOLD, 0.85)
	sb.set_border_width_all(1)
	sb.border_width_bottom = 2 # key-cap lip
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 7.0
	sb.content_margin_right = 7.0
	sb.content_margin_top = 1.0
	sb.content_margin_bottom = 2.0
	p.add_theme_stylebox_override("panel", sb)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	p.add_child(game._mk_label(text, 13, color))
	return p


func _chips(keys: Array, color: Color) -> HBoxContainer:
	var h: HBoxContainer = HBoxContainer.new()
	h.add_theme_constant_override("separation", 3)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for k: String in keys:
		h.add_child(_chip(k, color))
	return h


func _left_label(text: String, font_size: int, color: Color, wrap_w: float = 0.0) -> Label:
	var l: Label = game._mk_label(text, font_size, color)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if wrap_w > 0.0:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size = Vector2(wrap_w, 0.0)
	return l


# ---------------------------------------------------------------- pause

func _build_pause() -> Control:
	var v: VBoxContainer = _page_box(false, 14.0) # breathing room: its rows would otherwise touch the gold frame line
	_header(v, _tr("PAUSED", "JEDA"))
	var col: VBoxContainer = VBoxContainer.new()
	col.add_theme_constant_override("separation", 10)
	col.custom_minimum_size = Vector2(280.0, 0.0)
	col.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(col)
	var resume: Button = game._mk_button(_tr("RESUME", "SAMBUNG"), game.PLAYER_COLOR)
	resume.add_theme_font_size_override("font_size", 20)
	resume.pressed.connect(close_pause)
	col.add_child(resume)
	var howto: Button = game._mk_button(_tr("HOW TO PLAY", "CARA BERMAIN"), game.WOOD_AMBER)
	howto.pressed.connect(show_info.bind("howto"))
	col.add_child(howto)
	var settings: Button = game._mk_button(_tr("SETTINGS", "TETAPAN"), game.WOOD_AMBER)
	settings.pressed.connect(show_info.bind("settings"))
	col.add_child(settings)
	# SP campaign: leaving mid-duel forfeits it (game._forfeit_duel), and the button says so
	var campaign: bool = not game.net_active and not game.endless_mode
	var leave_text: String = _tr("LEAVE MATCH", "TINGGALKAN PERLAWANAN") if game.net_active \
		else (_tr("FORFEIT DUEL", "TARIK DIRI") if campaign else _tr("MAIN MENU", "MENU UTAMA"))
	var leave: Button = game._mk_button(leave_text, game.WOOD_DARK, true)
	leave.add_theme_color_override("font_color", game.DANGER)
	leave.add_theme_color_override("font_hover_color", game.DANGER.lightened(0.2))
	leave.pressed.connect(_on_leave_pressed)
	col.add_child(leave)
	if game.net_active:
		v.add_child(game._mk_label(_tr("The match keeps running", "Perlawanan masih berjalan"), 13, game.CREAM_MUTED))
	elif campaign:
		v.add_child(game._mk_label(_tr("Forfeiting counts as a lost duel: the story starts over",
			"Tarik diri dikira kalah duel: cerita bermula semula"), 13, game.CREAM_MUTED))
	v.add_child(game._mk_divider())
	# compact controls reminder
	var rows: Array = [
		[[["W", "A", "S", "D"], _tr("steer", "kemudi")], [[_tr("CLICK", "KLIK")], _tr("push", "tolak")], [["SHIFT"], _tr("dash", "pecut")], [["E"], _tr("rush", "meluru")]],
		[[["SPACE"], _tr("wind / jump", "lilit / lompat")], [["1", "2", "3"], _tr("select", "pilih")], [["ESC"], _tr("resume", "sambung")]],
	]
	for row: Array in rows:
		var h: HBoxContainer = HBoxContainer.new()
		h.alignment = BoxContainer.ALIGNMENT_CENTER
		h.add_theme_constant_override("separation", 16)
		for item: Array in row:
			var pair: HBoxContainer = _chips(item[0], game.TEXT_COLOR)
			var l: Label = _left_label(String(item[1]), 13, game.CREAM_MUTED)
			pair.add_child(l)
			h.add_child(pair)
		v.add_child(h)
	return v.get_parent() as Control


func _on_leave_pressed() -> void:
	var mp: bool = game.net_active
	close_pause() # unpause first so the teardown/menu transition tweens run
	if mp:
		game._net_teardown()
	else:
		game._forfeit_duel() # campaign: counts as a lost duel; endless: back to the title


# ---------------------------------------------------------------- settings

func _build_settings() -> Control:
	var v: VBoxContainer = _page_box(false, 14.0) # breathing room: its rows would otherwise touch the gold frame line
	_header(v, _tr("SETTINGS", "TETAPAN"))
	var grid: GridContainer = GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 28)
	grid.add_theme_constant_override("v_separation", 12)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(grid)
	var names: Dictionary = {
		"Master": _tr("Master volume", "Kelantangan utama"),
		"Music": _tr("Music", "Muzik"),
		"SFX": _tr("Sound effects", "Kesan bunyi"),
	}
	for bus: String in BUSES:
		grid.add_child(_left_label(String(names[bus]), 17, game.TEXT_COLOR))
		var h: HBoxContainer = HBoxContainer.new()
		h.add_theme_constant_override("separation", 10)
		var s: HSlider = HSlider.new()
		s.min_value = 0.0
		s.max_value = 1.0
		s.step = 0.05
		s.value = float(volumes[bus])
		s.custom_minimum_size = Vector2(260.0, 24.0)
		s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var pct: Label = _left_label("%d%%" % roundi(s.value * 100.0), 15, game.PLAYER_COLOR)
		pct.custom_minimum_size = Vector2(48.0, 0.0)
		s.value_changed.connect(_on_volume_changed.bind(bus, pct))
		h.add_child(s)
		h.add_child(pct)
		grid.add_child(h)
	grid.add_child(_left_label(_tr("Fullscreen  (F11)", "Skrin penuh  (F11)"), 17, game.TEXT_COLOR))
	_fs_check = CheckButton.new()
	_fs_check.focus_mode = Control.FOCUS_NONE # like every button: SPACE must never toggle it
	_fs_check.button_pressed = _is_fullscreen()
	_fs_check.toggled.connect(_set_fullscreen)
	grid.add_child(_fs_check)
	grid.add_child(_left_label(_tr("Low graphics", "Grafik rendah"), 17, game.TEXT_COLOR))
	var low: CheckButton = CheckButton.new()
	low.focus_mode = Control.FOCUS_NONE
	low.button_pressed = low_gfx
	low.tooltip_text = _tr("Turns off ambient occlusion, bounce light, glow and shadows", "Matikan oklusi ambien, pantulan cahaya, cahaya bara dan bayang")
	low.toggled.connect(_on_low_gfx_toggled)
	grid.add_child(low)
	grid.add_child(_left_label(_tr("Language", "Bahasa"), 17, game.TEXT_COLOR))
	var langs: HBoxContainer = HBoxContainer.new()
	langs.add_theme_constant_override("separation", 10)
	for entry: Array in [["en", "ENGLISH"], ["ms", "BAHASA MELAYU"]]:
		var code: String = entry[0]
		var on: bool = code == game.lang
		var b: Button = game._mk_button(String(entry[1]), game.PLAYER_COLOR if on else game.WOOD_DARK, not on)
		b.pressed.connect(_on_lang_chosen.bind(code))
		langs.add_child(b)
	grid.add_child(langs)
	v.add_child(game._mk_divider())
	_add_back_button(v)
	return v.get_parent() as Control


func _on_volume_changed(value: float, bus: String, pct: Label) -> void:
	volumes[bus] = value
	_apply_volume(bus)
	pct.text = "%d%%" % roundi(value * 100.0)
	save_settings()


func _on_low_gfx_toggled(on: bool) -> void:
	low_gfx = on
	_apply_low_gfx()
	save_settings()


func _on_lang_chosen(code: String) -> void:
	if code != game.lang:
		game._on_lang_pressed(code)
	save_settings()
	_render()


# ---------------------------------------------------------------- how to play

func _build_howto() -> Control:
	var v: VBoxContainer = _page_box()
	v.add_theme_constant_override("separation", 8)
	_header(v, _tr("HOW TO PLAY", "CARA BERMAIN"), 30.0)
	var gold: Color = game.PLAYER_COLOR
	var red: Color = game.DANGER
	var key: Color = game.TEXT_COLOR
	# [number, title, rows]; row = [chip texts, chip text colour, text]
	var sections: Array = [
		[1, _tr("WIND", "LILIT TALI"), [
			[["SPACE"], key, _tr("Hold SPACE (or left mouse) to wind the cord", "Tahan SPACE (atau tetikus kiri) untuk melilit tali")],
			[["80-95"], gold, _tr("Release in the GOLD zone for full spin and energy", "Lepas di zon EMAS untuk putaran dan tenaga penuh")],
			[["95+"], red, _tr("Overwinding past 95 weakens the launch", "Lilitan melebihi 95 melemahkan lontaran")],
			[["A", "D"], key, _tr("Aim the throw", "Halakan balingan")],
		]],
		[2, _tr("FIGHT", "BERTARUNG"), [
			[["W", "A", "S", "D"], key, _tr("Steer your selected gasing", "Kemudi gasing pilihan anda")],
			[[_tr("CLICK", "KLIK")], key, _tr("Free push toward the cursor", "Tolakan percuma ke arah kursor")],
			[["SHIFT"], key, _tr("Dash - 20 energy, 1 s cooldown", "Pecut - 20 tenaga, rehat 1 s")],
			[["E"], key, _tr("Hold to rush the cursor - 20 energy/s, drains enemy spin on contact", "Tahan untuk meluru - 20 tenaga/s, menyedut putaran lawan bila bersentuh")],
			[["SPACE"], key, _tr("Jump to dodge - 25 energy", "Lompat untuk mengelak - 25 tenaga")],
			[["!"], red, _tr("Energy never refills - spend it wisely", "Tenaga tidak diisi semula - guna dengan bijak")],
		]],
		[3, _tr("SQUAD", "PASUKAN"), [
			[["1", "2", "3"], key, _tr("You field three gasing - select one", "Anda turunkan tiga gasing - pilih satu")],
			[["SPACE"], key, _tr("Select a reserve, hold and release to launch it anywhere mid-fight", "Pilih simpanan, tahan dan lepas untuk melancarnya di mana-mana")],
			[["30s", "45s"], gold, _tr("Reserves auto-launch weakly at 30 s and 45 s", "Simpanan dilancar sendiri (lemah) pada 30 s dan 45 s")],
			[["5s"], red, _tr("Nothing of yours spinning? You get 5 s to launch", "Tiada gasing anda berpusing? Ada 5 s untuk melancar")],
		]],
		[4, _tr("WIN", "MENANG"), [
			[["OUT"], gold, _tr("Ring-out: knock every enemy gasing over the rim", "Keluar gelanggang: tolak setiap gasing lawan melepasi bibir")],
			[["0%"], gold, _tr("Topple: or outlast them until their spin runs out", "Tumbang: atau bertahan hingga putaran mereka habis")],
			[["90s"], gold, _tr("At 90 s more spinning gasing wins, then more spin", "Pada 90 s gasing berpusing terbanyak menang, kemudian putaran tertinggi")],
			[["2/3"], gold, _tr("Each master duel is best of 3 rounds", "Setiap duel mahaguru ialah terbaik 3 pusingan")],
		]],
	]
	var grid: GridContainer = GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 10)
	v.add_child(grid)
	for sec: Array in sections:
		var card: PanelContainer = game._mk_panel_box(true)
		card.size_flags_vertical = Control.SIZE_FILL
		var cv: VBoxContainer = VBoxContainer.new()
		cv.add_theme_constant_override("separation", 4)
		card.add_child(cv)
		var head: HBoxContainer = HBoxContainer.new()
		head.add_theme_constant_override("separation", 10)
		head.add_child(_chip(str(sec[0]), gold))
		var t: Label = game._mk_title(String(sec[1]), 24)
		t.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		head.add_child(t)
		# a small picture at the header's right, drawn with the HUD's own marks
		var art: Control = Control.new()
		art.custom_minimum_size = Vector2(150.0, 26.0)
		art.size_flags_horizontal = Control.SIZE_EXPAND | Control.SIZE_SHRINK_END
		art.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		art.mouse_filter = Control.MOUSE_FILTER_IGNORE
		art.draw.connect(_draw_howto_art.bind(art, int(sec[0])))
		head.add_child(art)
		cv.add_child(head)
		for row: Array in sec[2]:
			var h: HBoxContainer = HBoxContainer.new()
			h.add_theme_constant_override("separation", 8)
			var chips: HBoxContainer = _chips(row[0], row[1])
			chips.custom_minimum_size = Vector2(112.0, 0.0) # fixed chip column keeps the text aligned
			h.add_child(chips)
			h.add_child(_left_label(String(row[2]), 14, game.TEXT_COLOR, 392.0))
			cv.add_child(h)
		grid.add_child(card)
	_add_back_button(v)
	return v.get_parent() as Control


func _draw_howto_art(c: Control, card: int) -> void:
	var w: float = c.size.x - 4.0 # a little air before the card's gold frame line
	var y: float = c.size.y * 0.5
	match card:
		1: # the wind meter laid flat: GOOD wash, the songket-gold 80-95 band, overwind; released at 88
			c.draw_style_box(HT.groove_box(), Rect2(0.0, y - 6.0, w, 12.0))
			c.draw_rect(Rect2(w * 0.4, y - 5.0, w * 0.4, 10.0), Color(HT.ENERGY_BLUE, 0.3))
			c.draw_texture_rect_region(HT.TEX_SONGKET, Rect2(w * 0.8, y - 8.0, w * 0.15, 16.0), Rect2(0.0, 0.0, 64.0, 32.0), HT.SONGKET_GOLD)
			c.draw_rect(Rect2(w * 0.95, y - 5.0, w * 0.05, 10.0), Color(HT.OVERWIND_RED, 0.6))
			c.draw_line(Vector2(w * 0.88, y - 12.0), Vector2(w * 0.88, y + 12.0), HT.TEXT_COLOR, 2.0, true)
		2: # energy that never refills: a half-spent bar, dash and jump still lit
			for i: int in 2:
				c.draw_circle(Vector2(5.0 + 12.0 * i, y), 4.0, HT.SONGKET_GOLD)
			c.draw_style_box(HT.groove_box(), Rect2(28.0, y - 5.0, w - 28.0, 10.0))
			c.draw_rect(Rect2(29.0, y - 4.0, (w - 30.0) * 0.55, 8.0), HT.ENERGY_BLUE)
		3: # the squad glyphs: spinning, in reserve, knocked out
			var codes: Array[int] = [0, 1, 2]
			game.FightBar.draw_squad(c, Vector2(w - 38.0, y), codes, HT.SIDE_YOU)
		_: # best of 3: two gold diamonds beat one crimson
			for i: int in 3:
				var p: Vector2 = Vector2(w - 60.0 + 22.0 * i + (8.0 if i == 2 else 0.0), y)
				c.draw_colored_polygon(PackedVector2Array([p + Vector2(0.0, -9.0), p + Vector2(8.0, 0.0),
					p + Vector2(0.0, 9.0), p + Vector2(-8.0, 0.0)]), HT.SIDE_FOE if i == 2 else HT.SIDE_YOU)


# ---------------------------------------------------------------- credits

func _build_credits() -> Control:
	var v: VBoxContainer = _page_box()
	_header(v, _tr("CREDITS", "KREDIT"))
	var scroll: ScrollContainer = ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(620.0, 400.0)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(scroll)
	var body: VBoxContainer = VBoxContainer.new()
	body.add_theme_constant_override("separation", 6)
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(body)
	var audio: PackedStringArray = [
		_tr("Music and most sound effects: original gamelan-style pieces synthesized for this game", "Muzik dan kebanyakan kesan bunyi: gubahan gaya gamelan asli yang disintesis untuk permainan ini"),
		_tr("Impact and interface sounds: Kenney.nl (CC0)", "Bunyi hentaman dan antara muka: Kenney.nl (CC0)"),
		"\"Applause in a large hall or church\" - eXpl0it3r, OpenGameArt (CC0)",
	]
	var fonts: PackedStringArray = [
		"Kurland - GGBotNet (SIL OFL 1.1)",
		"Signika - The Signika Project Authors (SIL OFL 1.1)",
	]
	var sections: Array = [
		[_tr("GAME", "PERMAINAN"), ["Gasing Pangkah", _tr("A Malaysian spinning-top arena battler", "Permainan gelanggang gasing Malaysia")]],
		[_tr("AUDIO", "AUDIO"), audio],
		[_tr("FONTS", "FON"), fonts],
		[_tr("ENGINE", "ENJIN"), ["Godot Engine (MIT)", "GodotSteam (MIT) - Gramps / GodotSteam contributors", Engine.get_license_text()]],
		[_tr("CULTURE", "BUDAYA"), [_tr(
			"Gasing pangkah is a Malay heritage sport: players wind a cord, throw a hardwood top and strike (pangkah) their rival's spinning top. It is still played at village and state festivals in Kelantan, Terengganu, Melaka, Penang, Sabah, Sarawak and Kuala Lumpur. The story scenes borrow from wayang kulit, the Malay shadow-puppet theatre. This game is a tribute, made with respect for the craftsmen, players and dalang who keep these traditions alive.",
			"Gasing pangkah ialah sukan warisan Melayu: pemain melilit tali, membaling gasing kayu keras dan memangkah gasing lawan yang sedang berpusing. Ia masih dimainkan di pesta kampung dan negeri di Kelantan, Terengganu, Melaka, Pulau Pinang, Sabah, Sarawak dan Kuala Lumpur. Babak cerita meminjam seni wayang kulit, teater bayang Melayu. Permainan ini ialah penghormatan kepada tukang, pemain dan dalang yang memelihara warisan ini.")]],
	]
	for sec: Array in sections:
		var t: Label = game._mk_title(String(sec[0]), 22)
		body.add_child(t)
		for line: String in sec[1]:
			var l: Label = game._mk_label(line, 15 if line.length() < 400 else 11, game.CREAM_MUTED) # small print: the MIT notice
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			body.add_child(l)
		body.add_child(game._mk_divider())
	_add_back_button(v)
	return v.get_parent() as Control
