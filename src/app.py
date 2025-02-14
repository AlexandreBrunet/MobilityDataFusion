import logging
from flask import Flask, jsonify, request, send_from_directory
import yaml
from flask_cors import CORS
import subprocess
import os
import json
from geopandas import GeoDataFrame

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
logging.basicConfig(level=logging.DEBUG)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        with open('config.yaml', 'w') as file:
            yaml.dump(data, file)
        
        process = subprocess.Popen(['python3', 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Erreur lors de l'exécution de main.py: {stderr.decode()}")
        
        return jsonify({"message": "Configuration saved and main.py executed", "output": stdout.decode()}), 200
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/list_files', methods=['GET'])
def list_files():
    try:
        input_dir = './data/input/geojson/'
        files = [f for f in os.listdir(input_dir) if f.endswith('.geojson')]
        file_paths = {f.replace('.geojson', ''): os.path.join(input_dir, f) for f in files}
        return jsonify(file_paths), 200
    except Exception as e:
        logging.error(f"An error occurred while listing files: {str(e)}")
        return jsonify({"error": "Failed to list files"}), 500

@app.route('/get_table_html/<path:params>')
def get_table_html(params):
    try:
        directory = './data/output/visualisation/'
        filename = f'tableau_{params}.html'
        return send_from_directory(directory, filename, mimetype='text/html')
    except Exception as e:
        logging.error(f"An error occurred while serving table HTML file: {str(e)}")
        return jsonify({"error": "Failed to serve table HTML file"}), 500

@app.route('/get_map_html/<path:params>')
def get_map_html(params):
    try:
        directory = './data/output/visualisation/'
        filename = f'carte_{params}.html'
        return send_from_directory(directory, filename, mimetype='text/html')
    except Exception as e:
        logging.error(f"An error occurred while serving map HTML file: {str(e)}")
        return jsonify({"error": "Failed to serve map HTML file"}), 500

@app.route('/get_histogram_html/<aggregation_type>/<aggregation_column>/<groupby_column>')
def get_histogram_html(aggregation_type, aggregation_column, groupby_column):
    try:
        directory = './data/output/visualisation/'

        aggregation_type = aggregation_type.replace(" ", "_").lower()
        aggregation_column = aggregation_column.replace(" ", "_").lower()
        groupby_column = groupby_column.replace(" ", "_").lower()  # Ensure lowercase

        filename_base = f"hist_{aggregation_type}_{aggregation_column}"
        if groupby_column != "none":
            filename = f"{filename_base}_grouped_by_{groupby_column}.html"
        else:
            filename = f"{filename_base}.html"
        
        full_path = os.path.abspath(os.path.join(directory, filename))
        logging.info(f"Searching for histogram at: {full_path}")

        return send_from_directory(directory, filename, mimetype='text/html')
    except FileNotFoundError:
        logging.error(f"Missing file: {filename} in {directory}")
        return jsonify({"error": "Histogram not found"}), 404
    except Exception as e:
        logging.error(f"Error serving histogram: {str(e)}")
        return jsonify({"error": "Server error"}), 500

@app.route('/get_file_preview/<filename>')
def get_file_preview(filename):
    try:
        filepath = os.path.join('./data/input/geojson/', filename + '.geojson')
        gdf = GeoDataFrame.from_file(filepath)
        
        # Convert to GeoJSON and parse
        geojson = json.loads(gdf.head(100).to_json())
        
        # Extract columns from properties
        columns = list(gdf.columns)
        
        # Extract data with proper geometry serialization
        data = []
        for feature in geojson['features']:
            row = feature['properties'].copy()
            row['geometry'] = feature['geometry']
            data.append(row)
        
        return jsonify({
            'columns': columns,
            'data': data
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting file preview: {str(e)}")
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, port=5000)