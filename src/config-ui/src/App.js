import React, { useState, useEffect } from 'react';
import Form from 'react-jsonschema-form';
import * as yaml from 'js-yaml';

const App = () => {
  const [formData, setFormData] = useState({});
  const [schema, setSchema] = useState({});

  useEffect(() => {
    // Charger le fichier YAML depuis le dossier 'public'
    fetch('/config.yaml')
      .then(response => response.text())
      .then(yamlText => {
        const jsonConfig = yaml.load(yamlText);
        const schemaFromJson = createSchemaFromJSON(jsonConfig);
        setSchema(schemaFromJson);
        setFormData(jsonConfig);
      })
      .catch(error => console.error('Error loading config:', error));
  }, []);

  const createSchemaFromJSON = (config) => {
    let properties = {};
    const required = [];

    function traverse(obj, currentPath = '') {
      for (const key in obj) {
        const path = currentPath ? `${currentPath}.${key}` : key;
        if (typeof obj[key] === 'object' && obj[key] !== null) {
          traverse(obj[key], path);
        } else {
          let type = typeof obj[key];

          if (type === 'number' && Number.isInteger(obj[key])) {
            type = 'integer';
          } else if (type === 'number') {
            type = 'number';
          } else if (type === 'boolean') {
            type = 'boolean';
          } else {
            type = 'string';
          }

          properties[path] = { type };
          required.push(path);
        }
      }
    }

    traverse(config);
    return {
      type: "object",
      properties: properties,
      required: required,
      title: "Configuration"
    };
  };

  const onSubmit = ({ formData }) => {
    console.log("Data submitted: ", formData);
  };

  const uiSchema = {};

  return (
    <div>
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
    </div>
  );
};

export default App;