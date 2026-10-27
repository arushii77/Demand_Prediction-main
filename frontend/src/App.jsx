import React, { useState, useEffect, useCallback, useRef } from 'react';
import Navbar from './components/Navbar';
import HistoricalSection from './components/HistoricalSection';
import ForecastSection from './components/ForecastSection';
import InventorySection from './components/InventorySection';
import UploadSection from './components/UploadSection';
import { Database, RotateCcw, Filter, CheckCircle2, AlertCircle } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [apiOnline, setApiOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Single Source of Truth for Active Dataset
  const [datasetStatus, setDatasetStatus] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState('all');

  // Synchronized sections data
  const [historicalData, setHistoricalData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [inventoryData, setInventoryData] = useState(null);

  // User input parameters
  const [forecastDays, setForecastDays] = useState(14);
  const [inventoryParams, setInventoryParams] = useState({
    leadTime: 7,
    serviceLevel: 0.95,
    currentStock: '',
    targetStock: '',
  });

  // Notification message
  const [notification, setNotification] = useState(null);
  const reqSeq = useRef(0);

  // Show a notification that fades after 5 seconds
  const showToast = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => {
      setNotification((curr) => (curr?.message === message ? null : curr));
    }, 6000);
  };

  // Synchronized fetch across all sections
  const fetchAllSections = useCallback(async (product, days, invParams) => {
    const currentSeq = ++reqSeq.current;
    setRefreshing(true);

    try {
      const prodParam = encodeURIComponent(product || 'all');
      const histUrl = `/api/historical-demand?product=${prodParam}`;
      const fcastUrl = `/api/forecast?days=${days || 14}&product=${prodParam}`;

      const invBody = {
        lead_time_days: invParams.leadTime || 7,
        service_level: invParams.serviceLevel || 0.95,
        current_stock: invParams.currentStock === '' ? null : Number(invParams.currentStock),
        target_stock: invParams.targetStock === '' ? null : Number(invParams.targetStock),
        product: product || 'all',
      };

      const [histRes, fcastRes, invRes] = await Promise.all([
        fetch(histUrl),
        fetch(fcastUrl),
        fetch('/api/inventory/recommend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(invBody),
        }),
      ]);

      if (currentSeq !== reqSeq.current) return; // Prevent race conditions

      if (histRes.ok) {
        const histJson = await histRes.json();
        setHistoricalData(histJson);
      }
      if (fcastRes.ok) {
        const fcastJson = await fcastRes.json();
        setForecastData(fcastJson);
      }
      if (invRes.ok) {
        const invJson = await invRes.json();
        setInventoryData(invJson);
      }
    } catch (err) {
      console.error('Error fetching synchronized section data:', err);
    } finally {
      if (currentSeq === reqSeq.current) {
        setRefreshing(false);
      }
    }
  }, []);

  // Initial load on mount
  useEffect(() => {
    const initApp = async () => {
      setLoading(true);
      try {
        const healthRes = await fetch('/api/health');
        if (healthRes.ok) {
          setApiOnline(true);
        } else {
          setApiOnline(false);
        }

        const statusRes = await fetch('/api/dataset/status');
        if (statusRes.ok) {
          const statusJson = await statusRes.json();
          setDatasetStatus(statusJson);
          await fetchAllSections('all', forecastDays, inventoryParams);
        }
      } catch (err) {
        console.error('Initial load failure:', err);
        setApiOnline(false);
      } finally {
        setLoading(false);
      }
    };

    initApp();
  }, []);

  // Handler: When user selects a different product
  const handleProductChange = (newProduct) => {
    setSelectedProduct(newProduct);
    fetchAllSections(newProduct, forecastDays, inventoryParams);
  };

  // Handler: When user changes forecast horizon or start date
  const handleDaysChange = (newDays, startDate) => {
    setForecastDays(newDays);
    const prodParam = encodeURIComponent(selectedProduct || 'all');
    let url = `/api/forecast?days=${newDays}&product=${prodParam}`;
    if (startDate) url += `&start_date=${startDate}`;

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        if (!data.error) setForecastData(data);
      })
      .catch((err) => console.error(err));
  };

  // Handler: When user changes inventory parameters
  const handleInventoryParamChange = (paramName, value) => {
    const updated = { ...inventoryParams, [paramName]: value };
    setInventoryParams(updated);

    fetch('/api/inventory/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lead_time_days: updated.leadTime,
        service_level: updated.serviceLevel,
        current_stock: updated.currentStock === '' ? null : Number(updated.currentStock),
        target_stock: updated.targetStock === '' ? null : Number(updated.targetStock),
        product: selectedProduct || 'all',
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data.error) setInventoryData(data);
      })
      .catch((err) => console.error(err));
  };

  // Handler: Upload Successful -> Synchronize entire dashboard!
  const handleUploadSuccess = async (uploadResult) => {
    setDatasetStatus(uploadResult);
    setSelectedProduct('all');
    showToast(`Dataset "${uploadResult.name}" successfully activated across all dashboard sections!`, 'success');
    await fetchAllSections('all', forecastDays, inventoryParams);
    setActiveTab('overview');
  };

  // Handler: Reset to Default Dataset
  const handleResetToDefault = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/dataset/reset', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        setDatasetStatus(data.dataset);
        setSelectedProduct('all');
        showToast('Reverted to default UCI Online Retail dataset successfully.', 'info');
        await fetchAllSections('all', forecastDays, inventoryParams);
      }
    } catch (err) {
      console.error('Reset error:', err);
    } finally {
      setLoading(false);
    }
  };

  const productsList = datasetStatus?.products || [];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} apiOnline={apiOnline} />

      {/* Global Active Dataset Bar & Synchronization Control */}
      <div className="bg-slate-900 text-slate-100 border-b border-slate-800 shadow-inner">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Active Dataset Badge */}
          <div className="flex items-center space-x-2.5">
            <Database className="w-4 h-4 text-blue-400 flex-shrink-0" />
            <div className="flex items-center space-x-2">
              <span className="text-slate-400">Active Dataset:</span>
              <span className="font-semibold text-white bg-slate-800 px-2.5 py-1 rounded-md border border-slate-700">
                {datasetStatus?.name || 'Loading...'}
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                datasetStatus?.is_default
                  ? 'bg-blue-900/60 text-blue-300 border border-blue-700'
                  : 'bg-emerald-900/60 text-emerald-300 border border-emerald-700'
              }`}>
                {datasetStatus?.is_default ? 'DEFAULT' : 'USER UPLOADED'}
              </span>
            </div>
          </div>

          {/* Product Selector (Visible if dataset contains multiple products) */}
          <div className="flex items-center space-x-3">
            {datasetStatus?.has_products && productsList.length > 0 && (
              <div className="flex items-center space-x-1.5">
                <Filter className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-slate-400">Product:</span>
                <select
                  value={selectedProduct}
                  onChange={(e) => handleProductChange(e.target.value)}
                  className="bg-slate-800 text-slate-100 text-xs rounded-md border border-slate-700 px-2.5 py-1 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="all">All Products (Catalog Total)</option>
                  {productsList.map((p, idx) => (
                    <option key={idx} value={p.name}>
                      {p.name.length > 32 ? `${p.name.slice(0, 32)}...` : p.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Revert to default button */}
            {!datasetStatus?.is_default && (
              <button
                onClick={handleResetToDefault}
                className="flex items-center space-x-1 text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded-md border border-slate-700 transition-colors"
                title="Reset to default UCI Online Retail dataset"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset to Default</span>
              </button>
            )}

            {refreshing && (
              <div className="flex items-center space-x-1 text-blue-400 animate-pulse">
                <div className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                <span className="text-[11px]">Syncing...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Global Notification Toast */}
      {notification && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4 w-full">
          <div className={`p-3.5 rounded-xl border flex items-center justify-between text-xs shadow-sm transition-all ${
            notification.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : notification.type === 'error'
              ? 'bg-rose-50 border-rose-200 text-rose-800'
              : 'bg-blue-50 border-blue-200 text-blue-800'
          }`}>
            <div className="flex items-center space-x-2">
              {notification.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              )}
              <span className="font-medium">{notification.message}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="text-slate-400 hover:text-slate-600 ml-4 font-bold"
            >
              &times;
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!apiOnline && !loading && (
          <div className="mb-6 bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-xl text-xs flex items-center justify-between">
            <span>
              <strong>Note:</strong> The Flask backend appears to be offline. Start the backend by running{' '}
              <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono">python backend/app.py</code> in your VS Code terminal.
            </span>
          </div>
        )}

        {activeTab === 'overview' && (
          <HistoricalSection
            datasetStatus={datasetStatus}
            historicalData={historicalData}
            selectedProduct={selectedProduct}
            onProductChange={handleProductChange}
            loading={loading}
          />
        )}

        {activeTab === 'forecast' && (
          <ForecastSection
            forecastData={forecastData}
            datasetStatus={datasetStatus}
            selectedProduct={selectedProduct}
            days={forecastDays}
            onDaysChange={handleDaysChange}
            loading={refreshing}
          />
        )}

        {activeTab === 'inventory' && (
          <InventorySection
            inventoryData={inventoryData}
            inventoryParams={inventoryParams}
            onParamChange={handleInventoryParamChange}
            datasetStatus={datasetStatus}
            selectedProduct={selectedProduct}
            loading={refreshing}
          />
        )}

        {activeTab === 'upload' && (
          <UploadSection
            onUploadSuccess={handleUploadSuccess}
            datasetStatus={datasetStatus}
            onResetToDefault={handleResetToDefault}
          />
        )}
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <p className="font-semibold text-slate-700">
          AI-Powered Demand Forecasting & Supply Chain Optimization System
        </p>
        <p className="mt-1 text-slate-400">
          Single Source of Truth Architecture &bull; Built with React, Vite, Tailwind CSS, Scikit-Learn & Flask
        </p>
      </footer>
    </div>
  );
}
