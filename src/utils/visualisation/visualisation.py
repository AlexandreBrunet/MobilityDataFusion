import pydeck as pdk
import geopandas as gpd
from typing import List, Dict
import utils.gdf.gdfExtraction as gdfExtraction
import plotly.graph_objects as go
import os

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
        width_scale=10,
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
        get_radius=5,
        pickable=True
        )
    return point_layer

def create_polygon_layer(gdf: gpd.GeoDataFrame, color: List[int]):
    # Fonction pour extraire les coordonnées des Polygon
    def get_polygon_coordinates(geom):
        if geom and geom.geom_type == 'Polygon':
            return list(geom.exterior.coords)  # Coordonnées de l'extérieur du polygone
        return None

    # Appliquer la fonction pour extraire les coordonnées
    gdf['coordinates'] = gdf['geometry'].apply(get_polygon_coordinates)

    # Filtrer les géométries non valides
    gdf = gdf[gdf['coordinates'].notnull()]

    polygon_layer = pdk.Layer(
        'PolygonLayer',
        data=gdf,
        get_polygon='coordinates',
        get_fill_color='[0, 100, 255, 0]',
        get_line_color=color,
        get_line_width=3,
        pickable=True,
        auto_highlight=True
    )
    return polygon_layer

def create_multipolygon_layer(gdf: gpd.GeoDataFrame, color: List[int]):
    # Fonction pour extraire les coordonnées des MultiPolygon
    def get_multipolygon_coordinates(geom):
        if geom and geom.geom_type == 'MultiPolygon':
            coords = []
            for poly in geom.geoms:
                exterior_coords = list(poly.exterior.coords)
                coords.append(exterior_coords)
            return coords
        elif geom and geom.geom_type == 'Polygon':
            return [list(geom.exterior.coords)]  # Traiter comme un polygone unique
        return None

    # Appliquer la fonction pour extraire les coordonnées
    gdf['coordinates'] = gdf['geometry'].apply(get_multipolygon_coordinates)

    # Filtrer les géométries non valides
    gdf = gdf[gdf['coordinates'].notnull()]

    multipolygon_layer = pdk.Layer(
        'PolygonLayer',
        data=gdf,
        get_polygon='coordinates',
        get_fill_color='[0, 0, 0, 0]',
        get_line_color='[255, 140, 0, 200]',
        get_line_width=7,
        pickable=True,
        auto_highlight=True
    )
    return multipolygon_layer

