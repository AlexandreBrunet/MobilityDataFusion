import geopandas as gpd
import pandas as pd

def apply_buffer(points_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict) -> gpd.GeoDataFrame:
    """
    Applique un buffer aux géométries de type 'Point' dans un GeoDataFrame pour une couche spécifique.
    
    Paramètres :
    - points_gdf : GeoDataFrame contenant des points.
    - layer_name : nom de la couche pour laquelle appliquer le buffer.
    - buffer_layers : dictionnaire où les clés sont les noms de couche et les valeurs sont les distances de buffer en mètres.
    
    Retourne :
    - buffer_gdf : GeoDataFrame avec le buffer appliqué si la couche correspond.
    """
    buffer_gdf = points_gdf.copy()
    
    # Vérifie si la couche correspond à une entrée dans le dictionnaire de buffers
    if layer_name in buffer_layers:
        buffer_distance = buffer_layers[layer_name]
        
        # Reprojeter en CRS UTM pour appliquer le buffer en mètres
        buffer_gdf = buffer_gdf.to_crs(epsg=32618)  # Remplacer 32618 par l'EPSG adapté à la région si nécessaire
        buffer_gdf['geometry'] = buffer_gdf['geometry'].buffer(buffer_distance)
        
        # Reprojeter en WGS 84 pour revenir aux coordonnées d'origine
        buffer_gdf = buffer_gdf.to_crs(epsg=4326)
    
    return buffer_gdf