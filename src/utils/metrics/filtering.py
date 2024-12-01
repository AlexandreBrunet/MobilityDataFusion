import operator

OPERATORS = {
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    ">": operator.gt,
    "<": operator.lt,
    "!=": operator.ne
}

def filter_gdf(gdf, column, value, op):
    """Filtre un GeoDataFrame selon une colonne, une valeur et un opérateur."""
    if op not in OPERATORS:
        raise ValueError(f"Opérateur non valide : {op}. Choisissez parmi {list(OPERATORS.keys())}.")
    
    gdf_filtered = gdf[OPERATORS[op](gdf[column], value)]
    return gdf_filtered


def apply_layer_filtering(gdf, config, layer_name):
    """Applique le filtrage à une couche spécifique selon la configuration."""
    filter_config = config['filter_files'].get(layer_name)
    
    if filter_config:
        column = filter_config['column']
        value = filter_config['value']
        op = filter_config.get('operator', "==")  # Par défaut, utiliser l'égalité
        return filter_gdf(gdf, column, value, op)
    else:
        print(f"Aucun filtre trouvé pour la couche: {layer_name}")
        return gdf
    
def apply_filters_to_layers(geodataframes, config, filter_function):
    """
    Applique des filtres aux GeoDataFrames selon une configuration.

    Args:
        geodataframes (dict): Dictionnaire contenant des couches de GeoDataFrames.
        config (dict): Configuration avec les paramètres de filtrage.
        filter_function (callable): Fonction pour appliquer un filtre, prend (gdf, column, value, operator).

    Returns:
        dict: Dictionnaire mis à jour des GeoDataFrames après filtrage.
    """
    for layer_name, gdf_layer in geodataframes.items():
        # Récupère la configuration pour cette couche
        filter_config = config.get('filter_files', {}).get(layer_name)
        
        if not filter_config:
            # Skipper si aucune configuration n'est définie pour cette couche
            print(f"Aucune configuration de filtre trouvée pour la couche: {layer_name}. Skipping.")
            continue

        # Vérifie si tous les paramètres nécessaires sont présents
        column = filter_config.get('column')
        value = filter_config.get('value')
        operator = filter_config.get('operator', "==")  # Par défaut : égalité

        if column is None or value is None:
            # Skipper si des paramètres sont manquants
            print(f"Configuration de filtre incomplète pour la couche: {layer_name}. Skipping.")
            continue

        # Applique le filtrage
        try:
            gdf_layer = filter_function(gdf_layer, column, value, operator)
            geodataframes[layer_name] = gdf_layer
        except Exception as e:
            print(f"Erreur lors de l'application du filtre sur la couche {layer_name}: {e}")

    return geodataframes


def apply_global_filters(gdf, config):
    """
    Applique des filtres globaux sur un GeoDataFrame.

    Args:
        gdf (GeoDataFrame): Le GeoDataFrame à filtrer.
        config (dict): Configuration contenant les paramètres de filtrage.

    Returns:
        GeoDataFrame: Le GeoDataFrame filtré.
    """
    global_filters = config.get('filter_global', [])
    
    for filter_config in global_filters:
        column = filter_config.get('column')
        value = filter_config.get('value')
        op = filter_config.get('operator', "==")  # Par défaut, utiliser l'égalité
        
        if column is None or value is None:
            print(f"Filtre incomplet ignoré: {filter_config}")
            continue
        
        try:
            gdf = filter_gdf(gdf, column, value, op)
        except Exception as e:
            print(f"Erreur lors de l'application du filtre {filter_config}: {e}")
    
    return gdf