# Arquitectura End-to-End de RAG-Portable (RAG de Primer Nivel)

## Visión General
RAG-Portable es una aplicación diseñada para ofrecer una experiencia de Generación Aumentada por Recuperación (RAG) de **primer nivel**, completamente local. Esta arquitectura avanzada está diseñada para ser escalable, modular y compatible con futuras herramientas, asegurando una normalización rigurosa en cada etapa del pipeline.

## Stack Tecnológico Base

### Frontend (Interfaz de Usuario)
- **React + Vite**: Single Page Application (SPA) extremadamente rápida y reactiva.
- **Tailwind CSS**: Diseño visual responsivo y moderno.
- **Desacoplamiento Front-Back**: Interactúa exclusivamente mediante API REST, permitiendo servir los estáticos desde FastAPI en producción.

### Backend (Lógica y Orquestación)
- **FastAPI**: Capa de transporte asíncrona que coordina los flujos de IA.
- **LlamaIndex**: Motor orquestador de RAG.
- **Ollama**: Motor de inferencia local (`gemma3` para LLM, `nomic-embed-text` para Embeddings).

### Capa de Datos (Persistencia)
- **LanceDB**: Base de datos vectorial local para búsquedas ultrarrápidas (`data/vector_db/`).
- **SQLite (Fase 2)**: Almacenamiento estructurado (`data/sql_db/`).

---

## Flujos de Datos y Normalización (Advanced RAG Pipeline)

Para superar las limitaciones de un MVP tradicional, la arquitectura implementa una normalización estricta a través de cinco pilares fundamentales:

### 1. Preprocesamiento y Limpieza de Datos (Input Normalization)
El primer paso asegura que la información entrante sea consistente y de alta calidad antes de su procesamiento:
- **Limpieza de texto**: Eliminación proactiva de ruido mediante sanitización (remoción de caracteres especiales, pies de página repetitivos, avisos legales y fechas irrelevantes).
- **Conversión de formatos**: Transformación de todos los documentos fuente (PDFs, DOCX, HTML) a un formato de texto plano normalizado (UTF-8) para evitar cualquier artefacto de codificación.
- **Procesamiento de tablas e imágenes**: Integración en la capa de servicios de motores OCR (Reconocimiento Óptico de Caracteres) para extraer texto incrustado en imágenes y transformar tablas complejas a formatos semánticamente legibles por el LLM (como Markdown estructurado o CSV).

### 2. Segmentación Eficiente (Chunking Strategy)
Para garantizar que la búsqueda vectorial sea precisa y eficiente, los datos preprocesados se dividen de manera inteligente:
- **Estructura Jerárquica**: Los fragmentos respetan la topología del documento original (títulos, subtítulos, párrafos) utilizando *splitters* conscientes de la estructura, en lugar de realizar cortes ciegos.
- **Tamaño Óptimo normalizado**: Segmentación en tamaños consistentes y testeados (ej. 512 o 1024 tokens) que equilibran la granularidad de la búsqueda con la ventana de contexto óptima del LLM.
- **Superposición (Overlap)**: Inclusión sistemática de un margen de superposición (ej. 10-15%) entre fragmentos para evitar la pérdida de contexto semántico en los bordes de cada bloque de información.

### 3. Normalización de Embeddings y Metadatos
Una vez que el contenido está segmentado de forma óptima, se prepara para el almacenamiento vectorial:
- **Consistencia de Modelos**: Uso estricto del mismo modelo (`nomic-embed-text`) tanto para generar los vectores de los documentos durante la ingesta como para vectorizar las consultas del usuario.
- **Enriquecimiento con Metadatos**: A cada vector se le inyectan metadatos estructurados (nombre del documento, sección, autor, tema, fecha). Esto permite a **LanceDB** combinar la búsqueda por similitud semántica con un filtrado exacto, aumentando drásticamente la precisión.

### 4. Normalización de la Consulta (Query Processing)
Antes de ejecutar la búsqueda vectorial, la solicitud del usuario es refinada e interpretada:
- **Reescritura de Consulta (Query Rewriting / HyDE)**: Un proceso intermedio utiliza el LLM para reformular la pregunta del usuario haciéndola más clara, concisa y efectiva para la recuperación semántica (extrayendo la intención real detrás de la consulta).
- **Manejo de Sinónimos y Dominio**: Normalización del vocabulario de la consulta para emparejar la jerga o expresiones comunes del usuario con la terminología técnica presente en los documentos.

### 5. Post-procesamiento y Re-ranking (Retrieval & Generation)
El último tramo del pipeline maximiza la relevancia y la presentación de la información:
- **Re-ranking**: Los resultados recuperados inicialmente por la base vectorial pasan por un modelo evaluador secundario (*Cross-Encoder* o *Re-ranker*). Este modelo recalifica y reordena los fragmentos basándose en una comprensión semántica profunda, asegurando que solo el contenido más relevante alimente al LLM.
- **Normalización de Respuestas**: Aplicación de un *Prompt Engineering* estricto que fuerza al LLM a mantener un formato, tono y estilo consistentes en sus respuestas. Esto previene alucinaciones, respuestas excesivamente largas o salidas desestructuradas.

---

## Escalabilidad y Diseño Modular (Future-Proofing)

La implementación de este RAG de primer nivel está sustentada en principios de arquitectura limpia:
- **Interfaces Agnósticas (Ports & Adapters)**: Los componentes complejos (como OCR, Re-rankers, Vector Stores) interactúan a través de interfaces genéricas en `app/services/`. Agregar una nueva herramienta en el futuro (ej. cambiar a un modelo en la nube o integrar LlamaParse para OCR) requiere únicamente añadir un nuevo adaptador, sin necesidad de reescribir la lógica central o la API.
- **Escalabilidad Horizontal**: Aunque la aplicación opera 100% de forma local en su estado actual, la separación clara entre la API (FastAPI) y la lógica de negocio permite escalar o distribuir servicios pesados (como el procesamiento OCR o el re-ranking masivo) a entornos en la nube si las necesidades operativas lo exigen más adelante.
