
import utils.gdf.gdfExtraction as gdfExtraction
import itertools
import utils.buffer.buffer as buffer

def extract_geometries(geodataframes):
    points_gdfs = {layer_name: gdfExtraction.extract_points_gdf(gdf).assign(layer_name=layer_name) 
                   for layer_name, gdf in geodataframes.items()}
    polygons_gdfs = {layer_name: gdfExtraction.extract_polygons_gdf(gdf).assign(layer_name=layer_name) 
                     for layer_name, gdf in geodataframes.items()}
    multipolygons_gdfs = {layer_name: gdfExtraction.extract_multipolygons_gdf(gdf).assign(layer_name=layer_name) 
                          for layer_name, gdf in geodataframes.items()}
    return points_gdfs, polygons_gdfs, multipolygons_gdfs

def create_buffers(points_gdfs, buffer_layers):
    unique_id_counter = itertools.count(1)
    buffer_gdfs = {
        f"{layer_name}_buffer": buffer.apply_buffer(points_gdfs[layer_name], layer_name, buffer_layers)
                                       .assign(layer_name=f"{layer_name}_buffer",
                                               buffer_id=lambda df: [next(unique_id_counter) for _ in range(len(df))])
        for layer_name in buffer_layers
    }
    return buffer_gdfs