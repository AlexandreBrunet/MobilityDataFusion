import utils.utils as utils
import geopandas as gpd
import utils.visualisation as visualisation
import fiona
from shapely.geometry import shape
import pydeck as pdk

# Liste des fichiers de données
data_files = {
    "bus_stops": './data/bus_stops.geojson',
    "bixi_stations": './data/stations_bixi.geojson',
    "evaluation_fonciere": './data/uniteevaluationfoncieretest.geojson'
}

# Initialiser les listes de couches de points et de polygones
layers = []
colors = {'bus_stops': '[0, 200, 0, 160]', 'bixi_stations': '[200, 30, 0, 160]', 'evaluation_fonciere': '[0, 30, 200, 160]'}


geodataframes = utils.load_files_to_gdf(data_files)

for name, gdf in geodataframes:   
    # Déterminer le CRS en fonction des coordonnées si le CRS est absent
    if gdf.crs is None:
        gdf.set_crs(utils.determine_crs(gdf), inplace=True)
    
    # Convertir en EPSG:4326 si nécessaire
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    # Remplir les valeurs manquantes par 0
    gdf = gdf.fillna(0)

    # Séparer points et polygones
    points_gdf = gdf[gdf.geometry.type == "Point"].copy()
    if not points_gdf.empty:
        points_gdf['lon'] = points_gdf.geometry.x
        points_gdf['lat'] = points_gdf.geometry.y
        points_layer = visualisation.create_point_layer(points_gdf, colors[name])
        layers.append(points_layer)

        if name == "bixi_stations":
            buffer_gdf = points_gdf.copy()
            buffer_gdf = buffer_gdf.to_crs(epsg=32618)  # Changer le CRS pour le buffer
            buffer_gdf['geometry'] = buffer_gdf['geometry'].buffer(100)
            buffer_gdf = buffer_gdf.to_crs(epsg=4326)
            buffer_gdf['coordinates'] = buffer_gdf['geometry'].apply(lambda geom: geom.__geo_interface__['coordinates'])
            buffer_layer = visualisation.create_polygon_layer(buffer_gdf, '[200, 100, 50, 60]')
            layers.append(buffer_layer)

    polygons_gdf = gdf[gdf.geometry.type == "Polygon"].copy()
    if not polygons_gdf.empty:
        polygons_gdf['coordinates'] = polygons_gdf['geometry'].apply(lambda geom: geom.__geo_interface__['coordinates'])
        polygons_layer = visualisation.create_polygon_layer(polygons_gdf, colors[name])
        layers.append(polygons_layer)

# Initialiser la vue de la carte
initial_view = visualisation.create_initial_view()

# Créer la carte avec les couches de points, polygones et buffers
visualisation.create_map_layers(layers, initial_view)