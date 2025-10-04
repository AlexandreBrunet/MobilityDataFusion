import React, { useState, useEffect } from 'react';
import Form from 'react-jsonschema-form';
import * as yaml from 'js-yaml';
import './App.css';

// Icons (using Unicode symbols for simplicity)
const Icons = {
  config: '⚙️',
  table: '📊',
  map: '🗺️',
  chart: '📈',
  data: '💾',
  play: '▶️',
  stop: '⏹️',
  refresh: '🔄',
  download: '⬇️',
  upload: '⬆️',
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️'
};

// Configuration par défaut basée sur config.yaml actuel
const defaultConfig = {
  activate_visualisation: true,
  buffer_layer: {
    layer_name: "points_geojson",
    buffer_type: "circular",
    distance: 200,
    geometry_type: "Point"
  },
  colors: {
    lines_geojson: "[255, 165, 0, 160]",
    points_geojson: "[255, 0, 0, 160]",
    polygons_geojson: "[0, 255, 0, 160]"
  },
  count_columns: [],
  count_distinct_columns: [
    "line_name as nbr_line",
    "polygon_name as nbr_polygon"
  ],
  data_files: [
    { name: "lines_geojson", path: "./data/input/geojson/lines_geojson.geojson" },
    { name: "points_geojson", path: "./data/input/geojson/points_geojson.geojson" },
    { name: "polygons_geojson", path: "./data/input/geojson/polygons_geojson.geojson" }
  ],
  filter_data_files: {},
  filter_global: [],
  groupby_columns: [
    "buffer_id",
    "point_name"
  ],
  join_layers: {
    linestrings: { type: "intersects" },
    multipolygons: { type: "intersects" },
    points: { type: "contains" },
    polygons: { type: "intersects" }
  },
  max_columns: [],
  mean_columns: [],
  min_columns: [],
  multiply_columns: [],
  post_aggregation_metrics: {},
  ratio_columns: [],
  std_columns: [],
  sum_columns: []
};

