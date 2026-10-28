"""Paint any polygons by any column with your own colours.

Here: Urban Atlas parcels around Elbasan castle, grouped into just three
categories, drawn into an ordinary matplotlib figure.

    python custom_palette.py URBAN_ATLAS_FILE.fgb
"""
import sys

import matplotlib.pyplot as plt
from shapely.geometry import Point

from watercolourmap import read_urban_atlas, local_crs, paint_gdf, PAPER

path = sys.argv[1]
crs, centre = local_crs(20.087, 41.110)
gdf = read_urban_atlas(path, bbox=(20.06, 41.09, 20.12, 41.13)).to_crs(crs)
gdf = gdf.clip(centre.buffer(1500))


def group(code):
    code = int(code)
    if code == 50000:
        return "river"
    if code in (14110, 14120, 14130, 31000, 32000):
        return "green"
    if code < 12000:
        return "homes"
    return None


gdf["group"] = gdf["code_2021"].map(group)
img, extent = paint_gdf(gdf, "group", {"homes": "#c9a27e", "green": "#7a9a5a", "river": "#5f86b0"},
                        pixel_size=1.5)

fig, ax = plt.subplots(figsize=(8, 8), facecolor=PAPER)
ax.imshow(img, extent=extent)
ax.set_axis_off()
fig.savefig("custom_palette.png", dpi=200, facecolor=PAPER, bbox_inches="tight")
print("saved custom_palette.png")
