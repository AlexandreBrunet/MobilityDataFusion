
import utils.buffer.buffer as buffer

def calculate_buffer(buffer_layer, points_gdfs, polygons_gdfs, multipolygons_gdfs, linestrings_gdfs):
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