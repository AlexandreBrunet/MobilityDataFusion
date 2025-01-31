import logging
from flask import Flask, jsonify, request, send_from_directory
import yaml
from flask_cors import CORS
import subprocess
import os

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

@app.route('/get_histogram_html/<path:params>')
def get_histogram_html(params):
    try:
        directory = './data/output/visualisation/'
        # Assuming main.py generates histogram files with a naming convention similar to tables and maps
        filename = f'hist_{params}.html'
        return send_from_directory(directory, filename, mimetype='text/html')
    except Exception as e:
        logging.error(f"An error occurred while serving histogram HTML file: {str(e)}")
        return jsonify({"error": "Failed to serve histogram HTML file"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)