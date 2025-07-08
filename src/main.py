import utils.utils as utils
import utils.gdf.gdfExtraction as gdfExtraction
import utils.gdf.extractGeo as extractGeo
import utils.gdf.joins as joins
import utils.buffer.calculation as calculate_buffer
import utils.metrics.metrics as metrics
import utils.metrics.filtering as filtering
import utils.visualisation.visualisation as visualisation
import utils.metrics.proportion as proportion
import yaml
import time
import pandas as pd
import geopandas as gpd
import os

pd.set_option("future.no_silent_downcasting", True)

def main():
    start_time = time.time()

    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

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

    output_dir = "./data/output/"
    os.makedirs(output_dir, exist_ok=True)
    fusion_gdf_path = os.path.join(output_dir, "fusion_gdf.parquet")

    if os.path.exists(fusion_gdf_path):
        os.remove(fusion_gdf_path)

    if utils.should_regenerate_fusion_gdf(config, fusion_gdf_path):
        geodataframes = utils.load_files_to_gdf(data_files)
        geodataframes = filtering.apply_filters_to_layers(geodataframes, config, filtering.filter_gdf)
        gdf = gdfExtraction.process_geodataframes(geodataframes, utils)
        points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf = extractGeo.extract_geometries(gdf)
        buffers_gdf = calculate_buffer.calculate_buffer(buffer_layer, points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf)
        join_data = joins.get_join_layers(points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf, join_layers)
        fusion_gdf = joins.perform_spatial_joins(buffers_gdf, join_data, join_layers)

        # Fusionner avec les buffers pour avoir la géométrie du buffer
        all_buffers = pd.concat(
            [gdf.assign(buffer_name=key) for key, gdf in buffers_gdf.items()],
            ignore_index=True
        ).rename(columns={'geometry': 'buffer_geometry'})

        fusion_gdf = fusion_gdf.merge(all_buffers[['buffer_id', 'buffer_geometry']], on='buffer_id', how='left')

        # Remplacer la géométrie par celle du layer joint
        fusion_gdf['geometry'] = None
        for idx, row in fusion_gdf.iterrows():
            join_layer = row['join_layer']
            joined_geometry_col = f"{join_layer}_geometry"
            if joined_geometry_col in fusion_gdf.columns:
                fusion_gdf.at[idx, 'geometry'] = row[joined_geometry_col]

        fusion_gdf = gpd.GeoDataFrame(fusion_gdf, geometry='geometry', crs=fusion_gdf.crs)
        fusion_gdf = fusion_gdf[~fusion_gdf['geometry'].isna()]

        # Calcul vectorisé des proportions
        fusion_gdf['proportion'] = 1.0
        mask = fusion_gdf.geometry.geom_type.isin(['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon'])
        fusion_gdf.loc[mask, 'proportion'] = proportion.calculate_geometric_proportions(
            geometry=fusion_gdf.loc[mask, 'geometry'],
            buffer_geometry=fusion_gdf.loc[mask, 'buffer_geometry']
        )

        # Nettoyage des colonnes géométriques inutiles
        geometry_columns = [col for col in fusion_gdf.columns if isinstance(fusion_gdf[col].dtype, gpd.array.GeometryDtype) and col != 'geometry']
        wkt_columns = [col for col in fusion_gdf.columns if col.endswith('_wkt')]
        buffer_columns = [col for col in fusion_gdf.columns if col.endswith('_left') and col != 'area_km2']
        redundant_columns = [col for col in fusion_gdf.columns if col.endswith('_right') and col.replace('_right', '') in fusion_gdf.columns]
        fusion_gdf = fusion_gdf.drop(columns=geometry_columns + wkt_columns + buffer_columns + redundant_columns, errors='ignore')

        if config.get("groupby_columns"):
            valid_groupby_cols = [col for col in config["groupby_columns"] if col in fusion_gdf.columns]
            if valid_groupby_cols:
                initial_count = len(fusion_gdf)
                fusion_gdf = fusion_gdf.dropna(subset=valid_groupby_cols)
                print(f"Dropped {initial_count - len(fusion_gdf)} rows with NaN in {valid_groupby_cols}")

        for col in fusion_gdf.columns:
            if fusion_gdf[col].dtype == 'object' and col != 'geometry':
                fusion_gdf[col] = fusion_gdf[col].astype(str)

        fusion_gdf.to_parquet(fusion_gdf_path)
    else:
        print("Chargement de fusion_gdf depuis fusion_gdf.parquet...")
        fusion_gdf = gpd.read_parquet(fusion_gdf_path)

    # Calcul des statistiques
    agg_stats_gdf = metrics.calculate_metrics(fusion_gdf, config["groupby_columns"], metrics_config)
    agg_stats_gdf = filtering.apply_global_filters(agg_stats_gdf, config)
    if config.get("post_aggregation_metrics"):
        agg_stats_gdf = metrics.calculate_post_aggregation_metrics(agg_stats_gdf, config["post_aggregation_metrics"])

    # Export CSV et visualisation
    for layer_name, layer_config in buffer_layer.items():
        buffer_type = layer_config.get('buffer_type')
        params = layer_config.copy(); params.pop('buffer_type', None)

        distance = params.get('distance', None)
        fusion_gdf.to_csv(path_or_buf=f"./data/output/data/fusion/joined_data_{layer_name}_{buffer_type}_{distance}m.csv")

        filename = f"./data/output/data/agg/{buffer_type}_buffer"
        if buffer_type == 'circular':
            filename += f"_{params['distance']}m.csv"
        elif buffer_type == 'grid':
            filename += f"_{params['wide']}m_{params['length']}m.csv"
        elif buffer_type == 'isochrone':
            filename += f"_{params.get('network_type', 'walk')}m_{params.get('distance', 500)}m.csv"
        elif buffer_type == 'network':
            filename += f"_{params.get('network_type', 'walk')}_{params.get('distance', 500)}m.csv"
        elif buffer_type == 'zones':
            filename = f"./data/output/data/agg/{buffer_type}.csv"

        agg_stats_gdf.to_csv(filename, mode='w')
        visualisation.create_table_visualisation(agg_stats_gdf, buffer_type, **params)

        if activate_visualisation:
            visualisation.create_layers_and_map(
                geodataframes, points_gdf, polygons_gdf, multipolygons_gdf, linestrings_gdf,
                buffers_gdf, colors, buffer_type, **params
            )

    if not activate_visualisation:
        print("Visualisation désactivée.")

    print(f"Temps d'exécution total : {time.time() - start_time:.2f} secondes.")

if __name__ == '__main__':
    main()