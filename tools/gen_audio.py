# Generates Gasing Pangkah music + SFX (original, synthesized). Writes Ogg Vorbis.
# Needs: pip install numpy scipy soundfile. crowd_cheer mixes tools/applause.wav, the CC0
# "Applause in a large hall or church" (https://opengameart.org/content/applause-in-a-large-hall-or-church).
import os
import numpy as np
import scipy.signal as ss
import soundfile as sf

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'assets', 'audio')
rng = np.random.default_rng(1957)

SLENDRO = [0, 231, 474, 717, 955]      # 1 2 3 5 6
PELOG_BEM = [0, 120, 270, 670, 785]    # 1 2 3 5 6
DEG = {'1': 0, '2': 1, '3': 2, '5': 3, '6': 4}


def T(d):
	return np.arange(int(round(d * SR))) / SR


def ramp(n, a):
	e = np.ones(n)
	k = min(n, max(1, int(a * SR)))
	e[:k] = np.linspace(0, 1, k)
	return e


def release(y):
	"""Smooth fade over the last 30% so a render never ends in a click."""
	n = len(y)
	return y * np.sin(np.clip((n - np.arange(n)) / (0.3 * n), 0, 1) * np.pi / 2) ** 2


def partials(f, ratios, amps, taus, dur, att=0.002):
	t = T(dur)
	y = np.zeros_like(t)
	for r, a, tau in zip(ratios, amps, taus):
		if f * r > SR * 0.45:
			continue
		y += a * np.sin(2 * np.pi * f * r * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / tau)
	return release(y * ramp(len(t), att))


def bp_noise(dur, lo, hi, tau, order=2):
	t = T(dur)
	sos = ss.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
	return release(ss.sosfilt(sos, rng.standard_normal(len(t))) * np.exp(-t / tau))


def drum(f0, f1, tg, tau, dur, noise, nlo, nhi, ntau):
	t = T(dur)
	f = f1 + (f0 - f1) * np.exp(-t / tg)
	y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau)
	return release((y + noise * bp_noise(dur, nlo, nhi, ntau)) * ramp(len(t), 0.0008))


# ---------------------------------------------------------------- instruments
def saron(f, dur=2.5):
	a = partials(f, [1, 2.76, 5.40, 8.93], [1, .45, .20, .08], [1.1, .50, .18, .08], dur, .001)
	b = partials(f + 3.0, [1, 2.76, 5.40], [1, .45, .20], [1.1, .50, .18], dur, .001)  # ombak pair
	return 0.5 * (a + b) + 0.2 * bp_noise(dur, 2000, 6000, .006)


def gender(f, dur=3.5):
	return partials(f, [1, 2.71, 3.95], [1, .10, .04], [2.4, .45, .15], dur, .006) + 0.04 * bp_noise(dur, 300, 1500, .004)


def slenthem(f, dur=5.0):
	return partials(f, [1, 2.72, 1.003], [1, .07, .6], [3.5, .5, 3.2], dur, .012)


def bonang(f, dur=1.6):
	return partials(f, [1, 1.99, 2.41, 3.98], [1, .35, .22, .08], [.9, .35, .25, .12], dur, .001) + 0.25 * bp_noise(dur, 1500, 5000, .005)


def kenong(f, dur=5.0):
	return partials(f, [1, 2.02, 2.98, 4.1, 1.004], [1, .25, .12, .05, .7], [2.8, 1.0, .5, .25, 2.6], dur, .003)


def kempul(f, dur=6.0):
	y = partials(f, [1, 1.012, 2.0, 2.37, 3.0, 3.93, 5.0], [1, .8, .45, .2, .25, .12, .06], [3.5, 3.2, 1.8, 1.2, .9, .6, .4], dur, .006)
	return y + 0.3 * bp_noise(dur, 60, 400, .03)


