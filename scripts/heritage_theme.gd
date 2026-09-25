extends RefCounted
# Heritage UI theme (ukiran wood + songket gold): the canonical palette tokens and
# ONE Theme for get_tree().root.theme, so every control main.gd does not style by
# hand (OptionButton popups, tooltips, bare bars, sliders, toggles, scroll bars)
# matches the per-node overrides of _mk_button/_mk_panel_box/_mk_stat_row, which
# still win over it. Loaded via preload (no class_name).

# ---- palette (main.gd aliases these: const X = HT.X)
const PLAYER_COLOR: Color = Color(1.0, 0.78, 0.25)
const SONGKET_GOLD: Color = PLAYER_COLOR # semantic alias for UI gold
const FOE_COLOR: Color = Color(0.2, 0.85, 0.8)
const TEXT_COLOR: Color = Color(0.96, 0.9, 0.78)
const PANEL_BG: Color = Color(0.11, 0.06, 0.035, 0.94)
const WOOD_DARK: Color = Color(0.3, 0.2, 0.1) # dark plaque base (quit/back/lang/skip/material)
const WOOD_AMBER: Color = Color(0.82, 0.6, 0.24) # amber plaque base (host/join/pick/buy/mp)
const WOOD_EDGE: Color = Color(0.16, 0.09, 0.05) # deep carved-shadow brown
const BORDER_BROWN: Color = Color(0.55, 0.38, 0.16, 0.8) # carved rim / line-edit border
const CREAM_MUTED: Color = Color(0.75, 0.66, 0.52)
const PANDAN: Color = Color(0.55, 0.8, 0.45) # endless button green
const COPPER: Color = Color(0.85, 0.55, 0.3) # locked-card price text
const DANGER: Color = Color(1.0, 0.45, 0.3) # defeat / offline / match point
const GROOVE: Color = Color(0.05, 0.025, 0.01, 0.75) # recessed carved slot behind bars
const TEXT_DIM: Color = CREAM_MUTED # secondary text
const INK: Color = Color(0.12, 0.07, 0.03) # dark text on light plaques
const INACTIVE: Color = Color(0.72, 0.72, 0.72) # dimmed-button modulate
const ENERGY_BLUE: Color = Color(0.35, 0.72, 0.95)
const HIT_ORANGE: Color = Color(1.0, 0.55, 0.15)
const OVERWIND_RED: Color = Color(0.95, 0.22, 0.15)
const SIDE_YOU: Color = PLAYER_COLOR
const SIDE_FOE: Color = Color(0.88, 0.22, 0.26)
const SEPANG: Color = Color(0.48, 0.12, 0.14) # deep maroon lacquer, well clear of SIDE_FOE
const NILA: Color = Color(0.25, 0.5, 0.67) # indigo lacquer (a deep ENERGY_BLUE)

const TEX_BTN: Texture2D = preload("res://assets/ui/button_plaque.png")
const TEX_CARD: Texture2D = preload("res://assets/ui/panel_card.png")
const TEX_SONGKET: Texture2D = preload("res://assets/ui/songket_band.png")

static var _icon_cache: Dictionary = {}


