"""
AI-Powered Demand Forecasting & Supply Chain Optimization System
API Routes

Provides RESTful endpoints with full active dataset synchronization:
- GET  /api/health
- GET  /api/dataset/status (also /api/model-info for backwards compatibility)
- POST /api/dataset/reset
- GET  /api/historical-demand (?product=all|name)
- GET  /api/forecast & POST /api/forecast (?days=14&product=all|name)
- POST /api/inventory/recommend ({ lead_time_days, service_level, current_stock, target_stock, product })
- POST /api/upload (multipart/form-data)
- GET  /api/sample-data
"""

import os
from flask import Blueprint, jsonify, request, send_file
from services.forecast_service import forecast_service

forecast_blueprint = Blueprint("forecast", __name__)


@forecast_blueprint.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify API is active."""
    return jsonify({
        "status": "healthy",
        "service": "AI-Powered Demand Forecasting API",
        "active_dataset": forecast_service.active_dataset["name"] if forecast_service.active_dataset else None,
        "is_default": forecast_service.active_dataset["is_default"] if forecast_service.active_dataset else True,
    }), 200


@forecast_blueprint.route("/dataset/status", methods=["GET"])
@forecast_blueprint.route("/model-info", methods=["GET"])
def get_dataset_status():
    """Returns metadata, summary stats, product catalog, and evaluation for active dataset."""
    status = forecast_service.get_dataset_status()
    if "error" in status:
        return jsonify(status), 404
    return jsonify(status), 200


@forecast_blueprint.route("/dataset/reset", methods=["POST"])
def reset_dataset():
    """Resets active dataset back to the default UCI Online Retail dataset."""
    status = forecast_service.reset_to_default()
    if "error" in status:
        return jsonify(status), 400
    return jsonify({
        "message": "Reset to default UCI Online Retail dataset successfully.",
        "dataset": status,
    }), 200


@forecast_blueprint.route("/historical-demand", methods=["GET"])
def get_historical_demand():
    """
    Returns daily historical demand data and test evaluation comparison.
    Supports ?product=all or ?product=<ProductName>
    """
    product = request.args.get("product", default="all", type=str)
    data = forecast_service.get_historical_data(product=product)
    if "error" in data:
        return jsonify(data), 404
    return jsonify(data), 200


@forecast_blueprint.route("/forecast", methods=["POST", "GET"])
@forecast_blueprint.route("/predict", methods=["POST", "GET"])
def predict_demand():
    """
    Generates future demand predictions for N days (default: 14 days)
    for the currently active dataset and selected product.
    Supports query parameters or JSON body: { "days": 14, "start_date": "YYYY-MM-DD", "product": "all" }
    """
    days = 14
    start_date = None
    product = "all"

    if request.method == "POST" and request.is_json:
        body = request.get_json() or {}
        days = body.get("days", 14)
        start_date = body.get("start_date", None)
        product = body.get("product", "all")
    else:
        days = request.args.get("days", default=14, type=int)
        start_date = request.args.get("start_date", default=None, type=str)
        product = request.args.get("product", default="all", type=str)

    result = forecast_service.predict_future(days=days, start_date=start_date, product=product)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 200


@forecast_blueprint.route("/inventory/recommend", methods=["POST"])
def inventory_recommendations():
    """
    Calculates inventory recommendations using the active dataset's
    (or selected product's) genuine average daily demand and standard deviation.
    Accepts JSON body:
    {
        "lead_time_days": 7,
        "service_level": 0.95,
        "current_stock": 80000,
        "target_stock": 250000,
        "product": "all"
    }
    """
    data = request.get_json() or {}

    lead_time = float(data.get("lead_time_days", 7.0))
    service_level = float(data.get("service_level", 0.95))
    product = data.get("product", "all")

    current_stock = data.get("current_stock")
    if current_stock is not None and current_stock != "":
        try:
            current_stock = float(current_stock)
        except (ValueError, TypeError):
            current_stock = None
    else:
        current_stock = None

    target_stock = data.get("target_stock")
    if target_stock is not None and target_stock != "":
        try:
            target_stock = float(target_stock)
        except (ValueError, TypeError):
            target_stock = None
    else:
        target_stock = None

    recommendations = forecast_service.calculate_inventory_recommendations(
        lead_time_days=lead_time,
        service_level=service_level,
        current_stock=current_stock,
        target_stock=target_stock,
        product=product,
    )

    if "error" in recommendations:
        return jsonify(recommendations), 400

    return jsonify(recommendations), 200


@forecast_blueprint.route("/upload", methods=["POST"])
def upload_dataset():
    """
    Accepts CSV or Excel file upload, validates schema,
    aggregates daily demand, trains an aligned model with chronological split,
    and sets the uploaded dataset as the current active dataset.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file attached. Please select a .csv or .xlsx file."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    filename = file.filename
    if not (filename.lower().endswith(".csv") or filename.lower().endswith((".xlsx", ".xls"))):
        return jsonify({"error": f"Invalid file format '{filename}'. Only .csv and .xlsx files are supported."}), 400

    result = forecast_service.process_uploaded_dataset(file.stream, filename)
    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 200


@forecast_blueprint.route("/sample-data", methods=["GET"])
def get_sample_data():
    """Provides a sample multi-product retail sales CSV for testing."""
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "processed", "sample_sales_with_products.csv"
    )
    if not os.path.exists(sample_path):
        # Fallback to existing sample
        sample_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "processed", "sample_daily_demand.csv"
        )

    if os.path.exists(sample_path):
        return send_file(sample_path, as_attachment=True, download_name="sample_retail_sales.csv")
    return jsonify({"error": "Sample data file not found."}), 404
