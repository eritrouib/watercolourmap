# watercolourmap

Watercolour maps in Python. Polygons are painted as soft washes on textured paper, with uneven pigment, darker edges and a thin line of bare paper between neighbouring shapes.

It's inspired by John Nelson's [watercolour style for ArcGIS Pro](https://www.esri.com/arcgis-blog/products/arcgis-pro/mapping/steal-this-watercolor-style-for-pro-please), recreated in code so it works with any GeoDataFrame. You can see example prints at [etymo.co.uk/cartography](https://etymo.co.uk/cartography/).

## Install

```bash
pip install watercolourmap
```

## Paint any polygons

```python
import geopandas as gpd
import matplotlib.pyplot as plt
from watercolourmap import paint_gdf, PAPER

gdf = gpd.read_file("my_area.gpkg")
gdf = gdf.to_crs(gdf.estimate_utm_crs())          # needs a CRS in metres

img, extent = paint_gdf(
    gdf, "landuse",
    {"residential": "#c9a27e", "park": "#7a9a5a", "water": "#5f86b0"},
)

fig, ax = plt.subplots(figsize=(8, 8), facecolor=PAPER)
ax.imshow(img, extent=extent)
ax.set_axis_off()
fig.savefig("map.png", dpi=300, facecolor=PAPER)
```

- Polygons whose value isn't in the colour dictionary are left as bare paper.
- `pixel_size` sets the resolution in metres per pixel. By default the longer side is about 3,000 pixels.
- `seed` changes the brushwork.

## Print posters from Copernicus Urban Atlas

The command line tool turns a [Copernicus Urban Atlas](https://land.copernicus.eu/en/products/urban-atlas) city file into a print-ready poster. You get a title, the painted map, a legend painted with the same brush, a scale bar and the data credit, saved as PDF and PNG.

```bash
# An irregular circle, 1.8 km radius, with place labels
watercolourmap ELBASAN.fgb --center 20.097 41.106 --radius 1.8 \
    --title "Elbasan Land Cover" \
    --label "Kalaja|20.080|41.1125" --label "Lumi Shkumbin|20.0975|41.1006|-4" \
    --paper A2 --out elbasan

# A 12 km rectangle with a hand-torn edge, and the sea painted in
watercolourmap ATHINA.fgb --center 23.688 37.958 --width 12 --sea \
    --title "Athens Land Cover" --paper A2 --out athens
```

Run `watercolourmap --help` for every option: `--bbox` or `--clip` for other areas, `--signature` and `--website` to sign your map, and `--dpi 100` for quick drafts.

Urban Atlas codes are grouped into seven classes: Blue, Green, Green-Grey and Grey Cover, Land Use Changing, Unknown and Other Natural. Roads and railways are left as bare paper. Urban Atlas maps land use rather than land cover, so some groupings are judgement calls. For example, marinas are coded as sports and leisure. You can see the full mapping in `urban_atlas_class()`.

Keep the credit on your maps. The tool adds it by default: *Contains modified Copernicus Land Monitoring Service information (Urban Atlas 2021) © European Union*.

## Building blocks

| Function | What it does |
|---|---|
| `paint_gdf(gdf, column, colours)` | Paints any polygons and returns an image and its extent |
| `poster(gdf, legend, out, ...)` | Lays out a full poster from polygons with integer classes |
| `paint(classes, colours, pixel_size)` | Paints a raster of class ids |
| `irregular_circle(gdf, centre, radius)` | Keeps whole parcels inside a circle, for a ragged, parcel-shaped edge |
| `read_urban_atlas(path, bbox)` | Reads an Urban Atlas file and adds the legend class |
| `IGNITION` | The default seven-class legend and colours |

## Credits

- **Watercolour style:** inspired by John Nelson (Esri).
- **Legend:** from the University of Manchester IGNITION project land cover map.
- **Fonts:** Lora (SIL Open Font License) and FreeSerif (GPL with font exception) are bundled.

MIT licence © 2026 Eriola Trungu Impersimi
