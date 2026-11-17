"""Build the brand-core page: fill the template from content.json, generate the published-piece
carousels and the reference -> slide trace pairs, and inline every image as a JPEG data URI.

Usage:
    python3 -I build_page.py <content.json> <out.html> [--template PATH] [--standalone] [--strict]

    --template    defaults to ../assets/brand-core.tpl.html next to this script. Copy it next to
                  content.json and edit the copy; pass the copy here.
    --standalone  wrap the result in <!doctype html><html><head>...<body> for a local file. Leave it
                  off for a claude.ai Artifact (the host adds the document skeleton).
    --strict      exit 1 if any [[...]] text slot, unresolved @@marker@@ or missing image is left.
                  Always build with --strict before publishing.

Markers in the template:
    @@TITLE@@ @@BRAND@@ @@POSTS@@ @@PAIRS@@ @@DATA@@    generated from content.json
    @@<source>/<name>@@                                  image: first file <dir>/<name>.* of that source
    @@RATIO:<source>/<name>@@                            "W / H" of that image (for aspect-ratio)
    [[...]]                                              hand-written text slot
HTML comments are stripped from the output.

content.json (paths relative to the file; see assets/content.example.json):
    title, brand, lang, storage_key
    quality (68), default_box ([460, 740])
    sources: { key: { dir | file, box?: [w, h], label? } }   "made" = the brand's own published slides
    slide_name: "p{post}-{slide}"   how a published slide is named inside sources.made.dir
    posts:  [{ id, hook, series, tags[], slides: [{ role, note, flag?, alt? }] }]
    pairs:  [{ ref: "<source>/<name>", post, slide, ref_alt?, caption? }]
    palettes: [{ id, title, note, items: [[name, hex, sub?]] }]    declared / used / referenced
    ramps:    [[name, [hex, hex, hex, hex, hex]]]
    contrast_default: [fg_hex, bg_hex]
    decisions: [{ id, q, ctx, unblocks?, opts: [{ k, t, x, rec?, dot? }] }]

Size: board refs at ~460 px and slides at ~540 px, quality ~68, the guideline sheet at ~2000 px keep a
page with ~100 images under ~9 MB. Artifacts are capped at 16 MB.

Requirements: Python 3.9+, Pillow.
"""
import base64
import glob
import html
import io
import json
import os
import re
import sys

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape
IMG_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
PLACEHOLDER = 'data:image/gif;base64,R0lGODlhAQABAIAAAMzMzAAAACwAAAAAAQABAAACAkQBADs='


def opt(args, name):
    if name in args:
        args.remove(name)
        return True
    return False


def opt_val(args, name, default=None):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


