"""
AI-Powered Demand Forecasting & Supply Chain Optimization System
Flask Backend Application Entry Point
"""

import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from routes.forecast_routes import forecast_blueprint

app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) for all frontend origins
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(forecast_blueprint, url_prefix="/api")

STATIC_IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images")


@app.route("/")
def index():
    return jsonify({
        "project": "AI-Powered Demand Forecasting & Supply Chain Optimization System",
        "status": "online",
        "documentation": {
            "health": "/api/health",
            "model_info": "/api/model-info",
            "historical_demand": "/api/historical-demand",
            "forecast": "/api/forecast (POST or GET ?days=14)",
            "inventory_recommend": "/api/inventory/recommend (POST)",
            "upload_dataset": "/api/upload (POST multipart/form-data)",
            "download_sample": "/api/sample-data (GET)",
        }
    })


@app.route("/api/static/images/<path:filename>")
def serve_plot(filename):
    """Serves static plots generated during model evaluation."""
    if os.path.exists(os.path.join(STATIC_IMAGES_DIR, filename)):
        return send_from_directory(STATIC_IMAGES_DIR, filename)
    return jsonify({"error": "Image not found."}), 404


if __name__ == "__main__":
    print("Starting AI-Powered Demand Forecasting & Supply Chain Optimization System API on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
