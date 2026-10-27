# Trailer score for Gasing Pangkah: 60.000 s, 128 BPM, every hit locked to trailer/cues.json.
# Reuses tools/gen_audio.py's synth (never its write(), which targets assets/). Writes trailer/trailer_score.wav
# (44.1 kHz, 16-bit, stereo, exactly 2,646,000 samples) and prints the verification tables.
# Run from the project root: python tools/gen_trailer_audio.py
import json
import os
import sys

import numpy as np
import scipy.signal as ss
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_audio as ga  # noqa: E402
from gen_audio import (SR, T, Mix, Scale, SLENDRO, PELOG_BEM, parse, partials, saron, gender, slenthem, bonang,  # noqa: E402
	kenong, kempul, gong_ageng, ketuk, dhung, tung, tak, tap, pak, bum, kesi, wind_line, bp_noise, swept_noise,
	reverb_lin, master, s_whoosh, s_charge_tick, s_land)

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'trailer', 'trailer_score.wav')
with open(os.path.join(ROOT, 'trailer', 'cues.json')) as fh:
	CUES = json.load(fh)
SPB = 60 / CUES['bpm']
S16 = SPB / 4
LEN = CUES['bars'] * 4 * SPB
N = int(round(LEN * SR))
RMS_DB = -18.0  # master()'s >150 Hz RMS target; lands near -14 LUFS integrated
rng = ga.rng
SL = Scale(SLENDRO, 262.0)
PB = Scale(PELOG_BEM, 294.0)
BATTLE_BAL = parse("2 3 2 1  6. 5. 6. 1  3 2 1 2  3 5 6 5  6 5 3 2  1 2 3 5  6 5 3 2  1 6. 1 2 "  # battle()'s balungan
	"5 6 1' 6  5 3 5 6  1' 2' 1' 6  5 3 2 3  5 5 6 1'  6 5 3 2  3 5 3 2  1 2 6. 1")


def tb(bar, beat=1):
	return ((bar - 1) * 4 + beat - 1) * SPB


Q = {k: tb(*v) for k, v in CUES['cues'].items()}
GAP = Q['drop'] - S16  # the "suck" 16th before the drop
pat = lambda s: [i for i, c in enumerate(s) if c == 'x']  # noqa: E731

# Buses: (reverb rt, wet, hard cut time, gain). Linear (non-wrapping) reverb; a cut zeroes the bus, reverb tail included.
# Music buses sit ~3 dB under the hit buses so trailer hits punch through.
BUSES = {'intro': (3.0, .35, GAP, .8), 'A': (1.3, .18, Q['pangkah'], .7), 'B': (1.3, .18, Q['blackout'], .7),
	'title': (3.2, .38, None, .85), 'fx': (1.6, .2, Q['blackout'], 1.), 'fx2': (1.6, .2, None, 1.)}
BUS = {k: Mix(LEN, 0) for k in BUSES}  # tail 0: Mix.add truncates at 60.000 s, nothing wraps


def mus(y, t, pan=0., gain=1.):
	"""Music routed by start time; notes in the suck gap / pangkah dropout / blackout are simply not played."""
	for b, lo, hi in (('intro', 0, GAP), ('A', Q['drop'], Q['pangkah']), ('B', Q['snap_back'], Q['blackout']), ('title', Q['title_gong'], LEN)):
		if lo <= t < hi:
			BUS[b].add(y, t, pan, gain)
			return


def fx(y, t, pan=0., gain=1., bus=None):
	BUS[bus or ('fx' if t < Q['blackout'] else 'fx2')].add(y, t, pan, gain)


def fx_to(y, cue, pan=0., gain=1., bus=None):
	"""Swell whose last sample lands on the cue sample."""
	fx(y, (round(cue * SR) - len(y)) / SR, pan, gain, bus)


def nrm(y):
	return y / np.abs(y).max()


def one_shot(rel):
	y, sr = sf.read(os.path.join(ROOT, 'assets', 'audio', rel), always_2d=True)
	y = y.mean(1)  # mono; Mix.add pans it back to stereo
	if sr != SR:
		y = ss.resample_poly(y, SR, sr)
	return nrm(y[np.argmax(np.abs(y) > .02 * np.abs(y).max()):])  # transient on sample 0


def pitch(y, r):
	return np.interp(np.arange(0, len(y) - 1, r), np.arange(len(y)), y)


