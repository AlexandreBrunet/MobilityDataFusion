import geopandas as gpd
import pandas as pd
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

# Configure logging - ONLY INFO level for performance
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# Set multiprocessing start method to 'spawn' for macOS compatibility
try:
    set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set

# Global variable to hold the graph (avoids serialization overhead)
_GRAPH = None

def _init_worker(graph_data):
    """Initialize worker process with graph data."""
    global _GRAPH
    _GRAPH = graph_data

def create_network_buffer(args: Tuple[int, int, float, float, float, bool, str]) -> Tuple[int, Polygon]:
    """
    Create a network buffer for a single point using the global graph.
    
    Args:
        args: Tuple of (idx, nearest_node, x, y, distance, remove_holes, crs).
    
    Returns:
        Tuple of (index, buffer geometry in WGS84).
    """
    global _GRAPH
    idx, nearest_node, x, y, distance, remove_holes, crs = args
    
    try:
        # Calculate reachable nodes within distance
        lengths = nx.single_source_dijkstra_path_length(_GRAPH, nearest_node, weight='length', cutoff=distance)
        reachable_nodes = set(lengths.keys())

        # Get subgraph with only reachable nodes - MUCH faster than iterating all edges
        subgraph = _GRAPH.subgraph(reachable_nodes)
        
        # Extract edge geometries from subgraph
        edge_geoms = [
            data['geometry'] for u, v, data in subgraph.edges(data=True)
            if 'geometry' in data
        ]

        if not edge_geoms:
            # Fallback to circular buffer
            point_utm = Point(x, y)
            buffer = point_utm.buffer(distance)
        else:
            # Optimization: For large distances, simplify before union
            if len(edge_geoms) > 1000:
                # Simplify individual geometries to reduce complexity
                edge_geoms = [geom.simplify(5) for geom in edge_geoms]
            
            # Union and buffer
            network_union = unary_union(edge_geoms)
            buffer = network_union.buffer(10).simplify(2)  # Simplify final result

        # Remove holes if requested
        if remove_holes and buffer.geom_type in ['Polygon', 'MultiPolygon']:
            if buffer.geom_type == 'Polygon':
                buffer = Polygon(buffer.exterior)
            elif buffer.geom_type == 'MultiPolygon':
                buffer = MultiPolygon([Polygon(poly.exterior) for poly in buffer.geoms])

        if not buffer.is_valid:
            buffer = buffer.buffer(0)

        # Convert to WGS84
        buffer_wgs84 = gpd.GeoSeries([buffer], crs=crs).to_crs('EPSG:4326').iloc[0]
        return idx, buffer_wgs84

    except Exception as e:
        logger.error(f"Error processing point {idx}: {e}")
        return idx, None

