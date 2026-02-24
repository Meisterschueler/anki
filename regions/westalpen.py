"""
Region definition: Westalpen (Western Alps)
============================================
Geographic scope, projection, cities, and file paths for the Western Alps.
"""

from deck import Region, DATA_DIR_OSM, DATA_DIR_DEM

REGION = Region(
    name="westalpen",

    bbox_west=4.5, bbox_east=9.9, bbox_south=42.8, bbox_north=47.7,
    projection_params={
        "central_longitude": 7.2,
        "central_latitude": 45.25,
        "standard_parallels": (43.5, 47.0),
    },

    figure_width=9,
    figure_height=14,

    cities=[
        ("Genf",        6.143, 46.204,  0.05,  0.02),
        ("Bern",        7.447, 46.948,  0.05,  0.02),
        ("Luzern",      8.305, 47.051,  0.05,  0.02),
        ("Zürich",      8.541, 47.377,  0.05,  0.02),
        ("Dijon",       5.042, 47.322,  0.05,  0.02),
        ("Lyon",        4.835, 45.764,  0.05,  0.02),
        ("Grenoble",    5.724, 45.188,  0.05,  0.02),
        ("Valence",     4.891, 44.934,  0.05,  0.02),
        ("Gap",         6.079, 44.560,  0.05,  0.02),
        ("Avignon",     4.806, 43.949,  0.05,  0.02),
        ("Nizza",       7.262, 43.710,  0.05,  0.02),
        ("Turin",       7.686, 45.070,  0.05,  0.02),
        ("Mailand",     9.190, 45.464,  0.05,  0.02),
        ("Como",        9.085, 45.810,  0.05,  0.02),
        ("Lugano",      8.952, 46.010,  0.05,  0.02),
        ("Aosta",       7.315, 45.737,  0.05,  0.02),
        ("Chambéry",    5.917, 45.564,  0.05,  0.02),
        ("Sitten",      7.360, 46.233,  0.05,  0.02),
        ("Genua",       8.934, 44.407,  0.05,  0.02),
        ("Briançon",    6.643, 44.898,  0.05,  0.02),
        ("Annecy",      6.129, 45.899,  0.05,  0.02),
        ("Marseille",   5.369, 43.297,  0.05,  0.02),
        ("St. Gallen",  9.379, 47.423,  0.05,  0.02),
    ],

    osm_rivers_geojson=DATA_DIR_OSM / "osm_rivers_westalpen.geojson",
    osm_lakes_geojson=DATA_DIR_OSM / "osm_lakes_westalpen.geojson",
    osm_borders_geojson=DATA_DIR_OSM / "osm_borders_westalpen.geojson",
    dem_tif=DATA_DIR_DEM / "westalpen_dem.tif",
)
