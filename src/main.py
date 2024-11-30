import utils.utils as utils
import utils.gdf.gdfExtraction as gdfExtraction
import utils.gdf.extractGeo as extractGeo
import utils.gdf.joins as joins
import utils.metrics.metrics as metrics
import utils.metrics.filtering as filtering
import utils.visualisation.visualisation as visualisation
import yaml
import time
import utils.buffer.buffer as buffer
import geopandas as gpd
import pandas as pd

start_time = time.time()

# Charger la configuration depuis le fichier YAML
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Accéder aux paramètres de configuration 
activate_visualisation = config.get("activate_visualisation")
data_files = config.get("data_files")
buffer_layer = config.get("buffer_layer")
buffer_type = config.get("buffer_type")
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

geodataframes = utils.load_files_to_gdf(data_files)

geodataframes = filtering.apply_filters_to_layers(geodataframes, config, filtering.filter_gdf)

gdf = gdfExtraction.process_geodataframes(geodataframes, utils)

extracted_gdf = extractGeo.extract_geometries(gdf)

points_gdfs = extracted_gdf["points"].dropna(axis=1, how="all")
polygons_gdfs = extracted_gdf["polygons"].dropna(axis=1, how="all")
multipolygons_gdfs = extracted_gdf["multipolygons"].dropna(axis=1, how="all")
linestrings_gdfs = extracted_gdf["linestrings"].dropna(axis=1, how="all")

extracted_gdf = {
    "points": points_gdfs,
    "linestrings": linestrings_gdfs,
    "polygons": polygons_gdfs,
    "multipolygons": multipolygons_gdfs,
}

buffer_gdfs = buffer.create_buffers(extracted_gdf, buffer_layer)
buffer_gdf = gpd.GeoDataFrame(pd.concat(buffer_gdfs.values(), ignore_index=True)).dropna(axis=1, how="all")

final_joined_gdf = joins.spatial_join_all_layers(extracted_gdf, buffer_gdf, join_layers)

agg_stats_gdf = metrics.calculate_metrics(
    gdf=final_joined_gdf,
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

end_time = time.time()
execution_time = end_time - start_time

print(f"Temps d'exécution total : {execution_time:.2f} secondes.")