static func build(body_font: Font = null) -> Theme:
	var t: Theme = Theme.new()
	var body: FontVariation = _font(body_font, 0.0)
	t.default_font = body
	t.default_font_size = 16
	var icons: Dictionary = _icons()

	t.set_color("font_color", "Label", TEXT_COLOR)
	t.set_color("font_outline_color", "Label", WOOD_EDGE)
	t.set_constant("outline_size", "Label", 3)
	t.set_color("font_shadow_color", "Label", Color(0.0, 0.0, 0.0, 0.35))
	t.set_constant("shadow_offset_x", "Label", 1)
	t.set_constant("shadow_offset_y", "Label", 2)

	# plaque buttons, same slicing/tints as _mk_button's default amber
	for type: String in ["Button", "OptionButton", "MenuButton"]:
		t.set_stylebox("normal", type, plaque_box(WOOD_AMBER))
		t.set_stylebox("hover", type, plaque_box(WOOD_AMBER.lightened(0.18)))
		t.set_stylebox("pressed", type, plaque_box(WOOD_AMBER.darkened(0.28)))
		t.set_stylebox("disabled", type, plaque_box(WOOD_AMBER.darkened(0.45)))
		t.set_stylebox("focus", type, StyleBoxEmpty.new())
		for c: String in ["font_color", "font_hover_color", "font_focus_color"]:
			t.set_color(c, type, INK)
		t.set_color("font_pressed_color", type, INK.darkened(0.2))
		t.set_color("font_disabled_color", type, Color(INK, 0.45))
	# arrow takes the ink colour: gold would vanish on the amber plaque
	t.set_constant("modulate_arrow", "OptionButton", 1)
	t.set_constant("arrow_margin", "OptionButton", 14) # clear the carved plaque rim

	# CheckButton/CheckBox inherit Button, so blank the plaque back out
	var bare: StyleBoxEmpty = StyleBoxEmpty.new()
	bare.set_content_margin_all(4.0)
	for type: String in ["CheckButton", "CheckBox"]:
		for s: String in ["normal", "hover", "pressed", "hover_pressed", "disabled"]:
			t.set_stylebox(s, type, bare)
		t.set_stylebox("focus", type, StyleBoxEmpty.new())
		for c: String in ["font_color", "font_pressed_color", "font_focus_color"]:
			t.set_color(c, type, TEXT_COLOR)
		t.set_color("font_hover_color", type, SONGKET_GOLD)
		t.set_color("font_hover_pressed_color", type, SONGKET_GOLD)
		t.set_color("font_disabled_color", type, Color(TEXT_COLOR, 0.45))
	t.set_icon("checked", "CheckButton", icons.toggle_on)
	t.set_icon("unchecked", "CheckButton", icons.toggle_off)
	t.set_icon("checked_disabled", "CheckButton", icons.toggle_on_dis)
	t.set_icon("unchecked_disabled", "CheckButton", icons.toggle_off_dis)
	for type: String in ["CheckBox", "PopupMenu"]:
		t.set_icon("checked", type, icons.box_on)
		t.set_icon("unchecked", type, icons.box_off)
		t.set_icon("radio_checked", type, icons.radio_on)
		t.set_icon("radio_unchecked", type, icons.radio_off)
	t.set_icon("checked_disabled", "CheckBox", icons.box_on_dis)
	t.set_icon("unchecked_disabled", "CheckBox", icons.box_off_dis)

	# popups: slim card frame; slice at 18 like _mk_panel_box(compact) so the
	# gold line (texture px 15-16) stays in the border patches
	var card: StyleBoxTexture = StyleBoxTexture.new()
	card.texture = TEX_CARD
	card.set_texture_margin_all(18.0)
	card.content_margin_left = 20.0
	card.content_margin_right = 20.0
	card.content_margin_top = 16.0
	card.content_margin_bottom = 16.0
	t.set_stylebox("panel", "PopupMenu", card)
	t.set_stylebox("panel", "PopupPanel", card)
	var hover: StyleBoxFlat = StyleBoxFlat.new()
	hover.bg_color = Color(SONGKET_GOLD, 0.25)
	hover.set_corner_radius_all(4)
	t.set_stylebox("hover", "PopupMenu", hover)
	var band: StyleBoxTexture = songket_box(Color(SONGKET_GOLD, 0.85))
	band.content_margin_top = 4.0
	band.content_margin_bottom = 4.0
	t.set_stylebox("separator", "PopupMenu", band)
	t.set_color("font_color", "PopupMenu", TEXT_COLOR)
	t.set_color("font_hover_color", "PopupMenu", SONGKET_GOLD)
	t.set_color("font_disabled_color", "PopupMenu", Color(TEXT_COLOR, 0.4))
	t.set_color("font_separator_color", "PopupMenu", TEXT_DIM)
	t.set_color("font_accelerator_color", "PopupMenu", TEXT_DIM)
	t.set_stylebox("separator", "HSeparator", band)
	t.set_constant("separation", "HSeparator", 8)

	var tip: StyleBoxFlat = StyleBoxFlat.new()
	tip.bg_color = Color(WOOD_EDGE, 0.96)
	tip.set_border_width_all(2)
	tip.border_color = BORDER_BROWN
	tip.set_corner_radius_all(6)
	tip.content_margin_left = 10.0
	tip.content_margin_right = 10.0
	tip.content_margin_top = 6.0
	tip.content_margin_bottom = 6.0
	t.set_stylebox("panel", "TooltipPanel", tip)
	t.set_color("font_color", "TooltipLabel", TEXT_COLOR)
	t.set_font_size("font_size", "TooltipLabel", 14)
	# TooltipLabel falls through to Label: no outline/shadow on the small dark card
	t.set_constant("outline_size", "TooltipLabel", 0)
	t.set_color("font_shadow_color", "TooltipLabel", Color(0.0, 0.0, 0.0, 0.0))

	var panel: StyleBoxFlat = StyleBoxFlat.new()
	panel.bg_color = PANEL_BG
	panel.set_corner_radius_all(8)
	panel.set_border_width_all(1)
	panel.border_color = BORDER_BROWN
	panel.set_content_margin_all(10.0)
	t.set_stylebox("panel", "PanelContainer", panel)

	t.set_stylebox("background", "ProgressBar", groove_box())
	t.set_stylebox("fill", "ProgressBar", songket_box(SONGKET_GOLD))
	t.set_color("font_color", "ProgressBar", TEXT_COLOR)
	t.set_color("font_outline_color", "ProgressBar", WOOD_EDGE)
	t.set_constant("outline_size", "ProgressBar", 2)

	# recessed slot like _mk_line_edit; LineEdit draws "focus" OVER "normal",
	# so focus is just the gold rim
	var slot: StyleBoxFlat = StyleBoxFlat.new()
	slot.bg_color = Color(GROOVE, 0.9)
	slot.set_corner_radius_all(5)
	slot.set_border_width_all(1)
	slot.border_color = BORDER_BROWN
	slot.content_margin_left = 10.0
	slot.content_margin_right = 10.0
	slot.content_margin_top = 6.0
	slot.content_margin_bottom = 6.0
	t.set_stylebox("normal", "LineEdit", slot)
	var slot_ro: StyleBoxFlat = slot.duplicate()
	slot_ro.bg_color = Color(GROOVE, 0.5)
	t.set_stylebox("read_only", "LineEdit", slot_ro)
	var rim: StyleBoxFlat = StyleBoxFlat.new()
	rim.draw_center = false
	rim.set_corner_radius_all(5)
	rim.set_border_width_all(1)
	rim.border_color = SONGKET_GOLD
	t.set_stylebox("focus", "LineEdit", rim)
	t.set_color("font_color", "LineEdit", TEXT_COLOR)
	t.set_color("font_uneditable_color", "LineEdit", TEXT_DIM)
	t.set_color("font_placeholder_color", "LineEdit", Color(TEXT_DIM, 0.6))
	t.set_color("caret_color", "LineEdit", SONGKET_GOLD)
	t.set_color("selection_color", "LineEdit", Color(SONGKET_GOLD, 0.35))

	# slider groove height = the groove box's content margins (8 px)
	var track: StyleBoxFlat = groove_box()
	track.set_content_margin_all(4.0)
	for type: String in ["HSlider", "VSlider"]:
		t.set_stylebox("slider", type, track)
		t.set_stylebox("grabber_area", type, songket_box(SONGKET_GOLD))
		t.set_stylebox("grabber_area_highlight", type, songket_box(SONGKET_GOLD.lightened(0.2)))
		t.set_icon("grabber", type, icons.knob)
		t.set_icon("grabber_highlight", type, icons.knob_hi)
		t.set_icon("grabber_disabled", type, icons.knob_dis)

	# thin 8 px scroll bars: track and grabber minimum sizes set the width
	for type: String in ["VScrollBar", "HScrollBar"]:
		t.set_stylebox("scroll", type, track)
		t.set_stylebox("scroll_focus", type, track)
		t.set_stylebox("grabber", type, _flat(SONGKET_GOLD, 4))
		t.set_stylebox("grabber_highlight", type, _flat(SONGKET_GOLD.lightened(0.25), 4))
		t.set_stylebox("grabber_pressed", type, _flat(SONGKET_GOLD.darkened(0.15), 4))

	t.set_color("default_color", "RichTextLabel", TEXT_COLOR)
	t.set_font("normal_font", "RichTextLabel", body)
	t.set_font("bold_font", "RichTextLabel", _font(body_font, 0.7))
	return t


