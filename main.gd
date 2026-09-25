extends Node3D

enum State { READY, CRAFT, WIND, LAUNCH, BATTLE, ROUND_OVER, OVER, CUTSCENE }
enum MenuScreen { TITLE, MP, WAIT }

const ARENA_SCRIPT: Script = preload("res://scripts/arena_match.gd")
const GASING_SCENE: PackedScene = preload("res://gasing.tscn")
const MENUS_SCRIPT: Script = preload("res://scripts/menus.gd")
const HT = preload("res://scripts/heritage_theme.gd")
const FONT_TITLE: FontFile = preload("res://common/fonts/Kurland.ttf")
const TEX_PANEL: Texture2D = preload("res://assets/ui/panel_ukiran.png")
const TEX_CARD: Texture2D = preload("res://assets/ui/panel_card.png")
const TEX_BTN: Texture2D = preload("res://assets/ui/button_plaque.png")
const TEX_SONGKET: Texture2D = preload("res://assets/ui/songket_band.png")
const TEX_GUNUNGAN: Texture2D = preload("res://assets/ui/gunungan_gold.png")
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
# action kind -> [assets/audio/sfx stem ("" = Kenney only), Kenney fallback, volume dB, pitch];
# the sfx files are load()ed in _ready so a missing one never breaks parsing
const ACTION_SFX: Dictionary = {
	"push": ["", SND_NUDGE, -8.0, 1.0],
	"dash": ["whoosh", SND_NUDGE, -4.0, 1.0],
	"jump": ["jump", SND_LAUNCH, -4.0, 1.0],
	"rush": ["rush_loop", SND_NUDGE, -8.0, 1.0],
	"deny": ["", SND_CLICK, -6.0, 0.6],
	"charge_tick": ["charge_tick", SND_CLICK, -8.0, 1.0],
	"launch": ["", SND_LAUNCH, -7.0, 1.0],
	"snap": ["cord_snap", SND_RINGOUT, -2.0, 1.0],
	"land": ["land", SND_TOPPLE, -6.0, 1.0],
	"gong": ["gong", SND_WIN, -3.0, 1.0],
	"cheer": ["crowd_cheer", SND_WIN, 3.0, 1.0],
	"hover": ["ui_hover", null, 0.0, 1.0], # soft tick on every _mk_button hover (no Kenney fallback)
}
# state -> music bed; ROUND_OVER is absent so the battle bed carries on between rounds
# (MP's between-round CRAFT is skipped in _enter_state for the same reason)
const STATE_MUSIC: Dictionary = {
	State.READY: "menu", State.CRAFT: "menu", State.OVER: "menu",
	State.CUTSCENE: "cutscene", State.WIND: "battle", State.BATTLE: "battle",
}
const TITLE_CAM_SHIFT: float = -2.4 # title framing: the ring slides right of the menu column
const TITLE_FACTS: int = 6 # STRINGS fact_1..fact_6, rotated on the title card
# ---- heritage UI tokens: aliases of scripts/heritage_theme.gd, the one palette
const PLAYER_COLOR: Color = HT.PLAYER_COLOR
const FOE_COLOR: Color = HT.FOE_COLOR
const TEXT_COLOR: Color = HT.TEXT_COLOR
const PANEL_BG: Color = HT.PANEL_BG
const SONGKET_GOLD: Color = HT.SONGKET_GOLD # == PLAYER_COLOR; semantic alias for UI gold
const WOOD_DARK: Color = HT.WOOD_DARK # tertiary plaque (credits/quit/back/lang/skip)
const WOOD_AMBER: Color = HT.WOOD_AMBER # secondary plaque (endless/mp/how-to/settings/host/join)
const WOOD_EDGE: Color = HT.WOOD_EDGE # deep carved-shadow brown
const BORDER_BROWN: Color = HT.BORDER_BROWN # carved rim / line-edit border
const CREAM_MUTED: Color = HT.CREAM_MUTED # secondary text
const PANDAN: Color = HT.PANDAN
const COPPER: Color = HT.COPPER # locked-card price text
const DANGER: Color = HT.DANGER # defeat / offline / match point
const GROOVE: Color = HT.GROOVE # recessed carved slot behind bars
const TEXT_DIM: Color = HT.TEXT_DIM
const INK: Color = HT.INK # dark text on light plaques
const INACTIVE: Color = HT.INACTIVE # dimmed-button modulate
const ENERGY_BLUE: Color = HT.ENERGY_BLUE
const HIT_ORANGE: Color = HT.HIT_ORANGE
const OVERWIND_RED: Color = HT.OVERWIND_RED
const SIDE_YOU: Color = HT.SIDE_YOU
const SIDE_FOE: Color = HT.SIDE_FOE

# Fixed base stats per style; "shape" is the physics archetype (radius/role),
# "mesh" the glb id. The 4 unlockable styles copy their AI owner's preset stats.
const STYLE_DEFS: Dictionary = {
	"jantung": {"label": "Gasing Jantung", "shape": "jantung", "mesh": "jantung", "mass": 2.4, "spin_reserve": 70.0, "balance": 60.0},
	"uri": {"label": "Gasing Uri", "shape": "uri", "mesh": "uri", "mass": 1.4, "spin_reserve": 105.0, "balance": 78.0},
	"pakdin": {"label": "Gasing Pak Din", "shape": "uri", "mesh": "pakdin", "mass": 1.5, "spin_reserve": 88.0, "balance": 66.0, "price": 60},
	"cikros": {"label": "Gasing Cik Ros", "shape": "jantung", "mesh": "cikros", "mass": 2.2, "spin_reserve": 70.0, "balance": 62.0, "price": 80},
	"tokgayong": {"label": "Gasing Tok Gayong", "shape": "jantung", "mesh": "tokgayong", "mass": 2.7, "spin_reserve": 76.0, "balance": 68.0, "price": 110},
	"datuk": {"label": "Gasing Datuk", "shape": "jantung", "mesh": "datuk", "mass": 2.9, "spin_reserve": 82.0, "balance": 74.0, "price": 150},
	# master gasing — purchasable after defeating that master in the campaign
	"kelantan": {"label": "Gasing Kelantan", "shape": "uri", "mesh": "kelantan", "mass": 1.7, "spin_reserve": 82.0, "balance": 62.0, "price": 90},
	"penang": {"label": "Gasing Penang", "shape": "jantung", "mesh": "penang", "mass": 2.1, "spin_reserve": 72.0, "balance": 60.0, "price": 120},
	"melaka": {"label": "Gasing Melaka", "shape": "jantung", "mesh": "melaka", "mass": 1.6, "spin_reserve": 100.0, "balance": 74.0, "price": 150},
	"terengganu": {"label": "Gasing Terengganu", "shape": "uri", "mesh": "terengganu", "mass": 2.3, "spin_reserve": 78.0, "balance": 66.0, "price": 180},
	"sarawak": {"label": "Gasing Sarawak", "shape": "jantung", "mesh": "sarawak", "mass": 2.6, "spin_reserve": 74.0, "balance": 64.0, "price": 220},
	"sabah": {"label": "Gasing Sabah", "shape": "jantung", "mesh": "sabah", "mass": 2.9, "spin_reserve": 80.0, "balance": 76.0, "price": 260},
	"kl": {"label": "Gasing Merdeka", "shape": "uri", "mesh": "kl", "mass": 2.6, "spin_reserve": 92.0, "balance": 80.0, "price": 350},
}
const DEFAULT_STYLES: Array[String] = ["jantung", "uri"]
const LEVEL_XP: Array[int] = [0, 100, 250, 450, 700]
const NET_MATCH_TARGET: int = 3
const SAVE_PATH: String = "user://workshop.cfg"
# per-arena mood presets; "env" GLB swaps the kampung backdrop when the file exists,
# sky/fog/sun/lantern re-theming works even before the GLBs are produced.
# "exposure"/"ambient" (default 1.05/0.9) tame the pale high-albedo day arenas; lanterns stay
# warm/moderate so the dish keeps its wood tone and the dark tops read against it.
const ARENA_DEFS: Dictionary = {
	"kampung": {"env": "", "sky_top": Color(0.30, 0.28, 0.40), "sky_horizon": Color(0.86, 0.52, 0.30),
		"fog": Color(0.72, 0.52, 0.36), "fog_density": 0.008, "sun_color": Color(1.0, 0.86, 0.66),
		"sun_energy": 1.05, "lantern": Color(1.0, 0.62, 0.28), "lantern_energy": 2.2},
	"kelantan": {"env": "res://assets/arena_kelantan.glb", "sky_top": Color(0.35, 0.30, 0.35), "sky_horizon": Color(0.88, 0.58, 0.22),
		"fog": Color(0.62, 0.45, 0.25), "fog_density": 0.004, "sun_color": Color(1.0, 0.78, 0.50),
		"sun_energy": 1.0, "lantern": Color(1.0, 0.72, 0.30), "lantern_energy": 1.6, "exposure": 0.72, "ambient": 0.4},
	"penang": {"env": "res://assets/arena_penang.glb", "sky_top": Color(0.12, 0.08, 0.20), "sky_horizon": Color(0.60, 0.22, 0.18),
		"fog": Color(0.45, 0.22, 0.20), "fog_density": 0.010, "sun_color": Color(1.0, 0.60, 0.45),
		"sun_energy": 0.45, "lantern": Color(1.0, 0.42, 0.22), "lantern_energy": 1.8, "exposure": 0.95, "ambient": 0.55},
	"melaka": {"env": "res://assets/arena_melaka.glb", "sky_top": Color(0.12, 0.15, 0.30), "sky_horizon": Color(0.38, 0.32, 0.52),
		"fog": Color(0.40, 0.40, 0.60), "fog_density": 0.010, "sun_color": Color(0.75, 0.80, 1.0),
		"sun_energy": 0.55, "lantern": Color(1.0, 0.68, 0.40), "lantern_energy": 2.0, "exposure": 0.85, "ambient": 0.45},
	"terengganu": {"env": "res://assets/arena_terengganu.glb", "sky_top": Color(0.15, 0.25, 0.38), "sky_horizon": Color(0.80, 0.72, 0.60),
		"fog": Color(0.55, 0.60, 0.58), "fog_density": 0.005, "sun_color": Color(1.0, 0.86, 0.66),
		"sun_energy": 0.85, "lantern": Color(1.0, 0.72, 0.42), "lantern_energy": 1.6, "exposure": 0.78, "ambient": 0.45},
	"sarawak": {"env": "res://assets/arena_sarawak.glb", "sky_top": Color(0.08, 0.12, 0.14), "sky_horizon": Color(0.30, 0.38, 0.35),
		"fog": Color(0.22, 0.30, 0.26), "fog_density": 0.014, "sun_color": Color(0.70, 0.80, 0.85),
		"sun_energy": 0.5, "lantern": Color(1.0, 0.55, 0.25), "lantern_energy": 2.2},
	"sabah": {"env": "res://assets/arena_sabah.glb", "sky_top": Color(0.35, 0.45, 0.60), "sky_horizon": Color(0.85, 0.80, 0.65),
		"fog": Color(0.55, 0.60, 0.55), "fog_density": 0.004, "sun_color": Color(1.0, 0.88, 0.70),
		"sun_energy": 0.95, "lantern": Color(1.0, 0.85, 0.55), "lantern_energy": 1.5, "exposure": 0.75, "ambient": 0.42},
	"kl": {"env": "res://assets/arena_kl.glb", "sky_top": Color(0.05, 0.05, 0.12), "sky_horizon": Color(0.35, 0.22, 0.40),
		"fog": Color(0.28, 0.20, 0.35), "fog_density": 0.010, "sun_color": Color(0.85, 0.75, 1.0),
		"sun_energy": 0.4, "lantern": Color(0.95, 0.50, 0.90), "lantern_energy": 2.0},
}

# wayang kulit narration before each campaign duel: master id -> {lang -> [paragraphs]}
const CUTSCENES: Dictionary = {
	"kelantan": {
		"en": [
			"In Kelantan, where the paddy turns gold before harvest, giant gasing have spun for centuries. Villagers say the tradition carries the blessing of Che Siti Wan Kembang — the legendary warrior-queen who ruled these lands from the back of an elephant.",
			"Tok Wan Nik has wound cords since he was seven. His tops are cut from merbau heartwood and balanced so finely they hum. They call his gasing the golden heart of Kelantan.",
			"Beat him, and the gelanggang will speak your name from Kota Bharu to the sea.",
		],
		"ms": [
			"Di Kelantan, tempat padi menguning sebelum menuai, gasing raksasa telah berpusing berabad lamanya. Kata orang kampung, tradisi ini membawa restu Che Siti Wan Kembang — ratu pahlawan lagenda yang memerintah dari belakang gajah.",
			"Tok Wan Nik memusing tali sejak umur tujuh tahun. Gasingnya dilarik dari teras merbau dan diimbang halus hingga berdengung. Orang menggelarnya jantung emas Kelantan.",
			"Kalahkan beliau, dan gelanggang akan menyebut namamu dari Kota Bharu hingga ke laut.",
		],
	},
	"penang": {
		"en": [
			"In George Town's shophouse rows, East met West and made something new: the Peranakan — Straits Chinese whose kebaya, kitchens and craft weave two worlds into one.",
			"Kapitan Ong descends from the Kapitan Cina, leaders trusted to keep peace in the old port. His lacquered top burns vermillion and gold, quick and sharp as a festival firecracker.",
			"He strikes fast and laughs faster. Do not blink.",
		],
		"ms": [
			"Di deretan rumah kedai George Town, Timur bertemu Barat dan lahirlah sesuatu yang baharu: Peranakan — Cina Selat yang kebaya, dapur dan seni mereka menganyam dua dunia menjadi satu.",
			"Kapitan Ong berketurunan Kapitan Cina, pemimpin yang diamanahkan menjaga keamanan pelabuhan lama. Gasing lakuernya menyala merah saga dan emas, pantas dan tajam bak mercun perayaan.",
			"Pangkahnya pantas, tawanya lebih pantas. Jangan berkelip.",
		],
	},
	"melaka": {
		"en": [
			"Five hundred years ago, Tamil traders sailed the spice routes to Melaka and stayed. Their descendants, the Chitty, still keep temples fragrant with jasmine and customs found nowhere else on Earth.",
			"Tuan Pillay learned patience from the tides that carried his ancestors. His sapphire top spins long and low, a trading ship riding out the monsoon — it simply refuses to fall.",
			"Outlast him if you can. The spice trade taught his family to wait out anything.",
		],
		"ms": [
			"Lima ratus tahun lalu, pedagang Tamil belayar di laluan rempah ke Melaka dan terus menetap. Keturunan mereka, masyarakat Chitty, masih menjaga kuil yang harum dengan melur dan adat yang tiada di tempat lain di dunia.",
			"Tuan Pillay belajar kesabaran daripada pasang surut yang membawa nenek moyangnya. Gasing nilamnya berpusing lama dan rendah, bagai kapal dagang mengharungi monsun — ia enggan tumbang.",
			"Bertahanlah jika mampu. Perdagangan rempah mengajar keluarganya menunggu apa sahaja.",
		],
	},
	"terengganu": {
		"en": [
			"On Terengganu's coast, fishermen read the sea like scripture. They tell of spirits who guard the waves — and of gasing spun on the sand at monsoon's end, in thanks for a season survived.",
			"Pak Awang Laut carves his tops from driftwood the ocean gives back. His turquoise gasing strikes like a breaking wave, then slips away like the undertow.",
			"The monsoon is coming. Show him your winds blow stronger.",
		],
		"ms": [
			"Di pesisir Terengganu, nelayan membaca laut seperti kitab. Mereka bercerita tentang penunggu yang menjaga ombak — dan gasing yang dipusing di pasir pada hujung monsun, tanda syukur musim yang selamat.",
			"Pak Awang Laut melarik gasingnya daripada kayu hanyut yang dipulangkan lautan. Gasing firusnya memangkah bagai ombak pecah, lalu menghilang bagai arus bawah.",
			"Monsun bakal tiba. Tunjukkan anginmu bertiup lebih kencang.",
		],
	},
	"sarawak": {
		"en": [
			"In the longhouses of Sarawak, the Iban wear their history in ink. The Bunga Terung — the eggplant flower tattoo — marks a youth's first bejalai, the great journey into the world.",
			"Tuai Unggat's forebears were warriors whose names crossed rivers; today he honours that strength in the ring instead. His top crackles like lightning over the Rajang, every strike a thunderclap.",
			"Every scar on his gasing is a story. Do not become the next one.",
		],
		"ms": [
			"Di rumah panjang Sarawak, kaum Iban memakai sejarah pada tinta. Bunga Terung — tatu bunga terung — menandakan bejalai pertama seorang pemuda, pengembaraan besar ke dunia luar.",
			"Nenek moyang Tuai Unggat pahlawan yang namanya menyeberangi sungai; kini beliau menyanjung kekuatan itu di gelanggang. Gasingnya berdetap bagai kilat di atas Rajang, setiap pangkah bagai guruh.",
			"Setiap calar pada gasingnya adalah kisah. Jangan jadi kisah seterusnya.",
		],
	},
	"sabah": {
		"en": [
			"Beneath Mount Kinabalu, the Kadazan-Dusun tell of Monsopiad, the great warrior who defended his village so fiercely that a house still bears his name and legend.",
			"Huguan Gimbang farms rice on the very slopes his ancestors defended. His gasing is heavy as the mountain and patient as the harvest — it does not chase; it endures, green as the terraces after rain.",
			"At Kaamatan, the harvest festival, no one has out-spun him in thirty years.",
		],
		"ms": [
			"Di bawah Gunung Kinabalu, kaum Kadazan-Dusun bercerita tentang Monsopiad, pahlawan agung yang mempertahankan kampungnya hingga sebuah rumah masih menyandang nama dan lagendanya.",
			"Huguan Gimbang menanam padi di lereng yang dipertahankan nenek moyangnya. Gasingnya berat seperti gunung dan sabar seperti musim menuai — ia tidak mengejar; ia bertahan, hijau bagai teres sawah selepas hujan.",
			"Pada Pesta Kaamatan, tiada siapa menewaskan pusingannya selama tiga puluh tahun.",
		],
	},
	"kl": {
		"en": [
			"Kuala Lumpur — where every road in Malaysia eventually leads. Beneath the towers, kampung kids and city kids — Malay, Chinese, Indian, Iban, Kadazan and more — spin their tops in the same concrete gelanggang.",
			"They say the Mahaguru studied under every master you have faced. His gasing carries all their colours at once — a spinning rainbow, like the flags on Merdeka morning.",
			"One nation. One ring. One last duel. Everything you have learned comes down to this.",
		],
		"ms": [
			"Kuala Lumpur — destinasi segala jalan di Malaysia. Di bawah menara, anak kampung dan anak kota — Melayu, Cina, India, Iban, Kadazan dan banyak lagi — memusing gasing di gelanggang konkrit yang sama.",
			"Kata orang, Mahaguru pernah berguru dengan setiap mahaguru yang telah kaulawan. Gasingnya membawa semua warna mereka serentak — pelangi berpusing, bagai bendera pagi Merdeka.",
			"Satu bangsa. Satu gelanggang. Satu duel terakhir. Segala yang kaupelajari tertumpu di sini.",
		],
	},
}

const MATERIAL_DEFS: Dictionary = {
	"merbau": {"label": "Kayu Merbau", "mass": 0.3, "balance": 0.0},
	"kemuning": {"label": "Kayu Kemuning", "mass": 0.0, "balance": 7.0},
	"besi": {"label": "Teras Besi", "mass": 0.5, "balance": 0.0},
}
const MAT_PRICES: Dictionary = {"merbau": 20, "kemuning": 25, "besi": 30}
# heritage lacquers from the palette: emas, sepang maroon (well clear of the foe crimson),
# pandan, nila indigo, tembaga copper, gading ivory
const ACCENT_CHOICES: Array[Color] = [
	HT.SONGKET_GOLD, HT.SEPANG, HT.PANDAN, HT.NILA, HT.COPPER, HT.CREAM_MUTED,
]
# The story campaign: 7 masters, one per state/culture. id doubles as the STYLE_DEFS key,
# mesh id (gasing_<id>.glb), CUTSCENES key, wayang puppet suffix, and ARENA_DEFS key.
const MASTERS: Array[Dictionary] = [
	{"id": "kelantan", "name": "Tok Wan Nik", "region_en": "Kelantan", "region_ms": "Kelantan",
		"shape": "uri", "mesh": "kelantan", "color": Color(1.0, 0.82, 0.30),
		"mass": 1.7, "spin_reserve": 82.0, "balance": 62.0,
		"wind_mean": 66.0, "wind_dev": 16.0, "aggressive": false, "coins": 40, "arena": "kelantan"},
	{"id": "penang", "name": "Kapitan Ong", "region_en": "Penang", "region_ms": "Pulau Pinang",
		"shape": "jantung", "mesh": "penang", "color": Color(1.0, 0.42, 0.15),
		"mass": 2.1, "spin_reserve": 72.0, "balance": 60.0,
		"wind_mean": 72.0, "wind_dev": 13.0, "aggressive": true, "coins": 55, "arena": "penang"},
	{"id": "melaka", "name": "Tuan Pillay", "region_en": "Melaka", "region_ms": "Melaka",
		"shape": "jantung", "mesh": "melaka", "color": Color(0.25, 0.45, 1.0),
		"mass": 1.6, "spin_reserve": 100.0, "balance": 74.0,
		"wind_mean": 76.0, "wind_dev": 11.0, "aggressive": false, "coins": 70, "arena": "melaka"},
	{"id": "terengganu", "name": "Pak Awang Laut", "region_en": "Terengganu", "region_ms": "Terengganu",
		"shape": "uri", "mesh": "terengganu", "color": Color(0.20, 0.85, 0.80),
		"mass": 2.3, "spin_reserve": 78.0, "balance": 66.0,
		"wind_mean": 80.0, "wind_dev": 9.0, "aggressive": true, "coins": 85, "arena": "terengganu"},
	{"id": "sarawak", "name": "Tuai Unggat", "region_en": "Sarawak", "region_ms": "Sarawak",
		"shape": "jantung", "mesh": "sarawak", "color": Color(0.75, 0.85, 1.0),
		"mass": 2.6, "spin_reserve": 74.0, "balance": 64.0,
		"wind_mean": 84.0, "wind_dev": 7.0, "aggressive": true, "coins": 100, "arena": "sarawak"},
	{"id": "sabah", "name": "Huguan Gimbang", "region_en": "Sabah", "region_ms": "Sabah",
		"shape": "jantung", "mesh": "sabah", "color": Color(0.45, 0.80, 0.35),
		"mass": 2.9, "spin_reserve": 80.0, "balance": 76.0,
		"wind_mean": 88.0, "wind_dev": 5.0, "aggressive": false, "coins": 120, "arena": "sabah"},
	{"id": "kl", "name": "Mahaguru Merdeka", "region_en": "Kuala Lumpur", "region_ms": "Kuala Lumpur",
		"shape": "uri", "mesh": "kl", "color": Color(0.85, 0.70, 1.0),
		"mass": 2.6, "spin_reserve": 92.0, "balance": 80.0,
		"wind_mean": 92.0, "wind_dev": 3.5, "aggressive": true, "coins": 160, "arena": "kl"},
]

