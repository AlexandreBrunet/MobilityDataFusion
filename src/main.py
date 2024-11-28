import utils.utils as utils
import utils.gdf.gdfExtraction as gdfExtraction
import utils.gdf.extractGeo as extractGeo
import utils.gdf.joins as joins
import utils.metrics.metrics as metrics
import utils.metrics.filtering as filtering
import utils.visualisation.visualisation as visualisation
import pandas as pd
import geopandas as gpd
import yaml
import time

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
buffer_type = config.get("buffer_type")

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

points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs = extractGeo.extract_geometries(gdf)

buffer_gdfs = extractGeo.create_buffers(points_gdfs, buffer_layer, buffer_type)

raw_fusion_gdf = gpd.GeoDataFrame(pd.concat([*points_gdfs.values(), *polygons_gdfs.values(), *multipolygons_gdfs.values(), *linestrings_gdfs.values(), *buffer_gdfs.values()], ignore_index=True))

join_data = joins.get_join_layers(points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs, join_layers)
agg_fusion_gdf = joins.perform_spatial_joins(buffer_gdfs, join_data, join_layers)

agg_stats_gdf = metrics.calculate_metrics(
    gdf=agg_fusion_gdf,
    groupby_columns=config["groupby_columns"],
    metrics_config=metrics_config,
)

final_gdf = filtering.apply_global_filters(agg_stats_gdf, config)

visualisation.create_table_visualisation(final_gdf)

if activate_visualisation:
    print("Visualisation activée : création de la carte.")
    visualisation.create_layers_and_map(
        geodataframes, points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs, buffer_gdfs, colors
    )
else:
    print("Visualisation désactivée.")

raw_fusion_gdf.to_csv("./data/output/data/raw_data_fusion_output.csv")
agg_fusion_gdf.to_csv("./data/output/data/agg_data_fusion_output.csv")

end_time = time.time()
execution_time = end_time - start_time

print(f"Temps d'exécution total : {execution_time:.2f} secondes.")