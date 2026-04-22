import React, { useState } from 'react';
import { Brain, BarChart2, MessageSquare, Zap, Settings } from 'lucide-react';
import ChatPanel from './components/ChatPanel';
import DataVisualizer from './components/DataVisualizer';
import DatasetSelector from './components/DatasetSelector';
import './App.css';

const MODELS = ['llama3.2', 'llama3.1', 'mistral', 'gemma2', 'qwen2.5'];

function App() {
  const [activeDataset, setActiveDataset] = useState(null);
  const [activeView, setActiveView] = useState('chat');
  const [model, setModel] = useState('llama3.2');
  const [showModelPicker, setShowModelPicker] = useState(false);

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Brain size={28} className="logo-icon" />
          <div>
            <div className="logo-title">Agentic Analytics</div>
            <div className="logo-sub">Powered by Ollama</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeView === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveView('chat')}
          >
            <MessageSquare size={18} /> Chat & Insights
          </button>
          <button
            className={`nav-item ${activeView === 'visualize' ? 'active' : ''}`}
            onClick={() => setActiveView('visualize')}
          >
            <BarChart2 size={18} /> Visualizations
          </button>
        </nav>

        <div className="sidebar-section">
          <div className="sidebar-section-label">Dataset</div>
          <DatasetSelector selectedId={activeDataset} onSelect={setActiveDataset} />
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">
            <Settings size={12} /> Model
          </div>
          <div className="model-selector">
            <button className="model-btn" onClick={() => setShowModelPicker(!showModelPicker)}>
              <Zap size={14} /> {model}
            </button>
            {showModelPicker && (
              <div className="model-dropdown">
                {MODELS.map(m => (
                  <button
                    key={m}
                    className={`model-option ${m === model ? 'active' : ''}`}
                    onClick={() => { setModel(m); setShowModelPicker(false); }}
                  >
                    {m}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <span>Ollama connected</span>
        </div>
      </aside>

      {/* Main content */}
      <main className="main-content">
        <header className="topbar">
          <div className="topbar-title">
            {activeView === 'chat' ? 'AI Data Analyst' : 'Data Visualizations'}
            {activeDataset && <span className="topbar-dataset">→ {activeDataset}</span>}
          </div>
          {activeDataset && (
            <div className="topbar-actions">
              <span className="dataset-badge">{activeDataset}</span>
            </div>
          )}
        </header>

        <div className="content-area">
          {activeView === 'chat' && (
            <ChatPanel datasetId={activeDataset} model={model} />
          )}
          {activeView === 'visualize' && (
            <DataVisualizer datasetId={activeDataset} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
