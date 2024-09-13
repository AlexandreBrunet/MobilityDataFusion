import pydeck as pdk
import utils.utils as utils
import utils.visualisation as visualisation
import utils.buffer as buffer
import geopandas as gpd

# Paths to data files
bus_stops_file = './data/bus_stops.geojson'
bixi_stations_file = './data/stations_bixi.geojson'

# Load GeoJSON data
bus_stops_gdf = gpd.read_file(bus_stops_file)
bixi_stations_gdf = gpd.read_file(bixi_stations_file)

# Prepare the GeoDataFrames
bus_stops_gdf = utils.prepare_gdf(bus_stops_gdf)
bixi_stations_gdf = utils.prepare_gdf(bixi_stations_gdf)

# Create buffer for BIXI stations
bixi_buffer_gdf = buffer.buffer_oiseau(bixi_stations_gdf, 'buffer', 0.001)
bixi_buffer_gdf = utils.prepare_gdf(bixi_buffer_gdf)

# Extract buffer coordinates for visualization
bixi_buffer_gdf['buffer_coordinates'] = bixi_buffer_gdf['buffer'].apply(
    lambda geom: [[x, y] for x, y in zip(geom.exterior.coords.xy[0], geom.exterior.coords.xy[1])]
)

# Select only the necessary columns for buffer GeoDataFrame
buffer_gdf = bixi_buffer_gdf[['name', 'lon', 'lat', 'buffer_coordinates']].copy()

# Drop unnecessary 'buffer' column from BIXI stations GeoDataFrame
bixi_stations_gdf = bixi_stations_gdf.drop(columns=['buffer'])

# Create initial map view
initial_view = visualisation.create_initial_view(bus_stops_gdf)

# Define colors
color_red = '[200, 30, 0, 160]'
color_green = '[0, 200, 0, 160]'
color_blue = '[0, 30, 200, 160]'

# Create map layers
bus_stops_layer = visualisation.create_point_layer(bus_stops_gdf, color_red)
bixi_stations_layer = visualisation.create_point_layer(bixi_stations_gdf, color_green)
buffer_layer = visualisation.create_polygon_layer(buffer_gdf)

# Render the map with all layers
visualisation.create_map_layers([bus_stops_layer, bixi_stations_layer, buffer_layer], initial_view)
