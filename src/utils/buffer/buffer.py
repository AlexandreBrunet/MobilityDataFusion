import geopandas as gpd
import itertools
import utils.buffer.buffer as buffer
import utils.buffer.grid as grid
import geopandas as gpd

def apply_points_buffer(points_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict) -> gpd.GeoDataFrame:
    buffer_gdf = points_gdf.copy()
    
    # Vérifie si la couche correspond à une entrée dans le dictionnaire de buffers
    if layer_name in buffer_layers:
        buffer_distance = buffer_layers[layer_name].get("distance", 0)
        geometry_type = buffer_layers[layer_name].get("geometry_type", None)

        # Vérifie si le type de géométrie est un Point
        if geometry_type == "Point":
            try:
                # Vérifie si toutes les géométries sont des points
                if not all(buffer_gdf.geometry.geom_type == "Point"):
                    raise ValueError("Certaines géométries ne sont pas de type Point.")

                # Reprojeter en CRS UTM pour appliquer le buffer en mètres
                buffer_gdf = buffer_gdf.to_crs(epsg=32618)  # Adapter l'EPSG selon la région
                buffer_gdf['geometry'] = buffer_gdf['geometry'].buffer(buffer_distance)

                # Reprojeter en WGS 84 pour revenir aux coordonnées d'origine
                buffer_gdf = buffer_gdf.to_crs(epsg=4326)

            except Exception as e:
                print(f"Erreur lors de la reprojection ou du buffer : {e}")
        else:
            print(f"Le type de géométrie '{geometry_type}' n'est pas supporté pour cette couche.")
    
    return buffer_gdf

def apply_linestring_buffer(linestrings_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict) -> gpd.GeoDataFrame:
    buffer_gdf = linestrings_gdf.copy()

    # Vérifie si la couche correspond à une entrée dans le dictionnaire de buffers
    if layer_name in buffer_layers:
        buffer_distance = buffer_layers[layer_name].get("distance", 0)
        geometry_type = buffer_layers[layer_name].get("geometry_type", None)

        # Vérifie si le type de géométrie est un LineString
        if geometry_type == "LineString":
            try:
                # Reprojeter en CRS UTM pour appliquer le buffer en mètres
                buffer_gdf = buffer_gdf.to_crs(epsg=32618)  # Adapter l'EPSG selon la région

                # Calculer le centroïde de chaque LineString
                buffer_gdf['geometry'] = buffer_gdf['geometry'].centroid

                # Appliquer le buffer autour des centroïdes
                buffer_gdf['geometry'] = buffer_gdf['geometry'].buffer(buffer_distance)

                # Reprojeter en WGS 84 pour revenir aux coordonnées d'origine
                buffer_gdf = buffer_gdf.to_crs(epsg=4326)

            except Exception as e:
                print(f"Erreur lors de la reprojection ou du buffer : {e}")
        else:
            print(f"Le type de géométrie '{geometry_type}' n'est pas supporté pour cette couche.")
    
    return buffer_gdf

def apply_polygon_buffer(polygon_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict) -> gpd.GeoDataFrame:
    buffer_gdf = polygon_gdf.copy()

    # Vérifie si la couche correspond à une entrée dans le dictionnaire de buffers
    if layer_name in buffer_layers:
        if layer_name == "zones":
            return buffer_gdf
        else:
            buffer_distance = buffer_layers[layer_name].get("distance", 0)
            geometry_type = buffer_layers[layer_name].get("geometry_type", None)

        # Vérifie si le type de géométrie est un Polygon ou MultiPolygon
        if geometry_type in ["Polygon", "MultiPolygon"]:
            try:
                # Reprojeter en CRS UTM pour appliquer le buffer en mètres
                buffer_gdf = buffer_gdf.to_crs(epsg=32618)  # Adapter l'EPSG selon la région

                # Calculer le centroïde de chaque Polygon ou MultiPolygon
                buffer_gdf['geometry'] = buffer_gdf['geometry'].centroid

                # Appliquer le buffer autour des centroïdes
                buffer_gdf['geometry'] = buffer_gdf['geometry'].buffer(buffer_distance)

                # Reprojeter en WGS 84 pour revenir aux coordonnées d'origine
                buffer_gdf = buffer_gdf.to_crs(epsg=4326)

            except Exception as e:
                print(f"Erreur lors de la reprojection ou du buffer : {e}")
        else:
            print(f"Le type de géométrie '{geometry_type}' n'est pas supporté pour cette couche.")
    
    return buffer_gdf


def create_buffers(gdf, buffer_layer):
    unique_id_counter = itertools.count(1)

    for layer_name in buffer_layer:
        geometry_type = buffer_layer[layer_name].get('geometry_type', None)
        buffer_type = buffer_layer[layer_name].get('buffer_type', None)
    if geometry_type == "Point" and buffer_type == "circular":
        buffer_gdfs = {
            f"{layer_name}_buffer": buffer.apply_points_buffer(gdf[layer_name], layer_name, buffer_layer)
            .assign(layer_name=f"{layer_name}_buffer",
                    buffer_id=lambda df: [next(unique_id_counter) for _ in range(len(df))])
                    for layer_name in buffer_layer
    }
    elif geometry_type == "Point" and buffer_type == "grid":
        buffer_gdfs = {
            f"{layer_name}_buffer": grid.apply_points_grid(gdf[layer_name], layer_name, buffer_layer)
            .assign(layer_name=f"{layer_name}_buffer",
                    buffer_id=lambda df: [next(unique_id_counter) for _ in range(len(df))])
                    for layer_name in buffer_layer
    }
    elif geometry_type == "LineString":
        buffer_gdfs = {
            f"{layer_name}_buffer": buffer.apply_linestring_buffer(gdf[layer_name], layer_name, buffer_layer)
            .assign(layer_name=f"{layer_name}_buffer",
                    buffer_id=lambda df: [next(unique_id_counter) for _ in range(len(df))])
                    for layer_name in buffer_layer
    }
        
    elif geometry_type == "Polygon" or geometry_type == "MultiPolygon":
        buffer_gdfs = {
            f"{layer_name}_buffer": buffer.apply_polygon_buffer(gdf[layer_name], layer_name, buffer_layer)
            .assign(layer_name=f"{layer_name}_buffer",
                    buffer_id=lambda df: [next(unique_id_counter) for _ in range(len(df))])
                    for layer_name in buffer_layer
    }

    return buffer_gdfs