def apply_points_network_buffer(points_gdf: gpd.GeoDataFrame, layer_name: str, buffer_params: Dict) -> gpd.GeoDataFrame:
    """
    Generates network-based buffers for points with performance optimizations.

    Args:
        points_gdf: GeoDataFrame with Point geometries.
        layer_name: Name of the layer for buffer parameters.
        buffer_params: Dictionary of buffer parameters (e.g., distance, network_type, osm_file, use_envelope).

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
    use_envelope = params.get("use_envelope", True)

    osm_filename = params.get("osm_file")
    if not osm_filename:
        raise ValueError(f"Missing 'osm_file' name in buffer_params for layer '{layer_name}'")
    
    osm_file = os.path.join("./utils/buffer/networks", osm_filename)

    if distance <= 0:
        logger.warning(f"Invalid buffer distance {distance} for {layer_name}, returning unchanged")
        return points_gdf.copy()

    osm_file_path = os.path.abspath(osm_file)
    if not os.path.exists(osm_file_path):
        logger.error(f"OSM file not found: {osm_file_path}")
        raise FileNotFoundError(f"OSM file not found: {osm_file_path}")

    logger.info(f"Creating network buffers for {layer_name}: distance={distance}m, network_type={network_type}, "
                f"use_envelope={use_envelope}, osm_file={osm_file_path}")

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

        # 3. Find nearest nodes
        logger.info(f"Finding nearest nodes for {len(points_gdf)} points...")
        X = np.array([p.x for p in points_utm])
        Y = np.array([p.y for p in points_utm])
        nearest_nodes = ox.distance.nearest_nodes(G, X, Y)
        logger.info(f"Nearest nodes found")

        # 4. Process buffers with optimized multiprocessing
        num_cores = cpu_count()  # Use ALL cores
        chunk_size = 500  # Larger chunks = less overhead
        logger.info(f"Using {num_cores} CPU cores processing all {len(points_gdf)} points")
        
        buffer_gdf = points_gdf.copy()
        
        # Prepare ALL arguments at once (WITHOUT the graph)
        logger.info("Preparing worker arguments...")
        worker_args = [
            (i, nearest_nodes[i], points_utm.iloc[i].x, points_utm.iloc[i].y, distance, use_envelope, utm_crs)
            for i in range(len(points_gdf))
        ]

        # Create pool ONCE for all points
        logger.info("Starting parallel processing...")
        try:
            with Pool(num_cores, initializer=_init_worker, initargs=(G,)) as pool:
                results = list(tqdm(
                    pool.imap_unordered(create_network_buffer, worker_args, chunksize=chunk_size),
                    total=len(points_gdf),
                    desc="Creating buffers"
                ))
        except Exception as e:
            logger.warning(f"Multiprocessing failed: {e}. Falling back to single-threaded")
            _init_worker(G)
            results = [create_network_buffer(args) for args in tqdm(worker_args, desc="Creating buffers")]

        # Update all geometries at once
        logger.info("Updating geometries...")
        valid_buffers = 0
        for idx, buffer in results:
            if buffer is not None:
                buffer_gdf.at[idx, 'geometry'] = buffer
                valid_buffers += 1
        
        logger.info(f"Generated {valid_buffers}/{len(points_gdf)} valid buffers")

        # 5. Filter valid geometries and add metadata
        buffer_gdf = buffer_gdf[buffer_gdf.geometry.notnull()]

        if not buffer_gdf.empty:
            logger.info("Calculating areas...")
            buffer_gdf['area_km2'] = buffer_gdf.geometry.to_crs("EPSG:32618").area / 1_000_000
            buffer_gdf['buffer_type'] = 'network_buffer'
            buffer_gdf['buffer_layer'] = layer_name
            logger.info(f"Successfully created {len(buffer_gdf)} network buffers")
        else:
            logger.warning(f"No valid buffers created for {layer_name}, returning original GDF")
            return points_gdf.copy()

        return buffer_gdf

    except Exception as e:
        logger.error(f"Major error in network buffering for {layer_name}: {e}")
        return points_gdf.copy()

def apply_lines_network_buffer(
    lines_gdf: gpd.GeoDataFrame,
    layer_name: str,
    buffer_params: dict,
    mode: str = "all"  # "centroid" ou "all"
) -> gpd.GeoDataFrame:
    """
    Génère un buffer réseau autour des lignes :
      - mode="centroid" : buffer autour du centroïde
      - mode="all" : buffer autour du centroïde + extrémités, puis union
    """
    if lines_gdf.empty:
        logger.info(f"La couche '{layer_name}' est vide.")
        return lines_gdf.copy()

    if layer_name not in buffer_params:
        logger.info(f"Aucun paramètre trouvé pour la couche '{layer_name}'")
        return lines_gdf.copy()

    if not all(lines_gdf.geometry.geom_type == "LineString"):
        raise ValueError("Toutes les géométries doivent être de type LineString.")

    try:
        buffer_list = []

        for idx, row in lines_gdf.iterrows():
            line = row.geometry

            # Points à bufferiser
            points = [line.centroid]
            if mode == "all":
                points.append(Point(line.coords[0]))       # Extrémité début
                points.append(Point(line.coords[-1]))      # Extrémité fin

            # Construire un GDF temporaire avec ces points
            temp_gdf = gpd.GeoDataFrame([row] * len(points), geometry=points, crs=lines_gdf.crs)

            # Appliquer les buffers réseaux
            temp_buffers = apply_points_network_buffer(temp_gdf, layer_name, buffer_params)

            if not temp_buffers.empty:
                # Union des buffers
                merged = temp_buffers.unary_union
                buffer_list.append({"geometry": merged, **row.drop("geometry")})

        if buffer_list:
            return gpd.GeoDataFrame(buffer_list, crs=lines_gdf.crs)
        else:
            logger.info(f"Aucun buffer valide généré pour {layer_name}")
            return lines_gdf.copy()

    except Exception as e:
        logger.error(f"Erreur dans apply_lines_network_buffer pour '{layer_name}': {e}")
        return lines_gdf.copy()

def apply_polygons_network_buffer(
    polygons_gdf: gpd.GeoDataFrame,
    layer_name: str,
    buffer_params: dict,
    mode: str = "all"  # "centroid" ou "all"
) -> gpd.GeoDataFrame:
    """
    Génère un buffer réseau autour des polygones :
      - mode="centroid" : buffer autour du centroïde
      - mode="all" : buffer autour du centroïde + coins du bounding box, puis union
    """
    if polygons_gdf.empty:
        logger.info(f"La couche '{layer_name}' est vide.")
        return polygons_gdf.copy()

    if layer_name not in buffer_params:
        logger.info(f"Aucun paramètre trouvé pour la couche '{layer_name}'")
        return polygons_gdf.copy()

    if not polygons_gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        raise ValueError("Toutes les géométries doivent être de type Polygon ou MultiPolygon.")

    try:
        buffer_list = []

        for idx, row in polygons_gdf.iterrows():
            poly = row.geometry

            # Points à bufferiser
            points = [poly.centroid]

            if mode == "all":
                minx, miny, maxx, maxy = poly.bounds
                points.extend([
                    Point(minx, miny),
                    Point(minx, maxy),
                    Point(maxx, miny),
                    Point(maxx, maxy),
                ])

            # Construire un GDF temporaire avec ces points
            temp_gdf = gpd.GeoDataFrame([row] * len(points), geometry=points, crs=polygons_gdf.crs)

            # Appliquer les buffers réseaux
            temp_buffers = apply_points_network_buffer(temp_gdf, layer_name, buffer_params)

            if not temp_buffers.empty:
                # Union des buffers
                merged = temp_buffers.unary_union
                buffer_list.append({"geometry": merged, **row.drop("geometry")})

        if buffer_list:
            return gpd.GeoDataFrame(buffer_list, crs=polygons_gdf.crs)
        else:
            logger.info(f"Aucun buffer valide généré pour {layer_name}")
            return polygons_gdf.copy()

    except Exception as e:
        logger.error(f"Erreur dans apply_polygons_network_buffer pour '{layer_name}': {e}")
        return polygons_gdf.copy()
