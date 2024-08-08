import pandas as pd
import geopandas as gpd
import pydeck as pdk

# Lire le fichier GeoJSON
file_path = './data/test.geojson'
gdf = gpd.read_file(file_path)

# Convertir les données GeoPandas en DataFrame pandas
df = pd.DataFrame(gdf.drop(columns='geometry'))
df['lon'] = gdf.centroid.x
df['lat'] = gdf.centroid.y

# Vérifier les données après conversion
print(df.head())

# Créer la couche Pydeck pour les points
scatter_layer = pdk.Layer(
    'ScatterplotLayer',
    data=df,
    get_position='[lon, lat]',
    get_fill_color='[200, 30, 0, 160]',
    get_radius=100,
    pickable=True
)

# Créer la vue initiale de la carte
view_state = pdk.ViewState(
    latitude=df['lat'].mean(),
    longitude=df['lon'].mean(),
    zoom=10,
    pitch=0,
)

# Créer la carte Pydeck
r = pdk.Deck(
    layers=[scatter_layer],
    initial_view_state=view_state,
    map_style='dark'
)

# Afficher la carte
r.to_html('map.html', open_browser=True)
