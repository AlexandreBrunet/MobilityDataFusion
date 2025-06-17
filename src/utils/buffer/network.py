import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point
import numpy as np

def apply_points_network_buffer(points_gdf: gpd.GeoDataFrame, layer_name: str, buffer_params: dict) -> gpd.GeoDataFrame:
    """
    Génère des zones tampon réseau pour chaque point en conservant toutes les colonnes d'origine.
    
    Args:
        points_gdf: GeoDataFrame contenant les points
        layer_name: Nom de la couche pour les paramètres
        buffer_params: Dictionnaire de paramètres
        
    Returns:
        GeoDataFrame avec les polygones de buffer réseau
    """
    buffer_gdf = points_gdf.copy()
    
    if layer_name not in buffer_params:
        print(f"Aucun paramètre trouvé pour la couche '{layer_name}'")
        return buffer_gdf
    
    params = buffer_params[layer_name]
    distance = params.get("distance", 500)  # distance en mètres
    network_type = params.get("network_type", "walk")
    
    if not all(buffer_gdf.geometry.geom_type == "Point"):
        raise ValueError("Toutes les géométries doivent être de type Point.")
    
    try:
        # 1. Téléchargement du réseau
        bbox = buffer_gdf.total_bounds
        buffer_deg = distance * 2 / 111320  # Buffer large pour couvrir
        
        G = ox.graph_from_bbox(
            north=bbox[3] + buffer_deg,
            south=bbox[1] - buffer_deg,
            east=bbox[2] + buffer_deg,
            west=bbox[0] - buffer_deg,
            network_type=network_type,
            simplify=True,
            truncate_by_edge=True
        )
        
        # 2. Projection en UTM pour Montréal
        utm_crs = "EPSG:32618"
        G = ox.project_graph(G, to_crs=utm_crs)
        
        # 3. Conversion des points en UTM
        buffer_gdf = buffer_gdf.to_crs(utm_crs)
        
        # 4. Calcul des buffers réseau
        polygons = []
        for point in buffer_gdf.geometry:
            try:
                center_node = ox.distance.nearest_nodes(G, point.x, point.y)
                subgraph = nx.ego_graph(G, center_node, radius=distance, distance="length")
                
                if subgraph.number_of_nodes() == 0:
                    polygons.append(None)
                    continue
                    
                # Créer un polygone convexe à partir des nœuds
                node_points = [Point((data["x"], data["y"])) for _, data in subgraph.nodes(data=True)]
                poly = gpd.GeoSeries(node_points).unary_union.convex_hull
                polygons.append(poly)
            except Exception as e:
                print(f"Erreur lors du calcul du buffer: {e}")
                polygons.append(None)
        
        # 5. Mise à jour de la géométrie
        buffer_gdf['geometry'] = polygons
        buffer_gdf = buffer_gdf.to_crs(epsg=4326)
        
        # 6. Calcul de l'aire
        buffer_gdf['area_km2'] = buffer_gdf.geometry.to_crs(utm_crs).area / 1e6
        
        # Métadonnées
        buffer_gdf['buffer_type'] = 'network_buffer'
        buffer_gdf['buffer_layer'] = layer_name
        
    except Exception as e:
        print(f"Erreur majeure: {str(e)}")
        return points_gdf
    
    return buffer_gdf


#TODO Add this logic too 
# def apply_lines_network_buffer(lines_gdf: gpd.GeoDataFrame, layer_name: str, buffer_params: dict) -> gpd.GeoDataFrame:
#     """
#     Génère des zones tampon réseau pour chaque ligne (à partir de points équidistants).
#     """
#     buffer_gdf = lines_gdf.copy()
    
#     if layer_name not in buffer_params:
#         print(f"Aucun paramètre trouvé pour la couche '{layer_name}'")
#         return buffer_gdf
    
