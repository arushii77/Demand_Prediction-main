import React from 'react';
import { BarChart3, TrendingUp, Package, UploadCloud } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, apiOnline }) {
  const tabs = [
    { id: 'overview', label: 'Overview & Historical', icon: BarChart3 },
    { id: 'forecast', label: 'Future Forecast', icon: TrendingUp },
    { id: 'inventory', label: 'Inventory Optimization', icon: Package },
    { id: 'upload', label: 'Dataset Upload', icon: UploadCloud },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Project Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 flex-shrink-0">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight leading-snug">
                AI-Powered Demand Forecasting & Supply Chain Optimization System
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">Machine Learning Forecasting & Dynamic Inventory Engine</p>
            </div>
          </div>

          {/* API Health Status Badge */}
          <div className="hidden sm:flex items-center space-x-2 bg-slate-100 px-3 py-1.5 rounded-full text-xs font-medium flex-shrink-0">
            <span className={`w-2.5 h-2.5 rounded-full ${apiOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <span className={apiOnline ? 'text-slate-700' : 'text-rose-600'}>
              {apiOnline ? 'Backend Online (Port 5000)' : 'Backend Offline'}
            </span>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 sm:space-x-3 overflow-x-auto py-2 -mb-px">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 shadow-sm font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
