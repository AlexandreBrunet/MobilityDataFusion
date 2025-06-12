import geopandas as gpd
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union

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

def apply_line_grid(line_gdf: gpd.GeoDataFrame, layer_name: str, grid_layers: dict) -> gpd.GeoDataFrame:
    """
    Crée une grille rectangulaire centrée sur le centroïde de la ligne avec les dimensions spécifiées.
    Basée sur la structure de apply_linestring_buffer mais pour une grille.
    
    Args:
        line_gdf: GeoDataFrame contenant les lignes
        layer_name: Nom de la couche pour récupérer les paramètres
        grid_layers: Dictionnaire des paramètres de grille
        
    Returns:
        GeoDataFrame contenant une seule cellule de grille centrée sur le centroïde
    """
    grid_gdf = line_gdf.copy()
    
    # Vérifie si la couche est configurée
    if layer_name in grid_layers:
        cell_width = grid_layers[layer_name].get("wide", 100)  # Largeur par défaut: 100m
        cell_height = grid_layers[layer_name].get("length", 100)  # Hauteur par défaut: 100m
        geometry_type = grid_layers[layer_name].get("geometry_type", None)
        
        # Vérifie le type de géométrie
        if geometry_type == "LineString":
            try:
                # Vérification des géométries
                if not all(grid_gdf.geometry.geom_type == "LineString"):
                    raise ValueError("Toutes les géométries doivent être des LineString")
                
                # Conversion en CRS projeté (UTM)
                original_crs = grid_gdf.crs
                if not grid_gdf.crs.is_projected:
                    grid_gdf = grid_gdf.to_crs(epsg=32618)  # UTM zone 18N
                
                # Calcul du centroïde global
                combined_line = unary_union(grid_gdf.geometry)
                centroid = combined_line.centroid
                
                # Création de la grille rectangulaire centrée
                half_width = cell_width / 2
                half_height = cell_height / 2
                
                grid_cell = box(
                    centroid.x - half_width,
                    centroid.y - half_height,
                    centroid.x + half_width,
                    centroid.y + half_height
                )
                
                # Création du GeoDataFrame résultat
                result_gdf = gpd.GeoDataFrame(geometry=[grid_cell], crs=grid_gdf.crs)
                
                # Conversion de retour au CRS original si nécessaire
                if original_crs is not None:
                    result_gdf = result_gdf.to_crs(original_crs)
                
                return result_gdf
                
            except Exception as e:
                print(f"Erreur lors de la création de la grille: {e}")
                return grid_gdf
        else:
            print(f"Type de géométrie '{geometry_type}' non supporté pour cette couche")
    
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



##TODO REVOIR CETTE FONCTION QUI TRACE DES GRILLES AUTOUR DE L'OBJET AU COMPLET 
# def apply_line_grid(line_gdf: gpd.GeoDataFrame, layer_name: str, grid_layers: dict) -> gpd.GeoDataFrame:
#     """
#     Crée une grille rectangulaire autour des lignes d'un GeoDataFrame.
    
#     Args:
#         line_gdf: GeoDataFrame contenant les lignes à griller
#         layer_name: Nom de la couche pour récupérer les paramètres
#         grid_layers: Dictionnaire des paramètres de grille
        
#     Returns:
#         GeoDataFrame contenant les cellules de la grille intersectant les lignes
#     """
#     grid_gdf = line_gdf.copy()
    
#     # Vérifie si la couche est dans le dictionnaire des grilles
#     if layer_name in grid_layers:
#         cell_width = grid_layers[layer_name].get("wide", 100)  # Largeur par défaut : 100m
#         cell_height = grid_layers[layer_name].get("length", 100)  # Hauteur par défaut : 100m
#         geometry_type = grid_layers[layer_name].get("geometry_type", None)
        
#         # Vérifie si le type de géométrie est LineString
#         if geometry_type == "LineString":
#             try:
#                 # Vérifie que toutes les géométries sont de type LineString
#                 if not all(grid_gdf.geometry.geom_type == "LineString"):
#                     raise ValueError("Certaines géométries ne sont pas de type LineString.")

#                 # Reprojeter en CRS projeté pour calculer en mètres
#                 original_crs = grid_gdf.crs
#                 if not grid_gdf.crs.is_projected:
#                     grid_gdf = grid_gdf.to_crs(epsg=32618)  # UTM zone 18N - adapter à votre région
                
#                 # Obtenir les limites de toutes les lignes combinées
#                 xmin, ymin, xmax, ymax = grid_gdf.total_bounds
                
#                 # Créer une liste pour stocker les cellules de la grille
#                 grid_polygons = []
                
#                 # Générer les coordonnées de la grille
#                 x_coords = range(int(xmin), int(xmax) + cell_width, cell_width)
#                 y_coords = range(int(ymin), int(ymax) + cell_height, cell_height)
                
#                 # Créer les cellules de la grille
#                 for x in x_coords:
#                     for y in y_coords:
#                         cell = box(x, y, x + cell_width, y + cell_height)
#                         # Garder seulement les cellules qui intersectent une ligne
#                         if grid_gdf.intersects(cell).any():
#                             grid_polygons.append(cell)
                
#                 # Créer un nouveau GeoDataFrame avec la grille
#                 grid_gdf = gpd.GeoDataFrame(geometry=grid_polygons, crs=grid_gdf.crs)
                
#                 # Reprojeter dans le CRS d'origine si nécessaire
#                 if original_crs is not None:
#                     grid_gdf = grid_gdf.to_crs(original_crs)
            
#             except Exception as e:
#                 print(f"Erreur lors de la création de la grille pour les lignes : {e}")
#         else:
#             print(f"Le type de géométrie '{geometry_type}' n'est pas supporté pour cette couche.")
    
#     return grid_gdf