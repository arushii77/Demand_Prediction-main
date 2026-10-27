import os
import pandas as pd
import numpy as np

base_dir = r"C:\Users\DELL\Downloads\Demand_Prediction-main"
processed_dir = os.path.join(base_dir, "data", "processed")
nested_dir = os.path.join(base_dir, "Demand_Prediction-main", "data", "processed")
os.makedirs(processed_dir, exist_ok=True)
os.makedirs(nested_dir, exist_ok=True)

# 1. Multi-product sales dataset (60 days)
np.random.seed(42)
dates = pd.date_range(start="2023-06-01", end="2023-07-30", freq="D")
products_info = [
    ("Wireless Earbuds Pro", "Electronics", 79.99, (20, 80)),
    ("Smart Fitness Watch", "Electronics", 129.99, (15, 60)),
    ("Ergonomic Office Chair", "Furniture", 199.99, (5, 25)),
    ("Stainless Steel Kettle", "Home & Kitchen", 34.99, (30, 90)),
    ("Organic Arabica Coffee 1kg", "Groceries", 24.50, (40, 120)),
    ("Trail Running Shoes", "Apparel", 89.00, (10, 45)),
]

records = []
for dt in dates:
    is_weekend = int(dt.dayofweek in [5, 6])
    month = dt.month
    day_of_week = dt.dayofweek
    is_month_start = int(dt.is_month_start)
    is_month_end = int(dt.is_month_end)
    season = "Summer"
    is_holiday = int(dt.strftime("%m-%d") == "07-04")
    holiday_name = "Independence Day" if is_holiday else "None"
    
    for prod_name, cat, price, (q_min, q_max) in products_info:
        mult = 1.35 if is_weekend else 1.0
        qty = int(np.random.randint(q_min, q_max) * mult)
        rev = round(qty * price, 2)
        records.append({
            "date": dt.strftime("%Y-%m-%d"),
            "product": prod_name,
            "category": cat,
            "price": price,
            "quantity": qty,
            "revenue": rev,
            "source": "Online Store",
            "country": "United States",
            "is_weekend": is_weekend,
            "month": month,
            "day_of_week": day_of_week,
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "season": season,
            "is_month_start": is_month_start,
            "is_month_end": is_month_end
        })

df1 = pd.DataFrame(records)
p1 = os.path.join(processed_dir, "sample_sales_with_products.csv")
df1.to_csv(p1, index=False)
df1.to_csv(os.path.join(nested_dir, "sample_sales_with_products.csv"), index=False)
print("Created sample multi-product dataset:", p1, len(df1), "rows")

# 2. Revenue-only dataset (to test rejection)
df_rev = df1[["date", "product", "category", "price", "revenue"]].copy()
p2 = os.path.join(processed_dir, "test_revenue_only.csv")
df_rev.to_csv(p2, index=False)
df_rev.to_csv(os.path.join(nested_dir, "test_revenue_only.csv"), index=False)
print("Created test_revenue_only dataset:", p2)

# 3. Second distinct dataset (2024 dates, different products)
dates2 = pd.date_range(start="2024-01-01", end="2024-03-31", freq="D")
prods2 = [
    ("4K Gaming Monitor 27", "Tech", 299.99, (8, 30)),
    ("Mechanical Keyboard RGB", "Tech", 89.99, (15, 50)),
    ("Standing Desk Motorized", "Office", 349.99, (3, 12))
]
records2 = []
for dt in dates2:
    for pname, cat, pr, (q1, q2) in prods2:
        qty = int(np.random.randint(q1, q2))
        records2.append({
            "date": dt.strftime("%Y-%m-%d"),
            "product": pname,
            "category": cat,
            "price": pr,
            "quantity": qty,
            "revenue": round(qty * pr, 2),
            "country": "Canada"
        })
df2 = pd.DataFrame(records2)
p3 = os.path.join(processed_dir, "test_alternative_dataset.csv")
df2.to_csv(p3, index=False)
df2.to_csv(os.path.join(nested_dir, "test_alternative_dataset.csv"), index=False)
print("Created alternative 2024 dataset:", p3, len(df2), "rows")

# 4. Invalid schema file (missing quantity and date)
df_inv = pd.DataFrame({"random_col_1": [1, 2, 3], "random_col_2": ["a", "b", "c"]})
p4 = os.path.join(processed_dir, "test_missing_columns.csv")
df_inv.to_csv(p4, index=False)
df_inv.to_csv(os.path.join(nested_dir, "test_missing_columns.csv"), index=False)
print("Created test_missing_columns dataset:", p4)