const STRINGS: Dictionary = {
	"en": {
		"heritage": "A Malay heritage game — wind your top, strike your rival, rule the ring.",
		"prompt": "Press SPACE for single player",
		"bench": "WORKSHOP",
		"pick_info": "Pick three gasing. Drag to inspect, scroll to zoom, double-click to reset.",
		"level_xp": "Lv.%d · %d/%d XP",
		"level_max": "Lv.%d · MAX",
		"difficulty_normal": "Normal",
		"difficulty_hard": "Hard",
		"difficulty_master": "Master",
		"difficulty_tip": "Opponent difficulty",
		"loadout_tip": "Choose a slot, then browse to assign its gasing. Duplicate styles are allowed.",
		"selected_info": "%s selected.",
		"no_mat": "No %s — win duels to earn materials!",
		"forged": "%s forged onto %s!",
		"fight": "FIGHT!",
		"round_win": "YOU WIN!",
		"round_lose": "%s wins this duel...",
		"over_win": "CHAMPION OF THE GELANGGANG!",
		"over_lose": "DEFEATED...",
		"duels_won": "Duels won: %d / %d",
		"restart": "RESTART RUN",
		"or_space": "(or press SPACE)",
		"you": "You",
		"gauge_you": "YOU",
		"toast_topple": "%s TOPPLED!",
		"toast_ringout": "%s RING OUT!",
		"role_jantung": "Striker — knock rivals out",
		"role_uri": "Spinner — outlast rivals",
		"desc_merbau": "+0.3 mass",
		"desc_kemuning": "+7 balance",
		"desc_besi": "+0.5 mass, harder pangkah",
		"stat_mass": "Mass",
		"stat_spin": "Spin",
		"stat_balance": "Balance",
		"tip_stat_mass": "Mass — pangkah power.\nStrike force scales with (your mass ÷ theirs):\nheavy tops shove rivals far and barely budge when hit.",
		"tip_stat_spin": "Spin — your top's stamina.\nLaunch spin = wind quality × Spin, and a larger\nreserve also fades slower. Outlast the rival's top.",
		"tip_stat_balance": "Balance — steadiness as spin fades.\nWobble lean shrinks as Balance rises:\na balanced top staggers less and topples later.",
		"stat_legend": "Mass = strike power  ·  Spin = stamina  ·  Balance = steadiness  (hover a stat for details)",
		"meter": "WIND",
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
		"mp_code_label": "Lobby Code:",
		"join_code": "JOIN CODE",
		"share_code": "Share this code: %s",
		"steam_offline": "Steam not detected — Steam play unavailable.",
		"back": "BACK",
		"cancel": "CANCEL",
		"waiting_opponent": "WAITING FOR OPPONENT...",
		"connecting": "CONNECTING...",
		"lan_share_ip": "Friend joins with this IP: %s",
		"err_host_failed": "Could not host the match.",
		"err_join_failed": "Could not join — check the IP address.",
		"err_join_steam": "Could not join the Steam match (it may be full).",
		"mp_server_lost": "Connection to the host was lost.",
		"waiting": "Waiting for opponent...",
		"back_menu": "BACK TO MENU",
		"locked_hint": "Beat %s to unlock",
		"now_purchasable": "%s's gasing is now for sale in your workshop!",
		"locked_beat": "Defeat %s to unlock this purchase.",
		"locked_mp": "Locked — buy it in single player.",
		"bought": "%s bought — spin it well!",
		"need_coins": "Costs %d duit — you have %d.",
		"price_tag": "For sale — %d duit",
		"buy_prefix": "BUY: ",
		"mat_bought": "+1 %s bought.",
		"lacquer": "LACQUER",
		"next_opp": "NEXT OPPONENT",
		"duel_n": "Duel %d / %d",
		"wave_n": "Wave %d",
		"slot_assign": "Slot %d  ←  %s",
		"buy_mat": "BUY +1 · %d duit",
		"forge_gain": "Forge: %s",
		"forge_full": "%s · MAX",
		"continue": "CONTINUE",
		"round_of": "ROUND %d  ·  BEST OF 3",
		"stat_hits": "Hits",
		"stat_kos": "Knockouts",
		"stat_perfect": "Perfect launches",
		"coin_gain": "+%d duit",
		"masters_beaten": "Masters beaten",
		"run_coins": "+%d duit earned this run",
		"new_best": "NEW BEST!",
		"cut_continue": "Click / SPACE to continue",
		"cut_skip": "SKIP",
		"endless": "ENDLESS GELANGGANG",
		"endless_over": "Waves survived: %d",
		"endless_best_line": "Best: %d",
		"mats_saved": "Stored in your workshop.",
		"first_to_3": "First to 3 wins",
		"match_point": "MATCH POINT!",
		"match_win": "MATCH WON!",
		"match_lose": "%s takes the match...",
		"match_mats": "Materials this match:",
		"rematch": "REMATCH",
		"role_pakdin": "Steady spinner — calm and enduring",
		"role_cikros": "Swift striker — sharp pangkah",
		"role_tokgayong": "Heavy striker — crushing weight",
		"role_datuk": "The master's top — power and poise",
		"role_kelantan": "Golden heart — the old way",
		"role_penang": "Firecracker — swift pangkah",
		"role_melaka": "Trader's patience — endless spin",
		"role_terengganu": "Breaking wave — hit and slip",
		"role_sarawak": "Thunderclap — brutal strikes",
		"role_sabah": "The mountain — immovable",
		"role_kl": "All colours as one — the final master",
		"round_won": "ROUND WON!",
		"round_lost": "%s takes the round",
		"round_draw": "DRAW",
		"round_n": "ROUND %d",
		"time_up": "TIME!",
		"reason_ko": "Last one spinning",
		"reason_time_count": "Time — %d tops vs %d",
		"reason_time_spin": "Time — more spin %d%% vs %d%%",
		"reason_draw": "Draw — replay",
		"reason_forfeit": "A rival left the ring",
		"level_up": "LEVEL UP! %s Lv.%d",
		"continue_duel": "CONTINUE · Duel %d/%d",
		"howto": "HOW TO PLAY",
		"settings": "SETTINGS",
		"credits": "CREDITS",
		"howto_go": "GOT IT — FIGHT!",
		"progress_masters": "Masters defeated %d / %d",
		"progress_endless": "Endless best: wave %d",
		"did_you_know": "DID YOU KNOW?",
		"fact_1": "Gasing pangkah is a striking game: you throw your top to hit a rival's spinning top and knock it out.",
		"fact_2": "In gasing uri the longest spin wins — skilled players keep one spinning for an hour or more.",
		"fact_3": "Tops are carved from hardwoods such as merbau, kemuning and bakau, often ringed with metal for weight.",
		"fact_4": "Villages traditionally play gasing after the rice harvest, when the cleared fields host friendly contests.",
		"fact_5": "A perfectly balanced top 'sleeps': it spins so smoothly that it seems to stand still.",
		"fact_6": "Wayang kulit opens with the gunungan, the tree-of-life puppet — in Kelantan it is the pohon beringin.",
		"forge_max": "%s is already at its limit for that stat.",
		"buy_confirm": "Press again to buy %s for %d duit",
		"players_count": "PLAYERS %d / 4",
		"connected_wait": "CONNECTED — WAITING FOR HOST",
		"hint_steer": "WASD steer · click to push",
		"hint_dash": "SHIFT dash · hold E to rush — energy never refills",
		"hint_reserve": "Press %d, hold + release SPACE to launch a reserve!",
		"hud_duel": "Duel %d/%d · %s",
		"hud_wave": "Wave %d · %s",
		"hud_ffa": "FFA · first to %d",
		"hud_leading": "Leading: %s",
		"hud_even": "Dead even!",
		"hud_keycaps": "WASD|CLICK|SHIFT|E|SPACE|1 2 3|ESC",
		"hud_keys": "steer|push|dash|rush|jump|select|pause",
		# arena HUD / callouts / FFA lobby (squad card words split on "|")
		"call_launch": "LAUNCH!",
		"grade_snap": "CORD SNAPPED!",
		"grade_perfect": "PERFECT!",
		"grade_good": "GOOD",
		"grade_weak": "WEAK",
		"auto_launched": "Auto-launched",
		"reserve_auto_launched": "Reserve %d auto-launched",
		"deny_energy": "NO ENERGY",
		"deny_cooldown": "COOLDOWN",
		"hud_how": "Hold SPACE, release in gold",
		"hud_launch_in": "LAUNCH IN %d",
		"hud_aim_spin": "A/D aim · spin %d%%",
		"hud_launched": "LAUNCHED",
		"hud_waiting": "Waiting for rivals · %ds",
		"hud_reserve_n": "RESERVE %d",
		"hud_cancel_spin": "Esc cancels · spin %d%%",
		"prompt_grace": "No top spinning! Press %d + hold SPACE · auto in %ds",
		"prompt_reserve": "Reserve %d auto-launches in %ds · press %d + hold SPACE",
		"card_words": "SPIN|ENERGY|DASH|JUMP|RESERVE|OUT|Launches in %ds|Knocked out",
		"ffa_start": "START FFA",
		"ffa_players_n": "PLAYERS %d / 4",
		"ffa_wait_host": "Waiting for host to start",
		"ffa_ready": "Ready: %d / %d",
		"ffa_wait_all": "Waiting for all players",
		"ffa_players": "players",
	},
	"ms": {
		"heritage": "Permainan warisan Melayu — pusing gasingmu, pangkah lawan, jadi juara gelanggang.",
		"prompt": "Tekan SPACE untuk main sendirian",
		"bench": "BENGKEL GASING",
		"pick_info": "Pilih tiga gasing. Seret untuk lihat, skrol untuk zum, klik dua kali untuk set semula.",
		"level_xp": "Lv.%d · %d/%d XP",
		"level_max": "Lv.%d · MAKS",
		"difficulty_normal": "Biasa",
		"difficulty_hard": "Susah",
		"difficulty_master": "Mahaguru",
		"difficulty_tip": "Tahap kesukaran lawan",
		"loadout_tip": "Pilih slot, kemudian tukar gasing dengan anak panah. Boleh guna jenis yang sama.",
		"selected_info": "%s dipilih.",
		"no_mat": "Tiada %s — menang duel untuk dapat bahan!",
		"forged": "%s ditempa pada %s!",
		"fight": "MULA LAWAN!",
		"round_win": "KAMU MENANG!",
		"round_lose": "%s menang duel ini...",
		"over_win": "JUARA GELANGGANG!",
		"over_lose": "TEWAS...",
		"duels_won": "Duel dimenangi: %d / %d",
		"restart": "MULA SEMULA",
		"or_space": "(atau tekan SPACE)",
		"you": "Kamu",
		"gauge_you": "KAMU",
		"toast_topple": "%s TUMBANG!",
		"toast_ringout": "%s KELUAR GELANGGANG!",
		"role_jantung": "Pemangkah — tumbangkan lawan",
		"role_uri": "Pemusing — bertahan paling lama",
		"desc_merbau": "+0.3 jisim",
		"desc_kemuning": "+7 imbangan",
		"desc_besi": "+0.5 jisim, pangkah lebih kuat",
		"stat_mass": "Jisim",
		"stat_spin": "Pusingan",
		"stat_balance": "Imbangan",
		"tip_stat_mass": "Jisim — kuasa pangkah.\nDaya hentaman ikut (jisimmu ÷ jisim lawan):\ngasing berat menolak jauh dan tahan ditolak.",
		"tip_stat_spin": "Pusingan — stamina gasing.\nPusingan mula = mutu lilitan × Pusingan, dan simpanan\nbesar susut lebih perlahan. Bertahan lebih lama.",
		"tip_stat_balance": "Imbangan — kestabilan bila pusingan susut.\nGoyangan mengecil bila Imbangan tinggi:\nlambat terhuyung, lambat tumbang.",
		"stat_legend": "Jisim = kuasa pangkah  ·  Pusingan = stamina  ·  Imbangan = kestabilan  (tuding pada stat untuk butiran)",
		"meter": "PUSING",
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
		"mp_code_label": "Kod Lobi:",
		"join_code": "SERTAI KOD",
		"share_code": "Kongsi kod ini: %s",
		"steam_offline": "Steam tidak dikesan — mod Steam tidak tersedia.",
		"back": "KEMBALI",
		"cancel": "BATAL",
		"waiting_opponent": "MENUNGGU LAWAN...",
		"connecting": "MENYAMBUNG...",
		"lan_share_ip": "Rakan sertai dengan IP ini: %s",
		"err_host_failed": "Gagal membuka perlawanan.",
		"err_join_failed": "Gagal menyertai — semak alamat IP.",
		"err_join_steam": "Gagal menyertai perlawanan Steam (mungkin penuh).",
		"mp_server_lost": "Sambungan ke hos terputus.",
		"waiting": "Menunggu lawan...",
		"back_menu": "KEMBALI KE MENU",
		"locked_hint": "Kalahkan %s untuk buka",
		"now_purchasable": "Gasing %s kini boleh dibeli di bengkelmu!",
		"locked_beat": "Kalahkan %s untuk membuka pembelian ini.",
		"locked_mp": "Berkunci — beli dalam mod sendirian.",
		"bought": "%s dibeli — pusinglah elok-elok!",
		"need_coins": "Harga %d duit — kamu ada %d.",
		"price_tag": "Dijual — %d duit",
		"buy_prefix": "BELI: ",
		"mat_bought": "+1 %s dibeli.",
		"lacquer": "LAKUER",
		"next_opp": "LAWAN SETERUSNYA",
		"duel_n": "Duel %d / %d",
		"wave_n": "Gelombang %d",
		"slot_assign": "Slot %d  ←  %s",
		"buy_mat": "BELI +1 · %d duit",
		"forge_gain": "Tempa: %s",
		"forge_full": "%s · MAKS",
		"continue": "TERUSKAN",
		"round_of": "PUSINGAN %d  ·  TERBAIK DARI 3",
		"stat_hits": "Pangkah",
		"stat_kos": "Tumbang",
		"stat_perfect": "Lancar sempurna",
		"coin_gain": "+%d duit",
		"masters_beaten": "Mahaguru ditewaskan",
		"run_coins": "+%d duit diperoleh dalam larian ini",
		"new_best": "REKOD BAHARU!",
		"cut_continue": "Klik / SPACE untuk sambung",
		"cut_skip": "LANGKAU",
		"endless": "GELANGGANG TANPA HENTI",
		"endless_over": "Gelombang diharungi: %d",
		"endless_best_line": "Terbaik: %d",
		"mats_saved": "Disimpan dalam bengkel kamu.",
		"first_to_3": "Pertama capai 3 kemenangan",
		"match_point": "MATA PENENTU!",
		"match_win": "MENANG PERLAWANAN!",
		"match_lose": "%s memenangi perlawanan...",
		"match_mats": "Bahan perlawanan ini:",
		"rematch": "LAWAN SEMULA",
		"role_pakdin": "Pemusing seimbang — tenang dan tahan",
		"role_cikros": "Pemangkah pantas — pangkah tajam",
		"role_tokgayong": "Pemangkah berat — hentaman padu",
		"role_datuk": "Gasing mahaguru — kuasa dan imbangan",
		"role_kelantan": "Jantung emas — cara lama",
		"role_penang": "Mercun — pangkah pantas",
		"role_melaka": "Sabar pedagang — pusingan panjang",
		"role_terengganu": "Ombak pecah — pangkah dan undur",
		"role_sarawak": "Guruh — pangkah padu",
		"role_sabah": "Gunung — teguh tak goyah",
		"role_kl": "Segala warna bersatu — mahaguru terakhir",
		"round_won": "PUSINGAN DIMENANGI!",
		"round_lost": "%s menang pusingan ini",
		"round_draw": "SERI",
		"round_n": "PUSINGAN %d",
		"time_up": "MASA TAMAT!",
		"reason_ko": "Yang terakhir berpusing",
		"reason_time_count": "Masa tamat — %d gasing lawan %d",
		"reason_time_spin": "Masa tamat — pusingan lebih %d%% lawan %d%%",
		"reason_draw": "Seri — ulang semula",
		"reason_forfeit": "Seorang lawan meninggalkan gelanggang",
		"level_up": "NAIK TAHAP! %s Lv.%d",
		"continue_duel": "SAMBUNG · Duel %d/%d",
		"howto": "CARA BERMAIN",
		"settings": "TETAPAN",
		"credits": "KREDIT",
		"howto_go": "FAHAM — BERTARUNG!",
		"progress_masters": "Mahaguru ditewaskan %d / %d",
		"progress_endless": "Rekod tanpa henti: gelombang %d",
		"did_you_know": "TAHUKAH ANDA?",
		"fact_1": "Gasing pangkah ialah permainan memangkah: baling gasing anda untuk memukul dan menjatuhkan gasing lawan.",
		"fact_2": "Dalam gasing uri, pusingan paling lama menang — pemain mahir mampu memusingkannya sejam atau lebih.",
		"fact_3": "Gasing diukir daripada kayu keras seperti merbau, kemuning dan bakau, selalunya berlilit besi supaya berat.",
		"fact_4": "Secara tradisi, gasing dimainkan selepas musim menuai padi, apabila sawah lapang menjadi gelanggang.",
		"fact_5": "Gasing yang seimbang sempurna seolah-olah 'tidur': berpusing begitu tenang hingga nampak tidak bergerak.",
		"fact_6": "Wayang kulit dibuka dengan gunungan, patung pohon hayat — di Kelantan ia dipanggil pohon beringin.",
		"forge_max": "%s sudah mencapai had untuk stat itu.",
		"buy_confirm": "Tekan sekali lagi untuk beli %s dengan %d duit",
		"players_count": "PEMAIN %d / 4",
		"connected_wait": "DISAMBUNG — MENUNGGU HOS",
		"hint_steer": "WASD kemudi · klik untuk tolak",
		"hint_dash": "SHIFT pecut · tahan E untuk meluru — tenaga tidak diisi semula",
		"hint_reserve": "Tekan %d, tahan + lepas SPACE untuk melancar simpanan!",
		"hud_duel": "Duel %d/%d · %s",
		"hud_wave": "Gelombang %d · %s",
		"hud_ffa": "FFA · sasaran %d menang",
		"hud_leading": "Mendahului: %s",
		"hud_even": "Seri!",
		"hud_keycaps": "WASD|KLIK|SHIFT|E|SPACE|1 2 3|ESC",
		"hud_keys": "kemudi|tolak|pecut|meluru|lompat|pilih|jeda",
		# arena HUD / callouts / FFA lobby (squad card words split on "|")
		"call_launch": "LEPAS!",
		"grade_snap": "TALI PUTUS!",
		"grade_perfect": "SEMPURNA!",
		"grade_good": "BAGUS",
		"grade_weak": "LEMAH",
		"auto_launched": "Dilontar automatik",
		"reserve_auto_launched": "Simpanan %d dilontar automatik",
		"deny_energy": "TIADA TENAGA",
		"deny_cooldown": "BERTENANG",
		"hud_how": "Tahan SPACE, lepas di emas",
		"hud_launch_in": "LONTAR DALAM %d",
		"hud_aim_spin": "A/D halakan · pusingan %d%%",
		"hud_launched": "DILONTAR",
		"hud_waiting": "Menunggu lawan · %ds",
		"hud_reserve_n": "SIMPANAN %d",
		"hud_cancel_spin": "Esc batal · pusingan %d%%",
		"prompt_grace": "Tiada gasing! Tekan %d + tahan SPACE · auto %ds",
		"prompt_reserve": "Simpanan %d auto dalam %ds · tekan %d, tahan SPACE",
		"card_words": "PUSING|TENAGA|PECUT|LOMPAT|SIMPANAN|TUMBANG|Dilontar dalam %ds|Tersingkir",
		"ffa_start": "MULA FFA",
		"ffa_players_n": "PEMAIN %d / 4",
		"ffa_wait_host": "Menunggu host memulakan game",
		"ffa_ready": "Sedia: %d / %d",
		"ffa_wait_all": "Menunggu semua pemain",
		"ffa_players": "pemain",
	},
}

var lang: String = "en"
var state: State = State.READY
# persistent workshop state (saved to SAVE_PATH; loaded once in _ready)
var player_shapes: Dictionary = {}
var materials_owned: Dictionary = {}
var selected_shape: String = "jantung"
var loadout: Array[String] = ["jantung", "uri", "jantung"]
var loadout_slot: int = 0
var difficulty: int = 0 # Normal / Hard / Master
var style_xp: Dictionary = {}
var unlocked_styles: Array[String] = []
var coins: int = 0
var defeated_masters: Array[String] = [] # master ids beaten in the campaign (gates shop purchases)
var style_accents: Dictionary = {} # style_id -> Color, player-chosen lacquer trim (SP only)
var endless_best: int = 0
var endless_mode: bool = false
var workshop_preview: Node3D = null
var _inspect_dragging: bool = false
var _inspect_yaw: float = 0.0
var _inspect_pitch: float = 0.0
var _inspect_zoom: float = 2.8
var _preview_tween: Tween = null
var duel_index: int = 0
var run_won: bool = false
var arena: Node = null
var player_top: Gasing = null
var foe_top: Gasing = null
var _marker_tween: Tween = null
var _sfx_pool: Array[AudioStreamPlayer] = []
var _sfx_index: int = 0
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()

var ready_panel: Control = null
var craft_panel: Control = null
var round_panel: Control = null
var over_panel: Control = null
var hud: Control = null
var wind_meter: WindMeter = null
var wind_hint: Control = null # wind card: WIND countdown + how to launch (bottom-left)
var battle_hint: Control = null # key-cap controls strip (bottom centre)
var player_gauge: FightBar = null
var foe_gauge: FightBar = null
var duel_label: Label = null
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
var craft_index: int = 0 # roster position browsed in the fighter-select carousel (transient)
var craft_prev_button: Button = null
var craft_next_button: Button = null
var craft_name_label: Label = null
var craft_counter_label: Label = null
var craft_status_label: Label = null
var craft_level_label: Label = null
var craft_loadout_buttons: Array[Button] = []
var craft_difficulty: Array[Button] = [] # Normal / Hard / Master plaque toggles
var craft_sheet: Control = null
var craft_header: Control = null
var craft_stat_rows: Array = [] # 3 dicts from _mk_stat_row: mass, spin, balance
var craft_forge_box: Control = null
var material_buttons: Dictionary = {}
var material_buy_buttons: Dictionary = {}
var accent_row: Control = null # lacquer palette card beside the preview
var accent_label: Label = null
var cutscene_panel: Control = null
var cut_puppet: TextureRect = null
var cut_name_label: Label = null
var cut_text: Label = null
var cut_hint: Label = null
var cut_skip_button: Button = null
var _cut_pars: Array = []
var _cut_idx: int = 0
var _cut_tween: Tween = null
var _puppet_tween: Tween = null
var _env: Environment = null
var _sky_mat: ProceduralSkyMaterial = null
var _sun: DirectionalLight3D = null
var _lanterns: Array[OmniLight3D] = []
var _default_extras: Node3D = null
var _arena_node: Node3D = null
var current_arena: String = ""
var lang_buttons: Dictionary = {}

var menu_screen: MenuScreen = MenuScreen.TITLE
var mp_panel: Control = null
var wait_panel: Control = null
var _all_panels: Array[Control] = []
var menu_notice: Label = null
var _notice_tween: Tween = null
var ready_title: Label = null
var menu_top: Gasing = null
var sp_button: Button = null
var endless_button: Button = null
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
var join_code_edit: LineEdit = null
var join_code_button: Button = null
var mp_code_label: Label = null
var steam_offline_label: Label = null
var mp_back_button: Button = null
var wait_title: Label = null
var wait_info: Label = null
var invite_button: Button = null
var wait_cancel_button: Button = null
var over_menu_button: Button = null
var craft_back_button: Button = null

var net_active: bool = false
var net_ended: bool = false
var net_opp_name: String = ""
var net_ready_sent: bool = false
var net_my_wins: int = 0
var net_opp_wins: int = 0
var net_rematch_sent: bool = false
var net_bonus_text: String = "" # match-bonus line cached for the match-over screen
var net_match_mats: Dictionary = {} # per-match material tally for the match-over screen

var _netbot: bool = false # debug autopilot for LAN testing: run with `-- netbot-host` or `-- netbot-join`
var _test_mode: bool = false

var menus: Node = null # scripts/menus.gd: pause / settings / how-to / credits overlay
var campaign_index: int = 0 # saved campaign progress (SP story); endless never touches it
var sp_round: int = 0 # round number inside the current best-of-3 SP duel
var _seen_cutscenes: Dictionary = {} # master id -> true; a cutscene plays once per session
var _hints_shown: Dictionary = {} # hint key -> true; one-shot per session
var _pending_buy: String = "" # style id or "mat:<id>" awaiting its confirming second press
var _last_level_ups: Array = [] # [{style, level}] from the latest _award_style_xp
var _last_xp_gain: int = 0
var _action_streams: Dictionary = {} # ACTION_SFX kind -> AudioStream (new file or Kenney fallback)
var _rush_player: AudioStreamPlayer = null # looping whirr while the controlled top rushes
var _bursts: Array[CPUParticles3D] = [] # $HitBurst + duplicates, used round-robin
var _burst_index: int = 0
var _trauma: float = 0.0 # camera shake energy; offsets scale with trauma²
var _cam_fov: float = 55.0
var _fov_tween: Tween = null
var _warp_token: int = 0
var _warp_until: int = 0 # real msec the active time warp ends
const TOAST_BANNER_FLOOR: float = 282.0 # toast centre y whose 70 px rise stays under the banner band (y 122-192)
var _pangkah_next: int = 0 # real msec; PANGKAH! toast + hit-stop cooldown
var _grind_next: int = 0 # real msec; rush-contact effect rate limit
var _app_unfocused: bool = false # alt-tabbed away; the next WIND opens the pause
var _banner_box: Control = null
var _join_token: int = 0

@onready var camera: Camera3D = $Camera3D
@onready var aim_arrow: Node3D = $AimArrow
@onready var burst: CPUParticles3D = $HitBurst
@onready var click_marker: MeshInstance3D = $ClickMarker
@onready var ui: CanvasLayer = $UI

# ---- shell state
var _ui_theme: Theme = null # heritage theme; the UI CanvasLayer breaks theme inheritance, so each top-level control gets it
var _title_shift: float = 0.0 # eased camera h_offset that frames the ring beside the title menu
var howto_button: Button = null
var settings_button: Button = null
var credits_button: Button = null
var ready_gunungan: TextureRect = null # swaying wayang shadow behind the title
var ready_fact_head: Label = null
var ready_progress_pips: ScorePips = null
var ready_progress: Label = null
var _fact_idx: int = 0
var _music: Array[AudioStreamPlayer] = [] # two players crossfading on the Music bus
var _music_idx: int = 0 # the player carrying the current track
var _music_key: String = "" # track now playing ("" = silence)
var _music_bed: String = "" # loop the current state asked for; a stinger falls back to it
var _music_streams: Dictionary = {} # key -> AudioStream (null when the file is missing)
var _music_tween: Tween = null
var _curtain_root: Control = null
var _curtain_sweep: Control = null
var _curtain_puppet: TextureRect = null
var _curtain_tween: Tween = null
var _between_rounds: bool = false # MP loadout between rounds: no wipe, the battle bed plays on


func _ready() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	_test_mode = "--test-mode" in args
	_netbot = "netbot-host" in args or "netbot-join" in args
	_rng.randomize()
	get_window().title = "Gasing Pangkah" # config/name stays "gasing": renaming it would move user:// (the save)
	var body_font: Font = load("res://common/fonts/body.ttf") as Font if ResourceLoader.exists("res://common/fonts/body.ttf") else null
	_ui_theme = HT.build(body_font)
	get_tree().root.theme = _ui_theme # tooltips and popups hang off the root window
	ui.child_entered_tree.connect(_theme_ui_child)
	_build_sfx_pool()
	for kind: String in ACTION_SFX:
		var entry: Array = ACTION_SFX[kind]
		var stream: AudioStream = _load_audio("res://assets/audio/sfx/" + String(entry[0])) if String(entry[0]) != "" else null
		_action_streams[kind] = stream if stream != null else entry[1]
	# rush is a seamless loop sample, not a one-shot: its own player, polled in _process
	var rush: AudioStream = (_action_streams["rush"] as AudioStream).duplicate()
	rush.set("loop", true)
	_rush_player = AudioStreamPlayer.new()
	_rush_player.stream = rush
	_rush_player.volume_db = float(ACTION_SFX["rush"][2])
	if AudioServer.get_bus_index("SFX") >= 0:
		_rush_player.bus = "SFX"
	add_child(_rush_player)
	_cam_fov = camera.fov
	aim_arrow.visible = false
	_polish_visuals()
	_configure_burst()
	_build_ui()
	arena = ARENA_SCRIPT.new()
	arena.name = "Arena"
	arena.game = self
	add_child(arena)
	arena.build_ui()
	Online.joined_lobby.connect(_on_mp_joined_lobby)
	Online.player_connected.connect(_on_mp_player_connected)
	Online.player_disconnected.connect(_on_mp_player_disconnected)
	Online.server_disconnected.connect(_on_mp_server_disconnected)
	Online.connection_failed.connect(_on_mp_connection_failed)
	Online.lobby_join_response.connect(_on_mp_steam_join_response)
	_load_workshop()
	_reset_run()
	_apply_language()
	menus = MENUS_SCRIPT.new()
	menus.name = "Menus"
	menus.game = self
	add_child(menus)
	menus.build()
	menus.load_settings()
	_enter_state(State.READY)
	_curtain() # the show opens like a wayang: the gunungan sweeps off the kelir
	_netbot_init()


func _theme_ui_child(n: Node) -> void:
	if n is Control:
		(n as Control).theme = _ui_theme


