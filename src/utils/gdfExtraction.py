import geopandas as gpd
import pandas as pd

def extract_points_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    points_gdf = gdf[gdf.geometry.type == "Point"].copy()
    points_gdf = extract_points_coordinates(points_gdf)
    return points_gdf

def extract_polygons_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    polygons_gdf = gdf[gdf.geometry.type == "Polygon"].copy()
    polygons_gdf = extract_poly_coordinates(polygons_gdf)
    return polygons_gdf

def extract_poly_coordinates(polygons_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ajoute une colonne 'coordinates' contenant les coordonnées des géométries du GeoDataFrame."""
    if not polygons_gdf.empty:
        polygons_gdf['coordinates'] = polygons_gdf['geometry'].apply(lambda geom: geom.__geo_interface__['coordinates'])
    return polygons_gdf

def extract_points_coordinates(points_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ajoute des colonnes 'lon' et 'lat' avec les coordonnées x et y pour les géométries de type 'Point'."""
    if not points_gdf.empty:
        points_gdf = points_gdf.copy()
        points_gdf['lon'] = points_gdf.geometry.x
        points_gdf['lat'] = points_gdf.geometry.y
    return points_gdf
