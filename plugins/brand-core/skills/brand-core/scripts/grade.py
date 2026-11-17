"""Per-source color grade in CIELAB, a k-means palette per source, and saturation outliers.

Usage:
    python3 -I grade.py <work> [slug ...] [--k 10]

Reads <work>/media/<slug>/NNN.<ext> (one cover image per item; carousel slots and video frames are
not double counted) and writes <work>/grade.json, printing a summary per source.

Per source:
    n                    items measured
    L_mean               mean L* (0 dark - 100 light)
    L_sd                 mean within-image L* standard deviation (tonal contrast)
    chroma               mean C* (0 = grey; most photos 5-20)
    a_mean, b_mean       mean a* (green - / red +) and b* (blue - / yellow +; b* is "warmth")
    warm_share_pct       share of items with mean b* > +5
    low_chroma_share_pct share of items with mean C* < 12 ("muted")
    palette              10 k-means centers on 400 sampled pixels per item, with share %, computed
                         WITHOUT the saturation outliers
    outliers             items whose p90 chroma is >= 2x the source median: usually pinned for a
                         layout or a graphic, not for color. Listed so you can say why they were left out.
Per item (in items[]): n, file, L, L_sd, C, C_p90, a, b.

Requirements: Python 3.9+, Pillow, numpy. colorlab.py must sit next to this file.
"""
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True  # keep the skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from colorlab import chroma, hex_of, kmeans, self_test, srgb_to_lab  # noqa: E402

COVER = re.compile(r'^(\d{3})\.(jpe?g|png|webp|gif)$', re.I)


def main():
    args = sys.argv[1:]
    k = 10
    if '--k' in args:
        i = args.index('--k')
        k = int(args[i + 1])
        del args[i:i + 2]
    if not args:
        sys.exit(__doc__)
    work, only = args[0], set(args[1:])
    self_test()

    res = {}
    for d in sorted(glob.glob(os.path.join(work, 'media', '*'))):
        slug = os.path.basename(d)
        if not os.path.isdir(d) or (only and slug not in only):
            continue
        files = sorted(f for f in os.listdir(d) if COVER.match(f))
        items, pix = [], []
        for f in files:
            try:
                im = Image.open(os.path.join(d, f)).convert('RGB')
            except Exception:  # noqa: BLE001
                continue
            im.thumbnail((160, 160))
            a = np.asarray(im).reshape(-1, 3).astype(np.float64)
            lab = srgb_to_lab(a)
            c = chroma(lab)
            items.append({'n': int(COVER.match(f).group(1)), 'file': f, 'L': round(float(lab[:, 0].mean()), 1),
                          'L_sd': round(float(lab[:, 0].std()), 1), 'C': round(float(c.mean()), 1),
                          'C_p90': round(float(np.percentile(c, 90)), 1), 'a': round(float(lab[:, 1].mean()), 1),
                          'b': round(float(lab[:, 2].mean()), 1)})
            pix.append(a[np.random.default_rng(1).choice(len(a), min(400, len(a)), replace=False)])
        if not items:
            continue
        s = {key: np.array([it[key] for it in items]) for key in ('L', 'L_sd', 'C', 'C_p90', 'a', 'b')}
        med90 = float(np.median(s['C_p90']))
        outliers = [{'n': it['n'], 'C_p90': it['C_p90'], 'x_median': round(it['C_p90'] / med90, 1)}
                    for it in items if med90 > 0 and it['C_p90'] >= 2 * med90]
        out_n = {o['n'] for o in outliers}
        keep = [px for it, px in zip(items, pix) if it['n'] not in out_n] or pix
        cen, cnt = kmeans(np.concatenate(keep), k)
        order = np.argsort(-cnt)
        res[slug] = {
            'n': len(items),
            'L_mean': round(float(s['L'].mean()), 1),
            'L_sd': round(float(s['L_sd'].mean()), 1),
            'chroma': round(float(s['C'].mean()), 1),
            'a_mean': round(float(s['a'].mean()), 1),
            'b_mean': round(float(s['b'].mean()), 1),
            'warm_share_pct': int(round(float((s['b'] > 5).mean() * 100))),
            'low_chroma_share_pct': int(round(float((s['C'] < 12).mean() * 100))),
            'C_p90_median': round(med90, 1),
            'palette': [[hex_of(cen[i]), round(100 * float(cnt[i]) / float(cnt.sum()), 1)] for i in order],
            'outliers': outliers,
            'items': items,
        }

    with open(os.path.join(work, 'grade.json'), 'w') as fh:
        json.dump(res, fh, indent=1)
    for slug, v in res.items():
        print(f'{slug}: n {v["n"]} | L* {v["L_mean"]} (sd {v["L_sd"]}) | C* {v["chroma"]} | a* {v["a_mean"]} | '
              f'b* {v["b_mean"]:+} ({v["warm_share_pct"]}% warm) | {v["low_chroma_share_pct"]}% muted')
        print('   palette ', ' '.join(f'{h}({p})' for h, p in v['palette']), '(outliers excluded)' if v['outliers'] else '')
        if v['outliers']:
            print('   saturation outliers (C* p90 >= 2x median %.1f): ' % v['C_p90_median']
                  + ', '.join(f'#{o["n"]} ({o["x_median"]}x)' for o in v['outliers']))
    print('wrote', os.path.join(work, 'grade.json'))


if __name__ == '__main__':
    main()
