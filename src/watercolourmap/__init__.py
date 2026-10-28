"""watercolourmap: watercolour maps in Python, inspired by John Nelson's watercolour style for ArcGIS Pro.

Quick use with any polygons:

    import geopandas as gpd, matplotlib.pyplot as plt
    from watercolourmap import paint_gdf

    gdf = gpd.read_file("parks_and_water.gpkg")
    gdf = gdf.to_crs(gdf.estimate_utm_crs())
    img, extent = paint_gdf(gdf, "type", {"park": "#6b9954", "water": "#6b8cbd"})
    plt.imshow(img, extent=extent); plt.axis("off"); plt.savefig("map.png", dpi=300)

Print posters from Copernicus Urban Atlas files: see `watercolourmap --help`.
"""
from .brush import paint, swatch, deckle, PAPER
from .legends import IGNITION, URBAN_ATLAS_CREDIT, urban_atlas_class, read_urban_atlas
from .poster import paint_gdf, poster, map_box_aspect
from .shapes import local_crs, irregular_circle, rectangle, wobbly_circle

__version__ = "0.1.0"
__all__ = ["paint", "swatch", "deckle", "PAPER", "IGNITION", "URBAN_ATLAS_CREDIT",
           "urban_atlas_class", "read_urban_atlas", "paint_gdf", "poster", "map_box_aspect",
           "local_crs", "irregular_circle", "rectangle", "wobbly_circle"]
