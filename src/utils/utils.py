import pandas as pd
import geopandas as gpd
from typing import Optional, Dict
import fiona
from shapely.geometry import shape
import os
import time
import logging
import geopandas as gpd
from pyproj import CRS

# Configurer le logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

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
        # Générer le chemin pour le fichier Parquet
        parquet_path = file_path.replace("/geojson/", "/parquet/").replace(".geojson", ".parquet")

        # Vérifier si le dossier de sortie pour les fichiers Parquet existe, sinon le créer
        parquet_dir = os.path.dirname(parquet_path)
        if not os.path.exists(parquet_dir):
            os.makedirs(parquet_dir)

        # Si le fichier Parquet existe déjà, le charger
        if os.path.exists(parquet_path):
            print(f"Chargement de {parquet_path}...")
            gdf = gpd.read_parquet(parquet_path)
        else:
            # Charger le fichier GeoJSON et convertir en GeoDataFrame
            print(f"Chargement de {file_path} et conversion en Parquet...")
            geometries = []
            properties = []

            with fiona.open(file_path, "r") as src:
                for feature in src:
                    geom = shape(feature['geometry']) if feature['geometry'] is not None else None
                    if geom is not None:
                        geometries.append(geom)
                        properties.append(feature.get('properties', {}))  # Ajouter un dictionnaire vide si properties est None

            gdf = gpd.GeoDataFrame(properties, geometry=geometries)

            # Écrire en Parquet pour les utilisations futures
            gdf.to_parquet(parquet_path)

        # Ajouter le GeoDataFrame au dictionnaire
        geodataframes[name] = gdf

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

def detect_utm_crs(gdf: gpd.GeoDataFrame) -> str:
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        raise ValueError("Le GeoDataFrame doit être en WGS 84 (EPSG:4326) pour détecter l'UTM.")
    
    # Calcul de la longitude moyenne
    lon_mean = gdf.geometry.centroid.x.mean()
    
    # Déterminer la zone UTM basée sur la longitude
    utm_zone = int((lon_mean + 180) // 6) + 1
    
    # Déterminer l'hémisphère
    is_northern = gdf.geometry.centroid.y.mean() >= 0
    epsg_code = 32600 + utm_zone if is_northern else 32700 + utm_zone
    
    return f"EPSG:{epsg_code}"