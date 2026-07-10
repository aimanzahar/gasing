extends Node3D

enum State { READY, CRAFT, WIND, LAUNCH, BATTLE, ROUND_OVER, OVER, CUTSCENE }
enum MenuScreen { TITLE, MP, WAIT }

const GASING_SCENE: PackedScene = preload("res://gasing.tscn")
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
const NUDGE_POWER: float = 2.4
const MAX_IMPULSE: float = 6.0
const NUDGE_SPIN_COST: float = 2.0
const NUDGE_COOLDOWN: float = 0.35
const PLAYER_COLOR: Color = Color(1.0, 0.78, 0.25)
const FOE_COLOR: Color = Color(0.2, 0.85, 0.8)
const TEXT_COLOR: Color = Color(0.96, 0.9, 0.78)
const PANEL_BG: Color = Color(0.11, 0.06, 0.035, 0.94)
# ---- heritage UI tokens (ukiran wood + songket gold theme)
const SONGKET_GOLD: Color = Color(1.0, 0.78, 0.25) # == PLAYER_COLOR; semantic alias for UI gold
const WOOD_DARK: Color = Color(0.3, 0.2, 0.1) # dark plaque base (quit/back/lang/skip/material)
const WOOD_AMBER: Color = Color(0.82, 0.6, 0.24) # amber plaque base (host/join/pick/buy/mp)
const WOOD_EDGE: Color = Color(0.16, 0.09, 0.05) # deep carved-shadow brown
const BORDER_BROWN: Color = Color(0.55, 0.38, 0.16, 0.8) # carved rim / line-edit border
const CREAM_MUTED: Color = Color(0.75, 0.66, 0.52) # secondary text
const PANDAN: Color = Color(0.55, 0.8, 0.45) # endless button green
const COPPER: Color = Color(0.85, 0.55, 0.3) # locked-card price text
const DANGER: Color = Color(1.0, 0.45, 0.3) # defeat / offline / match point

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
const NET_MATCH_TARGET: int = 3
const SAVE_PATH: String = "user://workshop.cfg"
# per-arena mood presets; "env" GLB swaps the kampung backdrop when the file exists,
# sky/fog/sun/lantern re-theming works even before the GLBs are produced
const ARENA_DEFS: Dictionary = {
	"kampung": {"env": "", "sky_top": Color(0.30, 0.28, 0.40), "sky_horizon": Color(0.86, 0.52, 0.30),
		"fog": Color(0.72, 0.52, 0.36), "fog_density": 0.008, "sun_color": Color(1.0, 0.86, 0.66),
		"sun_energy": 1.05, "lantern": Color(1.0, 0.62, 0.28), "lantern_energy": 2.2},
	"kelantan": {"env": "res://assets/arena_kelantan.glb", "sky_top": Color(0.35, 0.30, 0.35), "sky_horizon": Color(0.95, 0.65, 0.25),
		"fog": Color(0.80, 0.60, 0.30), "fog_density": 0.007, "sun_color": Color(1.0, 0.88, 0.60),
		"sun_energy": 1.15, "lantern": Color(1.0, 0.72, 0.30), "lantern_energy": 2.2},
	"penang": {"env": "res://assets/arena_penang.glb", "sky_top": Color(0.12, 0.08, 0.20), "sky_horizon": Color(0.60, 0.22, 0.18),
		"fog": Color(0.45, 0.22, 0.20), "fog_density": 0.010, "sun_color": Color(1.0, 0.60, 0.45),
		"sun_energy": 0.45, "lantern": Color(1.0, 0.25, 0.15), "lantern_energy": 3.4},
	"melaka": {"env": "res://assets/arena_melaka.glb", "sky_top": Color(0.12, 0.15, 0.30), "sky_horizon": Color(0.45, 0.40, 0.60),
		"fog": Color(0.40, 0.40, 0.60), "fog_density": 0.010, "sun_color": Color(0.75, 0.80, 1.0),
		"sun_energy": 0.75, "lantern": Color(0.40, 0.60, 1.0), "lantern_energy": 2.6},
	"terengganu": {"env": "res://assets/arena_terengganu.glb", "sky_top": Color(0.15, 0.25, 0.38), "sky_horizon": Color(0.55, 0.75, 0.75),
		"fog": Color(0.50, 0.70, 0.70), "fog_density": 0.008, "sun_color": Color(0.85, 0.95, 1.0),
		"sun_energy": 1.0, "lantern": Color(0.30, 0.90, 0.80), "lantern_energy": 2.4},
	"sarawak": {"env": "res://assets/arena_sarawak.glb", "sky_top": Color(0.08, 0.12, 0.14), "sky_horizon": Color(0.30, 0.38, 0.35),
		"fog": Color(0.22, 0.30, 0.26), "fog_density": 0.014, "sun_color": Color(0.70, 0.80, 0.85),
		"sun_energy": 0.5, "lantern": Color(1.0, 0.55, 0.25), "lantern_energy": 3.0},
	"sabah": {"env": "res://assets/arena_sabah.glb", "sky_top": Color(0.35, 0.45, 0.60), "sky_horizon": Color(0.85, 0.80, 0.65),
		"fog": Color(0.70, 0.75, 0.70), "fog_density": 0.006, "sun_color": Color(1.0, 0.95, 0.85),
		"sun_energy": 1.2, "lantern": Color(0.60, 0.90, 0.50), "lantern_energy": 2.0},
	"kl": {"env": "res://assets/arena_kl.glb", "sky_top": Color(0.05, 0.05, 0.12), "sky_horizon": Color(0.35, 0.22, 0.40),
		"fog": Color(0.28, 0.20, 0.35), "fog_density": 0.010, "sun_color": Color(0.85, 0.75, 1.0),
		"sun_energy": 0.4, "lantern": Color(0.90, 0.40, 0.90), "lantern_energy": 3.2},
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
const ACCENT_CHOICES: Array[Color] = [
	Color(1.0, 0.78, 0.25), Color(0.90, 0.20, 0.15), Color(0.20, 0.85, 0.45),
	Color(0.25, 0.55, 1.00), Color(0.95, 0.45, 0.85), Color(0.95, 0.95, 0.90),
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
		"fact": "Did you know? Gasing is a heritage sport of Kelantan and Melaka.",
		"prompt": "Press SPACE for single player",
		"wind_hint": "Hold SPACE / left mouse to wind the cord — release in the GREEN zone!  (A/D to aim)",
		"bench": "WORKSHOP",
		"duel_line": "Duel %d / %d  —  Opponent: %s",
		"craft_duel_line": "Duel %d / %d  —  Next opponent: %s",
		"mats_line": "Duit %d  ·  Merbau %d  ·  Kemuning %d  ·  Besi %d",
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
		"tip_stat_mass": "Mass — pangkah power.\nStrike force scales with (your mass ÷ theirs):\nheavy tops shove rivals far and barely budge when hit.",
		"tip_stat_spin": "Spin — your top's stamina.\nLaunch spin = wind quality × Spin, and a larger\nreserve also fades slower. Outlast the rival's top.",
		"tip_stat_balance": "Balance — steadiness as spin fades.\nWobble lean shrinks as Balance rises:\na balanced top staggers less and topples later.",
		"stat_legend": "Mass = strike power  ·  Spin = stamina  ·  Balance = steadiness  (hover a stat for details)",
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
		"mp_code_label": "Lobby Code:",
		"join_code": "JOIN CODE",
		"share_code": "Share this code: %s",
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
		"coin_award": "+%d duit earned!",
		"now_purchasable": "%s's gasing is now for sale in your workshop!",
		"locked_beat": "Defeat %s to unlock this purchase.",
		"locked_mp": "Locked — buy it in single player.",
		"bought": "%s bought — spin it well!",
		"need_coins": "Costs %d duit — you have %d.",
		"price_tag": "For sale — %d duit",
		"buy_prefix": "BUY: ",
		"mat_buy": "+1 · %d duit",
		"mat_bought": "+1 %s bought.",
		"customize": "Lacquer colour:",
		"cut_continue": "Click / SPACE to continue",
		"cut_skip": "SKIP",
		"endless": "ENDLESS GELANGGANG",
		"wave_line": "Wave %d  —  %s",
		"endless_over": "Waves survived: %d",
		"endless_best_line": "Best: %d",
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
		"role_kelantan": "Golden heart — the old way",
		"role_penang": "Firecracker — swift pangkah",
		"role_melaka": "Trader's patience — endless spin",
		"role_terengganu": "Breaking wave — hit and slip",
		"role_sarawak": "Thunderclap — brutal strikes",
		"role_sabah": "The mountain — immovable",
		"role_kl": "All colours as one — the final master",
	},
	"ms": {
		"heritage": "Permainan warisan Melayu — pusing gasingmu, pangkah lawan, jadi juara gelanggang.",
		"fact": "Tahu tak? Gasing ialah sukan warisan di Kelantan dan Melaka.",
		"prompt": "Tekan SPACE untuk main sendirian",
		"wind_hint": "Tahan SPACE / tetikus kiri untuk memusing tali — lepas dalam zon HIJAU!  (A/D untuk sasaran)",
		"bench": "BENGKEL GASING",
		"duel_line": "Duel %d / %d  —  Lawan: %s",
		"craft_duel_line": "Duel %d / %d  —  Lawan seterusnya: %s",
		"mats_line": "Duit %d  ·  Merbau %d  ·  Kemuning %d  ·  Besi %d",
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
		"tip_stat_mass": "Jisim — kuasa pangkah.\nDaya hentaman ikut (jisimmu ÷ jisim lawan):\ngasing berat menolak jauh dan tahan ditolak.",
		"tip_stat_spin": "Pusingan — stamina gasing.\nPusingan mula = mutu lilitan × Pusingan, dan simpanan\nbesar susut lebih perlahan. Bertahan lebih lama.",
		"tip_stat_balance": "Imbangan — kestabilan bila pusingan susut.\nGoyangan mengecil bila Imbangan tinggi:\nlambat terhuyung, lambat tumbang.",
		"stat_legend": "Jisim = kuasa pangkah  ·  Pusingan = stamina  ·  Imbangan = kestabilan  (tuding pada stat untuk butiran)",
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
		"mp_code_label": "Kod Lobi:",
		"join_code": "SERTAI KOD",
		"share_code": "Kongsi kod ini: %s",
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
		"coin_award": "+%d duit diperoleh!",
		"now_purchasable": "Gasing %s kini boleh dibeli di bengkelmu!",
		"locked_beat": "Kalahkan %s untuk membuka pembelian ini.",
		"locked_mp": "Berkunci — beli dalam mod sendirian.",
		"bought": "%s dibeli — pusinglah elok-elok!",
		"need_coins": "Harga %d duit — kamu ada %d.",
		"price_tag": "Dijual — %d duit",
		"buy_prefix": "BELI: ",
		"mat_buy": "+1 · %d duit",
		"mat_bought": "+1 %s dibeli.",
		"customize": "Warna lakuer:",
		"cut_continue": "Klik / SPACE untuk sambung",
		"cut_skip": "LANGKAU",
		"endless": "GELANGGANG TANPA HENTI",
		"wave_line": "Gelombang %d  —  %s",
		"endless_over": "Gelombang diharungi: %d",
		"endless_best_line": "Terbaik: %d",
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
		"role_kelantan": "Jantung emas — cara lama",
		"role_penang": "Mercun — pangkah pantas",
		"role_melaka": "Sabar pedagang — pusingan panjang",
		"role_terengganu": "Ombak pecah — pangkah dan undur",
		"role_sarawak": "Guruh — pangkah padu",
		"role_sabah": "Gunung — teguh tak goyah",
		"role_kl": "Segala warna bersatu — mahaguru terakhir",
	},
}

