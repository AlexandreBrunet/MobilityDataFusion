import mimetypes
import pandas as pd
import geopandas as gdp

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
    
def check_geometry_column(df):
    geom_columns = ['geom', 'geo', 'geometry']
    for col in geom_columns:
        if col in df.columns:
            print(f"The dataframe contains a {col} column.")
            return col
    print("The dataframe does not contain a geom/geo/geometry column.")
    return None