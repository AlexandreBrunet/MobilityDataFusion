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
    travel_time = params.get("travel_time", [5])
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
        print(f"Projection du graphe : {G.graph['crs']}")
        
        # 2. Calcul du temps de parcours
        meters_per_minute = speed * 1000 / 60
        for _, _, _, data in G.edges(data=True, keys=True):
            data["time"] = data["length"] / meters_per_minute
        
        # 3. Conversion CRS pour les calculs
        isochrone_gdf = isochrone_gdf.to_crs(G.graph["crs"])
        print(f"CRS de isochrone_gdf après projection : {isochrone_gdf.crs}")
        
        # 4. Calcul des isochrones pour chaque point
        polygons = []
        for idx, point in enumerate(isochrone_gdf.geometry):
            try:
                center_node = ox.distance.nearest_nodes(G, point.x, point.y)
                print(f"Point {idx}: Nœud le plus proche trouvé: {center_node}")
                
                subgraph = nx.ego_graph(G, center_node, radius=max(travel_time), distance="time")
                print(f"Point {idx}: Sous-graphe généré avec {subgraph.number_of_nodes()} nœuds")
                
                node_points = [Point((data["x"], data["y"])) 
                             for _, data in subgraph.nodes(data=True)]
                
                print(f"Point {idx}: {len(node_points)} points de nœuds générés")
                
                if len(node_points) >= 3:
                    poly = gpd.GeoSeries(node_points).unary_union.convex_hull
                    print(f"Point {idx}: Polygone généré: {poly}")
                    polygons.append(poly)
                else:
                    print(f"Point {idx}: Pas assez de points pour générer un polygone")
                    polygons.append(None)
            except Exception as e:
                print(f"Point {idx}: Erreur lors du calcul de l'isochrone: {e}")
                polygons.append(None)
        
        # 5. Mise à jour de la géométrie
        isochrone_gdf['geometry'] = polygons
        print(f"Géométries générées: {isochrone_gdf['geometry'].notnull().sum()} isochrones valides sur {len(isochrone_gdf)} points")
        
        # 6. Reprojeter en WGS84 (EPSG:4326) pour la visualisation
        isochrone_gdf = isochrone_gdf.to_crs(epsg=4326)
        print(f"CRS après reprojection finale : {isochrone_gdf.crs}")
        
        # 7. Calcul de l'aire (après reprojection, pour éviter des biais dans les unités)
        isochrone_gdf['area_km2'] = isochrone_gdf.geometry.apply(
            lambda x: x.area / 1e6 if x else None
        )
        
        # 8. Ajout des métadonnées
        isochrone_gdf['buffer_type'] = 'isochrone'
        isochrone_gdf['buffer_layer'] = layer_name
        
    except Exception as e:
        print(f"Erreur lors du calcul des isochrones: {e}")
        return points_gdf
    
    return isochrone_gdf