func _polish_visuals() -> void:
	# One-time atmosphere rig: SSAO/SSIL, glow, AgX, fill light, floor/earth relief,
	# lantern lights, palms. Per-arena mood (sky/fog/sun/lantern colors) comes from
	# ARENA_DEFS via _apply_arena at the end and on every arena swap.
	var we: WorldEnvironment = get_node_or_null("WorldEnvironment") as WorldEnvironment
	if we != null and we.environment != null:
		_env = we.environment
		_sky_mat = ProceduralSkyMaterial.new()
		_sky_mat.sky_curve = 0.15
		_sky_mat.ground_bottom_color = Color(0.24, 0.15, 0.09)
		_sky_mat.sun_angle_max = 25.0
		var sky: Sky = Sky.new()
		sky.sky_material = _sky_mat
		_env.background_mode = Environment.BG_SKY
		_env.sky = sky
		_env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
		_env.ambient_light_sky_contribution = 1.0
		_env.ambient_light_energy = 0.9
		_env.ssao_enabled = true
		_env.ssao_radius = 0.7
		_env.ssao_intensity = 3.5
		_env.ssao_power = 1.6
		_env.ssil_enabled = true
		_env.ssil_intensity = 0.6
		_env.fog_enabled = true
		_env.fog_sky_affect = 0.2
		_env.glow_enabled = true
		_env.glow_intensity = 0.3
		_env.glow_bloom = 0.1
		_env.glow_hdr_threshold = 1.2
		_env.tonemap_mode = Environment.TONE_MAPPER_AGX
		_env.tonemap_exposure = 1.05

	_sun = get_node_or_null("Sun") as DirectionalLight3D
	if _sun != null:
		_sun.light_angular_distance = 2.0 # soft shadow penumbra
		_sun.shadow_enabled = true
		_sun.shadow_blur = 1.5

	# Cool fill from the opposite side so low-poly forms read as 3D, not flat silhouettes.
	var fill: DirectionalLight3D = DirectionalLight3D.new()
	fill.name = "FillLight"
	fill.light_color = Color(0.55, 0.66, 0.90)
	fill.light_energy = 0.35
	fill.shadow_enabled = false
	fill.rotation_degrees = Vector3(-25.0, 150.0, 0.0)
	add_child(fill)

	# Dirt surface relief on the surrounding earth + tan arena floor (procedural, no texture files).
	var dirt_normal: NoiseTexture2D = _make_noise_normal(0.06, 2.5)
	var earth_mat: StandardMaterial3D = StandardMaterial3D.new()
	earth_mat.albedo_color = Color(0.38, 0.26, 0.13)
	earth_mat.roughness = 1.0
	earth_mat.normal_enabled = true
	earth_mat.normal_texture = dirt_normal
	earth_mat.normal_scale = 1.2
	earth_mat.uv1_scale = Vector3(14.0, 14.0, 14.0)
	for p: String in ["Environment3D/EnvEarth", "Environment3D/EnvEarth2"]:
		var n: MeshInstance3D = get_node_or_null(p) as MeshInstance3D
		if n != null:
			n.set_surface_override_material(0, earth_mat)
	var floor_node: MeshInstance3D = get_node_or_null("Floor") as MeshInstance3D
	if floor_node != null:
		var floor_mat: StandardMaterial3D = StandardMaterial3D.new()
		floor_mat.albedo_color = Color(0.6, 0.42, 0.23) # lighter than the tops' dark wood (0.42, 0.24, 0.11)
		floor_mat.roughness = 0.92
		floor_mat.normal_enabled = true
		floor_mat.normal_texture = dirt_normal
		floor_mat.normal_scale = 0.9
		floor_mat.uv1_scale = Vector3(9.0, 9.0, 9.0)
		floor_node.set_surface_override_material(0, floor_mat)

	# Painted dish markings: songket medallion at the centre + a darker danger band at the rope
	# (r 3.6-4.2). A world-space plane just above the floor, never under a top's Visual.
	var mark_shader: Shader = load("res://assets/floor_markings.gdshader") as Shader
	if mark_shader != null:
		var mark_mat: ShaderMaterial = ShaderMaterial.new()
		mark_mat.shader = mark_shader
		mark_mat.render_priority = -1 # drawn before top shadows and sparks
		mark_mat.set_shader_parameter("band_color", Color(HT.WOOD_EDGE, 0.6))
		mark_mat.set_shader_parameter("inlay_color", Color(HT.SONGKET_GOLD, 0.5))
		var mark_plane: PlaneMesh = PlaneMesh.new()
		mark_plane.size = Vector2(8.4, 8.4)
		mark_plane.material = mark_mat
		var marks: MeshInstance3D = MeshInstance3D.new()
		marks.name = "FloorMarkings"
		marks.mesh = mark_plane
		marks.position.y = 0.006
		marks.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(marks)

	# Warm point-lights around the ring — local pools of firelight near the lanterns.
	var lantern_count: int = 8
	for i: int in lantern_count:
		var ang: float = TAU * float(i) / float(lantern_count)
		var om: OmniLight3D = OmniLight3D.new()
		om.name = "LanternLight%d" % i
		om.omni_range = 3.2
		om.omni_attenuation = 1.5
		om.shadow_enabled = false
		om.position = Vector3(cos(ang) * 4.25, 0.85, sin(ang) * 4.25)
		add_child(om)
		_lanterns.append(om)

	# The Rim torus is a rope boundary, not a neon light — drop the emissive glow.
	var rim: MeshInstance3D = get_node_or_null("Rim") as MeshInstance3D
	if rim != null:
		var rim_mat: StandardMaterial3D = StandardMaterial3D.new()
		rim_mat.albedo_color = Color(0.34, 0.22, 0.12)
		rim_mat.roughness = 0.8
		rim.set_surface_override_material(0, rim_mat)

	# Swap the flat palm cutouts for detailed palm models at the same spots.
	for pp: String in ["Environment3D/EnvPalms", "Environment3D/EnvPalms2"]:
		var pn: Node3D = get_node_or_null(pp) as Node3D
		if pn != null: pn.visible = false
	_default_extras = Node3D.new() # kampung-only props, hidden together with Environment3D on arena swaps
	_default_extras.name = "DefaultExtras"
	add_child(_default_extras)
	var palm_scene: PackedScene = load("res://assets/gasing_palm.glb")
	if palm_scene != null:
		# [Godot pos (Blender base x,-y), target height, yaw] — heights/positions from the original EnvPalms clusters.
		var palm_spots: Array = [
			[Vector3(6.51, 0.0, -5.40), 3.62, 0.4],
			[Vector3(2.85, 0.0, -10.54), 3.24, 1.7],
			[Vector3(-3.08, 0.0, -8.51), 3.81, 2.9],
			[Vector3(-7.36, 0.0, -4.27), 3.14, 4.1],
			[Vector3(-9.52, 0.0, 4.31), 3.42, 5.2],
			[Vector3(7.28, 0.0, 6.17), 3.24, 0.9],
		]
		for spot: Array in palm_spots:
			var palm: Node3D = palm_scene.instantiate() as Node3D
			_default_extras.add_child(palm)
			palm.position = spot[0]
			var s: float = float(spot[1]) / 3.4 # authored palm height
			palm.scale = Vector3(s, s, s)
			palm.rotation.y = float(spot[2])
	_apply_arena("kampung")


func _apply_arena(id: String) -> void:
	if id == current_arena:
		return
	var def: Dictionary = ARENA_DEFS.get(id, ARENA_DEFS["kampung"])
	current_arena = id
	if _sky_mat != null:
		_sky_mat.sky_top_color = def.sky_top
		_sky_mat.sky_horizon_color = def.sky_horizon
		_sky_mat.ground_horizon_color = (def.sky_horizon as Color).darkened(0.35)
	if _env != null:
		_env.fog_light_color = def.fog
		_env.fog_density = def.fog_density
		_env.tonemap_exposure = float(def.get("exposure", 1.05))
		_env.ambient_light_energy = float(def.get("ambient", 0.9))
	if _sun != null:
		_sun.light_color = def.sun_color
		_sun.light_energy = def.sun_energy
	for l: OmniLight3D in _lanterns:
		l.light_color = def.lantern
		l.light_energy = float(def.get("lantern_energy", 2.2))
	if _arena_node != null:
		_arena_node.queue_free()
		_arena_node = null
	var env_path: String = String(def.get("env", ""))
	var use_default: bool = env_path.is_empty()
	if not use_default:
		if ResourceLoader.exists(env_path):
			_arena_node = (load(env_path) as PackedScene).instantiate() as Node3D
			add_child(_arena_node)
			# glossy water (paddy, sea, fountain) mirrors the sun into a glare streak and the pale
			# sky into a washed-out sheet at this camera angle: matte, deepen and de-mirror it.
			# Edits the cached imported material once (roughness then exceeds the 0.4 test).
			for mi: Node in _arena_node.find_children("*", "MeshInstance3D", true, false):
				var mesh: Mesh = (mi as MeshInstance3D).mesh
				for s: int in (mesh.get_surface_count() if mesh != null else 0):
					var sm: StandardMaterial3D = mesh.surface_get_material(s) as StandardMaterial3D
					if sm != null and sm.metallic < 0.1 and sm.roughness < 0.4:
						sm.roughness = 0.5
						sm.metallic_specular = 0.15
						sm.albedo_color = sm.albedo_color.darkened(0.3)
		else:
			use_default = true # arena GLB not produced yet — the mood re-theme still lands
	var env3d: Node3D = get_node_or_null("Environment3D") as Node3D
	if env3d != null:
		env3d.visible = use_default
	if _default_extras != null:
		_default_extras.visible = use_default


func _make_noise_normal(freq: float, strength: float) -> NoiseTexture2D:
	var n: FastNoiseLite = FastNoiseLite.new()
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = freq
	var tex: NoiseTexture2D = NoiseTexture2D.new()
	tex.noise = n
	tex.seamless = true
	tex.as_normal_map = true
	tex.bump_strength = strength
	return tex


func _t(key: String) -> String:
	# a key missing in the current language falls back to English, then to the key itself
	return STRINGS.get(lang, {}).get(key, STRINGS["en"].get(key, key))


# ---------------------------------------------------------------- state flow

func _enter_state(next: State) -> void:
	var prev: State = state
	state = next
	_pending_buy = ""
	# MP rounds run ROUND_OVER -> CRAFT (loadout) -> WIND: that between-round loadout keeps
	# the battle bed and skips the wipe, so a match wipes only on its way in and out
	if next != State.WIND:
		_between_rounds = net_active and next == State.CRAFT and prev == State.ROUND_OVER
	var carry: bool = _between_rounds and (next == State.CRAFT or next == State.WIND)
	# major screen changes get the gunungan wipe: a pure overlay, nothing waits on it
	# (not into or out of CUTSCENE: the kelir there opens and closes with its own gunungan)
	var major: bool = not carry and (next in [State.READY, State.CRAFT, State.OVER] \
			or (next == State.WIND and prev == State.CRAFT))
	if major and next != prev:
		_curtain()
	if STATE_MUSIC.has(next) and not carry:
		_play_music(STATE_MUSIC[next]) # an already-playing bed carries on untouched
	# presentation resets: no slow-mo, punch or shake leaks into the next screen
	_warp_token += 1
	_warp_until = 0
	Engine.time_scale = 1.0
	if _fov_tween != null and _fov_tween.is_valid():
		_fov_tween.kill()
	camera.fov = _cam_fov
	_trauma = 0.0
	if next != State.WIND and next != State.BATTLE and is_instance_valid(_banner_box):
		_banner_box.queue_free() # battle callouts never outlive the battle
	if (next == State.READY or next == State.OVER) and menus != null:
		menus.close_pause() # no match left for the (MP, unpaused) overlay to cover
	if next != State.CRAFT:
		_clear_preview()
	if next != State.READY:
		if is_instance_valid(menu_top):
			menu_top.queue_free()
		menu_top = null
		camera.h_offset = 0.0
		camera.v_offset = 0.0 # _process owns the offsets (trauma shake / title drift)
	match next:
		State.READY:
			_clear_tops()
			_set_hud_visible(false)
			_apply_arena("kampung") # menu and every MP match run in the default arena
			aim_arrow.visible = false # leaving mid-wind (pause MAIN MENU / MP teardown) must not strand it
			_refresh_sp_button()
			_show_menu_screen(MenuScreen.TITLE)
			_update_menu_top()
			if ready_title != null:
				# the name and its gunungan pop from their centres (pivots set in _build_ready_panel)
				ready_title.scale = Vector2(1.14, 1.14)
				ready_title.modulate.a = 0.0
				ready_gunungan.scale = Vector2(0.82, 0.82)
				var title_tw: Tween = create_tween().set_parallel(true)
				title_tw.tween_property(ready_title, "scale", Vector2.ONE, 0.5).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
				title_tw.tween_property(ready_title, "modulate:a", 1.0, 0.35)
				title_tw.tween_property(ready_gunungan, "scale", Vector2.ONE, 0.7).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		State.CRAFT:
			_clear_tops()
			_set_hud_visible(false)
			net_ready_sent = false
			craft_index = maxi(0, STYLE_DEFS.keys().find(selected_shape))
			craft_opp_status.text = ""
			craft_info.text = _t("pick_info")
			_refresh_craft()
			_update_workshop_preview()
			_show_panel(craft_panel)
		State.CUTSCENE:
			_clear_tops()
			_set_hud_visible(false)
			_cutscene_begin(mini(duel_index, MASTERS.size() - 1))
			_show_panel(cutscene_panel)
		State.WIND:
			_show_panel(null)
			_set_hud_visible(true)
			arena.begin_wind()
			# focus lost on a round panel: its timer carried on into this round, so pause now
			if _app_unfocused and menus != null and not net_active and not _test_mode and not _netbot:
				menus.open_pause.call_deferred()
			if not net_active and not endless_mode:
				sp_round += 1
				if sp_round >= 2 and int(arena.scores.get(1, 0)) == 1 and int(arena.scores.get(2, 0)) == 1:
					_banner(_t("match_point"), DANGER, "%s  ·  %s" % [_t("round_n") % sp_round, _score_line()]) # the decider
				elif sp_round >= 2:
					_banner(_t("round_n") % sp_round, PLAYER_COLOR, _score_line())
		State.LAUNCH:
			pass # launches are per slot now
		State.BATTLE:
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
	# explicit key checks (never ui_accept for FIGHT): buttons stay FOCUS_NONE
	var key: InputEventKey = event as InputEventKey
	var key_down: bool = key != null and key.pressed and not key.echo
	if key_down and key.keycode == KEY_F11:
		get_viewport().set_input_as_handled()
		if menus != null:
			menus.toggle_fullscreen()
		return
	if event.is_action_pressed("ui_cancel") or (key_down and key.keycode == KEY_ESCAPE):
		if _on_escape():
			get_viewport().set_input_as_handled()
			return
	if key_down and (key.keycode == KEY_ENTER or key.keycode == KEY_KP_ENTER) and state == State.CRAFT:
		get_viewport().set_input_as_handled()
		if not fight_button.disabled:
			_on_fight_pressed()
		return
	match state:
		State.READY:
			if menu_screen == MenuScreen.TITLE and event.is_action_pressed("ui_accept"):
				get_viewport().set_input_as_handled()
				_on_single_player_pressed()
		State.CRAFT:
			if event is InputEventMouseButton:
				var click: InputEventMouseButton = event
				if click.button_index == MOUSE_BUTTON_LEFT and not click.pressed:
					_inspect_dragging = false
				elif click.pressed and _preview_contains(click.position):
					if click.button_index == MOUSE_BUTTON_LEFT:
						_inspect_dragging = not click.double_click
						if click.double_click:
							_inspect_yaw = 0.0
							_inspect_pitch = 0.0
							_inspect_zoom = 2.8
						_apply_inspection()
						get_viewport().set_input_as_handled()
					elif click.button_index == MOUSE_BUTTON_WHEEL_UP or click.button_index == MOUSE_BUTTON_WHEEL_DOWN:
						_inspect_zoom = clampf(_inspect_zoom + (0.2 if click.button_index == MOUSE_BUTTON_WHEEL_UP else -0.2), 1.8, 3.6)
						_apply_inspection()
						get_viewport().set_input_as_handled()
			elif event is InputEventMouseMotion and _inspect_dragging:
				var motion: InputEventMouseMotion = event
				_inspect_dragging = (motion.button_mask & MOUSE_BUTTON_MASK_LEFT) != 0
				if _inspect_dragging:
					_inspect_yaw = wrapf(_inspect_yaw + motion.relative.x * 0.012, -PI, PI)
					_inspect_pitch = clampf(_inspect_pitch + motion.relative.y * 0.012, -1.1, 1.1)
					_apply_inspection()
					get_viewport().set_input_as_handled()
			elif event.is_action_pressed("ui_left"):
				get_viewport().set_input_as_handled()
				_craft_cycle(-1)
			elif event.is_action_pressed("ui_right"):
				get_viewport().set_input_as_handled()
				_craft_cycle(1)
		State.CUTSCENE:
			if event.is_action_pressed("ui_accept"):
				get_viewport().set_input_as_handled()
				_cutscene_advance()
		State.BATTLE, State.WIND:
			arena.handle_input(event)
		State.OVER:
			if event.is_action_pressed("ui_accept"):
				_on_restart_pressed() # SP restart / MP rematch / disconnect teardown


func _on_escape() -> bool:
	# Esc = back everywhere; returns false when the event should fall through
	# (a live charge is cancelled by arena.handle_input)
	match state:
		State.WIND, State.BATTLE:
			if arena.charge_active:
				return false
			if menus != null:
				menus.open_pause()
		State.CRAFT:
			if net_active and menus != null:
				menus.open_pause() # MP loadout between rounds: leaving needs the LEAVE MATCH confirm
			else:
				_leave_to_title()
		State.CUTSCENE:
			_cutscene_finish()
		State.READY:
			if menu_screen == MenuScreen.MP:
				_on_mp_back_pressed()
			elif menu_screen == MenuScreen.WAIT and not wait_cancel_button.disabled:
				_on_mp_cancel_pressed()
			else:
				return false
		_:
			return false
	return true


func _notification(what: int) -> void:
	# alt-tab in a solo fight pauses it (or the next round's WIND, if it was lost on a panel)
	if what == NOTIFICATION_APPLICATION_FOCUS_IN or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		_app_unfocused = what == NOTIFICATION_APPLICATION_FOCUS_OUT
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and menus != null and not net_active and not _test_mode and not _netbot \
			and (state == State.WIND or state == State.BATTLE):
		menus.open_pause()


func _process(delta: float) -> void:
	# trauma shake: offsets scale with trauma², decaying 1.8/s; on the title the
	# slow drift keeps the screen alive
	_trauma = maxf(_trauma - 1.8 * delta, 0.0)
	var t: float = Time.get_ticks_msec() * 0.001
	var shake: float = _trauma * _trauma * 0.25
	var h: float = shake * 0.5 * (sin(t * 47.0) + sin(t * 29.0 + 1.3))
	var v: float = shake * 0.5 * (sin(t * 53.0 + 0.7) + sin(t * 31.0 + 2.1))
	if state == State.READY:
		h += sin(t * 0.25) * 0.25
		v += cos(t * 0.2) * 0.1
	# the title frames the ring beside its menu column; every other screen eases back to centre
	var framing: float = TITLE_CAM_SHIFT if state == State.READY and menu_screen == MenuScreen.TITLE else 0.0
	_title_shift = lerpf(_title_shift, framing, 1.0 - exp(-4.0 * delta))
	camera.h_offset = h + _title_shift
	camera.v_offset = v
	# rush whirr loops exactly while the controlled top rushes (paused with the tree)
	var rushing: bool = state == State.BATTLE and is_instance_valid(player_top) and player_top.rushing
	if rushing != _rush_player.playing:
		if rushing:
			_rush_player.play()
		else:
			_rush_player.stop()


func _update_menu_top() -> void:
	# the showpiece spinning (and precessing) in the ring beside the title — the player's
	# current top (rainbow if it's the KL arcana). World-placed: the title camera glides.
	if is_instance_valid(menu_top):
		menu_top.queue_free()
	menu_top = null
	if state != State.READY:
		return
	var g: Gasing = GASING_SCENE.instantiate() as Gasing
	add_child(g)
	g.setup("", String(STYLE_DEFS[selected_shape].shape), _style_battle_stats(selected_shape), _style_accent(selected_shape))
	g.set_showcase(true)
	g.position = Vector3.ZERO # on the ring's centre medallion
	g.scale = Vector3(0.01, 0.01, 0.01)
	var tw: Tween = create_tween()
	tw.tween_property(g, "scale", Vector3(1.8, 1.8, 1.8), 0.5).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	menu_top = g


# ---- screens state (workshop, cutscene, result panels)
var _turn_tween: Tween = null # slow idle turntable on the workshop preview
var craft_opp_card: Control = null
var craft_opp_caption: Label = null
var craft_opp_puppet: TextureRect = null
var craft_opp_name: Label = null
var craft_opp_region: Label = null
var craft_opp_duel: Label = null
var craft_slot_hint: Label = null
var craft_coin_chip: Control = null
var craft_forge_captions: Dictionary = {} # mat id -> "Forge: +0.3 Mass" label
var accent_swatches: Array[Button] = []
var cut_gunungan: TextureRect = null
var cut_region_label: Label = null
var cut_counter_label: Label = null
var _cut_gun_tween: Tween = null
var _cut_tick_stream: AudioStream = null
var _cut_ticked: int = 0 # typewriter: characters revealed at the last tick
var round_caption: Label = null
var round_score_row: HBoxContainer = null
var round_my_pips: ScorePips = null
var round_foe_pips: ScorePips = null
var round_score_label: Label = null
var round_reason_label: Label = null
var round_stats_row: HBoxContainer = null
var round_stat_values: Array[Label] = []
var round_stat_captions: Array[Label] = []
var round_timer_bar: ProgressBar = null
var round_continue_button: Button = null
var _round_next: Callable = Callable() # what CONTINUE triggers; the same guarded callback as the timer
var _round_token: int = 0 # bumped per armed panel: only the latest timer may advance
var _round_bar_tween: Tween = null
var over_masters_caption: Label = null
var over_masters_row: HBoxContainer = null
var over_coin_row: HBoxContainer = null
var over_coin_label: Label = null
var over_best_label: Label = null
var _endless_prev_best: int = 0 # endless best before this run (NEW BEST check)


