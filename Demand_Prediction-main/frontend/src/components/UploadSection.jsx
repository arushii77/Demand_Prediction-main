import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, Download, ArrowRight, ShieldCheck, Database, Layers } from 'lucide-react';
import StatCard from './StatCard';

export default function UploadSection({
  onUploadSuccess,
  datasetStatus,
  onResetToDefault,
}) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUploaded, setLastUploaded] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a CSV or Excel file first.');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Failed to process dataset');
      }

      setLastUploaded(data);
      // Synchronize entire app!
      if (onUploadSuccess) {
        onUploadSuccess(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const downloadSample = () => {
    window.location.href = '/api/sample-data';
  };

  const formatUnits = (num) => (num !== undefined && num !== null ? Number(num).toLocaleString() : '—');
  const formatCurrency = (num) => (num !== undefined && num !== null ? `$${Number(num).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—');

  return (
    <div className="space-y-6">
      {/* Upload Box */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-900">Upload Sales & Demand Dataset</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload retail sales logs (.csv or .xlsx) to dynamically synchronize all dashboard forecasting and inventory sections.
            </p>
          </div>
          <button
            onClick={downloadSample}
            type="button"
            className="flex items-center space-x-1.5 text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg border border-blue-200 transition-colors flex-shrink-0"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Sample CSV</span>
          </button>
        </div>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-300 hover:border-blue-400 rounded-xl p-8 text-center transition-colors">
            <UploadCloud className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <div className="text-sm text-slate-600">
              <label className="font-semibold text-blue-600 hover:text-blue-500 cursor-pointer">
                <span>Browse file from computer</span>
                <input
                  type="file"
                  accept=".csv, .xlsx, .xls"
                  onChange={handleFileChange}
                  className="sr-only"
                />
              </label>
              <span className="text-slate-400"> or drag and drop</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Supports CSV / Excel containing <strong>date</strong> and <strong>quantity/demand</strong> columns. Optional: product, category, price, revenue.
            </p>

            {file && (
              <div className="mt-4 inline-flex items-center space-x-2 bg-blue-50 text-blue-700 text-xs font-medium px-3.5 py-1.5 rounded-full border border-blue-200">
                <FileText className="w-4 h-4" />
                <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-center gap-3 pt-2">
            {!datasetStatus?.is_default && onResetToDefault && (
              <button
                type="button"
                onClick={onResetToDefault}
                className="text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3.5 py-2 rounded-lg transition-colors"
              >
                ↺ Revert to Default (UCI Online Retail)
              </button>
            )}

            <button
              type="submit"
              disabled={uploading || !file}
              className="ml-auto flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-5 py-2.5 rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              <span>{uploading ? 'Validating & Synchronizing...' : 'Upload & Synchronize Dashboard'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-4 bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-start space-x-3 text-xs leading-relaxed">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
            <div>
              <p className="font-bold">Dataset Validation Failed</p>
              <p className="mt-0.5">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation of Active Dataset */}
      {datasetStatus && (
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                Current Active Dataset: {datasetStatus.name}
              </h4>
              <p className="text-xs text-slate-500">
                Status: {datasetStatus.is_default ? 'Default UCI Online Retail Dataset' : 'Custom Uploaded Dataset'} &bull; All 4 dashboard sections are synchronized.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
            <StatCard
              title="Recorded Days"
              value={`${datasetStatus.summary?.total_days || 0} Days`}
              subtitle={`${datasetStatus.date_range?.start || '—'} to ${datasetStatus.date_range?.end || '—'}`}
              icon={Database}
              color="blue"
            />
            <StatCard
              title="Total Demand"
              value={`${formatUnits(datasetStatus.summary?.total_demand)} units`}
              subtitle={`Avg ${formatUnits(datasetStatus.summary?.average_daily_demand)} units/day`}
              icon={FileText}
              color="green"
            />
            <StatCard
              title="Products Catalog"
              value={`${datasetStatus.product_count || 1} Products`}
              subtitle={datasetStatus.has_products ? 'Individual product forecasting active' : 'Catalog aggregate'}
              icon={Layers}
              color="purple"
            />
            <StatCard
              title="Model Evaluation"
              value={datasetStatus.evaluation?.mae ? `MAE: ${formatUnits(datasetStatus.evaluation?.mae)}` : 'Baseline'}
              subtitle={datasetStatus.evaluation?.test_days > 0 ? `Held-out test split (${datasetStatus.evaluation?.test_days} days)` : '< 10 days'}
              icon={ShieldCheck}
              color="amber"
            />
          </div>
        </div>
      )}
    </div>
  );
}
