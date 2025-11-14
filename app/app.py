from flask import Flask, request, jsonify, redirect, render_template
import utils
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

links = utils.load_links()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods=["POST", "OPTIONS"])
def add_link():
    if request.method == "OPTIONS":
        return "", 200
        
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
        short_code = utils.generate_short_code()

    links[short_code] = original_url
    utils.save_links(links)

    return jsonify({
        "success": True,
        "short_code": short_code,
        "original_url": original_url
    }), 201

@app.route("/delete", methods=["POST", "OPTIONS"])
def delete_link():
    if request.method == "OPTIONS":
        return "", 200
        
    data = request.get_json()
    short_code = data.get("code")

    if not short_code:
        return jsonify({"error": "Short code is required"}), 400

    if short_code not in links:
        return jsonify({"error": "Short code not found"}), 404

    del links[short_code]
    utils.save_links(links)

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

# Catch-all route MUST be last
@app.route("/<path:short_code>", methods=["GET"])
def redirect_short_code(short_code):
    if '.' in short_code:
        return jsonify({"error": "Not found"}), 404
    links = utils.load_links()
    original_url = links.get(short_code)
    
    if original_url:
        return redirect(original_url, code=302)
    else:
        return jsonify({"error": "Short code not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')