func _update_workshop_preview() -> void:
	_clear_preview()
	if state != State.CRAFT:
		return
	# a real Gasing instance: wood + accent materials and idle spin for free,
	# and accent swatches recolor it live
	var viewed: String = _craft_viewed()
	var g: Gasing = GASING_SCENE.instantiate() as Gasing
	add_child(g)
	g.setup("", String(STYLE_DEFS[viewed].shape), _style_battle_stats(viewed), _style_accent(viewed))
	g.inspection_mode = true
	g.set_inspect_rotation(0.0, 0.0)
	workshop_preview = g
	# unproject to a point above screen center so the hero top spins in the
	# clear band between the header and the bottom sheet
	var vp: Vector2 = get_viewport().get_visible_rect().size
	var screen: Vector2 = Vector2(vp.x * 0.5, vp.y * 0.54)
	var hit: Variant = Plane(Vector3.UP, 0.0).intersects_ray(camera.project_ray_origin(screen), camera.project_ray_normal(screen))
	workshop_preview.position = hit if hit != null else Vector3.ZERO
	workshop_preview.scale = Vector3(0.01, 0.01, 0.01)
	_preview_tween = create_tween()
	_preview_tween.tween_property(workshop_preview, "scale", Vector3.ONE * _inspect_zoom, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	# slow idle turntable (one turn / 24 s) until the player grabs it; bound to the
	# preview so it dies with it
	_turn_tween = g.create_tween().set_loops()
	_turn_tween.tween_method(_turntable_yaw, 0.0, TAU, 24.0)


func _turntable_yaw(yaw: float) -> void:
	if not is_instance_valid(workshop_preview):
		return
	_inspect_yaw = wrapf(yaw, -PI, PI) # a later drag continues from here
	(workshop_preview as Gasing).set_inspect_rotation(_inspect_yaw, _inspect_pitch)


func _preview_contains(point: Vector2) -> bool:
	if not is_instance_valid(workshop_preview):
		return false
	var vp: Vector2 = get_viewport().get_visible_rect().size
	var top: float = craft_header.get_global_rect().end.y + 8.0
	var bottom: float = craft_sheet.get_global_rect().position.y - 8.0
	return Rect2(Vector2(vp.x * 0.15, top), Vector2(vp.x * 0.7, maxf(bottom - top, 0.0))).has_point(point)


func _apply_inspection() -> void:
	if not is_instance_valid(workshop_preview):
		return
	if _preview_tween != null and _preview_tween.is_valid():
		_preview_tween.kill()
	if _turn_tween != null and _turn_tween.is_valid():
		_turn_tween.kill() # the player took over the turntable
	(workshop_preview as Gasing).set_inspect_rotation(_inspect_yaw, _inspect_pitch)
	workshop_preview.scale = Vector3.ONE * _inspect_zoom


func _clear_preview() -> void:
	_inspect_dragging = false
	_inspect_yaw = 0.0
	_inspect_pitch = 0.0
	_inspect_zoom = 2.8
	if _preview_tween != null and _preview_tween.is_valid():
		_preview_tween.kill()
	_preview_tween = null
	if is_instance_valid(workshop_preview):
		workshop_preview.queue_free()
	workshop_preview = null


func _physics_process(delta: float) -> void:
	if _netbot and arena != null:
		arena.bot_tick(delta)


func _wind_effectiveness(power: float) -> float:
	if power > 95.0:
		return lerpf(1.0, 0.55, clampf((power - 95.0) / 5.0, 0.0, 1.0)) # graded overwind, not a cliff
	if power < 40.0:
		return 0.25 + 0.05 * (power / 40.0)
	if power < 80.0:
		return 0.3 + 0.65 * ((power - 40.0) / 40.0)
	return 0.95 + 0.05 * ((power - 80.0) / 15.0)


func _flash_click_marker(point: Vector3) -> void:
	click_marker.position = Vector3(point.x, 0.03, point.z)
	click_marker.visible = true
	click_marker.scale = Vector3(1.5, 1.5, 1.5)
	if _marker_tween != null and _marker_tween.is_valid():
		_marker_tween.kill()
	_marker_tween = create_tween()
	_marker_tween.tween_property(click_marker, "scale", Vector3(0.45, 0.45, 0.45), 0.35).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_marker_tween.tween_callback(click_marker.hide)


func _hit_effects(contact: Vector3, strength: float, kind: String = "hit", tint: Color = Color(1.0, 0.85, 0.4)) -> void:
	# kind "hit": strength = the faster top's impact speed (m/s) -> soft < 1.5 <= clash < 3.5 <= big
	var now: int = Time.get_ticks_msec()
	match kind:
		"grind": # rush contact: sparks + a soft tick, rate-limited, never shakes
			if now < _grind_next:
				return
			_grind_next = now + 150
			_emit_burst(contact, tint, 0.45)
			_play_sfx(SND_NUDGE, -16.0, 0.2)
		"rim": # near-miss at the rope; strength = radial speed
			_emit_burst(contact, tint, 0.55)
			_camera_nudge(0.1)
			_play_sfx(SND_RINGOUT, -12.0, 0.15)
		"land": # strength = launch quality 0..1
			_emit_burst(contact, tint, 0.35 + 0.35 * clampf(strength, 0.0, 1.0))
			_camera_nudge(0.08)
			_play_action_sfx("land", 0.9 + 0.2 * clampf(strength, 0.0, 1.0))
		"ko":
			_emit_burst(contact, tint, 1.4) # the crowd cheer is _toast_elimination's (it knows the owner)
			_camera_nudge(0.5)
		_:
			if strength < 1.5:
				_emit_burst(contact, tint, 0.5)
				_camera_nudge(0.05)
				_play_sfx(SND_NUDGE, -12.0, 0.15)
				return
			var big: bool = strength >= 3.5
			_emit_burst(contact, tint, 1.9 if big else 0.85)
			_camera_nudge(0.45 if big else 0.18)
			var clash: AudioStream = CLASH_SOUNDS[_rng.randi_range(0, CLASH_SOUNDS.size() - 1)]
			_play_sfx(clash, clampf(-10.0 + strength * 2.5, -10.0, 2.0), 0.12)
			if big:
				_play_sfx(SND_BIG_HIT, 0.0, 0.08)
				# the hit-stop and callout share one cooldown: a rush re-scores 'big' every
				# 0.3 s, and chained freezes read as hitching
				if now >= _pangkah_next:
					_pangkah_next = now + 1000
					_time_warp(0.05, 0.06) # hit-stop (SP only)
					_toast("PANGKAH!", HIT_ORANGE, contact, true)


func _emit_burst(point: Vector3, tint: Color, size: float) -> void:
	var b: CPUParticles3D = _bursts[_burst_index]
	_burst_index = (_burst_index + 1) % _bursts.size()
	b.global_position = point + Vector3(0.0, 0.35, 0.0)
	b.color = tint # multiplies the gold -> orange -> clear ramp
	b.scale_amount_min = 0.6 * size
	b.scale_amount_max = size
	b.initial_velocity_max = 2.0 + 2.5 * size
	b.restart()


func _time_warp(warp_scale: float, real_secs: float) -> void:
	# the single owner of Engine.time_scale; SP only. A shorter warp (hit-stop)
	# never cuts a longer active one (KO slow-mo) short.
	if net_active or _test_mode:
		return
	var until: int = Time.get_ticks_msec() + int(real_secs * 1000.0)
	if Engine.time_scale < 1.0 and until < _warp_until:
		return
	_warp_token += 1
	_warp_until = until
	Engine.time_scale = maxf(warp_scale, 0.05)
	get_tree().create_timer(real_secs, true, false, true).timeout.connect(_end_warp.bind(_warp_token))


func _end_warp(token: int) -> void:
	if token == _warp_token:
		Engine.time_scale = 1.0


func _fov_punch() -> void:
	if _fov_tween != null and _fov_tween.is_valid():
		_fov_tween.kill()
	_fov_tween = create_tween().set_ignore_time_scale(true)
	_fov_tween.tween_property(camera, "fov", _cam_fov - 7.0, 0.12).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	_fov_tween.tween_property(camera, "fov", _cam_fov, 0.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)


func _toast_elimination(top: Gasing, reason: String) -> void:
	var template: String = _t("toast_ringout") if reason == "ringout" else _t("toast_topple")
	if reason == "ringout":
		_play_sfx(SND_RINGOUT, -2.0, 0.1)
		_play_sfx(SND_TOPPLE, -6.0, 0.15)
	else:
		_play_sfx(SND_TOPPLE, -2.0, 0.1)
	if top.owner_id != arena.my_id():
		_play_action_sfx("cheer") # the crowd cheers your KOs, not your losses
	# the victim's side colour, naming the slot: "Tok Wan Nik · 2 RING OUT!"
	_toast(template % ("%s · %d" % [top.display_name, top.slot_id + 1]), top.team_color.lightened(0.15), top.position, false)


func _finish_duel(player_wins: bool, reason: Dictionary = {}) -> void:
	state = State.ROUND_OVER
	battle_hint.visible = false
	player_gauge.wobbling = false
	foe_gauge.wobbling = false
	_reset_round_panel()
	var opp: Dictionary = _current_opponent()
	if endless_mode and duel_index == 0:
		_endless_prev_best = endless_best # NEW BEST is judged against the best before this run
	round_caption.text = _duel_caption(opp)
	if player_wins:
		# the reward screen: purse + materials, XP / level-ups, and the master's top for sale
		_play_sfx(SND_WIN, -3.0, 0.02)
		_play_music("victory")
		round_label.text = _t("round_win")
		round_label.add_theme_color_override("font_color", PLAYER_COLOR)
		var counts: Dictionary = _grant_materials(_rng.randi_range(1, 2))
		mats_saved_label.text = _t("mats_saved")
		mats_saved_label.visible = true
		var wait: float = 4.5 # the reward panel has 5-6 lines to read; CONTINUE skips
		var reward: int = int(opp.get("coins", 40))
		coins += reward
		_show_award_icons(round_award_row, counts, "+%d", reward)
		if endless_mode:
			endless_best = maxi(endless_best, duel_index + 1)
		else:
			var mid: String = String(opp.id)
			if not defeated_masters.has(mid):
				defeated_masters.append(mid)
				unlock_label.text = _t("now_purchasable") % String(opp.name)
				unlock_label.add_theme_color_override("font_color", opp.get("color", PLAYER_COLOR))
				unlock_label.visible = true
				_pulse(unlock_label)
				wait = 5.5
		duel_index += 1
		if not endless_mode: # beating the last master starts the story over
			campaign_index = duel_index if duel_index < MASTERS.size() else 0
		_save_workshop()
		_fill_round_panel(1, reason) # the medallion keeps this duel's caption until the next one starts
		_show_panel(round_panel)
		_arm_round_advance(wait, _after_round.bind(player_wins))
		return
	if not endless_mode:
		campaign_index = 0 # a lost duel ends the run; saved now, not when the panel times out
		_save_workshop()
	_play_music("defeat") # a lost duel is the end of the run
	round_label.text = _t("round_lose") % opp.name
	round_label.add_theme_color_override("font_color", HT.SIDE_FOE) # the master's side colour, as on the HUD
	_fill_round_panel(2, reason)
	_show_panel(round_panel)
	_arm_round_advance(2.4, _after_round.bind(player_wins))


func _duel_caption(opp: Dictionary) -> String:
	# "Duel 3 / 7 · Tuan Pillay" / "Wave 4 · Kapitan Ong ★"
	if endless_mode:
		return "%s  ·  %s" % [_t("wave_n") % (duel_index + 1), String(opp.name)]
	return "%s  ·  %s" % [_t("duel_n") % [mini(duel_index + 1, MASTERS.size()), MASTERS.size()], String(opp.name)]


func _tally_match_mats(counts: Dictionary) -> void:
	for mat_id: String in counts:
		net_match_mats[mat_id] = int(net_match_mats.get(mat_id, 0)) + int(counts[mat_id])


func _show_award_icons(row: HBoxContainer, counts: Dictionary, fmt: String, coin_reward: int = 0) -> void:
	# reward cells: an optional coin purse first, then one icon per material
	for child: Node in row.get_children():
		child.queue_free()
	var cells: Array[HBoxContainer] = []
	if coin_reward > 0:
		var purse: HBoxContainer = HBoxContainer.new()
		purse.add_theme_constant_override("separation", 6)
		purse.add_child(_coin_icon(30.0))
		purse.add_child(_mk_label(_t("coin_gain") % coin_reward, 18, PLAYER_COLOR))
		cells.append(purse)
	for mat_id: String in counts:
		var cell: HBoxContainer = HBoxContainer.new()
		cell.add_theme_constant_override("separation", 4)
		var icon: TextureRect = TextureRect.new()
		icon.texture = load("res://assets/icon_%s.png" % mat_id)
		icon.custom_minimum_size = Vector2(36.0, 36.0)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		cell.add_child(icon)
		cell.add_child(_mk_label(fmt % int(counts[mat_id]), 18))
		cells.append(cell)
	for i: int in cells.size():
		# ponytail: staggered alpha pop instead of scale tween — no pivot bookkeeping
		cells[i].modulate.a = 0.0
		row.add_child(cells[i])
		var tw: Tween = create_tween()
		tw.tween_property(cells[i], "modulate:a", 1.0, 0.25).set_delay(0.1 + 0.08 * i)


func _reset_round_panel() -> void:
	for child: Node in round_award_row.get_children():
		child.queue_free()
	mats_saved_label.visible = false
	unlock_label.visible = false
	unlock_label.modulate.a = 1.0
	match_point_label.visible = false
	match_point_label.modulate.a = 1.0
	award_label.text = ""
	award_label.modulate.a = 1.0
	if _round_bar_tween != null and _round_bar_tween.is_valid():
		_round_bar_tween.kill()
	_round_next = Callable()
	round_continue_button.visible = false


func _pulse(l: CanvasItem) -> void:
	var tw: Tween = create_tween().set_loops(4)
	tw.tween_property(l, "modulate:a", 0.35, 0.4)
	tw.tween_property(l, "modulate:a", 1.0, 0.4)


func _after_round(player_wins: bool) -> void:
	if state != State.ROUND_OVER:
		return
	if not player_wins:
		_finish_run(false)
	elif not endless_mode and duel_index >= MASTERS.size():
		_finish_run(true)
	else:
		_enter_state(State.CRAFT)


func _finish_run(won: bool) -> void:
	run_won = won # campaign_index was already reset and saved by _finish_duel
	_play_sfx(SND_WIN if won else SND_LOSE, 0.0, 0.0)
	if won:
		_play_music("victory") # champion; a loss already played its stinger at the duel panel
	_reset_over_panel()
	# coins this run follow from how far it got: duel_index = duels won
	var earned: int = 0
	for i: int in duel_index:
		earned += int((_endless_opponent(i) if endless_mode else MASTERS[i]).coins)
	over_coin_label.text = _t("run_coins") % earned
	over_coin_row.visible = earned > 0
	if endless_mode:
		over_title.text = _t("over_lose")
		over_title.add_theme_color_override("font_color", DANGER)
		over_stats.text = _t("endless_over") % duel_index
		var new_best: bool = duel_index > _endless_prev_best
		over_best_label.text = _t("new_best") if new_best else _t("endless_best_line") % endless_best
		over_best_label.add_theme_color_override("font_color", PLAYER_COLOR if new_best else CREAM_MUTED)
		over_best_label.add_theme_font_size_override("font_size", 30 if new_best else 18)
		over_best_label.visible = true
		if new_best:
			_pulse(over_best_label)
	else:
		over_title.text = _t("over_win") if won else _t("over_lose")
		over_title.add_theme_color_override("font_color", PLAYER_COLOR if won else DANGER)
		over_stats.text = _t("duels_won") % [duel_index, MASTERS.size()]
		over_masters_caption.text = _t("masters_beaten")
		over_masters_caption.visible = true
		over_masters_row.visible = true
		for i: int in over_masters_row.get_child_count():
			var cell: Control = over_masters_row.get_child(i) as Control
			cell.modulate = Color(HT.INACTIVE, 0.25) # unlit lamp
			if i < duel_index: # beaten masters light up one after another
				create_tween().tween_property(cell, "modulate", Color.WHITE, 0.3).set_delay(0.3 + 0.12 * i)
	_enter_state(State.OVER)


func _reset_over_panel() -> void:
	for child: Node in over_award_row.get_children():
		child.queue_free()
	over_mats_title.visible = false
	over_award_row.visible = false
	over_bonus_label.visible = false
	over_masters_caption.visible = false
	over_masters_row.visible = false
	over_coin_row.visible = false
	over_best_label.visible = false
	over_best_label.modulate.a = 1.0
	rematch_status.text = ""
	rematch_status.visible = false
	rematch_status.modulate.a = 1.0
	restart_button.disabled = false


# ---------------------------------------------------------------- run / workshop

func _reset_run() -> void:
	duel_index = 0
	run_won = false


func _current_opponent() -> Dictionary:
	if endless_mode:
		return _endless_opponent(duel_index)
	return MASTERS[mini(duel_index, MASTERS.size() - 1)]


func _endless_opponent(wave: int) -> Dictionary:
	# cycle the masters with escalating multipliers; caps keep late waves beatable-but-brutal
	var m: Dictionary = MASTERS[wave % MASTERS.size()].duplicate()
	@warning_ignore("integer_division")
	var tier: int = wave / MASTERS.size()
	if tier > 0:
		m.name = "%s %s" % [String(m.name), "★".repeat(mini(tier, 3))]
	m.wind_mean = minf(float(m.wind_mean) + 2.0 * wave, 94.0)
	m.wind_dev = maxf(float(m.wind_dev) - 0.4 * wave, 2.0)
	m.spin_reserve = minf(float(m.spin_reserve) + 3.0 * tier, 130.0)
	m.mass = minf(float(m.mass) + 0.05 * wave, 3.4)
	m.aggressive = bool(m.aggressive) or wave >= 4
	m.coins = 15 + 8 * wave
	return m


func _style_accent(id: String) -> Color:
	var v: Variant = style_accents.get(id)
	return v if v is Color else PLAYER_COLOR


func _master_index(style_id: String) -> int:
	for i: int in MASTERS.size():
		if String(MASTERS[i].mesh) == style_id:
			return i
	return -1 # default/old-boss style, not gated behind a master


func _style_battle_stats(id: String) -> Dictionary:
	# MP is equal-footing: always fight with each style's base stats, never the forged workshop build.
	var src: Dictionary = STYLE_DEFS[id] if net_active else player_shapes[id]
	var s: Dictionary = {"mass": src.mass, "spin_reserve": src.spin_reserve, "balance": src.balance}
	s["mesh"] = STYLE_DEFS[id].mesh
	s["level"] = _style_level(id)
	if not net_active:
		var bonus: int = int(s.level) - 1
		s.mass += 0.04 * bonus
		s.spin_reserve += 4.0 * bonus
		s.balance += bonus
	return s


func _style_level(id: String) -> int:
	var xp: int = int(style_xp.get(id, 0))
	for level: int in range(LEVEL_XP.size(), 0, -1):
		if xp >= LEVEL_XP[level - 1]:
			return level
	return 1


func _award_style_xp(styles: Array, won: bool) -> void:
	# the result panels read _last_xp_gain / _last_level_ups right after this
	var awarded: Array[String] = []
	_last_xp_gain = 0
	_last_level_ups = []
	for value: Variant in styles:
		if not value is String:
			continue
		var id: String = value
		if not unlocked_styles.has(id) or awarded.has(id):
			continue
		awarded.append(id)
		var before: int = _style_level(id)
		_last_xp_gain = 30 if won else 15
		style_xp[id] = mini(int(style_xp.get(id, 0)) + _last_xp_gain, LEVEL_XP[-1])
		if _style_level(id) > before:
			_last_level_ups.append({"style": id, "level": _style_level(id)})
	_save_workshop()


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


func _load_workshop(source: ConfigFile = null) -> void:
	# defaults first — a missing/corrupt save degrades to a fresh workshop
	unlocked_styles = DEFAULT_STYLES.duplicate()
	materials_owned = {"merbau": 0, "kemuning": 0, "besi": 0}
	player_shapes = {}
	for id: String in STYLE_DEFS:
		var d: Dictionary = STYLE_DEFS[id]
		player_shapes[id] = {"mass": d.mass, "spin_reserve": d.spin_reserve, "balance": d.balance}
	selected_shape = "jantung"
	loadout = ["jantung", "uri", "jantung"]
	loadout_slot = 0
	difficulty = 0
	style_xp = {}
	coins = 0
	defeated_masters = []
	style_accents = {}
	endless_best = 0
	campaign_index = 0
	if source == null and (_test_mode or _netbot):
		return
	var cf: ConfigFile = source if source != null else _read_cfg(SAVE_PATH)
	if cf == null:
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
	# v2 keys — absent in v1 files, so old saves migrate to the defaults above
	var c: Variant = cf.get_value("workshop", "coins", 0)
	if c is int or c is float:
		coins = maxi(int(c), 0)
	var dv: Variant = cf.get_value("workshop", "defeated", [])
	if dv is Array:
		for mid: Variant in dv:
			if _master_index(String(mid)) >= 0 and not defeated_masters.has(String(mid)):
				defeated_masters.append(String(mid))
	var a: Variant = cf.get_value("workshop", "accents", {})
	if a is Dictionary:
		for k: Variant in a:
			if STYLE_DEFS.has(String(k)) and a[k] is Color:
				style_accents[String(k)] = a[k]
	var eb: Variant = cf.get_value("workshop", "endless_best", 0)
	if eb is int or eb is float:
		endless_best = maxi(int(eb), 0)
	# v3 keeps forged stats separate: level bonuses are derived, never saved into shapes.
	var xp: Variant = cf.get_value("workshop", "style_xp", {})
	if xp is Dictionary:
		for id: String in STYLE_DEFS:
			var value: Variant = xp.get(id, 0)
			if (value is int or value is float) and is_finite(float(value)):
				style_xp[id] = int(clampf(float(value), 0.0, float(LEVEL_XP[-1])))
	var saved_difficulty: Variant = cf.get_value("workshop", "difficulty", 0)
	if (saved_difficulty is int or saved_difficulty is float) and is_finite(float(saved_difficulty)):
		difficulty = int(clampf(float(saved_difficulty), 0.0, 2.0))
	var ci: Variant = cf.get_value("workshop", "campaign_index", 0)
	if (ci is int or ci is float) and is_finite(float(ci)):
		campaign_index = clampi(int(ci), 0, MASTERS.size() - 1)
	loadout[0] = selected_shape # old saves keep their selected top in slot one
	var saved_loadout: Variant = cf.get_value("workshop", "loadout", [])
	if saved_loadout is Array:
		for i: int in mini(saved_loadout.size(), 3):
			var value: Variant = saved_loadout[i]
			if value is String and unlocked_styles.has(value):
				loadout[i] = value
	selected_shape = loadout[0]


func _save_workshop() -> void:
	if _netbot or _test_mode:
		return # two local netbot instances share user:// — don't clobber the real save
	var cf: ConfigFile = ConfigFile.new()
	cf.set_value("workshop", "version", 3)
	cf.set_value("workshop", "unlocked", unlocked_styles)
	cf.set_value("workshop", "selected", selected_shape)
	cf.set_value("workshop", "materials", materials_owned)
	cf.set_value("workshop", "shapes", player_shapes)
	cf.set_value("workshop", "coins", coins)
	cf.set_value("workshop", "defeated", defeated_masters)
	cf.set_value("workshop", "accents", style_accents)
	cf.set_value("workshop", "endless_best", endless_best)
	cf.set_value("workshop", "style_xp", style_xp)
	cf.set_value("workshop", "loadout", loadout)
	cf.set_value("workshop", "difficulty", difficulty)
	cf.set_value("workshop", "campaign_index", campaign_index)
	_write_cfg(cf, SAVE_PATH) # non-fatal: _write_cfg warns


func _write_cfg(cf: ConfigFile, path: String) -> Error:
	# atomic save: write .tmp, keep the previous file as .bak, then swap the tmp in,
	# so a crash mid-write never leaves a truncated save
	var tmp: String = path + ".tmp"
	var err: Error = cf.save(tmp)
	if err == OK:
		var target: String = ProjectSettings.globalize_path(path)
		if FileAccess.file_exists(path):
			var bak_err: Error = DirAccess.copy_absolute(target, target + ".bak")
			if bak_err != OK:
				push_warning("Could not back up %s (error %d)" % [path, bak_err])
		err = DirAccess.rename_absolute(ProjectSettings.globalize_path(tmp), target)
	if err != OK:
		push_warning("Could not save %s (error %d)" % [path, err])
	return err


func _read_cfg(path: String) -> ConfigFile:
	# the save, else the .bak _write_cfg kept; null when neither parses
	for candidate: String in [path, path + ".bak"]:
		var cf: ConfigFile = ConfigFile.new() # fresh object: a failed parse may leave partial values behind
		if cf.load(candidate) == OK:
			return cf
	return null


func _restart_run() -> void:
	_reset_run()
	_enter_state(State.CRAFT)


func _on_restart_pressed() -> void:
	if net_active:
		if net_ended:
			_net_teardown()
			return
		if net_rematch_sent:
			return
		net_rematch_sent = true
		restart_button.disabled = true
		rematch_status.text = _t("ffa_wait_all")
		rematch_status.visible = true
		arena.request_rematch()
		return
	_restart_run()


func _on_over_menu_pressed() -> void:
	if net_active:
		_net_teardown()
		return
	_reset_run()
	_enter_state(State.READY)


func _on_fight_pressed() -> void:
	var viewed: String = _craft_viewed()
	if _can_buy(viewed):
		_on_shape_selected(viewed) # FIGHT doubles as BUY: reuse the confirm-then-buy flow
		return
	if not unlocked_styles.has(viewed):
		# browsing a locked top never blocks the duel: snap back to the loadout and fight
		_pending_buy = ""
		craft_index = maxi(0, STYLE_DEFS.keys().find(loadout[loadout_slot]))
		_refresh_craft()
		_update_workshop_preview()
	if net_active:
		arena.submit_loadout()
		return
	if menus != null and not menus.seen_howto and not _test_mode:
		# the very first fight: the how-to cards come first, and closing them starts it
		menus.show_info("howto", _t("howto_go"))
		menus.closed.connect(_on_howto_offer_closed, CONNECT_ONE_SHOT)
		return
	# a new SP duel (best of 3; endless waves are single rounds)
	arena.scores.clear()
	sp_round = 0
	var opp: Dictionary = _current_opponent()
	_apply_arena(String(opp.get("arena", "kampung"))) # swap happens behind the kelir
	var id: String = String(opp.id)
	if not endless_mode and CUTSCENES.has(id) and not _seen_cutscenes.has(id):
		_seen_cutscenes[id] = true
		_enter_state(State.CUTSCENE)
	else:
		_enter_state(State.WIND)


func _on_howto_offer_closed() -> void:
	if state == State.CRAFT:
		_on_fight_pressed()


static func _duel_outcome(scores: Dictionary) -> int:
	# best of 3: +1 player took the duel, -1 the master did, 0 play another round
	if int(scores.get(1, 0)) >= 2:
		return 1
	if int(scores.get(2, 0)) >= 2:
		return -1
	return 0


func _on_lang_pressed(code: String) -> void:
	if not STRINGS.has(code):
		return # a hand-edited settings.cfg: CUTSCENES/MASTERS/STRINGS index by lang directly
	lang = code
	_apply_language()
	if menus != null:
		menus.save_settings()


func _craft_viewed() -> String:
	return STYLE_DEFS.keys()[craft_index]


func _can_buy(id: String) -> bool:
	# locked, on sale (not behind an unbeaten master), affordable; SP only
	var gate: int = _master_index(id)
	return not unlocked_styles.has(id) and not net_active and coins >= int(STYLE_DEFS[id].get("price", 0)) \
		and not (gate >= 0 and not defeated_masters.has(String(MASTERS[gate].id)))


func _craft_cycle(dir: int) -> void:
	if net_active and net_ready_sent:
		return # config already on the wire; a late switch would desync the peers
	_pending_buy = ""
	craft_index = wrapi(craft_index + dir, 0, STYLE_DEFS.size())
	var id: String = _craft_viewed()
	if unlocked_styles.has(id):
		_on_shape_selected(id) # auto-select what you're looking at (sets, saves, refreshes, previews)
	else:
		_refresh_craft()
		_update_workshop_preview()


func _on_shape_selected(id: String) -> void:
	if not unlocked_styles.has(id):
		if net_active:
			craft_info.text = _t("locked_mp")
			return
		var gate: int = _master_index(id)
		var price: int = int(STYLE_DEFS[id].get("price", 0))
		if gate >= 0 and not defeated_masters.has(String(MASTERS[gate].id)):
			craft_info.text = _t("locked_beat") % String(MASTERS[gate].name)
		elif coins >= price:
			if _pending_buy != id: # purchases take a confirming second press
				_pending_buy = id
				craft_info.text = _t("buy_confirm") % [String(STYLE_DEFS[id].label), price]
				return
			_pending_buy = ""
			coins -= price
			unlocked_styles.append(id)
			selected_shape = id
			loadout[loadout_slot] = id
			_play_sfx(SND_WIN, -6.0, 0.05)
			craft_info.text = _t("bought") % String(STYLE_DEFS[id].label)
			_save_workshop()
			_refresh_craft()
			_update_workshop_preview()
			_update_top_bar()
		else:
			craft_info.text = _t("need_coins") % [price, coins]
		return
	selected_shape = id
	loadout[loadout_slot] = id
	craft_info.text = _t("selected_info") % String(STYLE_DEFS[id].label)
	_save_workshop()
	_refresh_craft()
	_update_workshop_preview()


func _on_loadout_slot_pressed(slot: int) -> void:
	if net_active and net_ready_sent:
		return
	loadout_slot = clampi(slot, 0, 2)
	selected_shape = loadout[loadout_slot]
	craft_index = STYLE_DEFS.keys().find(selected_shape)
	craft_info.text = _t("pick_info")
	_refresh_craft()
	_update_workshop_preview()


func _on_difficulty_selected(index: int) -> void:
	if net_active:
		return
	difficulty = clampi(index, 0, 2)
	_save_workshop()
	for i: int in craft_difficulty.size():
		craft_difficulty[i].set_pressed_no_signal(i == difficulty) # a re-click never un-selects


func _on_material_pressed(mat_id: String) -> void:
	if net_active: return # MP is equal-footing; forging is disabled
	var def: Dictionary = MATERIAL_DEFS[mat_id]
	if _forge_capped(mat_id):
		craft_info.text = _t("forge_max") % String(STYLE_DEFS[selected_shape].label)
		return
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


func _forge_capped(mat_id: String) -> bool:
	# true when forging this material would change nothing on the selected top
	var def: Dictionary = MATERIAL_DEFS[mat_id]
	var stats: Dictionary = player_shapes[selected_shape]
	return is_equal_approx(clampf(stats.mass + def.mass, 1.4, 3.0), stats.mass) \
		and is_equal_approx(clampf(stats.balance + def.balance, 55.0, 85.0), stats.balance)


func _on_accent_selected(c: Color) -> void:
	if net_active:
		return # MP tops are always gold/teal
	style_accents[selected_shape] = c
	_save_workshop()
	_refresh_accents()
	_update_workshop_preview() # live: the spinning preview rebuilds with the new lacquer


func _refresh_accents() -> void:
	# the chosen lacquer wears a gold ring; the rest a thin carved edge
	var current: Color = _style_accent(selected_shape)
	for i: int in accent_swatches.size():
		var on: bool = ACCENT_CHOICES[i].is_equal_approx(current)
		for kind: String in ["normal", "hover"]:
			# selected: carved dark rim + gold halo, so it reads even on the gold swatch
			var sb: StyleBoxFlat = accent_swatches[i].get_theme_stylebox(kind) as StyleBoxFlat
			sb.border_color = WOOD_EDGE
			sb.set_border_width_all(2 if on else 1)
			sb.set_expand_margin_all(2.0 if on else 0.0)
			sb.shadow_color = SONGKET_GOLD
			sb.shadow_size = 6 if on else 0


func _on_material_bought(mat_id: String) -> void:
	if net_active:
		return # MP is equal-footing; no economy
	var price: int = int(MAT_PRICES[mat_id])
	if coins < price:
		craft_info.text = _t("need_coins") % [price, coins]
		return
	if _pending_buy != "mat:" + mat_id: # purchases take a confirming second press
		_pending_buy = "mat:" + mat_id
		craft_info.text = _t("buy_confirm") % [String(MATERIAL_DEFS[mat_id].label), price]
		return
	_pending_buy = ""
	coins -= price
	materials_owned[mat_id] += 1
	craft_info.text = _t("mat_bought") % String(MATERIAL_DEFS[mat_id].label)
	_save_workshop()
	_refresh_craft()
	_update_top_bar()


func _clear_tops() -> void:
	if arena != null:
		arena.clear_tops()
	player_top = null
	foe_top = null


func _build_sfx_pool() -> void:
	var has_sfx_bus: bool = AudioServer.get_bus_index("SFX") >= 0
	for i: int in 8:
		var p: AudioStreamPlayer = AudioStreamPlayer.new()
		p.process_mode = Node.PROCESS_MODE_ALWAYS # menu clicks still sound while paused
		if has_sfx_bus:
			p.bus = "SFX"
		add_child(p)
		_sfx_pool.append(p)
	# the two music players _play_music crossfades between; the bed plays on under the pause menu
	for i: int in 2:
		var m: AudioStreamPlayer = AudioStreamPlayer.new()
		m.process_mode = Node.PROCESS_MODE_ALWAYS
		if AudioServer.get_bus_index("Music") >= 0:
			m.bus = "Music"
		m.finished.connect(_on_music_finished.bind(m))
		add_child(m)
		_music.append(m)


func _play_sfx(stream: AudioStream, volume_db: float = 0.0, pitch_jitter: float = 0.1, pitch: float = 1.0) -> void:
	if stream == null or _sfx_pool.is_empty():
		return
	var p: AudioStreamPlayer = _sfx_pool[_sfx_index]
	_sfx_index = (_sfx_index + 1) % _sfx_pool.size()
	p.stop()
	p.stream = stream
	p.volume_db = volume_db
	p.pitch_scale = pitch * (1.0 + _rng.randf_range(-pitch_jitter, pitch_jitter))
	p.play()


func _load_audio(path_no_ext: String) -> AudioStream:
	for ext: String in [".ogg", ".mp3", ".wav"]:
		if ResourceLoader.exists(path_no_ext + ext):
			return load(path_no_ext + ext) as AudioStream
	return null


func _play_action_sfx(kind: String, pitch: float = 1.0) -> void:
	# kinds: push, dash, jump, deny, charge_tick, launch, snap, land, gong, cheer (rush loops on _rush_player)
	var entry: Array = ACTION_SFX.get(kind, [])
	if entry.is_empty():
		return
	_play_sfx(_action_streams.get(kind) as AudioStream, float(entry[2]), 0.05, pitch * float(entry[3]))


func _play_music(key: String) -> void:
	# keys: menu, battle, cutscene (loops), victory, defeat (stingers); "" stops.
	# Beds crossfade; a stinger cuts in once, then the bed the current state last
	# asked for (_music_bed) fades back when it finishes.
	var stinger: bool = key == "victory" or key == "defeat"
	if not stinger:
		_music_bed = key
		if _music_key == "victory" or _music_key == "defeat":
			return # the stinger's finish brings this bed in
	if key == _music_key or _music.is_empty():
		return # never restart a bed that is already playing
	var stream: AudioStream = null
	if key != "":
		if not _music_streams.has(key):
			var loaded: AudioStream = _load_audio("res://assets/audio/music/" + key)
			if loaded != null:
				loaded.set("loop", not stinger) # the .import files keep loop off; loops live here
			_music_streams[key] = loaded
		stream = _music_streams[key]
	_music_key = key if stream != null else ""
	if _music_tween != null and _music_tween.is_valid():
		_music_tween.kill()
	_music_tween = create_tween().set_parallel(true).set_pause_mode(Tween.TWEEN_PAUSE_PROCESS).set_ignore_time_scale(true)
	var fade: float = 0.3 if stinger else 1.2
	var old: AudioStreamPlayer = _music[_music_idx]
	if old.playing:
		_music_tween.tween_property(old, "volume_linear", 0.0, fade)
		_music_tween.tween_callback(old.stop).set_delay(fade)
	_music_idx = 1 - _music_idx
	var cur: AudioStreamPlayer = _music[_music_idx]
	cur.stop()
	if stream == null:
		return
	cur.stream = stream
	cur.volume_linear = 1.0 if stinger else 0.0
	cur.play()
	if not stinger:
		_music_tween.tween_property(cur, "volume_linear", 1.0, fade)


func _on_music_finished(p: AudioStreamPlayer) -> void:
	# beds loop, so only a stinger ends here: hand back to the state's bed
	if p == _music[_music_idx] and (_music_key == "victory" or _music_key == "defeat"):
		_music_key = ""
		_play_music(_music_bed)


# ---------------------------------------------------------------- effects

func _configure_burst() -> void:
	burst.emitting = false
	burst.one_shot = true
	burst.amount = 26
	burst.lifetime = 0.45
	burst.explosiveness = 1.0
	burst.direction = Vector3.UP
	burst.spread = 70.0
	burst.initial_velocity_min = 2.0
	burst.initial_velocity_max = 4.5
	burst.gravity = Vector3(0.0, -9.0, 0.0)
	burst.scale_amount_min = 0.6
	burst.scale_amount_max = 1.0
	var shrink: Curve = Curve.new()
	shrink.add_point(Vector2(0.0, 1.0))
	shrink.add_point(Vector2(1.0, 0.0))
	burst.scale_amount_curve = shrink
	var ramp: Gradient = Gradient.new() # x tint (burst.color): hot core -> orange -> clear
	ramp.set_color(0, Color(1.0, 1.0, 0.85))
	ramp.set_color(1, Color(1.0, 0.45, 0.1, 0.0))
	ramp.add_point(0.45, Color(1.0, 0.65, 0.3))
	burst.color_ramp = ramp
	# unshaded vertex-colour sparks (gasing.gd trail pattern) so the ramp shows as-is
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.7, 0.3)
	mat.emission_energy_multiplier = 3.0
	var m: SphereMesh = SphereMesh.new()
	m.radius = 0.05
	m.height = 0.1
	m.radial_segments = 8
	m.rings = 4
	m.material = mat
	burst.mesh = m
	burst.color = Color(1.0, 0.85, 0.4)
	# 4 pooled bursts so back-to-back hits never restart one mid-flight
	_bursts = [burst]
	for i: int in 3:
		var b: CPUParticles3D = burst.duplicate() as CPUParticles3D
		b.name = "HitBurst%d" % (i + 2)
		add_child(b)
		_bursts.append(b)
	# pre-warm: fire the pool once under the ground (in the camera frustum, hidden by the Ground plane)
	# behind the title, so the first real clash doesn't stall compiling the spark pipeline
	for b: CPUParticles3D in _bursts:
		b.global_position = Vector3(0.0, -3.0, 0.0)
		b.restart()