var lang: String = "en"
var state: State = State.READY
# persistent workshop state (saved to SAVE_PATH; loaded once in _ready)
var player_shapes: Dictionary = {}
var materials_owned: Dictionary = {}
var selected_shape: String = "jantung"
var unlocked_styles: Array[String] = []
var coins: int = 0
var defeated_masters: Array[String] = [] # master ids beaten in the campaign (gates shop purchases)
var style_accents: Dictionary = {} # style_id -> Color, player-chosen lacquer trim (SP only)
var endless_best: int = 0
var endless_mode: bool = false
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
var ai_tier: float = 0.0 # 0..1.3 difficulty scalar, cached per battle in _do_launch
var ai_dodge_cd: float = 0.0 # reactive dodge cooldown — bounds the spin cost of dodging
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
var craft_index: int = 0 # roster position browsed in the fighter-select carousel (transient)
var craft_prev_button: Button = null
var craft_next_button: Button = null
var craft_name_label: Label = null
var craft_counter_label: Label = null
var craft_status_label: Label = null
var craft_stat_rows: Array = [] # 3 dicts from _mk_stat_row: mass, spin, balance
var craft_forge_box: Control = null
var material_buttons: Dictionary = {}
var material_buy_buttons: Dictionary = {}
var accent_row: HBoxContainer = null
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
	_polish_visuals()
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
		floor_mat.albedo_color = Color(0.54, 0.35, 0.17)
		floor_mat.roughness = 0.92
		floor_mat.normal_enabled = true
		floor_mat.normal_texture = dirt_normal
		floor_mat.normal_scale = 0.9
		floor_mat.uv1_scale = Vector3(9.0, 9.0, 9.0)
		floor_node.set_surface_override_material(0, floor_mat)

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
	return STRINGS[lang][key]


# ---------------------------------------------------------------- state flow

func _enter_state(next: State) -> void:
	state = next
	if next != State.CRAFT:
		_clear_preview()
	if next != State.READY:
		if is_instance_valid(menu_top):
			menu_top.queue_free()
		menu_top = null
		camera.h_offset = 0.0
		camera.v_offset = 0.0 # _camera_nudge owns v_offset in battle
	match next:
		State.READY:
			_clear_tops()
			_set_hud_visible(false)
			_apply_arena("kampung") # menu and every MP match run in the default arena
			_show_menu_screen(MenuScreen.TITLE)
			_update_menu_top()
			if ready_title != null:
				ready_title.scale = Vector2(1.14, 1.14)
				ready_title.modulate.a = 0.0
				var title_tw: Tween = create_tween().set_parallel(true)
				title_tw.tween_property(ready_title, "scale", Vector2.ONE, 0.5).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
				title_tw.tween_property(ready_title, "modulate:a", 1.0, 0.35)
		State.CRAFT:
			_clear_tops()
			_set_hud_visible(false)
			net_ready_sent = false
			net_opp_config = {}
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
		State.CRAFT:
			if event.is_action_pressed("ui_left"):
				get_viewport().set_input_as_handled()
				_craft_cycle(-1)
			elif event.is_action_pressed("ui_right"):
				get_viewport().set_input_as_handled()
				_craft_cycle(1)
		State.CUTSCENE:
			if event.is_action_pressed("ui_accept"):
				get_viewport().set_input_as_handled()
				_cutscene_advance()
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


