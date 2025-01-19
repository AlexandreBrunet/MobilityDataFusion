import React, { useState, useEffect } from 'react';
import Form from 'react-jsonschema-form';
import * as yaml from 'js-yaml';

const sampleConfig = `
data_files:
  bus_stops: "./data/input/geojson/stm_bus_stops.geojson"
  bixi_stations: "./data/input/geojson/stations_bixi.geojson"
  evaluation_fonciere: "./data/input/geojson/uniteevaluationfonciere.geojson"
  menage_2018: "./data/input/geojson/od_2018.geojson"
  reseau_cyclable: "./data/input/geojson/reseau_cyclable.geojson"
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
    operator: ">"
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

  useEffect(() => {
    const generatedSchema = {
      type: "object",
      properties: {
        data_files: {
          type: "object",
          properties: {
            bus_stops: { type: "string" },
            bixi_stations: { type: "string" },
            evaluation_fonciere: { type: "string" },
            menage_2018: { type: "string" },
            reseau_cyclable: { type: "string" }
          }
        },
        buffer_layer: {
          type: "object",
          properties: {
            bixi_stations: {
              type: "object",
              properties: {
                geometry_type: { 
                  type: "string",
                  enum: ["Point", "Polygon", "LineString", "MultiPolygon"]
                },
                buffer_type: { 
                  type: "string",
                  enum: ["circular", "grid", "isochrone", "zones", "zones_grid"]
                },
                distance: { type: "number" }
              }
            }
          }
        },
        filter_data_files: {
          type: "object",
          properties: {
            bus_stops: {
              type: "object",
              properties: {
                column: { type: "string" },
                value: { type: "string" }
              }
            },
            bixi_stations: {
              type: "object",
              properties: {
                column: { type: "string" },
                value: { type: "number" },
                operator: { type: "string", enum: ["==", ">=", "<=", ">", "<", "!="] }
              }
            }
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
                title: "Ratio Name"
              },
              numerator: { 
                type: "string",
                title: "Numerator"
              },
              denominator: { 
                type: "string",
                title: "Denominator"
              }
            },
            required: ["name", "numerator", "denominator"]
          }
        },
        sum_columns: {
          type: "array",
          items: { type: "string" }
        },
        max_columns: {
          type: "array",
          items: { type: "string" }
        },
        min_columns: {
          type: "array",
          items: { type: "string" }
        },
        mean_columns: {
          type: "array",
          items: { type: "string" }
        },
        std_columns: {
          type: "array",
          items: { type: "string" }
        },
        count_columns: {
          type: "array",
          items: { type: "string" }
        },
        count_distinct_columns: {
          type: "array",
          items: { type: "string" }
        },
        groupby_columns: {
          type: "array",
          items: { type: "string" }
        },
        filter_global: {
          type: "array",
          items: {
            type: "object",
            properties: {
              column: { type: "string" },
              value: {
                anyOf: [
                  { type: "number" },
                  { type: "string" }
                ]
              },
              operator: { type: "string", enum: ["==", ">=", "<=", ">", "<", "!="] }
            },
            required: ["column", "value", "operator"]
          }
        },
        activate_visualisation: {
          type: "boolean"
        },
        join_layers: {
          type: "object",
          properties: {
            points: {
              type: "object",
              properties: {
                type: { type: "string" }
              }
            },
            polygons: {
              type: "object",
              properties: {
                type: { type: "string" }
              }
            },
            multipolygons: {
              type: "object",
              properties: {
                type: { type: "string" }
              }
            },
            linestrings: {
              type: "object",
              properties: {
                type: { type: "string" }
              }
            }
          }
        },
        colors: {
          type: "object",
          properties: {
            bus_stops: { type: "string" },
            bixi_stations: { type: "string" },
            evaluation_fonciere: { type: "string" },
            menage_2018: { type: "string" },
            reseau_cyclable: { type: "string" }
          }
        }
      },
      required: ["data_files", "buffer_layer", "filter_data_files", "ratio_columns", "sum_columns", "max_columns", "min_columns", "mean_columns", "std_columns", "count_columns", "count_distinct_columns", "groupby_columns", "filter_global", "activate_visualisation", "join_layers", "colors"]
    };
    
    setSchema(generatedSchema);
  }, []);

  const onSubmit = ({ formData }) => {
    console.log("Submitted data:", formData);
    
    fetch('http://127.0.0.1:5000/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      setSubmitMessage('Configuration soumise avec succès !');
      console.log('Success:', data);
    })
    .catch((error) => {
      setSubmitMessage('Erreur lors de la soumission : ' + error.message);
      console.error('Error:', error);
    });
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
      "colors"
    ],
    ratio_columns: {
      "items": {
        name: {
          "ui:placeholder": "Enter ratio name"
        },
        numerator: {
          "ui:placeholder": "Enter numerator column"
       },
        denominator: {
          "ui:placeholder": "Enter denominator column"
        }
      }
    }
  };
  return (
    <div>
      <h1>Data Fusion UI</h1>
      {Object.keys(schema).length > 0 ? (
        <Form 
          schema={schema}
          uiSchema={uiSchema}
          formData={formData}
          onChange={({ formData }) => setFormData(formData)}
          onSubmit={onSubmit}
        >
          <button type="submit">Submit</button>
        </Form>
      ) : (
        <div>Loading configuration...</div>
      )}
      {submitMessage && <p>{submitMessage}</p>}
    </div>
  );
};

export default App;