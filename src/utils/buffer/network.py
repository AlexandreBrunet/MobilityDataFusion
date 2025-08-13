import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
from multiprocessing import Pool, cpu_count, set_start_method
from tqdm import tqdm
import numpy as np
import os
import logging
from typing import Dict, Tuple

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(processName)s - %(message)s")
logger = logging.getLogger(__name__)

# Set multiprocessing start method to 'spawn' for macOS compatibility
try:
    set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set

def create_network_buffer(args: Tuple[int, int, float, float, float, bool, str, nx.MultiDiGraph]) -> Tuple[int, Polygon]:
    """
    Create a network buffer for a single point using a provided graph.
    
    Args:
        args: Tuple of (idx, nearest_node, x, y, distance, remove_holes, crs, G).
    
    Returns:
        Tuple of (index, buffer geometry in WGS84).
    """
    idx, nearest_node, x, y, distance, remove_holes, crs, G = args
    try:
        logger.debug(f"Point {idx}: Processing nearest node {nearest_node}")

        # Calculate reachable nodes within distance
        lengths = nx.single_source_dijkstra_path_length(G, nearest_node, weight='length', cutoff=distance)
        reachable_nodes = list(lengths.keys())
        logger.debug(f"Point {idx}: Found {len(reachable_nodes)} reachable nodes")

        # Combine edge geometries
        edge_geoms = [
            data['geometry'] for u, v, data in G.edges(data=True)
            if u in reachable_nodes and v in reachable_nodes and 'geometry' in data
        ]
        logger.debug(f"Point {idx}: Found {len(edge_geoms)} edge geometries")

        if not edge_geoms:
            logger.warning(f"No edge geometries for point {idx}, using circular buffer")
            point_utm = Point(x, y)
            buffer = point_utm.buffer(distance)  # Fallback to circular buffer
        else:
            buffer = unary_union(edge_geoms).buffer(10)  # 10m buffer around edges

        # Remove holes if requested
        if remove_holes and buffer.geom_type in ['Polygon', 'MultiPolygon']:
            if buffer.geom_type == 'Polygon':
                buffer = Polygon(buffer.exterior)
            elif buffer.geom_type == 'MultiPolygon':
                buffer = MultiPolygon([Polygon(poly.exterior) for poly in buffer.geoms])
            logger.debug(f"Point {idx}: Removed holes from geometry")

        if not buffer.is_valid:
            buffer = buffer.buffer(0)
            logger.debug(f"Point {idx}: Fixed invalid geometry")

        # Convert to WGS84
        buffer_wgs84 = gpd.GeoSeries([buffer], crs=crs).to_crs('EPSG:4326').iloc[0]
        logger.debug(f"Point {idx}: Converted to WGS84")
        return idx, buffer_wgs84

    except Exception as e:
        logger.error(f"Error processing point {idx}: {e}")
        return idx, None

