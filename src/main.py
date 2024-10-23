import utils.utils as utils
import geopandas as gpd
import pydeck as pdk
import utils.utils as utils
import utils.visualisation as visualisation

# Paths to data files
bus_stops_file = './data/bus_stops.geojson'
bixi_stations_file = './data/stations_bixi.geojson'

# Load GeoJSON data
bus_stops_gdf = gpd.read_file(bus_stops_file)
bixi_stations_gdf = gpd.read_file(bixi_stations_file)

# Prepare the GeoDataFrames
bus_stops_gdf = utils.prepare_gdf(bus_stops_gdf)
bixi_stations_gdf = utils.prepare_gdf(bixi_stations_gdf)

# Buffer with a proper CRS (this avoids the warning)
buffer_gdf = bixi_stations_gdf.copy()
buffer_gdf = buffer_gdf.to_crs(epsg=32618)  # Changer le CRS pour le buffer
buffer_gdf['geometry'] = buffer_gdf['geometry'].buffer(100)  # Créer le buffer

bus_stops_gdf = bus_stops_gdf.to_crs(epsg=4326)
bixi_stations_gdf = bixi_stations_gdf.to_crs(epsg=4326)

buffer_gdf = buffer_gdf[['geometry']]
buffer_gdf = buffer_gdf.to_crs(epsg=4326)
buffer_gdf['buffer_coordinates'] = buffer_gdf['geometry'].apply(lambda geom: geom.__geo_interface__['coordinates'])


initial_view = visualisation.create_initial_view()

color_red = '[200, 30, 0, 160]'
color_green = '[0, 200, 0, 160]'
color_blue = '[0, 30, 200, 160]'

bus_stops_layer = visualisation.create_point_layer(bus_stops_gdf, color_red)
bixi_stations_layer = visualisation.create_point_layer(bixi_stations_gdf, color_green)
buffer_layer = visualisation.create_polygon_layer(buffer_gdf)

visualisation.create_map_layers([buffer_layer, bus_stops_layer, bixi_stations_layer], initial_view)