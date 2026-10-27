import sys
import os

# Append backend to path
sys.path.append(r"C:\Users\DELL\Downloads\Demand_Prediction-main\backend")
from app import app

client = app.test_client()

print("====================================================")
print("TESTING BACKEND DATASET SYNCHRONIZATION & VALIDATION")
print("====================================================")

# Test 1: Default Dataset Status
print("\n--- Test 1: Default Dataset Status ---")
r1 = client.get("/api/dataset/status")
assert r1.status_code == 200, f"Failed: {r1.status_code}"
d1 = r1.get_json()
print("Dataset Name:", d1["name"])
print("Is Default:", d1["is_default"])
print("Total Days:", d1["summary"]["total_days"])
print("Avg Daily Demand:", d1["summary"]["average_daily_demand"])
assert d1["is_default"] is True
assert d1["summary"]["total_days"] == 305

# Test 2: Upload Sample Multi-Product Dataset
print("\n--- Test 2: Upload Multi-Product Dataset ---")
sample_file = r"C:\Users\DELL\Downloads\Demand_Prediction-main\data\processed\sample_sales_with_products.csv"
with open(sample_file, "rb") as f:
    r2 = client.post("/api/upload", data={"file": (f, "sample_sales_with_products.csv")})
assert r2.status_code == 200, f"Upload failed: {r2.status_code} {r2.get_json()}"
d2 = r2.get_json()
print("Upload Success Message:", d2.get("message"))
print("Active Dataset Name:", d2["name"])
print("Is Default:", d2["is_default"])
print("Total Transactions:", d2["summary"]["total_transactions"])
print("Total Days:", d2["summary"]["total_days"])
print("Avg Daily Demand:", d2["summary"]["average_daily_demand"])
print("Has Products:", d2["has_products"], "Product Count:", d2["product_count"])
print("Has Revenue:", d2["has_revenue"], "Total Revenue:", d2["summary"]["total_revenue"])
print("Evaluation MAE:", d2["evaluation"]["mae"], "RMSE:", d2["evaluation"]["rmse"], "Test Days:", d2["evaluation"]["test_days"])
assert d2["is_default"] is False
assert d2["name"] == "sample_sales_with_products.csv"
assert d2["has_products"] is True
assert d2["has_revenue"] is True
assert d2["evaluation"]["mae"] is not None

# Test 3: Verify /api/historical-demand reflects uploaded dataset
print("\n--- Test 3: Historical Demand Reflection ---")
r3 = client.get("/api/historical-demand")
assert r3.status_code == 200
d3 = r3.get_json()
print("Active Dataset reflected:", d3["dataset_name"])
print("Total Days:", d3["total_days"])
print("Date Range:", d3["date_range"])
print("Average Demand:", d3["summary"]["average_daily_demand"])
assert d3["dataset_name"] == "sample_sales_with_products.csv"
assert d3["total_days"] == 60

# Test 4: Product-Level Historical Demand
print("\n--- Test 4: Product-Level Historical Demand ---")
r4 = client.get("/api/historical-demand?product=Wireless Earbuds Pro")
assert r4.status_code == 200
d4 = r4.get_json()
print("Selected Product:", d4["selected_product"])
print("Product Total Demand:", d4["summary"]["total_demand"])
print("Product Avg Daily Demand:", d4["summary"]["average_daily_demand"])
assert d4["selected_product"] == "Wireless Earbuds Pro"
assert d4["summary"]["total_demand"] < d3["summary"]["total_demand"]

# Test 5: Future Forecast Reflects Uploaded Dataset
print("\n--- Test 5: Future Forecast on Uploaded Dataset ---")
r5 = client.get("/api/forecast?days=14")
assert r5.status_code == 200
d5 = r5.get_json()
print("Forecast Dataset:", d5["dataset_name"])
print("Forecast Period:", d5["period"])
print("Forecast Avg Daily:", d5["summary"]["average_daily_demand"])
assert d5["dataset_name"] == "sample_sales_with_products.csv"
# Since data ends 2023-07-30, forecast should start 2023-07-31
assert d5["period"]["start"] == "2023-07-31"

# Test 6: Inventory Optimization Reflects Uploaded Dataset
print("\n--- Test 6: Inventory Recommendations on Uploaded Dataset ---")
r6 = client.post("/api/inventory/recommend", json={"lead_time_days": 7, "service_level": 0.95, "current_stock": 500})
assert r6.status_code == 200
d6 = r6.get_json()
print("Inventory Dataset:", d6["dataset_name"])
print("Avg Daily Demand Used:", d6["metrics"]["average_daily_demand"])
print("Safety Stock:", d6["metrics"]["safety_stock"])
print("Reorder Point:", d6["metrics"]["reorder_point"])
print("Status:", d6["status"]["code"])
assert d6["dataset_name"] == "sample_sales_with_products.csv"
# Uploaded dataset demand is ~300 units/day, not 20,000!
assert d6["metrics"]["average_daily_demand"] < 1000

# Test 7: Upload Revenue-Only Dataset (Should Be Rejected)
print("\n--- Test 7: Revenue-Only Rejection ---")
rev_file = r"C:\Users\DELL\Downloads\Demand_Prediction-main\data\processed\test_revenue_only.csv"
with open(rev_file, "rb") as f:
    r7 = client.post("/api/upload", data={"file": (f, "test_revenue_only.csv")})
print("Status Code (Expected 400):", r7.status_code)
print("Rejection Error Message:", r7.get_json().get("error"))
assert r7.status_code == 400
assert "revenue" in r7.get_json()["error"].lower()

# Test 8: Upload Invalid Schema (Missing columns)
print("\n--- Test 8: Missing Columns Rejection ---")
inv_file = r"C:\Users\DELL\Downloads\Demand_Prediction-main\data\processed\test_missing_columns.csv"
with open(inv_file, "rb") as f:
    r8 = client.post("/api/upload", data={"file": (f, "test_missing_columns.csv")})
print("Status Code (Expected 400):", r8.status_code)
print("Rejection Error Message:", r8.get_json().get("error"))
assert r8.status_code == 400

# Test 9: Upload Alternative Dataset (Canada 2024)
print("\n--- Test 9: Alternative Dataset Upload ---")
alt_file = r"C:\Users\DELL\Downloads\Demand_Prediction-main\data\processed\test_alternative_dataset.csv"
with open(alt_file, "rb") as f:
    r9 = client.post("/api/upload", data={"file": (f, "test_alternative_dataset.csv")})
assert r9.status_code == 200
d9 = r9.get_json()
print("Switched Active Dataset:", d9["name"])
print("New Date Range:", d9["date_range"])
assert d9["name"] == "test_alternative_dataset.csv"
assert "2024" in d9["date_range"]["start"]

# Test 10: Reset to Default Dataset
print("\n--- Test 10: Reset to Default Dataset ---")
r10 = client.post("/api/dataset/reset")
assert r10.status_code == 200
d10 = r10.get_json()["dataset"]
print("Reset Active Dataset:", d10["name"])
print("Is Default:", d10["is_default"])
print("Total Days:", d10["summary"]["total_days"])
assert d10["is_default"] is True
assert d10["summary"]["total_days"] == 305

print("\n====================================================")
print("ALL 10 BACKEND INTEGRATION & SYNCHRONIZATION TESTS PASSED!")
print("====================================================")
