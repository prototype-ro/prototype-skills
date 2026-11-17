"""Import a local folder (references or the brand's own published pieces) into the same layout the
Pinterest scraper produces, so contact_sheets.py and grade.py treat every source the same way.

Usage:
    python3 import_local.py <folder> <work> <slug> [--dpi 72]

What becomes an item (numbered 001, 002, ... in natural sort order):
    image file  (.jpg .jpeg .png .webp .gif .tif .tiff .bmp .heic)  -> single item
    video file  (.mp4 .mov .m4v .webm)                               -> video item: cover + frames every 2 s (max 6)
    PDF file                                                         -> carousel item: one slot per page
    sub-folder of images (e.g. one folder per published carousel)    -> carousel item: one slot per image

Writes <work>/media/<slug>/NNN.<ext> (+ NNN-cK.jpg slots, NNN-vK.jpg frames) and <work>/data/<slug>.json.
Prefer the designer's per-slide PNG exports over PDFs when both exist: they are sharper and keep color.

Requirements: Python 3.9+, Pillow; ffmpeg/ffprobe for videos; poppler (pdfinfo, pdftoppm) for PDFs;
macOS `sips` for HEIC.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

from PIL import Image

IMG = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
CONVERT = {'.tif', '.tiff', '.bmp', '.heic'}
VID = {'.mp4', '.mov', '.m4v', '.webm'}


def natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def size(path):
    try:
        with Image.open(path) as im:
            return im.width, im.height
    except Exception:  # noqa: BLE001
        return None, None


def put_image(src, dest_noext):
    """Copy (or convert to PNG) an image; return the written path or None."""
    ext = os.path.splitext(src)[1].lower()
    if ext in IMG:
        dest = dest_noext + ('.jpg' if ext == '.jpeg' else ext)
        shutil.copyfile(src, dest)
        return dest
    dest = dest_noext + '.png'
    if ext == '.heic':
        if shutil.which('sips') is None:
            print('skip HEIC (needs macOS sips):', src)
            return None
        subprocess.run(['sips', '-s', 'format', 'png', src, '--out', dest], capture_output=True, check=False)
        return dest if os.path.exists(dest) else None
    Image.open(src).convert('RGB').save(dest)
    return dest


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration',
                          '-of', 'json', path], capture_output=True, text=True, check=False).stdout
    j = json.loads(out or '{}')
    st = (j.get('streams') or [{}])[0]
    return st.get('width'), st.get('height'), round(float((j.get('format') or {}).get('duration') or 0) * 1000)


def main():
    args = sys.argv[1:]
    dpi = 72
    if '--dpi' in args:
        i = args.index('--dpi')
        dpi = int(args[i + 1])
        del args[i:i + 2]
    if len(args) != 3:
        sys.exit(__doc__)
    folder, work, slug = args
    out = os.path.join(work, 'media', slug)
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(work, 'data'), exist_ok=True)

    entries = sorted((e for e in os.listdir(folder) if not e.startswith('.')), key=natural)
    pins, n = [], 0
    for name in entries:
        src = os.path.join(folder, name)
        ext = os.path.splitext(name)[1].lower()
        item = {'id': name, 'title': os.path.splitext(name)[0], 'description': '', 'link': None, 'domain': None,
                'dominant_color': None, 'section': None, 'video': None, 'carousel': [], 'story_pages': 0}
        if os.path.isdir(src):
            slides = sorted((f for f in os.listdir(src) if os.path.splitext(f)[1].lower() in IMG | CONVERT), key=natural)
            if not slides:
                continue
            n += 1
            key = os.path.join(out, f'{n:03d}')
            for k, f in enumerate(slides, 1):
                p = put_image(os.path.join(src, f), f'{key}-c{k}')
                if p:
                    w, h = size(p)
                    item['carousel'].append({'file': p, 'name': f, 'w': w, 'h': h})
            first = item['carousel'][0]['file']
            cover = key + os.path.splitext(first)[1]
            shutil.copyfile(first, cover)
        elif ext == '.pdf':
            if shutil.which('pdftoppm') is None:
                print('skip PDF (needs poppler pdftoppm):', src)
                continue
            n += 1
            key = os.path.join(out, f'{n:03d}')
            info = subprocess.run(['pdfinfo', src], capture_output=True, text=True, check=False).stdout
            item['pdf'] = {k.strip(): v.strip() for k, v in (ln.split(':', 1) for ln in info.splitlines() if ':' in ln)
                           if k.strip() in ('Pages', 'Page size')}
            subprocess.run(['pdftoppm', '-r', str(dpi), '-jpeg', src, key + '-c'], check=False)
            # pdftoppm names pages key-c-1.jpg (or -01, -001 depending on page count): normalise to key-cK.jpg
            for f in glob.glob(key + '-c-*.jpg'):
                k = int(re.search(r'-c-(\d+)\.jpg$', f).group(1))
                os.replace(f, f'{key}-c{k}.jpg')
            slots = sorted(glob.glob(key + '-c*.jpg'), key=natural)
            for f in slots:
                w, h = size(f)
                item['carousel'].append({'file': f, 'w': w, 'h': h})
            if slots:
                shutil.copyfile(slots[0], key + '.jpg')
        elif ext in VID:
            if shutil.which('ffmpeg') is None:
                print('skip video (needs ffmpeg):', src)
                continue
            n += 1
            key = os.path.join(out, f'{n:03d}')
            w, h, ms = probe(src)
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '0.5', '-i', src, '-frames:v', '1',
                            '-vf', 'scale=1080:-2:force_original_aspect_ratio=decrease', key + '.jpg'], check=False)
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-vf', 'fps=1/2,scale=360:-2',
                            '-frames:v', '6', key + '-v%d.jpg'], check=False)
            item['video'] = {'file': src, 'w': w, 'h': h, 'ms': ms}
        elif ext in IMG | CONVERT:
            n += 1
            key = os.path.join(out, f'{n:03d}')
            if not put_image(src, key):
                n -= 1
                continue
        else:
            continue
        cover = (glob.glob(os.path.join(out, f'{n:03d}.*')) or [None])[0]
        w, h = size(cover) if cover else (None, None)
        if item['video']:
            w, h = item['video']['w'] or w, item['video']['h'] or h
        item.update({'n': n, 'img': {'url': None, 'file': cover, 'w': w, 'h': h}})
        pins.append(item)

    manifest = {'url': None, 'slug': slug, 'local_dir': os.path.abspath(folder), 'board': {'name': slug, 'pin_count': len(pins)},
                'sections': [], 'count': len(pins), 'pins': pins}
    json.dump(manifest, open(os.path.join(work, 'data', f'{slug}.json'), 'w'), indent=2)
    kinds = {'carousel': sum(1 for p in pins if p['carousel']), 'video': sum(1 for p in pins if p['video'])}
    print(f'{slug}: {len(pins)} items ({len(pins) - kinds["carousel"] - kinds["video"]} static, {kinds["carousel"]} carousel, {kinds["video"]} video)')


if __name__ == '__main__':
    main()
