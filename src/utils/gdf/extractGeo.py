
import utils.gdf.gdfExtraction as gdfExtraction
from typing import Dict, Tuple
import geopandas as gpd

def extract_geometries(geodataframes: Dict[str, gpd.GeoDataFrame]) -> Tuple[
    Dict[str, gpd.GeoDataFrame],  # Points GeoDataFrames
    Dict[str, gpd.GeoDataFrame],  # Polygons GeoDataFrames
    Dict[str, gpd.GeoDataFrame],  # MultiPolygons GeoDataFrames
    Dict[str, gpd.GeoDataFrame]   # LineStrings GeoDataFrames
]:
    points_gdfs = {layer_name: gdfExtraction.extract_points_gdf(gdf).assign(layer_name=layer_name) 
                   for layer_name, gdf in geodataframes.items()}
    polygons_gdfs = {layer_name: gdfExtraction.extract_polygons_gdf(gdf).assign(layer_name=layer_name) 
                     for layer_name, gdf in geodataframes.items()}
    multipolygons_gdfs = {layer_name: gdfExtraction.extract_multipolygons_gdf(gdf).assign(layer_name=layer_name) 
                          for layer_name, gdf in geodataframes.items()}
    linestrings_gdfs = {layer_name: gdfExtraction.extract_linestrings_gdf(gdf).assign(layer_name=layer_name) 
                          for layer_name, gdf in geodataframes.items()}
    return points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs