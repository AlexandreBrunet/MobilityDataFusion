import utils.utils as utils
import utils.buffer as buffer
import utils.gdfExtraction as gdfExtraction
import utils.visualisation as visualisation
import pandas as pd
import geopandas as gpd

# Liste des fichiers de données
data_files = {
    "bus_stops": './data/stm_bus_stops.geojson',
    "bixi_stations": './data/stations_bixi.geojson',
    "evaluation_fonciere": './data/uniteevaluationfoncieretest.geojson'
}

# Nom de la couche : distance du buffer en mètres
buffer_layers = {
    "bixi_stations": 100
}

# Initialiser les listes de couches de points et de polygones
layers = []
colors = {'bus_stops': '[0, 200, 0, 160]', 'bixi_stations': '[200, 30, 0, 160]', 'evaluation_fonciere': '[0, 30, 200, 160]'}

# Charger tous les GeoDataFrames en une fois
geodataframes = utils.load_files_to_gdf(data_files)

gdf = gdfExtraction.process_geodataframes(geodataframes, utils)

# Créer les GeoDataFrames pour les points, les polygones et les buffers en dehors de la boucle de création de couches
points_gdfs = {layer_name: gdfExtraction.extract_points_gdf(gdf).assign(layer_name=layer_name) 
               for layer_name, gdf in geodataframes.items()}

polygons_gdfs = {layer_name: gdfExtraction.extract_polygons_gdf(gdf).assign(layer_name=layer_name) 
                 for layer_name, gdf in geodataframes.items()}

buffer_gdfs = {layer_name: buffer.apply_buffer(points_gdfs[layer_name], layer_name, buffer_layers).assign(layer_name=layer_name) 
               for layer_name in buffer_layers}

merged_gdf = gpd.GeoDataFrame(pd.concat([*points_gdfs.values(), *polygons_gdfs.values(), *buffer_gdfs.values()], ignore_index=True))

merged_gdf.to_csv("allo.csv")

visualisation.create_layers_and_map(geodataframes, points_gdfs, polygons_gdfs, buffer_gdfs, colors)