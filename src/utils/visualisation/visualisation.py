import pydeck as pdk
import geopandas as gpd
from typing import List, Dict
import utils.gdf.gdfExtraction as gdfExtraction
import plotly.graph_objects as go
import os
import plotly.express as px

def create_initial_view() -> pdk.ViewState:
    # Coordonnées de Montréal
    latitude = 45.5017
    longitude = -73.5673
    zoom = 12  # Ajustez le niveau de zoom selon vos besoins
    pitch = 0
    
    view_state = pdk.ViewState(
        latitude=latitude,
        longitude=longitude,
        zoom=zoom,
        pitch=pitch,
    )
    return view_state

def create_linestring_layer(gdf: gpd.GeoDataFrame, color: List[int]):
    linestring_layer = pdk.Layer(
        'PathLayer',
        data=gdf,
        get_path='coordinates',
        get_color=color,
        width_scale=20,
        width_min_pixels=2,
        pickable=True
    )
    return linestring_layer

def create_point_layer(gdf: gpd.GeoDataFrame, color: List[int]):
    point_layer = pdk.Layer(
        'ScatterplotLayer',
        data=gdf,
        get_position='[lon, lat]',
        get_color=color,
        get_radius=10,
        pickable=True
        )
    return point_layer

#TODO: FIX COLOR
def create_polygon_layer(gdf: gpd.GeoDataFrame, color: List[int]):
    polygon_layer = pdk.Layer(
        'PolygonLayer',
        data=gdf,
        get_polygon='coordinates',
        get_fill_color='[0, 0, 200, 50]',
        get_line_color='[139, 0, 0, 200]',
        get_line_width=5,
        pickable=True
        )
    return polygon_layer

def create_multipolygon_layer(gdf: gpd.GeoDataFrame, color: List[int]):
    # Fonction pour extraire les coordonnées des MultiPolygon
    def get_multipolygon_coordinates(geom):
        if geom.geom_type == 'MultiPolygon':
            # Convert to list and ensure proper nesting level
            coords = []
            for poly in geom.geoms:
                # Get the exterior coordinates of each polygon
                exterior_coords = list(poly.exterior.coords)
                coords.append(exterior_coords)
            return coords
        return None

    # Appliquer la fonction pour extraire les coordonnées des MultiPolygon
    gdf['coordinates'] = gdf['geometry'].apply(get_multipolygon_coordinates)
    
    # Créer la couche PolygonLayer pour les MultiPolygon
    multipolygon_layer = pdk.Layer(
        'PolygonLayer',
        data=gdf,
        get_polygon='coordinates',  # Utiliser la colonne 'coordinates' pour les MultiPolygons
        get_fill_color=color,
        get_line_color='[255, 140, 0, 255]',
        get_line_width=10,
        pickable=True
    )
    
    return multipolygon_layer

def create_map_layers(layers: List[pdk.Layer], view_state: pdk.ViewState, filename="map.html"):

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if os.path.exists(filename):
        os.remove(filename)

    r = pdk.Deck(
        layers= layers,
        initial_view_state=view_state,
        map_style='dark'
        )
    r.to_html(filename, open_browser=False)

