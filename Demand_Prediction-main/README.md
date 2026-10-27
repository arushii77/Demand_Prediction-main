# IntelliSupply: AI-Powered Demand Forecasting & Supply Chain Optimization System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61dafb.svg)](https://reactjs.org/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Random%20Forest%20Regressor-orange.svg)](https://scikit-learn.org/)
[![TailwindCSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38bdf8.svg)](https://tailwindcss.com/)

**IntelliSupply** is a full-stack, machine learning-driven web application designed to forecast future product demand and provide actionable inventory replenishment recommendations. By analyzing historical retail transaction patterns, IntelliSupply mitigates both **stockouts** (lost sales) and **overstocking** (excess carrying costs).

---

## 🚀 Key Features

* **AI Demand Forecasting:** Pre-trained Random Forest Regressor predicting daily demand based on calendar seasonality (`Day`, `Month`, `DayOfWeek`, `Year`).
* **Chronological Model Validation:** Evaluated using strict time-based train-test split (80% train / 20% test) to prevent data leakage.
* **Explainable Inventory Optimization:**
  * Dynamic **Safety Stock** based on normal distribution service factors ($Z = 1.65$ for 95% service level).
  * **Reorder Point (ROP)** calculation: $\text{ROP} = (\text{Average Daily Demand} \times \text{Lead Time}) + \text{Safety Stock}$.
  * Replenishment Order Quantity recommendation with real-time stock status alerts.
* **Interactive React Dashboard:** Built with Vite, Tailwind CSS, Lucide icons, and Recharts.
* **Custom Dataset Upload:** Upload custom `.csv` or `.xlsx` files to preview data, evaluate accuracy, and compute instant inventory recommendations.

---

## 📁 Project Architecture

```text
Demand_Prediction-main/
├── backend/
│   ├── app.py                       # Flask application entry point with CORS
│   ├── train_model.py               # Standalone ML training pipeline script
│   ├── requirements.txt             # Python backend dependencies
│   ├── models/
│   │   ├── model.joblib             # Serialized Random Forest Regressor
│   │   └── model_metadata.json      # Accuracy metrics & baseline stats
│   ├── routes/
│   │   └── forecast_routes.py       # REST API endpoints
│   ├── services/
│   │   ├── forecast_service.py      # Inference, calendar features & file upload
│   │   └── inventory_service.py     # Safety stock & reorder point mathematics
│   └── static/images/               # Generated evaluation plots
├── data/
│   ├── raw/online+retail/
│   │   └── Online Retail.xlsx       # Original UCI transaction dataset (541k records)
│   └── processed/
│       ├── daily_demand.csv         # Aggregated 305 daily demand records
│       ├── sample_daily_demand.csv  # 30-day quick test sample
│       └── sample_transactions.csv  # 1,000 transaction sample for upload test
├── frontend/
│   ├── index.html                   # HTML entry point
│   ├── package.json                 # React 18, Vite, Recharts, Lucide-React
│   ├── vite.config.js               # Vite config with backend proxy
│   ├── tailwind.config.js           # Tailwind CSS styling configuration
│   └── src/
│       ├── App.jsx                  # Root layout & tab router
│       ├── main.jsx                 # React root DOM renderer
│       └── components/
│           ├── Navbar.jsx           # Navigation header & live health indicator
│           ├── StatCard.jsx         # Metric KPI card component
│           ├── HistoricalSection.jsx# 305-day trend & test actual vs predicted
│           ├── ForecastSection.jsx  # 7/14/30-day forecast horizon & bar chart
│           ├── InventorySection.jsx # Sliders for Lead Time, Stock, & ROP math
│           ├── UploadSection.jsx    # CSV/Excel drag-and-drop & instant audit
│           └── ProjectInfoSection.jsx# Abstract, architecture & College Viva Q&A
├── start_backend.bat                # 1-click backend launcher (Windows)
├── start_frontend.bat               # 1-click frontend launcher (Windows)
└── README.md
```

---

## 🛠️ Installation & Setup (Windows & VS Code)

### Prerequisites
* Python 3.10+ installed and added to PATH
* Node.js v18+ and npm installed

### Step 1: Open Project in VS Code
Open VS Code, click **File > Open Folder**, and select:
`C:\Users\DELL\Downloads\Demand_Prediction-main\Demand_Prediction-main`

### Step 2: Install Dependencies
Open a terminal in VS Code (`Ctrl + ~`) and run:

**Backend Dependencies:**
```powershell
python -m pip install flask flask-cors pandas numpy scikit-learn joblib openpyxl matplotlib
```

**Frontend Dependencies:**
```powershell
cd frontend
npm install
cd ..
```

---

## ▶️ Running the Application

To run the project, open **two separate terminal tabs** in VS Code:

### Terminal 1: Run the Backend
```powershell
python backend/app.py
```
> The Flask API will start on: **`http://127.0.0.1:5000`**

### Terminal 2: Run the Frontend Dashboard
```powershell
cd frontend
npm run dev
```
> The React Dashboard will start on: **`http://localhost:5173`**

Open **`http://localhost:5173`** in your browser to interact with the full dashboard!

---

## 📊 Model Evaluation & Metrics

The Random Forest Regressor was trained on the first 80% of daily records (244 days) and tested on the remaining 20% (61 days):

| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **Total Daily Records** | 305 days | Dec 1, 2010 – Dec 9, 2011 |
| **Training Set Size** | 244 days | Dec 1, 2010 – Sep 29, 2011 |
| **Testing Set Size** | 61 days | Sep 30, 2011 – Dec 9, 2011 |
| **Mean Absolute Error (MAE)** | `10,109.01` units | Average daily variance on global wholesale scale |
| **Root Mean Sq. Error (RMSE)**| `14,648.08` units | Penalty sensitivity to peak promotional spikes |
| **Baseline Daily Demand ($D_{avg}$)** | `20,157.34` units/day | Average daily shipment rate |
| **Safety Stock (95% Service, $L=7$)** | `19,876.46` units | Buffer inventory to absorb demand surges |
| **Reorder Point (ROP, $L=7$)** | `160,977.81` units | Threshold level to initiate supplier reorder |

---

## 🧮 Inventory Optimization Mathematics

1. **Lead Time Demand ($\text{LTD}$):**
   $$\text{LTD} = D_{\text{avg}} \times \text{Lead Time}$$
2. **Safety Stock ($\text{SS}$):**
   $$\text{SS} = Z \times \sigma_{\text{demand}} \times \sqrt{\text{Lead Time}}$$
   *(where $Z = 1.65$ represents a 95% service level)*
3. **Reorder Point ($\text{ROP}$):**
   $$\text{ROP} = \text{LTD} + \text{SS}$$
4. **Suggested Replenishment Quantity:**
   $$\text{Order Qty} = \max(0, \text{Target Stock} - \text{Current Stock})$$

---

## 🎓 College Viva & Submission Summary

* **Problem Statement:** Businesses struggle with balancing stock levels. Under-ordering causes lost revenue and lost customers; over-ordering incurs holding costs and dead stock.
* **Proposed System:** An automated full-stack AI system combining machine learning demand forecasting with mathematical safety stock and reorder point determination.
* **Technological Stack:** Python, Flask, Scikit-Learn, React.js, Vite, Tailwind CSS, Recharts.
