
import utils.buffer.buffer as buffer
from typing import Dict, Union
import geopandas as gpd

def calculate_buffer(buffer_layer: Dict[str, Dict[str, str]], points_gdfs: gpd.GeoDataFrame, polygons_gdfs: gpd.GeoDataFrame, multipolygons_gdfs: gpd.GeoDataFrame, linestrings_gdfs: gpd.GeoDataFrame) -> Union[gpd.GeoDataFrame, None]:
    for layer_name in buffer_layer:
        geometry_type = buffer_layer[layer_name].get('geometry_type', None)

        if geometry_type == "Point":
            buffer_gdfs = buffer.create_buffers(points_gdfs, buffer_layer)
        elif geometry_type == "Polygon":
            buffer_gdfs = buffer.create_buffers(polygons_gdfs, buffer_layer)
        elif geometry_type == "MultiPolygon":
            buffer_gdfs = buffer.create_buffers(multipolygons_gdfs, buffer_layer)
        elif geometry_type == "LineString":
            buffer_gdfs = buffer.create_buffers(linestrings_gdfs, buffer_layer)
        else:
            print("The geometry_type is unsupported either: Point, LineString, Polygon or MultiPolygon")

    return buffer_gdfs