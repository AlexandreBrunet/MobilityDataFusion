def calculate_max(gdf, groupby_columns, max_columns):
    agg_dict = {col: 'max' for col in max_columns}
    max_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    max_stats = max_stats.rename(columns={col: f"{col}_max" for col in max_columns})
    return max_stats.round(2)

def calculate_min(gdf, groupby_columns, min_columns):
    agg_dict = {col: 'min' for col in min_columns}
    min_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    min_stats = min_stats.rename(columns={col: f"{col}_max" for col in min_columns})
    return min_stats.round(2)

def calculate_mean(gdf, groupby_columns, mean_columns):
    agg_dict = {col: 'mean' for col in mean_columns}
    mean_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    mean_stats = mean_stats.rename(columns={col: f"{col}_mean" for col in mean_columns})
    return mean_stats.round(2)

def calculate_std(gdf, groupby_columns, std_columns):
    agg_dict = {col: 'std' for col in std_columns}
    std_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    std_stats = std_stats.rename(columns={col: f"{col}_std" for col in std_columns})
    return std_stats.round(2)

def calculate_count(gdf, groupby_columns, count_columns):
    agg_dict = {col: 'count' for col in count_columns}
    count_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    count_stats = count_stats.rename(columns={col: f"{col}_count" for col in count_columns})
    return count_stats

def calculate_ratio(gdf, numerator_col, denominator_col, ratio_col_name='ratio'):
    if numerator_col not in gdf.columns or denominator_col not in gdf.columns:
        raise ValueError("Les colonnes spécifiées doivent exister dans le GeoDataFrame.")
    
    # Calculer le ratio en évitant les divisions par zéro
    gdf[ratio_col_name] = gdf.apply(
        lambda row: row[numerator_col] / row[denominator_col] if row[denominator_col] != 0 else None,
        axis=1
    )
    
    return gdf

def calculate_metrics(gdf, groupby_columns, metrics_config):
    agg_dict = {}
    for func, cols in metrics_config.items():
        # Vérifier que la liste de colonnes n'est pas vide avant d'ajouter à agg_dict
        if cols:
            for col in cols:
                agg_dict[f"{col}_{func}"] = (col, func)
    
    # Si agg_dict est vide, il n'y a pas de colonnes à agréger, on renvoie directement le gdf
    if not agg_dict:
        return gdf
    
    # Effectuer l'agrégation et renommer les colonnes
    agg_stats = (
        gdf.groupby(groupby_columns)
        .agg(**agg_dict)
        .reset_index()
    )
    return agg_stats