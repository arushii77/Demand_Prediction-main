"""
AI-Powered Demand Forecasting & Supply Chain Optimization System
Forecast Service & Dataset Manager

Maintains a single source of truth for the currently active dataset (default or uploaded).
Handles:
- Explicit column validation (Date, Demand/Quantity, Product, Category, Price, Revenue)
- Rejection of revenue-only files with clear actionable guidance
- Multi-product demand isolation & aggregation
- Chronological 80/20 train/test splitting without data leakage
- Model training & evaluation (MAE, RMSE, R2) on genuine held-out test data
- Future forecasting starting from the active dataset's timeline
- Dynamic inventory recommendations derived from active dataset statistics
- Reverting to the default dataset
"""

import os
import json
import math
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from services.inventory_service import calculate_inventory_metrics

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "backend", "models")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

DEFAULT_MODEL_PATH = os.path.join(MODELS_DIR, "model.joblib")
DEFAULT_METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")
DEFAULT_DAILY_CSV = os.path.join(PROCESSED_DIR, "daily_demand.csv")
DEFAULT_TRANSACTIONS_CSV = os.path.join(PROCESSED_DIR, "sample_transactions.csv")


class ForecastService:
    def __init__(self):
        self.default_model = None
        self.default_metadata = None
        self.default_daily_df = None
        self.default_transactions_df = None

        # Active dataset state
        self.active_dataset = None

        # Initialize default resources
        self._load_default_resources()
        self.reset_to_default()

    def _load_default_resources(self):
        """Loads pre-trained default model and dataset."""
        if os.path.exists(DEFAULT_MODEL_PATH):
            try:
                self.default_model = joblib.load(DEFAULT_MODEL_PATH)
            except Exception as e:
                print(f"Error loading default model: {e}")

        if os.path.exists(DEFAULT_METADATA_PATH):
            try:
                with open(DEFAULT_METADATA_PATH, "r", encoding="utf-8") as f:
                    self.default_metadata = json.load(f)
            except Exception as e:
                print(f"Error loading default metadata: {e}")

        if os.path.exists(DEFAULT_DAILY_CSV):
            try:
                df = pd.read_csv(DEFAULT_DAILY_CSV)
                df["Date"] = pd.to_datetime(df["Date"])
                self.default_daily_df = df.sort_values("Date").reset_index(drop=True)
            except Exception as e:
                print(f"Error loading default daily demand: {e}")

        if os.path.exists(DEFAULT_TRANSACTIONS_CSV):
            try:
                self.default_transactions_df = pd.read_csv(DEFAULT_TRANSACTIONS_CSV)
            except Exception as e:
                print(f"Error loading default sample transactions: {e}")

    def reset_to_default(self):
        """Resets the active dataset back to the default UCI Online Retail dataset."""
        if self.default_daily_df is None:
            return {"error": "Default daily demand dataset is not available."}

        # Build daily series
        daily_df = self.default_daily_df.copy()
        daily_df["Day"] = daily_df["Date"].dt.day
        daily_df["Month"] = daily_df["Date"].dt.month
        daily_df["DayOfWeek"] = daily_df["Date"].dt.dayofweek
        daily_df["Year"] = daily_df["Date"].dt.year

        features = ["Day", "Month", "DayOfWeek", "Year"]

        # Chronological test split
        split_idx = int(len(daily_df) * 0.8)
        train_df = daily_df.iloc[:split_idx]
        test_df = daily_df.iloc[split_idx:].copy()

        comparison = []
        if self.default_model:
            preds = self.default_model.predict(test_df[features])
            for i, (_, row) in enumerate(test_df.iterrows()):
                comparison.append({
                    "date": row["Date"].strftime("%Y-%m-%d"),
                    "actual": int(row["Demand"]),
                    "predicted": round(float(preds[i]), 1),
                })

        avg_daily = float(daily_df["Demand"].mean())
        demand_std = float(daily_df["Demand"].std())

        metrics = self.default_metadata.get("metrics", {}) if self.default_metadata else {
            "mae": 10109.01,
            "rmse": 14648.08,
            "r2": -0.3756,
        }

        # Extract products from default sample transactions if available
        products = []
        if self.default_transactions_df is not None:
            prod_col = None
            for c in ["Description", "StockCode", "product", "item"]:
                if c in self.default_transactions_df.columns:
                    prod_col = c
                    break
            if prod_col:
                top_prods = (
                    self.default_transactions_df.groupby(prod_col)["Quantity"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(50)
                )
                for name, qty in top_prods.items():
                    if pd.notna(name) and str(name).strip():
                        products.append({"id": str(name), "name": str(name), "total_units": int(qty)})

        self.active_dataset = {
            "id": "default",
            "name": "Default: UCI Online Retail Dataset",
            "is_default": True,
            "raw_df": None,
            "daily_df": daily_df,
            "model": self.default_model,
            "has_products": len(products) > 0,
            "products": products,
            "has_categories": False,
            "categories": [],
            "has_revenue": False,
            "summary": {
                "total_demand": int(daily_df["Demand"].sum()),
                "total_revenue": None,
                "average_daily_demand": round(avg_daily, 2),
                "demand_std": round(demand_std, 2),
                "total_days": len(daily_df),
                "total_transactions": 541909,
                "product_count": len(products) if products else 3877,
                "category_count": 0,
            },
            "date_range": {
                "start": daily_df["Date"].min().strftime("%Y-%m-%d"),
                "end": daily_df["Date"].max().strftime("%Y-%m-%d"),
            },
            "evaluation": {
                "mae": metrics.get("mae", 10109.01),
                "rmse": metrics.get("rmse", 14648.08),
                "r2": metrics.get("r2", -0.3756),
                "train_days": len(train_df),
                "test_days": len(test_df),
                "train_start": train_df["Date"].min().strftime("%Y-%m-%d"),
                "train_end": train_df["Date"].max().strftime("%Y-%m-%d"),
                "test_start": test_df["Date"].min().strftime("%Y-%m-%d"),
                "test_end": test_df["Date"].max().strftime("%Y-%m-%d"),
                "description": f"Chronological split: 80% train ({len(train_df)} days), 20% test ({len(test_df)} days).",
            },
            "test_comparison": comparison,
        }

        return self.get_dataset_status()

    def get_dataset_status(self):
        """Returns the high-level status of the currently active dataset."""
        if not self.active_dataset:
            return {"error": "No active dataset loaded."}

        return {
            "id": self.active_dataset["id"],
            "name": self.active_dataset["name"],
            "is_default": self.active_dataset["is_default"],
            "has_products": self.active_dataset["has_products"],
            "product_count": len(self.active_dataset["products"]),
            "products": self.active_dataset["products"][:60],  # Return top 60 products for selector
            "has_categories": self.active_dataset["has_categories"],
            "categories": self.active_dataset["categories"][:30],
            "has_revenue": self.active_dataset["has_revenue"],
            "summary": self.active_dataset["summary"],
            "date_range": self.active_dataset["date_range"],
            "evaluation": self.active_dataset["evaluation"],
        }

    def _get_series_for_selection(self, product="all"):
        """
        Retrieves daily aggregated series for 'all' products or a specific product.
        Returns: (daily_df, model, actual_vs_predicted, summary_dict)
        """
        if not self.active_dataset:
            return None, None, None, None

        raw_df = self.active_dataset.get("raw_df")
        default_daily = self.active_dataset.get("daily_df")
        model = self.active_dataset.get("model")
        test_comp = self.active_dataset.get("test_comparison", [])

        # Case 1: All products or default dataset without raw_df
        if product == "all" or not product or raw_df is None:
            summary = {
                "total_demand": self.active_dataset["summary"]["total_demand"],
                "average_daily_demand": self.active_dataset["summary"]["average_daily_demand"],
                "demand_std": self.active_dataset["summary"]["demand_std"],
                "total_days": self.active_dataset["summary"]["total_days"],
                "selected_product": "All Products",
            }
            return default_daily, model, test_comp, summary

        # Case 2: Specific product selected from uploaded dataset with raw_df
        prod_col = self.active_dataset.get("product_col")
        date_col = self.active_dataset.get("date_col")
        demand_col = self.active_dataset.get("demand_col")
        revenue_col = self.active_dataset.get("revenue_col")

        if not prod_col or prod_col not in raw_df.columns:
            # Fallback to default
            return default_daily, model, test_comp, self.active_dataset["summary"]

        # Filter to selected product
        df_p = raw_df[raw_df[prod_col].astype(str).str.strip().str.lower() == str(product).strip().lower()].copy()

        if df_p.empty:
            return default_daily, model, test_comp, self.active_dataset["summary"]

        # Aggregate daily demand for this product
        agg_dict = {demand_col: "sum"}
        if revenue_col and revenue_col in df_p.columns:
            agg_dict[revenue_col] = "sum"

        p_daily = df_p.groupby(df_p[date_col].dt.date).agg(agg_dict).reset_index()
        p_daily.rename(columns={date_col: "Date", demand_col: "Demand"}, inplace=True)
        p_daily["Date"] = pd.to_datetime(p_daily["Date"])
        p_daily = p_daily.sort_values("Date").reset_index(drop=True)

        p_daily["Day"] = p_daily["Date"].dt.day
        p_daily["Month"] = p_daily["Date"].dt.month
        p_daily["DayOfWeek"] = p_daily["Date"].dt.dayofweek
        p_daily["Year"] = p_daily["Date"].dt.year

        features = ["Day", "Month", "DayOfWeek", "Year"]
        comparison = []
        p_model = None

        if len(p_daily) >= 10:
            split_idx = int(len(p_daily) * 0.8)
            train_p = p_daily.iloc[:split_idx]
            test_p = p_daily.iloc[split_idx:].copy()

            p_model = RandomForestRegressor(n_estimators=100, random_state=42)
            p_model.fit(train_p[features], train_p["Demand"])

            preds = p_model.predict(test_p[features])
            for i, (_, row) in enumerate(test_p.iterrows()):
                comparison.append({
                    "date": row["Date"].strftime("%Y-%m-%d"),
                    "actual": int(row["Demand"]),
                    "predicted": round(float(preds[i]), 1),
                })
        elif model is not None:
            # Scale default model predictions to product scale
            p_avg = float(p_daily["Demand"].mean())
            d_avg = float(default_daily["Demand"].mean()) if default_daily is not None else 1.0
            scale_ratio = (p_avg / d_avg) if d_avg > 0 else 1.0

            for _, row in p_daily.iterrows():
                row_features = pd.DataFrame([row[features]])
                raw_pred = float(model.predict(row_features)[0])
                scaled_pred = max(0.0, raw_pred * scale_ratio)
                comparison.append({
                    "date": row["Date"].strftime("%Y-%m-%d"),
                    "actual": int(row["Demand"]),
                    "predicted": round(scaled_pred, 1),
                })

        avg_daily = float(p_daily["Demand"].mean())
        std_daily = float(p_daily["Demand"].std()) if len(p_daily) > 1 else round(avg_daily * 0.25, 2)
        total_p_demand = int(p_daily["Demand"].sum())

        summary = {
            "total_demand": total_p_demand,
            "average_daily_demand": round(avg_daily, 2),
            "demand_std": round(std_daily, 2),
            "total_days": len(p_daily),
            "selected_product": str(product),
        }

        return p_daily, (p_model if p_model else model), comparison, summary

    def get_historical_data(self, product="all"):
        """Returns historical daily records and test comparison for active dataset / product."""
        if not self.active_dataset:
            return {"error": "No active dataset loaded."}

        daily_df, _, test_comp, summary = self._get_series_for_selection(product)

        if daily_df is None or daily_df.empty:
            return {"error": "No historical demand data available for this selection."}

        history = []
        for _, row in daily_df.iterrows():
            item = {
                "date": row["Date"].strftime("%Y-%m-%d"),
                "demand": int(row["Demand"]),
            }
            if "Revenue" in row:
                item["revenue"] = round(float(row["Revenue"]), 2)
            history.append(item)

        return {
            "dataset_name": self.active_dataset["name"],
            "is_default": self.active_dataset["is_default"],
            "selected_product": product,
            "total_days": len(history),
            "date_range": {
                "start": history[0]["date"] if history else None,
                "end": history[-1]["date"] if history else None,
            },
            "summary": summary,
            "history": history,
            "actual_vs_predicted": test_comp,
        }

    def predict_future(self, days: int = 14, start_date: str = None, product: str = "all"):
        """Generates future forecasts for the active dataset (or specific product)."""
        if not self.active_dataset:
            return {"error": "No active dataset loaded."}

        daily_df, model, _, summary = self._get_series_for_selection(product)

        if daily_df is None or daily_df.empty:
            return {"error": "No daily demand data available to base forecast on."}

        days = max(1, min(int(days), 90))

        if start_date:
            try:
                base_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                return {"error": "Invalid start_date format. Expected YYYY-MM-DD."}
        else:
            last_dt = daily_df["Date"].max()
            base_dt = last_dt + timedelta(days=1)

        future_dates = [base_dt + timedelta(days=i) for i in range(days)]
        future_df = pd.DataFrame({"Date": future_dates})
        future_df["Day"] = future_df["Date"].dt.day
        future_df["Month"] = future_df["Date"].dt.month
        future_df["DayOfWeek"] = future_df["Date"].dt.dayofweek
        future_df["Year"] = future_df["Date"].dt.year

        features = ["Day", "Month", "DayOfWeek", "Year"]

        # Run prediction
        if model is not None:
            raw_preds = model.predict(future_df[features])

            # Check if scaling is needed for product-level selection
            if product != "all" and not hasattr(model, "_is_product_trained"):
                p_avg = summary["average_daily_demand"]
                d_avg = self.active_dataset["summary"]["average_daily_demand"]
                ratio = (p_avg / d_avg) if d_avg > 0 else 1.0
                preds = [max(0.0, float(v) * ratio) for v in raw_preds]
            else:
                preds = [max(0.0, float(v)) for v in raw_preds]
        else:
            # Baseline mean
            avg_val = summary["average_daily_demand"]
            preds = [avg_val for _ in future_dates]

        forecast_points = []
        for i, dt in enumerate(future_dates):
            val = round(float(preds[i]), 1)
            forecast_points.append({
                "date": dt.strftime("%Y-%m-%d"),
                "day_name": dt.strftime("%A"),
                "predicted_demand": val,
            })

        pred_values = [p["predicted_demand"] for p in forecast_points]
        avg_demand = float(np.mean(pred_values))
        total_demand = float(np.sum(pred_values))
        peak_idx = int(np.argmax(pred_values))
        min_idx = int(np.argmin(pred_values))

        return {
            "dataset_name": self.active_dataset["name"],
            "selected_product": product,
            "forecast_days": days,
            "period": {
                "start": forecast_points[0]["date"],
                "end": forecast_points[-1]["date"],
            },
            "summary": {
                "total_demand": round(total_demand, 1),
                "average_daily_demand": round(avg_demand, 1),
                "peak_day": forecast_points[peak_idx],
                "lowest_day": forecast_points[min_idx],
            },
            "forecast": forecast_points,
        }

    def calculate_inventory_recommendations(
        self,
        lead_time_days: float = 7.0,
        service_level: float = 0.95,
        current_stock: float = None,
        target_stock: float = None,
        product: str = "all",
    ):
        """Calculates inventory parameters using the currently active dataset/product statistics."""
        if not self.active_dataset:
            return {"error": "No active dataset loaded."}

        _, _, _, summary = self._get_series_for_selection(product)

        avg_demand = float(summary.get("average_daily_demand", 100.0))
        demand_std = float(summary.get("demand_std", 20.0))

        recs = calculate_inventory_metrics(
            avg_daily_demand=avg_demand,
            demand_std=demand_std,
            lead_time_days=lead_time_days,
            service_level=service_level,
            current_stock=current_stock,
            target_stock=target_stock,
        )

        recs["dataset_name"] = self.active_dataset["name"]
        recs["selected_product"] = product
        return recs

    def process_uploaded_dataset(self, file_stream, filename: str):
        """
        Validates, cleans, and activates an uploaded CSV or Excel dataset.
        Implements explicit column detection, revenue-vs-quantity check,
        product isolation, and chronological 80/20 train/test evaluation.
        """
        fn_lower = filename.lower()
        try:
            if fn_lower.endswith(".csv"):
                df = pd.read_csv(file_stream)
            elif fn_lower.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_stream)
            else:
                return {
                    "error": f"Unsupported file extension for '{filename}'. Please upload a .csv or .xlsx file."
                }
        except Exception as e:
            return {"error": f"Failed to parse uploaded file: {str(e)}"}

        if df.empty:
            return {"error": "The uploaded file is empty (0 rows)."}

        # Normalize column lookup
        col_map = {str(c).strip().lower(): c for c in df.columns}

        # 1. Detect Date Column
        date_candidates = ["date", "invoicedate", "order_date", "day", "timestamp", "transaction_date", "datetime"]
        date_col = None
        for cand in date_candidates:
            if cand in col_map:
                date_col = col_map[cand]
                break

        # 2. Detect Demand / Quantity Column
        demand_candidates = ["quantity", "demand", "sales", "units", "qty", "volume", "sold", "order_qty"]
        demand_col = None
        for cand in demand_candidates:
            if cand in col_map:
                demand_col = col_map[cand]
                break

        # 3. Explicit Revenue vs Quantity Check
        revenue_candidates = ["revenue", "total_price", "total_amount", "amount", "sales_amount", "sales_value"]
        revenue_col = None
        for cand in revenue_candidates:
            if cand in col_map:
                revenue_col = col_map[cand]
                break

        if not demand_col and revenue_col:
            return {
                "error": (
                    f"Dataset contains a financial revenue column ('{revenue_col}') but no physical unit demand/quantity column. "
                    "Demand forecasting and inventory replenishment require physical unit counts (e.g., 'quantity', 'units', 'demand'). "
                    "Revenue cannot be automatically substituted for inventory units. Please include a quantity column in your dataset."
                )
            }

        missing_errs = []
        if not date_col:
            missing_errs.append("Date column (e.g., 'date', 'InvoiceDate', 'order_date')")
        if not demand_col:
            missing_errs.append("Quantity/Demand column (e.g., 'quantity', 'demand', 'sales', 'units')")

        if missing_errs:
            found_cols = ", ".join([f"'{c}'" for c in df.columns[:15]])
            return {
                "error": f"Missing required columns: {', '.join(missing_errs)}. Columns detected in your file: [{found_cols}]."
            }

        # 4. Optional Columns: Product, Category, Price
        product_candidates = ["product", "product_name", "stockcode", "item", "description", "sku", "product_id"]
        product_col = None
        for cand in product_candidates:
            if cand in col_map:
                product_col = col_map[cand]
                break

        category_candidates = ["category", "product_category", "dept", "department", "type", "group", "genre"]
        category_col = None
        for cand in category_candidates:
            if cand in col_map:
                category_col = col_map[cand]
                break

        price_candidates = ["price", "unitprice", "unit_price", "rate", "cost"]
        price_col = None
        for cand in price_candidates:
            if cand in col_map:
                price_col = col_map[cand]
                break

        # 5. Data Cleaning
        initial_count = len(df)
        clean_df = df.copy()

        # Remove duplicate rows
        clean_df = clean_df.drop_duplicates()

        # Filter cancelled transactions if invoice column present
        if "invoiceno" in col_map:
            clean_df = clean_df[~clean_df[col_map["invoiceno"]].astype(str).str.startswith("C")]

        # Parse date and drop invalid
        clean_df[date_col] = pd.to_datetime(clean_df[date_col], errors="coerce")
        clean_df = clean_df.dropna(subset=[date_col])

        # Parse quantity and filter positive
        clean_df[demand_col] = pd.to_numeric(clean_df[demand_col], errors="coerce")
        clean_df = clean_df[clean_df[demand_col] > 0]

        if clean_df.empty:
            return {
                "error": f"No valid records remained after filtering. Please ensure the '{demand_col}' column contains positive numbers and dates are valid."
            }

        # Parse price/revenue if available
        has_revenue = False
        if revenue_col and revenue_col in clean_df.columns:
            clean_df[revenue_col] = pd.to_numeric(clean_df[revenue_col], errors="coerce").fillna(0.0)
            has_revenue = True
        elif price_col and price_col in clean_df.columns:
            clean_df[price_col] = pd.to_numeric(clean_df[price_col], errors="coerce").fillna(0.0)
            clean_df["revenue"] = clean_df[price_col] * clean_df[demand_col]
            revenue_col = "revenue"
            has_revenue = True

        # 6. Aggregate into Daily Demand (Across all products)
        agg_rules = {demand_col: "sum"}
        if has_revenue:
            agg_rules[revenue_col] = "sum"

        daily = clean_df.groupby(clean_df[date_col].dt.date).agg(agg_rules).reset_index()
        daily.rename(columns={date_col: "Date", demand_col: "Demand"}, inplace=True)
        if has_revenue:
            daily.rename(columns={revenue_col: "Revenue"}, inplace=True)

        daily["Date"] = pd.to_datetime(daily["Date"])
        daily = daily.sort_values("Date").reset_index(drop=True)

        if len(daily) < 3:
            return {
                "error": f"Uploaded file only has {len(daily)} calendar days. A minimum of 3 distinct days is required for time-series analysis."
            }

        # 7. Extract Product & Category Information
        products = []
        if product_col and product_col in clean_df.columns:
            p_counts = clean_df.groupby(product_col)[demand_col].sum().sort_values(ascending=False).head(50)
            for p_name, p_qty in p_counts.items():
                if pd.notna(p_name) and str(p_name).strip():
                    products.append({"id": str(p_name), "name": str(p_name), "total_units": int(p_qty)})

        categories = []
        if category_col and category_col in clean_df.columns:
            c_counts = clean_df.groupby(category_col)[demand_col].sum().sort_values(ascending=False).head(20)
            for c_name, c_qty in c_counts.items():
                if pd.notna(c_name) and str(c_name).strip():
                    categories.append({"id": str(c_name), "name": str(c_name), "total_units": int(c_qty)})

        # 8. Train Model on Chronological 80/20 Split (Zero Data Leakage)
        daily["Day"] = daily["Date"].dt.day
        daily["Month"] = daily["Date"].dt.month
        daily["DayOfWeek"] = daily["Date"].dt.dayofweek
        daily["Year"] = daily["Date"].dt.year

        features = ["Day", "Month", "DayOfWeek", "Year"]

        comparison = []
        new_model = None
        eval_metrics = {}

        if len(daily) >= 10:
            split_idx = int(len(daily) * 0.8)
            train_df = daily.iloc[:split_idx]
            test_df = daily.iloc[split_idx:].copy()

            new_model = RandomForestRegressor(n_estimators=100, random_state=42)
            new_model.fit(train_df[features], train_df["Demand"])

            test_preds = new_model.predict(test_df[features])
            mae = float(mean_absolute_error(test_df["Demand"], test_preds))
            rmse = float(np.sqrt(mean_squared_error(test_df["Demand"], test_preds)))
            r2 = float(r2_score(test_df["Demand"], test_preds))

            for i, (_, row) in enumerate(test_df.iterrows()):
                comparison.append({
                    "date": row["Date"].strftime("%Y-%m-%d"),
                    "actual": int(row["Demand"]),
                    "predicted": round(float(test_preds[i]), 1),
                })

            eval_metrics = {
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "r2": round(r2, 4),
                "train_days": len(train_df),
                "test_days": len(test_df),
                "train_start": train_df["Date"].min().strftime("%Y-%m-%d"),
                "train_end": train_df["Date"].max().strftime("%Y-%m-%d"),
                "test_start": test_df["Date"].min().strftime("%Y-%m-%d"),
                "test_end": test_df["Date"].max().strftime("%Y-%m-%d"),
                "description": f"Chronological split: 80% train ({len(train_df)} days), 20% test ({len(test_df)} days).",
            }
        else:
            # Insufficient days for train/test split: fit on all or use fallback
            new_model = RandomForestRegressor(n_estimators=50, random_state=42)
            new_model.fit(daily[features], daily["Demand"])
            eval_metrics = {
                "mae": None,
                "rmse": None,
                "r2": None,
                "train_days": len(daily),
                "test_days": 0,
                "description": f"Dataset contains {len(daily)} days (< 10 days). Evaluation metrics require at least 10 days for held-out chronological testing.",
            }

        avg_daily = float(daily["Demand"].mean())
        demand_std = float(daily["Demand"].std()) if len(daily) > 1 else round(avg_daily * 0.25, 2)
        total_demand = int(daily["Demand"].sum())
        total_rev = round(float(daily["Revenue"].sum()), 2) if has_revenue else None

        # 9. Store as Current Active Dataset!
        self.active_dataset = {
            "id": f"upload_{int(datetime.now().timestamp())}",
            "name": filename,
            "is_default": False,
            "raw_df": clean_df,
            "daily_df": daily,
            "model": new_model,
            "date_col": date_col,
            "demand_col": demand_col,
            "product_col": product_col,
            "category_col": category_col,
            "revenue_col": revenue_col,
            "has_products": len(products) > 0,
            "products": products,
            "has_categories": len(categories) > 0,
            "categories": categories,
            "has_revenue": has_revenue,
            "summary": {
                "total_demand": total_demand,
                "total_revenue": total_rev,
                "average_daily_demand": round(avg_daily, 2),
                "demand_std": round(demand_std, 2),
                "total_days": len(daily),
                "total_transactions": len(clean_df),
                "product_count": len(products),
                "category_count": len(categories),
            },
            "date_range": {
                "start": daily["Date"].min().strftime("%Y-%m-%d"),
                "end": daily["Date"].max().strftime("%Y-%m-%d"),
            },
            "evaluation": eval_metrics,
            "test_comparison": comparison,
        }

        # Return full confirmation status
        status = self.get_dataset_status()
        status["message"] = f"Successfully activated '{filename}'. All dashboard sections synchronized."
        return status


# Global singleton instance
forecast_service = ForecastService()