def create_map_layers(layers: List[pdk.Layer], view_state: pdk.ViewState, filename="map.html"):

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if os.path.exists(filename):
        os.remove(filename)

    r = pdk.Deck(
        layers= layers,
        initial_view_state=view_state,
        map_style='road'
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

        # Créer les couches de points
        points_layer = create_point_layer(points_gdfs[layer_name], colors[layer_name])
        layers.append(points_layer)

        # Créer les couches de polygones ou multipolygones pour les isochrones/network
        if buffer_type in ["isochrone", "network"]:
            # Vérifier si la couche contient des MultiPolygon
            if any(polygons_gdfs[layer_name]['geometry'].geom_type == 'MultiPolygon'):
                multipolygons_layer = create_multipolygon_layer(polygons_gdfs[layer_name], colors[layer_name])
                layers.append(multipolygons_layer)
            else:
                polygons_layer = create_polygon_layer(polygons_gdfs[layer_name], colors[layer_name])
                layers.append(polygons_layer)
        else:
            polygons_layer = create_polygon_layer(polygons_gdfs[layer_name], colors[layer_name])
            multipolygons_layer = create_multipolygon_layer(multipolygons_gdfs[layer_name], colors[layer_name])
            layers.append(polygons_layer)
            layers.append(multipolygons_layer)

        # Créer la couche de lignes
        linestrings_layer = create_linestring_layer(linestrings_gdfs[layer_name], colors[layer_name])
        layers.append(linestrings_layer)

        # Ajouter la couche de buffer si elle existe
        if buffer_gdf_coord is not None:
            buffer_layer = create_polygon_layer(buffer_gdf_coord, [50, 50, 50, 200])
            layers.append(buffer_layer)

    # Initialiser la vue de la carte
    initial_view = create_initial_view()

    # Déterminer le nom du fichier en fonction du type de buffer
    output_dir = "./data/output/visualisation/"
    if buffer_type == "circular":
        distance = kwargs.get('distance')
        filename = f"{output_dir}carte_{buffer_type}_buffer_{distance}m.html"
    elif buffer_type == "grid":
        wide = kwargs.get('wide')
        length = kwargs.get('length')
        filename = f"{output_dir}carte_{buffer_type}_buffer_{wide}m_{length}m.html"
    elif buffer_type == "zones_grid":
        wide = kwargs.get('wide')
        length = kwargs.get('length')
        filename = f"{output_dir}carte_{buffer_type}_buffer_{wide}m_{length}m.html"
    elif buffer_type == "isochrone":
        travel_time = kwargs.get('travel_time', '5')  # Par défaut 5min
        network_type = kwargs.get('network_type', 'walk')  # Par défaut walk
        filename = f"{output_dir}carte_{buffer_type}_buffer_{network_type}_{travel_time}min.html"
    elif buffer_type == "network":
        distance = kwargs.get('distance', '500')  # Par défaut 500m
        network_type = kwargs.get('network_type', 'walk')  # Par défaut walk
        filename = f"{output_dir}carte_{buffer_type}_buffer_{network_type}_{distance}m.html"
    elif buffer_type == "zones":
        filename = f"{output_dir}carte_{buffer_type}_buffer.html"

    # Utiliser la nouvelle fonction simple au lieu de pydeck
    create_simple_leaflet_map(filename, buffer_type, **kwargs)

def create_simple_leaflet_map(filename: str, buffer_type: str, **kwargs):
    """Crée une carte Leaflet simple avec les GeoJSON générés"""
    
    # Déterminer les fichiers GeoJSON à charger
    input_geojson_files = [
        ('points_geojson', './data/input/geojson/points_geojson.geojson', '#ff0000'),
        ('lines_geojson', './data/input/geojson/lines_geojson.geojson', '#4ecdc4'),
        ('polygons_geojson', './data/input/geojson/polygons_geojson.geojson', '#45b7d1')
    ]
    
    # Déterminer le fichier buffer
    buffer_files = []
    if buffer_type == "circular":
        distance = kwargs.get('distance')
        buffer_file = f'./data/output/data/buffers/points_geojson_buffer_circular_{distance}m.geojson'
        buffer_files.append(('buffer', buffer_file, '#ffa500'))
    elif buffer_type == "network":
        distance = kwargs.get('distance', '500')
        network_type = kwargs.get('network_type', 'walk')
        buffer_file = f'./data/output/data/buffers/points_geojson_buffer_network_{distance}m.geojson'
        buffer_files.append(('buffer', buffer_file, '#ffa500'))
    
    # Créer le HTML
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Carte de visualisation - {buffer_type}</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ height: 100vh; width: 100vw; }}
        .legend {{ 
            position: absolute; 
            bottom: 10px; 
            right: 10px; 
            background: white; 
            padding: 10px; 
            border-radius: 5px; 
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
        .legend-item {{ 
            display: flex; 
            align-items: center; 
            margin: 5px 0; 
        }}
        .legend-color {{ 
            width: 20px; 
            height: 20px; 
            margin-right: 10px; 
            border: 1px solid #ccc;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="legend">
        <h4>Couches de données</h4>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #ff0000"></div>
            <span>Points (Rouge)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #4ecdc4"></div>
            <span>Lignes (Bleu)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #45b7d1"></div>
            <span>Polygones (Vert)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #ffa500"></div>
            <span>Buffer (Orange)</span>
        </div>
    </div>

    <script>
        // Initialiser la carte centrée sur Montréal
        const map = L.map('map').setView([45.5017, -73.5673], 12);
        
        // Ajouter la couche de tuiles
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        // Fonction pour charger et afficher un GeoJSON
        function loadGeoJSON(url, color, name) {{
            fetch(url)
                .then(response => response.json())
                .then(data => {{
                    L.geoJSON(data, {{
                        style: function(feature) {{
                            return {{
                                color: color,
                                weight: 2,
                                opacity: 0.8,
                                fillColor: color,
                                fillOpacity: 0.3
                            }};
                        }},
                        onEachFeature: function(feature, layer) {{
                            if (feature.properties) {{
                                const props = Object.entries(feature.properties)
                                    .map(([key, value]) => {{
                                        let displayValue = value;
                                        if (value === null || value === undefined) {{
                                            displayValue = 'N/A';
                                        }} else if (typeof value === 'number' && isNaN(value)) {{
                                            displayValue = 'N/A';
                                        }} else if (typeof value === 'string' && value.toLowerCase() === 'nan') {{
                                            displayValue = 'N/A';
                                        }}
                                        return `<b>${{key}}:</b> ${{displayValue}}`;
                                    }})
                                    .join('<br>');
                                layer.bindPopup(`<b>${{name}}</b><br>${{props}}`);
                            }}
                        }}
                    }}).addTo(map);
                    console.log(`${{name}} chargé: ${{data.features.length}} features`);
                }})
                .catch(error => {{
                    console.error(`Erreur lors du chargement de ${{name}}:`, error);
                }});
        }}
        
        // Charger les données
        const inputFiles = {input_geojson_files};
        const bufferFiles = {buffer_files};
        
        // Charger les fichiers d'entrée
        inputFiles.forEach(([name, url, color]) => {{
            loadGeoJSON(url, color, name);
        }});
        
        // Charger les fichiers buffer
        bufferFiles.forEach(([name, url, color]) => {{
            loadGeoJSON(url, color, name);
        }});
    </script>
</body>
</html>
"""
    
    # Sauvegarder le fichier
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Carte Leaflet créée: {filename}")

def create_table_visualisation(agg_stats_gdf: gpd.GeoDataFrame, buffer_type: str, **kwargs):
    # Drop the geometry column to avoid issues with Plotly
    df = agg_stats_gdf.drop(columns=['geometry'], errors='ignore')

    # Ensure area_km2 is present and formatted
    if 'area_km2' in df.columns:
        df['area_km2'] = df['area_km2'].round(4)  # Round to 4 decimal places for readability
    else:
        print("Warning: area_km2 column not found in the GeoDataFrame")

    # Create the Plotly table
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df.columns),
            font=dict(size=10),  # Réduit la taille de la police des en-têtes
            align="center"
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            align="left",
            height=50   # Ajuste la hauteur de chaque cellule pour plus de lisibilité
        )
    )])
    
    fig.update_layout(width=2000)  # Augmente la largeur totale du tableau
    
    output_dir = "./data/output/visualisation/"
    os.makedirs(output_dir, exist_ok=True)

    if buffer_type == "circular":
        distance = kwargs.get('distance')
        filename = f"{output_dir}tableau_{buffer_type}_buffer_{distance}m.html"
    elif buffer_type == "grid":
        wide = kwargs.get('wide')
        length = kwargs.get('length')
        filename = f"{output_dir}tableau_{buffer_type}_buffer_{wide}m_{length}m.html"
    elif buffer_type == "zones_grid":
        wide = kwargs.get('wide')
        length = kwargs.get('length')
        filename = f"{output_dir}tableau_{buffer_type}_buffer_{wide}m_{length}m.html"
    elif buffer_type == "isochrone":
        travel_time = kwargs.get('travel_time', '5')
        network_type = kwargs.get('network_type')
        filename = f"{output_dir}tableau_{buffer_type}_buffer_{network_type}_{travel_time}min.html"
    elif buffer_type == "network":
        distance = kwargs.get('distance', '500')
        network_type = kwargs.get('network_type', 'walk')
        filename = f"{output_dir}tableau_{buffer_type}_buffer_{network_type}_{distance}m.html"
    elif buffer_type == "zones":
        filename = f"{output_dir}tableau_zones_buffer.html"
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

def visualize_barchart(barchart_data, column, buffer_type):
    """
    Visualize bar chart data and save as HTML.
    """
    output_dir = "./data/output/visualisation/"
    os.makedirs(output_dir, exist_ok=True)

    # Use a generic filename for bar charts
    filename = f"barchart_{column}.html"

    # Extract bar chart data for the column
    data = barchart_data.get(column, {})
    if not data:
        return None

    # Create a bar plot using Plotly
    fig = go.Figure(
        data=[
            go.Bar(
                x=data["categories"],
                y=data["values"],
                text=data["values"],
                textposition="auto",
            )
        ]
    )

    # Update layout with titles and labels
    fig.update_layout(
        title=data.get("title", f"Bar Chart of {column}"),
        xaxis_title=data.get("xlabel", column),
        yaxis_title=data.get("ylabel", "Value"),
        bargap=0.2,
        width=1200,  # Largeur ajustée pour mieux afficher les catégories
        height=600,
        xaxis={'tickangle': 45}  # Rotation des étiquettes pour lisibilité
    )

    # Save the plot as HTML
    fig.write_html(os.path.join(output_dir, filename))
    return filename