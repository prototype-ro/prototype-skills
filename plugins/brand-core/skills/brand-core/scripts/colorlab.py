"""Shared color math for grade.py and measure.py: sRGB -> CIELAB (D65), chunked k-means, WCAG contrast.

Why everything is chunked: a macOS numpy build returned garbage (no error, plausible-looking numbers)
for vectorized math on arrays above ~20k rows, both 2D matmul and chains of 1D ops. Conversion runs in
chunks of <= 8000 rows and k-means distances in chunks of <= 2000 rows, and self_test() checks known
colors on a large array before any number is trusted. Call self_test() at the start of every script.
"""
import numpy as np

LAB_CHUNK = 8000
KM_CHUNK = 2000


def _lab(rgb):
    lin = []
    for k in range(3):  # per-channel 1D math, no matmul
        c = np.ascontiguousarray(rgb[:, k], dtype=np.float64) / 255.0
        lin.append(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))
    r, g, b = lin
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    fx, fy, fz = [np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16 / 116) for t in (x, y, z)]
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], 1)


def srgb_to_lab(rgb):
    """rgb: (N, 3) array of 0-255 values -> (N, 3) array of L*, a*, b*."""
    rgb = np.asarray(rgb, dtype=np.float64).reshape(-1, 3)
    if len(rgb) <= LAB_CHUNK:
        return _lab(rgb)
    return np.concatenate([_lab(rgb[i:i + LAB_CHUNK]) for i in range(0, len(rgb), LAB_CHUNK)])


def chroma(lab):
    return np.hypot(lab[:, 1], lab[:, 2])


def hue_deg(lab):
    return np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) % 360


def kmeans(x, k, it=25, seed=0):
    """Plain k-means on (N, D) rows; distances computed in chunks. Returns (centers, counts)."""
    x = np.asarray(x, dtype=np.float64)
    k = min(k, len(x))
    rng = np.random.default_rng(seed)
    cen = x[rng.choice(len(x), k, replace=False)]
    lab = np.zeros(len(x), dtype=int)
    for _ in range(it):
        lab = np.concatenate([((x[i:i + KM_CHUNK, None, :] - cen[None]) ** 2).sum(-1).argmin(1)
                              for i in range(0, len(x), KM_CHUNK)])
        cen = np.array([x[lab == i].mean(0) if (lab == i).any() else cen[i] for i in range(k)])
    return cen, np.bincount(lab, minlength=k)


def hex_of(rgb):
    return '#%02X%02X%02X' % tuple(int(round(min(255, max(0, v)))) for v in rgb)


def rgb_of(hexstr):
    h = hexstr.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rel_lum(hexstr):
    c = [v / 255 for v in rgb_of(hexstr)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(fg, bg):
    a, b = rel_lum(fg), rel_lum(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def delta_e76(lab1, lab2):
    return float(np.linalg.norm(np.asarray(lab1, dtype=np.float64) - np.asarray(lab2, dtype=np.float64)))


def self_test():
    """Abort loudly if this numpy build gives wrong answers on large arrays."""
    known = np.array([[255, 255, 255], [0, 0, 0], [255, 0, 0], [119, 119, 119]], dtype=np.float64)
    want = np.array([[100.0, 0.0, 0.0], [0.0, 0.0, 0.0], [53.24, 80.09, 67.20], [50.03, 0.0, 0.0]])
    big = np.repeat(known, 12000, axis=0)  # 48k rows: the size that broke before
    got = srgb_to_lab(big)
    for i in range(len(known)):
        rows = got[i * 12000:(i + 1) * 12000]
        if not np.allclose(rows, want[i], atol=0.6):
            bad = rows[np.abs(rows - want[i]).max(1).argmax()]
            raise SystemExit(f'colorlab self-test FAILED for rgb{tuple(int(v) for v in known[i])}: got {bad.round(2)}, '
                             f'want {want[i]}. Do not trust any number from this numpy build; lower LAB_CHUNK or '
                             f'reinstall numpy.')
    pts = np.concatenate([np.full((3000, 3), 10.0), np.full((3000, 3), 240.0)])
    cen, cnt = kmeans(pts, 2, it=5)
    if sorted(np.round(cen[:, 0]).tolist()) != [10.0, 240.0] or sorted(cnt.tolist()) != [3000, 3000]:
        raise SystemExit(f'colorlab self-test FAILED for k-means: centers {cen[:, 0]}, counts {cnt}')
    if abs(contrast('#FFFFFF', '#000000') - 21) > 0.01:
        raise SystemExit('colorlab self-test FAILED for WCAG contrast')
    return True


if __name__ == '__main__':
    self_test()
    print('colorlab self-test ok: white L*100, black L*0, red L*53.2, k-means and contrast correct on 48k rows')
