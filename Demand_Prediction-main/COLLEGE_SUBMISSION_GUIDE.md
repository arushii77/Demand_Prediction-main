# IntelliSupply: College Mini-Project Submission Document

**Project Title:** IntelliSupply: AI-Powered Demand Forecasting & Supply Chain Optimization System  
**Domain:** Machine Learning & Full-Stack Web Development  
**Target Submission:** College Mini Project / Final Semester Project  

---

## 1. Project Abstract

Accurate demand prediction and efficient inventory management are critical for business profitability and operational sustainability. Retail enterprises frequently confront the dual challenge of **stockouts** (depleted inventory leading to lost revenue and customer dissatisfaction) and **overstocking** (surplus inventory generating excessive holding costs and obsolescence).

**IntelliSupply** is an AI-powered, full-stack decision-support system that bridges machine learning with inventory control theory. Using historical transaction data from the UCI Online Retail dataset (comprising over 540,000 transactions), the system cleans and aggregates retail sales into daily demand, extracts calendar-based seasonal features, and trains a **Random Forest Regressor** to forecast future product demand. The forecast outputs feed directly into an explainable **Inventory Optimization Engine** that calculates dynamic **Safety Stock**, **Reorder Points (ROP)**, and **Replenishment Quantities** under user-defined service levels and lead times. The solution is delivered via an interactive, responsive **React + Vite** dashboard supported by a **Python Flask REST API**.

---

## 2. Problem Statement & Objectives

### Problem Statement
Traditional retail operations rely heavily on manual spreadsheets or naive moving averages to order inventory. These static approaches cannot adapt to weekly cycles, monthly seasonality, or supplier lead-time fluctuations, resulting in frequent stockout emergencies or high inventory carrying expenses.

### Objectives
1. **Automated Data Cleaning & Aggregation:** Filter transactional noise (cancellations, invalid returns) and aggregate records into continuous daily time-series demand.
2. **AI-Driven Forecasting:** Train and validate an ensemble machine learning model (Random Forest Regressor) with strict chronological train-test splitting to prevent future data leakage.
3. **Statistical Inventory Optimization:** Dynamically compute Safety Stock and Reorder Points using standard service-level $Z$-scores and vendor lead times.
4. **Interactive Full-Stack Web Interface:** Enable business managers and students to test custom dataset uploads, view comparative visual charts (Actual vs Predicted), and simulate inventory scenarios in real-time.

---

## 3. Existing System vs Proposed System

| Dimension | Existing System | Proposed System (IntelliSupply) |
| :--- | :--- | :--- |
| **Forecasting Method** | Manual spreadsheets / Naive historical averages | Random Forest Machine Learning Ensemble |
| **Feature Utilization** | Single-variable historical sum | Multi-temporal calendar features (Day, Month, DayOfWeek, Year) |
| **Data Leakage Control** | Often neglected in traditional classroom models | Strict chronological 80/20 train/test split |
| **Inventory Integration** | Disconnected from prediction models | Direct mathematical integration (Lead Time Demand + Safety Stock) |
| **User Interface** | Raw command-line scripts or static Jupyter Notebooks | Modern, responsive React dashboard with real-time interactive charts |
| **Extensibility** | Fixed to a single offline dataset | Dynamic drag-and-drop file upload supporting any retail CSV or Excel file |

---

## 4. System Architecture & Workflow

```text
[Raw Retail Transactions (Excel / CSV)]
                 │
                 ▼
┌─────────────────────────────────┐
│     Data Preprocessing Engine   │
│  - Filter cancellations (Inv 'C')│
│  - Remove non-positive quantities│
│  - Aggregate into Daily Demand  │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│       Feature Engineering       │
│  - Day of Month (1 - 31)        │
│  - Month of Year (1 - 12)       │
│  - Day of Week (0 - 6)          │
│  - Calendar Year                │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Random Forest Regressor (ML)  │
│  - 100 Decision Trees           │
│  - Chronological 80/20 Split    │
│  - Serialized via Joblib        │
└────────────────┬────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│               Python Flask REST API (Port 5000)         │
│  /api/health            /api/model-info                 │
│  /api/historical-demand /api/forecast                   │
│  /api/upload            /api/inventory/recommend        │
└────────────────┬───────────────────────────────────────┘
                 │ (JSON Responses over HTTP)
                 ▼
┌────────────────────────────────────────────────────────┐
│           React + Vite Dashboard (Port 5173)           │
│  - KPI Metric Cards (MAE, RMSE, Average Run-Rate)      │
│  - Recharts Visualizations (305-day Trend, Actual vs Pred)
│  - Future Forecast Horizon Selector (7, 14, 30, 60 Days)│
│  - Interactive Inventory Sliders (Lead Time & Service) │
│  - Custom Dataset File Drag-and-Drop & Instant Audit   │
└────────────────────────────────────────────────────────┘
```

