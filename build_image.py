#!/usr/bin/env python3
"""Build the news-image-20261119 entry: a one-day world-news front page.

Draws a 1024x1024 broadsheet-style infographic summing up the world news of
Thursday 19 November 2026, using only Pillow + numpy. Deterministic: no
randomness, no clock, no network. Run: python3 build_image.py -> entry.png

Stories (all verified against wire/agency reporting of 19 Nov 2026):
  LEAD  Trump, Xi and Putin meet in Shenzhen — the first-ever trilateral.
        Nuclear arms and the Iran war on the agenda; Ukraine left off it.
        New START, the last US-Russia arms cap, lapsed in February.
  AKVAN Cyclone Akvan, a severe cyclonic storm (90-100 km/h, gusts 110),
        closes on India's east coast; landfall Narsapur-Puri by noon Fri.
        Red alert; schools shut in six Odisha districts.
  GTA   After 13 years, Grand Theft Auto VI rolls out worldwide — midnight
        local time, starting in New Zealand. Metacritic 99; ~17m copies
        and $1.65bn in pre-sales (Sensor Tower).
  GULF  The US-Iran exchange widens: US jets strike an IRGC missile site
        on Qeshm Island; Iran's drones hit US bases in Bahrain and Kuwait.
  US    House Democrats nominate Hakeem Jeffries for Speaker, 251-11; he
        would be the first Black Speaker if elected on 3 January.
  SPACE Voyager 1 is one light-day from Earth (16bn miles); NASA briefs
        the milestone today at noon EST.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 230)      # warm newsprint
CARD = (255, 253, 247)       # card white
INK = (26, 32, 48)           # deep navy ink
NAVY = (16, 28, 52)          # band navy
NAVY2 = (30, 46, 78)         # lighter navy
CRIMSON = (166, 28, 28)      # headline red
TEAL = (14, 107, 98)         # secondary accent
TEAL_DK = (9, 74, 68)
GOLD = (185, 138, 29)        # rule gold
GOLD_LT = (226, 190, 90)
MUTED = (96, 104, 118)
LINE = (214, 205, 186)       # hairline
WHITE = (255, 255, 255)
SKY_TOP = (20, 26, 58)       # dusk sky
SKY_MID = (88, 52, 96)
SKY_LOW = (226, 130, 66)     # dusk horizon
SEA = (18, 52, 84)

# ---------------------------------------------------------------- fonts
FONT_DIR = "/usr/share/fonts/truetype/noto"
SERIF_B = os.path.join(FONT_DIR, "NotoSerif-Bold.ttf")
SERIF_R = os.path.join(FONT_DIR, "NotoSerif-Regular.ttf")
SANS_R = os.path.join(FONT_DIR, "NotoSans-Regular.ttf")
SANS_B = os.path.join(FONT_DIR, "NotoSans-Bold.ttf")
SANS_X = os.path.join(FONT_DIR, "NotoSans-Black.ttf")
SANS_I = os.path.join(FONT_DIR, "NotoSans-Italic.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- helpers
def vgrad(w, h, top, bottom):
    """Vertical RGB gradient as an Image."""
    t = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    top_a = np.array(top, dtype=np.float32)[None, None, :]
    bot_a = np.array(bottom, dtype=np.float32)[None, None, :]
    arr = (top_a * (1.0 - t) + bot_a * t).astype(np.uint8)
    arr = np.repeat(arr, w, axis=1)
    return Image.fromarray(arr, "RGB")


def soft_shadow(base, box, radius=10, alpha=60):
    """Paint a soft drop shadow for `box` onto RGBA image `base`."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0 + 3, y0 + 4, x1 + 3, y1 + 4], radius=radius,
                        fill=(20, 25, 40, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(4))
    base.alpha_composite(layer)


def card(base, box, fill=CARD, outline=LINE, radius=6, shadow=True):
    """A paper card with optional soft shadow; returns its draw context."""
    if shadow:
        soft_shadow(base, box, radius=radius)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=1)
    return d


