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
        print("Configuration reçue du frontend :", data)
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

@app.route('/get_geojson_data/<filename>', methods=['GET'])
def get_geojson_data(filename):
    try:
        # Chercher le fichier GeoJSON
        input_dir = './data/input/geojson/'
        file_path = os.path.join(input_dir, f'{filename}.geojson')
        
        if not os.path.exists(file_path):
            return jsonify({'error': f'Fichier {filename} non trouvé'}), 404
        
        # Charger le GeoJSON
        gdf = gpd.read_file(file_path)
        
        # Convertir en GeoJSON
        geojson_data = gdf.to_json()
        
        return geojson_data
    except Exception as e:
        logging.error(f"An error occurred while loading GeoJSON data: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        # Get the histogram configuration from the request
        histogram_config = request.json
        if not histogram_config or 'columns' not in histogram_config:
            return jsonify({"error": "Missing or invalid histogram_config. 'columns' is required."}), 400

        # Define the path to the GeoDataFrame
        fusion_gdf_path = './data/output/fusion_gdf.parquet'
        if not os.path.exists(fusion_gdf_path):
            return jsonify({"error": "Fusion GeoDataFrame not found. Run main.py first."}), 400

        # Load the GeoDataFrame
        fusion_gdf = gpd.read_parquet(fusion_gdf_path)

        # Log basic info for debugging
        logging.info(f"Loaded fusion_gdf with columns: {list(fusion_gdf.columns)}")
        logging.info(f"Sample data:\n{fusion_gdf.head().to_string()}")

        # Validate requested columns exist in the GeoDataFrame
        requested_columns = histogram_config.get('columns', [])
        missing_columns = [col for col in requested_columns if col not in fusion_gdf.columns]
        if missing_columns:
            return jsonify({"error": f"Columns not found in GeoDataFrame: {missing_columns}"}), 400

        # Convert columns to numeric where possible, coercing errors to NaN
        for col in requested_columns:
            if col in fusion_gdf.columns:
                fusion_gdf[col] = pd.to_numeric(fusion_gdf[col], errors='coerce')
                logging.info(f"Column '{col}' after conversion: {fusion_gdf[col].dtype}")
                logging.info(f"Sample values for '{col}': {fusion_gdf[col].head(10).tolist()}")
                logging.info(f"NaN count in '{col}': {fusion_gdf[col].isna().sum()}")

        # Calculate histogram data (assumed to be a function in metrics module)
        histogram_data = metrics.calculate_histogram_data(fusion_gdf, histogram_config)

        # Generate histograms for each column
        generated_histograms = {}
        for col in requested_columns:
            try:
                histogram_filename = visualisation.visualize_histogram(
                    histogram_data,
                    col,
                    buffer_type="histogram"
                )
                if histogram_filename:
                    generated_histograms[col] = histogram_filename
                else:
                    logging.warning(f"No histogram file generated for column '{col}'")
            except Exception as e:
                logging.error(f"Failed to generate histogram for '{col}': {str(e)}")
                return jsonify({"error": f"Failed to generate histogram for '{col}': {str(e)}"}), 500

        return jsonify({"histograms": generated_histograms}), 200

    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        return jsonify({"error": f"Validation error: {str(ve)}"}), 400
    except Exception as e:
        logging.error(f"Error generating histogram: {str(e)}")
        return jsonify({"error": f"Error generating histogram: {str(e)}"}), 500
    
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
    
@app.route('/generate_barchart', methods=['POST'])
def generate_barchart():
    try:
        # Get the bar chart configuration from the request
        barchart_config = request.json
        if not barchart_config or 'columns' not in barchart_config:
            return jsonify({"error": "Missing or invalid barchart_config. 'columns' is required."}), 400
        
        # Define the path to the GeoDataFrame
        fusion_gdf_path = './data/output/fusion_gdf.parquet'
        if not os.path.exists(fusion_gdf_path):
            return jsonify({"error": "Fusion GeoDataFrame not found. Run main.py first."}), 400

        # Load the GeoDataFrame
        fusion_gdf = gpd.read_parquet(fusion_gdf_path)

        # Log basic info for debugging
        logging.info(f"Loaded fusion_gdf with columns: {list(fusion_gdf.columns)}")
        logging.info(f"Sample data:\n{fusion_gdf.head().to_string()}")

        # Validate requested columns exist in the GeoDataFrame
        requested_columns = barchart_config.get('columns', [])
        missing_columns = [col for col in requested_columns if col not in fusion_gdf.columns]
        if missing_columns:
            return jsonify({"error": f"Columns not found in GeoDataFrame: {missing_columns}"}), 400

        # Convert columns to numeric where possible, coercing errors to NaN
        for col in requested_columns:
            if col in fusion_gdf.columns:
                fusion_gdf[col] = pd.to_numeric(fusion_gdf[col], errors='coerce')
                logging.info(f"Column '{col}' after conversion: {fusion_gdf[col].dtype}")
                logging.info(f"Sample values for '{col}': {fusion_gdf[col].head(10).tolist()}")
                logging.info(f"NaN count in '{col}': {fusion_gdf[col].isna().sum()}")

        # Calculate bar chart data
        barchart_data = metrics.calculate_barchart_data(fusion_gdf, barchart_config)

        # Generate bar charts for each column
        generated_barcharts = {}
        for col in requested_columns:
            try:
                barchart_filename = visualisation.visualize_barchart(
                    barchart_data,
                    col,
                    buffer_type="barchart"
                )
                if barchart_filename:
                    generated_barcharts[col] = barchart_filename
                else:
                    logging.warning(f"No bar chart file generated for column '{col}'")
            except Exception as e:
                logging.error(f"Failed to generate bar chart for '{col}': {str(e)}")
                return jsonify({"error": f"Failed to generate bar chart for '{col}': {str(e)}"}), 500

        return jsonify({"barcharts": generated_barcharts}), 200

    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        return jsonify({"error": f"Validation error: {str(ve)}"}), 400
    except Exception as e:
        logging.error(f"Error generating bar chart: {str(e)}")
        return jsonify({"error": f"Error generating bar chart: {str(e)}"}), 500

@app.route('/get_barchart_html/<path:filename>')
def get_barchart_html(filename):
    try:
        directory = './data/output/visualisation/'
        return send_from_directory(directory, filename, mimetype='text/html')
    except Exception as e:
        logging.error(f"Error serving bar chart: {str(e)}")
        return jsonify({"error": "Bar chart not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)