func _process(_delta: float) -> void:
	if state == State.READY:
		# slow camera drift for a living title screen
		var t: float = Time.get_ticks_msec() * 0.001
		camera.h_offset = sin(t * 0.25) * 0.25
		camera.v_offset = cos(t * 0.2) * 0.1


func _update_menu_top() -> void:
	# a spinning showpiece beside the title — the player's current top (rainbow if it's the KL arcana)
	if is_instance_valid(menu_top):
		menu_top.queue_free()
	menu_top = null
	if state != State.READY:
		return
	var g: Gasing = GASING_SCENE.instantiate() as Gasing
	add_child(g)
	g.setup("", String(STYLE_DEFS[selected_shape].shape), _style_battle_stats(selected_shape), _style_accent(selected_shape))
	var vp: Vector2 = get_viewport().get_visible_rect().size
	var screen: Vector2 = Vector2(vp.x * 0.82, vp.y * 0.66)
	var hit: Variant = Plane(Vector3.UP, 0.0).intersects_ray(camera.project_ray_origin(screen), camera.project_ray_normal(screen))
	if hit != null:
		g.position = hit
	g.scale = Vector3(0.01, 0.01, 0.01)
	var tw: Tween = create_tween()
	tw.tween_property(g, "scale", Vector3(1.6, 1.6, 1.6), 0.4).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	menu_top = g


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
	workshop_preview = g
	# the camera's center ray hits the ground plane at the world origin, so the
	# hero top spins dead-center screen in the gelanggang ring — no unprojection
	workshop_preview.position = Vector3.ZERO
	workshop_preview.scale = Vector3(0.01, 0.01, 0.01)
	var tw: Tween = create_tween()
	tw.tween_property(workshop_preview, "scale", Vector3(2.6, 2.6, 2.6), 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


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
		# MP keeps the gold-you/teal-them convention; custom lacquer is SP-only
		var accent: Color = PLAYER_COLOR if net_active else _style_accent(selected_shape)
		g.setup(my_name, String(STYLE_DEFS[selected_shape].shape), _style_battle_stats(selected_shape), accent)
		g.position = Vector3(0.0, 0.0, 3.0)
	elif net_active:
		var opp_style: String = String(net_opp_config.get("shape", "jantung"))
		g.setup(String(net_opp_config.get("name", net_opp_name)), String(STYLE_DEFS[opp_style].shape), net_opp_config.get("stats", STYLE_DEFS["jantung"]), FOE_COLOR)
		g.position = Vector3(0.0, 0.0, -3.0)
	else:
		var opp: Dictionary = _current_opponent()
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
	var opp: Dictionary = _current_opponent()
	ai_tier = _ai_tier()
	# floor rises with tier (masters stop fumbling); cap 95 — rolls past 95 hit the
	# cord-snap penalty (eff 0.15), which made high-dev masters throw 1 in 5 launches
	var wind_floor: float = 40.0 + 35.0 * minf(ai_tier, 1.0) # knob
	var foe_wind: float = clampf(_rng.randfn(opp.wind_mean, opp.wind_dev), wind_floor, 95.0)
	var foe_eff: float = _wind_effectiveness(foe_wind)
	var foe_dir: Vector3 = Vector3.BACK.rotated(Vector3.UP, _rng.randf_range(-0.25, 0.25))
	foe_top.launch(foe_dir, foe_eff)
	last_striker = ""
	hit_cooldown = 0.0
	nudge_cooldown = 0.0
	ai_think_timer = 1.2
	ai_dodge_cd = 0.0
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


func _ai_tier() -> float:
	# campaign: 0.1 (duel 1) .. 1.1 (duel 7); endless keeps climbing past the campaign cap
	var t: float = clampf(0.2 + 0.12 * float(duel_index), 0.2, 1.3) if endless_mode \
		else 0.1 + float(duel_index) / 6.0
	if bool(_current_opponent().aggressive):
		t += 0.15 # knob: aggressive masters fight a notch above their stage
	return t


func _ai_think(delta: float) -> void:
	var skill: float = minf(ai_tier, 1.0) # aim/lead/power saturate; cadence keeps scaling via duel_index
	var foe_flat: Vector2 = Vector2(foe_top.position.x, foe_top.position.z)
	var foe_dist: float = foe_flat.length()
	var out_dir: Vector3 = Vector3(foe_flat.x, 0.0, foe_flat.y) / maxf(foe_dist, 0.001)
	var to_player: Vector3 = player_top.position - foe_top.position
	to_player.y = 0.0
	var sep: float = to_player.length()
	# continuous drift (free): survive first, then hunt. Whiffed charges are the
	# suicide vector (friction 0.8 can't stop a 4 m/s sail past RIM_CLIMB_SPEED 1.7),
	# hence the speed cap and radial emergency brake.
	if foe_dist > 2.7 and foe_top.velocity.dot(out_dir) > 1.2: # knob
		foe_top.velocity += -out_dir * 2.6 * delta # emergency brake: never charge over the rim
	elif foe_dist > 3.2:
		foe_top.velocity += -out_dir * 1.8 * delta # recover footing
	else:
		var lead: Vector3 = player_top.position + player_top.velocity * (0.15 + 0.3 * skill) # knob
		var lead_flat: Vector2 = Vector2(lead.x, lead.z)
		if lead_flat.length() > 3.4:
			lead_flat = lead_flat.normalized() * 3.4 # never chase a point in the rim band
		var hunt: Vector3 = Vector3(lead_flat.x, 0.0, lead_flat.y) - foe_top.position
		hunt.y = 0.0
		if hunt.length() > 0.2 and foe_top.velocity.length() < 2.6: # knob speed cap
			foe_top.velocity += hunt.normalized() * (1.3 + 1.5 * skill) * delta # knob
	# reactive dodge (all tiers): sidestep an incoming charge the moment it's seen.
	# Cooldown is consumed on detection whether the roll succeeds or not — a failed
	# roll means the AI got caught flat, and a yo-yo-charging player can't bait
	# dodges faster than the cooldown to drain the AI's spin.
	ai_dodge_cd = maxf(ai_dodge_cd - delta, 0.0)
	var charge_threat: bool = sep < 2.6 and player_top.velocity.length() > 1.6 \
		and player_top.velocity.normalized().dot(-to_player / maxf(sep, 0.001)) > 0.6 # knob
	if charge_threat and ai_dodge_cd <= 0.0 \
			and foe_top.spin - NUDGE_SPIN_COST >= 0.10 * foe_top.launch_spin:
		ai_dodge_cd = 1.5 - 0.9 * skill # knob: ready again in 0.6-1.5s
		if _rng.randf() < 0.35 + 0.6 * skill: # knob: low tiers flinch late, high tiers read every charge
			var perp: Vector3 = (to_player / maxf(sep, 0.001)).rotated(Vector3.UP, PI * 0.5)
			var dodge: Vector3 = perp if perp.dot(-out_dir) >= 0.0 else -perp # lean inward, never rimward
			foe_top.velocity += dodge * NUDGE_POWER * 1.15 # knob: enough to clear the combined radii
			foe_top.spin = maxf(foe_top.spin - NUDGE_SPIN_COST, 0.0)
			foe_top.flash_direction(dodge)
			ai_think_timer = minf(ai_think_timer, 0.25) # matador: counter-ram the exposed back
	# paid pushes on the think timer — the AI plays by the player's push rules
	ai_think_timer -= delta
	if ai_think_timer > 0.0:
		return
	ai_think_timer = maxf(1.3 - 0.12 * float(duel_index), 0.45) + _rng.randf_range(-0.15, 0.25) # knob
	# spin budget relative to launch_spin: wobble starts at 0.25x, topple at 0.08x —
	# an absolute floor could push the AI into topple range on weak launches
	var spin_after: float = foe_top.spin - NUDGE_SPIN_COST
	if spin_after < 0.10 * foe_top.launch_spin:
		return # hard floor: a push may never topple us
	var conserving: bool = spin_after < 0.30 * foe_top.launch_spin # knob
	var kill_shot: bool = player_top.wobble > foe_top.wobble + 0.1 # winning the wobble race
	var player_dist: float = Vector2(player_top.position.x, player_top.position.z).length()
	var push_dir: Vector3 = Vector3.ZERO
	var power: float = NUDGE_POWER
	if foe_dist > 3.0:
		push_dir = -out_dir # paid center recovery
	elif player_dist > 2.8 and foe_dist < 2.3 and sep < 1.8 and (not conserving or kill_shot):
		push_dir = to_player # RIM KILL: shove them over — plain power, tight gates make whiffs rare
	elif sep < 2.6 and (not conserving or kill_shot) \
			and (foe_top.mass >= player_top.mass * 0.9 or kill_shot
				or player_top.velocity.length() < 1.4): # knob
		# matador rule: an out-massed top loses even trades (mass ratio doubles the
		# damage against it), so it only rams a slow/parked or wobbling target and
		# otherwise saves spin — dodging the heavy top's charges bleeds the charger
		push_dir = player_top.position + player_top.velocity * (0.15 + 0.3 * skill) - foe_top.position
		power = NUDGE_POWER * (1.0 + 0.2 * skill) # knob: capped 1.2x — more only raises self-ringout risk
	push_dir.y = 0.0
	if push_dir.length() < 0.05:
		return # out of range: save the spin, keep drifting
	# low tiers attack but miss — aim error shrinks to surgical as skill rises
	push_dir = push_dir.normalized().rotated(Vector3.UP, _rng.randfn(0.0, 0.45 * (1.0 - skill))) # knob
	foe_top.velocity += push_dir * power
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
	_toast(template % top.display_name, DANGER, top.position, false)


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
	var opp: Dictionary = _current_opponent()
	if player_wins:
		_play_sfx(SND_WIN, -3.0, 0.02)
		round_label.text = _t("round_win")
		round_label.add_theme_color_override("font_color", PLAYER_COLOR)
		var counts: Dictionary = _grant_materials(_rng.randi_range(1, 2))
		_show_award_icons(round_award_row, counts, "+%d")
		mats_saved_label.text = _t("mats_saved")
		mats_saved_label.visible = true
		var wait: float = 2.4
		var reward: int = int(opp.get("coins", 40))
		coins += reward
		unlock_label.text = _t("coin_award") % reward
		unlock_label.add_theme_color_override("font_color", PLAYER_COLOR)
		unlock_label.visible = true
		if endless_mode:
			endless_best = maxi(endless_best, duel_index + 1)
		else:
			var mid: String = String(opp.id)
			if not defeated_masters.has(mid):
				defeated_masters.append(mid)
				unlock_label.text += "\n" + _t("now_purchasable") % String(opp.name)
				unlock_label.add_theme_color_override("font_color", opp.get("color", PLAYER_COLOR))
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
	elif not endless_mode and duel_index >= MASTERS.size():
		_finish_run(true)
	else:
		_enter_state(State.CRAFT)


func _finish_run(won: bool) -> void:
	run_won = won
	_play_sfx(SND_WIN if won else SND_LOSE, 0.0, 0.0)
	_reset_over_panel()
	if endless_mode:
		over_title.text = _t("over_lose")
		over_title.add_theme_color_override("font_color", DANGER)
		over_stats.text = _t("endless_over") % duel_index + "\n" + _t("endless_best_line") % endless_best
	else:
		over_title.text = _t("over_win") if won else _t("over_lose")
		over_title.add_theme_color_override("font_color", PLAYER_COLOR if won else DANGER)
		over_stats.text = _t("duels_won") % [duel_index, MASTERS.size()]
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
	m.arena = "kampung"
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
	coins = 0
	defeated_masters = []
	style_accents = {}
	endless_best = 0
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


func _save_workshop() -> void:
	if _netbot:
		return # two local netbot instances share user:// — don't clobber the real save
	var cf: ConfigFile = ConfigFile.new()
	cf.set_value("workshop", "version", 2)
	cf.set_value("workshop", "unlocked", unlocked_styles)
	cf.set_value("workshop", "selected", selected_shape)
	cf.set_value("workshop", "materials", materials_owned)
	cf.set_value("workshop", "shapes", player_shapes)
	cf.set_value("workshop", "coins", coins)
	cf.set_value("workshop", "defeated", defeated_masters)
	cf.set_value("workshop", "accents", style_accents)
	cf.set_value("workshop", "endless_best", endless_best)
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
	var viewed: String = _craft_viewed()
	if not unlocked_styles.has(viewed):
		_on_shape_selected(viewed) # FIGHT doubles as BUY: reuse the gate/buy/need-coins flow
		return
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
	if endless_mode:
		_apply_arena("kampung")
		_enter_state(State.WIND)
		return
	var master: Dictionary = MASTERS[mini(duel_index, MASTERS.size() - 1)]
	_apply_arena(String(master.get("arena", "kampung"))) # swap happens behind the kelir
	if CUTSCENES.has(String(master.id)):
		_enter_state(State.CUTSCENE)
	else:
		_enter_state(State.WIND)


func _on_lang_pressed(code: String) -> void:
	lang = code
	_apply_language()


func _craft_viewed() -> String:
	return STYLE_DEFS.keys()[craft_index]


func _craft_cycle(dir: int) -> void:
	if net_active and net_ready_sent:
		return # config already on the wire; a late switch would desync the peers
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
			coins -= price
			unlocked_styles.append(id)
			selected_shape = id
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
	craft_info.text = _t("selected_info") % String(STYLE_DEFS[id].label)
	_save_workshop()
	_refresh_craft()
	_update_workshop_preview()


func _on_material_pressed(mat_id: String) -> void:
	if net_active: return # MP is equal-footing; forging is disabled
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


func _on_accent_selected(c: Color) -> void:
	if net_active:
		return # MP tops are always gold/teal
	style_accents[selected_shape] = c
	_save_workshop()
	_update_workshop_preview() # live: the spinning preview rebuilds with the new lacquer


func _on_material_bought(mat_id: String) -> void:
	if net_active:
		return # MP is equal-footing; no economy
	var price: int = int(MAT_PRICES[mat_id])
	if coins < price:
		craft_info.text = _t("need_coins") % [price, coins]
		return
	coins -= price
	materials_owned[mat_id] += 1
	craft_info.text = _t("mat_bought") % String(MATERIAL_DEFS[mat_id].label)
	_save_workshop()
	_refresh_craft()
	_update_top_bar()


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
	l.add_theme_color_override("font_outline_color", Color(0.0, 0.0, 0.0, 0.9))
	l.add_theme_constant_override("outline_size", 4)
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
		var opp: Dictionary = _current_opponent()
		if endless_mode:
			duel_label.text = _t("wave_line") % [duel_index + 1, opp.name]
		else:
			duel_label.text = _t("duel_line") % [mini(duel_index + 1, MASTERS.size()), MASTERS.size(), opp.name]
	mats_label.text = _t("mats_line") % [coins, materials_owned.merbau, materials_owned.kemuning, materials_owned.besi]


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
	craft_info.text = _t("pick_info")
	fight_button.text = _t("fight")
	restart_button.text = _t("restart")
	over_hint.text = _t("or_space")
	sp_button.text = _t("single_player")
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
	if accent_label != null:
		accent_label.text = _t("customize")
	for code: String in lang_buttons:
		var b: Button = lang_buttons[code]
		b.modulate = Color(1.0, 1.0, 1.0, 1.0) if code == lang else Color(0.55, 0.55, 0.55, 1.0)
	_update_top_bar()
	_refresh_craft()


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
	var txt_col: Color = TEXT_COLOR if light_text else Color(0.12, 0.07, 0.03)
	b.add_theme_color_override("font_color", txt_col)
	b.add_theme_color_override("font_hover_color", txt_col)
	b.add_theme_color_override("font_pressed_color", txt_col.darkened(0.2) if not light_text else txt_col)
	b.add_theme_color_override("font_disabled_color", Color(txt_col.r, txt_col.g, txt_col.b, 0.45))
	# neutral-bright carved plaque texture x modulate = plaque in any wood tone
	var sb: StyleBoxTexture = StyleBoxTexture.new()
	sb.texture = TEX_BTN
	sb.set_texture_margin_all(20.0)
	sb.content_margin_left = 14.0
	sb.content_margin_right = 14.0
	sb.content_margin_top = 8.0
	sb.content_margin_bottom = 8.0
	sb.modulate_color = base
	b.add_theme_stylebox_override("normal", sb)
	var sb_h: StyleBoxTexture = sb.duplicate()
	sb_h.modulate_color = base.lightened(0.18)
	b.add_theme_stylebox_override("hover", sb_h)
	var sb_p: StyleBoxTexture = sb.duplicate()
	sb_p.modulate_color = base.darkened(0.28)
	b.add_theme_stylebox_override("pressed", sb_p)
	var sb_d: StyleBoxTexture = sb.duplicate()
	sb_d.modulate_color = base.darkened(0.45)
	b.add_theme_stylebox_override("disabled", sb_d)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.focus_mode = Control.FOCUS_NONE # arrows must reach _unhandled_input (carousel), not focus-nav
	b.pressed.connect(_on_any_button_pressed)
	return b


func _on_any_button_pressed() -> void:
	_play_sfx(SND_CLICK, -6.0, 0.05)


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
	t.modulate = Color(1.0, 0.78, 0.25, 0.85)
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return t


func _mk_divider() -> Control:
	# songket band separator
	var d: HSeparator = HSeparator.new()
	var sb: StyleBoxTexture = StyleBoxTexture.new()
	sb.texture = TEX_SONGKET
	sb.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
	sb.modulate_color = Color(SONGKET_GOLD, 0.85)
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
	var bg: StyleBoxFlat = StyleBoxFlat.new()
	bg.bg_color = Color(0.05, 0.025, 0.01, 0.75) # recessed carved groove
	bg.set_corner_radius_all(4)
	bg.border_width_bottom = 1
	bg.border_color = Color(0.55, 0.38, 0.16, 0.35) # light catching the groove's lower lip
	bar.add_theme_stylebox_override("background", bg)
	# layered: bottom bar shows the forged total in a brighter tint; the overlay
	# draws the base on top, so the bright sliver past it reads as forged bonus
	var fill: StyleBoxTexture = StyleBoxTexture.new()
	fill.texture = TEX_SONGKET
	fill.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE # weave repeats, never stretches
	fill.modulate_color = fill_color.lightened(0.5) if layered else fill_color
	bar.add_theme_stylebox_override("fill", fill)
	var over: ProgressBar = null
	if layered:
		over = ProgressBar.new()
		over.max_value = 1.0
		over.show_percentage = false
		over.set_anchors_preset(Control.PRESET_FULL_RECT)
		over.mouse_filter = Control.MOUSE_FILTER_IGNORE
		over.add_theme_stylebox_override("background", StyleBoxEmpty.new())
		var ofill: StyleBoxTexture = StyleBoxTexture.new()
		ofill.texture = TEX_SONGKET
		ofill.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
		ofill.modulate_color = fill_color
		over.add_theme_stylebox_override("fill", ofill)
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
	wind_meter.offset_right = 110.0 # widened for the coil bulge
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


func _build_ready_panel() -> void:
	ready_panel = _mk_fullrect_center()
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	ready_panel.add_child(v)
	v.add_child(_mk_gunungan(44.0))
	ready_title = _mk_title("GASING PANGKAH", 64)
	ready_title.add_theme_constant_override("outline_size", 10) # bigger outline on the hero title
	ready_title.add_theme_constant_override("shadow_offset_y", 4)
	v.add_child(ready_title)
	ready_heritage = _mk_label("", 19)
	v.add_child(ready_heritage)
	ready_fact = _mk_label("", 14, CREAM_MUTED)
	v.add_child(ready_fact)
	var menu_col: VBoxContainer = VBoxContainer.new()
	menu_col.add_theme_constant_override("separation", 10)
	menu_col.custom_minimum_size = Vector2(260.0, 0.0)
	sp_button = _mk_button("", PLAYER_COLOR)
	sp_button.add_theme_font_size_override("font_size", 20)
	sp_button.pressed.connect(_on_single_player_pressed)
	menu_col.add_child(sp_button)
	endless_button = _mk_button("", PANDAN)
	endless_button.add_theme_font_size_override("font_size", 20)
	endless_button.pressed.connect(_on_endless_pressed)
	menu_col.add_child(endless_button)
	mp_button = _mk_button("", WOOD_AMBER)
	mp_button.add_theme_font_size_override("font_size", 20)
	mp_button.pressed.connect(_on_multiplayer_pressed)
	menu_col.add_child(mp_button)
	quit_button = _mk_button("", WOOD_DARK, true)
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
		var b: Button = _mk_button(entry[1], WOOD_DARK, true)
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
	v.add_child(_mk_gunungan(32.0))
	mp_title = _mk_title("", 26)
	v.add_child(mp_title)
	mp_steam_header_label = _mk_label("", 14, CREAM_MUTED)
	v.add_child(mp_steam_header_label)
	host_steam_button = _mk_button("", WOOD_AMBER)
	host_steam_button.pressed.connect(_on_host_steam_pressed)
	var hs_wrap: CenterContainer = CenterContainer.new()
	hs_wrap.add_child(host_steam_button)
	v.add_child(hs_wrap)
	steam_join_hint_label = _mk_label("", 12, Color(0.78, 0.7, 0.56))
	v.add_child(steam_join_hint_label)
	var code_row: HBoxContainer = HBoxContainer.new()
	code_row.add_theme_constant_override("separation", 8)
	code_row.alignment = BoxContainer.ALIGNMENT_CENTER
	mp_code_label = _mk_label("", 14)
	code_row.add_child(mp_code_label)
	join_code_edit = _mk_line_edit("ABC123")
	join_code_edit.text_submitted.connect(func(_txt: String) -> void: _on_join_code_pressed())
	code_row.add_child(join_code_edit)
	join_code_button = _mk_button("", WOOD_AMBER)
	join_code_button.pressed.connect(_on_join_code_pressed)
	code_row.add_child(join_code_button)
	v.add_child(code_row)
	steam_offline_label = _mk_label("", 13, DANGER)
	steam_offline_label.visible = false
	v.add_child(steam_offline_label)
	v.add_child(_mk_divider())
	mp_lan_header_label = _mk_label("", 14, CREAM_MUTED)
	v.add_child(mp_lan_header_label)
	host_lan_button = _mk_button("", WOOD_AMBER)
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
	join_lan_button = _mk_button("", WOOD_AMBER)
	join_lan_button.pressed.connect(_on_join_lan_pressed)
	join_row.add_child(join_lan_button)
	v.add_child(join_row)
	mp_back_button = _mk_button("", WOOD_DARK, true)
	mp_back_button.pressed.connect(_on_mp_back_pressed)
	var back_wrap: CenterContainer = CenterContainer.new()
	back_wrap.add_child(mp_back_button)
	v.add_child(back_wrap)


func _build_wait_panel() -> void:
	wait_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box(true, 6.0) # short panel: slim frame, no tall art to squash
	wait_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	box.add_child(v)
	wait_title = _mk_title("", 26)
	v.add_child(wait_title)
	wait_info = _mk_label("", 15)
	v.add_child(wait_info)
	invite_button = _mk_button("", WOOD_AMBER)
	invite_button.visible = false
	invite_button.pressed.connect(_on_invite_friend_pressed)
	var iv_wrap: CenterContainer = CenterContainer.new()
	iv_wrap.add_child(invite_button)
	v.add_child(iv_wrap)
	wait_cancel_button = _mk_button("", WOOD_DARK, true)
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
	# recessed carved slot (like the stat-bar grooves) — the 9-patch card frame
	# can't survive a ~34px-tall control, its corner patches overlap
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.025, 0.01, 0.9)
	sb.set_corner_radius_all(5)
	sb.set_border_width_all(1)
	sb.border_color = BORDER_BROWN
	sb.content_margin_left = 10.0
	sb.content_margin_right = 10.0
	sb.content_margin_top = 6.0
	sb.content_margin_bottom = 6.0
	e.add_theme_stylebox_override("normal", sb)
	var sb_f: StyleBoxFlat = sb.duplicate()
	sb_f.border_color = PLAYER_COLOR # gold rim while typing
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
	# top show through; header on top, roster arrows at the sides, stats + forge
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
	header_wrap.add_child(header)
	var hv: VBoxContainer = VBoxContainer.new()
	hv.add_theme_constant_override("separation", 2)
	header.add_child(hv)
	craft_title = _mk_title("", 24)
	hv.add_child(craft_title)
	craft_duel_label = _mk_label("", 16)
	hv.add_child(craft_duel_label)
	craft_sub = _mk_label("", 13, CREAM_MUTED)
	craft_sub.visible = false
	hv.add_child(craft_sub)

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
	# grown upward, so it can never overflow the 720px viewport like the old grid
	var sheet: PanelContainer = _mk_panel_box(true, 6.0)
	sheet.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	sheet.offset_left = 80.0
	sheet.offset_right = -80.0
	sheet.offset_top = -12.0
	sheet.offset_bottom = -12.0
	sheet.grow_vertical = Control.GROW_DIRECTION_BEGIN
	craft_panel.add_child(sheet)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 5)
	sheet.add_child(v)

	var name_row: HBoxContainer = HBoxContainer.new()
	name_row.alignment = BoxContainer.ALIGNMENT_CENTER
	name_row.add_theme_constant_override("separation", 10)
	v.add_child(name_row)
	craft_name_label = _mk_title("", 22)
	name_row.add_child(craft_name_label)
	craft_counter_label = _mk_label("", 13, CREAM_MUTED)
	craft_counter_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	name_row.add_child(craft_counter_label)
	craft_status_label = _mk_label("", 14)
	v.add_child(craft_status_label)

	var stats_row: HBoxContainer = HBoxContainer.new()
	stats_row.alignment = BoxContainer.ALIGNMENT_CENTER
	stats_row.add_theme_constant_override("separation", 24)
	v.add_child(stats_row)
	craft_stat_rows = [
		_mk_stat_row(stats_row, Color(0.85, 0.45, 0.25), true),
		_mk_stat_row(stats_row, Color(0.35, 0.75, 0.9), true),
		_mk_stat_row(stats_row, Color(0.5, 0.85, 0.4), true),
	]
	for r: Dictionary in craft_stat_rows:
		(r.bar as ProgressBar).custom_minimum_size = Vector2(130.0, 14.0)

	craft_mats_hint = _mk_label("", 14)
	v.add_child(craft_mats_hint)
	var forge_box: HBoxContainer = HBoxContainer.new()
	forge_box.alignment = BoxContainer.ALIGNMENT_CENTER
	forge_box.add_theme_constant_override("separation", 20)
	v.add_child(forge_box)
	craft_forge_box = forge_box
	for mat_id: String in MATERIAL_DEFS:
		var mat_col: VBoxContainer = VBoxContainer.new()
		mat_col.add_theme_constant_override("separation", 4)
		forge_box.add_child(mat_col)
		var mb: Button = _mk_button("", WOOD_DARK, true)
		mb.icon = load("res://assets/icon_%s.png" % mat_id)
		mb.add_theme_constant_override("icon_max_width", 38)
		mb.add_theme_constant_override("h_separation", 8)
		mb.pressed.connect(_on_material_pressed.bind(mat_id))
		mat_col.add_child(mb)
		material_buttons[mat_id] = mb
		var buy: Button = _mk_button("", WOOD_AMBER, true)
		buy.add_theme_font_size_override("font_size", 12)
		buy.pressed.connect(_on_material_bought.bind(mat_id))
		mat_col.add_child(buy)
		material_buy_buttons[mat_id] = buy

	accent_row = HBoxContainer.new()
	accent_row.add_theme_constant_override("separation", 8)
	accent_row.alignment = BoxContainer.ALIGNMENT_CENTER
	forge_box.add_child(accent_row)
	accent_label = _mk_label("", 13)
	accent_row.add_child(accent_label)
	for c: Color in ACCENT_CHOICES:
		var sw: Button = Button.new()
		sw.custom_minimum_size = Vector2(26.0, 26.0)
		sw.size_flags_vertical = Control.SIZE_SHRINK_CENTER # don't stretch to the forge row's height
		sw.focus_mode = Control.FOCUS_NONE
		var sb: StyleBoxFlat = StyleBoxFlat.new()
		sb.bg_color = c
		sb.set_corner_radius_all(6)
		sw.add_theme_stylebox_override("normal", sb)
		var sbh: StyleBoxFlat = sb.duplicate()
		sbh.bg_color = c.lightened(0.25)
		sw.add_theme_stylebox_override("hover", sbh)
		sw.add_theme_stylebox_override("pressed", sb)
		sw.pressed.connect(_on_accent_selected.bind(c))
		accent_row.add_child(sw)

	craft_info = _mk_label("", 14, Color(0.85, 0.8, 0.65))
	v.add_child(craft_info)
	craft_opp_status = _mk_label("", 14, FOE_COLOR)
	craft_opp_status.visible = false
	v.add_child(craft_opp_status)
	fight_button = _mk_button("", PLAYER_COLOR)
	fight_button.add_theme_font_size_override("font_size", 22)
	fight_button.pressed.connect(_on_fight_pressed)
	craft_back_button = _mk_button("", WOOD_DARK, true)
	craft_back_button.pressed.connect(_on_over_menu_pressed) # SP: reset run -> title; MP: leave lobby -> title
	var btn_row: HBoxContainer = HBoxContainer.new()
	btn_row.add_theme_constant_override("separation", 16)
	btn_row.alignment = BoxContainer.ALIGNMENT_CENTER
	btn_row.add_child(craft_back_button)
	btn_row.add_child(fight_button)
	v.add_child(btn_row)


