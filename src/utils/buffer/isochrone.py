import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point

def apply_points_isochrones(points_gdf: gpd.GeoDataFrame, layer_name: str, isochrone_params: dict) -> gpd.GeoDataFrame:
    """
    Génère des isochrones pour chaque point en conservant toutes les colonnes d'origine.
    Même logique que apply_points_grid mais pour les isochrones.
    
    Args:
        points_gdf: GeoDataFrame contenant les points avec toutes leurs colonnes
        layer_name: Nom de la couche pour les paramètres
        isochrone_params: Dictionnaire de paramètres des isochrones
        
    Returns:
        GeoDataFrame avec les polygones d'isochrones et toutes les colonnes originales
    """
    # Crée une copie pour ne pas modifier l'original
    isochrone_gdf = points_gdf.copy()
    
    # Vérifie si la couche est dans les paramètres
    if layer_name not in isochrone_params:
        print(f"Aucun paramètre trouvé pour la couche '{layer_name}'")
        return isochrone_gdf
    
    # Extraction des paramètres avec valeurs par défaut
    params = isochrone_params[layer_name]
    walk_time = params.get("walk_time", [5])
    speed = params.get("speed", 4.5)
    network_buffer = params.get("distance", 2000)
    network_type = params.get("network_type", "walk")
    
    # Vérification du type de géométrie
    if not all(isochrone_gdf.geometry.geom_type == "Point"):
        raise ValueError("Toutes les géométries doivent être de type Point.")
    
    try:
        # 1. Téléchargement du réseau
        bbox = isochrone_gdf.total_bounds
        buffer_deg = network_buffer / 111000  # Approximation
        
        G = ox.graph_from_bbox(
            north=bbox[3] + buffer_deg,
            south=bbox[1] - buffer_deg,
            east=bbox[2] + buffer_deg,
            west=bbox[0] - buffer_deg,
            network_type=network_type,
            simplify=True
        )
        G = ox.projection.project_graph(G)
        
        # 2. Calcul du temps de parcours
        meters_per_minute = speed * 1000 / 60
        for _, _, _, data in G.edges(data=True, keys=True):
            data["time"] = data["length"] / meters_per_minute
        
        # 3. Conversion CRS
        isochrone_gdf = isochrone_gdf.to_crs(G.graph["crs"])
        
        # 4. Calcul des isochrones pour chaque point
        polygons = []
        for point in isochrone_gdf.geometry:
            try:
                center_node = ox.distance.nearest_nodes(G, point.x, point.y)
                subgraph = nx.ego_graph(G, center_node, radius=max(walk_time), distance="time")
                
                node_points = [Point((data["x"], data["y"])) 
                             for _, data in subgraph.nodes(data=True)]
                
                if len(node_points) >= 3:
                    poly = gpd.GeoSeries(node_points).unary_union.convex_hull
                    polygons.append(poly)
                else:
                    polygons.append(None)
            except:
                polygons.append(None)
        
        # 5. Mise à jour de la géométrie
        isochrone_gdf['geometry'] = polygons
        
        # 6. Calcul de l'aire
        isochrone_gdf['area_km2'] = isochrone_gdf.geometry.apply(
            lambda x: x.area / 1e6 if x else None
        )
        
        # 7. Ajout des métadonnées
        isochrone_gdf['buffer_type'] = 'isochrone'
        isochrone_gdf['buffer_layer'] = layer_name
        
    except Exception as e:
        print(f"Erreur lors du calcul des isochrones: {e}")
        return points_gdf
    
    return isochrone_gdf