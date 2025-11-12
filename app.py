from flask import Flask, request, jsonify
from flask_cors import CORS
import string
import random
import os
import json
from threading import Lock

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
JSON_PATH = os.path.join(DATA_DIR, "links.json")

lock = Lock()

def load_links():
    if not os.path.exists(JSON_PATH):
        return {}
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_links(data):
    with lock:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

links = load_links()

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if code not in links:
            return code

@app.route("/add", methods=["POST"])
def add_link():
    data = request.get_json()
    original_url = data.get("url")
    custom_code = data.get("code")

    if not original_url:
        return jsonify({"error": "URL is required"}), 400

    if custom_code:
        if custom_code in links:
            return jsonify({"error": "Short code already exists"}), 400
        short_code = custom_code
    else:
        short_code = generate_short_code()

    links[short_code] = original_url
    save_links(links)

    return jsonify({
        "success": True,
        "short_code": short_code,
        "original_url": original_url
    }), 201

@app.route("/delete", methods=["POST"])
def delete_link():
    data = request.get_json()
    short_code = data.get("code")

    if not short_code:
        return jsonify({"error": "Short code is required"}), 400

    if short_code not in links:
        return jsonify({"error": "Short code not found"}), 404

    del links[short_code]
    save_links(links)

    return jsonify({"success": True, "message": "Link deleted successfully"}), 200

@app.route("/links", methods=["GET"])
def get_links():
    return jsonify(links), 200

@app.route("/map", methods=["GET"])
def get_mapping():
    short_code = request.args.get("code")

    if not short_code:
        return jsonify({"error": "Short code is required"}), 400

    original_url = links.get(short_code)
    if not original_url:
        return jsonify({"error": "Short code not found"}), 404

    return jsonify({"url": original_url}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