const App = () => {
  const [formData, setFormData] = useState(defaultConfig);
  const [schema, setSchema] = useState({});
  const [submitMessage, setSubmitMessage] = useState('');
  const [fileList, setFileList] = useState({});
  const [tableHTML, setTableHTML] = useState('');
  const [mapHTML, setMapHTML] = useState('');
  const [activeTab, setActiveTab] = useState('form');
  const [histograms, setHistograms] = useState({});
  const [histogramFormData, setHistogramFormData] = useState({
    columns: [],
    groupby: "",
    aggregation: { type: "count", column: "" },
    customBins: "",
    customLabels: "",
  });
  const [barCharts, setBarCharts] = useState({});
  const [barChartFormData, setBarChartFormData] = useState({
    columns: [],
    groupby: "",
    aggregation: { type: "count", column: "" },
  });
  const [activeDataExplorerFile, setActiveDataExplorerFile] = useState(null);
  const [filePreviews, setFilePreviews] = useState({});
  const [dataFiles, setDataFiles] = useState([]);
  const [geojsonData, setGeojsonData] = useState({});
  const [baseMapHTML, setBaseMapHTML] = useState('');

  // Fonction pour charger les données GeoJSON
  const loadGeojsonData = async (fileList) => {
    const geojsonFiles = Object.entries(fileList).filter(([key, value]) => 
      value.endsWith('.geojson')
    );
    
    const geojsonData = {};
    for (const [name, path] of geojsonFiles) {
      try {
        const response = await fetch(`http://127.0.0.1:5000/get_geojson_data/${name}`);
        if (response.ok) {
          const data = await response.json();
          geojsonData[name] = data;
        }
      } catch (error) {
        console.error(`Error loading ${name}:`, error);
      }
    }
    setGeojsonData(geojsonData);
    return geojsonData;
  };

  // Fonction pour créer une carte de base avec les GeoJSON
  const createBaseMap = (geojsonData) => {
    const colors = {
      cd: '#667eea',
      fsa: '#f093fb',
      points: '#ff6b6b',
      lines: '#4ecdc4',
      polygons: '#45b7d1'
    };

    const mapHTML = `
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100%; }
        .legend { 
            position: absolute; 
            bottom: 20px; 
            right: 20px; 
            background: white; 
            padding: 10px; 
            border-radius: 5px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        }
        .legend-item { 
            display: flex; 
            align-items: center; 
            margin: 5px 0; 
        }
        .legend-color { 
            width: 20px; 
            height: 15px; 
            margin-right: 10px; 
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="legend">
        <h4>Couches de données</h4>
        ${Object.keys(geojsonData).map(name => `
            <div class="legend-item">
                <div class="legend-color" style="background-color: ${colors[name] || '#666'}"></div>
                <span>${name}</span>
            </div>
        `).join('')}
    </div>
    <script>
        const map = L.map('map').setView([45.5017, -73.5673], 10);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        const geojsonData = ${JSON.stringify(geojsonData)};
        const colors = ${JSON.stringify(colors)};
        
        Object.entries(geojsonData).forEach(([name, data]) => {
            if (data && data.features) {
                const layer = L.geoJSON(data, {
                    style: {
                        color: colors[name] || '#666',
                        weight: 2,
                        opacity: 0.8,
                        fillOpacity: 0.3
                    },
                    pointToLayer: function(feature, latlng) {
                        return L.circleMarker(latlng, {
                            radius: 6,
                            fillColor: colors[name] || '#666',
                            color: colors[name] || '#666',
                            weight: 1,
                            opacity: 1,
                            fillOpacity: 0.8
                        });
                    },
                    onEachFeature: function(feature, layer) {
                        if (feature.properties) {
                            const props = Object.entries(feature.properties)
                                .map(([key, value]) => \`<b>\${key}:</b> \${value}\`)
                                .join('<br>');
                            layer.bindPopup(\`<b>\${name}</b><br>\${props}\`);
                        }
                    }
                }).addTo(map);
                
                // Ajuster la vue pour inclure toutes les données
                if (layer.getBounds().isValid()) {
                    map.fitBounds(layer.getBounds());
                }
            }
        });
    </script>
</body>
</html>`;
    
    return mapHTML;
  };

  useEffect(() => {
    fetch('http://127.0.0.1:5000/list_files')
      .then(response => response.json())
      .then(async (data) => {
        console.log('Fetched file list:', data);
        setFileList(data);
        setDataFiles(Object.keys(data));

        // Charger les données GeoJSON et créer la carte de base
        const geojsonData = await loadGeojsonData(data);
        if (Object.keys(geojsonData).length > 0) {
          const baseMap = createBaseMap(geojsonData);
          setBaseMapHTML(baseMap);
        }

        const dataFilesList = Object.entries(data).map(([key, value]) => ({
          name: key,
          path: value
        }));

        const baseSchema = {
          type: "object",
          properties: {
            data_files: {
              type: "array",
              title: "Data Files",
              items: {
                type: "object",
                properties: {
                  name: { type: "string", title: "File Name" },
                  path: { type: "string", title: "File Path" }
                },
                required: ["name", "path"]
              }
            },
            buffer_layer: {
              type: "object",
              title: "Buffer Layer Configuration",
              properties: {
                layer_name: {
                  type: "string",
                  title: "Layer Name",
                  default: "stations_bixi",
                  "description": "The name of the data file to create the buffers. This must match the File Name defined in the data source configuration."
                },
                geometry_type: {
                  type: "string",
                  title: "Geometry Type",
                  enum: ["Point", "Polygon", "LineString", "MultiPolygon"],
                  default: "Point"
                },
                buffer_type: {
                  type: "string",
                  title: "Buffer Type",
                  enum: ["circular", "grid", "isochrone","network", "zones", "zones_grid"],
                  default: "circular"
                },
                distance: {
                  type: "number",
                  title: "Distance (meters)",
                  default: 1000
                }
              },
              required: ["layer_name", "geometry_type", "buffer_type", "distance"]
            },
            filter_data_files: {
              type: "object",
              title: "Filter Data Files",
              properties: {},
              additionalProperties: {
                type: "object",
                properties: {
                  column: { type: "string", title: "Column to Filter" },
                  value: {
                    anyOf: [
                      { type: "string", title: "Value (String)" },
                      { type: "number", title: "Value (Number)" }
                    ]
                  },
                  operator: { type: "string", title: "Operator", enum: ["==", ">=", "<=", ">", "<", "!="] }
                },
                required: []
              }
            },
            ratio_columns: {
              type: "array",
              title: "Ratio Columns",
              items: {
                type: "object",
                properties: {
                  name: { type: "string", title: "Ratio Name", default: "permis_perslogi_ratio" },
                  numerator: { type: "string", title: "Numerator", default: "permis" },
                  denominator: { type: "string", title: "Denominator", default: "perslogi" }
                },
                required: ["name", "numerator", "denominator"]
              }
            },
            multiply_columns: {
              type: "array",
              title: "Multiply Columns",
              items: {
                type: "object",
                properties: {
                  name: { type: "string", title: "Multiply Name", default: "product_capacity_area" },
                  columns: {
                    type: "array",
                    title: "Columns to Multiply",
                    items: { type: "string", title: "Column" },
                    default: ["capacity", "SUPERFICIE_TERRAIN"]
                  }
                },
                required: ["name", "columns"]
              }
            },
            sum_columns: { type: "array", items: { type: "string", title: "Sum Column" } },
            max_columns: { type: "array", items: { type: "string", title: "Max Column" } },
            min_columns: { type: "array", items: { type: "string", title: "Min Column" } },
            mean_columns: { type: "array", items: { type: "string", title: "Mean Column" } },
            std_columns: { type: "array", items: { type: "string", title: "Standard Deviation Column" } },
            count_columns: { type: "array", items: { type: "string", title: "Count Column" } },
            count_distinct_columns: { type: "array", items: { type: "string", title: "Count Distinct Column" } },
            groupby_columns: { type: "array", items: { type: "string", title: "Group By Column" } },
            filter_global: {
              type: "array",
              title: "Global Filters",
              items: {
                type: "object",
                properties: {
                  column: { type: "string", title: "Column" },
                  value: { anyOf: [{ type: "number" }, { type: "string" }] },
                  operator: { type: "string", title: "Operator", enum: ["==", ">=", "<=", ">", "<", "!="] }
                },
                required: ["column", "value", "operator"]
              }
            },
            post_aggregation_metrics: {
              type: "object",
              title: "Post-Aggregation Metrics",
              properties: {
                ratio: {
                  type: "array",
                  title: "Ratio Metrics",
                  items: {
                    type: "object",
                    properties: {
                      name: { type: "string", title: "Ratio Name" },
                      numerator: { type: "string", title: "Numerator Column" },
                      denominator: { type: "string", title: "Denominator Column" }
                    },
                    required: ["name", "numerator", "denominator"]
                  }
                }
              }
            },
            activate_visualisation: { type: "boolean", title: "Activate Visualisation" },
            join_layers: {
              type: "object",
              title: "Join Layers",
              properties: {
                points: { type: "object", properties: { type: { type: "string", enum: ["contains", "intersects"] } } },
                polygons: { type: "object", properties: { type: { type: "string", enum: ["contains", "intersects"] } } },
                multipolygons: { type: "object", properties: { type: { type: "string", enum: ["contains", "intersects"] } } },
                linestrings: { type: "object", properties: { type: { type: "string", enum: ["contains", "intersects"] } } }
              }
            },
            colors: {
              type: "object",
              title: "Colors",
              properties: Object.keys(data).reduce((acc, layerName) => {
                acc[layerName] = { type: "string", title: `Color for ${layerName}` };
                return acc;
              }, {})
            }
          },
          required: [
            "data_files", "buffer_layer", "filter_data_files", "ratio_columns", "multiply_columns",
            "sum_columns", "max_columns", "min_columns", "mean_columns", "std_columns",
            "count_columns", "count_distinct_columns", "groupby_columns", "filter_global",
            "activate_visualisation", "join_layers", "colors"
          ]
        };

        setSchema(baseSchema);

        // Utiliser la configuration par défaut mais adapter aux fichiers détectés
        const updatedFormData = {
          ...defaultConfig,
          data_files: dataFilesList,
          // Adapter les couleurs aux fichiers détectés
          colors: Object.keys(data).reduce((acc, layerName) => {
            // Utiliser les couleurs par défaut si disponibles, sinon couleur par défaut
            acc[layerName] = defaultConfig.colors[layerName] || "[200, 30, 0, 160]";
            return acc;
          }, {}),
          // Utiliser la configuration par défaut du buffer_layer
          buffer_layer: defaultConfig.buffer_layer
        };
        
        setFormData(updatedFormData);
      })
      .catch(error => console.error('Error fetching file list:', error));
  }, []);

  useEffect(() => {
    if (activeTab === 'data-explorer' && activeDataExplorerFile) {
      if (!filePreviews[activeDataExplorerFile]) {
        fetch(`http://127.0.0.1:5000/get_file_preview/${activeDataExplorerFile}`)
          .then(response => response.json())
          .then(data => {
            setFilePreviews(prev => ({
              ...prev,
              [activeDataExplorerFile]: data
            }));
          })
          .catch(error => console.error('Error fetching file preview:', error));
      }
    }
  }, [activeDataExplorerFile, activeTab, filePreviews]);

  const histogramSchema = {
    type: "object",
    title: "Histogram Configuration",
    properties: {
      columns: {
        type: "array",
        title: "Columns",
        items: { type: "string" }
      },
      groupby: {
        type: "string",
        title: "Group By Column"
      },
      aggregation: {
        type: "object",
        title: "Aggregation",
        properties: {
          type: {
            type: "string",
            title: "Type",
            enum: ["count", "sum"]
          },
          column: {
            type: "string",
            title: "Column"
          }
        }
      },
      customBins: {
        type: "string",
        title: "Custom Bins (comma-separated, e.g., 0,5,15,30,50,Infinity)",
        default: ""
      },
      customLabels: {
        type: "string",
        title: "Custom Labels (comma-separated, e.g., 0-5,6-15,16-30,31-50,51+)",
        default: ""
      }
    }
  };

  const histogramUiSchema = {
    columns: {
      "ui:widget": "array",
      "items": {
        "ui:placeholder": "Enter column name"
      }
    },
    groupby: {
      "ui:placeholder": "Enter group by column"
    },
    aggregation: {
      type: {
        "ui:widget": "select"
      },
      column: {
        "ui:placeholder": "Enter aggregation column"
      }
    },
    customBins: {
      "ui:placeholder": "e.g., 0,5,15,30,50,Infinity"
    },
    customLabels: {
      "ui:placeholder": "e.g., 0-5,6-15,16-30,31-50,51+",
      "ui:help": "Note: Intervals are right-inclusive (e.g., 0-5 includes 0 to 5). The number of labels must equal the number of bins (e.g., for bins 0,10,20,30,40,Infinity, provide 5 labels like 0-9,10-19,20-29,30-39,40+). The last label typically ends with '+' (e.g., 51+). If the last label ends with '+', the last bin will automatically extend to Infinity."
    }
  };

  const barChartSchema = {
    type: "object",
    title: "Bar Chart Configuration",
    properties: {
      columns: {
        type: "array",
        title: "Columns",
        items: { type: "string" }
      },
      groupby: {
        type: "string",
        title: "Group By Column"
      },
      aggregation: {
        type: "object",
        title: "Aggregation",
        properties: {
          type: {
            type: "string",
            title: "Type",
            enum: ["count", "sum"]
          },
          column: {
            type: "string",
            title: "Column"
          }
        }
      }
    }
  };

  const barChartUiSchema = {
    columns: {
      "ui:widget": "array",
      "items": {
        "ui:placeholder": "Enter column name"
      }
    },
    groupby: {
      "ui:placeholder": "Enter group by column"
    },
    aggregation: {
      type: {
        "ui:widget": "select"
      },
      column: {
        "ui:placeholder": "Enter aggregation column"
      }
    }
  };

  const updateBufferLayerSchema = (currentSchema, bufferType) => {
    const newSchema = JSON.parse(JSON.stringify(currentSchema)); // Cloner pour éviter mutations
    const bufferProperties = newSchema.properties.buffer_layer.properties;

    // Supprimer les propriétés dynamiques
    delete bufferProperties.distance;
    delete bufferProperties.wide;
    delete bufferProperties.length;
    delete bufferProperties.travel_time;
    delete bufferProperties.speed;
    delete bufferProperties.network_type;
    delete bufferProperties.network_buffer;
    delete bufferProperties.osm_file;

    // Ajouter les propriétés selon buffer_type
    if (bufferType === "circular") {
      bufferProperties.distance = {
        type: "number",
        title: "Distance (meters)",
        default: 1000,
      };
    } else if (bufferType === "grid") {
      bufferProperties.wide = {
        type: "number",
        title: "Width (meters)",
        default: 1000,
      };
      bufferProperties.length = {
        type: "number",
        title: "Length (meters)",
        default: 1000,
      };
          } else if (bufferType === "zones_grid") {
      bufferProperties.wide = {
        type: "number",
        title: "Width (meters)",
        default: 1000,
      };
      bufferProperties.length = {
        type: "number",
        title: "Length (meters)",
        default: 1000,
      };
    } else if (bufferType === "isochrone") {
      bufferProperties.travel_time = {
        type: "array",
        title: "Travel Time (minutes)",
        items: { type: "number" },
        default: [15],
      };
      bufferProperties.speed = {
        type: "number",
        title: "Speed (km/h)",
        default: 4.5,
      };
      bufferProperties.network_type = {
        type: "string",
        title: "Network Type",
        enum: ["walk", "bike", "drive"],
        default: "walk",
      };
      bufferProperties.network_buffer = {
        type: "number",
        title: "Network Buffer Distance (meters)",
        default: 5000,
      };
    } else if (bufferType === "network") {
      bufferProperties.distance = {
        type: "number",
        title: "Distance (meters)",
        default: 500,
      };
      bufferProperties.network_type = {
        type: "string",
        title: "Network Type",
        enum: ["walk", "bike", "drive"],
        default: "walk",
      };
      bufferProperties.osm_file = {
        type: "string",
        title: "Network OSM File (optional)",
        description: "Name of the file to use for the network buffers. The file needs to be in the path src/utils/buffer/networks and need to be in xml format.",
      };
    }
    // Pas de champs pour "zones"

    newSchema.properties.buffer_layer.required = ["layer_name", "geometry_type", "buffer_type"];
    if (bufferType === "circular") {
      newSchema.properties.buffer_layer.required.push("distance");
    } else if (bufferType === "grid") {
      newSchema.properties.buffer_layer.required.push("wide", "length");
    } else if (bufferType === "zones_grid") {
      newSchema.properties.buffer_layer.required.push("wide", "length");
    } else if (bufferType === "isochrone") {
      newSchema.properties.buffer_layer.required.push("travel_time", "speed", "network_type", "network_buffer");
    } else if (bufferType === "network") {
    newSchema.properties.buffer_layer.required.push("distance", "network_type"); // osm_file reste optionnel
    }
    console.log("Updated schema:", JSON.stringify(newSchema.properties.buffer_layer, null, 2)); // Debug
    return newSchema;
  };

  const onChange = ({ formData }) => {
    const newBufferType = formData.buffer_layer?.buffer_type || "circular";

    // Mettre à jour le schéma dynamiquement pour buffer_layer
    setSchema(prev => updateBufferLayerSchema(prev, newBufferType));

    // Mettre à jour formData uniquement pour buffer_layer
    const updatedFormData = {
      ...formData,
      buffer_layer: {
        ...formData.buffer_layer,
        buffer_type: newBufferType,
      },
    };

    // Ajuster les champs dynamiques de buffer_layer
    if (newBufferType === "circular") {
      updatedFormData.buffer_layer.distance = formData.buffer_layer?.distance || 1000;
      delete updatedFormData.buffer_layer.wide;
      delete updatedFormData.buffer_layer.length;
      delete updatedFormData.buffer_layer.travel_time;
      delete updatedFormData.buffer_layer.speed;
      delete updatedFormData.buffer_layer.network_type;
      delete updatedFormData.buffer_layer.network_buffer;
      delete updatedFormData.buffer_layer.osm_file;
    } else if (newBufferType === "grid") {
      updatedFormData.buffer_layer.wide = formData.buffer_layer?.wide || 1000;
      updatedFormData.buffer_layer.length = formData.buffer_layer?.length || 1000;
      delete updatedFormData.buffer_layer.distance;
      delete updatedFormData.buffer_layer.travel_time;
      delete updatedFormData.buffer_layer.speed;
      delete updatedFormData.buffer_layer.network_type;
      delete updatedFormData.buffer_layer.network_buffer;
      delete updatedFormData.buffer_layer.osm_file;
    } else if (newBufferType === "zones_grid") {
      updatedFormData.buffer_layer.wide = formData.buffer_layer?.wide || 1000;
      updatedFormData.buffer_layer.length = formData.buffer_layer?.length || 1000;
      delete updatedFormData.buffer_layer.distance;
      delete updatedFormData.buffer_layer.travel_time;
      delete updatedFormData.buffer_layer.speed;
      delete updatedFormData.buffer_layer.network_type;
      delete updatedFormData.buffer_layer.network_buffer;
      delete updatedFormData.buffer_layer.osm_file;
    } else if (newBufferType === "isochrone") {
      updatedFormData.buffer_layer.travel_time = formData.buffer_layer?.travel_time || [15];
      updatedFormData.buffer_layer.speed = formData.buffer_layer?.speed || 4.5;
      updatedFormData.buffer_layer.network_type = formData.buffer_layer?.network_type || "walk";
      updatedFormData.buffer_layer.network_buffer = formData.buffer_layer?.network_buffer || 5000;
      delete updatedFormData.buffer_layer.distance;
      delete updatedFormData.buffer_layer.wide;
      delete updatedFormData.buffer_layer.length;
      delete updatedFormData.buffer_layer.osm_file;
    } else if (newBufferType === "network") {
      updatedFormData.buffer_layer.distance = formData.buffer_layer?.distance || 500;
      updatedFormData.buffer_layer.network_type = formData.buffer_layer?.network_type || "walk";
      updatedFormData.buffer_layer.osm_file = formData.buffer_layer?.osm_file || "";
      delete updatedFormData.buffer_layer.wide;
      delete updatedFormData.buffer_layer.length;
      delete updatedFormData.buffer_layer.travel_time;
      delete updatedFormData.buffer_layer.speed;
    } else if (newBufferType === "zones") {
      delete updatedFormData.buffer_layer.distance;
      delete updatedFormData.buffer_layer.wide;
      delete updatedFormData.buffer_layer.length;
      delete updatedFormData.buffer_layer.travel_time;
      delete updatedFormData.buffer_layer.speed;
      delete updatedFormData.buffer_layer.network_type;
      delete updatedFormData.buffer_layer.network_buffer;
      delete updatedFormData.buffer_layer.osm_file;
    }

    // Log pour déboguer
    console.log("Updated formData:", JSON.stringify(updatedFormData, null, 2));

    // Mettre à jour l’état
    setFormData(updatedFormData);
  };

  const onSubmit = ({ formData }) => {
    const bufferLayerData = {
      [formData.buffer_layer.layer_name]: {
        buffer_type: formData.buffer_layer.buffer_type,
        geometry_type: formData.buffer_layer.geometry_type
      }
    };

    if (formData.buffer_layer.buffer_type === "circular") {
      bufferLayerData[formData.buffer_layer.layer_name].distance = formData.buffer_layer.distance;
    } else if (formData.buffer_layer.buffer_type === "grid") {
      bufferLayerData[formData.buffer_layer.layer_name].wide = formData.buffer_layer.wide;
      bufferLayerData[formData.buffer_layer.layer_name].length = formData.buffer_layer.length;
    } else if (formData.buffer_layer.buffer_type === "zones_grid") {
      bufferLayerData[formData.buffer_layer.layer_name].wide = formData.buffer_layer.wide;
      bufferLayerData[formData.buffer_layer.layer_name].length = formData.buffer_layer.length;
    } else if (formData.buffer_layer.buffer_type === "isochrone") {
      bufferLayerData[formData.buffer_layer.layer_name].travel_time = formData.buffer_layer.travel_time;
      bufferLayerData[formData.buffer_layer.layer_name].speed = formData.buffer_layer.speed;
      bufferLayerData[formData.buffer_layer.layer_name].network_type = formData.buffer_layer.network_type;
      bufferLayerData[formData.buffer_layer.layer_name].distance = formData.buffer_layer.network_buffer;
    } else if (formData.buffer_layer.buffer_type === "network") {
    bufferLayerData[formData.buffer_layer.layer_name].distance = formData.buffer_layer.distance;
    bufferLayerData[formData.buffer_layer.layer_name].network_type = formData.buffer_layer.network_type;
    if (formData.buffer_layer.osm_file) {
      bufferLayerData[formData.buffer_layer.layer_name].osm_file = formData.buffer_layer.osm_file;
      }
    }

    const yamlData = {
      buffer_layer: bufferLayerData,
      data_files: formData.data_files.map(file => ({ name: file.name, path: file.path })),
      filter_data_files: formData.filter_data_files,
      ratio_columns: formData.ratio_columns,
      multiply_columns: formData.multiply_columns,
      sum_columns: formData.sum_columns,
      max_columns: formData.max_columns,
      min_columns: formData.min_columns,
      mean_columns: formData.mean_columns,
      std_columns: formData.std_columns,
      count_columns: formData.count_columns,
      count_distinct_columns: formData.count_distinct_columns,
      groupby_columns: formData.groupby_columns,
      filter_global: formData.filter_global,
      post_aggregation_metrics: formData.post_aggregation_metrics,
      activate_visualisation: formData.activate_visualisation,
      join_layers: formData.join_layers,
      colors: formData.colors
    };

    console.log("yamlData envoyé au backend :", JSON.stringify(yamlData, null, 2));

    fetch('http://127.0.0.1:5000/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(yamlData),
    })
    .then(response => {
      if (!response.ok) throw new Error('Network response was not ok');
      return response.json();
    })
    .then(data => {
      setSubmitMessage('Configuration submitted successfully!');
      console.log('Success:', data);

      const bufferType = formData.buffer_layer.buffer_type;
      let fetchParams;

      if (bufferType === 'circular') {
        fetchParams = `${bufferType}_buffer_${formData.buffer_layer.distance}m`;
      } else if (bufferType === 'grid') {
        fetchParams = `${bufferType}_buffer_${formData.buffer_layer.wide}m_${formData.buffer_layer.length}m`;
      } else if (bufferType === 'zones_grid') {
        fetchParams = `${bufferType}_buffer_${formData.buffer_layer.wide}m_${formData.buffer_layer.length}m`;
      } else if (bufferType === "isochrone") {
        const travelTime = formData.buffer_layer.travel_time[0] || 15;
        const networkType = formData.buffer_layer.network_type || "walk";
        fetchParams = `${bufferType}_buffer_${networkType}_${travelTime}min`;
      } else if (bufferType === 'network') {
        const networkType = formData.buffer_layer.network_type || "walk";
        fetchParams = `${bufferType}_buffer_${networkType}_${formData.buffer_layer.distance}m`;
      } else if (bufferType === 'zones') {
        fetchParams = `${bufferType}_buffer`;
      }

      const cacheBuster = `?t=${Date.now()}`;
      fetch(`http://127.0.0.1:5000/get_table_html/${fetchParams}${cacheBuster}`)
        .then(response => response.text())
        .then(setTableHTML);

      fetch(`http://127.0.0.1:5000/get_map_html/${fetchParams}${cacheBuster}`)
        .then(response => response.text())
        .then(setMapHTML);
    })
    .catch(error => {
      setSubmitMessage(`Error: ${error.message}`);
      console.error('Error:', error);
    });
  };

  const onHistogramSubmit = ({ formData }) => {
    setHistogramFormData(formData);

    let bins = formData.customBins
      .split(',')
      .map((val) => {
        val = val.trim();
        if (val.toLowerCase() === 'infinity') return Infinity;
        return parseFloat(val);
      })
      .filter((val) => !isNaN(val));

    const labels = formData.customLabels
      .split(',')
      .map((val) => val.trim())
      .filter((val) => val !== '');

    if (bins.length < 2) {
      setHistograms({
        error: `<div class="error">Error: Please provide at least two bin edges (e.g., "0,10,20,40,Infinity").</div>`
      });
      return;
    }

    const lastLabel = labels[labels.length - 1];
    if (lastLabel.endsWith('+') && bins[bins.length - 1] !== Infinity) {
      bins.push(Infinity);
    }

    const expectedLabelCount = bins.length - 1;
    if (labels.length !== expectedLabelCount) {
      setHistograms({
        error: `<div class="error">Error: Number of labels (${labels.length}) must be equal to number of bins (${expectedLabelCount}). For bins ${bins.join(',')}, provide ${expectedLabelCount} labels (e.g., "0-9,10-19,20-29,30-39,40+").</div>`
      });
      return;
    }

    const binsForSerialization = bins.map((val) =>
      val === Infinity ? "Infinity" : val
    );

    const configToSend = {
      ...formData,
      customBins: binsForSerialization,
      customLabels: labels,
    };

    fetch('http://127.0.0.1:5000/generate_histogram', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(configToSend),
    })
    .then(response => {
      if (!response.ok) throw new Error('Failed to generate histograms');
      return response.json();
    })
    .then(data => {
      const histogramPromises = Object.entries(data.histograms).map(([column, filepath]) =>
        fetch(`http://127.0.0.1:5000/get_histogram_html/${filepath.split('/').pop()}?t=${Date.now()}`)
          .then(response => response.text())
          .then(html => ({ column, html }))
          .catch(error => ({
            column,
            html: `<div class="error">Error loading histogram: ${error.message}</div>`
          }))
      );

      Promise.all(histogramPromises)
        .then(results => {
          const newHistograms = {};
          results.forEach(({ column, html }) => {
            newHistograms[column] = html;
          });
          setHistograms(newHistograms);
        });
    })
    .catch(error => {
      console.error('Error generating histograms:', error);
      setHistograms({
        error: `<div class="error">Error: ${error.message}</div>`
      });
    });
  };

  const onBarChartSubmit = ({ formData }) => {
    setBarChartFormData(formData);

    const configToSend = {
      ...formData,
    };

    fetch('http://127.0.0.1:5000/generate_barchart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(configToSend),
    })
    .then(response => {
      if (!response.ok) throw new Error('Failed to generate bar charts');
      return response.json();
    })
    .then(data => {
      const barChartPromises = Object.entries(data.barcharts).map(([column, filepath]) =>
        fetch(`http://127.0.0.1:5000/get_barchart_html/${filepath.split('/').pop()}?t=${Date.now()}`)
          .then(response => response.text())
          .then(html => ({ column, html }))
          .catch(error => ({
            column,
            html: `<div class="error">Error loading bar chart: ${error.message}</div>`
          }))
      );

      Promise.all(barChartPromises)
        .then(results => {
          const newBarCharts = {};
          results.forEach(({ column, html }) => {
            newBarCharts[column] = html;
          });
          setBarCharts(newBarCharts);
        });
    })
    .catch(error => {
      console.error('Error generating bar charts:', error);
      setBarCharts({
        error: `<div class="error">Error: ${error.message}</div>`
      });
    });
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const addFilter = () => {
    const fileName = prompt('Enter the name of the file to add a filter for:');
    if (fileName && !formData.filter_data_files[fileName]) {
      setFormData(prevFormData => ({
        ...prevFormData,
        filter_data_files: {
          ...prevFormData.filter_data_files,
          [fileName]: {}
        }
      }));
    }
  };

  const removeFilter = (fileName) => {
    setFormData(prevFormData => {
      const { [fileName]: _, ...remainingFilters } = prevFormData.filter_data_files;
      return {
        ...prevFormData,
        filter_data_files: remainingFilters
      };
    });
  };

  const CustomObjectFieldTemplate = (props) => {
    return (
      <div>
        <button type="button" onClick={addFilter}>Add Filter</button>
        {Object.keys(props.properties).map((name, index) => (
          <div key={index}>
            <h4>{name}</h4>
            <button type="button" onClick={() => removeFilter(name)}>Remove Filter</button>
            {props.properties[name].content}
          </div>
        ))}
      </div>
    );
  };

  const uiSchema = {
    "ui:order": [
      "data_files", "buffer_layer", "filter_data_files", "ratio_columns", "multiply_columns",
      "sum_columns", "max_columns", "min_columns", "mean_columns", "std_columns",
      "count_columns", "count_distinct_columns", "groupby_columns", "filter_global",
      "post_aggregation_metrics", "activate_visualisation", "join_layers", "colors"
    ],
    data_files: {
      "items": {
        name: { "ui:placeholder": "Enter custom file name" },
        path: { "ui:disabled": true, "ui:widget": "text" }
      }
    },
    buffer_layer: {
      osm_file: {"ui:placeholder": "Nom du fichier OSM (ex: montreal_walk.graphml)"},
      layer_name: { "ui:placeholder": "Enter layer name" },
      geometry_type: { "ui:placeholder": "Select geometry type" },
      buffer_type: { "ui:placeholder": "Select buffer type" },
      distance: { "ui:placeholder": "Enter buffer distance in meters" },
      wide: { "ui:placeholder": "Enter buffer width in meters" },
      length: { "ui:placeholder": "Enter buffer length in meters" },
      travel_time: {
        "ui:placeholder": "Enter travel time in minutes (e.g., 15)",
        items: { "ui:placeholder": "Enter a travel time value" },
      },
      speed: { "ui:placeholder": "Enter speed in km/h (e.g., 4.5)" },
      network_type: { "ui:widget": "select", "ui:placeholder": "Select network type" },
      network_buffer: { "ui:placeholder": "Enter network buffer distance in meters (e.g., 5000)" },
    },
    ratio_columns: {
      "items": {
        name: { "ui:placeholder": "Enter ratio name" },
        numerator: { "ui:placeholder": "Enter numerator column" },
        denominator: { "ui:placeholder": "Enter denominator column" }
      }
    },
    multiply_columns: {
      "items": {
        name: { "ui:placeholder": "Enter multiply name" },
        columns: { "items": { "ui:placeholder": "Enter column to multiply" } }
      }
    },
    "post_aggregation_metrics": {
      "ratio": {
        "items": {
          "name": { "ui:placeholder": "Enter ratio name" },
          "numerator": { "ui:placeholder": "Enter numerator column" },
          "denominator": { "ui:placeholder": "Enter denominator column" }
        }
      }
    },
    filter_data_files: {
      "ui:ObjectFieldTemplate": CustomObjectFieldTemplate
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>MobilityDataFusion</h1>
        <p style={{ textAlign: 'center', opacity: 0.8, marginTop: '0.5rem' }}>
          Analyse et visualisation de données de mobilité géospatiales
        </p>
      </header>

      <div className="tab-buttons">
        <button 
          className={`tab-button ${activeTab === 'data-explorer' ? 'active' : ''}`}
          onClick={() => handleTabChange('data-explorer')}
        >
          {Icons.data} Explorateur
        </button>
        <button 
          className={`tab-button ${activeTab === 'form' ? 'active' : ''}`}
          onClick={() => handleTabChange('form')}
        >
          {Icons.config} Configuration
        </button>
        <button 
          className={`tab-button ${activeTab === 'tables' ? 'active' : ''}`}
          onClick={() => handleTabChange('tables')}
        >
          {Icons.table} Tableaux
        </button>
        <button 
          className={`tab-button ${activeTab === 'map' ? 'active' : ''}`}
          onClick={() => handleTabChange('map')}
        >
          {Icons.map} Carte
        </button>
        <button 
          className={`tab-button ${activeTab === 'histogram' ? 'active' : ''}`}
          onClick={() => handleTabChange('histogram')}
        >
          {Icons.chart} Histogrammes
        </button>
        <button 
          className={`tab-button ${activeTab === 'barchart' ? 'active' : ''}`}
          onClick={() => handleTabChange('barchart')}
        >
          {Icons.chart} Bar Charts
        </button>
      </div>

      {activeTab === 'data-explorer' && (
        <div className="data-explorer-container fade-in">
          <h2>{Icons.data} Explorateur de données</h2>
          <div className="file-tabs">
            {dataFiles.map(fileName => (
              <button
                key={fileName}
                onClick={() => setActiveDataExplorerFile(fileName)}
                className={activeDataExplorerFile === fileName ? 'active' : ''}
              >
                {fileName}
              </button>
            ))}
          </div>

          {activeDataExplorerFile && (
            <div className="file-preview">
              <h3>{activeDataExplorerFile}</h3>
              {filePreviews[activeDataExplorerFile] ? (
                <div>
                  <table>
                    <thead>
                      <tr>
                        {filePreviews[activeDataExplorerFile].columns?.map(col => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filePreviews[activeDataExplorerFile].data?.map((row, index) => (
                        <tr key={index}>
                          {filePreviews[activeDataExplorerFile].columns?.map(col => (
                            <td key={col}>
                              {typeof row[col] === 'object'
                                ? JSON.stringify(row[col])
                                : row[col]}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p>Loading preview for {activeDataExplorerFile}...</p>
              )}
            </div>
          )}

          {!activeDataExplorerFile && (
            <p>Select a file from the tabs above to view its preview</p>
          )}
        </div>
      )}

      {activeTab === 'form' && (
        <div className="form-container">
          {Object.keys(schema).length > 0 ? (
            <div className="enhanced-form">
              <div className="section-header">
                <h3>{Icons.config} Configuration de l'analyse</h3>
              </div>
              <Form
                schema={schema}
                uiSchema={uiSchema}
                formData={formData}
                onChange={onChange}
                onSubmit={onSubmit}
              >
                <div className="submit-section">
                  <button type="submit" className="submit-button">
                    {Icons.play} Lancer l'analyse
                  </button>
                </div>
              </Form>
            </div>
          ) : (
            <div className="loading-message">
              {Icons.refresh} Chargement de la configuration...
            </div>
          )}
        </div>
      )}

      {activeTab === 'tables' && (
        <div className="table-container fade-in">
          <h2>{Icons.table} Tableau de données</h2>
          {tableHTML ? (
            <iframe
              title="data-table"
              srcDoc={tableHTML}
              className="full-iframe"
            />
          ) : (
            <div className="empty-state">
              <p>{Icons.info} Aucun tableau généré. Configurez et lancez l'analyse pour voir les résultats.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'map' && (
        <div className="map-container fade-in">
          <h2>{Icons.map} Visualisation cartographique</h2>
          {mapHTML ? (
            <div>
              <div className="map-tabs">
                <button 
                  className={`map-tab ${!baseMapHTML ? 'active' : ''}`}
                  onClick={() => setMapHTML('')}
                >
                  {Icons.map} Carte d'analyse
                </button>
                {baseMapHTML && (
                  <button 
                    className={`map-tab ${baseMapHTML ? 'active' : ''}`}
                    onClick={() => setMapHTML(baseMapHTML)}
                  >
                    {Icons.data} Données brutes
                  </button>
                )}
              </div>
              <iframe
                title="map-visualization"
                srcDoc={mapHTML}
                className="full-iframe"
              />
            </div>
          ) : baseMapHTML ? (
            <div>
              <div className="map-tabs">
                <button className="map-tab active">
                  {Icons.data} Données brutes
                </button>
                <button 
                  className="map-tab"
                  onClick={() => setMapHTML('')}
                >
                  {Icons.map} Carte d'analyse
                </button>
              </div>
              <iframe
                title="base-map"
                srcDoc={baseMapHTML}
                className="full-iframe"
              />
            </div>
          ) : (
            <div className="empty-state">
              <p>{Icons.info} Aucune donnée géographique disponible. Vérifiez que vos fichiers GeoJSON sont correctement chargés.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'histogram' && (
        <div className="histogram-container fade-in">
          <h2>{Icons.chart} Histogrammes</h2>
          <div className="histogram-form">
            <Form
              schema={histogramSchema}
              uiSchema={histogramUiSchema}
              formData={histogramFormData}
              onChange={({ formData }) => setHistogramFormData(formData)}
              onSubmit={onHistogramSubmit}
            >
              <button type="submit" className="submit-button">
                {Icons.chart} Générer les histogrammes
              </button>
            </Form>
          </div>
          {Object.keys(histograms).length === 0 ? (
            <p>No histograms generated yet. Configure and submit above to generate histograms.</p>
          ) : histograms.error ? (
            <div dangerouslySetInnerHTML={{ __html: histograms.error }} />
          ) : (
            Object.entries(histograms).map(([columnName, html]) => (
              <div key={columnName} className="histogram-item">
                <h3>{columnName}</h3>
                <iframe
                  title={`histogram-${columnName}`}
                  srcDoc={html}
                  className="histogram-iframe"
                />
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'barchart' && (
        <div className="barchart-container fade-in">
          <h2>{Icons.chart} Bar Charts</h2>
          <div className="barchart-form">
            <Form
              schema={barChartSchema}
              uiSchema={barChartUiSchema}
              formData={barChartFormData}
              onChange={({ formData }) => setBarChartFormData(formData)}
              onSubmit={onBarChartSubmit}
            >
              <button type="submit" className="submit-button">
                {Icons.chart} Générer les bar charts
              </button>
            </Form>
          </div>
          {Object.keys(barCharts).length === 0 ? (
            <p>No bar charts generated yet. Configure and submit above to generate bar charts.</p>
          ) : barCharts.error ? (
            <div dangerouslySetInnerHTML={{ __html: barCharts.error }} />
          ) : (
            Object.entries(barCharts).map(([columnName, html]) => (
              <div key={columnName} className="barchart-item">
                <h3>{columnName}</h3>
                <iframe
                  title={`barchart-${columnName}`}
                  srcDoc={html}
                  className="barchart-iframe"
                />
              </div>
            ))
          )}
        </div>
      )}

      {submitMessage && <div className="status-message">{submitMessage}</div>}
    </div>
  );
};

export default App;