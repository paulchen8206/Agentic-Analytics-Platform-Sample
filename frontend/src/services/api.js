const API_BASE = process.env.REACT_APP_API_URL || '';

export const api = {
  async listDatasets() {
    const res = await fetch(`${API_BASE}/api/datasets`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async uploadDataset(file) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE}/api/datasets/upload`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async previewDataset(datasetId, rows = 20) {
    const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/preview?rows=${rows}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async chat(message, datasetId, history = [], model = 'llama3.2') {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, dataset_id: datasetId, history, model }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async *chatStream(message, datasetId, history = [], model = 'llama3.2') {
    const res = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, dataset_id: datasetId, history, model }),
    });
    if (!res.ok) throw new Error(await res.text());

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          try { yield JSON.parse(data); } catch { /* skip */ }
        }
      }
    }
  },

  async describeDataset(datasetId) {
    const res = await fetch(`${API_BASE}/api/analytics/${datasetId}/describe`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async quickAnalyze(datasetId, model = 'llama3.2') {
    const res = await fetch(`${API_BASE}/api/analyze/quick`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id: datasetId, model }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};
