import pandas as pd
import warnings
import numpy as np
import logging

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
    # Validate that groupby_columns exist in the GeoDataFrame
    missing_cols = [col for col in groupby_columns if col not in gdf.columns]
    if missing_cols:
        raise ValueError(f"Groupby columns {missing_cols} not found in GeoDataFrame")

    # Extract area_km2 along with groupby_columns before aggregation
    if 'area_km2' in gdf.columns:
        # Drop duplicates to ensure one area_km2 per group
        area_data = gdf[groupby_columns + ['area_km2']].drop_duplicates(subset=groupby_columns)
    else:
        raise ValueError("area_km2 column not found in the GeoDataFrame")

    # Build the aggregation dictionary
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

    agg_stats = pd.merge(agg_stats, area_data, on=groupby_columns, how='left')

    if "ratio" in metrics_config and metrics_config["ratio"]:
        ratio_columns = metrics_config["ratio"]
        ratio_stats = calculate_ratio(gdf, groupby_columns, ratio_columns)
        agg_stats = pd.merge(agg_stats, ratio_stats, on=groupby_columns, how='left')

    if "multiply" in metrics_config and metrics_config["multiply"]:
        multiply_columns = metrics_config["multiply"]
        multiply_stats = calculate_multiply(gdf, groupby_columns, multiply_columns)
        agg_stats = pd.merge(agg_stats, multiply_stats, on=groupby_columns, how='left')

    return agg_stats.round(2)


logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
def calculate_histogram_data(gdf, histogram_config):
    columns = histogram_config.get("columns", [])
    groupby = histogram_config.get("groupby", "")
    aggregation = histogram_config.get("aggregation", {"type": "count", "column": ""})
    custom_bins = histogram_config.get("customBins", None)
    custom_labels = histogram_config.get("customLabels", None)

    logging.info(f"Histogram config: {histogram_config}")
    logging.info(f"Columns: {columns}, Groupby: {groupby}, Aggregation: {aggregation}")
    logging.info(f"Custom Bins: {custom_bins}, Custom Labels: {custom_labels}")

    histogram_data = {}

    # Validation de base
    if not columns:
        raise ValueError("No columns specified in histogram config")
    if not groupby:
        raise ValueError("groupby must be specified in histogram config")
    if groupby not in gdf.columns:
        raise ValueError(f"Groupby column '{groupby}' not found in GeoDataFrame. Available columns: {list(gdf.columns)}")
    if aggregation["type"] not in ["count", "sum"]:
        raise ValueError(f"Unsupported aggregation type '{aggregation['type']}'. Must be 'count' or 'sum'")
    if aggregation["type"] == "sum" and (not aggregation["column"] or aggregation["column"] not in gdf.columns):
        raise ValueError(f"For 'sum' aggregation, a valid 'column' must be specified. Got: {aggregation['column']}")

    # Validation des bins et labels
    if custom_bins is None or custom_labels is None:
        custom_bins = [0, 10, 20, 40, float("inf")]
        custom_labels = ["0-9", "10-19", "20-39", "40+"]
    else:
        if not isinstance(custom_bins, list) or len(custom_bins) < 2:
            raise ValueError("customBins must be a list of at least two numbers")
        try:
            custom_bins = [float("inf") if str(x).lower() == "infinity" else float(x) for x in custom_bins]
        except (ValueError, TypeError) as e:
            raise ValueError(f"All customBins values must be convertible to numbers, got: {custom_bins}. Error: {e}")
        if not all(custom_bins[i] <= custom_bins[i + 1] for i in range(len(custom_bins) - 1)):
            raise ValueError(f"customBins must be in ascending order, got: {custom_bins}")
        
        expected_label_count = len(custom_bins) - 1
        if not isinstance(custom_labels, list) or len(custom_labels) != expected_label_count:
            raise ValueError(f"customLabels must be a list of exactly {expected_label_count} strings, got {len(custom_labels)}: {custom_labels}")
        if not all(isinstance(label, str) for label in custom_labels):
            raise ValueError(f"All customLabels values must be strings, got: {custom_labels}")

    for col in columns:
        if col not in gdf.columns:
            raise ValueError(f"Column '{col}' not found in GeoDataFrame. Available columns: {list(gdf.columns)}")

        # Groupby et agrégation
        if aggregation["type"] == "count":
            # Compter le nombre d'occurrences par groupe
            grouped = gdf.groupby(groupby).size().reset_index(name="count")
            agg_col = "count"
            ylabel = "Number of Records"
        elif aggregation["type"] == "sum":
            # Sommer une colonne spécifique par groupe
            agg_col = aggregation["column"]
            if not pd.api.types.is_numeric_dtype(gdf[agg_col]):
                gdf[agg_col] = pd.to_numeric(gdf[agg_col], errors='coerce')
                logging.info(f"Converted '{agg_col}' to numeric. NaN count: {gdf[agg_col].isna().sum()}")
            grouped = gdf.groupby(groupby)[agg_col].sum().reset_index(name="sum")
            agg_col = "sum"
            ylabel = f"Sum of {agg_col}"

        logging.info(f"Grouped data for {col}:\n{grouped[[groupby, agg_col]]}")

        # Bin les résultats agrégés
        grouped["bin"] = pd.cut(
            grouped[agg_col],
            bins=custom_bins,
            labels=custom_labels,
            include_lowest=True,
            right=True
        )

        # Vérifier les valeurs non binnées
        if grouped["bin"].isna().any():
            unbinned = grouped[grouped["bin"].isna()][[groupby, agg_col]]
            raise ValueError(f"Some values in '{agg_col}' were not binned for {col}. Check bin edges: {custom_bins}. Unbinned data:\n{unbinned}")

        # Compter les groupes dans chaque bin
        bin_counts = grouped["bin"].value_counts().sort_index()

        # Remplir les bins manquants avec 0
        bin_counts = bin_counts.reindex(custom_labels, fill_value=0)

        logging.info(f"Bin counts for {col}:\n{bin_counts}")

        histogram_data[col] = {
            "bins": custom_labels,
            "counts": bin_counts.tolist(),
            "title": f"Histogram of {col} (grouped by {groupby})",
            "xlabel": f"{aggregation['type'].capitalize()} of {col if aggregation['type'] == 'count' else agg_col}",
            "ylabel": ylabel
        }

    return histogram_data

