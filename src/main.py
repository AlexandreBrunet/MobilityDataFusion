import pydeck as pdk
import utils.utils as utils
import utils.visualisation as visualisation
import utils.buffer as buffer
import geopandas as gpd

first_df = './data/bus_stops.geojson'
second_df = './data/stations_bixi.geojson'

first_gdf = gpd.read_file(first_df)
second_gdf = gpd.read_file(second_df)

first_gdf = utils.check_and_correct_crs(first_gdf)
second_gdf = utils.check_and_correct_crs(second_gdf)

first_gdf = utils.add_lon_lat_columns(first_gdf)
second_gdf = utils.add_lon_lat_columns(second_gdf)

buffer_gdf = buffer.buffer_oiseau(second_gdf, 'buffer', 0.001)
buffer_gdf = buffer_gdf.to_crs(epsg=4326)
buffer_gdf['lon'] = buffer_gdf.geometry.x
buffer_gdf['lat'] = buffer_gdf.geometry.y
buffer_gdf['buffer_coordinates'] = buffer_gdf['buffer'].apply(lambda geom: [[x, y] for x, y in zip(geom.exterior.coords.xy[0], geom.exterior.coords.xy[1])])

second_gdf = second_gdf.drop(columns=['buffer'])

buffer_gdf = buffer_gdf[['name','lon', 'lat', 'buffer_coordinates']].copy()

initial_view = visualisation.create_initial_view(first_gdf)
vert = '[0, 200, 0, 160]'
rouge = '[200, 30, 0, 160]'
bleu = '[0, 30, 200, 160]'
first_layer = visualisation.create_point_layer(first_gdf, rouge)
second_layer = visualisation.create_point_layer(second_gdf, vert)
buffer_layer = visualisation.create_polygon_layer(buffer_gdf)
visualisation.create_map_layers([first_layer, second_layer, buffer_layer], initial_view)


# print(gdf.head(10))
# print(len(gdf))
# print(second_df.head(10))
# print(len(second_df))

# joined_gdf = gpd.sjoin(gdf.set_geometry('buffer'), second_df, how="inner", predicate='intersects')
# print(joined_gdf.head(10))
# print(len(joined_gdf))

# joined_gdf.to_excel('test.xlsx', index=False)