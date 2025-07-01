import utils.buffer.buffer as buffer
from typing import Dict, Union
import geopandas as gpd
import os

def calculate_buffer(buffer_layer: Dict[str, Dict[str, str]], points_gdfs: gpd.GeoDataFrame, polygons_gdfs: gpd.GeoDataFrame, multipolygons_gdfs: gpd.GeoDataFrame, linestrings_gdfs: gpd.GeoDataFrame) -> Union[gpd.GeoDataFrame, None]:
    for layer_name in buffer_layer:
        geometry_type = buffer_layer[layer_name].get('geometry_type', None)
        buffer_type = buffer_layer[layer_name].get('buffer_type', None)
        distance = buffer_layer[layer_name].get('distance', None)
        wide = buffer_layer[layer_name].get('wide', None)
        length = buffer_layer[layer_name].get('length', None)

        if geometry_type == "Point":
            buffer_gdfs = buffer.create_buffers(points_gdfs, buffer_layer)
            if buffer_type == "grid":
                save_buffers_to_geojson(buffer_type, wide, buffer_gdfs)
            else:
                save_buffers_to_geojson(buffer_type, distance, buffer_gdfs)
        elif geometry_type == "Polygon":
            buffer_gdfs = buffer.create_buffers(polygons_gdfs, buffer_layer)
            if buffer_type == "grid":
                save_buffers_to_geojson(buffer_type, wide, buffer_gdfs)
            else:
                save_buffers_to_geojson(buffer_type, distance, buffer_gdfs)
        elif geometry_type == "MultiPolygon":
            buffer_gdfs = buffer.create_buffers(multipolygons_gdfs, buffer_layer)
            if buffer_type == "grid":
                save_buffers_to_geojson(buffer_type, wide, buffer_gdfs)
            else:
                save_buffers_to_geojson(buffer_type, distance, buffer_gdfs)
        elif geometry_type == "LineString":
            buffer_gdfs = buffer.create_buffers(linestrings_gdfs, buffer_layer)
            if buffer_type == "grid":
                save_buffers_to_geojson(buffer_type, wide, buffer_gdfs)
            else:
                save_buffers_to_geojson(buffer_type, distance, buffer_gdfs)
        else:
            print("The geometry_type is unsupported either: Point, LineString, Polygon or MultiPolygon")

    return buffer_gdfs

def save_buffers_to_geojson(buffer_type, distance, buffer_gdfs, output_dir="./data/output/data/buffers"):
    os.makedirs(output_dir, exist_ok=True)

    for layer_name, gdf in buffer_gdfs.items():
        output_path = os.path.join(output_dir, f"{layer_name}_{buffer_type}_{distance}m.geojson")
        gdf.to_file(output_path, driver="GeoJSON")
        print(f"{layer_name} saved to {output_path}")