"""Point measurements: guideline swatches vs their labels, accent colors, WCAG contrast.

Usage:
    python3 -I measure.py grid <image> <out.jpg> [--step 250]
        Downscaled copy with a labeled grid in ORIGINAL pixel units, so you can read swatch coordinates
        off a huge guideline sheet. Open out.jpg, then use the coordinates with `swatch`.

    python3 -I measure.py swatch <image> "<name>:x,y,w,h[=#LABEL]" [...]
        Median color of each box (original pixels) vs the hex written next to it. Prints dE76 and a
        verdict: ok (< 3), close (< 6), MISMATCH. Guideline sheets lie in their labels: sample the
        drawn swatch, never copy the label.

    python3 -I measure.py accent <image|dir> [...] [--hue 60-110] [--min-chroma 35] [--min-l 0] [--max-l 100]
        Without --hue: histogram of hues among saturated pixels, to find the accent's band.
        With --hue (degrees in CIELAB LCh, wraps: 340-20 is fine): the median matched pixel across all
        images (a real pixel, reported as hex), the share of matching pixels per image.

    python3 -I measure.py contrast "#FFFFFF:#5E8C8A" ["fg:bg" ...]
        WCAG 2.x ratio and passes: AA text >= 4.5, AA large (18 pt / 14 pt bold) >= 3, AAA >= 7.

Requirements: Python 3.9+, Pillow, numpy. colorlab.py must sit next to this file.
"""
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.dont_write_bytecode = True  # keep the skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from colorlab import chroma, contrast, delta_e76, hex_of, hue_deg, rgb_of, self_test, srgb_to_lab  # noqa: E402

IMG_RE = re.compile(r'\.(jpe?g|png|webp|gif)$', re.I)


def opt(args, name, default=None, cast=str):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return cast(v)
    return default


def expand(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(os.path.join(p, f) for f in os.listdir(p) if IMG_RE.search(f))
        else:
            out.append(p)
    return out


def cmd_grid(args):
    step = opt(args, '--step', 250, int)
    src, dest = args
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(src).convert('RGB')
    W, H = im.size
    view = im.copy()
    view.thumbnail((1600, 1600))
    s = view.width / W
    d = ImageDraw.Draw(view)
    for x in range(0, W, step):
        d.line([(x * s, 0), (x * s, view.height)], fill=(255, 0, 140), width=1)
        d.text((x * s + 2, 2), str(x), fill=(255, 0, 140))
    for y in range(0, H, step):
        d.line([(0, y * s), (view.width, y * s)], fill=(0, 150, 255), width=1)
        d.text((2, y * s + 2), str(y), fill=(0, 150, 255))
    view.save(dest, quality=85)
    print(f'{src}: {W}x{H} px; grid every {step} px drawn on a {view.width}x{view.height} copy -> {dest}')


def cmd_swatch(args):
    src, specs = args[0], args[1:]
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(src).convert('RGB')
    print(f'{src}: {im.width}x{im.height} px')
    for spec in specs:
        m = re.match(r'^(?:(.+?):)?(\d+),(\d+),(\d+),(\d+)(?:=(#?[0-9A-Fa-f]{3,6}))?$', spec)
        if not m:
            print('bad spec (want name:x,y,w,h=#HEX):', spec)
            continue
        name, x, y, w, h, label = m.group(1) or 'box', *map(int, m.group(2, 3, 4, 5)), m.group(6)
        a = np.asarray(im.crop((x, y, x + w, y + h))).reshape(-1, 3).astype(np.float64)
        med = np.median(a, 0)
        spread = float(np.abs(a - med).mean())
        line = f'  {name:<22} sampled {hex_of(med)}  (pixel spread {spread:.1f})'
        if label:
            de = delta_e76(srgb_to_lab(med[None])[0], srgb_to_lab(np.array([rgb_of(label)], dtype=np.float64))[0])
            verdict = 'ok' if de < 3 else 'close' if de < 6 else 'MISMATCH'
            line += f'  label {label.upper():<8} dE {de:5.1f}  {verdict}'
        if spread > 12:
            line += '  (box not flat: text, edge or gradient inside?)'
        print(line)


def cmd_accent(args):
    hue = opt(args, '--hue')
    min_c = opt(args, '--min-chroma', 35.0, float)
    min_l = opt(args, '--min-l', 0.0, float)
    max_l = opt(args, '--max-l', 100.0, float)
    files = expand(args)
    if not files:
        sys.exit('no images')
    all_rgb, all_lab, shares = [], [], []
    for f in files:
        try:
            im = Image.open(f).convert('RGB')
        except Exception:  # noqa: BLE001
            continue
        im.thumbnail((400, 400))
        rgb = np.asarray(im).reshape(-1, 3).astype(np.float64)
        lab = srgb_to_lab(rgb)
        c, hdeg = chroma(lab), hue_deg(lab)
        keep = (c >= min_c) & (lab[:, 0] >= min_l) & (lab[:, 0] <= max_l)
        if hue:
            lo, hi = (float(v) for v in hue.split('-'))
            keep &= ((hdeg >= lo) & (hdeg <= hi)) if lo <= hi else ((hdeg >= lo) | (hdeg <= hi))
        shares.append((os.path.join(os.path.basename(os.path.dirname(f)), os.path.basename(f)), 100 * keep.mean()))
        all_rgb.append(rgb[keep])
        all_lab.append(np.column_stack([lab[keep], hdeg[keep]]))
    rgb = np.concatenate(all_rgb)
    lab = np.concatenate(all_lab)
    if not len(rgb):
        sys.exit('no pixels matched; widen --hue or lower --min-chroma')
    if not hue:
        bins = np.bincount((lab[:, 3] // 20).astype(int), minlength=18)
        total = bins.sum()
        print(f'hue histogram of pixels with C* >= {min_c} across {len(shares)} images ({total} px):')
        for i in np.argsort(-bins)[:8]:
            if bins[i]:
                sel = (lab[:, 3] // 20).astype(int) == i
                print(f'  {i * 20:3d}-{i * 20 + 20:3d} deg  {100 * bins[i] / total:5.1f}%   median pixel {hex_of(np.median(rgb[sel], 0))}')
        print('re-run with --hue LO-HI (and --min-l/--max-l) to isolate one accent')
        return
    med = np.median(lab[:, :3], 0)
    nearest = rgb[np.argmin(((lab[:, :3] - med) ** 2).sum(1))]
    print(f'accent hue {hue}, C* >= {min_c}, L* {min_l}-{max_l}: {len(rgb)} px from {sum(1 for _, s in shares if s > 0)}/{len(shares)} images')
    print(f'  median pixel {hex_of(nearest)}  (L* {med[0]:.1f}, C* {np.hypot(med[1], med[2]):.1f})')
    for name, s in shares:
        if s >= 0.005:
            print(f'  {name:<36} {s:5.2f}% of pixels')


def cmd_contrast(args):
    for pair in args:
        fg, bg = pair.split(':')
        r = contrast(fg, bg)
        marks = [('AA text', r >= 4.5), ('AA large', r >= 3), ('AAA', r >= 7)]
        print(f'  {fg.upper()} on {bg.upper()}: {r:5.2f}:1  ' + '  '.join(f'{n} {"pass" if ok else "FAIL"}' for n, ok in marks))


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    self_test()
    {'grid': cmd_grid, 'swatch': cmd_swatch, 'accent': cmd_accent, 'contrast': cmd_contrast}.get(cmd, lambda a: sys.exit(__doc__))(args)


if __name__ == '__main__':
    main()
