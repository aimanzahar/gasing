extends Node3D

enum State { READY, CRAFT, WIND, LAUNCH, BATTLE, ROUND_OVER, OVER }
enum MenuScreen { TITLE, MP, WAIT }

const GASING_SCENE: PackedScene = preload("res://gasing.tscn")
const CLASH_SOUNDS: Array[AudioStream] = [
	preload("res://assets/audio/impactWood_heavy_000.ogg"),
	preload("res://assets/audio/impactWood_heavy_001.ogg"),
	preload("res://assets/audio/impactWood_heavy_002.ogg"),
	preload("res://assets/audio/impactWood_heavy_003.ogg"),
	preload("res://assets/audio/impactWood_heavy_004.ogg"),
]
const SND_BIG_HIT: AudioStream = preload("res://assets/audio/impactPlank_medium_000.ogg")
const SND_TOPPLE: AudioStream = preload("res://assets/audio/impactSoft_heavy_001.ogg")
const SND_RINGOUT: AudioStream = preload("res://assets/audio/impactWood_light_002.ogg")
const SND_LAUNCH: AudioStream = preload("res://assets/audio/pluck_002.ogg")
const SND_WIN: AudioStream = preload("res://assets/audio/confirmation_002.ogg")
const SND_LOSE: AudioStream = preload("res://assets/audio/error_008.ogg")
const SND_CLICK: AudioStream = preload("res://assets/audio/click_002.ogg")
const SND_NUDGE: AudioStream = preload("res://assets/audio/click_004.ogg")
const NUDGE_POWER: float = 2.4
const MAX_IMPULSE: float = 6.0
const NUDGE_SPIN_COST: float = 2.0
const NUDGE_COOLDOWN: float = 0.35
const PLAYER_COLOR: Color = Color(1.0, 0.78, 0.25)
const FOE_COLOR: Color = Color(0.2, 0.85, 0.8)
const TEXT_COLOR: Color = Color(0.96, 0.9, 0.78)
const PANEL_BG: Color = Color(0.11, 0.06, 0.035, 0.94)

# Fixed base stats per style; "shape" is the physics archetype (radius/role),
# "mesh" the glb id. The 4 unlockable styles copy their AI owner's preset stats.
const STYLE_DEFS: Dictionary = {
	"jantung": {"label": "Gasing Jantung", "shape": "jantung", "mesh": "jantung", "mass": 2.4, "spin_reserve": 70.0, "balance": 60.0},
	"uri": {"label": "Gasing Uri", "shape": "uri", "mesh": "uri", "mass": 1.4, "spin_reserve": 105.0, "balance": 78.0},
	"pakdin": {"label": "Gasing Pak Din", "shape": "uri", "mesh": "pakdin", "mass": 1.5, "spin_reserve": 88.0, "balance": 66.0},
	"cikros": {"label": "Gasing Cik Ros", "shape": "jantung", "mesh": "cikros", "mass": 2.2, "spin_reserve": 70.0, "balance": 62.0},
	"tokgayong": {"label": "Gasing Tok Gayong", "shape": "jantung", "mesh": "tokgayong", "mass": 2.7, "spin_reserve": 76.0, "balance": 68.0},
	"datuk": {"label": "Gasing Datuk", "shape": "jantung", "mesh": "datuk", "mass": 2.9, "spin_reserve": 82.0, "balance": 74.0},
}
const DEFAULT_STYLES: Array[String] = ["jantung", "uri"]
const NET_MATCH_TARGET: int = 3
const SAVE_PATH: String = "user://workshop.cfg"
const MATERIAL_DEFS: Dictionary = {
	"merbau": {"label": "Kayu Merbau", "mass": 0.3, "balance": 0.0},
	"kemuning": {"label": "Kayu Kemuning", "mass": 0.0, "balance": 7.0},
	"besi": {"label": "Teras Besi", "mass": 0.5, "balance": 0.0},
}
const OPPONENTS: Array[Dictionary] = [
	{"name": "Pak Din", "shape": "uri", "mesh": "pakdin", "color": Color(0.2, 0.85, 0.8), "mass": 1.5, "spin_reserve": 88.0, "balance": 66.0, "wind_mean": 72.0, "wind_dev": 14.0, "aggressive": false},
	{"name": "Cik Ros", "shape": "jantung", "mesh": "cikros", "color": Color(0.95, 0.35, 0.65), "mass": 2.2, "spin_reserve": 70.0, "balance": 62.0, "wind_mean": 82.0, "wind_dev": 9.0, "aggressive": true},
	{"name": "Tok Gayong", "shape": "jantung", "mesh": "tokgayong", "color": Color(1.0, 0.45, 0.1), "mass": 2.7, "spin_reserve": 76.0, "balance": 68.0, "wind_mean": 86.0, "wind_dev": 6.0, "aggressive": true},
	{"name": "Datuk Pangkah", "shape": "jantung", "mesh": "datuk", "color": Color(0.65, 0.35, 1.0), "mass": 2.9, "spin_reserve": 82.0, "balance": 74.0, "wind_mean": 90.0, "wind_dev": 3.5, "aggressive": true},
]

const STRINGS: Dictionary = {
	"en": {
		"heritage": "A Malay heritage game — wind your top, strike your rival, rule the ring.",
		"fact": "Did you know? Gasing is a heritage sport of Kelantan and Melaka.",
		"prompt": "Press SPACE for single player",
		"wind_hint": "Hold SPACE / left mouse to wind the cord — release in the GREEN zone!  (A/D to aim)",
		"bench": "WORKSHOP",
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
		"battle_hint": "Click the arena to push your gasing — each push costs spin!",
		"tip_merbau": "Merbau — dense heartwood.\n+0.3 Mass: your strikes shove rivals harder\nand this top resists knockback.",
		"tip_kemuning": "Kemuning — fine golden wood.\n+7 Balance: wobbles later as spin fades\nand resists toppling when struck.",
		"tip_besi": "Besi — a heavy iron core.\n+0.5 Mass: much harder pangkah strikes.",
		"single_player": "SINGLE PLAYER",
		"multiplayer": "MULTIPLAYER",
		"quit": "QUIT",
		"mp_steam_header": "VIA STEAM",
		"mp_lan_header": "VIA LAN",
		"host_steam": "HOST (STEAM)",
		"host_lan": "HOST (LAN)",
		"join_lan": "JOIN BY IP",
		"lan_ip_label": "Host IP:",
		"invite_friend": "INVITE FRIEND",
		"invite_hint": "Or press Shift+Tab and invite from the Steam overlay.",
		"steam_join_hint": "To join a friend, accept their Steam invite.",
		"steam_offline": "Steam not detected — Steam play unavailable.",
		"back": "BACK",
		"cancel": "CANCEL",
		"waiting_opponent": "WAITING FOR OPPONENT...",
		"connecting": "CONNECTING...",
		"opponent_found": "OPPONENT FOUND!",
		"lan_share_ip": "Friend joins with this IP: %s",
		"err_host_failed": "Could not host the match.",
		"err_join_failed": "Could not join — check the IP address.",
		"err_join_steam": "Could not join the Steam match (it may be full).",
		"mp_disconnected": "Opponent disconnected.",
		"mp_server_lost": "Connection to the host was lost.",
		"waiting": "Waiting for opponent...",
		"score_line": "You %d — %d %s",
		"opp_left": "OPPONENT DISCONNECTED",
		"back_menu": "BACK TO MENU",
		"vs_line": "Duel vs %s",
		"locked_hint": "Beat %s to unlock",
		"locked_info": "Locked — defeat %s in single player to unlock.",
		"unlocked_title": "NEW GASING UNLOCKED!",
		"unlock_line": "%s's gasing joins your workshop!",
		"unlock_try": "%s unlocked — take it for a spin!",
		"mats_saved": "Stored in your workshop.",
		"first_to_3": "First to 3 wins",
		"match_point": "MATCH POINT!",
		"opp_ready": "%s is ready!",
		"match_win": "MATCH WON!",
		"match_lose": "%s takes the match...",
		"match_mats": "Materials this match:",
		"win_bonus": "Winner's bonus: +1 %s",
		"rematch": "REMATCH",
		"rematch_wait": "Waiting for %s...",
		"rematch_offer": "%s wants a rematch!",
		"role_pakdin": "Steady spinner — calm and enduring",
		"role_cikros": "Swift striker — sharp pangkah",
		"role_tokgayong": "Heavy striker — crushing weight",
		"role_datuk": "The master's top — power and poise",
	},
	"ms": {
		"heritage": "Permainan warisan Melayu — pusing gasingmu, pangkah lawan, jadi juara gelanggang.",
		"fact": "Tahu tak? Gasing ialah sukan warisan di Kelantan dan Melaka.",
		"prompt": "Tekan SPACE untuk main sendirian",
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
		"battle_hint": "Klik gelanggang untuk tolak gasingmu — setiap tolakan makan pusingan!",
		"tip_merbau": "Merbau — teras kayu padat.\n+0.3 Jisim: pangkah anda lebih kuat\ndan gasing lebih tahan tolakan.",
		"tip_kemuning": "Kemuning — kayu halus keemasan.\n+7 Imbangan: lambat goyang bila pusingan susut\ndan tahan tumbang bila dipangkah.",
		"tip_besi": "Besi — teras besi berat.\n+0.5 Jisim: pangkah jauh lebih kuat.",
		"single_player": "MAIN SENDIRIAN",
		"multiplayer": "BERBILANG PEMAIN",
		"quit": "KELUAR",
		"mp_steam_header": "MELALUI STEAM",
		"mp_lan_header": "MELALUI LAN",
		"host_steam": "JADI HOS (STEAM)",
		"host_lan": "JADI HOS (LAN)",
		"join_lan": "SERTAI GUNA IP",
		"lan_ip_label": "IP hos:",
		"invite_friend": "JEMPUT RAKAN",
		"invite_hint": "Atau tekan Shift+Tab dan jemput dari overlay Steam.",
		"steam_join_hint": "Untuk sertai rakan, terima jemputan Steam mereka.",
		"steam_offline": "Steam tidak dikesan — mod Steam tidak tersedia.",
		"back": "KEMBALI",
		"cancel": "BATAL",
		"waiting_opponent": "MENUNGGU LAWAN...",
		"connecting": "MENYAMBUNG...",
		"opponent_found": "LAWAN DITEMUI!",
		"lan_share_ip": "Rakan sertai dengan IP ini: %s",
		"err_host_failed": "Gagal membuka perlawanan.",
		"err_join_failed": "Gagal menyertai — semak alamat IP.",
		"err_join_steam": "Gagal menyertai perlawanan Steam (mungkin penuh).",
		"mp_disconnected": "Lawan terputus sambungan.",
		"mp_server_lost": "Sambungan ke hos terputus.",
		"waiting": "Menunggu lawan...",
		"score_line": "Kamu %d — %d %s",
		"opp_left": "LAWAN TERPUTUS SAMBUNGAN",
		"back_menu": "KEMBALI KE MENU",
		"vs_line": "Duel lawan %s",
		"locked_hint": "Kalahkan %s untuk buka",
		"locked_info": "Berkunci — kalahkan %s dalam mod sendirian untuk membukanya.",
		"unlocked_title": "GASING BARU DIBUKA!",
		"unlock_line": "Gasing %s kini dalam bengkel kamu!",
		"unlock_try": "%s dibuka — cuba pusingkan!",
		"mats_saved": "Disimpan dalam bengkel kamu.",
		"first_to_3": "Pertama capai 3 kemenangan",
		"match_point": "MATA PENENTU!",
		"opp_ready": "%s sudah sedia!",
		"match_win": "MENANG PERLAWANAN!",
		"match_lose": "%s memenangi perlawanan...",
		"match_mats": "Bahan perlawanan ini:",
		"win_bonus": "Bonus juara: +1 %s",
		"rematch": "LAWAN SEMULA",
		"rematch_wait": "Menunggu %s...",
		"rematch_offer": "%s mahu lawan semula!",
		"role_pakdin": "Pemusing seimbang — tenang dan tahan",
		"role_cikros": "Pemangkah pantas — pangkah tajam",
		"role_tokgayong": "Pemangkah berat — hentaman padu",
		"role_datuk": "Gasing mahaguru — kuasa dan imbangan",
	},
}