# ---- shared styleboxes (main.gd helpers can reuse these instead of re-literals)

static func plaque_box(tint: Color) -> StyleBoxTexture:
	# neutral-bright carved plaque texture x modulate = plaque in any wood tone
	var sb: StyleBoxTexture = StyleBoxTexture.new()
	sb.texture = TEX_BTN
	sb.set_texture_margin_all(20.0)
	sb.content_margin_left = 14.0
	sb.content_margin_right = 14.0
	sb.content_margin_top = 8.0
	sb.content_margin_bottom = 8.0
	sb.modulate_color = tint
	return sb


static func groove_box() -> StyleBoxFlat:
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = GROOVE
	sb.set_corner_radius_all(4)
	sb.border_width_bottom = 1
	sb.border_color = Color(BORDER_BROWN, 0.35) # light catching the groove's lower lip
	return sb


static func songket_box(tint: Color) -> StyleBoxTexture:
	var sb: StyleBoxTexture = StyleBoxTexture.new()
	sb.texture = TEX_SONGKET
	sb.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE # weave repeats, never stretches
	sb.modulate_color = tint
	return sb


static func _flat(col: Color, radius: int) -> StyleBoxFlat:
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = col
	sb.set_corner_radius_all(radius)
	sb.set_content_margin_all(4.0)
	return sb


