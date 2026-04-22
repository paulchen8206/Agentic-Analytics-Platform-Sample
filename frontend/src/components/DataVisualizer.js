import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import { TrendingUp, AlertTriangle, BarChart2, PieChart as PieIcon } from 'lucide-react';
import { api } from '../services/api';

const COLORS = ['#6366f1', '#22d3ee', '#f59e0b', '#10b981', '#ef4444', '#a78bfa'];

function StatCard({ label, value, sub }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

export default function DataVisualizer({ datasetId }) {
  const [describe, setDescribe] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (!datasetId) return;
    setLoading(true);
    api.describeDataset(datasetId)
      .then(setDescribe)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (!datasetId) return (
    <div className="visualizer-empty">
      <BarChart2 size={40} />
      <p>Select or upload a dataset to visualize</p>
    </div>
  );

  if (loading) return <div className="loading-state">Loading visualizations…</div>;
  if (!describe) return null;

  const numericCols = describe.columns.filter(c => c.mean !== undefined);
  const categoryCols = describe.columns.filter(c => c.unique_count !== undefined);

  const overviewData = numericCols.slice(0, 6).map(c => ({
    name: c.name,
    mean: c.mean?.toFixed(2),
    min: c.min?.toFixed(2),
    max: c.max?.toFixed(2),
  }));

  const missingData = Object.entries(describe.missing_values)
    .filter(([, v]) => v > 0)
    .map(([col, count]) => ({ col, count, pct: ((count / describe.shape.rows) * 100).toFixed(1) }));

  return (
    <div className="visualizer">
      <div className="stats-row">
        <StatCard label="Total Rows" value={describe.shape.rows.toLocaleString()} />
        <StatCard label="Columns" value={describe.shape.columns} />
        <StatCard label="Numeric Cols" value={numericCols.length} />
        <StatCard label="Category Cols" value={categoryCols.length} />
        <StatCard
          label="Missing Values"
          value={Object.values(describe.missing_values).reduce((a, b) => a + b, 0)}
          sub={missingData.length > 0 ? `${missingData.length} cols affected` : 'No missing data'}
        />
      </div>

      <div className="tab-bar">
        {['overview', 'distribution', 'quality'].map(t => (
          <button key={t} className={`tab ${activeTab === t ? 'active' : ''}`} onClick={() => setActiveTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && numericCols.length > 0 && (
        <div className="chart-container">
          <h4 className="chart-title"><TrendingUp size={14} /> Numeric Column Statistics</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={overviewData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3d" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #3d4466', borderRadius: 8 }} />
              <Legend />
              <Bar dataKey="mean" fill="#6366f1" radius={[4, 4, 0, 0]} name="Mean" />
              <Bar dataKey="max" fill="#22d3ee" radius={[4, 4, 0, 0]} name="Max" />
              <Bar dataKey="min" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Min" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {activeTab === 'distribution' && categoryCols.length > 0 && (
        <div className="charts-grid">
          {categoryCols.slice(0, 4).map(col => {
            const pieData = Object.entries(col.top_values || {}).map(([name, value]) => ({ name, value }));
            return (
              <div key={col.name} className="chart-container">
                <h4 className="chart-title"><PieIcon size={14} /> {col.name}</h4>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                      {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #3d4466' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            );
          })}
        </div>
      )}

      {activeTab === 'quality' && (
        <div className="quality-panel">
          <h4 className="chart-title"><AlertTriangle size={14} /> Data Quality Report</h4>
          {missingData.length === 0 ? (
            <div className="quality-ok">No missing values detected. Data quality looks good.</div>
          ) : (
            <table className="quality-table">
              <thead>
                <tr><th>Column</th><th>Missing Count</th><th>Missing %</th></tr>
              </thead>
              <tbody>
                {missingData.map(r => (
                  <tr key={r.col}>
                    <td>{r.col}</td>
                    <td>{r.count}</td>
                    <td>
                      <span className={`badge ${parseFloat(r.pct) > 20 ? 'danger' : parseFloat(r.pct) > 5 ? 'warn' : 'ok'}`}>
                        {r.pct}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h4 className="chart-title" style={{ marginTop: 24 }}>Column Summary</h4>
          <table className="quality-table">
            <thead>
              <tr><th>Column</th><th>Type</th><th>Unique / Range</th></tr>
            </thead>
            <tbody>
              {describe.columns.map(col => (
                <tr key={col.name}>
                  <td>{col.name}</td>
                  <td><span className="badge info">{col.dtype}</span></td>
                  <td>
                    {col.mean !== undefined
                      ? `${col.min?.toFixed(2)} – ${col.max?.toFixed(2)}`
                      : `${col.unique_count} unique values`
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
