import pandas as pd
import geopandas as gpd
import pydeck as pdk
import utils as utils

file_path = './data/stations_bixi.geojson'
# file_path = './data/evaluation_fonciere_test.geojson'
gdf = gpd.read_file(file_path)

geometry_column = utils.check_geometry_column(gdf)
print(geometry_column)

check_geom_type = utils.check_geometry_type(gdf)

if check_geom_type == 'Point':
    point_layer = pdk.Layer(
        'ScatterplotLayer',
        data=gdf,
        get_position='[geometry.coordinates[0], geometry.coordinates[1]]',
        get_color='[200, 30, 0, 160]',
        get_radius=10,
        pickable=True
    )
    
    layers = [point_layer]
else:
    raise ValueError("Type de géométrie non supporté.")


# Configurer la vue
view_state = pdk.ViewState(
    latitude=gdf.geometry.centroid.y.mean(),
    longitude=gdf.geometry.centroid.x.mean(),
    zoom=50,
    pitch=0,
)

# Créer la carte
r = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    map_style='dark'
)

# Sauvegarder la carte en HTML
r.to_html('map.html', open_browser=True)






# if gdf.geom_type.unique().size == 1:
#     geom_type = gdf.geom_type.iloc[0]
# else:
#     raise ValueError("Les données contiennent plusieurs types de géométrie.")

# if geom_type == 'Polygon' or geom_type == 'MultiPolygon':
#     gdf['coordinates'] = gdf['geometry'].apply(lambda x: list(x.exterior.coords) if x.geom_type == 'Polygon' else list(x.representative_point().coords))
    
#     polygon_layer = pdk.Layer(
#         'PolygonLayer',
#         data=gdf,
#         get_polygon='coordinates',
#         get_fill_color='[200, 30, 0, 160]',
#         get_line_color='[255, 255, 255]',
#         get_line_width=2,
#         pickable=True
#     )
    
#     layers = [polygon_layer]
    
# elif geom_type == 'Point':
#     # Créer un layer pour les points
#     point_layer = pdk.Layer(
#         'ScatterplotLayer',
#         data=gdf,
#         get_position='[geometry.coordinates[0], geometry.coordinates[1]]',
#         get_color='[200, 30, 0, 160]',
#         get_radius=100,
#         pickable=True
#     )
    
#     layers = [point_layer]
# else:
#     raise ValueError("Type de géométrie non supporté.")