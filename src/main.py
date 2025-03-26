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
    "multiply": config["multiply_columns"],
    "count": config["count_columns"],
    "count_distinct": config["count_distinct_columns"]
}

# Charger les fichiers geojson
geodataframes = utils.load_files_to_gdf(data_files)

geodataframes = filtering.apply_filters_to_layers(geodataframes, config, filtering.filter_gdf)

gdf = gdfExtraction.process_geodataframes(geodataframes, utils)

points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf = extractGeo.extract_geometries(gdf)

buffers_gdf = calculate_buffer.calculate_buffer(buffer_layer, points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf)

join_data = joins.get_join_layers(points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf, join_layers)
fusion_gdf = joins.perform_spatial_joins(buffers_gdf, join_data, join_layers)

# Save fusion_gdf for histogram use later, handling multiple geometry columns
output_dir = "./data/output/"
os.makedirs(output_dir, exist_ok=True)

fusion_gdf['geometry'] = None
for idx, row in fusion_gdf.iterrows():
    join_layer = row['join_layer']
    joined_geometry_col = f"{join_layer}_geometry"
    if joined_geometry_col in fusion_gdf.columns:
        fusion_gdf.at[idx, 'geometry'] = row[joined_geometry_col]

fusion_gdf = gpd.GeoDataFrame(fusion_gdf, geometry='geometry', crs=fusion_gdf.crs)

fusion_gdf = fusion_gdf[~fusion_gdf['geometry'].isna()]

geometry_columns = [col for col in fusion_gdf.columns if isinstance(fusion_gdf[col].dtype, gpd.array.GeometryDtype) and col != 'geometry']
fusion_gdf = fusion_gdf.drop(columns=geometry_columns, errors='ignore')

wkt_columns = [col for col in fusion_gdf.columns if col.endswith('_wkt')]
fusion_gdf = fusion_gdf.drop(columns=wkt_columns, errors='ignore')

buffer_columns = [col for col in fusion_gdf.columns if col.endswith('_left')]
fusion_gdf = fusion_gdf.drop(columns=buffer_columns, errors='ignore')

redundant_columns = [col for col in fusion_gdf.columns if col.endswith('_right') and col.replace('_right', '') in fusion_gdf.columns]
fusion_gdf = fusion_gdf.drop(columns=redundant_columns, errors='ignore')

fusion_gdf.to_file(os.path.join(output_dir, "fusion_gdf.geojson"), driver="GeoJSON")

agg_stats_gdf = metrics.calculate_metrics(
    gdf=fusion_gdf,
    groupby_columns=config["groupby_columns"],
    metrics_config=metrics_config,
)

agg_stats_gdf = filtering.apply_global_filters(agg_stats_gdf, config)

for layer_name in buffer_layer:
    buffer_type = buffer_layer[layer_name].get('buffer_type')
    buffer_params = buffer_layer[layer_name].copy()

    if 'buffer_type' in buffer_params:
        del buffer_params['buffer_type']

    if buffer_type == 'circular':
        distance = buffer_layer[layer_name].get('distance')
        print(f"Calculating {buffer_type} buffer of {distance} meters for {layer_name}")
        visualisation.create_table_visualisation(
            agg_stats_gdf, 
            buffer_type, 
            distance=distance
        )
        if activate_visualisation:
            visualisation.create_layers_and_map(
                geodataframes, points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf, buffers_gdf, colors, buffer_type,
                distance=distance
            )
    elif buffer_type == 'grid':
        wide = buffer_layer[layer_name].get('wide')
        length = buffer_layer[layer_name].get('length')
        print(f"Calculating {buffer_type} buffer of width {wide} meters and length {length} meters for {layer_name}")
        visualisation.create_table_visualisation(
            agg_stats_gdf, 
            buffer_type, 
            wide=wide, 
            length=length
        )
        if activate_visualisation:
            visualisation.create_layers_and_map(
                geodataframes, points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf, buffers_gdf, colors, buffer_type,
                wide=wide,
                length=length
            )
    elif buffer_type == 'zones':
        print(f"Processing pre-defined zones for {layer_name}")
        visualisation.create_table_visualisation(
            agg_stats_gdf, 
            buffer_type
        )
        if activate_visualisation:
            visualisation.create_layers_and_map(
                geodataframes, points_gdf, polygons_gdf, multipolygons_gdf,
                linestrings_gdf, buffers_gdf, colors, buffer_type
            )
    else:
        raise ValueError(f"Unsupported buffer type: {buffer_type} in configuration")

if not activate_visualisation:
    print("Visualisation désactivée.")

end_time = time.time()
execution_time = end_time - start_time

print(f"Temps d'exécution total : {execution_time:.2f} secondes.")