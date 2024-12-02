import utils.utils as utils
import utils.gdf.gdfExtraction as gdfExtraction
import utils.gdf.extractGeo as extractGeo
import utils.gdf.joins as joins
import utils.buffer.buffer as buffer
import utils.metrics.metrics as metrics
import utils.visualisation.visualisation as visualisation
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

# Charger les fichers geojson
geodataframes = utils.load_files_to_gdf(data_files)

gdf = gdfExtraction.process_geodataframes(geodataframes, utils)

points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs = extractGeo.extract_geometries(gdf)

for layer_name in buffer_layer:
    geometry_type = buffer_layer[layer_name].get('geometry_type', None)

    if geometry_type == "Point":
        buffer_gdfs = buffer.create_buffers(points_gdfs, buffer_layer)
    elif geometry_type == "LineString":
        buffer_gdfs = buffer.create_buffers(linestrings_gdfs, buffer_layer)
    elif geometry_type == "Polygon":
        buffer_gdfs = buffer.create_buffers(polygons_gdfs, buffer_layer)
    elif geometry_type == "MultiPolygon":
        buffer_gdfs = buffer.create_buffers(multipolygons_gdfs, buffer_layer)
    else:
        print("The geometry_type is unsupported either: Point, LineString, Polygon or MultiPolygon")

join_data = joins.get_join_layers(points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs, join_layers)
agg_fusion_gdf = joins.perform_spatial_joins(buffer_gdfs, join_data, join_layers)


metrics_config = {
    "sum": config["sum_columns"],
    "max": config["max_columns"],
    "min": config["min_columns"],
    "mean": config["mean_columns"],
    "std": config["std_columns"],
    "ratio": config["ratio_columns"],
    "count": config["count_columns"]
}

agg_stats_gdf = metrics.calculate_metrics(
    gdf=agg_fusion_gdf,
    groupby_columns=config["groupby_columns"],
    metrics_config=metrics_config,
)

visualisation.create_table_visualisation(agg_stats_gdf)

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