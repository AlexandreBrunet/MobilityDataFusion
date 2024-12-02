import pandas as pd
import geopandas as gpd
from typing import Optional, Dict
import fiona
from shapely.geometry import shape
import os
import time
import logging
from shapely.errors import WKTReadingError

# Configurer le logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def log_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logging.info(f"Début de la fonction : {func.__name__}")
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Fin de la fonction : {func.__name__} | Temps d'exécution : {elapsed_time:.2f} secondes")
        return result
    return wrapper

def load_files_to_gdf(data_files: Dict[str, str]) -> Dict[str, gpd.GeoDataFrame]:
    geodataframes = {}

    for name, file_path in data_files.items():
        parquet_path = file_path.replace("/geojson/", "/parquet/").replace(".geojson", ".parquet")
        parquet_dir = os.path.dirname(parquet_path)
        if not os.path.exists(parquet_dir):
            os.makedirs(parquet_dir)

        try:
            if os.path.exists(parquet_path):
                logger.info(f"Chargement de {parquet_path}...")
                gdf = gpd.read_parquet(parquet_path)
            else:
                logger.info(f"Chargement de {file_path} et conversion en Parquet...")
                geometries = []
                properties = []

                with fiona.open(file_path, "r") as src:
                    for feature in src:
                        try:
                            # Convertir la géométrie en utilisant Shapely
                            geom = shape(feature['geometry']) if feature['geometry'] is not None else None
                            if geom is not None:
                                geometries.append(geom)
                                properties.append(feature.get('properties', {}))
                        except (TypeError, WKTReadingError) as e:
                            logger.warning(f"Géométrie invalide ignorée dans {file_path}: {e}")

                gdf = gpd.GeoDataFrame(properties, geometry=geometries, crs=src.crs)

                # Écrire en Parquet pour les utilisations futures
                gdf.to_parquet(parquet_path)

            # Identifier et filtrer les géométries invalides
            invalid_count = (~gdf.is_valid).sum()
            if invalid_count > 0:
                logger.warning(f"{invalid_count} géométrie(s) invalide(s) trouvée(s) dans {file_path} et supprimée(s).")
            gdf = gdf[gdf.is_valid]

            # Ajouter au dictionnaire
            geodataframes[name] = gdf

        except Exception as e:
            logger.error(f"Erreur lors du traitement de {file_path}: {e}")

    return geodataframes

def check_geometry_column(df: pd.DataFrame) -> Optional[str]:
    geom_columns = ['geom', 'geo', 'geometry']
    for col in geom_columns:
        if col in df.columns:
            return col
    return None

def rename_geometry_column(df: pd.DataFrame) -> pd.DataFrame:
    geometry_column = check_geometry_column(df)

    if geometry_column in ['geo', 'geom']:
        df = df.rename(columns={geometry_column: 'geometry'})
        print(f"Renamed column '{geometry_column}' to 'geometry'.")
    return df

def check_geometry_type(gdf: gpd.GeoDataFrame) -> str:
    unique_geom_types = gdf.geom_type.unique()

    if unique_geom_types.size == 1:
        return unique_geom_types[0]
    else:
        raise ValueError("Les données contiennent plusieurs types de géométrie.")

def determine_crs(gdf: gpd.GeoDataFrame) -> str:
    # Filtrer uniquement les géométries de type Point
    point_geometries = gdf[gdf.geometry.type == "Point"]
    # Extraire les coordonnées x pour estimation du CRS
    if not point_geometries.empty:
        x_coords = point_geometries.geometry.x
        # Si les coordonnées x sont grandes, on suppose qu'elles sont en EPSG:32188 (coordonnées projetées)
        if x_coords.mean() > 180:
            return "EPSG:32188"
    # Par défaut, si on a des petites valeurs de x ou pas de points, on utilise EPSG:4326
    return "EPSG:4326"

def add_lon_lat_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ajoute les colonnes 'lon' et 'lat' à partir de la géométrie."""
    gdf['lon'] = gdf.geometry.x
    gdf['lat'] = gdf.geometry.y
    return gdf

def prepare_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = determine_crs(gdf)
    return add_lon_lat_columns(gdf)