def gong_ageng(f, dur=12.0):
	r = [1, 1.025, 2.0, 2.018, 2.52, 2.99, 3.7, 4.43, 5.2, 6.1]
	a = [.6, .5, .7, .5, .25, .35, .15, .12, .07, .05]
	tau = [8, 7.5, 5, 4.5, 2.5, 3, 1.6, 1.2, .9, .7]
	y = partials(f, r, a, tau, dur, .012)
	return y + 0.12 * bp_noise(dur, 30, 300, .05) + 0.08 * bp_noise(dur, 200, 1500, .015)


def ketuk(f):
	return partials(f, [1, 2.9], [1, .2], [.09, .03], .4, .001) + 0.1 * bp_noise(.4, 500, 3000, .004)


def dhung():
	return drum(150, 88, .03, .22, .6, .25, 80, 1200, .02)


def tung():
	return drum(260, 215, .02, .12, .4, .2, 300, 2500, .015)


def tak():
	return 0.35 * drum(420, 380, .01, .035, .2, 0, 1, 2, 1) + 0.9 * bp_noise(.2, 900, 5000, .03)


def tap():
	return bp_noise(.08, 2000, 7000, .012)


def pak():
	return 0.8 * bp_noise(.15, 1500, 6500, .025) + 0.5 * partials(520, [1, 1.59, 2.14], [1, .5, .3], [.05, .03, .02], .15, .0005)


def bum():
	return drum(210, 170, .02, .14, .4, .15, 200, 1500, .02)


def kesi():
	sos = ss.butter(2, 5000, btype='high', fs=SR, output='sos')
	t = T(.25)
	return partials(3100, [1, 1.52, 2.07, 2.63], [1, .8, .6, .4], [.07, .05, .04, .03], .25, .0003) + 0.6 * ss.sosfilt(sos, rng.standard_normal(len(t))) * np.exp(-t / .03)


def wind_line(notes, spb, total, kind):
	"""notes: (start_beat, freq, dur_beats). Legato wind line (suling / serunai) with glide + vibrato."""
	n = int(total * SR)
	f = np.zeros(n)
	amp = np.zeros(n)
	cur = notes[0][1]
	last = 0
	for b, fr, d in sorted(notes):
		i0, i1 = int(b * spb * SR), min(n, int((b + d) * spb * SR))
		f[last:i0] = cur
		f[i0:i1] = fr
		cur, last = fr, i1
		seg = np.ones(i1 - i0)
		ka, kr = min(len(seg), int(.04 * SR)), min(len(seg), int(.09 * SR))
		seg[:ka] = np.linspace(0, 1, ka) ** 1.5
		seg[-kr:] *= np.linspace(1, 0, kr)
		amp[i0:i1] = np.maximum(amp[i0:i1], seg)
	f[last:] = cur
	a = np.exp(-1 / (.025 * SR))
	f = ss.lfilter([1 - a], [1, -a], f, zi=[f[0] * a])[0]  # portamento
	t = np.arange(n) / SR
	vib_depth = (0.006 if kind == 'suling' else 0.009) * np.clip(ss.lfilter([1 - np.exp(-1 / (.3 * SR))], [1, -np.exp(-1 / (.3 * SR))], amp), 0, 1)
	f = f * (1 + vib_depth * np.sin(2 * np.pi * 5.3 * t))
	ph = 2 * np.pi * np.cumsum(f) / SR
	y = np.zeros(n)
	for h in range(1, 24):
		fh = f * h
		if kind == 'suling':
			ah = [1, .22, .07, .025][h - 1] if h <= 4 else 0
		else:  # serunai: nasal double reed, formants ~1.3k/2.7k
			ah = h ** -0.7 * (1 + 2.5 * np.exp(-((fh - 1300) / 450) ** 2) + 1.5 * np.exp(-((fh - 2700) / 700) ** 2)) * 0.25
		if np.isscalar(ah) and ah == 0:
			continue
		y += ah * np.sin(h * ph) * (fh < 9000)
	breath = ss.sosfilt(ss.butter(2, [900, 5000], btype='band', fs=SR, output='sos'), rng.standard_normal(n))
	y += (0.05 if kind == 'suling' else 0.02) * breath
	return y * amp


