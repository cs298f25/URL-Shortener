"""
API/Endpoint Layer - HTTP request/response handling.
Thin layer that delegates to service layer for business logic.
"""
from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from flask_cors import CORS
from functools import wraps
import os

from services import AuthService, LinkService

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Initialize service instances (can be replaced for testing)
auth_service = AuthService()
link_service = LinkService()


# ==================== Authentication Decorator ====================

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


# ==================== Page Routes ====================

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


# ==================== Authentication API Routes ====================

@app.route("/api/signup", methods=["POST", "OPTIONS"])
def signup():
    """Handle user registration."""
    if request.method == "OPTIONS":
        return "", 200
    
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # Validation
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # Check if email already exists
    if auth_service.email_exists(email):
        return jsonify({"error": "Email already registered"}), 400

    # Create user via service
    try:
        user = auth_service.create_user(email, password)
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
    except Exception as e:
        return jsonify({"error": "Failed to create account"}), 500


@app.route("/api/login", methods=["POST", "OPTIONS"])
def login_api():
    """Handle user login."""
    if request.method == "OPTIONS":
        return "", 200
    
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # Validation
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Verify credentials via service
    user = auth_service.verify_user(email, password)
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
    try:
        user = auth_service.get_user_by_id(session['user_id'])
        if not user:
            session.clear()
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user_id": user.get("user_id"),
            "email": user.get("email"),
            "created_at": user.get("created_at")
        }), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve user"}), 500


# ==================== Link API Routes ====================

@app.route("/api/add", methods=["POST", "OPTIONS"])
@login_required
def add_link():
    """Add a new shortened link."""
    if request.method == "OPTIONS":
        return "", 200
    
    user_id = session['user_id']
    data = request.get_json() or {}
    original_url = data.get("url", "").strip()
    custom_code = data.get("code", "").strip() or None
    expires_in = data.get("expires_in", "never")

    try:
        # Create link via service
        link = link_service.create_link(
            user_id=user_id,
            url=original_url,
            custom_code=custom_code,
            expires_in=expires_in
        )

        return jsonify({
            "success": True,
            "short_code": link["short_code"],
            "original_url": link["url"],
            "expires_at": link["expires_at"]
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to create link"}), 500


@app.route("/api/delete", methods=["POST", "OPTIONS"])
@login_required
def delete_link():
    """Delete a shortened link."""
    if request.method == "OPTIONS":
        return "", 200
    
    user_id = session['user_id']
    data = request.get_json() or {}
    short_code = data.get("code", "").strip()

    # Validation
    if not short_code:
        return jsonify({"error": "Short code is required"}), 400

    # Check if link exists and get owner
    link_owner = link_service.get_link_owner(short_code)
    if not link_owner:
        return jsonify({"error": "Short code not found"}), 404

    # Check if user owns the link
    if link_owner != user_id:
        return jsonify({"error": "Forbidden: You don't own this link"}), 403

    # Delete via service
    try:
        deleted = link_service.delete_link(user_id, short_code)
        if not deleted:
            return jsonify({"error": "Failed to delete link"}), 500

        return jsonify({"success": True, "message": "Link deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to delete link"}), 500


@app.route("/api/links", methods=["GET"])
@login_required
def get_links():
    """Get all links for the current user."""
    user_id = session['user_id']
    
    try:
        links = link_service.get_user_links(user_id)
        
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
    except Exception as e:
        return jsonify({"error": "Failed to retrieve links"}), 500


# ==================== Public Redirect Route ====================

@app.route("/<path:short_code>", methods=["GET"])
def redirect_short_code(short_code):
    """Redirect to original URL (public route, no auth required)."""
    if '.' in short_code:
        return jsonify({"error": "Not found"}), 404

    try:
        link_data = link_service.get_link(short_code)
        
        if not link_data:
            # Check if it exists but is expired
            link_owner = link_service.get_link_owner(short_code)
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
    except Exception as e:
        return jsonify({"error": "An error occurred"}), 500
