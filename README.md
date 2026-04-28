# RAG Portable

Base inicial para un asistente RAG local con arquitectura limpia, pensado para correr completamente en la maquina del usuario y permitir cambios de modelo o vector store con impacto minimo.

## Stack

- `FastAPI` para la API y el punto de entrada web.
- `Ollama` como motor local de inferencia.
- `LlamaIndex` para la orquestación de embeddings e indexación.
- `LanceDB` como vector store persistente en disco.
- `SQLite` reservado para la fase 2 de datos estructurados.
- `React + Vite + Tailwind CSS` para una interfaz escalable, responsive y desacoplada del backend.

## Estructura

```text
data/
  raw/              # PDFs, TXTs, MDs y otros archivos fuente
  vector_db/        # Persistencia local de LanceDB
  sql_db/           # Espacio reservado para SQLite
app/
  core/
    config.py       # Configuración y paths
    prompts.py      # Prompt base del asistente RAG
  services/
    chunking.py     # Chunking recursivo orientado a estructura
    ingestion.py    # Lectura, chunking, embeddings e indexación
    chat.py         # Recuperación + síntesis con Ollama
    models.py       # Modelos internos de servicio
    ollama_client.py
  api/
    routes.py       # Endpoints HTTP
  main.py           # App FastAPI y archivos estáticos
frontend/
  src/              # UI en React
  dist/             # Build servido por FastAPI
requirements.txt
start.bat
start.sh
```

## Puesta en marcha

1. Instala y arranca Ollama.
2. Descarga los modelos que usará la app:

```bash
ollama pull gemma3:latest
ollama pull nomic-embed-text:latest
```

3. Coloca documentos en [data/raw](D:/Github/RAG-Portable/data/raw).
4. Arranca la aplicación:

Windows:

```powershell
.\start.bat
```

Linux / macOS:

```bash
./start.sh
```

5. Abre [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Desarrollo del frontend

- Dev frontend: `npm --prefix frontend run dev`
- Build frontend: `npm --prefix frontend run build`
- El backend expone `/api/*` y sirve `frontend/dist` cuando existe.

## Endpoints principales

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/sources`
- `POST /api/sources/upload`
- `POST /api/ingestion/run`
- `POST /api/chat`

## Notas de arquitectura

- La capa de `ingestion` solo se ocupa de transformar documentos en chunks con metadatos y persistirlos en LanceDB.
- La capa de `chat` solo se ocupa de recuperar contexto y pedirle a Ollama una respuesta grounded.
- La capa `workspace` alimenta el frontend con inventario de fuentes y estado general del studio.
- FastAPI queda como una capa fina de transporte.
- El acceso a Ollama está desacoplado en `ollama_client.py`, lo que deja preparado el reemplazo por otro proveedor.
- `data/sql_db/` queda reservado para incorporar la fase SQL sin mezclarla con la lógica RAG.
