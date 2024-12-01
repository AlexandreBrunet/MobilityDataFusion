import geopandas as gpd
from typing import Dict

def process_geodataframes(geodataframes: Dict[str, gpd.GeoDataFrame], utils) -> Dict[str, gpd.GeoDataFrame]:
    for layer_name, gdf in geodataframes.items():
        # Déterminer le CRS en fonction des coordonnées si le CRS est absent
        if gdf.crs is None:
            gdf.set_crs(utils.determine_crs(gdf), inplace=True)
        
        # Convertir en EPSG:4326 si nécessaire
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        
        # Remplir les valeurs manquantes par 0 et appliquer infer_objects()
        gdf = gdf.fillna(0).infer_objects(copy=False)
        
        # Mettre à jour le GeoDataFrame traité
        geodataframes[layer_name] = gdf
    
    return geodataframes

def extract_points_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    points_gdf = gdf[gdf.geometry.type == "Point"].copy()
    points_gdf = extract_points_coordinates(points_gdf)
    return points_gdf

def extract_linestrings_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    linestrings_gdf = gdf[gdf.geometry.type == "LineString"].copy()
    linestrings_gdf = extract_line_coordinates(linestrings_gdf)
    return linestrings_gdf

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

def extract_line_coordinates(linestrings_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ajoute une colonne 'coordinates' contenant les coordonnées des géométries de type LineString."""
    if not linestrings_gdf.empty:
        linestrings_gdf['coordinates'] = linestrings_gdf['geometry'].apply(
            lambda geom: list(geom.coords)
        )
    return linestrings_gdf

def extract_multipolygons_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Extrait les géométries de type MultiPolygon et ajoute une colonne 'coordinates' contenant leurs coordonnées."""
    multipolygons_gdf = gdf[gdf.geometry.type == "MultiPolygon"].copy()
    
    multipolygons_gdf['coordinates'] = multipolygons_gdf['geometry'].apply(
        lambda geom: [poly.__geo_interface__['coordinates'] for poly in geom.geoms]
    )
    
    return multipolygons_gdf
