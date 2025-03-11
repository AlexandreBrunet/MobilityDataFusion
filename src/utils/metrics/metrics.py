import pandas as pd
import warnings
import os
import geopandas as gpd
import numpy as np
import plotly.express as px

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

def calculate_count_distinct(gdf, groupby_columns, distinct_columns):
    parsed_columns = [(col, f"{col}_distinct") for col in distinct_columns]
    agg_dict = {original: pd.Series.nunique for original, _ in parsed_columns}
    count_distinct_stats = gdf.groupby(groupby_columns).agg(agg_dict).reset_index()
    count_distinct_stats = count_distinct_stats.rename(columns={original: renamed for original, renamed in parsed_columns})
    return count_distinct_stats

def calculate_ratio(gdf, groupby_columns, ratio_columns):
    ratio_stats_list = []

    for ratio in ratio_columns:
        ratio_name = ratio.get("name")
        numerator = ratio.get("numerator")
        denominator = ratio.get("denominator")

        if not numerator or not denominator or not ratio_name:
            warnings.warn(
                f"Le ratio '{ratio_name}' est incomplet (numérateur, dénominateur ou nom manquant). Il sera ignoré.",
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
        try:
            gdf[ratio_name] = gdf[numerator] / gdf[denominator]
        except ZeroDivisionError:
            warnings.warn(
                f"Division par zéro détectée lors du calcul du ratio '{ratio_name}'. Les valeurs seront remplacées par NaN.",
                UserWarning
            )
            gdf[ratio_name] = gdf[numerator] / gdf[denominator].replace(0, np.nan)
        
        ratio_stat = gdf.groupby(groupby_columns).agg({ratio_name: 'mean'}).reset_index()
        ratio_stats_list.append(ratio_stat)

    # Fusionner tous les ratios calculés
    if ratio_stats_list:
        ratio_stats = pd.concat(ratio_stats_list, axis=1).loc[:, ~pd.concat(ratio_stats_list, axis=1).columns.duplicated()]
    else:
        ratio_stats = pd.DataFrame()

    return ratio_stats.round(2)

def calculate_multiply(gdf, groupby_columns, multiply_columns):
    multiply_stats_list = []

    for multiply in multiply_columns:
        multiply_name = multiply.get("name")
        columns = multiply.get("columns", [])

        if not multiply_name or not columns:
            warnings.warn(
                f"The multiplication config '{multiply_name}' is incomplete (name or columns missing). It will be ignored.",
                UserWarning
            )
            continue

        # Parse column names and check validity
        parsed_columns = [parse_column_name(col) for col in columns]
        valid_columns = [(original, renamed) for original, renamed in parsed_columns if original in gdf.columns]
        invalid_columns = [original for original, _ in parsed_columns if original not in gdf.columns]

        if invalid_columns:
            warnings.warn(
                f"The following columns are missing from the GeoDataFrame and will be ignored for multiplication '{multiply_name}': {', '.join(invalid_columns)}.",
                UserWarning
            )

        if not valid_columns:
            warnings.warn(
                f"No valid columns to multiply for '{multiply_name}'. Skipping this multiplication.",
                UserWarning
            )
            continue

        # Calculate the product
        temp_product = gdf[valid_columns[0][0]].copy()
        for original, _ in valid_columns[1:]:
            temp_product *= gdf[original]

        # Group and aggregate
        temp_df = gdf[groupby_columns].copy()
        temp_df['temp_product'] = temp_product
        multiply_stat = temp_df.groupby(groupby_columns).agg({'temp_product': 'prod'}).reset_index()
        multiply_stat = multiply_stat.rename(columns={'temp_product': multiply_name})
        multiply_stats_list.append(multiply_stat)

    # Merge all multiplication results
    if multiply_stats_list:
        multiply_stats = pd.concat(multiply_stats_list, axis=1).loc[:, ~pd.concat(multiply_stats_list, axis=1).columns.duplicated()]
    else:
        multiply_stats = pd.DataFrame()

    return multiply_stats.round(2)

def calculate_metrics(gdf, groupby_columns, metrics_config):
    agg_dict = {}
    for func, cols in metrics_config.items():
        if func != "ratio" and func != "multiply" and cols:
            parsed_columns = [parse_column_name(col) for col in cols]
            for original, renamed in parsed_columns:
                if func == "count_distinct":
                    agg_dict[f"{renamed}_count_distinct"] = (original, "nunique")
                else:
                    agg_dict[f"{renamed}_{func}"] = (original, func)

    if agg_dict:
        agg_stats = gdf.groupby(groupby_columns).agg(**agg_dict).reset_index()
    else:
        agg_stats = gdf[groupby_columns].drop_duplicates().reset_index(drop=True)

    if "ratio" in metrics_config and metrics_config["ratio"]:
        ratio_columns = metrics_config["ratio"]
        ratio_stats = calculate_ratio(gdf, groupby_columns, ratio_columns)
        agg_stats = pd.merge(agg_stats, ratio_stats, on=groupby_columns, how='left')

    if "multiply" in metrics_config and metrics_config["multiply"]:
        multiply_columns = metrics_config["multiply"]
        multiply_stats = calculate_multiply(gdf, groupby_columns, multiply_columns)
        agg_stats = pd.merge(agg_stats, multiply_stats, on=groupby_columns, how='left')

    return agg_stats.round(2)

def calculate_histogram_data(gdf: gpd.GeoDataFrame, histogram_config: dict):
    if not isinstance(histogram_config, dict):
        raise TypeError("histogram_config must be a dictionary")

    histogram_data = {}
    
    # Get histogram parameters from config
    columns = histogram_config.get('columns', [])
    binsize = histogram_config.get('binsize', 10)  # Default bin size of 10
    groupby_column = histogram_config.get('groupby', None)
    aggregation = histogram_config.get('aggregation', {})
    aggregation_type = aggregation.get('type', 'count')
    aggregation_column = aggregation.get('column', None)
    
    for col in columns:
        if col not in gdf.columns:
            print(f"Column {col} not found, skipping histogram calculation")
            continue
        
        # Convert GeoDataFrame to DataFrame
        df = pd.DataFrame(gdf)
        
        # Determine the min and max values of the column to set bin edges
        min_val = df[col].min()
        max_val = df[col].max()
        
        # Ensure binsize is positive
        if binsize <= 0:
            print(f"Bin size for column {col} must be positive, skipping histogram calculation")
            continue
        
        # Handle case where min_val equals max_val
        if min_val == max_val:
            print(f"Minimum and maximum values for column {col} are the same, skipping histogram calculation")
            continue
        
        # Create bin edges
        try:
            bin_edges = np.arange(min_val, max_val + binsize, binsize)
            bin_labels = [f"[{bin_edges[i]}-{bin_edges[i+1]-1}]" for i in range(len(bin_edges)-1)]
        except ValueError as e:
            print(f"Error creating bin edges for column {col}: {str(e)}")
            continue
        
        # Bin the column
        df[f'{col}_bin'] = pd.cut(df[col], bins=bin_edges, labels=bin_labels, right=False)
        
        if groupby_column and groupby_column in df.columns:
            group_columns = [groupby_column, f'{col}_bin']
        else:
            group_columns = [f'{col}_bin']
        
        if aggregation_type == 'sum':
            if aggregation_column not in df.columns:
                print(f"Column {aggregation_column} for summing not found, skipping histogram calculation")
                continue
            agg_data = df.groupby(group_columns)[aggregation_column].sum().reset_index(name='value')
        else:  # Default to 'count'
            agg_data = df.groupby(group_columns).size().reset_index(name='value')
        
        histogram_data[col] = agg_data
    
    return histogram_data

def parse_column_name(column):
    if " as " in column:
        original, renamed = column.split(" as ")
        return original.strip(), renamed.strip()
    return column.strip(), column.strip()