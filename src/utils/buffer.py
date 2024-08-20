import geopandas as gpd

def buffer_oiseau(gdf: gpd.GeoDataFrame, column_name: str, buffer_size: float) -> gpd.GeoDataFrame:
    gdf[column_name] = gdf.geometry.buffer(buffer_size)
    return gdf