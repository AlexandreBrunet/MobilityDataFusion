import utils.utils as utils
import utils.gdf.gdfExtraction as gdfExtraction
import utils.gdf.extractGeo as extractGeo
import utils.gdf.joins as joins
import utils.buffer.calculation as calculate_buffer
import utils.metrics.metrics as metrics
import utils.metrics.filtering as filtering
import utils.visualisation.visualisation as visualisation
import yaml
import time
import pandas as pd
import geopandas as gpd
import utils.gdf.outputGdf as outputGdf
import os

pd.set_option("future.no_silent_downcasting", True)

start_time = time.time()

# Charger la configuration depuis le fichier YAML
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Accéder aux paramètres de configuration
activate_visualisation = config.get("activate_visualisation")
data_files = config.get("data_files")
buffer_layer = config.get("buffer_layer")
join_layers = config.get("join_layers")
colors = config.get("colors")
metrics_config = {
    "sum": config["sum_columns"],
    "max": config["max_columns"],
    "min": config["min_columns"],
    "mean": config["mean_columns"],
    "std": config["std_columns"],
    "ratio": config["ratio_columns"],
    "count": config["count_columns"]
}

# Charger les fichers geojson
geodataframes = utils.load_files_to_gdf(data_files)

geodataframes = filtering.apply_filters_to_layers(geodataframes, config, filtering.filter_gdf)

gdf = gdfExtraction.process_geodataframes(geodataframes, utils)

points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf = extractGeo.extract_geometries(gdf)

buffers_gdf_dict = calculate_buffer.calculate_buffer(buffer_layer, points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf)

join_data = joins.get_join_layers(points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf, join_layers)
fusion_gdf = joins.perform_spatial_joins(buffers_gdf_dict, join_data, join_layers)

agg_stats_gdf = metrics.calculate_metrics(
    gdf=fusion_gdf,
    groupby_columns=config["groupby_columns"],
    metrics_config=metrics_config,
)

agg_stats_gdf = filtering.apply_global_filters(agg_stats_gdf, config)

for layer_name in buffer_layer:
    distance = buffer_layer[layer_name].get('distance')
    print(f"Calculating {distance} meters buffer for {layer_name}")

output_path = "./geojson_output"
outputGdf.process_and_save_joined_data(fusion_gdf, output_folder=output_path)

buffers_gdf = gpd.GeoDataFrame(
        pd.concat(buffers_gdf_dict.values(), ignore_index=True),  # Combine les GeoDataFrames
        crs=list(buffers_gdf_dict.values())[0].crs  # Utilise le CRS du premier GeoDataFrame
    )

output_file = os.path.join(output_path, "buffers_all.geojson")
buffers_gdf.to_file(output_file, driver="GeoJSON")

visualisation.create_table_visualisation(agg_stats_gdf, distance)

if activate_visualisation:
    print("Visualisation activée : création de la carte.")
    visualisation.create_layers_and_map(
        geodataframes, points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf, buffers_gdf_dict, colors
    )
else:
    print("Visualisation désactivée.")

end_time = time.time()
execution_time = end_time - start_time

print(f"Temps d'exécution total : {execution_time:.2f} secondes.")