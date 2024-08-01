import pandas as pd
import geopandas as gdp
from utils import file_type, files_to_df, check_geometry_column

file_path = './data/lieux-fr.geojson'
file_type = file_type(file_path=file_path)

data = files_to_df(file_path, file_type)
print(data.head(10))
check_if_geo = check_geometry_column(data)
