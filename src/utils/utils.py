import pandas as pd
import geopandas as gpd
from typing import Optional, Dict
import fiona
from shapely.geometry import shape

def load_files_to_gdf(data_files: Dict[str, str]) -> Dict[str, gpd.GeoDataFrame]:
    
    geodataframes = {}

    for name, file_path in data_files.items():
        geometries = []
        properties = []

        # Charger et filtrer les géométries
        with fiona.open(file_path, "r") as src:
            for feature in src:
                geom = shape(feature['geometry']) if feature['geometry'] is not None else None
                if geom is not None:
                    geometries.append(geom)
                    properties.append(feature.get('properties', {}))  # Ajouter un dictionnaire vide si properties est None

        # Créer le GeoDataFrame sans valeurs None
        gdf = gpd.GeoDataFrame(properties, geometry=geometries)
        geodataframes[name] = gdf  # Ajouter le GeoDataFrame au dictionnaire avec le nom comme clé

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