---

## 5. Dataset Description

* **Source:** UCI Machine Learning Repository — Online Retail Dataset
* **Domain:** UK-based registered non-store online retail distributor
* **Total Raw Transactions:** 541,909 records
* **Time Period:** December 1, 2010 to December 9, 2011 (374 calendar days)
* **Preprocessed Daily Records:** 305 trading days

### Key Attributes:
1. `InvoiceNo`: 6-digit transaction identifier (codes starting with 'C' indicate cancellations).
2. `StockCode`: 5-digit product code.
3. `Description`: Product name.
4. `Quantity`: Quantities of each product ordered.
5. `InvoiceDate`: Day and time of purchase.
6. `UnitPrice`: Price per unit in Sterling (£).
7. `CustomerID`: 5-digit client identifier.
8. `Country`: Country of customer residency.

---

## 6. Machine Learning Methodology

### 1. Data Cleaning
* Removed cancelled invoices where `InvoiceNo.startswith('C')`.
* Filtered out negative and zero quantities (`Quantity > 0`).
* Converted `InvoiceDate` to calendar dates and summed quantities to obtain total daily demand.

### 2. Temporal Feature Engineering
* `Day`: Captures intra-month cycles (e.g. month-end salary purchasing).
* `Month`: Captures seasonal retail spikes (e.g. Q4 Black Friday and Christmas).
* `DayOfWeek`: Captures weekly patterns (weekdays vs weekend retail shopping).
* `Year`: Distinguishes year-over-year baseline growth.

### 3. Chronological Train-Test Split
* **Training Set:** 80% (244 records: Dec 1, 2010 – Sep 29, 2011)
* **Testing Set:** 20% (61 records: Sep 30, 2011 – Dec 9, 2011)

### 4. Algorithm & Hyperparameters
* **Algorithm:** `RandomForestRegressor` from `scikit-learn`
* `n_estimators = 100`
* `random_state = 42`

### 5. Evaluation Metrics
$$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i| = 10,109.01 \text{ units}$$
$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2} = 14,648.08 \text{ units}$$

---

## 7. Inventory Optimization Mathematics

1. **Average Daily Demand ($D_{\text{avg}}$):**
   $$D_{\text{avg}} = \frac{1}{N} \sum_{t=1}^N \hat{y}_t \approx 20,157.34 \text{ units/day}$$

2. **Demand Variability ($\sigma$):**
   $$\sigma = \text{std}(y_{\text{actual}} - \hat{y}_{\text{pred}}) \approx 12,046.34$$

3. **Safety Stock ($\text{SS}$):**
   $$\text{SS} = Z \times \sigma \times \sqrt{L}$$
   *Where $Z$ represents the service factor ($Z = 1.65$ for 95% service level) and $L = 7$ days lead time.*  
   $$\text{SS} = 1.65 \times 12,046.34 \times \sqrt{7} \approx 52,588 \text{ units}$$

4. **Reorder Point ($\text{ROP}$):**
   $$\text{ROP} = (D_{\text{avg}} \times L) + \text{SS}$$
   $$\text{ROP} = (20,157.34 \times 7) + 52,588 \approx 193,689 \text{ units}$$

5. **Suggested Replenishment Quantity:**
   $$\text{Replenishment Order} = \max(0, \text{Target Stock} - \text{Current Stock})$$

---

## 8. College Presentation (PPT) Slide Outline

