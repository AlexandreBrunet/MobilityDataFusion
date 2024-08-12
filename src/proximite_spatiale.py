import pandas as pd
import geopandas as gpd
import pydeck as pdk
import utils as utils

file_path = './data/stations_bixi.geojson'

gdf = gpd.read_file(file_path)

geometry_column = utils.check_geometry_column(gdf)

check_geom_type = utils.check_geometry_type(gdf)

# Créer un buffer de 100 mètres autour de chaque point
gdf['buffer'] = gdf.geometry.buffer(0.001)

# Convertir le GeoDataFrame en DataFrame compatible avec pydeck
gdf = gdf.to_crs(epsg=4326)  # S'assurer que les coordonnées sont en lat/lon
gdf['lon'] = gdf.geometry.x
gdf['lat'] = gdf.geometry.y

# Extraire les coordonnées du buffer sous forme de liste de listes
gdf['buffer_coordinates'] = gdf['buffer'].apply(lambda geom: [[x, y] for x, y in zip(geom.exterior.coords.xy[0], geom.exterior.coords.xy[1])])
print(gdf.head(10))

# Sélectionner les colonnes nécessaires pour éviter d'avoir des objets complexes
df = gdf[['name', 'capacity', 'lon', 'lat', 'buffer_coordinates']].copy()

# Création de la couche pour les points
point_layer = pdk.Layer(
    'ScatterplotLayer',
    data=df,
    get_position='[lon, lat]',
    get_color='[200, 30, 0, 160]',
    get_radius=10,
    pickable=True
)

# Création de la couche pour les buffers
buffer_layer = pdk.Layer(
    'PolygonLayer',
    data=df,
    get_polygon='buffer_coordinates',
    get_fill_color='[0, 0, 200, 50]',
    get_line_color='[0, 0, 200, 200]',
    pickable=True
)

# Définition de la vue initiale
view_state = pdk.ViewState(
    latitude=df['lat'].mean(),
    longitude=df['lon'].mean(),
    zoom=14,
    pitch=0,
)

# Création de la carte avec les deux couches
r = pdk.Deck(
    layers=[point_layer, buffer_layer],
    initial_view_state=view_state,
    map_style='dark'
)

# Exporter la carte en HTML et l'ouvrir dans le navigateur
r.to_html('map.html', open_browser=True)
