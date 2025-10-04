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
    # Extraire les Polygon existants
    polygons_gdf = gdf[gdf.geometry.type == "Polygon"].copy()
    
    # Extraire et convertir les MultiPolygon en Polygon individuels
    multipolygons_gdf = gdf[gdf.geometry.type == "MultiPolygon"].copy()
    if not multipolygons_gdf.empty:
        print(f"Conversion de {len(multipolygons_gdf)} MultiPolygon(s) en Polygon(s) individuels")
        # Exploser les MultiPolygon en Polygon individuels
        exploded_multipolygons = multipolygons_gdf.explode(index_parts=False).reset_index(drop=True)
        
        # Modifier les noms des polygon_name pour que chaque partie ait un nom unique
        if 'polygon_name' in exploded_multipolygons.columns:
            for idx, row in exploded_multipolygons.iterrows():
                original_name = row['polygon_name']
                # Ajouter un suffixe pour chaque partie du MultiPolygon explosé
                exploded_multipolygons.at[idx, 'polygon_name'] = f"{original_name}_part_{idx + 1}"
        
        # Ajouter les Polygon convertis
        polygons_gdf = gpd.pd.concat([polygons_gdf, exploded_multipolygons], ignore_index=True)
        print(f"Total de {len(polygons_gdf)} Polygon(s) après conversion")
        print("Les MultiPolygons originaux sont supprimés - seules les parties explosées sont conservées")
    
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
    """Les MultiPolygons sont explosés en Polygons - cette fonction retourne un GeoDataFrame vide."""
    # Les MultiPolygons sont traités dans extract_polygons_gdf et explosés
    # Ils ne doivent plus apparaître comme MultiPolygons dans les résultats
    print("Les MultiPolygons sont explosés en Polygons - aucun MultiPolygon ne sera conservé")
    return gpd.GeoDataFrame(columns=gdf.columns, crs=gdf.crs)
