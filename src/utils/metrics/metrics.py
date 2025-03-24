import pandas as pd
import warnings
import numpy as np

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

def calculate_histogram_data(gdf, histogram_config):
    columns = histogram_config.get("columns", [])
    binsize = histogram_config.get("binsize", 10)
    groupby = histogram_config.get("groupby", "")
    aggregation = histogram_config.get("aggregation", {"type": "count", "column": ""})

    print(f"Histogram config: {histogram_config}")
    print(f"Columns: {columns}, Groupby: {groupby}, Aggregation: {aggregation}")
    print(f"Condition check: groupby={bool(groupby)}, type={aggregation['type'] == 'count'}, column={bool(aggregation['column'])}")

    histogram_data = {}

    for col in columns:
        if groupby and aggregation["type"] == "count" and aggregation["column"]:
            print("Entering count aggregation block")
            # Step 1: Group by 'name_left' and count non-null 'stop_id' per group
            agg_col = aggregation["column"]
            grouped = gdf.groupby(groupby)[agg_col].count().reset_index(name="count")

            # Ensure 'count' column is numeric
            grouped["count"] = pd.to_numeric(grouped["count"], errors='coerce').fillna(0).astype(int)

            # Step 2: Define custom bins (0-9, 10-19, 20-39, 40+)
            bins = [0, 10, 20, 40, float("inf")]
            labels = ["0-9", "10-19", "20-39", "40+"]

            # Step 3: Bin the counts
            grouped["bin"] = pd.cut(grouped["count"], bins=bins, labels=labels, include_lowest=True, right=False)

            # Step 4: Count the number of buffers in each bin
            bin_counts = grouped["bin"].value_counts().sort_index()

            # Step 5: Prepare data for visualization
            histogram_data[col] = {
                "bins": labels,
                "counts": bin_counts.tolist(),
                "title": f"Number of Buffers by Bus Stops (grouped by {groupby})",
                "xlabel": "Number of Bus Stops",
                "ylabel": "Number of Buffers"
            }
        else:
            print("Entering fallback block")
            # Fallback for other types of histograms
            data = gdf[col].dropna()
            # Ensure data is numeric
            data = pd.to_numeric(data, errors='coerce').dropna()
            if len(data) > 0:
                # Ensure binsize results in a valid number of bins
                bin_range = data.max() - data.min()
                num_bins = int(bin_range / binsize) if bin_range > 0 else 1
                num_bins = max(1, num_bins)  # Ensure at least 1 bin
                hist, bin_edges = np.histogram(data, bins=num_bins)
                histogram_data[col] = {
                    "bins": bin_edges.tolist(),
                    "counts": hist.tolist(),
                    "title": f"Histogram of {col}",
                    "xlabel": col,
                    "ylabel": "Frequency"
                }
            else:
                # If no numeric data, skip this column and log a message
                print(f"Cannot create histogram for column {col}: No numeric data available after conversion")
                histogram_data[col] = {
                    "bins": [],
                    "counts": [],
                    "title": f"Histogram of {col} (No Numeric Data)",
                    "xlabel": col,
                    "ylabel": "Frequency"
                }

    return histogram_data

def parse_column_name(column):
    if " as " in column:
        original, renamed = column.split(" as ")
        return original.strip(), renamed.strip()
    return column.strip(), column.strip()