import React from 'react';
import { Package, ShieldAlert, CheckCircle, AlertTriangle, HelpCircle, Layers, Tag } from 'lucide-react';
import StatCard from './StatCard';

export default function InventorySection({
  inventoryData,
  inventoryParams,
  onParamChange,
  datasetStatus,
  selectedProduct,
  loading,
}) {
  const metrics = inventoryData?.metrics || {};
  const status = inventoryData?.status || {};
  const breakdown = inventoryData?.formula_breakdown || {};
  const formatUnits = (num) => (num !== undefined && num !== null ? Number(num).toLocaleString() : '—');

  const getStatusBanner = () => {
    switch (status.code) {
      case 'CRITICAL_STOCKOUT_RISK':
        return {
          bg: 'bg-rose-50 border-rose-200 text-rose-800',
          icon: ShieldAlert,
          title: 'Critical Stockout Risk',
        };
      case 'REORDER_NOW':
        return {
          bg: 'bg-amber-50 border-amber-200 text-amber-800',
          icon: AlertTriangle,
          title: 'Reorder Point Reached — Action Required',
        };
      case 'OVERSTOCKED':
        return {
          bg: 'bg-purple-50 border-purple-200 text-purple-800',
          icon: Layers,
          title: 'Excess Inventory / Overstocked',
        };
      default:
        return {
          bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
          icon: CheckCircle,
          title: 'Stock Level Optimal',
        };
    }
  };

  const banner = getStatusBanner();
  const StatusIcon = banner.icon;

  return (
    <div className="space-y-6">
      {/* Parameter Control Panel */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
          <div>
            <h3 className="text-base font-bold text-slate-900">Supply Chain Optimization Parameters</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Simulate safety stock and reorder point requirements based on live demand variance.
            </p>
          </div>
          <div className="flex items-center space-x-1.5 text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
            <Tag className="w-3.5 h-3.5 text-blue-600" />
            <span>Scope: <strong>{selectedProduct === 'all' ? 'All Products' : selectedProduct}</strong></span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Supplier Lead Time */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Supplier Lead Time
              </label>
              <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                {inventoryParams.leadTime} Days
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="30"
              value={inventoryParams.leadTime}
              onChange={(e) => onParamChange('leadTime', Number(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400 mt-1">Vendor delivery latency in days</p>
          </div>

          {/* Service Level */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Service Level Target
            </label>
            <select
              value={inventoryParams.serviceLevel}
              onChange={(e) => onParamChange('serviceLevel', Number(e.target.value))}
              className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2 text-slate-700 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              <option value="0.90">90% (Z = 1.28 - Economy)</option>
              <option value="0.95">95% (Z = 1.65 - Standard)</option>
              <option value="0.98">98% (Z = 2.05 - High)</option>
              <option value="0.99">99% (Z = 2.33 - Critical)</option>
            </select>
            <p className="text-[11px] text-slate-400 mt-1">Desired probability of avoiding stockouts</p>
          </div>

          {/* Current Stock */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Current Stock On Hand
            </label>
            <input
              type="number"
              value={inventoryParams.currentStock}
              onChange={(e) => onParamChange('currentStock', e.target.value)}
              placeholder="e.g. 5000"
              className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2 text-slate-700 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <p className="text-[11px] text-slate-400 mt-1">Units physically present in warehouse</p>
          </div>

          {/* Target Stock */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Target Stock (Optional)
            </label>
            <input
              type="number"
              value={inventoryParams.targetStock}
              onChange={(e) => onParamChange('targetStock', e.target.value)}
              placeholder="Auto-calculated if empty"
              className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2 text-slate-700 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <p className="text-[11px] text-slate-400 mt-1">Max inventory ceiling</p>
          </div>
        </div>
      </div>

      {/* Dynamic Status Alert Banner */}
      {status.description && (
        <div className={`p-4 rounded-xl border flex items-start space-x-3 ${banner.bg}`}>
          <StatusIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-bold">{banner.title}</h4>
            <p className="text-xs mt-0.5">{status.description}</p>
          </div>
        </div>
      )}

      {/* Inventory Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Safety Stock"
          value={`${formatUnits(metrics.safety_stock)} units`}
          subtitle={`Buffer for ${inventoryData?.inputs?.service_level || '95%'} service`}
          icon={ShieldAlert}
          color="amber"
        />
        <StatCard
          title="Reorder Point (ROP)"
          value={`${formatUnits(metrics.reorder_point)} units`}
          subtitle="Trigger order when stock hits this level"
          icon={AlertTriangle}
          color="rose"
        />
        <StatCard
          title="Suggested Replenishment"
          value={`${formatUnits(metrics.suggested_replenishment_quantity)} units`}
          subtitle="Recommended purchase order size"
          icon={Package}
          color={metrics.suggested_replenishment_quantity > 0 ? 'green' : 'blue'}
        />
        <StatCard
          title="Days of Supply"
          value={metrics.days_of_supply !== null && metrics.days_of_supply !== undefined ? `${metrics.days_of_supply} Days` : '—'}
          subtitle="Inventory coverage at average run-rate"
          icon={Layers}
          color="purple"
        />
      </div>

      {/* Mathematical Formula Explanation Card */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-2 mb-4">
          <HelpCircle className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-bold text-slate-900">Explainable Optimization Formulas (Active Dataset Values)</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
            <span className="font-bold text-slate-800 block mb-1">1. Lead Time Demand (LTD)</span>
            <code className="text-blue-700 bg-blue-50 px-1 py-0.5 rounded text-[11px] block mb-2 font-mono">
              LTD = D_avg × Lead Time
            </code>
            <p className="text-slate-600">{breakdown.lead_time_demand || 'Expected demand during vendor shipping'}</p>
          </div>

          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
            <span className="font-bold text-slate-800 block mb-1">2. Safety Stock (SS)</span>
            <code className="text-blue-700 bg-blue-50 px-1 py-0.5 rounded text-[11px] block mb-2 font-mono">
              SS = Z × σ_demand × √(Lead Time)
            </code>
            <p className="text-slate-600">{breakdown.safety_stock || 'Buffer against unexpected demand surges'}</p>
          </div>

          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
            <span className="font-bold text-slate-800 block mb-1">3. Reorder Point (ROP)</span>
            <code className="text-blue-700 bg-blue-50 px-1 py-0.5 rounded text-[11px] block mb-2 font-mono">
              ROP = LTD + Safety Stock
            </code>
            <p className="text-slate-600">{breakdown.reorder_point || 'Inventory threshold to trigger replenishment'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
