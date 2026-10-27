"""
IntelliSupply: Inventory Optimization Service
Provides mathematical inventory recommendations including:
- Average Daily Demand
- Demand Variability (Standard Deviation)
- Safety Stock (based on service level factor Z)
- Reorder Point (ROP = Demand during Lead Time + Safety Stock)
- Replenishment Order Quantity
- Stockout Risk & Status Evaluation
"""

import math
import numpy as np


# Service level to Z-score mapping (normal distribution standard scores)
SERVICE_LEVEL_Z = {
    0.90: 1.28,
    0.95: 1.65,
    0.98: 2.05,
    0.99: 2.33,
}


def calculate_inventory_metrics(
    avg_daily_demand: float,
    demand_std: float,
    lead_time_days: float = 7.0,
    service_level: float = 0.95,
    current_stock: float = None,
    target_stock: float = None,
):
    """
    Computes explainable supply chain inventory recommendations.

    Formulas:
    1. Safety Stock (SS) = Z * sigma * sqrt(Lead Time)
    2. Reorder Point (ROP) = (Average Daily Demand * Lead Time) + Safety Stock
    3. Target / Max Stock = ROP + (Average Daily Demand * Review Period)
    4. Replenishment Quantity = max(0, Target Stock - Current Stock)
    """
    # Find closest Z-score
    z_score = SERVICE_LEVEL_Z.get(service_level, 1.65)

    lead_time = max(1.0, float(lead_time_days))
    avg_demand = max(0.0, float(avg_daily_demand))
    sigma = max(0.0, float(demand_std))

    # Lead time demand = average daily demand * lead time
    lead_time_demand = avg_demand * lead_time

    # Safety stock accounting for lead time variance
    safety_stock = z_score * sigma * math.sqrt(lead_time)

    # Reorder point
    reorder_point = lead_time_demand + safety_stock

    # Default target stock: covers lead time + safety stock + 7 days cycle stock
    review_period_days = 7.0
    recommended_target = reorder_point + (avg_demand * review_period_days)

    if target_stock is None or float(target_stock) <= 0:
        effective_target = recommended_target
    else:
        effective_target = float(target_stock)

    # Stock assessment if current stock is provided
    status = "UNKNOWN"
    status_color = "gray"
    status_message = "Enter current stock to evaluate replenishment."
    suggested_order = 0.0
    days_of_supply = None

    if current_stock is not None:
        current = float(current_stock)
        days_of_supply = round(current / avg_demand, 1) if avg_demand > 0 else 999.0

        if current < safety_stock:
            status = "CRITICAL_STOCKOUT_RISK"
            status_color = "red"
            status_message = (
                f"Current stock ({current:,.0f}) is below Safety Stock ({safety_stock:,.0f}). "
                "High probability of stockout. Expedite replenishment immediately!"
            )
            suggested_order = max(0.0, effective_target - current)
        elif current <= reorder_point:
            status = "REORDER_NOW"
            status_color = "amber"
            status_message = (
                f"Current stock ({current:,.0f}) is below Reorder Point ({reorder_point:,.0f}). "
                "Place order now with supplier."
            )
            suggested_order = max(0.0, effective_target - current)
        elif current > effective_target * 1.25:
            status = "OVERSTOCKED"
            status_color = "purple"
            status_message = (
                f"Current stock ({current:,.0f}) exceeds Target Stock ({effective_target:,.0f}) by >25%. "
                "Risk of holding costs and depreciation."
            )
            suggested_order = 0.0
        else:
            status = "OPTIMAL"
            status_color = "green"
            status_message = f"Stock level is healthy ({days_of_supply:.1f} days of supply)."
            suggested_order = 0.0

    return {
        "inputs": {
            "lead_time_days": lead_time,
            "service_level": f"{int(service_level * 100)}%",
            "z_factor": z_score,
            "current_stock": current_stock,
            "target_stock": round(effective_target, 2),
        },
        "metrics": {
            "average_daily_demand": round(avg_demand, 2),
            "demand_std_dev": round(sigma, 2),
            "lead_time_demand": round(lead_time_demand, 2),
            "safety_stock": round(safety_stock, 2),
            "reorder_point": round(reorder_point, 2),
            "recommended_target_stock": round(recommended_target, 2),
            "suggested_replenishment_quantity": round(suggested_order, 2),
            "days_of_supply": days_of_supply,
        },
        "status": {
            "code": status,
            "badge_color": status_color,
            "description": status_message,
        },
        "formula_breakdown": {
            "lead_time_demand": f"{avg_demand:,.1f} units/day * {lead_time:.0f} days = {lead_time_demand:,.1f} units",
            "safety_stock": f"Z ({z_score}) * sigma ({sigma:,.1f}) * sqrt({lead_time:.0f}) = {safety_stock:,.1f} units",
            "reorder_point": f"Lead Time Demand ({lead_time_demand:,.1f}) + Safety Stock ({safety_stock:,.1f}) = {reorder_point:,.1f} units",
        },
    }
