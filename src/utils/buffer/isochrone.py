import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import networkx as nx
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point
import osmnx as ox
import networkx as nx


def apply_points_isochrones(points_gdf: gpd.GeoDataFrame, layer_name: str, isochrone_params: dict) -> gpd.GeoDataFrame:
    """
    Applique la génération d'isochrones sur un GeoDataFrame de points selon les paramètres fournis.

    :param points_gdf: GeoDataFrame contenant les points de départ.
    :param layer_name: Nom de la couche à traiter.
    :param isochrone_params: Dictionnaire contenant les paramètres de calcul des isochrones.
    :return: GeoDataFrame avec les isochrones calculés.
    """
    # Vérifie si la couche correspond à une entrée dans le dictionnaire des paramètres
    if layer_name not in isochrone_params:
        print(f"Aucun paramètre trouvé pour la couche '{layer_name}' dans le dictionnaire des isochrones.")
        return points_gdf

    # Extraire les paramètres nécessaires
    walk_time = isochrone_params[layer_name].get("walk_time", None)
    speed = isochrone_params[layer_name].get("speed", None)
    network_buffer = isochrone_params[layer_name].get("distance", None)
    network_type = isochrone_params[layer_name].get("network_type", "walk")

    try:
        # Étape 1 : Calcul des limites de la zone d'étude
        gdf_bounds = points_gdf.total_bounds  # [minx, miny, maxx, maxy]
        lat_min, lon_min, lat_max, lon_max = gdf_bounds[1], gdf_bounds[0], gdf_bounds[3], gdf_bounds[2]

        # Étendre la zone englobante
        lat_min, lat_max = lat_min - network_buffer / 111000, lat_max + network_buffer / 111000
        lon_min, lon_max = (
            lon_min - network_buffer / (111000 * abs(lat_min)), 
            lon_max + network_buffer / (111000 * abs(lat_max))
        )

        # Étape 2 : Charger le réseau routier
        print("Chargement du réseau routier pour la région...")
        G = ox.graph_from_bbox(lat_max, lat_min, lon_max, lon_min, network_type=network_type, simplify=True)

        # Étape 3 : Calcul des isochrones
        walking_meters = walk_time * speed * 1000 / 60  # Temps converti en distance
        isochrones = []

        for _, row in points_gdf.iterrows():
            if row.geometry.geom_type != "Point":
                raise ValueError("Toutes les géométries doivent être de type Point pour les isochrones.")

            lon, lat = row.geometry.x, row.geometry.y
            center_node = ox.nearest_nodes(G, X=lon, Y=lat)
            subgraph = nx.ego_graph(G, center_node, radius=walking_meters, distance='length')

            # Création d'un polygone d'isochrone
            node_points = [Point(data['x'], data['y']) for node, data in subgraph.nodes(data=True)]
            isochrone_polygon = (
                gpd.GeoSeries(node_points).unary_union.convex_hull if node_points else Polygon()
            )

            # Ajouter l'isochrone aux résultats
            isochrones.append({'geometry': isochrone_polygon, **row.drop('geometry')})

        # Étape 4 : Construire le GeoDataFrame final
        isochrone_gdf = gpd.GeoDataFrame(isochrones, crs=points_gdf.crs)

    except Exception as e:
        print(f"Erreur lors de la génération des isochrones pour la couche '{layer_name}': {e}")
        return points_gdf

    return isochrone_gdf