def create_layers_and_map(
    geodataframes: Dict[str, gpd.GeoDataFrame], 
    points_gdfs: Dict[str, gpd.GeoDataFrame], 
    polygons_gdfs: Dict[str, gpd.GeoDataFrame], 
    multipolygons_gdfs: Dict[str, gpd.GeoDataFrame], 
    linestrings_gdfs: Dict[str, gpd.GeoDataFrame], 
    buffer_gdfs: Dict[str, gpd.GeoDataFrame], 
    colors: Dict[str, str], 
    buffer_type: str,
    **kwargs):
    
    layers = []

    # Créer les couches pour chaque GeoDataFrame
    for layer_name in geodataframes.keys():
        # Vérifier si buffer_gdfs contient un objet valide pour la couche
        buffer_gdf = buffer_gdfs.get(f"{layer_name}_buffer")
        buffer_gdf_coord = gdfExtraction.extract_poly_coordinates(buffer_gdf) if buffer_gdf is not None else None

        # Créer les couches de points, de polygones, de multipolygones et de lignes
        points_layer = create_point_layer(points_gdfs[layer_name], colors[layer_name])
        polygons_layer = create_polygon_layer(polygons_gdfs[layer_name], colors[layer_name])
        multipolygons_layer = create_multipolygon_layer(multipolygons_gdfs[layer_name], colors[layer_name])
        linestrings_layer = create_linestring_layer(linestrings_gdfs[layer_name], colors[layer_name])

        layers.append(points_layer)
        layers.append(polygons_layer)
        layers.append(multipolygons_layer)
        layers.append(linestrings_layer)

        # Ajouter la couche de buffer si elle existe
        if buffer_gdf_coord is not None:
            buffer_layer = create_polygon_layer(buffer_gdf_coord, '[128, 0, 128, 200]')
            layers.append(buffer_layer)

    # Initialiser la vue de la carte
    initial_view = create_initial_view()

    # Déterminer le nom du fichier en fonction du type de buffer
    if buffer_type == "circular":
        distance = kwargs.get('distance')
        filename = f"./data/output/visualisation/carte_{buffer_type}_buffer_{distance}m.html"  # Add 'm'
    elif buffer_type == "grid":
        wide = kwargs.get('wide')
        length = kwargs.get('length')
        filename = f"./data/output/visualisation/carte_{buffer_type}_buffer_{wide}m_{length}m.html"
    elif buffer_type == "zones":
        filename = f"./data/output/visualisation/carte_{buffer_type}_buffer.html"

    # Créer la carte avec les couches et l'enregistrer sans ouvrir
    create_map_layers(layers, initial_view, filename=filename)

def create_table_visualisation(agg_stats_gdf: gpd.GeoDataFrame, buffer_type: str, **kwargs):
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(agg_stats_gdf.columns),
            font=dict(size=10),  # Réduit la taille de la police des en-têtes
            align="center"
        ),
        cells=dict(
            values=[agg_stats_gdf[col] for col in agg_stats_gdf.columns],
            align="left",
            height=50   # Ajuste la hauteur de chaque cellule pour plus de lisibilité
        )
    )])
    
    fig.update_layout(width=2000)  # Augmente la largeur totale du tableau
    
    # Determine the filename based on buffer type
    if buffer_type == "circular":
        distance = kwargs.get('distance')
        filename = f"./data/output/visualisation/tableau_{buffer_type}_buffer_{distance}m.html"
    elif buffer_type == "grid":
        wide = kwargs.get('wide')
        length = kwargs.get('length')
        filename = f"./data/output/visualisation/tableau_{buffer_type}_buffer_{wide}m_{length}m.html"
    elif buffer_type == "zones":
        filename = "./data/output/visualisation/tableau_zones_buffer.html"
    else:
        raise ValueError(f"Unsupported buffer type: {buffer_type}")
            
    fig.write_html(filename)


def visualize_histogram(histogram_data, column, buffer_type, histogram_config=None):
    """
    Visualize histogram data and save as HTML.
    """
    output_dir = "./data/output/visualisation/"
    os.makedirs(output_dir, exist_ok=True)

    # Use a generic filename for histograms
    filename = f"histogram_{column}.html"

    # Extract histogram data for the column
    data = histogram_data.get(column, {})
    if not data:
        return None

    # Create a bar plot using Plotly
    fig = go.Figure(
        data=[
            go.Bar(
                x=data["bins"],
                y=data["counts"],
                text=data["counts"],
                textposition="auto",
            )
        ]
    )

    # Update layout with titles and labels
    fig.update_layout(
        title=data.get("title", f"Histogram of {column}"),
        xaxis_title=data.get("xlabel", column),
        yaxis_title=data.get("ylabel", "Frequency"),
        bargap=0.2,
    )

    # Save the plot as HTML
    fig.write_html(os.path.join(output_dir, filename))
    return filename