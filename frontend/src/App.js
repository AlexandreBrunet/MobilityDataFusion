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
    distance: 500
    geometry_type: "Point"
filter_data_files:
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
count_distinct_columns:
  - "station_id as count_bixi_station"
groupby_columns:
  - "buffer_id"
  - "name"
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
                distance: { type: "number" },
                geometry_type: { 
                  type: "string",
                  enum: ["Point", "Polygon", "LineString", "MultiPolygon"]
                }
              }
            }
          }
        },
        filter_data_files: {
          type: "object",
          properties: {
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
          type: "object",
          properties: {
            permis_perslogi_ratio: {
              type: "object",
              properties: {
                numerator: { type: "string" },
                denominator: { type: "string" }
              }
            }
          }
        },
        sum_columns: {
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
      }
    };
    setSchema(generatedSchema);
  }, []);

    
    // Modification de l'URL pour correspondre à l'adresse et au port de votre backend Flask
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
    "ui:order": ["data_files", "buffer_layer", "filter_data_files", "ratio_columns", "sum_columns", "count_distinct_columns", "groupby_columns", "join_layers", "colors"]
  };

  return (
    <div>
      <h1>Configuration UI</h1>
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