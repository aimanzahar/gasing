# Generates the Gasing Pangkah branding images from the gunungan art (assets/ui/gunungan_gold.png):
#   assets/branding/icon.png (256) + icon.ico (16..256)  app / exe / window icon
#   assets/branding/splash.png (1920x1080)                boot splash, gunungan on PANEL_BG
#   assets/branding/cursor.png (32)                       mouse cursor, hotspot (2, 2)
# Needs: pip install pillow. Colours are the heritage_theme.gd palette tokens.
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'assets', 'branding')


def rgb(r, g, b):
	return (round(r * 255), round(g * 255), round(b * 255))


PANEL_BG = rgb(0.11, 0.06, 0.035)
SONGKET_GOLD = rgb(1.0, 0.78, 0.25)
WOOD_AMBER = rgb(0.82, 0.6, 0.24)
WOOD_DARK = rgb(0.3, 0.2, 0.1)
WOOD_EDGE = rgb(0.16, 0.09, 0.05)
INK = rgb(0.12, 0.07, 0.03)


def gradient(size, top, bottom):
	# vertical two-colour gradient, RGBA
	w, h = size
	col = Image.new('RGBA', (1, h))
	for y in range(h):
		t = y / max(h - 1, 1)
		col.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)) + (255,))
	return col.resize((w, h))


