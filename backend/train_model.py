"""
IntelliSupply: Demand Forecasting Model Training Pipeline
Processes the raw Online Retail dataset or aggregated daily demand,
trains a Random Forest Regressor, evaluates MAE/RMSE, and serializes
the model and metadata for the Flask backend.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw", "online+retail", "Online Retail.xlsx")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "backend", "models")
STATIC_PLOTS = os.path.join(BASE_DIR, "backend", "static", "images")

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(STATIC_PLOTS, exist_ok=True)

DAILY_DEMAND_CSV = os.path.join(PROCESSED_DIR, "daily_demand.csv")


def prepare_daily_demand():
    """Extracts and aggregates daily demand from raw Excel or cached daily CSV."""
    if os.path.exists(DAILY_DEMAND_CSV):
        print(f"Loading cached daily demand from {DAILY_DEMAND_CSV}...")
        df = pd.read_csv(DAILY_DEMAND_CSV)
        df["Date"] = pd.to_datetime(df["Date"])
        return df

    if not os.path.exists(DATA_RAW):
        raise FileNotFoundError(f"Raw data file not found at: {DATA_RAW}")

    print(f"Reading raw Excel transactions from {DATA_RAW} (this may take ~1 minute)...")
    raw_df = pd.read_excel(DATA_RAW)

    print("Cleaning transactions...")
    # Remove cancelled transactions (InvoiceNo starting with 'C')
    raw_df = raw_df[~raw_df["InvoiceNo"].astype(str).str.startswith("C")]
    # Keep only positive quantities
    raw_df = raw_df[raw_df["Quantity"] > 0]
    raw_df["InvoiceDate"] = pd.to_datetime(raw_df["InvoiceDate"])

    # Save a lightweight sample for frontend upload testing
    sample_path = os.path.join(PROCESSED_DIR, "sample_transactions.csv")
    raw_df.head(1000).to_csv(sample_path, index=False)
    print(f"Saved sample transaction CSV to {sample_path}")

    # Aggregate by date
    daily = (
        raw_df.groupby(raw_df["InvoiceDate"].dt.date)["Quantity"]
        .sum()
        .reset_index()
    )
    daily.columns = ["Date", "Demand"]
    daily["Date"] = pd.to_datetime(daily["Date"])
    daily = daily.sort_values("Date").reset_index(drop=True)

    daily.to_csv(DAILY_DEMAND_CSV, index=False)
    print(f"Saved daily demand ({len(daily)} rows) to {DAILY_DEMAND_CSV}")
    return daily


def train_and_evaluate():
    daily_demand = prepare_daily_demand()

    # Time-based calendar features
    daily_demand["Day"] = daily_demand["Date"].dt.day
    daily_demand["Month"] = daily_demand["Date"].dt.month
    daily_demand["DayOfWeek"] = daily_demand["Date"].dt.dayofweek
    daily_demand["Year"] = daily_demand["Date"].dt.year

    features = ["Day", "Month", "DayOfWeek", "Year"]

    # 80/20 chronological train-test split
    split_index = int(len(daily_demand) * 0.8)
    train = daily_demand.iloc[:split_index]
    test = daily_demand.iloc[split_index:].copy()

    X_train = train[features]
    y_train = train["Demand"]
    X_test = test[features]
    y_test = test["Demand"]

    print(f"Training on {len(X_train)} days, evaluating on {len(X_test)} days...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    test["Predicted"] = predictions

    mae = float(mean_absolute_error(y_test, predictions))
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    r2 = float(r2_score(y_test, predictions))

    print("\n--- Model Evaluation ---")
    print(f"MAE  : {mae:.2f}")
    print(f"RMSE : {rmse:.2f}")
    print(f"R^2  : {r2:.4f}")

    # Inventory baseline planning calculations
    avg_demand = float(predictions.mean())
    demand_std = float(np.std(y_test.values - predictions))
    lead_time_days = 7
    service_factor = 1.65  # 95% service level
    safety_stock = float(service_factor * demand_std)
    reorder_point = float((avg_demand * lead_time_days) + safety_stock)

    # Save model
    model_file = os.path.join(MODELS_DIR, "model.joblib")
    joblib.dump(model, model_file)
    print(f"\nTrained model serialized to: {model_file}")

    # Save metadata
    metadata = {
        "features": features,
        "total_records": len(daily_demand),
        "train_records": len(train),
        "test_records": len(test),
        "train_start": str(train["Date"].min().date()),
        "train_end": str(train["Date"].max().date()),
        "test_start": str(test["Date"].min().date()),
        "test_end": str(test["Date"].max().date()),
        "metrics": {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2": round(r2, 4),
        },
        "inventory_baseline": {
            "average_daily_demand": round(avg_demand, 2),
            "demand_std": round(demand_std, 2),
            "lead_time_days": lead_time_days,
            "service_level": "95%",
            "safety_stock": round(safety_stock, 2),
            "reorder_point": round(reorder_point, 2),
        },
    }

    meta_file = os.path.join(MODELS_DIR, "model_metadata.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {meta_file}")

    return metadata


if __name__ == "__main__":
    train_and_evaluate()
