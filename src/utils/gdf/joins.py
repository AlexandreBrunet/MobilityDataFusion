import geopandas as gpd
import pandas as pd

# Fonction pour récupérer les couches de points et de polygones pour les jointures
def get_join_layers(points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs, join_layers):
    join_data = {}
    if "points" in join_layers:
        join_data["points"] = points_gdfs
    if "polygons" in join_layers:
        join_data["polygons"] = polygons_gdfs
    if "multipolygons" in join_layers:
        join_data["multipolygons"] = multipolygons_gdfs
    if "linestrings" in join_layers: 
        join_data["linestrings"] = linestrings_gdfs
    return join_data

def perform_spatial_joins(buffer_gdfs, join_data, join_layers):
    buffer_joins = []
    for layer_name, buffer_gdf in buffer_gdfs.items():
        for geom_type, gdfs in join_data.items():
            join_type = join_layers[geom_type]["type"]
            for join_layer_name, join_gdf in gdfs.items():
                join_result = gpd.sjoin(buffer_gdf, join_gdf, how="inner", predicate=join_type).assign(
                    buffer_layer=layer_name,
                    join_type=join_layer_name
                )
                buffer_joins.append(join_result)
    return pd.concat(buffer_joins, ignore_index=True)

def spatial_join_all_layers(extracted_gdf, buffer_gdf, join_layers):
    """
    Effectue un spatial join pour chaque GeoDataFrame dans extracted_gdf avec buffer_gdf
    selon les critères définis dans join_layers.

    Args:
        extracted_gdf (dict): Un dictionnaire contenant des GeoDataFrames.
        buffer_gdf (GeoDataFrame): Le GeoDataFrame contenant les buffers à utiliser pour la jointure.
        join_layers (dict): Dictionnaire contenant les types de jointure pour chaque couche (points, polygones, etc.).

    Returns:
        GeoDataFrame: Un GeoDataFrame résultant de la concaténation des résultats des jointures spatiales.
    """
    joined_gdfs = []  # Liste pour stocker les résultats des jointures
    
    # Effectuer un spatial join pour chaque GeoDataFrame selon les critères définis
    for layer, gdf in extracted_gdf.items():
        # Vérifier si le layer est défini dans join_layers et extraire le type de jointure
        if layer in join_layers:
            join_type = join_layers[layer]["type"]  # Récupère le type de jointure pour cette couche
            
            if join_type == "contains":
                # Jointure avec "contains" (par exemple, points à buffer)
                joined_gdf = gpd.sjoin(gdf, buffer_gdf, how="inner", predicate="within")  # "within" pour les points
            elif join_type == "intersects":
                # Jointure avec "intersects" (par exemple, polygones, lignes, multipolygones)
                joined_gdf = gpd.sjoin(gdf, buffer_gdf, how="inner", predicate="intersects")
            else:
                raise ValueError(f"Unsupported join type: {join_type}")
            
            # Ajouter le résultat de cette jointure à la liste
            joined_gdfs.append(joined_gdf)
    
    # Concaténer tous les résultats des jointures dans un seul GeoDataFrame
    final_joined_gdf = gpd.GeoDataFrame(pd.concat(joined_gdfs, ignore_index=True))
    
    # Optionnel: Supprimer les colonnes vides dans le GeoDataFrame final
    final_joined_gdf = final_joined_gdf.dropna(axis=1, how="all")
    
    # Si nécessaire, vérifier le CRS et l'ajuster
    final_joined_gdf = final_joined_gdf.set_crs(buffer_gdf.crs, allow_override=True)  # Assurez-vous que le CRS est compatible
    
    return final_joined_gdf
