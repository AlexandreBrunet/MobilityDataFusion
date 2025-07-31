import geopandas as gpd
from shapely.geometry import LineString, Polygon
import pandas as pd

def calculate_geometric_proportions(geometry: gpd.GeoSeries, buffer_geometry: gpd.GeoSeries) -> gpd.GeoSeries:
    """
    Calcule la proportion d'inclusion (aire ou longueur) d'une géométrie dans un buffer de manière vectorisée.

    Parameters
    ----------
    geometry : gpd.GeoSeries
        Géométries à évaluer.
    buffer_geometry : gpd.GeoSeries
        Buffers correspondants.

    Returns
    -------
    gpd.GeoSeries
        Proportions (float entre 0 et 1).
    """
    intersections = geometry.intersection(buffer_geometry, align=False)

    proportions = []
    for geom, buf, inter in zip(geometry, buffer_geometry, intersections):
        if geom.is_empty or inter.is_empty:
            proportions.append(0.0)
        elif isinstance(geom, LineString):
            length = geom.length
            inter_length = inter.length
            proportions.append(round(inter_length / length, 4) if length > 0 else 0.0)
        elif isinstance(geom, Polygon):
            area = geom.area
            inter_area = inter.area
            proportions.append(round(inter_area / area, 4) if area > 0 else 0.0)
        else:
            proportions.append(1.0 if buf.contains(geom) else 0.0)

    return pd.Series(proportions, index=geometry.index)