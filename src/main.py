import utils.utils as utils
import utils.buffer.buffer as buffer
import utils.gdf.gdfExtraction as gdfExtraction
import utils.gdf.extractGeo as extractGeo
import utils.visualisation.visualisation as visualisation
import pandas as pd
import geopandas as gpd
import itertools
import utils.metrics.metrics as metrics

# Liste des fichiers de données
data_files = {
    "bus_stops": './data/input/stm_bus_stops.geojson',
    "bixi_stations": './data/input/stations_bixi.geojson',
    "evaluation_fonciere": './data/input/uniteevaluationfoncieretest.geojson'
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

points_gdfs, polygons_gdfs, multipolygons_gdfs = extractGeo.extract_geometries(gdf)

buffer_gdfs = extractGeo.create_buffers(points_gdfs, buffer_layers)

raw_fusion_gdf = gpd.GeoDataFrame(pd.concat([*points_gdfs.values(), *polygons_gdfs.values(), *multipolygons_gdfs.values(), *buffer_gdfs.values()], ignore_index=True))

##TODO: enlever la hardcoded
bus_stops_gdf = points_gdfs["bus_stops"]
evaluation_fonciere_gdf = polygons_gdfs["evaluation_fonciere"]

# Effectuer la jointure spatiale sur chaque buffer avec bus_stops et evaluation_fonciere
buffer_joins = []
##TODO: enlever la bus_stops et evaluation_fonciere
for layer_name, buffer_gdf in buffer_gdfs.items():
    # Jointure avec bus_stops
    bus_stops_join = gpd.sjoin(buffer_gdf, bus_stops_gdf, how="inner", predicate="contains").assign(buffer_layer=layer_name, join_type="bus_stops")
    buffer_joins.append(bus_stops_join)
    
    # Jointure avec evaluation_fonciere
    evaluation_fonciere_join = gpd.sjoin(buffer_gdf, evaluation_fonciere_gdf, how="inner", predicate="intersects").assign(buffer_layer=layer_name, join_type="evaluation_fonciere")
    buffer_joins.append(evaluation_fonciere_join)

# Concaténer tous les résultats de jointure en un seul DataFrame
agg_fusion_gdf = pd.concat(buffer_joins, ignore_index=True)

raw_fusion_gdf.to_csv("./data/ouput/data/raw_data_fusion_output.csv")
agg_fusion_gdf.to_csv("./data/ouput/data/agg_data_fusion_output.csv")

agg_columns = ['NOMBRE_LOGEMENT', 'SUPERFICIE_BATIMENT', 'SUPERFICIE_TERRAIN', 'capacity']
count_columns = ['stop_id']
groupby_columns = ['buffer_id', 'name']

agg_stats_gdf = metrics.aggregate_stats(agg_fusion_gdf, groupby_columns, agg_columns, count_columns)

visualisation.create_table_visualisation(agg_stats_gdf)
visualisation.create_layers_and_map(geodataframes, points_gdfs, polygons_gdfs, multipolygons_gdfs, buffer_gdfs, colors)