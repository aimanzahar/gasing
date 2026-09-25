shader_type spatial;
// Painted gelanggang markings, drawn on a plane just above the dish floor (main.gd _polish_visuals):
// a songket medallion at the centre (bunga petals + pucuk rebung ring) and a darker danger band
// where the rope is near (band_inner .. 4.2 m), edged with inward pucuk rebung teeth and a gold thread.
render_mode blend_mix, depth_draw_never, cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec4 band_color : source_color = vec4(0.16, 0.09, 0.05, 0.6);
uniform vec4 inlay_color : source_color = vec4(1.0, 0.78, 0.25, 0.5);
uniform float band_inner = 3.6;
uniform float dish_edge = 4.15; // Floor cylinder top radius is 4.2; the Rim rope covers 3.95..4.35

varying vec2 p;

void vertex() {
	p = VERTEX.xz;
}

// 1 on a ring of half-width w around d == 0, anti-aliased by aa
float thread(float d, float w, float aa) {
	return 1.0 - smoothstep(w - aa, w + aa, abs(d));
}

// 0 at a tooth's centre line, 1 at the gap between teeth
float saw(float a, float count) {
	return abs(fract(a / TAU * count) - 0.5) * 2.0;
}

void fragment() {
	float r = length(p);
	float a = atan(p.y, p.x);
	float aa = max(fwidth(r), 0.002);
	float dark = 0.0;
	float gold = 0.0;

	// danger band (clipped at the dish edge, under the rope) + inward teeth (depth 0.24)
	// + gold thread just inside the tooth tips
	dark = smoothstep(band_inner - aa, band_inner + aa, r) * (1.0 - smoothstep(dish_edge - aa, dish_edge + aa, r));
	float tooth = band_inner - 0.24 * (1.0 - saw(a, 40.0));
	dark = max(dark, smoothstep(tooth - aa, tooth + aa, r) * step(r, band_inner + aa));
	gold = max(gold, thread(r - (band_inner - 0.32), 0.018, aa));

	// medallion: double gold ring, lacquer disc, outward pucuk rebung ring, 8-petal bunga, dark boss
	gold = max(gold, thread(r - 1.0, 0.03, aa));
	gold = max(gold, thread(r - 0.88, 0.012, aa));
	float disc = 1.0 - smoothstep(0.86 - aa, 0.86 + aa, r);
	float rebung_tip = 0.5 + 0.32 * (1.0 - saw(a + TAU / 32.0, 16.0));
	float rebung = (1.0 - smoothstep(rebung_tip - aa, rebung_tip + aa, r)) * smoothstep(0.5 - aa, 0.5 + aa, r);
	float petal_r = 0.42 * (0.3 + 0.7 * pow(abs(cos(a * 4.0)), 1.4));
	float petal = 1.0 - smoothstep(petal_r - aa, petal_r + aa, r);
	float boss = 1.0 - smoothstep(0.08 - aa, 0.08 + aa, r);
	gold = max(gold, max(rebung, petal) * (1.0 - boss));
	dark = max(dark, disc * 0.45);
	dark = max(dark, boss);

	vec3 col = mix(band_color.rgb, inlay_color.rgb, gold);
	ALBEDO = col;
	ALPHA = max(dark * band_color.a, gold * inlay_color.a);
	ROUGHNESS = 0.9;
	SPECULAR = 0.2;
}
