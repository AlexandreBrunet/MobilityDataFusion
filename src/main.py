import pydeck as pdk
import utils.utils as utils
import utils.visualisation as visualisation
import utils.buffer as buffer
import geopandas as gpd

first_df = './data/bus_stops.geojson'

first_gdf = gpd.read_file(first_df)

first_gdf = first_gdf.set_crs(epsg=2950, allow_override=True)
first_gdf = first_gdf.to_crs(epsg=4326)

first_gdf['lon'] = first_gdf.geometry.x
first_gdf['lat'] = first_gdf.geometry.y

second_df = './data/stations_bixi.geojson'

second_gdf = gpd.read_file(second_df)
second_gdf = second_gdf.to_crs(epsg=4326)

second_gdf['lon'] = second_gdf.geometry.x
second_gdf['lat'] = second_gdf.geometry.y


initial_view = visualisation.create_initial_view(first_gdf)

rouge = '[200, 30, 0, 160]'
bleu = '[0, 30, 200, 160]'
first_layer = visualisation.create_point_layer(first_gdf, rouge)
second_layer = visualisation.create_point_layer(second_gdf, bleu)
visualisation.create_map_layers([first_layer, second_layer], initial_view)