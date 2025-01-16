from flask import Flask, jsonify, request
import yaml

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)