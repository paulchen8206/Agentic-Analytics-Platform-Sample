# Simple Agentic Analytics Platform

> Turn data into insights with agentic AI powered by **Ollama** — running entirely on your local machine.

![Architecture](https://img.shields.io/badge/AI-Ollama-blue) ![Backend](https://img.shields.io/badge/Backend-FastAPI-green) ![Frontend](https://img.shields.io/badge/Frontend-React-61dafb) ![Python](https://img.shields.io/badge/Python-3.12-yellow)

---

## Features

- **Agentic Loop**: Multi-step reasoning where the AI plans, calls analytics tools, interprets results, and synthesizes insights.
- **Real-Time Streaming**: Server-Sent Events deliver thinking steps, tool calls, and the final answer as they happen.
- **7 Analytics Tools**: Describe, NL Query, Anomaly Detection, Trend Analysis, Correlation, Segmentation, and Forecasting.
- **Multi-Format Data**: Upload CSV, JSON, Parquet, and Excel files up to 100 MB.
- **Local & Private**: 100% local inference via Ollama, so your data never leaves your machine.
- **Interactive Dashboard**: React frontend with live charts, data quality reports, and chat interface.
- **Model Agnostic**: Switch between llama3.2, mistral, gemma2, qwen2.5, and other Ollama-compatible models.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│  ChatPanel ◄─── SSE Stream ──► DataVisualizer               │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP / SSE
┌───────────────────────▼─────────────────────────────────────┐
│                   FastAPI Backend                           │
│  /api/chat/stream  /api/datasets  /api/analytics/*          │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  Analytics Agent                            │
│                                                             │
│  ┌─────────┐   ┌──────────────┐   ┌────────────────────┐    │
│  │  Ollama │◄──│ Agentic Loop │──►│  Analytics Engine  │    │
│  │  LLM    │   │ (tool calls) │   │  - Describe        │    │
│  └─────────┘   └──────────────┘   │  - Anomalies       │    │
│                                   │  - Trends          │    │
│  ┌─────────────────────────────┐  │  - Correlation     │    │
│  │       Data Loader           │  │  - Segmentation    │    │
│  │  CSV / JSON / Parquet / XLS │  │  - Forecasting     │    │
│  └─────────────────────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start (Docker)

### Prerequisites

- Docker Desktop (or Docker Engine + Compose)

```bash
# Clone and enter the project
cd /path/to/Agentic-Analytics-Platform

# See all procedures
make help

# One-command startup
make start
```

> Note: `start.sh` is no longer part of this project. Use `make` procedures only.

This will:

1. Build backend/frontend images
2. Start Ollama, backend, and frontend containers
3. Expose backend on [http://localhost:8000](http://localhost:8000)
4. Expose frontend on [http://localhost:3000](http://localhost:3000)

The first startup can take several minutes because `ollama/ollama` is a large image.

`make start` waits for the Ollama container to become healthy before the backend starts.
The Compose healthcheck uses `ollama list` rather than `curl` because the upstream
`ollama/ollama` image does not include `curl`.

If startup appears stalled, check service status and Ollama logs with:

```bash
make ps
docker compose logs ollama
```

---

## Procedures (Makefile)

- `make help`: List all available procedures.
- `make start`: Start full stack in Docker (detached).
- `make stop`: Stop Docker stack.
- `make restart`: Restart Docker stack.
- `make logs`: Tail Docker logs.
- `make ps`: Show Docker service status.
- `make build`: Build Docker images.
- `make pull`: Pull latest upstream base images.
- `make test`: Run tests in Docker test container.
- `make clean`: Stop stack and remove volumes/orphans.
- `make prune`: Run clean and prune dangling images.

Legacy aliases are still available:

- `make docker-up`, `make docker-down`, `make docker-logs`, `make docker-ps`, `make docker-build`.

---

## Docker Compose

```bash
make start
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Reference

- `GET /api/datasets`: List all datasets.
- `POST /api/datasets/upload`: Upload a file.
- `GET /api/datasets/{id}/preview`: Preview rows.
- `POST /api/chat`: Chat with the AI agent (blocking).
- `POST /api/chat/stream`: Chat with the AI agent (SSE streaming).
- `POST /api/analyze/quick`: Auto-analyze a dataset.
- `GET /api/analytics/{id}/describe`: Statistical description.
- `GET /api/analytics/{id}/anomalies/{col}`: Anomaly detection.
- `GET /api/analytics/{id}/trend/{col}?time_col=`: Trend analysis.
- `GET /api/analytics/{id}/correlate?col_a=&col_b=`: Correlation.
- `GET /api/analytics/{id}/segment/{col}`: Segmentation.
- `GET /api/analytics/{id}/forecast/{col}?time_col=&periods=`: Forecasting.

---

## Sample Datasets

Three sample datasets are auto-generated on startup:

| Dataset       | Description                                        | Rows |
| ------------- | -------------------------------------------------- | ---- |
| `sales`       | Multi-region product sales with injected anomalies | 500  |
| `web_traffic` | Daily web traffic with trend and seasonality       | 365  |
| `hr_data`     | Employee records for attrition analysis            | 300  |

---

## Running Tests

```bash
make test
```

---

## Changing the Model

```bash
# Pull models inside the running Ollama container
docker exec -it app-ollama ollama pull mistral
docker exec -it app-ollama ollama pull gemma2
docker exec -it app-ollama ollama pull qwen2.5

# Then select it in the UI.
# If you want a backend default model, set OLLAMA_MODEL in docker-compose.yml
# under the backend service environment block and restart:
# make restart
```
