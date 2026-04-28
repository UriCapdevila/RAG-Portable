const healthCard = document.getElementById("health-card");
const ingestionForm = document.getElementById("ingestion-form");
const ingestionOutput = document.getElementById("ingestion-output");
const chatForm = document.getElementById("chat-form");
const answerCard = document.getElementById("chat-answer");
const sourcesList = document.getElementById("sources-list");
const refreshHealthButton = document.getElementById("refresh-health");

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "La solicitud fallo.");
  }
  return payload;
}

function renderHealth(data) {
  healthCard.innerHTML = `
    <div class="status-pill ${data.ollama_connected ? "ok" : "error"}">
      Ollama: ${data.ollama_connected ? "conectado" : "sin conexion"}
    </div>
    <div class="status-pill ${data.vector_store_ready ? "ok" : "warn"}">
      Vector store: ${data.vector_store_ready ? "listo" : "sin indice"}
    </div>
    <div class="status-meta">
      <span>Chat: ${data.chat_model}</span>
      <span>Embeddings: ${data.embedding_model}</span>
    </div>
  `;
}

function renderAnswer(data) {
  answerCard.innerHTML = `
    <p class="answer-text">${data.answer}</p>
    <p class="answer-meta">Modelo: ${data.model}</p>
  `;

  if (!data.sources.length) {
    sourcesList.innerHTML = "";
    return;
  }

  sourcesList.innerHTML = `
    <h3>Fuentes</h3>
    ${data.sources
      .map(
        (source) => `
          <article class="source-card">
            <strong>${source.file_name}</strong>
            <span>${source.source_path}</span>
          </article>
        `
      )
      .join("")}
  `;
}

async function loadHealth() {
  try {
    const data = await fetchJson("/api/health");
    renderHealth(data);
  } catch (error) {
    healthCard.innerHTML = `<div class="status-pill error">${error.message}</div>`;
  }
}

ingestionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  ingestionOutput.textContent = "Procesando documentos...";

  try {
    const rebuildIndex = document.getElementById("rebuild-index").checked;
    const data = await fetchJson("/api/ingestion/run", {
      method: "POST",
      body: JSON.stringify({ rebuild_index: rebuildIndex }),
    });
    ingestionOutput.textContent = JSON.stringify(data, null, 2);
    await loadHealth();
  } catch (error) {
    ingestionOutput.textContent = error.message;
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = document.getElementById("question").value.trim();
  if (!question) {
    answerCard.innerHTML = `<p class="empty-state">Escribe una pregunta primero.</p>`;
    return;
  }

  answerCard.innerHTML = `<p class="empty-state">Consultando contexto y generando respuesta...</p>`;
  sourcesList.innerHTML = "";

  try {
    const data = await fetchJson("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question }),
    });
    renderAnswer(data);
  } catch (error) {
    answerCard.innerHTML = `<p class="empty-state">${error.message}</p>`;
  }
});

refreshHealthButton.addEventListener("click", loadHealth);

loadHealth();

