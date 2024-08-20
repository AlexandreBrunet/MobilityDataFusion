import pydeck as pdk
import geopandas as gpd
from typing import List

def create_initial_view(gdf: gpd.GeoDataFrame) -> pdk.ViewState:
    view_state = pdk.ViewState(
        latitude=gdf['lat'].mean(),
        longitude=gdf['lon'].mean(),
        zoom=14,
        pitch=0,
        )
    return view_state

def create_point_layer(gdf: gpd.GeoDataFrame, color: List[int]):
    point_layer = pdk.Layer(
        'ScatterplotLayer',
        data=gdf,
        get_position='[lon, lat]',
        get_color=color,
        get_radius=10,
        pickable=True
        )
    return point_layer

#TODO: FIX COLOR
def create_polygon_layer(gdf: gpd.GeoDataFrame):
    polygon_layer = pdk.Layer(
        'PolygonLayer',
        data=gdf,
        get_polygon='buffer_coordinates',
        get_fill_color='[0, 0, 200, 50]',
        get_line_color='[0, 0, 200, 200]',
        pickable=True
        )
    return polygon_layer


def create_map_layers(layers: List[pdk.Layer], view_state: pdk.ViewState):
    r = pdk.Deck(
        layers= layers,
        initial_view_state=view_state,
        map_style='dark'
        )
    r.to_html('map.html', open_browser=True)


# second_df['coordinates'] = second_df['geometry'].apply(lambda geom: [[x, y] for x, y in zip(geom.exterior.coords.xy[0], geom.exterior.coords.xy[1])])
# second_layer = pdk.Layer(
#     'PolygonLayer',
#     data=second_df,
#     get_polygon='coordinates',
#     get_fill_color='[0, 255, 0, 50]',
#     get_line_color='[0, 255, 0, 200]',
#     pickable=True
# )