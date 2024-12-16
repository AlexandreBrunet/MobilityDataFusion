import geopandas as gpd
from shapely.geometry import Polygon

def apply_points_grid(points_gdf: gpd.GeoDataFrame, layer_name: str, grid_layers: dict) -> gpd.GeoDataFrame:
    grid_gdf = points_gdf.copy()
    
    # Vérifie si la couche correspond à une entrée dans le dictionnaire des grilles
    if layer_name in grid_layers:
        cell_width = grid_layers[layer_name].get("wide", 100)  # Largeur par défaut : 100m
        cell_height = grid_layers[layer_name].get("length", 100)  # Hauteur par défaut : 100m
        geometry_type = grid_layers[layer_name].get("geometry_type", None)
        
        # Vérifie si le type de géométrie est un Point
        if geometry_type == "Point":
            try:
                # Vérifie que toutes les géométries sont de type Point
                if not all(grid_gdf.geometry.geom_type == "Point"):
                    raise ValueError("Certaines géométries ne sont pas de type Point.")

                # Reprojeter en CRS UTM pour calculer en mètres
                grid_gdf = grid_gdf.to_crs(epsg=32618)  # Adapter l'EPSG à votre région
                
                # Créer une liste de polygones centrés sur chaque point
                polygons = []
                for point in grid_gdf.geometry:
                    x, y = point.x, point.y
                    polygons.append(Polygon([
                        (x - cell_width / 2, y - cell_height / 2), 
                        (x + cell_width / 2, y - cell_height / 2), 
                        (x + cell_width / 2, y + cell_height / 2), 
                        (x - cell_width / 2, y + cell_height / 2)
                    ]))
                
                # Ajouter les polygones au GeoDataFrame
                grid_gdf['geometry'] = polygons

                # Reprojeter en WGS 84 pour revenir aux coordonnées d'origine
                grid_gdf = grid_gdf.to_crs(epsg=4326)
            
            except Exception as e:
                print(f"Erreur lors de la reprojection ou de la création de la grille : {e}")
        else:
            print(f"Le type de géométrie '{geometry_type}' n'est pas supporté pour cette couche.")
    
    return grid_gdf