"""
Region definition: Ostalpen (Eastern Alps)
===========================================
Geographic scope, projection, cities, and file paths for the Eastern Alps.
"""

from deck import Region, DATA_DIR_OSM, DATA_DIR_DEM

REGION = Region(
    name="ostalpen",

    bbox_west=9.05, bbox_east=16.82, bbox_south=45.2, bbox_north=48.62,
    projection_params={
        "central_longitude": 12.0,
        "central_latitude": 46.75,
        "standard_parallels": (46.0, 48.0),
    },

    figure_width=14,
    figure_height=9,

    cities=[
        ("München",     11.576, 48.137,  0.05,  0.02),
        ("Innsbruck",   11.394, 47.260,  0.05,  0.02),
        ("Bozen",       11.354, 46.498,  0.05,  0.02),
        ("Venedig",     12.338, 45.440,  0.05,  0.02),
        ("Wien",        16.373, 48.209,  0.05,  0.02),
        ("St. Pölten",  15.627, 48.204,  0.05,  0.02),
        ("Salzburg",    13.055, 47.810,  0.05,  0.02),
        ("Bregenz",      9.748, 47.503, -0.05,  0.02),
        ("Vaduz",        9.521, 47.141, -0.05,  0.02),
        ("Trient",      11.122, 46.067,  0.05,  0.02),
        ("Graz",        15.441, 47.070,  0.05,  0.02),
        ("Klagenfurt",  14.306, 46.624,  0.05,  0.02),
        ("Laibach",     14.506, 46.052,  0.05,  0.02),
        ("Mailand",      9.190, 45.464,  0.05,  0.02),
        ("Verona",      10.992, 45.438,  0.05,  0.02),
        ("Triest",      13.776, 45.649,  0.05,  0.02),
        ("Zagreb",      15.978, 45.815,  0.05,  0.02),
    ],

    osm_rivers_geojson=DATA_DIR_OSM / "osm_rivers_ostalpen.geojson",
    osm_lakes_geojson=DATA_DIR_OSM / "osm_lakes_ostalpen.geojson",
    osm_borders_geojson=DATA_DIR_OSM / "osm_borders_ostalpen.geojson",
    dem_tif=DATA_DIR_DEM / "ostalpen_dem.tif",
)
