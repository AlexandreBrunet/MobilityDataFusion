import geopandas as gpd
import pandas as pd

# Fonction pour récupérer les couches de points et de polygones pour les jointures
def get_join_layers(points_gdfs, polygons_gdfs, join_layers):
    join_data = {}
    if "points" in join_layers:
        join_data["points"] = points_gdfs
    if "polygons" in join_layers:
        join_data["polygons"] = polygons_gdfs
    return join_data

# Appliquer les jointures sans hardcoding
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