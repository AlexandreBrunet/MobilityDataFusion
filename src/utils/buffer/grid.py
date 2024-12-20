import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import box

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

def apply_zones_grid(zones_gdf: gpd.GeoDataFrame, layer_name: str, grid_layers: dict) -> gpd.GeoDataFrame:
    # Vérifier si la couche correspond à une entrée dans le dictionnaire des grilles
    if layer_name not in grid_layers:
        raise ValueError(f"La couche '{layer_name}' n'est pas définie dans grid_layers.")

    # Récupérer les dimensions de la cellule depuis grid_layers
    cell_width = grid_layers[layer_name].get("wide", 100)  # Largeur par défaut : 100m
    cell_height = grid_layers[layer_name].get("length", 100)  # Hauteur par défaut : 100m

    # Définir le CRS initial si nécessaire
    if zones_gdf.crs is None:
        zones_gdf.set_crs(epsg=4326, inplace=True)  # Par défaut, WGS84

    # Convertir en projection métrique
    if not zones_gdf.crs.is_projected:
        zones_gdf = zones_gdf.to_crs(epsg=32618)  # CRS métrique pour UTM zone 18N

    # Obtenir les limites de l'enveloppe
    xmin, ymin, xmax, ymax = zones_gdf.total_bounds

    # Créer une liste pour stocker les géométries des grilles
    grid_polygons = []

    # Générer la grille
    x_coords = range(int(xmin), int(xmax), cell_width)
    y_coords = range(int(ymin), int(ymax), cell_height)

    for x in x_coords:
        for y in y_coords:
            grid_cell = box(x, y, x + cell_width, y + cell_height)
            # Vérifier si la cellule intersecte au moins une géométrie du GeoDataFrame
            if zones_gdf.intersects(grid_cell).any():
                grid_polygons.append(grid_cell)

    # Créer un GeoDataFrame pour la grille
    grid_gdf = gpd.GeoDataFrame(geometry=grid_polygons, crs=zones_gdf.crs)

    # Reprojeter la grille en WGS84 si nécessaire
    grid_gdf = grid_gdf.to_crs(epsg=4326)

    return grid_gdf