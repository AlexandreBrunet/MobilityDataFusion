
import utils.gdf.gdfExtraction as gdfExtraction
import geopandas as gpd
import pandas as pd
from typing import Dict

# def extract_geometries(geodataframes):
#     points_gdfs = {layer_name: gdfExtraction.extract_points_gdf(gdf).assign(layer_name=layer_name) 
#                    for layer_name, gdf in geodataframes.items()}
#     polygons_gdfs = {layer_name: gdfExtraction.extract_polygons_gdf(gdf).assign(layer_name=layer_name) 
#                      for layer_name, gdf in geodataframes.items()}
#     multipolygons_gdfs = {layer_name: gdfExtraction.extract_multipolygons_gdf(gdf).assign(layer_name=layer_name) 
#                           for layer_name, gdf in geodataframes.items()}
#     linestrings_gdfs = {layer_name: gdfExtraction.extract_linestrings_gdf(gdf).assign(layer_name=layer_name) 
#                           for layer_name, gdf in geodataframes.items()}
#     return points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs


def extract_geometries(geodataframes: Dict[str, gpd.GeoDataFrame]) -> Dict[str, gpd.GeoDataFrame]:
    # Extraire les géométries et les fusionner dans un seul GeoDataFrame par type
    points_gdfs = [
        gdfExtraction.extract_points_gdf(gdf).assign(layer_name=layer_name) 
        for layer_name, gdf in geodataframes.items()
    ]
    polygons_gdfs = [
        gdfExtraction.extract_polygons_gdf(gdf).assign(layer_name=layer_name) 
        for layer_name, gdf in geodataframes.items()
    ]
    multipolygons_gdfs = [
        gdfExtraction.extract_multipolygons_gdf(gdf).assign(layer_name=layer_name) 
        for layer_name, gdf in geodataframes.items()
    ]
    linestrings_gdfs = [
        gdfExtraction.extract_linestrings_gdf(gdf).assign(layer_name=layer_name) 
        for layer_name, gdf in geodataframes.items()
    ]

    # Fusionner toutes les couches pour chaque type de géométrie
    extracted_geometries = {
        "points": gpd.GeoDataFrame(pd.concat(points_gdfs, ignore_index=True), crs="EPSG:4326") if points_gdfs else gpd.GeoDataFrame(),
        "polygons": gpd.GeoDataFrame(pd.concat(polygons_gdfs, ignore_index=True), crs="EPSG:4326") if polygons_gdfs else gpd.GeoDataFrame(),
        "multipolygons": gpd.GeoDataFrame(pd.concat(multipolygons_gdfs, ignore_index=True), crs="EPSG:4326") if multipolygons_gdfs else gpd.GeoDataFrame(),
        "linestrings": gpd.GeoDataFrame(pd.concat(linestrings_gdfs, ignore_index=True), crs="EPSG:4326") if linestrings_gdfs else gpd.GeoDataFrame(),
    }

    return extracted_geometries