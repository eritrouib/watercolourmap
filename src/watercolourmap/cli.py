"""Command line: watercolour posters from Copernicus Urban Atlas files."""
import argparse

import geopandas as gpd
from shapely.geometry import box

from .legends import IGNITION, URBAN_ATLAS_CREDIT, read_urban_atlas
from .poster import poster, map_box_aspect
from .shapes import local_crs, irregular_circle, rectangle


def parse_label(spec):
    parts = spec.split("|")
    return (parts[0], float(parts[1]), float(parts[2]), float(parts[3]) if len(parts) > 3 else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="watercolourmap",
                                 description="Watercolour land cover poster from a Copernicus Urban Atlas file.")
    ap.add_argument("data", help="Urban Atlas .fgb or .gpkg")
    ap.add_argument("--layer")
    where = ap.add_argument_group("area (pick one)")
    where.add_argument("--center", nargs=2, type=float, metavar=("LON", "LAT"))
    where.add_argument("--radius", type=float, help="with --center: irregular circle, km")
    where.add_argument("--width", type=float, default=8, help="with --center: rectangle width, km")
    where.add_argument("--bbox", nargs=4, type=float, metavar=("MINLON", "MINLAT", "MAXLON", "MAXLAT"))
    where.add_argument("--clip", help="any polygon file")
    ap.add_argument("--landscape", action="store_true")
    ap.add_argument("--sea", action="store_true", help="paint everything outside the data as Blue Cover")
    ap.add_argument("--label", action="append", default=[], metavar='"Name|lon|lat[|angle]"')
    ap.add_argument("--title", default="Land Cover")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--signature", default="", help="e.g. your name or handle, top right")
    ap.add_argument("--website", default="", help="small line under the signature")
    ap.add_argument("--credit", default=URBAN_ATLAS_CREDIT)
    ap.add_argument("--paper", default="A2", choices=["A1", "A2", "A3", "A4"])
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--out", default="landcover")
    a = ap.parse_args(argv)

    bounds, landscape, torn = None, None, False
    if a.center and a.radius:
        crs, c = local_crs(*a.center)
        R = a.radius * 1000
        read = tuple(gpd.GeoSeries([c.buffer(R * 1.6)], crs=crs).to_crs(4326).total_bounds)
        gdf = read_urban_atlas(a.data, read, a.layer).to_crs(crs)
        gdf = irregular_circle(gdf, c, R)
        landscape = False
    elif a.center:
        crs, c = local_crs(*a.center)
        landscape = a.landscape
        rect = rectangle(c, a.width * 1000, map_box_aspect(a.paper, landscape))
        read = tuple(gpd.GeoSeries([rect], crs=crs).to_crs(4326).total_bounds)
        gdf = gpd.clip(read_urban_atlas(a.data, read, a.layer).to_crs(crs), rect)
        bounds, torn = rect.bounds, True
    else:
        gdf = read_urban_atlas(a.data, a.bbox, a.layer)
        gdf = gdf.to_crs(gdf.estimate_utm_crs())
        if a.clip:
            gdf = gpd.clip(gdf, gpd.read_file(a.clip).to_crs(gdf.crs).union_all())
        elif a.bbox:
            gdf = gpd.clip(gdf, gpd.GeoSeries([box(*a.bbox)], crs=4326).to_crs(gdf.crs).union_all())
    gdf = gdf[gdf.cls >= 0]   # class 0 (roads) is burnt in as bare paper, so --sea can't fill it

    poster(gdf, IGNITION, a.out, bounds=bounds, paper=a.paper, landscape=landscape, dpi=a.dpi,
           title=a.title, subtitle=a.subtitle, signature=a.signature, website=a.website,
           credit=a.credit, labels=[parse_label(s) for s in a.label],
           sea_class=1 if a.sea else None, torn_edge=torn)


if __name__ == "__main__":
    main()
