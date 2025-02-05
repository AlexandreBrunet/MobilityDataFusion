import React, { useState, useEffect } from 'react';
import Form from 'react-jsonschema-form';
import * as yaml from 'js-yaml';
import './App.css';

const sampleConfig = `
buffer_layer:
  bixi_stations:
    geometry_type: "Point"
    buffer_type: "circular"
    distance: 500
filter_data_files:
  bus_stops:
    column:
    value:
  bixi_stations:
    column: "capacity"
    value: 0
    operator: ">="
ratio_columns:
  permis_perslogi_ratio:
    numerator: "permis"
    denominator: "perslogi"
sum_columns:
  - "permis as total_permis"
  - "autologi as total_autologi"
max_columns:
  - "capacity as max_capacity"
min_columns:
  - "capacity as min_capacity"
mean_columns:
  - "SUPERFICIE_TERRAIN as moy_superficie_terrain"
  - "LONGUEUR as moy_long_piste_cy"
std_columns:
  - "SUPERFICIE_TERRAIN as std_superficie_terrain"
count_columns:
  - "stop_id as count_arret_bus"
  - "feuillet as count_nb_menage"
  - "ID_UEV as count_num_bati"
count_distinct_columns:
  - "station_id as count_bixi_station"
groupby_columns:
  - "buffer_id"
  - "name"
filter_global:
  - column: "count_arret_bus_count"
    value: 0
    operator: ">="
activate_visualisation: false
join_layers:
  points:
    type: "contains"
  polygons:
    type: "intersects"
  multipolygons:
    type: "intersects"
  linestrings:
    type: "intersects"
colors:
  bus_stops: "[0, 200, 0, 160]"
  bixi_stations: "[200, 30, 0, 160]"
  evaluation_fonciere: "[0, 30, 200, 160]"
  menage_2018: "[255, 255, 0, 160]"
  reseau_cyclable: "[255, 165, 0, 160]"
`;

const config = yaml.load(sampleConfig);

