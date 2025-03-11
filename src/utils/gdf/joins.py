import geopandas as gpd
import pandas as pd
from typing import Dict

# Fonction pour récupérer les couches de points et de polygones pour les jointures
def get_join_layers(points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs, join_layers):
    join_data = {}
    if "points" in join_layers:
        join_data["points"] = points_gdfs
    if "polygons" in join_layers:
        join_data["polygons"] = polygons_gdfs
    if "multipolygons" in join_layers:
        join_data["multipolygons"] = multipolygons_gdfs
    if "linestrings" in join_layers: 
        join_data["linestrings"] = linestrings_gdfs
    return join_data

import geopandas as gpd
import pandas as pd
from typing import Dict

def perform_spatial_joins(buffer_gdfs: Dict[str, gpd.GeoDataFrame], join_data: Dict[str, Dict[str, gpd.GeoDataFrame]], join_layers: Dict[str, Dict[str, str]]) -> gpd.GeoDataFrame:
    
    buffer_joins = []
    
    for buffer_name, buffer_gdf in buffer_gdfs.items():
        buffer_crs = buffer_gdf.crs
        
        for geom_type, join_gdfs in join_data.items():
            join_type = join_layers[geom_type]["type"]
            
            for join_layer_name, join_gdf in join_gdfs.items():
                if join_gdf.crs != buffer_crs:
                    join_gdf = join_gdf.to_crs(buffer_crs)
                
                join_gdf = join_gdf.reset_index(drop=True).copy()
                
                try:
                    joined = gpd.sjoin(
                        buffer_gdf, 
                        join_gdf, 
                        how='inner', 
                        predicate=join_type
                    )
                    
                    if joined.empty:
                        continue
                        
                    joined[f'{join_layer_name}_geometry'] = join_gdf.loc[
                        joined['index_right'], 
                        'geometry'
                    ].values
                    
                    # Add metadata
                    joined = joined.assign(
                        buffer_layer=buffer_name,
                        join_layer=join_layer_name,
                        join_type=join_type
                    )
                    
                    buffer_joins.append(joined)
                    
                except Exception as e:
                    print(f"Error joining {buffer_name} with {join_layer_name}: {str(e)}")
                    continue

    if not buffer_joins:
        return gpd.GeoDataFrame()
    
    # Preserve geometry information and combine results
    final_gdf = gpd.GeoDataFrame(
        pd.concat(buffer_joins, ignore_index=True),
        crs=buffer_gdfs[next(iter(buffer_gdfs))].crs
    )
    
    # Clean up index columns
    final_gdf = final_gdf.drop(columns=['index_right'], errors='ignore')
    
    return final_gdf