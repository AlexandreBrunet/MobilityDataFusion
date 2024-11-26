import geopandas as gpd
import utils.utils as utils
import networkx as nx
import osmnx as ox
from shapely.geometry import MultiPolygon, Polygon

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

def apply_isochrones(points_gdf: gpd.GeoDataFrame, layer_name: str, isochrone_layers: dict) -> gpd.GeoDataFrame:
    """
    Génère des isochrones (zones accessibles) autour de points pour une couche spécifique.

    Paramètres :
    - points_gdf : GeoDataFrame contenant des points.
    - layer_name : nom de la couche pour laquelle générer les isochrones.
    - isochrone_layers : dictionnaire où les clés sont les noms de couche et les valeurs sont les distances (en mètres).

    Retourne :
    - isochrone_gdf : GeoDataFrame contenant les isochrones sous forme de polygones.
    """
    if layer_name not in isochrone_layers:
        raise ValueError(f"La couche '{layer_name}' n'est pas définie dans isochrone_layers.")
    
    if not points_gdf.geometry.geom_type.eq('Point').all():
        raise TypeError("Le GeoDataFrame doit contenir uniquement des géométries de type 'Point'.")

    travel_distance = isochrone_layers[layer_name]
    isochrones = []
    isochrone_metadata = []

    for idx, point in points_gdf.iterrows():
        point_geom = point.geometry

        # Charger le graphe routier autour de chaque point
        G = ox.graph_from_point((point_geom.y, point_geom.x), dist=travel_distance, network_type="walk")

        # Trouver le nœud le plus proche dans le graphe
        node = ox.nearest_nodes(G, point_geom.x, point_geom.y)

        # Calculer les distances via le réseau
        subgraph = nx.ego_graph(G, node, radius=travel_distance, distance="length")

        # Extraire les arêtes du sous-graphe pour construire le polygone
        nodes, edges = ox.graph_to_gdfs(subgraph, nodes=True, edges=True)
        isochrone_polygon = edges.unary_union.convex_hull

        # Ajouter le polygone ou None si invalide
        if isinstance(isochrone_polygon, (Polygon, MultiPolygon)):
            isochrones.append(isochrone_polygon)
            isochrone_metadata.append({"isochrone_id": idx, "layer_name": layer_name, "travel_distance": travel_distance})
        else:
            isochrones.append(None)
            isochrone_metadata.append({"isochrone_id": idx, "layer_name": layer_name, "travel_distance": travel_distance})
    
    # Créer un GeoDataFrame avec les isochrones et les métadonnées
    isochrone_gdf = gpd.GeoDataFrame(
        isochrone_metadata,
        geometry=isochrones,
        crs=points_gdf.crs
    )
    
    return isochrone_gdf