PLANK = one_shot('impactPlank_medium_000.ogg')
SOFT = one_shot('impactSoft_heavy_001.ogg')
WOOD_L = one_shot('impactWood_light_002.ogg')
WOOD_H = [one_shot(f'impactWood_heavy_00{i}.ogg') for i in range(5)]
PLUCK = one_shot('pluck_002.ogg')
CHEER = one_shot('sfx/crowd_cheer.ogg')  # s_crowd_cheer() needs tools/applause.wav, which isn't checked in


# ---------------------------------------------------------------- trailer-only sounds
def thunder(dur=4.5):
	t = T(dur)
	y = nrm(bp_noise(dur, 35, 180, .8)) + .6 * nrm(bp_noise(dur, 50, 350, 1.1) * (.5 + .5 * np.sin(2 * np.pi * 1.3 * t + 1) ** 2))
	for k in range(7):  # crack on the cue, then scattered crackle
		c = nrm(bp_noise(.25, 1200, 7000, .04 if k == 0 else .02))
		i = 0 if k == 0 else int(rng.uniform(.03, .9) * SR)
		y[i:i + len(c)] += (1 if k == 0 else rng.uniform(.15, .5)) * c
	return y


def water_whoosh(dur=1.4):
	y = nrm(swept_noise(dur, [250, 700, 1500, 800, 400], lambda t: np.minimum(t / .005, 1) * np.exp(-t / .45) * (.6 + .4 * np.sin(2 * np.pi * 6.5 * t) ** 2)))
	s = nrm(bp_noise(.15, 600, 4000, .03))  # splash on the cue
	y[:len(s)] += s
	for _ in range(8):  # bubbles
		tt = T(.04)
		b = np.sin(2 * np.pi * np.cumsum(rng.uniform(500, 900) * (1 + 1.5 * tt / .04)) / SR) * np.exp(-tt / .012)
		i = int(rng.uniform(.05, .9) * SR)
		y[i:i + len(b)] += .3 * b
	return y


def rev_swell(dur, f, cym=.6):
	"""Reverse gong + cymbal: rises from nothing, peaks on its last sample."""
	t = T(dur)
	y = partials(f, [1, 1.025, 2.0, 2.52, 2.99, 4.43], [.6, .5, .7, .25, .35, .12], [dur * .5] * 6, dur, .001)
	y = nrm(y) + cym * nrm(ss.sosfilt(ss.butter(2, 3500, btype='high', fs=SR, output='sos'), rng.standard_normal(len(t))) * np.exp(-t / (dur * .3)))
	return (ga.release(y * ga.ramp(len(y), .003)))[::-1]


def rattle():
	y = np.zeros(int(.45 * SR))
	t0, gap, a = .07, .07, .5
	while gap > .012:  # top wobbling to rest: clicks speed up and fade (t0 converges on .42 s)
		c = partials(rng.uniform(700, 1100), [1, 2.4, 3.9], [1, .4, .2], [.012, .006, .004], .04, .0003)
		i = int(t0 * SR)
		y[i:i + len(c)] += a * c[:len(y) - i]
		t0, gap, a = t0 + gap, gap * .8, a * .85
	return y


def accent(t, g=1.):
	fx(dhung(), t, 0, .6 * g)
	fx(tak(), t, .1, .6 * g)
	fx(bum(), t, .2, .25 * g)


