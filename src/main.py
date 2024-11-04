import utils.utils as utils
import utils.buffer as buffer
import utils.gdfExtraction as gdfExtraction
import geopandas as gpd
import utils.visualisation as visualisation
import fiona
from shapely.geometry import shape
import pydeck as pdk

# Liste des fichiers de données
data_files = {
    "bus_stops": './data/stm_bus_stops.geojson',
    "bixi_stations": './data/stations_bixi.geojson',
    "evaluation_fonciere": './data/uniteevaluationfoncieretest.geojson'
}

# Nom de la couche : distance du buffer en mètres
buffer_layers = {
    "bixi_stations": 100
}

# Initialiser les listes de couches de points et de polygones
layers = []
colors = {'bus_stops': '[0, 200, 0, 160]', 'bixi_stations': '[200, 30, 0, 160]', 'evaluation_fonciere': '[0, 30, 200, 160]'}


geodataframes = utils.load_files_to_gdf(data_files)

for layer_name, gdf in geodataframes:   
    # Déterminer le CRS en fonction des coordonnées si le CRS est absent
    if gdf.crs is None:
        gdf.set_crs(utils.determine_crs(gdf), inplace=True)
    
    # Convertir en EPSG:4326 si nécessaire
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    # Remplir les valeurs manquantes par 0
    gdf = gdf.fillna(0)

    # Séparer points et polygones

    points_gdf = gdfExtraction.extract_points_gdf(gdf)
    points_layer = visualisation.create_point_layer(points_gdf, colors[layer_name])

    polygons_gdf = gdfExtraction.extract_polygons_gdf(gdf)
    polygons_layer = visualisation.create_polygon_layer(polygons_gdf, colors[layer_name])

    layers.append(points_layer)
    layers.append(polygons_layer)

    buffer_gdf = buffer.apply_buffer(points_gdf, layer_name, buffer_layers)
    buffer_gdf = gdfExtraction.extract_poly_coordinates(buffer_gdf)
    buffer_layer = visualisation.create_polygon_layer(buffer_gdf, '[200, 100, 50, 60]')
    layers.append(buffer_layer)


# Initialiser la vue de la carte
initial_view = visualisation.create_initial_view()

# Créer la carte avec les couches de points, polygones et buffers
visualisation.create_map_layers(layers, initial_view)

##les gens vont vouloir un gros ficher avec toutes les colonnes