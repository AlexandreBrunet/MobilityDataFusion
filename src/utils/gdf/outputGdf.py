import os
import geopandas as gpd

def process_and_save_joined_data(gdf: gpd.GeoDataFrame, output_folder: str):
    """
    Traite et sauvegarde les données jointes par `buffer_layer` et `join_type`.
    Préserve toutes les propriétés des couches tout en gérant les géométries multiples.

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame contenant les données.
        output_folder (str): Chemin du dossier de sortie.
    """
    # Créer le dossier de sortie si nécessaire
    os.makedirs(output_folder, exist_ok=True)

    # Vérifier les colonnes nécessaires
    if "buffer_layer" not in gdf.columns or "join_type" not in gdf.columns:
        raise ValueError("Le GeoDataFrame doit contenir les colonnes 'buffer_layer' et 'join_type'.")

    # Identifier les colonnes de géométrie dynamiques basées sur '_geometry'
    geometry_columns = [col for col in gdf.columns if col.endswith('_geometry')]

    if not geometry_columns:
        raise ValueError("Aucune colonne géométrique détectée avec le suffixe '_geometry'.")

    # Supprimer les suffixes `_left` et `_right` dans les noms de colonnes
    gdf.columns = [col.replace('_left', '').replace('_right', '') for col in gdf.columns]

    # Grouper par `buffer_layer` et `join_type`
    for (buffer_layer, join_type), group in gdf.groupby(['buffer_layer', 'join_type']):
        for geom_col in geometry_columns:
            if geom_col in group:
                # Filtrer les lignes avec une géométrie non nulle
                non_empty = group[group[geom_col].notnull()].copy()

                # Si le DataFrame est vide après le filtrage, ne pas sauvegarder
                if non_empty.empty:
                    print(f"Aucun enregistrement trouvé pour {buffer_layer}_{join_type}_{geom_col}")
                    continue  # Passer à l'itération suivante si le groupe est vide

                # Renommer temporairement la colonne géométrique
                non_empty = non_empty.rename(columns={geom_col: 'geometry_temp'})
                non_empty = gpd.GeoDataFrame(non_empty, geometry='geometry_temp', crs=gdf.crs)

                # Supprimer la colonne 'geometry' si elle existe déjà
                if 'geometry' in non_empty.columns:
                    non_empty = non_empty.drop(columns=['geometry'])

                # Renommer la géométrie temporaire en `geometry`
                non_empty = non_empty.rename_geometry('geometry')

                # Conserver `buffer_id` et toutes les autres colonnes importantes
                keep_columns = ['geometry', 'buffer_id', 'buffer_layer', 'join_type']
                non_empty = non_empty[keep_columns]

                # Définir le nom du fichier de sortie
                output_file = os.path.join(
                    output_folder,
                    f"{buffer_layer}_{geom_col.replace('_geometry', '')}.geojson"
                )

                # Sauvegarder en GeoJSON
                non_empty.to_file(output_file, driver="GeoJSON")
                print(f"Enregistré : {output_file}")