"""Labeled contact sheets, so you can SEE every item before classifying or citing it.

Usage:
    python3 contact_sheets.py <work> [slug ...]

Reads <work>/data/<slug>.json + <work>/media/<slug>/ and writes <work>/sheets/:
    <slug>-1.jpg, <slug>-2.jpg ...   12 tiles per sheet (4 x 3), each labeled "#N  ratio  kind"
    <slug>-x007.jpg                  strip of every carousel slot / video frame of item #7 (max 10)

Kinds: img, CAROUSEL xK, VIDEO 12s. Ratios snap to 9:16, 2:3, 4:5, 3:4, 1:1, 4:3, 16:9, 3:2 (else the decimal).
Open every sheet before citing a number: board order changes between scrapes, and the label on the
sheet is the only numbering that matches the current manifest.

Requirements: Python 3.9+, Pillow (10.1+ for the scalable fallback font).
"""
import glob
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

TW, TH, COLS, PER = 400, 500, 4, 12
FONTS = ['/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/SFNS.ttf', '/Library/Fonts/Arial.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf']


def load_font(px=22):
    for f in FONTS:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, px)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=px)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


FONT = load_font()


def ratio(w, h):
    if not w or not h:
        return '?'
    r = w / h
    for name, v in [('9:16', 9 / 16), ('2:3', 2 / 3), ('4:5', 4 / 5), ('3:4', 3 / 4), ('1:1', 1), ('4:3', 4 / 3),
                    ('16:9', 16 / 9), ('3:2', 3 / 2)]:
        if abs(r - v) < 0.03:
            return name
    return f'{r:.2f}'


def tile(path, label, w=TW, h=TH):
    t = Image.new('RGB', (w, h + 30), 'white')
    try:
        im = Image.open(path).convert('RGB')
        im.thumbnail((w - 8, h - 8))
        t.paste(im, ((w - im.width) // 2, 30 + (h - im.height) // 2))
    except Exception:  # noqa: BLE001 - missing/unreadable file: leave the tile blank but labeled
        label += '  (missing)'
    ImageDraw.Draw(t).text((6, 4), label, fill='black', font=FONT)
    return t


def kind(p):
    if p.get('video'):
        ms = p['video'].get('ms') or 0
        return f'VIDEO {round(ms / 1000)}s' if ms else 'VIDEO'
    if p.get('carousel'):
        return f'CAROUSEL x{len(p["carousel"])}'
    return 'img'


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    work, only = sys.argv[1], set(sys.argv[2:])
    out = os.path.join(work, 'sheets')
    os.makedirs(out, exist_ok=True)
    written = []
    for f in sorted(glob.glob(os.path.join(work, 'data', '*.json'))):
        d = json.load(open(f))
        slug = d['slug']
        if only and slug not in only:
            continue
        media = os.path.join(work, 'media', slug)
        pins = d['pins']
        for i, p in enumerate(pins, 1):
            p.setdefault('n', i)
        for s in range(0, len(pins), PER):
            chunk = pins[s:s + PER]
            rows = (len(chunk) + COLS - 1) // COLS
            sheet = Image.new('RGB', (COLS * TW, rows * (TH + 30)), 'white')
            for i, p in enumerate(chunk):
                src = (sorted(glob.glob(os.path.join(media, f'{p["n"]:03d}.*'))) or [''])[0]
                label = f'#{p["n"]}  {ratio(p["img"].get("w"), p["img"].get("h"))}  {kind(p)}'
                sheet.paste(tile(src, label), ((i % COLS) * TW, (i // COLS) * (TH + 30)))
            name = os.path.join(out, f'{slug}-{s // PER + 1}.jpg')
            sheet.save(name, quality=82)
            written.append(name)
        for p in pins:
            if not (p.get('carousel') or p.get('video')):
                continue
            files = (sorted(glob.glob(os.path.join(media, f'{p["n"]:03d}-c*')), key=lambda x: int(x.rsplit('-c', 1)[1].split('.')[0]))
                     or sorted(glob.glob(os.path.join(media, f'{p["n"]:03d}-v*.jpg')), key=lambda x: int(x.rsplit('-v', 1)[1].split('.')[0])))
            if not files:
                continue
            files = files[:10]
            tw, th = 300, 375
            strip = Image.new('RGB', (min(len(files), 5) * tw, ((len(files) + 4) // 5) * (th + 30)), 'white')
            for i, fp in enumerate(files):
                strip.paste(tile(fp, f'#{p["n"]}.{i + 1}', tw, th), ((i % 5) * tw, (i // 5) * (th + 30)))
            name = os.path.join(out, f'{slug}-x{p["n"]:03d}.jpg')
            strip.save(name, quality=82)
            written.append(name)
    print(f'{len(written)} sheets in {out}')
    for w in written:
        print(' ', os.path.basename(w))


if __name__ == '__main__':
    main()