var lang: String = "en"
var state: State = State.READY
# persistent workshop state (saved to SAVE_PATH; loaded once in _ready)
var player_shapes: Dictionary = {}
var materials_owned: Dictionary = {}
var selected_shape: String = "jantung"
var unlocked_styles: Array[String] = []
var pending_unlock: String = "" # style to showcase on next CRAFT entry
var workshop_preview: Node3D = null
var duel_index: int = 0
var run_won: bool = false
var player_top: Gasing = null
var foe_top: Gasing = null
var wind_power: float = 0.0
var winding: bool = false
var aim_angle: float = 0.0
var hit_cooldown: float = 0.0
var nudge_cooldown: float = 0.0
var ai_think_timer: float = 1.0
var _marker_tween: Tween = null
var _sfx_pool: Array[AudioStreamPlayer] = []
var _sfx_index: int = 0
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
var battle_hint: Label = null
var player_gauge: SpinGauge = null
var foe_gauge: SpinGauge = null
var duel_label: Label = null
var mats_label: Label = null
var ready_heritage: Label = null
var ready_fact: Label = null
var ready_prompt: Label = null
var craft_title: Label = null
var craft_duel_label: Label = null
var craft_sub: Label = null
var craft_mats_hint: Label = null
var craft_info: Label = null
var craft_opp_status: Label = null
var round_label: Label = null
var award_label: Label = null
var round_award_row: HBoxContainer = null
var mats_saved_label: Label = null
var unlock_label: Label = null
var match_point_label: Label = null
var over_title: Label = null
var over_stats: Label = null
var over_hint: Label = null
var over_mats_title: Label = null
var over_award_row: HBoxContainer = null
var over_bonus_label: Label = null
var rematch_status: Label = null
var score_row: HBoxContainer = null
var my_pips: ScorePips = null
var opp_pips: ScorePips = null
var fight_button: Button = null
var restart_button: Button = null
var shape_cards: Dictionary = {}
var material_buttons: Dictionary = {}
var lang_buttons: Dictionary = {}

var menu_screen: MenuScreen = MenuScreen.TITLE
var mp_panel: Control = null
var wait_panel: Control = null
var _all_panels: Array[Control] = []
var menu_notice: Label = null
var _notice_tween: Tween = null
var sp_button: Button = null
var mp_button: Button = null
var quit_button: Button = null
var mp_title: Label = null
var mp_steam_header_label: Label = null
var mp_lan_header_label: Label = null
var host_steam_button: Button = null
var host_lan_button: Button = null
var join_lan_button: Button = null
var lan_ip_edit: LineEdit = null
var lan_ip_label: Label = null
var steam_join_hint_label: Label = null
var steam_offline_label: Label = null
var mp_back_button: Button = null
var wait_title: Label = null
var wait_info: Label = null
var invite_button: Button = null
var wait_cancel_button: Button = null
var over_menu_button: Button = null

var net_active: bool = false
var net_ended: bool = false
var net_opp_name: String = ""
var net_opp_config: Dictionary = {}
var net_ready_sent: bool = false
var net_wind_sent: bool = false
var net_my_wind: Vector2 = Vector2.ZERO
var net_opp_wind: Vector2 = Vector2.ZERO
var net_opp_wind_in: bool = false
var net_my_wins: int = 0
var net_opp_wins: int = 0
var net_client_nudge_cd: float = 0.0
var net_rematch_sent: bool = false
var net_opp_rematch: bool = false
var net_bonus_text: String = "" # match-bonus line cached for the match-over screen
var net_match_mats: Dictionary = {} # per-match material tally for the match-over screen

var _netbot: bool = false # debug autopilot for LAN testing: run with `-- netbot-host` or `-- netbot-join`
var _netbot_cd: float = 0.0

@onready var camera: Camera3D = $Camera3D
@onready var aim_arrow: Node3D = $AimArrow
@onready var burst: CPUParticles3D = $HitBurst
@onready var click_marker: MeshInstance3D = $ClickMarker
@onready var ui: CanvasLayer = $UI


func _ready() -> void:
	_rng.randomize()
	_build_sfx_pool()
	aim_arrow.visible = false
	var earth: MeshInstance3D = get_node_or_null("Environment3D/EnvEarth") as MeshInstance3D
	if earth != null:
		var earth_mat: StandardMaterial3D = StandardMaterial3D.new()
		earth_mat.albedo_color = Color(0.38, 0.26, 0.13)
		earth_mat.roughness = 1.0
		earth.set_surface_override_material(0, earth_mat)
	_configure_burst()
	_build_ui()
	Online.joined_lobby.connect(_on_mp_joined_lobby)
	Online.player_connected.connect(_on_mp_player_connected)
	Online.player_disconnected.connect(_on_mp_player_disconnected)
	Online.server_disconnected.connect(_on_mp_server_disconnected)
	Online.connection_failed.connect(_on_mp_connection_failed)
	Online.lobby_join_response.connect(_on_mp_steam_join_response)
	_load_workshop()
	_reset_run()
	_apply_language()
	_enter_state(State.READY)
	_netbot_init()


func _t(key: String) -> String:
	return STRINGS[lang][key]


# ---------------------------------------------------------------- state flow

func _enter_state(next: State) -> void:
	state = next
	if next != State.CRAFT:
		_clear_preview()
	match next:
		State.READY:
			_clear_tops()
			_set_hud_visible(false)
			_show_menu_screen(MenuScreen.TITLE)
		State.CRAFT:
			_clear_tops()
			_set_hud_visible(false)
			net_ready_sent = false
			net_opp_config = {}
			fight_button.disabled = false
			craft_opp_status.text = ""
			craft_info.text = _t("pick_info")
			if pending_unlock != "":
				# showcase the freshly unlocked style: auto-select it so the 3D
				# preview pops it in, and nudge the player to try it
				selected_shape = pending_unlock
				craft_info.text = _t("unlock_try") % String(STYLE_DEFS[pending_unlock].label)
				_play_sfx(SND_WIN, -8.0, 0.05)
				pending_unlock = ""
				_save_workshop()
			_refresh_craft()
			_update_workshop_preview()
			_show_panel(craft_panel)
		State.WIND:
			_show_panel(null)
			_set_hud_visible(true)
			net_wind_sent = false
			net_opp_wind_in = false
			battle_hint.visible = false
			player_gauge.visible = false
			foe_gauge.visible = false
			wind_meter.visible = true
			wind_hint.visible = true
			wind_hint.text = _t("wind_hint")
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
			battle_hint.visible = true
		State.ROUND_OVER:
			pass
		State.OVER:
			_clear_tops()
			_set_hud_visible(false)
			# MP match-over offers REMATCH + back-to-menu; the disconnect screen
			# (net_ended) keeps only the restart button acting as back-to-menu
			over_menu_button.visible = not net_active or not net_ended
			_show_panel(over_panel)


func _unhandled_input(event: InputEvent) -> void:
	match state:
		State.READY:
			if menu_screen == MenuScreen.TITLE and event.is_action_pressed("ui_accept"):
				get_viewport().set_input_as_handled()
				_enter_state(State.CRAFT)
		State.BATTLE:
			var click: InputEventMouseButton = event as InputEventMouseButton
			if click != null and click.pressed and click.button_index == MOUSE_BUTTON_LEFT:
				_try_nudge(click.position)
		State.WIND:
			if net_wind_sent:
				return # released already — waiting for the opponent's wind
			if event.is_action_pressed("wind"):
				winding = true
			elif event.is_action_released("wind") and winding:
				winding = false
				if net_active:
					_net_release_wind()
				else:
					_enter_state(State.LAUNCH)
			elif event is InputEventMouseMotion and winding:
				var motion: InputEventMouseMotion = event
				aim_angle = clampf(aim_angle - motion.relative.x * 0.003, -1.1, 1.1)
		State.OVER:
			if event.is_action_pressed("ui_accept"):
				_on_restart_pressed() # SP restart / MP rematch / disconnect teardown


func _process(delta: float) -> void:
	if is_instance_valid(workshop_preview):
		workshop_preview.rotate_y(2.5 * delta)