func _camera_nudge(amount: float = 0.18) -> void:
	# adds shake trauma; _process turns it into decaying camera offsets
	_trauma = minf(_trauma + amount, 1.0)


# ---- hud state
var hud_medallion: Control = null # centre plaque: round clock, best-of-3 pips, duel line
var hud_clock: Label = null
var hud_lead: Label = null # "Leading: X" in the last 15 s (replaces duel_label)
var hud_rows: Array = [] # SquadRow x3: FFA rivals beyond the one on the foe bar
var wind_count: Label = null # wind card title: WIND countdown / reserve being charged
var wind_text: Label = null
var _strip_labels: Array[Label] = [] # key-cap strip: [cap, caption] pairs, texts per language
var _hud_tween: Tween = null
var _banner_queue: Array = [] # [text, color, sub] waiting behind the banner on screen
var _banner_since: int = 0 # real msec the current banner appeared
var _toast_last: Dictionary = {} # toast text -> real msec it last showed (rate limit)


func _toast(text: String, color: Color, world_pos: Vector3, big: bool) -> void:
	# world-anchored carved-Kurland callout (same type as the banners): the same text at
	# most every 0.35 s, starting above the top's spin label, stacked above any toast
	# still rising at that spot, and clamped fully on screen clear of the HUD bars
	var now: int = Time.get_ticks_msec()
	if now - int(_toast_last.get(text, -100000)) < 350:
		return
	_toast_last[text] = now
	var l: Label = _mk_title(text, 40 if big else 26, color)
	l.size = Vector2(500.0, 50.0)
	l.pivot_offset = Vector2(250.0, 25.0)
	l.z_index = 10
	l.scale = Vector2(0.6, 0.6)
	hud.add_child(l) # in the tree first: the font decides the text width
	var half_w: float = l.get_minimum_size().x * 0.5 + 16.0
	var vp: Vector2 = hud.size
	var screen: Vector2 = camera.unproject_position(world_pos + Vector3(0.0, 1.6, 0.0))
	screen.x = clampf(screen.x, half_w, maxf(vp.x - half_w, half_w))
	for other: Node in hud.get_children():
		if other.has_meta("toast") and (other as Control).position.distance_to(screen - Vector2(250.0, 25.0)) < 44.0:
			screen.y -= 44.0
	# rises 70 px: stays below the top bars, and below the banner band while one shows
	screen.y = clampf(screen.y, TOAST_BANNER_FLOOR if is_instance_valid(_banner_box) else 150.0, vp.y - 110.0)
	l.position = screen - Vector2(250.0, 25.0)
	l.set_meta("toast", true)
	var tw: Tween = create_tween()
	tw.set_parallel(true)
	tw.tween_property(l, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(l, "position:y", l.position.y - 70.0, 1.0)
	tw.tween_property(l, "modulate:a", 0.0, 0.55).set_delay(0.45)
	tw.chain().tween_callback(l.queue_free)


func _banner(text: String, color: Color, sub: String = "") -> void:
	# centre-screen Kurland callout (ROUND n, LAUNCH! + grade, K.O., TIME!, MATCH POINT) that
	# never overwrites another: the same title in the same beat refines the one on screen
	# (LAUNCH! then its grade); anything else queues and cuts the current one short at 0.5 s
	if not is_instance_valid(_banner_box):
		_banner_queue.clear() # nothing on screen (a state change freed it): the queue is stale
		_banner_show(text, color, sub)
		return
	if _banner_queue.is_empty() and _banner_box.get_meta("text") == text and Time.get_ticks_msec() - _banner_since < 600:
		_banner_fill(_banner_box, color, sub)
		return
	if not _banner_queue.is_empty() and _banner_queue.back()[0] == text:
		_banner_queue[-1] = [text, color, sub]
		return
	_banner_queue.append([text, color, sub])
	if _banner_queue.size() > 2:
		_banner_queue.pop_front() # a burst of callouts keeps only the latest two
	var box: Control = _banner_box
	(box.get_meta("tw") as Tween).kill()
	var tw: Tween = box.create_tween().set_ignore_time_scale(true)
	tw.tween_property(box, "modulate:a", 1.0, 0.08)
	tw.parallel().tween_property(box, "scale", Vector2.ONE, 0.08)
	tw.tween_interval(maxf(0.42 - (Time.get_ticks_msec() - _banner_since) * 0.001, 0.0))
	tw.tween_property(box, "modulate:a", 0.0, 0.15)
	tw.tween_callback(_banner_next)
	box.set_meta("tw", tw)


func _banner_show(text: String, color: Color, sub: String) -> void:
	# a dark band fading out at both ends between songket-gold rules, title + sub centred.
	# y 122-192: under the medallion (to y 120), above the far rim where the foe spawns
	# a world toast in, or rising into, the band would garble with it: the banner supersedes it
	for t: Node in hud.get_children():
		if t.has_meta("toast") and (t as Control).position.y + 25.0 < TOAST_BANNER_FLOOR:
			t.queue_free()
	var box: Control = Control.new()
	box.set_anchors_preset(Control.PRESET_TOP_WIDE)
	box.offset_top = 122.0
	box.offset_bottom = 192.0
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for part: Array in [[0.0, 70.0, Color(HT.WOOD_EDGE, 0.8)], [0.0, 2.0, Color(HT.SONGKET_GOLD, 0.9)], [68.0, 70.0, Color(HT.SONGKET_GOLD, 0.9)]]:
		var c: Color = part[2]
		var g: Gradient = Gradient.new()
		g.offsets = PackedFloat32Array([0.0, 0.3, 0.7, 1.0])
		g.colors = PackedColorArray([Color(c, 0.0), c, c, Color(c, 0.0)])
		var gt: GradientTexture2D = GradientTexture2D.new()
		gt.gradient = g
		gt.height = 1
		var band: TextureRect = TextureRect.new()
		band.texture = gt
		band.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		band.set_anchors_preset(Control.PRESET_TOP_WIDE)
		band.offset_top = part[0]
		band.offset_bottom = part[1]
		band.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(band)
	var v: VBoxContainer = VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", -10)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var title: Label = _mk_title(text, 44, color)
	var sub_l: Label = _mk_title("", 22, TEXT_COLOR)
	v.add_child(title)
	v.add_child(sub_l)
	box.add_child(v)
	box.set_meta("text", text)
	box.set_meta("title", title)
	box.set_meta("sub", sub_l)
	_banner_fill(box, color, sub)
	ui.add_child(box)
	_banner_box = box
	_banner_since = Time.get_ticks_msec()
	box.pivot_offset = Vector2(get_viewport().get_visible_rect().size.x * 0.5, 35.0)
	box.scale = Vector2(1.18, 1.18)
	box.modulate.a = 0.0
	var tw: Tween = box.create_tween().set_ignore_time_scale(true)
	tw.tween_property(box, "modulate:a", 1.0, 0.15)
	tw.parallel().tween_property(box, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(1.0)
	tw.tween_property(box, "modulate:a", 0.0, 0.3)
	tw.tween_callback(_banner_next)
	box.set_meta("tw", tw)


func _banner_fill(box: Control, color: Color, sub: String) -> void:
	(box.get_meta("title") as Label).add_theme_color_override("font_color", color)
	var sub_l: Label = box.get_meta("sub")
	sub_l.text = sub
	sub_l.visible = not sub.is_empty()


func _banner_next() -> void:
	if is_instance_valid(_banner_box):
		_banner_box.queue_free()
	_banner_box = null
	if not _banner_queue.is_empty():
		var next: Array = _banner_queue.pop_front()
		_banner_show(next[0], next[1], next[2])


func _hint(key: String) -> void:
	# one-shot contextual tip ("steer" | "dash" | "reserve"), once per session; SP only
	if _test_mode or net_active or _hints_shown.has(key) or not STRINGS[lang].has("hint_" + key):
		return
	var text: String = _t("hint_" + key)
	if key == "reserve": # name the key of a reserve that can actually launch
		var slot: int = arena.reserve_slot(arena.my_id())
		if slot < 0:
			return
		text = text % (slot + 1)
	_hints_shown[key] = true
	for old: Node in hud.get_children():
		if old.has_meta("hint"):
			old.queue_free() # one tip at a time
	# a gold tip on a carved plate just above the key-cap strip, clear of the ring
	var l: PanelContainer = PanelContainer.new()
	l.add_theme_stylebox_override("panel", _hud_plate())
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_child(_mk_label(text, 18, HT.SONGKET_GOLD))
	l.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	l.offset_top = -82.0 # y 638-672: clear of the ring (to y 635) and the key strip (from y 674)
	l.offset_bottom = -48.0
	l.grow_horizontal = Control.GROW_DIRECTION_BOTH
	l.grow_vertical = Control.GROW_DIRECTION_BEGIN
	l.set_meta("hint", true)
	hud.add_child(l)
	l.modulate.a = 0.0
	var tw: Tween = l.create_tween()
	tw.tween_property(l, "modulate:a", 1.0, 0.25)
	tw.tween_interval(4.0)
	tw.tween_property(l, "modulate:a", 0.0, 0.6)
	tw.tween_callback(l.queue_free)


# ---------------------------------------------------------------- UI build

func _set_hud_visible(v: bool) -> void:
	# the battle HUD fades (0.25 s in / 0.2 s out) instead of popping; test runs switch at once
	if _hud_tween != null and _hud_tween.is_valid():
		_hud_tween.kill()
	if _test_mode:
		hud.visible = v
		hud.modulate.a = 1.0
		return
	if v:
		if not hud.visible:
			hud.modulate.a = 0.0
		hud.visible = true
		_hud_tween = hud.create_tween()
		_hud_tween.tween_property(hud, "modulate:a", 1.0, 0.25)
	elif hud.visible:
		_hud_tween = hud.create_tween()
		_hud_tween.tween_property(hud, "modulate:a", 0.0, 0.2)
		_hud_tween.tween_callback(hud.hide)


func _show_panel(target: Control) -> void:
	if target != null and is_instance_valid(_banner_box):
		_banner_box.queue_free() # a results card takes the stage from any battle callout (TIME!)
		_banner_queue.clear()
	for panel: Control in _all_panels:
		if panel == null:
			continue
		# one fade per panel: a quick A -> B -> A must not let A's stale fade-out hide it
		if panel.has_meta("fade"):
			(panel.get_meta("fade") as Tween).kill()
		if panel == target:
			panel.visible = true
			if panel == cutscene_panel:
				panel.modulate.a = 1.0 # its opaque kelir IS the curtain: the arena swap behind it never shows
				panel.remove_meta("fade")
				continue
			panel.modulate.a = 0.0
			var tw: Tween = create_tween()
			tw.tween_property(panel, "modulate:a", 1.0, 0.25)
			panel.set_meta("fade", tw)
		elif panel.visible:
			var tw2: Tween = create_tween()
			tw2.tween_property(panel, "modulate:a", 0.0, 0.15)
			tw2.tween_callback(panel.hide)
			panel.set_meta("fade", tw2)


func _curtain() -> void:
	# wayang scene change: the gunungan sweeps across the lamp-lit kelir and the new
	# screen appears behind it. The caller has ALREADY changed state, synchronously:
	# this is a pure overlay nothing waits on, and in test mode it never runs.
	if _test_mode:
		return
	if _curtain_root == null:
		_curtain_root = Control.new()
		_curtain_root.set_anchors_preset(Control.PRESET_FULL_RECT)
		_curtain_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_curtain_root.z_index = 50 # over panels and HUD, under the menus overlay (100)
		ui.add_child(_curtain_root)
		_curtain_sweep = Control.new()
		_curtain_sweep.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_curtain_root.add_child(_curtain_sweep)
		_curtain_sweep.add_child(_mk_kelir())
		_curtain_puppet = TextureRect.new()
		var path: String = "res://assets/wayang/wayang_gunungan.png"
		_curtain_puppet.texture = load(path) as Texture2D if ResourceLoader.exists(path) else TEX_GUNUNGAN
		_curtain_puppet.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_curtain_puppet.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		_curtain_puppet.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_curtain_sweep.add_child(_curtain_puppet)
	# the cut-out (a square 1.3 screens tall, so tip and rod overhang) leads and the kelir
	# trails from its centre line, so the kelir's edge always hides behind the puppet
	var vp: Vector2 = get_viewport().get_visible_rect().size
	var g: float = vp.y * 1.3
	_curtain_puppet.size = Vector2(g, g)
	_curtain_puppet.position = Vector2(0.0, (vp.y - g) * 0.5)
	_curtain_puppet.pivot_offset = Vector2(g, g) * 0.5
	_curtain_puppet.rotation = deg_to_rad(-10.0)
	var kelir: Control = _curtain_sweep.get_child(0)
	kelir.position = Vector2(g * 0.5, 0.0)
	kelir.size = Vector2(vp.x + g, vp.y)
	_curtain_sweep.position = Vector2(-g, 0.0)
	_curtain_root.visible = true
	if _curtain_tween != null and _curtain_tween.is_valid():
		_curtain_tween.kill()
	_curtain_tween = create_tween().set_parallel(true).set_pause_mode(Tween.TWEEN_PAUSE_PROCESS).set_ignore_time_scale(true)
	_curtain_tween.tween_property(_curtain_sweep, "position:x", vp.x, 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_curtain_tween.tween_property(_curtain_puppet, "rotation", deg_to_rad(8.0), 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_curtain_tween.chain().tween_callback(_curtain_root.hide)


func _mk_kelir() -> TextureRect:
	var kelir: TextureRect = TextureRect.new()
	kelir.texture = _kelir_texture()
	kelir.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	kelir.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return kelir


func _update_top_bar() -> void:
	# medallion caption: which fight this is (clock, pips and leader are live in arena.update_hud)
	if net_active:
		duel_label.text = _t("hud_ffa") % NET_MATCH_TARGET
		return
	var region: String = String(_current_opponent().get("region_" + lang, ""))
	if endless_mode:
		duel_label.text = _t("hud_wave") % [duel_index + 1, region]
	else:
		duel_label.text = _t("hud_duel") % [mini(duel_index + 1, MASTERS.size()), MASTERS.size(), region]


func _apply_language() -> void:
	ready_heritage.text = _t("heritage")
	ready_fact_head.text = _t("did_you_know")
	ready_fact.text = _t("fact_%d" % (_fact_idx + 1))
	ready_prompt.text = _t("prompt")
	howto_button.text = _t("howto")
	settings_button.text = _t("settings")
	credits_button.text = _t("credits")
	var caps: PackedStringArray = _t("hud_keycaps").split("|")
	var verbs: PackedStringArray = _t("hud_keys").split("|")
	for i: int in caps.size():
		if i * 2 + 1 < _strip_labels.size():
			_strip_labels[i * 2].text = caps[i]
			_strip_labels[i * 2 + 1].text = verbs[i]
	wind_meter.label_text = _t("meter") # gauge titles are live in arena.update_hud
	craft_title.text = _t("bench")
	craft_info.text = _t("pick_info")
	fight_button.text = _t("fight")
	restart_button.text = _t("restart")
	over_hint.text = _t("or_space")
	_refresh_sp_button()
	endless_button.text = _t("endless")
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
	mp_code_label.text = _t("mp_code_label")
	join_code_button.text = _t("join_code")
	steam_offline_label.text = _t("steam_offline")
	mp_back_button.text = _t("back")
	invite_button.text = _t("invite_friend")
	wait_cancel_button.text = _t("cancel")
	over_menu_button.text = _t("back_menu")
	craft_back_button.text = _t("back")
	craft_sub.text = _t("first_to_3")
	var names: Array = ["stat_mass", "stat_spin", "stat_balance"]
	var tips: Array = ["tip_stat_mass", "tip_stat_spin", "tip_stat_balance"]
	for i: int in craft_stat_rows.size():
		var r: Dictionary = craft_stat_rows[i]
		(r.label as Label).text = _t(names[i])
		(r.label as Label).tooltip_text = _t(tips[i])
		(r.bar as ProgressBar).tooltip_text = _t(tips[i])
	for mat_id: String in material_buttons:
		var mb: Button = material_buttons[mat_id]
		mb.tooltip_text = _t("tip_" + mat_id)
	for code: String in lang_buttons:
		var b: Button = lang_buttons[code]
		b.modulate = Color.WHITE if code == lang else Color(INACTIVE, 0.7)
	_update_top_bar()
	_refresh_craft()


func _refresh_sp_button() -> void:
	# title-screen live text: CONTINUE label + the progress line (masters beaten, endless best)
	sp_button.text = (_t("continue_duel") % [campaign_index + 1, MASTERS.size()]) if campaign_index > 0 else _t("single_player")
	ready_progress_pips.wins = defeated_masters.size()
	ready_progress_pips.queue_redraw()
	ready_progress.text = _t("progress_masters") % [defeated_masters.size(), MASTERS.size()]
	if endless_best > 0:
		ready_progress.text += "   ·   " + _t("progress_endless") % endless_best


func _mk_title(text: String, font_size: int, color: Color = PLAYER_COLOR) -> Label:
	# Kurland display font with a carved-wood outline — panel headers
	var l: Label = _mk_label(text, font_size, color)
	l.add_theme_font_override("font", FONT_TITLE)
	l.add_theme_color_override("font_outline_color", Color(0.25, 0.12, 0.02))
	l.add_theme_constant_override("outline_size", 6)
	l.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.6))
	l.add_theme_constant_override("shadow_offset_y", 3)
	return l


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
	var txt_col: Color = TEXT_COLOR if light_text else INK
	b.add_theme_color_override("font_color", txt_col)
	b.add_theme_color_override("font_hover_color", txt_col)
	b.add_theme_color_override("font_pressed_color", txt_col.darkened(0.2) if not light_text else txt_col)
	b.add_theme_color_override("font_hover_pressed_color", txt_col.darkened(0.2) if not light_text else txt_col)
	b.add_theme_color_override("font_disabled_color", Color(TEXT_DIM, 0.75)) # muted but legible on the darkened plaque
	_set_plaque(b, base)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.focus_mode = Control.FOCUS_NONE # arrows must reach _unhandled_input (carousel), not focus-nav
	b.pressed.connect(_on_any_button_pressed)
	b.mouse_entered.connect(_on_button_hover.bind(b, true))
	b.mouse_exited.connect(_on_button_hover.bind(b, false))
	return b


func _set_plaque(b: Button, base: Color) -> void:
	# neutral-bright carved plaque texture x modulate = plaque in any wood tone
	b.add_theme_stylebox_override("normal", HT.plaque_box(base))
	b.add_theme_stylebox_override("hover", HT.plaque_box(base.lightened(0.18)))
	var sb_p: StyleBoxTexture = HT.plaque_box(base.darkened(0.28))
	b.add_theme_stylebox_override("pressed", sb_p)
	b.add_theme_stylebox_override("hover_pressed", sb_p) # toggle plaques (loadout slots) keep their wood while hovered
	b.add_theme_stylebox_override("disabled", HT.plaque_box(base.darkened(0.45)))


func _on_any_button_pressed() -> void:
	_play_sfx(SND_CLICK, -6.0, 0.05)


func _on_button_hover(b: Button, on: bool) -> void:
	# every plaque answers the mouse: a soft tick and a 4% lift from its centre
	if on and b.disabled:
		return
	if on:
		_play_action_sfx("hover")
	b.pivot_offset = b.size * 0.5
	if b.has_meta("hover_tw"):
		(b.get_meta("hover_tw") as Tween).kill()
	var tw: Tween = b.create_tween()
	tw.tween_property(b, "scale", Vector2.ONE * (1.04 if on else 1.0), 0.12).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	b.set_meta("hover_tw", tw)


func _mk_panel_box(compact: bool = false, pad: float = 0.0) -> PanelContainer:
	# carved ukiran frame; compact = slim double-groove variant (craft cards, small boxes);
	# pad = extra breathing room for text-heavy boxes
	var p: PanelContainer = PanelContainer.new()
	var sb: StyleBoxTexture = StyleBoxTexture.new()
	sb.texture = TEX_CARD if compact else TEX_PANEL
	# card frame's gold line sits at texture px 15-16: slice at 18 so the whole
	# line stays in the border patches (16 cut through it and bled gold into the
	# stretched center)
	sb.set_texture_margin_all(18.0 if compact else 48.0)
	if not compact:
		# tile the scroll border instead of stretching it (motifs must not distort);
		# the slim card frame is straight lines, so default STRETCH is seamless for it
		sb.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
		sb.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	var m: float = (20.0 if compact else 52.0) + pad # content must fully clear the border art
	sb.content_margin_left = m
	sb.content_margin_right = m
	sb.content_margin_top = (18.0 if compact else 50.0) + pad
	sb.content_margin_bottom = (18.0 if compact else 50.0) + pad
	p.add_theme_stylebox_override("panel", sb)
	return p


func _mk_gunungan(h: float) -> TextureRect:
	# gold wayang gunungan ornament above panel titles
	var t: TextureRect = TextureRect.new()
	t.texture = TEX_GUNUNGAN
	t.custom_minimum_size = Vector2(h, h)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	t.modulate = Color(SONGKET_GOLD, 0.85)
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return t


func _mk_divider() -> Control:
	# songket band separator
	var d: HSeparator = HSeparator.new()
	var sb: StyleBoxTexture = HT.songket_box(Color(SONGKET_GOLD, 0.85))
	sb.content_margin_top = 4.0
	sb.content_margin_bottom = 4.0
	d.add_theme_stylebox_override("separator", sb)
	d.add_theme_constant_override("separation", 8)
	return d


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
	lbl.custom_minimum_size = Vector2(64.0, 0.0)
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	lbl.mouse_filter = Control.MOUSE_FILTER_STOP # labels ignore the mouse by default — needed for tooltips
	row.add_child(lbl)
	var bar: ProgressBar = ProgressBar.new()
	bar.max_value = 1.0
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(100.0, 14.0)
	bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	bar.add_theme_stylebox_override("background", HT.groove_box()) # recessed carved groove
	# layered: bottom bar shows the forged total in a brighter tint; the overlay
	# draws the base on top, so the bright sliver past it reads as forged bonus
	bar.add_theme_stylebox_override("fill", HT.songket_box(fill_color.lightened(0.5) if layered else fill_color))
	var over: ProgressBar = null
	if layered:
		over = ProgressBar.new()
		over.max_value = 1.0
		over.show_percentage = false
		over.set_anchors_preset(Control.PRESET_FULL_RECT)
		over.mouse_filter = Control.MOUSE_FILTER_IGNORE
		over.add_theme_stylebox_override("background", StyleBoxEmpty.new())
		over.add_theme_stylebox_override("fill", HT.songket_box(fill_color))
		bar.add_child(over)
	row.add_child(bar)
	parent.add_child(row)
	return {"label": lbl, "bar": bar, "over": over}


func _build_ui() -> void:
	# always-on vignette under every panel: frames the arena, hides banding at the edges
	var vignette: TextureRect = TextureRect.new()
	vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var vgrad: Gradient = Gradient.new()
	vgrad.set_color(0, Color(0.0, 0.0, 0.0, 0.0))
	vgrad.set_color(1, Color(0.0, 0.0, 0.0, 0.38))
	vgrad.add_point(0.62, Color(0.0, 0.0, 0.0, 0.0))
	var vgt: GradientTexture2D = GradientTexture2D.new()
	vgt.gradient = vgrad
	vgt.fill = GradientTexture2D.FILL_RADIAL
	vgt.fill_from = Vector2(0.5, 0.5)
	vgt.fill_to = Vector2(1.15, 0.5)
	vignette.texture = vgt
	vignette.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ui.add_child(vignette)

	hud = Control.new()
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.visible = false
	ui.add_child(hud)

	# ---- battle HUD at 1280x720; the ring (x 365-915, y 145-635) stays clear for the tops
	# top corners: fighting-game spin bars in the side colours (you, and the nearest rival)
	player_gauge = FightBar.new()
	player_gauge.position = Vector2(20.0, 12.0)
	player_gauge.side_color = HT.SIDE_YOU
	hud.add_child(player_gauge)
	foe_gauge = FightBar.new()
	foe_gauge.rtl = true
	foe_gauge.side_color = HT.SIDE_FOE
	foe_gauge.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	foe_gauge.offset_left = -470.0
	foe_gauge.offset_right = -20.0
	foe_gauge.offset_top = 12.0
	foe_gauge.offset_bottom = 64.0
	hud.add_child(foe_gauge)
	# FFA rivals beyond the one on the foe bar: one glyph row each under it
	for i: int in 3:
		var row: SquadRow = SquadRow.new()
		row.set_anchors_preset(Control.PRESET_TOP_RIGHT)
		row.offset_left = -470.0
		row.offset_right = -20.0
		row.offset_top = 70.0 + 22.0 * i
		row.offset_bottom = 90.0 + 22.0 * i
		row.visible = false
		hud.add_child(row)
		hud_rows.append(row)

	# centre medallion (x 540-740, y 6-120): Kurland clock, best-of-3 pips, duel line / leader
	hud_medallion = Panel.new()
	var msb: StyleBoxFlat = _hud_plate(Color(HT.SONGKET_GOLD, 0.8))
	msb.set_border_width_all(2)
	msb.corner_radius_bottom_left = 44
	msb.corner_radius_bottom_right = 44
	hud_medallion.add_theme_stylebox_override("panel", msb)
	hud_medallion.set_anchors_preset(Control.PRESET_CENTER_TOP)
	hud_medallion.offset_left = -100.0
	hud_medallion.offset_right = 100.0
	hud_medallion.offset_top = 6.0
	hud_medallion.offset_bottom = 120.0
	hud_medallion.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud_medallion.visible = false
	hud.add_child(hud_medallion)
	var band: Panel = Panel.new() # songket weave along the top edge
	band.add_theme_stylebox_override("panel", HT.songket_box(Color(HT.SONGKET_GOLD, 0.9)))
	band.set_anchors_preset(Control.PRESET_TOP_WIDE)
	band.offset_left = 6.0
	band.offset_right = -6.0
	band.offset_top = 3.0
	band.offset_bottom = 9.0
	band.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud_medallion.add_child(band)
	hud_clock = _mk_title("90", 40, HT.TEXT_COLOR)
	hud_clock.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hud_clock.set_anchors_preset(Control.PRESET_TOP_WIDE)
	hud_clock.offset_top = 8.0
	hud_clock.offset_bottom = 54.0
	hud_clock.pivot_offset = Vector2(100.0, 23.0)
	hud_medallion.add_child(hud_clock)
	score_row = HBoxContainer.new()
	score_row.alignment = BoxContainer.ALIGNMENT_CENTER
	score_row.add_theme_constant_override("separation", 18)
	score_row.set_anchors_preset(Control.PRESET_TOP_WIDE)
	score_row.offset_top = 56.0
	score_row.offset_bottom = 74.0
	score_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	my_pips = ScorePips.new()
	my_pips.color = HT.SIDE_YOU
	score_row.add_child(my_pips)
	opp_pips = ScorePips.new()
	opp_pips.color = HT.SIDE_FOE
	opp_pips.rtl = true # mirrored so both scores grow toward the center
	score_row.add_child(opp_pips)
	hud_medallion.add_child(score_row)
	duel_label = _mk_label("", 14, HT.CREAM_MUTED)
	hud_lead = _mk_label("", 14, HT.SONGKET_GOLD)
	for l: Label in [duel_label, hud_lead]:
		l.set_anchors_preset(Control.PRESET_TOP_WIDE)
		l.offset_top = 76.0
		l.offset_bottom = 98.0
		l.clip_text = true
		hud_medallion.add_child(l)
	hud_lead.visible = false

	wind_meter = WindMeter.new()
	wind_meter.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	wind_meter.offset_left = 46.0
	wind_meter.offset_right = 110.0 # widened for the coil bulge
	wind_meter.offset_top = -320.0
	wind_meter.offset_bottom = -50.0
	wind_meter.visible = false
	hud.add_child(wind_meter)

	# wind card beside the meter (x 120-360, y 580-670): WIND countdown + how to launch
	var card: PanelContainer = PanelContainer.new()
	card.add_theme_stylebox_override("panel", _hud_plate())
	card.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	card.offset_left = 120.0
	card.offset_right = 360.0
	card.offset_top = -140.0
	card.offset_bottom = -50.0
	card.grow_vertical = Control.GROW_DIRECTION_BEGIN
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.visible = false
	hud.add_child(card)
	var wv: VBoxContainer = VBoxContainer.new()
	wv.alignment = BoxContainer.ALIGNMENT_CENTER
	wv.add_theme_constant_override("separation", 0)
	wv.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(wv)
	wind_count = _mk_title("", 22, HT.SONGKET_GOLD)
	wind_text = _mk_label("", 14)
	for l: Label in [wind_count, wind_text]:
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		wv.add_child(l)
	wind_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	wind_hint = card

	# key-cap controls strip (x 330-950, y 674-712): the first 10 s of each round's battle
	var strip: KeyStrip = KeyStrip.new()
	strip.game = self
	strip.add_theme_stylebox_override("panel", _hud_plate(Color(HT.SONGKET_GOLD, 0.35)))
	strip.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	strip.offset_left = -310.0
	strip.offset_right = 310.0
	strip.offset_top = -46.0
	strip.offset_bottom = -8.0
	strip.grow_horizontal = Control.GROW_DIRECTION_BOTH
	strip.visible = false
	hud.add_child(strip)
	var keys: HBoxContainer = HBoxContainer.new()
	keys.alignment = BoxContainer.ALIGNMENT_CENTER
	keys.add_theme_constant_override("separation", 3)
	keys.mouse_filter = Control.MOUSE_FILTER_IGNORE
	strip.add_child(keys)
	var cap_box: StyleBoxFlat = StyleBoxFlat.new() # key-cap: dark wood, gold rim, a thicker lip
	cap_box.bg_color = Color(HT.WOOD_EDGE, 0.96)
	cap_box.border_color = Color(HT.SONGKET_GOLD, 0.85)
	cap_box.set_border_width_all(1)
	cap_box.border_width_bottom = 2
	cap_box.set_corner_radius_all(4)
	cap_box.content_margin_left = 5.0
	cap_box.content_margin_right = 5.0
	cap_box.content_margin_bottom = 1.0
	for i: int in 7:
		if i > 0:
			var gap: Control = Control.new()
			gap.custom_minimum_size = Vector2(5.0, 0.0)
			gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
			keys.add_child(gap)
		var chip: PanelContainer = PanelContainer.new()
		chip.add_theme_stylebox_override("panel", cap_box)
		chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var cap: Label = _mk_label("", 13, HT.SONGKET_GOLD)
		chip.add_child(cap)
		keys.add_child(chip)
		var verb: Label = _mk_label("", 14)
		keys.add_child(verb)
		_strip_labels.append(cap)
		_strip_labels.append(verb)
	battle_hint = strip

	menu_notice = _mk_label("", 15, DANGER)
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
	_build_cutscene_panel()
	_build_round_panel()
	_build_over_panel()


func _hud_plate(border: Color = Color(HT.SONGKET_GOLD, 0.55)) -> StyleBoxFlat:
	# the one small-HUD surface: dark carved wood with a thin songket-gold rim
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = Color(HT.WOOD_EDGE, 0.86)
	sb.border_color = border
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(6)
	sb.shadow_color = Color(0.0, 0.0, 0.0, 0.3)
	sb.shadow_size = 4
	sb.content_margin_left = 12.0
	sb.content_margin_right = 12.0
	sb.content_margin_top = 4.0
	sb.content_margin_bottom = 5.0
	return sb


func _build_ready_panel() -> void:
	# the title is a dalang's screen: the name over a swaying gunungan shadow, a carved
	# menu plaque (primary gold / secondary amber / tertiary dark), campaign progress and
	# rotating heritage facts, while the showcase top spins in the ring on the right
	ready_panel = Control.new()
	ready_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	ready_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ready_panel.visible = false
	ui.add_child(ready_panel)
	_all_panels.append(ready_panel)
	var col: VBoxContainer = VBoxContainer.new()
	col.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	col.offset_left = 64.0
	col.offset_right = 504.0
	col.offset_top = 20.0
	col.offset_bottom = -20.0
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_theme_constant_override("separation", 10)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ready_panel.add_child(col)

	var title_block: Control = Control.new()
	title_block.custom_minimum_size = Vector2(440.0, 176.0)
	title_block.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(title_block)
	ready_gunungan = TextureRect.new() # shadow puppet: the black cut-out, half-lit through the kelir
	var gun_path: String = "res://assets/wayang/wayang_gunungan.png"
	ready_gunungan.texture = load(gun_path) as Texture2D if ResourceLoader.exists(gun_path) else TEX_GUNUNGAN
	ready_gunungan.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ready_gunungan.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ready_gunungan.modulate = Color(1.0, 1.0, 1.0, 0.62)
	ready_gunungan.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ready_gunungan.size = Vector2(290.0, 290.0)
	ready_gunungan.position = Vector2(220.0, 88.0) - ready_gunungan.size * 0.5
	ready_gunungan.pivot_offset = ready_gunungan.size * 0.5
	ready_gunungan.rotation = deg_to_rad(-4.0)
	title_block.add_child(ready_gunungan)
	ready_title = _mk_title("GASING\nPANGKAH", 78)
	ready_title.add_theme_constant_override("outline_size", 12) # bigger outline on the hero title
	ready_title.add_theme_constant_override("shadow_offset_y", 5)
	ready_title.add_theme_constant_override("line_spacing", -22)
	ready_title.set_anchors_preset(Control.PRESET_FULL_RECT)
	ready_title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	ready_title.pivot_offset = Vector2(220.0, 88.0) # the block's centre
	title_block.add_child(ready_title)
	ready_heritage = _mk_label("", 17)
	ready_heritage.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ready_heritage.custom_minimum_size = Vector2(420.0, 0.0)
	col.add_child(ready_heritage)

	var plaque: PanelContainer = _mk_panel_box(true, 6.0)
	plaque.self_modulate = Color(1.0, 1.0, 1.0, 0.86) # translucent carved plaque: the arena glows through
	plaque.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	col.add_child(plaque)
	var menu_col: VBoxContainer = VBoxContainer.new()
	menu_col.add_theme_constant_override("separation", 9)
	menu_col.custom_minimum_size = Vector2(330.0, 0.0)
	plaque.add_child(menu_col)
	sp_button = _mk_button("", PLAYER_COLOR) # primary: gold
	sp_button.add_theme_font_size_override("font_size", 22)
	sp_button.custom_minimum_size.y = 52.0
	sp_button.pressed.connect(_on_single_player_pressed)
	menu_col.add_child(sp_button)
	endless_button = _mk_button("", WOOD_AMBER) # secondary: amber
	endless_button.pressed.connect(_on_endless_pressed)
	mp_button = _mk_button("", WOOD_AMBER)
	mp_button.pressed.connect(_on_multiplayer_pressed)
	howto_button = _mk_button("", WOOD_AMBER)
	howto_button.pressed.connect(func() -> void: menus.show_info("howto"))
	settings_button = _mk_button("", WOOD_AMBER)
	settings_button.pressed.connect(func() -> void: menus.show_info("settings"))
	credits_button = _mk_button("", WOOD_DARK, true) # tertiary: dark wood
	credits_button.pressed.connect(func() -> void: menus.show_info("credits"))
	quit_button = _mk_button("", WOOD_DARK, true)
	quit_button.pressed.connect(_on_quit_pressed)
	for row: Array in [[endless_button], [mp_button], [howto_button, settings_button], [credits_button, quit_button]]:
		var h: HBoxContainer = HBoxContainer.new()
		h.add_theme_constant_override("separation", 9)
		menu_col.add_child(h)
		for b: Button in row:
			b.add_theme_font_size_override("font_size", 18 if row.size() == 1 else 16)
			b.custom_minimum_size.y = 42.0 if row.size() == 1 else 38.0
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			h.add_child(b)

	var progress: VBoxContainer = VBoxContainer.new()
	progress.add_theme_constant_override("separation", 3)
	col.add_child(progress)
	ready_progress_pips = ScorePips.new()
	ready_progress_pips.color = PLAYER_COLOR
	ready_progress_pips.set_total(MASTERS.size())
	ready_progress_pips.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	progress.add_child(ready_progress_pips)
	ready_progress = _mk_label("", 14, CREAM_MUTED)
	progress.add_child(ready_progress)
	ready_prompt = _mk_label("", 15)
	ready_prompt.add_theme_constant_override("outline_size", 4) # sits right on the busy 3D backdrop
	col.add_child(ready_prompt)
	var pulse: Tween = create_tween().set_loops() # a gentle breath that never drops below legible
	pulse.tween_property(ready_prompt, "modulate:a", 0.6, 0.7)
	pulse.tween_property(ready_prompt, "modulate:a", 1.0, 0.7)
	var sway: Tween = create_tween().set_loops() # the dalang rocks the gunungan
	sway.tween_property(ready_gunungan, "rotation", deg_to_rad(4.0), 2.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	sway.tween_property(ready_gunungan, "rotation", deg_to_rad(-4.0), 2.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

	var lang_row: HBoxContainer = HBoxContainer.new()
	lang_row.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	lang_row.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	lang_row.offset_left = -28.0
	lang_row.offset_right = -28.0
	lang_row.offset_top = 22.0
	lang_row.add_theme_constant_override("separation", 8)
	ready_panel.add_child(lang_row)
	for entry: Array in [["en", "ENGLISH"], ["ms", "BAHASA MELAYU"]]:
		var code: String = entry[0]
		var b: Button = _mk_button(entry[1], WOOD_DARK, true)
		b.add_theme_font_size_override("font_size", 14)
		b.pressed.connect(_on_lang_pressed.bind(code))
		lang_row.add_child(b)
		lang_buttons[code] = b

	# "did you know?" card: a heritage fact that turns over every few seconds
	var fact_card: PanelContainer = _mk_panel_box(true, 2.0)
	fact_card.self_modulate = Color(1.0, 1.0, 1.0, 0.86)
	fact_card.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	fact_card.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	fact_card.grow_vertical = Control.GROW_DIRECTION_BEGIN
	fact_card.offset_left = -28.0
	fact_card.offset_right = -28.0
	fact_card.offset_top = -24.0
	fact_card.offset_bottom = -24.0
	fact_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ready_panel.add_child(fact_card)
	var fv: VBoxContainer = VBoxContainer.new()
	fv.add_theme_constant_override("separation", 2)
	fact_card.add_child(fv)
	var head: HBoxContainer = HBoxContainer.new()
	head.add_theme_constant_override("separation", 6)
	head.add_child(_mk_gunungan(22.0))
	ready_fact_head = _mk_title("", 20)
	head.add_child(ready_fact_head)
	fv.add_child(head)
	ready_fact = _mk_label("", 15)
	ready_fact.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	ready_fact.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	ready_fact.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ready_fact.custom_minimum_size = Vector2(400.0, 64.0) # three lines, so the card never jumps
	fv.add_child(ready_fact)
	_fact_idx = _rng.randi_range(0, TITLE_FACTS - 1)
	var facts: Tween = create_tween().set_loops()
	facts.tween_interval(7.0)
	facts.tween_property(ready_fact, "modulate:a", 0.0, 0.35)
	facts.tween_callback(_next_fact)
	facts.tween_property(ready_fact, "modulate:a", 1.0, 0.35)


func _next_fact() -> void:
	_fact_idx = (_fact_idx + 1) % TITLE_FACTS
	ready_fact.text = _t("fact_%d" % (_fact_idx + 1))


func _build_mp_panel() -> void:
	# a carved page like the menus overlay: Steam and LAN side by side as slim cards,
	# each led by its amber HOST plaque, with the dark BACK plaque below
	mp_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box()
	mp_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	box.add_child(v)
	v.add_child(_mk_gunungan(36.0))
	mp_title = _mk_title("", 36)
	v.add_child(mp_title)
	v.add_child(_mk_divider())
	var cards: HBoxContainer = HBoxContainer.new()
	cards.add_theme_constant_override("separation", 16)
	v.add_child(cards)
	var cols: Array[VBoxContainer] = []
	for i: int in 2:
		var card: PanelContainer = _mk_panel_box(true, 6.0)
		cards.add_child(card)
		var cv: VBoxContainer = VBoxContainer.new()
		cv.add_theme_constant_override("separation", 10)
		cv.custom_minimum_size = Vector2(320.0, 0.0)
		card.add_child(cv)
		cols.append(cv)
	mp_steam_header_label = _mk_title("", 22)
	cols[0].add_child(mp_steam_header_label)
	host_steam_button = _mk_button("", WOOD_AMBER)
	host_steam_button.pressed.connect(_on_host_steam_pressed)
	cols[0].add_child(host_steam_button)
	steam_offline_label = _mk_label("", 13, DANGER)
	steam_offline_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	steam_offline_label.visible = false
	cols[0].add_child(steam_offline_label)
	steam_join_hint_label = _mk_label("", 13, CREAM_MUTED)
	steam_join_hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cols[0].add_child(steam_join_hint_label)
	mp_code_label = _mk_label("", 14)
	mp_code_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	cols[0].add_child(mp_code_label)
	var code_row: HBoxContainer = HBoxContainer.new()
	code_row.add_theme_constant_override("separation", 8)
	join_code_edit = _mk_line_edit("ABC123")
	join_code_edit.custom_minimum_size.x = 150.0
	join_code_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	join_code_edit.text_submitted.connect(func(_txt: String) -> void: _on_join_code_pressed())
	code_row.add_child(join_code_edit)
	join_code_button = _mk_button("", WOOD_AMBER)
	join_code_button.pressed.connect(_on_join_code_pressed)
	code_row.add_child(join_code_button)
	cols[0].add_child(code_row)
	mp_lan_header_label = _mk_title("", 22)
	cols[1].add_child(mp_lan_header_label)
	host_lan_button = _mk_button("", WOOD_AMBER)
	host_lan_button.pressed.connect(_on_host_lan_pressed)
	cols[1].add_child(host_lan_button)
	lan_ip_label = _mk_label("", 14)
	lan_ip_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	cols[1].add_child(lan_ip_label)
	var join_row: HBoxContainer = HBoxContainer.new()
	join_row.add_theme_constant_override("separation", 8)
	lan_ip_edit = _mk_line_edit("127.0.0.1")
	lan_ip_edit.text = "127.0.0.1"
	lan_ip_edit.custom_minimum_size.x = 140.0
	lan_ip_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lan_ip_edit.text_submitted.connect(func(_txt: String) -> void: _on_join_lan_pressed())
	join_row.add_child(lan_ip_edit)
	join_lan_button = _mk_button("", WOOD_AMBER)
	join_lan_button.pressed.connect(_on_join_lan_pressed)
	join_row.add_child(join_lan_button)
	cols[1].add_child(join_row)
	mp_back_button = _mk_button("", WOOD_DARK, true)
	mp_back_button.custom_minimum_size = Vector2(200.0, 0.0)
	mp_back_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	mp_back_button.pressed.connect(_on_mp_back_pressed)
	v.add_child(mp_back_button)


func _build_wait_panel() -> void:
	# the lobby card, headed like every page (gunungan, Kurland title, songket band), then
	# INVITE / CANCEL; arena_match.build_ui slots its roster + START above CANCEL in this VBox
	wait_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box(true, 10.0) # short panel: slim frame, no tall art to squash
	wait_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	v.custom_minimum_size = Vector2(440.0, 0.0)
	box.add_child(v)
	v.add_child(_mk_gunungan(40.0))
	wait_title = _mk_title("", 28)
	v.add_child(wait_title)
	v.add_child(_mk_divider())
	wait_info = _mk_label("", 15)
	v.add_child(wait_info)
	invite_button = _mk_button("", WOOD_AMBER)
	invite_button.visible = false
	invite_button.pressed.connect(_on_invite_friend_pressed)
	var iv_wrap: CenterContainer = CenterContainer.new()
	iv_wrap.add_child(invite_button)
	v.add_child(iv_wrap)
	wait_cancel_button = _mk_button("", WOOD_DARK, true)
	wait_cancel_button.custom_minimum_size = Vector2(200.0, 0.0) # same plaque width as the MP page's BACK
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
	# the recessed carved slot, cream text and gold focus rim come from the heritage theme's LineEdit
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
	host_steam_button.disabled = not steam_ok # the disabled plaque style already dims it
	steam_offline_label.visible = not steam_ok
	join_code_button.disabled = not steam_ok
	join_code_edit.editable = steam_ok
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
	endless_mode = false
	duel_index = campaign_index # CONTINUE resumes the saved campaign
	_enter_state(State.CRAFT)


func _on_endless_pressed() -> void:
	endless_mode = true
	_reset_run()
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
		_set_wait_status(_t("waiting_opponent"), _t("share_code") % Online.lobby_code + "\n" + _t("invite_hint"), true)
		arena.refresh_lobby()
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
		arena.refresh_lobby()
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
	# via player_connected (count 2) and failure via connection_failed. ENet can
	# retry silently for a long time, so give up after 8 s.
	_show_menu_screen(MenuScreen.WAIT)
	_set_wait_status(_t("connecting"), "", false)
	_join_token += 1
	get_tree().create_timer(8.0).timeout.connect(_on_join_timeout.bind(_join_token))


func _on_join_timeout(token: int) -> void:
	if token != _join_token or state != State.READY or menu_screen != MenuScreen.WAIT or Online.is_host or not Online.players.is_empty():
		return
	Online.leave_lobby()
	_show_menu_screen(MenuScreen.MP)
	_show_menu_notice(_t("err_join_failed"))


func _on_join_code_pressed() -> void:
	if not Online.steam_ready:
		_show_menu_notice(_t("steam_offline"))
		return
	var code: String = join_code_edit.text.strip_edges()
	if code.is_empty():
		return
	host_steam_button.disabled = true
	host_lan_button.disabled = true
	join_lan_button.disabled = true
	join_code_button.disabled = true
	_show_menu_screen(MenuScreen.WAIT)
	_set_wait_status(_t("connecting"), "", false)
	var err: int = await Online.find_lobby_by_code(code)
	# SUCCESS is handled by joined_lobby -> _on_mp_joined_lobby (WAIT) then player_connected;
	# only the failure path needs handling here.
	if err != Online.ErrorCodes.SUCCESS:
		_show_menu_screen(MenuScreen.MP)
		_show_menu_notice(_t("err_join_steam"))


func _on_mp_cancel_pressed() -> void:
	Online.leave_lobby()
	_show_menu_screen(MenuScreen.MP)


func _build_craft_panel() -> void:
	# fighter-select: the center stays clear so the arena and the spinning hero
	# top show through; squad header on top, next-opponent card top-left, coin
	# chip top-right, roster arrows + lacquer palette at the sides, stats + forge
	# sheet along the bottom
	craft_panel = Control.new()
	craft_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	craft_panel.visible = false
	craft_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(craft_panel)
	_all_panels.append(craft_panel)

	var header_wrap: CenterContainer = CenterContainer.new()
	header_wrap.set_anchors_preset(Control.PRESET_TOP_WIDE)
	header_wrap.offset_top = 8.0
	header_wrap.offset_bottom = 124.0
	craft_panel.add_child(header_wrap)
	var header: PanelContainer = _mk_panel_box(true, 2.0)
	craft_header = header
	header_wrap.add_child(header)
	var hv: VBoxContainer = VBoxContainer.new()
	hv.add_theme_constant_override("separation", 2)
	header.add_child(hv)
	craft_title = _mk_title("", 26)
	hv.add_child(craft_title)
	craft_duel_label = _mk_label("", 16) # MP only; SP shows the next-opponent card
	hv.add_child(craft_duel_label)
	craft_sub = _mk_label("", 13, CREAM_MUTED)
	craft_sub.visible = false
	hv.add_child(craft_sub)
	var squad_row: HBoxContainer = HBoxContainer.new()
	squad_row.alignment = BoxContainer.ALIGNMENT_CENTER
	squad_row.add_theme_constant_override("separation", 8)
	hv.add_child(squad_row)
	for slot: int in 3:
		var slot_button: Button = _craft_toggle(14)
		slot_button.name = "LoadoutSlot%d" % (slot + 1)
		slot_button.custom_minimum_size = Vector2(118.0, 0.0)
		slot_button.pressed.connect(_on_loadout_slot_pressed.bind(slot))
		squad_row.add_child(slot_button)
		craft_loadout_buttons.append(slot_button)
	craft_slot_hint = _mk_label("", 13, CREAM_MUTED) # "Slot 2 ← Cik Ros": where browsing lands
	hv.add_child(craft_slot_hint)

	# next opponent (SP): the master's wayang on a little lamp-lit kelir, then
	# the difficulty plaques — difficulty is about them, so it lives on their card
	craft_opp_card = _mk_panel_box(true)
	craft_opp_card.position = Vector2(16.0, 8.0)
	craft_panel.add_child(craft_opp_card)
	var ov: VBoxContainer = VBoxContainer.new()
	ov.add_theme_constant_override("separation", 6)
	craft_opp_card.add_child(ov)
	craft_opp_caption = _mk_label("", 12, CREAM_MUTED)
	craft_opp_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	ov.add_child(craft_opp_caption)
	var oh: HBoxContainer = HBoxContainer.new()
	oh.add_theme_constant_override("separation", 10)
	ov.add_child(oh)
	var opp_kelir: TextureRect = TextureRect.new()
	opp_kelir.texture = _kelir_texture()
	opp_kelir.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	opp_kelir.custom_minimum_size = Vector2(62.0, 80.0)
	opp_kelir.mouse_filter = Control.MOUSE_FILTER_IGNORE
	oh.add_child(opp_kelir)
	craft_opp_puppet = TextureRect.new()
	craft_opp_puppet.set_anchors_preset(Control.PRESET_FULL_RECT)
	craft_opp_puppet.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	craft_opp_puppet.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	craft_opp_puppet.modulate = HT.INK # shadow against the lamp
	craft_opp_puppet.mouse_filter = Control.MOUSE_FILTER_IGNORE
	opp_kelir.add_child(craft_opp_puppet)
	var names: VBoxContainer = VBoxContainer.new()
	names.alignment = BoxContainer.ALIGNMENT_CENTER
	names.add_theme_constant_override("separation", 0)
	oh.add_child(names)
	craft_opp_name = _mk_title("", 22)
	craft_opp_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	names.add_child(craft_opp_name)
	craft_opp_region = _mk_label("", 14, CREAM_MUTED)
	craft_opp_region.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	names.add_child(craft_opp_region)
	craft_opp_duel = _mk_label("", 14)
	craft_opp_duel.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	names.add_child(craft_opp_duel)
	var diff_row: HBoxContainer = HBoxContainer.new()
	diff_row.add_theme_constant_override("separation", 4)
	ov.add_child(diff_row)
	for i: int in 3:
		var diff_button: Button = _craft_toggle(13)
		diff_button.name = "Difficulty%d" % i
		diff_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		diff_button.pressed.connect(_on_difficulty_selected.bind(i))
		diff_row.add_child(diff_button)
		craft_difficulty.append(diff_button)

	# coin chip (SP): a drawn pitis coin + the purse in Kurland numerals
	var chip: PanelContainer = _mk_panel_box(true)
	craft_coin_chip = chip
	chip.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	chip.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	chip.offset_left = -16.0
	chip.offset_right = -16.0
	chip.offset_top = 8.0
	craft_panel.add_child(chip)
	var ch: HBoxContainer = HBoxContainer.new()
	ch.add_theme_constant_override("separation", 8)
	chip.add_child(ch)
	ch.add_child(_coin_icon(26.0))
	craft_mats_hint = _mk_title("", 24) # the purse amount
	ch.add_child(craft_mats_hint)
	var unit: Label = _mk_label("duit", 14, CREAM_MUTED)
	unit.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	ch.add_child(unit)

	craft_prev_button = _mk_button("<", WOOD_DARK, true)
	craft_next_button = _mk_button(">", WOOD_DARK, true)
	for arrow: Button in [craft_prev_button, craft_next_button]:
		arrow.add_theme_font_size_override("font_size", 40)
		arrow.custom_minimum_size = Vector2(64.0, 96.0)
		arrow.anchor_top = 0.36
		arrow.anchor_bottom = 0.36
		arrow.offset_top = -48.0
		arrow.offset_bottom = 48.0
		craft_panel.add_child(arrow)
	craft_prev_button.offset_left = 28.0
	craft_prev_button.offset_right = 92.0
	craft_next_button.anchor_left = 1.0
	craft_next_button.anchor_right = 1.0
	craft_next_button.offset_left = -92.0
	craft_next_button.offset_right = -28.0
	craft_prev_button.pressed.connect(_craft_cycle.bind(-1))
	craft_next_button.pressed.connect(_craft_cycle.bind(1))

	# bottom sheet auto-heights from content: anchored to the bottom edge and
	# grown upward — kept to 4 dense rows so the spinning preview stays visible
	var sheet: PanelContainer = _mk_panel_box(true, 2.0)
	craft_sheet = sheet
	sheet.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	sheet.offset_left = 80.0
	sheet.offset_right = -80.0
	sheet.offset_top = -12.0
	sheet.offset_bottom = -12.0
	sheet.grow_vertical = Control.GROW_DIRECTION_BEGIN
	craft_panel.add_child(sheet)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	sheet.add_child(v)

	# row 1: name + roster counter
	var name_row: HBoxContainer = HBoxContainer.new()
	name_row.alignment = BoxContainer.ALIGNMENT_CENTER
	name_row.add_theme_constant_override("separation", 10)
	v.add_child(name_row)
	craft_name_label = _mk_title("", 26)
	name_row.add_child(craft_name_label)
	craft_counter_label = _mk_label("", 13, CREAM_MUTED)
	craft_counter_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	name_row.add_child(craft_counter_label)

	# row 2: role / lock status + level on their own line
	var info_row: HBoxContainer = HBoxContainer.new()
	info_row.alignment = BoxContainer.ALIGNMENT_CENTER
	info_row.add_theme_constant_override("separation", 18)
	v.add_child(info_row)
	craft_status_label = _mk_label("", 15)
	info_row.add_child(craft_status_label)
	craft_level_label = _mk_label("", 15, PLAYER_COLOR)
	craft_level_label.name = "StyleLevel"
	info_row.add_child(craft_level_label)

	# row 3: stat bars, each with its number
	var stats_row: HBoxContainer = HBoxContainer.new()
	stats_row.alignment = BoxContainer.ALIGNMENT_CENTER
	stats_row.add_theme_constant_override("separation", 30)
	v.add_child(stats_row)
	craft_stat_rows = [
		_mk_stat_row(stats_row, COPPER, true),
		_mk_stat_row(stats_row, HT.ENERGY_BLUE, true),
		_mk_stat_row(stats_row, PANDAN, true),
	]
	for r: Dictionary in craft_stat_rows:
		(r.label as Label).add_theme_font_size_override("font_size", 14)
		(r.bar as ProgressBar).custom_minimum_size = Vector2(172.0, 14.0)
		var num: Label = _mk_title("", 18, TEXT_COLOR)
		num.add_theme_constant_override("outline_size", 4)
		num.custom_minimum_size = Vector2(40.0, 0.0)
		num.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		(r.bar as Control).get_parent().add_child(num)
		r["value"] = num

	# row 4: forge — [material | BUY] per material, captioned with what it raises
	var forge_box: HBoxContainer = HBoxContainer.new()
	forge_box.alignment = BoxContainer.ALIGNMENT_CENTER
	forge_box.add_theme_constant_override("separation", 22)
	v.add_child(forge_box)
	craft_forge_box = forge_box
	# Balance's material sits under the Balance column; both Mass materials lead from the left
	for mat_id: String in ["merbau", "besi", "kemuning"]:
		var mat_group: VBoxContainer = VBoxContainer.new()
		mat_group.add_theme_constant_override("separation", 0)
		forge_box.add_child(mat_group)
		var mat_col: HBoxContainer = HBoxContainer.new()
		mat_col.add_theme_constant_override("separation", 6)
		mat_group.add_child(mat_col)
		var mb: Button = _mk_button("", WOOD_DARK, true)
		mb.icon = load("res://assets/icon_%s.png" % mat_id)
		mb.add_theme_constant_override("icon_max_width", 26)
		mb.add_theme_constant_override("h_separation", 8)
		mb.add_theme_font_size_override("font_size", 14)
		mb.pressed.connect(_on_material_pressed.bind(mat_id))
		mat_col.add_child(mb)
		material_buttons[mat_id] = mb
		var buy: Button = _mk_button("", WOOD_AMBER)
		buy.add_theme_font_size_override("font_size", 12)
		buy.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		buy.pressed.connect(_on_material_bought.bind(mat_id))
		mat_col.add_child(buy)
		material_buy_buttons[mat_id] = buy
		var gain: Label = _mk_label("", 13, CREAM_MUTED)
		mat_group.add_child(gain)
		craft_forge_captions[mat_id] = gain

	# lacquer palette: a small card beside the preview it recolours
	var palette: PanelContainer = _mk_panel_box(true)
	accent_row = palette
	palette.anchor_left = 1.0
	palette.anchor_right = 1.0
	palette.anchor_top = 0.36
	palette.anchor_bottom = 0.36
	palette.offset_top = 64.0 # just under the > arrow
	palette.offset_right = -24.0
	palette.offset_left = -24.0
	palette.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	craft_panel.add_child(palette)
	var pv: VBoxContainer = VBoxContainer.new()
	pv.add_theme_constant_override("separation", 8)
	palette.add_child(pv)
	accent_label = _mk_label("", 12, CREAM_MUTED)
	pv.add_child(accent_label)
	var grid: GridContainer = GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)
	pv.add_child(grid)
	for c: Color in ACCENT_CHOICES:
		var sw: Button = Button.new()
		sw.custom_minimum_size = Vector2(26.0, 26.0)
		sw.focus_mode = Control.FOCUS_NONE
		var sb: StyleBoxFlat = StyleBoxFlat.new()
		sb.bg_color = c
		sb.set_corner_radius_all(13)
		sw.add_theme_stylebox_override("normal", sb)
		var sbh: StyleBoxFlat = sb.duplicate()
		sbh.bg_color = c.lightened(0.25)
		sw.add_theme_stylebox_override("hover", sbh)
		sw.add_theme_stylebox_override("pressed", sb)
		sw.pressed.connect(_on_any_button_pressed)
		sw.pressed.connect(_on_accent_selected.bind(c))
		grid.add_child(sw)
		accent_swatches.append(sw)

	craft_opp_status = _mk_label("", 13, FOE_COLOR)
	craft_opp_status.visible = false
	v.add_child(craft_opp_status)

	# row 5: BACK — info (expands, centered) — FIGHT
	craft_info = _mk_label("", 14, TEXT_COLOR)
	craft_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	craft_info.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	fight_button = _mk_button("", PLAYER_COLOR)
	fight_button.add_theme_font_size_override("font_size", 20)
	fight_button.pressed.connect(_on_fight_pressed)
	craft_back_button = _mk_button("", WOOD_DARK, true)
	craft_back_button.pressed.connect(_leave_to_title) # SP: title, campaign kept; MP: leave lobby -> title
	var btn_row: HBoxContainer = HBoxContainer.new()
	btn_row.add_theme_constant_override("separation", 16)
	btn_row.add_child(craft_back_button)
	btn_row.add_child(craft_info)
	btn_row.add_child(fight_button)
	v.add_child(btn_row)


func _craft_toggle(font_size: int) -> Button:
	# dark plaque that turns amber while selected (loadout slots, difficulty)
	var b: Button = _mk_button("", WOOD_DARK, true)
	b.toggle_mode = true
	b.add_theme_font_size_override("font_size", font_size)
	var on: StyleBoxTexture = HT.plaque_box(WOOD_AMBER)
	b.add_theme_stylebox_override("pressed", on)
	b.add_theme_stylebox_override("hover_pressed", on)
	b.add_theme_color_override("font_pressed_color", HT.INK)
	b.add_theme_color_override("font_hover_pressed_color", HT.INK)
	return b


func _kelir_texture() -> GradientTexture2D:
	# the kelir, the dalang's lamp-lit cloth: pale gold at the flame, amber, then carved-wood dark
	# (cutscene, curtain wipe, next-opponent card and the masters row all share it)
	var grad: Gradient = Gradient.new()
	grad.set_color(0, SONGKET_GOLD.lerp(TEXT_COLOR, 0.5))
	grad.set_color(1, WOOD_EDGE)
	grad.add_point(0.45, WOOD_AMBER)
	var gt: GradientTexture2D = GradientTexture2D.new()
	gt.gradient = grad
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.42)
	gt.fill_to = Vector2(0.5, 1.1)
	return gt


func _coin_icon(px: float) -> Control:
	# a gold pitis — the old Kelantan/Terengganu coin with a square hole — drawn, no texture
	var c: Control = Control.new()
	c.custom_minimum_size = Vector2(px, px)
	c.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.draw.connect(func() -> void:
		var mid: Vector2 = c.size * 0.5
		var r: float = minf(mid.x, mid.y)
		c.draw_circle(mid, r, WOOD_EDGE)
		c.draw_circle(mid, r - 1.5, SONGKET_GOLD)
		c.draw_arc(mid, r * 0.66, 0.0, TAU, 24, COPPER, maxf(r * 0.12, 1.0), true)
		var h: float = r * 0.28
		c.draw_rect(Rect2(mid - Vector2(h, h), Vector2(h, h) * 2.0), WOOD_EDGE))
	return c


func _build_cutscene_panel() -> void:
	# the kelir: a backlit cloth screen; the gunungan opens and closes the telling,
	# a swaying shadow puppet speaks, narration types out below
	cutscene_panel = Control.new()
	cutscene_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	cutscene_panel.visible = false
	cutscene_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	cutscene_panel.gui_input.connect(_on_cutscene_gui_input)
	ui.add_child(cutscene_panel)
	_all_panels.append(cutscene_panel)

	var kelir: TextureRect = TextureRect.new()
	kelir.set_anchors_preset(Control.PRESET_FULL_RECT)
	kelir.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kelir.texture = _kelir_texture()
	kelir.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cutscene_panel.add_child(kelir)
	for side_right: bool in [false, true]:
		var frame: ColorRect = ColorRect.new() # the wooden banana-trunk frame edges
		frame.color = HT.INK
		frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
		frame.set_anchors_preset(Control.PRESET_RIGHT_WIDE if side_right else Control.PRESET_LEFT_WIDE)
		frame.offset_right = 0.0 if side_right else 26.0
		frame.offset_left = -26.0 if side_right else 0.0
		cutscene_panel.add_child(frame)

	# the gunungan (tree of life) stands centre-stage to open the telling, then is
	# planted at the side; _cutscene_begin/_cutscene_advance animate it
	cut_gunungan = TextureRect.new()
	cut_gunungan.anchor_left = 0.5
	cut_gunungan.anchor_right = 0.5
	cut_gunungan.anchor_top = 0.04
	cut_gunungan.anchor_bottom = 0.68
	cut_gunungan.offset_left = -170.0
	cut_gunungan.offset_right = 170.0
	cut_gunungan.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cut_gunungan.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	cut_gunungan.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cut_gunungan.modulate = HT.INK
	var gun_path: String = "res://assets/wayang/wayang_gunungan.png"
	if ResourceLoader.exists(gun_path):
		cut_gunungan.texture = load(gun_path)
	cutscene_panel.add_child(cut_gunungan)

	cut_puppet = TextureRect.new()
	cut_puppet.anchor_left = 0.52
	cut_puppet.anchor_right = 0.94
	cut_puppet.anchor_top = 0.06
	cut_puppet.anchor_bottom = 0.66
	cut_puppet.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cut_puppet.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	cut_puppet.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cut_puppet.modulate = HT.INK # silhouette against the lamp
	cutscene_panel.add_child(cut_puppet)

	var text_box: PanelContainer = _mk_panel_box(true, 8.0) # wide + short: slim frame
	text_box.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	text_box.offset_left = 70.0
	text_box.offset_right = -70.0
	text_box.offset_top = -228.0
	text_box.offset_bottom = -24.0
	text_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cutscene_panel.add_child(text_box)
	var tv: VBoxContainer = VBoxContainer.new()
	tv.add_theme_constant_override("separation", 6)
	tv.mouse_filter = Control.MOUSE_FILTER_IGNORE
	text_box.add_child(tv)
	# header: master name in Kurland, region, and the paragraph counter at the right
	var head: HBoxContainer = HBoxContainer.new()
	head.add_theme_constant_override("separation", 14)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tv.add_child(head)
	cut_name_label = _mk_title("", 30)
	cut_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	head.add_child(cut_name_label)
	cut_region_label = _mk_label("", 17, CREAM_MUTED)
	cut_region_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	cut_region_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cut_region_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	head.add_child(cut_region_label)
	cut_counter_label = _mk_title("", 18, CREAM_MUTED)
	cut_counter_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(cut_counter_label)
	cut_text = _mk_label("", 18)
	cut_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	cut_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cut_text.visible_characters_behavior = TextServer.VC_CHARS_AFTER_SHAPING # words never jump lines mid-type
	cut_text.custom_minimum_size = Vector2(0.0, 84.0)
	cut_text.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	tv.add_child(cut_text)
	cut_hint = _mk_label("", 12, CREAM_MUTED)
	cut_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	tv.add_child(cut_hint)

	cut_skip_button = _mk_button("", WOOD_DARK, true)
	cut_skip_button.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	cut_skip_button.grow_horizontal = Control.GROW_DIRECTION_BEGIN # longer labels (LANGKAU) grow inward
	cut_skip_button.offset_left = -130.0
	cut_skip_button.offset_right = -40.0
	cut_skip_button.offset_top = 20.0
	cut_skip_button.offset_bottom = 56.0
	cut_skip_button.pressed.connect(_cutscene_finish)
	cutscene_panel.add_child(cut_skip_button)


func _on_cutscene_gui_input(event: InputEvent) -> void:
	var click: InputEventMouseButton = event as InputEventMouseButton
	if click != null and click.pressed and click.button_index == MOUSE_BUTTON_LEFT:
		_cutscene_advance()


func _cutscene_begin(idx: int) -> void:
	var m: Dictionary = MASTERS[idx]
	_cut_pars = CUTSCENES[String(m.id)][lang]
	_cut_idx = -1
	cut_name_label.text = String(m.name)
	cut_name_label.add_theme_color_override("font_color", m.get("color", PLAYER_COLOR))
	cut_region_label.text = String(m["region_" + lang])
	cut_hint.text = _t("cut_continue")
	cut_skip_button.text = _t("cut_skip")
	if _cut_tick_stream == null:
		_cut_tick_stream = _load_audio("res://assets/audio/sfx/ui_hover")
	var path: String = "res://assets/wayang/wayang_%s.png" % String(m.id)
	cut_puppet.visible = ResourceLoader.exists(path)
	if cut_puppet.visible:
		cut_puppet.texture = load(path)
		cut_puppet.pivot_offset = Vector2(cut_puppet.size.x * 0.5, cut_puppet.size.y) # rocks from its rod
		cut_puppet.rotation = 0.0
		if _puppet_tween != null and _puppet_tween.is_valid():
			_puppet_tween.kill()
		_puppet_tween = create_tween().set_loops()
		_puppet_tween.tween_property(cut_puppet, "rotation", deg_to_rad(3.0), 2.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		_puppet_tween.tween_property(cut_puppet, "rotation", deg_to_rad(-3.0), 2.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	# opening: the gunungan stands centre, then is planted at the left as the
	# puppet steps up to the lamp
	if _cut_gun_tween != null and _cut_gun_tween.is_valid():
		_cut_gun_tween.kill()
	cut_gunungan.offset_left = -170.0
	cut_gunungan.offset_right = 170.0
	cut_gunungan.scale = Vector2.ONE
	cut_gunungan.pivot_offset = Vector2(170.0, cut_gunungan.size.y) # stands on its rod
	cut_puppet.modulate.a = 0.0 if cut_gunungan.texture != null else 1.0
	_cut_gun_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	_cut_gun_tween.tween_property(cut_gunungan, "offset_left", -170.0 - 470.0, 0.8).set_delay(0.3)
	_cut_gun_tween.tween_property(cut_gunungan, "offset_right", 170.0 - 470.0, 0.8).set_delay(0.3)
	_cut_gun_tween.tween_property(cut_gunungan, "scale", Vector2(0.7, 0.7), 0.8).set_delay(0.3)
	_cut_gun_tween.tween_property(cut_puppet, "modulate:a", 1.0, 0.5).set_delay(0.7)
	_pulse(cut_hint)
	_cutscene_advance()


func _cutscene_advance() -> void:
	if state != State.CUTSCENE:
		return
	if _cut_tween != null and _cut_tween.is_valid() and _cut_tween.is_running():
		_cut_tween.kill()
		cut_text.visible_ratio = 1.0 # first click completes the typewriter
		return
	_cut_idx += 1
	if _cut_idx == _cut_pars.size():
		_cutscene_close()
	if _cut_idx >= _cut_pars.size():
		return # closing; further clicks wait for it
	cut_counter_label.text = "%d / %d" % [_cut_idx + 1, _cut_pars.size()]
	cut_text.text = String(_cut_pars[_cut_idx])
	cut_text.visible_characters = 0
	_cut_ticked = 0
	_cut_tween = create_tween()
	_cut_tween.tween_method(_cut_type, 0, cut_text.text.length(), maxf(cut_text.text.length() / 42.0, 0.6))


func _cut_type(count: int) -> void:
	# typewriter step with a soft tick every few letters
	cut_text.visible_characters = count
	if count >= _cut_ticked + 3:
		_cut_ticked = count
		_play_sfx(_cut_tick_stream, -8.0, 0.2)


func _cutscene_close() -> void:
	# natural end: the gunungan returns to centre stage and the puppet leaves the lamp;
	# SKIP / Esc go straight to _cutscene_finish
	if cut_gunungan.texture == null:
		_cutscene_finish()
		return
	if _cut_gun_tween != null and _cut_gun_tween.is_valid():
		_cut_gun_tween.kill()
	_cut_gun_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	_cut_gun_tween.tween_property(cut_gunungan, "offset_left", -170.0, 0.45)
	_cut_gun_tween.tween_property(cut_gunungan, "offset_right", 170.0, 0.45)
	_cut_gun_tween.tween_property(cut_gunungan, "scale", Vector2.ONE, 0.45)
	_cut_gun_tween.tween_property(cut_puppet, "modulate:a", 0.0, 0.3)
	_cut_gun_tween.chain().tween_callback(_cutscene_finish)


func _cutscene_finish() -> void:
	if state != State.CUTSCENE:
		return
	if _cut_tween != null and _cut_tween.is_valid():
		_cut_tween.kill()
	if _puppet_tween != null and _puppet_tween.is_valid():
		_puppet_tween.kill()
	if _cut_gun_tween != null and _cut_gun_tween.is_valid():
		_cut_gun_tween.kill()
	_enter_state(State.WIND)


func _build_round_panel() -> void:
	# one results card for every round / duel end: caption, verdict, best-of-3 pips
	# around the score, why it ended, your round in numbers, rewards, then
	# CONTINUE beside a bar that drains with the auto-advance timer
	round_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box(true, 14.0) # short panel: slim frame, roomy
	box.custom_minimum_size = Vector2(560.0, 0.0)
	round_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	box.add_child(v)
	round_caption = _mk_label("", 14, CREAM_MUTED)
	v.add_child(round_caption)
	round_label = _mk_title("", 38)
	round_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART # a long verdict wraps; the card keeps its width
	round_label.custom_minimum_size = Vector2(492.0, 0.0) # the 560 card's inner width
	v.add_child(round_label)
	round_score_row = HBoxContainer.new()
	round_score_row.alignment = BoxContainer.ALIGNMENT_CENTER
	round_score_row.add_theme_constant_override("separation", 16)
	v.add_child(round_score_row)
	round_my_pips = ScorePips.new()
	round_my_pips.set_total(2)
	round_my_pips.color = HT.SIDE_YOU
	round_my_pips.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	round_score_row.add_child(round_my_pips)
	round_score_label = _mk_title("", 32, TEXT_COLOR)
	round_score_row.add_child(round_score_label)
	round_foe_pips = ScorePips.new()
	round_foe_pips.set_total(2)
	round_foe_pips.rtl = true
	round_foe_pips.color = HT.SIDE_FOE
	round_foe_pips.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	round_score_row.add_child(round_foe_pips)
	round_reason_label = _mk_label("", 18)
	v.add_child(round_reason_label)
	v.add_child(_mk_divider())
	round_stats_row = HBoxContainer.new()
	round_stats_row.alignment = BoxContainer.ALIGNMENT_CENTER
	round_stats_row.add_theme_constant_override("separation", 40)
	v.add_child(round_stats_row)
	for i: int in 3:
		var cell: VBoxContainer = VBoxContainer.new()
		cell.add_theme_constant_override("separation", -2)
		round_stats_row.add_child(cell)
		var num: Label = _mk_title("", 30)
		cell.add_child(num)
		round_stat_values.append(num)
		var cap: Label = _mk_label("", 13, CREAM_MUTED)
		cell.add_child(cap)
		round_stat_captions.append(cap)
	round_award_row = HBoxContainer.new()
	round_award_row.add_theme_constant_override("separation", 18)
	round_award_row.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(round_award_row)
	mats_saved_label = _mk_label("", 13, CREAM_MUTED)
	mats_saved_label.visible = false
	v.add_child(mats_saved_label)
	award_label = _mk_label("", 17, PLAYER_COLOR) # +XP and LEVEL UP lines
	v.add_child(award_label)
	unlock_label = _mk_label("", 18, PLAYER_COLOR)
	unlock_label.visible = false
	v.add_child(unlock_label)
	match_point_label = _mk_title("", 26, DANGER)
	match_point_label.visible = false
	v.add_child(match_point_label)
	var foot: HBoxContainer = HBoxContainer.new()
	foot.add_theme_constant_override("separation", 14)
	v.add_child(foot)
	# the auto-advance countdown: a thin plain groove, so it never reads as another gold XP / spin gauge
	round_timer_bar = ProgressBar.new()
	round_timer_bar.max_value = 1.0
	round_timer_bar.show_percentage = false
	round_timer_bar.custom_minimum_size = Vector2(0.0, 3.0)
	round_timer_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	round_timer_bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	round_timer_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var groove: StyleBoxFlat = StyleBoxFlat.new()
	groove.bg_color = GROOVE
	var drain: StyleBoxFlat = StyleBoxFlat.new()
	drain.bg_color = Color(TEXT_DIM, 0.6)
	round_timer_bar.add_theme_stylebox_override("background", groove)
	round_timer_bar.add_theme_stylebox_override("fill", drain)
	foot.add_child(round_timer_bar)
	round_continue_button = _mk_button("", WOOD_AMBER)
	round_continue_button.add_theme_font_size_override("font_size", 16)
	round_continue_button.pressed.connect(_on_round_continue)
	# Enter works too: a Button shortcut only fires while the button is visible
	var keys: Shortcut = Shortcut.new()
	var enter: InputEventKey = InputEventKey.new()
	enter.keycode = KEY_ENTER
	var kp_enter: InputEventKey = InputEventKey.new()
	kp_enter.keycode = KEY_KP_ENTER
	keys.events = [enter, kp_enter]
	round_continue_button.shortcut = keys
	round_continue_button.shortcut_in_tooltip = false
	foot.add_child(round_continue_button)


func _on_round_continue() -> void:
	# CONTINUE and the auto-advance timer share one armed callback: whichever
	# fires first takes it, so the other (or a double click) finds nothing to run
	var next: Callable = _round_next
	_round_next = Callable()
	if next.is_valid():
		next.call()


func _on_round_timeout(token: int) -> void:
	if token == _round_token: # a timer left over from an earlier panel never advances this one
		_on_round_continue()


func _arm_round_advance(secs: float, next: Callable) -> void:
	# the bar drains in step with the auto-advance timer (both pause- and time-scale-aware)
	_round_token += 1
	_round_next = next
	round_continue_button.text = _t("continue")
	round_continue_button.visible = next.is_valid()
	round_timer_bar.value = 1.0
	_round_bar_tween = create_tween()
	_round_bar_tween.tween_property(round_timer_bar, "value", 0.0, secs)
	if next.is_valid():
		get_tree().create_timer(secs, false).timeout.connect(_on_round_timeout.bind(_round_token))


func _fill_round_panel(winner: int, reason: Dictionary) -> void:
	# score, why the round ended, your round in numbers, XP / level-ups
	# (every caller sets the verdict first: a long one, e.g. a Malay master's win, steps down a size)
	round_label.add_theme_font_size_override("font_size", 38 if round_label.text.length() <= 24 else 32)
	var me: int = arena.my_id()
	var campaign: bool = not net_active and not endless_mode
	round_score_row.visible = campaign or net_active
	round_my_pips.visible = campaign
	round_foe_pips.visible = campaign
	if campaign:
		round_my_pips.wins = int(arena.scores.get(1, 0))
		round_foe_pips.wins = int(arena.scores.get(2, 0))
		round_my_pips.queue_redraw()
		round_foe_pips.queue_redraw()
		round_score_label.text = _score_line()
	elif net_active:
		round_score_label.text = arena.scoreboard()
	round_score_label.add_theme_font_size_override("font_size", 32 if campaign else 20)
	round_reason_label.text = _reason_text(reason, winner)
	round_reason_label.visible = not round_reason_label.text.is_empty()
	var rs: Dictionary = arena.round_stats.get(me, {})
	var nums: Array[int] = [int(rs.get("hits", 0)), int(rs.get("kos", 0)) + int(rs.get("ringouts", 0)), int(rs.get("perfect", 0))]
	var caps: Array[String] = ["stat_hits", "stat_kos", "stat_perfect"]
	for i: int in nums.size():
		round_stat_values[i].text = str(nums[i])
		round_stat_values[i].add_theme_color_override("font_color", PLAYER_COLOR if nums[i] > 0 else CREAM_MUTED)
		round_stat_captions[i].text = _t(caps[i])
	var lines: Array[String] = []
	if _last_xp_gain > 0:
		lines.append("+%d XP" % _last_xp_gain)
	for up: Dictionary in _last_level_ups:
		lines.append(_t("level_up") % [String(STYLE_DEFS[up.style].label), int(up.level)])
	award_label.text = "\n".join(lines)
	award_label.visible = not lines.is_empty()
	if not _last_level_ups.is_empty():
		_pulse(award_label)


func _build_over_panel() -> void:
	over_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box(true, 12.0) # mid-height panel: slim frame, roomy
	over_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	box.add_child(v)
	v.add_child(_mk_gunungan(32.0))
	over_title = _mk_title("", 38)
	over_stats = _mk_label("", 18)
	v.add_child(over_title)
	v.add_child(over_stats)
	# campaign run: the seven masters as wayang, the beaten ones lit in gold
	over_masters_caption = _mk_label("", 13, CREAM_MUTED)
	over_masters_caption.visible = false
	v.add_child(over_masters_caption)
	over_masters_row = HBoxContainer.new()
	over_masters_row.alignment = BoxContainer.ALIGNMENT_CENTER
	over_masters_row.add_theme_constant_override("separation", 6)
	over_masters_row.visible = false
	v.add_child(over_masters_row)
	for m: Dictionary in MASTERS:
		# each master's shadow on its own little kelir; the lamp is lit once beaten
		var cell: TextureRect = TextureRect.new()
		cell.texture = _kelir_texture()
		cell.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		cell.custom_minimum_size = Vector2(44.0, 58.0)
		cell.tooltip_text = String(m.name)
		over_masters_row.add_child(cell)
		var puppet: TextureRect = TextureRect.new()
		var path: String = "res://assets/wayang/wayang_%s.png" % String(m.id)
		puppet.texture = load(path) if ResourceLoader.exists(path) else null
		puppet.set_anchors_preset(Control.PRESET_FULL_RECT)
		puppet.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		puppet.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		puppet.modulate = HT.INK
		puppet.mouse_filter = Control.MOUSE_FILTER_IGNORE
		cell.add_child(puppet)
	# coins earned this run, and NEW BEST / best in endless
	over_coin_row = HBoxContainer.new()
	over_coin_row.alignment = BoxContainer.ALIGNMENT_CENTER
	over_coin_row.add_theme_constant_override("separation", 8)
	over_coin_row.visible = false
	v.add_child(over_coin_row)
	over_coin_row.add_child(_coin_icon(22.0))
	over_coin_label = _mk_label("", 17, PLAYER_COLOR)
	over_coin_row.add_child(over_coin_label)
	over_best_label = _mk_title("", 26)
	over_best_label.visible = false
	v.add_child(over_best_label)
	over_mats_title = _mk_label("", 14, CREAM_MUTED)
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
	over_menu_button = _mk_button("", WOOD_DARK, true)
	over_menu_button.pressed.connect(_on_over_menu_pressed)
	var om_wrap: CenterContainer = CenterContainer.new()
	om_wrap.add_child(over_menu_button)
	v.add_child(om_wrap)
	rematch_status = _mk_label("", 14, CREAM_MUTED)
	rematch_status.visible = false
	v.add_child(rematch_status)
	over_hint = _mk_label("", 13, CREAM_MUTED)
	v.add_child(over_hint)


func _refresh_craft() -> void:
	for slot: int in craft_loadout_buttons.size():
		var button: Button = craft_loadout_buttons[slot]
		button.text = "%d · %s" % [slot + 1, String(STYLE_DEFS[loadout[slot]].label).trim_prefix("Gasing ")]
		button.set_pressed_no_signal(slot == loadout_slot)
		button.tooltip_text = _t("loadout_tip")
		button.disabled = net_active and net_ready_sent
	for index: int in craft_difficulty.size():
		var diff_button: Button = craft_difficulty[index]
		diff_button.text = _t(["difficulty_normal", "difficulty_hard", "difficulty_master"][index])
		diff_button.tooltip_text = _t("difficulty_tip")
		diff_button.set_pressed_no_signal(index == difficulty)
	# SP: the next-opponent card + purse; MP: the header's FFA line instead
	craft_opp_card.visible = not net_active
	craft_coin_chip.visible = not net_active
	craft_duel_label.visible = net_active
	if net_active:
		craft_duel_label.text = "FFA · %d %s" % [arena.connected_ids().size(), _t("ffa_players")]
	else:
		var opp: Dictionary = _current_opponent()
		craft_opp_caption.text = _t("next_opp")
		craft_opp_name.text = String(opp.name)
		craft_opp_name.add_theme_color_override("font_color", opp.get("color", PLAYER_COLOR))
		craft_opp_region.text = String(opp.get("region_" + lang, ""))
		craft_opp_duel.text = (_t("wave_n") % (duel_index + 1)) if endless_mode \
			else (_t("duel_n") % [mini(duel_index + 1, MASTERS.size()), MASTERS.size()])
		var puppet_path: String = "res://assets/wayang/wayang_%s.png" % String(opp.id)
		craft_opp_puppet.texture = load(puppet_path) if ResourceLoader.exists(puppet_path) else null
		craft_mats_hint.text = str(coins)
	craft_sub.visible = net_active
	craft_opp_status.visible = net_active

	var viewed: String = _craft_viewed()
	var def: Dictionary = STYLE_DEFS[viewed]
	var locked: bool = not unlocked_styles.has(viewed)
	var idx: int = _master_index(viewed)
	var gated: bool = idx >= 0 and not defeated_masters.has(String(MASTERS[idx].id))

	craft_name_label.text = String(def.label)
	craft_counter_label.text = "%d / %d" % [craft_index + 1, STYLE_DEFS.size()]
	var level: int = _style_level(viewed)
	craft_level_label.text = (_t("level_max") % level) if level == LEVEL_XP.size() else (_t("level_xp") % [level, int(style_xp.get(viewed, 0)), LEVEL_XP[level]])
	if locked:
		if net_active:
			craft_status_label.text = _t("locked_mp")
		elif gated:
			craft_status_label.text = _t("locked_hint") % String(MASTERS[idx].name)
		else:
			craft_status_label.text = _t("price_tag") % int(def.get("price", 0))
		craft_status_label.add_theme_color_override("font_color", COPPER)
	else:
		craft_status_label.text = _t("role_" + viewed)
		craft_status_label.add_theme_color_override("font_color", CREAM_MUTED)
	# browsing an unlocked top drops it into the active slot; say so
	craft_slot_hint.text = _t("slot_assign") % [loadout_slot + 1, String(def.label).trim_prefix("Gasing ")]
	craft_slot_hint.modulate.a = 0.0 if locked or net_active else 1.0

	var stats: Dictionary = _style_battle_stats(viewed) # includes SP levels; MP stays normalized
	# each bar spans the roster's range above a 15% floor, so the lowest stat never reads as empty
	var keys: Array[String] = ["mass", "spin_reserve", "balance"]
	var lows: Array[float] = [1.4, 60.0, 55.0]
	var spans: Array[float] = [2.0, 70.0, 35.0]
	for i: int in keys.size():
		_tween_bar(craft_stat_rows[i].bar, 0.15 + 0.85 * (float(stats[keys[i]]) - lows[i]) / spans[i])
		_tween_bar(craft_stat_rows[i].over, 0.15 + 0.85 * (float(def[keys[i]]) - lows[i]) / spans[i])
	# the numbers; gold when forging/levels lift a stat past the style's base
	for i: int in keys.size():
		var num: Label = craft_stat_rows[i].value
		var value: float = float(stats[keys[i]])
		num.text = ("%.1f" % value) if i == 0 else str(roundi(value))
		num.add_theme_color_override("font_color", PLAYER_COLOR if value > float(def[keys[i]]) + 0.001 else TEXT_COLOR)

	# forging/recoloring targets selected_shape, so hide the forge while browsing
	# a locked style (selected_shape is some other top) and in MP (equal footing)
	var forging: bool = not net_active and not locked
	craft_forge_box.visible = forging
	accent_row.visible = forging
	accent_label.text = _t("lacquer")
	_refresh_accents()
	for mat_id: String in MATERIAL_DEFS:
		var mdef: Dictionary = MATERIAL_DEFS[mat_id]
		var capped: bool = _forge_capped(mat_id)
		material_buttons[mat_id].text = "%s ×%d" % [mdef.label, materials_owned.get(mat_id, 0)]
		material_buttons[mat_id].disabled = forging and capped # never waste a material
		material_buy_buttons[mat_id].text = _t("buy_mat") % int(MAT_PRICES[mat_id])
		material_buy_buttons[mat_id].disabled = coins < int(MAT_PRICES[mat_id]) # unaffordable reads as such before the click
		var gains: Array[String] = []
		if float(mdef.mass) > 0.0:
			gains.append("+%s %s" % [str(mdef.mass), _t("stat_mass")])
		if float(mdef.balance) > 0.0:
			gains.append("+%d %s" % [int(mdef.balance), _t("stat_balance")])
		var gain: String = _t("forge_gain") % ", ".join(gains)
		var caption: Label = craft_forge_captions[mat_id]
		caption.text = (_t("forge_full") % gain) if capped else gain
		caption.add_theme_color_override("font_color", COPPER if float(mdef.mass) > 0.0 else PANDAN) # its stat bar's colour
		caption.modulate.a = 0.55 if capped else 1.0

	# the confirm button doubles as the BUY button (a copper plaque) on an affordable locked style;
	# on any other locked style it still fights, with the loadout (the status line says why not)
	var can_buy: bool = _can_buy(viewed)
	fight_button.text = (_t("buy_prefix") + String(def.label)) if can_buy else _t("fight")
	_set_plaque(fight_button, COPPER if can_buy else PLAYER_COLOR)
	fight_button.disabled = net_active and net_ready_sent


func _tween_bar(bar: ProgressBar, value: float) -> void:
	var tw: Tween = create_tween()
	tw.tween_property(bar, "value", clampf(value, 0.0, 1.0), 0.35).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


# ---------------------------------------------------------------- multiplayer presentation
func _net_teardown() -> void:
	net_ended = true
	Online.leave_lobby()
	arena.reset()
	net_active = false
	net_ended = false
	net_ready_sent = false
	net_rematch_sent = false
	net_my_wins = 0
	net_opp_wins = 0
	_reset_run()
	_apply_language()
	_enter_state(State.READY)


func _on_mp_joined_lobby() -> void:
	if not Online.is_host:
		if state != State.READY:
			_reset_run()
			_enter_state(State.READY)
		_show_menu_screen(MenuScreen.WAIT)
		_set_wait_status(_t("connecting"), "", false)
	arena.refresh_lobby()


func _on_mp_player_connected(_pd: PlayerData) -> void:
	arena.refresh_lobby()
	_refresh_wait_title()


func _refresh_wait_title() -> void:
	# lobby status: the host counts players, a client knows it reached the host
	if state != State.READY or menu_screen != MenuScreen.WAIT or Online.players.is_empty():
		return
	wait_title.text = (_t("players_count") % Online.players.size()) if Online.is_host else _t("connected_wait")


func _on_mp_player_disconnected(pd: PlayerData) -> void:
	if net_ended:
		return
	if pd.multiplayer_id == multiplayer.get_unique_id():
		return
	arena.peer_left(pd.multiplayer_id)
	_refresh_wait_title()


func _on_mp_server_disconnected() -> void:
	_handle_mp_loss(_t("mp_server_lost"))


func _on_mp_connection_failed() -> void:
	if state == State.READY and menu_screen == MenuScreen.WAIT:
		_show_menu_screen(MenuScreen.MP)
		_show_menu_notice(_t("err_join_failed"))


func _on_mp_steam_join_response(code: int) -> void:
	if code == Online.ErrorCodes.SUCCESS or Online.is_host or Online.is_busy:
		return
	if state == State.READY:
		_show_menu_screen(MenuScreen.MP)
		_show_menu_notice(_t("err_join_steam"))


func _netbot_init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if "netbot-host" in args:
		_netbot = true
		_on_host_lan_pressed.call_deferred()
	elif "netbot-join" in args:
		_netbot = true
		_on_join_lan_pressed.call_deferred()


func _handle_mp_loss(msg: String) -> void:
	if state == State.READY:
		Online.leave_lobby()
		_show_menu_screen(MenuScreen.MP)
		_show_menu_notice(msg)
	elif net_active and not net_ended:
		net_ended = true
		Online.leave_lobby()
		_reset_over_panel()
		over_title.text = msg
		over_title.add_theme_color_override("font_color", DANGER)
		over_stats.text = arena.scoreboard()
		restart_button.text = _t("back_menu")
		_enter_state(State.OVER)


func _arena_round_finished(winner: int, reason: Dictionary = {}) -> void:
	state = State.ROUND_OVER
	battle_hint.visible = false
	player_gauge.wobbling = false
	foe_gauge.wobbling = false
	var kind: String = String(reason.get("kind", ""))
	if not net_active:
		# let the deciding moment play out before any panel: KO slow-mo + FOV punch
		# while the topple/ring-out finishes, or a TIME! callout
		var delay: float = Gasing.DIE_SECONDS
		if kind.begins_with("time"):
			_banner(_t("time_up"), PLAYER_COLOR)
			delay = 0.9
		elif kind == "ko":
			_banner("K.O.!", DANGER)
			_time_warp(0.35, 0.8)
			_fov_punch()
		# game time (not real): the delay stretches with the slow-mo, like die()'s tween
		get_tree().create_timer(delay, false).timeout.connect(_sp_round_result.bind(winner, reason))
		return
	_reset_round_panel()
	var won: bool = winner == arena.my_id()
	var who: String = str(arena.roster.get(winner, ""))
	round_caption.text = _t("first_to_3")
	round_label.text = _t("round_draw") if winner == 0 else (_t("round_won") if won else _t("round_lost") % who)
	round_label.add_theme_color_override("font_color", CREAM_MUTED if winner == 0 else arena._side(winner))
	if winner != 0:
		_play_sfx(SND_WIN if won else SND_LOSE, -3.0, 0.02)
	_fill_round_panel(winner, reason)
	if won:
		var counts: Dictionary = _grant_materials(_rng.randi_range(1, 2))
		_tally_match_mats(counts)
		_show_award_icons(round_award_row, counts, "+%d")
		mats_saved_label.text = _t("mats_saved")
		mats_saved_label.visible = true
		_save_workshop()
	var decided: bool = false
	var match_point: bool = false
	for id: int in arena.connected_ids():
		var s: int = int(arena.scores.get(id, 0))
		decided = decided or s >= NET_MATCH_TARGET
		match_point = match_point or s == NET_MATCH_TARGET - 1
	if match_point and not decided:
		_show_match_point()
	_arm_round_advance(2.4, Callable()) # MP: the host's after_round advances; no CONTINUE
	get_tree().create_timer(2.4, false).timeout.connect(arena.after_round)
	_show_panel(round_panel)


func _sp_round_result(winner: int, reason: Dictionary) -> void:
	if state != State.ROUND_OVER or net_active:
		return # left to the title (or the match changed) during the KO delay
	# endless waves are single rounds; campaign duels are best of 3
	var outcome: int = (1 if winner == 1 else -1) if endless_mode else _duel_outcome(arena.scores)
	if winner != 0 and outcome != 0:
		_finish_duel(outcome > 0, reason)
		return
	_reset_round_panel()
	round_caption.text = _duel_caption(_current_opponent()) if endless_mode else _t("round_of") % sp_round
	round_label.text = _t("round_draw") if winner == 0 else (_t("round_won") if winner == 1 else _t("round_lost") % String(_current_opponent().name))
	round_label.add_theme_color_override("font_color", CREAM_MUTED if winner == 0 else (PLAYER_COLOR if winner == 1 else HT.SIDE_FOE))
	if winner != 0:
		_play_sfx(SND_WIN if winner == 1 else SND_LOSE, -3.0, 0.02)
	_fill_round_panel(winner, reason)
	if not endless_mode and int(arena.scores.get(1, 0)) == 1 and int(arena.scores.get(2, 0)) == 1:
		_show_match_point()
	_show_panel(round_panel)
	_arm_round_advance(2.6, _sp_next_round)


func _sp_next_round() -> void:
	# same loadout, straight back to the wind-up: begin_wind resets the round
	if state == State.ROUND_OVER and not net_active:
		_enter_state(State.WIND)


func _show_match_point() -> void:
	match_point_label.text = _t("match_point")
	match_point_label.visible = true
	_pulse(match_point_label)


func _score_line() -> String:
	return "%d – %d" % [int(arena.scores.get(1, 0)), int(arena.scores.get(2, 0))]


func _reason_text(reason: Dictionary, winner: int) -> String:
	# numbers read winner first vs the best of the rest
	var key: String = "counts" if String(reason.get("kind", "")) == "time_count" else "spins"
	var values: Dictionary = reason.get(key, {})
	var mine: int = int(values.get(winner, 0))
	var best_other: int = 0
	for id: Variant in values:
		if int(id) != winner:
			best_other = maxi(best_other, int(values[id]))
	match String(reason.get("kind", "")):
		"ko":
			return _t("reason_ko")
		"time_count":
			return _t("reason_time_count") % [mine, best_other]
		"time_spin":
			return _t("reason_time_spin") % [mine, best_other]
		"draw":
			return _t("reason_draw")
		"forfeit":
			return _t("reason_forfeit")
	return ""


func _forfeit_duel() -> void:
	# pause-menu FORFEIT DUEL: quitting a live campaign duel loses it like any other duel
	# loss (the run starts over), so a losing duel can't be replayed from 0-0 via the title
	if not net_active and not endless_mode and (state == State.WIND or state == State.BATTLE):
		campaign_index = 0
		_save_workshop()
	_leave_to_title()


func _leave_to_title() -> void:
	# workshop BACK / Esc, endless pause MAIN MENU: the campaign continues from the title
	get_tree().paused = false
	Engine.time_scale = 1.0
	if net_active:
		_net_teardown()
		return
	_enter_state(State.READY) # READY clears the tops; no _reset_run


func _arena_match_finished(winner: int) -> void:
	var won: bool = winner == arena.my_id()
	_play_music("victory" if won else "defeat")
	_reset_over_panel()
	over_title.text = _t("match_win") if won else _t("match_lose") % str(arena.roster.get(winner, "Player"))
	over_title.add_theme_color_override("font_color", PLAYER_COLOR if won else DANGER)
	over_stats.text = arena.scoreboard()
	if won:
		_tally_match_mats(_grant_materials(1))
		_save_workshop()
	if not net_match_mats.is_empty():
		over_mats_title.text = _t("match_mats")
		over_mats_title.visible = true
		over_award_row.visible = true
		_show_award_icons(over_award_row, net_match_mats, "×%d")
	net_rematch_sent = false
	restart_button.text = _t("rematch")
	restart_button.disabled = arena.connected_ids().size() < 2
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

	func set_total(n: int) -> void:
		total = n
		custom_minimum_size = Vector2(total * 22.0, 18.0)
		queue_redraw()

	func show_score(w: int, t: int, c: Color) -> void:
		# called every HUD tick: redraws only when the score, target or side colour changed
		if w == wins and t == total and c == color:
			return
		wins = w
		color = c
		set_total(t)

	func _draw() -> void:
		# belah-ketupat diamonds (songket motif), filled vs hollow in the side colour
		for i: int in total:
			var idx: int = total - 1 - i if rtl else i
			var c: Vector2 = Vector2(11.0 + i * 22.0, 9.0)
			var pts: PackedVector2Array = PackedVector2Array([
				c + Vector2(0.0, -8.0), c + Vector2(7.0, 0.0), c + Vector2(0.0, 8.0), c + Vector2(-7.0, 0.0)])
			if idx < wins:
				draw_colored_polygon(pts, color)
				draw_line(c + Vector2(0.0, -8.0), c + Vector2(0.0, 8.0), color.darkened(0.35), 1.0, true)
			else:
				var outline: PackedVector2Array = pts.duplicate()
				outline.append(pts[0])
				draw_polyline(outline, Color(color, 0.4), 2.0, true)


class FightBar:
	extends Control
	# fighting-game spin bar: a slanted bar anchored at the outer screen edge that
	# drains toward center; `shown` lags behind `frac` so chunk hits leave an orange
	# damage trail that melts away (frac is the live fill, drawn over the trail).
	# Under it: the name at the outer edge, the squad glyph row, the spin % inward.

	const BAR_H: float = 30.0
	const SKEW: float = 14.0

	var frac: float = 1.0
	var shown: float = 1.0
	var ring_color: Color = Color.WHITE # fill: the side colour (you gold; the rival crimson / its FFA seat)
	var side_color: Color = HT.SIDE_YOU # frame, ticks and squad glyphs
	var title: String = ""
	var squad: Array[int] = [1, 1, 1] # per slot: 0 alive, 1 reserve, 2 out
	var wobbling: bool = false
	var rtl: bool = false # foe bar: mirrored so both bars drain toward the center
	var _flash: float = 0.0

	static func draw_squad(ci: CanvasItem, origin: Vector2, codes: Array[int], col: Color) -> void:
		# ● alive / ○ reserve / ✕ out, drawn as shapes (the body font has none of these)
		for i: int in codes.size():
			var c: Vector2 = origin + Vector2(15.0 * i, 0.0)
			match codes[i]:
				0:
					ci.draw_circle(c, 5.5, col)
					ci.draw_arc(c, 5.5, 0.0, TAU, 20, HT.WOOD_EDGE, 1.2, true)
				1:
					ci.draw_arc(c, 4.8, 0.0, TAU, 20, col, 1.6, true)
				_:
					ci.draw_line(c + Vector2(-4.0, -4.0), c + Vector2(4.0, 4.0), Color(HT.DANGER, 0.85), 2.2, true)
					ci.draw_line(c + Vector2(-4.0, 4.0), c + Vector2(4.0, -4.0), Color(HT.DANGER, 0.85), 2.2, true)

	func _ready() -> void:
		custom_minimum_size = Vector2(450.0, 52.0)
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _process(delta: float) -> void:
		shown = lerpf(shown, frac, minf(3.0 * delta, 1.0))
		if wobbling:
			_flash = wrapf(_flash + delta * 7.0, 0.0, TAU)
		queue_redraw()

	func _cut(t: float) -> PackedVector2Array:
		# slanted cut line at fraction t (0 = outer edge, 1 = center end)
		var xt: float = lerpf(SKEW, size.x, t)
		var xb: float = lerpf(0.0, size.x - SKEW, t)
		if rtl:
			xt = size.x - xt
			xb = size.x - xb
		return PackedVector2Array([Vector2(xt, 0.0), Vector2(xb, BAR_H)])

	func _quad(t0: float, t1: float) -> PackedVector2Array:
		var a: PackedVector2Array = _cut(t0)
		var b: PackedVector2Array = _cut(t1)
		return PackedVector2Array([a[0], b[0], b[1], a[1]])

	func _draw() -> void:
		draw_colored_polygon(_quad(0.0, 1.0), Color(HT.WOOD_EDGE, 0.88))
		var f0: float = clampf(frac, 0.0, 1.0)
		var s0: float = clampf(shown, 0.0, 1.0)
		if s0 > f0 + 0.003:
			draw_colored_polygon(_quad(f0, s0), Color(HT.HIT_ORANGE, 0.9))
		var col: Color = ring_color
		if wobbling:
			col = ring_color.lerp(HT.DANGER, 0.5 + 0.5 * sin(_flash))
		if f0 > 0.003:
			var q: PackedVector2Array = _quad(0.0, f0)
			draw_colored_polygon(q, col)
			draw_colored_polygon(PackedVector2Array([
				q[0], q[1], q[1].lerp(q[2], 0.4), q[0].lerp(q[3], 0.4)]), col.lightened(0.22))
		var frame: PackedVector2Array = _quad(0.0, 1.0)
		frame.append(frame[0])
		draw_polyline(frame, Color(side_color, 0.85), 2.0, true)
		for i: int in [1, 2, 3]:
			var c: PackedVector2Array = _cut(float(i) / 4.0)
			draw_line(c[0], c[0].lerp(c[1], 0.18), Color(side_color, 0.4), 2.0, true)
		# label line: name at the outer edge, squad glyphs inward of it, spin % at the inner end
		var f: Font = get_theme_default_font()
		var y: float = BAR_H + 17.0
		var name_w: float = f.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x
		var name_x: float = size.x - name_w if rtl else 0.0
		draw_string_outline(f, Vector2(name_x, y), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, 4, HT.WOOD_EDGE)
		draw_string(f, Vector2(name_x, y), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, HT.TEXT_COLOR)
		var gx: float = size.x - name_w - 20.0 - 30.0 if rtl else name_w + 20.0
		draw_squad(self, Vector2(gx, y - 5.0), squad, side_color)
		var pct: String = "%d%%" % roundi(f0 * 100.0)
		var pw: float = FONT_TITLE.get_string_size(pct, HORIZONTAL_ALIGNMENT_LEFT, -1, 22).x
		var px: float = SKEW if rtl else size.x - SKEW - pw
		draw_string_outline(FONT_TITLE, Vector2(px, y + 3.0), pct, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, 5, HT.WOOD_EDGE)
		draw_string(FONT_TITLE, Vector2(px, y + 3.0), pct, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, HT.DANGER if wobbling else HT.TEXT_COLOR)


class WindMeter:
	extends Control
	# a cord winding around a gasing spindle: coils stack as you charge;
	# the 80-95 sweet spot is a songket gold band, >95 is overwind. The tip takes the
	# launch-grade colours: WEAK dim < 40 <= GOOD blue < 80 <= PERFECT gold <= 95 < snap red

	const ROPE: Color = Color(0.78, 0.62, 0.42) # natural cord
	const ROPE_DARK: Color = Color(0.35, 0.25, 0.15)
	const COIL_H: float = 7.0

	var power: float = 0.0
	var shown: float = 0.0
	var label_text: String = "WIND"
	var _plate: StyleBoxFlat = StyleBoxFlat.new() # the HUD's dark-wood plate: zone washes never mix with the floor

	func _ready() -> void:
		custom_minimum_size = Vector2(64.0, 270.0)
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		_plate.bg_color = Color(HT.WOOD_EDGE, 0.85)
		_plate.border_color = Color(HT.SONGKET_GOLD, 0.5)
		_plate.set_border_width_all(1)
		_plate.set_corner_radius_all(6)

	func _process(delta: float) -> void:
		shown = lerpf(shown, power, minf(10.0 * delta, 1.0))
		queue_redraw()

	func _y(v: float) -> float:
		return size.y * (1.0 - v / 100.0)

	func _hw(y: float) -> float:
		return lerpf(7.0, 11.0, y / size.y) # shaft tapers top -> bottom

	func _draw() -> void:
		var cx: float = size.x * 0.5
		draw_style_box(_plate, Rect2(Vector2(-2.0, -2.0), size + Vector2(4.0, 4.0)))
		# spindle shaft
		var shaft: PackedVector2Array = PackedVector2Array([
			Vector2(cx - _hw(0.0), 0.0), Vector2(cx + _hw(0.0), 0.0),
			Vector2(cx + _hw(size.y), size.y), Vector2(cx - _hw(size.y), size.y)])
		draw_colored_polygon(shaft, HT.WOOD_DARK)
		draw_line(shaft[0], shaft[3], HT.WOOD_EDGE, 2.0, true)
		draw_line(shaft[1], shaft[2], HT.WOOD_EDGE, 2.0, true)
		draw_line(Vector2(cx - 2.5, 3.0), Vector2(cx - 3.5, size.y - 3.0), HT.WOOD_DARK.lightened(0.35), 2.5, true)
		# zones: 40-80 GOOD wash, 80-95 songket sweet band, >95 overwind
		draw_rect(Rect2(Vector2(6.0, _y(80.0)), Vector2(size.x - 12.0, _y(40.0) - _y(80.0))), Color(HT.ENERGY_BLUE, 0.14), true)
		draw_texture_rect_region(HT.TEX_SONGKET, Rect2(Vector2(2.0, _y(95.0)), Vector2(size.x - 4.0, _y(80.0) - _y(95.0))),
			Rect2(0.0, 0.0, 64.0, 32.0), Color(HT.SONGKET_GOLD, 0.9))
		draw_rect(Rect2(Vector2(6.0, 0.0), Vector2(size.x - 12.0, _y(95.0))), Color(HT.OVERWIND_RED, 0.3), true)
		for v: float in [80.0, 95.0]:
			var yv: float = _y(v)
			draw_line(Vector2(0.0, yv), Vector2(9.0, yv), HT.SONGKET_GOLD, 2.0, true)
			draw_line(Vector2(size.x - 9.0, yv), Vector2(size.x, yv), HT.SONGKET_GOLD, 2.0, true)
		var sweet: bool = shown >= 80.0 and shown <= 95.0
		var tip: Color = HT.TEXT_DIM
		if shown > 95.0:
			tip = HT.OVERWIND_RED
		elif sweet:
			tip = HT.SONGKET_GOLD
		elif shown >= 40.0:
			tip = HT.ENERGY_BLUE
		# cord coils stack bottom -> _y(shown)
		var fill_top: float = _y(shown)
		var n: int = int((size.y - fill_top) / COIL_H)
		if sweet and n > 0: # soft gold glow behind the top coils: release now
			draw_circle(Vector2(cx, size.y - (float(n) - 1.0) * COIL_H), 22.0, Color(HT.SONGKET_GOLD, 0.22))
		for i: int in n:
			var yc: float = size.y - (float(i) + 0.5) * COIL_H
			var half: float = _hw(yc) + 6.0
			var body: Color = tip if i >= n - 2 else ROPE
			var w: float = COIL_H - 1.0
			draw_line(Vector2(cx - half, yc), Vector2(cx + half, yc), body, w, true)
			draw_circle(Vector2(cx - half, yc), w * 0.5, body)
			draw_circle(Vector2(cx + half, yc), w * 0.5, body)
			draw_line(Vector2(cx - half, yc + w * 0.5), Vector2(cx + half, yc + w * 0.5), ROPE_DARK, 1.0, true)
		if n > 0:
			# loose cord end pulling away from the top coil
			var yt: float = size.y - (float(n) - 0.5) * COIL_H
			draw_line(Vector2(cx + _hw(yt) + 6.0, yt), Vector2(size.x + 16.0, yt - 22.0), tip, 3.0, true)
		# label on a small wood plaque (gold while the release would be PERFECT)
		var f: Font = get_theme_default_font()
		draw_rect(Rect2(Vector2(2.0, -26.0), Vector2(size.x - 4.0, 20.0)), Color(HT.WOOD_EDGE, 0.85), true)
		draw_rect(Rect2(Vector2(2.0, -26.0), Vector2(size.x - 4.0, 20.0)), Color(HT.SONGKET_GOLD, 0.5), false, 1.0)
		draw_string(f, Vector2(0.0, -11.0), label_text, HORIZONTAL_ALIGNMENT_CENTER, size.x, 13, HT.SONGKET_GOLD if sweet else HT.TEXT_COLOR)


class SquadRow:
	extends Control
	# FFA standings row under the foe bar (right-aligned): colour chip, name, squad glyphs, wins

	var title: String = ""
	var color: Color = Color.WHITE
	var squad: Array[int] = [1, 1, 1]
	var wins: int = 0

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func show_row(p_title: String, p_color: Color, codes: Array[int], p_wins: int) -> void:
		if p_title == title and p_color == color and codes == squad and p_wins == wins:
			return
		title = p_title
		color = p_color
		squad.assign(codes)
		wins = p_wins
		queue_redraw()

	func _draw() -> void:
		var f: Font = get_theme_default_font()
		var y: float = size.y * 0.5
		draw_rect(Rect2(size.x - 10.0, y - 5.0, 10.0, 10.0), color)
		var name_w: float = f.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x
		var x: float = size.x - 18.0 - name_w
		draw_string_outline(f, Vector2(x, y + 5.0), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, 4, HT.WOOD_EDGE)
		draw_string(f, Vector2(x, y + 5.0), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, HT.TEXT_COLOR)
		FightBar.draw_squad(self, Vector2(x - 44.0, y), squad, color)
		for i: int in wins: # match wins as small belah-ketupat diamonds
			var c: Vector2 = Vector2(x - 64.0 - 12.0 * i, y)
			draw_colored_polygon(PackedVector2Array([c + Vector2(0.0, -6.0), c + Vector2(5.0, 0.0),
				c + Vector2(0.0, 6.0), c + Vector2(-5.0, 0.0)]), color)


class KeyStrip:
	extends PanelContainer
	# key-cap controls strip: fades in for the first 10 s of each round's battle; the
	# pause page's own controls row replaces it, so it fades out (even paused) under the pause

	var game: Node

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		process_mode = Node.PROCESS_MODE_ALWAYS
		modulate.a = 0.0

	func _process(delta: float) -> void:
		var arena: Node = game.arena
		if arena == null:
			return
		var want: bool = arena.phase == arena.Phase.BATTLE and arena.elapsed < 10.0 \
			and not (game.menus != null and game.menus.is_open())
		modulate.a = move_toward(modulate.a, 1.0 if want else 0.0, delta * 4.0)
