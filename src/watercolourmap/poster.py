"""Painting GeoDataFrames and laying out print-ready posters."""
from pathlib import Path

import numpy as np
import geopandas as gpd
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely.geometry import Point
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm

from .brush import PAPER, EMPTY, paint, swatch, deckle, fade_paper

FONTS = Path(__file__).resolve().parent / "fonts"
PAPER_SIZES = {"A1": (594, 841), "A2": (420, 594), "A3": (297, 420), "A4": (210, 297)}
INK = (0.25, 0.25, 0.25)
MAX_PIXELS = 60_000_000   # roughly 5 GB of working memory while painting


def font(name="Lora-Italic-Variable.ttf"):
    return fm.FontProperties(fname=str(FONTS / name))


# ------------------------------------------------------------------ painting
def rasterise(gdf, column, bounds, pixel_size):
    """Burn polygons into a class raster. Larger polygons first, small ones on top."""
    minx, miny, maxx, maxy = bounds
    W = int(np.ceil((maxx - minx) / pixel_size))
    H = int(np.ceil((maxy - miny) / pixel_size))
    if W * H > MAX_PIXELS:
        raise ValueError(
            f"The map would be {W} x {H} pixels, too big to paint in memory. "
            "Clip the data to a smaller area or use a larger pixel_size / lower dpi. "
            "Is the data in a metric CRS (metres)?")
    order = gdf.assign(_a=gdf.area).sort_values("_a", ascending=False)
    return rasterize(((g, int(c)) for g, c in zip(order.geometry, order[column])),
                     out_shape=(H, W), transform=from_origin(minx, maxy, pixel_size, pixel_size),
                     fill=EMPTY, dtype="uint8")


def paint_gdf(gdf, column, colours, pixel_size=None, bounds=None, seed=7):
    """Paint any polygon GeoDataFrame as watercolour.

    gdf         polygons in a metric CRS (use gdf.to_crs(gdf.estimate_utm_crs()))
    column      column holding a category for each polygon
    colours     {category: (r, g, b)} (0-1 floats or '#rrggbb' strings)
    pixel_size  metres per pixel; default makes the longer side about 3000 px
    Returns (image, extent) ready for ax.imshow(image, extent=extent).
    """
    # any category type -> small integer ids for the raster
    cats = list(colours)
    ids = {c: i + 1 for i, c in enumerate(cats)}
    g = gdf[gdf[column].isin(ids)].assign(_id=lambda d: d[column].map(ids))
    if g.empty:
        raise ValueError(f"No polygons have a {column!r} value listed in colours")
    bounds = bounds if bounds is not None else tuple(g.total_bounds)
    if pixel_size is None:
        pixel_size = max(bounds[2] - bounds[0], bounds[3] - bounds[1]) / 3000
    ras = rasterise(g, "_id", bounds, pixel_size)
    rgb = {ids[c]: matplotlib.colors.to_rgb(colours[c]) for c in cats}
    img = fade_paper(paint(ras, rgb, pixel_size, seed), ras)
    minx, miny, maxx, maxy = bounds
    H, W = ras.shape
    return img, (minx, minx + W * pixel_size, maxy - H * pixel_size, maxy)


# ------------------------------------------------------------------ posters
def _page(paper, landscape):
    pw, ph = PAPER_SIZES[paper]
    if landscape:
        pw, ph = ph, pw
    win, hin = pw / 25.4, ph / 25.4
    base = 10.5 * np.sqrt((pw * ph) / (297 * 420))   # pt, scales with paper
    m_in = min(win, hin) * 0.06
    title_in = base * 4.2 / 72
    panel_in = base * 15 / 72
    gap = base * 1.6 / 72
    if landscape:   # legend panel on the left
        box_in = (m_in + panel_in, m_in, win - 2 * m_in - panel_in, hin - 2 * m_in - title_in - gap)
    else:           # legend panel along the bottom
        box_in = (m_in, m_in + panel_in * 0.75 + gap, win - 2 * m_in,
                  hin - 2 * m_in - title_in - panel_in * 0.75 - 2 * gap)
    return dict(win=win, hin=hin, base=base, m_in=m_in, panel_in=panel_in, box_in=box_in)


def map_box_aspect(paper="A2", landscape=False):
    """Height / width of the map area on a page, for shaping a rectangle to fill it."""
    b = _page(paper, landscape)["box_in"]
    return b[3] / b[2]


