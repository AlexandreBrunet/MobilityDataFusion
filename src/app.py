import logging
from flask import Flask, jsonify, request, send_from_directory
import yaml
from flask_cors import CORS
import subprocess
import os
import json
from geopandas import GeoDataFrame
import geopandas as gpd
import utils.metrics.metrics as metrics
import utils.visualisation.visualisation as visualisation
import pandas as pd

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

@app.route('/generate_histogram', methods=['POST'])
def generate_histogram():
    try:
        histogram_config = request.json
        fusion_gdf_path = './data/output/fusion_gdf.geojson'
        
        if not os.path.exists(fusion_gdf_path):
            return jsonify({"error": "Fusion GeoDataFrame not found. Run main.py first."}), 400
        
        # Load the GeoDataFrame and ensure correct data types
        fusion_gdf = gpd.read_file(fusion_gdf_path)
        
        # Debugging: Inspect stop_id values and data types
        print(f"Loaded fusion_gdf data types: {fusion_gdf.dtypes}")
        print(f"Sample stop_id values: {fusion_gdf['stop_id'].head(10)}")
        print(f"Unique stop_id values: {fusion_gdf['stop_id'].unique()}")
        
        # Convert stop_id to nullable integer type if possible
        if 'stop_id' in fusion_gdf.columns:
            fusion_gdf['stop_id'] = pd.to_numeric(fusion_gdf['stop_id'], errors='coerce')
            print(f"After conversion to numeric, stop_id values: {fusion_gdf['stop_id'].head(10)}")
            fusion_gdf['stop_id'] = fusion_gdf['stop_id'].astype('Int64')
        
        histogram_data = metrics.calculate_histogram_data(fusion_gdf, histogram_config)
        
        generated_histograms = {}
        for col in histogram_config.get('columns', []):
            histogram_filename = visualisation.visualize_histogram(
                histogram_data,
                col,
                buffer_type="histogram"
                # Removed histogram_config parameter
            )
            if histogram_filename:
                generated_histograms[col] = histogram_filename
        
        return jsonify({"histograms": generated_histograms}), 200
    except Exception as e:
        logging.error(f"Error generating histogram: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/get_histogram_html/<path:filename>')
def get_histogram_html(filename):
    try:
        directory = './data/output/visualisation/'
        return send_from_directory(directory, filename, mimetype='text/html')
    except Exception as e:
        logging.error(f"Error serving histogram: {str(e)}")
        return jsonify({"error": "Histogram not found"}), 404

@app.route('/get_file_preview/<filename>')
def get_file_preview(filename):
    try:
        filepath = os.path.join('./data/input/geojson/', filename + '.geojson')
        gdf = GeoDataFrame.from_file(filepath)
        
        geojson = json.loads(gdf.head(100).to_json())
        
        columns = list(gdf.columns)
        
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