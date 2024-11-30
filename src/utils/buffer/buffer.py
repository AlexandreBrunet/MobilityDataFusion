import geopandas as gpd
import utils.utils as utils
import networkx as nx
import osmnx as ox
from shapely.geometry import MultiPolygon, Polygon
import itertools

def apply_point_buffer(points_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict) -> gpd.GeoDataFrame:
    if not layer_name in buffer_layers:
        raise ValueError(f"La couche '{layer_name}' n'est pas définie dans buffer_layers.")
    
    if not points_gdf.geometry.geom_type.eq('Point').all():
        raise TypeError("Le GeoDataFrame doit contenir uniquement des géométries de type 'Point'.")
    
    buffer_distance = buffer_layers[layer_name]
    buffer_gdf = points_gdf.copy()
    
    # Reprojection dynamique pour appliquer le buffer en mètres
    utm_crs = buffer_gdf.estimate_utm_crs()  # Implémente une fonction pour détecter l'UTM
    buffer_gdf = buffer_gdf.to_crs(utm_crs)
    
    buffer_gdf['geometry'] = buffer_gdf['geometry'].buffer(buffer_distance)
    
    # Reprojeter en WGS 84 (EPSG:4326) pour la sortie
    buffer_gdf = buffer_gdf.to_crs(epsg=4326)
    
    # Ajouter des métadonnées
    buffer_gdf['buffer_layer'] = layer_name
    buffer_gdf['buffer_distance_m'] = buffer_distance
    
    return buffer_gdf

def apply_line_buffer(lines_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict) -> gpd.GeoDataFrame:
    if not layer_name in buffer_layers:
        raise ValueError(f"La couche '{layer_name}' n'est pas définie dans buffer_layers.")
    
    if not lines_gdf.geometry.geom_type.eq('LineString').all():
        raise TypeError("Le GeoDataFrame doit contenir uniquement des géométries de type 'LineString'.")
    
    buffer_distance = buffer_layers[layer_name]
    buffer_gdf = lines_gdf.copy()
    
    # Reprojection dynamique pour appliquer le buffer en mètres
    utm_crs = buffer_gdf.estimate_utm_crs()  # Implémente une fonction pour détecter l'UTM
    buffer_gdf = buffer_gdf.to_crs(utm_crs)
    
    buffer_gdf['geometry'] = buffer_gdf['geometry'].buffer(buffer_distance)
    
    # Reprojeter en WGS 84 (EPSG:4326) pour la sortie
    buffer_gdf = buffer_gdf.to_crs(epsg=4326)
    
    # Ajouter des métadonnées
    buffer_gdf['buffer_layer'] = layer_name
    buffer_gdf['buffer_distance_m'] = buffer_distance
    
    return buffer_gdf


def apply_polygon_buffer(polygons_gdf: gpd.GeoDataFrame, layer_name: str, buffer_layers: dict) -> gpd.GeoDataFrame:
    if not layer_name in buffer_layers:
        raise ValueError(f"La couche '{layer_name}' n'est pas définie dans buffer_layers.")
    
    if not polygons_gdf.geometry.geom_type.eq('Polygon').all():
        raise TypeError("Le GeoDataFrame doit contenir uniquement des géométries de type 'Polygon'.")
    
    buffer_distance = buffer_layers[layer_name]
    buffer_gdf = polygons_gdf.copy()
    
    # Reprojection dynamique pour appliquer le buffer en mètres
    utm_crs = buffer_gdf.estimate_utm_crs()  # Implémente une fonction pour détecter l'UTM
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

def create_buffers(points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs, buffer_layers, buffer_type):
    unique_id_counter = itertools.count(1)
    
    buffer_gdfs = {}
    
    # Combiner tous les GeoDataFrames en un seul dictionnaire
    all_gdfs = {
        'Point': points_gdfs,
        'Polygon': polygons_gdfs,
        'MultiPolygon': multipolygons_gdfs,
        'LineString': linestrings_gdfs
    }
    
    for layer_name, buffer_distance in buffer_layers.items():
        # Identifier le type de géométrie correspondant pour chaque couche
        layer_gdf = None
        for geom_type, gdf in all_gdfs.items():
            if layer_name in gdf:
                layer_gdf = gdf[layer_name]
                layer_geom_type = geom_type
                break
        
        if layer_gdf is None:
            raise ValueError(f"La couche '{layer_name}' n'est pas définie dans les géométries.")
        
        # Vérifier la validité des géométries avant de créer le buffer
        if not layer_gdf.is_valid.all():
            raise ValueError(f"Des géométries invalides sont présentes dans la couche '{layer_name}'.")

        # Appliquer le buffer en fonction du type de géométrie
        if layer_geom_type == 'Point':
            apply_buffer_func = apply_point_buffer
        elif layer_geom_type == 'LineString':
            apply_buffer_func = apply_line_buffer
        elif layer_geom_type == 'Polygon' or layer_geom_type == 'MultiPolygon':
            apply_buffer_func = apply_polygon_buffer
        else:
            raise TypeError(f"Le type de géométrie '{layer_geom_type}' pour la couche '{layer_name}' est incompatible.")

        # Appliquer le buffer selon le type spécifié
        if buffer_type == "apply_buffer":
            buffer_gdfs[f"{layer_name}_buffer"] = apply_buffer_func(
                layer_gdf, 
                layer_name, 
                buffer_layers
            ).assign(
                layer_name=f"{layer_name}_buffer",
                buffer_id=lambda df: [next(unique_id_counter) for _ in range(len(df))]
            )
        elif buffer_type == "apply_isochrones":
            buffer_gdfs[f"{layer_name}_isochrones"] = apply_isochrones(
                layer_gdf, 
                layer_name, 
                buffer_layers
            ).assign(
                layer_name=f"{layer_name}_isochrones",
                buffer_id=lambda df: [next(unique_id_counter) for _ in range(len(df))]
            )
        else:
            raise ValueError(f"Le type de buffer '{buffer_type}' n'est pas valide.")
    
    return buffer_gdfs