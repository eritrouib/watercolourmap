"""Legends: the IGNITION land cover palette and the Urban Atlas reclassification."""
import re

import geopandas as gpd
import pyogrio
from shapely.geometry import box

# Muted watercolour pigments, close to the Gorton and Abbey Hey map (IGNITION legend)
IGNITION = {
    1: ("Blue Cover",        (0.42, 0.55, 0.74)),
    2: ("Green Cover",       (0.42, 0.60, 0.33)),
    3: ("Green-Grey Cover",  (0.55, 0.66, 0.66)),
    4: ("Grey Cover",        (0.66, 0.70, 0.76)),
    5: ("Land Use Changing", (0.80, 0.38, 0.38)),
    6: ("Unknown",           (0.82, 0.63, 0.50)),
    7: ("Other Natural",     (0.83, 0.77, 0.62)),
}
BARE = 0  # roads and rail: left as bare paper

URBAN_ATLAS_CREDIT = ("Contains modified Copernicus Land Monitoring Service "
                      "information (Urban Atlas 2021) © European Union")


def urban_atlas_class(code):
    """Copernicus Urban Atlas code -> IGNITION legend class id."""
    c = int(code)
    if c in (11100, 11210, 12100, 12300, 12400):      return 4   # grey
    if c in (11220, 11230, 11240, 11300):             return 3   # green-grey
    if c in (12210, 12220, 12230):                    return BARE
    if c in (13100, 13300):                           return 5   # changing
    if c == 13400:                                    return 6   # unknown / vacant
    if c in (14100, 14110, 14120, 14130):             return 2   # urban green (2021 splits by access)
    if c == 14200:                                    return 3   # sports and leisure, incl. marinas
    if 31000 <= c <= 32000 or 40000 <= c < 50000:     return 2   # forest, grassland, wetland
    if 20000 <= c < 30000:                            return 7   # agriculture
    if c == 33000:                                    return 7   # bare ground, beaches
    if c == 50000:                                    return 1   # water
    return 6


def read_urban_atlas(path, bbox=None, layer=None, verbose=True):
    """Read an Urban Atlas file (gpkg or fgb) and add a 'cls' column with legend ids.

    bbox  optional (minlon, minlat, maxlon, maxlat) to read only part of the city
    """
    layers = [l[0] for l in pyogrio.list_layers(path)]
    if layer is None:
        cand = [l for l in layers if not re.search(r"bound|core|fua_area", l, re.I)]
        layer = (cand or layers)[0]
    kw = {}
    if bbox:
        crs = pyogrio.read_info(path, layer=layer)["crs"]
        kw["bbox"] = tuple(gpd.GeoSeries([box(*bbox)], crs=4326).to_crs(crs).total_bounds)
    gdf = gpd.read_file(path, layer=layer, **kw)
    codecol = next(c for c in gdf.columns if re.fullmatch(r"code_20\d\d", c, re.I))
    gdf["cls"] = gdf[codecol].map(urban_atlas_class)
    if verbose:
        print(f"layer={layer} code column={codecol} features={len(gdf)}")
    return gdf
