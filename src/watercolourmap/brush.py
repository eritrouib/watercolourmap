"""The watercolour engine: turns a raster of class ids into a painted RGB image."""
import numpy as np
from scipy import ndimage as ndi

PAPER = np.array([0.985, 0.972, 0.925], np.float32)
EMPTY = 255  # class id for "no data": stays bare paper


def fbm(shape, rng, scales=(160, 60, 22, 8), weights=(0.45, 0.3, 0.17, 0.08)):
    """Smooth multi-octave noise in [0, 1], made at low resolution and upsampled."""
    h, w = shape
    out = np.zeros(shape, np.float32)
    for s, wt in zip(scales, weights):
        lh, lw = max(2, h // s + 2), max(2, w // s + 2)
        n = rng.standard_normal((lh, lw)).astype(np.float32)
        n = ndi.zoom(n, (h / lh * 1.0001, w / lw * 1.0001), order=3)[:h, :w]
        out += wt * n
    out -= out.min()
    out /= max(out.max(), 1e-6)
    return out


def paint(classes, colours, pixel_size=2.5, seed=7, paper=PAPER):
    """Paint a class raster as watercolour.

    classes     2-D integer array of class ids (EMPTY = bare paper)
    colours     {class_id: (r, g, b)} with values 0-1
    pixel_size  ground size of a pixel in metres; effects are scaled to it so
                the brush looks the same at any resolution
    Returns an (h, w, 3) float array in 0-1.
    """
    rng = np.random.default_rng(seed)
    h, w = classes.shape
    k = max(1.0, 2.5 / pixel_size)

    # paper with a faint fibre texture
    fibre = fbm((h, w), rng, scales=(40, 6, 2), weights=(0.3, 0.4, 0.3))
    img = np.empty((h, w, 3), np.float32)
    img[:] = paper
    img *= (0.985 + 0.03 * fibre)[..., None]

    # one shared wobble field, so neighbouring washes keep their gaps consistent
    dx = (fbm((h, w), rng, scales=(90, 30)) - 0.5) * 6 * k
    dy = (fbm((h, w), rng, scales=(90, 30)) - 0.5) * 6 * k
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    coords = np.array([yy + dy, xx + dx])
    del yy, xx

    for cid, col in colours.items():
        m = (classes == cid).astype(np.float32)
        if not m.any():
            continue
        m = ndi.map_coordinates(m, coords, order=1, mode="nearest")   # hand-drawn edge
        m = ndi.gaussian_filter(m, 0.9 * k)
        m = np.clip((m - 0.35) / 0.4, 0, 1)        # slight shrink: bare paper between parcels
        edge = np.clip(m - ndi.gaussian_filter(m, 3.0 * k), 0, 1)   # pigment pooling at edges
        wash = fbm((h, w), rng, scales=(220, 70, 18))                # uneven wash
        gran = fbm((h, w), rng, scales=(5, 2), weights=(0.6, 0.4))  # granulation
        alpha = np.clip(m * (0.50 + 0.38 * wash) * (0.88 + 0.24 * gran) + 1.6 * edge, 0, 0.97)
        colv = np.asarray(col, np.float32)
        img *= 1 - alpha[..., None] * (1 - colv)    # multiply glaze, like pigment on paper
    return np.clip(img, 0, 1)


def swatch(colour, seed=1, size=(40, 110)):
    """A small painted rectangle in one colour, for legends."""
    c = np.full(size, EMPTY, np.uint8)
    c[6:size[0] - 6, 6:size[1] - 6] = 1
    return paint(c, {1: colour}, pixel_size=2.0, seed=seed)


def deckle(img, pixel_size, seed=3, paper=PAPER):
    """Fade the outer edge of a rectangular painting into a torn, hand-painted edge."""
    h, w = img.shape[:2]
    rng = np.random.default_rng(seed)
    d = np.minimum.outer(np.minimum(np.arange(h), np.arange(h)[::-1]),
                         np.minimum(np.arange(w), np.arange(w)[::-1])).astype(np.float32)
    k = max(1.0, 2.5 / pixel_size)
    n = fbm((h, w), rng, scales=(120, 35, 10), weights=(0.5, 0.35, 0.15))
    fe = np.clip((d - 28 * k * n) / (5 * k), 0, 1)[..., None]
    return paper + (img - paper) * fe


def fade_paper(img, classes, paper=PAPER):
    """Fade the paper fibre out towards the frame where there is no paint."""
    h, w = classes.shape
    ramp = max(1, int(max(h, w) * 0.03))
    fy = np.clip(np.minimum(np.arange(h), np.arange(h)[::-1]) / ramp, 0, 1)
    fx = np.clip(np.minimum(np.arange(w), np.arange(w)[::-1]) / ramp, 0, 1)
    f = np.minimum.outer(fy, fx)[..., None]
    outside = (classes == EMPTY)[..., None]
    return np.where(outside, paper + (img - paper) * f, img)
