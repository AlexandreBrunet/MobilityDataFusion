import pandas as pd

def calculate_max(gdf, groupby_columns, max_columns):
    parsed_columns = [parse_column_name(col) for col in max_columns]
    agg_dict = {original: 'max' for original, _ in parsed_columns}
    max_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    max_stats = max_stats.rename(columns={original: f"{renamed}_max" for original, renamed in parsed_columns})
    return max_stats.round(2)

def calculate_min(gdf, groupby_columns, min_columns):
    parsed_columns = [parse_column_name(col) for col in min_columns]
    agg_dict = {original: 'min' for original, _ in parsed_columns}
    min_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    min_stats = min_stats.rename(columns={original: f"{renamed}_min" for original, renamed in parsed_columns})
    return min_stats.round(2)

def calculate_mean(gdf, groupby_columns, mean_columns):
    parsed_columns = [parse_column_name(col) for col in mean_columns]
    agg_dict = {original: 'mean' for original, _ in parsed_columns}
    mean_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    mean_stats = mean_stats.rename(columns={original: f"{renamed}_mean" for original, renamed in parsed_columns})
    return mean_stats.round(2)

def calculate_std(gdf, groupby_columns, std_columns):
    parsed_columns = [parse_column_name(col) for col in std_columns]
    agg_dict = {original: 'std' for original, _ in parsed_columns}
    std_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    std_stats = std_stats.rename(columns={original: f"{renamed}_std" for original, renamed in parsed_columns})
    return std_stats.round(2)

def calculate_count(gdf, groupby_columns, count_columns):
    parsed_columns = [parse_column_name(col) for col in count_columns]
    agg_dict = {original: 'count' for original, _ in parsed_columns}
    count_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    count_stats = count_stats.rename(columns={original: f"{renamed}_count" for original, renamed in parsed_columns})
    return count_stats

def calculate_ratio(gdf, groupby_columns, ratio_columns):
    if len(ratio_columns) != 2:
        raise ValueError("ratio_columns doit contenir exactement deux colonnes au format 'colonne_originale as colonne_renommée'.")
    
    parsed_columns = [parse_column_name(col) for col in ratio_columns]
    numerator, denominator = [original for original, _ in parsed_columns]
    ratio_name = f"{parsed_columns[0][1]}_to_{parsed_columns[1][1]}_ratio"

    gdf[ratio_name] = gdf[numerator] / gdf[denominator]
    ratio_stats = gdf.groupby(groupby_columns).agg({ratio_name: 'mean'}).reset_index()
    return ratio_stats.round(2)

def calculate_metrics(gdf, groupby_columns, metrics_config):
    agg_dict = {}
    for func, cols in metrics_config.items():
        if func != "ratio" and cols:
            parsed_columns = [parse_column_name(col) for col in cols]
            for original, renamed in parsed_columns:
                agg_dict[f"{renamed}_{func}"] = (original, func)
    
    # Calcul des métriques standards
    agg_stats = gdf.groupby(groupby_columns).agg(**agg_dict).reset_index() if agg_dict else gdf

    # Gestion du ratio séparément
    if "ratio" in metrics_config and metrics_config["ratio"]:
        ratio_columns = metrics_config["ratio"]
        ratio_stats = calculate_ratio(gdf, groupby_columns, ratio_columns)
        agg_stats = pd.merge(agg_stats, ratio_stats, on=groupby_columns, how='left')

    return agg_stats

def parse_column_name(column):
    if " as " in column:
        original, renamed = column.split(" as ")
        return original.strip(), renamed.strip()
    return column.strip(), column.strip()