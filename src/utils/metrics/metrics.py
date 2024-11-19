def aggregate_stats(agg_fusion_gdf, groupby_columns, agg_columns, count_columns):
    # Créer un dictionnaire pour les opérations d'agrégation
    agg_dict = {col: ['min', 'max', 'mean', 'std'] for col in agg_columns}
    agg_dict.update({col: 'count' for col in count_columns})
    
    # Effectuer l'agrégation
    agg_stats = agg_fusion_gdf.groupby(groupby_columns).agg(agg_dict).reset_index().round(2)
    
    return agg_stats