def main():
    args = sys.argv[1:]
    standalone, strict = opt(args, '--standalone'), opt(args, '--strict')
    tpl_path = opt_val(args, '--template', os.path.join(HERE, '..', 'assets', 'brand-core.tpl.html'))
    if len(args) != 2:
        sys.exit(__doc__)
    content_path, out_path = args
    base = os.path.dirname(os.path.abspath(content_path))
    C = json.load(open(content_path, encoding='utf-8'))
    tpl = open(tpl_path, encoding='utf-8').read()
    tpl = re.sub(r'<!--[\s\S]*?-->\n?', '', tpl)

    sources = C.get('sources', {})
    labels = {k: v.get('label', k) for k, v in sources.items()}
    slide_name = C.get('slide_name', 'p{post}-{slide}')

    # ---- published pieces: swipeable carousels ----
    posts_html = []
    for post in C.get('posts', []):
        pid, slides = str(post['id']), post.get('slides', [])
        s = [f'<article class="post"><div class="post-head"><div class="meta"><span><b>{E(post.get("label", "piece " + pid))}</b></span>'
             f'<span>{len(slides)} slides</span><span>{E(post.get("series", ""))}</span></div>',
             f'<p class="hook">{E(post.get("hook", ""))}</p><div class="tags">'
             + ''.join(f'<span class="tag">{E(t)}</span>' for t in post.get('tags', [])) + '</div></div>',
             f'<div class="track" tabindex="0" aria-label="{E(post.get("label", "Piece " + pid))} slides">']
        for i, sl in enumerate(slides, 1):
            key = sl.get('img') or 'made/' + slide_name.format(post=pid, slide=i)
            alt = sl.get('alt') or f'{post.get("label", "Piece " + pid)} slide {i}: {sl.get("role", "")}'
            flag = f'<span class="flag">{E(sl["flag"])}</span>' if sl.get('flag') else ''
            s.append(f'<figure class="slide"><button class="ph" aria-label="Enlarge {E(post.get("label", "piece " + pid))} slide {i}">'
                     f'<img src="@@{key}@@" alt="{E(alt)}"></button>'
                     f'<figcaption><span class="role">{i} · {E(sl.get("role", ""))}</span><span>{E(sl.get("note", ""))}</span>{flag}</figcaption></figure>')
        s.append('</div><div class="track-ctl"><button class="iconbtn" type="button" data-dir="-1" aria-label="Previous slide">←</button>'
                 '<button class="iconbtn" type="button" data-dir="1" aria-label="Next slide">→</button><span class="count"></span></div></article>')
        posts_html.append(''.join(s))

    # ---- reference -> slide trace pairs ----
    pairs_html = []
    for p in C.get('pairs', []):
        src, name = p['ref'].split('/', 1)
        num = name.split('-')[0].lstrip('0') or name
        pid, i = str(p['post']), int(p['slide'])
        post = next((x for x in C.get('posts', []) if str(x['id']) == pid), {})
        plabel = post.get('label', 'piece ' + pid)
        slide_key = 'made/' + slide_name.format(post=pid, slide=i)
        ref_alt = p.get('ref_alt') or f'{labels.get(src, src)} #{num}'
        cap = p.get('caption') or f'{labels.get(src, src)} #{num} → {plabel} · slide {i}'
        pairs_html.append(f'<figure class="pair"><button class="ph" aria-label="Enlarge {E(labels.get(src, src))} #{E(num)}"><img src="@@{p["ref"]}@@" alt="{E(ref_alt)}"></button>'
                          f'<span class="arrow">→</span><button class="ph" aria-label="Enlarge {E(plabel)} slide {i}"><img src="@@{slide_key}@@" alt="{E(plabel)} slide {i}"></button>'
                          f'<figcaption>{E(cap)}</figcaption></figure>')

    data = {k: C[k] for k in ('palettes', 'ramps', 'contrast_default', 'decisions', 'storage_key') if k in C}
    data['source_labels'] = labels
    data_json = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')

    out = (tpl.replace('@@TITLE@@', E(C.get('title', 'Brand Core')))
              .replace('@@BRAND@@', E(C.get('brand', '')))
              .replace('@@POSTS@@', '\n'.join(posts_html))
              .replace('@@PAIRS@@', '\n'.join(pairs_html))
              .replace('@@DATA@@', data_json))

    # ---- images ----
    marker = re.compile(r'@@(RATIO:)?([a-z0-9_-]+)/([A-Za-z0-9_.-]+)@@')
    cache, sizes, missing = {}, {}, []

    def resolve(src, name):
        cfg = sources.get(src)
        if not cfg:
            return None
        if cfg.get('file'):
            f = os.path.join(base, cfg['file'])
            return f if os.path.exists(f) else None
        d = os.path.join(base, cfg['dir'])
        exact = os.path.join(d, name)
        if os.path.splitext(name)[1].lower() in IMG_EXT and os.path.exists(exact):
            return exact
        hits = sorted(f for f in glob.glob(os.path.join(glob.escape(d), glob.escape(name) + '.*')) if f.lower().endswith(IMG_EXT))
        return hits[0] if hits else None

    def inline(m):
        is_ratio, src, name = m.group(1), m.group(2), m.group(3)
        key = f'{src}/{name}'
        if key not in cache:
            f = resolve(src, name)
            if not f:
                missing.append(key)
                cache[key] = None
            else:
                im = Image.open(f)
                sizes[key] = im.size
                im = im.convert('RGB')
                im.thumbnail(tuple(sources[src].get('box') or C.get('default_box') or (460, 740)))
                buf = io.BytesIO()
                im.save(buf, 'JPEG', quality=int(C.get('quality', 68)), optimize=True, progressive=True)
                cache[key] = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
        if is_ratio:
            w, h = sizes.get(key, (1, 1))
            return f'{w} / {h}'
        return cache[key] or PLACEHOLDER

    out = marker.sub(inline, out)
    leftover = re.findall(r'@@[^@\s"]{1,60}@@', out)
    out = re.sub(r'(src=")@@[^"]*@@(")', r'\1' + PLACEHOLDER + r'\2', out)
    # text slots: scan the markup only (JSON data and JS legitimately contain "[[")
    scan = re.sub(r'<(script|style)[\s\S]*?</\1>', lambda m: '\n' * m.group(0).count('\n'), out)
    slots = [(scan[:m.start()].count('\n') + 1, m.group(0)[:70]) for m in re.finditer(r'\[\[[^\]]*\]\]', scan)]

    if standalone:
        cut = out.index('</style>') + len('</style>')
        out = (f'<!doctype html>\n<html lang="{E(C.get("lang", "en"))}">\n<head>\n<meta charset="utf-8">\n'
               '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
               + out[:cut] + '\n</head>\n<body>\n' + out[cut:] + '\n</body>\n</html>\n')
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(out)

    mb = len(out.encode('utf-8')) / 1e6
    print(f'wrote {out_path}: {mb:.2f} MB, {len([v for v in cache.values() if v])} images, '
          f'{len(posts_html)} pieces, {len(pairs_html)} pairs')
    problems = 0
    if missing:
        problems += 1
        print(f'MISSING images ({len(missing)}):', ', '.join(sorted(set(missing))[:20]))
    if leftover:
        problems += 1
        print(f'UNRESOLVED markers ({len(leftover)}):', ', '.join(sorted(set(leftover))[:10]))
    if slots:
        problems += 1
        print(f'UNFILLED [[slots]] ({len(slots)}), first ones:')
        for ln, s in slots[:12]:
            print(f'  line {ln}: {s}')
    if mb > 16:
        problems += 1
        print('TOO BIG: over the 16 MB artifact cap. Lower quality or the boxes, or cut images.')
    elif mb > 9:
        print('warning: over ~9 MB; consider smaller boxes or fewer images')
    if strict and problems:
        sys.exit(1)


if __name__ == '__main__':
    main()
