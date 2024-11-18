import geopandas as gpd
import osmnx as ox
import time

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


def apply_network_buffer(points_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict, network_type='walk') -> gpd.GeoDataFrame:
    """
    Applique un buffer basé sur une distance réseau autour des points dans un GeoDataFrame pour une couche spécifique.
    
    Paramètres :
    - points_gdf : GeoDataFrame contenant des points.
    - layer_name : nom de la couche pour laquelle appliquer le buffer.
    - buffer_layers : dictionnaire où les clés sont les noms de couche et les valeurs sont les distances de buffer en mètres.
    - network_type : type de réseau pour les calculs (ex. 'walk', 'drive', 'bike'). Défaut : 'walk'.
    
    Retourne :
    - buffer_gdf : GeoDataFrame contenant des buffers réseau si la couche correspond.
    """
    start_time = time.time()
    
    if layer_name not in buffer_layers:
        return points_gdf  # Retourner inchangé si aucun buffer n'est défini

    buffer_distance = buffer_layers[layer_name]
    buffer_polygons = []

    # Charger le réseau basé sur la zone des points
    bounds = points_gdf.total_bounds  # xmin, ymin, xmax, ymax
    graph = ox.graph_from_bbox(bounds[3], bounds[1], bounds[2], bounds[0], network_type=network_type)

    # Calculer les buffers pour chaque point
    for point in points_gdf.geometry:
        if point is None or point.is_empty:
            continue  # Ignorer les géométries manquantes ou vides

        # Trouver le nœud le plus proche dans le graphe
        nearest_node = ox.distance.nearest_nodes(graph, point.x, point.y)

        # Tronquer le graphe à la distance donnée
        subgraph = ox.truncate.truncate_graph_dist(graph, source_node=nearest_node, max_dist=buffer_distance)

        # Extraire l'enveloppe des nœuds accessibles pour former le buffer
        nodes, _ = ox.graph_to_gdfs(subgraph)
        buffer_polygon = nodes.unary_union.convex_hull
        buffer_polygons.append(buffer_polygon)

    # Créer un GeoDataFrame des buffers
    buffer_gdf = gpd.GeoDataFrame(
        points_gdf,
        geometry=gpd.GeoSeries(buffer_polygons, crs=points_gdf.crs),
    )

    elapsed_time = time.time() - start_time
    print(f"Temps d'exécution pour '{layer_name}': {elapsed_time:.2f} secondes.")

    return buffer_gdf


########################################################
from pyrosm import OSM
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Polygon
from multiprocessing import Pool

def process_point_with_local_osm(args):
    point, osm_data, buffer_distance = args
    if point is None or point.is_empty:
        return None

    # Charger un graphe localement basé sur les limites du point
    bounds = point.buffer(buffer_distance).bounds  # xmin, ymin, xmax, ymax
    graph = osm_data.get_network(bounds, network_type="walking")

    if graph is None:
        return None  # Aucun réseau disponible pour cette zone

    # Trouver le nœud le plus proche dans le graphe
    nearest_node = ox.distance.nearest_nodes(graph, point.x, point.y)

    # Tronquer le graphe à la distance donnée
    subgraph = ox.truncate.truncate_graph_dist(graph, source_node=nearest_node, max_dist=buffer_distance)

    # Créer le buffer à partir des nœuds accessibles
    nodes, _ = ox.graph_to_gdfs(subgraph)
    return nodes.unary_union.convex_hull if not nodes.empty else None

def apply_network_buffer_with_local_osm(points_gdf, layer_name, buffer_layers, osm_pbf_path='/Users/alexandrebrunet/Desktop/Memoire/prog/MobilityDataFusion/src/utils/buffer/quebec-latest.osm.pbf', network_type="walking"):
    """
    Applique un buffer réseau localisé autour des points à partir d'un fichier OSM local.

    Paramètres :
    - points_gdf : GeoDataFrame contenant des points.
    - layer_name : nom de la couche pour laquelle appliquer le buffer.
    - buffer_layers : dictionnaire où les clés sont les noms de couche et les valeurs sont les distances de buffer en mètres.
    - osm_pbf_path : chemin vers le fichier OSM PBF local.
    - network_type : type de réseau à charger (walking, driving, cycling, etc.). Défaut : "walking".

    Retourne :
    - buffer_gdf : GeoDataFrame contenant les buffers.
    """
    if layer_name not in buffer_layers:
        return points_gdf  # Retourner inchangé si aucun buffer n'est défini

    buffer_distance = buffer_layers[layer_name]

    # Charger les données OSM localement
    osm_data = OSM(osm_pbf_path)

    # Préparer les arguments pour chaque point
    args_list = [(point, osm_data, buffer_distance) for point in points_gdf.geometry]

    # Parallélisation
    with Pool() as pool:
        buffer_polygons = pool.map(process_point_with_local_osm, args_list)

    # Créer un GeoDataFrame
    buffer_gdf = gpd.GeoDataFrame(
        points_gdf,
        geometry=gpd.GeoSeries(buffer_polygons, crs=points_gdf.crs),
    )

    return buffer_gdf
