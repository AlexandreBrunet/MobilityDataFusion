import mimetypes
import pandas as pd
import geopandas as gdp
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
        return gdp.read_file(file_path)
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

def check_geometry_type(gdf: gdp.GeoDataFrame) -> str:
    unique_geom_types = gdf.geom_type.unique()

    if unique_geom_types.size == 1:
        return unique_geom_types[0]
    else:
        raise ValueError("Les données contiennent plusieurs types de géométrie.")