
import utils.gdf.gdfExtraction as gdfExtraction
from typing import Dict, Tuple
import geopandas as gpd
import pandas as pd

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

def simplify_geometries(geometries_dict: Dict[str, gpd.GeoDataFrame], tolerance: float) -> Dict[str, gpd.GeoDataFrame]:
    """
    Simplifie les géométries dans un dictionnaire de GeoDataFrames et retourne un dictionnaire reconstruit
    correspondant au format d'origine.

    Parameters:
        geometries_dict (Dict[str, gpd.GeoDataFrame]): Dictionnaire initial avec des GeoDataFrames.
        tolerance (float): Tolérance pour la simplification des géométries.

    Returns:
        Dict[str, gpd.GeoDataFrame]: Nouveau dictionnaire avec des GeoDataFrames simplifiés.
    """
    # Combiner toutes les géométries en une seule GeoSeries
    combined_geo_series = gpd.GeoSeries(
        pd.concat([df['geometry'] for df in geometries_dict.values()], ignore_index=True)
    )
    
    # Appliquer la simplification
    simplified_geo_series = combined_geo_series.simplify(tolerance, preserve_topology=False)
    
    # Reconstruire le dictionnaire avec des GeoDataFrames
    simplified_dict = {}
    start = 0
    for key, original_df in geometries_dict.items():
        num_geometries = len(original_df)
        
        # Extraire les géométries simplifiées pour cette couche
        geometries = simplified_geo_series[start:start + num_geometries]
        
        # Reconstruire le GeoDataFrame avec les colonnes originales
        simplified_dict[key] = gpd.GeoDataFrame(
            original_df.drop(columns='geometry').assign(geometry=geometries),  # Conserver les autres colonnes
            crs=original_df.crs
        )
        
        start += num_geometries

    return simplified_dict