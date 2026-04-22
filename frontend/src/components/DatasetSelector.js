import React, { useEffect, useState, useRef } from 'react';
import { Upload, Database, ChevronDown, Check, Plus } from 'lucide-react';
import { api } from '../services/api';

export default function DatasetSelector({ selectedId, onSelect }) {
  const [datasets, setDatasets] = useState([]);
  const [open, setOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef();
  const dropRef = useRef();

  const refresh = () => {
    api.listDatasets().then(r => setDatasets(r.datasets)).catch(() => {});
  };

  useEffect(() => { refresh(); }, []);

  const handleFile = async (file) => {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const result = await api.uploadDataset(file);
      refresh();
      onSelect(result.dataset_id);
      setOpen(false);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const selected = datasets.find(d => d.id === selectedId);

  return (
    <div className="dataset-selector">
      <button className="ds-trigger" onClick={() => setOpen(!open)}>
        <Database size={16} />
        <span>{selected ? selected.name : 'Select Dataset'}</span>
        <ChevronDown size={14} />
      </button>

      {open && (
        <div className="ds-dropdown">
          {/* Upload area */}
          <div
            ref={dropRef}
            className="ds-upload-zone"
            onDragOver={e => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileRef.current.click()}
          >
            {uploading
              ? <span>Uploading…</span>
              : <><Upload size={16} /><span>Drop CSV / JSON / Parquet / Excel here or click</span></>
            }
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.json,.parquet,.xlsx,.xls"
            style={{ display: 'none' }}
            onChange={e => handleFile(e.target.files[0])}
          />
          {error && <div className="ds-error">{error}</div>}

          {/* Dataset list */}
          {datasets.length > 0 && (
            <div className="ds-list">
              {datasets.map(d => (
                <button
                  key={d.id}
                  className={`ds-item ${d.id === selectedId ? 'active' : ''}`}
                  onClick={() => { onSelect(d.id); setOpen(false); }}
                >
                  <Database size={14} />
                  <span className="ds-item-name">{d.name}</span>
                  <span className="ds-item-badge">{d.source}</span>
                  {d.id === selectedId && <Check size={14} className="ds-check" />}
                </button>
              ))}
            </div>
          )}

          {datasets.length === 0 && !uploading && (
            <div className="ds-empty">No datasets yet. Upload one above.</div>
          )}
        </div>
      )}
    </div>
  );
}
