"""Generate sample datasets for demo purposes."""

import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
os.makedirs(OUTPUT_DIR, exist_ok=True)

random.seed(42)
np.random.seed(42)

# ------------------------------------------------------------------
# 1. Sales Dataset
# ------------------------------------------------------------------
n = 500
start = date(2023, 1, 1)
dates = [start + timedelta(days=i) for i in range(n)]
regions = ["North", "South", "East", "West"]
products = ["Widget A", "Widget B", "Gadget X", "Gadget Y", "Super Tool"]

sales_df = pd.DataFrame({
    "date": dates,
    "region": np.random.choice(regions, n),
    "product": np.random.choice(products, n),
    "units_sold": np.random.randint(10, 500, n),
    "unit_price": np.round(np.random.uniform(9.99, 199.99, n), 2),
    "discount_pct": np.round(np.random.uniform(0, 0.3, n), 2),
    "returns": np.random.randint(0, 30, n),
    "customer_satisfaction": np.round(np.random.uniform(3.0, 5.0, n), 1),
})
sales_df["revenue"] = np.round(
    sales_df["units_sold"] * sales_df["unit_price"] * (1 - sales_df["discount_pct"]), 2
)
# Inject anomalies
sales_df.loc[50, "revenue"] = 99999.0
sales_df.loc[200, "units_sold"] = 5000

sales_df.to_csv(os.path.join(OUTPUT_DIR, "sales.csv"), index=False)
print(f"Generated sales.csv ({len(sales_df)} rows)")

# ------------------------------------------------------------------
# 2. Website Traffic Dataset
# ------------------------------------------------------------------
n2 = 365
start2 = date(2023, 1, 1)
dates2 = [start2 + timedelta(days=i) for i in range(n2)]
base_traffic = 1000
trend = np.linspace(0, 500, n2)
seasonality = 200 * np.sin(2 * np.pi * np.arange(n2) / 7)
noise = np.random.normal(0, 50, n2)
traffic = np.maximum(100, base_traffic + trend + seasonality + noise).astype(int)

traffic_df = pd.DataFrame({
    "date": dates2,
    "page_views": traffic,
    "unique_visitors": (traffic * np.random.uniform(0.5, 0.8, n2)).astype(int),
    "bounce_rate": np.round(np.random.uniform(0.3, 0.7, n2), 3),
    "avg_session_duration_sec": np.random.randint(60, 600, n2),
    "conversions": np.random.randint(0, 50, n2),
    "channel": np.random.choice(["organic", "paid", "social", "email", "direct"], n2),
})
traffic_df.to_csv(os.path.join(OUTPUT_DIR, "web_traffic.csv"), index=False)
print(f"Generated web_traffic.csv ({len(traffic_df)} rows)")

# ------------------------------------------------------------------
# 3. HR Dataset
# ------------------------------------------------------------------
n3 = 300
departments = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"]
hr_df = pd.DataFrame({
    "employee_id": range(1001, 1001 + n3),
    "department": np.random.choice(departments, n3),
    "tenure_years": np.round(np.random.exponential(3.5, n3), 1),
    "salary": np.round(np.random.normal(75000, 20000, n3), 0),
    "performance_score": np.round(np.random.uniform(1, 5, n3), 1),
    "age": np.random.randint(22, 62, n3),
    "attrition": np.random.choice([0, 1], n3, p=[0.85, 0.15]),
    "training_hours": np.random.randint(0, 80, n3),
    "overtime_hours": np.random.randint(0, 20, n3),
})
hr_df.to_csv(os.path.join(OUTPUT_DIR, "hr_data.csv"), index=False)
print(f"Generated hr_data.csv ({len(hr_df)} rows)")

print("All sample datasets generated.")