# ---------------------------------------------------------------- scales/mixing
class Scale:
	def __init__(self, cents, base):
		self.c, self.base = cents, base

	def f(self, idx):
		o, p = divmod(idx, 5)
		return self.base * 2 ** ((self.c[p] + 1200 * o) / 1200)


def parse(s):
	out = []
	for tok in s.split():
		if tok == '-':
			out.append(None)
			continue
		idx = DEG[tok[0]] + 5 * (tok.count("'") - tok.count('.'))
		out.append(idx)
	return out


class Mix:
	def __init__(self, length_s, tail_s):
		self.L = int(round(length_s * SR))
		self.buf = np.zeros((self.L + int(tail_s * SR), 2))

	def add(self, y, t, pan=0.0, gain=1.0):
		i = int(round(t * SR))
		th = (pan + 1) * np.pi / 4
		e = min(len(self.buf), i + len(y))
		self.buf[i:e] += y[:e - i, None] * np.array([np.cos(th), np.sin(th)]) * gain

	def loop(self):
		out = self.buf[:self.L].copy()
		tail = self.buf[self.L:]
		while len(tail):  # wrap overhang into the head -> seamless loop
			k = min(len(tail), self.L)
			out[:k] += tail[:k]
			tail = tail[k:]
		return out


def make_ir(rt, damp=4500, pre=.015):
	n = int(rt * SR)
	t = np.arange(n) / SR
	ir = rng.standard_normal((n, 2)) * np.exp(-6.9 * t / rt)[:, None]
	ir = ss.sosfilt(ss.butter(1, damp, fs=SR, output='sos'), ir, axis=0)
	ir = np.vstack([np.zeros((int(pre * SR), 2)), ir])
	return ir / np.sqrt((ir ** 2).sum(0))


def reverb_loop(x, rt, wet):
	ir = make_ir(rt)
	L = len(x)
	Y = np.fft.irfft(np.fft.rfft(x, axis=0) * np.fft.rfft(ir, n=L, axis=0), n=L, axis=0)  # circular
	return x + wet * Y


