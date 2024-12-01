import geopandas as gpd
import itertools
import utils.buffer.buffer as buffer

def apply_points_buffer(points_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict) -> gpd.GeoDataFrame:
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

def create_buffers(points_gdfs, buffer_layers):
    unique_id_counter = itertools.count(1)
    buffer_gdfs = {
        f"{layer_name}_buffer": buffer.apply_points_buffer(points_gdfs[layer_name], layer_name, buffer_layers)
                                       .assign(layer_name=f"{layer_name}_buffer",
                                               buffer_id=lambda df: [next(unique_id_counter) for _ in range(len(df))])
        for layer_name in buffer_layers
    }
    return buffer_gdfs