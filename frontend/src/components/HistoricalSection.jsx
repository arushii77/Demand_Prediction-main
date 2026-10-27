import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Calendar, Database, CheckCircle2, AlertCircle, DollarSign, Layers } from 'lucide-react';
import StatCard from './StatCard';

export default function HistoricalSection({
  datasetStatus,
  historicalData,
  selectedProduct,
  onProductChange,
  loading,
}) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-500">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium">Loading dataset & historical demand...</p>
      </div>
    );
  }

  const summary = historicalData?.summary || datasetStatus?.summary || {};
  const evaluation = datasetStatus?.evaluation || {};
  const history = historicalData?.history || [];
  const testComparison = historicalData?.actual_vs_predicted || [];
  const products = datasetStatus?.products || [];
  const hasRevenue = datasetStatus?.has_revenue && summary.total_revenue;

  // Format numbers nicely
  const formatUnits = (num) => (num !== undefined && num !== null ? Number(num).toLocaleString() : '—');
  const formatCurrency = (num) => (num !== undefined && num !== null ? `$${Number(num).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—');

  // Downsample if dataset has more than 180 points for smooth charting
  const displayHistory = history.length > 180
    ? history.filter((_, idx) => idx % Math.ceil(history.length / 120) === 0 || idx === history.length - 1)
    : history;

  return (
    <div className="space-y-6">
      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Recorded Demand"
          value={`${formatUnits(summary.total_demand)} units`}
          subtitle={`${historicalData?.date_range?.start || '—'} to ${historicalData?.date_range?.end || '—'}`}
          icon={Database}
          badge={`${historicalData?.total_days || summary.total_days || 0} Days`}
          color="blue"
        />

        <StatCard
          title="Average Daily Demand"
          value={`${formatUnits(summary.average_daily_demand)} units/day`}
          subtitle={`Std Dev: ±${formatUnits(summary.demand_std)} units`}
          icon={Calendar}
          color="green"
        />

        {hasRevenue ? (
          <StatCard
            title="Total Revenue Recorded"
            value={formatCurrency(summary.total_revenue)}
            subtitle="Calculated from unit sales & price"
            icon={DollarSign}
            color="amber"
          />
        ) : (
          <StatCard
            title="Product Catalog"
            value={`${datasetStatus?.product_count || 1} Products`}
            subtitle={datasetStatus?.has_categories ? `${datasetStatus?.categories?.length || 0} Categories` : 'Unit-level retail demand'}
            icon={Layers}
            color="purple"
          />
        )}

        <StatCard
          title="Model Accuracy (MAE / RMSE)"
          value={evaluation.mae ? `${Number(evaluation.mae).toLocaleString()} / ${Number(evaluation.rmse).toLocaleString()}` : 'N/A'}
          subtitle={evaluation.test_days > 0 ? `Held-out test split (${evaluation.test_days} days)` : 'Requires 10+ historical days'}
          icon={AlertCircle}
          badge="Random Forest"
          color={evaluation.mae ? 'amber' : 'purple'}
        />
      </div>

      {/* Main Historical Demand Trend Chart */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              Historical Daily Demand Trend
              {selectedProduct !== 'all' && (
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700">
                  {selectedProduct}
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Daily units sold from {historicalData?.date_range?.start || 'start'} to {historicalData?.date_range?.end || 'end'} ({datasetStatus?.name})
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs bg-slate-100 text-slate-700 font-semibold px-3 py-1 rounded-full border border-slate-200">
              {history.length} Daily Observations
            </span>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={displayHistory} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
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
                formatter={(val, name) => [
                  name === 'Daily Revenue' ? `$${Number(val).toLocaleString()}` : `${Number(val).toLocaleString()} units`,
                  name,
                ]}
                labelFormatter={(label) => `Date: ${label}`}
                contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
              />
              <Legend verticalAlign="top" height={36} />
              <Line
                type="monotone"
                dataKey="demand"
                name="Actual Daily Demand"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5 }}
              />
              {hasRevenue && (
                <Line
                  type="monotone"
                  dataKey="revenue"
                  name="Daily Revenue"
                  stroke="#f59e0b"
                  strokeWidth={1.5}
                  dot={false}
                  yAxisId="right"
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Model Evaluation: Genuine Held-Out Test Actual vs Predicted */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Model Evaluation: Actual vs Predicted Demand
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {evaluation.description || 'Strict chronological train/test split (Zero future data leakage)'}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs bg-emerald-50 text-emerald-700 font-semibold px-3 py-1 rounded-full border border-emerald-100">
              {evaluation.test_days > 0 ? `Held-out Test Set (${evaluation.test_days} Days)` : 'Baseline Mode'}
            </span>
          </div>
        </div>

        {testComparison.length > 0 ? (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={testComparison} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
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
                  formatter={(val, name) => [`${Number(val).toLocaleString()} units`, name]}
                  labelFormatter={(label) => `Test Date: ${label}`}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                />
                <Legend verticalAlign="top" height={36} />
                <Line
                  type="monotone"
                  dataKey="actual"
                  name="Actual Test Demand"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  name="Random Forest Predicted"
                  stroke="#16a34a"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="py-12 text-center text-xs text-slate-500 bg-slate-50 rounded-lg border border-slate-100">
            <AlertCircle className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="font-semibold text-slate-700">Chronological Split Not Applicable</p>
            <p className="mt-1 max-w-md mx-auto text-slate-500">
              The active dataset contains {history.length} calendar days. A minimum of 10 days is required to establish a valid 80% train / 20% test chronological split without data leakage.
            </p>
          </div>
        )}
      </div>

      {/* Top Products Table (If Multi-Product Dataset) */}
      {datasetStatus?.has_products && products.length > 0 && (
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Top Products in Active Dataset</h3>
              <p className="text-xs text-slate-500">Sorted by cumulative unit demand</p>
            </div>
            {selectedProduct !== 'all' && (
              <button
                onClick={() => onProductChange('all')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md"
              >
                Clear Filter (View All Products)
              </button>
            )}
          </div>

          <div className="overflow-x-auto max-h-56">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 text-slate-700 uppercase font-semibold sticky top-0 border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Product Name</th>
                  <th className="py-2.5 px-4 text-right">Total Units Sold</th>
                  <th className="py-2.5 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {products.slice(0, 15).map((p, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2 px-4 font-medium text-slate-900">{p.name}</td>
                    <td className="py-2 px-4 text-right font-semibold text-blue-600">
                      {formatUnits(p.total_units)}
                    </td>
                    <td className="py-2 px-4 text-center">
                      <button
                        onClick={() => onProductChange(p.name)}
                        className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors ${
                          selectedProduct === p.name
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-100 text-slate-700 hover:bg-blue-50 hover:text-blue-600'
                        }`}
                      >
                        {selectedProduct === p.name ? 'Active' : 'Analyze'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
