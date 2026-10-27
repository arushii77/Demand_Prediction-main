import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, Calendar, Zap, AlertTriangle, ArrowUpRight, ArrowDownRight, Tag } from 'lucide-react';
import StatCard from './StatCard';

export default function ForecastSection({
  forecastData,
  datasetStatus,
  selectedProduct,
  days,
  onDaysChange,
  loading,
}) {
  const [customDays, setCustomDays] = useState(days || 14);
  const [startDate, setStartDate] = useState('');

  const summary = forecastData?.summary || {};
  const points = forecastData?.forecast || [];
  const formatUnits = (num) => (num !== undefined && num !== null ? Number(num).toLocaleString() : '—');

  const handleApply = (e) => {
    e.preventDefault();
    onDaysChange(customDays, startDate);
  };

  return (
    <div className="space-y-6">
      {/* Control Bar */}
      <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
        <form onSubmit={handleApply} className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5">
              Forecast Horizon
            </label>
            <div className="flex rounded-lg bg-slate-100 p-1 space-x-1">
              {[7, 14, 30, 60].map((d) => (
                <button
                  type="button"
                  key={d}
                  onClick={() => {
                    setCustomDays(d);
                    onDaysChange(d, startDate);
                  }}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                    customDays === d
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {d} Days
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5">
              Custom Start Date (Optional)
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors disabled:opacity-50"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{loading ? 'Forecasting...' : 'Update Forecast'}</span>
          </button>
        </form>
      </div>

      {/* Target scope pill */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center space-x-2 text-xs text-slate-600">
          <Tag className="w-4 h-4 text-blue-600" />
          <span>
            Forecasting for:{' '}
            <strong className="text-slate-900">
              {selectedProduct === 'all' ? 'All Products (Catalog Aggregate)' : selectedProduct}
            </strong>
          </span>
          <span className="text-slate-400">&bull;</span>
          <span>Active Dataset: <strong>{datasetStatus?.name}</strong></span>
        </div>
      </div>

      {/* Forecast KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Forecasted Demand"
          value={`${formatUnits(summary.total_demand)} units`}
          subtitle={`Over next ${customDays} days`}
          icon={TrendingUp}
          color="blue"
        />
        <StatCard
          title="Average Daily Demand"
          value={`${formatUnits(summary.average_daily_demand)} units/day`}
          subtitle="Expected daily run-rate"
          icon={Calendar}
          color="green"
        />
        <StatCard
          title="Peak Demand Day"
          value={summary.peak_day ? `${formatUnits(summary.peak_day.predicted_demand)} units` : '—'}
          subtitle={summary.peak_day ? `${summary.peak_day.day_name} (${summary.peak_day.date})` : '—'}
          icon={ArrowUpRight}
          color="amber"
        />
        <StatCard
          title="Lowest Demand Day"
          value={summary.lowest_day ? `${formatUnits(summary.lowest_day.predicted_demand)} units` : '—'}
          subtitle={summary.lowest_day ? `${summary.lowest_day.day_name} (${summary.lowest_day.date})` : '—'}
          icon={ArrowDownRight}
          color="purple"
        />
      </div>

      {/* Forecast Chart */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Future Demand Predictions
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Projected daily requirements from {forecastData?.period?.start || '—'} to {forecastData?.period?.end || '—'}
            </p>
          </div>
          <span className="text-xs bg-indigo-50 text-indigo-700 font-semibold px-3 py-1 rounded-full border border-indigo-100">
            Random Forest Ensemble
          </span>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={points} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="date"
                stroke="#94a3b8"
                fontSize={11}
                tickFormatter={(val) => (val ? val.slice(5) : '')}
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={11}
                tickFormatter={(val) => (val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)}
              />
              <Tooltip
                formatter={(val) => [`${Number(val).toLocaleString()} units`, 'Predicted Demand']}
                labelFormatter={(label) => `Forecast Date: ${label}`}
                contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
              />
              <Legend verticalAlign="top" height={36} />
              <Bar
                dataKey="predicted_demand"
                name="Predicted Daily Demand"
                fill="#3b82f6"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Daily Breakdown Table */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-4">Detailed Daily Forecast Schedule</h3>
        <div className="overflow-x-auto max-h-64">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50 text-slate-700 uppercase font-semibold sticky top-0 border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Date</th>
                <th className="py-2.5 px-4">Day of Week</th>
                <th className="py-2.5 px-4 text-right">Predicted Demand (Units)</th>
                <th className="py-2.5 px-4 text-right">Run-Rate vs Average</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {points.map((pt, idx) => {
                const diff = summary.average_daily_demand
                  ? ((pt.predicted_demand - summary.average_daily_demand) / summary.average_daily_demand) * 100
                  : 0;
                return (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2 px-4 font-medium text-slate-900">{pt.date}</td>
                    <td className="py-2 px-4">{pt.day_name}</td>
                    <td className="py-2 px-4 text-right font-semibold text-blue-600">
                      {Number(pt.predicted_demand).toLocaleString()}
                    </td>
                    <td className="py-2 px-4 text-right">
                      <span className={`inline-flex items-center text-[11px] font-semibold ${diff >= 0 ? 'text-emerald-600' : 'text-slate-500'}`}>
                        {diff >= 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