func _update_workshop_preview() -> void:
	_clear_preview()
	if state != State.CRAFT:
		return
	var scene: PackedScene = load("res://assets/gasing_%s.glb" % String(STYLE_DEFS[selected_shape].mesh))
	if scene == null:
		return
	workshop_preview = scene.instantiate() as Node3D
	add_child(workshop_preview)
	# park it on the arena floor in the strip right of the workshop panel;
	# unprojecting survives the canvas_items/expand stretch at any aspect
	var vp: Vector2 = get_viewport().get_visible_rect().size
	var screen: Vector2 = Vector2(vp.x * 0.88, vp.y * 0.55)
	var hit: Variant = Plane(Vector3.UP, 0.0).intersects_ray(camera.project_ray_origin(screen), camera.project_ray_normal(screen))
	if hit != null:
		workshop_preview.position = hit
	workshop_preview.scale = Vector3(0.01, 0.01, 0.01)
	var tw: Tween = create_tween()
	tw.tween_property(workshop_preview, "scale", Vector3(1.5, 1.5, 1.5), 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _clear_preview() -> void:
	if is_instance_valid(workshop_preview):
		workshop_preview.queue_free()
	workshop_preview = null


func _physics_process(delta: float) -> void:
	if _netbot:
		_netbot_tick(delta)
	if state == State.WIND:
		if net_wind_sent:
			return # meter/arrow hidden while waiting for the opponent
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
	nudge_cooldown = maxf(nudge_cooldown - delta, 0.0)
	if _net_sim_authority():
		net_client_nudge_cd = maxf(net_client_nudge_cd - delta, 0.0)
		var p_ok: bool = is_instance_valid(player_top) and player_top.alive
		var f_ok: bool = is_instance_valid(foe_top) and foe_top.alive
		if p_ok and f_ok:
			if not net_active:
				_ai_think(delta)
			_check_collision()
		_resolve_eliminations()
		if net_active and state == State.BATTLE and p_ok and f_ok:
			_net_snapshot.rpc(
				Vector2(player_top.position.x, player_top.position.z), player_top.spin, player_top.wobble,
				Vector2(foe_top.position.x, foe_top.position.z), foe_top.spin, foe_top.wobble)
	_update_gauges()


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
	g.puppet = net_active and not _net_is_host() # client renders both tops from host snapshots
	if is_player:
		var my_name: String = Online.personal_player_data.display_name if net_active else _t("you")
		g.setup(my_name, String(STYLE_DEFS[selected_shape].shape), _style_battle_stats(selected_shape), PLAYER_COLOR)
		g.position = Vector3(0.0, 0.0, 3.0)
	elif net_active:
		var opp_style: String = String(net_opp_config.get("shape", "jantung"))
		g.setup(String(net_opp_config.get("name", net_opp_name)), String(STYLE_DEFS[opp_style].shape), net_opp_config.get("stats", STYLE_DEFS["jantung"]), FOE_COLOR)
		g.position = Vector3(0.0, 0.0, -3.0)
	else:
		var opp: Dictionary = OPPONENTS[duel_index]
		g.setup(opp.name, opp.shape, opp, opp.get("color", FOE_COLOR))
		g.position = Vector3(0.0, 0.0, -3.0)
	return g


func _do_launch() -> void:
	last_wind_effectiveness = _wind_effectiveness(wind_power)
	var dir: Vector3 = Vector3.FORWARD.rotated(Vector3.UP, aim_angle)
	player_top.set_winding(false)
	player_top.launch(dir, last_wind_effectiveness)
	_play_sfx(SND_LAUNCH, -4.0, 0.15)
	if wind_power > 95.0:
		_toast(_t("toast_snap"), Color(1.0, 0.35, 0.25), Vector3(0.0, 0.5, 3.0), true)
	foe_top = _spawn_top(false)
	foe_gauge.ring_color = foe_top.accent_color
	var opp: Dictionary = OPPONENTS[duel_index]
	var foe_wind: float = clampf(_rng.randfn(opp.wind_mean, opp.wind_dev), 5.0, 100.0)
	var foe_eff: float = _wind_effectiveness(foe_wind)
	var foe_dir: Vector3 = Vector3.BACK.rotated(Vector3.UP, _rng.randf_range(-0.25, 0.25))
	foe_top.launch(foe_dir, foe_eff)
	last_striker = ""
	hit_cooldown = 0.0
	nudge_cooldown = 0.0
	ai_think_timer = 1.2
	_enter_state(State.BATTLE)


# ---------------------------------------------------------------- battle

func _try_nudge(screen_pos: Vector2) -> void:
	if nudge_cooldown > 0.0:
		return
	if not is_instance_valid(player_top) or not player_top.alive or player_top.spin <= NUDGE_SPIN_COST:
		return
	var origin: Vector3 = camera.project_ray_origin(screen_pos)
	var normal: Vector3 = camera.project_ray_normal(screen_pos)
	var hit: Variant = Plane(Vector3.UP, 0.0).intersects_ray(origin, normal)
	if hit == null:
		return
	var point: Vector3 = hit
	var dir: Vector3 = point - player_top.position
	dir.y = 0.0
	if dir.length() < 0.05:
		return
	dir = dir.normalized()
	nudge_cooldown = NUDGE_COOLDOWN
	_play_sfx(SND_NUDGE, -8.0, 0.2)
	if net_active and not _net_is_host():
		# optimistic FX only; the host validates and applies it to our top (its foe_top)
		player_top.flash_direction(dir)
		_flash_click_marker(point)
		_net_request_nudge.rpc_id(1, Vector2(-point.x, -point.z))
		return
	player_top.velocity += dir * NUDGE_POWER
	player_top.spin = maxf(player_top.spin - NUDGE_SPIN_COST, 0.0)
	player_top.flash_direction(dir)
	_flash_click_marker(point)
	if net_active:
		_net_nudge_fx.rpc(Vector2(dir.x, dir.z))


func _flash_click_marker(point: Vector3) -> void:
	click_marker.position = Vector3(point.x, 0.03, point.z)
	click_marker.visible = true
	click_marker.scale = Vector3(1.5, 1.5, 1.5)
	if _marker_tween != null and _marker_tween.is_valid():
		_marker_tween.kill()
	_marker_tween = create_tween()
	_marker_tween.tween_property(click_marker, "scale", Vector3(0.45, 0.45, 0.45), 0.35).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_marker_tween.tween_callback(click_marker.hide)


func _ai_think(delta: float) -> void:
	var opp: Dictionary = OPPONENTS[duel_index]
	# continuous gentle drift (must beat the 0.8 friction decel or the AI never moves once parked)
	var target: Vector3 = player_top.position if opp.aggressive else Vector3.ZERO
	var to_target: Vector3 = target - foe_top.position
	to_target.y = 0.0
	if to_target.length() > 0.2:
		var strength: float = 1.6 if opp.aggressive else 0.95
		foe_top.velocity += to_target.normalized() * strength * delta
	# decisive pushes on a think timer — the AI plays by the player's push rules
	ai_think_timer -= delta
	if ai_think_timer > 0.0:
		return
	ai_think_timer = maxf(1.5 - 0.22 * float(duel_index), 0.5) + _rng.randf_range(-0.2, 0.3)
	if foe_top.spin < NUDGE_SPIN_COST * 4.0:
		return
	var push_dir: Vector3 = Vector3.ZERO
	var foe_dist: float = Vector2(foe_top.position.x, foe_top.position.z).length()
	var to_player: Vector3 = player_top.position - foe_top.position
	to_player.y = 0.0
	if foe_dist > 3.0:
		push_dir = -foe_top.position
	elif opp.aggressive or player_top.wobble > 0.0:
		push_dir = (player_top.position + player_top.velocity * 0.3) - foe_top.position
	elif not opp.aggressive and to_player.length() < 2.0:
		push_dir = -to_player.rotated(Vector3.UP, _rng.randf_range(-0.6, 0.6))
	push_dir.y = 0.0
	if push_dir.length() < 0.05:
		return
	push_dir = push_dir.normalized()
	foe_top.velocity += push_dir * NUDGE_POWER
	foe_top.spin = maxf(foe_top.spin - NUDGE_SPIN_COST, 0.0)
	foe_top.flash_direction(push_dir)


func _check_collision() -> void:
	# ponytail: exactly two tops -> plain distance check is the overlap query
	var diff: Vector3 = foe_top.position - player_top.position
	diff.y = 0.0
	var min_d: float = player_top.radius + foe_top.radius
	if diff.length() >= min_d or hit_cooldown > 0.0:
		return
	hit_cooldown = 0.3
	var dir: Vector3 = diff.normalized() if diff.length() > 0.001 else Vector3.FORWARD
	# charging into the hit transfers momentum — a ram knocks far harder than a drift
	var charge_p: float = maxf(player_top.velocity.dot(dir), 0.0)
	var charge_f: float = maxf(-foe_top.velocity.dot(dir), 0.0)
	var imp_on_foe: float = minf(0.02 * player_top.spin * (player_top.mass / foe_top.mass) + charge_p * 1.3 * (player_top.mass / foe_top.mass), MAX_IMPULSE)
	var imp_on_player: float = minf(0.02 * foe_top.spin * (foe_top.mass / player_top.mass) + charge_f * 1.3 * (foe_top.mass / player_top.mass), MAX_IMPULSE)
	foe_top.apply_hit(dir, imp_on_foe, imp_on_foe * 2.5)
	player_top.apply_hit(-dir, imp_on_player, imp_on_player * 2.5)
	var overlap: float = min_d - diff.length()
	foe_top.position += dir * overlap * 0.5
	player_top.position -= dir * overlap * 0.5
	last_striker = "player" if imp_on_foe >= imp_on_player else "foe"
	var contact: Vector3 = player_top.position + dir * player_top.radius
	_hit_effects(contact, maxf(imp_on_foe, imp_on_player))
	if net_active:
		_net_hit_fx.rpc(Vector2(contact.x, contact.z), maxf(imp_on_foe, imp_on_player))


func _hit_effects(contact: Vector3, strength: float) -> void:
	burst.global_position = contact + Vector3(0.0, 0.35, 0.0)
	burst.restart()
	_camera_nudge()
	var clash: AudioStream = CLASH_SOUNDS[_rng.randi_range(0, CLASH_SOUNDS.size() - 1)]
	_play_sfx(clash, clampf(-10.0 + strength * 2.5, -10.0, 2.0), 0.12)
	if strength > 3.0:
		_play_sfx(SND_BIG_HIT, 0.0, 0.08)
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
	elif f_reason != "":
		player_wins = true
	else:
		player_wins = false
	if net_active:
		# reasons are in host roles: player_top here IS the host's top
		_net_round_over.rpc(p_reason, f_reason, player_wins)
		return
	_apply_round_result(p_reason, f_reason, player_wins)


func _apply_round_result(my_reason: String, opp_reason: String, i_win: bool) -> void:
	if my_reason != "" and opp_reason != "":
		_toast(_t("toast_double"), TEXT_COLOR, Vector3.ZERO, false)
		if is_instance_valid(player_top):
			player_top.die(my_reason)
		if is_instance_valid(foe_top):
			foe_top.die(opp_reason)
	elif opp_reason != "":
		_toast_elimination(foe_top, opp_reason)
		foe_top.die(opp_reason)
	else:
		_toast_elimination(player_top, my_reason)
		player_top.die(my_reason)
	_finish_duel(i_win)


func _toast_elimination(top: Gasing, reason: String) -> void:
	var template: String = _t("toast_ringout") if reason == "ringout" else _t("toast_topple")
	if reason == "ringout":
		_play_sfx(SND_RINGOUT, -2.0, 0.1)
		_play_sfx(SND_TOPPLE, -6.0, 0.15)
	else:
		_play_sfx(SND_TOPPLE, -2.0, 0.1)
	_toast(template % top.display_name, Color(1.0, 0.45, 0.3), top.position, false)


func _finish_duel(player_wins: bool) -> void:
	state = State.ROUND_OVER
	battle_hint.visible = false
	player_gauge.wobbling = false
	foe_gauge.wobbling = false
	_reset_round_panel()
	if net_active:
		if player_wins:
			net_my_wins += 1
			_play_sfx(SND_WIN, -3.0, 0.02)
			round_label.text = _t("round_win")
			round_label.add_theme_color_override("font_color", PLAYER_COLOR)
		else:
			net_opp_wins += 1
			_play_sfx(SND_LOSE, -3.0, 0.02)
			round_label.text = _t("round_lose") % net_opp_name
			round_label.add_theme_color_override("font_color", FOE_COLOR)
		var match_over: bool = net_my_wins >= NET_MATCH_TARGET or net_opp_wins >= NET_MATCH_TARGET
		if player_wins:
			var counts: Dictionary = _grant_materials(_rng.randi_range(1, 2))
			_tally_match_mats(counts)
			_show_award_icons(round_award_row, counts, "+%d")
			mats_saved_label.text = _t("mats_saved")
			mats_saved_label.visible = true
			if match_over:
				var bonus: Dictionary = _grant_materials(1)
				_tally_match_mats(bonus)
				net_bonus_text = _t("win_bonus") % _mat_summary(bonus)
			_save_workshop() # bank rewards NOW — a disconnect during the pause cannot void them
		if not match_over and maxi(net_my_wins, net_opp_wins) == NET_MATCH_TARGET - 1:
			match_point_label.text = _t("match_point")
			match_point_label.visible = true
			_pulse(match_point_label)
		award_label.text = _t("score_line") % [net_my_wins, net_opp_wins, net_opp_name]
		_update_top_bar()
		_show_panel(round_panel)
		get_tree().create_timer(2.4).timeout.connect(_net_after_round)
		return
	var opp: Dictionary = OPPONENTS[duel_index]
	if player_wins:
		_play_sfx(SND_WIN, -3.0, 0.02)
		round_label.text = _t("round_win")
		round_label.add_theme_color_override("font_color", PLAYER_COLOR)
		var counts: Dictionary = _grant_materials(_rng.randi_range(1, 2))
		_show_award_icons(round_award_row, counts, "+%d")
		mats_saved_label.text = _t("mats_saved")
		mats_saved_label.visible = true
		var wait: float = 2.4
		var unlock_style: String = String(opp.mesh)
		if not unlocked_styles.has(unlock_style):
			unlocked_styles.append(unlock_style)
			pending_unlock = unlock_style
			unlock_label.text = _t("unlocked_title") + "\n" + _t("unlock_line") % String(opp.name)
			unlock_label.add_theme_color_override("font_color", opp.get("color", PLAYER_COLOR))
			unlock_label.visible = true
			_pulse(unlock_label)
			wait = 3.4
		_save_workshop()
		duel_index += 1
		_update_top_bar()
		_show_panel(round_panel)
		get_tree().create_timer(wait).timeout.connect(_after_round.bind(player_wins))
		return
	round_label.text = _t("round_lose") % opp.name
	round_label.add_theme_color_override("font_color", FOE_COLOR)
	award_label.text = _t("round_out")
	_show_panel(round_panel)
	get_tree().create_timer(2.4).timeout.connect(_after_round.bind(player_wins))


func _tally_match_mats(counts: Dictionary) -> void:
	for mat_id: String in counts:
		net_match_mats[mat_id] = int(net_match_mats.get(mat_id, 0)) + int(counts[mat_id])


func _show_award_icons(row: HBoxContainer, counts: Dictionary, fmt: String) -> void:
	for child: Node in row.get_children():
		child.queue_free()
	var i: int = 0
	for mat_id: String in counts:
		var cell: HBoxContainer = HBoxContainer.new()
		cell.add_theme_constant_override("separation", 4)
		var icon: TextureRect = TextureRect.new()
		icon.texture = load("res://assets/icon_%s.png" % mat_id)
		icon.custom_minimum_size = Vector2(36.0, 36.0)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		cell.add_child(icon)
		cell.add_child(_mk_label(fmt % int(counts[mat_id]), 16))
		# ponytail: staggered alpha pop instead of scale tween — no pivot bookkeeping
		cell.modulate.a = 0.0
		row.add_child(cell)
		var tw: Tween = create_tween()
		tw.tween_property(cell, "modulate:a", 1.0, 0.25).set_delay(0.1 + 0.08 * i)
		i += 1


func _reset_round_panel() -> void:
	for child: Node in round_award_row.get_children():
		child.queue_free()
	mats_saved_label.visible = false
	unlock_label.visible = false
	unlock_label.modulate.a = 1.0
	match_point_label.visible = false
	match_point_label.modulate.a = 1.0
	award_label.text = ""


func _pulse(l: Label) -> void:
	var tw: Tween = create_tween().set_loops(4)
	tw.tween_property(l, "modulate:a", 0.35, 0.4)
	tw.tween_property(l, "modulate:a", 1.0, 0.4)


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
	_play_sfx(SND_WIN if won else SND_LOSE, 0.0, 0.0)
	_reset_over_panel()
	over_title.text = _t("over_win") if won else _t("over_lose")
	over_title.add_theme_color_override("font_color", PLAYER_COLOR if won else Color(1.0, 0.45, 0.3))
	over_stats.text = _t("duels_won") % [duel_index, OPPONENTS.size()]
	_enter_state(State.OVER)


func _reset_over_panel() -> void:
	for child: Node in over_award_row.get_children():
		child.queue_free()
	over_mats_title.visible = false
	over_award_row.visible = false
	over_bonus_label.visible = false
	rematch_status.text = ""
	rematch_status.visible = false
	rematch_status.modulate.a = 1.0
	restart_button.disabled = false


# ---------------------------------------------------------------- run / workshop

func _reset_run() -> void:
	duel_index = 0
	run_won = false
	last_striker = ""


func _style_unlock_index(style_id: String) -> int:
	for i: int in OPPONENTS.size():
		if String(OPPONENTS[i].mesh) == style_id:
			return i
	return -1 # default style, never locked


func _style_battle_stats(id: String) -> Dictionary:
	var s: Dictionary = (player_shapes[id] as Dictionary).duplicate()
	s["mesh"] = STYLE_DEFS[id].mesh
	return s


func _grant_materials(count: int) -> Dictionary:
	var counts: Dictionary = {}
	var keys: Array = MATERIAL_DEFS.keys()
	for i: int in count:
		var pick: String = keys[_rng.randi_range(0, keys.size() - 1)]
		materials_owned[pick] += 1
		counts[pick] = int(counts.get(pick, 0)) + 1
	return counts


func _mat_summary(counts: Dictionary) -> String:
	var parts: Array[String] = []
	for mat_id: String in counts:
		var label: String = String(MATERIAL_DEFS[mat_id].label)
		parts.append(label if int(counts[mat_id]) == 1 else "%s ×%d" % [label, counts[mat_id]])
	return ", ".join(parts)


func _load_workshop() -> void:
	# defaults first — a missing/corrupt save degrades to a fresh workshop
	unlocked_styles = DEFAULT_STYLES.duplicate()
	materials_owned = {"merbau": 0, "kemuning": 0, "besi": 0}
	player_shapes = {}
	for id: String in STYLE_DEFS:
		var d: Dictionary = STYLE_DEFS[id]
		player_shapes[id] = {"mass": d.mass, "spin_reserve": d.spin_reserve, "balance": d.balance}
	selected_shape = "jantung"
	var cf: ConfigFile = ConfigFile.new()
	if cf.load(SAVE_PATH) != OK:
		return
	var u: Variant = cf.get_value("workshop", "unlocked", [])
	if u is Array:
		for id: Variant in u:
			if STYLE_DEFS.has(id) and not unlocked_styles.has(String(id)):
				unlocked_styles.append(String(id))
	var m: Variant = cf.get_value("workshop", "materials", {})
	if m is Dictionary:
		for k: String in materials_owned:
			var v: Variant = (m as Dictionary).get(k, 0)
			if v is int or v is float:
				materials_owned[k] = maxi(int(v), 0)
	var s: Variant = cf.get_value("workshop", "shapes", {})
	if s is Dictionary:
		for id: String in player_shapes:
			var sv: Variant = (s as Dictionary).get(id)
			if sv is Dictionary:
				var mass_v: Variant = (sv as Dictionary).get("mass")
				var bal_v: Variant = (sv as Dictionary).get("balance")
				if mass_v is float or mass_v is int:
					player_shapes[id].mass = clampf(float(mass_v), 1.4, 3.0)
				if bal_v is float or bal_v is int:
					player_shapes[id].balance = clampf(float(bal_v), 55.0, 85.0)
				# spin_reserve deliberately NOT loaded — always the style base
	var sel: String = String(cf.get_value("workshop", "selected", "jantung"))
	if STYLE_DEFS.has(sel) and unlocked_styles.has(sel):
		selected_shape = sel


func _save_workshop() -> void:
	if _netbot:
		return # two local netbot instances share user:// — don't clobber the real save
	var cf: ConfigFile = ConfigFile.new()
	cf.set_value("workshop", "version", 1)
	cf.set_value("workshop", "unlocked", unlocked_styles)
	cf.set_value("workshop", "selected", selected_shape)
	cf.set_value("workshop", "materials", materials_owned)
	cf.set_value("workshop", "shapes", player_shapes)
	cf.save(SAVE_PATH) # ignore error; non-fatal


func _restart_run() -> void:
	_reset_run()
	_enter_state(State.CRAFT)


func _on_restart_pressed() -> void:
	if net_active:
		if net_ended:
			_net_teardown() # disconnect screen: the button is BACK TO MENU
			return
		if net_rematch_sent:
			return
		net_rematch_sent = true
		restart_button.disabled = true
		rematch_status.text = _t("rematch_wait") % net_opp_name
		rematch_status.visible = true
		_pulse(rematch_status)
		_net_rematch_ready.rpc()
		_maybe_start_rematch()
		return
	_restart_run()


func _on_over_menu_pressed() -> void:
	if net_active:
		_net_teardown()
		return
	_reset_run()
	_enter_state(State.READY)


func _on_fight_pressed() -> void:
	if net_active:
		if net_ready_sent:
			return
		net_ready_sent = true
		fight_button.disabled = true
		craft_info.text = _t("waiting")
		_net_craft_ready.rpc(_net_my_config())
		if not net_opp_config.is_empty():
			_enter_state(State.WIND)
		return
	_enter_state(State.WIND)


func _on_lang_pressed(code: String) -> void:
	lang = code
	_apply_language()


func _on_shape_selected(id: String) -> void:
	if not unlocked_styles.has(id):
		var idx: int = _style_unlock_index(id)
		craft_info.text = _t("locked_info") % (String(OPPONENTS[idx].name) if idx >= 0 else "")
		return
	selected_shape = id
	craft_info.text = _t("selected_info") % String(STYLE_DEFS[id].label)
	_save_workshop()
	_refresh_craft()
	_update_workshop_preview()


func _on_material_pressed(mat_id: String) -> void:
	var def: Dictionary = MATERIAL_DEFS[mat_id]
	if materials_owned.get(mat_id, 0) <= 0:
		craft_info.text = _t("no_mat") % def.label
		return
	materials_owned[mat_id] -= 1
	var stats: Dictionary = player_shapes[selected_shape]
	stats.mass = clampf(stats.mass + def.mass, 1.4, 3.0)
	stats.balance = clampf(stats.balance + def.balance, 55.0, 85.0)
	craft_info.text = _t("forged") % [def.label, STYLE_DEFS[selected_shape].label]
	_save_workshop()
	_refresh_craft()


func _clear_tops() -> void:
	if is_instance_valid(player_top):
		player_top.queue_free()
	if is_instance_valid(foe_top):
		foe_top.queue_free()
	player_top = null
	foe_top = null


# ---------------------------------------------------------------- audio

func _build_sfx_pool() -> void:
	for i: int in 8:
		var p: AudioStreamPlayer = AudioStreamPlayer.new()
		add_child(p)
		_sfx_pool.append(p)


func _play_sfx(stream: AudioStream, volume_db: float = 0.0, pitch_jitter: float = 0.1) -> void:
	if stream == null or _sfx_pool.is_empty():
		return
	var p: AudioStreamPlayer = _sfx_pool[_sfx_index]
	_sfx_index = (_sfx_index + 1) % _sfx_pool.size()
	p.stop()
	p.stream = stream
	p.volume_db = volume_db
	p.pitch_scale = 1.0 + _rng.randf_range(-pitch_jitter, pitch_jitter)
	p.play()


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
	for panel: Control in _all_panels:
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
	score_row.visible = net_active
	if net_active:
		duel_label.text = _t("vs_line") % net_opp_name
		my_pips.wins = net_my_wins
		opp_pips.wins = net_opp_wins
		my_pips.queue_redraw()
		opp_pips.queue_redraw()
	else:
		var opp: Dictionary = OPPONENTS[mini(duel_index, OPPONENTS.size() - 1)]
		duel_label.text = _t("duel_line") % [mini(duel_index + 1, OPPONENTS.size()), OPPONENTS.size(), opp.name]
	mats_label.text = _t("mats_line") % [materials_owned.merbau, materials_owned.kemuning, materials_owned.besi]


func _apply_language() -> void:
	ready_heritage.text = _t("heritage")
	ready_fact.text = _t("fact")
	ready_prompt.text = _t("prompt")
	wind_hint.text = _t("wind_hint")
	battle_hint.text = _t("battle_hint")
	wind_meter.label_text = _t("meter")
	player_gauge.title = _t("gauge_you")
	foe_gauge.title = net_opp_name if net_active and not net_opp_name.is_empty() else _t("gauge_foe")
	craft_title.text = _t("bench")
	craft_mats_hint.text = _t("mats_hint")
	craft_info.text = _t("pick_info")
	fight_button.text = _t("fight")
	restart_button.text = _t("restart")
	over_hint.text = _t("or_space")
	sp_button.text = _t("single_player")
	mp_button.text = _t("multiplayer")
	quit_button.text = _t("quit")
	mp_title.text = _t("multiplayer")
	mp_steam_header_label.text = _t("mp_steam_header")
	mp_lan_header_label.text = _t("mp_lan_header")
	host_steam_button.text = _t("host_steam")
	host_lan_button.text = _t("host_lan")
	join_lan_button.text = _t("join_lan")
	lan_ip_label.text = _t("lan_ip_label")
	steam_join_hint_label.text = _t("steam_join_hint")
	steam_offline_label.text = _t("steam_offline")
	mp_back_button.text = _t("back")
	invite_button.text = _t("invite_friend")
	wait_cancel_button.text = _t("cancel")
	over_menu_button.text = _t("back_menu")
	craft_sub.text = _t("first_to_3")
	for id: String in shape_cards:
		var card: Dictionary = shape_cards[id]
		# role text is owned by _refresh_craft (locked hint vs role line)
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
	b.pressed.connect(_on_any_button_pressed)
	return b


func _on_any_button_pressed() -> void:
	_play_sfx(SND_CLICK, -6.0, 0.05)


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
	_all_panels.append(c)
	return c


func _mk_stat_row(parent: Container, fill_color: Color, layered: bool = false) -> Dictionary:
	var row: HBoxContainer = HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var lbl: Label = _mk_label("", 13)
	lbl.custom_minimum_size = Vector2(70.0, 0.0)
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	row.add_child(lbl)
	var bar: ProgressBar = ProgressBar.new()
	bar.max_value = 1.0
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(130.0, 14.0)
	bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var bg: StyleBoxFlat = StyleBoxFlat.new()
	bg.bg_color = Color(0.0, 0.0, 0.0, 0.5)
	bg.set_corner_radius_all(4)
	bar.add_theme_stylebox_override("background", bg)
	var fill: StyleBoxFlat = StyleBoxFlat.new()
	# layered: bottom bar shows the forged total in a brighter tint; the overlay
	# draws the base on top, so the bright sliver past it reads as forged bonus
	fill.bg_color = fill_color.lightened(0.5) if layered else fill_color
	fill.set_corner_radius_all(4)
	bar.add_theme_stylebox_override("fill", fill)
	var over: ProgressBar = null
	if layered:
		over = ProgressBar.new()
		over.max_value = 1.0
		over.show_percentage = false
		over.set_anchors_preset(Control.PRESET_FULL_RECT)
		over.mouse_filter = Control.MOUSE_FILTER_IGNORE
		over.add_theme_stylebox_override("background", StyleBoxEmpty.new())
		var ofill: StyleBoxFlat = StyleBoxFlat.new()
		ofill.bg_color = fill_color
		ofill.set_corner_radius_all(4)
		over.add_theme_stylebox_override("fill", ofill)
		bar.add_child(over)
	row.add_child(bar)
	parent.add_child(row)
	return {"label": lbl, "bar": bar, "over": over}


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
	score_row = HBoxContainer.new()
	score_row.alignment = BoxContainer.ALIGNMENT_CENTER
	score_row.add_theme_constant_override("separation", 16)
	score_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	score_row.visible = false
	my_pips = ScorePips.new()
	my_pips.color = PLAYER_COLOR
	score_row.add_child(my_pips)
	opp_pips = ScorePips.new()
	opp_pips.color = FOE_COLOR
	opp_pips.rtl = true # mirrored so both scores grow toward the center
	score_row.add_child(opp_pips)
	center_box.add_child(score_row)
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

	battle_hint = _mk_label("", 15)
	battle_hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	battle_hint.offset_left = -420.0
	battle_hint.offset_right = 420.0
	battle_hint.offset_top = -40.0
	battle_hint.offset_bottom = -14.0
	battle_hint.modulate = Color(1.0, 1.0, 1.0, 0.75)
	battle_hint.visible = false
	hud.add_child(battle_hint)

	menu_notice = _mk_label("", 15, Color(1.0, 0.45, 0.3))
	menu_notice.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	menu_notice.offset_left = -420.0
	menu_notice.offset_right = 420.0
	menu_notice.offset_top = -80.0
	menu_notice.offset_bottom = -50.0
	menu_notice.modulate.a = 0.0
	ui.add_child(menu_notice)

	_build_ready_panel()
	_build_mp_panel()
	_build_wait_panel()
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
	var menu_col: VBoxContainer = VBoxContainer.new()
	menu_col.add_theme_constant_override("separation", 10)
	menu_col.custom_minimum_size = Vector2(260.0, 0.0)
	sp_button = _mk_button("", PLAYER_COLOR)
	sp_button.add_theme_font_size_override("font_size", 20)
	sp_button.pressed.connect(_on_single_player_pressed)
	menu_col.add_child(sp_button)
	mp_button = _mk_button("", Color(0.82, 0.6, 0.24))
	mp_button.add_theme_font_size_override("font_size", 20)
	mp_button.pressed.connect(_on_multiplayer_pressed)
	menu_col.add_child(mp_button)
	quit_button = _mk_button("", Color(0.3, 0.2, 0.1), true)
	quit_button.pressed.connect(_on_quit_pressed)
	menu_col.add_child(quit_button)
	var menu_wrap: CenterContainer = CenterContainer.new()
	menu_wrap.add_child(menu_col)
	v.add_child(menu_wrap)
	ready_prompt = _mk_label("", 16, Color(0.95, 0.95, 0.9))
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


func _build_mp_panel() -> void:
	mp_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box()
	mp_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	box.add_child(v)
	mp_title = _mk_label("", 30, PLAYER_COLOR)
	v.add_child(mp_title)
	mp_steam_header_label = _mk_label("", 14, Color(0.75, 0.66, 0.52))
	v.add_child(mp_steam_header_label)
	host_steam_button = _mk_button("", Color(0.82, 0.6, 0.24))
	host_steam_button.pressed.connect(_on_host_steam_pressed)
	var hs_wrap: CenterContainer = CenterContainer.new()
	hs_wrap.add_child(host_steam_button)
	v.add_child(hs_wrap)
	steam_join_hint_label = _mk_label("", 12, Color(0.78, 0.7, 0.56))
	v.add_child(steam_join_hint_label)
	steam_offline_label = _mk_label("", 13, Color(1.0, 0.45, 0.3))
	steam_offline_label.visible = false
	v.add_child(steam_offline_label)
	v.add_child(HSeparator.new())
	mp_lan_header_label = _mk_label("", 14, Color(0.75, 0.66, 0.52))
	v.add_child(mp_lan_header_label)
	host_lan_button = _mk_button("", Color(0.82, 0.6, 0.24))
	host_lan_button.pressed.connect(_on_host_lan_pressed)
	var hl_wrap: CenterContainer = CenterContainer.new()
	hl_wrap.add_child(host_lan_button)
	v.add_child(hl_wrap)
	var join_row: HBoxContainer = HBoxContainer.new()
	join_row.add_theme_constant_override("separation", 8)
	join_row.alignment = BoxContainer.ALIGNMENT_CENTER
	lan_ip_label = _mk_label("", 14)
	join_row.add_child(lan_ip_label)
	lan_ip_edit = _mk_line_edit("127.0.0.1")
	lan_ip_edit.text = "127.0.0.1"
	lan_ip_edit.text_submitted.connect(func(_txt: String) -> void: _on_join_lan_pressed())
	join_row.add_child(lan_ip_edit)
	join_lan_button = _mk_button("", Color(0.82, 0.6, 0.24))
	join_lan_button.pressed.connect(_on_join_lan_pressed)
	join_row.add_child(join_lan_button)
	v.add_child(join_row)
	mp_back_button = _mk_button("", Color(0.3, 0.2, 0.1), true)
	mp_back_button.pressed.connect(_on_mp_back_pressed)
	var back_wrap: CenterContainer = CenterContainer.new()
	back_wrap.add_child(mp_back_button)
	v.add_child(back_wrap)


func _build_wait_panel() -> void:
	wait_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box()
	wait_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	box.add_child(v)
	wait_title = _mk_label("", 30, PLAYER_COLOR)
	v.add_child(wait_title)
	wait_info = _mk_label("", 15)
	v.add_child(wait_info)
	invite_button = _mk_button("", Color(0.82, 0.6, 0.24))
	invite_button.visible = false
	invite_button.pressed.connect(_on_invite_friend_pressed)
	var iv_wrap: CenterContainer = CenterContainer.new()
	iv_wrap.add_child(invite_button)
	v.add_child(iv_wrap)
	wait_cancel_button = _mk_button("", Color(0.3, 0.2, 0.1), true)
	wait_cancel_button.pressed.connect(_on_mp_cancel_pressed)
	var cc_wrap: CenterContainer = CenterContainer.new()
	cc_wrap.add_child(wait_cancel_button)
	v.add_child(cc_wrap)
	var pulse: Tween = create_tween().set_loops()
	pulse.tween_property(wait_title, "modulate:a", 0.35, 0.7)
	pulse.tween_property(wait_title, "modulate:a", 1.0, 0.7)


func _mk_line_edit(placeholder: String) -> LineEdit:
	var e: LineEdit = LineEdit.new()
	e.placeholder_text = placeholder
	e.custom_minimum_size = Vector2(190.0, 0.0)
	e.add_theme_font_size_override("font_size", 16)
	e.add_theme_color_override("font_color", TEXT_COLOR)
	e.add_theme_color_override("caret_color", PLAYER_COLOR)
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = Color(0.0, 0.0, 0.0, 0.5)
	sb.set_corner_radius_all(8)
	sb.border_width_bottom = 2
	sb.border_width_top = 2
	sb.border_width_left = 2
	sb.border_width_right = 2
	sb.border_color = Color(0.55, 0.38, 0.16, 0.8)
	sb.content_margin_left = 10.0
	sb.content_margin_right = 10.0
	sb.content_margin_top = 6.0
	sb.content_margin_bottom = 6.0
	e.add_theme_stylebox_override("normal", sb)
	var sb_f: StyleBoxFlat = sb.duplicate()
	sb_f.border_color = PLAYER_COLOR
	e.add_theme_stylebox_override("focus", sb_f)
	return e


func _show_menu_screen(screen: MenuScreen) -> void:
	menu_screen = screen
	match screen:
		MenuScreen.TITLE:
			_show_panel(ready_panel)
		MenuScreen.MP:
			_refresh_mp_panel()
			_show_panel(mp_panel)
		MenuScreen.WAIT:
			_show_panel(wait_panel)


func _show_menu_notice(text: String) -> void:
	menu_notice.text = text
	menu_notice.modulate.a = 1.0
	if _notice_tween != null and _notice_tween.is_valid():
		_notice_tween.kill()
	_notice_tween = create_tween()
	_notice_tween.tween_property(menu_notice, "modulate:a", 0.0, 0.8).set_delay(4.0)


func _refresh_mp_panel() -> void:
	var steam_ok: bool = Online.steam_ready
	host_steam_button.disabled = not steam_ok
	host_steam_button.modulate = Color(1.0, 1.0, 1.0, 1.0) if steam_ok else Color(0.55, 0.55, 0.55, 1.0)
	steam_offline_label.visible = not steam_ok
	host_lan_button.disabled = false
	join_lan_button.disabled = false


func _set_wait_status(title: String, info: String, show_invite: bool) -> void:
	wait_title.text = title
	wait_info.text = info
	invite_button.visible = show_invite


func _lan_display_ip() -> String:
	var fallback: String = ""
	for ip: String in IP.get_local_addresses():
		if ip.count(".") != 3 or ip.begins_with("127."):
			continue
		if ip.begins_with("192.168.") or ip.begins_with("10."):
			return ip
		if fallback.is_empty():
			fallback = ip
	return fallback if not fallback.is_empty() else "127.0.0.1"


func _on_single_player_pressed() -> void:
	_enter_state(State.CRAFT)


func _on_multiplayer_pressed() -> void:
	_show_menu_screen(MenuScreen.MP)


func _on_quit_pressed() -> void:
	Online.leave_lobby()
	get_tree().quit()


func _on_mp_back_pressed() -> void:
	_show_menu_screen(MenuScreen.TITLE)


func _on_host_steam_pressed() -> void:
	host_steam_button.disabled = true
	host_lan_button.disabled = true
	join_lan_button.disabled = true
	_show_menu_screen(MenuScreen.WAIT)
	_set_wait_status(_t("connecting"), "", false)
	wait_cancel_button.disabled = true # cancelling mid-await would let the late lobby_created callback resurrect an abandoned lobby
	var err: int = await Online.host_steam_lobby()
	wait_cancel_button.disabled = false
	if err == Online.ErrorCodes.SUCCESS:
		_set_wait_status(_t("waiting_opponent"), _t("invite_hint"), true)
	else:
		_show_menu_screen(MenuScreen.MP)
		_show_menu_notice(_t("err_host_failed"))


func _on_invite_friend_pressed() -> void:
	if Online.steam_lobby_id != 0:
		Steam.activateGameOverlayInviteDialog(Online.steam_lobby_id)


func _on_host_lan_pressed() -> void:
	var err: int = Online.host_local_lobby()
	if err == Online.ErrorCodes.SUCCESS:
		_show_menu_screen(MenuScreen.WAIT)
		_set_wait_status(_t("waiting_opponent"), _t("lan_share_ip") % _lan_display_ip(), false)
	else:
		_show_menu_notice(_t("err_host_failed"))


func _on_join_lan_pressed() -> void:
	var address: String = lan_ip_edit.text.strip_edges()
	if address.is_empty():
		address = Online.LOCAL_SERVER_ADDRESS
	var err: int = Online.join_address(address)
	if err != Online.ErrorCodes.SUCCESS:
		_show_menu_notice(_t("err_join_failed"))
		return
	# SUCCESS only means the ENet connection attempt started; completion arrives
	# via player_connected (count 2) and failure via connection_failed.
	_show_menu_screen(MenuScreen.WAIT)
	_set_wait_status(_t("connecting"), "", false)


func _on_mp_cancel_pressed() -> void:
	Online.leave_lobby()
	_show_menu_screen(MenuScreen.MP)


func _build_craft_panel() -> void:
	craft_panel = _mk_fullrect_center()
	craft_panel.offset_right = -240.0 # leave a strip of arena visible for the 3D preview
	var box: PanelContainer = _mk_panel_box()
	craft_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	box.add_child(v)
	craft_title = _mk_label("", 30, PLAYER_COLOR)
	v.add_child(craft_title)
	craft_duel_label = _mk_label("", 16)
	v.add_child(craft_duel_label)
	craft_sub = _mk_label("", 13, Color(0.75, 0.66, 0.52))
	craft_sub.visible = false
	v.add_child(craft_sub)

	var cards: GridContainer = GridContainer.new()
	cards.columns = 3
	cards.add_theme_constant_override("h_separation", 12)
	cards.add_theme_constant_override("v_separation", 12)
	var cards_wrap: CenterContainer = CenterContainer.new()
	cards_wrap.add_child(cards)
	v.add_child(cards_wrap)
	for id: String in STYLE_DEFS:
		var def: Dictionary = STYLE_DEFS[id]
		var card: PanelContainer = _mk_panel_box()
		var csb: StyleBoxFlat = card.get_theme_stylebox("panel") as StyleBoxFlat
		csb.content_margin_left = 12.0
		csb.content_margin_right = 12.0
		csb.content_margin_top = 10.0
		csb.content_margin_bottom = 10.0
		cards.add_child(card)
		var cv: VBoxContainer = VBoxContainer.new()
		cv.add_theme_constant_override("separation", 5)
		card.add_child(cv)
		var pick: Button = _mk_button(def.label, Color(0.82, 0.6, 0.24))
		pick.pressed.connect(_on_shape_selected.bind(id))
		cv.add_child(pick)
		var role: Label = _mk_label("", 12, Color(0.78, 0.7, 0.56))
		cv.add_child(role)
		var mass_row: Dictionary = _mk_stat_row(cv, Color(0.85, 0.45, 0.25), true)
		var spin_row: Dictionary = _mk_stat_row(cv, Color(0.35, 0.75, 0.9), true)
		var bal_row: Dictionary = _mk_stat_row(cv, Color(0.5, 0.85, 0.4), true)
		shape_cards[id] = {
			"card": card,
			"pick": pick,
			"role": role,
			"mass": mass_row.bar,
			"spin_reserve": spin_row.bar,
			"balance": bal_row.bar,
			"mass_over": mass_row.over,
			"spin_over": spin_row.over,
			"bal_over": bal_row.over,
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
	craft_opp_status = _mk_label("", 14, FOE_COLOR)
	v.add_child(craft_opp_status)
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
	v.add_child(round_label)
	round_award_row = HBoxContainer.new()
	round_award_row.add_theme_constant_override("separation", 14)
	round_award_row.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(round_award_row)
	mats_saved_label = _mk_label("", 13, Color(0.75, 0.66, 0.52))
	mats_saved_label.visible = false
	v.add_child(mats_saved_label)
	unlock_label = _mk_label("", 20, PLAYER_COLOR)
	unlock_label.visible = false
	v.add_child(unlock_label)
	match_point_label = _mk_label("", 20, Color(1.0, 0.45, 0.3))
	match_point_label.visible = false
	v.add_child(match_point_label)
	award_label = _mk_label("", 18)
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
	over_mats_title = _mk_label("", 14, Color(0.75, 0.66, 0.52))
	over_mats_title.visible = false
	v.add_child(over_mats_title)
	over_award_row = HBoxContainer.new()
	over_award_row.add_theme_constant_override("separation", 14)
	over_award_row.alignment = BoxContainer.ALIGNMENT_CENTER
	over_award_row.visible = false
	v.add_child(over_award_row)
	over_bonus_label = _mk_label("", 14, PLAYER_COLOR)
	over_bonus_label.visible = false
	v.add_child(over_bonus_label)
	restart_button = _mk_button("", PLAYER_COLOR)
	restart_button.name = "RestartButton"
	restart_button.add_theme_font_size_override("font_size", 20)
	restart_button.pressed.connect(_on_restart_pressed)
	var rb_wrap: CenterContainer = CenterContainer.new()
	rb_wrap.add_child(restart_button)
	v.add_child(rb_wrap)
	over_menu_button = _mk_button("", Color(0.3, 0.2, 0.1), true)
	over_menu_button.pressed.connect(_on_over_menu_pressed)
	var om_wrap: CenterContainer = CenterContainer.new()
	om_wrap.add_child(over_menu_button)
	v.add_child(om_wrap)
	rematch_status = _mk_label("", 14, Color(0.75, 0.66, 0.52))
	rematch_status.visible = false
	v.add_child(rematch_status)
	over_hint = _mk_label("", 13, Color(0.75, 0.66, 0.52))
	v.add_child(over_hint)


func _refresh_craft() -> void:
	if net_active:
		craft_duel_label.text = _t("score_line") % [net_my_wins, net_opp_wins, net_opp_name]
	else:
		var opp: Dictionary = OPPONENTS[mini(duel_index, OPPONENTS.size() - 1)]
		craft_duel_label.text = _t("craft_duel_line") % [mini(duel_index + 1, OPPONENTS.size()), OPPONENTS.size(), opp.name]
	craft_sub.visible = net_active
	for mat_id: String in MATERIAL_DEFS:
		var mb: Button = material_buttons[mat_id]
		var def: Dictionary = MATERIAL_DEFS[mat_id]
		mb.text = "%s ×%d\n%s" % [def.label, materials_owned.get(mat_id, 0), _t("desc_" + mat_id)]
	for id: String in shape_cards:
		var card: Dictionary = shape_cards[id]
		var stats: Dictionary = player_shapes[id]
		var base: Dictionary = STYLE_DEFS[id]
		var locked: bool = not unlocked_styles.has(id)
		_tween_bar(card.mass, (stats.mass - 1.4) / 1.6)
		_tween_bar(card.spin_reserve, (stats.spin_reserve - 60.0) / 50.0)
		_tween_bar(card.balance, (stats.balance - 55.0) / 30.0)
		_tween_bar(card.mass_over, (base.mass - 1.4) / 1.6)
		_tween_bar(card.spin_over, (base.spin_reserve - 60.0) / 50.0)
		_tween_bar(card.bal_over, (base.balance - 55.0) / 30.0)
		var role: Label = card.role
		if locked:
			var idx: int = _style_unlock_index(id)
			role.text = _t("locked_hint") % (String(OPPONENTS[idx].name) if idx >= 0 else "")
			role.add_theme_color_override("font_color", Color(0.85, 0.55, 0.3))
		else:
			role.text = _t("role_" + id)
			role.add_theme_color_override("font_color", Color(0.78, 0.7, 0.56))
		var pick: Button = card.pick
		pick.disabled = locked
		var panel: PanelContainer = card.card
		if locked:
			panel.modulate = Color(0.42, 0.42, 0.42, 1.0)
		elif id == selected_shape:
			panel.modulate = Color(1.0, 1.0, 1.0, 1.0)
		else:
			panel.modulate = Color(0.68, 0.68, 0.68, 1.0)
		var prefix: String = "> " if id == selected_shape else ""
		pick.text = prefix + String(STYLE_DEFS[id].label)


func _tween_bar(bar: ProgressBar, value: float) -> void:
	var tw: Tween = create_tween()
	tw.tween_property(bar, "value", clampf(value, 0.0, 1.0), 0.35).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


# ---------------------------------------------------------------- multiplayer
# Wire convention: every vector on the wire is in HOST frame. The client negates
# x/z at its boundary (applying snapshots/FX, sending its nudge point). Aim angles
# cross unchanged: FORWARD.rotated(UP, a) mirrored through the origin equals
# BACK.rotated(UP, a). Own top is always gold at z=+3, opponent teal at z=-3;
# PlayerData.color is deliberately ignored for the tops.

func _net_is_host() -> bool:
	return multiplayer.is_server()


func _net_sim_authority() -> bool:
	return not net_active or multiplayer.is_server()


func _net_my_config() -> Dictionary:
	return {
		"name": Online.personal_player_data.display_name,
		"shape": selected_shape,
		"stats": (player_shapes[selected_shape] as Dictionary).duplicate(),
	}


func _net_setup() -> void:
	net_active = true
	net_ended = false
	net_opp_config = {}
	net_ready_sent = false
	net_wind_sent = false
	net_opp_wind_in = false
	net_my_wins = 0
	net_opp_wins = 0
	net_client_nudge_cd = 0.0
	net_rematch_sent = false
	net_opp_rematch = false
	net_bonus_text = ""
	net_match_mats = {}
	net_opp_name = ""
	for pd: PlayerData in Online.players.values():
		if pd.multiplayer_id != multiplayer.get_unique_id():
			net_opp_name = pd.display_name
			break # first non-self entry (host sorts first); ignore any stale duplicates
	_reset_run()
	# MP fights with the persistent workshop build + materials, same as SP
	foe_gauge.title = net_opp_name
	foe_gauge.ring_color = FOE_COLOR


@rpc("authority", "reliable", "call_local")
func _net_start_match() -> void:
	_net_setup()
	_enter_state(State.CRAFT)


func _net_sanitize_config(cfg: Dictionary) -> Dictionary:
	# The host simulates everything (clients are puppets), so clamping here is the
	# entire anti-cheat boundary: a modded client can at worst field a maximally
	# forged LEGAL build. Both peers sanitize for display consistency.
	var style: String = String(cfg.get("shape", "jantung"))
	if not STYLE_DEFS.has(style):
		style = "jantung"
	var def: Dictionary = STYLE_DEFS[style]
	var raw: Variant = cfg.get("stats")
	var in_stats: Dictionary = raw if raw is Dictionary else {}
	var mass_v: Variant = in_stats.get("mass", def.mass)
	var bal_v: Variant = in_stats.get("balance", def.balance)
	return {
		"name": String(cfg.get("name", net_opp_name)),
		"shape": style,
		"stats": {
			"mass": clampf(float(mass_v) if (mass_v is float or mass_v is int) else float(def.mass), 1.4, 3.0),
			"balance": clampf(float(bal_v) if (bal_v is float or bal_v is int) else float(def.balance), 55.0, 85.0),
			"spin_reserve": def.spin_reserve, # not forgeable — always the style base
			"mesh": def.mesh, # derived, never client-supplied
		},
	}


@rpc("any_peer", "reliable")
func _net_craft_ready(cfg: Dictionary) -> void:
	net_opp_config = _net_sanitize_config(cfg)
	if state == State.CRAFT and not net_ready_sent:
		craft_opp_status.text = _t("opp_ready") % net_opp_name
	if net_ready_sent and state == State.CRAFT:
		_enter_state(State.WIND)


func _net_release_wind() -> void:
	net_wind_sent = true
	net_my_wind = Vector2(wind_power, aim_angle)
	wind_meter.visible = false
	aim_arrow.visible = false
	if is_instance_valid(player_top):
		player_top.set_winding(false)
	wind_hint.text = _t("waiting")
	if wind_power > 95.0:
		_toast(_t("toast_snap"), Color(1.0, 0.35, 0.25), Vector3(0.0, 0.5, 3.0), true)
	_net_wind_done.rpc(net_my_wind.x, net_my_wind.y)
	if net_opp_wind_in:
		_mp_do_launch(net_my_wind.x, net_my_wind.y, net_opp_wind.x, net_opp_wind.y)


@rpc("any_peer", "reliable")
func _net_wind_done(power: float, angle: float) -> void:
	net_opp_wind = Vector2(power, angle)
	net_opp_wind_in = true
	if net_wind_sent and state == State.WIND:
		_mp_do_launch(net_my_wind.x, net_my_wind.y, power, angle)


func _mp_do_launch(my_power: float, my_angle: float, opp_power: float, opp_angle: float) -> void:
	# Deterministic on both peers: pure function of the two (power, angle) pairs.
	# Never add RNG here — the peers must converge without a host round-trip.
	if state != State.WIND:
		return
	wind_meter.visible = false
	wind_hint.visible = false
	aim_arrow.visible = false
	last_wind_effectiveness = _wind_effectiveness(my_power)
	player_top.set_winding(false)
	player_top.launch(Vector3.FORWARD.rotated(Vector3.UP, my_angle), last_wind_effectiveness)
	_play_sfx(SND_LAUNCH, -4.0, 0.15)
	foe_top = _spawn_top(false)
	foe_gauge.ring_color = foe_top.accent_color
	foe_top.launch(Vector3.BACK.rotated(Vector3.UP, opp_angle), _wind_effectiveness(opp_power))
	if opp_power > 95.0:
		_toast(_t("toast_snap"), Color(1.0, 0.35, 0.25), Vector3(0.0, 0.5, -3.0), true)
	last_striker = ""
	hit_cooldown = 0.0
	nudge_cooldown = 0.0
	net_client_nudge_cd = 0.0
	_enter_state(State.BATTLE)


@rpc("authority", "unreliable_ordered")
func _net_snapshot(hp: Vector2, hspin: float, hwob: float, cp: Vector2, cspin: float, cwob: float) -> void:
	if state != State.BATTLE:
		return # late packets after round end
	if is_instance_valid(foe_top) and foe_top.alive:
		foe_top.position.x = -hp.x
		foe_top.position.z = -hp.y
		foe_top.spin = hspin
		foe_top.wobble = hwob
	if is_instance_valid(player_top) and player_top.alive:
		player_top.position.x = -cp.x
		player_top.position.z = -cp.y
		player_top.spin = cspin
		player_top.wobble = cwob


@rpc("any_peer", "reliable")
func _net_request_nudge(point: Vector2) -> void:
	# point is already in HOST frame (the client negated it)
	if not _net_is_host() or state != State.BATTLE:
		return
	if net_client_nudge_cd > 0.0:
		return
	if not is_instance_valid(foe_top) or not foe_top.alive or foe_top.spin <= NUDGE_SPIN_COST:
		return
	var dir: Vector3 = Vector3(point.x, 0.0, point.y) - foe_top.position
	dir.y = 0.0
	if dir.length() < 0.05:
		return
	dir = dir.normalized()
	# shorter than the client's own 0.35s gate: arrival-time jitter must not eat pushes
	# the client already rate-limited (and showed optimistic FX for) at send time
	net_client_nudge_cd = NUDGE_COOLDOWN * 0.8
	foe_top.velocity += dir * NUDGE_POWER
	foe_top.spin = maxf(foe_top.spin - NUDGE_SPIN_COST, 0.0)
	foe_top.flash_direction(dir)


@rpc("authority", "reliable")
func _net_hit_fx(contact: Vector2, strength: float) -> void:
	_hit_effects(Vector3(-contact.x, 0.0, -contact.y), strength)
	if is_instance_valid(player_top):
		player_top.flash_accent()
	if is_instance_valid(foe_top):
		foe_top.flash_accent()


@rpc("authority", "reliable")
func _net_nudge_fx(dir: Vector2) -> void:
	if is_instance_valid(foe_top):
		foe_top.flash_direction(Vector3(-dir.x, 0.0, -dir.y))
	_play_sfx(SND_NUDGE, -8.0, 0.2)


@rpc("authority", "reliable", "call_local")
func _net_round_over(host_reason: String, cli_reason: String, host_wins: bool) -> void:
	if state != State.BATTLE:
		return
	var i_win: bool = host_wins if _net_is_host() else not host_wins
	var my_reason: String = host_reason if _net_is_host() else cli_reason
	var opp_reason: String = cli_reason if _net_is_host() else host_reason
	_apply_round_result(my_reason, opp_reason, i_win)


func _net_after_round() -> void:
	if not net_active or net_ended or state != State.ROUND_OVER:
		return
	if net_my_wins >= NET_MATCH_TARGET or net_opp_wins >= NET_MATCH_TARGET:
		# win counters are mirrored on both peers (reliable call_local round RPC),
		# so the match end is deterministic locally — no extra RPC needed
		_net_finish_match()
	elif _net_is_host():
		_net_next_round.rpc()


func _net_finish_match() -> void:
	var i_won: bool = net_my_wins >= NET_MATCH_TARGET
	if _netbot:
		print("netbot: match over %d-%d vs %s" % [net_my_wins, net_opp_wins, net_opp_name])
	_play_sfx(SND_WIN if i_won else SND_LOSE, 0.0, 0.0)
	_reset_over_panel()
	over_title.text = _t("match_win") if i_won else _t("match_lose") % net_opp_name
	over_title.add_theme_color_override("font_color", PLAYER_COLOR if i_won else Color(1.0, 0.45, 0.3))
	over_stats.text = _t("score_line") % [net_my_wins, net_opp_wins, net_opp_name]
	if not net_match_mats.is_empty():
		over_mats_title.text = _t("match_mats")
		over_mats_title.visible = true
		over_award_row.visible = true
		_show_award_icons(over_award_row, net_match_mats, "×%d")
	if i_won and not net_bonus_text.is_empty():
		over_bonus_label.text = net_bonus_text
		over_bonus_label.visible = true
	restart_button.text = _t("rematch")
	_enter_state(State.OVER)


@rpc("any_peer", "reliable")
func _net_rematch_ready() -> void:
	net_opp_rematch = true
	if not net_rematch_sent and state == State.OVER:
		rematch_status.text = _t("rematch_offer") % net_opp_name
		rematch_status.visible = true
		_pulse(rematch_status)
	_maybe_start_rematch()


func _maybe_start_rematch() -> void:
	if _net_is_host() and net_rematch_sent and net_opp_rematch:
		_net_start_match.rpc() # _net_setup zeroes wins/flags -> CRAFT


@rpc("authority", "reliable", "call_local")
func _net_next_round() -> void:
	if state != State.ROUND_OVER:
		return
	_enter_state(State.CRAFT)


func _net_teardown() -> void:
	net_ended = true # swallow our own player_disconnected echo during leave_lobby
	Online.leave_lobby() # idempotent
	net_ended = false
	net_opp_config = {}
	net_ready_sent = false
	net_wind_sent = false
	net_opp_wind_in = false
	net_my_wins = 0
	net_opp_wins = 0
	net_rematch_sent = false
	net_opp_rematch = false
	net_bonus_text = ""
	net_match_mats = {}
	net_opp_name = ""
	net_active = false
	_reset_run()
	_apply_language() # restores restart_button / foe_gauge texts
	_enter_state(State.READY)


func _on_mp_joined_lobby() -> void:
	if Online.is_host:
		return # host UI is driven by its own button handlers
	if state != State.READY:
		_reset_run() # abort the SP run for real — stale duel progress must not resume later (workshop persists)
		_enter_state(State.READY) # Steam invite accepted mid-run aborts the run
	_show_menu_screen(MenuScreen.WAIT)
	_set_wait_status(_t("connecting"), "", false)


func _on_mp_player_connected(_pd: PlayerData) -> void:
	if state != State.READY:
		return
	if Online.players.size() < 2:
		return # self-registration echo — keep waiting
	_set_wait_status(_t("opponent_found"), "", false)
	if Online.is_host:
		_net_start_match.rpc()


func _on_mp_player_disconnected(pd: PlayerData) -> void:
	if pd == Online.personal_player_data:
		# our own leave echo: a teardown we started is already handling it, unless an
		# external flow (e.g. accepting a Steam invite mid-match) pulled us out
		if net_active and not net_ended:
			_net_teardown()
		return
	_handle_mp_loss(_t("mp_disconnected"))


func _on_mp_server_disconnected() -> void:
	_handle_mp_loss(_t("mp_server_lost"))


func _on_mp_connection_failed() -> void:
	if state == State.READY and menu_screen == MenuScreen.WAIT:
		_show_menu_screen(MenuScreen.MP)
		_show_menu_notice(_t("err_join_failed"))


func _on_mp_steam_join_response(code: int) -> void:
	# invite-accept failures (lobby full) otherwise produce zero feedback
	if code == Online.ErrorCodes.SUCCESS:
		return
	if Online.is_host or Online.is_busy:
		return # hosting: entering our own lobby echoes as JOIN_FAILED_SAME_OWNER_ID — not a join failure
	if state == State.READY:
		if menu_screen == MenuScreen.WAIT:
			_show_menu_screen(MenuScreen.MP)
		_show_menu_notice(_t("err_join_steam"))


# debug: headless-ish autopilot so a second local instance can play a LAN duel
# unattended (`godot --path . -- netbot-host` / `-- netbot-join`). Inert otherwise.
func _netbot_init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if "netbot-host" in args:
		_netbot = true
		_on_host_lan_pressed.call_deferred()
	elif "netbot-join" in args:
		_netbot = true
		_on_join_lan_pressed.call_deferred()


func _netbot_tick(delta: float) -> void:
	_netbot_cd -= delta
	if _netbot_cd > 0.0:
		return
	_netbot_cd = 0.8
	if not net_active:
		return
	match state:
		State.CRAFT:
			if not net_ready_sent:
				_on_fight_pressed()
		State.WIND:
			if net_wind_sent:
				return
			if not winding:
				winding = true # charge through the real path: _physics_process ramps wind_power
			elif wind_power >= 55.0:
				winding = false
				_net_release_wind()
		State.OVER:
			if not net_ended and not net_rematch_sent:
				_on_restart_pressed() # auto-rematch so soak tests loop; disconnect screen is left alone


func _handle_mp_loss(msg: String) -> void:
	if state == State.READY:
		Online.leave_lobby()
		if menu_screen == MenuScreen.WAIT:
			_show_menu_screen(MenuScreen.MP)
		_show_menu_notice(msg)
	elif net_active and not net_ended:
		net_ended = true # keep net_active true so no SP branch (AI) wakes up mid-teardown
		Online.leave_lobby()
		_reset_over_panel() # clears any rematch-wait state; banked rewards are already saved
		over_title.text = _t("opp_left")
		over_title.add_theme_color_override("font_color", Color(1.0, 0.45, 0.3))
		over_stats.text = _t("score_line") % [net_my_wins, net_opp_wins, net_opp_name]
		restart_button.text = _t("back_menu")
		_enter_state(State.OVER)


# ---------------------------------------------------------------- widgets

class ScorePips:
	extends Control

	var wins: int = 0
	var total: int = 3
	var color: Color = Color.WHITE
	var rtl: bool = false # mirrored fill so both players' pips grow toward the center

	func _ready() -> void:
		custom_minimum_size = Vector2(total * 22.0, 18.0)
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		# drawn circles, not "●○" text — default-font glyph coverage isn't guaranteed
		for i: int in total:
			var idx: int = total - 1 - i if rtl else i
			var center: Vector2 = Vector2(11.0 + i * 22.0, 9.0)
			if idx < wins:
				draw_circle(center, 7.0, color)
			else:
				draw_arc(center, 7.0, 0.0, TAU, 24, Color(1.0, 1.0, 1.0, 0.25), 2.0, true)


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