func _build_cutscene_panel() -> void:
	# the kelir: a backlit cloth screen with a swaying shadow puppet and narration
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
	var grad: Gradient = Gradient.new()
	grad.set_color(0, Color(0.98, 0.85, 0.55))
	grad.set_color(1, Color(0.24, 0.10, 0.04))
	grad.add_point(0.45, Color(0.75, 0.45, 0.18))
	var gt: GradientTexture2D = GradientTexture2D.new()
	gt.gradient = grad
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.42)
	gt.fill_to = Vector2(0.5, 1.1)
	kelir.texture = gt
	kelir.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cutscene_panel.add_child(kelir)
	for side_right: bool in [false, true]:
		var frame: ColorRect = ColorRect.new() # the wooden banana-trunk frame edges
		frame.color = Color(0.12, 0.05, 0.02)
		frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
		frame.set_anchors_preset(Control.PRESET_RIGHT_WIDE if side_right else Control.PRESET_LEFT_WIDE)
		frame.offset_right = 0.0 if side_right else 26.0
		frame.offset_left = -26.0 if side_right else 0.0
		cutscene_panel.add_child(frame)

	cut_puppet = TextureRect.new()
	cut_puppet.anchor_left = 0.52
	cut_puppet.anchor_right = 0.94
	cut_puppet.anchor_top = 0.06
	cut_puppet.anchor_bottom = 0.66
	cut_puppet.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cut_puppet.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	cut_puppet.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cut_puppet.modulate = Color(0.10, 0.05, 0.03) # silhouette against the lamp
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
	cut_name_label = _mk_label("", 22, PLAYER_COLOR)
	cut_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	tv.add_child(cut_name_label)
	cut_text = _mk_label("", 16)
	cut_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	cut_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cut_text.custom_minimum_size = Vector2(0.0, 84.0)
	cut_text.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	tv.add_child(cut_text)
	cut_hint = _mk_label("", 12, Color(0.8, 0.68, 0.5))
	cut_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	tv.add_child(cut_hint)

	cut_skip_button = _mk_button("", WOOD_DARK, true)
	cut_skip_button.set_anchors_preset(Control.PRESET_TOP_RIGHT)
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
	cut_name_label.text = "%s  —  %s" % [String(m.name), String(m["region_" + lang])]
	cut_name_label.add_theme_color_override("font_color", m.get("color", PLAYER_COLOR))
	cut_hint.text = _t("cut_continue")
	cut_skip_button.text = _t("cut_skip")
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
	if _cut_idx >= _cut_pars.size():
		_cutscene_finish()
		return
	cut_text.text = String(_cut_pars[_cut_idx])
	cut_text.visible_ratio = 0.0
	_cut_tween = create_tween()
	_cut_tween.tween_property(cut_text, "visible_ratio", 1.0, maxf(cut_text.text.length() / 42.0, 0.6))