def reverb_lin(x, rt, wet):
	ir = make_ir(rt)
	Y = np.stack([ss.fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)
	return x + wet * Y


def master(x, rms_db, peak_db=-1.0):
	fr = np.fft.rfftfreq(len(x), 1 / SR)[:, None]
	x = np.fft.irfft(np.fft.rfft(x, axis=0) * (fr / 45) ** 2 / (1 + (fr / 45) ** 2), n=len(x), axis=0)  # circular 45 Hz HPF, kills DC
	p = 10 ** (peak_db / 20)
	xh = ss.sosfilt(ss.butter(2, 150, btype='high', fs=SR, output='sos'), x, axis=0)  # loudness judged above 150 Hz
	r = np.sqrt(np.mean(xh ** 2))
	crest = 20 * np.log10(np.abs(x).max() / r)
	rms_db = min(rms_db, peak_db - crest + 3.0)  # allow at most ~3 dB of soft limiting
	x = x * 10 ** (rms_db / 20) / r
	k = 0.7 * p
	a = np.abs(x)
	o = a > k
	x[o] = np.sign(x[o]) * (k + (p - k) * np.tanh((a[o] - k) / (p - k)))
	return x


def sfx_master(y, peak_db=-1.0):
	y = y - y.mean()
	nz = np.nonzero(np.abs(y) > np.abs(y).max() * 10 ** (-60 / 20))[0]
	y = y[max(0, nz[0] - 20):nz[-1] + 1]  # trim leading/trailing silence
	k = min(len(y), int(.01 * SR))
	y[-k:] *= np.linspace(1, 0, k)
	return y * 10 ** (peak_db / 20) / np.abs(y).max()


def write(rel, x, loop_len=None):
	path = os.path.join(OUT, rel)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	x = x.astype('float32')
	with sf.SoundFile(path, 'w', SR, 1 if x.ndim == 1 else x.shape[1], format='OGG', subtype='VORBIS') as f:
		for i in range(0, len(x), 4096):  # chunked: libsndfile's vorbis encoder overflows the stack on big writes
			f.write(x[i:i + 4096])
	d, _ = sf.read(path, always_2d=True)
	if loop_len is not None:
		assert len(d) == loop_len, (rel, len(d), loop_len)
		seam = np.abs(d[0] - d[-1]).max()  # wrap step must look like any other sample step, not a click
		assert seam < 0.5 * np.abs(np.diff(d, axis=0)).max(), (rel, seam)
	rms = 20 * np.log10(np.sqrt(np.mean(d ** 2)) + 1e-12)
	pk = 20 * np.log10(np.abs(d).max())
	print(f'{rel:24s} {len(d) / SR:6.2f}s  peak {pk:6.1f} dBFS  rms {rms:6.1f} dBFS  {os.path.getsize(path) // 1024} KB')


# ---------------------------------------------------------------- music
def menu():
	bpm, B = 76, 32
	spb = 60 / bpm
	m = Mix(B * spb, 14)
	S = Scale(SLENDRO, 262.0)
	bal = parse("3 2 1 2  3 5 6 5  1' 6 5 3  5 6 3 2  2 3 5 6  1' 6 5 3  5 3 2 1  2 1 2 6.")
	for i, n in enumerate(bal):
		m.add(saron(S.f(n), 3.0), i * spb, -.1, .42)                     # demung
		m.add(gender(S.f(n - 3)), (i + .5) * spb, -.45, .16)             # gender, kempyung below
	for i in range(0, B, 2):                                            # peking a a b b
		for k, x in enumerate((bal[i], bal[i], bal[i + 1], bal[i + 1])):
			m.add(saron(S.f(x + 10), 1.0), (i + k * .5) * spb, .4, .06)
	for g in range(8):                                                  # bonang mipil
		n = bal[4 * g:4 * g + 4]
		for k, x in enumerate([n[0], n[1], n[0], n[1], n[2], n[3], n[2], n[3]]):
			m.add(bonang(S.f(x + 5)), (4 * g + k * .5) * spb, .5, .10)
		m.add(ketuk(S.f(1)), (4 * g + 1) * spb, .3, .12)
		m.add(tak(), (4 * g + 1.5) * spb, .1, .06)
		m.add(tung(), (4 * g + 2.5) * spb, -.1, .08)
		m.add(dhung(), (4 * g + 3) * spb, 0, .16)
	for i in (7, 15, 23, 31):
		m.add(kenong(S.f(bal[i])), i * spb, .15, .28)
	for i in (11, 19, 27):
		m.add(kempul(S.f(bal[i] - 5)), i * spb, -.2, .22)
	m.add(gong_ageng(S.f(4 - 15)), 31 * spb, 0, .4)
	sul = [(9, "1'", 1), (10, '6', 1), (11, '5', .5), (11.5, '6', .5), (12, '5', 1), (13, '3', 1), (14, '5', .5), (14.5, '3', .5), (15, '2', 2.5),
		(24.5, '3', 1.5), (26, '2', 1), (27, '1', 1), (28, '2', .5), (28.5, '3', .5), (29, '2', 1), (30, '1', 1), (31, '6.', 3.0)]
	notes = [(b, S.f(parse(tok)[0] + 5), d) for b, tok, d in sul]
	m.add(wind_line(notes, spb, 35 * spb, 'suling'), 0, .2, .2)
	x = reverb_loop(m.loop(), 2.2, .30)
	write('music/menu.ogg', master(x, -20), m.L)


def battle():
	bpm, B = 136, 64
	spb = 60 / bpm
	s16 = spb / 4
	m = Mix(B * spb, 14)
	S = Scale(PELOG_BEM, 294.0)
	bal = parse("2 3 2 1  6. 5. 6. 1  3 2 1 2  3 5 6 5  6 5 3 2  1 2 3 5  6 5 3 2  1 6. 1 2 "
		"5 6 1' 6  5 3 5 6  1' 2' 1' 6  5 3 2 3  5 5 6 1'  6 5 3 2  3 5 3 2  1 2 6. 1")
	pat = lambda s: [i for i, c in enumerate(s) if c == 'x']
	for i in range(B):
		a, b = bal[i], bal[(i + 1) % B]
		t = i * spb
		sec_b = i >= 32
		m.add(saron(S.f(a), 2.0), t, -.05, .40)                          # demung
		m.add(saron(S.f(a + 5), 1.2), t, -.3, .20)                       # saron nacah
		m.add(saron(S.f(b + 5), 1.2), t + 2 * s16, -.3, .16)
		if sec_b:                                                        # bonang imbal
			for k in (0, 2):
				m.add(bonang(S.f(b + 5)), t + k * s16, -.55, .07)
			for k in (1, 3):
				m.add(bonang(S.f(b + 6)), t + k * s16, .55, .06)
		else:                                                            # peking a a b b
			for k, x in enumerate((a, a, b, b)):
				m.add(saron(S.f(x + 10), .8), t + k * s16, .4, .07)
		m.add(kesi(), t + 2 * s16, .25, .10)
	for bar in range(16):
		t0 = bar * 4 * spb
		fill = bar in (7, 15)
		for k in pat("x..x....x..x.x.."):
			if not (fill and k > 8):
				m.add(dhung(), t0 + k * s16, 0, .45)
		for k in pat("....x.......x..."):
			if not (fill and k > 8):
				m.add(tak(), t0 + k * s16, .1, .35)
		for k in pat("..x...x...x...x."):
			if not (fill and k > 8):
				m.add(tung(), t0 + k * s16, -.1, .22)
		for k in range(16):
			m.add(tap(), t0 + k * s16, .05, .05 if k % 2 else .08)
		if fill:
			for k in range(9, 16):
				m.add(tak() if k % 2 else tung(), t0 + k * s16, .1 if k % 2 else -.1, .18 + .05 * (k - 9))
		for k in pat("x.x.x.x.x.x.x.x."):
			m.add(pak(), t0 + k * s16, -.5, .14)
		if bar >= 8:
			for k in pat("...x..x....x..xx"):
				m.add(pak(), t0 + k * s16, .5, .12)
		for k in pat("x.......x......."):
			m.add(bum(), t0 + k * s16, .2, .22)
		m.add(kenong(S.f(bal[4 * bar + 3])), t0 + 3 * spb, .15, .22)
		if bar % 8:
			m.add(kempul(S.f(bal[4 * bar + 1] - 5)), t0 + spb, -.2, .2)
	m.add(kempul(S.f(0 - 5) * 0.75), 31 * spb, 0, .32)                    # gong suwukan
	m.add(gong_ageng(S.f(0 - 15)), 63 * spb, 0, .4)
	notes = []
	for g in range(8, 16):                                              # serunai over section B
		n = bal[4 * g:4 * g + 4]
		b0 = 4 * g
		notes += [(b0 - .12, S.f(n[1] + 6), .12), (b0, S.f(n[1] + 5), 1.5), (b0 + 1.5, S.f(n[2] + 5), .5),
			(b0 + 1.88, S.f(n[3] + 6), .12), (b0 + 2, S.f(n[3] + 5), 1.75)]
	m.add(wind_line(notes, spb, 66 * spb, 'serunai'), 0, -.15, .16)
	x = reverb_loop(m.loop(), 1.3, .18)
	write('music/battle.ogg', master(x, -17), m.L)


def cutscene():
	bpm, B = 60, 32
	spb = 60 / bpm
	m = Mix(B * spb, 14)
	S = Scale(SLENDRO, 262.0)
	bal = parse("2 1 6. 5.  6. 1 2 3  5 3 2 1  2 1 6. 5.")
	for j, n in enumerate(bal):
		t = 2 * j * spb
		m.add(slenthem(S.f(n - 5)), t + spb, 0, .5)
		for k, x in enumerate((n + 5, n, n + 2, n)):
			m.add(gender(S.f(x), 4.0), t + k * .5 * spb, -.4 if k % 2 else .35, .10)
	for i in (7, 15, 23):
		m.add(kempul(S.f(bal[(i + 1) // 2 - 1] - 5)), i * spb, -.15, .25)
	m.add(gong_ageng(S.f(4 - 15)), 31 * spb, 0, .45)
	Ld = m.L / SR
	t = np.arange(m.L) / SR
	drone = np.zeros(m.L)
	for fr in (S.f(-1), S.f(2 - 5)):  # 6. and 3., frequencies snapped to whole cycles per loop
		fq = round(fr * Ld) / Ld
		drone += sum(h ** -1.5 * np.sin(2 * np.pi * fq * h * t) for h in range(1, 9))
	drone *= 0.55 + 0.45 * np.sin(2 * np.pi * 2 * t / Ld) ** 2
	x = m.loop() + 0.025 * drone[:, None]
	fr = np.fft.rfftfreq(m.L, 1 / SR)[:, None]
	x = np.fft.irfft(np.fft.rfft(x, axis=0) / np.sqrt(1 + (fr / 7000) ** 2), n=m.L, axis=0)  # circular low-pass
	x = reverb_loop(x, 3.0, .35)
	write('music/cutscene.ogg', master(x, -23), m.L)


def stinger(name, events, length, rms):
	m = Mix(length, 0)
	for y, t, pan, g in events:
		m.add(y, t, pan, g)
	x = reverb_lin(m.buf, 1.8, .25)
	k = int(.9 * SR)
	x[-k:] *= np.linspace(1, 0, k)[:, None] ** 2
	write(f'music/{name}.ogg', master(x, rms))


def victory():
	S = Scale(PELOG_BEM, 294.0)
	ev = []
	for k, n in enumerate(parse("1 2 3 5 6 1' 2' 3'")):
		ev += [(saron(S.f(n + 5), 1.5), k * .07, .3, .35), (bonang(S.f(n + 5)), k * .07, -.3, .15)]
	for n in parse("1 5 1'"):
		ev.append((saron(S.f(n + 5), 2.5), .6, 0, .35))
	ev += [(dhung(), .6, 0, .6), (bum(), .6, .2, .4), (kempul(S.f(-5)), .6, -.2, .5)]
	for k, n in enumerate(parse("5 6 1'")):
		ev += [(saron(S.f(n + 5), 1.5), 1.0 + k * .2, .1, .4), (bonang(S.f(n + 10)), 1.0 + k * .2, -.4, .12), (tak(), 1.0 + k * .2, .1, .3)]
	for k in range(10):
		ev.append((pak(), 1.1 + k * .045, (-.5, .5)[k % 2], .08 + .02 * k))
	for n in parse("1 3 5 1'"):
		ev += [(saron(S.f(n + 5), 3.5), 1.6, 0, .35), (bonang(S.f(n + 10)), 1.6, .3, .1)]
	ev += [(gong_ageng(S.f(-15) * 1.5, 3.5), 1.6, 0, .4), (kempul(S.f(-5)), 1.6, .2, .4), (dhung(), 1.6, 0, .5), (bum(), 1.6, -.2, .5), (pak(), 1.6, .3, .4)]
	stinger('victory', ev, 4.4, -16)


def defeat():
	S = Scale(PELOG_BEM, 294.0)
	ev = []
	for k, n in enumerate(parse("6 5 3 2 1")):
		t = k * .38 + (.25 if k == 4 else 0)  # last note lingers (suwuk)
		ev += [(gender(S.f(n), 4.0), t, (-.3, .3)[k % 2], .5), (gender(S.f(n - 5), 4.0), t, 0, .25)]
	ev += [(kempul(S.f(-5)), 1.77, -.1, .5), (gong_ageng(S.f(-15), 3.0), 1.77, 0, .5), (slenthem(S.f(-5), 3.0), 1.77, .1, .4)]
	stinger('defeat', ev, 4.4, -19)


# ---------------------------------------------------------------- sfx
def swept_noise(dur, centers, env, bw=.35):
	n = int(dur * SR)
	f, t, Z = ss.stft(rng.standard_normal(n), SR, nperseg=1024)
	c = np.interp(t / dur, np.linspace(0, 1, len(centers)), centers)
	g = np.exp(-0.5 * ((np.log(np.maximum(f[:, None], 1)) - np.log(c[None, :])) / bw) ** 2)
	y = ss.istft(Z * g, SR, nperseg=1024)[1][:n]
	return y * env(np.arange(n) / SR)


def s_whoosh():
	return swept_noise(.45, [350, 1400, 2200, 1300, 800], lambda t: (np.minimum(t / .14, 1) ** 2) * np.exp(-np.maximum(t - .14, 0) / .09))


def s_jump():
	y = swept_noise(.32, [500, 1500, 2600, 3000], lambda t: np.minimum(t / .06, 1) * np.exp(-np.maximum(t - .06, 0) / .07))
	y[:int(.05 * SR)] += 0.6 * partials(1800, [1, 2.3], [1, .3], [.015, .006], .05, .0005)
	return y


def s_rush_loop():
	L = int(2.0 * SR)  # 2 s; every component is periodic over L -> seamless
	t = np.arange(L) / SR
	whirr = sum(np.sin(2 * np.pi * 75 * h * t + h) / h for h in range(1, 13)) * (1 + .3 * np.sin(2 * np.pi * 15 * t))
	fr = np.fft.rfftfreq(L, 1 / SR)

	def pnoise(lo, hi):
		spec = (rng.standard_normal(len(fr)) + 1j * rng.standard_normal(len(fr))) * ((fr > lo) & (fr < hi))
		y = np.fft.irfft(spec, n=L)
		return y / np.abs(y).max()

	grind = pnoise(800, 4000) * (.6 + .4 * np.abs(np.sin(2 * np.pi * 20 * t)))
	rumble = pnoise(40, 200)
	y = .5 * whirr / np.abs(whirr).max() + .35 * grind + .3 * rumble
	y -= y.mean()
	return y * 10 ** (-2 / 20) / np.abs(y).max()


def s_charge_tick():
	return partials(2300, [1, 2.1, 3.7], [1, .4, .2], [.012, .008, .004], .05, .0005) + .15 * bp_noise(.05, 3000, 8000, .002)


def s_ui_hover():
	return partials(1350, [1, 2.4], [1, .15], [.009, .004], .04, .0015)


def s_gong():
	f = 82.0
	r = [1, 1.02, 2.0, 2.015, 2.52, 3.0, 3.7, 4.43, 5.2, 6.1, 7.3, 8.6]
	a = [1, .8, .8, .5, .35, .5, .3, .25, .15, .12, .08, .05]
	tau = [3.5, 3.2, 2.8, 2.6, 1.6, 2.0, 1.2, 1.0, .8, .6, .45, .35]
	y = partials(f, r, a, tau, 4.0, .004) + .35 * bp_noise(4.0, 40, 400, .04) + .12 * bp_noise(4.0, 400, 3000, .02)
	t = T(4.0)
	for _ in range(20):  # shimmer bloom
		y += rng.uniform(.01, .04) * np.sin(2 * np.pi * rng.uniform(500, 3000) * t) * (1 - np.exp(-t / rng.uniform(.05, .2))) * np.exp(-t / rng.uniform(.5, 1.5))
	k = int(.6 * SR)
	y[-k:] *= np.linspace(1, 0, k) ** 2
	return y


def s_crowd_cheer():
	dur = 3.0
	n = int(dur * SR)
	t = np.arange(n) / SR
	src, sr = sf.read(os.path.join(HERE, 'applause.wav'))
	assert sr == SR
	mono = src.mean(1)
	w = int(dur * SR)
	e = np.convolve(mono ** 2, np.ones(SR // 10), 'same')[::SR // 20]
	best = max(range(0, len(e) - w // (SR // 20)), key=lambda i: e[i:i + w // (SR // 20)].sum()) * (SR // 20)
	clap = ss.sosfilt(ss.butter(2, 150, btype='high', fs=SR, output='sos'), mono[best:best + n])
	clap /= np.sqrt(np.mean(clap ** 2))
	vox = np.zeros(n)
	formants = [(800, 1150, 2900), (400, 2000, 2550), (500, 900, 2400), (650, 1700, 2600)]
	for _ in range(36):
		f0 = rng.uniform(140, 330)
		on = rng.uniform(0, .35)
		ln = rng.uniform(1.2, 2.3)
		tt = t - on
		act = (tt > 0) & (tt < ln + .4)
		glide = f0 * (0.85 + .4 * np.clip(tt / .4, 0, 1) - .2 * np.clip((tt - .4) / ln, 0, 1))
		glide *= 1 + .02 * np.sin(2 * np.pi * rng.uniform(4, 7) * t + rng.uniform(0, 6))
		ph = 2 * np.pi * np.cumsum(glide) / SR
		src_v = sum(h ** -1.2 * np.sin(h * ph) for h in range(1, 25)) + .6 * rng.standard_normal(n)
		fo = formants[rng.integers(len(formants))]
		v = sum(ss.sosfilt(ss.butter(2, [fc * .85, fc * 1.15], btype='band', fs=SR, output='sos'), src_v) * g for fc, g in zip(fo, (1, .6, .3)))
		env = np.clip(tt / rng.uniform(.1, .25), 0, 1) * np.clip((ln + .4 - tt) / .4, 0, 1) * act
		vox += v * env * rng.uniform(.5, 1)
	vox /= np.sqrt(np.mean(vox ** 2))
	roar = ss.sosfilt(ss.butter(2, [300, 3000], btype='band', fs=SR, output='sos'), rng.standard_normal(n))
	roar /= np.sqrt(np.mean(roar ** 2))
	env = np.clip(t / .08, 0, 1) * np.clip((dur - t) / 1.4, 0, 1) ** 1.5
	return (.7 * clap + .45 * vox + .2 * roar) * env


def s_cord_snap():
	n = int(.5 * SR)
	y = np.zeros(n)
	z = swept_noise(.07, [2500, 6000], lambda t: (t / .07) ** 2)
	y[:len(z)] += .5 * z
	i = len(z)
	y[i:i + 4] += [1, -.8, .5, -.3]
	crack = bp_noise(.004, 2500, 12000, .0015)
	y[i:i + len(crack)] += .9 * crack / np.abs(crack).max()
	p = int(SR / 220)  # Karplus-Strong twang
	buf = rng.uniform(-1, 1, p)
	ks = np.zeros(int(.35 * SR))
	for k in range(len(ks)):
		ks[k] = buf[k % p]
		buf[k % p] = .996 * .5 * (buf[k % p] + buf[(k + 1) % p])
	y[i:i + len(ks)] += .35 * ks[:n - i] * np.exp(-np.arange(len(ks))[:n - i] / SR / .12)
	return y


def s_land():
	def hit(a):
		t = T(.3)
		f = 110 + 70 * np.exp(-t / .015)
		y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .09)
		y += partials(410, [1, 2.27, 4.2, 6.34], [.5, .35, .2, .1], [.05, .03, .018, .01], .3, .0005)
		sos = ss.butter(2, 3000, fs=SR, output='sos')
		y += .4 * ss.sosfilt(sos, rng.standard_normal(len(t))) * np.exp(-t / .004)
		return a * y
	y = np.zeros(int(.45 * SR))
	for t0, a in ((0, 1), (.085, .35), (.15, .12)):
		h = hit(a)
		i = int(t0 * SR)
		y[i:i + len(h)] += h[:len(y) - i]
	return y


def sfx():
	for name, fn, pk in (('whoosh', s_whoosh, -1), ('jump', s_jump, -1), ('charge_tick', s_charge_tick, -1), ('ui_hover', s_ui_hover, -10),
			('gong', s_gong, -1), ('crowd_cheer', s_crowd_cheer, -1), ('cord_snap', s_cord_snap, -1), ('land', s_land, -1)):
		write(f'sfx/{name}.ogg', sfx_master(fn(), pk))
	y = s_rush_loop()
	write('sfx/rush_loop.ogg', y, len(y))


if __name__ == '__main__':
	sfx()
	menu()
	battle()
	cutscene()
	victory()
	defeat()