def poster(gdf, legend, out, *, column="cls", bounds=None, paper="A2", landscape=None, dpi=300,
           title="", subtitle="", signature="", website="", credit="", labels=(),
           legend_title="Land Use Types", sea_class=None, torn_edge=False, seed=7,
           formats=("pdf", "png")):
    """Paint a poster: title, map, painted legend, scale bar and credits.

    gdf        polygons in a metric CRS with an integer class column
    legend     {class_id: (name, (r, g, b))}, in legend order
    bounds     map extent (minx, miny, maxx, maxy); default is the data extent
    landscape  None picks it from the shape of the area
    labels     [(name, lon, lat, angle), ...] small italic place labels
    sea_class  paint everything outside the data with this class (e.g. sea)
    torn_edge  hand-torn edge for rectangular maps
    """
    minx, miny, maxx, maxy = bounds if bounds is not None else gdf.total_bounds
    if landscape is None:
        landscape = (maxx - minx) > (maxy - miny)
    p = _page(paper, landscape)
    win, hin, base, m_in, panel_in, box_in = (p[k] for k in ("win", "hin", "base", "m_in", "panel_in", "box_in"))
    span = max((maxx - minx) / box_in[2], (maxy - miny) / box_in[3])  # metres per inch on paper
    px = span / dpi
    ras = rasterise(gdf, column, (minx, miny, maxx, maxy), px)
    H, W = ras.shape
    print(f"raster {W}x{H}px at {px:.2f} m/px, page {paper} {'landscape' if landscape else 'portrait'}")
    if sea_class is not None:
        ras[ras == EMPTY] = sea_class
    img = paint(ras, {k: v[1] for k, v in legend.items()}, px, seed)
    if torn_edge:
        img = deckle(img, px)
    img = fade_paper(img, ras)

    f = font()
    fig = plt.figure(figsize=(win, hin), dpi=dpi)
    fig.patch.set_facecolor(PAPER)
    X = lambda i: i / win
    Y = lambda i: i / hin
    mw, mh = (maxx - minx) / span, (maxy - miny) / span
    ax = fig.add_axes([X(box_in[0] + (box_in[2] - mw) / 2), Y(box_in[1] + (box_in[3] - mh) / 2), X(mw), Y(mh)])
    ax.imshow(img, extent=(minx, minx + W * px, maxy - H * px, maxy), interpolation="lanczos")
    ax.set_xlim(minx, maxx); ax.set_ylim(miny, maxy)
    ax.set_aspect("equal"); ax.axis("off")

    for lab in labels:
        name, lon, lat = lab[:3]
        ang = lab[3] if len(lab) > 3 else 0
        pt = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(gdf.crs).iloc[0]
        ax.text(pt.x, pt.y, name, fontproperties=f, fontsize=base * 1.05, color=(0.22,) * 3,
                ha="center", va="center", rotation=ang, rotation_mode="anchor",
                path_effects=[pe.withStroke(linewidth=base * 0.35, foreground=(*PAPER, 0.75))])

    if title:
        fig.text(X(m_in), 1 - Y(m_in), title, fontproperties=f, fontsize=base * 2.6, color=INK, va="top")
    if subtitle:   # Lora has no Greek glyphs: fall back to FreeSerif Italic
        sf = f if all(ord(ch) < 0x370 for ch in subtitle) else font("FreeSerifItalic.ttf")
        fig.text(X(m_in), 1 - Y(m_in + base * 3.3 / 72), subtitle, fontproperties=sf,
                 fontsize=base * 1.05, color=(0.42,) * 3, va="top")

    # legend, painted with the same brush
    present = [c for c in legend if (ras == c).any()]
    row = base * 2.0 / 72
    lx = m_in
    ly = (m_in + panel_in * 0.75 + len(present) * row) if landscape else box_in[1] - base * 2.6 / 72 - row
    if legend_title:
        fig.text(X(lx), Y(ly + row * 0.9), legend_title, fontproperties=f, fontsize=base * 1.15, color=INK)
    per = int(np.ceil(len(present) / (1 if landscape else 2))) or 1
    for i, cid in enumerate(present):
        cx = lx + (i // per) * base * 13 / 72
        y = ly - row * (i % per)
        sw, sh = base * 2.2 / 72, base * 0.9 / 72
        sax = fig.add_axes([X(cx), Y(y - sh / 2), X(sw), Y(sh)])
        sax.imshow(swatch(legend[cid][1], cid), aspect="auto"); sax.axis("off")
        fig.text(X(cx + sw + base * 0.6 / 72), Y(y), legend[cid][0], fontproperties=f,
                 fontsize=base * 0.95, color=INK, va="center")

    # scale bar, true to map scale
    target = panel_in * 0.7 * span
    total = 10 ** np.floor(np.log10(target))
    for mult in (5, 2, 1):
        if total * mult <= target:
            total *= mult
            break
    bar_in = total / span
    sy = (m_in + base * 2.2 / 72) if landscape else (m_in + base * 0.8 / 72)
    sx = m_in if landscape else win - m_in - bar_in - base * 10 / 72
    sbx = fig.add_axes([X(sx), Y(sy), X(bar_in), Y(base * 0.5 / 72)])
    sbx.set_xlim(0, total); sbx.set_ylim(0, 1); sbx.axis("off")
    sbx.plot([0, total], [0, 0], color=INK, lw=0.8, clip_on=False)
    for t in np.linspace(0, total, 11):
        sbx.plot([t, t], [0, 0.55 if t in (0, total / 2, total) else 0.3], color=INK, lw=0.6, clip_on=False)
    unit = 1000 if total >= 1000 else 1
    for t in (0, total / 2, total):
        sbx.text(t, 1.0, f"{t / unit:g}" + ((" km" if unit == 1000 else " m") if t == total else ""),
                 ha="center", va="bottom", fontsize=base * 0.75, color=INK, fontproperties=f)

    if signature:
        fig.text(1 - X(m_in), 1 - Y(m_in + base * 0.9 / 72), signature, ha="right", va="top",
                 fontproperties=f, fontsize=base * 1.5, color=INK)
    if website:
        fig.text(1 - X(m_in), 1 - Y(m_in + base * 3.3 / 72), website, ha="right", va="top",
                 fontproperties=f, fontsize=base * 0.8, color=(0.45,) * 3)
    if credit:
        fig.text(1 - X(m_in), Y(m_in * 0.55), credit, ha="right", fontsize=base * 0.6,
                 color=(0.45,) * 3, fontproperties=f)

    out = Path(out)
    for ext in formats:
        fig.savefig(out.with_suffix(f".{ext}"), dpi=dpi, facecolor=PAPER)
    plt.close(fig)
    print("saved", out)
    return out