def apply_points_network_buffer(points_gdf: gpd.GeoDataFrame, layer_name: str, buffer_params: Dict) -> gpd.GeoDataFrame:
    """
    Generates network-based buffers for points, preserving original columns, using a pre-downloaded OSM XML file.

    Args:
        points_gdf: GeoDataFrame with Point geometries.
        layer_name: Name of the layer for buffer parameters.
        buffer_params: Dictionary of buffer parameters (e.g., distance, network_type, osm_file, use_convex_hull).

    Returns:
        GeoDataFrame with network buffer polygons.
    """
    if points_gdf.empty:
        logger.warning(f"Empty GeoDataFrame for {layer_name}, returning unchanged")
        return points_gdf.copy()

    if not all(points_gdf.geometry.geom_type == "Point"):
        logger.error(f"Non-Point geometries found in {layer_name}")
        raise ValueError("All geometries must be Points")

    if layer_name not in buffer_params:
        logger.warning(f"No buffer parameters for {layer_name}, returning unchanged")
        return points_gdf.copy()

    params = buffer_params[layer_name]
    distance = params.get("distance", 500)  # meters
    network_type = params.get("network_type", "walk")
    use_enveloppe = params.get("use_envelope", True)

    osm_filename = params.get("osm_file")
    if not osm_filename:
        raise ValueError(f"Missing 'osm_file' name in buffer_params for layer '{layer_name}'")
    
    osm_file = os.path.join("./utils/buffer/networks", osm_filename)

    if distance <= 0:
        logger.warning(f"Invalid buffer distance {distance} for {layer_name}, returning unchanged")
        return points_gdf.copy()

    if not osm_file:
        logger.error(f"No OSM file specified for {layer_name}")
        raise ValueError(f"OSM file must be specified in buffer_params for {layer_name}")

    osm_file_path = os.path.abspath(osm_file)
    if not os.path.exists(osm_file_path):
        logger.error(f"OSM file not found: {osm_file_path}")
        raise FileNotFoundError(f"OSM file not found: {osm_file_path}")

    logger.info(f"Creating network buffers for {layer_name}: distance={distance}m, network_type={network_type}, "
                f"use_convex_hull={use_convex_hull}, osm_file={osm_file_path}")

    try:
        # 1. Load street network from OSM XML file
        logger.info(f"Loading OSM file: {osm_file_path}")
        G = ox.graph_from_xml(osm_file_path, simplify=True)
        logger.info(f"Loaded network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        if G.number_of_nodes() == 0:
            logger.error(f"No nodes in network for {layer_name}, returning original GDF")
            return points_gdf.copy()

        # 2. Project to UTM
        G = ox.project_graph(G, to_crs="EPSG:32618")  # UTM Zone 18N for Montreal
        points_utm = points_gdf.to_crs("EPSG:32618").geometry
        utm_crs = G.graph['crs']
        logger.debug(f"Projected to UTM CRS: {utm_crs}")

        # 3. Find nearest nodes
        X = np.array([p.x for p in points_utm])
        Y = np.array([p.y for p in points_utm])
        nearest_nodes = ox.distance.nearest_nodes(G, X, Y)
        logger.debug(f"Found nearest nodes for {len(points_gdf)} points")

        # 4. Process buffers with multiprocessing
        num_cores = min(cpu_count() - 1, 4)
        logger.info(f"Using {num_cores} CPU cores for processing")
        chunk_size = 50
        buffer_gdf = points_gdf.copy()

        for start in range(0, len(points_gdf), chunk_size):
            end = min(start + chunk_size, len(points_gdf))
            chunk_utm = points_utm[start:end]
            chunk_nodes = nearest_nodes[start:end]
            logger.info(f"Processing chunk {start//chunk_size + 1} ({start} to {end})")

            # Prepare arguments for workers
            worker_args = [
                (i + start, chunk_nodes[i], chunk_utm.iloc[i].x, chunk_utm.iloc[i].y, distance, use_convex_hull, utm_crs, G)
                for i in range(len(chunk_utm))
            ]

            try:
                with Pool(num_cores) as pool:
                    results = list(tqdm(
                        pool.imap(create_network_buffer, worker_args),
                        total=len(chunk_utm),
                        desc=f"Chunk {start//chunk_size + 1}"
                    ))
            except Exception as e:
                logger.warning(f"Multiprocessing failed for chunk {start//chunk_size + 1}: {e}. Falling back to single-threaded")
                results = [create_network_buffer(args) for args in tqdm(worker_args, desc=f"Chunk {start//chunk_size + 1}")]

            # Update geometries
            valid_buffers = 0
            for idx, buffer in results:
                if buffer is not None:
                    buffer_gdf.at[idx, 'geometry'] = buffer
                    valid_buffers += 1
            logger.info(f"Chunk {start//chunk_size + 1}: Generated {valid_buffers}/{len(chunk_utm)} valid buffers")

        # 5. Filter valid geometries and add metadata
        buffer_gdf = buffer_gdf[buffer_gdf.geometry.notnull()]
        logger.info(f"Generated {len(buffer_gdf)}/{len(points_gdf)} valid buffer polygons")

        if not buffer_gdf.empty:
            buffer_gdf['area_km2'] = buffer_gdf.geometry.to_crs("EPSG:32618").area / 1_000_000
            buffer_gdf['buffer_type'] = 'network_buffer'
            buffer_gdf['buffer_layer'] = layer_name
        else:
            logger.warning(f"No valid buffers created for {layer_name}, returning original GDF")
            return points_gdf.copy()

        return buffer_gdf

    except Exception as e:
        logger.error(f"Major error in network buffering for {layer_name}: {e}")
        return points_gdf.copy()

def apply_lines_network_buffer(lines_gdf: gpd.GeoDataFrame, layer_name: str, buffer_params: dict) -> gpd.GeoDataFrame:
    """
    Génère un buffer réseau autour du centroïde de chaque ligne.
    """
    if lines_gdf.empty:
        print(f"La couche '{layer_name}' est vide.")
        return lines_gdf.copy()

    if layer_name not in buffer_params:
        print(f"Aucun paramètre trouvé pour la couche '{layer_name}'")
        return lines_gdf.copy()

    if not all(lines_gdf.geometry.geom_type == "LineString"):
        raise ValueError("Toutes les géométries doivent être de type LineString.")

    try:
        # Calcul du centroïde de chaque ligne
        centroids_gdf = lines_gdf.copy()
        centroids_gdf["geometry"] = centroids_gdf.geometry.centroid

        # Application du buffer réseau comme pour des points
        buffer_gdf = apply_points_network_buffer(centroids_gdf, layer_name, buffer_params)

        # Dissolution facultative (si plusieurs points par entité initiale)
        if "buffer_id" in buffer_gdf.columns:
            buffer_gdf = buffer_gdf.dissolve(by="buffer_id").reset_index()

        return buffer_gdf

    except Exception as e:
        print(f"Erreur dans apply_lines_network_buffer pour '{layer_name}': {e}")
        return lines_gdf.copy()

def apply_polygons_network_buffer(polygons_gdf: gpd.GeoDataFrame, layer_name: str, buffer_params: dict) -> gpd.GeoDataFrame:
    """
    Génère un buffer réseau à partir du centroïde de chaque polygone.
    """
    if polygons_gdf.empty:
        print(f"La couche '{layer_name}' est vide.")
        return polygons_gdf.copy()

    if layer_name not in buffer_params:
        print(f"Aucun paramètre trouvé pour la couche '{layer_name}'")
        return polygons_gdf.copy()

    if not polygons_gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        raise ValueError("Toutes les géométries doivent être de type Polygon ou MultiPolygon.")

    try:
        centroids_gdf = polygons_gdf.copy()
        centroids_gdf["geometry"] = centroids_gdf.geometry.centroid

        buffer_gdf = apply_points_network_buffer(centroids_gdf, layer_name, buffer_params)

        return buffer_gdf

    except Exception as e:
        print(f"Erreur dans apply_polygons_network_buffer pour '{layer_name}': {e}")
        return polygons_gdf.copy()


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