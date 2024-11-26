import geopandas as gpd
import utils.utils as utils

def apply_buffer(points_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict) -> gpd.GeoDataFrame:
    if not layer_name in buffer_layers:
        raise ValueError(f"La couche '{layer_name}' n'est pas définie dans buffer_layers.")
    
    if not points_gdf.geometry.geom_type.eq('Point').all():
        raise TypeError("Le GeoDataFrame doit contenir uniquement des géométries de type 'Point'.")
    
    buffer_distance = buffer_layers[layer_name]
    buffer_gdf = points_gdf.copy()
    
    # Reprojection dynamique pour appliquer le buffer en mètres
    utm_crs = utils.detect_utm_crs(buffer_gdf)  # Implémente une fonction pour détecter l'UTM
    buffer_gdf = buffer_gdf.to_crs(utm_crs)
    
    buffer_gdf['geometry'] = buffer_gdf['geometry'].buffer(buffer_distance)
    
    # Reprojeter en WGS 84 (EPSG:4326) pour la sortie
    buffer_gdf = buffer_gdf.to_crs(epsg=4326)
    
    # Ajouter des métadonnées
    buffer_gdf['buffer_layer'] = layer_name
    buffer_gdf['buffer_distance_m'] = buffer_distance
    
    return buffer_gdf