def wrap_text(text, fnt, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if fnt.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(d, x, y, text, fnt, fill, max_w, leading=None):
    """Draw wrapped text; returns y after the last line."""
    if leading is None:
        leading = int(fnt.size * 1.28)
    for line in wrap_text(text, fnt, max_w):
        d.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def kicker(d, x, y, text, size=15, fill=CRIMSON):
    """Small-caps section label with a short rule after it."""
    f = font(SANS_B, size)
    d.text((x, y), text, font=f, fill=fill)
    tw = f.getlength(text)
    d.line([(x + tw + 10, y + size // 2), (x + tw + 34, y + size // 2)],
           fill=fill, width=2)
    return x + tw + 44


def rule(d, x0, x1, y, fill=INK, width=2):
    d.line([(x0, y), (x1, y)], fill=fill, width=width)


def dot(d, cx, cy, r, fill):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


# ---------------------------------------------------------------- illustrations
def sky3(w, h, c_top, c_mid, c_low):
    """Three-stop vertical sky gradient."""
    t = np.linspace(0.0, 1.0, h, dtype=np.float32)
    top = np.array(c_top, dtype=np.float32)
    mid = np.array(c_mid, dtype=np.float32)
    low = np.array(c_low, dtype=np.float32)
    arr = np.zeros((h, 3), dtype=np.float32)
    half = t <= 0.55
    s = np.clip(t[half] / 0.55, 0, 1)[:, None]
    arr[half] = top * (1 - s) + mid * s
    s2 = np.clip((t[~half] - 0.55) / 0.45, 0, 1)[:, None]
    arr[~half] = mid * (1 - s2) + low * s2
    arr = np.repeat(arr[:, None, :], w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def draw_flag_us(d, x, y, w, h):
    """Stars and Stripes, simplified but recognisable."""
    for i in range(13):
        col = (178, 34, 52, 255) if i % 2 == 0 else (255, 255, 255, 255)
        d.rectangle([x, y + i * h // 13, x + w, y + (i + 1) * h // 13],
                    fill=col)
    cw, ch = int(w * 0.42), int(h * 7 // 13)
    d.rectangle([x, y, x + cw, y + ch], fill=(28, 48, 94, 255))
    for r in range(4):
        for c in range(5):
            sx = x + 5 + c * (cw - 8) // 4
            sy = y + 4 + r * (ch - 8) // 3
            dot(d, sx, sy, 1, (255, 255, 255, 255))


def draw_flag_cn(d, x, y, w, h):
    """China: red field, one large gold star and four small ones."""
    d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16, 255))
    cx, cy = x + int(w * 0.20), y + int(h * 0.26)
    star(d, cx, cy, 7, GOLD_LT + (255,))
    for sx, sy in ((0.48, 0.12), (0.60, 0.26), (0.58, 0.44), (0.44, 0.50)):
        star(d, x + int(w * sx), y + int(h * sy), 3, GOLD_LT + (255,))


def draw_flag_ru(d, x, y, w, h):
    """Russia: white-blue-red horizontal tricolour."""
    d.rectangle([x, y, x + w, y + h // 3], fill=(255, 255, 255, 255))
    d.rectangle([x, y + h // 3, x + w, y + 2 * h // 3],
                fill=(0, 57, 166, 255))
    d.rectangle([x, y + 2 * h // 3, x + w, y + h], fill=(213, 0, 50, 255))


def star(d, cx, cy, r, fill):
    """Five-pointed star centred at (cx, cy)."""
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill)


def draw_hero(box):
    """Shenzhen at dusk: skyline, low sun, bay — and the three flags of
    the first-ever Trump-Xi-Putin trilateral. Returns an RGB image."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    img = sky3(w, h, SKY_TOP, SKY_MID, SKY_LOW).convert("RGBA")
    d = ImageDraw.Draw(img)
    # early stars in the deep sky
    for sx, sy, sr in ((int(w * 0.08), int(h * 0.10), 2),
                       (int(w * 0.14), int(h * 0.06), 1),
                       (int(w * 0.42), int(h * 0.08), 2),
                       (int(w * 0.58), int(h * 0.05), 1),
                       (int(w * 0.90), int(h * 0.12), 2),
                       (int(w * 0.95), int(h * 0.06), 1),
                       (int(w * 0.30), int(h * 0.14), 1)):
        dot(d, sx, sy, sr, (255, 255, 255, 200))
    # crescent moon, upper right
    mx, my, mr = int(w * 0.88), int(h * 0.16), 15
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr],
              fill=(240, 234, 210, 255))
    d.ellipse([mx - mr + 7, my - mr - 2, mx + mr + 7, my + mr - 2],
              fill=(52, 44, 78, 255))
    # low sun with glow, left of centre
    sx, sy, sr = int(w * 0.30), int(h * 0.62), 32
    for r, a in ((84, 26), (62, 40), (46, 70)):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 196, 110, a))
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 214, 140, 255))
    # haze band above the skyline
    d.rectangle([0, int(h * 0.60), w, int(h * 0.66)],
                fill=(240, 170, 110, 55))
    # skyline silhouette (deterministic heights), one tapered tower
    heights = [52, 88, 64, 118, 76, 96, 58, 132, 84, 70, 108, 62, 92, 74,
               126, 66, 98, 56, 82, 110, 60, 88, 72, 104, 64, 78]
    bw = w // len(heights)
    base_y = int(h * 0.78)
    sil = (13, 20, 40, 255)
    for i, hh in enumerate(heights):
        bx = i * bw
        top = base_y - hh
        if i == 14:  # tapered landmark tower
            d.polygon([(bx + 2, base_y), (bx + 8, top - 30),
                       (bx + bw - 8, top - 30), (bx + bw - 2, base_y)],
                      fill=sil)
            d.line([(bx + bw // 2, top - 30), (bx + bw // 2, top - 44)],
                   fill=sil, width=3)
            dot(d, bx + bw // 2, top - 46, 3, (255, 90, 90, 255))
        else:
            d.rectangle([bx + 1, top, bx + bw - 1, base_y], fill=sil)
        if i % 5 == 2:  # antenna spire
            d.line([(bx + bw // 2, top), (bx + bw // 2, top - 20)],
                   fill=sil, width=3)
            dot(d, bx + bw // 2, top - 22, 3, (255, 90, 90, 255))
        # lit windows, deterministic pattern
        for wy in range(top + 8, base_y - 6, 12):
            for wx in range(bx + 5, bx + bw - 5, 9):
                if (wx * 7 + wy * 13) % 11 < 4:
                    d.rectangle([wx, wy, wx + 3, wy + 4],
                                fill=(255, 205, 110, 220))
    # the three flags of the trilateral, on poles in front of the skyline
    fw, fh = 60, 40
    for fx, flag in ((int(w * 0.43), draw_flag_us),
                     (int(w * 0.545), draw_flag_cn),
                     (int(w * 0.66), draw_flag_ru)):
        pole_top = base_y - 68
        d.line([(fx, pole_top), (fx, base_y)], fill=(216, 190, 130, 255),
               width=3)
        dot(d, fx, pole_top - 3, 3, GOLD + (255,))
        d.rectangle([fx, pole_top, fx + fw, pole_top + fh],
                    outline=(0, 0, 0, 90), width=1)
        flag(d, fx + 1, pole_top + 1, fw - 2, fh - 2)
    # bay water with sun reflection
    d.rectangle([0, base_y, w, h], fill=SEA + (255,))
    for k in range(9):
        yy = base_y + 6 + k * 5
        half_w = 150 - k * 12
        d.line([(sx - half_w, yy), (sx + half_w, yy)],
               fill=(255, 190, 110, 150 - k * 12), width=2)
    for k in range(26):  # wave strokes
        wx = (k * 97) % w
        wy = base_y + 8 + (k * 29) % (h - base_y - 10)
        ln = 14 + (k * 13) % 22
        d.line([(wx, wy), (wx + ln, wy)], fill=(140, 190, 220, 90), width=2)
    # birds
    for bx, by, s in ((int(w * 0.08), int(h * 0.24), 7),
                      (int(w * 0.15), int(h * 0.19), 5),
                      (int(w * 0.72), int(h * 0.12), 6)):
        d.arc([bx - s, by - s, bx, by + s], 200, 340, fill=(20, 28, 50, 220),
              width=2)
        d.arc([bx, by - s, bx + s, by + s], 200, 340, fill=(20, 28, 50, 220),
              width=2)
    return img.convert("RGB")


def draw_cyclone(box):
    """Cyclone Akvan spiral over the Bay of Bengal. Returns an RGB image."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    img = vgrad(w, h, (10, 60, 74), (16, 110, 122)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # coastline hint (India's east coast) on the right
    coast = [(w, 0), (int(w * 0.88), 0), (int(w * 0.83), int(h * 0.28)),
             (int(w * 0.89), int(h * 0.52)), (int(w * 0.84), int(h * 0.76)),
             (int(w * 0.89), h), (w, h)]
    d.polygon(coast, fill=(216, 188, 138, 255))
    d.line(coast[1:-1], fill=(120, 90, 50, 255), width=2)
    dot(d, int(w * 0.875), int(h * 0.55), 5, CRIMSON + (255,))
    d.ellipse([int(w * 0.875) - 8, int(h * 0.55) - 8,
               int(w * 0.875) + 8, int(h * 0.55) + 8],
              outline=(255, 255, 255, 255), width=2)
    # spiral bands: arcs of growing radius, shrinking sweep
    cx, cy = int(w * 0.44), int(h * 0.52)
    for k in range(9):
        r = 12 + k * 11
        a0 = 40 + k * 52
        a1 = a0 + 250 - k * 14
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1,
              fill=(255, 255, 255, 235 - k * 16), width=7)
    # eye
    d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=(8, 44, 56, 255),
              outline=(255, 255, 255, 255), width=2)
    # rain streaks
    for k in range(18):
        rx = (k * 53) % w
        ry = (k * 37) % h
        d.line([(rx, ry), (rx - 7, ry + 13)], fill=(200, 225, 235, 110),
               width=2)
    # wind tag
    tag = "90-100 KM/H"
    f = font(SANS_B, 15)
    tw = f.getlength(tag)
    d.rounded_rectangle([10, 10, 10 + tw + 18, 34], radius=5,
                        fill=(166, 28, 28, 235))
    d.text((19, 13), tag, font=f, fill=(255, 255, 255, 255))
    return img.convert("RGB")


def draw_vicecity(box):
    """Vice City at night: synthwave sun, palms, neon skyline.
    Returns an RGB image."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    img = sky3(w, h, (58, 16, 92), (176, 44, 118), (255, 140, 60)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # synthwave sun with slats
    sx, sy, sr = int(w * 0.50), int(h * 0.46), 34
    for r, a in ((58, 30), (46, 55)):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 190, 90, a))
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 214, 120, 255))
    # slat gaps across the sun's lower half
    for k in range(4):
        yy = sy + 4 + k * 9
        d.rectangle([sx - sr, yy, sx + sr, yy + 4], fill=(176, 44, 118, 255))
    # stars
    for px, py in ((18, 10), (52, 22), (w - 30, 12), (w - 64, 26),
                   (120, 8), (w - 120, 8)):
        dot(d, px, py, 1, (255, 255, 255, 220))
    # neon skyline
    heights = [34, 58, 44, 70, 50, 64, 40, 78, 54, 46, 66, 38, 60, 48]
    bw = w // len(heights)
    base_y = int(h * 0.86)
    sil = (24, 10, 44, 255)
    for i, hh in enumerate(heights):
        bx = i * bw
        top = base_y - hh
        d.rectangle([bx + 1, top, bx + bw - 1, base_y], fill=sil)
        for wy in range(top + 6, base_y - 5, 10):
            for wx in range(bx + 5, bx + bw - 5, 8):
                if (wx * 5 + wy * 7) % 9 < 3:
                    col = (90, 240, 255, 230) if (wx + wy) % 3 else (255, 120, 200, 230)
                    d.rectangle([wx, wy, wx + 2, wy + 3], fill=col)
    # palm silhouettes, left and right — filled fronds so they read
    # against the bright sky
    palm = (38, 16, 62, 255)
    for px, lean in ((int(w * 0.06), 1), (int(w * 0.94), -1)):
        d.line([(px, base_y), (px + lean * 10, base_y - 56)],
               fill=palm, width=5)
        tx, ty = px + lean * 10, base_y - 56
        for ang in (-75, -40, -5, 30, 65):
            rad = math.radians(ang)
            ex = tx + lean * int(30 * math.cos(rad))
            ey = ty + int(24 * math.sin(rad)) - 10
            mx = tx + lean * int(15 * math.cos(rad))
            my = ty + int(12 * math.sin(rad)) - 2
            d.polygon([(tx, ty), (mx, my - 6), (ex, ey), (mx, my + 6)],
                      fill=palm)
    # wet boulevard with neon reflections
    d.rectangle([0, base_y, w, h], fill=(16, 8, 34, 255))
    for k in range(6):
        yy = base_y + 3 + k * 2
        d.line([(sx - 60 + k * 6, yy), (sx + 60 - k * 6, yy)],
               fill=(255, 170, 90, 140 - k * 16), width=2)
    # "VICE CITY" neon sign strip
    sign = "VICE CITY"
    f = font(SANS_X, 13)
    tw = f.getlength(sign)
    d.rounded_rectangle([w // 2 - tw // 2 - 10, base_y + 2,
                         w // 2 + tw // 2 + 10, base_y + 20], radius=4,
                        fill=(20, 8, 40, 230), outline=(255, 110, 200, 255),
                        width=1)
    d.text((w // 2, base_y + 4), sign, font=f,
           fill=(255, 140, 220, 255), anchor="ma")
    return img.convert("RGB")


def draw_radar(box):
    """Radar screen with sweep and blips, plus a drone silhouette."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2 - 6, h // 2
    # screen
    d.rounded_rectangle([2, 2, w - 14, h - 2], radius=8, fill=NAVY + (255,),
                        outline=GOLD + (255,), width=2)
    # range rings + crosshair
    for r in (10, 19, 28):
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  outline=(46, 160, 140, 255), width=1)
    d.line([(cx - 28, cy), (cx + 28, cy)], fill=(46, 160, 140, 255), width=1)
    d.line([(cx, cy - 28), (cx, cy + 28)], fill=(46, 160, 140, 255), width=1)
    # sweep wedge
    d.pieslice([cx - 28, cy - 28, cx + 28, cy + 28], 300, 345,
               fill=(90, 220, 190, 160))
    # blips
    dot(d, cx + 14, cy - 12, 3, (255, 90, 90, 255))
    dot(d, cx - 16, cy + 10, 3, (255, 205, 110, 255))
    dot(d, cx + 6, cy + 18, 2, (255, 255, 255, 255))
    # drone silhouette, upper right — kept fully inside the screen frame
    dx, dy = w - 30, 14
    d.line([(dx - 10, dy - 6), (dx + 10, dy + 6)], fill=INK + (255,),
           width=3)
    d.line([(dx - 10, dy + 6), (dx + 10, dy - 6)], fill=INK + (255,),
           width=3)
    for rx, ry in ((dx - 10, dy - 6), (dx + 10, dy - 6),
                   (dx - 10, dy + 6), (dx + 10, dy + 6)):
        d.ellipse([rx - 4, ry - 2, rx + 4, ry + 2], fill=INK + (255,))
    dot(d, dx, dy, 4, CRIMSON + (255,))
    return img


def draw_capitol(box):
    """US Capitol dome in navy and gold."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    # base steps
    d.rectangle([cx - 34, h - 10, cx + 34, h - 4], fill=NAVY + (255,))
    d.rectangle([cx - 28, h - 16, cx + 28, h - 10], fill=NAVY2 + (255,))
    # columns
    for k in range(5):
        colx = cx - 24 + k * 12
        d.rectangle([colx, h - 34, colx + 5, h - 16], fill=NAVY + (255,))
    d.rectangle([cx - 28, h - 38, cx + 28, h - 34], fill=NAVY + (255,))
    # drum + dome
    d.rectangle([cx - 14, h - 52, cx + 14, h - 38], fill=NAVY2 + (255,))
    d.pieslice([cx - 20, h - 66, cx + 20, h - 26], 180, 360,
               fill=GOLD + (255,))
    d.rectangle([cx - 1, h - 74, cx + 1, h - 66], fill=GOLD + (255,))
    dot(d, cx, h - 76, 2, GOLD + (255,))
    # flag on the dome
    d.line([(cx, h - 76), (cx, h - 88)], fill=INK + (255,), width=2)
    d.polygon([(cx, h - 88), (cx + 12, h - 85), (cx, h - 82)],
              fill=CRIMSON + (255,))
    # stars
    for sx, sy in ((8, 8), (w - 10, 14), (12, h - 8)):
        star(d, sx, sy, 3, GOLD + (255,))
    return img


def draw_voyager(box):
    """Voyager probe with dish, boom and signal rings against stars."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # deep-space backdrop
    d.rounded_rectangle([2, 2, w - 2, h - 2], radius=8, fill=NAVY + (255,))
    for sx, sy, sr in ((10, 8, 1), (w - 12, 10, 1), (16, h - 10, 1),
                       (w - 18, h - 14, 2), (30, 16, 1)):
        dot(d, sx, sy, sr, (255, 255, 255, 230))
    # signal rings from the dish
    for r, a in ((16, 120), (24, 80), (32, 50)):
        d.arc([w // 2 - r, h // 2 - 8 - r, w // 2 + r, h // 2 - 8 + r],
              200, 340, fill=(120, 200, 240, a), width=2)
    # bus + wide dish (parabola opening upward)
    cx, cy = w // 2, h // 2 + 10
    d.rectangle([cx - 12, cy - 4, cx + 12, cy + 8], fill=GOLD + (255,),
                outline=WHITE + (255,), width=1)
    d.pieslice([cx - 18, cy - 34, cx + 18, cy - 2], 0, 180,
               fill=(226, 190, 90, 255), outline=WHITE + (255,))
    d.line([(cx, cy - 4), (cx, cy - 24)], fill=WHITE + (255,), width=2)
    dot(d, cx, cy - 24, 2, (255, 255, 255, 255))
    # boom with RTG fins
    d.line([(cx + 12, cy + 2), (cx + 30, cy + 10)], fill=WHITE + (255,),
           width=2)
    for k in range(3):
        fx = cx + 18 + k * 5
        d.line([(fx, cy + 4), (fx, cy + 12)], fill=(200, 210, 225, 255),
               width=2)
    # antenna mast
    d.line([(cx - 12, cy), (cx - 26, cy - 12)], fill=WHITE + (255,), width=2)
    dot(d, cx - 26, cy - 12, 2, (255, 90, 90, 255))
    return img


# ---------------------------------------------------------------- layout
MX = 24            # side margin
RX = W - MX        # right edge


def masthead(img):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=CRIMSON)
    # nameplate
    d.text((W // 2, 12), "THE WORLD", font=font(SERIF_B, 80), fill=INK,
           anchor="ma")
    small = font(SANS_R, 13)
    d.text((MX, 52), "VOL. I — No. 323", font=small, fill=MUTED)
    d.text((RX, 52), "PRICE: ONE DAY'S NEWS", font=small, fill=MUTED,
           anchor="ra")
    rule(d, MX, RX, 106, fill=INK, width=2)
    rule(d, MX, RX, 110, fill=INK, width=1)
    # date band
    d.rounded_rectangle([MX, 118, RX, 152], radius=6, fill=NAVY)
    band = "THURSDAY  •  19 NOVEMBER 2026  •  THE DAY IN THE WORLD"
    d.text((W // 2, 125), band, font=font(SANS_B, 21), fill=WHITE,
           anchor="ma")
    d.line([(MX + 14, 135), (MX + 64, 135)], fill=GOLD, width=2)
    d.line([(RX - 64, 135), (RX - 14, 135)], fill=GOLD, width=2)


def hero(img):
    d = ImageDraw.Draw(img)
    pic = draw_hero((0, 0, RX - MX, 234))
    img.paste(pic, (MX, 158))
    d.rectangle([MX, 158, RX, 392], outline=INK, width=2)
    # headline block: kicker + headline left, deck right
    kicker(d, MX, 402, "THE LEAD — SHENZHEN")
    d.text((MX, 420), "THREE AT THE TABLE", font=font(SERIF_B, 50), fill=INK)
    deck = ("Trump, Xi and Putin sit down in Shenzhen for the first-ever "
            "trilateral. Nuclear arms and the Iran war top the agenda; "
            "Ukraine is left off it.")
    draw_wrapped(d, 648, 408, deck, font(SERIF_R, 17), (52, 58, 76),
                 RX - 648, leading=22)
    rule(d, MX, RX, 498, fill=INK, width=2)


def middle_card(img, x, y, w, h, pic, kick, head, deck):
    card(img, (x, y, x + w, y + h))
    img.paste(pic, (x + 1, y + 1))
    d = ImageDraw.Draw(img)
    d.rectangle([x, y + 131, x + w, y + 132], fill=LINE)
    kicker(d, x + 14, y + 142, kick, size=13)
    draw_wrapped(d, x + 14, y + 160, head, font(SERIF_B, 23), INK,
                 w - 28, leading=28)
    draw_wrapped(d, x + 14, y + 218, deck, font(SERIF_R, 15), (52, 58, 76),
                 w - 28, leading=19)


def lower_card(img, x, y, w, h, icon, kick, head, deck):
    card(img, (x, y, x + w, y + h))
    img.paste(icon, (x + 12, y + 10), icon)
    d = ImageDraw.Draw(img)
    tx = x + 104
    d.text((tx, y + 12), kick, font=font(SANS_B, 12), fill=CRIMSON)
    draw_wrapped(d, tx, y + 30, head, font(SERIF_B, 19), INK,
                 w - 114, leading=23)
    draw_wrapped(d, x + 14, y + 78, deck, font(SERIF_R, 14), (52, 58, 76),
                 w - 28, leading=18)


def ticker(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([MX, 926, RX, 968], radius=6, fill=NAVY)
    label = "ALSO TODAY"
    lf = font(SANS_B, 14)
    d.text((MX + 14, 938), label, font=lf, fill=GOLD_LT)
    items = ("EU's €45bn Ukraine loan  •  Nvidia halts H-series chips  •  "
             "Canada rethinks China ties  •  Australia sanctions settlers")
    d.text((MX + 14 + lf.getlength(label) + 14, 938), items,
           font=font(SANS_R, 14), fill=WHITE)


def footer(img):
    d = ImageDraw.Draw(img)
    txt = ("Sources: Reuters · AP · AFP · Al Jazeera · IMD · NASA  —  "
           "Scenes drawn by program  —  Thursday, 19 November 2026")
    d.text((W // 2, 982), txt, font=font(SANS_I, 13), fill=MUTED,
           anchor="ma")


def build():
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    masthead(img)
    hero(img)
    # middle row: cyclone + GTA VI
    middle_card(img, MX, 508, 476, 264,
                draw_cyclone((0, 0, 474, 130)),
                "WEATHER — BAY OF BENGAL",
                "AKVAN CLOSES IN ON INDIA'S EAST COAST",
                "Severe cyclonic storm, winds 90–100 km/h. Landfall "
                "Narsapur–Puri by noon Friday; red alert.")
    middle_card(img, RX - 476, 508, 476, 264,
                draw_vicecity((0, 0, 474, 130)),
                "CULTURE — VICE CITY",
                "VICE CITY OPENS ITS DOORS",
                "After 13 years, GTA VI rolls out worldwide. Metacritic "
                "99; ~17m copies, $1.65bn in pre-sales.")
    # lower row: Gulf + US politics + space
    lower_card(img, MX, 784, 309, 132,
               draw_radar((0, 0, 84, 64)),
               "GULF — ESCALATION",
               "US–IRAN CLASH WIDENS",
               "US jets hit Qeshm; Iran's drones strike US bases in "
               "Bahrain and Kuwait.")
    lower_card(img, 357, 784, 309, 132,
               draw_capitol((0, 0, 84, 64)),
               "POLITICS — WASHINGTON",
               "JEFFRIES FOR SPEAKER",
               "House Democrats pick him 251–11; first Black Speaker if "
               "elected on 3 January.")
    lower_card(img, 690, 784, 310, 132,
               draw_voyager((0, 0, 84, 64)),
               "SPACE — INTERSTELLAR",
               "VOYAGER 1, A LIGHT-DAY OUT",
               "16bn miles from Earth; NASA briefs the milestone today "
               "at noon EST.")
    ticker(img)
    footer(img)
    return img.convert("RGB")


def main():
    img = build()
    img.save("entry.png", optimize=True)
    size = os.path.getsize("entry.png")
    print(f"entry.png: {img.size[0]}x{img.size[1]} {size} bytes "
          f"({'OK' if size <= 1048576 else 'TOO BIG'})")


if __name__ == "__main__":
    main()