# ---------------------------------------------------------------- sections
def intro():
	S = SL
	bal = parse("2 1 6. 5.  6. 1 2 3  5 3 2 1  2 1 6. 5.")
	mus(gong_ageng(S.f(-11), 12.0), Q['lamp_on'], 0, .20)  # lamp_on: soft gong
	t = T(GAP)
	drone = sum(h ** -1.5 * np.sin(2 * np.pi * fr * h * t) for fr in (S.f(-1), S.f(-3)) for h in range(1, 9))
	mus(drone * np.minimum(t / 4, 1) * (.6 + .4 * np.sin(2 * np.pi * t / 7.5) ** 2), 0, 0, .012)
	for j, x in enumerate(bal[:14]):  # half-time: one balungan note per 2 beats, bars 1-7
		t0 = 2 * j * SPB
		mus(slenthem(S.f(x - 5)), t0 + SPB, 0, .25)
		if j:
			for k, n in enumerate((x + 5, x, x + 2, x)):
				mus(gender(S.f(n), 4.0), t0 + k * .5 * SPB, -.4 if k % 2 else .35, .07)
	sul = [(8, '3', 1.5), (9.5, '5', .5), (10, '6', 2), (12, "1'", 1), (13, '6', .5), (13.5, '5', .5), (14, '3', 2),
		(16, '5', 1), (17, '3', 1), (18, '2', 2), (20, '3', .5), (20.5, '5', .5), (21, '3', 1), (22, '2', 1), (23, '1', 1),
		(24, '2', 2), (26, '6.', 2)]
	mus(wind_line([(b, S.f(parse(n)[0] + 5), d) for b, n, d in sul], SPB, 28.5 * SPB, 'suling'), 0, .2, .13)

	t = Q['gunungan_turn']  # glint
	fx(bonang(S.f(10)), t, .4, .3)
	fx(bonang(S.f(12)), t + S16, .5, .2)
	fx(ketuk(S.f(5)), t, .3, .2)
	fx(kesi(), t, .4, .12)
	fx(nrm(s_whoosh()), Q['storm_wipe'], -.3, .35)
	fx(thunder(), Q['thunder_1'], -.2, .55)
	fx(thunder(), Q['thunder_2'], .25, .6)
	fx(nrm(bp_noise(.2, 1500, 8000, .03)), Q['thunder_2'], .3, .35)  # extra crack so it cuts through thunder_1's roll
	fx(thunder(5.0), Q['shipwreck'], 0, .6)
	fx(kempul(S.f(-6), 3.0), Q['shipwreck'], 0, .55)
	fx(water_whoosh(), Q['shore_wipe'], .2, .6)
	fx(kenong(S.f(3)), Q['stranger'], .15, .35)

	t7 = tb(7)  # kendang enters
	for fn, p, pan, g in ((dhung, 'x.....x.x.....x.', 0, .3), (tung, '...x.......x..x.', -.1, .18), (tak, '....x.......x...', .1, .22), (tap, 'x.x.x.x.x.x.x.x.', .05, .05)):
		for k in pat(p):
			mus(fn(), t7 + k * S16, pan, g)
	for c in ('village', 'game', 'gasing'):
		accent(Q[c])

	r0 = Q['riser']  # roll 8ths -> 16ths -> 32nds + noise riser + rising saron tremolo; the intro bus cut makes the suck gap
	hits = [0, .5, 1, 1.5, 2, 2.25, 2.5, 2.75] + [3 + k / 8 for k in range(6)]
	for k, b in enumerate(hits):
		mus((dhung, tak, tung, tak)[k % 4](), r0 + b * SPB, (-.15, .15)[k % 2], .18 + .3 * k / len(hits))
	d = GAP - r0
	mus(nrm(swept_noise(d, [300, 600, 1200, 2500, 5000, 8000], lambda t: (t / d) ** 2.5)), r0, 0, .3)
	for k in range(int(round(d / (S16 / 2)))):
		mus(saron(PB.f(k // 2 + 2), .5), r0 + k * S16 / 2, (-.3, .3)[k % 2], .07 + .13 * k / 30)


def groove():
	S, bal = PB, BATTLE_BAL
	for bar in range(9, 29):  # battle() re-tempo'd; bus routing drops the pangkah gap and everything after the blackout
		t0 = tb(bar)
		sec_b, fill = bar >= 17, bar in (16, 24)
		lift = {22: 1.8, 23: 2.0, 24: 2.2}.get(bar, 1.)  # drums + bonang build into the bar-24 fill as the cards accelerate
		for j in range(4):
			i = (bar - 9) * 4 + j
			a, b = bal[i % 64], bal[(i + 1) % 64]
			t = t0 + j * SPB
			mus(saron(S.f(a), 2.0), t, -.05, .40)  # demung
			mus(saron(S.f(a + 5), 1.2), t, -.3, .20)  # saron nacah
			mus(saron(S.f(b + 5), 1.2), t + 2 * S16, -.3, .16)
			if sec_b:  # bonang imbal
				for k in (0, 2):
					mus(bonang(S.f(b + 5)), t + k * S16, -.55, .11 * lift)
				for k in (1, 3):
					mus(bonang(S.f(b + 6)), t + k * S16, .55, .10 * lift)
			else:  # peking a a b b
				for k, x in enumerate((a, a, b, b)):
					mus(saron(S.f(x + 10), .8), t + k * S16, .4, .07)
			mus(kesi(), t + 2 * S16, .25, .10)
		drums = [(dhung, 'x..x....x..x.x..', 0, .45), (tak, '....x.......x...', .1, .35), (tung, '..x...x...x...x.', -.1, .22),
			(pak, 'x.x.x.x.x.x.x.x.', -.5, .14), (bum, 'x.......x.......', .2, .22)]
		if sec_b:
			drums.append((pak, '...x..x....x..xx', .5, .12))
		if bar >= 21:  # kompang off-16ths: density climbs as the cards accelerate
			drums.append((pak, '.x.x.x.x.x.x.x.x', .35, .1 + .03 * min(bar - 21, 3)))
			drums.append((tung, '......x.......x.', -.25, .18))
		for fn, p, pan, g in drums:
			for k in pat(p):
				if not (fill and k > 8):
					mus(fn(), t0 + k * S16, pan, g * lift)
		for k in range(16):
			mus(tap(), t0 + k * S16, .05, (.05 if k % 2 else .08) * lift)
		if fill:
			for k in range(9, 16):
				mus(tak() if k % 2 else tung(), t0 + k * S16, .1 if k % 2 else -.1, (.18 + .05 * (k - 9)) * lift)
		i4 = (bar - 9) * 4
		mus(kenong(S.f(bal[(i4 + 3) % 64])), t0 + 3 * SPB, .15, .22)
		if (bar - 9) % 8:
			mus(kempul(S.f(bal[(i4 + 1) % 64] - 5)), t0 + SPB, -.2, .2)
	notes = []
	for bar in range(17, 27):  # serunai lead, battle()'s section-B line
		n = bal[4 * ((bar - 9) % 16):4 * ((bar - 9) % 16) + 4]
		b0 = (bar - 17) * 4 + 1  # beats from one beat before bar 17 (room for the grace note)
		notes += [(b0 - .12, S.f(n[1] + 6), .12), (b0, S.f(n[1] + 5), 1.5), (b0 + 1.5, S.f(n[2] + 5), .5),
			(b0 + 1.88, S.f(n[3] + 6), .12), (b0 + 2, S.f(n[3] + 5), 1.75)]
	mus(wind_line(notes, SPB, 42 * SPB, 'serunai'), tb(17) - SPB, -.15, .26)


def groove_hits():
	S = PB
	t = Q['drop']
	mus(gong_ageng(S.f(-15), 10.0), t, 0, .45)
	fx(dhung(), t, 0, .9)
	fx(bum(), t, .1, .6)
	fx(tak(), t, .1, .6)
	fx(pak(), t, -.2, .45)
	fx(kempul(S.f(-5)), t, -.2, .4)
	for c, n in (('callout_1', 10), ('callout_2', 12), ('callout_3', 13)):
		fx(saron(S.f(n), 1.5), Q[c], .2, .35)
		fx(bonang(S.f(n)), Q[c], -.2, .2)
	t = Q['wind']  # cord pull: rising swish + firm tak on the cue, so the ratchet starts with an attack
	fx(nrm(swept_noise(.25, [700, 1800, 4500], lambda t: np.minimum(t / .003, 1) * np.exp(-t / .12))), t, -.2, .45)
	fx(tak(), t, .1, .8)
	for k in range(15):  # wind: 16th ratchet rising through 11.4.5
		fx(pitch(nrm(s_charge_tick()), .75 * 2 ** (k / 14)), Q['wind'] + k * S16, (-.2, .2)[k % 2], .25 + .02 * k)
	t = Q['perfect']
	for n, g in ((10, .22), (13, .2)):
		fx(bonang(S.f(n)), t, -.3, g)
	fx(saron(S.f(12), 1.5), t, .3, .25)
	fx(saron(S.f(15), 1.5), t, .4, .2)
	fx(kesi(), t, .2, .2)
	t = Q['launch_land']
	fx(nrm(s_land()), t, 0, .8)
	fx(bum(), t, .1, .5)
	fx(WOOD_H[0], t, -.1, .6)
	t = Q['rival_land']
	fx(nrm(s_land()), t, .3, .45)
	fx(WOOD_H[3], t, .3, .35)
	fx(tak(), Q['strike'], .1, .7)
	fx(pak(), Q['strike'], -.2, .4)

	t = Q['pangkah']  # massive hit, then 2 beats of drone + tail + reverse swell
	fx(PLANK, t, 0, 1.0)
	tt = T(3.0)
	fx((gong_ageng(S.f(-15), 3.0) + kempul(S.f(-10), 3.0)) * np.exp(-tt / .35), t, 0, .6)  # gong-ish boom, short so the dropout reads
	fx(nrm(bp_noise(.3, 2000, 10000, .03)), t, .1, .5)
	fx(bum(), t, -.1, .6)
	fx(dhung(), t, 0, .8)
	d = Q['snap_back'] - t
	tt = T(d)
	fx(sum(h ** -1.2 * np.sin(2 * np.pi * S.f(-10) * h * tt) for h in (1, 2, 3)) * np.minimum(tt / .2, 1) * np.minimum((d - tt) / .03, 1), t, 0, .12)
	fx_to(rev_swell(.9 * d, S.f(-5)), Q['snap_back'], 0, .2)
	t = Q['snap_back']
	fx(dhung(), t, 0, .8)
	fx(tak(), t, .1, .55)
	fx(pak(), t, -.2, .4)
	fx(bum(), t, .2, .45)
	fx(kempul(S.f(-5)), t, -.2, .35)
	t = Q['ringout']
	fx(WOOD_L, t, .2, .8)
	fx(nrm(s_whoosh()), t, -.2, .35)
	c = CHEER[:int(1.2 * SR)].copy()
	c[-int(.4 * SR):] *= np.linspace(1, 0, int(.4 * SR))
	fx(c, t, 0, .35)
	for k in range(13):  # map: one saron note per state pip
		fx(saron(S.f(3 + k), 1.0), Q['map'] + k * S16, -.4 + .8 * k / 12, .35)
	fx(kempul(S.f(-5)), Q['masters'], -.2, .45)
	fx(dhung(), Q['masters'], 0, .4)
	fx_to(nrm(swept_noise(SPB, [400, 900, 2000, 3500], lambda t: (t / SPB) ** 2 * (1 - np.exp(-(SPB - t) / .004)))), Q['card_perlis'], .2, .35)

	for k, c in enumerate(sorted((c for c in Q if c.startswith('card_')), key=Q.get)):
		t, g = Q[c], .45 + .02 * k
		fx(tak(), t, .1, g)
		fx(pak(), t, -.25, .7 * g)
		fx(nrm(s_whoosh()), t, (-.4, .4)[k % 2], .22)
		if CUES['cues'][c][0] <= 20:
			fx(kenong(S.f(k)), t, .15, .35)
		else:  # faster cuts get a bum underneath
			fx(bum(), t, .2, .35)

	accent(Q['food'], .7)
	for k in range(13):  # food: playful pops
		t = Q['food'] + k * S16
		fx(bonang(S.f(k + 5)), t, -.3 + .05 * k, .25)
		fx(pitch(PLUCK, S.f(k + 5) / S.f(8)), t, .3 - .05 * k, .4)
	fx(nrm(swept_noise(1.6, [200, 500, 1500, 2500, 900, 300], lambda t: np.minimum(t / .03, 1) * np.exp(-t / .6))), Q['tops'], 0, .35)
	for k in range(8):
		fx(saron(S.f(5 + k), 1.0), Q['tops'] + k * S16, .3, .2)
	for k, c in enumerate(('tag_1', 'tag_2', 'tag_3')):  # stabs: each one bigger, kempul choked so the next lands clean
		t, g = Q[c], 1 + .12 * k
		fx(bum(), t, 0, .6 * g)
		fx(tak(), t, .1, .6 * g)
		fx(dhung(), t, 0, .5 * g)
		fx(kempul(S.f(k - 5), SPB) * np.exp(-T(SPB) / .15), t, -.2, .5 * g)
		fx(saron(S.f(k + 5), 1.5), t, .2, .25 * g)
	fx(CHEER, tb(27), 0, .15)  # crowd bed (cut at the blackout)
	t = Q['ffa_ringout']
	fx(PLANK, t, 0, .9)
	fx(WOOD_L, t, .2, .5)
	fx(bum(), t, 0, .6)
	fx(dhung(), t, 0, .7)
	fx(kempul(S.f(-5)), t, -.2, .45)
	fx(CHEER[:SR] * np.linspace(.3, 1, SR), t, 0, .5)
	fx_to(rev_swell(Q['title_gong'] - Q['blackout'], SL.f(-6)), Q['title_gong'], 0, .45, bus='fx2')


def title():
	S = SL
	t = Q['title_gong']
	mus(gong_ageng(S.f(-11), 12.0), t, 0, .65)
	mus(kempul(S.f(-6)), t, -.15, .55)
	mus(bum(), t, .15, .5)
	mus(dhung(), t, 0, .7)
	mus(tak(), t, .1, .4)
	tt = T(LEN - t)
	pad = sum(h ** -1.5 * np.sin(2 * np.pi * fr * h * tt) for fr in (S.f(-1), S.f(-3), S.f(1)) for h in range(1, 7))
	mus(pad * np.minimum(tt / 1.5, 1) * (.75 + .25 * np.sin(2 * np.pi * tt / 3.75) ** 2), t, 0, .025)
	pairs = [(4, 6), (3, 6), (2, 4), (1, 4)]  # gender tremolo: alternating pairs, one pair per 2 beats
	for k in range(64):
		x = pairs[(k // 8) % 4][k % 2]
		g = .03 + .06 * np.sin(np.pi * k / 31) if k < 32 else .018  # swells over bars 29-30, then thins under the heartbeat
		mus(gender(S.f(x), 3.5), t + k * S16, (-.35, .35)[k % 2], g)
		if k < 32:
			mus(saron(S.f(14 + k % 2), .6), t + k * S16 + S16 / 2, .4, .02)
	for k in range(15):  # title_letters: peking glissando (on fx2 so the title-bus duck doesn't touch it)
		fx(saron(S.f(6 + k), .9), Q['title_letters'] + k * S16 / 2, -.5 + k / 14, .3)
	fx(bonang(S.f(11)), Q['title_letters'], .3, .3)
	fx(kesi(), Q['title_letters'], .3, .3)
	fx(tak(), Q['title_letters'], .1, .5)
	for bar in (31, 32):
		for beat in (1, 3):
			mus(dhung(), tb(bar, beat), 0, .35)
	for c, n in (('tagline_1', 2), ('tagline_2', 3), ('tagline_3', 5)):
		fx(tak(), Q[c], .1, .7)
		fx(kenong(S.f(n), 1.2), Q[c], .15, .4)  # choked so the next accent lands clean
	fx(saron(S.f(13), .8), Q['tagline_2'], -.3, .3)  # peking + pak: brighter transient over the wash
	fx(pak(), Q['tagline_2'], -.2, .4)
	fx(SOFT, Q['topple'], 0, 1.0)
	fx(WOOD_H[1], Q['topple'], -.1, .7)  # impactSoft is mostly thud; this gives it the wooden clack
	fx(rattle(), Q['topple'], .1, .4)


def render():
	intro()
	groove()
	groove_hits()
	title()
	outs = {}
	for k, (rt, wet, cut, g) in BUSES.items():
		y = g * reverb_lin(BUS[k].buf, rt, wet)
		if cut is not None:
			i, f = round(cut * SR), int(.008 * SR)
			y[i - f:i] *= np.linspace(1, 0, f)[:, None]
			y[i:] = 0
		if k == 'title':  # sidechain-style dip in the gong/gender wash just before these accents
			for c in (Q['title_letters'], Q['tagline_2']):
				i = round(c * SR)
				n = np.arange(i - int(.04 * SR), i + int(.15 * SR))
				y[n] *= np.interp(n, [i - .04 * SR, i - .03 * SR, i, i + .15 * SR], [1, .35, .35, 1])[:, None]
		outs[k] = y
	pad = np.zeros((SR // 2, 2))  # master()'s HPF is circular: pad so the ending can't wrap onto the head
	x = master(np.vstack([pad, sum(outs.values()), pad]), RMS_DB)[len(pad):len(pad) + N]
	f = int(.01 * SR)
	x[-f:] *= np.linspace(1, 0, f)[:, None]
	sf.write(OUT, x, SR, subtype='PCM_16')
	return outs


# ---------------------------------------------------------------- verification
def lufs(x):
	"""BS.1770 integrated loudness (K-weighting + gating)."""
	def biquad(kind, fc, q, g=0.):
		A, w = 10 ** (g / 40), 2 * np.pi * fc / SR
		c, al = np.cos(w), np.sin(w) / (2 * q)
		if kind == 'shelf':
			b = [A * ((A + 1) + (A - 1) * c + 2 * np.sqrt(A) * al), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - 2 * np.sqrt(A) * al)]
			a = [(A + 1) - (A - 1) * c + 2 * np.sqrt(A) * al, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - 2 * np.sqrt(A) * al]
		else:
			b, a = [(1 + c) / 2, -(1 + c), (1 + c) / 2], [1 + al, -2 * c, 1 - al]
		return b, a
	y = ss.lfilter(*biquad('shelf', 1681.97, .7072, 4.0), x, axis=0)
	y = ss.lfilter(*biquad('hp', 38.135, .5003), y, axis=0)
	blk, hop = int(.4 * SR), int(.1 * SR)
	z = np.array([np.mean(y[i:i + blk] ** 2, 0).sum() for i in range(0, len(y) - blk + 1, hop)])
	z = z[-.691 + 10 * np.log10(z + 1e-20) > -70]
	z = z[-.691 + 10 * np.log10(z + 1e-20) > -.691 + 10 * np.log10(z.mean()) - 10]
	return -.691 + 10 * np.log10(z.mean())


def verify(outs):
	y, sr = sf.read(OUT, always_2d=True)
	yh = ss.sosfilt(ss.butter(2, 150, btype='high', fs=SR, output='sos'), y, axis=0)  # judged above 150 Hz, like master()
	db =lambda s: 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-9) if len(s) else -np.inf  # noqa: E731
	pk = 20 * np.log10(np.abs(y).max())
	print(f'{OUT}\n  {sr} Hz, {y.shape[1]} ch, {len(y)} samples = {len(y) / sr:.6f} s, peak {pk:.2f} dBFS, '
		f'integrated {lufs(y):.1f} LUFS, rms {db(y):.1f} dBFS')
	assert sr == SR and len(y) == N == 2_646_000 and pk <= -1.0, (sr, len(y), pk)

	w = int(.02 * SR)
	print('\nOnsets (20 ms RMS >150 Hz before/after the cue sample)\n  cue               bar.beat     t (s)   before   after    jump')
	worst = 99.
	for c in sorted(Q, key=lambda c: (Q[c], c)):
		if c in ('riser', 'songket_wipe', 'blackout'):
			continue
		i = round(Q[c] * SR)
		a, b = db(yh[max(0, i - w):i]), db(yh[i:i + w])
		worst = min(worst, b - a)
		bar, beat = CUES['cues'][c]
		print(f'  {c:16s} {bar:3d}.{beat:<5g} {Q[c]:9.4f} {a:8.1f} {b:7.1f} {b - a:+7.1f} dB')
	print(f'  smallest jump: {worst:+.1f} dB')

	def strip(name, t0, t1, n):
		edges = np.linspace(t0, t1, n + 1)
		row = ' '.join(f'{db(y[round(a * SR):round(b * SR)]):6.1f}' for a, b in zip(edges[:-1], edges[1:]))
		print(f'  {name:34s} {row}')
	print('\nGaps (RMS dBFS per 16th)')
	strip('groove bar 13 beats 1-2 (ref)', tb(13), Q['pangkah'], 8)
	strip('suck gap 8.4.75 -> drop', GAP, Q['drop'], 1)
	strip('pangkah dropout 13.3 -> 14.1', Q['pangkah'], Q['snap_back'], 8)
	strip('blackout 28.4 -> 29.1 (swell only)', Q['blackout'], Q['title_gong'], 8)
	print('\nPre-master bus RMS (dB) per window     ' + ' '.join(f'{k:>6s}' for k in outs))
	for name, a, b in (('suck gap', GAP, Q['drop']), ('pangkah dropout', Q['pangkah'], Q['snap_back']), ('blackout', Q['blackout'], Q['title_gong'])):
		print(f'  {name:37s}' + ' '.join(f'{db(o[round(a * SR):round(b * SR)]):6.1f}' for o in outs.values()))

	print('\nPer bar: RMS full band / RMS >150 Hz / peak (dBFS); graph = RMS >150 Hz')
	for bar in range(1, CUES['bars'] + 1):
		i0, i1 = round(tb(bar) * SR), round(tb(bar + 1) * SR)
		r = db(yh[i0:i1])
		sec = next(k for k, (lo, hi) in CUES['sections'].items() if lo <= bar <= hi)
		print(f'  {bar:2d} {tb(bar):6.2f}s {sec:9s} {db(y[i0:i1]):6.1f} {r:6.1f} {20 * np.log10(np.abs(y[i0:i1]).max()):6.1f}  ' + '#' * max(0, int(r + 40)))
	assert worst > 1.0, worst


if __name__ == '__main__':
	verify(render())