#     params = buffer_params[layer_name]
#     distance = params.get("distance", 500)
#     network_type = params.get("network_type", "walk")
#     sample_distance = params.get("sample_distance", 50)  # Distance entre les points d'échantillonnage
    
#     if not all(buffer_gdf.geometry.geom_type == "LineString"):
#         raise ValueError("Toutes les géométries doivent être de type LineString.")
    
#     try:
#         # 1. Échantillonnage des points le long des lignes
#         buffer_gdf['sample_points'] = buffer_gdf.geometry.apply(
#             lambda geom: [Point(geom.interpolate(d).coords[0]) 
#                          for d in np.arange(0, geom.length, sample_distance)]
#         )
        
#         # 2. Explosion des points
#         buffer_gdf = buffer_gdf.explode('sample_points')
#         buffer_gdf['geometry'] = buffer_gdf['sample_points'].apply(lambda x: Point(x))
#         buffer_gdf = buffer_gdf.drop(columns=['sample_points'])
        
#         # 3. Application du buffer réseau sur les points
#         buffer_gdf = apply_points_network_buffer(buffer_gdf, layer_name, buffer_params)
        
#         # 4. Dissoudre les buffers par entité originale
#         if 'buffer_id' in buffer_gdf.columns:
#             buffer_gdf = buffer_gdf.dissolve(by='buffer_id').reset_index()
        
#     except Exception as e:
#         print(f"Erreur majeure: {str(e)}")
#         return lines_gdf
    
#     return buffer_gdf

def apply_lines_network_buffer(lines_gdf: gpd.GeoDataFrame, layer_name: str, buffer_params: dict) -> gpd.GeoDataFrame:
    """
    Génère un buffer réseau autour du centroïde de chaque ligne.
    """
    buffer_gdf = lines_gdf.copy()

    if layer_name not in buffer_params:
        print(f"Aucun paramètre trouvé pour la couche '{layer_name}'")
        return buffer_gdf

    params = buffer_params[layer_name]
    # Ici on utilise une distance réseau, pas besoin de vitesse
    network_type = params.get("network_type", "walk")
    distance = params.get("distance", 500)  # Distance réseau

    if not all(buffer_gdf.geometry.geom_type == "LineString"):
        raise ValueError("Toutes les géométries doivent être de type LineString.")

    try:
        # 1. Calculer le centroïde de chaque ligne
        buffer_gdf["geometry"] = buffer_gdf.geometry.centroid

        # 2. Appliquer la fonction de buffer réseau sur ces points-centroïdes
        buffer_gdf = apply_points_network_buffer(buffer_gdf, layer_name, buffer_params)

        # 3. Dissoudre les buffers si identifiants disponibles
        if "buffer_id" in buffer_gdf.columns:
            buffer_gdf = buffer_gdf.dissolve(by="buffer_id").reset_index()

    except Exception as e:
        print(f"Erreur majeure : {str(e)}")
        return lines_gdf

    return buffer_gdf


def apply_polygons_network_buffer(polygons_gdf: gpd.GeoDataFrame, layer_name: str, buffer_params: dict) -> gpd.GeoDataFrame:
    """
    Génère des zones tampon réseau pour chaque polygone (à partir du centroïde).
    """
    buffer_gdf = polygons_gdf.copy()
    
    if layer_name not in buffer_params:
        print(f"Aucun paramètre trouvé pour la couche '{layer_name}'")
        return buffer_gdf
    
    if not all(buffer_gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])):
        raise ValueError("Toutes les géométries doivent être de type Polygon ou MultiPolygon.")
    
    try:
        # 1. Utiliser les centroïdes comme points
        buffer_gdf['geometry'] = buffer_gdf.geometry.centroid
        
        # 2. Appliquer le buffer réseau sur les points
        buffer_gdf = apply_points_network_buffer(buffer_gdf, layer_name, buffer_params)
        
    except Exception as e:
        print(f"Erreur majeure: {str(e)}")
        return polygons_gdf
    
    return buffer_gdf