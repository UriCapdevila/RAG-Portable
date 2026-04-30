# RAG Portable

Asistente RAG **100% local** y **OSS-first**, con personalidad tuneable (personas), framework de herramientas extensible, retrieval híbrido, observabilidad por etapa y arquitectura Ports & Adapters lista para crecer.

> Pensado para correr completamente en la máquina del usuario y permitir reemplazar modelos, vector store, reranker u otros componentes sin reescribir el núcleo.

## Stack

- **FastAPI** — API y servidor estático.
- **Ollama** — motor local de inferencia (LLM + embeddings).
- **LlamaIndex** — utilidades de loaders/indexación.
- **LanceDB** — vector store persistente en disco.
- **SQLite** — persistencia liviana (settings, manifest de ingesta, traces).
- **Pydantic / pydantic-settings** — configuración tipada.
- **structlog** — logging estructurado por request.
- **sentence-transformers** *(opcional)* — reranker cross-encoder local.
- **React + Vite + Tailwind CSS** — UI desacoplada del backend.

Toda dependencia que no es local-first es opcional y se activa por flag.

## Estructura

```text
data/
  raw/                # Documentos fuente (PDF, TXT, MD, CSV, DOCX, HTML, EPUB)
  vector_db/          # Persistencia local de LanceDB
  sql_db/app.db       # SQLite: app_settings, ingest_manifest, traces, trace_stages
  eval/               # Set de evaluación + corridas

app/
  main.py             # App FastAPI, middlewares, exception handlers
  api/routes.py       # Endpoints HTTP (capa fina de transporte)

  core/
    config.py         # AppSettings (pydantic-settings)
    container.py      # Composición de dependencias (lru_cache)
    db.py             # Bootstrap SQLite + tablas
    errors.py         # Errores tipados (AppError, OllamaError, ...)
    logging.py        # structlog + middleware request_id
    prompts.py        # build_system_prompt(persona) + build_user_prompt()

  ports/              # Interfaces Protocol-based
    llm.py
    embeddings.py
    vector_store.py
    keyword_index.py
    reranker.py
    tool.py

  adapters/           # Implementaciones concretas
    llm/ollama.py
    embeddings/ollama.py
    vector_store/lancedb.py
    reranker/passthrough.py
    reranker/cross_encoder.py
    loaders/registry.py

  personas/           # Personas YAML (slug, tono, parámetros, allowed_tools)
    default.yaml
    enterprise-analyst.yaml
    developer-helper.yaml
    friendly-tutor.yaml

  services/
    chat.py           # Orquestador de chat (small-talk + RAG)
    ingestion.py      # Ingesta incremental con manifest sha256+mtime
    chunking.py       # Recursive chunker
    preprocessing.py  # InputNormalizer
    workspace.py      # Inventario de fuentes
    personas.py       # PersonaService (CRUD YAML + persona activa)
    query_processor.py# Reescritura / HyDE
    fusion.py         # Reciprocal Rank Fusion
    grounding_validator.py
    intent_detector.py# Detector de small-talk
    tool_dispatcher.py# Loop ReAct mínimo
    tracing.py        # TraceService (timings + métricas)
    tools/
      registry.py
      builtin.py      # list_sources, get_document
    models.py

  tools/evaluate.py   # Evaluador (scaffold)

frontend/
  src/                # UI React
  dist/               # Build servido por FastAPI
```

## Puesta en marcha

1. Instalá y arrancá Ollama.
2. Descargá los modelos:

```bash
ollama pull gemma3:latest
ollama pull nomic-embed-text:latest
```

3. Creá el venv e instalá dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Colocá documentos en `data/raw/` (PDF, TXT, MD, CSV, DOCX, HTML, EPUB).
5. Arrancá la app:

Windows:
```powershell
.\start.bat
```

Linux / macOS:
```bash
./start.sh
```

6. Abrí [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Desarrollo del frontend

- Dev frontend: `npm --prefix frontend run dev`
- Build frontend: `npm --prefix frontend run build`
- El backend expone `/api/*` y sirve `frontend/dist` cuando existe.

## Variables de entorno (.env)

Todas son opcionales y tienen default razonable. Ver `.env.example`.

| Variable | Default | Descripción |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL del runtime Ollama |
| `OLLAMA_CHAT_MODEL` | `gemma3:latest` | Modelo para generación |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text:latest` | Modelo para embeddings |
| `APP_HOST` / `APP_PORT` | `127.0.0.1` / `8000` | Binding del backend |
| `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` | `1200` / `180` | Tamaño/overlap de chunks |
| `RAG_TOP_K` | `4` | Default si la persona no lo sobreescribe |
| `RAG_VECTOR_TABLE` | `document_chunks` | Tabla LanceDB |
| `RAG_RERANKER_ENABLED` | `false` | Activa cross-encoder local |
| `RAG_RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Modelo de rerank |
| `RAG_GROUNDING_THRESHOLD` | `0.15` | Umbral por defecto (la persona puede sobreescribir) |
| `RAG_MAX_REACT_STEPS` | `3` | Iteraciones máximas del ToolDispatcher |

## Endpoints principales

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/sources`
- `POST /api/sources/upload`
- `POST /api/sources/delete`
- `POST /api/ingestion/run`
- `POST /api/chat`
- `GET /api/personas`
- `GET /api/personas/active`
- `POST /api/personas/active`
- `POST /api/personas`
- `GET /api/traces`
- `GET /api/metrics`

## Documentación adicional

- [docs/architecture.md](docs/architecture.md) — visión arquitectónica y principios de diseño.
- [docs/system-skeleton.md](docs/system-skeleton.md) — esqueleto detallado del sistema, prompts, flujos y observabilidad.
