import utils.utils as utils
import utils.buffer.buffer as buffer
import utils.gdf.gdfExtraction as gdfExtraction
import utils.visualisation.visualisation as visualisation
import pandas as pd
import geopandas as gpd
import itertools
import plotly.graph_objects as go
import webbrowser

# Liste des fichiers de données
data_files = {
    "bus_stops": './data/input/stm_bus_stops.geojson',
    "bixi_stations": './data/input/stations_bixi.geojson',
    "evaluation_fonciere": './data/input/uniteevaluationfoncieretest.geojson'
}

# Nom de la couche : distance du buffer en mètres
buffer_layers = {
    "bixi_stations": 100
}

# Initialiser les listes de couches de points et de polygones
layers = []
colors = {'bus_stops': '[0, 200, 0, 160]', 'bixi_stations': '[200, 30, 0, 160]', 'evaluation_fonciere': '[0, 30, 200, 160]'}

# Charger tous les GeoDataFrames en une fois
geodataframes = utils.load_files_to_gdf(data_files)

gdf = gdfExtraction.process_geodataframes(geodataframes, utils)

# Créer les GeoDataFrames pour les points, les polygones et les buffers en dehors de la boucle de création de couches
points_gdfs = {layer_name: gdfExtraction.extract_points_gdf(gdf).assign(layer_name=layer_name) 
               for layer_name, gdf in geodataframes.items()}

polygons_gdfs = {layer_name: gdfExtraction.extract_polygons_gdf(gdf).assign(layer_name=layer_name) 
                 for layer_name, gdf in geodataframes.items()}

multipolygons_gdfs = {layer_name: gdfExtraction.extract_multipolygons_gdf(gdf).assign(layer_name=layer_name) 
                 for layer_name, gdf in geodataframes.items()}

# Créer les GeoDataFrames pour les buffers avec un nom de couche différent (e.g., 'bixi_stations_buffer')
unique_id_counter = itertools.count(1)
buffer_gdfs = {
    f"{layer_name}_buffer": buffer.apply_buffer(points_gdfs[layer_name], layer_name, buffer_layers)
                                   .assign(layer_name=f"{layer_name}_buffer",
                                           buffer_id=lambda df: [next(unique_id_counter) for _ in range(len(df))])
    for layer_name in buffer_layers
}

raw_fusion_gdf = gpd.GeoDataFrame(pd.concat([*points_gdfs.values(), *polygons_gdfs.values(), *multipolygons_gdfs.values(), *buffer_gdfs.values()], ignore_index=True))

##TODO: enlever la hardcoded
bus_stops_gdf = points_gdfs["bus_stops"]
evaluation_fonciere_gdf = polygons_gdfs["evaluation_fonciere"]

# Effectuer la jointure spatiale sur chaque buffer avec bus_stops et evaluation_fonciere
buffer_joins = []
##TODO: enlever la bus_stops et evaluation_fonciere
for layer_name, buffer_gdf in buffer_gdfs.items():
    # Jointure avec bus_stops
    bus_stops_join = gpd.sjoin(buffer_gdf, bus_stops_gdf, how="inner", predicate="contains").assign(buffer_layer=layer_name, join_type="bus_stops")
    buffer_joins.append(bus_stops_join)
    
    # Jointure avec evaluation_fonciere
    evaluation_fonciere_join = gpd.sjoin(buffer_gdf, evaluation_fonciere_gdf, how="inner", predicate="intersects").assign(buffer_layer=layer_name, join_type="evaluation_fonciere")
    buffer_joins.append(evaluation_fonciere_join)

# Concaténer tous les résultats de jointure en un seul DataFrame
agg_fusion_gdf = pd.concat(buffer_joins, ignore_index=True)

# Sélection des colonnes nécessaires et agrégation
agg_stats = agg_fusion_gdf.groupby(['buffer_id','name']).agg({
    'NOMBRE_LOGEMENT': ['min', 'max', 'mean'],
    'SUPERFICIE_BATIMENT': ['min', 'max', 'mean'],
    'SUPERFICIE_TERRAIN': ['min', 'max', 'mean'],
    'capacity': ['min', 'max', 'mean'],
    'stop_id': 'count' 
}).reset_index().round(2)

# Renommer les colonnes pour plus de lisibilité, si souhaité
agg_stats.columns = ['buffer_id', 'name',
                     'nb_log_min', 'nb_log_max', 'nb_log_moy',
                     'sup_bat_min', 'sup_bat_max', 'sup_bat_moy',
                     'sup_ter_min', 'sup_ter_max', 'sup_ter_moy',
                     'cap_station_min', 'cap_station_max', 'cap_station_moy',
                     'bus_stops_count']

print(agg_stats)

raw_fusion_gdf.to_csv("./data/ouput/data/raw_data_fusion_output.csv")
agg_fusion_gdf.to_csv("./data/ouput/data/agg_data_fusion_output.csv")

fig = go.Figure(data=[go.Table(
    header=dict(
        values=list(agg_stats.columns),
        font=dict(size=10),  # Réduit la taille de la police des en-têtes
        align="center"
    ),
    cells=dict(
        values=[agg_stats[col] for col in agg_stats.columns],
        align="left",
        height=50   # Ajuste la hauteur de chaque cellule pour plus de lisibilité
    )
)])

fig.update_layout(width=2000)  # Augmente la largeur totale du tableau
fig.write_html("./data/ouput/visualisation/tableau.html")

visualisation.create_layers_and_map(geodataframes, points_gdfs, polygons_gdfs, multipolygons_gdfs, buffer_gdfs, colors)