static func _font(body_font: Font, embolden: float) -> FontVariation:
	# body font lacks ▶ ◆ ● ○ ✕: they render via the engine fallback + OS system-font fallback (desktop)
	var fv: FontVariation = FontVariation.new()
	fv.base_font = body_font if body_font else ThemeDB.fallback_font
	if body_font:
		var fb: Array[Font] = [ThemeDB.fallback_font]
		fv.fallbacks = fb
	fv.variation_embolden = embolden
	return fv


# ---- procedural icons (anti-aliased signed-distance shapes, built once)

static func _icons() -> Dictionary:
	if _icon_cache.is_empty():
		_icon_cache = {
			"knob": _knob(SONGKET_GOLD),
			"knob_hi": _knob(SONGKET_GOLD.lightened(0.25)),
			"knob_dis": _knob(INACTIVE.darkened(0.3)),
			"toggle_on": _toggle(true, false),
			"toggle_off": _toggle(false, false),
			"toggle_on_dis": _toggle(true, true),
			"toggle_off_dis": _toggle(false, true),
			"box_on": _box(true, false),
			"box_off": _box(false, false),
			"box_on_dis": _box(true, true),
			"box_off_dis": _box(false, true),
			"radio_on": _radio(true),
			"radio_off": _radio(false),
		}
	return _icon_cache


static func _shape(img: Image, sdf: Callable, fill: Color, rim: Color, rim_w: float) -> void:
	# paint sdf(p) < 0 over img with a 1 px AA edge; the band within rim_w of the
	# edge takes the rim colour (a transparent fill leaves a ring)
	for y: int in img.get_height():
		for x: int in img.get_width():
			var d: float = sdf.call(Vector2(x + 0.5, y + 0.5))
			var a: float = clampf(0.5 - d, 0.0, 1.0)
			if a <= 0.0:
				continue
			var c: Color = rim.lerp(fill, clampf(-d - rim_w + 0.5, 0.0, 1.0)) if rim_w > 0.0 else fill
			img.set_pixel(x, y, img.get_pixel(x, y).blend(Color(c, c.a * a)))


static func _capsule(a: Vector2, b: Vector2, r: float) -> Callable:
	# a == b gives a disc
	return func(p: Vector2) -> float: return Geometry2D.get_closest_point_to_segment(p, a, b).distance_to(p) - r


static func _canvas(w: int, h: int) -> Image:
	return Image.create_empty(w, h, false, Image.FORMAT_RGBA8)


static func _knob(col: Color) -> ImageTexture:
	var img: Image = _canvas(20, 20)
	_shape(img, _capsule(Vector2(10, 10), Vector2(10, 10), 9.0), col, col.darkened(0.55), 2.0)
	return ImageTexture.create_from_image(img)


static func _toggle(on: bool, disabled: bool) -> ImageTexture:
	# pill switch: off = groove + cream knob left, on = gold + knob right
	var img: Image = _canvas(44, 24)
	if on:
		_shape(img, _capsule(Vector2(12, 12), Vector2(32, 12), 11.0), SONGKET_GOLD, SONGKET_GOLD.darkened(0.45), 1.5)
	else:
		_shape(img, _capsule(Vector2(12, 12), Vector2(32, 12), 11.0), Color(GROOVE, 0.9), BORDER_BROWN, 1.5)
	var kx: float = 32.0 if on else 12.0
	_shape(img, _capsule(Vector2(kx, 12), Vector2(kx, 12), 8.0), TEXT_COLOR, WOOD_EDGE, 1.5)
	if disabled:
		img.adjust_bcs(0.6, 1.0, 0.25)
	return ImageTexture.create_from_image(img)


