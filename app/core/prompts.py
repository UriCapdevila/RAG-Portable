from app.services.personas import Persona


def build_system_prompt(persona: Persona, tool_schemas: list[dict] | None = None) -> str:
    constraints = "\n".join(f"- {item}" for item in persona.constraints) if persona.constraints else "- Sin restricciones adicionales."
    tools_block = ""
    if tool_schemas:
        tools_block = (
            "\nHerramientas disponibles (JSON schema):\n"
            f"{tool_schemas}\n"
            'Si necesitas usar herramienta, responde estrictamente con JSON: {"tool_call": {"name": "...", "args": {...}}}\n'
            'Si no necesitas herramientas, responde estrictamente con JSON: {"answer": "..."}'
        )
    return f"""
Eres {persona.name}, asistente local especializado en {persona.domain}.
Idioma preferido: {persona.language}
Tono: {persona.tone}

Reglas:
- Responde únicamente con información respaldada por el contexto.
- Si falta evidencia suficiente, responde: "{persona.fallback_message}"
- Cita fuentes con formato [Nombre del Archivo].
{constraints}
{tools_block}
""".strip()


def build_user_prompt(question: str, context_blocks: list[str]) -> str:
    joined_context = "\n\n".join(context_blocks)
    return (
        "Contexto recuperado:\n"
        f"{joined_context}\n\n"
        "Pregunta del usuario:\n"
        f"{question}\n\n"
        "Instrucciones:\n"
        "- Responde solo con base en el contexto.\n"
        "- Si falta evidencia, indicalo.\n"
        "- Cita las fuentes relevantes al final."
    )

QUERY_REWRITE_PROMPT = """
Eres un experto en optimización de motores de búsqueda semántica.
Tu tarea es reescribir la consulta del usuario para maximizar las posibilidades de encontrar información relevante en una base de datos vectorial.

Reglas:
1. Extrae la intención principal de la consulta.
2. Añade sinónimos relevantes y jerga de dominio si es aplicable.
3. Elimina palabras vacías (stopwords) o saludos.
4. Devuelve SOLO la consulta reescrita, sin introducciones ni explicaciones.

Consulta original: {question}
Consulta optimizada:
""".strip()