func _cutscene_finish() -> void:
	if state != State.CUTSCENE:
		return
	if _cut_tween != null and _cut_tween.is_valid():
		_cut_tween.kill()
	if _puppet_tween != null and _puppet_tween.is_valid():
		_puppet_tween.kill()
	_enter_state(State.WIND)


func _build_round_panel() -> void:
	round_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box(true, 12.0) # short panel: slim frame, roomy
	round_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	box.add_child(v)
	round_label = _mk_title("", 30)
	v.add_child(round_label)
	round_award_row = HBoxContainer.new()
	round_award_row.add_theme_constant_override("separation", 14)
	round_award_row.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(round_award_row)
	mats_saved_label = _mk_label("", 13, CREAM_MUTED)
	mats_saved_label.visible = false
	v.add_child(mats_saved_label)
	unlock_label = _mk_label("", 20, PLAYER_COLOR)
	unlock_label.visible = false
	v.add_child(unlock_label)
	match_point_label = _mk_label("", 20, DANGER)
	match_point_label.visible = false
	v.add_child(match_point_label)
	award_label = _mk_label("", 18)
	v.add_child(award_label)


func _build_over_panel() -> void:
	over_panel = _mk_fullrect_center()
	var box: PanelContainer = _mk_panel_box(true, 12.0) # mid-height panel: slim frame, roomy
	over_panel.add_child(box)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	box.add_child(v)
	v.add_child(_mk_gunungan(32.0))
	over_title = _mk_title("", 34)
	over_stats = _mk_label("", 18)
	v.add_child(over_title)
	v.add_child(over_stats)
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
	if net_active:
		craft_duel_label.text = _t("score_line") % [net_my_wins, net_opp_wins, net_opp_name]
	else:
		var opp: Dictionary = _current_opponent()
		if endless_mode:
			craft_duel_label.text = _t("wave_line") % [duel_index + 1, opp.name]
		else:
			craft_duel_label.text = _t("craft_duel_line") % [mini(duel_index + 1, MASTERS.size()), MASTERS.size(), opp.name]
	craft_sub.visible = net_active
	craft_opp_status.visible = net_active

	var viewed: String = _craft_viewed()
	var def: Dictionary = STYLE_DEFS[viewed]
	var locked: bool = not unlocked_styles.has(viewed)
	var idx: int = _master_index(viewed)
	var gated: bool = idx >= 0 and not defeated_masters.has(String(MASTERS[idx].id))
	var buyable: bool = locked and not net_active and not gated

	craft_name_label.text = String(def.label)
	craft_counter_label.text = "%d / %d" % [craft_index + 1, STYLE_DEFS.size()]
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
		craft_status_label.add_theme_color_override("font_color", Color(0.78, 0.7, 0.56))

	var stats: Dictionary = def if net_active else player_shapes[viewed] # MP shows base = what you fight with
	_tween_bar(craft_stat_rows[0].bar, (stats.mass - 1.4) / 1.6)
	_tween_bar(craft_stat_rows[1].bar, (stats.spin_reserve - 60.0) / 50.0)
	_tween_bar(craft_stat_rows[2].bar, (stats.balance - 55.0) / 30.0)
	_tween_bar(craft_stat_rows[0].over, (def.mass - 1.4) / 1.6)
	_tween_bar(craft_stat_rows[1].over, (def.spin_reserve - 60.0) / 50.0)
	_tween_bar(craft_stat_rows[2].over, (def.balance - 55.0) / 30.0)

	# forging/recoloring targets selected_shape, so hide the forge while browsing
	# a locked style (selected_shape is some other top) and in MP (equal footing)
	var forging: bool = not net_active and not locked
	craft_forge_box.visible = forging
	craft_mats_hint.visible = forging
	craft_mats_hint.text = _t("mats_hint") + "  ·  %d duit" % coins
	for mat_id: String in MATERIAL_DEFS:
		var mdef: Dictionary = MATERIAL_DEFS[mat_id]
		material_buttons[mat_id].text = "%s ×%d\n%s" % [mdef.label, materials_owned.get(mat_id, 0), _t("desc_" + mat_id)]
		material_buy_buttons[mat_id].text = _t("mat_buy") % int(MAT_PRICES[mat_id])

	# the confirm button doubles as the BUY button on a locked-but-buyable style
	fight_button.text = (_t("buy_prefix") + String(def.label)) if buyable else _t("fight")
	fight_button.modulate = Color(1.0, 0.78, 0.6) if buyable else Color(1.0, 1.0, 1.0)
	fight_button.disabled = (locked and not buyable) or (net_active and net_ready_sent)


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
	# MP is equal-footing: send base stats, matching _style_battle_stats (else the peers desync).
	var base: Dictionary = STYLE_DEFS[selected_shape]
	return {
		"name": Online.personal_player_data.display_name,
		"shape": selected_shape,
		"stats": {"mass": base.mass, "spin_reserve": base.spin_reserve, "balance": base.balance},
	}