static func _box(checked: bool, disabled: bool) -> ImageTexture:
	# carved square slot with a gold tick
	var img: Image = _canvas(20, 20)
	var rbox: Callable = func(p: Vector2) -> float:
		var q: Vector2 = (p - Vector2(10, 10)).abs() - Vector2(5.0, 5.0) # half-size 8.5, corner radius 3.5
		return Vector2(maxf(q.x, 0.0), maxf(q.y, 0.0)).length() + minf(maxf(q.x, q.y), 0.0) - 3.5
	_shape(img, rbox, Color(GROOVE, 0.9), BORDER_BROWN, 1.5)
	if checked:
		var s1: Callable = _capsule(Vector2(5.5, 10.5), Vector2(8.5, 13.5), 1.4)
		var s2: Callable = _capsule(Vector2(8.5, 13.5), Vector2(14.5, 6.5), 1.4)
		_shape(img, func(p: Vector2) -> float: return minf(s1.call(p), s2.call(p)), SONGKET_GOLD, SONGKET_GOLD, 0.0)
	if disabled:
		img.adjust_bcs(0.6, 1.0, 0.25)
	return ImageTexture.create_from_image(img)


static func _radio(checked: bool) -> ImageTexture:
	var img: Image = _canvas(16, 16)
	var c: Vector2 = Vector2(8, 8)
	_shape(img, _capsule(c, c, 6.5), Color(GROOVE, 0.9), BORDER_BROWN, 1.5)
	if checked:
		_shape(img, _capsule(c, c, 3.5), SONGKET_GOLD, SONGKET_GOLD, 0.0)
	return ImageTexture.create_from_image(img)


static func run_checks() -> bool:
	var ok: bool = true
	# the AA shape painter: opaque fill centre, rim-coloured edge, clear corner
	var img: Image = _canvas(20, 20)
	_shape(img, _capsule(Vector2(10, 10), Vector2(10, 10), 9.0), Color.WHITE, Color.BLACK, 2.0)
	var centre: Color = img.get_pixel(10, 10)
	var edge: Color = img.get_pixel(10, 1)
	var shape_ok: bool = is_equal_approx(centre.a, 1.0) and centre.r > 0.99 and edge.a > 0.5 and edge.r < 0.1 and img.get_pixel(0, 0).a == 0.0
	if not shape_ok:
		push_error("heritage_theme check failed: sdf painter %s %s" % [centre, edge])
		ok = false
	var sf: SystemFont = SystemFont.new()
	sf.font_names = PackedStringArray(["Sans-Serif"])
	for font: Font in [null, sf]:
		var t: Theme = build(font)
		var fv: FontVariation = t.default_font as FontVariation
		var checks: Dictionary = {
			"default_font": fv != null and fv.base_font == (font if font else ThemeDB.fallback_font),
			"fallback": font == null or (fv != null and fv.fallbacks.size() == 1),
			"font_size": t.default_font_size == 16,
			"label_outline": t.get_constant("outline_size", "Label") == 3,
			"button": t.get_stylebox("normal", "Button") is StyleBoxTexture,
			"option_button": t.has_stylebox("normal", "OptionButton"),
			"check_button_bare": t.get_stylebox("normal", "CheckButton") is StyleBoxEmpty,
			"popup": t.has_stylebox("panel", "PopupMenu") and t.has_stylebox("hover", "PopupMenu"),
			"tooltip": t.has_stylebox("panel", "TooltipPanel"),
			"progress": t.has_stylebox("fill", "ProgressBar") and t.has_stylebox("background", "ProgressBar"),
			"line_edit": t.has_stylebox("focus", "LineEdit"),
			"slider": t.has_icon("grabber", "HSlider") and t.get_icon("grabber", "HSlider").get_size() == Vector2(20, 20),
			"check_button": t.has_icon("checked", "CheckButton") and t.get_icon("checked", "CheckButton").get_size() == Vector2(44, 24),
			"check_box": t.has_icon("checked", "CheckBox"),
			"scroll": t.has_stylebox("grabber", "VScrollBar"),
			"separator": t.has_stylebox("separator", "HSeparator"),
			"rich_bold": t.get_font("bold_font", "RichTextLabel") is FontVariation,
		}
		for k: String in checks:
			if not checks[k]:
				push_error("heritage_theme check failed: %s (font=%s)" % [k, font])
				ok = false
	return ok
