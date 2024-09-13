import mimetypes
import pandas as pd
import geopandas as gpd
from typing import Optional

def file_type(file_path):
    try:
        mimetypes.add_type('application/geo+json', '.geojson')
            
        file_type, encoding = mimetypes.guess_type(file_path)
            
        if file_type == 'application/geo+json':
            file_type = 'geojson'
                        
        return file_type

    except FileNotFoundError:
        return "File not found"
    except Exception as e:
        return str(e)

def files_to_df(file_path, file_type):
    if file_type == 'csv':
        return pd.read_csv(file_path)
    elif file_type == 'geojson':
        return gpd.read_file(file_path)
    else:
        raise ValueError("Unsupported file type. Please use 'csv' or 'geojson'.")
    
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


def check_and_correct_crs(gdf, expected_crs=4326, true_crs=2950):
    """Vérifie si le CRS est correctement étiqueté, et corrige si nécessaire."""
    # Si le CRS est EPSG:4326 mais les coordonnées semblent incorrectes
    if gdf.crs.to_string() == f'EPSG:{expected_crs}':
        # Vérification manuelle (par exemple : si les valeurs sont trop grandes pour des lat/lon en degrés)
        if gdf.total_bounds[0] > 180 or gdf.total_bounds[1] > 90:
            print("Les coordonnées semblent incorrectes pour EPSG:4326. Forçage à EPSG:2950.")
            gdf = gdf.set_crs(epsg=true_crs, allow_override=True)
            gdf = gdf.to_crs(epsg=expected_crs)
        else:
            print("CRS est déjà EPSG:4326 et semble correct.")
    else:
        print(f"CRS actuel : {gdf.crs.to_string()}. Reprojection vers EPSG:{expected_crs}.")
        gdf = gdf.to_crs(epsg=expected_crs)
    
    return gdf

def add_lon_lat_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ajoute les colonnes 'lon' et 'lat' à partir de la géométrie."""
    gdf['lon'] = gdf.geometry.x
    gdf['lat'] = gdf.geometry.y
    return gdf

def prepare_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = check_and_correct_crs(gdf)
    return add_lon_lat_columns(gdf)