* **Slide 1: Title Slide**
  * Title: IntelliSupply: AI-Powered Demand Forecasting & Supply Chain Optimization
  * Subtitle: A Machine Learning and Full-Stack Web Application
  * Student Name, Roll Number, Branch/Department, College Name, Guide/Mentor Name.
* **Slide 2: Problem Statement**
  * The Bullwhip Effect in Retail.
  * Stockout penalties vs Overstock carrying expenses.
* **Slide 3: Proposed Solution & Objectives**
  * Data-driven demand forecasting with Random Forest.
  * Mathematical inventory optimization (Safety Stock & ROP).
  * Web interface for interactive management.
* **Slide 4: System Architecture Diagram**
  * [Include architecture diagram from Section 4].
* **Slide 5: Dataset & Preprocessing Pipeline**
  * UCI Online Retail dataset (541k transactions).
  * Data cleaning steps and chronological 80/20 train/test split.
* **Slide 6: Machine Learning Model & Evaluation**
  * Random Forest Regressor rationale.
  * Evaluation metrics: MAE = 10,109, RMSE = 14,648.
  * Actual vs Predicted comparison plot.
* **Slide 7: Inventory Optimization Module**
  * Formulas for Safety Stock and Reorder Point.
  * How service level factor $Z$ controls stockout probability.
* **Slide 8: Full-Stack Web Application Demo**
  * Screenshots of the React dashboard: Overview, Forecast, Inventory, and Upload.
* **Slide 9: Limitations & Future Scope**
  * Adding lag features and rolling window statistics.
  * Product-level hierarchical forecasting (SKU level).
  * Deep learning models (LSTM, Transformers).
* **Slide 10: Conclusion & References**
  * Summary of project outcomes.
  * Key references (UCI repository, Scikit-learn, React docs).

---

## 9. Top 10 Viva Questions with Simple Model Answers

1. **Q: Why is demand forecasting important in supply chains?**  
   *A: It allows businesses to order inventory proactively rather than reactively, minimizing both expensive stockouts and costly overstock inventory holding fees.*

2. **Q: Why did you choose Random Forest Regressor?**  
   *A: Random Forest is an ensemble learning method combining 100 decision trees. It handles non-linear relationships, resists overfitting through feature bagging, and captures complex interactions among calendar features without assuming a normal distribution.*

3. **Q: What is data leakage and how did you prevent it?**  
   *A: In time series, randomly shuffling data causes the model to learn from future events to predict past events (data leakage). We prevented this by using a chronological split: the first 80% of days for training and the final 20% for testing.*

4. **Q: What are MAE and RMSE, and why use both?**  
   *A: MAE measures the average absolute magnitude of errors in identical units. RMSE squares errors before averaging, penalizing larger error spikes more severely. Using both helps us evaluate both typical errors and extreme outlier prediction errors.*

5. **Q: What is Safety Stock?**  
   *A: Safety stock is buffer inventory held to protect against sudden surges in customer demand or unexpected supplier shipping delays.*

6. **Q: How does the Service Level factor Z work?**  
   *A: The Z-factor comes from the standard normal distribution. A 95% service level corresponds to $Z = 1.65$, meaning there is a 95% mathematical probability that demand during lead time will not exceed available stock.*

7. **Q: What is the Reorder Point (ROP)?**  
   *A: ROP is the predetermined inventory level that triggers a replenishment order: $\text{ROP} = (\text{Lead Time Demand}) + \text{Safety Stock}$.*

8. **Q: Why did you build the backend with Flask instead of Django?**  
   *A: Flask is a lightweight microframework that provides clean, decoupled RESTful APIs with minimal overhead, making it ideal for serving pre-trained machine learning models without unnecessary database bloat.*

9. **Q: How does the dataset upload feature work?**  
   *A: The user uploads a CSV or Excel file via the React dashboard. Flask validates the schema, aggregates the rows into daily demand, feeds the temporal features to the trained Random Forest model, and returns customized forecasts and inventory advice instantly.*

10. **Q: What is the primary limitation of your model and how would you extend it?**  
    *A: The baseline model forecasts global daily wholesale demand using calendar features. Future enhancements include SKU-level forecasting, incorporating 7-day lag features, and testing LSTM neural networks for long-term sequential dependencies.*
