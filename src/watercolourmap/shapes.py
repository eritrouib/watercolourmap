"""Map shapes: irregular circles and page-filling rectangles."""
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon, box


def local_crs(lon, lat):
    """A metric (UTM) CRS for a point, and the point in that CRS."""
    s = gpd.GeoSeries([Point(lon, lat)], crs=4326)
    crs = s.estimate_utm_crs()
    return crs, s.to_crs(crs).iloc[0]


def wobbly_circle(centre, radius, seed=11, n=1440):
    """A slightly irregular circle polygon around a projected point."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    wob = sum(rng.uniform(0.008, 0.03) * np.sin(f * t + rng.uniform(0, 6.3)) for f in (3, 5, 8, 13, 21))
    return Polygon([(centre.x + radius * (1 + w) * np.cos(q), centre.y + radius * (1 + w) * np.sin(q))
                    for q, w in zip(t, wob)])


def irregular_circle(gdf, centre, radius, seed=11):
    """Keep whole parcels whose centre is within `radius` of `centre`.

    This gives the ragged, parcel-shaped edge. Very large parcels (a river,
    a forest, the road network) are trimmed with a wobbly circle so they
    don't run off the page. gdf must be in a metric CRS.
    """
    inside = gdf.representative_point().distance(centre) <= radius
    edge = wobbly_circle(centre, radius * 1.08, seed)
    big = gdf.intersects(centre.buffer(radius)) & ~gdf.within(edge)
    keep = gdf[inside | big].copy()
    keep["geometry"] = keep.geometry.intersection(edge)
    return keep[~keep.geometry.is_empty]


def rectangle(centre, width, aspect):
    """A rectangle `width` metres wide, height = width * aspect, around a projected point."""
    hw, hh = width / 2, width * aspect / 2
    return box(centre.x - hw, centre.y - hh, centre.x + hw, centre.y + hh)
