from flask import Flask, request, jsonify, redirect, render_template, make_response, session, url_for
import utils
from flask_cors import CORS
from typing import Optional
from functools import wraps
import os
import time

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')  # Should be set via env var in production
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


def login_required(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def parse_expires_in(expires_in: Optional[str]) -> Optional[int]:
    """
    Parse expires_in parameter and return Unix timestamp.
    Returns None if 'never' or invalid.
    Options: '1h', '24h', '7d', '30d', 'never'
    """
    if not expires_in or expires_in.lower() == 'never':
        return None
    
    current_time = int(time.time())
    
    try:
        if expires_in.endswith('h'):
            hours = int(expires_in[:-1])
            return current_time + (hours * 60 * 60)
        elif expires_in.endswith('d'):
            days = int(expires_in[:-1])
            return current_time + (days * 24 * 60 * 60)
        else:
            # Try to parse as integer (seconds)
            seconds = int(expires_in)
            return current_time + seconds
    except (ValueError, AttributeError):
        return None


@app.route("/")
def index():
    """Redirect to login if not authenticated, otherwise show main page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("index.html")


@app.route("/signup", methods=["GET"])
def signup_page():
    """Show sign up page."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template("signup.html")


@app.route("/login", methods=["GET"])
def login():
    """Show login page."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template("login.html")


@app.route("/api/signup", methods=["POST", "OPTIONS"])
def signup():
    """Handle user registration."""
    if request.method == "OPTIONS":
        return "", 200
    
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # Check if email already exists
    if utils.email_exists(email):
        return jsonify({"error": "Email already registered"}), 400

    # Create user
    user = utils.create_user(email, password)
    if not user:
        return jsonify({"error": "Failed to create account"}), 500

    # Set session
    session['user_id'] = user['user_id']
    session['email'] = user['email']
    session.permanent = True

    return jsonify({
        "success": True,
        "message": "Account created successfully",
        "user": {
            "user_id": user['user_id'],
            "email": user['email']
        }
    }), 201


@app.route("/api/login", methods=["POST", "OPTIONS"])
def login_api():
    """Handle user login."""
    if request.method == "OPTIONS":
        return "", 200
    
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Verify credentials
    user = utils.verify_user(email, password)
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    # Set session
    session['user_id'] = user['user_id']
    session['email'] = user['email']
    session.permanent = True

    return jsonify({
        "success": True,
        "message": "Logged in successfully",
        "user": {
            "user_id": user['user_id'],
            "email": user['email']
        }
    }), 200


@app.route("/api/logout", methods=["POST", "OPTIONS"])
@login_required
def logout():
    """Handle user logout."""
    if request.method == "OPTIONS":
        return "", 200
    
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"}), 200


@app.route("/api/user", methods=["GET"])
@login_required
def get_user():
    """Get current user info."""
    user = utils.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "created_at": user.get("created_at")
    }), 200


@app.route("/api/add", methods=["POST", "OPTIONS"])
@login_required
def add_link():
    """Add a new shortened link."""
    if request.method == "OPTIONS":
        return "", 200
    
    user_id = session['user_id']
    data = request.get_json()
    original_url = data.get("url")
    custom_code = data.get("code")
    expires_in = data.get("expires_in", "never")

    if not original_url:
        return jsonify({"error": "URL is required"}), 400

    # Parse expiration
    expires_at = parse_expires_in(expires_in)

    # Check if custom code already exists
    if custom_code:
        if utils.link_exists(custom_code):
            return jsonify({"error": "Short code already exists"}), 400
        short_code = custom_code
    else:
        short_code = utils.generate_short_code()

    utils.save_link(user_id, short_code, original_url, expires_at)

    return jsonify({
        "success": True,
        "short_code": short_code,
        "original_url": original_url,
        "expires_at": expires_at
    }), 201


@app.route("/api/delete", methods=["POST", "OPTIONS"])
@login_required
def delete_link():
    """Delete a shortened link."""
    if request.method == "OPTIONS":
        return "", 200
    
    user_id = session['user_id']
    data = request.get_json()
    short_code = data.get("code")

    if not short_code:
        return jsonify({"error": "Short code is required"}), 400

    # Check if link exists
    link_owner = utils.get_link_owner(short_code)
    if not link_owner:
        return jsonify({"error": "Short code not found"}), 404

    # Check if user owns the link
    if link_owner != user_id:
        return jsonify({"error": "Forbidden: You don't own this link"}), 403

    utils.remove_link(user_id, short_code)

    return jsonify({"success": True, "message": "Link deleted successfully"}), 200


@app.route("/api/links", methods=["GET"])
@login_required
def get_links():
    """Get all links for the current user."""
    user_id = session['user_id']
    links = utils.get_user_links(user_id)
    
    # Format links for frontend
    formatted_links = []
    for link in links:
        formatted_links.append({
            "short_code": link.get("short_code"),
            "url": link.get("url"),
            "created_at": link.get("created_at"),
            "expires_at": link.get("expires_at"),
            "is_expired": link.get("is_expired", False)
        })
    
    return jsonify(formatted_links), 200


@app.route("/<path:short_code>", methods=["GET"])
def redirect_short_code(short_code):
    """Redirect to original URL (public route, no auth required)."""
    if '.' in short_code:
        return jsonify({"error": "Not found"}), 404

    link_data = utils.get_link(short_code)
    
    if not link_data:
        # Check if it exists but is expired
        link_owner = utils.get_link_owner(short_code)
        if link_owner:
            # Link exists but is expired
            return jsonify({
                "error": "This link has expired",
                "message": "The shortened link you're trying to access is no longer available."
            }), 410
        else:
            # Link doesn't exist
            return jsonify({"error": "Short code not found"}), 404
    
    original_url = link_data.get("url")
    if original_url:
        return redirect(original_url, code=302)
    else:
        return jsonify({"error": "Short code not found"}), 404
