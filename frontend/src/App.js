import React, { useState, useEffect } from 'react';
import Form from 'react-jsonschema-form';
import * as yaml from 'js-yaml';

// Exemple simplifié du contenu de votre config.yaml converti en JSON
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
  ratio_test:
    numerator:
    denominator:

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

  useEffect(() => {
    // Génération du schéma JSON basé sur la structure du config
    const generatedSchema = {
      type: "object",
      properties: {
        data_files: {
          type: "object",
          properties: {
            bus_stops: { type: "string" }
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
        }
      }
    };
    setSchema(generatedSchema);
  }, []);

  const onSubmit = ({ formData }) => {
    console.log("Submitted data:", formData);
    // Ici, vous pourriez envoyer formData à un backend pour sauver en YAML
  };

  const uiSchema = {
    "ui:order": ["data_files", "buffer_layer", "filter_data_files"]
  };

  return (
    <div>
      <h1>Configuration UI</h1>
      <Form 
        schema={schema}
        uiSchema={uiSchema}
        formData={formData}
        onChange={({ formData }) => setFormData(formData)}
        onSubmit={onSubmit}
      >
        <button type="submit">Submit</button>
      </Form>
    </div>
  );
};

export default App;