func _net_setup() -> void:
	net_active = true
	endless_mode = false
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
	over_title.add_theme_color_override("font_color", PLAYER_COLOR if i_won else DANGER)
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
		over_title.add_theme_color_override("font_color", DANGER)
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
		# belah-ketupat diamonds (songket motif), filled vs hollow
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
				draw_polyline(outline, Color(1.0, 1.0, 1.0, 0.25), 2.0, true)


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
		# carved groove track with rims + gold compass notches (ukiran ring)
		draw_arc(c, r, 0.0, TAU, 48, Color(0.16, 0.09, 0.05, 0.85), 10.0, true)
		draw_arc(c, r + 5.5, 0.0, TAU, 48, Color(0.55, 0.38, 0.16, 0.55), 1.5, true)
		draw_arc(c, r - 5.5, 0.0, TAU, 48, Color(0.55, 0.38, 0.16, 0.55), 1.5, true)
		for i: int in 8:
			var a: float = -PI / 2.0 + float(i) * TAU / 8.0
			var dir: Vector2 = Vector2(cos(a), sin(a))
			draw_line(c + dir * (r - 4.0), c + dir * (r + 4.0), Color(1.0, 0.78, 0.25, 0.45), 2.0, true)
		var col: Color = ring_color
		if wobbling:
			col = ring_color.lerp(Color(1.0, 0.3, 0.2), 0.5 + 0.5 * sin(_flash))
		if shown > 0.004:
			var a1: float = -PI / 2.0 + TAU * clampf(shown, 0.0, 1.0)
			draw_arc(c, r, -PI / 2.0, a1, 48, col, 7.0, true)
			draw_circle(c + Vector2(0.0, -r), 3.5, col)
			draw_circle(c + Vector2(cos(a1), sin(a1)) * r, 3.5, col)
		var f: Font = get_theme_default_font()
		draw_string(f, Vector2(0.0, c.y + 7.0), str(int(round(shown * 100.0))), HORIZONTAL_ALIGNMENT_CENTER, size.x, 20, col)
		draw_string(f, Vector2(0.0, size.x + 18.0), title, HORIZONTAL_ALIGNMENT_CENTER, size.x, 14, Color(0.96, 0.9, 0.78))


