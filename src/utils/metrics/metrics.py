import pandas as pd
import warnings

def calculate_sum(gdf, groupby_columns, sum_columns):
    parsed_columns = [parse_column_name(col) for col in sum_columns]
    
    valid_columns = [(original, renamed) for original, renamed in parsed_columns if original in gdf.columns]
    invalid_columns = [original for original, _ in parsed_columns if original not in gdf.columns]

    if invalid_columns:
        warnings.warn(
            f"Les colonnes suivantes sont absentes du GeoDataFrame et seront ignorées pour la somme : {', '.join(invalid_columns)}.",
            UserWarning
        )

    agg_dict = {original: 'sum' for original, _ in valid_columns}
    sum_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()

    sum_stats = sum_stats.rename(columns={original: f"{renamed}_sum" for original, renamed in valid_columns})

    return sum_stats.round(2)

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
    ratio_stats_list = []

    for ratio_name, cols in ratio_columns.items():
        numerator = cols.get("numerator")
        denominator = cols.get("denominator")

        if not numerator or not denominator:
            warnings.warn(
                f"Le ratio '{ratio_name}' est incomplet (numérateur ou dénominateur manquant). Il sera ignoré.",
                UserWarning
            )
            continue

        # Vérifier que les colonnes existent dans le DataFrame
        if numerator not in gdf.columns or denominator not in gdf.columns:
            warnings.warn(
                f"Le ratio '{ratio_name}' ne peut pas être calculé car '{numerator}' ou '{denominator}' n'existe pas dans le GeoDataFrame. Il sera ignoré.",
                UserWarning
            )
            continue

        # Calculer le ratio et ajouter une colonne temporaire
        gdf[ratio_name] = gdf[numerator] / gdf[denominator]
        ratio_stat = gdf.groupby(groupby_columns).agg({ratio_name: 'mean'}).reset_index()
        ratio_stats_list.append(ratio_stat)

    # Fusionner tous les ratios calculés
    if ratio_stats_list:
        ratio_stats = pd.concat(ratio_stats_list, axis=1).loc[:, ~pd.concat(ratio_stats_list, axis=1).columns.duplicated()]
    else:
        ratio_stats = pd.DataFrame()

    return ratio_stats.round(2)

def calculate_metrics(gdf, groupby_columns, metrics_config):
    agg_dict = {}
    for func, cols in metrics_config.items():
        if func != "ratio" and cols:
            parsed_columns = [parse_column_name(col) for col in cols]
            for original, renamed in parsed_columns:
                agg_dict[f"{renamed}_{func}"] = (original, func)

    agg_stats = gdf.groupby(groupby_columns).agg(**agg_dict).reset_index() if agg_dict else gdf

    if "ratio" in metrics_config and metrics_config["ratio"]:
        ratio_columns = metrics_config["ratio"]
        ratio_stats = calculate_ratio(gdf, groupby_columns, ratio_columns)
        agg_stats = pd.merge(agg_stats, ratio_stats, on=groupby_columns, how='left')

    return agg_stats.round(2)

def parse_column_name(column):
    if " as " in column:
        original, renamed = column.split(" as ")
        return original.strip(), renamed.strip()
    return column.strip(), column.strip()