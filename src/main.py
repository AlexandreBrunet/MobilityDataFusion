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