def radial(size, inner, outer, radius):
	# radial glow from the centre; exactly `outer` from `radius` (fraction of the half-diagonal) out
	w, h = size
	small = Image.new('RGB', (w // 8, h // 8))
	cx, cy = small.width / 2, small.height / 2
	rmax = radius * (cx * cx + cy * cy) ** 0.5
	for y in range(small.height):
		for x in range(small.width):
			t = min((((x - cx) ** 2 + (y - cy) ** 2) ** 0.5) / rmax, 1.0)
			t = t * t * (3 - 2 * t)
			small.putpixel((x, y), tuple(round(a + (b - a) * t) for a, b in zip(inner, outer)))
	return small.resize((w, h), Image.BICUBIC).convert('RGBA')


def gunungan(height, top=SONGKET_GOLD, bottom=WOOD_AMBER):
	# the gunungan silhouette (cut-outs kept) filled with a gold -> amber gradient, cropped to its bbox
	src = Image.open(os.path.join(ROOT, 'assets', 'ui', 'gunungan_gold.png')).convert('RGBA')
	src = src.crop(src.getbbox())
	w = round(src.width * height / src.height)
	mask = src.getchannel('A').resize((w, height), Image.LANCZOS)
	fill = gradient((w, height), top, bottom)
	fill.putalpha(mask)
	return fill


def paste_shadowed(dst, img, pos, blur, drop, alpha):
	# soft drop shadow (padded so the blur never clips), then the image on top
	pad = round(blur * 3) + drop
	sh = Image.new('RGBA', (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
	sh.paste((0, 0, 0, 255), (pad, pad + drop), img.getchannel('A').point(lambda v: round(v * alpha)))
	dst.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)), (pos[0] - pad, pos[1] - pad))
	dst.alpha_composite(img, pos)


def make_icon(n=1024):
	img = Image.new('RGBA', (n, n), (0, 0, 0, 0))
	radius = round(n * 0.2)
	plate = radial((n, n), WOOD_DARK, PANEL_BG, 0.95)
	mask = Image.new('L', (n, n), 0)
	ImageDraw.Draw(mask).rounded_rectangle((0, 0, n - 1, n - 1), radius, fill=255)
	img.paste(plate, (0, 0), mask)
	d = ImageDraw.Draw(img)
	# songket double border: gold outer line, thin amber inner line
	m = round(n * 0.045)
	d.rounded_rectangle((m, m, n - 1 - m, n - 1 - m), radius - m, outline=SONGKET_GOLD, width=round(n * 0.03))
	m2 = round(n * 0.1)
	d.rounded_rectangle((m2, m2, n - 1 - m2, n - 1 - m2), radius - m2, outline=WOOD_AMBER, width=round(n * 0.01))
	g = gunungan(round(n * 0.7))
	pos = ((n - g.width) // 2, round(n * 0.155))
	paste_shadowed(img, g, pos, n * 0.012, round(n * 0.015), 0.7)
	return img


def make_splash(w=1920, h=1080):
	img = radial((w, h), rgb(0.22, 0.12, 0.06), PANEL_BG, 0.8) # blencong lamp glow on the kelir
	g = gunungan(round(h * 0.5))
	pos = ((w - g.width) // 2, round(h * 0.14))
	paste_shadowed(img, g, pos, 14, 10, 0.8)
	font = ImageFont.truetype(os.path.join(ROOT, 'common', 'fonts', 'Kurland.ttf'), round(h * 0.085))
	d = ImageDraw.Draw(img)
	text = 'GASING PANGKAH'
	box = d.textbbox((0, 0), text, font=font)
	tx = (w - (box[2] - box[0])) // 2 - box[0]
	ty = round(h * 0.7) - box[1]
	d.text((tx + 4, ty + 6), text, font=font, fill=INK)
	d.text((tx, ty), text, font=font, fill=SONGKET_GOLD)
	# songket band under the title: the greyscale tile tinted gold (the engine modulates it the same way)
	tile = Image.open(os.path.join(ROOT, 'assets', 'ui', 'songket_band.png')).convert('RGBA')
	bh = round(h * 0.026)
	tile = tile.resize((round(tile.width * bh / tile.height), bh), Image.LANCZOS)
	tinted = Image.new('RGBA', tile.size)
	tinted.putdata([(r * SONGKET_GOLD[0] // 255, g2 * SONGKET_GOLD[1] // 255, b * SONGKET_GOLD[2] // 255, a) for r, g2, b, a in tile.getdata()])
	count = 7
	for i in range(count):
		img.alpha_composite(tinted, ((w - tinted.width * count) // 2 + i * tinted.width, round(h * 0.84)))
	return img.convert('RGB')


def make_cursor():
	s = 8 # draw at 8x, downsample for anti-aliasing
	n = 32 * s
	img = Image.new('RGBA', (n, n), (0, 0, 0, 0))
	tip = (2, 2)
	pts = [(0, 0), (0, 21), (5, 16.5), (8.5, 25), (12, 23.5), (8.8, 15.2), (15.5, 15.2)]
	poly = [((tip[0] + x) * s, (tip[1] + y) * s) for x, y in pts]
	shadow = Image.new('RGBA', (n, n), (0, 0, 0, 0))
	ImageDraw.Draw(shadow).polygon([(x + 1.5 * s, y + 1.5 * s) for x, y in poly], fill=(0, 0, 0, 110))
	img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(s)))
	fill = gradient((n, n), SONGKET_GOLD, WOOD_AMBER)
	mask = Image.new('L', (n, n), 0)
	ImageDraw.Draw(mask).polygon(poly, fill=255)
	img.paste(fill, (0, 0), mask)
	ImageDraw.Draw(img).line(poly + [poly[0]], fill=INK + (255,), width=round(1.6 * s), joint='curve')
	return img.resize((32, 32), Image.LANCZOS)


if __name__ == '__main__':
	os.makedirs(OUT, exist_ok=True)
	master = make_icon()
	master.resize((256, 256), Image.LANCZOS).save(os.path.join(OUT, 'icon.png'))
	sizes = [16, 24, 32, 48, 64, 128, 256]
	frames = [master.resize((k, k), Image.LANCZOS) for k in sizes]
	frames[-1].save(os.path.join(OUT, 'icon.ico'), format='ICO', sizes=[(k, k) for k in sizes], append_images=frames[:-1])
	make_splash().save(os.path.join(OUT, 'splash.png'), optimize=True)
	cur = make_cursor()
	cur.save(os.path.join(OUT, 'cursor.png'))
	# self-check: the ICO carries every size, the splash edge is exactly PANEL_BG (seamless letterbox)
	ico = Image.open(os.path.join(OUT, 'icon.ico'))
	assert sorted(ico.info['sizes']) == sorted((k, k) for k in sizes), ico.info['sizes']
	sp = Image.open(os.path.join(OUT, 'splash.png'))
	assert sp.getpixel((0, 0)) == PANEL_BG and sp.getpixel((sp.width - 1, sp.height - 1)) == PANEL_BG, sp.getpixel((0, 0))
	assert cur.getpixel((2, 2))[3] > 0 and cur.size == (32, 32)
	print('branding: ok ->', OUT)
