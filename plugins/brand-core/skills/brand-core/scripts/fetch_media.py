"""Download the media behind every scraped board manifest.

Usage:
    python3 fetch_media.py <work> [slug ...]

Reads <work>/data/<slug>.json (written by scrape_pinterest.mjs) and writes <work>/media/<slug>/:
    NNN.<ext>        the original image of item NNN (cover image for videos)
    NNN-cK.<ext>     carousel slot K
    NNN-vK.jpg       video frames: one every 2 s, at most 6, 360 px wide (ffmpeg)
    .ids.json        which pin id each NNN belongs to

Board order changes between scrapes. If a NNN already on disk belongs to a different pin id than the
current manifest says, its files are deleted and downloaded again, so numbers on contact sheets always
match the current manifest.

Requirements: Python 3.9+, ffmpeg on PATH (only for video frames).
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131 Safari/537.36'}


def ext_of(url, default='.jpg'):
    e = os.path.splitext((url or '').split('?')[0])[1].lower()
    return e if e in ('.jpg', '.jpeg', '.png', '.gif', '.webp') else default


def dl(job):
    url, dest = job
    if not url or os.path.exists(dest):
        return dest
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r, open(dest + '.part', 'wb') as f:
            shutil.copyfileobj(r, f)
        os.replace(dest + '.part', dest)
    except Exception as e:  # noqa: BLE001 - report and continue
        print('fail', url, e)
        return None
    return dest


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    work = sys.argv[1]
    only = set(sys.argv[2:])
    if shutil.which('ffmpeg') is None:
        print('warning: ffmpeg not found, video frames will be skipped')

    manifests = [f for f in sorted(glob.glob(os.path.join(work, 'data', '*.json')))
                 if not only or os.path.splitext(os.path.basename(f))[0] in only]
    jobs, videos = [], []
    for f in manifests:
        d = json.load(open(f))
        if d.get('local_dir'):
            continue  # imported with import_local.py, media already in place
        out = os.path.join(work, 'media', d['slug'])
        os.makedirs(out, exist_ok=True)
        ids_path = os.path.join(out, '.ids.json')
        prior = json.load(open(ids_path)) if os.path.exists(ids_path) else {}
        ids = {}
        for i, p in enumerate(d['pins'], 1):
            n = p.setdefault('n', i)
            key = f'{n:03d}'
            ids[key] = p['id']
            if key in prior and prior[key] != p['id']:
                for old in glob.glob(os.path.join(out, key + '.*')) + glob.glob(os.path.join(out, key + '-*')):
                    os.remove(old)
            jobs.append((p['img']['url'], os.path.join(out, key + ext_of(p['img']['url']))))
            for k, c in enumerate(p.get('carousel') or [], 1):
                if c.get('url'):
                    jobs.append((c['url'], os.path.join(out, f'{key}-c{k}{ext_of(c["url"])}')))
            v = p.get('video')
            if v and v.get('url'):
                v['frames'] = os.path.join(out, f'{key}-v%d.jpg')
                videos.append((d['slug'], n, v))
        json.dump(ids, open(ids_path, 'w'), indent=1)
        json.dump(d, open(f, 'w'), indent=2)

    with ThreadPoolExecutor(12) as ex:
        ok = sum(1 for r in ex.map(dl, jobs) if r)
    print(f'images: {ok}/{len(jobs)} on disk')

    if shutil.which('ffmpeg') is None:
        return
    for slug, n, v in videos:
        pat = v['frames']
        if os.path.exists(pat % 1):
            continue
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', v['url'], '-vf', 'fps=1/2,scale=360:-2',
                        '-frames:v', '6', pat], timeout=180)
        print('video', slug, f'#{n}', f'{v.get("w")}x{v.get("h")}', f'{(v.get("ms") or 0) / 1000:.1f}s')


if __name__ == '__main__':
    main()