def calculate_barchart_data(gdf, barchart_config):
    columns = barchart_config.get("columns", [])
    groupby = barchart_config.get("groupby", "")
    aggregation = barchart_config.get("aggregation", {"type": "count", "column": ""})

    logging.info(f"Bar chart config: {barchart_config}")
    logging.info(f"Columns: {columns}, Groupby: {groupby}, Aggregation: {aggregation}")

    # Validation de base
    if not columns:
        raise ValueError("No columns specified in bar chart config")
    if not groupby:
        raise ValueError("groupby must be specified in bar chart config")
    if groupby not in gdf.columns:
        raise ValueError(f"Groupby column '{groupby}' not found in GeoDataFrame. Available columns: {list(gdf.columns)}")
    if aggregation["type"] not in ["count", "sum"]:
        raise ValueError(f"Unsupported aggregation type '{aggregation['type']}'. Must be 'count' or 'sum'")
    if aggregation["type"] == "sum" and (not aggregation["column"] or aggregation["column"] not in gdf.columns):
        raise ValueError(f"For 'sum' aggregation, a valid 'column' must be specified. Got: {aggregation['column']}")

    barchart_data = {}
    for col in columns:
        if col not in gdf.columns:
            raise ValueError(f"Column '{col}' not found in GeoDataFrame. Available columns: {list(gdf.columns)}")

        # Groupby et agrégation
        if aggregation["type"] == "count":
            grouped = gdf.groupby(groupby).size().reset_index(name="count")
            agg_col = "count"
            ylabel = "Number of Records"
        elif aggregation["type"] == "sum":
            agg_col = aggregation["column"]
            if not pd.api.types.is_numeric_dtype(gdf[agg_col]):
                gdf[agg_col] = pd.to_numeric(gdf[agg_col], errors='coerce')
                logging.info(f"Converted '{agg_col}' to numeric. NaN count: {gdf[agg_col].isna().sum()}")
            grouped = gdf.groupby(groupby)[agg_col].sum().reset_index(name="sum")
            agg_col = "sum"
            ylabel = f"Sum of {agg_col}"

        logging.info(f"Grouped data for {col}:\n{grouped[[groupby, agg_col]]}")

        # Préparer les données pour un bar chart (pas de binnage)
        barchart_data[col] = {
            "categories": grouped[groupby].tolist(),
            "values": grouped[agg_col].tolist(),
            "title": f"Bar Chart of {col} (grouped by {groupby})",
            "xlabel": groupby,
            "ylabel": ylabel
        }

    return barchart_data

def calculate_post_aggregation_metrics(agg_stats_gdf, post_aggregation_config):
    result_gdf = agg_stats_gdf.copy()

    # Gestion des ratios
    if "ratio" in post_aggregation_config:
        for ratio in post_aggregation_config["ratio"]:
            ratio_name = ratio.get("name")
            numerator = ratio.get("numerator")
            denominator = ratio.get("denominator")

            if not all([ratio_name, numerator, denominator]):
                warnings.warn(f"Ratio '{ratio_name}' incomplet. Ignoré.", UserWarning)
                continue

            if numerator not in result_gdf.columns or denominator not in result_gdf.columns:
                warnings.warn(f"Colonnes '{numerator}' ou '{denominator}' absentes dans agg_stats_gdf. Ratio '{ratio_name}' ignoré.", UserWarning)
                continue

            try:
                result_gdf[ratio_name] = result_gdf[numerator] / result_gdf[denominator]
            except ZeroDivisionError:
                warnings.warn(f"Division par zéro dans ratio '{ratio_name}'. Remplacement par NaN.", UserWarning)
                result_gdf[ratio_name] = result_gdf[numerator] / result_gdf[denominator].replace(0, np.nan)

    # Tu peux ajouter d'autres types de métriques ici (ex. multiply, diff, etc.)
    
    return result_gdf.round(2)

def parse_column_name(column):
    if " as " in column:
        original, renamed = column.split(" as ")
        return original.strip(), renamed.strip()
    return column.strip(), column.strip()