const App = () => {
  const [formData, setFormData] = useState(config);
  const [schema, setSchema] = useState({});
  const [submitMessage, setSubmitMessage] = useState('');
  const [fileList, setFileList] = useState({});
  const [tableHTML, setTableHTML] = useState('');
  const [mapHTML, setMapHTML] = useState('');
  const [activeTab, setActiveTab] = useState('form');
  const [histograms, setHistograms] = useState({});

  useEffect(() => {
    fetch('http://127.0.0.1:5000/list_files')
      .then(response => response.json())
      .then(data => {
        console.log('Fetched file list:', data);
        setFileList(data);

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
                  default: "stations_bixi"
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
                  enum: ["circular", "grid", "isochrone", "zones", "zones_grid"],
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
            histogram_config: {
              type: "object",
              title: "Histogram Configuration",
              properties: {
                columns: {
                  type: "array",
                  title: "Columns",
                  items: { type: "string" }
                },
                binsize: {
                  type: "number",
                  title: "Bin Size",
                  default: 10
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
                  name: {
                    type: "string",
                    title: "Ratio Name",
                    default: "permis_perslogi_ratio"
                  },
                  numerator: {
                    type: "string",
                    title: "Numerator",
                    default: "permis"
                  },
                  denominator: {
                    type: "string",
                    title: "Denominator",
                    default: "perslogi"
                  }
                },
                required: ["name", "numerator", "denominator"]
              }
            },
            sum_columns: {
              type: "array",
              items: { type: "string", title: "Sum Column" }
            },
            max_columns: {
              type: "array",
              items: { type: "string", title: "Max Column" }
            },
            min_columns: {
              type: "array",
              items: { type: "string", title: "Min Column" }
            },
            mean_columns: {
              type: "array",
              items: { type: "string", title: "Mean Column" }
            },
            std_columns: {
              type: "array",
              items: { type: "string", title: "Standard Deviation Column" }
            },
            count_columns: {
              type: "array",
              items: { type: "string", title: "Count Column" }
            },
            count_distinct_columns: {
              type: "array",
              items: { type: "string", title: "Count Distinct Column" }
            },
            groupby_columns: {
              type: "array",
              items: { type: "string", title: "Group By Column" }
            },
            filter_global: {
              type: "array",
              title: "Global Filters",
              items: {
                type: "object",
                properties: {
                  column: { type: "string", title: "Column" },
                  value: {
                    anyOf: [
                      { type: "number", title: "Value (Number)" },
                      { type: "string", title: "Value (String)" }
                    ]
                  },
                  operator: { type: "string", title: "Operator", enum: ["==", ">=", "<=", ">", "<", "!="] }
                },
                required: ["column", "value", "operator"]
              }
            },
            activate_visualisation: {
              type: "boolean",
              title: "Activate Visualisation"
            },
            join_layers: {
              type: "object",
              title: "Join Layers",
              properties: {
                points: {
                  type: "object",
                  properties: {
                    type: { type: "string", title: "Join Type for Points", enum: ["contains", "intersects"] }
                  }
                },
                polygons: {
                  type: "object",
                  properties: {
                    type: { type: "string", title: "Join Type for Polygons", enum: ["contains", "intersects"] }
                  }
                },
                multipolygons: {
                  type: "object",
                  properties: {
                    type: { type: "string", title: "Join Type for MultiPolygons", enum: ["contains", "intersects"] }
                  }
                },
                linestrings: {
                  type: "object",
                  properties: {
                    type: { type: "string", title: "Join Type for LineStrings", enum: ["contains", "intersects"] }
                  }
                }
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
          required: ["data_files", "buffer_layer", "filter_data_files", "ratio_columns", "sum_columns", "max_columns", "min_columns", "mean_columns", "std_columns", "count_columns", "count_distinct_columns", "groupby_columns", "filter_global", "activate_visualisation", "join_layers", "colors"]
        };

        setSchema(baseSchema);

        setFormData(prevFormData => ({
          ...prevFormData,
          data_files: dataFilesList,
          buffer_layer: {
            [prevFormData.buffer_layer ? Object.keys(prevFormData.buffer_layer)[0] : "bixi_stations"]: {
              buffer_type: "circular",
              distance: 1000,
              geometry_type: "Point"
            }
          },
          filter_data_files: {},
          colors: Object.keys(data).reduce((acc, layerName) => {
            acc[layerName] = "[200, 30, 0, 160]";
            return acc;
          }, {})
        }));
      })
      .catch(error => console.error('Error fetching file list:', error));
  }, []);

  const updateBufferLayerSchema = (currentSchema, bufferType) => {
    const newSchema = { ...currentSchema };
    const bufferProperties = newSchema.properties.buffer_layer.properties;
    
    delete bufferProperties.distance;
    delete bufferProperties.wide;
    delete bufferProperties.length;
  
  
    // Add appropriate properties based on buffer type

    // Add appropriate properties based on buffer type
    if (bufferType === "circular") {
      bufferProperties.distance = {
        type: "number",
        title: "Distance (meters)",
        default: 1000
      };
    } else if (bufferType === "grid") {
      bufferProperties.wide = {
        type: "number",
        title: "Width (meters)",
        default: 1000
      };
      bufferProperties.length = {
        type: "number",
        title: "Length (meters)",
        default: 1000
      };
    }

    return newSchema;
  };

  const onChange = ({ formData }) => {
    const newBufferType = formData.buffer_layer.buffer_type;
    setSchema(prev => updateBufferLayerSchema(prev, newBufferType));
    setFormData(formData);
  };

  const onSubmit = ({ formData }) => {
    const bufferLayerData = {
      [formData.buffer_layer.layer_name]: {
        buffer_type: formData.buffer_layer.buffer_type,
        geometry_type: formData.buffer_layer.geometry_type
      }
    };
  
  
    // Add appropriate properties based on buffer type

    // Add appropriate properties based on buffer type
    if (formData.buffer_layer.buffer_type === "circular") {
      bufferLayerData[formData.buffer_layer.layer_name].distance = formData.buffer_layer.distance;
    } else if (formData.buffer_layer.buffer_type === "grid") {
      bufferLayerData[formData.buffer_layer.layer_name].wide = formData.buffer_layer.wide;
      bufferLayerData[formData.buffer_layer.layer_name].length = formData.buffer_layer.length;
    }

    const yamlData = {
      buffer_layer: bufferLayerData,
      data_files: formData.data_files.map(file => ({ name: file.name, path: file.path })),
      filter_data_files: formData.filter_data_files,
      ratio_columns: formData.ratio_columns,
      sum_columns: formData.sum_columns,
      max_columns: formData.max_columns,
      min_columns: formData.min_columns,
      mean_columns: formData.mean_columns,
      std_columns: formData.std_columns,
      count_columns: formData.count_columns,
      count_distinct_columns: formData.count_distinct_columns,
      groupby_columns: formData.groupby_columns,
      filter_global: formData.filter_global,
      activate_visualisation: formData.activate_visualisation,
      join_layers: formData.join_layers,
      colors: formData.colors,
      histogram_config: formData.histogram_config
    };
  
  
    console.log("Submitted data in YAML format:", yaml.dump(yamlData));
  

    console.log("Submitted data in YAML format:", yaml.dump(yamlData));
  
    fetch('http://127.0.0.1:5000/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(yamlData),
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      setSubmitMessage('Configuration submitted successfully!');
      console.log('Success:', data);
    
    
      // Fetch the table and map HTML based on buffer type

      // Fetch the table and map HTML based on buffer type
      const bufferType = formData.buffer_layer.buffer_type;
      let fetchParams;

      if (bufferType === 'circular') {
        fetchParams = `${bufferType}_buffer_${formData.buffer_layer.distance}m`;
      } else if (bufferType === 'grid') {
        fetchParams = `${bufferType}_buffer_${formData.buffer_layer.wide}m_${formData.buffer_layer.length}m`;
      } else if (bufferType === 'zones') {
        fetchParams = `${bufferType}_buffer`;
      }

      const histPromises = formData.histogram_config.columns.map(columnConfig => {
        const aggregationType = formData.histogram_config.aggregation.type || 'count';
        const aggregationColumn = formData.histogram_config.aggregation.column || columnConfig;
        const groupBy = formData.histogram_config.groupby || "None";
        
        return fetch(
            `http://127.0.0.1:5000/get_histogram_html/${encodeURIComponent(aggregationType)}/${encodeURIComponent(aggregationColumn)}/${encodeURIComponent(groupBy)}?t=${Date.now()}`
        )
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.text();
        })
        .then(html => ({ column: aggregationColumn, html }))
        .catch(error => {
            console.error('Error loading histogram:', error);
            return { column: aggregationColumn, html: `<div class="error">Error loading histogram: ${error.message}</div>` };
        });
    });

      Promise.all(histPromises)
        .then(results => {
          const newHistograms = {};
          results.forEach(({ column, html }) => {
            newHistograms[column] = html;
          });
          setHistograms(newHistograms);
          setActiveTab('histogram');
        });

      // Fetch table and map
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
      "data_files",
      "buffer_layer",
      "filter_data_files",
      "ratio_columns",
      "sum_columns",
      "max_columns",
      "min_columns",
      "mean_columns",
      "std_columns",
      "count_columns",
      "count_distinct_columns",
      "groupby_columns",
      "filter_global",
      "activate_visualisation",
      "join_layers",
      "colors",
      "histogram_config"
    ],
    data_files: {
      "items": {
        name: {
          "ui:placeholder": "Enter custom file name"
        },
        path: {
          "ui:disabled": true,
          "ui:widget": "text"
        }
      }
    },
    buffer_layer: {
      layer_name: {
        "ui:placeholder": "Enter layer name"
      },
      geometry_type: {
        "ui:placeholder": "Select geometry type"
      },
      buffer_type: {
        "ui:placeholder": "Select buffer type"
      },
      distance: {
        "ui:placeholder": "Enter buffer distance in meters"
      }
    },
    ratio_columns: {
      "items": {
        name: {
          "ui:placeholder": "Enter ratio name"
        },
        numerator: {
          "ui:placeholder": "Enter denominator column"
        }
      }
    },
    filter_data_files: {
      "ui:ObjectFieldTemplate": CustomObjectFieldTemplate
    },
    histogram_config: {
      columns: {
        "ui:widget": "array",
        "items": {
          "ui:placeholder": "Enter column name"
        }
      },
      binsize: {
        "ui:placeholder": "Enter bin size"
      },
      groupby: {
        "ui:placeholder": "Enter group by column"
      },
      aggregation: {
        type: {
          "ui:widget": "select",
          "ui:options": {
            "enumOptions": [
              { "value": "count", "label": "Count" },
              { "value": "sum", "label": "Sum" }
            ]
          }
        },
        column: {
          "ui:placeholder": "Enter aggregation column"
        }
      }
    }
  };

  return (
    <div className="App">
      <h1>Data Fusion UI</h1>
      <div className="tab-buttons">
        <button onClick={() => handleTabChange('form')}>Form</button>
        <button onClick={() => handleTabChange('tables')}>Tables</button>
        <button onClick={() => handleTabChange('map')}>Map</button>
        <button onClick={() => handleTabChange('histogram')}>Histograms</button>
      </div>

      {activeTab === 'form' && (
        <div className="form-container">
          {Object.keys(schema).length > 0 ? (
            <Form
              schema={schema}
              uiSchema={uiSchema}
              formData={formData}
              onChange={onChange}
              onSubmit={onSubmit}
            >
              <button type="submit">Submit</button>
            </Form>
          ) : (
            <div>Loading configuration...</div>
          )}
        </div>
      )}

      {activeTab === 'tables' && (
        <div className="table-container">
          <h2>Data Table</h2>
          {tableHTML && (
            <iframe
              title="data-table"
              srcDoc={tableHTML}
              className="full-iframe"
            />
          )}
        </div>
      )}

      {activeTab === 'map' && (
        <div className="map-container">
          <h2>Map Visualization</h2>
          {mapHTML && (
            <iframe
              title="map-visualization"
              srcDoc={mapHTML}
              className="full-iframe"
            />
          )}
        </div>
      )}

      {activeTab === 'histogram' && (
        <div className="histogram-container">
          <h2>Histograms</h2>
          {Object.keys(histograms).length === 0 ? (
            <p>No histograms generated yet. Submit the form to generate histograms.</p>
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

      {submitMessage && <div className="status-message">{submitMessage}</div>}
    </div>
  );
};

export default App;