import utils.utils as utils
import utils.gdf.gdfExtraction as gdfExtraction
import utils.gdf.extractGeo as extractGeo
import utils.gdf.joins as joins
import utils.metrics.metrics as metrics
import utils.visualisation.visualisation as visualisation
import pandas as pd
import geopandas as gpd
import yaml

# Charger la configuration depuis le fichier YAML
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Accéder aux paramètres de configuration
data_files = config["data_files"]
buffer_layers = config["buffer_layers"]
join_layers = config["join_layers"]
colors = config["colors"]
agg_columns = config["agg_columns"]
count_columns = config["count_columns"]
groupby_columns = config["groupby_columns"]

# Charger les fichers geojson
geodataframes = utils.load_files_to_gdf(data_files)

gdf = gdfExtraction.process_geodataframes(geodataframes, utils)

points_gdfs, polygons_gdfs, multipolygons_gdfs = extractGeo.extract_geometries(gdf)

buffer_gdfs = extractGeo.create_buffers(points_gdfs, buffer_layers)

raw_fusion_gdf = gpd.GeoDataFrame(pd.concat([*points_gdfs.values(), *polygons_gdfs.values(), *multipolygons_gdfs.values(), *buffer_gdfs.values()], ignore_index=True))

join_data = joins.get_join_layers(points_gdfs, polygons_gdfs, multipolygons_gdfs, join_layers)
agg_fusion_gdf = joins.perform_spatial_joins(buffer_gdfs, join_data, join_layers)

raw_fusion_gdf.to_csv("./data/ouput/data/raw_data_fusion_output.csv")
agg_fusion_gdf.to_csv("./data/ouput/data/agg_data_fusion_output.csv")

agg_stats_gdf = metrics.aggregate_stats(agg_fusion_gdf, groupby_columns, agg_columns, count_columns)

visualisation.create_table_visualisation(agg_stats_gdf)
visualisation.create_layers_and_map(geodataframes, points_gdfs, polygons_gdfs, multipolygons_gdfs, buffer_gdfs, colors)