class WindMeter:
	extends Control
	# a cord winding around a gasing spindle: coils stack as you charge;
	# the 80-95 sweet spot is a songket gold band, >95 is overwind

	const ROPE: Color = Color(0.78, 0.62, 0.42)
	const ROPE_DARK: Color = Color(0.35, 0.25, 0.15)
	const WOOD: Color = Color(0.32, 0.20, 0.10)
	const WOOD_EDGE_C: Color = Color(0.16, 0.09, 0.05)
	const GOLD: Color = Color(1.0, 0.78, 0.25)
	const CREAM: Color = Color(0.96, 0.9, 0.78)
	const COIL_H: float = 7.0
	const SONGKET_TEX: Texture2D = preload("res://assets/ui/songket_band.png")

	var power: float = 0.0
	var shown: float = 0.0
	var label_text: String = "WIND"

	func _ready() -> void:
		custom_minimum_size = Vector2(64.0, 270.0)
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _process(delta: float) -> void:
		shown = lerpf(shown, power, minf(10.0 * delta, 1.0))
		queue_redraw()

	func _y(v: float) -> float:
		return size.y * (1.0 - v / 100.0)

	func _hw(y: float) -> float:
		return lerpf(7.0, 11.0, y / size.y) # shaft tapers top -> bottom

	func _draw() -> void:
		var cx: float = size.x * 0.5
		# spindle shaft
		var shaft: PackedVector2Array = PackedVector2Array([
			Vector2(cx - _hw(0.0), 0.0), Vector2(cx + _hw(0.0), 0.0),
			Vector2(cx + _hw(size.y), size.y), Vector2(cx - _hw(size.y), size.y)])
		draw_colored_polygon(shaft, WOOD)
		draw_line(shaft[0], shaft[3], WOOD_EDGE_C, 2.0, true)
		draw_line(shaft[1], shaft[2], WOOD_EDGE_C, 2.0, true)
		draw_line(Vector2(cx - 2.5, 3.0), Vector2(cx - 3.5, size.y - 3.0), WOOD.lightened(0.35), 2.5, true)
		# zone semantics preserved: 40-80 amber wash, 80-95 songket sweet band, >95 overwind
		draw_rect(Rect2(Vector2(6.0, _y(80.0)), Vector2(size.x - 12.0, _y(40.0) - _y(80.0))), Color(0.9, 0.7, 0.2, 0.16), true)
		draw_texture_rect_region(SONGKET_TEX, Rect2(Vector2(2.0, _y(95.0)), Vector2(size.x - 4.0, _y(80.0) - _y(95.0))),
			Rect2(0.0, 0.0, 64.0, 32.0), Color(GOLD, 0.9))
		draw_rect(Rect2(Vector2(6.0, 0.0), Vector2(size.x - 12.0, _y(95.0))), Color(0.95, 0.2, 0.15, 0.30), true)
		for v: float in [80.0, 95.0]:
			var yv: float = _y(v)
			draw_line(Vector2(0.0, yv), Vector2(9.0, yv), GOLD, 2.0, true)
			draw_line(Vector2(size.x - 9.0, yv), Vector2(size.x, yv), GOLD, 2.0, true)
		# tip color: same thresholds as the old bar (readability preserved)
		var tip: Color = Color(0.55, 0.6, 0.75)
		if shown > 95.0:
			tip = Color(1.0, 0.25, 0.2)
		elif shown >= 80.0:
			tip = Color(0.25, 0.95, 0.35)
		elif shown >= 40.0:
			tip = Color(0.95, 0.75, 0.25)
		# cord coils stack bottom -> _y(shown)
		var fill_top: float = _y(shown)
		var n: int = int((size.y - fill_top) / COIL_H)
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
		# label on a small wood plaque
		var f: Font = get_theme_default_font()
		draw_rect(Rect2(Vector2(2.0, -26.0), Vector2(size.x - 4.0, 20.0)), Color(WOOD_EDGE_C, 0.85), true)
		draw_rect(Rect2(Vector2(2.0, -26.0), Vector2(size.x - 4.0, 20.0)), Color(GOLD, 0.5), false, 1.0)
		draw_string(f, Vector2(0.0, -11.0), label_text, HORIZONTAL_ALIGNMENT_CENTER, size.x, 13, CREAM)
