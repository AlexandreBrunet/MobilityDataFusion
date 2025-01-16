from flask import Flask, jsonify, request
import yaml
from flask_cors import CORS

app = Flask(__name__)
# Configure CORS to allow requests from localhost:3000
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

@app.route('/config', methods=['GET'])
def get_config():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return jsonify(config)

@app.route('/config', methods=['POST'])
def update_config():
    config = request.json
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file)
    return jsonify({"status": "success"}), 200

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        with open('config.yaml', 'w') as file:
            yaml.dump(data, file)
        return jsonify({"message": "Configuration saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Assurez-vous que Flask écoute sur le port 5000